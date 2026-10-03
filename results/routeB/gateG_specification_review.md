# Route B Gate G Conservation Specification Review

## 1. Review purpose

レビュー日: 2026-10-04（Asia/Tokyo）。対象は Foundation v6 `buoyantBoussinesqSimpleFoam` による Route B の保存則判定である。支配方程式、solverの離散方程式、後処理演算子、Hard閾値の対応を検討する。既存結果を通すための閾値調整は行わない。

**結論案: Candidate Bを推奨する。ただしfluxのHard閾値は未確定であり、採用・実装・既存結果の再判定にはユーザー判断が必要である。** 現行Formal Ra=1e3 Gate GはFAILのまま。solver実行、既存コード・仕様・CSV・status・manifest・fieldの変更は行わない。

根拠はローカルv6ソース、現行仕様、既存後処理式である。新しい文献上の標準閾値が確認されたとする主張はしない。現在値は演算子の差を示す例として使い、推奨の論理や閾値を導く根拠には使わない。

## 2. Current criterion

[acceptance_criteria.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/acceptance_criteria.md:298) §9.2 は

$$
\epsilon_m=\frac{L\langle|\nabla\cdot(\rho\boldsymbol u)|\rangle_V}{\rho_0 U_p}\le10^{-6},\qquad
\epsilon_v=\frac{L\langle|\nabla\cdot\boldsymbol u|\rangle_V}{U_p}\le2\times10^{-3},
\quad U_p=\max|\boldsymbol u|
$$

を要求する。離散divergence、境界face、体積重みをroute別に固定し、一定rho0のRoute Bでは両閾値を満たす、と規定している。現行後処理は同一の再構成U演算子に対して `epsilon_m=epsilon_v` とするため、同時要求は厳密に

$$\epsilon_v\le\min(10^{-6},2\times10^{-3})=10^{-6}$$

となる。第二の閾値はRoute Bでは論理上冗長である。これは形式的な矛盾ではないが、再構成速度場に対する厳しい品質要件になっており、独立した二種類のsolver保存性の検証ではない。

Gate Gの他の現行Hard条件は、壁面熱不釣合い≤0.2%、全鉛直face-planeのNuの中央断面からの最大偏差≤0.5%、温度・速度の中心対称L2相対誤差それぞれ≤0.2%である。本レビューはこれらを変更する案ではない。`epsilon_phi` は現在、solver-flux diagnosticであって `epsilon_m` の代替Hard量ではない。

Gate Bは対象方程式・ソースの対応、Gate Dは反復収束・健全性、Gate Gは保存則・対称性、Gate Fは格子誤差を扱う。小さいcontinuity誤差だけでGate B/D/E/Fを代替できず、定常収束だけで格子精度を保証できない。

21000 accepted fineの現行値は以下であり、判定は保持する。

| 指標 | 現在値 | 現行判定上の扱い |
|---|---:|---|
| epsilon_phi | 2.8283979308e-11 | 独立Diagnostic |
| epsilon_v | 2.1995159935e-4 | 2e-3以下 |
| epsilon_m | 2.1995159935e-4 | 1e-6超過、Formal Gate G FAIL |

## 3. Continuum equations

[benchmark_spec.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/benchmark_spec.md:92) §3.3 と [routeB_design.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeB_design.md:56) §3 は古典Boussinesqの非圧縮条件

$$\nabla\cdot\boldsymbol u=0$$

を対象にする。連続式で使う密度は一定reference densityであり、浮力用の温度依存係数 `rhok=1-beta*(T-TRef)` を連続式の密度に代入しない。

$$\nabla\cdot(\rho_0\boldsymbol u)=\rho_0\nabla\cdot\boldsymbol u=0$$

なので、mass conservationとvolume conservationはこの連続体モデルでは同値である。**同じ離散演算子に定数を掛ければこの同値性は離散的にも保たれる。しかし、補正済みface流束と再補間したcell速度流束に異なる演算子を適用した値まで同じになることは意味しない。**

