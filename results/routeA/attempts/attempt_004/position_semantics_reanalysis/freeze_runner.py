import copy,csv,hashlib,json
from pathlib import Path
R=Path.cwd();B=R/'results/routeA/attempts/attempt_004';O=B/'position_semantics_reanalysis'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
 p=Path(p);assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def write(p,s):
 p=Path(p);assert not p.exists(),p;p.write_text(s)
parentpath=R/'docs/routeA_execution_contract_v1.3.json';P=sha(parentpath);OLD='e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac';NEW=sha(R/'Scripts/routeA/analyze_case.py');old=json.loads(parentpath.read_text())
assert P=='227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1'
assert sha(O/'source_before/analyze_case_before.py')==OLD
check=json.loads((O/'comparison_semantics_check.json').read_text());assert check['status']=='PASS'
protected=json.loads((O/'protected_before_sha256.json').read_text())
for p,h in protected.items():assert sha(R/p)==h,p
# Existing A-B position rows are already absolute-coordinate differences.
rows=list(csv.DictReader((B/'Ra1e3_routeA_vs_routeB.csv').open()))
for row in rows:
 if row['quantity'] in ['Umax_Z','Wmax_X','Nu_hot_local_max_Z','Nu_hot_local_min_Z']:
  assert float(row['absolute_position_difference'])==abs(float(row['A'])-float(row['B']))
