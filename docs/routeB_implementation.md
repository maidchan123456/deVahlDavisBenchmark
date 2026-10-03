# Route B — Foundation v6 minimal implementation record

記録改訂: 1.3（2026-10-03）。実施日: 2026-09-30（Asia/Tokyo）。実行時の対象仕様: `benchmark_spec.md` v1.1、判定基準: `acceptance_criteria.md` v1.1、実装根拠: `routeB_design.md`。現行の交差参照は仕様・判定基準とも v1.4で、閾値は実行時から変更していない。

### 現在の status summary

| 項目 | 状態 |
|---|---|
| `ROUTE_B_AUDIT_PASS` | **付与**。根拠は `routeB_design.md` の v6 ソース監査 |
| minimal-case Gate A | **PASS**。Foundation v6 build、入力、mesh、kinematic pressure、`alphat=0` を確認 |
| Route B Gate C | **PASS**（B-COND） |
| Route B smoke / minimal implementation | **PASS**（B-SMOKE） |
| full Gate D/E/F/G/K | **未実施** |
| `BENCHMARK_CORE_PASS` | **未付与** |

CFD field、数値条件、失敗・無効化試行、diagnostic concern は変更していない。2026-10-03 に保存済み field だけを再後処理し、旧 Nu 比較の定義誤りを訂正した。solver は再実行していない。

### Nu 定義訂正と再後処理

旧記録は高温壁平均 `2.257421662...` を Table V の全領域平均 `2.243` と比較していた。この比較は異なる定義の混同であり無効である。原論文の $Q=U\theta-\partial\theta/\partial X$ に従い、全鉛直 face plane を再評価した。内部 face の対流項は保存済み v6 volume flux `phi` と線形補間した $\theta_f$、伝導項は直交2-cell 温度勾配と face 面積を用いる。全領域平均は cell-volume $U\theta$ 積分と固定壁による伝導積分1で計算し、Simpson 則は使わない。

高温壁局所極値は raw face-centre 値と、固定5点局所4次多項式による benchmark 値を分離した。内部極値は微分根、端点は端の5点から明示的に外挿する。全量を `metrics.json`、summary、`section_nusselt.csv` に保存した。

Table V 基準値は canonical `reference/de_vahl_davis_table_v.csv` だけから読む。原論文比較は符号付き相対差と絶対相対誤差、位置の符号付き差と絶対誤差を別フィールドに保存する。legacy `error` は互換用の符号付き差であり Gate に使わない。`Nu_bar_cavity` は cell-volume primary、`Nu_bar_cavity_from_section_trapezoid` は独立な台形積分 diagnostic であり、方法相対差の分母は $|Nu_{cell}|$ に固定した。

accepted 結果に使った v6 実行側の5スクリプトを canonical `Scripts/routeB/` に hash 一致を確認して収録した。収録後、Nu 定義は変えずに canonical reference 読み込み、誤差フィールド分離、方法差、manifest provenance を v6/canonical の両方へ同一内容で追加した。旧 accepted 時の script hash、新しい実行側/canonical hash、両者の一致は `run_manifest.json` に記録する。この変更は保存済み field の後処理のみであり、solver、physics、BC、scheme、relaxation、tolerance、Gate 閾値を変更していない。

## 1. Pre-implementation plan

