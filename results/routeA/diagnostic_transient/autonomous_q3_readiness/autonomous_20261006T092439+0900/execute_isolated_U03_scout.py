from pathlib import Path
import json,os,sys,subprocess
root=Path.cwd();master=Path(Path('/tmp/route_a_master_path').read_text());dispatch=json.loads((master/'Isolated_U03_scout_dispatch.json').read_text());os.environ['ROUTE_A_REVISION_PLAN']=dispatch['plan'];os.environ['ROUTE_A_REVISION_MANIFEST']=dispatch['manifest'];sys.path.insert(0,str(root/'Scripts/routeA/diagnostic_transient/compute_revision_v3/measurement'))
from common import atomic,load,sha
cfg=load(Path(dispatch['plan']));scope=cfg['cpu_scope_name']
if os.environ.get('ROUTE_A_CPU_SCOPE')!=scope:
 log=(master/'Isolated_U03_scout_execution_scoped.log').open('xb');env=dict(os.environ,ROUTE_A_CPU_SCOPE=scope);p=subprocess.run(['systemd-run','--user','--scope','--quiet','--unit',scope.removesuffix('.scope'),'-p','CPUAccounting=yes',sys.executable,'-B',__file__],env=env,stdout=log,stderr=log,timeout=cfg['stages']['SCOUT']['budgets']['stage_wall_seconds']+8);log.close();sys.exit(p.returncode)
from scope_cpu import verify_scope
verify_scope(scope)
from runner import verify_authorization
out=Path(dispatch['output']);auth=Path(dispatch['authorization']);prior={'Q0_status':'PASS'};verify_authorization(auth,'SCOUT',out,prior)
atomic(master,'Isolated_U03_scout_permission_preflight.json',{'status':'PASS','scope':scope,'scope_cgroup':str(verify_scope(scope)),'plan_SHA256':sha(Path(dispatch['plan'])),'manifest_SHA256':sha(Path(dispatch['manifest'])),'master_based_authorization':True,'Q3_authorized':False})
atomic(master,'Isolated_U03_scout_scope.json',{'resource_only':True,'Q2_PASS_claim':False,'full_Q2_requires_Q1_PASS':True,'one_shot':True,'budgets':cfg['stages']['SCOUT']['budgets']})
from campaign import launch_campaign
r=launch_campaign(out,'SCOUT',auth,prior);atomic(master,'Isolated_U03_scout_result.json',{'output':str(out),'result':r});print(json.dumps({'status':r['status'],'STOP_reason':r['STOP_reason'],'completed_repeats':r['completed_repeats']}))
