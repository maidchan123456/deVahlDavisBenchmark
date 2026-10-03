# Route A — Foundation v13 minimal implementation record

記録改訂: 1.1（2026-10-03）。実施日: 2026-09-30（Asia/Tokyo）。実行時の対象仕様: `benchmark_spec.md` v1.1、判定基準: `acceptance_criteria.md` v1.1。現行の交差参照は両文書とも v1.2であり、閾値は実行時から変更していない。Route A は Foundation v13 標準 formulation の特性評価用であり、古典 Boussinesq 方程式の Verification route ではない。

### 現在の status summary

| 項目 | 状態 |
|---|---|
| `ROUTE_A_AUDIT_PASS` | **付与**。根拠は `openfoam_design.md` の v13 ソース監査 |
| OQ-02 / minimal-case Gate A | **PASS**。cell と4物理 wall patch で確認 |
| Route A Gate C | **PASS**（A-COND） |
| Route A smoke / minimal implementation | **PASS**（A-SMOKE） |
| full Gate D/F/G/K、Gate H、Gate J | **未実施** |
| `ROUTE_A_CHARACTERIZED` / `DOWNSTREAM_TRANSIENT_READY` | **未付与** |

本文の数値、失敗試行、diagnostic concern は実施記録として変更しない。

## 1. Pre-implementation plan

- 環境: `source /opt/openfoam13/etc/bashrc`、`foamVersion=OpenFOAM-13`、`WM_PROJECT_VERSION=13`、`WM_PROJECT_DIR=/opt/openfoam13`、`WM_OPTIONS=linux64GccDPInt32Opt`、実行系 `foamRun` + `solver fluid`。
- 許可されたケース: `A-COND`（Ra=0、80×80×1）と `A-SMOKE`（Ra=10^4、40×40×1）のみ。
- 作成先: `cases/routeA/template`、`cases/routeA/Ra0_medium`、`cases/routeA/Ra1e4_coarse`、`Scripts/routeA`、`results/routeA`。Route B のケースは作成しない。
- モデル: `heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy`、laminar Stokes、laminar Fourier、放射・MRF・fvModels/fvConstraints・粒子なし。
- OQ-02: `hRef=0`、`pRef=0`、内部 `U=0,T=T0,rho=rho0,p_rgh=0` とし、内部 `p=rho0*gh+pRef` を mesh 生成後に作る。固定温度壁では EOS の patch 密度が直ちに `rho0` と異なるため、実装中の patch 検査で判明したとおり、物理壁の `p` 初期値は `rho(T_patch)*gh+pRef` とする。既定 `hydrostaticInitialisation=false` が solver constructor で `p_rgh=p-rho*gh-pRef` を再構成した直後の cell と patch を、別コピーの execute-at-start dump で確認する。`PIMPLE/pRefValue=0` と `constant/pRef=0` を区別する。
- 空間離散: 定常、Gauss linear convection/gradient、Gauss linear orthogonal Laplacian、linear interpolation、orthogonal snGrad。監査で列挙した active `e`, `K`, `p/rho`, `U` の演算を明示する。一次 upwind は使用しない。
- coupling: v13 `PIMPLE` の steady SIMPLE mode（`nOuterCorrectors=1`）。初期 solver/relaxation は再現可能に固定し、変更時は本書へ履歴を残す。residualControl で早期終了させず、十分な反復と最終200反復窓を保存する。
- Nu path A1: 壁 patch の有限体積法線温度勾配を face 面積で積分し、hot/cold の座標符号を明示して無次元化する。
- Nu path A2: v13 `wallHeatFlux` の `-q`、面積積分 Q [W]、patch area を使い、`k*DeltaT*W` で規格化する。放射 field がないことを確認する。A1 と同じ wallHeatFlux field の再変換を独立経路とは数えない。
- 速度極値: exact centreline 上の固定4097点へ線形 cell-point 補間し、正の Umax/Vmax と位置を抽出する。最近傍 cell 最大値は主値にしない。
- 監視: solver residuals、両 Nu、Umax/Vmax、熱収支を反復ごとまたは保存時刻ごとに保持し、最終200反復の相対レンジを評価する。Ra=0 では解析 T と無次元速度も判定する。
- 現時点の不確定事項: v13 の function-object 出力形式、初期化専用起動で constructor 後 field が書き出せるか、中央差分による smoke case の非線形収束性、圧力基準 cell の格子依存 ID。実装中にローカル v13 の実挙動で解消し、仕様との矛盾があれば該当段階を停止する。