- v6 activation: `source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc`。確認値は `foamVersion=OpenFOAM-6`、`WM_PROJECT_VERSION=6`、`WM_PROJECT_DIR=/home/mirai/OpenFOAM/OpenFOAM-6`、`WM_OPTIONS=linux64GccDPInt32Opt`、binary `/home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam`。
- execution root: `/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark`。case と実行・後処理 script はこの下だけに作る。
- canonical research root: `/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark`。v13 bashrc は隔離 subshell で path を読むだけとし、canonical document/result はこの下に保存する。v6 の実行 shell に v13 環境を source しない。
- authorized cases: B-COND（Ra=0、80×80×1）と B-SMOKE（Ra=1e4、40×40×1）のみ。Gate C 合格後だけ B-SMOKE を実行する。
- solver/model: native Foundation v6 `buoyantBoussinesqSimpleFoam`、Newtonian `nu=1e-5 m2/s`、`beta=1e-3 1/K`、`TRef=300 K`、`Pr=0.71`、`Prt=0.85`、laminar/Stokes、no radiation/MRF/fvOptions。
- pressure: kinematic `p_rgh` だけを入力し、`0/p` は作らない。`p_rgh=0`、`hRef=0`、中心最近傍の最小 cell ID を `pRefCell`、`pRefValue=0 m2/s2` とする。solver 生成 `p=p_rgh+rhok*gh` と finite field を実行時に確認する。
- alphat: MUST_READ の `0/alphat` を内部と4物理壁で0、front/backをemptyとする。実行後も cell/patch の最大絶対値0、runtime の laminar/Stokes 選択を確認する。
- schemes: steadyState、`grad(U)` を含む Gauss linear、`div(phi,U)`/`div(phi,T)` と viscous-stress div を Gauss linear、全 laplacian を Gauss linear orthogonal、linear interpolation、orthogonal snGrad。一次 upwind/limiterなし。診断 `div(U)` も Gauss linearで事前に明示する。
- SIMPLE: native steady SIMPLE、`momentumPredictor yes`、`nNonOrthogonalCorrectors 0`。PCG/DIC と PBiCGStab/DILU、絶対 tolerance `1e-10`、`relTol=0`。初期 relaxation は `p_rgh=0.3`, `U=0.5`, `T=0.7`、residualControlなし、3000反復、fieldを10反復ごとに保存する。
- Nu B1: 当初は各保存時刻で v6 `postProcess -func grad(T)` を使う計画とした。実行時にインストール済み v6 の function-object 辞書 digest が `OSHA1stream.sinkFile_` で停止したため、同じ v6 patch `snGrad()` の式 `(Twall-Towner)*deltaCoeffs` を実 field と実 mesh 距離から直接評価した。根拠は `$WM_PROJECT_DIR/src/finiteVolume/fields/fvPatchFields/fvPatchField/fvPatchField.C:216-219` である。直交等間隔格子では `deltaCoeffs=2/h` となる。これは B2 の二次再構成を再利用しない。
- Nu B2: B1 fieldを使わず、各wall faceについて壁値 `Tw`、第1/第2 cell-center値 `T1,T2` と座標 `0,h/2,3h/2` の二次補間を使う。壁から流体内向き座標 `s` で `dT/ds|w=(-8Tw/3+3T1-T2/3)/h`。正の熱輸送は hot で `Nu=-L(dT/ds)/DeltaT`、cold で `Nu=+L(dT/ds)/DeltaT` とする。face center列だけを用い、角のnode値やendpoint外挿は加えない。
- velocity: Route A と同じく、centrelineを挟む2 cell列/行から exact `X=0.5` / `Z=0.5` へ線形補間し、no-slip端点を含む固定4097点で正負 extrema と位置を抽出する。
- monitoring: solver log の全反復 residual/continuity、10反復ごとの Nu B1/B2、Umax/Wmax、熱収支を保存し、最終200反復の `Rwin` を評価する。`phi` はvolume fluxとして `div(phi)`、速度から `div(U)` を別に評価する。
- pre-run uncertainties: v6 `grad(T)` の実行可否、central scheme の収束性、laminar時の alphat patch挙動、3000反復で200反復windowが十分定常になるか。下記の実行結果で判定し、物性・BC・scheme・閾値は調整しない。

このタスクでは full matrix、Route A再実行、transient、custom solver、OpenFOAM source変更を行わない。

## 2. Implementation and environment evidence

実行には毎回 `source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc` を使用した。確認値は次のとおりであり、Foundation v6 と OpenCFD/ESI 系を混同していない。

| item | verified value |
|---|---|
| `foamVersion` | `OpenFOAM-6` |
| build | `6-af7d7f427be7` |
| source Git HEAD | `af7d7f427be78e9b9beb6aceca8fe7d5d4636876` |
| solver | `/home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam` |
| `WM_PROJECT_DIR` | `/home/mirai/OpenFOAM/OpenFOAM-6` |
| `FOAM_RUN` | `/home/mirai/OpenFOAM/mirai-6/run` |
| `WM_OPTIONS` | `linux64GccDPInt32Opt` |
| execution root | `/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark` |
| canonical root | `/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark` |

