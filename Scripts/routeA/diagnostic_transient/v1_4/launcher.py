"""Future single-series launcher. prepare() is read-only; execution never automatic.
Production is disabled until contract resource readiness and explicit run authorization.
A failed capacity check does not delete any data.
"""
import hashlib,json,os,subprocess,time
from pathlib import Path
from packed import need
from log_rotation import RawLog
from resource_guard import preflight
H=Path(__file__).resolve().parent

def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def prepare(spec):
    # All identities are pinned BEFORE execution; no input/mesh creation here.
    required={'contract','input','mesh','source','instrumentation','binary','libraries','compiler','analysis'}
    need(set(spec['provenance'])==required,'PREFLIGHT_PROVENANCE_CATEGORIES')
    for category,entries in spec['provenance'].items():
        need(entries,'EMPTY_PROVENANCE_'+category)
        for entry in entries:need(hash_file(entry['path'])==entry['sha256'],'PREFLIGHT_HASH_'+category)
    contract_path=spec['provenance']['contract'][0]['path'];contract=json.loads(Path(contract_path).read_text())
    need(contract['version']=='1.4','PREFLIGHT_CONTRACT_VERSION')
    repository=H.parents[3]
    for rel,digest in contract['resource_revision_fix']['source_SHA256'].items():need(hash_file(repository/rel)==digest,'RUNTIME_IMPLEMENTATION_HASH')
    observer_hash=contract['resource_revision']['replacement_library_sha256']
    need(any(e['sha256']==observer_hash for e in spec['provenance']['libraries']),'PINNED_OBSERVER_LIBRARY_MISSING')
    co=spec['Co'];registered=contract['series']['primary']+[contract['series']['conditional']]
    need(any(x['case_id']==spec['case_id'] and x['Co_target']==co for x in registered),'SERIES_IDENTITY_MISMATCH')
    from lifecycle import Series
    retained=0;previous_targets=[]
    for previous in spec.get('previous_series_seals',[]):
        series=Series(previous['root']);seal=series.verify(previous['seal_id'])
        need(seal['identity']['classification']=='DIAGNOSTIC_OBSERVATION','SYNTHETIC_SEAL_CANNOT_AUTHORIZE_PRODUCTION_SEQUENCE')
        with series.lock() as fd:need(series.state(fd)=='PURGED','PREVIOUS_SERIES_NOT_PURGED')
        previous_targets.append(seal['identity']['Co']);retained+=sum(x['bytes'] for x in seal['must_retain'])
        retained+=sum((series.root/x).stat().st_size for x in ('series_seal_manifest.json','series_seal_manifest.sha256','purge_manifest.json','purge_journal.jsonl','lifecycle.jsonl') if (series.root/x).exists())
    need(sorted(previous_targets)==([] if co==.5 else [.5] if co==.25 else [.25,.5]),'SEQUENTIAL_PREVIOUS_SERIES_MISSING')
    need(spec['existing_permanent_bytes']==retained,'EXISTING_PERMANENT_FOOTPRINT_NOT_MEASURED')
    model=contract['resource_revision_fix']['capacity']['series'][str(co)]
    need(spec['planned_files']>=model['file_bound'],'FILE_BUDGET_TOO_SMALL')
    need(spec['planned_peak_bytes']==model['working_peak_bytes'] and spec['post_seal_bytes']==model['permanent_bytes'],'UNREGISTERED_STORAGE_MODEL')
    need(Path(spec['export_root']).absolute()==repository/'results/routeA/diagnostic_transient/diagnostic_attempt_001/series'/spec['case_id'],'UNREGISTERED_EXPORT_NAMESPACE')
    need(not Path(spec['export_root']).exists(),'EXPORT_ROOT_MUST_BE_NEW')
    space_root=Path(spec['export_root']).parent
    while not space_root.exists():space_root=space_root.parent
    guard=preflight(space_root,spec['planned_peak_bytes'],spec['planned_files'],co,spec.get('conditional_authorized',False))
    # Current free space already excludes existing permanent bytes. Keep the user's
    # stricter additional reserve as a conservative reserve, not extra actual usage.
    safety=max(32*2**30,int(.10*guard['free_bytes']))
    existing=spec['existing_permanent_bytes']
    need(existing>=0 and guard['free_bytes']>spec['planned_peak_bytes']+existing+safety,'SEQUENTIAL_DISK_GUARD')
    if co==.125:need(spec.get('separate_resource_review_id') and spec.get('conditional_authorization_id'),'C3_STOP_REVIEW_AND_EXPLICIT_AUTHORIZATION')
    return dict(guard,contract_sha256=hash_file(contract_path),contract_path=contract_path,export_root=str(Path(spec['export_root']).absolute()),Co=co,case_id=spec['case_id'],existing_permanent_bytes=existing,safety_bytes=safety,provenance=spec['provenance'],post_seal_bytes=spec['post_seal_bytes'],scratch_bytes=16*2**30,resource_ready=contract['final_status']['DIAGNOSTIC_TRANSIENT_RESOURCE_READY']=='YES')

