# Route B — OpenFOAM Foundation v6 pre-implementation audit

記録改訂: 1.1（2026-10-03）。原監査日: 2026-09-30。対象は **Foundation v6 `buoyantBoussinesqSimpleFoam` のソース上の適合性**であり、計算結果の合格ではない。原監査の研究仕様は `benchmark_spec.md` v1.1、判定基準は `acceptance_criteria.md` v1.1。現行は両文書とも v1.2。`openfoam_design.md` は Route A の v13 監査としてのみ参照した。3文書を監査前に読んだ。原論文値、物性計画、許容値は変更していない。

> **記録の読み方:** 本文の「将来」「実装前」「今回は作成しない」は監査実施時の記録として保持する。その後 `routeB_implementation.md` により minimal implementation は完了した。現在状態は末尾の post-audit update にまとめる。

本書の **[PAPER]** は研究仕様に採録された原論文条件、**[OF6]** は下記ローカル v6 ソースで確認した実装事実、**[OF6-CANDIDATE]** は採用候補という研究上の位置づけ、**[OF13]** は既存 Route A 監査に限定した事実、**[PROJECT]** は今後の設定案、**[GATE]** は実装・計算前に満たす条件、**[OPEN]** は未確定事項を表す。ソースからの連続体式への変形は「解析的導出」と明記する。

## 1. Environment audit

作業領域 `pwd` は `/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark`。`type cf6` は非対話・対話 bash の両方で未定義だった。read-only で `/home/mirai/.bashrc` を調べると `cfdem6='bash --rcfile ~/.bashrc_cfdem6'` が定義され、`/home/mirai/.bashrc_cfdem6` は `/home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc` を source していた。したがって **設定ファイルが明示する同じ v6 bashrc** を直接 source して以下を確認した。CFDEM の追加環境は本監査に不要であり読み込んでいない。`cf13` および v13 環境は今回のソース監査に使用していない。

```text
source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc
foamVersion                         OpenFOAM-6
which buoyantBoussinesqSimpleFoam    /home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam
WM_PROJECT                          OpenFOAM
WM_PROJECT_VERSION                  6
WM_PROJECT_DIR                      /home/mirai/OpenFOAM/OpenFOAM-6
FOAM_RUN                            /home/mirai/OpenFOAM/mirai-6/run
WM_OPTIONS                          linux64GccDPInt32Opt
```

**[OF6]** v6 bashrc は `WM_PROJECT_VERSION=6` を設定し、ソルバのヘッダは `openfoam.org` / `OpenFOAM Foundation`、ローカル Git remote は `https://github.com/OpenFOAM/OpenFOAM-6.git`、HEAD は `af7d7f427be78e9b9beb6aceca8fe7d5d4636876`（2018-09-14）。追跡ファイルの `git status --short --untracked-files=no` は空だった。これらと実行ファイルの絶対パスから **OpenFOAM Foundation v6** と判断し、OpenCFD/ESI fork と区別した。配布 binary と現在のソースの完全一致はソース閲覧だけでは証明できず、実装後の Gate A manifest に runtime banner と build 情報を残す **[OPEN]**。環境切替後もプロジェクトは上記 v13-run 内の現行領域に留めた。

## 2. Source evidence table

以下のパスは全てローカル Foundation v6 ツリー。S 番号を本文の各結論に付す。リンクの行は代表行で、括弧内は確認した範囲である。

