import ast, csv, hashlib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
ROOT=Path.cwd(); OUT=ROOT/'results/routeA/attempts/attempt_005'; NEW=OUT/'B_coarse_symmetry_review'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'Scripts/routeA'))
from foam_fields import read_scalar,read_vector

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,d):
    p=Path(p);assert not p.exists(),p
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert head=='c0d84cac3bd8c01501c8ed4a41bdbeaa930fc0bd'
contract=load(ROOT/'docs/routeA_execution_contract_v1.4.json')
guards={'docs/routeA_execution_contract_v1.4.json':'2665b8a62211618ae531e7b8d42242e3d8f9ae469b95b634beab672c89b345d7',**contract['implementation_sha256'],**contract['template_source']['unchanged_template_sha256']}
protected={}; verification=[]
def check(base,entries,label):
    for rel,expected in entries.items():
        p=base/rel;assert p.is_file(),p
        actual=sha(p);assert actual==expected,(label,str(p),expected,actual)
        protected[str(p)]=actual
    verification.append({'category':label,'count':len(entries),'status':'PASS'})
check(ROOT,guards,'effective contract and implementations/templates/reference')
check(OUT,load(OUT/'attempt_sealed_sha256.json'),'original attempt 005 seal')
protected[str(OUT/'attempt_sealed_sha256.json')]=sha(OUT/'attempt_sealed_sha256.json')
report=load(OUT/'Ra1e4_trio_report.json'); group=load(OUT/'Ra1e4_group_evaluation.json')
assert report['overall']=='COMPLETE' and len(report['cases'])==3
for row in report['cases']:
    assert row['accepted'] and row['Gate_D']=='PASS'
    case=ROOT/'cases/routeA'/row['case_id']
    check(ROOT,{row['metrics_path']:row['metrics_sha256']},row['case_id']+' accepted metrics')
    for seg in row['segments']:
        folder=ROOT/seg['path'];check(folder,{'sealed_sha256.json':seg['sealed_sha256_manifest']},'segment seal '+str(folder))
        check(folder,load(folder/'sealed_sha256.json'),'segment artifacts '+str(folder))
    last=ROOT/row['segments'][-1]['path'];manifest=load(last/'segment_manifest.json')
    check(case/str(row['final_iteration']),manifest['final_field_validation']['field_sha256'],row['case_id']+' accepted native final fields')
    check(case,manifest['mesh_sha256'],row['case_id']+' mesh')
assert group['Gate_E_diagnostic']['status']=='PASS' and group['Gate_F']['status']=='FAIL' and group['Gate_G']['status']=='PASS'
w=group['Gate_F']['quantities']['Wmax'];assert not w['monotonic'] and w['p_obs'] is None and w['GCI_fine'] is None and w['needs_320']
full=load(ROOT/'results/routeB/full_matrix_manifest.json');hist=load(ROOT/'results/routeB/run_manifest.json');b=full['cases']['B-Ra1e4-coarse'];bh=hist['cases']['B-SMOKE'];case=Path(b['generated_manifest']['case_path']);m=load(b['metrics_path'])
assert b['source_case_id']=='B-SMOKE' and b['Gate_D']=='PASS' and b['generated_manifest']==bh['generated_manifest']
assert b['accepted_final_field_sha256']==bh['accepted_final_field_sha256']
assert b['generated_manifest']['grid']==[40,40,1] and b['generated_manifest']['Ra_actual']==10000 and m['final_iteration']==3000
master=list(csv.DictReader((ROOT/'results/routeB/routeB_master_matrix.csv').open()));mr=[x for x in master if x.get('case_id')=='B-Ra1e4-coarse'];assert len(mr)==1,mr
assert mr[0]['accepted']=='YES',mr
check(Path(b['accepted_field_hash_root']),b['accepted_final_field_sha256'],'B accepted final fields')
check(case,bh['mesh_sha256'],'B accepted mesh')
check(case,bh['log_sha256'],'B accepted logs/environment')
check(case,bh['executed_input_sha256'],'B accepted inputs')
for bid in ['B-Ra1e4-coarse','B-Ra1e4-medium','B-Ra1e4-fine']:
    br=full['cases'][bid];check(Path('/'),{br['metrics_path']:br['metrics_sha256']},bid+' canonical metrics')
