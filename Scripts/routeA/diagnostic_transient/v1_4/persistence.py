"""P1 bounded retention, fail-closed chunk commits and verified reload; no CFD."""
import collections,hashlib,json,math,os,struct
from pathlib import Path
from packed import encode,decode,sha,need,EvidenceFailure
from online_evaluator import canonical,norms
CHUNK_STEPS=64
SCRATCH_CAP=16*2**30
RING_CAP=2**30
STAGE_CAP=32*2**20
BUNDLE_CAP=512*2**20
AUDIT_CAP=9*2**30
FIELD_CAP=16*2**20
class Schedule:
    """All targets map to the first completed step after crossing, without dt edits."""
    def __init__(self):
        self.full_targets=collections.deque([.5,1.,1.5,1.99])
        self.bundle_targets=collections.deque([i*.05 for i in range(1,41)])
        self.field_targets=collections.deque([i*.001 for i in range(1,51)]+[.05+i*.005 for i in range(1,391)])
        self.step=0;self.full=False;self.selected=False;self.field=False
        self.full_count=self.bundle_count=0;self.field_count=1 # initial constructor snapshot t*=0
    def begin(self,time):
        self.step+=1;t=time/710
        def crosses(q):
            hit=False
            while q and t+1e-14>=q[0]:q.popleft();hit=True
            return hit
        self.full=self.step<=3 or crosses(self.full_targets)
        self.selected=crosses(self.bundle_targets)
        self.field=crosses(self.field_targets)
        if self.full:self.full_count+=1
        if self.selected:self.bundle_count+=1
        if self.field:self.field_count+=1
        need(self.full_count<=7 and self.bundle_count<=40 and self.field_count<=441,'SCHEDULE_QUOTA')

def receipt_bytes(receipt):
    """Stage identity + folded full epoch identity + all computed scalar metrics."""
    m=receipt['metadata']
    # Every matrix/field/oldTime/BC identity is folded into this exact metadata digest.
    identity=bytes.fromhex(sha(canonical(m).encode()))
    payload=bytes.fromhex(receipt['payload_sha256'])
    metrics={}
    def flatten(x,path=''):
        if isinstance(x,dict):
            for k,v in sorted(x.items()):flatten(v,path+'/'+k)
        elif isinstance(x,list):
            for i,v in enumerate(x):flatten(v,path+'/'+str(i))
        elif type(x) in (int,float):metrics[path]=float(x)
    flatten(receipt['matrix_metrics'],'matrix');flatten(receipt['term_metrics'],'terms')
    sync=receipt['synchronization']
    # Do not retain sync cell arrays: retain global/L1/Linf and max-cell instead.
    for i,s in enumerate(sync):
        for key,value in s.items():
            if isinstance(value,list) and value and all(type(v) in (int,float) for v in value):
                metrics[f'sync/{i}/{key}/sum']=math.fsum(value)
                metrics[f'sync/{i}/{key}/L1']=math.fsum(abs(v) for v in value)/len(value)
                metrics[f'sync/{i}/{key}/Linf']=max(abs(v) for v in value)
                metrics[f'sync/{i}/{key}/max_cell']=float(max(range(len(value)),key=lambda j:abs(value[j])))
            elif key=='energy_end_terms':
                for term,values in value.items():
                    metrics[f'sync/{i}/energy_end_terms/{term}/sum']=math.fsum(values)
                    metrics[f'sync/{i}/energy_end_terms/{term}/absolute']=math.fsum(abs(v) for v in values)
            else:flatten(value,f'sync/{i}/{key}')
    base=[receipt['sequence'],m['time_index'],m['outer'],m['pressure'],m['nonOrthogonal'],m['energy_solve'],m['rho_solve'],m['physical_time'],m['deltaT'],m['previous_deltaT']]
    return {'stage':m['stage'],'values':base+[metrics[k] for k in sorted(metrics)],'columns':sorted(metrics),'identity':identity,'payload':payload,'valid':receipt['valid'],'term_name':receipt.get('term_name')}