このタスクでは full 4 Ra × 3 grid matrix、Route A 感度試験、非定常、Route B、custom solver を実施しない。

## 2. Implementation and environment evidence

実行環境は次のとおり。`cf13` は当該非対話 shell で未定義だったため、事前監査で確認済みの `/opt/openfoam13/etc/bashrc` を source した。OpenFOAM 6 および OpenCFD/ESI 系列は使用していない。

| 項目 | 実測値 |
|---|---|
| 作業ディレクトリ | `/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark` |
| `foamVersion` | `OpenFOAM-13` |
| build | `13-441953dfbb42` |
| `foamRun` | `/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/foamRun` |
| `WM_PROJECT` / `WM_PROJECT_VERSION` | `OpenFOAM` / `13` |
| `WM_PROJECT_DIR` | `/opt/openfoam13`（read-only） |
| `WM_OPTIONS` | `linux64GccDPInt32Opt` |
| host | `mirai-Precision-5860-Tower` |

作成物は `cases/routeA/template`、`cases/routeA/Ra0_medium`、`cases/routeA/Ra1e4_coarse`、`Scripts/routeA`、`results/routeA` と本書だけである。4つの仕様・監査文書は変更しておらず、最終 SHA-256 は manifest に保存した。`$WM_PROJECT_DIR` 以下の変更、再ビルド、custom solver、Route B、他の Ra/grid はない。

runtime log は両 case とも次を選択したことを示す。

- solver: `fluid`、steady-state、1 outer corrector、SIMPLE mode
- thermo: `heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy`
- momentum transport: `laminar`、stress model `Stokes`
- thermophysical transport: `laminar`、model `Fourier`
- MRF、turbulence、radiation、particle、任意 source/constraint: なし

物性は `rho0=1 kg/m3`、`beta=1e-3 1/K`、`mu=1e-5 Pa s`、`Pr=0.71`、`Cv=1000 J/(kg K)`。実使用対応値は `nu0=1e-5 m2/s`、`alpha0=1.4084507042253522e-5 m2/s`、`k=0.014084507042253521 W/(m K)`、`beta DeltaT=1e-3` である。A-SMOKE の重力は丸め表でなく式から `g=(0,-1.4084507042253521,0) m/s2` とし、再計算値は `Ra_actual=10000.0`、`Pr_actual=0.71` だった。

mesh は一様直交 hex、厚さ1 cell、front/back `empty`。`checkMesh -allGeometry -allTopology` は両方 `Mesh OK`、非直交度0、幾何・解方向 `(1 1 0)` を報告した。A-COND は6400 cells、物理壁各80 faces、front/back各6400 faces。A-SMOKE は1600 cells、物理壁各40 faces、front/back各1600 faces である。

`writeCellCentres` で実 mesh を再読込した結果、基準 cell 3159/779 の中心は manifest 値と最大 `6.94e-18 m` で一致した。

離散化は `steadyState`、`Gauss linear` の gradient/convection、`Gauss linear orthogonal` Laplacian、`linear` interpolation、`orthogonal` snGrad。active entries `div(phi,U)`, `div(phi,e)`, `div(phi,K)`, `div(phi,(p|rho))` と粘性 stress の div を明示した。A-SMOKE には診断専用 `div(U) Gauss linear` も実行前に加えた。upwind/limiter は使っていない。linear solver tolerance は全て `1e-10`, `relTol=0`、緩和は `p_rgh=0.3`, `U=0.5`, `e=0.7`、`nCorrectors=2`、`nNonOrthogonalCorrectors=0`。両 case とも residualControl なしで3000 steady iterations を実施した。

