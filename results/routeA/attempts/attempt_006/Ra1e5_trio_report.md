# Route A Ra1e5 attempt 006

**COMPLETE / accepted 3/3**。指定HEAD `85d7f5ebc76b8be3b840ae31217a457833b5a8d6`と一致。effective v1.5をsole current guardとしてdigest、implementation/template/caps/reference、parent/amendments001–005、accepted Ra1e3/Ra1e4 history、Ra1e4 review、accepted Route B Ra1e5 baselinesを照合した。物理・numerics・threshold・AB policy・position semantics・iteration policyへの変更なし。

coarse→medium→fineの順にcanonical generatorのA-SMOKE roleからNEW formal casesを生成。raw generated_manifest_original.jsonを保存し、formal metadataのみ変更した。歴史field/caseのpromotion/reuseは行っていない。input hashes/template expansion、blockMesh/checkMesh、既存initialization clone、canonical runtime provenance、OQ-02、Gate Aを確認後primary実行。solver concurrency=1。

initial3000、increment3000、absolute cap30000。normal finite segmentはraw evidence seal→canonical analyzer→六項目Gate D→final checksum sealの順に保存した。FAIL継続ではstartFrom/endTimeだけを変更、sealed latestTimeからrestartし、cold retryは行わない。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| A-Ra1e5-coarse | 3000 | YES | PASS | 4.62617047 | 4.61628503 | 4.61866749 | 4.61628503 | 34.8279606 | 68.873693 |
| A-Ra1e5-medium | 3000 | YES | PASS | 4.5492008 | 4.54560576 | 4.54777217 | 4.54560659 | 34.7848546 | 68.5707766 |
| A-Ra1e5-fine | 12000 | YES | PASS | 4.52982575 | 4.52764979 | 4.52982626 | 4.52765067 | 34.7549843 | 68.6552097 |

| Case | Segment end | Gate D | Failure components |
|---|---:|---|---|
| A-Ra1e5-coarse | 3000 | PASS | NONE |
| A-Ra1e5-medium | 3000 | PASS | NONE |
| A-Ra1e5-fine | 3000 | FAIL | QOI_RWIN_PASS,RESIDUAL_PASS,HEAT_TREND_PASS |
| A-Ra1e5-fine | 6000 | FAIL | QOI_RWIN_PASS,RESIDUAL_PASS |
| A-Ra1e5-fine | 9000 | FAIL | RESIDUAL_PASS |
| A-Ra1e5-fine | 12000 | PASS | NONE |

Paper comparisonはPRACTICAL_BENCHMARK_COMPARISON。scalar欄はabsolute relative error、position欄はabsolute coordinate error。canonical POSITION_KEYSを使用し、Nu_bar_1は独立paper referenceがない既存handlingを保持する。観測された差は純粋numerical errorやphysical/model causeの証明ではない。

| Paper QoI error | coarse | medium | fine |
|---|---:|---:|---:|
| Nu_bar_cavity | 0.0237155278 | 0.00668307179 | 0.00239560731 |
| Nu_bar_half | 0.0220552097 | 0.00636693207 | 0.00239572006 |
| Nu_bar_0 | 0.0237935312 | 0.00811837592 | 0.00413612573 |
| Nu_hot_local_max | 0.0551895461 | 0.0149109596 | 0.00405452195 |
| Nu_hot_local_max_Z | 0.00844638218 | 0.00250081789 | 9.18032536e-05 |
| Nu_hot_local_min | 0.018534907 | 0.00577715982 | 0.00240172601 |
| Nu_hot_local_min_Z | 0 | 0 | 0 |
| Umax | 0.00282063306 | 0.00157945844 | 0.000719385759 |
| Umax_Z | 0.00754882813 | 0.00120117188 | 0.00172851562 |
| Wmax | 0.00413606869 | 0.000280264804 | 0.000950717353 |
| Wmax_X | 0.0035 | 0.00260351562 | 0.000326171875 |

Route A–B比較=COMPLETE、primary coverage=COMPLETE。accepted B coarse6000/medium9000/fine12000のcanonical evidenceをread-only使用。比較CSVには全QoI、sampling/method/version、source IDs、iteration、operator compatibilityを保存。scalar gap=abs(A-B)/abs(B)、position gap=absolute coordinate difference。AB Hard thresholdなし。Nu_half/sectionのA reconstructed U_f対B corrected native volume phi、native A mass phi対B volume phiはNOT_LIKE_FOR_LIKE。熱・reconstructed U divergence・対称性は定義を区別して診断比較する。欠損はNOT_EVALUATEDとして記録し、補助欠損単独を新しいmatrix blocking条件にしない。

| A–B relative/position gap | coarse | medium | fine |
|---|---:|---:|---:|
| Nu_bar_cavity | 0.000390716538 | 0.000378466897 | 0.000389346384 |
| Nu_bar_0 | 6.03893673e-07 | 2.67709994e-06 | 2.96620967e-07 |
| Umax | 0.000250166139 | 0.000241084335 | 0.00025049989 |
| Umax_Z | 0 | 0 | 0 |
| Wmax | 0.000124921211 | 0.000121174484 | 0.000120608603 |
| Wmax_X | 0 | 0 | 0 |

Gate E diagnostic=PASS。fine acceptedの場合のみformal診断を評価。既存scalar relative error/position absolute error criteriaを適用。