Route Aは必要最小限の比較に留める。既存の [routeB_design.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeB_design.md:215) §16 によれば、温度依存rhoとmass fluxを使う。一般には

$$\nabla\cdot(\rho\boldsymbol u)=\rho\nabla\cdot\boldsymbol u+\boldsymbol u\cdot\nabla\rho$$

であり、mass/volumeの指標は同値ではない。ただし、現行mass閾値が歴史的に「Route Aのために設定された」とまでは今回の資料から立証できない。確認できる問題は、共通形式をRoute Bの同じ再構成演算子に適用すると要件が重複することである。Route Aの閾値・仕様変更は提案しない。

## 4. OpenFOAM discrete continuity

監査した実ソースとline numberを示す。ソース全文の転載は行わない。

| 根拠 | 確認した内容 |
|---|---|
| [main solver:74](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/buoyantBoussinesqSimpleFoam.C:74)、80–82 | SIMPLEの各反復でUEqn→TEqn→pEqn |
| [createFields.H:32](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/createFields.H:32)、45、55–64 | Uはcell field、createPhiを使用、rhokは浮力係数 |
| [createPhi.H:36](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/incompressible/createPhi.H:36)、43–46 | phiはREAD_IF_PRESENT/AUTO_WRITE、未保存ならfvc::flux(U)で生成 |
| [fvcFlux.C:31](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcFlux.C:31)、36–40 | face補間のdotInterpolate(Sf,U) |
| [pEqn.H:2](/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam/pEqn.H:2)、8–23、29–46 | 予測flux、浮力flux、境界整合、圧力Poisson、flux/Uの別個の補正 |
| [continuityErrs.H:33](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/incompressible/continuityErrs.H:33)、35–40 | div(phi)の体積重み付き絶対平均・符号付き平均をdeltaT倍 |
| [fvcDiv.C:56](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcDiv.C:56) | surface fieldのdivergenceはsurfaceIntegrate |
| [fvcReconstruct.C:87](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/finiteVolume/fvc/fvcReconstruct.C:87) | face normal情報から幾何テンソルによるcell vectorを再構成 |
| [constrainPressure.C:61](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/constrainPressure/constrainPressure.C:61)、66–73、104 | fixedFluxPressure勾配を所望の壁速度fluxに整合、incompressible overloadはgeometricOneField |
| [adjustPhi.C:87](/home/mirai/OpenFOAM/OpenFOAM-6/src/finiteVolume/cfdTools/general/adjustPhi/adjustPhi.C:87)、94–105、135 | 境界fluxの全体整合。汎用変数名massIn等はphiの次元をmass fluxへ変えない |

### phiの次元と圧力補正

`fvc::flux(U)` はface面積ベクトルと補間速度の内積なので

$$[\phi]=[\boldsymbol S_f][\boldsymbol u]=\mathrm{m^2}\,\mathrm{m/s}=\mathrm{m^3/s},\qquad
\text{OpenFOAM dimensions}=[0\ 3\ {-1}\ 0\ 0\ 0\ 0].$$

これはmass fluxではない。一定rho0を掛けた `rho0*phi` が対応するmass fluxである。rhokを掛けたfluxではない。

離散face divergenceを

$$D_h\phi_i=\frac{1}{V_i}\sum_{f\in\partial i}s_{if}\phi_f$$

とし、予測流束をPhi_H、圧力行列からの流束をF_pと書けば、pEqn.H:29、39は

$$L_h p_{rgh}=D_h\Phi_H,\qquad \Phi=\Phi_H-F_p$$

に対応する。圧力行列とそのfluxを整合させることで、各control volumeの `sum_f phi_f` は圧力解の残差等の範囲で零になる。圧力reference、境界条件、非直交補正の整合も必要であり、有限toleranceで厳密な零になるとは主張しない。

`continuityErrs.H` のsum localは `deltaT*<|D_h phi|>_V`、globalは `deltaT*<D_h phi>_V`。これはepsilon_phiと同じdivergence入力だが、規格化は異なる。globalの小ささだけではcellごとの誤差相殺を除外できない。今回のsteady反復のdeltaTを物理的な過渡検証と解釈しない。

