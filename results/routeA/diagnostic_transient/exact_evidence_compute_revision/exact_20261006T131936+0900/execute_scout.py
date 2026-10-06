from pathlib import Path
import json,os,sys,subprocess
master=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/exact_evidence_compute_revision/exact_20261006T131936+0900');cycle=int(sys.argv[1]);attempt=int(sys.argv[2]);dispatch=json.loads((master/f'Scout_dispatch_cycle_{cycle}_a{attempt}.json').read_text());os.environ['ROUTE_A_REVISION_PLAN']=dispatch['plan'];os.environ['ROUTE_A_REVISION_MANIFEST']=dispatch['manifest'];sys.path.insert(0,str(Path.cwd()/'Scripts/routeA/diagnostic_transient/compute_revision_v4/measurement'))
from common import atomic,load
cfg=load(Path(dispatch['plan']));scope=cfg['cpu_scope_name']
if os.environ.get('ROUTE_A_CPU_SCOPE')!=scope:
 log=(master/f'Scout_execution_cycle_{cycle}_a{attempt}.log').open('xb');env=dict(os.environ,ROUTE_A_CPU_SCOPE=scope);p=subprocess.run(['systemd-run','--user','--scope','--quiet','--unit',scope.removesuffix('.scope'),'-p','CPUAccounting=yes',sys.executable,'-B',__file__,str(cycle),str(attempt)],env=env,stdout=log,stderr=log,timeout=cfg['stages']['SCOUT']['budgets']['stage_wall_seconds']+8);log.close();sys.exit(p.returncode)
from campaign import launch_campaign
r=launch_campaign(Path(dispatch['output']),'SCOUT',Path(dispatch['authorization']),{'Q0_status':'PASS'});atomic(master,f'Scout_result_cycle_{cycle}_a{attempt}.json',{'output':dispatch['output'],'result':r});print(json.dumps({'status':r['status'],'STOP_reason':r['STOP_reason'],'completed_repeats':r['completed_repeats']}))