| ID | フルパス・根拠処理 |
|---|---|
| S01 | [buoyantBoussinesqSimpleFoam.C](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/buoyantBoussinesqSimpleFoam.C:53)（53–103: include、SIMPLE loop、UEqn→TEqn→pEqn） |
| S02 | [createFields.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/createFields.H:1)（1–126: T/p_rgh/U/phi、rhok、alphat、gh、p、reference、radiation/options） |
| S03 | [readTransportProperties.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/readTransportProperties.H:1)（1–18: beta/TRef/Pr/Prt） |
| S04 | [UEqn.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/UEqn.H:5)（5–35: U 対流、応力、MRF/options、浮力・圧力予測） |
| S05 | [TEqn.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/TEqn.H:1)（1–27: alphat/alphaEff、T 式、radiation/options、rhok 更新） |
| S06 | [pEqn.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/pEqn.H:2)（2–66: phig、p_rgh Poisson、phi/U 補正、p 基準） |
| S07 | [createPhi.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/incompressible/createPhi.H:34)、[continuityErrs.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/incompressible/continuityErrs.H:32)（34–47: `phi=fvc::flux(U)`、32–46: `div(phi)` 診断） |
| S08 | [readGravitationalAcceleration.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/include/readGravitationalAcceleration.H:1)、[readhRef.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/include/readhRef.H:1)、[gh.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/include/gh.H:1)（g MUST_READ、hRef 既定0、gh/ghf） |
| S09 | [singlePhaseTransportModel.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/transportModels/incompressible/singlePhaseTransportModel/singlePhaseTransportModel.C:40)、[viscosityModelNew.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/transportModels/incompressible/viscosityModels/viscosityModel/viscosityModelNew.C:40)、[Newtonian.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/transportModels/incompressible/viscosityModels/Newtonian/Newtonian.C:44)（transportProperties、Newtonian `nu`、一定 field） |
| S10 | [TurbulenceModel.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/TurbulenceModels/turbulenceModels/TurbulenceModel/TurbulenceModel.C:90)、[turbulentTransportModels.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/TurbulenceModels/incompressible/turbulentTransportModels/turbulentTransportModels.C:30)、[laminarModel.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/TurbulenceModels/turbulenceModels/laminar/laminarModel/laminarModel.C:80)（`simulationType`、incompressible 登録、Stokes 既定） |
| S11 | [Stokes.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/TurbulenceModels/turbulenceModels/laminar/Stokes/Stokes.C:85)、[linearViscousStress.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/TurbulenceModels/turbulenceModels/linearViscousStress/linearViscousStress.C:68)（nut=0、nuEff=nu、偏差応力の div） |
| S12 | [createIncompressibleRadiationModel.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/thermophysicalModels/radiation/include/createIncompressibleRadiationModel.H:1)、[radiationModelNew.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/thermophysicalModels/radiation/radiationModels/radiationModel/radiationModelNew.C:32)、[noRadiation.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/thermophysicalModels/radiation/radiationModels/noRadiation/noRadiation.C:71)、[radiationModel.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/thermophysicalModels/radiation/radiationModels/radiationModel/radiationModel.C:230)（none の零 source、rhoCpRef の条件付き読込） |
| S13 | [createFvOptions.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/include/createFvOptions.H:1)、[createMRF.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/include/createMRF.H:1)、[IOMRFZoneList.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/MRF/IOMRFZoneList.C:32)、[MRFZoneList.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/MRF/MRFZoneList.C:164)（空 options、MRFProperties 不在・空 MRF で追加源なし） |
| S14 | [findRefCell.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/findRefCell/findRefCell.C:30)（30–119: `pRefCell`/`pRefPoint`/`pRefValue` と needReference） |
| S15 | [constrainPressure.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/constrainPressure/constrainPressure.C:59)、[fixedFluxPressureFvPatchScalarField.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure/fixedFluxPressureFvPatchScalarField.C:131)（圧力勾配と所望壁流束の一致） |
| S16 | [emptyFvPatchField.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fields/fvPatchFields/constraint/empty/emptyFvPatchField.C:65)、[polyMesh.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/OpenFOAM/meshes/polyMesh/polyMesh.C:90)（empty patch 型検査と面外 solution direction の除外） |
| S17 | [simpleControl.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/solutionControl/simpleControl/simpleControl.C:59)、[singleRegionSolutionControl.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/solutionControl/solutionControl/singleRegionSolutionControl/singleRegionSolutionControl.C:58)、[fluidSolutionControl.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/solutionControl/solutionControl/fluidSolutionControl/fluidSolutionControl.C:69)、[nonOrthogonalSolutionControl.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/solutionControl/solutionControl/nonOrthogonalSolutionControl/nonOrthogonalSolutionControl.C:60)（SIMPLE 辞書・反復・制御キー） |
| S18 | [wallHeatFlux.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/functionObjects/field/wallHeatFlux/wallHeatFlux.C:61)（61–116: alpha·snGrad(he) と qr、204–240: registry 要求、246–290: integral） |
| S19 | [fvmDiv.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvm/fvmDiv.C:43)、[fvmLaplacian.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvm/fvmLaplacian.C:210)、[fvcSnGrad.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcSnGrad.C:42)、[fvcDiv.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcDiv.C:44)、[fvcFlux.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcFlux.C:35)、[surfaceInterpolate.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/interpolation/surfaceInterpolation/surfaceInterpolation/surfaceInterpolate.C:78)、[fvSchemes.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvSchemes/fvSchemes.C:398)（fvSchemes lookup と直接 face 積分） |
| S20 | [hotRoom/transportProperties](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/constant/transportProperties:18)、[turbulenceProperties](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/constant/turbulenceProperties:18)、[fvSchemes](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/system/fvSchemes:18)、[fvSolution](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/system/fvSolution:37)、[p_rgh](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/0/p_rgh:17)、[U](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/0/U:17)、[g](/home/mirai/OpenFOAM/OpenFOAM-6/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/constant/g:18)（v6 構文・次元の対照専用。RAS/upwind/物性値は転用しない） |
| S21 | [zeroGradientFvPatchField.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fields/fvPatchFields/basic/zeroGradient/zeroGradientFvPatchField.H:137)、[noSlipFvPatchVectorField.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fields/fvPatchFields/derived/noSlip/noSlipFvPatchVectorField.C:34)（断熱 T と U 壁条件） |

主要ファイル SHA-256: S01 `abd34036fbe81e415f333a9d6ca0854f15b70f77fd837d5dc048861ebd65f909`、S02 `123e261cecbd8ff187b40e529f07b92b2594252d13e8405464f05e50474f3418`、S04 `74a2aa996ff4de945965c62d9881e224a7931c236d62e1914093c7f00f421e02`、S05 `13056bf4ad6a45089c86d7c64d17e561036e6076faa16fa63cebc8fcfbf9acfb`、S06 `9ba4feb13369ac01da0da42411dee7375c4c7c1aa4e7f7d4ac6c2dbb5668c21b`、S18 `5b556514755950ec254a1f8fe60b4479c4065f851e2fe492b3c071b78dd53bb5`。ソース・binary の同一性確認は Gate A の後続作業で行う。

## 3. Target de Vahl Davis equations

**[PAPER]** `benchmark_spec.md` 3.3 の対象は `div(u)=0`、一定 `nu0` の運動量、温度による密度変化は浮力だけ、一定 `alpha0` の温度対流拡散である。基準静水圧を除く有次元式は

