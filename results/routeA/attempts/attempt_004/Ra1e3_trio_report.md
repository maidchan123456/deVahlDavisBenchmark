# Route A Ra1e3 attempt 004

**COMPLETE / accepted 3/3**。HEADは指定d68140988ec6fbc1473614bf62f2fe9ca8cf73caと一致。effective v1.3、analyzer/runtime checker、全implementation/template/caps/reference/parent/amendment guard PASS。契約・physics・numerics・threshold変更なし。

coarseはpost-fix ownerのcanonical metrics/Gate D PASSをhash照合し、accepted 3000 checkpointとしてattempt 004へ封印登録した。coarse solver/clone再実行なし。attempt 003自身のSTOP/computed NO/accepted NO/NOT_EVALUATEDとraw sealは保持する。

medium→fineを順次新規生成、input/hash→mesh→initialization clone→canonical runtime checker→OQ-02→Gate A→primaryの順で実施。segmentごとにnormal finite/actual exit/End/runtime/field/input/meshを確認し、raw evidence seal→canonical analyzer→Gate D→final checksum sealを完了してから継続／次caseへ進んだ。continuationはstartFrom/endTimeだけの変更。concurrent solver=1。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| A-Ra1e3-coarse | 3000 | YES | PASS | 1.11885517 | 1.11861213 | 1.11873791 | 1.11861218 | 3.64807845 | 3.68953716 |
| A-Ra1e3-medium | 6000 | YES | PASS | 1.1181033 | 1.11800122 | 1.11812312 | 1.11800168 | 3.64729762 | 3.69686626 |
| A-Ra1e3-fine | 18000 | YES | PASS | 1.11794249 | 1.11784797 | 1.11802097 | 1.11785036 | 3.65009512 | 3.69868728 |

paper比較は各canonical metricsのpaper_comparison_like_for_likeを保存。fine Gate E diagnostic=PASS。分類はPRACTICAL_BENCHMARK_COMPARISONで、差を純粋なnumerical errorとしない。Nu_bar_1には独立paper referenceなし。Gate Eの位置判定は既存criteriaどおりabsolute coordinate difference。Amendment 003で保持されたcanonical `_Z` dispatchによりWmax_Xのpayloadはrelative errorのまま保存し、位置のGate E判定にはcanonical calculated/referenceのabsolute differenceを使う。

Route A–B比較=COMPLETE。同一Ra/gridの既存accepted B baselineだけをread-only使用。scalarはabs(A-B)/abs(B)、signed差も保存、positionはabsolute coordinate差。heat/reconstructed-U/symmetryもCSVに記録。native A mass phiとB volume phi、section reconstructed U_fとnative volume phiはNOT_LIKE_FOR_LIKE。AB Hard thresholdは設けていない。詳細は [comparison CSV](Ra1e3_routeA_vs_routeB.csv)。

Gate F=FAIL、needs_320=YES。accepted dataのみformal使用、fine-medium≤1%、GCI limits Nu1.5%/U2%/W2%、Fs=3。Umaxは3.648078448→3.647297616→3.650095122と非単調のためp/GCI null、Gate F FAIL／needs_320 YES。320²は実行していない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
| Nu_bar_cavity | MONOTONIC_CONVERGENCE | 2.2251698040628134 | 0.00011740037407130161 | PASS |
| Umax | NON_MONOTONIC_OR_UNDEFINED | None | None | FAIL |
| Wmax | MONOTONIC_CONVERGENCE | 2.0088859291315257 | 0.0004883204639927135 | PASS |

Gate G=PASS。既存fine criteriaとfrozen operator/normalizationのみ使用。

| Component | Value | Limit | Status |
|---|---:|---:|---|
| physical_heat_imbalance | 2.13613082e-06 | 0.002 | PASS |
| section_Nu_deviation | 0.000154739194 | 0.005 | PASS |
| native_mass_epsilon_m | 4.94625773e-13 | 1e-06 | PASS |
| reconstructed_velocity_epsilon_v | 0.000564844789 | 0.002 | PASS |
| temperature_symmetry | 1.82845973e-05 | 0.002 | PASS |
| velocity_symmetry | 0.000387906469 | 0.002 | PASS |

