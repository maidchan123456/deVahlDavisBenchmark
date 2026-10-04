# Route A execution contract v1.0

凍結日: 2026-10-04（Asia/Tokyo）。開始HEADは指定の `d4624b29030521f10b24a59bf6a7af528533bd8c` と一致。**solver、case生成、mesh生成なし**。既存数値設定／規範／accepted dataは変更していない。

**FROZEN / Gate D READY YES / 最初のRa1e3 trioは技術的準備完了。** 今回は実行の許可ではない。次のユーザー実行指示を受けて `RUN_ROUTE_A_RA1E3_TRIO` を開始する。

## 1. 凍結対象とhash guard

authoritative machine-readable file: [routeA_execution_contract.json](routeA_execution_contract.json)。

```text
ROUTE_A_EXECUTION_CONTRACT_VERSION = 1.0
CONTRACT_SHA256 = 33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936
```

SHA-256は**JSONの保存済みbytes**のdigest。本Markdownのdigestではない。自己参照を避け、digestはJSON外の本書に保存する。実行前にJSONのdigestが上記に一致し、JSON内のevaluator/generator/template/caps CSV hashも一致することを確認する。違えば**case生成／mesh／solverを始める前にSTOP**。

前回preflightのD未確定・iteration cap null・自動延長不可という歴史的計画は、この契約の判定手順／事前登録継続に関する部分だけを更新する。前回文書自体は保存する。F/G policy、正式Gate閾値・上位status論理、smokeの位置づけは変えない。

結果を見て契約をin-place改訂しない。変更は別amendmentにreason、date、user authorization、version/hash、影響caseを記録する。過去caseを新基準で自動昇格しない。

## 2. Frozen numerical model

既存preflight JSON、canonical templateとA-COND/A-SMOKEの必要辞書を照合し**一致**。既存値の修正なし。

| 項目 | 固定値 |
|---|---|
| distribution / version / historical build | OpenFOAM Foundation v13 / 13-441953dfbb42 |
| solver / steady algorithm | foamRun + solver fluid、PIMPLE辞書のsteady SIMPLE mode、nOuterCorrectors=1 |
| thermo | heRhoThermo / pureMixture / const / eConst / Boussinesq / specie / sensibleInternalEnergy |
| momentum / thermal | laminar Stokes / laminar Fourier |
| sources | turbulence、radiation、MRF、fvModels、fvConstraints、particleなし |
| ddt / spatial | steadyState、既存Gauss linear、orthogonal diffusion、linear interpolation/snGrad |
| linear tolerances / relTol | p_rgh/U/e=1e-10、relTol=0 |
| relaxation | p_rgh=0.3、U=0.5、e=0.7 |
| correctors | nCorrectors=2、nNonOrthogonalCorrectors=0 |
| timing / field output | deltaT=1、writeInterval=100、writePrecision=16、purgeWrite=0、residualControlなし |

templateのmomentumTransportは `simulationType laminar`。Stokesは既存runtime/auditで確認された選択であり、新しいモデル指定を辞書へ足さない。今後実際に選ばれたmodel/build等が異なればSTOP。

## 3. Gate D exact logic

```text
GATE_D_PASS =
NORMAL_EXIT
AND NO_FATAL_OR_NAN
AND INPUT_PROVENANCE_PASS
AND QOI_RWIN_PASS
AND RESIDUAL_PASS
AND HEAT_TREND_PASS
```

- NORMAL_EXIT: **process exit_code=0**かつ選択segment logの独立行 `End`。substring一致や反復上限到達だけでは足りない。
- NO_FATAL_OR_NAN: segment全体にfatal/FPE/NaN/Inf/divergenceがなく、必須fieldとmonitor値がfinite。実行時の全区間health flagと最終field検査を保存する。
- INPUT_PROVENANCE_PASS: 版/model、BC/物性/gravity、実Ra/Pr/grid、input/mesh hash、OQ-02がmanifestと一致。継続時の登録済みcontrol変更は別hashで管理。
- QOI_RWIN_PASS: Nu_bar_0/Umax/Wmaxがそれぞれ既存5e-4以下。
- RESIDUAL_PASS: Ux/Uy/e/p_rghの最終normalized **Initial residual**がそれぞれ1e-7以下。
- HEAT_TREND_PASS: 同じ窓のphysical heat imbalanceのOLS slope≤0。