for folder,pattern in [(ROOT/'docs','routeA_execution_contract*'),(ROOT/'reference','*'),(ROOT/'results/routeB','*'),(ROOT/'results/routeB/cases/B-SMOKE','*')]:
    for p in folder.glob(pattern):
        if p.is_file():protected[str(p)]=sha(p)
protected[str(ROOT/'Scripts/routeB/analyze_case.py')]=sha(ROOT/'Scripts/routeB/analyze_case.py')
log=(case/'log.buoyantBoussinesqSimpleFoam').read_text();meshlog=(case/'log.checkMesh').read_text();block=(case/'system/blockMeshDict').read_text()
assert 'Build  : 6-af7d7f427be7' in log and re.search(r'^Time = 3000$',log,re.M) and re.search(r'^End$',log,re.M)
assert 'Mesh OK.' in meshlog and '(40 40 1) simpleGrading (1 1 1)' in block
rows=list(csv.DictReader((OUT/'Ra1e4_routeA_vs_routeB.csv').open()))
missing=[x for x in rows if not x['B'] or not x['A']]
assert [(x['quantity'],json.loads(x['grid'])) for x in missing]==[('temperature_symmetry_L2',[40,40,1]),('velocity_symmetry_L2',[40,40,1])]
assert 'symmetry' not in m
before_path=NEW/'protected_before_sha256.json'
if before_path.exists():
    assert load(before_path)==protected
else:
    write(before_path,protected)
