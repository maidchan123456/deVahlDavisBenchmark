# Route B epsilon_phi Hard Threshold Review

## 1. Purpose

レビュー日: 2026-10-04（Asia/Tokyo）。Foundation OpenFOAM v6 `buoyantBoussinesqSimpleFoam` の pressure-corrected face volume flux に基づく Candidate B を対象とする。

**結論: 数値 `tau_phi` は UNRESOLVED。Decision tree は Case C。推奨は Scheme 3（事前のerror budget）を主軸に、Scheme 2の条件付き残差変換とScheme 4の独立検証で裏付ける方式である。Candidate B は PROVISIONAL。** 支配方程式から条件付き上界は導けるが、linear solver toleranceだけから全Ra・全格子に共通の数値は導けない。検討した一次資料にも、この演算子・規格化へそのまま適用できる数値閾値は確認できなかった。

今回solverは一切実行していない。既存benchmarkのepsilon_phiを閾値導出に使用せず、post-hoc consistency checkも実施しない。既存レビューに記載された結果は背景資料として扱い、合否や数値設計へ使用しない。現行Formal Ra=1e3 Gate GはFAIL、新仕様による判定はNOT_EVALUATEDを維持する。

## 2. Current epsilon_phi definition

cell i、face fの外向き符号を s_if、保存された体積流束を phi_f とする。

$$
q_i=\sum_f s_{if}\phi_f,\quad d_i^\phi=q_i/V_i,\quad
M_\phi=\langle|d_i^\phi|\rangle_V
=\frac{\sum_i|q_i|}{V_\Omega},\quad V_\Omega=\sum_i V_i,
$$

$$
\epsilon_\phi=\frac{L}{U_p}M_\phi,\qquad U_p=\max_{\mathrm{cell}}|\boldsymbol U|.
$$

phi、qの単位はm³/s、Vはm³、dとMはs⁻¹、L/Upはs、epsilon_phiは無次元。Upは保存cell速度の大きさの最大値であり、中心線のbenchmark Umaxや速度成分の最大値ではない。一定rho0でrho0 phiを使っても、rho0で除した質量保存指標は同じ値になる。温度依存のrhokを連続式へ掛けない。

実装 [S01] はinternal faceをownerへ加算、neighbourから減算する。物理壁は**保存phiのboundary値**をownerへ加算し、壁流束を無条件にゼロへ置換しない。front/backはemptyとして寄与を除外する。patch順序・個数はRoute Bの単一blockに固定されており、任意polyMeshへ汎用化された処理ではない。均一V=(L/nx)(L/ny)widthなので、実装の算術平均は体積平均と一致する。非一様格子へ転用する場合は実Vとpatch metadataに基づく処理が必要である。

この定義はsolverの離散連続式を直接評価する点で適切。ただし平均が局所異常を隠すこと、保存phiの出力精度に依存すること、Upが小さいと規格化が不安定になることが閾値設計上の制約。Up=0では実装がNoneを返す。Ra=0はGate Cの絶対速度・伝導条件で扱い、任意のUp floorは追加しない。

## 3. OpenFOAM pressure residual definition

ここではv6 PCGの実装を確認した [S03–S06]。圧力linear solveの開始時fieldをp⁰、boundary/referenceを組み込んだ系を A_s p=b_s とする。

$$
\bar p^0=\frac{1}{N_c}\sum_i p_i^0,\qquad
a_{\mathrm{bar}}=(A_s\boldsymbol1)\bar p^0,
$$

$$
N_p=\sum_i\left(|(A_s p^0)_i-a_{\mathrm{bar},i}|
+|b_{s,i}-a_{\mathrm{bar},i}|\right)+10^{-20},
$$

$$
R_{\mathrm{initial}}=\frac{\|b_s-A_s p^0\|_1}{N_p},\qquad
R_{\mathrm{final}}=\frac{\|r_{\mathrm{rec}}\|_1}{N_p}.
$$

normはglobal unweighted L1 sumで、p平均もcell数によるglobal算術平均。各matrix row自体が体積積分されたFV方程式なので、このnormをcell divergenceの算術平均と同一視しない。N_pは各solveの入口で一度計算し、そのsolve中は固定する。`small_=1e-20` は分母の正則化定数であり、machine epsilonや物理的保存閾値ではない [S06]。

