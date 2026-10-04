# Ra1e4 result review — REVIEW_ROUTE_A_RA1E4_RESULT

HEAD `c0d84cac3bd8c01501c8ed4a41bdbeaa930fc0bd`。effective v1.4、analyzer、runtime checkerのhash guardはPASS。solver/continuation/case/mesh生成は全て未実行。

Ra1e4 formal executionはCOMPLETE。coarse 3000、medium 6000、fine 15000で3/3 accepted、Gate D全PASS。Gate E diagnostic PASS、Gate F FAIL、needs_320 YES、Gate G PASSを保持。

元のA–B PARTIALの直接原因は、B-Ra1e4-coarse → B-SMOKEのcanonical metricsにtemperature/velocity symmetryが保存されていない2行のみ。Case B（補助diagnostic欠損）に該当し、主要QoIの欠損はない。元report/CSV/group/sealは不変。

B coarseのT/Uを含むaccepted最終6場、mesh 5ファイル、入力12ファイル、solver/environment/mesh logs 4ファイルを既存manifestのSHA-256と照合。formal master accepted YES、Ra10000、40×40×1、final3000、Foundation6 buildおよびEndを確認。分類PROVEN_ACCEPTED。既存accepted field hash登録がfinal-state sealであり、独立segment sealを新規のhistorical証拠として発明していない。

既存凍結group_evaluation.pyのsymmetry関数だけをAST抽出して実行。uniform cell pairingと1e-12正規化を再利用。B canonical式の1e-30 floorは今回inactiveで、速度単位の定数倍は相殺されることをcrosscheck。Route B canonical metrics/Gate statusへ書き戻していない。

導出値：temperature L2 `4.6986328783797357e-10`、velocity L2 `3.7722791370251563e-10`。ownership `DERIVED_DIAGNOSTIC_FROM_EXISTING_ACCEPTED_B_FIELDS`。補助比較diagnosticに限定。

| Quantity | 40² | 80² | 160² |
|---|---|---|---|
| Nu_bar_0 | COMPLETE | COMPLETE | COMPLETE |
| Nu_bar_1 | COMPLETE | COMPLETE | COMPLETE |
| Nu_bar_cavity | COMPLETE | COMPLETE | COMPLETE |
| Nu_bar_half | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE |
| Nu_hot_local_max | COMPLETE | COMPLETE | COMPLETE |
| Nu_hot_local_max_Z | COMPLETE | COMPLETE | COMPLETE |
| Nu_hot_local_min | COMPLETE | COMPLETE | COMPLETE |
| Nu_hot_local_min_Z | COMPLETE | COMPLETE | COMPLETE |
| Umax | COMPLETE | COMPLETE | COMPLETE |
| Umax_Z | COMPLETE | COMPLETE | COMPLETE |
| Wmax | COMPLETE | COMPLETE | COMPLETE |
| Wmax_X | COMPLETE | COMPLETE | COMPLETE |
| heat_imbalance | COMPLETE | COMPLETE | COMPLETE |
| native_phi_continuity | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE |
| reconstructed_U_epsilon_v | COMPLETE | COMPLETE | COMPLETE |
| reconstructed_U_mean_abs_divergence_1_s | COMPLETE | COMPLETE | COMPLETE |
| section_Nu_max_relative_deviation_from_half | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE | NOT_LIKE_FOR_LIKE |
| temperature_symmetry_L2 | COMPLETE | COMPLETE | COMPLETE |
| velocity_symmetry_L2 | COMPLETE | COMPLETE | COMPLETE |

A_B_PRIMARY_QOI_COMPARISON=COMPLETE。Nu_halfは値が揃っているが離散operator差によりNOT_LIKE_FOR_LIKE。A_B_CONSERVATION_COMPARISON=NOT_LIKE_FOR_LIKE（熱収支とreconstructed U divergenceはCOMPLETE、native fluxとsectionはoperator/unit差を保持）。A_B_SYMMETRY_COMPARISON=COMPLETE。reviewed overall COMPLETEはcoverage完了を示し、全量Hard一致/PASSを意味しない。

`AB_comparison.hard_AB_threshold=null`。`unaligned_operator_comparison_allowed=false`、`operator_rule`は異なるoperator/unit/samplingについてLIKE_FOR_LIKE=NO、Hard比較禁止。missing/near-zero baselineはnull/ABSOLUTE_ONLY、区別不能ならNOT_EVALUATEDで値を発明しない。Gate F/Gはblocking=false。batch_stop_policyのSTOPは環境・入力・mesh・nonfinite・証拠破損・evaluator failure等で、A–B全量COMPLETEという明示的前提はない。