v6 側に reusable template、`Ra0_medium`、Gate C 合格後にだけ `Ra1e4_coarse`、生成・実行・解析・集約 script を作成した。v13 canonical 側には本書、`results/routeB/`、`Scripts/routeB/` の実スクリプトを置き、Route B case directory と Foundation v6 本体はコピーしていない。両 mesh は uniform structured orthogonal、front/back `empty`、1 cell in z である。`checkMesh -allGeometry -allTopology` は B-COND 6400 cells、B-SMOKE 1600 cells の双方で `Mesh OK`、geometric/solution directions `(1 1 0)`、max non-orthogonality 0° を確認した。

実行時選択は両 case とも `Newtonian`、`laminar`、`Stokes`、`radiationModel none` である。`0/p` は存在せず、solver が `p` を生成した。入力 hash、mesh hash、log hash、script hash、両 root は `run_manifest.json` に記録した。保護対象5文書の hash は実行後も manifest 記載値で固定されている。

## 3. Pressure and alphat verification

圧力は kinematic 単位 m²/s² で、入力は `p_rgh=0` のみである。`hRef=0`、`pRefValue=0`。中心最近傍の同距離候補から最小 cell ID を選び、B-COND は cell 3159 at `(0.049375,0.049375,0.0005) m`、B-SMOKE は cell 779 at `(0.04875,0.04875,0.0005) m` とした。最終生成 `p` は両 case で参照 cell 値が厳密に 0 で、B-SMOKE の `p_rgh` range は `[0.0686173986,0.0687286616] m²/s²`、finite である。

`alphat` は internal field と4物理壁で初期値0、front/back `empty` とした。最終値の `max(abs(alphat))` は両 case とも internal/physical patches で 0 であり、`Prt=0.85` は解に寄与していない。

## 4. B-COND Gate C

B-COND は 80×80×1、`g=(0,0,0)`、`Ra_actual=0` で3000 steady iterations を正常終了した。

| check | result | criterion | status |
|---|---:|---:|---|
| Nu hot B1 | 1.00003939249 | `abs(Nu-1)<=0.001` | PASS |
| Nu cold B1 | 1.00003940403 | `abs(Nu-1)<=0.001` | PASS |
| Nu hot B2 | 1.00003944237 | `abs(Nu-1)<=0.001` | PASS |
| Nu cold B2 | 1.00003945650 | `abs(Nu-1)<=0.001` | PASS |
| max B1/B2 relative difference | 5.24729e-8 | `<=0.001` | PASS |
| `max(|U|)L/alpha0` | 0 | `<=1e-6` | PASS |
| `max abs(theta-(1-X))` | 6.32833e-6 | `<=1e-4` | PASS |
| heat imbalance | 1.15377e-8 | diagnostic | healthy |
| alphat max | 0 | exactly zero | PASS |

paper-definition 自己検証は $\overline{Nu}_0=1.000039392488$、$\overline{Nu}_{1/2}=0.999960632154$、$\overline{Nu}=1.000000000000$、$\overline{Nu}_1=1.000039404027$ で、全て1から0.001以内だった。全断面最大偏差は中央断面比 `7.8775e-5`。よって自然対流結果を正式に再出力した。

符号は絶対値で隠していない。hot outward `snGrad(T)>0` を正、cold outward `snGrad(T)<0` に負号を掛けて正とした。温度 range `[299.506250240,300.493749759] K` は cell-centre analytic range と一致し、横流れもない。最終 T initial residual は `2.70767e-8`、最終200反復の既存壁 monitor `Rwin(Nu_bar_0)=4.17492e-5`、Umax/Wmax は0である。したがって Route B Gate C は PASS と判定した。

## 5. B-SMOKE results

Gate C 合格後にだけ B-SMOKE を生成した。40×40×1、`g=(0,-1.408450704225352,0) m/s²`、`Ra_actual=10000.0`、`Pr_actual=0.71` で、両者の target relative error は0である。3000 steady iterations を正常終了した。