### cell Uからphiを復元できるか

pEqn.H:39でface phiを更新した後、:42でpressureを緩和し、:46で

$$\boldsymbol U_h=HbyA+rAU\,R_h\!\left[(phig-F_p)/rAU_f\right]$$

としてcell Uを補正する。再構成R_hとcell-to-face補間I_hは逆演算として実装されていない。一般に `I_h R_h=identity` ではなく、積の補間も交換可能ではない。したがって `I_h(U_h) dot Sf` が保存済みPhiを完全再現する保証はない。これはcollocated配置と圧力・face flux連成の離散構造による。ここでは実装で確認した演算を根拠とし、特定のnamed momentum-interpolation方式の追加仮定を置かない。

## 5. Current post-processing operators

[analyze_case.py:89](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeB/analyze_case.py:89)–116、258–261、357が対象である。Nセル、等体積V、`Up=max_cell |U|`、L=キャビティ辺長とする。

| 出力量 | 入力・face値・境界 | 演算・重み・規格化 | 意味 |
|---|---|---|---|
| mean_abs_div_phi | 保存済みphi、owner/neighbour、physical patch phi。内部faceはownerに加算、neighbourに減算。emptyは零 | `N^-1 sum_i |sum_f s_if phi_f / V|`、1/s | solverと同じface流束の局所FV保存性 |
| epsilon_phi | 上記とcell UのUp | `L*mean_abs_div_phi/Up`、無次元 | corrected-face流束のadvective-scale continuity error |
| mean_abs_div_U | 保存済みcell U。内部faceで隣接cell平均、noSlip壁でnormal速度零、面外項なし | Cartesian face差分の絶対値平均、1/s | 再構成速度表現の非零divergence |
| epsilon_v | 上記と同じUp | `L*mean_abs_div_U/Up`、無次元 | reconstructed velocity-field divergence diagnostic |
| epsilon_m | epsilon_vへのalias。rho fieldや保存mass fluxを別に読まない | 同じ数値 | constant-rho reconstructed mass-divergence diagnostic |

正確には

$$d_i^\phi=V^{-1}\sum_f s_{if}\phi_f,\quad
\overline{|d^\phi|}=N^{-1}\sum_i|d_i^\phi|,\quad
\epsilon_\phi=(L/U_p)\overline{|d^\phi|}.$$

再構成速度側は

$$u_{i+1/2,j}^{rec}=\tfrac12(u_{i,j}+u_{i+1,j}),\quad
w_{i,j+1/2}^{rec}=\tfrac12(w_{i,j}+w_{i,j+1}),$$

$$d_{ij}^{rec}=\frac{u_{i+1/2,j}^{rec}-u_{i-1/2,j}^{rec}}{h_x}
+\frac{w_{i,j+1/2}^{rec}-w_{i,j-1/2}^{rec}}{h_y},\quad
\epsilon_v=\frac{L}{U_p}N^{-1}\sum_{ij}|d_{ij}^{rec}|.$$

壁faceは指定noSlip速度零を使う。端のcellもface差分に含む。対してphi側は実保存境界fluxを読む。現在のuniform直交・1-depth-cell格子では算術平均と体積平均は等価である。非一様格子への一般化には実V_iによる重みと境界startFace情報を使う改修・検証が必要で、現コードを任意mesh対応とは扱わない。phi側はdeclared patch順を仮定しており、その前提は現caseのmesh監査対象である。

$$\epsilon_m^{rec}=\frac{L\langle|\rho_0 d^{rec}|\rangle_V}{\rho_0 U_p}=\epsilon_v$$

は数学的に正しい。しかし正確な名称は **constant-density reconstructed mass-divergence diagnostic** であり、「solverのdiscrete mass conservation error」と呼ぶと別のface演算子を混同する。定数rho0のsolver mass fluxに同じFV演算子を適用した量はepsilon_phiと同値である。

## 6. Why epsilon_phi != epsilon_v

例示値の比は約7.78e6。両指標は同じLと同じUpで割っているため、この比は未規格化divergenceの比そのものでもある。