A_B_PARTIAL_BLOCKS_NEXT_RA=NO。歴史group_evaluation.py line114のnextready=complete and ABstatus==COMPLETEはv1.4にない追加制約で、このreviewで解釈を訂正する。元artifactは変更しない。

Wmaxはcoarse→medium→fineで非単調。fine–medium差が小さくてもp/GCI未定義、Gate F FAIL/needs_320 YESを保持。Ra1e4 steady trio COMPLETE=YES、CHARACTERIZED=NO。

科学的なmatrix進行と既存model/evaluatorは準備済み。ただしv1.4のexecution.first_unit、attempt_policy.next_attempt、next_single_task、final_status.NEXT_SINGLE_TASKはRa1e4/attempt005を明示している。全matrixのcase_order/capsだけでは新しいRa1e5 execution snapshotにならない。RA1E5_TRIO_TECHNICALLY_READY=NO（次実行snapshot未準備が理由）、NEXT_EXECUTION_CONTRACT_UPDATE_REQUIRED=YES。今回criteria/numerics/AB policyは変えず、Amendmentも作らない。

**NEXT_SINGLE_TASK=PREPARE_ROUTE_A_RA1E5_EXECUTION_CONTRACT**。推奨gpt-6.1-sol / medium。USER_DECISION_REQUIRED=YES。

保護hash前後一致：751ファイル、original attempt seal 48 entries、solver segment seals 8件。reference/contracts/B formal status/A accepted fields不変。git add/commit/push未実行。

```text
ROUTE_A_RA1E4_RESULT_REVIEW=COMPLETE
RA1E4_TRIO_FORMAL_EXECUTION_STATUS=COMPLETE
RA1E4_ACCEPTED_CASE_COUNT=3
RA1E4_GATE_D=PASS_ALL
RA1E4_GATE_E_DIAGNOSTIC=PASS
RA1E4_GATE_F=FAIL
RA1E4_GATE_F_FAILURE_REASON=WMAX_NON_MONOTONIC
RA1E4_NEEDS_320=YES
RA1E4_GATE_G=PASS
A_B_ORIGINAL_COMPARISON_STATUS=PARTIAL
A_B_PARTIAL_DIRECT_CAUSE=B_COARSE_CANONICAL_TEMPERATURE_AND_VELOCITY_SYMMETRY_NOT_STORED
B_COARSE_SOURCE_CASE=B-SMOKE
B_COARSE_ACCEPTED_BASELINE_VERIFIED=YES
B_COARSE_FINAL_FIELDS_PROVENANCE=PROVEN_ACCEPTED
B_COARSE_SYMMETRY_CAN_BE_DERIVED_FROM_EXISTING_EVIDENCE=YES
B_COARSE_SYMMETRY_DERIVATION_PERFORMED=YES
B_COARSE_TEMPERATURE_SYMMETRY=4.698632878379736e-10
B_COARSE_VELOCITY_SYMMETRY=3.7722791370251563e-10
B_COARSE_DERIVED_SYMMETRY_OWNERSHIP=DERIVED_DIAGNOSTIC_FROM_EXISTING_ACCEPTED_B_FIELDS
ROUTE_B_FORMAL_STATUS_CHANGED=NO
ROUTE_B_CANONICAL_METRICS_MODIFIED=NO
A_B_PRIMARY_QOI_COMPARISON=COMPLETE
A_B_CONSERVATION_COMPARISON=NOT_LIKE_FOR_LIKE
A_B_SYMMETRY_COMPARISON=COMPLETE
A_B_REVIEWED_OVERALL_STATUS=COMPLETE
A_B_HARD_THRESHOLD_EXISTS=NO
A_B_PARTIAL_BLOCKS_NEXT_RA=NO
RA1E4_STEADY_TRIO_COMPLETE=YES
RA1E4_STEADY_TRIO_CHARACTERIZED=NO
FORMAL_CRITERIA_CHANGED=NO
NUMERICAL_SETTINGS_CHANGED=NO
PHYSICAL_MODEL_CHANGED=NO
REFERENCE_DATA_CHANGED=NO
A_RESULTS_CHANGED=NO
B_RESULTS_CHANGED=NO
ROUTE_A_SOLVER_EXECUTED=NO
ROUTE_B_SOLVER_EXECUTED=NO
CASE_GENERATED=NO
MESH_GENERATED=NO
CONTINUATION_EXECUTED=NO
CONTRACT_AMENDMENT_CREATED=NO
NEXT_EXECUTION_CONTRACT_UPDATE_REQUIRED=YES
RA1E5_TRIO_TECHNICALLY_READY=NO
NEXT_SINGLE_TASK=PREPARE_ROUTE_A_RA1E5_EXECUTION_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK=gpt-6.1-sol / medium
USER_DECISION_REQUIRED=YES
```
