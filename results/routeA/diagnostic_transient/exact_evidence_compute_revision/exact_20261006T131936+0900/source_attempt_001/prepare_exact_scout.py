"""Preregister a single 3-repeat non-CFD representative campaign; no retries."""
import copy,datetime,sys
from common import ROOT,HERE,REVISION_ROOT,CONTRACT,sha,load,atomic

def main(cycle):
 scope=load(REVISION_ROOT/'master_scope.json');cfg=load(REVISION_ROOT/'validation_plan.json')
 proofs=['reuse_unit_validation.json','revision_validation_cycle2.json','cross_revision_scientific_equivalence.json','native_array_cache_validation.json','historical_regression_reuse.json']
 for name in proofs:assert load(REVISION_ROOT/name)['status']=='PASS',name
 requests=[{'kind':'pipeline','mode':'ON','purpose':'primitive','sample_class':c,'phase':'scout_'+c,'context_kind':'RECURRING_STEP_EQUIVALENT','repeat':r} for c in ('controller','field','matrix','term','energy_matrix','pressure_matrix') for r in range(3)]
 requests += [{'kind':'pipeline','mode':'OFF','purpose':'primitive','sample_class':'pressure_matrix','phase':'scout_OFF','context_kind':'RECURRING_STEP_EQUIVALENT','repeat':r} for r in range(3)]
 # Retain baseline-derived bounds (76s/trial, 1627s/stage); improve compute,
 # never lower limits based on an unmeasured optimized path.
 b=copy.deepcopy(cfg['stages']['Q1']['budgets']);b.update(single_trial_wall_seconds=76,stage_wall_seconds=1627,scratch_bytes=2*2**30,files_max=192)
 cfg.update(schema='routeA_exact_evidence_scout_plan/4.0',task=scope['allowed'],HEAD=scope['HEAD'],execution_authorized=False,revision='compute_revision_v4',scout_requests=requests)
 cfg['stages']['SCOUT']={'budgets':b};cfg['cpu_scope_name']='route-a-exact-scout-'+REVISION_ROOT.name+'-c'+str(cycle)+'.scope'
 cfg['exact_evidence_architecture']={'cycle':cycle,'cache_lifetime':'callback','cache_key':'actual typed content + SHA + full byte equality + scientific epoch/callback sequence','cache_bound_per_process':128*2**20,'bulk_schema':None,'parallel_workers':1,'callback_batching':False,'async_backend':False}
 cfg['scout_preregistration']={'basis':'unchanged v3 bound derived from historical constructor/control/matrix sizes and uncertainty envelope','one_shot':True,'repeats':3,'automatic_extra_repeats':False,'existing_stability_rules_unchanged':True,'scratch_model':'21 two-packet source-shaped artifacts + bounded96MiB ledger (actual <=3records each) + complete compressed traces + 16MiB STOP +4MiB sidechannel;192file cap failclosed','files_model':'48 active workspace +24control+32archive+8STOP+8sidechannel <=192'}
 planpath=REVISION_ROOT/f'Scout_plan_cycle_{cycle}.json';atomic(REVISION_ROOT,planpath.name,cfg)
 manifest={'schema':'diagnostic_compute_revision/2','canonical_SHA256':sha(CONTRACT),'plan_SHA256':sha(planpath),'source_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.C','.H')},'artifact_SHA256':{str(p.relative_to(ROOT)):sha(p) for p in (REVISION_ROOT/'build').iterdir() if p.is_file()},'validation_SHA256':{str((REVISION_ROOT/n).relative_to(ROOT)):sha(REVISION_ROOT/n) for n in proofs},'original_46_tests':'PASS','revision_validation':'PASS','measurement_ready':{'SCOUT':True,'Q1':False,'Q2':False},'CFD_ready':False,'production_authorized':False}
 manifestpath=REVISION_ROOT/f'Scout_manifest_cycle_{cycle}.json';atomic(REVISION_ROOT,manifestpath.name,manifest)
 ident='scout_'+datetime.datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')+'_exact_c'+str(cycle);out=ROOT/'results/routeA/diagnostic_transient/timing_qualification'/ident
 auth={'schema':'nonCFD_revision_authorization/2','authorized_task':'AUTONOMOUSLY_REVISE_EXACT_EVIDENCE_COMPUTE_ARCHITECTURE_AND_ADVANCE_TO_Q3_READY','task_reference':scope['master_prompt'],'master_prompt_SHA256':scope['master_prompt_sha256'],'scope':'NONCFD_DIAGNOSTIC_COMPUTE_REVISION','allowed_stages':['SCOUT'],'execution_authorized':True,'canonical_SHA256':sha(CONTRACT),'plan_SHA256':sha(planpath),'harness_manifest_SHA256':sha(manifestpath),'qualification_id':ident}
 authpath=REVISION_ROOT/f'Scout_authorization_cycle_{cycle}.json';atomic(REVISION_ROOT,authpath.name,auth)
 atomic(REVISION_ROOT,f'Scout_dispatch_cycle_{cycle}.json',{'output':str(out),'authorization':str(authpath),'plan':str(planpath),'manifest':str(manifestpath)})
 print(out)
if __name__=='__main__':main(int(sys.argv[1]))
