# Route A Ra1e4 attempt 005

**COMPLETE / accepted 3/3**。HEADは指定36c0c7b0c41581c612e77d563c3c6cb06737e5f9と一致。effective v1.4、analyzer/runtime checker、全implementation/template/caps/reference/parent/amendment guard PASS。契約・physics・numerics・threshold変更なし。

coarse→medium→fineの新規formalケースをcanonical generatorで作成。既存A-SMOKE/Ra1e4_coarseのpromotion/reuseなし。attempt 005の結果所有を過去attemptと分離する。

coarse→medium→fineを順次新規生成、input/hash→mesh→initialization clone→canonical runtime checker→OQ-02→Gate A→primaryの順で実施。segmentごとにnormal finite/actual exit/End/runtime/field/input/meshを確認し、raw evidence seal→canonical analyzer→Gate D→final checksum sealを完了してから継続／次caseへ進んだ。continuationはstartFrom/endTimeだけの変更。concurrent solver=1。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| A-Ra1e4-coarse | 3000 | YES | PASS | 2.25995463 | 2.25742142 | 2.2585147 | 2.25742147 | 16.1213351 | 19.5973335 |
| A-Ra1e4-medium | 6000 | YES | PASS | 2.24907728 | 2.24798515 | 2.24905367 | 2.24798528 | 16.1730705 | 19.6268395 |
| A-Ra1e4-fine | 15000 | YES | PASS | 2.2463852 | 2.2455727 | 2.24677347 | 2.24557519 | 16.1845829 | 19.6219614 |

paper比較は各canonical metricsのpaper_comparison_like_for_likeを保存。fine Gate E diagnostic=PASS。分類はPRACTICAL_BENCHMARK_COMPARISONで、差を純粋なnumerical errorとしない。A–Bのobserved differenceとcauseを区別し、本Ra一点の差から原因を断定しない。Nu_bar_1には独立paper referenceなし。v1.4の明示POSITION_KEYSによるabsolute_position_errorをGate Eの既存位置基準へ使用。

Route A–B比較=PARTIAL。同一Ra/gridの既存accepted B baselineだけをread-only使用。B coarseはformal manifestが指すaccepted B-SMOKE artifactで、metrics path/hash/source IDを保存。scalarはabs(A-B)/abs(B)、signed差も保存、positionはabsolute coordinate差。heat/reconstructed-U/symmetryもCSVに記録。native A mass phiとB volume phi、section reconstructed U_fとnative volume phiはNOT_LIKE_FOR_LIKE。AB Hard thresholdは設けていない。詳細は [comparison CSV](Ra1e4_routeA_vs_routeB.csv)。

Gate F=FAIL、needs_320=YES。accepted dataのみformal使用、fine-medium≤1%、GCI limits Nu1.5%/U2%/W2%、Fs=3。非単調/未定義ではp/GCI null。320²は実行していない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
| Nu_bar_cavity | MONOTONIC_CONVERGENCE | 2.0145361248427722 | 0.0011824381366717367 | PASS |
| Umax | MONOTONIC_CONVERGENCE | 2.167958109096661 | 0.0006107739175196977 | PASS |
| Wmax | NON_MONOTONIC_OR_UNDEFINED | None | None | FAIL |

Gate G=PASS。既存fine criteriaとfrozen operator/normalizationのみ使用。

| Component | Value | Limit | Status |
|---|---:|---:|---|
| physical_heat_imbalance | 1.1068983e-06 | 0.002 | PASS |
| section_Nu_deviation | 0.000538673899 | 0.005 | PASS |
| native_mass_epsilon_m | 2.594755e-12 | 1e-06 | PASS |
| reconstructed_velocity_epsilon_v | 0.000529218345 | 0.002 | PASS |
| temperature_symmetry | 8.18911866e-05 | 0.002 | PASS |
| velocity_symmetry | 0.000348993322 | 0.002 | PASS |

