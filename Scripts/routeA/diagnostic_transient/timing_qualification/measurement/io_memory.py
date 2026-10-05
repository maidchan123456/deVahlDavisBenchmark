"""Bounded real publication/fsync and isolated retention events; no production lifecycle."""
import hashlib,json,os,re,stat,time
from common import atomic,before_write,plan,need
from fixture import state,tiny_topology
from persistence import Writer,receipt_bytes
from packed import encode
from log_rotation import RawLog


def operation_size(cfg,keyword):
 for text in cfg['IO_design']['operations']:
  if keyword in text:
   m=re.search(r'(\d+)MiB',text);need(m is not None,'STOP_IO_SIZE_AUTHORITY');return int(m[1])*2**20
 raise ValueError('STOP_IO_OPERATION_UNREGISTERED')

def io_trial(out,budget,tiny=False):
 cfg=plan();s=[operation_size(cfg,k) for k in ('raw log','field-sized','selected-bundle')]
 if tiny:s=[128,256,512]
 root=out/'io';root.mkdir();writer=Writer(root);timings=[];original=os.fsync
 def fsync(fd):
  t=time.perf_counter();result=original(fd);timings.append({'kind':'directory' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'file','seconds':time.perf_counter()-t});return result
 os.fsync=fsync
 rows=[]
 try:
  # Published encoded chunks use the frozen writer commit/manifest operation;
  # payloads here are resource-only size fixtures, not scientific field evidence.
  for name,size,kind in [('receipt_chunk.bin',s[1],'receipts_size_fixture'),('primary_chunk.bin',s[1],'primary_size_fixture'),('field_size.bin',s[1],'field_size_fixture'),('bundle_size.bin',s[2],'selected_bundle_size_fixture')]:
   before_write(out,budget,size+8192,3);raw=b'\x5a'*size;begin=time.perf_counter();writer.publish(name,raw,kind);write=time.perf_counter()-begin
   t=time.perf_counter();h=hashlib.sha256()
   with (root/name).open('rb') as f:
    for block in iter(lambda:f.read(2**20),b''):h.update(block)
   need(h.hexdigest()==hashlib.sha256(raw).hexdigest(),'STOP_IO_READBACK_HASH')
   rows.append({'operation':name,'logical_bytes':size,'publish_seconds':write,'effective_MB_s':size/write/1e6,'hash_read_seconds':time.perf_counter()-t,'cache':'NEW_FILE_COLD_UNCONTROLLED_WRITE_WARM_READ','full9GiB_throughput_qualified':False})
  class PublishLog:
   def publish(self,name,raw,kind):before_write(out,budget,len(raw)+8192,3);writer.publish(name,raw,kind)
  log=RawLog(PublishLog(),chunk_bytes=s[0]);log.write(b'\x5a'*s[0]);log.flush()
  prefix=512 if tiny else cfg['IO_design']['audit_prefix_per_trial_max_bytes'];chunk=128 if tiny else cfg['Q1_design']['packet_limit_bytes'];path=root/'audit_prefix.scratch';h=hashlib.sha256();begin=time.perf_counter()
  with path.open('xb') as f:
   for start in range(0,prefix,chunk):
    raw=b'\x5a'*min(chunk,prefix-start);before_write(out,budget,len(raw),0);f.write(raw);h.update(raw)
   f.flush();os.fsync(f.fileno())
  with path.open('rb') as f:
   readhash=hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else None
  if readhash is None:
   check=hashlib.sha256()
   with path.open('rb') as f:
    for raw in iter(lambda:f.read(2**20),b''):check.update(raw)
   readhash=check.hexdigest()
  need(readhash==h.hexdigest(),'STOP_STREAM_READBACK')
  rows.append({'operation':'raw_audit_stream_prefix','logical_bytes':prefix,'publish_seconds':time.perf_counter()-begin,'full9GiB_throughput_qualified':False,'cache':'UNCONTROLLED'})
  result={'status':'COMPLETE','operations':rows,'fsync_latencies':timings,'logical_bytes':writer.written_bytes+prefix,'physical_IO_source':'watchdog /proc io, not logical byte count','classification':'TINY_SELF_TEST_ONLY' if tiny else 'RESOURCE_QUALIFICATION_FIXTURE_ONLY'}
  atomic(out,'worker_result.json',result,budget);return result
 finally:os.fsync=original

def memory_event(out,budget,event,packet,tiny=False,packed_records=None,live=None):
 cfg=plan();need(event in cfg['memory_events'],'STOP_UNREGISTERED_MEMORY_EVENT');root=out/'memory';root.mkdir();writer=Writer(root);raw=encode(packet);values=[]
 # Native packet remains resident while the receiver exercises the actual codec
 # and writer methods; pipeline supervisor tracks native/backend concurrently.
 if event=='rolling buffer full including join/transient copy':
  values=packed_records or [raw]*16;writer.ring.extend(values);writer.ring_bytes=sum(map(len,values));joined=b''.join(values)
 elif event=='selected512MiB bundle':
  values=packed_records or [raw];from persistence import BUNDLE_CAP
  need(sum(map(len,values))<=BUNDLE_CAP,'STOP_BUNDLE_CAP');before_write(out,budget,sum(map(len,values))+8192,3);writer.audit(values,'selected_fixture.bin','selected_audit')
 elif event=='field16MiB snapshot':
  before_write(out,budget,len(raw)+8192,3);writer.snapshot(packet['payload']['native_state_epoch'],'field_fixture.bin')
 elif event=='full raw audit preparation as streaming path':
  import struct
  values=packed_records or [raw];writer.full_spool=(root/'full_audit.scratch').open('xb');writer.full_spool.write(b'RAB13\0')
  for chunk in values:before_write(out,budget,len(chunk)+8,0);writer.full_spool.write(struct.pack('<Q',len(chunk))+chunk)
  writer.full_spool.flush();os.fsync(writer.full_spool.fileno());writer.full_spool.close();writer.full_spool=None;writer.publish_spool('audit_fixture.bin','full_audit')
 elif event=='U01 last5 states':
  values=list(live.outer) if live else [];need(len(values)==5,'STOP_U01_LAST5_SHAPE')
  from fixture import graph
  live.outer_count=cfg['frozen_switches']['nOuterCorrectors']
  live.linear=[dict(x,initial=0.,final=0.,iterations=0) for r in graph() for x in r['live_binding'].get('linear',[])];live.outer_certificate()
 elif event=='U03 history evaluation':
  from worker import u03
  return u03(out,budget,4 if tiny else cfg['Q2_U03']['node_counts'][0],tiny,result_name='memory_U03_result.json')
 else:values=[raw]
 atomic(out,'memory_event_result.json',{'status':'COMPLETE','event':event,'packed_bytes':len(raw),'retained_copy_bytes':sum(len(v) if isinstance(v,bytes) else len(encode(list(v) if isinstance(v,tuple) else v)) for v in values),'event_size_scope':'ACTUAL_TARGET_PACKET_SIZE_NOT_THEORETICAL_MAX_CAP','full_9GiB_stream_coverage':False,'classification':'TINY_SELF_TEST_ONLY' if tiny else 'RESOURCE_QUALIFICATION_FIXTURE_ONLY'},budget)
 return values
