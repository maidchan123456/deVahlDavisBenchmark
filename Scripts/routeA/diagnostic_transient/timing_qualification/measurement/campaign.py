"""Whole-stage campaign: sealed permission, nested guards, archived logical trials."""
import copy,json,os,sys,time
from pathlib import Path
from common import ROOT,HERE,plan,need,atomic,sha,load,host,footprint,before_write,manifest,safe_output,authority,qualification
from archive import Archive,recover,layout,STOP_FILES,STOP_BYTES,WORK_FILES
from watchdog import launch,alive
from analysis import fit,stability,host_stability
from schedule import accounting


def request_schedule(cfg,stage,tiny=False):
 if stage=='Q1':
  return [{'kind':'pipeline','mode':'ON','context_kind':'STARTUP_ONE_TIME','cost_class':'STARTUP_ONE_TIME','phase':'startup'}]+[{'kind':'pipeline','mode':mode,'context_kind':'RECURRING_STEP_EQUIVALENT','cost_class':'RECURRING_STEP_EQUIVALENT','phase':'recurring'} for mode in cfg['Q1_design']['order']]
 rows=[]
 for n in cfg['Q2_U03']['node_counts']:
  for repeat in range(cfg['Q2_U03']['repeats']):rows.append({'kind':'u03','N':4 if tiny else n,'registered_N':n,'phase':'U03','repeat':repeat})
 for cls in ('scalar','field','matrix','term','controller','selected'):
  for repeat in range(cfg['Q2_pipeline']['repeats']):rows.append({'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':cls,'phase':'primitives','repeat':repeat,'context_kind':'RECURRING_STEP_EQUIVALENT'})
 for ev in cfg['memory_events']+['chunk publication']:
  for repeat in range(cfg['repeatability']['minimum_repeats']):rows.append({'kind':'pipeline','mode':'ON','purpose':'memory','sample_class':'scalar' if ev=='chunk publication' else 'selected','event':ev,'phase':'memory','repeat':repeat,'context_kind':'RECURRING_STEP_EQUIVALENT'})
 for repeat in range(cfg['repeatability']['minimum_repeats']):rows.append({'kind':'io','phase':'IO','repeat':repeat})
 return rows

def test_receipt(out,stage,budget,prior):
 # This substitutes only the external permission boundary. Frozen authority and
 # declaration validation still run; no real authorization receipt is issued.
 authority_receipt=authority.verify_authority()
 spec={'mode':stage,'output_root':str(ROOT/'results/routeA/diagnostic_transient/timing_qualification/TINY_DECLARATION_ONLY'),'authorization':{'scope':'NONCFD_TIMING_QUALIFICATION','task_reference':'TINY_TEST_VALIDATOR_SUBSTITUTE_NO_EXECUTION_PERMISSION','allowed_stages':[stage]},'plan_sha256':sha(__import__('common').PLAN),'prerequisites':prior}
 declaration=qualification.validate_permission(spec)
 need(declaration['execution_authorized'] is False,'STOP_TEST_PERMISSION_ESCALATION')
 r={'schema':'tiny_timing_stage_receipt/2','mode':stage,'classification':'TINY_SELF_TEST_ONLY','fixture_cells':4,'execution_authorized':False,'permission_substitute':declaration,'authority':authority_receipt,'budget':budget,'qualification_id':out.name}
 atomic(out,'stage_receipt.json',r);atomic(out,'stage_receipt_sha256.json',{'sha256':sha(out/'stage_receipt.json')});return out/'stage_receipt.json'

def verify_test_receipt(path):
 path=Path(path);r=load(path);need(sha(path)==load(path.parent/'stage_receipt_sha256.json')['sha256'],'STOP_TEST_RECEIPT_TAMPERED')
 need(set(r)=={'schema','mode','classification','fixture_cells','execution_authorized','permission_substitute','authority','budget','qualification_id'} and r['schema']=='tiny_timing_stage_receipt/2','STOP_TEST_RECEIPT_SCHEMA')
 need(r['classification']=='TINY_SELF_TEST_ONLY' and r['fixture_cells']==4 and r['execution_authorized'] is False and r['permission_substitute']['execution_authorized'] is False,'STOP_TEST_RECEIPT_SCOPE')
 plan();need(r['authority']['canonical_authority']['sha256']==sha(__import__('common').CONTRACT),'STOP_TEST_AUTHORITY_CHANGED');return r