checks={'status':'PASS','count':15,'unit_command':"PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=Scripts/routeA python3 -m unittest discover -s Scripts/routeA -p 'test_paper*.py' -v",'log_path':str((O/'unit_tests.log').relative_to(R)),'log_sha256':sha(O/'unit_tests.log'),'seven_required_position_scalar_tests':'PASS','unknown_suffix_does_not_imply_position':'PASS','numerical_helper_regression':'PASS','numerical_helper_outputs_exactly_identical':True,'unrelated_analyzer_AST_identical':True,'prior_order_tests_preserved_except_obsolete_suffix_dispatch_expectation':True}
changes={k:False for k in ['formal_criteria_changed','numerical_settings_changed','physical_model_changed','reference_data_changed','solver_results_changed','historical_statuses_changed','solver_executed','primary_solver_executed','continuation_executed','case_generated','mesh_generated','Route_B_modified']}
parent={'version':'1.3','path':'docs/routeA_execution_contract_v1.3.json','sha256':P,'unchanged':True}
req=Path('/home/mirai/.codex/attachments/2a7a53d9-ca02-4f29-88c6-13f9e8e42aac/貼り付けたテキスト.txt')
amend={'schema':'routeA-execution-contract-amendment-v1','id':'Route A Execution Contract Amendment 004','date':'2026-10-04','timezone':'Asia/Tokyo','observed_HEAD':'922c45ff5b179eead8058045757f07d71cfb17fd','parent_contract':parent,'effective_version':'1.4','effective_path':'docs/routeA_execution_contract_v1.4.json','issue_class':'PAPER_COMPARISON_POSITION_SEMANTICS_BUG','direct_cause':'canonical paper comparison classified position quantities using key.endswith("_Z"), causing Wmax_X to receive scalar-relative semantics','affected_file':'Scripts/routeA/analyze_case.py','old_analyzer_sha256':OLD,'new_analyzer_sha256':NEW,'exact_behavioral_change':{'scope':'PAPER_POSITION_CLASSIFICATION_ONLY','position_keys':['Umax_Z','Wmax_X','Nu_hot_local_max_Z','Nu_hot_local_min_Z'],'classification':'key in POSITION_KEYS; explicit frozenset; suffix alone is not a position rule','position_payload':['calculated','reference','signed_position_difference','absolute_position_error','error (signed position difference)','error_legacy_semantics'],'scalar_payload':['calculated','reference','signed_relative_difference','absolute_relative_error','error (signed relative difference)','error_legacy_semantics'],'Wmax_X_relative_fields_absent':True,'paper_difference_formula_unchanged':True,'Nu_bar_1_special_handling_unchanged':True,'unchanged_helpers':['paper_nusselt','local_quartic_extremum','sample_extrema','evaluate_gate_d_monitors','parse_residuals','classify_health_lines','paper_difference']},'unit_and_regression_tests':checks,'read_only_reanalysis':{'owner':check['owner'],'status':'PASS','path':str(O.relative_to(R)),'check_path':str((O/'comparison_semantics_check.json').relative_to(R)),'check_sha256':sha(O/'comparison_semantics_check.json'),'all_12_QoIs_exactly_unchanged':True,'all_other_metrics_exactly_unchanged':True,'Wmax_X_payload_before_after':check['cases'][2]['Wmax_X_before']|{'after':check['cases'][2]['Wmax_X_after']},'Gate_D_unchanged':True,'Gate_E_unchanged':True,'Gate_F_unchanged':True,'Gate_G_unchanged':True,'Gate_D':['PASS','PASS','PASS'],'Gate_E_diagnostic':'PASS','Gate_F':'FAIL','needs_320':'YES','Gate_G':'PASS','A_B_position_csv_consistency':'PASS','A_B_comparison_changed':False},'changes':changes,'protected_evidence':{'path':str((O/'protected_before_sha256.json').relative_to(R)),'sha256':sha(O/'protected_before_sha256.json'),'hash_entry_count':len(protected),'before_after_status':'PASS','authorized_source_edits':['Scripts/routeA/analyze_case.py','Scripts/routeA/test_paper_comparison_order.py'],'new_artifacts_only_in_addition_to_source_edits':True},'user_authorization':{'task':'FIX_ROUTE_A_PAPER_POSITION_SEMANTICS','attachment':str(req),'attachment_sha256':sha(req),'explicit_scope':'Position classification fix, tests, solver-free accepted Ra1e3 reanalysis, Amendment 004/effective v1.4 and Ra1e4 readiness; no solver execution.'}}
amendpath=R/'docs/routeA_execution_contract_amendment_004.json';dump(amendpath,amend);AH=sha(amendpath)
c=copy.deepcopy(old);c['version']='1.4';c['observed_HEAD']=amend['observed_HEAD'];c['historical_v1_3_amendment']=c['amendment'];c['historical_v1_3_evaluator_change']=c['evaluator_change'];c['historical_v1_3_attempt_policy']=c['attempt_policy']
entry={'id':amend['id'],'path':str(amendpath.relative_to(R)),'sha256':AH,'parent':{k:parent[k] for k in ['version','path','sha256']},'snapshot_rule':'v1.0 + Amendments 001–004; only explicit paper position classification and necessary version/ownership/next-trio metadata change; numerical contract identical.'}
c['amendment']=entry;c['amendment_chain'].append(entry);c['implementation_sha256']['Scripts/routeA/analyze_case.py']=NEW
c['contract_hash'].update(authoritative_file='docs/routeA_execution_contract_v1.4.json',expected_digest_location='docs/routeA_execution_contract_v1.4.md; external to JSON',start_guard='Before authorized Ra1e4 execution, verify effective v1.4 digest, all implementation/template/caps/reference and immutable parent/amendment hashes, accepted Ra1e3 historical evidence and position-semantics reanalysis linkage. Any mismatch STOP. v1.3 is immutable history and cannot authorize current execution.')
c['evaluator_change']={'file':'Scripts/routeA/analyze_case.py','previous_sha256':OLD,'new_sha256':NEW,'evaluation_version':'routeA-paper-position-amendment-004','numerical_evaluation_version_unchanged':'routeA-gateD-contract-v1.0','behavior':amend['exact_behavioral_change'],'physical_or_numerical_inputs_changed':False,'historical_results_or_script_hashes_in_old_manifests_updated':False}
c['paper_comparison_position_semantics']=amend['exact_behavioral_change']
c['position_semantics_reassessment']=amend['read_only_reanalysis']
c['position_semantics_tests']=checks
c['current_protected_evidence']=amend['protected_evidence']
nextids=['A-Ra1e4-'+n for n in ['coarse','medium','fine']]
assert all(not (R/'cases/routeA'/cid).exists() for cid in nextids)
c['execution']['first_unit']=nextids
c['attempt_policy']['attempt_004']={'status':'COMPLETE','root':'results/routeA/attempts/attempt_004/','accepted_case_count':3,'Gate_D':['PASS','PASS','PASS'],'Gate_E_diagnostic':'PASS','Gate_F':'FAIL','needs_320':'YES','Gate_G':'PASS','historical_artifacts_unchanged':True,'reanalysis_owner':check['owner'],'reanalysis_is_separate_from_historical_execution':True}
c['attempt_policy']['next_attempt']={'id':'attempt_005','status':'NOT_STARTED','batch_artifact_root':'results/routeA/attempts/attempt_005/','case_ids':nextids,'Ra_target':10000,'grids':[[40,40,1],[80,80,1],[160,160,1]],'requires_new_user_run_instruction':True,'formal_case_destinations_absent':True,'destination_state':{cid:'Absent; generate new only in authorized Ra1e4 task' for cid in nextids},'coarse_reuse':{'allowed':False,'reason':'Ra1e3 reuse policy is historical and does not authorize Ra1e4 reuse'},'batch_filenames':['Ra1e4_trio_report.md','Ra1e4_trio_report.json','Ra1e4_trio_matrix.csv','Ra1e4_routeA_vs_routeB.csv'],'historical_batch_paths_must_not_be_overwritten':True}
c['historical_v1_3_registered_coarse_reuse']=c['case_generation']['registered_coarse_reuse']
c['case_generation']['registered_coarse_reuse']={'allowed_for_Ra1e4':False,'Ra1e3_policy_historical':True}
c['case_generation']['reject']='Reject unexpected existing Ra1e4 formal destinations; do not overwrite/delete/regenerate historical cases. No Ra1e4 registered reuse exception.'
c['case_generation']['analysis_command']='Use current canonical analyzer with exact segment-start and sealed solver-log; v1.4 position semantics required.'
c['authority'].update(solver_executed=False,solver_authorized_in_this_task=False,user_decision_required_to_run=True,first_trio_technically_ready=True)
c['supersedes']['current_execution_guard']='v1.4 supersedes v1.3 only as current guard; previous contracts/results/statuses retained unchanged.'
c['final_status'].update(EFFECTIVE_CONTRACT_VERSION='1.4',FIRST_SOLVER_UNIT=','.join(nextids),FIRST_SOLVER_UNIT_TECHNICALLY_READY='YES',NEXT_SINGLE_TASK='RUN_ROUTE_A_RA1E4_TRIO',USER_DECISION_REQUIRED='YES',FORMAL_CRITERIA_CHANGED='NO')
# Prove scientific/numerical blocks and all other implementation hashes are unchanged.
blocks=['frozen_model','template_source','monitor','Gate_D','statuses','batch_stop_policy','Gate_F','Gate_G','continuity','energy_diagnostics','AB_comparison']
for k in blocks:assert c[k]==old[k],k
execution=copy.deepcopy(c['execution']);execution['first_unit']=old['execution']['first_unit'];assert execution==old['execution']
for p,h in old['implementation_sha256'].items():assert c['implementation_sha256'][p]==(NEW if p=='Scripts/routeA/analyze_case.py' else h)
contractpath=R/'docs/routeA_execution_contract_v1.4.json';dump(contractpath,c);CH=sha(contractpath)
write(R/'docs/routeA_execution_contract_amendment_004.md',f'''# Route A Execution Contract Amendment 004

2026-10-04（Asia/Tokyo）。parent v1.3 SHA-256 `{P}`。ユーザーtask FIX_ROUTE_A_PAPER_POSITION_SEMANTICSに基づく位置分類だけの修正。

原因はcanonical paper comparisonの`key.endswith("_Z")`。Wmax_Xがscalar-relative payloadになっていた。4つの明示POSITION_KEYS（Umax_Z、Wmax_X、Nu_hot_local_max_Z、Nu_hot_local_min_Z）へのmembershipへ変更し、paper_differenceの数式・scalar semantics・Nu_bar_1 handlingは維持。

analyzer old `{OLD}` → new `{NEW}`。15 tests PASS。7 helperの出力が完全一致し、分類変更を正規化した全ASTも一致。従来order testのobsolete suffix assertionだけを更新、旧source/testを別所有artifactへ保存。

3ケースをnative fields/log/monitor read-onlyでcanonical再解析。12 QoIと全非paper metrics、Gate D monitor、Wmax_X以外のpaper payloadが完全一致。Wmax_X calculated/referenceは不変、signed_position_difference/absolute_position_errorへ変更しrelative fieldsなし。Gate D各PASS、Gate E診断PASS、Gate F FAIL・needs_320 YES、Gate G PASSを保持。attempt 004の既存報告・CSV・sealは上書きなし。

Gate Eは元からabsolute coordinate differenceでPASS。基準・numerics・physics・reference・solver results・historical status変更なし。solver/continuation/case/mesh生成なし。全{len(protected)}既存保護ファイルのhash不変。Route Bはread-only、既存A–B位置差CSVの整合PASS。

詳細とuser authorizationは[amendment JSON](routeA_execution_contract_amendment_004.json)。別所有再解析は[comparison check](../results/routeA/attempts/attempt_004/position_semantics_reanalysis/comparison_semantics_check.json)。effective v1.4は[JSON](routeA_execution_contract_v1.4.json)と[MD](routeA_execution_contract_v1.4.md)。Ra1e4実行には新しいユーザー指示が必要。
''')
write(R/'docs/routeA_execution_contract_v1.4.md',f'''# Route A execution contract v1.4

2026-10-04（Asia/Tokyo）。**FROZEN / Ra1e4 trio technically ready YES**。v1.0 + Amendments 001/002/003/004のfull effective snapshot。sole current guardは[JSON](routeA_execution_contract_v1.4.json)。旧versionはhistoricalとして不変。

```text
EFFECTIVE_CONTRACT_VERSION = 1.4
EFFECTIVE_CONTRACT_SHA256 = {CH}
ANALYZER_SHA256 = {NEW}
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
PARENT_V1_3_SHA256 = {P}
AMENDMENT_004_JSON_SHA256 = {AH}
```

自己参照を避けJSON digestは本書に保存。実行前に全implementation/template/caps/reference、immutable parent/amendment chainと保存済みRa1e3/reanalysis証拠を照合。不一致ならSTOP。

唯一のanalyzer behavior変更はpaper position/scalar classification。POSITION_KEYSはUmax_Z/Wmax_X/Nu_hot_local_max_Z/Nu_hot_local_min_Z。他のscalarはrelative semantics。paper_difference自体、4097点速度、quartic local Nu、全QoI、Gate D/E/F/G基準は不変。

initial/continuation/cap=3000/3000/30000、Rwin≤5e-4、Ux/Uy/e/p_rgh最終Initial residual≤1e-7、inclusive 200 window、元decimal Qのexact rational OLS slope≤0を維持。physics・scheme・relaxation・correctorsはparentと一致。F/G FAILはNON_BLOCKING_WITH_DOCUMENTED_LIMITATION、automatic tuning/retry/320/post-cap extensionは禁止。

Ra1e3 attempt 004はCOMPLETE/accepted3、D各PASS/E診断PASS/F FAIL・needs_320 YES/G PASSをhistoricalとして保存。別所有POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIOにcorrected paper payloadを保存。既存report/json/csv/solver sealは不変。

次回task RUN_ROUTE_A_RA1E4_TRIO。新規formal A-Ra1e4-coarse→medium→fine、40²/80²/160²、Ra=10000、Pr=.71、concurrency=1。各caseでinput/hash→blockMesh→checkMesh→initialization/runtime/OQ-02/Gate A→primary。Ra1e3 coarse reuseはRa1e4には適用しない。予定batch root attempt_005はNOT_STARTED。今回はsolverなしで終了し、次のユーザー実行指示を待つ。

詳細は[Amendment 004](routeA_execution_contract_amendment_004.md)。
''')
meta={'new_analyzer_sha256':NEW,'effective_contract_sha256':CH,'amendment_004_sha256':AH,'parent_sha256':P,'numeric_blocks_identical':blocks,'execution_identical_except_next_first_unit_metadata':True,'protected_hash_entries':len(protected)}
dump(O/'freeze_verification.json',meta)
print(json.dumps(meta,indent=2))
