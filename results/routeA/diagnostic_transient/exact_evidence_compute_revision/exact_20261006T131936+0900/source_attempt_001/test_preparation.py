"""Tiny correctness tests only. No target timing or CFD campaign."""
import ast,copy,json,os,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from common import HERE,ROOT,plan,atomic,sha,load,qualification,authority
import fixture,watchdog,pipeline,runner,analysis


class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cfg=plan();cls.topo=fixture.topology();cls.nodes=fixture.graph()
 def launch_child(self,mode,changes=None,injection=None):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);b=copy.deepcopy(self.cfg['stages']['Q1']['budgets']);b.update(changes or {})
   r=watchdog.launch({'command':[sys.executable,'-B',str(HERE/'tiny_child.py'),mode,str(out)],'budget':b,'trial_wall':.25 if mode not in ('normal','memory','files') else 2.,'test_injection':injection},out)
   rows=[json.loads(line) for line in (out/'resource_trace.jsonl').read_text().splitlines()]
   self.assertTrue(rows);self.assertTrue(all('timestamp_monotonic' in row for row in rows));self.assertTrue(r['partial_output_retained'])
   self.assertTrue((out/'process_group.json').exists())
   if (out/'grandchild_pid').exists():self.assertFalse(watchdog.alive(int((out/'grandchild_pid').read_text())))
   if mode=='normal':self.assertEqual((out/'tiny_payload').read_text(),'UNCHANGED_BY_WATCHDOG')
   return r
 def worker(self,request):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);b=copy.deepcopy(self.cfg['stages']['Q1']['budgets']);request.update(tiny=True,classification='TINY_SELF_TEST_ONLY',budget=b);atomic(out,'worker_request.json',request)
   r=watchdog.launch({'command':[sys.executable,'-B',str(HERE/'worker.py'),str(out/'worker_request.json')],'budget':b,'trial_wall':30.},out)
   if r['status']!='COMPLETE':
    logs='\n'.join((out/n).read_text()[-1800:] for n in ('worker.log','backend.log') if (out/n).exists());self.fail(str(r)+logs)
   result=load(out/'worker_result.json')
   if request.get('kind')=='pipeline' and request.get('mode')=='ON':
    backend=load(out/'backend_result.json');self.assertIn('status',backend)
    if request.get('purpose','full')=='full':self.assertEqual(backend['matrix_packets'],701);self.assertEqual(backend['callbacks_including_constructor'],1145)
   return result,r
 def test_authority_and_frozen_plan(self):
  self.assertEqual(authority.verify_authority()['RUNTIME_AUTHORITY_COMPATIBILITY'],'PASS');self.assertFalse(self.cfg['execution_authorized'])
 def test_wrong_authority_hash_fails(self):
  original=authority.sha;target=ROOT/'docs/routeA_diagnostic_transient_contract_v1.5.json'
  with patch.object(authority,'sha',side_effect=lambda p:'0'*64 if Path(p)==target else original(p)):
   with self.assertRaises(ValueError):authority.verify_authority()
 def test_target_shape_only_no_timing(self):
  self.assertEqual(self.topo['counts']['nCells'],25600);self.assertEqual(self.topo['counts']['nInternalFaces'],50880);s=fixture.state(self.topo)
  for k in fixture.DIMS:self.assertEqual(len(s[k]['cells']),25600)
  self.assertEqual(len(s['U']['cells']),25600);self.assertEqual(len(s['phi']['internal']),50880)
  self.assertEqual([len(p['values']) for p in s['phi']['patches']],[160]*4+[0,0])
 def test_wrong_topology_fails(self):
  original=fixture.labels
  with patch.object(fixture,'labels',side_effect=lambda p:original(p)[:-1] if p.name=='neighbour' else original(p)):
   with self.assertRaises(ValueError):fixture.topology()
 def test_callback_matrix_graph_valid(self):self.assertTrue(fixture.validate_graph(self.nodes))
 def test_wrong_callback_and_matrix_graph_fail(self):
  with self.assertRaises(ValueError):fixture.validate_graph(self.nodes[:-1])
  nodes=copy.deepcopy(self.nodes);r=next(r for r in nodes if 'matrix' in r['payload']);r['payload'].pop('matrix')
  with self.assertRaises(ValueError):fixture.validate_graph(nodes)
 def test_normal_child_and_trace(self):self.assertEqual(self.launch_child('normal')['status'],'COMPLETE')
 def test_wall_timeout_and_group_kill(self):
  r=self.launch_child('tree');self.assertEqual(r['STOP_reason'],'STOP_WALL_TIME');self.assertEqual(r['status'],'CENSORED');self.assertFalse(r['sample_valid']);self.assertFalse(r.get('remaining_live_pids'))
 def test_memory_guard_safe_override(self):self.assertEqual(self.launch_child('memory',{'native_RSS_max_bytes':8*2**20})['STOP_reason'],'STOP_MEMORY_GUARD')
 def test_disk_guard_safe_override(self):self.assertEqual(self.launch_child('sleep',{'scratch_bytes':1024})['STOP_reason'],'STOP_STORAGE_GUARD')
 def test_file_count_guard(self):self.assertEqual(self.launch_child('files',{'files_max':10})['STOP_reason'],'STOP_STORAGE_GUARD')
 def test_child_group_escape_fail_closed(self):self.assertEqual(self.launch_child('escape')['STOP_reason'],'STOP_CHILD_PROCESS_ESCAPE')
 def test_supervisor_crash_fail_closed(self):self.assertEqual(self.launch_child('tree',injection='supervisor_crash')['STOP_reason'],'STOP_WATCHDOG_FAILURE')
 def test_path_traversal_symlink_and_production_namespace(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);base=root/'results/routeA/diagnostic_transient/timing_qualification';base.mkdir(parents=True);series=root/'series';series.mkdir();(base/'escape').symlink_to(series)
   for out in (base/'../series/TEST',base/'escape/TEST',series/'TEST'):
    with self.assertRaises(ValueError):qualification.validate_output(root,str(out))
 def test_q1_cfd_and_q3_escalation(self):
  base={'mode':'Q1','output_root':str(ROOT/'results/routeA/diagnostic_transient/timing_qualification/TEST_ONLY'),'authorization':{'scope':'NONCFD_TIMING_QUALIFICATION','task_reference':'UNIT_ONLY','allowed_stages':['Q1']},'plan_sha256':sha(runner.PLAN),'prerequisites':{'Q0_status':'PASS'}}
  for key in ('command','binary','foamRun','solver','case_execution'):
   with self.assertRaises(ValueError):qualification.validate_permission(dict(base,**{key:'FORBIDDEN'}))
  for mode in ('UNKNOWN','Q3'):
   with self.assertRaises(ValueError):qualification.validate_permission(dict(base,mode=mode))
 def test_receipt_immutable_and_hash(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);digest=atomic(root,'receipt.json',{'scope':'TINY_SELF_TEST_ONLY','execution_authorized':False});self.assertEqual(digest,sha(root/'receipt.json'))
   with self.assertRaises(FileExistsError):atomic(root,'receipt.json',{'changed':True})
   self.assertEqual(load(root/'receipt.json')['execution_authorized'],False)
 def test_fit_excludes_censored(self):
  rows=[{'N':n,'kernel_wall_seconds':n*n*1e-6,'status':'COMPLETE'} for n in (100,200,400) for _ in range(3)]+[{'N':800,'kernel_wall_seconds':15.,'status':'CENSORED'}]
  result=analysis.fit(rows);self.assertAlmostEqual(result['p'],2.);self.assertEqual(len(result['censored']),1);self.assertEqual(analysis.fit(rows[:3])['status'],'UNRESOLVED')
 def test_missing_authorization_and_no_actual_receipt(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'denied.json';p.write_text('{"execution_authorized":false}')
   with self.assertRaises(ValueError):runner.verify_authorization(p,'Q1',ROOT/'results/routeA/diagnostic_transient/timing_qualification/TEST_ONLY',{'Q0_status':'PASS'})
 def test_target_pipeline_without_permission_fails_before_launch(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):pipeline.run(Path(d),'ON',self.cfg['stages']['Q1']['budgets'])
 def test_stage_receipt_tampering_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);atomic(root,'stage_receipt.json',{'mode':'Q1'});atomic(root,'stage_receipt_sha256.json',{'sha256':'0'*64})
   with self.assertRaises(ValueError):runner.verify_stage_execution(root/'stage_receipt.json',root/'absent_auth.json')
 def test_native_direct_missing_permission_fails_closed(self):
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTE_A_TIMING_')}
  p=subprocess.run([str(pipeline.BINARY),'-1','OFF','33554432'],input=b'',capture_output=True,env=env,timeout=2)
  self.assertNotEqual(p.returncode,0);self.assertIn(b'STAGE_PERMISSION_REQUIRED',p.stderr)
 def test_native_adapter_has_no_solver_or_time_api(self):
  text=(HERE/'native_adapter.C').read_text();self.assertIn('DiagnosticJson.H',text);self.assertNotIn('setDeltaT(',text);self.assertNotIn('operator++(',text);self.assertNotIn('.solve(',text)
 def test_tiny_full_native_backend_end_to_end(self):
  r,trace=self.worker({'kind':'pipeline','mode':'ON'});self.assertEqual(r['callbacks_recurring'],1144);self.assertEqual(r['matrix_packets'],701);self.assertGreater(trace['peak_RSS_bytes']['combined_simultaneous'],0)
 def test_off_retains_fixture_framework(self):
  r,_=self.worker({'kind':'pipeline','mode':'OFF'});self.assertEqual(r['callbacks_recurring'],1144);self.assertEqual(r['matrix_packets'],701)
 def test_tiny_U03_and_IO(self):
  r,_=self.worker({'kind':'u03','N':4});self.assertEqual(r['windows'],3)
  r,_=self.worker({'kind':'io'});self.assertTrue(r['fsync_latencies']);self.assertFalse(r['operations'][-1]['full9GiB_throughput_qualified'])
 def test_tiny_primitive_and_memory_events(self):
  self.worker({'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':'matrix'})
  for event in self.cfg['memory_events']:
   self.worker({'kind':'pipeline','mode':'ON','purpose':'memory','sample_class':'selected','event':event})

if __name__=='__main__':unittest.main()