# Extract ONLY the frozen helper. Never execute the historical script's top-level runner.
source=(OUT/'group_evaluation.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='symmetry')
helper=ast.get_source_segment(source,node)
namespace={'np':np,'read_scalar':read_scalar,'read_vector':read_vector}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'group_evaluation.py'),'exec'),namespace)
derived=namespace['symmetry'](case,3000,b['generated_manifest'])
T=read_scalar(case/'3000/T',1600).reshape(40,40);U=read_vector(case/'3000/U',1600).reshape(40,40,3)[:,:,:2]
theta=(T-299.5);trms=float(np.sqrt(np.mean(theta**2)));urms=float(np.sqrt(np.mean(np.sum(U**2,axis=2))))
assert trms>1e-12 and urms>1e-12 and np.isfinite(T).all() and np.isfinite(U).all()
# Exact stored Route B canonical expressions provide an independent consistency check.
btheta=float(np.sqrt(np.mean((theta+theta[::-1,::-1]-1)**2))/max(trms,1e-30))
bvelocity=float(np.sqrt(np.mean(np.sum((U+U[::-1,::-1,:])**2,axis=2)))/max(urms,1e-30))
assert np.isclose(derived['theta_L2_relative'],btheta,rtol=1e-12,atol=0)
# Algebraic equivalence; check absolute floating-point roundoff, not a formal CFD tolerance.
velocity_roundoff_difference=abs(derived['velocity_L2_relative']-bvelocity)
assert velocity_roundoff_difference<=8*np.finfo(float).eps
proof={'classification':'PROVEN_ACCEPTED','formal_mapping':'B-Ra1e4-coarse -> B-SMOKE','accepted_master_row':mr[0],'final_iteration':3000,'Ra_actual':10000,'grid':[40,40,1],'case_path':str(case),'full_matrix_manifest_sha256':sha(ROOT/'results/routeB/full_matrix_manifest.json'),'historical_manifest_sha256':sha(ROOT/'results/routeB/run_manifest.json'),'accepted_hash_seal':b['accepted_final_field_sha256'],'mesh_sha256':bh['mesh_sha256'],'log_sha256':bh['log_sha256'],'mesh_evidence':bh['mesh'],'log_checks':'Foundation 6 build 6-af7d7f427be7, exact case path, Time=3000, End; all stored log hashes match','seal_interpretation':'Existing accepted field hashes in full_matrix_manifest and historical run_manifest are the final-state hash seal; no standalone segment seal is required or fabricated for this historical v6 run.','checks':verification}
write(NEW/'accepted_B_provenance.json',proof)
diag={'owner':'DERIVED_DIAGNOSTIC_FROM_EXISTING_ACCEPTED_B_FIELDS','formal_B_Gate_metric':False,'solver_executed':False,'native_results_modified':False,'source_provenance':'accepted_B_provenance.json','frozen_operator_contract':contract['continuity']['symmetry'],'helper_source_path':str(OUT/'group_evaluation.py'),'helper_source_sha256':sha(OUT/'group_evaluation.py'),'helper_function_sha256':hashlib.sha256(helper.encode()).hexdigest(),'helper_source':helper,'parser_sha256':sha(ROOT/'Scripts/routeA/foam_fields.py'),'canonical_B_operator_path':str(ROOT/'Scripts/routeB/analyze_case.py'),'canonical_B_operator_sha256':sha(ROOT/'Scripts/routeB/analyze_case.py'),'uniform_cell_pairing':'Frozen blockMesh 40x40x1, simpleGrading(1 1 1), checkMesh hash/1600 cells/constant volumes, canonical row-major field reshape; reverse both active axes','normalization_equivalence':'A floor 1e-12 on dimensionless velocity, B floor 1e-30 on physical velocity. Both inactive here; uniform scaling cancels. No new operator/threshold.','theta_RMS':trms,'physical_velocity_RMS_m_s':urms,'frozen_A_operator_result':derived,'canonical_B_expression_crosscheck':{'theta_L2_relative':btheta,'velocity_L2_relative':bvelocity},'velocity_crosscheck_absolute_roundoff_difference':velocity_roundoff_difference,'roundoff_check_note':'Absolute floating-point consistency check only (8 machine eps); no new formal diagnostic or AB threshold. Relative discrepancy is amplified by near cancellation in a ~1e-10 defect.','diagnostic_use_only':True}
write(NEW/'derived_symmetry.json',diag)
coverage=[]
for x in rows:
    y=dict(x);y['historical_status']=x['status'];y['historical_B']=x['B'];y['ownership']='EXISTING_CANONICAL_RESULT'
    if x in missing:
        key='theta_L2_relative' if x['quantity'].startswith('temperature') else 'velocity_L2_relative'
        y['B']=derived[key];y['status']='COMPLETE';y['ownership']=diag['owner'];y['signed_difference']=float(x['A'])-y['B'];y['absolute_difference']=abs(y['signed_difference']);y['relative_difference']=abs(y['signed_difference'])/abs(y['B']);y['diagnostic_only']=True
    y['coverage_status']='NOT_LIKE_FOR_LIKE' if x['comparison_class']=='NOT_LIKE_FOR_LIKE' else y['status']
    coverage.append(y)