density residual閾値は追加しない。rhoのfinite/positive、T/rho範囲、rho0[1-beta(T-T0)]との最大absolute/relative差、native mass診断を保存する。EOSから計算したthermo-density proxyと独立registry dumpを区別し、独立thermo rhoがない場合はNOT_AVAILABLE。これを「独立fieldを検証済み」としない。

不足したflag、曖昧なparser、欠損cadence、壊れたevidenceは**evaluator failureでSTOP**。通常の数値threshold FAILと区別する。evaluator単独のnumerical_checks_passを正式Gate D PASSとして使わない。

## 4. Residual fields / parser

| field | 適用 |
|---|---|
| Ux / Uy | active 2D components。OpenFOAM yがpaper Z。Uzはempty方向でinactive |
| e | energyのnormalized Initial residual。primary T residualは作らない |
| p_rgh | Paのpressure residual。Bのkinematic pressureとは別 |

canonical `analyze_case.py:parse_residual_lines` は `Solving for ..., Initial residual = ..., Final residual = ...` の**Initial**を取得し、同じ反復・同じfieldの全solve/correctorの最大を保存する。最終checkpoint Nの値を1e-7と照合する。Final residualは別欄の診断であり代用しない。

同じ窓の各反復でfield取得が可能か検査するが、Hard residual thresholdを窓内最大へ変更しない。非finite、整数でないsteady iteration、重複restart iterationはSTOP。入力logは1 segmentに限定する。

## 5. Monitor / window contract

最終checkpoint Nの**[N-199,N]、両端inclusive、200反復**。例N=3000なら2801–3000。200反復は200個の整数iteration labelを数える意味で、端点差は199。

| series | 既存sampling interval | 必須samples | 例N=3000 |
|---|---:|---:|---|
| Nu_bar_0 / physical heat imbalance | 1 | 200 | 2801…3000 |
| residual records | 1 | 200 | 2801…3000 |
| Umax / Wmax monitor | 10 | 20ずつ | 2810,2820,…,3000 |

新cadenceは作らない。公式wallHeatFluxは毎反復、centrelineMonitorは既存257点・cellPointFace・10反復ごと。Umaxはvertical.xyのU_x正最大、Wmaxはhorizontal.xyのU_y正最大をL/alpha0で無次元化する。最終表の4097点法は別に保持し、monitorと最終reportのsampling_methodを明示する。

`Rwin=(max-min)/max(abs(mean),1)`、scaleは全3量で1。欠けたsamplesを補間して通さない。Nは3000の倍数なのでcadence endpointsが固定される。

restart窓を跨がない。毎segment3000反復の最後200だけを使用する。新segmentのstart iterationは既存checkpointで、最初のfresh solveはstart+1。壁時系列は `wallHeatFluxMonitor/<segment_start>/wallHeatFlux.dat`、centrelineは絶対iteration folder、residualは同segment immutable logを選択する。重複を黙って平均／上書きしない。

## 6. Nu_bar_0 identity: CONFIRMED

formal monitorは **hot-only**:

```text
Nu_bar_0 = Q_hot / (k*DeltaT*W)
Q_hot = integral_hot wallHeatFlux dA
A_hot = L*W
```

公式wallHeatFlux=-qでhot Q>0、cold Q<0。hotのarea-meanにL/(k DeltaT)を掛ける定義と上式は同じ。no-slip壁ではnormal convective flux=0なので、X=0のpaper-definition Nu_bar_0は伝導項だけである。一定k・orthogonal boundary gradientの既存A1/A2と対応する。

