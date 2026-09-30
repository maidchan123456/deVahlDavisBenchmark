# de Vahl Davis benchmark — OpenFOAM Foundation v13 実装前設計監査

監査日: 2026-09-29（Asia/Tokyo）。研究仕様: `benchmark_spec.md` 1.0、判定基準: `acceptance_criteria.md` 1.0。両文書を全文読了し、物理条件、掲載基準値、許容値は変更していない。

**監査結論:** Foundation v13 の標準 Route A は利用可能な構成であるが、古典的 Boussinesq 方程式と厳密には一致しない。温度依存密度による差に加え、総エネルギーに由来する追加項がある。固定 Ra の二点感度だけで全差分が消えることは証明できない。A を段階検証の第一候補として維持するが、初期圧力の整合と追加エネルギー項の評価方法に判断が必要であり、実装準備判定は **NO** とする。

計算状態は `NOT_RUN`。ソース調査は完了したが、未解決の設計判断を残して `AUDIT_PASS`、`BENCHMARK_CORE_PASS`、`DOWNSTREAM_TRANSIENT_READY` は宣言しない。作成・変更した成果物は本書のみ。ケース、solver、辞書、スクリプトの作成、計算、OpenFOAM 本体の変更・再ビルドは行っていない。

区分は研究仕様に従う。**[PAPER]** は仕様書が採録した原論文条件、**[OF13]** は本機の v13 ソースから確認した実装事実、**[PROJECT]** は研究上の設定・提案、**[GATE]** は進行条件、**[OPEN]** は未確定事項。式の変形・尺度評価は、実装事実からの解析的推論として明記する。

## 1. Environment audit

### 1.1 環境有効化と実測結果

最初の非対話 bash で `type cf13` は `type: cf13: not found`。`bash -ic 'type cf13; type of13'` でも `cf13` は未定義、`of13` は `bash --rcfile ~/.bashrc_of13` の alias だった。read-only で確認した [`.bashrc:124`](/home/mirai/.bashrc:124) と [`.bashrc_of13:5`](/home/mirai/.bashrc_of13:5) は、後者で `source /opt/openfoam13/etc/bashrc` を指定していた。`cf13` の定義は確認した shell 設定・標準候補位置では見つからなかった。

この問題を報告した後、ユーザーから **「確認済みの設定で v13 を有効化して続行」** の回答を受けた。以後は各調査 shell の冒頭で、確認済みの `source /opt/openfoam13/etc/bashrc` を実行した。`cf13` を作成していない。`cf6`、OpenFOAM 6 は使用していない。

```text
$ source /opt/openfoam13/etc/bashrc
$ pwd
/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark
$ foamVersion
OpenFOAM-13
$ which foamRun
/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/foamRun
$ echo "$WM_PROJECT_VERSION"
13
$ echo "$WM_PROJECT_DIR"
/opt/openfoam13
$ echo "$FOAM_RUN"
/home/mirai/OpenFOAM/mirai-13/run
$ ls -ld "$WM_PROJECT_DIR/applications/modules/fluid" \
         "$WM_PROJECT_DIR/tutorials/fluid/hotRoomBoussinesq"
drwxr-xr-x 4 root root 4096 Jun 18 13:15 /opt/openfoam13/applications/modules/fluid
drwxr-xr-x 5 root root 4096 Jun 18 13:15 /opt/openfoam13/tutorials/fluid/hotRoomBoussinesq
```

**[OF13]** `WM_PROJECT_VERSION` の実際の文字列は `13`（`v13` ではない）。`foamVersion` は `OpenFOAM-13`、ソースのヘッダは `openfoam.org` / OpenFOAM Foundation、`etc/bashrc:34–36` は `WM_PROJECT=OpenFOAM` / `WM_PROJECT_VERSION=13`。これらを合わせて **OpenFOAM Foundation v13** と確認した。OpenCFD/ESI の版・同名機能と混同しない。

| 追加識別 | 実測値・制約 |
|---|---|
| binary の実パス | `readlink -f` でも上記 foamRun パス |
| WM_OPTIONS | `linux64GccDPInt32Opt` |
| compiler / precision / label | `Gcc` / `DP` / `32` |
| dpkg package | `openfoam13 20260407` |
| host | `mirai-Precision-5860-Tower` |
| OS / kernel | Ubuntu 24.04.1 LTS / Linux 7.0.0-28-generic |
| ソース Git commit | `/opt/openfoam13/.git` は存在しないため未取得 |
| FOAMbuild | runtime banner は未取得。ケース起動を行わず、package・options・ソース hash で今回を識別。実装後の manifest には banner の build 識別も保存する |

**[OPEN] OQ-01:** 依頼文の `$FOAM_RUN/deVahlDavis` は実測 cwd と異なる。本書はユーザーが共有した現在の書き込み可能な benchmark 領域 `.../deVahlDavisBenchmark` に保存した。移動・別領域作成はしていない。今後も現在の領域を使う案を明示し、名前の整合を実装前に確認する。

### 1.2 追跡可能性

読み取り前後に仕様書の SHA-256 が同一であることを確認した。

```text
benchmark_spec.md:
f5a695573a055b4ecd0b35ee52d656be9d2b4c3a4c120a4558bc1dd08d398583
acceptance_criteria.md:
d8e9df247b8703c66bedeee89ad6b91e9f7fc519f5acc3b5ca08fa54df5dccaa

/opt/openfoam13/applications/modules/fluid/thermophysicalPredictor.C:
b3271ffca3d544eec49c79cf220ade3013204a5de959a9d887a4f46a64223be9
/opt/openfoam13/applications/modules/isothermalFluid/correctBuoyantPressure.C:
c6524988fa021329821055747369c30720240e005aa0eef322cbeb3a12ef3bb7
```

以後の `Sxx` は次の **本機の一次ソース** を指す。リンクは代表行、括弧内は監査した行・処理。式の根拠は本文で S 番号と処理を対応付ける。

