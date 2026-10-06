"""Revision-only validation. Four-cell fixtures; never target authorization."""
import copy,gzip,hashlib,io,json,os,random,socket,subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path
from common import ROOT,HERE,REVISION_ROOT,plan,load,sha,atomic
from transport import PacketStream
from durable import SpanLedger,recover,canonical
from spans import Span
from trace_codec import Trace,iter_trace
from cpu_attribution import sample,interval
import pipeline,watchdog

class Revision(unittest.TestCase):
 def receive(self,raw,segments,legacy,limit=512):
  a,b=socket.socketpair();s=PacketStream(a,limit,legacy);result=[]
  def send():
   try:
    for block in segments:b.sendall(block)
   except BrokenPipeError:return
   try:b.shutdown(socket.SHUT_WR)
   except OSError:pass
  t=threading.Thread(target=send);t.start()
  try:
   while True:
    line=s.readline()
    if not line:break
    if not line.endswith(b'\n'):result.append(('STOP_TRANSPORT_TRUNCATED',line));break
    try:result.append(('JSON',json.loads(line)))
    except ValueError:result.append(('JSON_ERROR',line));break
  finally:s.close();a.close();t.join();b.close()
  return result
 def test_framing_exact_equivalence(self):
  rng=random.Random(2306)
  cases=[b'{"x":1}\n',b'{"x":1}\n{"x":2}\n',b'',b'{"x":1}',b'\n',b'x'*513+b'\n',b'"'+b'a'*510+b'"\n',b'{}\n{}\n{}\n']
  for raw in cases:
   random_segments=[];pos=0
   while pos<len(raw):n=rng.randint(1,11);random_segments.append(raw[pos:pos+n]);pos+=n
   for segments in ([raw] if raw else [],[raw[i:i+1] for i in range(len(raw))],random_segments,[raw[:-1],raw[-1:]]):
    with self.subTest(raw=raw[:20],segments=len(segments)):self.assertEqual(self.receive(raw,segments,True),self.receive(raw,segments,False))
 def test_32MiB_bound(self):
  # Prove buffer calls are bounded independently of total line size, using a
  # deterministic RawIOBase source without allocating an oversized socket line.
  from transport import io as transport_io
  class Source(io.RawIOBase):
   def readable(self):return True
   def readinto(self,b):self.maximum=max(getattr(self,'maximum',0),len(b));n=min(len(b),self.left);b[:n]=b'x'*n;self.left-=n;return n
  src=Source();src.left=32*2**20+10;reader=transport_io.BufferedReader(src,64*1024);line=reader.readline(32*2**20+1);self.assertEqual(len(line),32*2**20+1);self.assertLessEqual(src.maximum,64*1024)
 def ledger(self,out,enabled=True):
  ledger=SpanLedger(out,plan()['stages']['Q1']['budgets'],enabled);spans=Span(compact=True)
  with spans.scope('receive'):
   with spans.scope('decode'):pass
  ledger.commit(spans,{'sequence':1,'payload_sha256':'a'*64},1,0,8);ledger.close()
 def test_ledger_chain_corruption_and_partial(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);self.ledger(out);p=out/'backend_span_ledger.jsonl';r,tail=recover(p);self.assertEqual(r[0]['callback_count'],1);self.assertFalse(tail)
   with p.open('ab') as f:f.write(b'{"partial":')
   r,tail=recover(p);self.assertEqual(len(r),1);self.assertTrue(tail)
   with self.assertRaises(ValueError):recover(p,False)
   raw=p.read_bytes().replace(b'"callback_count":1',b'"callback_count":2');p.write_bytes(raw)
   with self.assertRaises(ValueError):recover(p)
 def test_ledger_sigkill_after_ACK(self):
  with tempfile.TemporaryDirectory() as d:
   code="from pathlib import Path; from durable import SpanLedger; from spans import Span; from common import plan; import time; s=Span(compact=True); l=SpanLedger(Path(__import__('sys').argv[1]),plan()['stages']['Q1']['budgets']); exec('with s.scope(\"receive\"):\\n pass'); l.commit(s,{'sequence':1,'payload_sha256':'a'*64},1,0,8); print('OK',flush=True); time.sleep(20)"
   p=subprocess.Popen([sys.executable,'-B','-c',code,d],cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(p.stdout.readline(),b'OK\n');p.kill();p.communicate(timeout=3);rows,tail=recover(Path(d)/'backend_span_ledger.jsonl');self.assertEqual(len(rows),1);self.assertFalse(tail);self.assertEqual(rows[0]['span_tree'][0]['path'],['receive'])
 def test_trace_lossless_and_accounting(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);p=out/'trace.jsonl.gz';trace=Trace(p,out,plan()['stages']['Q1']['budgets']);rows=[{'RSS':i,'VmSize':i+10,'MemAvailable':100-i,'disk_free':200-i,'file_count':i,'load':i/3,'IO':{'wchar':i*9},'STOP':None if i<99 else 'STOP_WALL_TIME'} for i in range(100)];raw=''.join(json.dumps(r)+'\n' for r in rows)
   for line in raw.splitlines(keepends=True):trace.write(line)
   account=trace.accounting();trace.close();self.assertEqual(gzip.decompress(p.read_bytes()),raw.encode());self.assertEqual(list(iter_trace(p)),rows);self.assertEqual(account['stored_bytes'],p.stat().st_size);self.assertEqual(account['raw_SHA256'],hashlib.sha256(raw.encode()).hexdigest())
   p.write_bytes(p.read_bytes()[:-3]);
   with self.assertRaises((EOFError,OSError)):list(iter_trace(p))
 def test_CPU_late_child_and_reaped_short_lived(self):
  def p(pid,u,child=0):return {'pid':pid,'starttime_ticks':pid*10,'CPU_user_ticks':u,'CPU_system_ticks':0,'CPU_children_user_ticks':child,'CPU_children_system_ticks':0}
  old=sample({1:p(1,10)},[p(9,2)],1);old['boottime']=.1
  late=sample({1:p(1,11),2:p(2,7)},[p(9,3)],1);r=interval(old,late,100,20);self.assertEqual(r['own_ticks'],9);self.assertEqual(r['other_fraction_upper'],.11)
  reaped=sample({1:p(1,12,7)},[p(9,4)],1);r=interval(late,reaped,100,20);self.assertEqual(r['own_ticks'],2);self.assertEqual(r['other_fraction_upper'],.18)
  self.assertFalse(r['uncertainty']);self.assertEqual(interval(old,reaped,100,20)['own_ticks'],11)
 def test_CPU_controlled_tree(self):
  # Root remains live and waits for a short CPU child. Poll before/after proves
  # final child ticks survive in cutime; an unrelated CPU process is excluded.
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);script="import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; end=time.process_time()+.16\\nwhile time.process_time()<end: pass']); p.wait(); print('reaped',flush=True); time.sleep(.3)"
   child=subprocess.Popen([sys.executable,'-c',script],stdout=subprocess.PIPE)
   external=subprocess.Popen([sys.executable,'-c','import time; end=time.process_time()+.2\nwhile time.process_time()<end: pass'])
   try:
    child.stdout.readline();tree=watchdog.descendants(child.pid);self.assertNotIn(external.pid,tree);r=tree[child.pid];self.assertGreater(r['CPU_children_user_ticks']+r['CPU_children_system_ticks'],0);self.assertEqual(sample(tree,[],child.pid)['subtree_ticks'],r['CPU_user_ticks']+r['CPU_system_ticks']+r['CPU_children_user_ticks']+r['CPU_children_system_ticks'])
   finally:child.wait();external.wait()
 def worker(self,out,receiver,observer,purpose='full'):
  req={'kind':'pipeline','mode':'ON','purpose':purpose,'sample_class':'matrix','tiny':True,'classification':'TINY_SELF_TEST_ONLY','budget':plan()['stages']['Q1']['budgets']};atomic(out,'worker_request.json',req)
  env=dict(os.environ,ROUTE_A_RECEIVER=receiver,ROUTE_A_OBSERVER=observer)
  p=subprocess.run([sys.executable,'-B',str(HERE/'worker.py'),str(out/'worker_request.json')],env=env,capture_output=True,timeout=35)
  self.assertEqual(p.returncode,0,p.stderr.decode()+(out/'backend.log').read_text())
  backend=load(out/'backend_result.json');science={k:backend[k] for k in ('status','callbacks_including_constructor','matrix_packets','bytes_IPC_received','evaluator_summary','rows','writer_bytes','writer_fsyncs','U01_primary_steps','schedule')}
  evidence={str(p.relative_to(out/'runtime')):sha(p) for p in (out/'runtime').rglob('*') if p.is_file()};return science,evidence
 def test_full_backend_receiver_observer_evidence_equivalence(self):
  base=REVISION_ROOT/'tiny_equivalence_cycle2';base.mkdir(exist_ok=False);results=[]
  for name,receiver,observer in [('old','LEGACY','OFF'),('new_off','BUFFERED','OFF'),('new_on','BUFFERED','ON')]:
   out=base/name;out.mkdir();results.append(self.worker(out,receiver,observer))
  self.assertEqual(results[0],results[1]);self.assertEqual(results[1],results[2]);rows,tail=recover(base/'new_on/backend_span_ledger.jsonl');self.assertFalse(tail);self.assertEqual(rows[-1]['callback_count'],1145);self.assertEqual(rows[-1]['matrix_count'],701)
  progress=[json.loads(x) for x in (base/'new_on/native_progress.jsonl').read_text().splitlines() if x.startswith('{')];self.assertEqual([x['callbacks_including_constructor'] for x in progress if 'callbacks_including_constructor' in x],list(range(1,1146)))
 def test_new_watchdog_timeout_trace(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);r=watchdog.launch({'command':[sys.executable,'-B',str(HERE/'tiny_child.py'),'tree',str(out)],'budget':plan()['stages']['Q1']['budgets'],'trial_wall':.3},out);self.assertEqual(r['STOP_reason'],'STOP_WALL_TIME');self.assertFalse(r.get('remaining_live_pids'));rows=list(iter_trace(out/'resource_trace.jsonl.gz'));self.assertEqual(len(rows),r['trace_accounting']['samples']);self.assertTrue(all('cpu_attribution' in x for x in rows))
if __name__=='__main__':
 begin=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Revision);result=unittest.TextTestRunner(verbosity=2).run(suite);atomic(REVISION_ROOT,'revision_validation_cycle2.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'wall_seconds':time.monotonic()-begin,'classification':'TINY_ONLY','CFD_executed':False});sys.exit(not result.wasSuccessful())
