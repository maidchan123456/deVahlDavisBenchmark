"""Immutable per-series seal and explicitly authorized, flat allowlist purge.
No directory deletion, symlink following, automatic capacity-driven purge or resume.
The owner must keep the series directory private and quiescent during validation/purge.
"""
import contextlib,fcntl,hashlib,json,os,stat,time
from pathlib import Path

CHECKS=('run_complete','raw_log','primary_history','U01','U03','mass_energy','selected_replay','StageLedger','selected_fields','provenance','final_statistics','limitations')
PROVENANCE=('contract','input','mesh','source','instrumentation','binary','libraries','compiler','analysis')
CONTROL={'lifecycle.lock','lifecycle.jsonl','validation.json','series_seal_manifest.json','series_seal_manifest.sha256','purge_manifest.json','purge_journal.jsonl'}
CLASSES={'R0','R1','R2','R3','R4'}
REPOSITORY=Path(__file__).resolve().parents[4]
PRODUCTION_BASE=REPOSITORY/'results/routeA/diagnostic_transient/diagnostic_attempt_001/series'
SYNTHETIC_BASE=REPOSITORY/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/resource_revision_fix'

def need(ok,why):
    if not ok:raise ValueError(why)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def name(path):
    need(isinstance(path,str) and path not in ('','.','..') and '/' not in path and '\\' not in path and not path.startswith('.'),'UNSAFE_PATH')
    need(path not in CONTROL,'CONTROL_PATH');return path

def required_retention(path):
    # Classification is independently constrained, never trusted from the purge list.
    if path.startswith(('validation_copy_','nonselected_raw_','nonselected_fields_','expanded_temporary_','conversion_temporary_')):return 'R3'
    if path.startswith(('scratch_','replay_workspace_','atomic_temporary_')):return 'R4'
    if path in ('initial_state.bin','final_fields.bin') or path.startswith(('fields_','trigger_fields_')):return 'R2'
    if path=='final_bundle.bin' or path.endswith('.bin') and path.startswith(('full_','bundle_','anomaly_')):return 'R1'
    return 'R0'