\[
\nabla\cdot\boldsymbol u=0,\quad
\partial_t\boldsymbol u+(\boldsymbol u\cdot\nabla)\boldsymbol u
=-\nabla\pi+\nu_0\nabla^2\boldsymbol u
-\beta(T-T_0)\boldsymbol g,\quad
\partial_tT+\boldsymbol u\cdot\nabla T=\alpha_0\nabla^2T.
\]

本候補は**定常 solver**であり `partial_t` 項を持たない。今回の原論文定常値に対してはそれらが零となるが、この executable によって過渡解を検証したとは言わない。`g=(0,-g,0)`、`T0=TRef=300 K`、`theta=(T-Tc)/DeltaT`、速度尺度 `alpha0/L` で、浮力係数は `Ra Pr` となる。

## 4. Solver architecture

**[OF6]** S01 は個別 executable、`simpleControl` の反復で **UEqn → TEqn → pEqn** を順に実行し、その後に輸送・乱流モデルを `correct()` する。S02 は `T`,`p_rgh`,`U`,`alphat` を MUST_READ し、`phi` を作り、`rhok` と診断用 `p` を生成する。`p` は NO_READ/AUTO_WRITE、`rhok` は内部生成場。`gh` は `constant/g` と任意 `constant/hRef` から得る。S09–S11 の系は **incompressible singlePhaseTransportModel + incompressible turbulenceModel**であり、v13 の thermophysical EOS や `fluid` module ではない。S12/S13 の radiation、fvOptions、MRF は汎用 hook だが、今回の設定では零とする。

## 5. Continuity equation audit

**[OF6]** S07 の `phi=fvc::flux(U)` は face における `U·Sf` の**体積流束 [m³/s]**であり、`rho U·Sf` の質量流束ではない。入力 `phi` が存在すれば READ_IF_PRESENT なので、将来ケースでは読み込まれる既存 `phi` の出所・次元も監査する。S06 の pressure equation は

\[
\nabla_h\cdot(rAU_f\nabla_h p_{rgh})=\nabla_h\cdot\phi_{HbyA},\qquad
\phi=\phi_{HbyA}-\operatorname{flux}(p_{rgh}\text{ Eqn})
\]

という face-flux 補正で、収束した離散流束の `div(phi)=0` を強制する。S07 の `continuityErrs.H` も `fvc::div(phi)` を評価する。S02/S04–S06 のどこにも `rhok*phi` を連続式へ入れる処理はない。有限反復・線形 solver tolerance の誤差は別に Gate G で判定する。

**判定: EXACT MATCH（定常の対象方程式の構造）。** 体積流束 `phi` に対する零発散であり、温度依存密度の質量保存式ではない。速度場から再構成した divergence と補正後 `phi` の divergence は離散的に異なり得るため、両者を区別して報告する。

## 6. Momentum equation audit

**[OF6]** S04 の主行列は `fvm::div(phi,U)+MRF.DDt(U)+turbulence->divDevReff(U)==fvOptions(U)`。`fvm::ddt` も `rhok` を掛けた慣性・移流もない。MRF ゾーンを作らなければ S13 の `DDt(U)` は零、fvOptions が空なら source も零。laminar/Stokes/Newtonian なら S09–S11 により `nut=0`、`nuEff=nu0` で、粘性離散式は `-fvm::laplacian(nu0,U)-fvc::div(nu0*dev2(T(grad(U))))` を左辺に置く。連続体対応は `nu0[laplacian(u)+(1/3)grad(div u)]` の応力発散であり、`div u=0` なら原論文の `nu0 laplacian(u)` と一致する。有限格子での勾配補正・非零再構成 `div(U)` は離散化差として Gate F/G で確認する。

S04 の momentum predictor は面法線の `-ghf*snGrad(rhok)-snGrad(p_rgh)` を再構成する。`rhok` はここ、S06 の buoyancy flux と `p=p_rgh+rhok gh` のみに現れ、U の慣性、対流、粘性係数、T 方程式、連続式には現れない（S02/S04–S06）。**[PROJECT]/[GATE]** MRF zone、fvOptions の U/T source、非 Newtonian viscosity、RAS/LES を無効にする。

**判定: MATCH UNDER STATED ASSUMPTIONS。** 定常・laminar・Newtonian・`div u=0`・零追加源の連続体式として古典運動量に対応する。rhok は浮力とその静水圧分離、および診断圧力 p の構成に使われる。

## 7. Boussinesq buoyancy and p_rgh audit

**[OF6]** S02/S03/S08 と v6 tutorial S20 の次元指定を合わせると、`U` は m/s、`p` と `p_rgh` は **kinematic pressure [m²/s²]**、`gh` と `ghf` も [m²/s²]、`rhok` は無次元、`g` は [m/s²]、`beta` は [1/K]。Pa の `p` を入力する Route A とは異なる。式は

\[
rhok=1-\beta(T-TRef),\quad gh=\boldsymbol g\cdot\boldsymbol x-ghRef,
\quad ghRef=-|\boldsymbol g|hRef,\quad p=p_{rgh}+rhok\,gh.
\]

S06 の `phig=-rAUf*ghf*snGrad(rhok)*|Sf|` と pressure Poisson の流束補正が、`-gh grad(rhok)` を U に戻す。**解析的導出:** `grad(gh)=g` なので

\[
-\nabla p_{rgh}-gh\nabla rhok=-\nabla p+rhok\boldsymbol g
=-\nabla(p-gh)-\beta(T-TRef)\boldsymbol g.
\]