旧 `(Q_hot-Q_cold)/(2*k*DeltaT*W)` は両壁平均で**同一量ではない**。legacy Rwinは診断として残し、正式Gate Dに使用しない。新しい `Gate_D_monitor_evaluation.Rwin.Nu_bar_0` が正式量である。

future convergence.csvのNu_bar_0はhot path2を毎反復保存し、保存Tからの独立path1は `Nu_bar_0_path1_snapshot` に別保存する。最終metricsの既存paper QoI定義は維持する。今回canonical accepted CSV/metricsは書き換えていない。

## 7. Physical heat imbalance / exact trend

coldは負のQを反転してpositive transport directionにそろえる。

```text
Nu_hot =  Q_hot/(k*DeltaT*W)
Nu_cold = -Q_cold/(k*DeltaT*W)
epsilon_Q = abs(Nu_hot-Nu_cold)/((Nu_hot+Nu_cold)/2)
          = 2*abs(Q_hot+Q_cold)/(Q_hot-Q_cold)
```

Q_hot>0、Q_cold<0を要求し、符号をabsで隠さない。paper-definition section Nuをphysical energy conservationと混同しない。

入力は**元のwallHeatFlux.datのQ decimal token**、200 samples、同じ[ N-199,N ]、独立変数はabsolute iteration。intercept付きOLS:

```text
slope = sum((i-mean(i))*(epsilon_Q-mean(epsilon_Q)))
        / sum((i-mean(i))^2)
PASS: slope <= 0
FAIL: slope > 0
```

既存Q出力はscientific formatで小数点後16桁、17 significant digits。writePrecision=16を変更しない。tokenは少なくともこの精度を要求し、浮動小数点へ丸めず `Fraction` でepsilon、mean、slopeの符号を**厳密有理数計算**する。float slopeは表示だけで、PASS/FAILは `heat_slope_sign_exact` を使う。表示がunderflowで0でもpositive exact signはFAIL。

source低精度／欠損／重複／nonfinite／符号不整合なら `HEAT_TREND_EVALUATOR_UNRESOLVED` またはEVALUATOR_FAILUREでSTOP。positive toleranceを追加しない。ゼロは保存された17桁時系列でのゼロであり、出力桁より細かい物理傾向を保証するものではない。

## 8. Initial / continuation / caps

```text
INITIAL_ITERATIONS = 3000
CONTINUATION_INCREMENT = 3000
ALL_CASE_ITERATION_CAP = 30000
```

理由: minimalの3000と同じ初回、sampling/write cadenceに整合する共通increment。B fineの18000–21000等をbudget参考とし、30000を全case共通capにする。A収束保証でもB floor解釈の転用でもない。

| case | initial | increment | absolute cap |
|---|---:|---:|---:|
| A-Ra1e3-coarse | 3000 | 3000 | 30000 |
| A-Ra1e3-medium | 3000 | 3000 | 30000 |
| A-Ra1e3-fine | 3000 | 3000 | 30000 |
| A-Ra1e4-coarse | 3000 | 3000 | 30000 |
| A-Ra1e4-medium | 3000 | 3000 | 30000 |
| A-Ra1e4-fine | 3000 | 3000 | 30000 |
| A-Ra1e5-coarse | 3000 | 3000 | 30000 |
| A-Ra1e5-medium | 3000 | 3000 | 30000 |
| A-Ra1e5-fine | 3000 | 3000 | 30000 |
| A-Ra1e6-coarse | 3000 | 3000 | 30000 |
| A-Ra1e6-medium | 3000 | 3000 | 30000 |
| A-Ra1e6-fine | 3000 | 3000 | 30000 |

全checkpoint: 3000,6000,…,30000。**同じcaseの同じ解経路を継続**する。D FAILで初期化し直すretryとは区別する。