| quantity | result |
|---|---:|
| Nu hot B1 / B2 | 2.25742166223 / 2.25970994049 |
| Nu cold B1 / B2 | 2.25742166289 / 2.25970994083 |
| B1/B2 maximum relative difference | 0.00101315545 (0.1013155%) |
| $\overline{Nu}_0$ | 2.257421662233 |
| $\overline{Nu}_{1/2}$ | 2.257421665255 |
| $\overline{Nu}$ | 2.259326039869 |
| $\overline{Nu}_1$ | 2.257421662889 |
| Umax, Z | 16.1184374584, 0.8125 |
| Umin, Z | -16.1184374610, 0.1875 |
| Wmax, X | 19.5952224756, 0.112548828125 |
| Wmin, X | -19.5952224696, 0.887451171875 |
| T range | `[299.507289059,300.492710941] K` |
| rhok range | `[0.999507289059,1.000492710941]` |
| heat imbalance | 2.90736e-10 |

流れは hot wall 側で上昇、cold wall 側で下降する正しい向きで、正負 extrema は180°回転対称の位置・大きさを示す。B1/B2 差は coarse grid 上で Gate C の0.1%値を 0.0013155 percentage points 超える。ただし0.1%条件は Gate C の conduction test に対する Hard 条件であり、B-COND は十分な余裕で合格した。B2 は異なる壁面再構成なので、この差は隠さず coarse-grid post-processing diagnostic として残す。

原論文との like-for-like 差は、$\overline{Nu}_0$ +0.868%、$\overline{Nu}_{1/2}$ +0.643%、$\overline{Nu}$ +0.728%、$Nu_{max}=3.577149661 at Z=0.139672955$（+1.393%、$\Delta Z=-0.00333$）、$Nu_{min}=0.582092917 at Z=1$（-0.667%、$\Delta Z=0$）である。raw face-centre extrema は max `3.577088314 at Z=0.1375`、min `0.583124741 at Z=0.9875`。$\overline{Nu}_1$ は Table V に独立値がないため paper error を計算しない。全鉛直断面の中央断面比最大偏差は `3.8140e-9`。これは coarse smoke test の診断であり、Gate E や `BENCHMARK_CORE_PASS` を判定しない。

## 6. Convergence and conservation

B-SMOKE の最終 initial residual は Ux `3.44e-11`、Uy `3.65e-11`、T `2.52e-10`、p_rgh `1.23e-8` で、全て目標 `1e-7` 以下である。最終200反復（21保存時刻）の `Rwin` は既存壁 monitor `1.41324e-9`、追加した $\overline{Nu}_{1/2}$ `1.31923e-8`、Umax `3.44263e-10`、Wmax `1.88906e-10` で、閾値 `5e-4` を大幅に下回る。Hard 監視対象は変更していない。熱不釣合いは丸めレベルで揺らぐが、同 window の線形 slope は `-1.72883e-12/iteration` で増加傾向ではない。反復上限到達だけではなく、これらにより収束を判定した。

continuity は2経路で評価した。

- 保存済み v6 volume flux `phi` を owner/neighbour と境界 face で有限体積和し、cell volume で割った `mean abs(div(phi))` は `1.19217e-12 1/s`。solver log の最終 `sum local=1.19218e-12` と一致し、`epsilon_phi=4.29842e-11` である。
- cell U を内部 face で central interpolation、no-slip boundary face で0として独立再構成した `mean abs(div(U))` は `1.19412e-4 1/s`、project 定義の `epsilon_v=epsilon_m=0.00430542` である。Route B の密度は一定なので両規格化量は同一である。

後者は Gate G の fine-grid 閾値0.002を超えるが、Gate G は仕様上 fine 解で判定する。今回の coarse smoke test では failure label に使わず、full matrix 前に追跡すべき格子依存 diagnostic とする。熱収支は Gate G 閾値0.2%に比べ十分小さいが、同様に正式 Gate G 判定ではない。

## 7. Minimal Route A/B diagnostic

