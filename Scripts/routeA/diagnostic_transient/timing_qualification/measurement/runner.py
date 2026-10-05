"""Default dry-run. Future Q1/Q2 campaign requires a separate explicit authorization file."""
import argparse,copy,json,os,sys,time
from pathlib import Path
from common import ROOT,HERE,PREP,PLAN,CONTRACT,plan,load,sha,need,safe_output,atomic,host,manifest,footprint,qualification,authority,before_write
from fixture import topology,graph
from watchdog import launch
from analysis import fit,stability

HARNESS_MANIFEST=PREP/'TimingQualification_harness_manifest.json'

def verify_harness():
 m=load(HARNESS_MANIFEST)
 for path,digest in m['source_SHA256'].items():need(sha(ROOT/path)==digest,'STOP_HARNESS_SHA256:'+path)
 for path,digest in m['artifact_SHA256'].items():need(sha(ROOT/path)==digest,'STOP_HARNESS_BINARY_SHA256:'+path)
 need(m['canonical_SHA256']==sha(CONTRACT) and m['plan_SHA256']==sha(PLAN),'STOP_HARNESS_AUTHORITY')
 return m

def verify_authorization(path,stage,output,prior):
 auth=load(path);allowed={'schema','authorized_task','task_reference','scope','allowed_stages','execution_authorized','canonical_SHA256','plan_SHA256','harness_manifest_SHA256'}
 need(set(auth)==allowed,'STOP_AUTHORIZATION_FORMAT')
 need(auth['schema']=='nonCFD_timing_authorization/1' and auth['authorized_task']=='RUN_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION','STOP_NOT_MEASUREMENT_AUTHORIZATION')
 need(auth['execution_authorized'] is True and auth['scope']=='NONCFD_TIMING_QUALIFICATION','STOP_EXPLICIT_NONCFD_AUTH_REQUIRED')
 need(auth['canonical_SHA256']==sha(CONTRACT) and auth['plan_SHA256']==sha(PLAN) and auth['harness_manifest_SHA256']==sha(HARNESS_MANIFEST),'STOP_AUTHORIZATION_HASH')
 need(verify_harness()['measurement_ready'].get(stage) is True,'STOP_MEASUREMENT_PREPARATION_INCOMPLETE:'+stage)
 spec={'mode':stage,'output_root':str(output),'authorization':{'scope':auth['scope'],'task_reference':auth['task_reference'],'allowed_stages':auth['allowed_stages']},'plan_sha256':auth['plan_SHA256'],'prerequisites':prior}
 qualification.validate_permission(spec);verify_harness();return auth

def stage_receipt(out,stage,authorization_file,prior):
 cfg=plan();auth=verify_authorization(authorization_file,stage,out,prior);t=topology();g=graph()
 receipt={'schema':'timing_stage_receipt/1','qualification_id':out.name,'mode':stage,'authority_SHA256':sha(CONTRACT),'plan_SHA256':sha(PLAN),'runtime_adapter_SHA256':sha(ROOT/'Scripts/routeA/diagnostic_transient/v1_5_runtime/runtime_authority_manifest.json'),'harness_manifest_SHA256':sha(HARNESS_MANIFEST),'watchdog_SHA256':sha(HERE/'watchdog.py'),'authorization_SHA256':sha(authorization_file),'permission_scope':auth['scope'],'host_snapshot':host(),'budgets':cfg['stages'][stage]['budgets'],'topology':t['counts'],'patches':[{k:p[k] for k in ('name','type','nFaces','startFace')} for p in t['patches']],'mesh_SHA256':t['mesh_SHA256'],'callbacks_recurring':len(g)-1,'matrix_packets':701,'prior_stage_status':prior,'production_run_authorized':False}
 atomic(out,'stage_receipt.json',receipt,cfg['stages'][stage]['budgets']);atomic(out,'stage_receipt_sha256.json',{'sha256':sha(out/'stage_receipt.json')},cfg['stages'][stage]['budgets']);return out/'stage_receipt.json'