1. segment正常／有限／provenance・evaluator正常を確認し、全artifactをseal。
2. D PASSならcomputed YES / accepted YESとしてcase終了。
3. D FAILかつN<30000ならstartFrom latestTime、endTime=N+3000で継続。
4. D FAILかつN=30000ならCONVERGENCE_NOT_REACHED、computed YES / accepted NOを保存し次caseへ。
5. evaluator/health/provenance異常ならbatch STOP。

未来の新規formal caseでsegment間に変えてよいcontrolは**startFrom/endTimeだけ**。deltaT/solver/correctors/relaxation/tolerances/schemes/model/mesh/monitor/write cadenceは固定。実行中の辞書編集なし。initial case_manifestはimmutable、segment controlDictの新hashと登録2key差分を別manifestに保存する。

restart最新時刻は前のsealed Nと一致し、field/mesh hashを照合する。OQ-02は初期状態で実施済みとし、進展済みrestartにp_rgh=0を再要求／再初期化しない。

**POST_CAP_EXTENSION_ALLOWED=NO、AUTOMATIC_RETRY=NO。** cap後は別user decision/amendment。結果を見てincrement/capやsolver settingsを変えない。

## 9. STOP / F/G scope

STOP: environment/build/version mismatch、wrong solver/physics、input/Ra/Pr/mesh/OQ-02 mismatch、NaN/Inf/FPE/fatal/divergence、過去evidence破損、evaluator failure/ambiguity。

STOPしない: 正常有限のD numerical FAIL（登録incrementでcapまで）、A steady paper mismatch、F non-monotonic/FAIL、G formal FAIL、local Nu diagnostic mismatch。

finite residual plateauやpositive heat slopeだけをdivergenceと呼ばない。分類できない危険な状態はSTOP。solver tuningへの自動移行なし。

- F: formal評価、FAIL/needs_320 YES維持、non-monotonic/invalid orderではp/GCI=null、320は自動実行しない。unaccepted dataのformal評価を強行しない。
- G: formal FAILとnative mass/reconstructed U/physical heat/symmetryを保存し、原因候補はmodel/discretization/iteration/postprocessingまで。閾値研究、microcase、tolerance study、方法再設計、B研究再開なし。
- どちらもmatrix収集は非blocking。正式上位statusに必要なF/G PASSを免除した意味ではなく、particle couplingの保存要件にも代替しない。

## 10. Continuity / energy / A–B

| quantity | 固定operator・単位 |
|---|---|
| A_native_mass_phi | corrected phi、kg/s。face balance/Vのmean absolute divergence [kg/(m³ s)] |
| epsilon_mass_phi_A | L mean_V|div(phi)|/(rho0 max|u|)。legacy epsilon_mはoperator metadata付きalias |
| A_reconstructed_U_divergence | cell UからGauss linear div(U) [1/s]。no-slip/empty、体積加重 |
| epsilon_volume_reconstructed_U_A | L mean_V|div(U)|/max|u|。legacy epsilon_vと対応 |
| symmetry | 既存design §13.2の180°写像、volume L2、theta／dimensionless velocity RMSで規格化、既存zero guard 1e-12・0.2%維持 |

A massとB volume phiの単位を混ぜず、B epsilon_phiを名称だけコピーしない。新しいphi/rhof studyは追加しない。

保存するenergy-related診断はphysical Q_hot/Q_cold/epsilon_Q、e residual、T/rho/e（保存されていれば）範囲、EOS整合、native mass。wall heat balanceだけで全energy保存やtransient保存を検証済みとしない。full storage/work budgetはNOT_EVALUATEDとし、Gate Jで必要になるraw fields/fluxes/hashを引き継ぐ。新Hard閾値なし。

A–B join keysはRa_actual/grid/QoI_definition/sampling_method/postprocessing_version。Nu_cavity、Nu0/half/1、Umax/Wmax＋位置、local Nu extrema＋位置、heat、native continuity、reconstructed U、theta/U symmetryを保存する。