write(NEW/'reviewed_comparison_coverage.json',coverage)
# The contracts include matrix-wide settings but the active next-attempt snapshot is Ra1e4 only.
assert contract['AB_comparison']['hard_AB_threshold'] is None
assert contract['Gate_F']['blocking'] is False and contract['Gate_G']['blocking'] is False
assert contract['attempt_policy']['next_attempt']['Ra_target']==10000
assert contract['execution']['first_unit']==['A-Ra1e4-coarse','A-Ra1e4-medium','A-Ra1e4-fine']
assert all(not (ROOT/'cases/routeA'/('A-Ra1e5-'+g)).exists() for g in ['coarse','medium','fine'])
status={'ROUTE_A_RA1E4_RESULT_REVIEW':'COMPLETE','RA1E4_TRIO_FORMAL_EXECUTION_STATUS':'COMPLETE','RA1E4_ACCEPTED_CASE_COUNT':3,'RA1E4_GATE_D':'PASS_ALL','RA1E4_GATE_E_DIAGNOSTIC':'PASS','RA1E4_GATE_F':'FAIL','RA1E4_GATE_F_FAILURE_REASON':'WMAX_NON_MONOTONIC','RA1E4_NEEDS_320':'YES','RA1E4_GATE_G':'PASS','A_B_ORIGINAL_COMPARISON_STATUS':'PARTIAL','A_B_PARTIAL_DIRECT_CAUSE':'B_COARSE_CANONICAL_TEMPERATURE_AND_VELOCITY_SYMMETRY_NOT_STORED','B_COARSE_SOURCE_CASE':'B-SMOKE','B_COARSE_ACCEPTED_BASELINE_VERIFIED':'YES','B_COARSE_FINAL_FIELDS_PROVENANCE':'PROVEN_ACCEPTED','B_COARSE_SYMMETRY_CAN_BE_DERIVED_FROM_EXISTING_EVIDENCE':'YES','B_COARSE_SYMMETRY_DERIVATION_PERFORMED':'YES','B_COARSE_TEMPERATURE_SYMMETRY':derived['theta_L2_relative'],'B_COARSE_VELOCITY_SYMMETRY':derived['velocity_L2_relative'],'B_COARSE_DERIVED_SYMMETRY_OWNERSHIP':diag['owner'],'ROUTE_B_FORMAL_STATUS_CHANGED':'NO','ROUTE_B_CANONICAL_METRICS_MODIFIED':'NO','A_B_PRIMARY_QOI_COMPARISON':'COMPLETE','A_B_CONSERVATION_COMPARISON':'NOT_LIKE_FOR_LIKE','A_B_SYMMETRY_COMPARISON':'COMPLETE','A_B_REVIEWED_OVERALL_STATUS':'COMPLETE','A_B_HARD_THRESHOLD_EXISTS':'NO','A_B_PARTIAL_BLOCKS_NEXT_RA':'NO','RA1E4_STEADY_TRIO_COMPLETE':'YES','RA1E4_STEADY_TRIO_CHARACTERIZED':'NO','FORMAL_CRITERIA_CHANGED':'NO','NUMERICAL_SETTINGS_CHANGED':'NO','PHYSICAL_MODEL_CHANGED':'NO','REFERENCE_DATA_CHANGED':'NO','A_RESULTS_CHANGED':'NO','B_RESULTS_CHANGED':'NO','ROUTE_A_SOLVER_EXECUTED':'NO','ROUTE_B_SOLVER_EXECUTED':'NO','CASE_GENERATED':'NO','MESH_GENERATED':'NO','CONTINUATION_EXECUTED':'NO','CONTRACT_AMENDMENT_CREATED':'NO','NEXT_EXECUTION_CONTRACT_UPDATE_REQUIRED':'YES','RA1E5_TRIO_TECHNICALLY_READY':'NO','NEXT_SINGLE_TASK':'PREPARE_ROUTE_A_RA1E5_EXECUTION_CONTRACT','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / medium','USER_DECISION_REQUIRED':'YES'}
after={p:sha(Path(p)) for p in protected};mismatches=[p for p in protected if protected[p]!=after[p]];assert not mismatches,mismatches
verification_result={'status':'PASS','protected_file_count':len(protected),'mismatches':mismatches,'original_attempt_seal_entries':48,'original_solver_segment_count':8,'before_manifest_sha256':sha(NEW/'protected_before_sha256.json'),'after_sha256':after}
write(NEW/'protected_after_check.json',verification_result)
review={'schema':'routeA-Ra1e4-result-review-v1','task':'REVIEW_ROUTE_A_RA1E4_RESULT','date':'2026-10-04','HEAD':head,'owner':'SEPARATE_RESULT_REVIEW_OF_ATTEMPT_005','effective_contract_sha256':guards['docs/routeA_execution_contract_v1.4.json'],'final_status':status,'A_B_OVERALL_COMPARISON':'COMPLETE','original_PARTIAL_classification':'Case B: only auxiliary coarse symmetry diagnostics absent; no missing primary QoIs','original_missing_rows':missing,'original_artifacts_unchanged':True,'accepted_A_cases':[{'case_id':x['case_id'],'final_iteration':x['final_iteration'],'accepted':x['accepted'],'Gate_D':x['Gate_D']} for x in report['cases']],'B_coarse_provenance':proof,'derived_diagnostic':diag,'coverage':coverage,'coverage_status_meaning':'COMPLETE means evidence coverage, not a Hard AB PASS. NOT_LIKE_FOR_LIKE rows retain values/metadata but prohibit direct numeric/Hard gaps.','conservation_summary':'Heat balance and reconstructed U divergence COMPLETE on all grids. Native mass-A / volume-B flux and reconstructed-A / corrected-phi-B section diagnostics NOT_LIKE_FOR_LIKE on all grids.','contract_review':{'AB_comparison':contract['AB_comparison'],'batch_stop_policy':contract['batch_stop_policy'],'Gate_F':contract['Gate_F'],'Gate_G':contract['Gate_G'],'comparison_completeness_hard_prerequisite_exists':False,'missing_symmetry_is_safety_evaluator_failure':False,'blocking_determination':'NO: accepted A trio and complete primary evidence; auxiliary comparison gaps are not an explicit batch STOP. No new blocking rule may be introduced.','historical_reporting_rule_correction':'group_evaluation.py line 114 imposed nextready=complete and ABstatus==COMPLETE without a v1.4 prerequisite. This review supersedes that interpretation only; historical report and script remain unchanged.'},'Gate_F_evidence':w,'Ra1e4_characterization':'Complete accepted trio, not fully characterized: Wmax non-monotonic leaves p/GCI undefined and needs_320 YES. No 320 execution.','Ra1e5_readiness':{'scientific_matrix_progression_not_blocked':True,'technical_model_and_evaluator_ready':True,'current_execution_snapshot_ready':False,'reason':'v1.4 execution.first_unit, attempt_policy.next_attempt (attempt_005/Ra_target=10000/Ra1e4 case_ids), next_single_task and final_status.NEXT_SINGLE_TASK explicitly target Ra1e4. Ra1e5 case_order/caps register general settings only. Need a separate next-execution snapshot; no scientific/AB policy amendment is needed by this review.','destination_directories_absent':True,'metadata_evidence':{'first_unit':contract['execution']['first_unit'],'next_attempt':contract['attempt_policy']['next_attempt'],'next_single_task':contract['next_single_task'],'final_status_next_single_task':contract['final_status']['NEXT_SINGLE_TASK']},'next_task':status['NEXT_SINGLE_TASK']},'protected_evidence':{'status':'PASS','file_count':len(protected),'path':str(NEW/'protected_after_check.json')},'git_add_commit_push_performed':False}
write(OUT/'Ra1e4_result_review.json',review)
lines=['# Ra1e4 result review — REVIEW_ROUTE_A_RA1E4_RESULT','',f'HEAD `{head}`。effective v1.4、analyzer、runtime checkerのhash guardはPASS。solver/continuation/case/mesh生成は全て未実行。','', 'Ra1e4 formal executionはCOMPLETE。coarse 3000、medium 6000、fine 15000で3/3 accepted、Gate D全PASS。Gate E diagnostic PASS、Gate F FAIL、needs_320 YES、Gate G PASSを保持。','', '元のA–B PARTIALの直接原因は、B-Ra1e4-coarse → B-SMOKEのcanonical metricsにtemperature/velocity symmetryが保存されていない2行のみ。Case B（補助diagnostic欠損）に該当し、主要QoIの欠損はない。元report/CSV/group/sealは不変。','', 'B coarseのT/Uを含むaccepted最終6場、mesh 5ファイル、入力12ファイル、solver/environment/mesh logs 4ファイルを既存manifestのSHA-256と照合。formal master accepted YES、Ra10000、40×40×1、final3000、Foundation6 buildおよびEndを確認。分類PROVEN_ACCEPTED。既存accepted field hash登録がfinal-state sealであり、独立segment sealを新規のhistorical証拠として発明していない。','', '既存凍結group_evaluation.pyのsymmetry関数だけをAST抽出して実行。uniform cell pairingと1e-12正規化を再利用。B canonical式の1e-30 floorは今回inactiveで、速度単位の定数倍は相殺されることをcrosscheck。Route B canonical metrics/Gate statusへ書き戻していない。','', f"導出値：temperature L2 `{derived['theta_L2_relative']:.17g}`、velocity L2 `{derived['velocity_L2_relative']:.17g}`。ownership `{diag['owner']}`。補助比較diagnosticに限定。",'', '| Quantity | 40² | 80² | 160² |','|---|---|---|---|']
for q in sorted({x['quantity'] for x in coverage}):
    ss=[next(x['coverage_status'] for x in coverage if x['quantity']==q and json.loads(x['grid'])[0]==n) for n in [40,80,160]]
    lines.append('| '+q+' | '+' | '.join(ss)+' |')
