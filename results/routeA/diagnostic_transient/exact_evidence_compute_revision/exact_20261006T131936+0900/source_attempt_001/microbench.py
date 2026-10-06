"""Finite receiver and observer microbenchmarks, not production qualification."""
import copy,hashlib,json,os,socket,statistics,sys,threading,time
from pathlib import Path
from common import REVISION_ROOT,plan,atomic,sha,load,HERE,CONTRACT
from transport import PacketStream
from durable import SpanLedger,recover
from spans import Span

def receiver(raw,legacy):
 a,b=socket.socketpair();stream=PacketStream(a,32*2**20,legacy)
 t=threading.Thread(target=lambda:(b.sendall(raw),b.shutdown(socket.SHUT_WR)));begin=time.perf_counter();t.start();got=stream.readline();end=time.perf_counter();t.join();stream.close();a.close();b.close();assert got==raw;return end-begin

def main():
 out=REVISION_ROOT/'microbench_001';out.mkdir(exist_ok=False)
 atomic(out,'receipt.json',{'schema':'bounded_nonCFD_microbenchmark/1','task':'NONCFD_DIAGNOSTIC_COMPUTE_REVISION_TEST','master_prompt_SHA256':load(REVISION_ROOT/'master_scope.json')['master_prompt_sha256'],'payloads_bytes':[4096,512*1024],'repeats':3,'finite_total_wall_seconds':45,'receiver_limit_bytes':32*2**20,'observer_cases':[32,512*1024],'max_files':32,'scratch_bytes':16*2**20,'CFD_authorized':False,'claim':'synthetic isolated operations only'})
 deadline=time.monotonic()+45;results=[]
 for size in (4096,512*1024):
  raw=b'"'+b'a'*(size-3)+b'"\n'
  for repeat in range(3):
   for legacy in (True,False):
    assert time.monotonic()<deadline;wall=receiver(raw,legacy);results.append({'kind':'receiver','bytes':len(raw),'legacy':legacy,'repeat':repeat,'wall_seconds':wall,'content_sha256':hashlib.sha256(raw).hexdigest()})
 for size in (32,512*1024):
  value={'payload':'x'*size};digests=[]
  for repeat in range(3):
   for enabled in (False,True):
    assert time.monotonic()<deadline;work=out/f'observer_{size}_{repeat}_{enabled}';work.mkdir();spans=Span(compact=True);ledger=SpanLedger(work,plan()['stages']['Q1']['budgets'],enabled);start=time.perf_counter()
    with spans.scope('canonicalization'):
     raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(raw).hexdigest()
    with spans.scope('ACK_preparation'):pass
    ledger.commit(spans,{'sequence':1,'payload_sha256':digest},1,0,len(raw));wall=time.perf_counter()-start;ledger.close();digests.append(digest);results.append({'kind':'observer','bytes':size,'enabled':enabled,'repeat':repeat,'wall_seconds':wall,'observer_commit_seconds':ledger.last_overhead,'payload_sha256':digest,'note':'isolated ledger incremental cost; not full evaluator wall'})
  assert len(set(digests))==1
 summary=[]
 for size in (4096,512*1024):
  old=[r['wall_seconds'] for r in results if r['kind']=='receiver' and r['bytes']==size and r['legacy']];new=[r['wall_seconds'] for r in results if r['kind']=='receiver' and r['bytes']==size and not r['legacy']];summary.append({'bytes':size,'old_median_seconds':statistics.median(old),'new_median_seconds':statistics.median(new),'isolated_receiver_ratio':statistics.median(old)/statistics.median(new)})
 atomic(out,'result.json',{'status':'PASS','repeats':3,'rows':results,'receiver_summary':summary,'production_speedup_claim':False,'total_wall_seconds':45-(deadline-time.monotonic())});print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