Gate F/GのFAILはNON_BLOCKING_WITH_DOCUMENTED_LIMITATIONとしてそのまま保持し、追加研究・tuningはしない。STEADY_TRIO_COMPLETE=True、RA1E4_STEADY_TRIO_CHARACTERIZED=False（accepted3＋F/G PASS＋比較完了の資格）。Ra1e4のexecution完了とRoute A全体のVerification完了は区別する。

fineのcanonical図はcase/figuresとfinal segment seal内へ保存。既存A-SMOKE図は保護した。保護対象83282hash entriesは前後一致。Route B再計算・変更なし。過去attempt 001–004、Ra1e3 accepted結果・position semantics reanalysis、全contract/amendmentsは不変。

Ra1e5 trio technically ready=False。契約ではF/G/paper/cap convergence failure単独はmatrix collectionをblockしない。required A–B symmetry comparisonのB coarse canonical値が未保存のため比較はPARTIALとして残し、次Raの前にresult/provenance reviewを推奨する。Bを再計算して値を作らない。次task=REVIEW_ROUTE_A_RA1E4_RESULT、新しいユーザー実行指示が必要。今回はRa1e4のみで終了。

詳細は [JSON](Ra1e4_trio_report.json)、[matrix](Ra1e4_trio_matrix.csv)、[group evaluation](Ra1e4_group_evaluation.json)。

```text
ROUTE_A_RA1E4_ATTEMPT = 005
ROUTE_A_RA1E4_TRIO = COMPLETE
EFFECTIVE_CONTRACT_VERSION = 1.4
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = 2665b8a62211618ae531e7b8d42242e3d8f9ae469b95b634beab672c89b345d7
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
RUNTIME_CHECKER_HASH_VERIFIED = YES
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
A_RA1E4_COARSE_COMPUTED = YES
A_RA1E4_COARSE_ACCEPTED = YES
A_RA1E4_COARSE_FINAL_ITERATION = 3000
A_RA1E4_COARSE_GATE_D = PASS
A_RA1E4_COARSE_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E4_MEDIUM_COMPUTED = YES
A_RA1E4_MEDIUM_ACCEPTED = YES
A_RA1E4_MEDIUM_FINAL_ITERATION = 6000
A_RA1E4_MEDIUM_GATE_D = PASS
A_RA1E4_MEDIUM_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E4_FINE_COMPUTED = YES
A_RA1E4_FINE_ACCEPTED = YES
A_RA1E4_FINE_FINAL_ITERATION = 15000
A_RA1E4_FINE_GATE_D = PASS
A_RA1E4_FINE_GATE_D_FAILURE_COMPONENTS = NONE
RA1E4_ACCEPTED_CASE_COUNT = 3
RA1E4_STEADY_TRIO_COMPLETE = YES
RA1E4_GATE_E_DIAGNOSTIC = PASS
RA1E4_GATE_F = FAIL
RA1E4_NEEDS_320 = YES
RA1E4_GATE_G = PASS
ROUTE_A_VS_ROUTE_B_COMPARISON = PARTIAL
RA1E4_STEADY_TRIO_CHARACTERIZED = NO
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
RA1E5_TRIO_TECHNICALLY_READY = NO
NEXT_SINGLE_TASK = REVIEW_ROUTE_A_RA1E4_RESULT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```

最終照合: 全native再開field・divergence field・input/mesh・raw/final seals・runtime/OQ-02/Gate AはPASS。過去checkpointの派生wallHeatFlux working fieldは後続function-object実行で再出力されるため、5件の観測hash差をfinal_verification.jsonへ保存。最終fieldは全hash一致、封印raw Q/log/metricsは不変。

初回bootstrapのfoamRun -help表記判定はVersion表記を期待してfalse negativeとなった。実際のUsing: OpenFOAM-13／Build: 13-441953dfbb42を確認し、case生成前に修正した。初回log/sourceはbootstrap_attempt_001に保存。環境・frozen checker・contract・criteriaへの変更なし。