class LogPublisher:
    """Independent immutable raw log chain; merged into the series seal as R0."""
    def __init__(self,root):self.root=Path(root);self.chain='0'*64;self.total=0
    def publish(self,name,raw,kind):
        need(self.root.is_dir(),'NATIVE_EXPORT_ROOT_NOT_CREATED')
        tmp=self.root/(name+'.partial')
        with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.link(tmp,self.root/name);tmp.unlink()
        entry={'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'previous':self.chain};self.chain=hashlib.sha256(json.dumps(entry,sort_keys=True).encode()).hexdigest();entry['chain']=self.chain
        with (self.root/'raw_log_manifest.jsonl').open('ab') as f:f.write((json.dumps(entry,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
        fd=os.open(self.root,os.O_DIRECTORY);os.fsync(fd);os.close(fd);self.total+=len(raw)
    def finish(self,exit_code):
        with (self.root/'raw_log_completion.json').open('x') as f:json.dump({'exit_code':exit_code,'bytes':self.total,'chain':self.chain,'complete':exit_code==0},f,sort_keys=True);f.flush();os.fsync(f.fileno())
        fd=os.open(self.root,os.O_DIRECTORY);os.fsync(fd);os.close(fd)

def run(spec,explicit_run_authorization_id):
    receipt=prepare(spec)
    need(receipt['resource_ready'],'RESOURCE_READY_NO_NO_EXECUTION')
    need(explicit_run_authorization_id,'EXPLICIT_RUN_AUTHORIZATION_REQUIRED')
    # C3 and all hashes/capacity rechecked at the immediate execution boundary.
    receipt=prepare(spec)
    receipt_path=Path(spec['preflight_receipt_path']);raw=(json.dumps(receipt,sort_keys=True)+'\n').encode()
    with receipt_path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    env=dict(os.environ,**spec['native_environment']);env.update(ROUTE_A_PREFLIGHT_RECEIPT=str(receipt_path),ROUTE_A_PREFLIGHT_RECEIPT_SHA256=hashlib.sha256(raw).hexdigest(),ROUTE_A_BIND_LIVE='1',ROUTE_A_P1_SERVER=str(H/'server.py'),ROUTE_A_P1_SERVER_SHA256=hash_file(H/'server.py'),ROUTE_A_DIAGNOSTIC_CONTRACT_FILE=receipt['contract_path'])
    binary=spec['provenance']['binary'][0]['path'];need(spec['command'][0]==binary,'UNPINNED_BINARY')
    Path(spec['export_root']).parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    publisher=LogPublisher(spec['export_root']);logs=RawLog(publisher)
    with subprocess.Popen(spec['command'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT) as p:
        try:
            while True:
                block=p.stdout.read(64*1024)
                if not block:break
                logs.write(block)
            code=p.wait();logs.flush();publisher.finish(code)
        except BaseException:
            p.terminate();p.wait();publisher.root.mkdir(exist_ok=True);logs.flush();publisher.finish(p.returncode or -1);raise
    need(code==0,'NATIVE_RUN_FAILED_EVIDENCE_PRESERVED');return receipt

def verify_preflight_receipt(root,guard):
    path=os.environ['ROUTE_A_PREFLIGHT_RECEIPT'];need(hash_file(path)==os.environ['ROUTE_A_PREFLIGHT_RECEIPT_SHA256'],'PREFLIGHT_RECEIPT_HASH')
    x=json.loads(Path(path).read_text());need(x['export_root']==str(Path(root).absolute()) and x['contract_sha256']==guard and x['resource_ready'],'PREFLIGHT_AUTHORITY_MISMATCH')
    for entries in x['provenance'].values():
        for e in entries:need(hash_file(e['path'])==e['sha256'],'PREFLIGHT_PROVENANCE_CHANGED')
    return x