class Writer:
    def __init__(self,root,chunk_steps=CHUNK_STEPS,ring_cap=RING_CAP,stage_cap=STAGE_CAP):
        self.retained_limit=int(os.environ.get('ROUTE_A_SERIES_RETAINED_CAP_BYTES',450*10**9));need(self.retained_limit>0,'RETAINED_LIMIT')
        self.root=Path(root);self.root.mkdir(exist_ok=True)
        need(not any(self.root.iterdir()),'ROOT_NOT_EMPTY')
        self.chunk_steps=chunk_steps;self.ring_cap=ring_cap;self.stage_cap=stage_cap
        self.schema={};self.rows=[];self.rows_bytes=0;self.events=0;self.completed_steps=0;self.chunk_start=1
        self.chain='0'*64;self.manifest=[];self.fsyncs=0;self.written_bytes=0
        self.schedule=Schedule();self.full=[];self.full_bytes=0;self.bundle=[];self.bundle_bytes=0
        self.ring=collections.deque();self.ring_bytes=0;self.peak_ring_bytes=0;self.anomalies=0
        self.first_state=None;self.closed=False;self.immutable={};self.immutable_keys={};self.full_spool=None;self.final_field=None
    def share(self,value):
        # Only source-static mesh data and frozen constant properties. Exact bytes
        # must remain equal at every callback, otherwise fail before discard.
        keys={'geometry','volumes','Cv','g','owner','neighbour'}
        def walk(x):
            if isinstance(x,dict):
                result={}
                for key,v in x.items():
                    if key in keys:
                        raw=encode(v);digest=sha(raw)
                        need(key not in self.immutable_keys or self.immutable_keys[key]==digest,'STATIC_BLOB_CHANGED: '+key)
                        self.immutable_keys[key]=digest
                        if digest not in self.immutable:
                            self.immutable[digest]=v;self.publish('immutable_'+digest+'.bin',raw,'immutable')
                        result[key]={'$immutable':digest}
                    else:result[key]=walk(v)
                return result
            if isinstance(x,list):return [walk(v) for v in x]
            return x
        return walk(value)
    def publish(self,name,raw,kind):
        need(self.written_bytes+len(raw)<=self.retained_limit,'RETAINED_QUOTA')
        path=self.root/name;tmp=self.root/(name+'.partial');need(not path.exists(),'DUPLICATE_PUBLICATION')
        need(os.statvfs(self.root).f_bavail*os.statvfs(self.root).f_frsize>=len(raw)+SCRATCH_CAP,'DISK_GUARD')
        try:
            with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno());self.fsyncs+=1
            os.link(tmp,path);tmp.unlink()
            fd=os.open(self.root,os.O_DIRECTORY);os.fsync(fd);self.fsyncs+=1;os.close(fd)
            entry={'file':name,'kind':kind,'bytes':len(raw),'sha256':sha(raw),'previous':self.chain}
            self.chain=sha(json.dumps(entry,sort_keys=True,separators=(',',':')).encode());entry['chain']=self.chain
            with (self.root/'manifest.jsonl').open('ab') as f:
                f.write((json.dumps(entry,sort_keys=True,separators=(',',':'))+'\n').encode());f.flush();os.fsync(f.fileno());self.fsyncs+=1
            self.manifest.append(entry);self.written_bytes+=len(raw)
        except OSError as e:raise EvidenceFailure('EVIDENCE_FAILURE: ATOMIC_COMMIT '+str(e)) from e
    def chunk(self):
        if not self.rows:return
        meta=json.dumps({'schema':'routeA_receipts/1.3','schema_table':self.schema,'events':len(self.rows),'first_sequence':self.chunk_start,'last_sequence':self.events,'steps':self.completed_steps},sort_keys=True,separators=(',',':')).encode()
        raw=b'RAC13\0'+struct.pack('<Q',len(meta))+meta+b''.join(self.rows)
        need(len(raw)<=64*1024*1024,'CHUNK_MEMORY_QUOTA')
        self.publish(f'chunk_{self.chunk_start:010d}_{self.events:010d}.bin',raw,'receipts')
        self.rows=[];self.rows_bytes=0;self.schema={};self.chunk_start=self.events+1
    def accept(self,r,receipt):
        need(not self.closed,'AFTER_FINISH');self.events+=1;need(r['sequence']==self.events,'MISSING_DUPLICATE_STAGE')
        m=r['metadata'];stage=m['stage']
        if stage=='time_start':self.schedule.begin(m['physical_time']);self.full=[];self.full_bytes=0;self.bundle=[];self.bundle_bytes=0
        compact=receipt_bytes(receipt);key=json.dumps([compact['stage'],compact['columns'],compact['term_name']],separators=(',',':'))
        need(compact['valid'] is True,'INVALID_ONLINE_RECEIPT')
        if key not in self.schema:self.schema[key]=len(self.schema)
        values=compact['values'];need(all(math.isfinite(v) for v in values),'NONFINITE_RECEIPT')
        row=struct.pack('<II',self.schema[key],len(values))+compact['identity']+compact['payload']+struct.pack('<'+'d'*len(values),*values)
        self.rows.append(row);self.rows_bytes+=len(row);need(self.rows_bytes<=64*2**20,'CHUNK_MEMORY_QUOTA')
        packed=encode(self.share(r) if stage!='auxiliary_fixture' else r);need(len(packed)<=self.stage_cap,'STAGE_MEMORY_QUOTA')
        self.ring.append(packed);self.ring_bytes+=len(packed)
        while len(self.ring)>16 or self.ring_bytes>self.ring_cap:
            self.ring_bytes-=len(self.ring.popleft())
        self.peak_ring_bytes=max(self.peak_ring_bytes,self.ring_bytes)
        if stage=='constructor_complete':
            self.publish('initial_state.bin',encode(self.share(r['payload']['native_state_epoch'])),'field_initial')
        if self.schedule.full and stage not in {'constructor_complete','preSolve_before','preSolve_after','controller_complete','auxiliary_fixture'}:
            if self.full_spool is None:
                self.full_spool=(self.root/'full_audit.scratch').open('xb');self.full_spool.write(b'RAB13\0')
            self.full_spool.write(struct.pack('<Q',len(packed))+packed);self.full_bytes+=len(packed)+8
            need(self.full_bytes<=AUDIT_CAP and self.full_bytes<=SCRATCH_CAP,'FULL_AUDIT_QUOTA')
        # Density predictor7 records plus complete terminal outer52 records.
        selected=m['outer']==24 or m['outer']==1 and m['pressure']==0 and (stage in {'before_correctDensity','mass_unrelaxed_assembly','mass_after_solve','after_correctDensity'} or stage=='term_capture' and r['payload']['term'] in {'D_B_rho','div_phi','mass_models'})
        if selected and stage!='auxiliary_fixture':
            self.bundle.append(packed);self.bundle_bytes+=len(packed);need(self.bundle_bytes<=BUNDLE_CAP,'BUNDLE_MEMORY_QUOTA')
        if stage=='time_end':
            self.final_field=encode(self.share(r['payload']['native_state_epoch']));need(len(self.final_field)<=FIELD_CAP,'MANDATORY_FINAL_FIELD_QUOTA')
            self.completed_steps+=1
            if self.schedule.full:
                self.full_spool.flush();os.fsync(self.full_spool.fileno());self.fsyncs+=1;self.full_spool.close();self.full_spool=None
                self.publish_spool(f'full_{m["time_index"]}.bin','full_audit')
            if self.schedule.selected:self.audit(self.bundle,f'bundle_{m["time_index"]}.bin','selected_audit')
            if self.schedule.field:self.snapshot(r['payload']['native_state_epoch'],f'fields_{m["time_index"]}.bin')
            if self.completed_steps%self.chunk_steps==0:self.chunk()
            self.full=[];self.full_bytes=0
    def publish_spool(self,name,kind):
        scratch=self.root/'full_audit.scratch';need(scratch.stat().st_size<=AUDIT_CAP,'SCRATCH_QUOTA')
        path=self.root/name;need(not path.exists(),'DUPLICATE_PUBLICATION')
        need(self.written_bytes+scratch.stat().st_size<=self.retained_limit,'RETAINED_QUOTA')
        digest=hashlib.sha256()
        with scratch.open('rb') as f:
            for block in iter(lambda:f.read(2**20),b''):digest.update(block)
        size=scratch.stat().st_size;os.link(scratch,path);scratch.unlink()
        fd=os.open(self.root,os.O_DIRECTORY);os.fsync(fd);self.fsyncs+=1;os.close(fd)
        e={'file':name,'kind':kind,'bytes':size,'sha256':digest.hexdigest(),'previous':self.chain}
        self.chain=sha(json.dumps(e,sort_keys=True,separators=(',',':')).encode());e['chain']=self.chain
        with (self.root/'manifest.jsonl').open('ab') as f:f.write((json.dumps(e,sort_keys=True,separators=(',',':'))+'\n').encode());f.flush();os.fsync(f.fileno());self.fsyncs+=1
        self.manifest.append(e);self.written_bytes+=size
    def audit(self,packed_records,name,kind):
        raw=b'RAB13\0'+b''.join(struct.pack('<Q',len(p))+p for p in packed_records)
        self.publish(name,raw,kind)
    def snapshot(self,state,name):
        raw=encode(self.share(state));need(len(raw)<=FIELD_CAP,'MANDATORY_FIELD_QUOTA');self.publish(name,raw,'field')
    def anomaly(self,reason):
        self.anomalies+=1;need(self.anomalies<=16,'ANOMALY_QUOTA')
        self.audit(list(self.ring),f'anomaly_{self.anomalies:03d}.bin','anomaly_recent16')
        self.publish(f'anomaly_{self.anomalies:03d}.json',json.dumps({'reason':reason,'last_sequence':self.events,'scope':'last16stages only; no unavailable full-step reconstruction'},sort_keys=True).encode(),'event')
    def finish(self,summary):
        need(self.completed_steps>0,'NO_COMPLETE_STEP');self.chunk()
        # Current terminal bundle is available for actual final-window endpoint.
        self.audit(self.bundle,'final_bundle.bin','final_audit');self.publish('final_fields.bin',self.final_field,'field');self.publish('evaluator_summary.json',json.dumps(summary,sort_keys=True,allow_nan=False).encode(),'summary')
        raw=json.dumps({'complete':True,'schema':'routeA_run/1.3','events':self.events,'steps':self.completed_steps,'chain':self.chain,'manifest_sha256':sha((self.root/'manifest.jsonl').read_bytes()),'interruption_invalidates_primary':True},sort_keys=True).encode()
        with (self.root/'complete.json.partial').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno());self.fsyncs+=1
        os.link(self.root/'complete.json.partial',self.root/'complete.json');(self.root/'complete.json.partial').unlink()
        fd=os.open(self.root,os.O_DIRECTORY);os.fsync(fd);self.fsyncs+=1;os.close(fd);self.closed=True