def compact_worker(r):
 if r is None:return None
 return {k:v for k,v in r.items() if k in ('status','N','kernel_wall_seconds','mode','purpose','callbacks_recurring','matrix_packets','context_kind','recurring_native_seconds','constructor_native_seconds','native_time_v','backend_time_v','native_exit','backend_exit','setup_completed_monotonic')}

def execute_trial(root,stage,ordinal,req,receipt,auth,remaining,budget,tiny=False):
 before_write(root,budget,16384,WORK_FILES)
 work=root/'active_trial';need(not work.exists(),'STOP_STALE_WORKSPACE');work.mkdir()
 request=dict(req,budget=budget,classification='TINY_SELF_TEST_ONLY' if tiny else 'RESOURCE_QUALIFICATION_FIXTURE_ONLY',tiny=tiny,stage_receipt=str(receipt),authorization_file=str(auth) if auth else None)
 atomic(work,'worker_request.json',request,budget)
 cfg=plan();wall=min(budget['single_trial_wall_seconds'],remaining)
 if req['kind']=='u03':wall=min(wall,cfg['Q2_U03']['single_trial_wall_seconds'])
 if tiny and req.get('fault')=='timeout':wall=min(wall,.3)
 if tiny and req.get('fault') in ('nested_ignore','writer_race'):wall=min(wall,3.)
 result=launch({'command':[sys.executable,'-B',str(HERE/'worker.py'),str(work/'worker_request.json')],'budget':budget,'trial_wall':wall,'interval':cfg['measurement']['simultaneous_RSS_sample_interval_seconds'],'disk_interval':.1,'test_injection':'supervisor_crash' if tiny and req.get('fault')=='watchdog_crash' else None},work)
 trace=[];tracefile=work/'resource_trace.jsonl'
 if tracefile.exists():
  try:trace=[json.loads(line) for line in tracefile.read_text().splitlines()]
  except ValueError:result.update(status='STOPPED',STOP_reason='STOP_WATCHDOG_FAILURE',sample_valid=False)
 else:result.update(status='STOPPED',STOP_reason='STOP_WATCHDOG_FAILURE',sample_valid=False)
 worker=load(work/'worker_result.json') if (work/'worker_result.json').exists() else None
 result.update(trial_id=f'{ordinal:03d}_{req["phase"]}',stage=stage,request=req,worker=compact_worker(worker),host_stability=host_stability(trace),resource_trace_SHA256=sha(tracefile) if tracefile.exists() else None)
 if req.get('kind')=='pipeline' and req.get('purpose','full')=='full' and result['status']=='COMPLETE':
  need(worker and worker['callbacks_recurring']==cfg['callback_graph']['recurring_callbacks_per_physical_step'] if 'callback_graph' in cfg else worker and worker['callbacks_recurring']==sum(x['frequency_per_step'] for x in cfg['callback_classes']),'STOP_CALLBACK_CAMPAIGN_COUNT')
 # Store actual spans and all trace/log/worker bytes in the archive, not a huge
 # duplicate stage JSON. Compact metadata references the immutable artifact index.
 if req.get('cost_class')=='RECURRING_STEP_EQUIVALENT' and req.get('mode')=='ON' and result['status']=='COMPLETE':
  digest=sha(work/'runtime/final_bundle.bin');reference=root/'fixture_bundle_identity.json'
  if reference.exists():need(load(reference)['sha256']==digest,'STOP_RECURRING_FIXTURE_CONTENT_CHANGED')
  else:atomic(root,reference.name,{'sha256':digest,'rule':'identical immutable fixture/checkpoint only; write timings were performed'},budget)
 if (work/'backend_result.json').exists():
  backend=load(work/'backend_result.json');result['memory_event_coverage']=[]
  for ev in backend.get('memory_events',[]):
   if ev.get('phase')!='after':continue
   name=ev['event'];start=next(x['monotonic'] for x in backend['memory_events'] if x['event']==name and x['phase']=='before');end=ev['monotonic'];samples=[x for x in trace if start<=x['timestamp_monotonic']<=end]
   result['memory_event_coverage'].append({'event':name,'before_monotonic':start,'after_monotonic':end,'samples':len(samples),'native_peak_RSS':max((sum(p['RSS'] for p in x['processes'] if p['role']=='native') for x in samples),default=None),'backend_peak_RSS':max((sum(p['RSS'] for p in x['processes'] if p['role']=='backend') for x in samples),default=None),'combined_simultaneous_peak_RSS':max((x['native_plus_backend_RSS'] for x in samples),default=None),'coverage':'MEASURED_EVENT_INTERVAL' if samples else 'UNRESOLVED_SAMPLING_GAP','not_guard_limit':True})
 result['trace_samples']=len(trace);need(footprint(work)[1]<=WORK_FILES,'STOP_WORKSPACE_FILE_BOUND');return result,work