| ID | ローカルソース・処理 |
|---|---|
| S01 | [foamRun.C](/opt/openfoam13/applications/solvers/foamRun/foamRun.C:81)（81–113 module 選択、122–193 外側ループ・predictor/corrector 順序） |
| S02 | [fluid.C](/opt/openfoam13/applications/modules/fluid/fluid.C:43)（43–56 isothermalFluid 継承、熱輸送生成、h/e validate） |
| S03 | [thermophysicalPredictor.C](/opt/openfoam13/applications/modules/fluid/thermophysicalPredictor.C:34)（34–63 energy 全項と thermo.correct） |
| S04 | [isothermalFluid.C](/opt/openfoam13/applications/modules/isothermalFluid/isothermalFluid.C:90)（64–85 pressureWork、90–221 場・モデル生成、330–398 密度予測・圧力補正・postSolve） |
| S05 | [momentumPredictor.C](/opt/openfoam13/applications/modules/isothermalFluid/momentumPredictor.C:36)（36–67 密度付き UEqn と netForce） |
| S06 | [correctDensity.C](/opt/openfoam13/applications/modules/isothermalFluid/correctDensity.C:35)（35–46 rhoEqn） |
| S07 | [correctBuoyantPressure.C](/opt/openfoam13/applications/modules/isothermalFluid/correctBuoyantPressure.C:54)（54–108 係数と浮力流束、170–224 非 transonic 圧力式・phi/U/K、226–284 p/rho 更新） |
| S08 | [buoyancy.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/buoyancy/buoyancy.C:36)（36–91 g/hRef/pRef/gh/ghf/p_rgh、99–112 起動条件） |
| S09 | [Boussinesq.C](/opt/openfoam13/src/thermophysicalModels/specie/equationOfState/Boussinesq/Boussinesq.C:39)（39–41 rho0/T0/beta 読み取り） |
| S10 | [BoussinesqI.H](/opt/openfoam13/src/thermophysicalModels/specie/equationOfState/Boussinesq/BoussinesqI.H:75)（75–109 rho/h/Cp/e/Cv、137–176 psi/CpMCv/alphav）、[Boussinesq.H](/opt/openfoam13/src/thermophysicalModels/specie/equationOfState/Boussinesq/Boussinesq.H:166)（166–170 incompressible/isochoric） |
| S11 | [eConstThermo.C](/opt/openfoam13/src/thermophysicalModels/specie/thermo/eConst/eConstThermo.C:39)（39–52 Cv/hf/Tref/esRef）、[eConstThermoI.H](/opt/openfoam13/src/thermophysicalModels/specie/thermo/eConst/eConstThermoI.H:85)（85–113 Cv/es/ea）、[EtoHthermo.H](/opt/openfoam13/src/thermophysicalModels/specie/thermo/thermo/EtoHthermo.H:1)（Cp=Cv+CpMCv、hs=es+p/rho） |
| S12 | [constTransport.C](/opt/openfoam13/src/thermophysicalModels/specie/transport/const/constTransport.C:40)（40–56 mu と Pr/kappa 排他）、[constTransportI.H](/opt/openfoam13/src/thermophysicalModels/specie/transport/const/constTransportI.H:75)（75–92 mu/kappa） |
| S13 | [RhoFluidThermo.C](/opt/openfoam13/src/thermophysicalModels/basic/rhoFluidThermo/RhoFluidThermo.C:57)（57–71 energy→T→Cp/Cv/psi/rho/mu/kappa、境界も同様）、[fluidThermo.C](/opt/openfoam13/src/thermophysicalModels/basic/fluidThermo/fluidThermo.C:102)（102–111 nu=mu/rho） |
| S14 | [Stokes.C](/opt/openfoam13/src/MomentumTransportModels/momentumTransportModels/laminar/Stokes/Stokes.C:76)（76–92 nuEff=nu）、[linearViscousStress.C](/opt/openfoam13/src/MomentumTransportModels/momentumTransportModels/linearViscousStress/linearViscousStress.C:89)（89–124 偏差応力と implicit Laplacian） |
| S15 | [Fourier.C](/opt/openfoam13/src/ThermophysicalTransportModels/fluid/laminar/Fourier/Fourier.C:99)（99–145 q と divq）、[sensibleInternalEnergy.H](/opt/openfoam13/src/thermophysicalModels/specie/thermo/sensibleInternalEnergy/sensibleInternalEnergy.H:69)（69–111 energyName=e、Cpv=Cv、es/Tes） |
| S16 | [wallHeatFlux.C](/opt/openfoam13/src/functionObjects/field/wallHeatFlux/wallHeatFlux.C:62)（62–103 -q と qr、148–182 wall filter、192–225 transport registry、256–271 Q と平均） |
| S17 | [constrainPressure.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/constrainPressure/constrainPressure.C:59)（59–74 流束から法線勾配）、[fixedFluxPressureFvPatchScalarField.C](/opt/openfoam13/src/finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure/fixedFluxPressureFvPatchScalarField.C:110)（110–139 gradient 更新順） |
| S18 | [pressureReference.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/pressureReference/pressureReference.C:31)（31–46 setRefCell）、[findRefCell.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/findRefCell/findRefCell.C:41)（41–119 needReference、pRefCell/Point/Value） |
| S19 | [hydrostaticInitialisation.C](/opt/openfoam13/src/thermophysicalModels/basic/fluidThermo/hydrostaticInitialisation.C:51)（51–119 hydrostaticInitialisation 分岐と初期 p_rgh 上書き） |
| S20 | [basicThermo.C](/opt/openfoam13/src/thermophysicalModels/basic/basicThermo/basicThermo.C:48)（48–76 p 読込共通処理、252–279 T・dpdt）、[fluidThermo.C](/opt/openfoam13/src/thermophysicalModels/basic/fluidThermo/fluidThermo.C:46)（46 p 取得）、[rhoFluidThermo.C](/opt/openfoam13/src/thermophysicalModels/basic/rhoFluidThermo/rhoFluidThermo.C:57)（57–66 thermo rho の名前分離・correctRho） |
| S21 | [polyMesh.C](/opt/openfoam13/src/OpenFOAM/meshes/polyMesh/polyMesh.C:68)（68–130 empty 方向除外）、[emptyFvPatchField.C](/opt/openfoam13/src/finiteVolume/fields/fvPatchFields/constraint/empty/emptyFvPatchField.C:31)（31–63 サイズ0・型整合）、[fvMatrixSolve.C](/opt/openfoam13/src/finiteVolume/fvMatrices/fvMatrix/fvMatrixSolve.C:136)（136–143 面外成分 solve を除外） |
| S22 | [fvSchemes.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvSchemes/fvSchemes.C:61)（61–83 steady 判定、238–295 scheme lookup）、[steadyStateDdtScheme.C](/opt/openfoam13/src/finiteVolume/finiteVolume/ddtSchemes/steadyStateDdtScheme/steadyStateDdtScheme.C:153)（時間行列ゼロ、ddtCorr もゼロ） |
| S23 | [pimpleSingleRegionControl.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/solutionControl/pimpleControl/pimpleSingleRegionControl/pimpleSingleRegionControl.C:55)（55–66 SIMPLE/PISO mode、89–124 loop/run）、[pimpleNoLoopControl.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/solutionControl/pimpleControl/pimpleNoLoopControl/pimpleNoLoopControl.C:56)（56–61 simpleRho の既定）、[pimpleLoop.C](/opt/openfoam13/src/finiteVolume/cfdTools/general/solutionControl/pimpleControl/pimpleLoop/pimpleLoop.C:38)（38–42 outer 回数） |
| S24 | [laminarModel.C](/opt/openfoam13/src/MomentumTransportModels/momentumTransportModels/laminar/laminarModel/laminarModel.C:83)（83–150 explicit model または Stokes）、[laminarThermophysicalTransportModel.C](/opt/openfoam13/src/ThermophysicalTransportModels/fluid/laminar/laminarThermophysicalTransportModel/laminarThermophysicalTransportModel.C:65)（65–119 model 選択・既定 unityLewisFourier）、[fluidThermoThermophysicalTransportModels.C](/opt/openfoam13/src/ThermophysicalTransportModels/fluidThermo/fluidThermoThermophysicalTransportModels.C:42)（42–46 Fourier 登録） |
| S25 | [forGases.H](/opt/openfoam13/src/thermophysicalModels/specie/include/forGases.H:50)（50–66 Boussinesq/eConst/const/内部energy の組合せ）、[rhoFluidThermos.C](/opt/openfoam13/src/thermophysicalModels/basic/rhoFluidThermo/rhoFluidThermos.C:40)（40–42 登録）、[rhoFluidThermo.H](/opt/openfoam13/src/thermophysicalModels/basic/rhoFluidThermo/rhoFluidThermo.H:78)（78 heRhoThermo 名） |
| S26 | [fvmDiv.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvm/fvmDiv.C:104)（104–121 divc は指定 face-flux の直接積分）、[momentumTransportModel.C](/opt/openfoam13/src/MomentumTransportModels/momentumTransportModels/momentumTransportModel.C:143)（143–160 devTauCorrFlux の divc） |
| S27 | [fvmLaplacian.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvm/fvmLaplacian.C:339)（339–384 laplacianCorrection は補間と固定直交行列）、[fvcDiv.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvc/fvcDiv.C:44)（44–55 surface-flux の積分）、[fvcFluxTemplates.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvc/fvcFluxTemplates.C:42)（42–52 flux(HbyA)）、[fvcDdt.C](/opt/openfoam13/src/finiteVolume/finiteVolume/fvc/fvcDdt.C:263)（263–274 静的格子の rho/U flux correction） |
| S28 | [tutorial physicalProperties](/opt/openfoam13/tutorials/fluid/hotRoomBoussinesq/constant/physicalProperties:17)、[momentumTransport](/opt/openfoam13/tutorials/fluid/hotRoomBoussinesq/constant/momentumTransport:17)、[fvSchemes](/opt/openfoam13/tutorials/fluid/hotRoomBoussinesq/system/fvSchemes:17)、[fvSolution](/opt/openfoam13/tutorials/fluid/hotRoomBoussinesq/system/fvSolution:53)、[0/p](/opt/openfoam13/tutorials/fluid/hotRoomBoussinesq/0/p:16)（構文・対照用、コピーしない） |

## 2. OpenFOAM v13 solver architecture

**[OF13]** S01 は `controlDict` の `solver` または `-solver` から library を load し、module を runtime selection で生成する。S02 は `fluid` を登録し、`isothermalFluid` を継承してエネルギー輸送を追加する。`fluid` という名称は一定密度を保証しない。