| 原因候補 | 本監査の評価・限界 |
|---|---|
| A. solver自身のcontinuity違反 | その直接量epsilon_phiは約2.83e-11。epsilon_vだけからsolver保存則違反を結論できない。ただし平均量だけで全cellの最大誤差を保証するわけではない |
| B. corrected fluxと再構成U fluxの相違 | 主要な構造的説明。pEqn.Hと後処理コードが明確に別の流束を作っている |
| C. 補間誤差 | I_hによる再表現は連続体速度の近似を含む。smooth interiorではcentral補間は整合的だが、このcaseでの誤差次数・寄与率は格子解析なしに断定しない |
| D. collocated FV配置 | Uとpressureがcell、continuity fluxがfaceで別個に補正される構造。R_h後の再補間が保存fluxの逆写像ではないことが根拠 |
| E. 境界処理 | 一方は保存patch flux、他方はnoSlip零を直接代入。constrainPressureは指定壁fluxと整合させるため、壁からの物理漏れを直ちに推定する根拠はない。近壁cellの再構成誤差は残り得る。face別の寄与分解は今回未実施 |
| F. 規格化の差 | 除外できる。二つともL/Up、同じuniform-volume平均、同じ単位 |
| G. 有限反復、丸め、保存precision、圧力緩和 | 付加的影響はあり得る。個別寄与を定量分離したとは主張しない。極小の保存flux残差と有限の再構成残差が共存すること自体は離散構造と整合する |

重要な恒等式は

$$D_h\Phi^{rec}=D_h\Phi+D_h(\Phi^{rec}-\Phi).$$

solverが第一項を小さくしても、第二項を同じalgebraic toleranceで消す方程式は解いていない。これはsolver離散continuityと、cell velocityの再構成整合性を分ける結果非依存の根拠である。差を誤差要因別に何%ずつ帰属したか、あるいはsolver実装に一切問題がないかまで立証する式ではない。

## 7. Candidate criteria

**Candidate A: 現行維持。** Hardはepsilon_m≤1e-6とepsilon_v≤2e-3。Route Bでは同じ再構成指標に実効1e-6を課す。変更不要で歴史的整合性を守るが、solver-flux conservationを直接Hard評価する構成ではない。連続体速度の再構成品質を非常に厳しく要求する仕様と明記するなら一貫している。その厳しさの独立した精度予算は今回未確認。

**Candidate B: solver-flux conservationをHard化。** Hardはepsilon_phi≤tau_phi、Diagnosticはepsilon_vとlegacy epsilon_m。一定rho0によりvolume/massの保存flux判定を一本化する。熱保存・対称性等の他の既存Hard条件は維持する。tau_phiは未決定。診断量に異常が出た場合の調査・格子依存報告も残し、flux合格だけで速度場全体の品質を主張しない。

**Candidate C: 両方をHard、役割分離。** Hard 1はepsilon_phi≤tau_phi（solver continuity）、Hard 2はepsilon_v≤tau_rec（reconstructed-field quality）。epsilon_mは後者の冗長aliasとし、二重の保存則と呼ばない。現在の2e-3をtau_recの候補に挙げる根拠は「既存事前仕様」であり、現在値を通すためではない。ただしoperatorに対応した誤差予算や製造解・格子整合性の根拠は不足しているため、2e-3を確定提案とはしない。

## 8. Candidate comparison

| 比較項目 | A | B（推奨） | C |
|---|---|---|---|
| 物理的意味 | 同一再構成Uのmass/volume条件 | 一定rho0下のsolver mass/volume flux保存 | solver保存と再構成速度品質を別目的で要求 |
| 離散的意味 | D_h I_h Uを実効1e-6で制約 | D_h Phiを直接制約 | D_h PhiとD_h I_h Uを別々に制約 |
| 長所 | 現行・履歴の連続性、厳しいfield制約 | 解いている離散連続式との対応が直接的、冗長性を解消 | solverとfield両面を明示的に管理 |
| 短所 | 直接保存指標をDiagnosticに留め、再構成制約の意味が不明瞭 | 速度場の品質はDiagnosticと他Gateで確認する必要 | field Hard閾値の根拠・operator検証が追加で必要 |
| 閾値の準備状態 | 数値は登録済み、再構成品質としての独立根拠は未確認 | tau_phi未確定 | tau_phi、tau_recとも研究レビューが必要 |
| Route Bへの適合性 | 再構成場の厳格品質要件を目的にするなら可 | solver離散continuityのVerificationに最も直接的 | field-qualityも独立Hard要件と決めた場合に適合 |