PCGは残差を再帰更新するため、最終報告値の分子r_recと、最終pから再計算したtrue residual b_s−A_s pが有限精度では一致しない場合がある [S03:172–180]。initial residualは毎回のpressure solve前、final residualはその内部solve後の量である。SIMPLE outer iterationの収束指標やGate Dの監視値と区別する。

収束判定は `R_final < tolerance` **または** `relTol > 1e-20` かつ `R_final < relTol*R_initial` [S05:70–94]。relTol=0なら相対条件は無効。`tolerance` は規格化残差に対するabsolute toleranceであり、m³/sの絶対不均衡ではない。maxIter、singularity、minIterも関与し、単に設定されたtoleranceから成功終了を仮定しない。

N_pはmatrix係数（rAU、面積、距離、格子、reference行）、source（phiHbyA、boundary・明示補正）、入口圧力field、BCに依存する。未参照Neumann Laplacianでは定数圧力シフトに不変な構造があるが、reference行を変更した系でその不変性を無条件に仮定できない。物理的流束の圧力ゲージ不変性とsolver残差の規格化を区別する。

## 4. Relation between algebraic residual and flux divergence

[S02:29–39] のpressure equationと補正は

$$
\mathrm{laplacian}_h(rAU_f,p^*)=D_h(\phi_{HbyA}),\qquad
\phi=\phi_{HbyA}-F_h(p^*).
$$

p*は**pressure relaxation前のsolve解**。phiを設定した後にp_rghをrelaxし、Uを別に再構成する [S02:39–46]。保存されたrelaxed p_rghだけからこのsolveを再現することは一般にはできない。

referenceを除き、boundaryと明示face補正を同じ流束形式で組み込んだ物理系を A₀p=b₀ と定義する。FV matrix sourceにVが掛かる [S08:1458–1466] ため、b₀−A₀pとqの単位はともにm³/s。matrixとface fluxが整合する正確算術では

$$
q_i=V_i D_h(\phi)_i=(b_0-A_0p^*)_i.
$$

符号規約を逆にしても以下のL1評価は同じ。explicit nonorthogonal correction、fixedFluxPressure、最後の非直交solve、boundary assemblyが一致していることが条件である。matrix fluxにはboundary寄与とfaceFluxCorrectionが含まれる [S08:948–953]。

**reference行に注意。** `setReference` はreference cellのsourceとdiagを変更する [S08:507–518]。solverが見るr_s=b_s−A_s p*はその変更後の系なので、reference cellのr_sをそのまま物理qと扱えない。BCを組み込む処理も [S07:154–169] にある。

この差をdelta_ref、matrix/faceの不整合をdelta_op、保存・後処理の差をdelta_outとし、E_rec=||r_s−r_rec||₁と定義すると、三角不等式による条件付き上界は

$$
\epsilon_\phi\le\frac{L}{U_pV_\Omega}
\left(N_pR_{\mathrm{final}}+E_{\mathrm{rec}}
+\|\delta_{\mathrm{ref}}\|_1+\|\delta_{\mathrm{op}}\|_1
+\|\delta_{\mathrm{out}}\|_1\right).
$$

Upは判定対象の保存Uから求める。同一Up・Vを用い、欠陥を全て除ける理想条件では

$$
\epsilon_\phi=K_pR_{\mathrm{final}},\qquad
K_p=\frac{LN_p}{U_pV_\Omega}.
$$

**K_p=1を保証する根拠はない。** よって `tolerance=1e-10 => epsilon_phi<=1e-10` は不可。relTol=0かつabsolute条件を満たした場合のみR_final<toleranceを代入できる。relative終了を許す場合は有効なrelTolについてmax(tolerance,relTol R_initial)を使う。未収束終了なら設定値による上界は使えない。

閉領域・単一reference cell jの場合の別の保守的評価も導ける。非reference行でq_i=r_s,i、全boundary net fluxをBとすると、内部faceの相殺からq_j=B−sum_(i≠j)q_i。したがって