S04 が `fluidThermo::New`、`p`、solver の `rho`、`U`、質量流束 `phi`、`K=|u|²/2`、compressible momentum transport、MRF container、buoyancy、pressureReference を生成する。S02 は momentum transport と thermo から thermophysical transport を生成する。compressible framework の使用と、EOS の圧力非依存性は別事項である。

静的格子・単一流体・MRF なし・source/constraint なしという今回の設計では、各外側反復は概ね

`prePredictor（必要時密度）→輸送モデル予測→momentumPredictor→thermophysicalPredictor→pressureCorrector→輸送モデル補正→postSolve`

となる（S01、S04）。energy 解後に EOS の T/rho/transport を更新し、圧力補正でも密度を更新する。非定常の solver rho と thermo rho は途中で同一とは限らない。

**[PROJECT]** 候補 thermo tuple は `heRhoThermo / pureMixture / const / eConst / Boussinesq / specie / sensibleInternalEnergy`。S25 の登録と S28 の公式 tutorial がこの組合せを裏付ける。今回の物性値は tutorial から採用せず仕様書4節を使う。

laminar stress は明示的 `Stokes`、熱輸送は明示的 `Fourier` を候補とする（S24）。`Stokes` はここでは Newtonian 応力モデル名であり、慣性・対流を落とす creeping-flow solver という意味ではない。熱輸送辞書を省略すると v13 の既定は **unityLewisFourier** であるため、「既定が Fourier」とは書かない。

`p_rgh` の header があれば buoyancy を生成し `constant/g` を読む（S08）。Ra=0 でも同じ route を維持し、g=0 とする案。放射・体積発熱・粒子・剛体・乱流・MRF・mesh motion を導入する fvModels/fvConstraints 等は設定しない。S03/S05 の汎用 source hook は存在するが、本 benchmark では零である。

## 3. Boussinesq implementation

**[OF13]** S09 が `mixture/equationOfState` の `rho0,T0,beta` を読み、S10 が

\[
\rho_T=\rho_0[1-\beta(T-T_0)],\quad \psi=\left.\partial\rho/\partial p\right|_T=0
\]

を返す。`incompressible=true` は **rho が p の関数でない** こと、`isochoric=false` は **rho が一定でない** ことを表す。`div(u)=0` の選択フラグではない。

EOS の補正は `e=0,Cv=0,Cp=0,CpMCv=0`、`h=p/rho`。実際の比熱・energy は eConst と組み合わされる（8節）。`alphav=rho0*beta/rho` なので thermo が返す体膨張率は入力 beta と厳密には同じでない。密度は S13 で cell/patch に更新され、S04/S07 から solver 側に利用される。

**[PROJECT]** 主条件の epsilon=beta DeltaT=1e-3 では壁密度は rhoh=0.9995、rhoc=1.0005 kg/m³。感度条件は0.99995/1.00005。正密度は仕様温度範囲では保証されるが、数値振動で温度が境界値範囲外にならないかを将来監視する。

## 4. Governing-equation mapping

### 4.1 記号・適用範囲

**[PAPER]** 無次元速度を \(\boldsymbol U=L\boldsymbol u/\alpha_0\)、温度を \(\theta=(T-T_c)/\Delta T\)、時間を \(\tau=\alpha_0t/L^2\) とする。本節の \(\boldsymbol u\) は OpenFOAM field `U` の有次元値。圧力 p と p_rgh は Pa、古典方程式の reduced pressure は \(P=\pi L^2/(\rho_0\alpha_0^2)\)。

以下は source/constraint なし、静的格子、MRF なし、laminar、収束して solver rho=thermo rho となった場合の **ソースから推論した連続体対応**。有限反復・離散式で積の法則が厳密成立するとは主張しない。

### 4.2 Continuity

**[OF13]** S06 は `fvm::ddt(rho)+fvc::div(phi)=0`。`phi` は S04 の初期 `linearInterpolate(rho*U)&Sf` と S07 の圧力補正を経た **kg/s の質量流束**。非 transonic の S07 圧力式にも `ddt(rho)+psi*correction(ddt(p_rgh))+div(phiHbyA)-laplacian(...,p_rgh)=0` がある。Boussinesq では psi=0 だが ddt(rho) は残る。

連続体対応は

\[
\partial_t\rho+\nabla\cdot(\rho\boldsymbol u)=0,
\qquad
\nabla\cdot\boldsymbol u={\rho_0\beta\over\rho}\,{DT\over Dt}.
\]

定常では \(\nabla\cdot(\rho\boldsymbol u)=0\)、\(\nabla\cdot\boldsymbol u=(\rho_0\beta/\rho)\boldsymbol u\cdot\nabla T\)。古典式の `div(u)=0` と **厳密一致しない**。epsilon→0 で滑らかな解・温度勾配が有界ならこの差は O(epsilon)。

非定常の S04 prePredictor、S07 correctDensity、S04 postSolve による EOS rho への再同期も記録する。閉領域で psi=0 なので、圧力で密度・総質量を調整できない。反復中の EOS 密度と連続式密度の差、領域積分質量の drift を将来確認する（OQ-07）。

### 4.3 Momentum、静水圧、符号

**[OF13]** S05 の式は

\[
\partial_t(\rho\boldsymbol u)+\nabla\cdot(\rho\boldsymbol u\otimes\boldsymbol u)
=-\nabla p_{rgh}-gh\nabla\rho+\nabla\cdot\boldsymbol\tau,
\]

\[
\boldsymbol\tau=\mu[\nabla\boldsymbol u+(\nabla\boldsymbol u)^T
-\tfrac23(\nabla\cdot\boldsymbol u)\boldsymbol I]
\]

に対応する（S14）。密度付き保存形時間・移流、Pa 圧力、動粘度を通した応力係数がある。連続式が成立すれば左辺は \(\rho D\boldsymbol u/Dt\)。一定 mu のとき \(\nabla\cdot\tau=\mu[\nabla^2\boldsymbol u+\tfrac13\nabla(\nabla\cdot\boldsymbol u)]\)。古典式にない体積膨張に伴う応力が残る。

S08 と S07 の定義:

\[
 gh=\boldsymbol g\cdot\boldsymbol x-gh_{ref},\quad
 gh_{ref}=-|\boldsymbol g|h_{ref},\quad
 p_{rgh}=p-\rho gh-p_{Ref}.
\]

\(p_{Ref}\) は `constant/pRef` の一様圧力、既定0。pressureReference の `pRefValue` とは別物。\(h_{ref}\) は既定0、\(\nabla gh=\boldsymbol g\)。したがって

\[
-\nabla p+\rho\boldsymbol g=-\nabla p_{rgh}-gh\nabla\rho.
\]

S04 の netForce と S07 の `ghGradRhof=-ghf*snGrad(rho)*magSf` がこの右辺を面流束として生成する。浮力は単独の `+rho*g` を UEqn に直接書く方式ではない。

**[OF13 → 解析的写像]** 基準静水圧を引いた \(\pi=p-\rho_0gh-p_{Ref}\) を使えば

\[
-\nabla p+\rho\boldsymbol g=-\nabla\pi+(\rho-\rho_0)\boldsymbol g.
\]

\(\boldsymbol g=(0,-g,0)\) なので

\[
(\rho-\rho_0)\boldsymbol g
=+\rho_0\beta g(T-T_0)\boldsymbol e_y.
\]

高温側の力は上向き。rho0 で除す古典極限では \(+g\beta(T-T_0)\boldsymbol e_y\)。\(T-T_0=\Delta T(\theta-1/2)\) だから、空間一定の \(-g\beta\Delta T/2\) を圧力勾配に吸収すると \(+g\beta\Delta T\theta\boldsymbol e_y\)。熱拡散尺度で係数は

\[
{g\beta\Delta T L^3\over\alpha_0^2}=RaPr.
\]

Route A では慣性除算に局所 rho、粘性に mu/rho、応力に div(u) が残るため、この古典極限と同一式にはならない。

### 4.4 p_rgh 補正式

S07 の非 transonic branch を選ぶ。予測質量流束は rhof*flux(HbyA)、時間流束補正、重力密度勾配補正から作る。\(a_f=\operatorname{interp}(\rho rAU)\)（consistent correction 時は rAtU）として

\[
\partial_t\rho+\psi\,\delta(\partial_t p_{rgh})
+\nabla\cdot\phi_H-\nabla\cdot(a_f\nabla p_{rgh})=0.
\]