非零かつ同一定義のscalarは|A-B|/|B|、位置は絶対座標差。zero/near-zeroで規格化が不明ならnull/ABSOLUTE_ONLYまたはNOT_EVALUATEDとし、cutoffを作らない。A–B Hard thresholdなし。

**LIKE_FOR_LIKE=NO**: A native mass vs B native volume、A section再構成U vs B section native phiなど。nativeの物理解釈と離散operatorを分け、同名で直接Hard比較しない。B accepted9行はaccepted baseline、Ra1e6はunaccepted diagnostic。Bにない列は既存出力からread-onlyで取得するかNOT_EVALUATEDにし、B resultを書き換えない。

## 11. Case generation / first trio execution recipe

今回は生成しない。次の実行指示後、契約hashと全implementation/template hashを照合したうえで以下を行う。

1. canonical generatorを使い、`cases/routeA/A-Ra1e3-{coarse,medium,fine}` の**新規**destinationを生成。既存destinationはSTOP。各gridは40/80/160、Ra=1000、endTime=3000。
2. generator CLIはminimal roleのA-COND/A-SMOKEだけを受けるため、`--case-id A-SMOKE --name <formal ID>` で新規割当する。raw生成manifestを `generated_manifest_original.json` に保持し、**新規caseのmetadataだけ**case_idをformal IDへ登録する。generator_role、contract version/hash、generator hashを記録し、OpenFOAM inputは変更しない。これは既存A-SMOKEの再利用・promotionではない。
3. generated input/Ra/Pr/model/hashを確認し、新規caseのblockMesh/checkMeshを行う。既存caseを触らない。
4. canonical prepare_initialization_check.pyの既存1反復clone手順とverify_initialization.pyで、cell/4wall OQ-02を**primary solve前**に確認・保存。新microcase研究ではない。
5. solverを逐次で実行し、実process exit_code・segment全体health flags・immutable logを保存。
6. canonical analysisを `--segment-start S --solver-log IMMUTABLE_SEGMENT_LOG` で実行。formal Gate Dの外部flagsとnumerical評価を結合し、artifactをseal。
7. cap内継続または次caseへ。coarse完了の記録をmedium終了まで待たない。

既存run_case.shをblind batch/restartとしてそのまま使わない。mesh/initializationを毎回呼び、explicit initialization verificationをprimary前に挟まず、logを同名へ出すためである。次taskは既存のcanonical stepsを個別に実施する。新solver runnerは今回作っていない。

## 12. Partial result protection / computed vs accepted

各segmentごとに `results/routeA/cases/<formal ID>/segments/end_<N>/` をimmutable証拠単位とする。

保存: case/segment manifest、contract hash、input/mesh/log/field hashes、OQ-02、process exit/health、metrics/convergence、formal Gate D全boolean、raw wall Qと20 centreline files、Initial/Final residual出力、computed/accepted、comparison（欠損なら理由付きNOT_EVALUATED）。

canonical analyzerがcurrent working出力を書いた直後に、**継続前**にsegment snapshotとraw sourceをsealする。次segmentがworking metricsを更新しても前segmentのevidenceを失わない。case status/aggregateはsealed artifactを確認してatomicに更新する。

COMPUTEDは正常有限のfield・metrics・provenance保存、ACCEPTEDはformal D PASS。cap時のnormal FAILはcomputed YES / accepted NO。未完runはPARTIAL/STOPPED、出所不明はINVALID/UNRESOLVED。完了caseを巻き戻さず、FAILを削除・平均・丸めで隠さない。

## 13. Evaluator correction / dry validation

変更は**analyze_case.pyの解析部分のみ**。正式hot-only Nu、exact heat trend、残差parser、segment source指定を追加。数値・物理辞書は変更なし。legacy Rwin欄は保存するがformal判定に使わない。

