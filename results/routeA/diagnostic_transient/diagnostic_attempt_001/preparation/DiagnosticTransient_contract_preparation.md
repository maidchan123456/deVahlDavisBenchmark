# Route A diagnostic transient contract preparation report

Task: `PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT`  
Date: 2026-10-05 (Asia/Tokyo); ownership: `DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION`.

## 1. Overall preparation result

**INCOMPLETE**。独立診断契約 v1.0 の MD/JSON を作成した。ソースから診断式・評価段階・証拠設計を固定したが、U01–U04 を未解決の blocking fields として残す。solver/case/mesh/initialization は一切実行・生成していない。技術準備 NO、実行許可 NO。

契約: [説明文](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.0.md) / [JSON](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.0.json) / [SHA-256 sidecar](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.0.sha256)。JSON SHA-256: `3ea8c134b1c0468a455c8d090eb3b47dae510b06a9886eedbaa5f79aed8e152f`。これは未解決事項を含む設計の seal であり、完全な実行設定の凍結ではない。

## 2. Authority and provenance

開始 HEAD は要求された `fd129af05d43e3551cf0d4a037b5dd8f54ccbe4a` と一致。formal v1.7 JSON hash は `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60` と一致。AC §12/14、現行契約、Gate J prerequisite review、accepted A-Ra1e6-fine end_9000 の入力/判定/provenance、既存 source audit を限定参照した。無関係な全 repository 履歴の再監査はしていない。

local `/opt/openfoam13` の24 source files を equation/diagnostic に対応させて SHA-256 を保存。native algorithm と sparse matrix の境界・reference/correction を確認した。公開 Foundation source は補助照合であり、local source/binary の完全一致や将来 runtime の保証をここでは付与しない。既存 runtime provenance は参照資料とし、今の solver を起動していない。

## 3. Diagnostic ownership

`DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION`。formal execution contract の続番ではない。独立結果 namespace `results/routeA/diagnostic_transient/diagnostic_attempt_001/` を採用した。report はその `preparation/` に置く。既に sealed の formal attempt_008 に新規内容を混ぜず、そこにある review を read-only 参照するためである。

## 4. Formal Gate J separation

J は未実施、PASS=NOT_EVALUATED、currently allowed=NO のまま。H PASS は支持証拠だが formal blockers の免除にならない。core/Route A characterization/downstream/particle readiness は NO、全 Ra Gate F FAIL・needs_320 YES を保持。formal v1.7/current guard/AC/formal seals を変更していない。

## 5. Target physical case

Ra=1e6、Pr=0.71、160×160×1、betaDeltaT=1e-3 の original A-Ra1e6-fine。L=0.1 m、W=0.001 m、Th/T0/Tc=300.5/300/299.5 K。Boussinesq/eConst/internal energy、Stokes/Fourier の native Route A を固定。Gate H beta1e-4 側ではない。grid/physics は全 Co series で同一。

## 6. Initial condition

独立 cold start：internal U=0、T=T0、rho=rho0、K=phi=0。wall T は最初から Th/Tc、patch rho はその EOS 値。hRef=pRef=0、gh=g·x、p=rho(T)gh+pRef、p_rgh=0 を cell/physical patch で整合させる。pRefCell=12719。steady 最終 field の流用は禁止。constructor 後かつ solve 前の観測方式は U04。

## 7. Transient algorithm

native foamRun+fluid の preSolve→dt調整→時間更新→outer predictor/energy/thermo/pressure correctors→postSolve→write を確認。simpleRho=false、non-transonic/non-consistent、静的格子、nonOrthogonal=0 を固定。exact outer/inner counts・linear/relaxation/error policy は U01 未解決なので TRANSIENT_ALGORITHM=UNRESOLVED。PISO/PIMPLE の名称だけで完成扱いにしない。

## 8. Time scheme

`ddtSchemes { default backward; }`。可変刻み BDF2 の a=1+h/(h+k)、c=h²/[k(h+k)]、b=a+c と native old rho*old e/K products を使う。nOldTimes<2 は first-order startup limit。初期履歴を捏造せず記録し、secant storage と discrete BDF2 storage を区別。

## 9. Co series and controller

maxCo targets 0.5/0.25、conditional 0.125。adjustTimeStep=true、deltaTFactor=1.2、native min/cap rule を固定。初期 deltaT/finite maxDeltaT/overshoot policy は U02。cold Co=0 は startup step を拘束しない。log の prior-state control Co と新規 step 終了時の実測 Co を別記録する。

## 10. Inner convergence

UNRESOLVED U01。native outerCorrectorResidualControl の initial-residual/abs OR relative/final extra iteration の意味を確認した。small linear final residual は outer convergence の代用にならない。Ux/Uy/e/p_rgh の全 solve initial/final residual と iteration count、rho solve、corrector index を保存。非収束 step は series STOP・partial data保持、再試行/tuningは禁止。具体数値の根拠を steady Gate D から流用しない。