補正後 phi は `phiHbyA+p_rghEqn.flux()`。この matrix は負 Laplacian なので flux の符号を v5 の書式からコピーしない。U は HbyA と pressure/buoyancy force から更新し、K も再計算する。psi=0 は圧力時間係数を消すが、質量保存を体積保存へ変更しない。

### 4.5 Energy / Temperature

**[OF13]** S03 の内部エネルギー branch、S15 Fourier の対応は

\[
\partial_t(\rho e)+\nabla\cdot(\rho\boldsymbol u e)
+\partial_t(\rho K)+\nabla\cdot(\rho\boldsymbol u K)
+\nabla\cdot(p\boldsymbol u)
=\nabla\cdot(k\nabla T)+\rho\boldsymbol u\cdot\boldsymbol g,
\quad K=|\boldsymbol u|^2/2.
\]

S03 は `div(phi,p/rho)` を使い、静的格子の S04 pressureWork はそのまま返す。メッシュ移動補正は今回無効。熱拡散は `divq(he)` として左辺にあるので、右辺へ移すと正の \(\nabla\cdot(k\nabla T)\)。

| 項 | v13 Route A | [PAPER] 温度式との関係 |
|---|---|---|
| thermal 時間・移流 | ddt(rho,e)+div(phi,e) | 密度付き。定常でも rho は残る |
| 熱拡散 | Fourier の温度勾配と energy implicit correction | Cp=Cv、定数 k なら温度拡散に換算可能 |
| 運動エネルギー | ddt(rho,K)+div(phi,K) | 原論文にない。steady でも移流は残る |
| 圧力仕事（e） | div(phi,p/rho) | 原論文にない。psi=0 でも有効 |
| 圧力仕事（h branch） | -dpdt | e branch とは式・熱量関係が異なる |
| 重力仕事 | rho*(U&g) | 原論文にない。steady でも残る |
| 密度変化 | thermal/K/flux 全て | 浮力だけに限定されない |
| 粘性仕事/散逸 | `div(tau·u)` や `tau:grad(u)` の独立明示項は S03 にない | 原論文の散逸無視と同一とは認定できない（下式） |
| 生成熱・放射・粒子 | fvModels hook、今回は設定なし | 今回は零 |

**[OF13 → 解析的推論]** 質量保存と運動量式を使って K を消去すると、追加項の相殺を考慮した温度式は

\[
\rho C_v{DT\over Dt}=\nabla\cdot(k\nabla T)
-p\nabla\cdot\boldsymbol u-\boldsymbol u\cdot(\nabla\cdot\boldsymbol\tau).
\]

つまり重力仕事・圧力移流・K 項を個々の大きさだけで誤差評価するのも誤りである。一方、相殺後も二つの追加項が残る。後者は粘性散逸そのものではなく、S03 に粘性仕事 flux がないことから生じる組合せ。div(u)=0 の極限でも \(-u\cdot div(tau)\) は一般に零でない。

`dpdt no` は e branch の `div(phi,p/rho)` を消さない。enthalpy へ変更して追加項をなくしたと扱わない。eConst の hs=es+p/rho には圧力・密度依存性があり、監査した内部energy route からの変更は別設計である。

## 5. Differences from de Vahl Davis equations

### 5.1 項ごとの差分一覧

| 原論文の項 | Route A の対応・差分 | 根拠 |
|---|---|---|
| div(U)=0 | ddt(rho)+div(rho u)=0。温度輸送に伴う div(u) が非零 | S04/S06/S07/S10 |
| dU/dtau | ddt(rho,u)、慣性に局所 rho | S05 |
| (U·grad)U | div(phi,u)、phi は質量 flux | S04/S05 |
| -grad(P) | -grad(p_rgh)-gh grad(rho)、局所 rho で加速度へ換算 | S04/S07/S08 |
| Pr Laplacian U | 偏差応力、mu/rho と grad(div u) が残る | S13/S14 |
| RaPr theta ey | rho anomaly と負 y 重力、基準圧力への吸収で古典極限 | S07–S10、4.3節の導出 |
| dtheta/dtau・U·grad theta | thermal energy の密度付き保存形 | S03/S11/S15 |
| Laplacian theta | k/(rho Cv)、rho 依存 | S12/S15 |
| 原論文にない項 | K 輸送、圧力仕事、重力仕事。相殺後は -p div u-u·div tau | S03/S05、4.5節の導出 |
| 原論文にない gauge 依存 | 圧力の一様定数は energy の p div u に影響し得る | S03/S08、下記解析 |

### 5.2 O(epsilon) と言える範囲

**[OF13 → 解析的推論]** rho/rho0=1-epsilon(theta-1/2) だから、滑らかな有界解を仮定すれば、密度付き慣性、continuity、nu/alpha、grad(div u) の差は O(epsilon) と期待できる。しかし **全 energy 差分は O(epsilon) ではない**。

熱拡散速度の Eckert 型係数

\[
E_\alpha={\alpha_0^2\over L^2C_v\Delta T}=1.9837334\times10^{-11}
\]

は beta に依存しない。\(-u\cdot div(tau)\) の無次元係数は \(Pr E_\alpha\)、速度・その勾配を掛けた場で評価する必要がある。小さい係数だけでは許容値合格を証明できない。

さらに固定 Ra の感度試験では g∝1/epsilon。静水圧部分 p_h≈rho0 gh による圧力膨張仕事の係数は

\[
H\epsilon={gL\over C_v\Delta T}\epsilon
=RaPr E_\alpha,
\]

となり epsilon を1/10にしても一定。

| Ra=1e6 | epsilon=1e-3 | epsilon=1e-4 |
|---|---:|---:|
| g [m/s²] | 140.8450704225… | 1408.450704225… |
| H=gL/(Cv DeltaT) | 0.0140845070… | 0.1408450704… |
| H epsilon | 1.408450704e-5 | 1.408450704e-5 |

これは場の誤差ではなく **追加項の尺度**。温度・速度勾配や相殺を含む実測が必要。動圧部分・一様基準圧力の寄与も別に評価する。p→p+C なら相殺後の温度 source は -C div(u) だけ変わる。psi=0 の EOS が圧力非依存でも energy の gauge 不変性は保証されない。

**[GATE]** Gate H の二点試験は密度由来の影響を検査するために必須かつ有用。しかし両条件に共通する energy 差分、絶対モデル誤差、漸近次数まで証明する試験ではない。仕様書6.4の「epsilon→0 で古典式へ近づく」は、全項について無条件には成立しない。仕様を改変せず OQ-03 に記録する。

さらに、S03の実際の離散式は大きい圧力仕事と重力仕事を別々に評価する。gを10倍すると個々の項も大きくなり、離散的な相殺誤差が同じ割合で小さくなる保証はない。4.5節の連続体での消去式を、有限格子で厳密に成立する恒等式として用いない。二点比較では追加項の各積分・局所値と相殺後残差も確認する案とする。

## 6. OpenFOAM v5 vs v13

v13 の結論はローカルソースを使用した。v5 は本機に v5 の一次ソースを確認できていないため、比較に限って **Foundation 公式 OpenFOAM-5.x 公開ソース** を read-only 参照した。v6 を代用していない。以下は公式5.x branch の標準コードとの比較であり、過去研究の patch・CFDEM custom solver が同じという証明ではない。

| 構造 | Foundation v5 Boussinesq solvers | Foundation v13 Route A |
|---|---|---|
| 実行 | 個別 executable、Simple/Pimple | foamRun が fluid module を load |
| continuity / flux | 体積流束の pressure projection、div(u)=0 | 質量流束、ddt(rho)+div(rho u)=0 |
| 慣性・移流 | U の直接式、温度密度は係数に使わない | rho U の保存形 |
| 浮力密度 | rhok=1-beta(T-TRef)、浮力・圧力分離用 | EOS の有次元 rho、全輸送へ使用 |
| 圧力 | p/rho0 相当の kinematic pressure、p=p_rgh+rhok gh | Pa、p=p_rgh+rho gh+pRef |
| 熱輸送 | T を直接解く。laminar alpha=nu/Pr | e を解き thermo で T を復元 |
| 熱力学 | laminarTransport と beta/TRef/Pr 等 | fluidThermo、EOS、eConst、const、Fourier |
| additional energy | 標準 T 式に K/圧力仕事/重力仕事なし | 4.5節の項がある |
| 定常 coupling | SIMPLE | PIMPLE framework の SIMPLE mode が可能 |
| 非定常 coupling | PIMPLE | PIMPLE/PISO mode が可能 |
| sources/constraints | fvOptions・radiation hook | fvModels/fvConstraints・thermophysical transport |