def restore(value,root):
    def walk(x):
        if isinstance(x,dict) and set(x)=={'$immutable'}:
            digest=x['$immutable'];need(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'IMMUTABLE_IDENTITY')
            raw=(Path(root)/('immutable_'+digest+'.bin')).read_bytes();need(sha(raw)==digest,'IMMUTABLE_HASH');return decode(raw)
        if isinstance(x,dict):return {k:walk(v) for k,v in x.items()}
        if isinstance(x,list):return [walk(v) for v in x]
        return x
    return walk(value)

def load_bundle(raw,root=None):
    need(raw[:6]==b'RAB13\0','BUNDLE_SCHEMA');position=6;records=[]
    while position<len(raw):
        need(position+8<=len(raw),'BUNDLE_TRUNCATED');n=struct.unpack('<Q',raw[position:position+8])[0];position+=8
        need(position+n<=len(raw),'BUNDLE_TRUNCATED');value=decode(raw[position:position+n]);records.append(restore(value,root) if root else value);position+=n
    return records

def iter_bundle_file(root,filename):
    path=Path(root)/filename
    with path.open('rb') as f:
        need(f.read(6)==b'RAB13\0','BUNDLE_SCHEMA')
        while True:
            length=f.read(8)
            if not length:return
            need(len(length)==8,'BUNDLE_TRUNCATED');n=struct.unpack('<Q',length)[0]
            need(0<n<=STAGE_CAP,'BUNDLE_STAGE_CAP');raw=f.read(n);need(len(raw)==n,'BUNDLE_TRUNCATED')
            yield restore(decode(raw),root)