## 11. Dimensionless time

`t*=alpha0*t/L²=t/(710 s)` に固定。repository の参照熱拡散時間と整合し、local alpha(T) で時間軸を変えない。710 s は尺度であり停止時間ではない。

## 12. Termination and steady arrival

UNRESOLVED U03。minimum/maximum t*、物理時間 window、range/drift/confirmation、mass/energy/rho の arrival rule を閉じる必要がある。steady iteration9000 を seconds に変換しない。cap で未到達なら STEADY_NOT_REACHED、延長しない。final value は将来登録される同一長 physical confirmed window の time-weighted mean とし endpoint も保存。whole-run average は禁止。

## 13. Mass diagnostic

actual correctDensity の D_B rho_s+div(phi) を volume 積分し R_M,C=D_B M_C+Σboundary phi [kg/s] とする。native phi は kg/s。end-state residual と continuity-stage residual、secant rate、局所 L1/Linf、mass drift、EOS sync jump を分ける。mass rate scale=Mref/710=1.4084507042253522e-8 kg/s。psi=0 の closed pressure compatibility と reference cell に加えられた equation contribution を保存する。

## 14. Energy diagnostic

actual e equation に従い R_E=S_e+S_K+F_e+F_K+W_p+H_out−W_g−S_models [W] を定義。internal/kinetic storage、native phi transport、composite p/rho pressure work、Fourier explicit Laplacian+implicit correction、cell rho U·g を全て含む。Q_wall は inward positive。assembly matrix の lagged fields と end fields を混ぜず2残差に分ける。matrix residual b−Aψ は LHS−RHS のため符号反転し、既に volume 積分単位なので V を再乗算しない。Eref=0.01 J、Qref=kΔTW=1.4084507042253522e-5 W。pressure/gravity を解析的に相殺してから評価しない。

## 15. Thermo/rho synchronization

pressure correction 中の thermo rho copy→correctDensity→native continuity→postSolve rho=thermo.rho を stage 観測する。native transient continuity log は rho_s−rho_T discrepancy であり mass-equation residual ではない。postSolve による一致は代入で、mass保存の証明ではない。さらに p/p_rgh は再構成されないので pressure relation defect を保存。実際の内部段階取得/未緩和 matrix evaluator は U04。

## 16. Temporal comparison

`D_t(Q)=|Q_fineCo−Q_coarseCo|/|Q_fineCo|` を新規診断規約として固定した。既存 AC/review は分母未指定であり、低 Co を意図した細時間制御として比較参照にする理由を明記。trajectory は shared t* interval の raw node union に線形補間し、native grids を残す。保存残差用の oldTime inputs は補間しない。arrival time と normalized mass/energy residual の RMS/L1/Linf/integral も比較。

## 17. Conditional Co0.125

valid arrival と inner/evaluator evidence が成立した 0.5/0.25 の final Nu_bar_cavity/Umax/Wmax のどれか D_t>0.005 なら future Co0.125 を独立 cold start で追加。等号は target 内。未到達/invalid evidence/zero fine denominator は比較不能であり、勝手な third-series trigger にしない。最細2系列で再診断し、0.125 でも超過なら target unmet、第四系列は自動追加しない。Gate J PASS は付与しない。

## 18. Evidence and output design

全 step scalar/QoI/end fields、全 outer/pressure residual/stage diagnostics と time0 を保存。4097-point extrema と paper Nu 定義を保持。full field write は every timeStep、binary、purgeWrite0、diagnostic/time precision17。duration/caps 決定後に disk preflight。input/runtime/source/evaluator hashes、raw logs/oldTime/coefficient identity、field/CSV整合、plots、STOP/cap history、seal を計画。既存 steady analyzer の integer rounding/formal results write を使わない。

## 19. Unresolved items

| ID | Remaining closure |
| --- | --- |
| U01 | 正確な corrector/linear/maxIter/relaxation と per-step nonlinear convergence/error budget。 |
| U02 | cold-start deltaT、finite maxDeltaT、Co overshoot/underflow policy。 |
| U03 | minimum/maximum physical t*、arrival/confirmed window と数値 criteria。 |
| U04 | constructor/in-loop stage観測、未緩和 energy/reference matrix evaluator の取得・検証・floor policy。 |

mass/energy hard accuracy threshold は UNRESOLVED。根拠のない1e-6/1e-4/1%は追加していない。finite/positive-state/evaluator-health/evidence の STOP は登録済みだが、これらだけで実行準備完了にしない。

## 20. Technical readiness and verification

DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY=NO。scientific allowance は CONDITIONAL。完成した resolved definitions があることと、実行に必要な全設定が凍結されたことを区別する。

