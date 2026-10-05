"""Append-only bounded content archive. Packing changes representation, never evidence.

Trial workspace bytes are migrated only after every artifact and the trial index
are fsynced and readback verified. Duplicate references retain exact logical
bytes; measured writes already happened. An uncommitted tail is never rewritten.
"""
import hashlib,json,os,struct
from pathlib import Path
from common import need,sha,before_write,atomic,load
from persistence import AUDIT_CAP,STAGE_CAP

CHUNK_BYTES=64*2**20 # the frozen receipt chunk bound, distinct from IPC stage cap
STOP_FILES=8
STOP_BYTES=16*2**20
WORK_FILES=48
CONTROL_FILES=24

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fsync_dir(path):
 fd=os.open(path,os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)

class Archive:
 def __init__(self,root,budget,chunk_bytes=CHUNK_BYTES):
  self.root=Path(root);self.budget=budget;self.cap=chunk_bytes;self.objects={};self.trials=[];self.previous='0'*64;self.chunk=None;self.record_sources={};self.bundle_header=None
  self.index=self.root/'trial_index.jsonl';self.root.mkdir(exist_ok=True)
  if self.index.exists():
   records,tail=recover(self.root)
   need(not tail,'STOP_ARCHIVE_PARTIAL_TAIL_NO_RESUME')
   for r in records:
    self.trials.append(r['trial_id']);self.previous=r['record_hash']
    for a in r['artifacts']:self.objects[a['sha256']]=a['segments']
  # Archive instances may read completed history; append after a sealed stage is forbidden.
  need(not (self.root.parent/'stage_result.json').exists(),'STOP_ARCHIVE_STAGE_SEALED')
 def index_audit(self,path):
  with path.open('rb') as f:
   if f.read(6)!=b'RAB13\0':return
   self.bundle_header={'file':path.name,'offset':0,'length':6}
   while True:
    offset=f.tell();header=f.read(8)
    if not header or len(header)<8:break
    length=struct.unpack('<Q',header)[0];need(length<=STAGE_CAP,'STOP_AUDIT_RECORD_BOUND')
    raw=f.read(length)
    if len(raw)!=length:break # partial STOP artifact; complete prefix remains addressable
    self.record_sources[hashlib.sha256(header+raw).hexdigest()]={'file':path.name,'offset':offset,'length':8+length}
 def bundle_view(self,path):
  if self.bundle_header is None:return None
  refs=[self.bundle_header]
  with path.open('rb') as f:
   if f.read(6)!=b'RAB13\0':return None
   while True:
    header=f.read(8)
    if not header:break
    if len(header)!=8:return None
    length=struct.unpack('<Q',header)[0]
    if length>STAGE_CAP:return None
    raw=f.read(length)
    if len(raw)!=length:return None
    key=hashlib.sha256(header+raw).hexdigest()
    if key not in self.record_sources:return None
    refs.append(self.record_sources[key])
  return refs
 def put_file(self,path,adopt=False,required_view=False):
  path=Path(path);digest=sha(path);size=path.stat().st_size
  if digest in self.objects:return {'bytes':size,'sha256':digest,'segments':self.objects[digest],'content_shared':True}
  segments=[]
  view=self.bundle_view(path) if path.name=='final_bundle.bin' else None
  need(not required_view or view is not None,'STOP_REQUIRED_STARTUP_SOURCE_SHARING')
  if view is not None:
   obj={'bytes':size,'sha256':digest,'segments':view,'content_shared':True};verify_artifact(self.root,obj);self.objects[digest]=view;return obj
  if adopt:
   need(size<=AUDIT_CAP,'STOP_ARCHIVE_BLOB_CAP');name='audit_'+digest+'.bin';dest=self.root/name
   need(not dest.exists(),'STOP_ARCHIVE_BLOB_COLLISION')
   # Atomic representation migration: same inode, no extra raw-audit copy or omitted write.
   os.rename(path,dest);fsync_dir(self.root);self.index_audit(dest);segments=[{'file':name,'offset':0,'length':size}]
  else:
   with path.open('rb') as source:
    while True:
     if self.chunk is None or not self.chunk.exists() or self.chunk.stat().st_size>=self.cap:
      name='data_'+str(len(list(self.root.glob('data_*.bin')))).zfill(4)+'.bin';self.chunk=self.root/name
      need(not self.chunk.exists(),'STOP_ARCHIVE_CHUNK_COLLISION')
     offset=self.chunk.stat().st_size if self.chunk.exists() else 0
     raw=source.read(min(2**20,self.cap-offset))
     if not raw:break
     before_write(self.root,self.budget,len(raw),0 if self.chunk.exists() else 1)
     with self.chunk.open('ab') as f:f.write(raw);f.flush();os.fsync(f.fileno())
     if segments and segments[-1]['file']==self.chunk.name and segments[-1]['offset']+segments[-1]['length']==offset:segments[-1]['length']+=len(raw)
     else:segments.append({'file':self.chunk.name,'offset':offset,'length':len(raw)})
   fsync_dir(self.root)
  obj={'bytes':size,'sha256':digest,'segments':segments,'content_shared':False};verify_artifact(self.root,obj);self.objects[digest]=segments;return obj
 def commit(self,trial_id,ordinal,workspace,metadata):
  need(trial_id not in self.trials,'STOP_DUPLICATE_TRIAL_ID')
  need(ordinal==len(self.trials),'STOP_TRIAL_ORDER')
  need(not (self.root.parent/'stage_result.json').exists(),'STOP_ARCHIVE_STAGE_SEALED')
  workspace=Path(workspace);artifacts=[]
  for path in sorted(workspace.rglob('*'),key=lambda p:(not str(p.relative_to(workspace)).startswith('runtime/full_'),str(p))):
   need(not path.is_symlink(),'STOP_ARCHIVE_SYMLINK')
   if path.is_file():
    name=str(path.relative_to(workspace));obj=self.put_file(path,adopt=name.startswith('runtime/full_'),required_view=metadata.get('request',{}).get('context_kind')=='STARTUP_ONE_TIME' and name=='runtime/final_bundle.bin');artifacts.append(dict(obj,path=name))
  record={'schema':'timing_trial_archive/2','trial_id':trial_id,'ordinal':ordinal,'metadata':metadata,'artifacts':artifacts,'previous_record_hash':self.previous}
  record['record_hash']=hashlib.sha256(canonical(record)).hexdigest();raw=canonical(record)+b'\n'
  need(len(raw)<=256*1024,'STOP_INDEX_RECORD_BOUND')
  before_write(self.root,self.budget,len(raw),0 if self.index.exists() else 1)
  with self.index.open('ab') as f:offset=f.tell();f.write(raw);f.flush();os.fsync(f.fileno())
  fsync_dir(self.root);read=read_trial(self.root,trial_id);need(read==record,'STOP_ARCHIVE_COMMIT_READBACK')
  self.previous=record['record_hash'];self.trials.append(trial_id)
  # Only verified duplicate workspace representations are retired. Every logical
  # artifact remains readable through this immutable committed index. No purge.
  for p in sorted(workspace.rglob('*'),reverse=True):
   if p.is_file():p.unlink()
   elif p.is_dir():p.rmdir()
  workspace.rmdir()
  return {'trial_id':trial_id,'index_offset':offset,'index_length':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'record_hash':record['record_hash'],'status':metadata['status'],'artifacts':len(artifacts)}