def file_digest(path):
    h=hashlib.sha256();total=0
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block);total+=len(block)
    return h.hexdigest(),total

def verify(root,external_files=()):
    root=Path(root);done=json.loads((root/'complete.json').read_text());manifest=(root/'manifest.jsonl').read_bytes()
    need(done['complete'] and done['schema']=='routeA_run/1.3' and sha(manifest)==done['manifest_sha256'],'BAD_MANIFEST_COMPLETION')
    chain='0'*64;expected={'manifest.jsonl','complete.json'}|(set(external_files)&{p.name for p in root.iterdir()});event_count=0
    for line in manifest.splitlines():
        e=json.loads(line);claimed=e.pop('chain');need(e['previous']==chain and sha(json.dumps(e,sort_keys=True,separators=(',',':')).encode())==claimed,'MANIFEST_CHAIN');chain=claimed
        path=root/e['file'];need(path.name==e['file'],'UNSAFE_FILE');digest,size=file_digest(path);need(size==e['bytes'] and digest==e['sha256'],'FILE_HASH');expected.add(e['file']);raw=path.read_bytes() if e['kind'] not in {'full_audit','selected_audit','final_audit','anomaly_recent16'} else None
        if e['kind']=='receipts':
            need(raw[:6]==b'RAC13\0','CHUNK_SCHEMA');n=struct.unpack('<Q',raw[6:14])[0];h=json.loads(raw[14:14+n]);need(h['schema']=='routeA_receipts/1.3','CHUNK_SCHEMA');pos=14+n
            for _ in range(h['events']):
                need(pos+72<=len(raw),'CHUNK_TRUNCATED');sid,count=struct.unpack('<II',raw[pos:pos+8]);pos+=72
                need(sid in h['schema_table'].values() and count>=10 and pos+count*8<=len(raw),'CHUNK_SHAPE')
                v=struct.unpack('<'+'d'*count,raw[pos:pos+count*8]);need(all(math.isfinite(x) for x in v),'NONFINITE');event_count+=1;need(v[0]==event_count,'MISSING_DUPLICATE_EVENTS');pos+=count*8
            need(pos==len(raw),'CHUNK_ORPHAN')
        elif e['kind'] in {'full_audit','selected_audit','final_audit','anomaly_recent16'}:all(True for _ in iter_bundle_file(root,e['file']))
        elif e['kind'] in {'field','field_initial','live_geometry'}:restore(decode(raw),root)
        elif e['kind']=='immutable':decode(raw)
    need(chain==done['chain'] and event_count==done['events'],'MISSING_DUPLICATE_EVENTS')
    need({p.name for p in root.iterdir()}==expected,'PARTIAL_OR_ORPHAN_COMMIT')
    return {'status':'PASS','events':event_count,'files':len(expected)}