$$
\sum_i|q_i|\le2\sum_{i\ne j}|r_{s,i}|+|B|,
$$

$$
\epsilon_\phi\le\frac{L}{U_pV_\Omega}
\left(2N_pR_{\mathrm{final}}+2E_{\mathrm{rec}}+|B|+E_{\mathrm{other}}\right).
$$

E_otherは非reference行のoperator不整合、丸め・出力の伝播を覆うL1 budget。これはreference差をゼロと仮定する式ではない。B=0、整合operator、無丸めならepsilon_phi<2K_p toleranceという**条件付き**上界になる。しかしN_p、K_p、true残差差、出力budgetを今回測定・定量化していないため、保証された数値上界は得ていない。

Q1: 物理系とfluxが整合すれば代数残差から離散不均衡の式を導ける。Q2: toleranceとの数値同一視は不可。Q3: 規格化はmatrix/source/入口field/reference/BC依存。Q4: 上記の条件付き記号上界は導けるが、tolerance単独による共通数値上界は導けない。

## 5. OpenFOAM native continuity errors

[S09:33–40] では、同じpressure-corrected phiについて

$$
\mathrm{sumLocal}=\Delta t\langle|D_h\phi|\rangle_V,
\quad \mathrm{global}=\Delta t\langle D_h\phi\rangle_V,
\quad \mathrm{cumulative}_k=\sum_{n\le k}\mathrm{global}_n.
$$

均一格子・同一時点・同一phi・同一精度ならsumLocal/deltaTは現在のmean_abs_div_phiと同じ内容で、epsilon_phi=(L/Up)/deltaT*sumLocal。logの丸め、保存fieldの出力精度、浮動小数点の加算順、時点が異なると数値差が生じ得る。globalはsignedなので相殺があり、cumulativeも局所保存性を保証しない。

steady SIMPLEのdeltaTはiteration管理に現れる値であり、その積を実流体の時間積分誤差と解釈しない。deltaTを任意に変更できるnative sumLocalをそのまま全Ra共通Hardにする根拠は弱い。epsilon_phiはadvective scaleで規格化し、native各量は実装整合のcross-checkとして保存する方が今回の目的に合う。native metricへ置換してもthreshold問題は解消しない。

## 6. Normalization by L/Up

L/Upはcavity長さを最大cell速度で横断するadvective time scale。epsilon_phiは「その時間scaleで見た平均的な単位体積当たり離散生成・消滅率」に相当する。signedでないため実際の体積変化の積分値ではない。流れの典型速度と最大速度も同一ではない。

Ra=1e3、1e4、1e5、1e6のUpが異なっても、同じL、Up定義、V平均、face演算子で無次元値を比較できる。ただし**比較可能であることと、同一閾値がsolver/出力誤差を均等に制御することは別**。Upの格子誤差、K_p、conditioning、流束scaleや丸めfloorはRa・格子で変わる。固定tauなら許す dimensional M_phi=tau Up/LもRaで変わる。共通の相対保存budgetを研究目的として事前指定し、全対象Ra・格子で実現性を独立確認することが必要。

Up→0では同じ絶対誤差でもepsilon_phiが増大する。Ra=0はGate Cを用い、epsilon_phiはNOT_APPLICABLE/undefinedとして絶対量を診断保存する案とする。Ra>0でも極小Upへの対応を事前に明記し、後付けのfloorでPASSを作らない。

## 7. Floating-point and numerical floor

Python/NumPy float64で確認したmachine epsilonは2.220446049250313e-16。v6のbashrcはDPを指定 [S12:75–76]。この指定だけで全solver binaryのbuild精度を再監査したことにはならない。machine epsilonは1付近の表現間隔であり、epsilon_phiのfloorではない。

face不均衡の加算について、m_i個のface、unit roundoff u=machine epsilon/2、mu<1なら、通常の丸めモデルによる概算は

$$
|\delta q_i|\lesssim\gamma_{m_i}\sum_f|\phi_f|,
\qquad\gamma_m=mu/(1-mu).
$$