全 input/mesh/log hash、BC/model/scheme、property、参照 cell、結果は `results/routeA/run_manifest.json` にある。A-COND は `pRefCell=3159`, centre `(0.049375,0.049375,0.0005) m`、A-SMOKE は `pRefCell=779`, centre `(0.04875,0.04875,0.0005) m`。いずれも中心に等距離な4 cell の最小 global ID、`PIMPLE/pRefValue=0 Pa`、`constant/pRef=0 Pa`、`hRef=0 m` である。

## 3. OQ-02 initialization verification

solver constructor の後かつ最初の方程式 solve の前を検査するため、各入力 case を `results/routeA/initialization_check` に複製した。その clone に `writeObjects` の `executeAtStart=true` を加え、`foamRun` が constructor を完了して time loop に入る時点で `p,p_rgh,rho,gh` を time 0 に書かせた。clone はその後1反復するが、検査は time 0 だけを読むため benchmark 解と混同しない。元 case の time 0 は保持した。

最初の A-SMOKE attempt では内部 cell のみを検査して合格と誤認した。patch まで拡張すると、hot/cold 固定温度が EOS 密度 `0.9995/1.0005 kg/m3` を直ちに与えるため、壁の入力 `p=rho0 gh` に対して constructor 後 `|p_rgh|` が最大 `6.954225352118204e-5 Pa` になっていた。この attempt は受理せず、case/log/解析を `results/routeA/failed_runs/A-SMOKE-attempt1-boundary-init` に完全保存した。

修正後は内部 cell で仕様どおり `p=rho0 gh`、物理 wall patch で `p=rho(T_patch) gh` を初期値とした。これは `p` の `calculated` BC や温度 BCを変えず、constructor が実際に使う patch density と圧力関係を整合させるための seed 値である。front/back は `empty` で値を持たない。

| case | cell relation max [Pa] | cell max `|p_rgh|` [Pa] | patch relation max [Pa] | patch max `|p_rgh|` [Pa] | constructor `p`−input `p` max [Pa] |
|---|---:|---:|---:|---:|---:|
| A-COND | 0 | 0 | 0 | 0 | 0 |
| A-SMOKE accepted attempt | `8.33e-17` | `5.55e-17` | `6.94e-17` | `5.55e-17` | `5.55e-17` |

判定 tolerance は `1e-12 Pa`。全 cell と4物理 patch で `p_rgh=p-rho gh-pRef` および `p_rgh≈0` を満たした。数値詳細は各 `results/routeA/cases/*/initialization.json` にある。

## 4. A-COND Gate C results

80×80×1、`g=0`、3000反復。A1 は最終 T と直交 face geometry から、壁値と隣接 cell 中心の距離 `dx/2` を使って patch face ごとの法線勾配を独立計算した。A2 は実行中の公式 v13 `wallHeatFlux` の `wallHeatFlux=-q` と面積積分 `Q` を使用した。hot の `Q>0`、cold の `Q<0` を確認し、`Nu_h=Q_h/(k DeltaT W)`, `Nu_c=-Q_c/(k DeltaT W)` とした。放射 model/field はない。

| Gate C 項目 | 結果 | 閾値 | 判定 |
|---|---:|---:|---|
| A1 `Nu_h` | 1.000039392478 | `|Nu-1|<=0.001` | PASS |
| A1 `Nu_c` | 1.000039404051 | 同上 | PASS |
| A2 `Nu_h` | 1.000039392479 | 同上 | PASS |
| A2 `Nu_c` | 1.000039404051 | 同上 | PASS |
| 2経路最大相対差 | `4.55e-13` | `<=0.001` | PASS |
| `max(|U|)L/alpha0` | 0 | `<=1e-6` | PASS |
| cell中心 `max|theta-(1-X)|` | `6.3283e-6` | `<=1e-4` | PASS |
| hot/cold 熱不釣合い | `1.1572e-8` | 符号・balance確認 | PASS |