def stage_body(root,stage,auth,prior,tiny=False,test_requests=None):
 start=time.monotonic();cfg=plan();budget=load(root/'quota_context.json')['budget'];deadline=start+budget['stage_wall_seconds'];archive=Archive(root/'archive',budget)
 receipt=test_receipt(root,stage,budget,prior) if tiny else __import__('runner').stage_receipt(root,stage,auth,prior)
 atomic(root,'authority_receipt.json',authority.verify_authority(),budget)
 if tiny and os.environ.get('ROUTE_A_STAGE_TEST_RECEIPT'):
  if os.environ['ROUTE_A_STAGE_TEST_RECEIPT']=='tamper':receipt.write_text(receipt.read_text()+' ')
  else:receipt.write_text('{}')
 rows=[];stop=None;phase=None;phase_end=deadline
 requests=test_requests if test_requests is not None else request_schedule(cfg,stage,tiny)
 try:
  for ordinal,req in enumerate(requests):
   if tiny:verify_test_receipt(receipt)
   else:__import__('runner').verify_stage_execution(receipt,auth)
   if req['phase']!=phase:
    phase=req['phase'];phase_end=min(deadline,time.monotonic()+cfg['Q2_subbudgets_seconds'].get(phase,budget['stage_wall_seconds']))
   remaining=min(deadline,phase_end)-time.monotonic()
   if remaining<=0:stop='STOP_PHASE_OR_STAGE_WALL';break
   row,work=execute_trial(root,stage,ordinal,req,receipt,auth,remaining,budget,tiny)
   handle=archive.commit(row['trial_id'],ordinal,work,row);rows.append(dict(row,archive_index=handle))
   if row['status']!='COMPLETE':stop=row.get('STOP_reason') or 'STOP_TRIAL';break
 except BaseException as error:stop=str(error)
 result=stage_summary(stage,rows,stop,start,cfg,tiny)
 finalize(root,result,budget);return result

def stage_summary(stage,rows,stop,start,cfg,tiny=False):
 grouped={}
 for r in rows:
  if r['status']!='COMPLETE':continue
  q=r['request'];key=q['phase']+'|'+str(q.get('event',q.get('sample_class',q.get('registered_N',q.get('mode','IO')))))
  grouped.setdefault(key,[]).append(r)
 stats={k:stability([x['worker']['kernel_wall_seconds'] if x['request']['kind']=='u03' else x['wall_seconds'] for x in group],[x['host_stability'] for x in group]) for k,group in grouped.items()}
 pairs=[]
 recurring=[r for r in rows if r['request']['phase']=='recurring']
 for i in range(0,len(recurring)-1,2):
  a,b=recurring[i:i+2]
  if a['status']==b['status']=='COMPLETE':
   on=a if a['request']['mode']=='ON' else b;off=b if on is a else a
   pairs.append({'ON':on['trial_id'],'OFF':off['trial_id'],'pairedONminusOFF_native_recurring_seconds':on['worker']['recurring_native_seconds']-off['worker']['recurring_native_seconds'],'pairedONminusOFF_external_wall_seconds':on['wall_seconds']-off['wall_seconds'],'constructor_excluded_from_native_recurring':True})
 costs={'campaign_startup':[r['trial_id'] for r in rows if r['request']['phase']=='startup'],'startup_audit_projection_multiplicity':3,'per_trial_setup':'worker_summary.setup_completed_monotonic minus watchdog start; includes authority/process setup','recurring_step_equivalent':'native callback spans excluding constructor; full external wall retained separately','selected_audit':'backend class persistence_write_fsync_manifest spans at bundle publication','full_startup_audit':'startup Writer.accept inclusive spans + stream_hash_commit_fsync; no additive ACK','finalization':'native FINISH span and backend finalization parent tree overlap'}
 out={'classification':'TINY_CORRECTNESS_ONLY_NOT_TARGET_MEASUREMENT' if tiny else 'RESOURCE_QUALIFICATION_FIXTURE_ONLY','status':'STOPPED' if stop else 'COMPLETE_REQUIRES_RESOURCE_REVIEW','STOP_reason':stop,'stage':stage,'trials':rows,'completed_repeats':sum(r['status']=='COMPLETE' for r in rows),'stability':stats,'pairedONminusOFF':pairs,'cost_classes':costs,'Q1_accounting':accounting(cfg) if stage=='Q1' else None,'file_layout':layout(cfg,stage),'resource_feasibility':'UNRESOLVED','Q3_authorized':False,'execution_authorized':False,'actual_authorization_created':False,'wall_seconds':time.monotonic()-start}
 if stage=='Q2':out['U03_fit']=fit([dict(r['worker'] or {},N=r['request'].get('N') if tiny else r['request'].get('registered_N',r['request'].get('N')),status=r['status']) for r in rows if r['request']['kind']=='u03'])
 return out

