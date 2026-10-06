"""Bounded hash-chained callback receipts. Commit and fsync BEFORE OK ACK.

One sync per callback, never per subspan. A crash may leave an unacknowledged
committed receipt; native ACK progress is the acknowledgement witness. The
observer's own encode/write/sync duration is carried by the next receipt; final
sync has external ACK wall coverage and is explicitly not self-observed.
"""
import hashlib,json,os,time
from common import before_write,need
CAP=64*1024
MAX_BYTES=96*2**20

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
class SpanLedger:
 def __init__(self,out,budget,enabled=True):
  self.out=out;self.budget=budget;self.enabled=enabled;self.prev='0'*64;self.sequence=0;self.bytes=0;self.last_overhead=None;self.file=None
  if enabled:
   before_write(out,budget,4096,1);self.file=(out/'backend_span_ledger.jsonl').open('xb');self.file.flush();os.fsync(self.file.fileno());fd=os.open(out,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 def commit(self,spans,packet,count,matrices,bytes_in):
  if not self.enabled:return
  begin=time.perf_counter();need(not spans.stack,'STOP_LEDGER_OPEN_SPAN')
  # Snapshot this callback only, preserving exact parent paths and counters.
  nodes=spans.nodes;paths={};groups={}
  for n in nodes:
   parent=paths.get(n['parent_id'],());path=parent+(n['name'],);paths[n['id']]=path
   key=(n['payload_class'],path);row=groups.setdefault(key,{'path':list(path),'payload_class':n['payload_class'],'count':0,'inclusive_seconds':0.,'exclusive_seconds':0.,'start':n['start'],'end':n['start']})
   row['count']+=1
   for k in ('inclusive_seconds','exclusive_seconds'):row[k]+=n[k]
   row['end']=n['start']+n['inclusive_seconds']
  r={'schema':'durable_backend_spans/1','sequence':self.sequence,'previous_hash':self.prev,'backend_pid':os.getpid(),'packet_sequence':packet.get('sequence') if packet else None,'payload_sha256':packet.get('payload_sha256') if packet else None,'callback_count':count,'matrix_count':matrices,'bytes_received':bytes_in,'span_tree':list(groups.values()),'observer_previous_commit_seconds':self.last_overhead,'observer_coverage':'previous commit only; current sync covered externally by send-to-ACK wall','ACK_semantics':'this record fsynced before OK; ACK witness is native progress'}
  digest=hashlib.sha256(canonical(r)).hexdigest();raw=canonical(dict(r,record_hash=digest))+b'\n'
  need(len(raw)<=CAP and self.bytes+len(raw)<=MAX_BYTES,'STOP_LEDGER_BOUND');before_write(self.out,self.budget,len(raw),0)
  self.file.write(raw);self.file.flush();os.fsync(self.file.fileno());self.prev=digest;self.sequence+=1;self.bytes+=len(raw);self.last_overhead=time.perf_counter()-begin
 def close(self):
  if self.file:self.file.close()
def recover(path,allow_partial=True):
 rows=[];prev='0'*64;tail=False
 with path.open('rb') as f:
  while True:
   raw=f.readline(CAP+1)
   if not raw:break
   need(len(raw)<=CAP,'STOP_LEDGER_BOUND')
   if not raw.endswith(b'\n'):
    need(allow_partial,'STOP_LEDGER_TRUNCATED');tail=True;break
   r=json.loads(raw);digest=r.pop('record_hash');need(r['previous_hash']==prev and r['sequence']==len(rows) and hashlib.sha256(canonical(r)).hexdigest()==digest,'STOP_LEDGER_HASH_CHAIN');rows.append(dict(r,record_hash=digest));prev=digest
 return rows,tail