def verify_stage_execution(receipt_path,authorization_file):
 receipt_path=Path(receipt_path);r=load(receipt_path);need(sha(receipt_path)==load(receipt_path.parent/'stage_receipt_sha256.json')['sha256'],'STOP_STAGE_RECEIPT_CHANGED')
 need(r['mode'] in ('Q1','Q2'),'STOP_CFD_STAGE_FORBIDDEN')
 need(r['plan_SHA256']==sha(PLAN) and r['authority_SHA256']==sha(CONTRACT) and r['harness_manifest_SHA256']==sha(HARNESS_MANIFEST),'STOP_STAGE_AUTHORITY')
 verify_authorization(authorization_file,r['mode'],receipt_path.parent,r['prior_stage_status']);need(sha(authorization_file)==r['authorization_SHA256'],'STOP_AUTHORIZATION_CHANGED')
 t=topology();need(t['counts']==r['topology'] and t['mesh_SHA256']==r['mesh_SHA256'],'STOP_MESH_CHANGED');return r

def trial(stage_root,stage,ident,request,receipt,auth,remaining):
 cfg=plan();b=cfg['stages'][stage]['budgets'];out=stage_root/ident;before_write(stage_root,b,4096,8);out.mkdir(exist_ok=False)
 used,count=footprint(stage_root);local=copy.deepcopy(b);local['scratch_bytes']=max(1,b['scratch_bytes']-used);local['files_max']=max(1,b['files_max']-count)
 request.update(budget=local,classification='RESOURCE_QUALIFICATION_FIXTURE_ONLY',stage_receipt=str(receipt),authorization_file=str(auth));atomic(out,'worker_request.json',request,local)
 wall=min(b['single_trial_wall_seconds'],remaining)
 if request['kind']=='u03':wall=min(wall,cfg['Q2_U03']['single_trial_wall_seconds'])
 result=launch({'command':[sys.executable,'-B',str(HERE/'worker.py'),str(out/'worker_request.json')],'budget':local,'trial_wall':wall,'interval':cfg['measurement']['simultaneous_RSS_sample_interval_seconds'],'disk_interval':.1},out)
 result.update(trial_id=ident,stage=stage,request=request,resource_trace_SHA256=sha(out/'resource_trace.jsonl') if (out/'resource_trace.jsonl').exists() else None,worker=load(out/'worker_result.json') if (out/'worker_result.json').exists() else None)
 atomic(out,'measurement_manifest.json',result,local);manifest(out,local);return result