def finalize(root,result,budget):
 need(not (root/'stage_result.json').exists(),'STOP_DOUBLE_FINALIZATION')
 atomic(root,'stage_result.json',result,budget,emergency=True)


def launch_campaign(root,stage,auth=None,prior=None,tiny=False,test_requests=None,test_budget=None,fault=None):
 root=Path(root);cfg=plan();need(stage in ('Q1','Q2'),'STOP_NO_CFD_STAGE');prior=prior or {'Q0_status':'PASS','Q1_status':'PASS'}
 if not tiny:
  safe_output(root);need(auth is not None,'STOP_FUTURE_AUTH_REQUIRED');__import__('runner').verify_authorization(auth,stage,root,prior)
 need(not root.exists(),'STOP_EXISTING_CAMPAIGN_OUTPUT');root.mkdir(parents=True,mode=0o700)
 budget=copy.deepcopy(cfg['stages'][stage]['budgets'])
 if test_budget:
  need(tiny,'STOP_TARGET_BUDGET_OVERRIDE');budget.update(test_budget)
 reserve_bytes=min(STOP_BYTES,budget['scratch_bytes']//4) if tiny else STOP_BYTES;reserve_files=min(STOP_FILES,max(2,budget['files_max']//4)) if tiny else STOP_FILES
 atomic(root,'quota_context.json',{'root':str(root.absolute()),'budget':budget,'stop_reserve_bytes':reserve_bytes,'stop_reserve_files':reserve_files,'sidechannel_reserve_bytes':min(4*2**20,budget['scratch_bytes']//16) if tiny else 4*2**20,'sidechannel_reserve_files':min(8,max(1,budget['files_max']//8)) if tiny else 8})
 request={'stage':stage,'auth':str(auth) if auth else None,'prior':prior,'tiny':tiny,'test_requests':test_requests,'test_fault':fault}
 need(tiny or (test_requests is None and fault is None),'STOP_TARGET_TEST_INPUT')
 atomic(root,'stage_request.json',request,budget)
 start=time.monotonic();r=launch({'command':[sys.executable,'-B',str(HERE/'campaign.py'),str(root/'stage_request.json')],'budget':budget,'trial_wall':budget['stage_wall_seconds'],'allow_nested':True,'test_injection':'supervisor_crash' if tiny and fault=='stage_watchdog_crash' else None},root)
 if not (root/'stage_result.json').exists():
  records,tail=recover(root/'archive',verify=False);rows=[x['metadata'] for x in records]
  result=stage_summary(stage,rows,r.get('STOP_reason') or 'STOP_STAGE_RUNNER_EXIT',start,cfg,tiny);result['partial_archive_tail']=tail;finalize(root,result,budget)
 result=load(root/'stage_result.json')
 if r['status']!='COMPLETE' and result['status']!='STOPPED':
  # Immutable normal summary remains readable but external guard veto is a new
  # final-state record, never a rewrite or a valid completed stage sample.
  atomic(root,'stage_supervisor_veto.json',r,budget,emergency=True);result=dict(result,status='STOPPED',STOP_reason=r['STOP_reason'])
 manifest(root,budget) if not (root/'qualification_manifest.json').exists() else None
 need(not r.get('remaining_live_pids'),'STOP_STAGE_ORPHAN');return result

if __name__=='__main__':
 reqfile=Path(sys.argv[1]);r=load(reqfile)
 if r['tiny']:
  need(r['auth'] is None,'STOP_NO_REAL_TEST_AUTHORIZATION')
  if r.get('test_fault') in ('tamper','malformed'):os.environ['ROUTE_A_STAGE_TEST_RECEIPT']=r['test_fault']
 stage_body(reqfile.parent,r['stage'],Path(r['auth']) if r['auth'] else None,r['prior'],r['tiny'],r['test_requests'])
