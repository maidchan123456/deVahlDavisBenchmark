import hashlib,json,shutil
from pathlib import Path
R=Path.cwd();B=R/'results/routeA/attempts/attempt_004';O=B/'position_semantics_reanalysis'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
 p=Path(p);assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
f=json.loads((O/'freeze_verification.json').read_text());c=json.loads((O/'comparison_semantics_check.json').read_text());p=f['parent_sha256'];old='e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac'
s={'ROUTE_A_PAPER_POSITION_SEMANTICS_REVIEW':'COMPLETE','ISSUE_CLASS':'PAPER_COMPARISON_POSITION_SEMANTICS_BUG','DIRECT_CAUSE':'key.endswith("_Z") misclassified Wmax_X as scalar-relative','ANALYZER_FIX_APPLIED':'YES','ANALYZER_FIX_SCOPE':'PAPER_POSITION_CLASSIFICATION_ONLY','OLD_ANALYZER_SHA256':old,'NEW_ANALYZER_SHA256':f['new_analyzer_sha256'],'POSITION_KEYS_EXPLICITLY_DEFINED':'YES','WMAX_X_POSITION_TEST':'PASS','UMAX_Z_POSITION_TEST':'PASS','LOCAL_NU_POSITION_TESTS':'PASS','SCALAR_RELATIVE_SEMANTICS_TEST':'PASS','NUMERICAL_HELPER_REGRESSION':'PASS','RA1E3_READ_ONLY_REANALYSIS':'PASS','RA1E3_QOIS_UNCHANGED':'YES','WMAX_X_CANONICAL_POSITION_SEMANTICS':'PASS','RA1E3_GATE_D_STATUSES_UNCHANGED':'YES','RA1E3_GATE_E_DIAGNOSTIC':'PASS','RA1E3_GATE_E_STATUS_CHANGED':'NO','RA1E3_GATE_F':'FAIL','RA1E3_GATE_G':'PASS','RA1E3_NEEDS_320':'YES','CONTRACT_AMENDMENT_004_CREATED':'YES','PARENT_EFFECTIVE_CONTRACT_VERSION':'1.3','PARENT_EFFECTIVE_CONTRACT_SHA256':p,'EFFECTIVE_CONTRACT_VERSION':'1.4','EFFECTIVE_CONTRACT_SHA256':f['effective_contract_sha256'],'FORMAL_CRITERIA_CHANGED':'NO','NUMERICAL_SETTINGS_CHANGED':'NO','PHYSICAL_MODEL_CHANGED':'NO','REFERENCE_DATA_CHANGED':'NO','SOLVER_RESULTS_CHANGED':'NO','ATTEMPT_004_HISTORY_PRESERVED':'YES','PRIMARY_SOLVER_EXECUTED':'NO','CONTINUATION_EXECUTED':'NO','CASE_GENERATED':'NO','MESH_GENERATED':'NO','RA1E4_TRIO_TECHNICALLY_READY':'YES','NEXT_SINGLE_TASK':'RUN_ROUTE_A_RA1E4_TRIO','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / medium','USER_DECISION_REQUIRED':'YES'}
review={'task':'FIX_ROUTE_A_PAPER_POSITION_SEMANTICS','status':'COMPLETE','date':'2026-10-04','timezone':'Asia/Tokyo','observed_HEAD':'922c45ff5b179eead8058045757f07d71cfb17fd','issue_class':s['ISSUE_CLASS'],'direct_cause':s['DIRECT_CAUSE'],'fix_scope':s['ANALYZER_FIX_SCOPE'],'source_change':'Explicit frozenset POSITION_KEYS and key membership in canonical paper comparison; paper_difference unchanged','test_results':{'status':'PASS','count':15,'log_path':str((O/'unit_tests.log').relative_to(R)),'helper_regression':'Exact before/after outputs for all seven specified helpers; only classification differs in normalized AST'},'read_only_reanalysis':c,'contract_freeze':f,'history_preservation':{'status':'PASS','protected_files':f['protected_hash_entries'],'baseline_path':str((O/'protected_before_sha256.json').relative_to(R)),'historical_attempt_004_files_not_overwritten':True,'historical_Gate_E_F_G_statuses_unchanged':True,'A_B_CSV_unchanged':True},'isolation_harness_repair':{'first_try':'Output-isolated ROOT required reference CSV under that ROOT for relative_to; no analyzer numerical failure','correction':'Byte-identical canonical reference copied into new analysis workspace','failed_output_preserved':'position_semantics_reanalysis/isolation_attempt_001_failed/','original_CFD_inputs_outputs_changed':False},'next_execution':{'technically_ready':True,'task':'RUN_ROUTE_A_RA1E4_TRIO','authorized_now':False,'formal_destinations_absent':True,'planned_attempt':'005'},'final_status':s,'git_add_commit_push_performed':False}
dump(B/'paper_position_semantics_review.json',review)
before=c['cases'][2]['Wmax_X_before'];after=c['cases'][2]['Wmax_X_after']
status='\n'.join(k+' = '+v for k,v in s.items())
text=f'''# Route A paper position semantics review

COMPLETE。HEADは指定922c45ff5b179eead8058045757f07d71cfb17fdと一致。pre-fix v1.3/analyzer/runtime/implementation/template/caps/reference/parent/amendment/checkpoint/attempt seal guard PASS。

原因はcanonical `key.endswith("_Z")` がWmax_Xをscalar-relativeに分類したこと。ISSUE_CLASS=PAPER_COMPARISON_POSITION_SEMANTICS_BUG。明示frozenset POSITION_KEYS（Umax_Z/Wmax_X/Nu_hot_local_max_Z/Nu_hot_local_min_Z）へのmembershipだけを変更。paper_difference関数・scalar formula・Nu_bar_1 handlingは不変。

15 unit/regression tests PASS。実際のmain内comparison comprehensionに対し位置4key、scalar3key、その他scalar／未登録suffixを確認。指定7helperの出力は完全一致、分類を戻した全ASTも一致。旧order testのsuffix assertionだけを新classification expectationへ更新し、旧source/testをsource_beforeへ保存した。

accepted coarse3000/medium6000/fine18000をsolverなしread-only canonical再解析。12 QoIすべて、Gate D monitor、非paper metrics、Wmax_X以外のpaper payloadは完全一致。別所有owner=POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIO。metricsは[position_semantics_reanalysis](position_semantics_reanalysis/)、checkは[JSON](position_semantics_reanalysis/comparison_semantics_check.json)。

fine Wmax_X calculated={after['calculated']}、reference={after['reference']}は不変。

| Payload | Before | After |
|---|---:|---:|
| signed_relative_difference | {before['signed_relative_difference']} | absent |
| absolute_relative_error | {before['absolute_relative_error']} | absent |
| signed_position_difference | absent | {after['signed_position_difference']} |
| absolute_position_error | absent | {after['absolute_position_error']} |
| legacy error | {before['error']} (signed relative) | {after['error']} (signed position) |

Gate Dは3case PASSを維持。Gate E diagnosticは既存criteriaのscalar relative≤1%／位置absolute≤0.01でPASSを再確認。Umax_Z absolute error={c['Gate_E_diagnostic']['absolute_position_errors']['Umax_Z']}、Wmax_X absolute error={c['Gate_E_diagnostic']['absolute_position_errors']['Wmax_X']}。元Gate Eは既にabsolute coordinate differenceで正しくPASSしていたためstatus変更なし。

Gate F FAIL（Umax non-monotonic）、needs_320 YES、Gate G PASSはhistoricalのまま保持。F/G追加研究なし。A–B CSVのposition difference整合確認PASS、比較定義・CSV変更なし。

[Amendment 004](../../../../docs/routeA_execution_contract_amendment_004.md)をparent v1.3から新規作成。[effective v1.4](../../../../docs/routeA_execution_contract_v1.4.md)はv1.0+A001+A002+A003+A004のfull snapshot。新analyzer `{f['new_analyzer_sha256']}`、v1.4 JSON `{f['effective_contract_sha256']}`。

physics/numerics/criteria/reference/solver結果/historyは不変。initial/continuation/cap=3000/3000/30000、200 window、Rwin≤5e-4、Initial residual≤1e-7、exact heat slope≤0を維持。実行first-unitなど次trioのmetadataだけをRa1e4へ更新し、他のexecution項目はparentと完全一致。全{f['protected_hash_entries']}保護ファイルは不変。

再解析の最初の隔離harnessでreference相対path条件に失敗し、新workspaceへ同一reference CSVをコピーして解決。失敗出力は隔離pathに保存。これはcanonical数値評価／solver異常ではない。原case/native fields/log/monitorへwriteなし。

Ra1e4 trio technically ready YES。次task RUN_ROUTE_A_RA1E4_TRIO、推奨gpt-6.1-sol / medium。今回solver/continuation/case/mesh生成なし。新しいユーザー指示を待つ。

```text
{status}
```
'''
assert not (B/'paper_position_semantics_review.md').exists();(B/'paper_position_semantics_review.md').write_text(text)
shutil.copy2('/tmp/routeA_position_fix/freeze.py',O/'freeze_runner.py');shutil.copy2(__file__,O/'review_report_runner.py')
# Final guard of every old file, the old immutable attempt seal, and current v1.4.
protected=json.loads((O/'protected_before_sha256.json').read_text())
for path,h in protected.items():assert sha(R/path)==h,path
for path,h in json.loads((B/'attempt_sealed_sha256.json').read_text()).items():assert sha(B/path)==h,path
v=json.loads((R/'docs/routeA_execution_contract_v1.4.json').read_text());assert sha(R/'docs/routeA_execution_contract_v1.4.json')==f['effective_contract_sha256']
for path,h in v['implementation_sha256'].items():assert sha(R/path)==h,path
for path,h in v['template_source']['unchanged_template_sha256'].items():assert sha(R/path)==h,path
for entry in v['amendment_chain']:
 for obj in [entry,entry['parent']]:assert sha(R/obj['path'])==obj['sha256'],obj['path']