Gate F/GのFAILはNON_BLOCKING_WITH_DOCUMENTED_LIMITATIONとしてそのまま保持し、追加研究・tuningはしない。STEADY_TRIO_COMPLETE=True、RA1E3_STEADY_TRIO_CHARACTERIZED=False（accepted3＋F/G PASS＋比較完了の資格）。Ra1e3のexecution完了とRoute A全体のVerification完了は区別する。

fineのcanonical図はcase/figuresとfinal segment seal内へ保存。既存A-SMOKE図は保護した。保護対象7094hash entriesは前後一致。Route B再計算・変更なし。過去attempt 001/002/003、coarse原seal/post-fix reanalysis、全contract/amendmentsは不変。

作業caseの過去checkpointでは後続のfunction-object実行により派生wallHeatFlux fieldが再出力され、6件の観測hash差がある。native再開field（rho/U/phi/T/p/p_rgh）、divergence field、全sealed raw wall Q/log/metrics/checksumは一致。各再開直前の全field guardはPASS、最終accepted fieldも全hash一致。原checkpointで観測した派生field hashはseal内に保持し、現在の派生fieldとの差をfinal_verification.jsonに記録した。派生fieldの再出力をnative restart mismatch／raw seal corruptionと混同しない。

Ra1e4 trio technically ready=True。契約ではF/G/paper/cap convergence failureはmatrix collectionをblockしない。次task=RUN_ROUTE_A_RA1E4_TRIO、新しいユーザー実行指示が必要。今回はRa1e3のみで終了。

詳細は [JSON](Ra1e3_trio_report.json)、[matrix](Ra1e3_trio_matrix.csv)、[group evaluation](Ra1e3_group_evaluation.json)。

```text
ROUTE_A_RA1E3_ATTEMPT = 004
ROUTE_A_RA1E3_TRIO = COMPLETE
EFFECTIVE_CONTRACT_VERSION = 1.3
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = 227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac
RUNTIME_CHECKER_HASH_VERIFIED = YES
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
COARSE_ACCEPTED_REUSE = YES
COARSE_SOLVER_RERUN = NO
A_RA1E3_COARSE_COMPUTED = YES
A_RA1E3_COARSE_ACCEPTED = YES
A_RA1E3_COARSE_FINAL_ITERATION = 3000
A_RA1E3_COARSE_GATE_D = PASS
A_RA1E3_MEDIUM_COMPUTED = YES
A_RA1E3_MEDIUM_ACCEPTED = YES
A_RA1E3_MEDIUM_FINAL_ITERATION = 6000
A_RA1E3_MEDIUM_GATE_D = PASS
A_RA1E3_MEDIUM_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E3_FINE_COMPUTED = YES
A_RA1E3_FINE_ACCEPTED = YES
A_RA1E3_FINE_FINAL_ITERATION = 18000
A_RA1E3_FINE_GATE_D = PASS
A_RA1E3_FINE_GATE_D_FAILURE_COMPONENTS = NONE
RA1E3_ACCEPTED_CASE_COUNT = 3
RA1E3_GATE_E_DIAGNOSTIC = PASS
RA1E3_GATE_F = FAIL
RA1E3_NEEDS_320 = YES
RA1E3_GATE_G = PASS
ROUTE_A_VS_ROUTE_B_COMPARISON = COMPLETE
RA1E3_STEADY_TRIO_CHARACTERIZED = NO
FORMAL_CRITERIA_CHANGED = NO
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
SOLVER_TUNING_PERFORMED = NO
POST_CAP_EXTENSION_PERFORMED = NO
AUTOMATIC_320_PERFORMED = NO
ROUTE_B_MODIFIED = NO
ATTEMPT_001_HISTORY_PRESERVED = YES
ATTEMPT_002_HISTORY_PRESERVED = YES
ATTEMPT_003_HISTORY_PRESERVED = YES
RA1E4_TRIO_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RUN_ROUTE_A_RA1E4_TRIO
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