`g=(0,-g,0)`、`T>TRef` なら `-beta(T-TRef)g_vector=+beta g(T-TRef)e_y` で**上向き**。`TRef=T0`、`T-T0=DeltaT(theta-1/2)` と置き、空間一様の `-beta g DeltaT/2` を圧力勾配へ吸収すれば、熱拡散尺度で `+Ra Pr theta e_y`。S02/S06 は基準静水圧を `rhok gh` として分離している。この導出は連続体の積の法則によるもので、離散した `phig` と pressure correction が同じ恒等式を厳密に満たすとは主張しない。

## 8. Temperature equation audit

**[OF6]** S05 は未知量 `T` を直接解き、定常式を

\[
\nabla_h\cdot(\phi T)-\nabla_h\cdot(\alpha_{eff}\nabla_h T)
=S_{rad}/(\rho Cp) + S_{fvOptions},\qquad
\alpha_{eff}=\nu/Pr+\alpha_t,
\quad \alpha_t=nut/Prt
\]

と構成する。ソースの `radiation->ST(rhoCpRef,T)` は radiationModel の実装で `Ru/rhoCpRef−Sp(Rp*T³/rhoCpRef,T)`。`radiationModelNew.C` は radiationProperties が無ければ `none`、S12 の noRadiation は `Ru=Rp=0`、`correct()` も空。よって noRadiation のとき `rhoCpRef` は初期値1のままであり、`rhoRef`/`CpRef` は**読まれず**、T 解に入らない。放射を有効にすると同じ名前の物性が条件付きで必要となるので、本 benchmark では有効にしない。fvOptions も空にする。

S10/S11 で `simulationType laminar`、Stokes とすれば `nut=0`。S02 の `alphat` は MUST_READ なので、内部・境界で零になる設定が必要。`Prt` は S03 で laminar でも必須入力だが `nut=0` なら解に寄与しない。Newtonian `nu0` と `Pr=0.71` なら **`alphaEff=alpha0=nu0/Pr` 一定**。T 解に `rhok`、kinetic energy、pressure work、gravitational work、compressibility work、viscous dissipation、密度重み付き energy storage は現れない。S05 は T 解の**後**に `rhok` を更新するため、反復中は U が直前の rhok を使う固定点連成である。

**判定: EXACT MATCH（定常の対象方程式、laminar/定物性/零 source 条件下）。** 未収束反復では分割連成誤差があり、最終定常性を Gate D で判定する。

## 9. Transport-property mapping

**[PROJECT]** `L=0.1 m`、`W=0.001 m`、`T0=TRef=300 K`、`Th=300.5 K`、`Tc=299.5 K`、`DeltaT=1 K`、`rho0=1 kg/m³`、`beta=1e-3 K⁻¹`、`mu=1e-5 Pa s`、`Pr=0.71` を維持する。**[OF6]** 実際の v6 入力経路は S03/S09/S20 の `constant/transportProperties` にある `transportModel Newtonian; nu [0 2 -1 0 0 0 0] ...; beta; TRef; Pr; Prt`。ここで入力するのは **動粘度 `nu0=mu/rho0=1e-5 m²/s`** であり、`mu` [Pa s] を `nu` キーに入れてはならない。Newtonian.C は `nu` を一定 field にし、singlePhaseTransportModel と turbulence model がこれを渡す。S05 は `nu/Pr` を直接使用する。

\[
\nu_0=10^{-5}\ \mathrm{m^2/s},\qquad
\alpha_0=\nu_0/0.71=1.40845070422535\times10^{-5}\ \mathrm{m^2/s},
\quad Pr_{actual}=0.71.
\]

`rho0` と `mu` は v6 solver の必要入力ではなく、プロジェクトの参照値・換算の根拠として manifest に記録する。`cv=1000`、分子量、生成エンタルピー、v13 の thermo tuple はこの v6 `T` solver に入力しない。`rhoRef`,`CpRef` は放射を使わない限り S12 で読まれない。`Prt` は v6 構文上必要だが laminar の定常解には寄与しない値として記録する。重力は `constant/g` で `Ra nu0 alpha0/(beta DeltaT L³)` から**表示表の丸め値でなく**十分な桁数を使う（Gate A の 1e−10 を維持）。基準熱伝導率 `k=rho0 Cp alpha0` と有次元熱量は solver からは決まらず、後処理で `Cp` の定義を明示する必要がある（14節）。

## 10. Laminar-model audit

**[OF6]** S02 は `incompressible::turbulenceModel::New(U,phi,laminarTransport)` を生成する。S10 は `constant/turbulenceProperties` の `simulationType` を読み、`laminar` を選べる。laminar subdict を省略した場合、S10 は Newtonian stress の **Stokes** を既定で作る。明示する場合は v6 構文の `laminarModel Stokes` を使う。S11 は Stokes `nut()` と patch `nut()` を零、`nuEff()` を `nu()` とする。名称 Stokes は**応力モデル名**であり、UEqn の慣性・対流を消す creeping-flow 近似ではない。S05 の `alphat=nut/Prt` も零とし、RAS/LES または tutorial の kEpsilon を選ばない。

## 11. Boundary-condition audit

**[PAPER]/[PROJECT]** 左・右・上・下の `U=noSlip`、左 `T=Th`、右 `T=Tc`、上・下 `T=zeroGradient` を維持する。S21 の `zeroGradient` は `snGrad()` を零と返し、定数 `alpha0` の S05 の拡散項では上下の伝導 flux が零になる。front/back は mesh patch と `U,T,p_rgh,alphat` の場で `empty` とし、z方向1セル、面外初期速度0、`g_z=0` を合わせる。S16 は empty patch 型を照合し、面外方向を解から除く。今後 Gate A で幾何と二次元性を確認する。