v5 Simple の rho を含まない運動量式は [公式 UEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/UEqn.H)、T の直接定常輸送と rhok 更新は [公式 TEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/TEqn.H)。Pimple 側では [UEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqPimpleFoam/UEqn.H) と [TEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqPimpleFoam/TEqn.H) に U/T の ddt が追加される。

rhok と kinematic pressure の生成、incompressible turbulence framework は [createFields.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/createFields.H)、体積流束 projection と最終 p の基準合わせは [Simple pEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/pEqn.H)、時間 flux correction は [Pimple pEqn.H](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-5.x/master/applications/solvers/heatTransfer/buoyantBoussinesqPimpleFoam/pEqn.H)。

**結論:** executable 名だけの変更ではない。`buoyantBoussinesqSimpleFoam` と `foamRun+fluid+Boussinesq` を完全に同じ solver と扱わない。

## 7. Boundary-condition audit

### 7.1 速度・温度・二次元性

**[PAPER]/[PROJECT]** 候補は妥当。左 U=noSlip、T=300.5 K fixedValue、右 U=noSlip、T=299.5 K fixedValue、上下 U=noSlip、T=zeroGradient。front/back は mesh と全場の両方で empty。定数 k・Fourier・放射なしなら zeroGradient T は零伝導熱流束を与える（S15）。energy 境界は thermo が温度境界から整合させるため、独立した不整合な e fixedValue を追加しない。

**[OF13]** S21 の empty field は零サイズの境界演算を持ち、polyMesh が empty 法線方向を solutionD から除き、vector matrix solve が無効成分を除く。**奥行き1セル、平行な z 法線の front/back、面外初期速度0、g_z=0、面外 source なし** を揃える必要がある。empty という文字だけを設定して任意の三次元 mesh を二次元化できるとはしない。将来 checkMesh の2D判定と U_z・面外勾配を Gate A で確認する。奥行き W は Nu の面積規格化で消えるが、Q [W] には残る。

### 7.2 fixedFluxPressure

S07 は浮力補正済み phiHbyA に対して S17 の constrainPressure を呼ぶ。境界で

\[
\partial_n p_{rgh}={\phi_H-\rho_f\boldsymbol u_b\cdot\boldsymbol S_f
\over |\boldsymbol S_f|a_f}
\]

を設定し、pressure flux correction が指定壁流束を満たす。noSlip の壁では目標流束0。`fixedFluxPressure` は浮力込みの予測流束と整合し、閉領域の物理壁の候補として適切。`zeroGradient p_rgh` に機械的に置き換えない。S17 は gradient 更新が先に呼ばれることを要求するが、標準 correctBuoyantPressure がこれを実施する。

### 7.3 圧力基準と初期値の重要事項

**[OF13]** 全壁 fixedFluxPressure / empty は pressure の定数を固定しない。Boussinesq の incompressible=true により S04→S18 が基準を要求する。辞書キーは field p の名前から作るため、`PIMPLE` 内の **pRefCell（または pRefPoint）、pRefValue**。`p_rghRefCell` ではない。

S07 はその refCell/refValue を **p_rghEqn.setReference** に渡す。この audited branch では最後に v5 のような `pRefValue-getRefCellValue(p,...)` による p の全体 shift を行わない。したがって pRefValue=0 を指定しても、最終 p(refCell)=0 とは限らず、p≈rho gh+pRef が足される。基準値がどの場を固定するかを manifest に明記する。

**[PROJECT]** 中心に最も近い cell を使う。40/80/160 の偶数格子では中心に等距離の4セルがあるため、「距離最小、同距離なら最小 global cell ID」という再現可能な tie-break 案を提案する。各格子の ID と座標を記録する。pRefPoint を正確な格子中心交点に置くと cell/partition の曖昧性があるため、選んだ cell 内点または cell ID を使う。

**[OPEN] OQ-02:** `0/p` は必須（S20）。S19 の既定 hydrostaticInitialisation=false は、読み込んだ p_rgh を **p-rho gh-pRef に上書き**する。したがって `0/p=0` と `0/p_rgh=0` を同時に書いても、g≠0 なら仕様の初期 p_rgh=0 が維持されない。

仕様を変えない整合案は、U=0,T=T0,rho=rho0 として **p(x)=rho0 gh(x)+pRef** を初期場に与え、p_rgh=0 を保持すること。`0/p` の壁は calculated、front/back は empty（S28 も calculated の先例）。この整合場の初期化方法と hRef/pRef の扱いは実装前に決定する。hydrostaticInitialisation=true は ph_rgh 等の追加入力を要するので、そのまま有効化して問題を隠さない。p の一様定数が energy に入るため、任意に大気圧を追加しない。

## 8. Transport-property mapping

**[PROJECT]** L=0.1 m、W=0.001 m、rho0=1 kg/m³、mu=1e-5 Pa s、Pr=0.71、Cv=1000 J/(kg K)、beta=1e-3 K⁻¹、T0=300 K、Th/Tc=300.5/299.5 K、molWeight=28.9 kg/kmol、hf=0 J/kg を保持する。辞書の比熱キーは **Cv**（大文字）、参照 EOS 温度は **T0**。eConst の **Tref** は energy の基準であり T0 と同義ではない。

**[OF13]** 実際の算出経路:

1. S11: Cv_total=Cv_input+EOS.Cv=1000、e_s=Cv_input(T-Tref)+esRef（EOS.e=0）。hf は sensibleInternalEnergy には加算されない。
2. S11/S10: Cp=Cv+CpMCv=1000。ideal-gas の R を Cv に足して Cp を作る route ではない。
3. S12: const transport は mu を固定し、Pr と kappa は排他入力。Pr を入力した場合 k=Cp mu/Pr=**0.0140845070422535… W/(m K)**。
4. S13: thermo が T から rho_T、mu、k を更新し、nu()=mu/rho_T を返す。
5. S14: Stokes の nuEff=nu。solver rho_s が応力係数 rho_s nuEff に入る。収束して rho_s=rho_T なら動粘性応力係数は mu に戻る。非定常・反復途中の不一致時は厳密には mu rho_s/rho_T。
6. S15: Fourier は温度で -div(k grad T) を作り、k/Cpv（ここでは k/Cv）を energy implicit correction に使う。this->alpha() は単相体積分率1であり、温度拡散率 alpha ではない。

収束した局所値は

\[
\nu(T)={\mu\over\rho_T},\qquad
\alpha_T(T)={k\over\rho_T C_v}={\mu\over\rho_T Pr},\qquad
{\nu(T)\over\alpha_T(T)}=0.71.
\]

局所 Pr は同一密度・Cp=Cv の条件で一定だが、nu と alpha は一定でない。反復中には solver rho_s と thermo rho_T を区別し、実効係数をむやみに同一視しない。

| 位置 | rho [kg/m³] | nu [m²/s] | alpha_T [m²/s] |
|---|---:|---:|---:|
| T0 | 1 | 1e-5 | 1.40845070422535e-5 |
| Th | 0.9995 | 1.00050025012506e-5 | 1.40915528186628e-5 |
| Tc | 1.0005 | 9.99500249875063e-6 | 1.40774683080994e-5 |

**[OF13]** molWeight は specie の形式入力。今回の rho/e/Cv/Cp/mu/k の経路では R を使わない。S10 の Z は R を使うが、本 module の上記方程式経路で Z は使用しない。したがって単相非反応の監査対象経路では分子量は輸送解に入らない。entropy など別 thermo API まで無影響とは広げない。

**[PROJECT]** 参照 nu0=1e-5、alpha0=nu0/0.71、速度尺度 alpha0/L=1.40845070422535e-4 m/s、時間尺度 L²/alpha0=710 s。Ra は参照 rho0/nu0/alpha0 から仕様の式で再計算し、局所係数に基づく値を目標 Ra と取り違えない。