def run_stage(stage,out,auth,prior,supervised=False):
 start=time.monotonic();cfg=plan();safe_output(out);need(stage in ('Q1','Q2'),'STOP_CFD_STAGE_FORBIDDEN');verify_authorization(auth,stage,out,prior);need(supervised or not out.exists(),'STOP_EXISTING_QUALIFICATION_OUTPUT')
 end=start+cfg['stages'][stage]['budgets']['stage_wall_seconds'];
 if not supervised:out.mkdir(parents=True,exist_ok=False,mode=0o700)
 receipt=stage_receipt(out,stage,auth,prior);rows=[];stop=None
 try:
  if stage=='Q1':
   requests=[{'kind':'pipeline','mode':mode} for mode in cfg['Q1_design']['order']]
   for i,req in enumerate(requests):
    if time.monotonic()>=end:stop='STOP_STAGE_WALL';break
    row=trial(out,stage,'trial_'+str(i),req,receipt,auth,end-time.monotonic());rows.append(row)
    if row['status']!='COMPLETE':stop=row.get('STOP_reason') or 'STOP_INCOMPLETE_STEP_MIX';break
  else:
   suite_end=min(end,time.monotonic()+cfg['Q2_U03']['suite_wall_seconds'])
   for n in cfg['Q2_U03']['node_counts']:
    for repeat in range(cfg['Q2_U03']['repeats']):
     if time.monotonic()>=suite_end:stop='STOP_U03_BENCHMARK_LIMIT';break
     row=trial(out,stage,f'u03_{n}_{repeat}',{'kind':'u03','N':n},receipt,auth,suite_end-time.monotonic());rows.append(row)
     if row['status']!='COMPLETE':stop='STOP_U03_BENCHMARK_LIMIT';break
    if stop:break
   if not stop:
    for phase in ('primitives','memory','IO'):
     phase_end=min(end,time.monotonic()+cfg['Q2_subbudgets_seconds'][phase]);requests=[]
     if phase=='primitives':requests=[{'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':cl} for cl in ('scalar','field','matrix','term','selected') for _ in range(cfg['repeatability']['minimum_repeats'])]
     elif phase=='memory':requests=[{'kind':'pipeline','mode':'ON','purpose':'memory','sample_class':'selected','event':ev} for ev in cfg['memory_events'] for _ in range(cfg['repeatability']['minimum_repeats'])]
     else:requests=[{'kind':'io'} for _ in range(cfg['repeatability']['minimum_repeats'])]
     for i,req in enumerate(requests):
      if time.monotonic()>=phase_end:stop='STOP_PHASE_OR_STAGE_WALL';break
      row=trial(out,stage,f'{phase}_{i}',req,receipt,auth,phase_end-time.monotonic());rows.append(row)
      if row['status']!='COMPLETE':stop=row.get('STOP_reason') or 'STOP_TRIAL';break
     if stop:break
  if stage=='Q2':
   urows=[dict(r['worker'],status=r['status']) if r['worker'] else {'N':r['request']['N'],'status':r['status'],'censored':True,'elapsed_lower_bound_seconds':min(cfg['Q2_U03']['single_trial_wall_seconds'],r.get('wall_seconds',0.))} for r in rows if r['request']['kind']=='u03'];atomic(out,'U03_fit.json',fit(urows),cfg['stages'][stage]['budgets'])
  # Stage completion is resource evidence, not an automatic feasibility or Q3 gate.
  result={'status':'STOPPED' if stop else 'COMPLETE_REQUIRES_RESOURCE_REVIEW','STOP_reason':stop,'trials':rows,'resource_feasibility':'UNRESOLVED_UNTIL_REGISTERED_REVIEW','execution_authorized':False,'Q3_authorized':False,'production_run_authorized':False,'wall_seconds':time.monotonic()-start}
  atomic(out,'stage_result.json',result,cfg['stages'][stage]['budgets']);return result
 except BaseException as error:
  atomic(out,'stage_failure.json',{'status':'STOPPED','error':str(error),'completed_repeats':sum(r['status']=='COMPLETE' for r in rows),'partial_trials':rows,'sample_valid':False});raise

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=('Q1','Q2'));parser.add_argument('--authorization',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--prior',type=Path);parser.add_argument('--stage-request',type=Path,help=argparse.SUPPRESS);args=parser.parse_args()
 if args.stage_request:
  r=load(args.stage_request);run_stage(r['stage'],args.stage_request.parent,Path(r['authorization_file']),r['prior'],supervised=True)
 elif args.authorization is None:
  print(json.dumps({'mode':'DRY_RUN','execution_authorized':False,'Q1_Q2_executed':False,'Q3_supported':False,'target_topology':topology()['counts'],'plan_SHA256':sha(PLAN),'requirements':['separate NONCFD measurement task authorization','immutable stage receipt','new qualification output'],'harness_manifest':str(HARNESS_MANIFEST)},indent=2))
 else:
  need(args.stage and args.output and args.prior,'STOP_REQUIRED_STAGE_OUTPUT_PRIOR');safe_output(args.output);verify_authorization(args.authorization,args.stage,args.output,load(args.prior));need(not args.output.exists(),'STOP_EXISTING_QUALIFICATION_OUTPUT');cfg=plan();args.output.mkdir(parents=True,mode=0o700);atomic(args.output,'stage_request.json',{'stage':args.stage,'authorization_file':str(args.authorization.resolve()),'prior':load(args.prior)},cfg['stages'][args.stage]['budgets']);result=launch({'command':[sys.executable,'-B',str(HERE/'runner.py'),'--stage-request',str(args.output/'stage_request.json')],'budget':cfg['stages'][args.stage]['budgets'],'trial_wall':cfg['stages'][args.stage]['budgets']['stage_wall_seconds'],'allow_nested':True},args.output);manifest(args.output,cfg['stages'][args.stage]['budgets']);print(json.dumps(result))
