"""Additional fixed-path permission and actual backend SIGKILL validation."""
import hashlib,json,os,socket,subprocess,sys,time,unittest
from pathlib import Path
from common import HERE,ROOT,REVISION_ROOT,atomic,plan,load,sha
from persistence import iter_bundle_file
from durable import recover
class Additional(unittest.TestCase):
 def test_actual_backend_SIGKILL_after_ACK(self):
  out=REVISION_ROOT/'actual_backend_kill_tiny_cycle2';out.mkdir();budget=plan()['stages']['Q1']['budgets'];atomic(out,'budget.json',budget)
  packet=next(iter_bundle_file(REVISION_ROOT/'tiny_equivalence_cycle2/new_on/runtime','full_2.bin'));packet['sequence']=1;raw=(json.dumps(packet,separators=(',',':'))+'\n').encode();a,b=socket.socketpair();env=dict(os.environ,ROUTE_A_TIMING_SELF_TEST='TINY_SELF_TEST_ONLY');log=(out/'backend.log').open('xb')
  p=subprocess.Popen([sys.executable,'-B',str(HERE/'backend.py'),str(b.fileno()),str(out),str(out/'budget.json'),'primitive','NONE','TINY'],pass_fds=(b.fileno(),),stdout=log,stderr=log,env=env);b.close();a.settimeout(10)
  try:
   a.sendall(raw);ack=a.recv(16);self.assertEqual(ack,b'OK\n');p.kill();p.wait(timeout=2);rows,tail=recover(out/'backend_span_ledger.jsonl');self.assertFalse(tail);self.assertEqual(rows[-1]['callback_count'],1);self.assertEqual(rows[-1]['payload_sha256'],packet['payload_sha256']);names={row['path'][-1] for row in rows[-1]['span_tree']};self.assertTrue({'backend_receive','JSON_decode','canonicalization','replay','writer_accept','ACK_preparation'}<=names);atomic(out,'validation.json',{'status':'PASS','ACK':ack.decode(),'exit':p.returncode,'durable_callbacks':len(rows),'span_names':sorted(names),'target_size':False})
  finally:
   if p.poll() is None:p.kill();p.wait()
   a.close();log.close()
 def test_permission_rejects_CFD_and_wrong_Q2_prior(self):
  import runner
  with self.assertRaises((ValueError,OSError)):runner.verify_authorization(Path('/absent'),'Q3',ROOT,{'Q0_status':'PASS'})
  # Each wrapper and native fixed helper must independently validate. Verify
  # direct native execution cannot launch even if it receives no packets.
  from pipeline import BINARY
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTE_A_TIMING_')};p=subprocess.run([str(BINARY),'-1','OFF',str(32*2**20)],env=env,capture_output=True,timeout=3);self.assertNotEqual(p.returncode,0);self.assertIn(b'STAGE_PERMISSION_REQUIRED',p.stderr)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Additional));atomic(REVISION_ROOT,'additional_validation_cycle2.json',{'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors)});sys.exit(not r.wasSuccessful())