**[OPEN] OQ-04:** 仕様の重力表は表示値が丸められており、その桁をそのまま入力すると Gate A の相対差1e-10を満たさない条件がある。例えば Ra=1e3 の g=0.1408450704 は約1.68e-10の相対差。将来は **仕様4.2の式**から十分な桁で生成する（目標・物性の変更ではない）。

## 9. Numerical-scheme candidates

### 9.1 方針と active operators

**[PROJECT]** 一様直交40²/80²/160²で中心差分相当を主候補とする。空間二次精度を狙うが、壁・角部・極値抽出を含む全比較量が必ず二次収束するとは仮定せず Gate F で実測する。以下は設計候補の一覧であり fvSchemes は作成していない。

| 種類・active term | 主定常候補 | 非定常候補・補足 | ソース |
|---|---|---|---|
| ddt(rho,U), ddt(rho,e), ddt(rho,K), ddt(rho), ddt(p_rgh), ddt(p) | 全て steadyState | 全て backward。psi=0 の p_rgh ddt も式構築で参照される | S03/S05–S07/S22 |
| ddtCorr(rho,U,phi) | steadyState により零 | 同じ backward。静的 mesh の lookup は ddt(rho,U) | S07/S27 |
| grad(U)（応力）、後処理 grad(T) | Gauss linear | 同じ | S14 |
| div(phi,U), div(phi,e) | Gauss linear | 同じ | S03/S05 |
| div(phi,K), div(phi,(p\|rho)) | Gauss linear | 同じ。energy の追加項も指定する | S03/S28 |
| div(phi), div(phiHbyA)、devTauCorrFlux の divergence | 既存 face flux の有限体積積分 | convection scheme の lookup ではない | S26/S27 |
| momentum Laplacian（補間した rho_s nuEff、U） | Gauss linear orthogonal | 同じ | S14 |
| pressure Laplacian（rhorAUf または rhoRAtUf、p_rgh） | Gauss linear orthogonal | 同じ | S07 |
| thermal explicit Laplacian（k,T） | Gauss linear orthogonal | 同じ | S15 |
| thermal energy laplacianCorrection（k/Cv,e） | コードで固定の uncorrected orthogonal matrix correction | 通常の laplacian(e) scheme lookup と違う。係数補間を指定 | S27 |
| snGrad(rho), snGrad(p_rgh), snGrad(U), snGrad(T) | orthogonal | 同じ。壁 T.snGrad は patch 評価 | S04/S07/S14/S15 |
| rho、rho*rAU、rho*rAtU、rho_s nuEff、k/Cv の補間 | linear | 同じ | S07/S14/S27 |
| flux(HbyA)、stress の dotInterpolate | linear | 同じ | S14/S27 |
| 初期 phi の rho*U | hard-coded linearInterpolate | scheme 辞書で upwind に切替える処理ではない | S04 |
| reconstruct、surface integration、K=magSqr(U)/2、rho U·g | コードの幾何・代数操作 | 独立の対流 scheme は不要 | S03/S04/S07 |

S26 により v13 の応力補正は直接面流束 divc であり、古い `div(((rho*nuEff)*dev2(T(grad(U)))))` というキーだけを追加して「応力 scheme を設定した」とはしない。公式 tutorial にその項目があっても本機の active code を優先する。

辞書化するときは ddt の mode 判定用 default を明示し、全 active lookup に上表の名前または明示的パターンを割り当てる。対流の未指定 default は none、補間・勾配・Laplacian も明示的に選ぶ。計算名から生成される係数名は v13 の式に照合してパターンで網羅し、暗黙の「適当な default」へ依存しない。S27 の固定演算子は辞書項が存在しないことを記録する。`transonic=false`、`consistent` の採否は fvSolution で明示する案。

### 9.2 tutorial との差と安定化

S28 は Euler、U/e upwind、corrected Laplacian/snGrad、RAS kEpsilon、nut/alphat/k/epsilon を含む。benchmark は **laminar、放射なし、粒子なし**。これらをコピーしない。一次 upwind は主結果に使わない。

高 Ra・粗格子では cell Peclet 数が大きく、中心差分行列が単調性を失い振動する可能性がある。まず反復緩和・pressure/energy coupling・格子解像度を調べる。緩和は離散方程式の収束解を変えないことを再収束比較で示す。limiter が必要なら別条件IDで、平均/局所 Nu、速度極値、位置、保存量、観測次数の変化を中心差分と比較する。必要性や影響の証拠なしに limiter を主設定へ昇格させない。

線形解法は圧力に PCG+DIC または GAMG、非対称 U/e に PBiCGStab+DILU 等を候補とするが、具体 tolerance、緩和、回数は [OPEN] のまま。solution residual と物理監視窓を併用する。smoke 結果で計算効率を決めても、物性・Ra・acceptance criteria を事後調整しない。

## 10. Steady vs transient strategy

**[OF13]** 両方可能。S22 は default ddt が steadyState なら mesh.schemes().steady() とし、S23 は nOuterCorrectors=1 のとき steady を **SIMPLE mode**、transient を **PISO mode** と表示する。複数 outer correctors は PIMPLE 反復。いずれも制御辞書はこの module の `PIMPLE` を使用する。旧 solver 名を使って判断しない。

| 観点 | A. 直接定常 | B. 非定常から定常到達 |
|---|---|---|
| 時間離散 | steadyState。時間行列・ddtCorr が零 | backward。密度付き ddt と flux correction が有効 |
| coupling | PIMPLE 内の SIMPLE mode を第一候補（outer=1） | PISO（outer=1）または PIMPLE（outer>1） |
| 密度 | thermo rho と反復緩和、質量 flux projection | rho continuity 更新、EOS 再同期も含む |
| 数値的意味 | 非線形定常連立式の固定点反復。Time 表示は反復ラベル | 物理時間の初期値問題。十分後に定常解を比較 |
| benchmark 適合 | 定常を直接求め、仕様6.1の主計算と一致 | 定常極限が同じ離散定常式に達すれば比較可能。非定常の物理は原論文主表の判定対象外 |
| 長所 | 時間刻み誤差なし、定常比較を簡潔に分離 | 初期過渡、到達履歴、将来の時系列検証に利用可能 |
| 短所 | 高 Ra で緩和・収束が難しい可能性。残差だけで誤収束する | 時間刻み・終了時間・inner収束の誤差、計算量増。closed-volume EOS 整合にも注意 |

**[PROJECT] 推奨案:** 主12条件は直接定常、非定常は Gate J の別 study。理由は仕様と一致し時間誤差を主結果から分離できること。定常収束が難しい場合の transient 到達案はユーザー判断で採否を決め、主判定手順を無断で置き換えない。最終決定はまだ行わない。

Gate D は最終200反復以上の Rwin≤5e-4、速度/e/圧力の正規化残差≤1e-7を目標、熱収支非増加、正常終了を併用する。**[PROJECT] 監視のゼロ除算 scale 案:** 無次元平均Nu/Umax/Vmax は各1、熱収支 Q は参照 conduction heat rate k DeltaT W を使う。収束停止は残差条件を満たした後も200反復の窓を満たすよう設計し、早期 residualControl 終了だけで合格にしない。

非定常は Co 0.5/0.25、必要なら0.125、同じ初期 U=0/T0 と backward。最終値の比較と無次元時間での定常到達を記録し、初期過渡平均で未収束を隠さない。初回の backward 履歴不足・可変時間刻みも記録する。

## 11. Route A vs Route B

| 評価 | Route A: foamRun+fluid+Boussinesq | Route B: 最小専用実装 |
|---|---|---|
| continuity | 密度付き、体積 divergence 非零 | div(u)=0 の volume-flux projection |
| momentum | rho慣性・偏差応力・rho gh 分離 | 一定rho0/nu0、浮力だけ beta(T-T0) |
| thermal | e 総エネルギー構成、追加仕事項 | 定数alpha0 の温度対流拡散のみ |
| 標準機能 | Foundation の module/thermo/BC/熱流束を利用可能 | 方程式・圧力・BC・後処理の独立検証が必要 |
| 主なリスク | epsilon 感度で評価できない energy 部分、圧力 gauge、EOS/質量再同期 | 実装誤り、維持負担、標準 wallHeatFlux registry の再利用可否 |
| 必要な証拠 | Gate H に加え energy 差の定量化案 | 方程式の厳密一致監査・単体試験、Gate H 代替の Hard 証拠 |

