from pathlib import Path
import json,os,sys,time
root=Path.cwd();master=Path('/tmp/route_a_master_path').read_text().strip();master=Path(master);dispatch=json.loads((master/'Scout_dispatch_cycle_1.json').read_text());os.environ['ROUTE_A_REVISION_PLAN']=dispatch['plan'];os.environ['ROUTE_A_REVISION_MANIFEST']=dispatch['manifest'];sys.path.insert(0,str(root/'Scripts/routeA/diagnostic_transient/compute_revision_v2/measurement'))
from common import atomic,load,sha
from runner import verify_authorization
out=Path(dispatch['output']);auth=Path(dispatch['authorization']);prior={'Q0_status':'PASS'};verify_authorization(auth,'SCOUT',out,prior)
neg=[]
for label,stage,p in [('CFD_forbidden','Q3',prior),('Q0_required','SCOUT',{'Q0_status':'FAIL'})]:
 try:verify_authorization(auth,stage,out,p)
 except ValueError as e:neg.append({'test':label,'status':'PASS','refusal':str(e)})
 else:raise RuntimeError('negative permission unexpectedly accepted')
b=load(auth);b['allowed_stages']=['Q2'];atomic(master,'negative_Q2_gate_authorization.json',b)
try:verify_authorization(master/'negative_Q2_gate_authorization.json','Q2',out,{'Q0_status':'PASS','Q1_status':'STOPPED'})
except ValueError as e:assert str(e)=='STOP_Q1_NOT_PASS';neg.append({'test':'Q2_Q1_PASS_gate','status':'PASS','refusal':str(e)})
else:raise RuntimeError('Q2 gate unexpectedly accepted')
atomic(master,'Scout_permission_preflight_cycle_1.json',{'status':'PASS','negative_tests':neg,'plan_SHA256':sha(Path(dispatch['plan'])),'harness_manifest_SHA256':sha(Path(dispatch['manifest'])),'scope':'NONCFD_RESOURCE_ONLY; never Q1 or Q2 PASS'})
rows=load(master/'Autonomous_Q3_readiness_progress.json');rows.append({'sequence':len(rows)+1,'task':'SCOUT_CYCLE_1_PREREGISTERED','input_HEAD':'53e81a3ccd2a621d31ff5c7cefdd4864a4db62f3','action':'C0 revision frozen/pinned; one-shot actual target 25600-cell scout: controller/field/term and 1/2/3 matrix packets plus OFF framework. New ID and immutable master-based authorization.','tests':'original46 PASS; fullgraph scientific/Writer equivalence PASS; 9 revision +2 additional +7 CPU bounds +6 tiny campaign trials PASS; new permission negatives PASS. Earlier fixture/declaration/verifier mistakes retained, corrected before target execution.','measurement':load(master/'microbench_001/result.json')['receiver_summary'],'decision':'Trial76s/stage563s derived from historical callback wall, source copy/matrix counts, microbench upper proxies and explicit margin; no doubling/retry.','next':'Run exactly preregistered scout once, then evaluate C0 and resource budget model.'});(master/'Autonomous_Q3_readiness_progress.json').write_text(json.dumps(rows,indent=2)+'\n')
with (master/'Autonomous_Q3_readiness_progress.md').open('a') as f:f.write('\n3. SCOUT_CYCLE_1_PREREGISTERED: original46 and additional revision validation PASS. All prior failed tiny attempts retained. One-shot target scout with immutable plan/auth/manifest, 76s per trial, 563s stage, seven trials. Q2 Q1-PASS prerequisite and Q3 refusal validated.\n')
from campaign import launch_campaign
result=launch_campaign(out,'SCOUT',auth,prior);atomic(master,'Scout_result_cycle_1.json',{'output':str(out),'result':result});print(json.dumps({'status':result['status'],'STOP_reason':result['STOP_reason'],'completed_repeats':result['completed_repeats']}))