def recover(root,verify=True):
 root=Path(root);index=root/'trial_index.jsonl';records=[];tail=False;previous='0'*64
 if not index.exists():return records,False
 with index.open('rb') as f:
  for raw in f:
   if not raw.endswith(b'\n'):tail=True;break
   try:r=json.loads(raw)
   except (ValueError,UnicodeError):tail=True;break
   saved=r['record_hash'];copy=dict(r);copy.pop('record_hash')
   need(hashlib.sha256(canonical(copy)).hexdigest()==saved and r['previous_record_hash']==previous,'STOP_ARCHIVE_HASH_CHAIN')
   need(r['ordinal']==len(records) and all(x['trial_id']!=r['trial_id'] for x in records),'STOP_ARCHIVE_INDEX_ORDER')
   if verify:
    for a in r['artifacts']:verify_artifact(root,a)
   previous=saved;records.append(r)
 return records,tail

def artifact_blocks(root,artifact):
 for s in artifact['segments']:
  path=Path(root)/s['file'];need(path.name==s['file'] and not path.is_symlink(),'STOP_ARCHIVE_SEGMENT_PATH')
  with path.open('rb') as f:
   f.seek(s['offset']);left=s['length']
   while left:
    raw=f.read(min(left,2**20));need(raw,'STOP_ARCHIVE_TRUNCATED_COMMITTED_DATA');left-=len(raw);yield raw

def verify_artifact(root,artifact):
 h=hashlib.sha256();size=0
 for raw in artifact_blocks(root,artifact):h.update(raw);size+=len(raw)
 need(size==artifact['bytes'] and h.hexdigest()==artifact['sha256'],'STOP_ARCHIVE_ARTIFACT_HASH')

def read_trial(root,trial_id):
 records,_=recover(root,verify=False)
 for r in records:
  if r['trial_id']==trial_id:
   for a in r['artifacts']:verify_artifact(root,a)
   return r
 raise ValueError('STOP_TRIAL_NOT_COMMITTED')

def layout(cfg,stage):
 b=cfg['stages'][stage]['budgets'];retained=b['scratch_bytes']
 if stage=='Q1':
  from schedule import accounting
  retained=accounting(cfg)['maximum_retained_bytes']-AUDIT_CAP
 chunks=(retained+CHUNK_BYTES-1)//CHUNK_BYTES
 # Largest blob remains a separately adopted bounded startup audit; data chunk
 # count below is conservative even with this blob's bytes charged to scratch.
 blobs=1 if stage=='Q1' else 2 # complete streaming event plus final partial STOP
 maximum=chunks+1+blobs+WORK_FILES+CONTROL_FILES+STOP_FILES+2
 return {'stage':stage,'worst_case_physical_files':maximum,'reserved_stop_files':STOP_FILES,'reserved_stop_bytes':STOP_BYTES,'physical_chunks_max':chunks,'adopted_event_blobs_max':blobs,'active_workspace_files_max':WORK_FILES,'stage_control_files_max':CONTROL_FILES,'index_files':1,'partial_publish_files':2,'registered_files_limit':b['files_max'],'logical_trials':7 if stage=='Q1' else len(cfg['Q2_U03']['node_counts'])*cfg['Q2_U03']['repeats']+6*cfg['Q2_pipeline']['repeats']+8*cfg['repeatability']['minimum_repeats']+cfg['repeatability']['minimum_repeats'],'no_purge':True,'representation_migration_after_verified_commit':True}