その寄与をL/(Up VΩ) sum_iで伝播できるが、これはphi生成自体の誤差、conditioning、残差再帰のdriftを含む完全保証ではない。face間のcancellationは小さい真qに対する相対誤差を拡大する。細分化でViが小さくなりlocal divergenceの丸め増幅が変わる。cell数・face数とmean/maxのfloorは単純なN倍則で固定できない。

出力誤差をdelta phi_fとすると、共有internal faceが両cellに寄与するため

$$
\|\delta q_{\mathrm{io}}\|_1
\le2\sum_{f\in\mathrm{internal}}|\delta\phi_f|
+\sum_{f\in\mathrm{physical\ boundary}}|\delta\phi_f|.
$$

ASCIIの有効桁数はmachine epsilonより粗い量子化を作り得る。Binaryもscalar幅・形式・読み込み対応を確認する必要があり、保存形式を変えるだけでoperator検証が完了しない。parserのfloat64変換は失われた桁を復元できない。restart時は保存p/U/phiの量子化が次のmatrix、入口p、N_pに伝播する。Up側の出力誤差も分母に伝播する。

matrix conditioning、linear toleranceと停止理由、preconditioner、並列decomposition/reductionの加算順、face accumulation、出力precision、restart、parserを合わせた数値floorは今回一意に決められない。machine epsilonから1e-12等を選ぶことはしない。**floor測定は実現性確認であり、許容物理誤差のerror budgetとは別である。**

## 8. Literature / official-source review

一次情報を優先し、以下を閲覧した。accessed dateは全て2026-10-04。DOIはこれらのWeb/source資料では該当なし。長いsource引用や、異なる定義の数値移植は行わない。