既存の accepted A-SMOKE だけを読み、Route A は再実行していない。

| quantity | Route A | Route B | `(B-A)/A` |
|---|---:|---:|---:|
| $\overline{Nu}_0$ | 2.25742142226 | 2.25742166223 | +1.06305e-7 |
| $\overline{Nu}_{1/2}$ | 2.25851469700 | 2.25742166526 | -4.839e-4 |
| $\overline{Nu}$ | 2.25995462940 | 2.25932603987 | -2.781e-4 |
| $\overline{Nu}_1$ | 2.25742147185 | 2.25742166289 | +8.463e-8 |
| Umax | 16.1213350963 | 16.1184374584 | -1.79739e-4 |
| Z(Umax) | 0.8125 | 0.8125 | 0 |
| Wmax | 19.5973334630 | 19.5952224756 | -1.07718e-4 |
| X(Wmax) | 0.112548828125 | 0.112548828125 | 0 |
| epsilon_v | 0.00436508641 | 0.00430542228 | -0.0136685 |

coarse-grid の比較量は近い。しかし Route A は mass-weighted continuity と可変密度輸送、Route B は volume-flux continuity と定物性温度式を使う。現段階の差には離散化誤差と後処理差が含まれるため、モデル差の因果や漸近的一致を主張しない。

## 8. Adjustments, risks, and final decisions

物性、Ra、Pr、geometry、BC、central schemes、relaxation、solver tolerance、acceptance threshold は変更していない。失敗・無効化した試行は `results/routeB/failed_runs/` に保存した。

| ID | event and response |
|---|---|
| F-B1-POST-001 | solver 完了後の `postProcess -func grad(T)` が v6 `OSHA1stream.sinkFile_` で fatal。log を保存し、監査済み patch `snGrad` 式を actual field/mesh に直接適用した。 |
| F-ANALYZE-001 | Python labelList reader が OpenFOAM footer comment を許容せず停止。reader の終端だけを修正。 |
| F-ANALYZE-002 | empty patch の `phi` が `nonuniform 0()` であることを初版 reader が扱えず停止。empty face flux=0 として修正。 |
| F-ANALYZE-003 | B2 hot-wall の inward-coordinate 符号変換を誤った初版結果を無効化し、`Nu_hot=-L*dT/ds/DeltaT` に修正。 |
| F-ENV-001 | B-SMOKE 生成 wrapper で v6 source 前に `set -e` を置いたため、case 生成前に shell が停止。required activation を先に行う順序へ修正。 |

残る懸念は、(1) installed v6 command-line function-object digest の不具合により B1 を OpenFOAM utility の出力 field として保存できていないこと、(2) B-SMOKE coarse の B1/B2差が0.1%をわずかに超えること、(3) reconstructed `epsilon_v` が fine-grid用 Gate G 閾値を coarse grid で超えること、(4) $\overline{Nu}$ の cell-volume primary `2.259326039869` と face-plane profile の台形積分 `2.257421661124` に `0.00190438`（約0.084%）の coarse-grid 離散積分差があること、である。両 cavity 積分値は `metrics.json` に保存した。B1 は v6 patch operator と同じ式を actual mesh 上で評価し、B-COND の解析解で検証したため、この最小実装の blocker とはしない。full Route B matrix では格子収束と fine-grid Gate G を必ず再評価する。

この PASS は native Foundation v6 Route B case、B-COND Gate C、B-SMOKE の数値健全性だけを意味する。full 4 Ra × 3 grids、Gate E/F、formal fine-grid Gate G、final Gate K、`BENCHMARK_CORE_PASS` は未実施・未付与である。本定常 Route B solver は transient Gate J 用ではない。

現在の次段階は Route B の full 4 Ra × 3 grid matrix である。ここで Gate D/E/F/G/I/K を判定し、全 Hard 条件が揃った場合にのみ `BENCHMARK_CORE_PASS` を付与する。B-SMOKE の原論文値への近さや coarse A/B の近さは、その代用証拠ではない。

ROUTE B GATE C: PASS

ROUTE B SMOKE TEST: PASS

ROUTE B MINIMAL IMPLEMENTATION: PASS