dry validationはhelperだけをread-onlyで既存dataへ適用し、main()のresult writerは呼んでいない。solver logは各caseの**tail 4000行のみ**。accepted result/statusは無変更。

| dry case | window / samples | Nu_bar_0 Rwin | heat OLS slope / iteration | exact sign | max final Initial residual | dry evaluator |
|---|---|---:|---:|---:|---:|---|
| A-COND | 2801–3000、Nu/heat200、U/W20 | 4.14523648e-5 | -4.79812287e-11 | -1 | 2.70767065e-8 | PASS |
| A-SMOKE | 同上 | 0 | 0 | 0 | 1.17104748e-10 | PASS |

2900/3000の保存Tのpath1 Nuとofficial hot-Q path2の絶対差は、COND最大7.954e-13、SMOKE5.675e-13。既存2経路許容0.1%内を確認し、定義一致を解析とデータで確認した。新identity閾値なし。

memory内fixtureでpositive/zero/negative heat slope、hot-onlyとpair averageの区別、Initial/Final/corrector最大、欠損cadence・低精度・重複restartの拒否も確認。CFD caseやtest fileは生成していない。dry PASSはevaluatorの動作確認であり、A-COND/A-SMOKEのformal matrix acceptance付与ではない。

## 14. Next single task / final status

**NEXT_SINGLE_TASK = RUN_ROUTE_A_RA1E3_TRIO**。coarse→medium→fine、parallelなし。contract digest一致・runtime preflight・各caseの初期化検証は実行時も必須。技術的準備YESは将来のユーザー実行指示の代替ではない。

推奨はユーザー指定の `gpt-6.1-sol / medium`。範囲はtrioのみで、残り9case/H/J/320/tuningへ自動拡張しない。

```text
ROUTE_A_EXECUTION_CONTRACT = FROZEN
ROUTE_A_EXECUTION_CONTRACT_VERSION = 1.0
CONTRACT_SHA256 = 33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936
ROUTE_A_GATE_D_READY = YES
GATE_D_QOI_MONITOR_IDENTITY = CONFIRMED
GATE_D_RESIDUAL_FIELDS = Ux,Uy,e,p_rgh
GATE_D_RESIDUAL_LIMIT = 1e-7
GATE_D_RWIN_QOIS = Nu_bar_0,Umax,Wmax
GATE_D_RWIN_LIMIT = 5e-4
GATE_D_WINDOW_ITERATIONS = 200
GATE_D_SAMPLING_INTERVAL = 1
GATE_D_HEAT_TREND_EVALUATOR = FROZEN
GATE_D_HEAT_TREND_RULE = SLOPE_LE_ZERO
INITIAL_ITERATIONS = 3000
CONTINUATION_INCREMENT = 3000
ITERATION_CAP_POLICY = FROZEN
AUTOMATIC_CONTINUATION_WITHIN_CAP = YES
POST_CAP_EXTENSION_ALLOWED = NO
AUTOMATIC_RETRY = NO
AUTOMATIC_SOLVER_TUNING = NO
AUTOMATIC_320 = NO
GATE_F_BLOCKS_MATRIX = NO
GATE_G_BLOCKS_MATRIX = NO
COMPUTED_ACCEPTED_SEPARATED = YES
A_B_OPERATOR_COMPATIBILITY_RULE = FROZEN
EVALUATOR_DRY_VALIDATION = PASS
SOLVER_EXECUTED = NO
CASE_CREATED = NO
FORMAL_CRITERIA_CHANGED = NO
FIRST_SOLVER_UNIT = A-Ra1e3-coarse,A-Ra1e3-medium,A-Ra1e3-fine
FIRST_SOLVER_UNIT_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RUN_ROUTE_A_RA1E3_TRIO
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```

GATE_D_SAMPLING_INTERVAL=1はNu/heatのcadence。U/Wは既存interval10、20samplesで、単一cadenceへ変更した意味ではない。Git add/commit/pushなし。
