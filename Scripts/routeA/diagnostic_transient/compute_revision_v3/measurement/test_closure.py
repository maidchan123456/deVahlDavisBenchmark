"""B1-B4 closure tests: tiny only; no target measurement authorization."""
import copy,hashlib,json,os,random,struct,sys,tempfile,unittest
from pathlib import Path
from common import HERE,PREP,ROOT,plan,load,sha,atomic,footprint,before_write
from archive import Archive,recover,read_trial,artifact_blocks,layout
from schedule import context,accounting,recurring_time
from spans import Span
from fixture import compact_receipt,tiny_topology
from backend import pack_compact
from analysis import stability,host_stability,thresholds
from campaign import launch_campaign,request_schedule,verify_test_receipt
import watchdog

RESULTS=[]

class ClosureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cfg=plan()
 def budget(self):return copy.deepcopy(self.cfg['stages']['Q2']['budgets'])
 def stage(self,requests=None,stage='Q2',fault=None,budget=None):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'campaign';r=launch_campaign(out,stage,tiny=True,test_requests=requests,test_budget=budget,fault=fault)
   self.assertTrue((out/'stage_receipt.json').exists() or fault=='stage_watchdog_crash');self.assertTrue((out/'authority_receipt.json').exists() or fault=='stage_watchdog_crash')
   self.assertTrue((out/'qualification_manifest.json').exists());self.assertEqual(load(out/'stage_receipt.json')['execution_authorized'],False) if (out/'stage_receipt.json').exists() and fault not in ('tamper','malformed') else None
   self.assertLessEqual(footprint(out)[1],(budget or {}).get('files_max',256));self.assertLessEqual(footprint(out)[0],(budget or {}).get('scratch_bytes',self.cfg['stages'][stage]['budgets']['scratch_bytes']))
   for pid in [pid for row in r['trials'] for pid in row.get('tracked_pids',[])]:self.assertFalse(watchdog.alive(pid))
   records,tail=recover(out/'archive');self.assertFalse(tail)
   for row in records:
    self.assertIn('record_hash',row);self.assertEqual(read_trial(out/'archive',row['trial_id']),row)
   outer=[json.loads(line) for line in (out/'resource_trace.jsonl').read_text().splitlines()] if (out/'resource_trace.jsonl').exists() else []
   RESULTS.append({'stage':stage,'status':r['status'],'STOP_reason':r['STOP_reason'],'logical_trials':len(records),'physical_files_final':footprint(out)[1],'physical_files_peak_sampled':max((x.get('file_count',0) for x in outer),default=0),'scratch_peak_sampled_bytes':max((x.get('scratch_bytes',0) for x in outer),default=0),'no_orphans':True,'traces_parseable':True,'all_artifact_SHA_readback_verified':True,'actual_authorization_created':False})
   return r,records
 def req(self,fault=None):return [{'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':'scalar','phase':'primitives','context_kind':'RECURRING_STEP_EQUIVALENT',**({'fault':fault} if fault else {})}]
 def test_B1_schedule_unchanged_checkpoint(self):
  startup=context('STARTUP_ONE_TIME');startup.begin(.3);self.assertTrue(startup.full);self.assertEqual(startup.step,1)
  recur=context('RECURRING_STEP_EQUIVALENT');recur.begin(recurring_time());self.assertFalse(recur.full);self.assertTrue(recur.selected);self.assertEqual(recur.step,4);self.assertEqual(recur.full_count,3)
  self.assertEqual(list(recur.full_targets),[.5,1.,1.5,1.99]);self.assertEqual(list(recur.bundle_targets)[0],.1)
  self.assertTrue(accounting(self.cfg)['within_budget'])
 def test_B1_tiny_whole_Q1_campaign(self):
  r,rows=self.stage(stage='Q1');self.assertEqual(r['status'],'COMPLETE_REQUIRES_RESOURCE_REVIEW',r['STOP_reason']);self.assertEqual(len(rows),7)
  self.assertEqual([x['metadata']['request']['mode'] for x in rows[1:]],self.cfg['Q1_design']['order'])
  self.assertTrue(r['Q1_accounting']['within_budget']);startup_bundle=next(a for a in rows[0]['artifacts'] if a['path']=='runtime/final_bundle.bin');self.assertTrue(startup_bundle['content_shared']);self.assertEqual(rows[0]['metadata']['request']['context_kind'],'STARTUP_ONE_TIME')
  bundles=[next(a for a in row['artifacts'] if a['path']=='runtime/final_bundle.bin') for row in rows[1:] if row['metadata']['request']['mode']=='ON'];self.assertEqual(len({a['sha256'] for a in bundles}),1);self.assertTrue(all(a['content_shared'] for a in bundles[1:]))
 def test_B1_startup_bundle_exact_view_of_full_audit(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=Archive(root/'archive',self.budget());work=root/'work';runtime=work/'runtime';runtime.mkdir(parents=True)
   packets=[bytes([i])*100 for i in range(10)];header=b'RAB13\0'
   (runtime/'full_2.bin').write_bytes(header+b''.join(struct.pack('<Q',len(p))+p for p in packets))
   (runtime/'final_bundle.bin').write_bytes(header+b''.join(struct.pack('<Q',len(p))+p for p in packets[::3]))
   a.commit('startup',0,work,{'status':'COMPLETE','request':{'context_kind':'STARTUP_ONE_TIME'}})
   r=read_trial(root/'archive','startup');bundle=next(x for x in r['artifacts'] if x['path']=='runtime/final_bundle.bin')
   self.assertTrue(bundle['content_shared']);self.assertTrue(all(s['file'].startswith('audit_') for s in bundle['segments']));self.assertFalse(list((root/'archive').glob('data_*')))
 def test_B2_hundreds_logical_trials_bounded_chunks(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);archive=Archive(root/'archive',self.budget(),chunk_bytes=4096)
   for i in range(240):
    work=root/'work';work.mkdir();(work/'sample.bin').write_bytes(bytes([i%4])*100)
    archive.commit(str(i),i,work,{'status':'COMPLETE','value':i})
   self.assertLess(footprint(root)[1],8)
   for i in random.Random(7).sample(range(240),12):
    r=read_trial(root/'archive',str(i));self.assertEqual(r['metadata']['value'],i);self.assertEqual(b''.join(artifact_blocks(root/'archive',r['artifacts'][0])),bytes([i%4])*100)
   work=root/'work';work.mkdir();(work/'a').write_bytes(b'a')
   with self.assertRaises(ValueError):archive.commit('1',240,work,{'status':'COMPLETE'})
   with self.assertRaises(ValueError):archive.commit('later',999,work,{'status':'COMPLETE'})
 def test_B2_tail_crash_and_truncated_uncommitted_chunk(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=Archive(root/'archive',self.budget(),chunk_bytes=4096);w=root/'w';w.mkdir();(w/'a').write_bytes(b'committed');a.commit('0',0,w,{'status':'COMPLETE'})
   chunk=next((root/'archive').glob('data_*'));committed=chunk.stat().st_size
   with chunk.open('ab') as f:f.write(b'partial uncommitted tail')
   with chunk.open('r+b') as f:f.truncate(committed+3)
   self.assertEqual(len(recover(root/'archive')[0]),1)
   with (root/'archive/trial_index.jsonl').open('ab') as f:f.write(b'{"mid_record":')
   rows,tail=recover(root/'archive');self.assertTrue(tail);self.assertEqual(len(rows),1)
   with self.assertRaises(ValueError):Archive(root/'archive',self.budget())
   with chunk.open('r+b') as f:f.truncate(2)
   with self.assertRaises(ValueError):recover(root/'archive')
 def test_B2_static_layout_and_full_Q2_runtime(self):
  model=layout(self.cfg,'Q2');self.assertLessEqual(model['worst_case_physical_files'],256);self.assertGreater(model['reserved_stop_files'],0)
  r,rows=self.stage(stage='Q2');self.assertEqual(r['status'],'COMPLETE_REQUIRES_RESOURCE_REVIEW',r['STOP_reason']);self.assertEqual(len(rows),model['logical_trials'])
  self.assertEqual(r['file_layout']['registered_files_limit'],256)
 def test_B3_compact_receipt_exact_production_row(self):
  p=compact_receipt(tiny_topology())['payload'];raw=pack_compact(p)
  expected=struct.pack('<II',0,len(p['values']))+bytes.fromhex(p['identity'])+bytes.fromhex(p['payload'])+struct.pack('<'+'d'*len(p['values']),*p['values'])
  self.assertEqual(raw,expected);self.assertNotIn('native_state_epoch',p);self.assertLess(len(json.dumps(p)),2048)
  with self.assertRaises(ValueError):pack_compact(dict(p,field_state={}))
 def test_B3_Writer_static_aliasing_and_changed_blob_rejection(self):
  from persistence import Writer
  from fixture import state
  with tempfile.TemporaryDirectory() as d:
   w=Writer(Path(d));s=state(tiny_topology());result=w.share(s)
   key=result['geometry']['$immutable'];self.assertIs(w.immutable[key],s['geometry']);self.assertIn('volumes',w.immutable_keys)
   self.assertEqual(w.share(copy.deepcopy(s)),result)
   changed=copy.deepcopy(s);changed['geometry']['linear_weights'][0]=.25
   with self.assertRaises(ValueError):w.share(changed)
 def test_B3_span_children_exclusive_and_ACK_overlap_rule(self):
  s=Span()
  with s.scope('callback'):
   with s.scope('packing'):pass
  parent,child=s.nodes;self.assertEqual(child['parent_id'],parent['id']);self.assertAlmostEqual(parent['exclusive_seconds']+child['inclusive_seconds'],parent['inclusive_seconds'])
  self.assertIn('never add',s.report()['cross_process_rule'])
 def test_B3_registered_repeatability_and_missing_host(self):
  x=stability([1.,1.,1.],[{'status':'STABLE'}]*3);self.assertEqual(x['status'],'STABLE');self.assertFalse(x['automatic_extra_repeats'])
  self.assertEqual(stability([1.,2.,3.],[{'status':'STABLE'}]*3)['status'],'UNRESOLVED');self.assertEqual(stability([1.,1.,1.],[{'status':'UNRESOLVED'}]*3)['status'],'UNRESOLVED');self.assertEqual(host_stability([])['status'],'UNRESOLVED');self.assertEqual(thresholds()['CV'],.20)
 def test_B4_positive_stage_and_immutable_readback(self):
  r,rows=self.stage(self.req()*3);self.assertEqual(r['status'],'COMPLETE_REQUIRES_RESOURCE_REVIEW');self.assertEqual(len(rows),3)
  self.assertTrue(all(row['metadata']['sample_valid'] for row in rows))
 def test_B4_trial_timeout_retains_completed_and_partial(self):
  r,rows=self.stage(self.req()+self.req('timeout')+self.req());self.assertEqual(r['status'],'STOPPED');self.assertEqual(len(rows),2);self.assertEqual(rows[-1]['metadata']['status'],'CENSORED');self.assertEqual(r['completed_repeats'],1)
 def test_B4_worker_and_backend_crashes(self):
  for fault in ('worker_crash','backend_crash'):
   r,rows=self.stage(self.req(fault));self.assertEqual(r['status'],'STOPPED');self.assertFalse(rows[0]['metadata']['sample_valid'])
 def test_B4_trial_and_stage_watchdog_crash(self):
  for fault in ('watchdog_crash','stage_watchdog_crash'):
   r,rows=self.stage(self.req(fault if fault=='watchdog_crash' else None),fault=fault if fault=='stage_watchdog_crash' else None);self.assertEqual(r['status'],'STOPPED');self.assertIn('WATCHDOG',r['STOP_reason'])
 def test_B4_nested_SIGTERM_ignore_no_orphans(self):
  r,rows=self.stage([dict(self.req('nested_ignore')[0],sample_class='matrix')]);self.assertEqual(r['status'],'STOPPED');self.assertEqual(rows[0]['metadata']['status'],'CENSORED');self.assertGreater(len(rows[0]['metadata']['tracked_pids']),3)
 def test_B4_quota_and_file_reserve(self):
  for budget in ({'scratch_bytes':100*1024},{'files_max':20}):
   r,rows=self.stage(self.req(),budget=budget);self.assertEqual(r['status'],'STOPPED');self.assertIn('STOP_STORAGE_GUARD',r['STOP_reason'])
 def test_B4_malformed_and_tampered_receipt(self):
  for fault in ('malformed','tamper'):
   r,rows=self.stage(self.req(),fault=fault);self.assertEqual(r['status'],'STOPPED');self.assertFalse(rows);self.assertIn('RECEIPT',r['STOP_reason'])
 def test_B4_STOP_publish_race_retains_committed_and_partial(self):
  req=self.req()+[dict(self.req('writer_race')[0],sample_class='matrix')]
  r,rows=self.stage(req);self.assertEqual(r['status'],'STOPPED');self.assertEqual(len(rows),2)
  self.assertTrue(any(a['path'].endswith('initial_state.bin.partial') for a in rows[-1]['artifacts']))
  self.assertFalse(rows[-1]['metadata']['sample_valid']);self.assertTrue(rows[0]['metadata']['sample_valid'])
 def test_readiness_is_all_or_nothing_and_never_authorizes(self):
  from readiness import derive
  b={k:{'status':'PASS'} for k in ('B1','B2','B3','B4')};self.assertEqual(derive(b),{'Q1':True,'Q2':True})
  for key in b:
   changed=copy.deepcopy(b);changed[key]['status']='UNRESOLVED';r=derive(changed)
   self.assertFalse(r['Q1'] if key=='B1' else r['Q2'] if key in ('B2','B3') else r['Q1'] or r['Q2'])
 def test_B4_no_overwrite_double_finalization(self):
  from campaign import finalize
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'out';launch_campaign(root,'Q2',tiny=True,test_requests=self.req())
   h=sha(root/'stage_result.json')
   with self.assertRaises(ValueError):launch_campaign(root,'Q2',tiny=True,test_requests=self.req())
   with self.assertRaises(ValueError):finalize(root,{},self.budget())
   self.assertEqual(sha(root/'stage_result.json'),h)

if __name__=='__main__':unittest.main()
