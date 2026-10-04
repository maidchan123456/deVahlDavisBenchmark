# Route A Ra1e6 attempt 007

**COMPLETE / computed 3/3 / accepted 3/3**。HEAD `302e5b4ac41dba187678b84f0132d5c6db72fa99`は指定302e5b4ac41dba187678b84f0132d5c6db72fa99と一致。effective v1.6のみをcurrent guardとし、digest、implementation/template/reference/caps、parent/amendments001–006、accepted Ra1e3–Ra1e5、attempt006 seals、B Ra1e6 computed/unaccepted evidenceを照合。凍結criteria/physics/numericsに変更なし。

coarse→medium→fine、solver concurrency1。canonical generatorで全NEWケースを生成、generated_manifest_original.jsonを保存しmetadataのみformal IDへ対応付け。input/hash/template expansion→blockMesh/checkMesh→既存initialization clone→canonical runtime provenance→OQ-02→Gate A→primaryの順。歴史fieldやA-SMOKE solutionのpromotionなし。

各segmentはhealth→raw seal→canonical analyzer→六boolean Gate D→final checksum sealの順で保存。initial3000、+3000、cap30000。継続はstartFrom/endTimeのみ変更しsealed latestTimeからrestart。正常有限cap FAILはCONVERGENCE_NOT_REACHED/computed YES/accepted NOで終了する。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| A-Ra1e6-coarse | 3000 | YES | PASS | 9.4389884 | 9.40228468 | 9.40641067 | 9.40228463 | 65.627838 | 222.709205 |
| A-Ra1e6-medium | 3000 | YES | PASS | 8.98785498 | 8.9764923 | 8.98100123 | 8.9764923 | 65.1185531 | 218.333412 |
| A-Ra1e6-fine | 9000 | YES | PASS | 8.86898946 | 8.86338339 | 8.86766918 | 8.86338376 | 64.9147346 | 219.900262 |

| Case | Segment end | Gate D | Failure components |
|---|---:|---|---|
| A-Ra1e6-coarse | 3000 | PASS | NONE |
| A-Ra1e6-medium | 3000 | PASS | NONE |
| A-Ra1e6-fine | 3000 | FAIL | QOI_RWIN_PASS,RESIDUAL_PASS |
| A-Ra1e6-fine | 6000 | FAIL | QOI_RWIN_PASS,RESIDUAL_PASS |
| A-Ra1e6-fine | 9000 | PASS | NONE |

Paper comparisonはPRACTICAL_BENCHMARK_COMPARISON。scalarはabsolute relative error、POSITION_KEYSはabsolute coordinate error。Nu_bar_1は独立paper referenceなし。紙面値との差を純粋numerical errorや原因の証明とはしない。

| Paper QoI error | coarse | medium | fine |
|---|---:|---:|---:|
| Nu_bar_cavity | 0.072612318 | 0.0213471571 | 0.00783971088 |
| Nu_bar_half | 0.0690317839 | 0.0206843089 | 0.00780420233 |
| Nu_bar_0 | 0.0663813856 | 0.0180891805 | 0.00526067737 |
| Nu_hot_local_max | 0.125467116 | 0.0379244595 | 0.0056269919 |
| Nu_hot_local_max_Z | 0.00833905184 | 0.00360241021 | 0.000656340067 |
| Nu_hot_local_min | 0.0620008576 | 0.0247666891 | 0.013482149 |
| Nu_hot_local_min_Z | 0.0125 | 0 | 0 |
| Umax | 0.0154392394 | 0.00755923167 | 0.00440561034 |
| Umax_Z | 0.0125488281 | 0.00620117188 | 0.00302734375 |
| Wmax | 0.0152680746 | 0.00467992554 | 0.00246289962 |
| Wmax_X | 0.00030234375 | 0.00665 | 0.00262734375 |

Gate E diagnostic=PASS。fine A accepted時だけ既存基準で評価する。unaccepted fineならformal NOT_EVALUATEDで、paperが近いだけでは昇格しない。

