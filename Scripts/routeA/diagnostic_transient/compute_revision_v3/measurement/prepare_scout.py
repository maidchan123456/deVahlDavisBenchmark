"""One-shot actual-target scout preregistration under the master permission."""
import copy,datetime,json,math,statistics
from common import ROOT,HERE,REVISION_ROOT,PREP,CONTRACT,sha,load,atomic
from durable import MAX_BYTES

def main():
 scope=load(REVISION_ROOT/'master_scope.json');cfg=load(REVISION_ROOT/'validation_plan.json');micro=load(REVISION_ROOT/'microbench_001/result.json')
 proof_paths=['original_46_regression.json','revision_validation_cycle2.json','additional_validation_cycle2.json','bounds_validation_cycle2.json','tiny_campaign_validation_cycle2.json','microbench_001/result.json','codec_equivalence_cycle2.json','scope_CPU_validation_cycle2.json','cross_revision_scientific_equivalence_cycle2.json']
 for name in proof_paths:
  r=load(REVISION_ROOT/name);assert r.get('status') in ('PASS','PASS_ALL_TESTS'),(name,r.get('status'))
 # Historical observed constructor/control include the slow receive and are
 # conservative workload anchors. Matrix arrays are unmeasured; reserve up to
 # two state copies + three matrix slots, then a factor2 uncertainty margin.
 receiver_upper=max(x['wall_seconds'] for x in micro['rows'] if x['kind']=='receiver' and not x['legacy'] and x['bytes']==512*1024)*(32*2**20/(512*1024))
 observer_upper=max(x['observer_commit_seconds'] or 0 for x in micro['rows'] if x['kind']=='observer')
 trial=math.ceil(2*(7.445911754973*2+6.482728749*3+2*receiver_upper+2*observer_upper+2.164647629+1))
 classes=('controller','field','matrix','term','energy_matrix','pressure_matrix')
 requests=[{'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':c,'phase':'scout_'+c,'context_kind':'RECURRING_STEP_EQUIVALENT','repeat':0} for c in classes]
 requests=[dict(r,repeat=repeat) for r in requests for repeat in range(3)]
 requests+=[{'kind':'pipeline','mode':'OFF','purpose':'primitive','sample_class':'pressure_matrix','phase':'scout_OFF','context_kind':'RECURRING_STEP_EQUIVALENT','repeat':repeat} for repeat in range(3)]
 stage=trial*len(requests)+math.ceil(2*7.445911754973+16)
 b=copy.deepcopy(cfg['stages']['Q1']['budgets']);b.update(single_trial_wall_seconds=trial,stage_wall_seconds=stage,scratch_bytes=2*2**30,files_max=192)
 cfg.update(schema='routeA_timing_scout_plan/2.0',task='NONCFD_RECEIVER_SCOUT',HEAD='53e81a3ccd2a621d31ff5c7cefdd4864a4db62f3',execution_authorized=False,revision='compute_revision_v3',scout_requests=requests)
 cfg['stages']['SCOUT']={'budgets':b};cfg['cpu_scope_name']='route-a-target-scout-cycle2-v3.scope';cfg['scout_preregistration']={'basis':'historical maximum constructor/control callback wall, source state-copy and 3-matrix shape, measured C0 32MiB receive envelope, observer micro max, measured startup setup, factor2 unmeasured-matrix margin','historical_anchor_seconds':7.445911754973,'receiver_32MiB_upper_proxy_seconds':receiver_upper,'observer_max_seconds':observer_upper,'trial_wall_formula':'ceil(2*(2*constructor + 3*control + 2*receiver32MiB + 2*observer + setup + cleanup))','single_trial_wall_seconds':trial,'stage_wall_seconds':stage,'scientific_graph_unchanged':True,'replays_full_step':False,'Q1_or_Q2_PASS_claim_allowed':False,'one_shot':True,'STOP_reserve_bytes':16*2**20,'sidechannel_reserve_bytes':4*2**20,'ledger_bound_per_trial_bytes':MAX_BYTES,'scratch_model':'21 two-packet artifacts at source shapes + bounded ledgers + complete compressed traces + STOP; 2GiB finite quota guards fail closed','files_model':'48 active trial workspace + 24 control + 32 archive chunks + STOP8 + sidechannel8 <=192','implementation_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.C','.H')}}
 atomic(REVISION_ROOT,'Scout_plan_cycle_2.json',cfg)
 manifest={'schema':'diagnostic_compute_revision/2','canonical_SHA256':sha(CONTRACT),'plan_SHA256':sha(REVISION_ROOT/'Scout_plan_cycle_2.json'),'source_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.C','.H')},'artifact_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in (REVISION_ROOT/'build_cycle2_codec').iterdir() if p.is_file()},'validation_SHA256':{str((REVISION_ROOT/name).relative_to(ROOT)):sha(REVISION_ROOT/name) for name in proof_paths},'original_46_tests':'PASS','revision_validation':'PASS','measurement_ready':{'SCOUT':True,'Q1':False,'Q2':False},'CFD_ready':False,'production_authorized':False}
 atomic(REVISION_ROOT,'Scout_harness_manifest_cycle_2.json',manifest)
 ident='scout_'+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y%m%dT%H%M%S%z')+'_cycle2';out=ROOT/'results/routeA/diagnostic_transient/timing_qualification'/ident
 auth={'schema':'nonCFD_revision_authorization/2','authorized_task':'AUTONOMOUSLY_ADVANCE_ROUTE_A_DIAGNOSTIC_TRANSIENT_TO_Q3_READY','task_reference':scope['master_prompt'],'master_prompt_SHA256':scope['master_prompt_sha256'],'scope':'NONCFD_DIAGNOSTIC_COMPUTE_REVISION','allowed_stages':['SCOUT'],'execution_authorized':True,'canonical_SHA256':sha(CONTRACT),'plan_SHA256':sha(REVISION_ROOT/'Scout_plan_cycle_2.json'),'harness_manifest_SHA256':sha(REVISION_ROOT/'Scout_harness_manifest_cycle_2.json'),'qualification_id':ident}
 atomic(REVISION_ROOT,'Scout_authorization_cycle_2.json',auth);atomic(REVISION_ROOT,'Scout_dispatch_cycle_2.json',{'output':str(out),'authorization':str(REVISION_ROOT/'Scout_authorization_cycle_2.json'),'plan':str(REVISION_ROOT/'Scout_plan_cycle_2.json'),'manifest':str(REVISION_ROOT/'Scout_harness_manifest_cycle_2.json')});print(json.dumps({'output':str(out),'trial_wall_seconds':trial,'stage_wall_seconds':stage}))
if __name__=='__main__':main()