**[OF6]** S06 は `phiHbyA` に `phig` を加えた後、S15 `constrainPressure(p_rgh,U,phiHbyA,rAUf,MRF)` を呼ぶ。物理壁の `fixedFluxPressure` は予測流束と指定壁速度の face flux（noSlip なら0）が一致するよう法線勾配を更新する。これは**kinematic `p_rgh`**の境界であり、S20 の公式 v6 tutorial にも使用例がある。`zeroGradient p_rgh` に機械的に置換しない。`fixedFluxPressure` 自体は辞書中の `rho rhok` により温度密度を自動適用する処理ではなく、S15 が勾配を設定する。front/back は `empty`。

閉領域は全壁が flux 型なので pressure gauge が必要。S02 の `setRefCell(p,p_rgh,simple.dict(),...)` と S14 により **`system/fvSolution` の `SIMPLE` 下の `pRefCell`（または `pRefPoint`）と `pRefValue`** を使う。キーは `p` から作るが、needReference は `p_rgh` で判定する。S06 は p_rgh 行列の reference にその cell の現値を渡し、解後に `p=p_rgh+rhok gh` を作って `p(refCell)=pRefValue` となる全体シフトを行い、`p_rgh=p-rhok gh` と再同期する。**pRefValue は最終的な kinematic p の値 [m²/s²]**で、v13 Route A の Pa 圧力基準とは別。格子ごとの cell ID と座標を将来記録する。

**初期圧力:** S02 は `0/p_rgh` を MUST_READ、`p` を NO_READ で自動生成する。したがって Route A OQ-02 のような `0/p` と `0/p_rgh` の同時指定矛盾は **ない**。`U=0,T=TRef,rhok=1,p_rgh=0` なら生成直後は `p=gh`、基準値の一様シフトを除き静水圧に整合する。初期 `p` の gauge shift は最初の pEqn 前には `p_rgh` へ反映されないが、p は U/T 式で使われず、S06 が後で再同期する。T 壁の初期境界温度に伴う rhok 境界値も確認し、実装時に初期 field と基準後の値を記録する。

## 12. Numerical-scheme audit

**[PROJECT]** 等間隔・直交40²/80²/160²上で中心差分相当を主候補とする。下表は**将来の候補**であり `fvSchemes` は作成していない。S04–S06、S11、S19 により active operator と lookup を分けた。

| active operator | v6 lookup / 候補 | 備考 |
|---|---|---|
| U/T の ddt | 式に ddt なし。`ddtSchemes default steadyState` を明示候補 | 反復時刻は物理時間でない |
| `fvm::div(phi,U)`, `fvm::div(phi,T)` | `div(phi,U)`, `div(phi,T)` → `Gauss linear` | 一次 upwind を主結果に使わない |
| `fvc::grad(U)` | `grad(U)` → `Gauss linear` | 粘性偏差応力の explicit correction |
| `grad(T)` | solver の T 式には直接現れない。後処理で使うなら `Gauss linear` | T 式の diffusion は laplacian、浮力は `snGrad(rhok)` |
| momentum `fvm::laplacian(nuEff,U)` | `laplacian(nuEff,U)` または明示 default → `Gauss linear orthogonal` | nuEff=nu0 |
| momentum `fvc::div(nuEff*dev2(T(grad(U))))` | `div((nuEff*dev2(T(grad(U)))))` → `Gauss linear` | S11 と v6 tutorial S20 の式名を実装前に照合 |
| thermal `fvm::laplacian(alphaEff,T)` | `laplacian(alphaEff,T)` → `Gauss linear orthogonal` | alphaEff=alpha0 |
| pressure `fvm::laplacian(rAUf,p_rgh)` | `laplacian(rAUf,p_rgh)` → `Gauss linear orthogonal` | 直交 mesh の想定 |
| `fvc::snGrad(rhok)`, pressure の snGrad、壁温度 gradient | `snGradSchemes` → `orthogonal`。壁の `T.patch.snGrad()` は BC 自身の評価 | 浮力の明示 face 勾配を落とさない |
| 初期 `fvc::flux(U)`、`fvc::interpolate(rAU)`, `fvc::flux(HbyA)`, stress の face 補間 | `interpolationSchemes` → `linear` | S07/S19。`flux(U)` と `flux(HbyA)` も補間 scheme lookup |
| `fvc::div(phiHbyA)`, continuity `fvc::div(phi)` | face の幾何積分。独立の convection scheme lookup なし | S19 の `surfaceIntegrate` |
| `MRF.DDt(U)`, `radiation->ST`, fvOptions、RAS/LES の k/epsilon 等 | benchmark 設定では零・非 active | 追加辞書を tutorial からコピーしない |

v6 公式 hotRoom tutorial S20 は RAS と U/T の `bounded Gauss upwind`、corrected laplacian を含む。今回の中心差分・laminar・直交 mesh にそのまま複製しない。高 Ra の coarse 格子では cell Peclet 数増大による振動や反復不安定があり得る。まず収束制御と格子依存を確認し、limiter 等が必要なら別ケースで主量・局所 Nu・GCI への影響を定量化する。物性、Ra、許容値を調整しない。

## 13. SIMPLE / steady-solution audit