assert sha(R/v['current_protected_evidence']['path'])==v['current_protected_evidence']['sha256']
assert sha(R/v['position_semantics_reassessment']['check_path'])==v['position_semantics_reassessment']['check_sha256']
dump(O/'protected_after_check.json',{'status':'PASS','protected_count':len(protected),'baseline_sha256':sha(O/'protected_before_sha256.json'),'historical_attempt_seal_unchanged':True,'current_v1_4_all_hash_guards':'PASS'})
outputs={str(p.relative_to(R)):sha(p) for p in O.rglob('*') if p.is_file()}
for path in [B/'paper_position_semantics_review.md',B/'paper_position_semantics_review.json',R/'docs/routeA_execution_contract_amendment_004.json',R/'docs/routeA_execution_contract_amendment_004.md',R/'docs/routeA_execution_contract_v1.4.json',R/'docs/routeA_execution_contract_v1.4.md',R/'Scripts/routeA/analyze_case.py',R/'Scripts/routeA/test_paper_comparison_order.py',R/'Scripts/routeA/test_paper_position_semantics.py']:outputs[str(path.relative_to(R))]=sha(path)
dump(O/'artifacts_sha256.json',outputs)
print('Review COMPLETE; protected',len(protected),'unchanged; current v1.4 full hash guard PASS; new artifacts sealed',len(outputs))
print('fine Wmax_X before/after:',before,after)