Aが今回FAILとなること、B/Cが将来どう判定するかを候補選択の根拠にしない。未承認・閾値未確定の候補にPASS/FAILを付与しない。

## 9. Recommended criterion

**Candidate Bを研究仕様案として推奨する。** Q1への答えはepsilon_phiである。pressure equationが直接小さくしているD_h Phiを測るため、solverの離散continuityのVerificationに最も直接的である。

Q2への答えはepsilon_vを残すことである。再構成された速度場のsolenoidal品質、補間・境界・後処理の整合性、格子依存を診断できる。保存flux残差だけでは見落とすfield問題を調査する入力となる。ただしepsilon_v単独は全速度精度、pressure checkerboarding、solver不具合の種類を特定する検査ではない。

Q3への答えは名称の分離である。既存epsilon_mは `epsilon_m_reconstructed_legacy` として保持し、必要なら `epsilon_mass_flux` をepsilon_phiに数値的に等しい別名として追加する。既存keyを無告知で新しい意味へ置換しない。epsilon_vも `epsilon_U_reconstructed` 等の明示的aliasを追加できる。phiの意味・rho0・離散演算子・規格化をschemaに保存する。

推奨するHard保存指標はepsilon_phi、推奨Diagnosticはepsilon_v、legacy epsilon_m、cell/faceの流束不一致に関する将来の調査指標。熱保存・対称性等の既存Hardは維持する。Route Aとの整合性は「そのrouteが保存する正しい離散流束を明記する」という原則で確保し、Bのvolume fluxやrho0同値性をAへ転用しない。Aは今回変更しない。

採用時はspecification versionとresults schema versionを上げ、旧基準と新基準の結果を併記する。既存Formal Gate G FAILを消さない。Gate Fの独立したFAIL・needs_320もこの変更では解消しない。旧結果を新基準でも再判定する範囲、採用日、閾値の決定根拠をユーザーが明示する必要がある。

## 10. Threshold evidence / unresolved questions

**THRESHOLDS_FULLY_JUSTIFIED = NO。tau_phiを数値で提案しない。** 保存量の選択にはソースと数学の根拠があるが、どの大きさをHard合格にするかは別問題である。

- 線形solver tolerance、final normalized residual、epsilon_phiは同じ量ではない。圧力行列の残差をcell-volumeとL/Upで規格化したdivergenceへ対応付ける必要がある。行列の残差規格化・pressure reference・boundary flux・nonorthogonal項の扱いを含むため、例えばsolver tolerance=1e-10からtau_phi=1e-10と直結できない。
- dimensional scalingによりL/Upはadvective time尺度である。Upが小さい/零の極限を事前規定し、Ra=0では既存Gate Cの絶対基準と連携する。今回の非零流れに合わせてfloorを後付けしない。
- machine precisionだけでは、格子数、pressure conditioning、flux cancellation、出力precision、並列和の影響を含む床値を保証できない。本レビューはmachine epsilonの定数を合格閾値に流用しない。
- 将来の追加調査では、格子・版ごとにmatrix残差からの許容保存誤差を見積もり、既知のdivergence-free製造解/解析場でoperator・壁・empty・owner/neighbour・体積重みを検証する。これらは提案であり、今回はsolverや試験を実行していない。
- 現行のmass上限1e-6は既存の厳しい保存性方針の証拠にはなるが、異なるoperatorへの数値移植を自動的に正当化しない。tau_phiへ同値を採用する案も、物理的保存誤差予算と演算子の対応をレビューしてから決める。
- 再構成fieldをHardとするCなら、将来の用途で許容するdivergenceを定義し、同じoperatorの格子整合性・境界精度に対してtau_recを検証する。単にfine値が小さい、二次補間らしい、という理由では根拠にならない。
- literature/standard practiceに基づく普遍的なtau_phiは今回確認していない。追加調査で引用・規格化を検証し、別定義の閾値を無条件に移植しない。