**[OF6]** S01 は `simple.loop(runTime)`、S17 は `fvSolution` の **SIMPLE** subdict を読む。1反復の順序は momentum predictor（`momentumPredictor` 既定 true）、T solve と rhok 更新、`nNonOrthogonalCorrectors`（既定0）に応じた p_rgh correction、phi/U/p 更新、その後 laminarTransport と turbulence の correct、書出しである（S01/S04–S06/S17）。S06 では最終非直交反復だけが保存的 phi を更新する。`UEqn.relax()`、`TEqn.relax()`、`p_rgh.relax()` と `fvSolution/relaxationFactors` を使える。S17 の residualControl は収束停止を制御するが、Gate D の**最終200反復以上の Nu/速度極値/熱収支の安定性**を省略できない。

これは直接定常の固定点反復であり、`Time = ...` は反復ラベルであって物理経過時間ではない。定常原論文 benchmark には適切だが、本 solver で非定常 Gate J を実行しない。必要なら後続別 solver/route 設計とする。

## 14. Nusselt and wall-heat-flux audit

**[PAPER]** `Nu_h=-L/DeltaT·(dT/dx)|hot`。hot 壁外向き法線は `−e_x`、cold は `+e_x`。定数 `alpha0` の面積重み付き face 法線勾配を使えば

\[
\overline{Nu}_h={L\over\Delta T A_h}\sum_{f\in hot} A_f(\partial_n T)_f,
\qquad
\overline{Nu}_c=-{L\over\Delta T A_c}\sum_{f\in cold} A_f(\partial_n T)_f,
\]

で両壁の正の熱輸送を表せる。局所 Nu は各 wall face の対応する勾配から取り、角部/端点の扱いを別途固定する。`A_h=A_c=L W`、`W=0.001 m`。`Nu_bar=Q/(k DeltaT W)` と書く場合の物理熱流束は hot 側で `Q_h=k sum(A_f partial_n T)`、cold は符号反転する。

**[OF6] 標準 `wallHeatFlux` はこの solver に直接適用不可。** S18 は `compressible::turbulenceModel` あるいは `solidThermo` を registry から探すが、S02 が作るのは **`incompressible::turbulenceModel`**で、`he` field/thermo もない。両方無ければ FatalError。S18 の `alpha*snGrad(he)` はエネルギー場を前提に [kg/s³]=[W/m²] の field を作り、外向き温度勾配が正の高温壁で正、低温壁で負となる符号規約を持つ。`qr` があれば差し引き、各 wall patch で `sum(A_f wallHeatFlux_f)` [W] を `integral` として出す。`min/max` は face 値で、面積平均ではない。これは T に `alpha0` を掛けてそのまま使える経路ではない。`rhoRef CpRef` を勝手に指定しても registry 要求は解消しない。放射を使わなければ `qr` の補正も不要。

**[PROJECT]/[GATE] 独立した Nu 算出経路:** (1) v6 の face/patch `snGrad(T)` と面積積分で定義どおり Nu を算出する。(2) wall face ごとに既知の壁温度と法線方向の第1・第2 cell-centre T から局所二次多項式を再構成し、その壁面微分を積分する。第2経路は `snGrad` field を再利用しない。壁に隣接する直交 cell 列、角部の端点、非一様化時の距離は実装前に固定する。Ra=0、80²以上の解析解 `theta=1−X` で両壁 Nu=1、2経路差≤0.1%、U≈0、T 直線性を Gate C で確認する。主結果は有限体積 face 値の面積加重値とし、別再構成との差と局所 Nu の角部感度を報告する。後処理はまだ実装しない。

`k=rho0 Cp alpha0` は**熱量 [W] への物理換算を選ぶ場合のみ**必要で、v6 solver は noRadiation では Cp を読まない。研究仕様の `cv=1000 J/(kg K)` を v6 の必須 `Cp` 入力と偽らない。`Cp` の採用値を実装前に明記すれば `Q_h/(k DeltaT W)` の k は約分され、Nu は同じ温度勾配から決まる。熱保存を物理 Q で報告するときも、この任意換算を一貫して使う。

## 15. Differences from de Vahl Davis equations

| 対象項 | v6 候補と古典式の関係 | 判定・根拠 |
|---|---|---|
| `div u=0` | `div(phi)=0`、phi は U の体積 flux | 一致、S02/S06/S07 |
| 定常慣性・移流 | `div(phi,U)`、温度密度なし。ddt は solver に存在せず定常問題では零 | 定常で一致、S01/S04 |
| 粘性 | Stokes の偏差応力。`div u=0` なら `nu0 laplacian U`、離散的 correction は残る | 仮定付き一致、S09–S11 |
| 圧力・浮力 | kinematic p、`p_rgh=p−rhok gh`、`−beta(T−TRef)g` | TRef=T0 で一致、S02/S03/S06/S08 |
| 温度 | `div(phi,T)−laplacian(nu0/Pr,T)=0` | laminar/零 source で一致、S05/S09–S12 |
| 追加 energy work | K、圧力仕事、重力仕事、可変密度貯蔵はない | 古典式と一致、S05 |
| 数値的差 | SIMPLE 分割・有限反復、有限体積応力/面勾配、壁・角部抽出、中心差分安定性 | Gate C–G で評価、S04–S06/S11/S19 |

結論は**定常・laminar・Newtonian・零放射/源/MRF・適切な境界/物性という条件で、原論文式に十分対応する**こと。これは掲載値への一致を予告しない。Gate E/F/G と局所診断は実装・計算後に独立に判定する。