class Series:
    def __init__(self,root):
        self.root=Path(root).absolute()
        need(not self.root.is_symlink() and self.root==self.root.resolve(),'ROOT_SYMLINK_OR_TRAVERSAL')
        need(self.root.is_dir(),'ROOT_MISSING')
        production=self.root.is_relative_to(PRODUCTION_BASE) and self.root!=PRODUCTION_BASE
        synthetic=self.root.is_relative_to(SYNTHETIC_BASE) and self.root.relative_to(SYNTHETIC_BASE).parts and self.root.relative_to(SYNTHETIC_BASE).parts[0].startswith('lifecycle_test')
        need(production or synthetic,'OUTSIDE_REGISTERED_ALLOWED_ROOT')
        self.synthetic_root=bool(synthetic)
    @contextlib.contextmanager
    def lock(self):
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        lock=os.open('lifecycle.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield fd
        finally:fcntl.flock(lock,fcntl.LOCK_UN);os.close(lock);os.close(fd)
    def read(self,fd,path):
        f=os.open(path,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            st=os.fstat(f);need(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'NOT_PRIVATE_REGULAR_FILE')
            blocks=[]
            while True:
                b=os.read(f,2**20)
                if not b:break
                blocks.append(b)
            return b''.join(blocks)
        finally:os.close(f)
    def digest(self,fd,path):
        f=os.open(path,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            st=os.fstat(f);need(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'NOT_PRIVATE_REGULAR_FILE')
            h=hashlib.sha256();size=0
            while True:
                b=os.read(f,2**20)
                if not b:break
                h.update(b);size+=len(b)
            end=os.fstat(f);need((st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino),'CHANGED_DURING_HASH')
            return {'bytes':size,'sha256':h.hexdigest()}
        finally:os.close(f)
    def write(self,fd,path,value):
        raw=canonical(value)+b'\n';f=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400,dir_fd=fd)
        try:
            offset=0
            while offset<len(raw):offset+=os.write(f,raw[offset:])
            os.fsync(f)
        finally:os.close(f)
        os.fsync(fd);return sha(raw)
    def append(self,fd,path,event):
        if path in os.listdir(fd):
            previous=self.events(fd,path);chain=previous[-1]['chain'] if previous else '0'*64
        else:chain='0'*64
        item=dict(event,timestamp_UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),previous=chain)
        item['chain']=sha(canonical(item));raw=canonical(item)+b'\n'
        f=os.open(path,os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
        try:
            offset=0
            while offset<len(raw):offset+=os.write(f,raw[offset:])
            os.fsync(f)
        finally:os.close(f)
        os.fsync(fd)
    def events(self,fd,path):
        raw=self.read(fd,path);need(not raw or raw.endswith(b'\n'),'INTERRUPTED_JOURNAL')
        rows=[];chain='0'*64
        for line in raw.splitlines():
            row=json.loads(line);claimed=row.pop('chain');need(row['previous']==chain and sha(canonical(row))==claimed,'INVALID_JOURNAL_CHAIN');row['chain']=claimed;chain=claimed;rows.append(row)
        return rows
    def begin(self):
        with self.lock() as fd:
            need('lifecycle.jsonl' not in os.listdir(fd),'ALREADY_STARTED');self.append(fd,'lifecycle.jsonl',{'state':'RUNNING'})
    def state(self,fd):return self.events(fd,'lifecycle.jsonl')[-1]['state']
    def seal(self,classification,identity,provenance,validator):
        """validator reads actual artifacts and must return all registered checks PASS.
        FAIL/NOT_APPLICABLE may not be used to seal a scientific production series.
        Synthetic fixture validators have an explicit synthetic identity/limitations.
        """
        with self.lock() as fd:
            need(self.state(fd)=='RUNNING','SEAL_WRONG_STATE');need(identity['classification'].startswith('SYNTHETIC')==self.synthetic_root,'SEAL_SCOPE_ROOT_MISMATCH')
            need(set(provenance)==set(PROVENANCE),'PROVENANCE_MISSING')
            need(all(isinstance(v,str) and len(v)==64 and set(v)<=set('0123456789abcdef') for v in provenance.values()),'PROVENANCE_HASH')
            need({'case_id','Co','start_time','end_time','classification'}<=identity.keys(),'IDENTITY_MISSING')
            need(identity['Co'] in (.5,.25,.125) and identity['end_time']>=identity['start_time'],'IDENTITY_INVALID')
            expected=set(classification)|CONTROL
            need(set(os.listdir(fd))<=expected,'UNKNOWN_FILE')
            need(all(c in CLASSES for c in classification.values()),'UNKNOWN_CLASS')
            for path,c in classification.items():
                name(path);need(c==required_retention(path),'RETENTION_CLASS_VIOLATION_'+path)
            self.append(fd,'lifecycle.jsonl',{'state':'VALIDATING'})
            validation=validator(self.root)
            need(set(validation['checks'])==set(CHECKS) and all(x=='PASS' for x in validation['checks'].values()),'VALIDATION_FAILED')
            self.write(fd,'validation.json',validation)
            entries=[]
            for path,c in sorted(classification.items()):entries.append(dict(path=path,classification=c,**self.digest(fd,path)))
            need(sum(x['bytes'] for x in entries if x['classification'] in {'R3','R4'})<=16*2**30,'SHARED_TEMPORARY_SCRATCH_CAP')
            if not identity['classification'].startswith('SYNTHETIC'):
                retained_hashes={x['sha256'] for x in entries if x['classification']=='R0'}
                need(set(provenance.values())<=retained_hashes,'PROVENANCE_DOCUMENTS_MUST_BE_RETAINED_R0')
            # Validation report is immutable permanent core too.
            entries.append(dict(path='validation.json',classification='R0',**self.digest(fd,'validation.json')))
            keep=[x for x in entries if x['classification'] in {'R0','R1','R2'}]
            remove=[dict(x,reason_deletable='Nonselected validation copy or scratch; permanent original evidence verified',replacement_evidence=[k['path'] for k in keep],regeneration_method='REGENERABLE_BY_RECOMPUTATION; same sealed inputs/mesh/source/contract, no bitwise rerun guarantee') for x in entries if x['classification'] in {'R3','R4'}]
            manifest={'schema':'routeA_series_seal/1.4','identity':identity,'provenance_sha256':provenance,'validation':'PASS','must_retain':keep,'purge_eligible':remove,'limitations':validation['limitations'],'retained_content_not_replaced_by_rerun':True}
            seal_id=self.write(fd,'series_seal_manifest.json',manifest)
            self.write(fd,'series_seal_manifest.sha256',{'seal_id':seal_id})
            self.write(fd,'purge_manifest.json',{'seal_id':seal_id,'entries':remove,'authorization_required':True})
            self.append(fd,'lifecycle.jsonl',{'state':'SEALED','seal_id':seal_id})
            return seal_id
    def verify_locked(self,fd,seal_id,allow_purged=False):
        raw=self.read(fd,'series_seal_manifest.json');need(sha(raw)==seal_id,'INVALID_SEAL_HASH')
        need(json.loads(self.read(fd,'series_seal_manifest.sha256'))['seal_id']==seal_id,'SEAL_ID_MISMATCH')
        seal=json.loads(raw);purge=json.loads(self.read(fd,'purge_manifest.json'))
        need(purge=={'seal_id':seal_id,'entries':seal['purge_eligible'],'authorization_required':True},'PURGE_MANIFEST_MISMATCH')
        for x in seal['must_retain']+seal['purge_eligible']:
            if x['path']!='validation.json':need(x['classification']==required_retention(x['path']),'SEALED_RETENTION_CLASS_VIOLATION')
        known={x['path'] for x in seal['must_retain']+seal['purge_eligible']}|CONTROL
        need(set(os.listdir(fd))<=known,'UNKNOWN_FILE')
        deleted=set();journal=[]
        if 'purge_journal.jsonl' in os.listdir(fd):
            journal=self.events(fd,'purge_journal.jsonl')
            need(journal and journal[-1]['event']=='COMPLETED','PARTIAL_OR_INTERRUPTED_PURGE')
            need(all(j['seal_id']==seal_id and j['authorization_status']=='EXPLICIT' for j in journal),'JOURNAL_AUTHORITY')
            intents=[x['path'] for x in journal if x['event']=='INTENT'];results=[x['path'] for x in journal if x['event']=='DELETED']
            need(intents==results and len(set(results))==len(results),'PARTIAL_PURGE')
            deleted=set(results);need(deleted=={x['path'] for x in seal['purge_eligible']},'PARTIAL_PURGE')
        need(not deleted or allow_purged,'ALREADY_PURGED')
        for x in seal['must_retain']+seal['purge_eligible']:
            if x['path'] in deleted:
                need(x['classification'] in {'R3','R4'} and x['path'] not in os.listdir(fd),'PURGE_CORE_OR_REAPPEARED');continue
            d=self.digest(fd,x['path']);need(d=={k:x[k] for k in ('bytes','sha256')},'SEALED_FILE_CHANGED')
        return seal
    def verify(self,seal_id):
        with self.lock() as fd:return self.verify_locked(fd,seal_id,True)
    def dry_run(self,seal_id):
        with self.lock() as fd:
            need(self.state(fd) in {'SEALED','PURGE_ELIGIBLE'},'PURGE_WRONG_STATE')
            seal=self.verify_locked(fd,seal_id)
            plan={'seal_id':seal_id,'files':[x['path'] for x in seal['purge_eligible']],'bytes_reclaimed':sum(x['bytes'] for x in seal['purge_eligible']),'retained_evidence':[x['path'] for x in seal['must_retain']]}
            plan['dry_run_id']=sha(canonical(plan))
            if self.state(fd)=='SEALED':self.append(fd,'lifecycle.jsonl',{'state':'PURGE_ELIGIBLE','seal_id':seal_id,'dry_run_id':plan['dry_run_id']})
            return plan
    def purge(self,seal_id,dry_run_id,authorization_id,explicit_authorized=False,inject_interrupt_after=None):
        need(explicit_authorized and isinstance(authorization_id,str) and bool(authorization_id.strip()),'USER_AUTHORIZATION_REQUIRED')
        with self.lock() as fd:
            need(self.state(fd)=='PURGE_ELIGIBLE','DRY_RUN_REQUIRED')
            seal=self.verify_locked(fd,seal_id)
            plan={'seal_id':seal_id,'files':[x['path'] for x in seal['purge_eligible']],'bytes_reclaimed':sum(x['bytes'] for x in seal['purge_eligible']),'retained_evidence':[x['path'] for x in seal['must_retain']]}
            need(sha(canonical(plan))==dry_run_id and self.events(fd,'lifecycle.jsonl')[-1]['dry_run_id']==dry_run_id,'STALE_DRY_RUN')
            base={'seal_id':seal_id,'authorization_id':authorization_id,'authorization_status':'EXPLICIT'}
            # Prevalidate the entire allowlist before the first unlink.
            for x in seal['purge_eligible']:need(x['classification'] in {'R3','R4'},'CORE_PURGE_FORBIDDEN');name(x['path'])
            for i,x in enumerate(seal['purge_eligible']):
                need(self.digest(fd,x['path'])=={k:x[k] for k in ('bytes','sha256')},'CHANGED_AFTER_DRY_RUN')
                self.append(fd,'purge_journal.jsonl',dict(base,event='INTENT',path=x['path'],bytes=x['bytes']))
                if inject_interrupt_after==i:raise RuntimeError('INJECTED_INTERRUPT; manual recovery required, no automatic resume')
                os.unlink(x['path'],dir_fd=fd);os.fsync(fd)
                self.append(fd,'purge_journal.jsonl',dict(base,event='DELETED',path=x['path'],bytes=x['bytes']))
            self.append(fd,'purge_journal.jsonl',dict(base,event='COMPLETED',bytes_reclaimed=plan['bytes_reclaimed']))
            self.append(fd,'lifecycle.jsonl',{'state':'PURGED','seal_id':seal_id})
            self.verify_locked(fd,seal_id,True)
            return plan