**[GATE]** A なら仕様どおり Ra=1e6、fine160²、epsilon=1e-3/1e-4、betaを1/10・gを10倍、その他同一の Gate H は必須。3主量相対差各≤0.2%、epsilon_v は低下または非悪化。失敗すれば A でコア合格を出さず、原因を continuity/momentum/energy/後処理に分けて B 案を提示する。

**[PROJECT] 追加提案（仕様への追加は未承認）:** 同じ解から energy の K 輸送、圧力仕事、重力仕事、相殺後 source、EOS/solver density 差を共通の熱拡散尺度で報告し、全体相殺と局所残差を確認する。Gate H に合格しても、共通する追加項が主量に十分小さいと示せなければ、方程式を一致させた B との同条件比較を検討する。Cv を変更して誤差を小さくする方法は物性変更になるので採用しない。

B が必要となる条件は、(i) Gate H/G 等の不合格がモデル差に起因、(ii) 非 O(epsilon) の energy 影響を許容以下と立証できない、(iii) 圧力 gauge に主量が依存して古典 benchmark の比較を損なう、(iv) 研究目的が項単位の厳密一致を要求する、と整理する。今回コードは作成しない。B は既存 v13 thermo を単に Boussinesq に変えるだけでは達成できず、一定密度の質量/運動量と独立 T 式を設計する必要がある。

**現時点の推奨 route:** 仕様どおり **A を条件付きの第一候補**として、初期圧力整合と energy 誤差の検証設計を先に確定する。A の完全一致や Gate H だけによる十分性は認めない。採否と追加証拠の扱いはユーザーが決定する。

## 12. Proposed file structure

予定一覧のみ。以下のファイル・ディレクトリは本タスクで作成していない。現行 `Scripts/` の大文字小文字を保持する。

| 将来のパス | 内容と方程式・モデル |
|---|---|
| `cases/template/0/U` | 初期静止、noSlip/empty。運動量と壁流束 |
| `cases/template/0/T` | T0、左Th/右Tc、上下断熱、empty。thermal境界 |
| `cases/template/0/p` | Pa、p_rghと整合した静水圧初期値、calculated/empty。thermoの必須入力 |
| `cases/template/0/p_rgh` | Pa、初期0とfixedFluxPressure/empty。浮力圧力補正 |
| `cases/template/constant/physicalProperties` | 2節のtuple、rho0/T0/beta、Cv/hf/specie、mu/Pr。EOS・熱量・輸送 |
| `cases/template/constant/momentumTransport` | simulationType laminar、明示Stokes。Newtonian応力 |
| `cases/template/constant/thermophysicalTransport` | laminar/Fourierの明示選択。定数k熱拡散 |
| `cases/template/constant/g` | Raから高精度生成した (0,-g,0)。浮力 |
| `constant/hRef`, `constant/pRef`（必要時） | 静水圧・一様圧力の規約。省略時0をmanifestに記録。勝手に追加値を設定しない |
| `cases/template/system/blockMeshDict` | L×L×W、等間隔40/80/160、z方向1セル、wall/empty |
| `cases/template/system/fvSchemes` | 9節の全active lookup、定常/非定常の切替 |
| `cases/template/system/fvSolution` | PIMPLE、pressureReference、線形解法・緩和・収束、rho solve必要時 |
| `cases/template/system/controlDict` | application foamRun、solver fluid、反復/時間、出力・監視function objects |
| `system` 内の後処理設定（controlDictから参照可） | wallHeatFlux、中心線サンプル、無次元量、残差・保存監視 |
| `cases/Ra*_grid*/`、conduction/smoke/sensitivity/transient領域 | 再現可能な入力・case ID。12主条件と補助条件を区別 |
| `Scripts/` の将来生成・実行・監視・解析用ファイル | 物性/重力/格子の生成、環境check、実行、Nu/極値/保存/GCI/図の抽出 |
| `results/run_manifest.json` | 版・build・host・入力hash・物性・参照/局所係数・実際Ra/Pr・格子・BC・圧力規約 |
| `results/benchmark_summary.csv` | 4Ra×3gridの主量・位置・基準値・誤差・status |
| `results/grid_convergence.csv` | 3grid差、次数、GCI、非単調診断と320²追加 |
| `results/conservation.csv` | 壁/断面heat、mass/volume divergence、symmetry、density drift |
| `results/figures/`、各ケース実行ログ | 温度/流れ/中心線/局所Nu/収束/格子誤差の証拠 |

e/rho/K/phi を不要な独立初期入力として追加せず、thermo/module の生成経路を使う。nut/alphat/k/epsilon、radiation、particle、MRF、mesh-motion 辞書は今回不要。root直下の0/constant/systemを別ケースとして重複作成せず cases 内に配置する案。Bのソース領域は必要性判断と明示許可後の別設計。

## 13. Planned verification sequence

### 13.1 順序と合否

**[PROJECT]/[GATE]** 指定順序は妥当。保存・対称性は計算中から監視し、後段で正式判定する。物理条件・基準値・acceptance criteria の変更は提案しない。

1. 本監査の Open questions 解決、route/圧力規約/抽出法を決定、実装開始の明示指示。実装後に Gate A/B の全証拠を確認。
2. **Ra=0 conduction、80²以上** → Gate C。g=0、線形theta=1-X、無流動、両壁Nu=1。熱流束の符号を校正。
3. **Ra=1e4、40² smoke** → 実行・coupling・監視・出力の健全性。反復上限等の運用設定を固定。
4. **4 Ra × 3 grids = 12主条件** → 全条件Gate D。fineでGate E、全gridでGate F。
5. **grid convergence** → Nu単調、fine–medium差・観測次数・GCI。非漸近/振動する量は320²を追加。
6. **conservation / symmetry** → fineでGate G。基準値一致だけで保存失敗を合格にしない。
7. **Boussinesq sensitivity** → AのGate H。必要な追加energy証拠は11節の提案をユーザー判断後に組み込む。
8. Gate I diagnostic と Gate K traceability を確認。A∧B∧C∧D∧E∧F∧G∧H∧K成立時だけ `BENCHMARK_CORE_PASS`。
9. **optional transient** → Gate J、Co0.5/0.25、必要なら0.125。合格時だけ `DOWNSTREAM_TRANSIENT_READY`。

| Gate | 変更せず維持する判定値 |
|---|---|
| A | Pr/Raの目標相対差≤1e-10、2D/mesh/版/入力/実際係数・境界の証拠 |
| C | 両壁Nu誤差≤0.001、独立2経路差≤0.1%、無次元速度≤1e-6、cell中心温度最大誤差≤1e-4 |
| D | 200反復以上の3主量Rwin≤5e-4、残差≤1e-7目標、熱収支非増加・正常終了 |
| E | 4Raのfine平均Nu/Umax/Vmax各≤1%、速度極値位置≤0.01 |
| F | 各主量fine–medium≤1%、Nu単調、GCI Nu≤1.5%・速度各≤2%、Fs=3 |
| G | heat imbalance≤0.2%、断面算出時≤0.5%、epsilon_m≤1e-6、epsilon_v≤2e-3、両対称L2≤0.2% |
| H | 3主量差各≤0.2%、volume divergence減少/非悪化 |
| I | 局所Nu極値各≤3%、位置≤0.02はDiagnostic、超過時原因分析 |
| J | 最終3主量の時間系列差各≤0.5%、E/Gも合格、定常到達履歴 |
| K | 全行case_id/Ra_target/Ra_actual/Pr_actual/grid/route/status/source_time_or_iteration/method_version |

Gate F の \(p_{obs}=\ln|(\phi_3-\phi_2)/(\phi_2-\phi_1)|/\ln2\)、\(GCI_f=3|(\phi_1-\phi_2)/\phi_1|/(2^{p_{obs}}-1)\) を維持する。未定義・負・不合理な次数で形式合格にしない。速度非単調/振動/漸近域外は320²追加、Nuの単調必須は緩和しない。

### 13.2 Nu・保存・抽出の設計案

**[OF13]** Fourier の q は外向き伝導熱流束 \(-k\partial_nT\)。S16 の wallHeatFlux は **-q**、従って \(w=k\partial_nT\) で流体への流入が正。qr が registry にあればさらに subtract するので、放射なし/qrなしを確認する。wall patch だけが対象。function object は thermophysicalTransportModel を registry に要求するので、Tファイルだけの単独postProcessで必ず使えるとはしない。