## 16. Route B vs Route A comparison

この表の Route A 欄だけが `openfoam_design.md` の **[OF13]** 監査結果。v6 の証拠は上記 S 番号であり、v13 ソースを v6 の根拠に使わない。既存 Route A 設計書の旧 v1.0 推奨/合格論理は、現行 v1.1 研究仕様により置き換わる。

| 観点 | Route B 候補 **[OF6]** | Route A **[OF13]** |
|---|---|---|
| continuity / flux | `div(phi)=0`、`phi=U·Sf` [m³/s] | `ddt(rho)+div(phi)=0`、`phi=rho U·Sf` [kg/s] |
| momentum inertia | U の体積流束移流、温度密度は係数にない | rho U の密度重み付き慣性・移流 |
| viscosity | Newtonian 定数 nu0、laminar Stokes 偏差応力 | 定数 mu から局所 `nu=mu/rho(T)`、偏差応力 |
| buoyancy density | `rhok=1−beta(T−TRef)`、浮力/圧力分離のみ | EOS `rho0[1−beta(T−T0)]` が全輸送に使用 |
| pressure | kinematic p/p_rgh [m²/s²]、`p=p_rgh+rhok gh` | dimensional p/p_rgh [Pa]、`p=p_rgh+rho gh+pRef` |
| thermal | T 直接、`alpha0=nu0/Pr` | e と thermo T、局所 rho 依存の温度拡散 |
| energy work | K/圧力/重力仕事なし | K、圧力仕事、重力仕事等を含む |
| laminar | incompressible turbulence framework の Stokes | compressible framework の Stokes と Fourier |
| steady coupling | 個別 solver の SIMPLE、UEqn→TEqn→pEqn | foamRun/fluid の PIMPLE framework の SIMPLE mode |
| pressure reference | SIMPLE の pRefCell/pRefValue は最終 kinematic **p** を固定 | PIMPLE の pRefCell/pRefValue は補正対象 **p_rgh** の reference |
| wall heat flux | v6 標準 wallHeatFlux は registry 不適合。T 勾配の独立後処理が必要 | v13 の thermophysicalTransport を用いる wallHeatFlux が候補 |

目的はソルバの優劣付けではなく、Route B を古典 Boussinesq 方程式の Verification、Route A をモデル・定式化比較として扱う理由を明確にすること。

## 17. Proposed future Route B file structure

**[PROJECT]** 予定のみで、今回以下のケース・辞書・スクリプトは一切作成しない。Route A と版・入力を分離する。

| 将来のパス例 | 役割 |
|---|---|
| `cases/routeB/template/0/U`, `0/T`, `0/p_rgh`, `0/alphat` | v6 が MUST_READ する初期/境界場。`0/p` は不要 |
| `cases/routeB/template/constant/transportProperties` | Newtonian `nu`、beta、TRef、Pr、Prt |
| `cases/routeB/template/constant/turbulenceProperties` | `simulationType laminar`、必要なら Stokes を明示 |
| `cases/routeB/template/constant/g`, 任意 `hRef` | Ra を満たす負 y 重力、静水圧高さ基準 |
| `cases/routeB/template/system/blockMeshDict` | L×L×W、等間隔40/80/160、z 1セル、前後 empty |
| `cases/routeB/template/system/fvSchemes` | 12節の全 active scheme、主結果は中心差分相当 |
| `cases/routeB/template/system/fvSolution` | SIMPLE、p 参照、線形 solve/緩和/収束監視 |
| `cases/routeB/template/system/controlDict` | v6 個別 solver、反復/出力/監視 |
| `cases/routeB/Ra*_grid*/`、conduction/smoke | 4 Ra×3格子と Gate C/smoke の route 分離 |
| `Scripts/`、`results/` | 後続指示時のケース生成、独立 Nu 後処理、manifest、Gate 表、比較図 |

放射、MRF、fvOptions は使わない。v6 標準 wallHeatFlux を `controlDict` に指定して失敗を隠さず、T face 勾配の後処理計画を先に固定する。

## 18. Risks and unresolved questions

| ID | 内容と次の判断 |
|---|---|
| RB-01 **[OPEN]** | v6 標準 wallHeatFlux は不適合。二つの T 勾配経路の離散定義・角部処理を実装前に固定し、Gate C で検証する。専用後処理は別タスクの許可後 |
| RB-02 **[OPEN]** | `k=rho0 Cp alpha0` の **Cp** は v6 noRadiation solver の入力でない。有次元 Q を報告するなら換算規約を研究者が固定する。Nu 自体には不要 |
| RB-03 **[GATE]** | `alphat` の全 cell/壁で零、Prt 入力、Newtonian/laminar、zero source/MRF/noRadiation、p_rgh 初期場と圧力参照を将来の実ケースで確認する |
| RB-04 **[GATE]** | 高 Ra の中心差分・一様160²で Gate E/F を満たす保証はなく、緩和・格子・局所 Nu の影響を結果で確認。許容値変更や upwind 主結果化はしない |
| RB-05 **[GATE]** | v6 ソースと使用 binary の build 対応、実際に読み込まれた入力・Pr/Ra・2D・境界を Gate A manifest で確認する |
| RB-06 **[OPEN]** | `phi` READ_IF_PRESENT なので、restart 時に古い/別版 flux を誤読しないよう出所と次元を記録する |
| RB-07 **[OPEN]** | v13 Route A 設計書の OQ-01（作業領域名）・OQ-05/06（診断と補間）は現在の v1.1 方針と共通して残る。v13 の旧 Route B=専用実装という提案を現在の v6 採用条件へ転用しない |