79 relevant pre-existing authority/design/baseline files の before/after SHA-256 は一致。formal v1.7 guard と Gate_J_authorized=false を再確認。JSON/MD/status/hash consistency と物性/可変刻み BDF2/sync decomposition の純粋代数検証は companion verification JSON に記録する。これは native evaluator の実装/実行検証ではない。

## 21. Exact next task

`FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT`。U01–U04 だけを source/theory/evaluator design により閉じ、独立 diagnostic revision を事前登録する。solver実行、case/mesh生成、formal J、320、Route B、particles は次のfix taskにも含めない。complete readiness後に別の明示RUN判断を行う。

推奨 next model: gpt-6.1-sol / medium。USER_DECISION_REQUIRED=YES。今回の依頼は準備だけであり、RUN permission を要求・推定していない。

## Final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_CONTRACT_PREPARATION = INCOMPLETE
DIAGNOSTIC_TRANSIENT_CONTRACT_PREPARATION = INCOMPLETE
STUDY_OWNERSHIP = DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_STATUS_CHANGED = NO
FORMAL_ROUTE_A_CONTRACT_VERSION = 1.7
FORMAL_ROUTE_A_CONTRACT_CHANGED = NO
DIAGNOSTIC_CONTRACT_CREATED = YES
DIAGNOSTIC_CONTRACT_VERSION = 1.0
TARGET_RA = 1000000
TARGET_PR = 0.71
TARGET_GRID = 160x160x1
TARGET_BETA_DELTA_T = 1e-3
INITIAL_CONDITION = REST_AND_UNIFORM_T0
TIME_DISCRETIZATION = BACKWARD_SECOND_ORDER
CO_SERIES = 0.5,0.25
CO_0125_CONDITIONAL = YES
CO_0125_TRIGGER = PRIMARY_QOI_DIFFERENCE_GT_0P5_PERCENT
GRID_HELD_FIXED = YES
PHYSICS_HELD_FIXED_ACROSS_CO_SERIES = YES
COLD_START_EACH_CO_SERIES = YES
TRANSIENT_ALGORITHM = UNRESOLVED
INNER_CONVERGENCE_RULE = UNRESOLVED
TRANSIENT_INNER_CONVERGENCE_RULE = UNRESOLVED
DIMENSIONLESS_TIME_DEFINITION = t*=alpha0*t/L^2=t/(710 s)
STEADY_ARRIVAL_RULE = UNRESOLVED
MAXIMUM_DURATION_RULE = UNRESOLVED
SAMPLING_RULE = time0 and every physical step; residual/stage diagnostics every outer/pressure solve; full fields every step
RESTART_POLICY = single continuous process per Co series; interruption invalidates primary; new authorized cold attempt; resume requires diagnostic revision
MASS_DIAGNOSTIC_DESIGNED = YES
MASS_STORAGE_TERM_INCLUDED = YES
BOUNDARY_MASS_FLUX_INCLUDED = YES
MASS_BALANCE_RESIDUAL_DEFINED = YES
THERMO_RHO_SYNCHRONIZATION_DIAGNOSTIC_DEFINED = YES
ENERGY_DIAGNOSTIC_DESIGNED = YES
ENERGY_STORAGE_TERM_INCLUDED = YES
WALL_HEAT_TERMS_INCLUDED = YES
PRESSURE_WORK_ACCOUNTED = YES
KINETIC_ENERGY_TERM_ACCOUNTED = YES
GRAVITY_WORK_ACCOUNTED = YES
ENERGY_BALANCE_RESIDUAL_DEFINED = YES
MASS_ENERGY_HARD_THRESHOLD = UNRESOLVED
PRIMARY_TEMPORAL_QOIS = Nu_bar_cavity,Umax,Wmax
TEMPORAL_PRIMARY_DIFFERENCE_TARGET = 0.5_percent_diagnostic
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
FORMAL_GATE_J_CLAIM_ALLOWED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
GRID_320_EXECUTED = NO
SOLVER_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
DIAGNOSTIC_TRANSIENT_EXECUTED = NO
ROUTE_B_RERUN = NO
PARTICLE_COUPLING_STARTED = NO
ACCEPTANCE_CRITERIA_CHANGED = NO
FORMAL_STATUS_CHANGED = NO
FORMAL_GATE_J_AUTHORIZED = NO
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = CONDITIONAL
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
DIAGNOSTIC_CONTRACT_SHA256 = 3ea8c134b1c0468a455c8d090eb3b47dae510b06a9886eedbaa5f79aed8e152f
```

## Verification artifacts

[Preparation JSON](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_contract_preparation.json) / [Verification JSON](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_contract_preparation_verification.json) / [Preparation seal](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/preparation_sealed_sha256.json)。