## 11. Impact on existing results

21000のaccepted solver fieldは、支配方程式・mesh・BC・solver settingsを変えないB/Cの判定仕様変更だけなら再利用できる。**solver再実行は不要。post-processing/判定成果物の再生成は必要。** 既存の監査済みmetricsからepsilon_phi・epsilon_vを読み、Gateを新versionで再判定するだけなら、全fieldを再数値後処理することまで必須ではない。名称・schema/version・provenanceを更新するpipelineは必要である。新しいfield metricや違うoperatorを採用する場合だけ、保存fieldから該当後処理を追加する。

| 将来の変更対象 | 必要/不要 | 理由 |
|---|---|---|
| docs/acceptance_criteria.md | 必要 | B限定のHard/Diagnostic、tau_phi、versionと旧基準履歴を明文化 |
| docs/benchmark_spec.md | 必要 | 保存則指標、route別演算子、成果物要件を新仕様と整合 |
| docs/routeB_design.md | 必要 | 既存source証拠を維持し、判定との対応・alias定義を追記 |
| docs/routeB_implementation.md | 必要 | 新schema/判定記録を追記。minimalの歴史的記録は保持 |
| Scripts/routeB/analyze_case.py | 必要（metadata/alias） | operator変更は不要。明示名・method/schema versionとlegacy意味を出力。既存metrics再利用時にこのscriptを再実行することは必須ではない |
| Scripts/routeB/finalize_full_matrix.py | 必要 | 承認済み新Hard選択、旧/新判定の分離、Diagnostic報告 |
| results schema・summary/conservation/status/manifest | 必要 | criteria version、operator version、旧/新判定、field hashと判定更新履歴を保存 |
| solver、mesh、BC、properties、scheme、relaxation、tolerance、field | 不要 | 保存性の評価仕様を変えるだけで離散解は変わらない |
| Route A仕様・コード・結果 | 今回不要 | rho/fluxの意味が異なる。B限定改訂としAを自動変更しない |

レビューだけでは旧Gate GをPASSにしない。新tau_phiが未確定なので、新仕様でのGate Gの値は未判定である。Ra=1e3 Gate F FAIL/needs_320とfull 12点未完は別に残る。

## 12. Required user decision

1. Bのsolver-flux conservationをHard、再構成UをDiagnosticとする役割分離を採用するか。field-qualityもHardにしたい場合はCを選び、その独立精度予算を定める。
2. tau_phi、必要ならtau_recを、上記の結果非依存の調査・保存誤差予算から事前定義する。今回の2.83e-11/2.20e-4を通す数値から逆算しない。
3. 新specification/schema version、旧/新判定の併記方法、既存accepted結果を再判定する範囲を承認する。

今回の変更はこのレビューMDとJSONの作成のみ。現行仕様・式・結果・status・manifestは保持し、solverは実行していない。

```text
CURRENT_FORMAL_RA1E3_GATE_G = FAIL
GATE_G_CRITERIA_MODIFIED = NO
RECOMMENDED_CANDIDATE = B
RECOMMENDED_HARD_METRICS = epsilon_phi (tau_phi未確定; 他の既存Gate G Hard条件を維持)
RECOMMENDED_DIAGNOSTICS = epsilon_v, epsilon_m_reconstructed_legacy
THRESHOLDS_FULLY_JUSTIFIED = NO
SOLVER_RERUN_IF_ADOPTED = NO
POSTPROCESSING_RERUN_IF_ADOPTED = YES (Gate/schema再生成; field数値抽出の全面再実行は条件付き)
SPEC_VERSION_CHANGE_RECOMMENDED = YES
USER_DECISION_REQUIRED = YES
```
