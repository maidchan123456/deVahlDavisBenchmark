from pathlib import Path
import json,os,sys,subprocess
root=Path.cwd();master=Path(Path('/tmp/route_a_master_path').read_text());dispatch=json.loads((master/'Scout_dispatch_cycle_2.json').read_text());os.environ['ROUTE_A_REVISION_PLAN']=dispatch['plan'];os.environ['ROUTE_A_REVISION_MANIFEST']=dispatch['manifest'];sys.path.insert(0,str(root/'Scripts/routeA/diagnostic_transient/compute_revision_v3/measurement'))
from common import atomic,load,sha
cfg=load(Path(dispatch['plan']));scope=cfg['cpu_scope_name']
if os.environ.get('ROUTE_A_CPU_SCOPE')!=scope:
 log=(master/'Scout_execution_scoped_cycle_2.log').open('xb');env=dict(os.environ,ROUTE_A_CPU_SCOPE=scope);p=subprocess.run(['systemd-run','--user','--scope','--quiet','--unit',scope.removesuffix('.scope'),'-p','CPUAccounting=yes',sys.executable,'-B',__file__],env=env,stdout=log,stderr=log,timeout=cfg['stages']['SCOUT']['budgets']['stage_wall_seconds']+8);log.close();sys.exit(p.returncode)
from scope_cpu import verify_scope
verify_scope(scope)
from runner import verify_authorization
out=Path(dispatch['output']);auth=Path(dispatch['authorization']);prior={'Q0_status':'PASS'};verify_authorization(auth,'SCOUT',out,prior)
atomic(master,'Scout_permission_preflight_cycle_2.json',{'status':'PASS','scope':scope,'scope_cgroup':str(verify_scope(scope)),'plan_SHA256':sha(Path(dispatch['plan'])),'manifest_SHA256':sha(Path(dispatch['manifest'])),'master_based_authorization':True,'Q3_authorized':False})
rows=load(master/'Autonomous_Q3_readiness_progress.json');rows.append({'sequence':len(rows)+1,'task':'SCOUT_CYCLE_2_PREREGISTERED','input_HEAD':'53e81a3ccd2a621d31ff5c7cefdd4864a4db62f3','action':'New v3 C0+exact codec optimization, dedicated cgroup CPU counter, lossless trace, durable ledger frozen. New one-shot scout with 3 repeats of six classes and OFF.','tests':'original46 PASS reused unchanged historical sources; cycle2 9 fullgraph/receiver/observer +2 kill/permission +7 bounds tests PASS; 6 nested tiny scoped trials all host STABLE; controlled short child/external scope test PASS; native JSON2000 +RAP13 310 fixtures exact; crossrevision1145/701 Writer hashes and backend results exact.','measurement':load(master/'scope_CPU_validation_cycle2.json')['query_wall_max_seconds'],'decision':'Freeze new sources/plan; keep76s cap derived from source/micro/historical model, stage1627s for21 trials. No retry of cycle1.','next':'Execute21 registered trials, then evaluate feasibility and Q1 full protocol.'});(master/'Autonomous_Q3_readiness_progress.json').write_text(json.dumps(rows,indent=2)+'\n')
with (master/'Autonomous_Q3_readiness_progress.md').open('a') as f:f.write('\n5. SCOUT_CYCLE_2_PREREGISTERED: new v3 namespace, exact byte/evidence equivalence PASS; tiny dedicated-scope host STABLE. New21-trial scout (3 repeats per class/OFF), 76s/trial,1627s/stage, same10% rule.\n')
from campaign import launch_campaign
r=launch_campaign(out,'SCOUT',auth,prior);atomic(master,'Scout_result_cycle_2.json',{'output':str(out),'result':r});print(json.dumps({'status':r['status'],'STOP_reason':r['STOP_reason'],'completed_repeats':r['completed_repeats']}))
