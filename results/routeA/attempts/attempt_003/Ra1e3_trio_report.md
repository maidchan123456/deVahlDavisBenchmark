# Route A Ra1e3 attempt 003

**STOPPED after coarse primary checkpoint 3000**。HEADは指定9c1baa6f3b92a9d53512bb6008e8b1cbc2c11fddと一致。v1.2、runtime checker、analyzer、全implementation/template/caps/reference/parent/amendment hash guardはPASS。

保存済みcoarseを再利用し、input/template/Ra/Pr/mesh/clone/sealを再照合。clone solverは再実行していない。canonical runtime provenanceはPASS。canonical OQ-02はinternal/physical wallsともPASS、cell relation residual最大8.6736e-18 Pa、patch最大5.2042e-18 Pa（既存1e-12 Pa以内）。Gate AはPASS。

coarse primary 0→3000を実行、exit code 0、独立Endあり。全segmentのfatal/FPE/NaN/Inf/明示的divergence evidenceなし、必須field finite、rho positive。runtime selectionはcanonical checkerでPASS。正常bannerのFPE誤分類なし。primary elapsed 7.002 seconds。

その後canonical analyzer mainが `analyze_case.py:348` のpaper comparisonで `KeyError: 'Umax'`。calculated辞書はNu/local Nuしか含まないのに、referenceの全keyを参照している。Umax等はその後で計算されるため、この時点で未定義。このevaluator failureによりbatch全体STOP。analyzer/classifier/contract変更やretry/continuationはしていない。

| Grid | Primary checkpoint | Computed | Accepted | Gate D |
|---|---:|---|---|---|
| coarse | 3000 | NO | NO | NOT_EVALUATED |
| medium | NONE | NO | NO | NOT_EVALUATED |
| fine | NONE | NO | NO | NOT_EVALUATED |

COMPUTEDをNOとした理由は、required canonical metrics生成・評価が完了していないため。正常終了したprimary checkpointとfinite raw fieldsは別途保存済みで、計算が行われなかったという意味ではない。

coarse raw checkpointのQoIを既存pure helperと固定4097点centreline定義でread-only保存した。以下は**diagnostic only**でformal metricsの代替ではない。

| QoI | Coarse checkpoint diagnostic |
|---|---:|
| Nu_bar_cavity | 1.118855173 |
| Nu_bar_0 | 1.11861213 |
| Nu_bar_half | 1.11873791 |
| Nu_bar_1 | 1.118612176 |
| Umax | 3.648078448 |
| Umax_Z | 0.8125 |
| Wmax | 3.689537161 |
| Wmax_X | 0.1875 |
| Nu_hot_local_max | 1.51056348 |
| Nu_hot_local_max_Z | 0.08857841034 |
| Nu_hot_local_min | 0.6898370869 |
| Nu_hot_local_min_Z | 1 |

frozen monitor helperによる[2801,3000]のread-only診断は、Nu Rwin=0、Umax Rwin=3.79637779e-10、Wmax Rwin=3.80570852e-10、Initial residual4量すべて≤1e-7、exact heat slope sign=0でnumerical components PASS。数値helper version 1.0は不変。しかしcanonical mainのevaluator failure後にformal Gate D/ACCEPTEDへ昇格していない。Gate D failure componentは未判定で、STOP理由と区別する。

paper comparisonはPRACTICAL_BENCHMARK_COMPARISONとしてNOT_EVALUATED（canonical comparison失敗）。A–B比較、fine Gate E/G、accepted trio Gate FもNOT_EVALUATED。native A mass phi対B volume phiと異なるsection operatorはNOT_LIKE_FOR_LIKE。Route Bの再計算／変更なし。

raw solver log、runtime/health、Q tokens、20 centreline sets、全residual、field hashes、input/mesh/control/OQ-02をraw sealとして保存した後にanalyzerを実行した。停止後、diagnostic-only結果とevaluator tracebackを追加して `results/routeA/cases/A-Ra1e3-coarse/segments/end_3000/` を最終checksumで封印した。既存raw seal checksumsも一致。native final fieldsはcase/3000に残し、hashで参照する。過去attempt 001/002とcoarse pre_primary_stopを含む保護対象194ファイルは不変。

medium/fineは未生成。fine図なし。Ra1e4の技術準備はNO。次はFIX_ROUTE_A_EXECUTION_ISSUE：canonical analyzerのpaper比較key準備順序を別taskでレビューし、保存済み3000 checkpointからの再開方針と必要amendmentを決める。今回は自動修正／再開しない。

詳細は [JSON](Ra1e3_trio_report.json)、[matrix](Ra1e3_trio_matrix.csv)、[A–B](Ra1e3_routeA_vs_routeB.csv)。

```text
ROUTE_A_RA1E3_ATTEMPT = 003
ROUTE_A_RA1E3_TRIO = STOPPED
EFFECTIVE_CONTRACT_VERSION = 1.2
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
EFFECTIVE_CONTRACT_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
RUNTIME_CHECKER_HASH_VERIFIED = YES
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
ANALYZER_HASH_VERIFIED = YES
ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
AMENDMENT_001_ACTIVE = YES
AMENDMENT_002_ACTIVE = YES
COARSE_EXISTING_CASE_REUSED = YES
COARSE_INITIALIZATION_CLONE_RERUN = NO
COARSE_RUNTIME_PROVENANCE = PASS
COARSE_OQ02 = PASS
A_RA1E3_COARSE_COMPUTED = NO
A_RA1E3_COARSE_ACCEPTED = NO
A_RA1E3_COARSE_FINAL_ITERATION = 3000
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
FORMAL_CRITERIA_CHANGED = NO
SOLVER_TUNING_PERFORMED = NO
POST_CAP_EXTENSION_PERFORMED = NO
AUTOMATIC_320_PERFORMED = NO
ROUTE_B_MODIFIED = NO
ATTEMPT_001_HISTORY_PRESERVED = YES
ATTEMPT_002_HISTORY_PRESERVED = YES
RA1E4_TRIO_TECHNICALLY_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_EXECUTION_ISSUE
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