lines += ['', 'A_B_PRIMARY_QOI_COMPARISON=COMPLETE。Nu_halfは値が揃っているが離散operator差によりNOT_LIKE_FOR_LIKE。A_B_CONSERVATION_COMPARISON=NOT_LIKE_FOR_LIKE（熱収支とreconstructed U divergenceはCOMPLETE、native fluxとsectionはoperator/unit差を保持）。A_B_SYMMETRY_COMPARISON=COMPLETE。reviewed overall COMPLETEはcoverage完了を示し、全量Hard一致/PASSを意味しない。','', '`AB_comparison.hard_AB_threshold=null`。`unaligned_operator_comparison_allowed=false`、`operator_rule`は異なるoperator/unit/samplingについてLIKE_FOR_LIKE=NO、Hard比較禁止。missing/near-zero baselineはnull/ABSOLUTE_ONLY、区別不能ならNOT_EVALUATEDで値を発明しない。Gate F/Gはblocking=false。batch_stop_policyのSTOPは環境・入力・mesh・nonfinite・証拠破損・evaluator failure等で、A–B全量COMPLETEという明示的前提はない。','', 'A_B_PARTIAL_BLOCKS_NEXT_RA=NO。歴史group_evaluation.py line114のnextready=complete and ABstatus==COMPLETEはv1.4にない追加制約で、このreviewで解釈を訂正する。元artifactは変更しない。','', 'Wmaxはcoarse→medium→fineで非単調。fine–medium差が小さくてもp/GCI未定義、Gate F FAIL/needs_320 YESを保持。Ra1e4 steady trio COMPLETE=YES、CHARACTERIZED=NO。','', '科学的なmatrix進行と既存model/evaluatorは準備済み。ただしv1.4のexecution.first_unit、attempt_policy.next_attempt、next_single_task、final_status.NEXT_SINGLE_TASKはRa1e4/attempt005を明示している。全matrixのcase_order/capsだけでは新しいRa1e5 execution snapshotにならない。RA1E5_TRIO_TECHNICALLY_READY=NO（次実行snapshot未準備が理由）、NEXT_EXECUTION_CONTRACT_UPDATE_REQUIRED=YES。今回criteria/numerics/AB policyは変えず、Amendmentも作らない。','', '**NEXT_SINGLE_TASK=PREPARE_ROUTE_A_RA1E5_EXECUTION_CONTRACT**。推奨gpt-6.1-sol / medium。USER_DECISION_REQUIRED=YES。','', f'保護hash前後一致：{len(protected)}ファイル、original attempt seal 48 entries、solver segment seals 8件。reference/contracts/B formal status/A accepted fields不変。git add/commit/push未実行。','', '```text']
lines += [f'{k}={v}' for k,v in status.items()]+['```','']
p=OUT/'Ra1e4_result_review.md';assert not p.exists();p.write_text('\n'.join(lines))
write(NEW/'review_artifacts_sha256.json',{str(p.relative_to(ROOT)):sha(p) for p in [OUT/'Ra1e4_result_review.md',OUT/'Ra1e4_result_review.json',*sorted(NEW.glob('*.json')),NEW/'review_runner.py']})
print(json.dumps({'review':'COMPLETE','protected':len(protected),'derived':derived,'next_task':status['NEXT_SINGLE_TASK']},ensure_ascii=False))