最終 energy initial residual は `2.708e-8`、U/p_rgh は0。最終200反復の `Rwin(Nu)=4.146e-5`、無流動なので速度 Rwin は0、熱不釣合いは `1.99e-8` から `1.16e-8` へ低下した。正常 `End`、NaN/Inf/FATALなし。解析温度直線、Nu履歴、速度 magnitude の図も保存した。

**ROUTE A GATE C: PASS**

## 5. A-SMOKE results

Gate C 合格後に accepted attempt を実行した。40×40×1、`Ra_actual=10000.0`、3000反復。A1/A2 の face/sign/規格化は A-COND と同一である。速度極値の主値は、偶数格子の centreline を挟む2 cell 列/行から exact `X=0.5` / `Y=0.5` へ線形補間し、no-slip 端点を含む固定4097点上で正の最大を求めた。

| 量 | Route A coarse | de Vahl Davis diagnostic | 差 |
|---|---:|---:|---:|
| mean `Nu_h` A1 | 2.257421422258 | 2.243 | +0.643% |
| mean `Nu_h` A2 | 2.257421422257 | 2.243 | +0.643% |
| mean `Nu_c` A2 | 2.257421471854 | 2.243 | +0.643% |
| `Umax` | 16.12133510 | 16.178 | -0.350% |
| `Y(Umax)` | 0.8125000 | 0.823 | -0.0105 absolute |
| `Vmax` | 19.59733346 | 19.617 | -0.100% |
| `X(Vmax)` | 0.11254883 | 0.119 | -0.00645 absolute |

hot wall 上向き、cold wall 下向きの循環であり、対応する centreline の負側 extrema は `Umin=-16.11554` at `Y=0.1875`、`Vmin=-19.59311` at `X=0.88745` だった。`T` range `299.507288–300.492710 K`、density range `0.999507290–1.000492712 kg/m3` で、場の向きと範囲に異常はない。熱不釣合いは `2.1970e-8`。これは coarse smoke の diagnostic comparison であり Gate E、格子収束、古典 Boussinesq 方程式との同一性を主張しない。

**ROUTE A SMOKE TEST: PASS**

## 6. Convergence and conservation evidence

runtime の official wallHeatFlux は毎反復、solver residual は毎反復、centreline monitor は257点を10反復ごとに記録した。最終報告値だけは固定4097点法を使う。`Rwin=(max-min)/max(|mean|,phi_scale)` とし、事前固定 scale は Nu/Umax/Vmax とも1である。

| case | final window | `Rwin(Nu)` | `Rwin(Umax)` | `Rwin(Vmax)` | final initial residual max |
|---|---|---:|---:|---:|---:|
| A-COND | 2801–3000 | `4.146e-5` | 0 | 0 | `2.708e-8` |
| A-SMOKE | 2801–3000 | 0（出力精度内一定） | `2.785e-11` | `1.942e-11` | `1.171e-10` |

A-SMOKE の最終 initial residual は Ux `4.73e-12`、Uy `4.29e-12`、e `9.66e-11`、p_rgh `1.17e-10`。両 case は反復上限に到達した事実だけでなく、200反復 window、residual、熱収支の全証拠で収束判定した。

OpenFOAM FV 診断では A-SMOKE の `mean|div(phi)|=7.859e-13 kg/(m3 s)`、`epsilon_m=2.833e-11`。`fvc::div(U)` の `mean|div(U)|=1.2108e-4 1/s`、`epsilon_v=4.365e-3`。mass continuity は良好だが volume divergence は将来 fine case に適用する Gate G の `2e-3` を超える。Gate G はこの coarse smoke の formal 合否ではなく、Route A の密度重み付き continuity と古典 incompressible continuity の構造差を示す重要な懸念として残す。A-COND は速度0なので Gate C の絶対速度基準を使う。

