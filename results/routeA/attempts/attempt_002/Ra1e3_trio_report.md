# Route A Ra1e3 attempt 002

**STOPPED before primary solver**。HEADは指定の1370e1d738b5253983f6b0230fb20643d9ac89aaと一致。v1.1、analyzer、generator、initialization scripts、template、reference、caps、historical parent、Amendment 001のhash guardはPASS。

coarseを新規生成し、blockMesh/checkMesh（Mesh OK.）を完了。canonical初期化cloneのfoamRunは1 iteration、exit code 0、Endあり、fatal/FPE/NaN/Infなしで正常終了した。正常bannerの誤分類は発生していない。primary solverは全gridで未実行。

停止理由は `STOP_EVALUATOR_FAILURE_RUNTIME_EVIDENCE_COLLECTION`。今回作成したexecution_runner.pyがSelecting/Build/SIMPLE行だけを収集したため、複数行thermo辞書内のheRhoThermoを落とし、runtime_checkが未取得として停止した。担当agentが追加した実行checkerの不備である。raw log先頭95行にはheRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergyが契約どおり存在する。Stokes/Fourier/SIMPLEも記録されている。このSTOPはactual model mismatch、実FPE、Gate D numerical failureを示さない。

ユーザー指示section 24のevaluator failure STOPに従い、修正して自動再開／retryはしなかった。verify_initialization.pyはまだ未実行で、OQ-02とGate AはNOT_EVALUATED。初期化cloneのtime 1はformal solution/checkpointではない。

| Grid | Case/mesh | Primary | Computed | Accepted | Final iteration | Gate D |
|---|---|---|---|---|---|---|
| coarse 40² | 生成済み | 未実行 | NO | NO | NONE | NOT_EVALUATED |
| medium 80² | 未生成 | 未実行 | NO | NO | NONE | NOT_EVALUATED |
| fine 160² | 未生成 | 未実行 | NO | NO | NONE | NOT_EVALUATED |

主QoI・paper comparison（PRACTICAL_BENCHMARK_COMPARISON）・A–B差・Gate E/F/GはNOT_EVALUATED。数値を0で埋めていない。native A mass phiとB volume phi、およびsectionの異なるoperatorはNOT_LIKE_FOR_LIKEとしてCSVに明示。Route Bの計算／変更はなし。fine図は未生成。

coarseのinput/mesh/clone初期field hash、manifest、mesh/initialization logとSTOP根拠を `results/routeA/cases/A-Ra1e3-coarse/pre_primary_stop/` に封印した。primary segmentは0なのでend_N segmentは存在しない。生成したcase/mesh/cloneは削除／上書きせず保存する。既存保護対象108ファイルは前後hash一致。attempt 001のSTOP四成果物も不変。

Ra1e4 trioの技術準備はNO。次はFIX_ROUTE_A_EXECUTION_ISSUE：実行用checkerのmultiline thermo証拠収集をレビューし、既存coarseの保存証拠を保護して再開手順を決める。凍結済みclassifier、数値条件、model、solver設定は変更しない。新しいユーザー指示が必要。

詳細は [JSON](Ra1e3_trio_report.json)、[matrix](Ra1e3_trio_matrix.csv)、[A–B comparison](Ra1e3_routeA_vs_routeB.csv)。

```text
ROUTE_A_RA1E3_ATTEMPT = 002
ROUTE_A_RA1E3_TRIO = STOPPED
EFFECTIVE_CONTRACT_VERSION = 1.1
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
AMENDMENT_001_ACTIVE = YES
NORMAL_BANNER_MISCLASSIFIED_AS_FPE = NO
A_RA1E3_COARSE_COMPUTED = NO
A_RA1E3_COARSE_ACCEPTED = NO
A_RA1E3_COARSE_FINAL_ITERATION = NONE
A_RA1E3_COARSE_GATE_D = NOT_EVALUATED
A_RA1E3_COARSE_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E3_MEDIUM_COMPUTED = NO
A_RA1E3_MEDIUM_ACCEPTED = NO
A_RA1E3_MEDIUM_FINAL_ITERATION = NONE
A_RA1E3_MEDIUM_GATE_D = NOT_EVALUATED
A_RA1E3_MEDIUM_GATE_D_FAILURE_COMPONENTS = NONE
A_RA1E3_FINE_COMPUTED = NO
A_RA1E3_FINE_ACCEPTED = NO
A_RA1E3_FINE_FINAL_ITERATION = NONE
A_RA1E3_FINE_GATE_D = NOT_EVALUATED
A_RA1E3_FINE_GATE_D_FAILURE_COMPONENTS = NONE
RA1E3_GATE_E_DIAGNOSTIC = NOT_EVALUATED
RA1E3_GATE_F = NOT_EVALUATED
RA1E3_NEEDS_320 = NOT_EVALUATED
RA1E3_GATE_G = NOT_EVALUATED
ROUTE_A_VS_ROUTE_B_COMPARISON = NOT_EVALUATED
POST_CAP_EXTENSION_PERFORMED = NO
SOLVER_TUNING_PERFORMED = NO
AUTOMATIC_320_PERFORMED = NO
FORMAL_CRITERIA_CHANGED = NO
ROUTE_B_MODIFIED = NO
ATTEMPT_001_HISTORY_PRESERVED = YES
RA1E4_TRIO_TECHNICALLY_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_EXECUTION_ISSUE
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