## 19. Gate B checklist

`acceptance_criteria.md` v1.1 Gate B の**ソース監査**について、以下を確認した。`ROUTE_B_AUDIT_PASS` は本監査の候補適合判断を表し、Gate A/C–G/K の**計算合格を意味しない**。

| 要件 | 監査判定・証拠 |
|---|---|
| volume flux と `div U=0` | 満たす。S02/S06/S07、5節 |
| 慣性・粘性に温度密度がない | 満たす。S04/S09–S11、6節 |
| `rhok` は浮力・圧力分離のみ | 満たす。S02/S04–S06、7節 |
| T の定数 alpha0 対流拡散 | 条件付きで満たす。S05/S09–S12、8–10節。laminar/alphat=0/零源必須 |
| p_rgh/gh/符号/reference | 満たす。S02/S06/S08/S14/S15、7/11節。p は kinematic |
| SIMPLE と active scheme | 満たす。S01/S17/S19、12/13節。具体辞書は後続実装 |
| 壁熱流束・Nu | 標準 v6 FO は不適合と判明。S18、14節の独立 face 勾配2経路で Gate C の計画を立てた |
| 原論文式との差の列挙 | 15節。定常・零源・laminar・定物性で重大な連続体方程式差は確認されない |

**[GATE]** Gate B のソース上の採用条件は満たす。実際の辞書・境界・後処理と binary build の検証は、後続のユーザー指示による実装・計算の Gate A/C 以降で行う。候補適合は benchmark 合格宣言ではない。

## 20. Recommendation

**[OF6-CANDIDATE]/[PROJECT]** Foundation v6 `buoyantBoussinesqSimpleFoam` を Route B の**実装候補として採用可能**と判断する。理由は、体積連続式、温度密度を係数に含まない U 式、浮力専用 `rhok`、一定 `nu0/Pr` の T 式がローカル v6 ソースで追跡でき、原論文の定常式と所定条件下で対応するため。必須条件は Newtonian、laminar/Stokes、`alphat=0`、放射・MRF・fvOptions 無効、kinematic 圧力と正しい p 参照、中心差分相当、独立 Nu 後処理である。標準 wallHeatFlux を直接使用しない。

採用の最終研究判断と実装開始はユーザーが行う。本書の **IMPLEMENTATION READY** は後続の実装作業に必要なソース監査が揃ったという意味に限る。今回、CFD ケース、solver、辞書、スクリプト、計算、OpenFOAM 本体の変更・ビルドは行っていない。

ROUTE B CANDIDATE: ACCEPTABLE

IMPLEMENTATION READY: YES

## 21. Post-audit status update（2026-10-03）

本節は `routeB_implementation.md`、`results/routeB/run_manifest.json`、`minimal_test_summary.csv`、`conservation.csv`、`failed_runs/` を照合した現在の状態である。上記の監査本文と当時の結論は保持する。

### 21.1 実装で確認された項目

- Foundation v6 build `6-af7d7f427be7`、Newtonian/laminar/Stokes、`alphat=0`、放射・MRF・fvOptions なし、定数 $\nu_0$/$\alpha_0$、kinematic $p/p_{rgh}$、中心差分相当を B-COND/B-SMOKE の実入力・log で確認した。RB-03 と RB-05 の minimal-case 確認は完了。
- B-COND（$Ra=0$、80×80×1）は Gate C PASS。B-SMOKE（$Ra=10^4$、40×40×1）は正常終了、収束、熱収支、流れの向きを確認し smoke test PASS。Route B minimal implementation PASS。
- RB-01 は計画どおり「v6 標準 `wallHeatFlux` を使えない」ことを実行時にも確認した。command-line `postProcess -func grad(T)` も installed v6 の dictionary digest で停止したため、B1 は監査済み fixed-value patch `snGrad=(Twall-Towner)*deltaCoeffs` を実 field/mesh に直接適用した。B2 は `Tw,T1,T2` の独立二次再構成。失敗 log は `results/routeB/failed_runs/F-B1-POST-001/` に保存済み。
- 上記ソース監査は現行 v1.2 の Gate B の全条件を満たすため、`ROUTE_B_AUDIT_PASS` を付与する。

### 21.2 未完了と diagnostic concern

- B-SMOKE の B1/B2 平均 Nu 差は `0.1013155%`で、Gate C に用いる0.1%値を僅かに超える。B-COND 自体は十分な余裕で Gate C 合格であり、これは coarse smoke の後処理 diagnostic として full matrix で追跡する。
- B-SMOKE の補正後 volume-flux は $\epsilon_\phi=4.2984\times10^{-11}$ だが、cell U から再構成した $\epsilon_v=\epsilon_m=4.3054223\times10^{-3}$ は fine-grid Gate G 閾値 $2\times10^{-3}$ を超える。coarse smoke なので formal Gate G failure ではない。
- Route B の4 Ra × 3 grids、Gate E/F、formal fine-grid Gate G、final Gate K は未実施。`BENCHMARK_CORE_PASS` は未付与である。coarse smoke の原論文への近さを benchmark 合格と呼ばない。

POST-AUDIT CURRENT STATUS: ROUTE_B_AUDIT_PASS

ROUTE B MINIMAL IMPLEMENTATION: PASS

BENCHMARK_CORE_PASS: NOT AWARDED