S16 の Q=ΣAf wf [W]、qmean=Q/ΣAf [W/m²]。体積fieldの内部0をvolume-averageして壁値の代わりにしない。今回の壁面積は A=L W=1e-4 m²、参照 conduction Q0=k DeltaT W=1.40845070422535e-5 W。

**[PROJECT]** hot壁法線n=-ex、cold壁n=+exだから、Nuの規約は

\[
Nu_h={L\over\Delta T}(\partial_n T)_h,
\quad Nu_c=-{L\over\Delta T}(\partial_n T)_c,
\]
\[
\overline{Nu}_h={Q_h\over k\Delta T W},\qquad
\overline{Nu}_c={-Q_c\over k\Delta T W}.
\]

hot の w/Q は正、cold は負。絶対値ではなくこの座標変換を使う。平均Nuの主値はface面積加重。有限体積face列へSimpson則を機械的に適用しない。

独立2経路は、(1)温度と壁位置からwall-normal gradientを抽出して上式へ変換、(2)公式wallHeatFluxのQを規格化、とする。同じwallHeatFlux場の変換だけを二経路と呼ばない。両者は物理的に同じFourier則を共有するので、Ra=0の解析解との校正も必須。

**[PROJECT] 診断の定義案:** 質量divはpressure-corrected phiのcell face収支/V、体積divは同じphiを同じlinear rhofで除したvolume fluxのface収支/V。壁はnoSlip flux0、empty faceは寄与なし、volume weightingはV_i/ΣV_i。再構成速度からlinearInterpolate(U)·Sfで作るdivも併記し、pressure fluxと再構成Uの違いを隠さない。Gate Gへ適用する主定義は実装前に固定する（OQ-05）。非定常はddt(rho)も含む保存残差・全質量を別途監視し、定常Gateのdiv(rho u)だけで過渡を判定しない。

対称L2の提案は \(\langle|e_\theta|^2\rangle_V^{1/2}/\max(\langle|\theta|^2\rangle_V^{1/2},10^{-12})\)、\(\langle|e_U|^2\rangle_V^{1/2}/\max(\langle|U|^2\rangle_V^{1/2},10^{-12})\)。温度は0–1theta、速度は熱拡散尺度の無次元U、180°写像を同じ補間で評価する。Ra=0の零速度ではGate Cを主に使い、L2 absolute defectも併記する。許容0.2%を変更しない。

中心線は正確な X=0.5/Y=0.5 上へ補間して正のUmax/Vmaxと位置を同時に抽出する。案として全格子共通の無次元等間隔4097点を用い、端点noSlipを含め、linear cell-point補間とpeak近傍局所二次補間を固定して使う。点列密度を倍にした抽出差は数値解析誤差として確認する。負の対称極値も保存する。最近傍cellだけの最大値を主値にしない。角部Nu端点の再構成はface-center値と区別して報告する未確定事項（OQ-06）。

断面 \(Nu_x=\int(U\theta-\partial_X\theta)dY\) を計算する場合は仕様の0.5%基準を維持する。Route Aはrho輸送・追加仕事を含むため、この古典断面Nuが厳密なエネルギー保存量とは限らない。rho e/rho K/p u/k grad T等のsolver保存診断も別に計算して不一致を切り分ける。断面Nu・中心対称性のモデル差と、壁熱収支の離散誤差もepsilon感度と関連付ける。

連続体の定常・閉領域で \(\nabla\cdot(\rho\boldsymbol u)=0\)、壁流束0なら、\(\int_V\rho\boldsymbol u\cdot\boldsymbol g\,dV=\int_V\nabla\cdot(gh\rho\boldsymbol u)\,dV=0\)。全領域でenergyを積分するとK・圧力・thermal移流の境界fluxも零で、両壁の熱量は一致する。したがって **Route Aの追加項を理由に壁熱収支基準を緩める必要はない**。離散式ではgravity sourceがcellのrho U、保存fluxがphiなので、その不整合と反復誤差を評価する。

### 13.3 想定計算量

12主条件の面内セル数合計は4(1600+6400+25600)=**134400**。conduction80²、smoke40²、感度160²を別実行すると計15実行、総セル数168000。smokeを正式主条件として再利用できるなら14実行（入力・収束・出力が全て正式基準に合う場合）。非定常は最低2系列、320²は1条件102400セルでfineの4倍。時間依存では格子細分化による時間刻み縮小も増分となる。wall-clockは未実行なので数値を創作せず、将来smokeで測る。反復上限・終了無次元時間は仕様の[OPEN]を維持。

## 14. Risks and unresolved questions

### Open questions

| ID | 区分・問題 | 決定・解決方法 |
|---|---|---|
| OQ-01 | [OPEN] 作業領域名がdeVahlDavisとdeVahlDavisBenchmarkで不一致 | 現在のcwdを将来も使う案を確認。移動や別領域生成はしない |
| OQ-02 | [GATE] 初期p_rgh=0と必須0/p・既定初期化の整合、基準値の対象場 | 7.3節のp=rho0 gh+pRef整合案、hRef/pRef、pRefCell/Valueの規約を実装前に決定。入力0だけを見て整合を認定しない |
| OQ-03 | [GATE] 全差分がO(epsilon)で消えるという期待は成立しない | 5.2/11節の追加energy証拠案を決める。Gate Hは保持し、これだけで十分と断定しない。必要ならBを提案、採否はユーザー判断 |
| OQ-04 | [OPEN] 重力表示桁とRa相対差1e-10 | 表の丸め値でなく仕様の式から高精度生成し、実際入力からRaを再計算 |
| OQ-05 | [OPEN] divergence/L2/監視規格化・線形解法・緩和/補正回数 | 本書の案を計算前に固定。残差の意味、phiとUの整合、200反復窓を記録。smokeによる運用決定は追跡可能にする |
| OQ-06 | [OPEN] 中心線補間・局所Nuの角部/端点極値 | 13.2節の抽出案、壁face対節点の差を固定。局所量はDiagnostic、主量と混同しない |
| OQ-07 | [OPEN] 非定常closed-volume EOS/solver rho再同期と全質量整合 | sourceなし・psi=0の制約を確認し、密度差/全質量履歴・内反復収束を記録。Gate Jとは別に原因分析 |
| OQ-08 | [OPEN] 過去研究の正確なv5版・custom modifications | 公式5.xとの比較を過去custom solverの同一性証明に使わない。必要なら別監査 |
| OQ-09 | [OPEN] sourceと配布binaryの完全一致・build識別 | 今回package/options/hashを記録。実行許可後のbanner・log/必要なlibrary識別をGate A manifestへ保存 |

リスクはモデル差、数値誤差、反復誤差、抽出誤差を分離する。Ra=1e6の中心差分・一様160²で1%一致が得られることを事前保証しない。標準routeは古典的な中心対称性や断面Nuにモデル差を生じ得る。壁熱収支は13.2節の定常積分保存も確認し、いずれもGate Gの基準を無断で緩めない。圧力定数のchoiceはenergyへ入るため純粋な無影響gaugeと扱わない。

**解決済み:** `cf13` 未定義はユーザーの代替有効化指示で監査続行可能となり、Foundation v13を確認済み。OpenFOAM 6へのfallbackはしていない。

## 15. Recommendation

**[PROJECT]** Route Aを条件付き第一候補として保持し、主計算の直接定常SIMPLE mode、中心差分相当、Stokes/Fourier、仕様物性、指定の検証順序を推奨する。理由はFoundation v13の標準機構を利用でき、研究仕様の計画と一致すること。ただし **古典式と完全に同じsolverという前提で実装しない**。

**[GATE]** 実装前に OQ-02 の初期圧力/基準場の整合案と OQ-03 の非O(epsilon) energy差を評価する方針を決定し、OQ-05/06の診断・抽出法を固定する必要がある。Gate Hはそのまま必須とし、追加証拠が必要か、Bを選ぶかはユーザーが最終判断する。これらを未解決のまま実装準備完了やAUDIT_PASSとはしない。

本書は実装前監査の成果物であり、計算による合否証拠ではない。ユーザーが明示的に許可するまで、ケース・solver・スクリプト実装へ進まない。

IMPLEMENTATION READY: NO