| ID | Title / provider / URL | 本レビューへの寄与と比較限界 |
|---|---|---|
| W01 | OpenFOAM 6 PCG.C Source File — OpenFOAM Foundation; [公式v6 source](https://cpp.openfoam.org/v6/PCG_8C_source.html) | L1規格化残差・再帰更新。ローカルv6実装と照合。保存epsilon_phiの数値閾値を規定しない。 |
| W02 | OpenFOAM 6 lduMatrixSolver.C Source File — OpenFOAM Foundation; [公式v6 source](https://cpp.openfoam.org/v6/lduMatrixSolver_8C_source.html) | N_pの定義。規格化因子を介した変換が必要であり、toleranceそのものは流束不均衡ではない。 |
| W03 | OpenFOAM 6 SolverPerformance.C Source File — OpenFOAM Foundation; [公式v6 source](https://cpp.openfoam.org/v6/SolverPerformance_8C_source.html) | absolute/relativeのOR停止条件。Hard保存性を別途確認する必要がある。 |
| W04 | Notes on Computational Fluid Dynamics: General Principles, 5.4 Residual — Chris Greenshields / Henry Weller, CFD Direct; [解説](https://doc.cfd.direct/notes/cfd-general-principles/residual) | residualのscale normalizationと許容値の概念を説明。バージョン固有の判断はv6 sourceを優先し、一般解説からtau_phiを転記しない。 |
| W05 | Verification Assessment — NASA Glenn / NPARC Alliance, John W. Slater; [公式tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html) | mass conservationのconsistency checkと、code/calculation verificationの区別。ここでの演算子・Up規格化に対する数値は示さない。 |
| W06 | Examining Iterative Convergence — NASA Glenn / NPARC Alliance, John W. Slater; [公式tutorial](https://www.grc.nasa.gov/WWW/wind/valid/tutorial/iterconv.html) | 規格化残差と目的量の反復監視を併用する根拠。残差低下桁数をepsilon_phi Hard閾値へ転用しない。 |

他distribution/versionのOpenFOAM資料、forumの経験値、原論文PDFは数値の根拠にしていない。original SIMPLE論文・peer-reviewed verification論文・AIAA文書原本は今回未精読であり、それらがtau_phiを推奨すると主張しない。NASAのAIAAへの参照はNASAの記述として扱う。**調査した資料で直接移植できる数値は見つからなかった**という限定した結論であり、全世界の文献に存在しないという断定ではない。

ローカルsource位置（pathはabsolute、行はone-based）:

| ID | Source / relevant lines |
|---|---|
| S01 | [analyze_case.py](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeB/analyze_case.py:89):89–116 continuity、258–261 Up/epsilon、357 legacy alias |
| S02 | [pEqn.H](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/pEqn.H:29):29–46 pressure solve/phi/relax/U、52 native continuity |
| S03 | [PCG.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/OpenFOAM/matrices/lduMatrix/solvers/PCG/PCG.C:93):93–117 initial norm、172–188 recursive final residual/stop |
| S04 | [lduMatrixSolver.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/OpenFOAM/matrices/lduMatrix/lduMatrix/lduMatrixSolver.C:174):158–164 controls、174–196 N_p |
| S05 | [SolverPerformance.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/OpenFOAM/matrices/LduMatrix/LduMatrix/SolverPerformance.C:70):70–94 convergence |
| S06 | [SolverPerformance.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/OpenFOAM/matrices/LduMatrix/LduMatrix/SolverPerformance.H:288):288 small_ |
| S07 | [fvScalarMatrix.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fvMatrices/fvScalarMatrix/fvScalarMatrix.C:154):154–169 boundary assembly/solve |
| S08 | [fvMatrix.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/fvMatrices/fvMatrix/fvMatrix.C:507):507–518 reference、948–953 flux correction、1458–1466 integrated RHS |
| S09 | [continuityErrs.H](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/incompressible/continuityErrs.H:33):33–40 local/global/cumulative |
| S10 | [fvcDiv.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcDiv.C:45):45–56 surfaceIntegrate |
| S11 | [fvcSurfaceIntegrate.C](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcSurfaceIntegrate.C:51):51–75 owner/neighbour/boundary/volume |
| S12 | [v6 bashrc](/home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc:75):75–76 DP default |
| S13 | [acceptance_criteria.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/acceptance_criteria.md:281):281–330 current Gate G |
| S14 | [routeB_design.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeB_design.md:76):76–85 continuity model、172 operator |

## 9. Local versus mean conservation

volume-mean absolute M_phiは全領域のL1欠陥を測る主Hard候補。ただし局所品質は保証しない。均一Nc cellでは max|d| ≤ Nc M_phi しか一般には言えず、細分化でこの保証が弱くなる。percentileも極少数の異常cellを除外するため、maxの代用ではない。

提案する将来保存量（今回は実装しない）:

| Metric | Proposed role |
|---|---|
| mean_abs_div_phi、epsilon_phi | Candidate B primary Hard、閾値未確定 |
| max_abs_div_phi、(L/Up)max_abs_div_phi、max cell ID/coordinate | 必須Diagnostic。local error budgetを独立定義できた場合に追加Hard候補 |
| volume-weighted P95/P99(|d|)とそのL/Up規格化 | 分布Diagnostic。分位点の定義・重み・補間を事前固定 |
| max_abs_cell_flux_imbalance_m3_s、局所Vi | dimensional局所budgetの監査。qだけでは格子依存が強く、q/Viも併記 |
| signed net boundary flux、signed volume-mean divergence、absolute total boundary flux | global telescoping/壁条件Diagnostic。signed値だけでHard PASSを出さない |
| native local/global/cumulative、true vs recursive residual difference | solver/source整合Diagnostic |

軽量Python/NumPy合成検証を実施した。L=1m、depth=1m、Uref=1m/sを**試験用に事前指定**し、psi=sin²(pi x)sin²(2pi y)、u=∂psi/∂y、v=−∂psi/∂xを用いた。vertex境界psiを厳密に0とし、Fx=psi(x_i,y_(j+1))−psi(x_i,y_j)、Fy=−[psi(x_(i+1),y_j)−psi(x_i,y_j)]とすると、cellのface和は正確算術でtelescopingして0。cell Uには現行と同じ中央face補間、no-slip wall face=0を使った。

| Grid | exact edge-flux mean | exact edge-flux max | reconstructed U mean | reconstructed U max |
|---|---:|---:|---:|---:|
| 40² | 4.37882e-16 | 1.66533e-14 | 1.32923e-1 | 7.33436e-1 |
| 80² | 2.56834e-16 | 2.22045e-14 | 3.37510e-2 | 3.82315e-1 |
| 160² | 1.28128e-16 | 2.22045e-14 | 8.47068e-3 | 1.93130e-1 |

値の単位はs⁻¹。L/Uref=1sなので試験用無次元値は同じ数値だが、UrefはbenchmarkのUpではない。再構成meanは概ね2次、maxは境界近傍の寄与により概ね1次の減少であり、meanから局所収束も推定できない。edge-fluxの値は特定のtelescoping構成の丸め水準にすぎず、一般のfloorやtau_phiを与えない。

negative controlとして、零fieldの1つのinternal faceだけにdelta_phi=1e-8m³/sを与えた。2つのcellへ±delta_phiが入り、理論値 mean=2delta_phi/VΩ、max=delta_phi/Vi、signed sum=0 をassertで確認した。40²/80²/160²のmeanは全て2e-8s⁻¹、maxは1.6e-5/6.4e-5/2.56e-4s⁻¹、max/meanは800/3200/12800。注入値は演算子試験の既知入力であり、受入閾値の候補ではない。

これは**等価Cartesian operatorの検証**であり、実際のanalyze_case関数、owner/neighbour parser、OpenFOAM boundary serialization、pressure-corrected phiをend-to-endで検証していない。合成phiはsolver phiと異なる。全試験結果を同行JSONへ保存し、新規test/scriptをrepositoryには追加していない。

## 10. Threshold schemes considered

| Scheme | 長所 | 短所 / 必要な根拠 | Ra・mesh・solver依存 | 判断 |
|---|---|---|---|---|
| 1: fixed dimensionless epsilon_phi≤tau_phi | 全Raを一つの相対保存budgetで比較、明快な事前登録 | 共通budgetとlocal guard、出力floorの余裕が必要。数値の一次根拠なし | dimensional許容値はUp依存。gridのUp誤差・floorとtoleranceによる実現性が変わる | 数値UNRESOLVED。方式自体は将来可能 |
| 2: solver-tolerance-linked | solverが解く離散式と直接対応 | K_p、reference/BC、true residual drift、出力誤差を要する。toleranceだけの数値同一視はREJECT | K_pがRa・grid・outer stateで変わる。relTol/停止理由も必要 | 条件付き記号変換のみSUPPORTED。現状Hard採用不可 |
| 3: absolute + relative/error budget | meanと局所欠陥、低速度時の絶対誤差を分けて管理 | 目的量への影響と許容誤差を独立に定義する必要。複数の数値が未確定 | relative scaleはUp/L、absolute budgetはVi・geometry・出力scaleを考慮。solver実現性も別確認 | 推奨する設計主軸、数値UNRESOLVED |
| 4: empirically verified operator floor | parser/演算子/serializationの検証、必要精度の把握 | floorは物理的acceptanceを正当化しない。単一testや任意安全係数を普遍化できない | grid/scale/precision/parallel/restart/versionを事前test suiteでカバー | 支持する補助検証。今回の合成試験だけでは不足 |

Scheme 3の候補形として、mean relative budget eta_meanを独立に設定してepsilon_phi≤eta_meanを要求し、局所について

$$
|q_i|\le V_i\left(a_{\mathrm{local}}+eta_{\mathrm{local}}U_p/L\right)
$$

を別の候補guardとすることができる。a_localはs⁻¹の絶対局所budget、eta_localは無次元。絶対項の選定理由・使えるrangeを事前定義し、許容する物理誤差を後から緩めない。これは例示であり未採用。Ra=0でepsilon_phiをこの式から復活させず、Gate Cへ分岐する。単一fixed tau_phiを必須とする場合も、その値は独立budgetと検証の両方が整ってから登録する。

## 11. Evidence comparison

| Evidence | 得られたこと | 得られていないこと |
|---|---|---|
| 現行operatorとFV source | epsilon_phiがsolver face continuityを測る。uniform平均の整合 | parser・保存形式の全条件での誤差保証 |
| v6 PCG/N_p/reference source | qとtrue pressure残差の条件付き関係、referenceを覆う閉領域上界 | 数値K_p、E_rec、E_other、全Raの共通上界 |
| native continuity | 同一状態ならsumLocal/deltaTとM_phiが対応 | native log自体の物理的Hard threshold |
| float64と合成場 | machine epsilonの確認、mean/max/globalの違い、演算子差 | 実solverのnumerical floor、許容物理誤差、安全係数 |
| 一次資料 | 規格化残差と保存/反復/格子verificationを分離する根拠 | epsilon_phiへ直接移植できる数値tau |
| 既存benchmark結果 | 使用しない | 閾値の事前正当化には寄与させない |

## 12. Recommended threshold strategy

**Scheme 3 + conditional Scheme 2 audit + Scheme 4 verification。** 最初に、benchmarkの目的量精度と独立した保存性要求からmean/localのerror budgetを定義する。次にreference/BC/true residual/serializationを含む変換を定量検証し、そのbudgetをsolver・後処理で達成できるか確認する。operator floorはbudgetが計測可能かを判定する補助根拠とする。

mean absoluteをCandidate B Hard、reconstructed epsilon_vとlegacy epsilon_mをDiagnosticとする方向は妥当。ただしmean単独で局所品質を保証すると書かず、max・percentile・signed/globalを必須の将来保存候補とする。局所Hardを追加するなら独立budget・仕様版を定める。

K_pに比例するだけのtolerance-linked閾値は、solver toleranceを緩めると許容保存誤差も緩まるため、物理受入budgetの代替にはしない。toleranceは独立budgetを満たせるよう設計・監査する。version、precision、operator、boundary、Up定義、対象Ra・格子を採用仕様に記録する。

## 13. Can tau_phi be fixed now?

**できない。tau_phi=null / UNRESOLVED。fixed_threshold_supported=false。** 正当化できる数値、安全係数、数値不確かさを今回は作らない。

Decision tree:

- Case A: 該当しない。直接適用できる数値の理論・一次資料がない。
- Case B: 該当しない。operator verificationだけではN_pやpressure solveのdrift、物理budgetを決められない。
- **Case C: 主判定。solver toleranceから保存不均衡への変換を、reference・BC・出力を含め定量化する追加研究が必要。**
- Case D: local guardや低速度のabsolute budgetを正式Hardにするなら、単一fixed tauより別形式が適切となる可能性がある。現時点でCase Cに代えて確定採用する判断はしない。

direct_residual_to_epsilon_phi_mapping_available=falseは「報告残差または設定toleranceだけから使える無条件数値変換がない」という意味。条件付き理論関係そのものは導出済みであり、JSONでは別fieldに記録する。

## 14. Additional verification required

1. **独立error budgetの事前登録:** 現benchmarkの値を見る前に、mean/local保存欠陥の許容量、目的量への影響評価法、全Ra・格子への適用条件を決める。小さい残差だけからNuや速度誤差を保証しない。
2. **実operatorのend-to-end検証:** 既知の均一flux、telescoping field、既知のdivergence、single-face欠陥をOpenFOAM形式へ書き、現parser/owner/neighbour/patch order/empty処理を検証。物理壁非zero fluxの検出も含む。今回の合成検証をこの完了証拠にはしない。
3. **pressure matrixの量的対応:** 独立manufactured状態でA₀/b₀とA_s/b_s、N_p、relTol/停止理由、unrelaxed p*、r_true/r_rec、matrix flux、q、Bを同時評価。reference行を含め上界を検証。保存relaxed p_rghからの単純な再構成を避ける。
4. **誤差伝播とfloor:** 対象40²/80²/160²のscaleを用いた独立test suiteで、精度、加算順、write precision、ASCII/Binary対応、restart、必要なら並列reductionを検証。floorの上包絡とその不確かさを求めるが、物理budgetをfloorに合わせて緩めない。
5. **meanとlocalの記録・仕様:** max位置、volume-weighted percentile、signed/global、absolute local qとViを設計し、Hard/Diagnosticを決める。分位点だけで孤立欠陥を見落とさない。
6. **数値選択の再現性:** threshold、安全係数、条件とversionを現在結果から独立に登録し、その後のみ既存結果を `post-hoc consistency check only` として照合する。必要な後処理再実行と正式判定は別の採用作業で行う。

今回およびCandidate Bのmetric採用だけのために既存CFDを再計算する必要はない。追加のpressure検証はoffline assembly/独立検証問題で計画可能だが、実solver instrumentationや新しい検証solveが必要になる場合は別作業として扱う。**このレビューではそれらを実行していない。** 未確定閾値を確定する研究が不要という意味でsolver_rerun_required=falseとしているのではない。

## 15. Provisional Candidate B specification

**PROVISIONAL SPECIFICATION — 未採用・未実装。**

- Ra>0のRoute B solver continuity Hard候補: `epsilon_phi <= tau_phi`。tau_phiはUNRESOLVEDなので実際の合否判定を行えない。
- 定義: 保存されたpressure-corrected volume flux、現uniform FV incidence、volume-mean absolute divergence、Up=max cell|U|、L/Up規格化。solver residualをepsilon_phiへ代入しない。
- Route B reconstructed velocity: epsilon_vをDiagnosticとして報告し、新Candidate BではHard thresholdを設けない案。
- Legacy: epsilon_m_reconstructed_legacyをDiagnosticとして保存する案。既存epsilon_m keyの意味と旧仕様判定を静かに置換しない。
- mean以外のmax/percentile/globalは将来保存候補。local Hardの数値と採用は別途決定し、今回は実装しない。
- Ra=0: epsilon_phiはundefined/NOT_APPLICABLE、Gate Cの絶対速度・伝導基準へ分岐。任意Up floorなし。
- 既存Gate Gの壁面熱収支0.2%、断面保存0.5%、温度・速度対称性各0.2%は変更しない。他Gateの役割も維持する。

正式採用には独立のtau_phi根拠、必要なlocal guardの決定、仕様version更新、postprocessingとstatus schemaの更新、保存fieldを用いた後処理・判定記録が必要。現時点ではREADY_FOR_ADOPTIONではない。

## 16. Impact on existing results

CURRENT_FORMAL_RA1E3_GATE_G=FAIL。NEW_SPEC_RA1E3_GATE_G=NOT_EVALUATED。criteria_modified=false、solver_executed=false、spec_change_executed=false。benchmark結果から閾値を逆算せず、新Candidate BでのPASS/FAILを付与していない。

今回のrepository書き込みは本Markdownと同行JSONの新規作成だけ。docs、Scripts、reference/de_vahl_davis_table_v.csv、既存CSV/metrics/status/manifest、solver case/field/controlDictは変更しない。合成検証の一時データは/tmpに置き、結果をレビューJSONへ収録した。

開始時git status --shortは `?? cases/routeA/Ra0_medium/` と `?? cases/routeA/Ra1e4_coarse/` の2つ。これらは既存のuntracked directoryで、今回の変更ではない。触れておらず、commitや修正もしない。完了時はこれらと新規review 2ファイルのみであることを確認する。別の既存差分が検出されたら報告する。

## 17. Required user decision

次に判断する内容は、Case Cの定量検証と独立error budgetの作成を進めるか、そしてCandidate BのmeanをHardとする際にlocal guardまでHardへ含めるかである。今回の依頼内では正式採用や現行仕様変更を行わない。数値tauの採用は根拠を揃えた後に判断する。

```text
CURRENT_FORMAL_RA1E3_GATE_G = FAIL
GATE_G_CRITERIA_MODIFIED = NO
RECOMMENDED_THRESHOLD_SCHEME = SCHEME_3_WITH_CONDITIONAL_SCHEME_2_AND_SCHEME_4_VERIFICATION
TAU_PHI = UNRESOLVED
TAU_PHI_STATUS = UNRESOLVED
DIRECT_SOLVER_TOLERANCE_MAPPING = NO
CANDIDATE_B_STATUS = PROVISIONAL
NEW_SPEC_RA1E3_GATE_G = NOT_EVALUATED
SOLVER_RERUN_REQUIRED = NO
SPEC_CHANGE_EXECUTED = NO
USER_DECISION_REQUIRED = YES
```
