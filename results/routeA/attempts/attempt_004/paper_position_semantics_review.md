# Route A paper position semantics review

COMPLETE。HEADは指定922c45ff5b179eead8058045757f07d71cfb17fdと一致。pre-fix v1.3/analyzer/runtime/implementation/template/caps/reference/parent/amendment/checkpoint/attempt seal guard PASS。

原因はcanonical `key.endswith("_Z")` がWmax_Xをscalar-relativeに分類したこと。ISSUE_CLASS=PAPER_COMPARISON_POSITION_SEMANTICS_BUG。明示frozenset POSITION_KEYS（Umax_Z/Wmax_X/Nu_hot_local_max_Z/Nu_hot_local_min_Z）へのmembershipだけを変更。paper_difference関数・scalar formula・Nu_bar_1 handlingは不変。

15 unit/regression tests PASS。実際のmain内comparison comprehensionに対し位置4key、scalar3key、その他scalar／未登録suffixを確認。指定7helperの出力は完全一致、分類を戻した全ASTも一致。旧order testのsuffix assertionだけを新classification expectationへ更新し、旧source/testをsource_beforeへ保存した。

accepted coarse3000/medium6000/fine18000をsolverなしread-only canonical再解析。12 QoIすべて、Gate D monitor、非paper metrics、Wmax_X以外のpaper payloadは完全一致。別所有owner=POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIO。metricsは[position_semantics_reanalysis](position_semantics_reanalysis/)、checkは[JSON](position_semantics_reanalysis/comparison_semantics_check.json)。

fine Wmax_X calculated=0.17822265625、reference=0.178は不変。

| Payload | Before | After |
|---|---:|---:|
| signed_relative_difference | 0.0012508778089888116 | absent |
| absolute_relative_error | 0.0012508778089888116 | absent |
| signed_position_difference | absent | 0.00022265625000000844 |
| absolute_position_error | absent | 0.00022265625000000844 |
| legacy error | 0.0012508778089888116 (signed relative) | 0.00022265625000000844 (signed position) |

Gate Dは3case PASSを維持。Gate E diagnosticは既存criteriaのscalar relative≤1%／位置absolute≤0.01でPASSを再確認。Umax_Z absolute error=0.002429687500000055、Wmax_X absolute error=0.00022265625000000844。元Gate Eは既にabsolute coordinate differenceで正しくPASSしていたためstatus変更なし。

Gate F FAIL（Umax non-monotonic）、needs_320 YES、Gate G PASSはhistoricalのまま保持。F/G追加研究なし。A–B CSVのposition difference整合確認PASS、比較定義・CSV変更なし。

[Amendment 004](../../../../docs/routeA_execution_contract_amendment_004.md)をparent v1.3から新規作成。[effective v1.4](../../../../docs/routeA_execution_contract_v1.4.md)はv1.0+A001+A002+A003+A004のfull snapshot。新analyzer `e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed`、v1.4 JSON `2665b8a62211618ae531e7b8d42242e3d8f9ae469b95b634beab672c89b345d7`。

physics/numerics/criteria/reference/solver結果/historyは不変。initial/continuation/cap=3000/3000/30000、200 window、Rwin≤5e-4、Initial residual≤1e-7、exact heat slope≤0を維持。実行first-unitなど次trioのmetadataだけをRa1e4へ更新し、他のexecution項目はparentと完全一致。全83200保護ファイルは不変。

再解析の最初の隔離harnessでreference相対path条件に失敗し、新workspaceへ同一reference CSVをコピーして解決。失敗出力は隔離pathに保存。これはcanonical数値評価／solver異常ではない。原case/native fields/log/monitorへwriteなし。

Ra1e4 trio technically ready YES。次task RUN_ROUTE_A_RA1E4_TRIO、推奨gpt-6.1-sol / medium。今回solver/continuation/case/mesh生成なし。新しいユーザー指示を待つ。

```text
ROUTE_A_PAPER_POSITION_SEMANTICS_REVIEW = COMPLETE
ISSUE_CLASS = PAPER_COMPARISON_POSITION_SEMANTICS_BUG
DIRECT_CAUSE = key.endswith("_Z") misclassified Wmax_X as scalar-relative
ANALYZER_FIX_APPLIED = YES
ANALYZER_FIX_SCOPE = PAPER_POSITION_CLASSIFICATION_ONLY
OLD_ANALYZER_SHA256 = e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac
NEW_ANALYZER_SHA256 = e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
POSITION_KEYS_EXPLICITLY_DEFINED = YES
WMAX_X_POSITION_TEST = PASS
UMAX_Z_POSITION_TEST = PASS
LOCAL_NU_POSITION_TESTS = PASS
SCALAR_RELATIVE_SEMANTICS_TEST = PASS
NUMERICAL_HELPER_REGRESSION = PASS
RA1E3_READ_ONLY_REANALYSIS = PASS
RA1E3_QOIS_UNCHANGED = YES
WMAX_X_CANONICAL_POSITION_SEMANTICS = PASS
RA1E3_GATE_D_STATUSES_UNCHANGED = YES
RA1E3_GATE_E_DIAGNOSTIC = PASS
RA1E3_GATE_E_STATUS_CHANGED = NO
RA1E3_GATE_F = FAIL
RA1E3_GATE_G = PASS
RA1E3_NEEDS_320 = YES
CONTRACT_AMENDMENT_004_CREATED = YES
PARENT_EFFECTIVE_CONTRACT_VERSION = 1.3
PARENT_EFFECTIVE_CONTRACT_SHA256 = 227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1
EFFECTIVE_CONTRACT_VERSION = 1.4
EFFECTIVE_CONTRACT_SHA256 = 2665b8a62211618ae531e7b8d42242e3d8f9ae469b95b634beab672c89b345d7
FORMAL_CRITERIA_CHANGED = NO
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
REFERENCE_DATA_CHANGED = NO
SOLVER_RESULTS_CHANGED = NO
ATTEMPT_004_HISTORY_PRESERVED = YES
PRIMARY_SOLVER_EXECUTED = NO
CONTINUATION_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
RA1E4_TRIO_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RUN_ROUTE_A_RA1E4_TRIO
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