Gate F=FAIL、needs_320=YES。accepted dataのみ使用。既存fine-medium≤1%、GCI limits Nu1.5%/U2%/W2%、Fs=3。非単調ではp/GCI null、FAIL/needs_320 YESを保存する。320²を実行しない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
| Nu_bar_cavity | MONOTONIC_CONVERGENCE | 1.9900898630526633 | 0.00431661798078801 | PASS |
| Umax | MONOTONIC_CONVERGENCE | 0.5291756216247349 | 0.005818862337358696 | PASS |
| Wmax | NON_MONOTONIC_OR_UNDEFINED | None | None | FAIL |

Gate G=PASS。fine acceptedの場合のみformal判定、未acceptedならdiagnostic-only。既存operator/normalization/thresholdを適用し、FAILでも追加研究は行わない。

| Component | Value | Limit | Status |
|---|---:|---:|---|
| physical_heat_imbalance | 1.94329477e-07 | 0.002 | PASS |
| section_Nu_deviation | 0.000491317934 | 0.005 | PASS |
| native_mass_epsilon_m | 1.69270367e-11 | 1e-06 | PASS |
| reconstructed_velocity_epsilon_v | 0.000638071716 | 0.002 | PASS |
| temperature_symmetry | 0.000100028431 | 0.002 | PASS |
| velocity_symmetry | 0.000387391048 | 0.002 | PASS |

Unresolved: execution stop=None。Gate F/G limitationや比較データ欠損はJSONのunresolved_issuesに保存。previous Ra1e3/Ra1e4 Gate F FAIL/needs_320 YESは変更しない。

RA1E5_STEADY_TRIO_COMPLETE=YES、CHARACTERIZED=NO。execution完了とcharacterization/full verificationは別。

RA1E6_TRIO_SCIENTIFICALLY_ALLOWED=YES。v1.5はRa1e5/attempt006のsnapshotなのでRa1e6_TRIO_TECHNICALLY_READY=NO、snapshot update required=YES。次task=PREPARE_ROUTE_A_RA1E6_EXECUTION_CONTRACT。Ra1e6/320/Gate H/Jを実行せず、Ra1e5 group evaluationまでで終了する。

既存9356ファイルhashを保護。全contract/amendments、attempts001–005、Ra1e3/Ra1e4結果/review、Route B、reference、canonical scripts/templates不変。fine図は既存canonical workflowを使用し、新case/figuresとsegment内に保存する。

詳細: [JSON](Ra1e5_trio_report.json)、[matrix](Ra1e5_trio_matrix.csv)、[comparison CSV](Ra1e5_routeA_vs_routeB.csv)、[group evaluation](Ra1e5_group_evaluation.json)。git add/commit/push未実行。

```text
ROUTE_A_RA1E5_ATTEMPT = 006
ROUTE_A_RA1E5_TRIO = COMPLETE
EFFECTIVE_CONTRACT_VERSION = 1.5
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = c33efe4aa81ce0644fd709fe944563e93c7ee2f08304161000784f6418e159c1
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
RUNTIME_CHECKER_HASH_VERIFIED = YES
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
A_RA1E5_COARSE_COMPUTED = YES
A_RA1E5_COARSE_ACCEPTED = YES
A_RA1E5_COARSE_FINAL_ITERATION = 3000
A_RA1E5_COARSE_GATE_D = PASS
A_RA1E5_COARSE_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E5_MEDIUM_COMPUTED = YES
A_RA1E5_MEDIUM_ACCEPTED = YES
A_RA1E5_MEDIUM_FINAL_ITERATION = 3000
A_RA1E5_MEDIUM_GATE_D = PASS
A_RA1E5_MEDIUM_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E5_FINE_COMPUTED = YES
A_RA1E5_FINE_ACCEPTED = YES
A_RA1E5_FINE_FINAL_ITERATION = 12000
A_RA1E5_FINE_GATE_D = PASS
A_RA1E5_FINE_GATE_D_FAILURE_COMPONENTS = NONE
RA1E5_ACCEPTED_CASE_COUNT = 3
RA1E5_STEADY_TRIO_COMPLETE = YES
RA1E5_GATE_E_DIAGNOSTIC = PASS
RA1E5_GATE_F = FAIL
RA1E5_NEEDS_320 = YES
RA1E5_GATE_G = PASS
ROUTE_A_VS_ROUTE_B_COMPARISON = COMPLETE
RA1E5_STEADY_TRIO_CHARACTERIZED = NO
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
RA1E6_TRIO_TECHNICALLY_READY = NO
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_RA1E6_EXECUTION_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
A_B_PRIMARY_QOI_COMPARISON = COMPLETE
A_B_HARD_THRESHOLD_EXISTS = NO
AB_COMPARISON_POLICY_CHANGED = NO
POSITION_SEMANTICS_CHANGED = NO
ITERATION_POLICY_CHANGED = NO
RA1E4_RESULTS_MODIFIED = NO
RA1E6_TRIO_SCIENTIFICALLY_ALLOWED = YES
RA1E6_EXECUTION_CONTRACT_UPDATE_REQUIRED = YES
```

最終照合: native restart fields・final accepted fields・input/mesh・raw/final seals・runtime/OQ-02/Gate AはPASS。派生wallHeatFluxの旧working checkpoint再出力差は3件で、封印raw Q/log/metricsは不変。詳細final_verification.json。