Gate F=FAIL、needs_320=YES。accepted A3格子のみformal使用。未accepted gridがあればformal NOT_EVALUATED。非単調時はp/GCI null、FAIL/needs_320 YES。320²や新thresholdは追加しない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
| Nu_bar_cavity | MONOTONIC_CONVERGENCE | 1.9242237858496105 | 0.014383698842540909 | FAIL |
| Umax | MONOTONIC_CONVERGENCE | 1.3211876136563185 | 0.006284952281840569 | PASS |
| Wmax | NON_MONOTONIC_OR_UNDEFINED | None | None | FAIL |

Gate G formal=PASS、diagnostic=PASS。fine A accepted時だけformal。既存operator/normalizationとthresholdを使用。

| Component | Value | Limit | Diagnostic check |
|---|---:|---:|---|
| physical_heat_imbalance | 4.10599117e-08 | 0.002 | PASS |
| section_Nu_deviation | 0.000539266406 | 0.005 | PASS |
| native_mass_epsilon_m | 9.20128249e-11 | 1e-06 | PASS |
| reconstructed_velocity_epsilon_v | 0.000949693062 | 0.002 | PASS |
| temperature_symmetry | 0.000110370354 | 0.002 | PASS |
| velocity_symmetry | 0.000401098248 | 0.002 | PASS |

A–B diagnostic comparison coverage=COMPLETE、primary=COMPLETE。全Ra1e6 comparison ownershipは**DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE**。Bは各grid computed YES、accepted NO、Gate D FAIL、final30000。CSV/JSONにA_accepted/B_computed/B_accepted/ownershipを保存。Aがacceptedでもformal accepted AB comparison NO。B FAILはA Gate D/E/F/Gへ伝播させない。B再計算・追加反復・status変更なし。

scalar abs(A-B)/abs(B)、signed差、position絶対差は既存定義を使用。Nu_half/sectionとnative continuityはNOT_LIKE_FOR_LIKE、missingはNOT_EVALUATED。AB Hard thresholdなし。AがPASSしてBがFAILしても物理的優位やB誤りを証明しない。両者FAILでも同じ原因/physical unsteadiness/solver defectを断定しない。

Solver completion=True、computed=3/3、accepted=3/3、characterized=Falseを区別。RA1E6_STEADY_TRIO_COMPLETEは従来のaccepted3ケース定義を保持し、全computed実行完了とは別に記録する。

| Ra | Computed | Accepted | Gate D c/m/f | E diagnostic | F | G formal | needs_320 |
|---|---|---|---|---|---|---|---|
| 1e3 | 3/3 | 3/3 | PASS,PASS,PASS | PASS | FAIL | PASS | YES |
| 1e4 | 3/3 | 3/3 | PASS,PASS,PASS | PASS | FAIL | PASS | YES |
| 1e5 | 3/3 | 3/3 | PASS,PASS,PASS | PASS | FAIL | PASS | YES |
| 1e6 | 3/3 | 3/3 | PASS,PASS,PASS | PASS | FAIL | PASS | YES |

全matrix computed=12/12、accepted=12/12。ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE=YESは全accepted/all Gates PASS/full verificationを意味しない。過去Ra1e3–Ra1e5のstatusは保存reportから転記しただけで再判定していない。

Unresolved: execution stop=None。Gate F/G未達、cap failure、formal accepted B baseline不在はJSONに記録。追加研究・tuning・post-hoc例外・post-cap延長なし。今回の実行はRa1e6とgroup評価までで終了。Gate H/J/320は開始しない。

保護対象10077file hashes。旧contracts/amendments/attempts001–006/Route B/reference/scripts/templates/previous accepted fields/seals不変。fine図は既存canonical workflowだけで新caseとsegmentへ保存。

**NEXT_SINGLE_TASK=REVIEW_ROUTE_A_FULL_STEADY_MATRIX**。full steady matrix reviewを別taskとして行い、Gate Hはその後に実行可否を判断する。USER_DECISION_REQUIRED=YES。git add/commit/push未実行。

詳細: [JSON](Ra1e6_trio_report.json)、[matrix](Ra1e6_trio_matrix.csv)、[diagnostic comparison CSV](Ra1e6_routeA_vs_routeB.csv)、[group evaluation](Ra1e6_group_evaluation.json)、[full matrix summary](RouteA_full_steady_matrix_summary.json)。