## 7. Adjustments and unresolved concerns

調整履歴は以下。物性、Ra、geometry、BC、中心差分、solver tolerance、緩和係数は結果を見て変更していない。

1. runner 内で OpenFOAM bashrc を source する前の strict shell option が bashrc と衝突したため、source 後に `set -eo pipefail` とした。CFD 起動前の runner 修正。
2. A-COND の最初の起動は v13 が sampled-set `uniform` を旧名として拒否した。指示どおり `lineUniform` に変更しただけで、失敗ログ `log.foamRun.attempt1_sampleTypeError` を保存した。
3. `div(U) Gauss linear` を A-SMOKE 生成前に post-processing diagnostic 用として追加した。fluid 方程式では使わない。
4. A-SMOKE attempt 1 は OQ-02 の内部検査だけで一度実行したが、patch 再監査で無効化した。hot/cold `p` patch seed を実際の EOS patch density に合わせ、attempt 2 で cell/patch の OQ-02 を合格させた。attempt 1 は上記 failed-runs path に保存した。
5. A-COND で `div(U)` scheme を追加する前に試した post-process は dictionary error となった。Ra=0 の volume-divergence 判定は仕様どおり絶対速度 Gate C を使い、この失敗ログは `results/routeA/failed_runs/A-COND-postprocess-divU-attempt1-missingScheme.log` に保存した。

残る懸念は3点ある。

- 仕様の「全領域 `T=T0,rho=rho0,p=rho0 gh`」は OpenFOAM field の内部初期場として実現できるが、fixedValue hot/cold patch は開始時から `Th/Tc` であり patch density は `rho0` ではない。accepted 実装は全 cell で仕様式を保ち、patch では完全な pressure relation と `p_rgh=0` を優先した。この internal/patch 区別は後続実装でも保持する。
- coarse smoke の `epsilon_v=4.365e-3` は formal fine-grid Gate G 閾値を超える。Route A の formulation 差、格子依存性、post-processing definition を full matrix 前に追跡する必要がある。
- A1 と A2 は独立のコード経路（T/geometry parser 対 official wallHeatFlux）だが、同じ Fourier law と orthogonal boundary gradient を物理的に共有する。Gate C の解析解との一致を併用して校正した。

## 8. Final decisions

再利用可能な Route A template、case generator、constructor 初期化検査、runner、2経路 Nu、4097点 centreline 抽出、residual/Rwin、divergence、CSV/JSON/figure 生成を実装した。必須 artifact は次のとおり。

- `results/routeA/run_manifest.json`
- `results/routeA/minimal_test_summary.csv`
- `results/routeA/convergence.csv`
- `results/routeA/conservation.csv`
- `results/routeA/figures/`
- case 内の `log.environment`, `log.blockMesh`, `log.checkMesh`, `log.foamRun`, post-process logs

A-COND は Gate C に合格し、A-SMOKE accepted attempt は OQ-02、正常終了、residual、200反復 Rwin、熱収支、自然対流方向の health 条件に合格した。volume divergence の懸念は status を隠さず記録した。この PASS は minimal Route A 実装だけを意味し、`BENCHMARK_CORE_PASS`、Route A と原論文方程式の同一性、grid convergence、tea simulation validation を意味しない。この Route A 実装タスクでは full matrix、感度、transient、Route B へは進まなかった。Route B はその後に別タスクで minimal implementation まで完了している。

現在の次段階は、まず Route B の full 4 Ra × 3 grid Verification matrix、続いて Route A の full matrix と3比較、その後に Gate H である。Gate H は A–B 同一性の証明としない。

ROUTE A GATE C: PASS

ROUTE A SMOKE TEST: PASS

ROUTE A MINIMAL IMPLEMENTATION: PASS