```text
ROUTE_A_RA1E6_ATTEMPT = 007
ROUTE_A_RA1E6_TRIO = COMPLETE
EFFECTIVE_CONTRACT_VERSION = 1.6
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
RUNTIME_CHECKER_HASH_VERIFIED = YES
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
A_RA1E6_COARSE_COMPUTED = YES
A_RA1E6_COARSE_ACCEPTED = YES
A_RA1E6_COARSE_FINAL_ITERATION = 3000
A_RA1E6_COARSE_GATE_D = PASS
A_RA1E6_COARSE_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E6_MEDIUM_COMPUTED = YES
A_RA1E6_MEDIUM_ACCEPTED = YES
A_RA1E6_MEDIUM_FINAL_ITERATION = 3000
A_RA1E6_MEDIUM_GATE_D = PASS
A_RA1E6_MEDIUM_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E6_FINE_COMPUTED = YES
A_RA1E6_FINE_ACCEPTED = YES
A_RA1E6_FINE_FINAL_ITERATION = 9000
A_RA1E6_FINE_GATE_D = PASS
A_RA1E6_FINE_GATE_D_FAILURE_COMPONENTS = NONE
RA1E6_ACCEPTED_CASE_COUNT = 3
RA1E6_STEADY_TRIO_COMPLETE = YES
RA1E6_GATE_E_DIAGNOSTIC = PASS
RA1E6_GATE_F = FAIL
RA1E6_NEEDS_320 = YES
RA1E6_GATE_G = PASS
RA1E6_STEADY_TRIO_CHARACTERIZED = NO
FORMAL_CRITERIA_CHANGED = NO
REFERENCE_DATA_CHANGED = NO
RA1E3_RESULTS_MODIFIED = NO
POSITION_SEMANTICS_V1_4_USED = YES
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
SOLVER_TUNING_PERFORMED = NO
POST_CAP_EXTENSION_PERFORMED = NO
AUTOMATIC_320_PERFORMED = NO
ROUTE_B_MODIFIED = NO
ATTEMPT_001_HISTORY_PRESERVED = YES
ATTEMPT_002_HISTORY_PRESERVED = YES
ATTEMPT_003_HISTORY_PRESERVED = YES
NEXT_SINGLE_TASK = REVIEW_ROUTE_A_FULL_STEADY_MATRIX
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
A_B_HARD_THRESHOLD_EXISTS = NO
AB_COMPARISON_POLICY_CHANGED = NO
POSITION_SEMANTICS_CHANGED = NO
ITERATION_POLICY_CHANGED = NO
RA1E4_RESULTS_MODIFIED = NO
ROUTE_B_RA1E6_COMPUTED_BASELINE_COUNT = 3
ROUTE_B_RA1E6_ACCEPTED_BASELINE_COUNT = 0
RA1E6_AB_COMPARISON_POLICY = DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE
FORMAL_ACCEPTED_AB_COMPARISON_AVAILABLE = NO
ROUTE_A_VS_ROUTE_B_DIAGNOSTIC_COMPARISON = COMPLETE
A_B_PRIMARY_QOI_DIAGNOSTIC_COMPARISON = COMPLETE
B_GATE_D_FAILURE_PROPAGATED_TO_A = NO
RA1E5_RESULTS_MODIFIED = NO
AB_HARD_THRESHOLD_ADDED = NO
POST_HOC_RA1E6_ACCEPTANCE_RULE_ADDED = NO
ROUTE_B_SOLVER_EXECUTED = NO
FULL_STEADY_MATRIX_REVIEW_REQUIRED = YES
ROUTE_A_MATRIX_CASE_COUNT = 12
ROUTE_A_MATRIX_COMPUTED_COUNT = 12
ROUTE_A_MATRIX_ACCEPTED_COUNT = 12
ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE = YES
ALL_ROUTE_A_CASES_ACCEPTED = YES
ALL_ROUTE_A_GATES_PASSED = NO
```

最終照合: native restart fields・final accepted fields・input/mesh・raw/final seals・runtime/OQ-02/Gate AはPASS。派生wallHeatFluxの旧working checkpoint再出力差は2件で、封印raw Q/log/metricsは不変。詳細final_verification.json。
