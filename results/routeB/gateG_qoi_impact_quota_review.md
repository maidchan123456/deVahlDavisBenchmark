# Route B Gate G QoI Impact Quota Review

## 1. Purpose

研究レビュー日: 2026-10-04。Budget Cを次段階の設計基準として、continuity conservation defectに関連するQoI impact quota `b_Q`の**形式・根拠・将来検証手順**を事前設計する。推奨は**HYBRID（BのQoI別形式＋Cのsame-QoI verification hierarchy）**。architectureはREADY、数値quota・hierarchy factor・tau_meanはUNRESOLVEDである。

solver、sensitivity experiment、microcase、320²を実行していない。正式benchmarkのfield/log/実測Gate E/F/conservation値を読まず、既存結果の再判定もしていない。現在の正式Ra1e3 Gate G=FAILは与えられた研究状態の転記である。仕様、production code、既存verification実装を変更しない。

使用したlocal contextは、前回Budget reviewの推奨・未解決点、epsilon threshold reviewの結論、Case C reportの独立試験設計・限界、acceptance_criteriaのGate D/E/F/G、benchmark_specの研究目的・QoI・Route B定義に限定した。de Vahl Davis原論文PDFやrepository全体を再読していない。

## 2. Current Budget C architecture

| Role | 次段階の設計基準 | 今回の状態 |
|---|---|---|
| Hard候補 | pressure-corrected face volume fluxのepsilon_phi_mean | tau_mean未決定、正式採用なし |
| Investigation trigger候補 | local max/concentration、boundary leakage、cell-sum/boundary closure | cutoff未決定。調査中は自動clearanceしない |
| Diagnostics | max、P95/P99、global signed、boundary net/absolute total、patch flux、local q_i/V_i/location、epsilon_v、legacy epsilon_m | 保存・報告。単独Hard判定にしない |

Budget C architecture=READYは役割と設計手順の準備完了を意味する。Candidate B=PROVISIONAL、NEW_SPEC_RA1E3_GATE_G=NOT_EVALUATED、numerical thresholds=UNRESOLVEDを維持する。既存Gate Gの熱収支・断面・対称性条件も、この研究レビューによって変更されない。

## 3. Why epsilon_phi cannot directly equal QoI error

cell-face incidenceをB_h、corrected volume fluxをphiとすると、

\[
q_i=(B_h\phi)_i,\quad d_i=q_i/V_i,\quad
\epsilon_{\phi,mean}=\frac{L}{U_pV_\Omega}\sum_i|q_i|,
\quad U_p=\max_{cell}|\boldsymbol U|.
\]

q_iの単位はm³/s、d_iはs⁻¹。epsilonは全領域L1の無次元残差量であり、Nuの相対差や極値位置の絶対差ではない。同じepsilonでも残差の符号・位置・support、mesh、state、coupling、QoI抽出が異なればDelta Qが変わる。

以下は本レビューの局所線形化による説明であり、実測感度や保証ではない。完全coupled離散系R(y)=0にcontinuity blockの摂動gを入れたとき、同じ解branchでJacobian Jが可逆、QoIが微分可能なら、J Delta y≈P_c g、Delta Q≈lambda_Q^T P_c g、J^T lambda_Q=grad Q。従って、適切な残差単位で、

\[
|\Delta Q|\lesssim\|\lambda_{Q,c}\|_\infty\|g\|_1.
\]

epsilonからQoI errorを得るには未知のoutput-specific sensitivityが必要である。epsilonだけではその係数・非線形剰余・他方程式残差を決められない。極値位置のbranch switch/flat peakでは上の微分可能性自体が失われうる。[Fidkowski–Darmofalの査読reviewの公開abstract](https://websites.umich.edu/~kfid/MYPUBS/Fidkowski_Darmofal_2011.pdf)は、output sensitivityとresidual source perturbationの関係を支持するが、closed cavityのquota数値は与えない。

## 4. QoI classification

| Class | QoI | Impactの形式 | quotaの扱い |
|---|---|---|---|
| relative-value / Nu | Nu_bar_cavity、Nu_bar_0、Nu_bar_half | abs(Q_test−Q_base)/scale_Q | Nu群の形式は共通化可。数値を共通化する根拠は別途必要 |
| relative-value / velocity magnitude | Umax、Wmax | abs(Q_test−Q_base)/scale_Q | velocity群。既存の符号・無次元化・centerline定義を固定 |
| absolute-position | Umax_Z、Wmax_X | abs(s_test−s_base) | s=Z/L、X/Lという無次元位置の絶対差 |

Nu_bar_cavityはcavity積分、Nu_bar_0は壁面、Nu_bar_halfは中央断面の対流＋伝導であり、同一QoIの別名ではない。位置をそのbaseline位置で割るrelative quotaは、原点近傍で特異になり、研究上必要な空間誤差とも一致しない。

全7QoIをsensitivity観測・quota研究のrequired setとすることを推奨する。ただしNu_bar_0/halfを正式Gate Eの新Hard条件へ昇格させる意味ではない。baselineが零に近いvalue QoIでは独立characteristic scaleへ事前に分岐する（§19）。

## 5. Verification error hierarchy

| Gate | 対象 | 今回のcontinuity impactとの関係 |
|---|---|---|
| D | iterative / steady convergence | coupled状態と各方程式の収束が比較の前提。収束monitorが小さくても定常的なconservation defectによるbiasは残りうる |
| E | paper benchmark agreement | comparison allowanceはreference uncertainty等も含む研究要求。現在のagreementや1%をcontinuity quotaへ転記しない |
| F | grid convergence / discretization uncertainty | same-QoIの独立U_Q,discとの階層比較。conservationが良くても離散化精度は悪いうる |
| G | conservation / symmetry | discrete conservation品質を直接見る。QoI impactとの対応を独立に検証する |

Gate Dの残差・RwinとGate FのGCIは別の誤差を測る。Gate Dで十分steadyな非zero-source状態を得ても、それは元のzero-source方程式の正確な解を意味しない。Gate Gに適合しても粗いmeshのNu/velocity errorは消えない。

自然なpressure solveのcontinuity残差によるimpactはiterative errorの一部と重なりうる。`U_iter + E_cont`を常に独立成分として加算するbudgetは二重計上を招く。一方、controlled source armは十分収束した**摂動方程式**とzero-source baselineとの差を測る。両者の解釈を分け、他方程式の残留誤差は比較差のmeasurement uncertaintyへ含める。

## 6. Literature review

一次資料を優先し、下記の公開箇所を確認した。access dateは2026-10-04。外部資料の係数を今回のb_Q/epsilonへ直接採用していない。

| Source / 確認範囲 | この設計への支持 | 直接適用の限界 |
|---|---|---|
| [ASME JFE official editorial-policy bundle](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf): Celik, Ghia, Roache, Freitas名義のProcedure、Preliminaries、Appendix A（PDF p.14） | rationalに推定したiteration convergence errorをdiscretization errorより少なくとも1 order小さくするguidance。残差低下だけで十分な収束を保証しない | 推定solution errorについての推奨。continuity残差そのもの、全QoI、極値位置、人工sourceのimpactに対する普遍的数値quotaではない |
| [ASME 2017 discretization-error workshop introduction](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty/workshop-on-estimation-of-discretization-errors-based-on-grid-refinement-studies-2017/introduction) | steady-flow grid studyの前提としてiteration/round-off errorが小さいことを求める | その前提を今回の実験でも検証する必要がある。acceptable conservation budgetは指定しない |
| [NASA NPARC iterative convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html) | residualと目的outputの両方を監視し、outputごとに収束速度が違うことを扱う | 具体的なclosed-cavity b_Qを提供しない |
| [NASA NPARC spatial convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html) | output functionalのgrid convergence、Richardson/GCIの適用条件、零近傍relative estimateの問題 | GCIはepsilonに対する許容量ではない。有効な独立grid studyが先に必要 |
| [NASA tutorialとAIAA G-077-1998の関係](https://www.grc.nasa.gov/www/wind/valid/tutorial/tutorial.html) | tutorialは多くの内容がAIAA Guideに基づくと明記 | AIAA原標準全文の適合性監査はしていない。NASA経由の支持をAIAA本文の確認と呼ばない |
| [Fidkowski & Darmofal (2011), AIAA Journal 49(4), 673–694, DOI 10.2514/1.J050073](https://websites.umich.edu/~kfid/MYPUBS/Fidkowski_Darmofal_2011.pdf); [著者の書誌情報](https://websites.umich.edu/~kfid/journals_bib.html) | 査読reviewの公開abstractでoutput-specific residual sensitivity/adjoint-weighted error estimationを確認 | 本文取得はweb size limit/HTTP403で失敗。abstractと著者書誌のみ確認し、本文中のerror boundや適用定理を確認済みとはしない |
| OpenFOAM Foundation v6 [pEqn.H](https://cpp.openfoam.org/v6/heatTransfer_2buoyantBoussinesqSimpleFoam_2pEqn_8H_source.html)、[TEqn.H](https://cpp.openfoam.org/v6/heatTransfer_2buoyantBoussinesqSimpleFoam_2TEqn_8H_source.html) | corrected phiのpressure flux subtraction、pressure reference、phiを使うtemperature convectionというcouplingを確認 | solver実装の根拠。research acceptance quotaの根拠ではない |

ASME公開bundleは誌上版との著者数等の差があるため、確認した公開版の表記を使う。ASME V&V 20の全文レビュー、Roacheの書籍全文レビューもしていない。文献は階層・output-specific評価・scope限定へのqualitative supportであり、今回の係数cを自動的に0.1へ固定する根拠とはしない。

## 7. Quota Scheme A

全value QoIに `abs(Delta Q)/scale_Q <= b_rel`、位置に `abs(Delta s) <= b_pos`。Q_ref/scaleは独立実験内のsteady numerical baselineか独立characteristic scaleであり、formal paper値ではない。

長所は簡潔で登録・監査しやすいこと。短所は積分熱輸送・断面熱輸送・局所速度peakの物理的感度を同じrelative allowanceで扱う根拠が必要なこと。位置には別quotaが必要なので、本当の全QoI単一quotaでもない。非zero baselineのvalueには適するが、零近傍では分母が不安定になる。b_rel/b_posはともに未決定。簡潔さだけで採用しない。

## 8. Quota Scheme B

`b_Q`をQoI別に登録し、Nu群、velocity群、position群で形式を整理する。群内同一数値を採用する場合にも独立根拠を記録する。valueはrelative/characteristic scale、positionは無次元座標のabsolute unitsとする。

長所は各QoIの意味・reference scale・抽出精度に合わせられること。短所は自由度が増え、観測差に合わせたquota選びが容易になること。研究目的、必要reporting resolution、comparison allowanceの独立割当等がない限り数値は決めない。形式として採用し、数値の恣意性をCの階層レビューと事前登録で制限する。

## 9. Quota Scheme C

先に `continuity defect -> Delta QoI -> E_Q,cont` と変換し、**同じQoI・同じunits・同じscope**でiterative uncertainty、discretization uncertainty、independent comparison allowanceと比較する。位置QoIのU_discもabsolute position unitsで評価する。

候補の階層条件は、

\[
E_{Q,cont}^{+}\le b_Q,\qquad
E_{Q,cont}^{+}\le c_Q\,\widetilde U_{Q,disc}
\]

である。tilde Uはvalueではscale_Qで正規化し、positionではabsolute unitsとする。**c_Qは未決定**。この2条件を正式採用したわけではなく、独立capと階層条件を併用する将来案である。

ASMEのfactorは、同一量のrationalなiteration error estimateとvalidなdiscretization estimateという文脈に限られる。continuity残差normは前者でなく、人工source responseは通常のiteration estimateとも異なる。従ってb_Q=GCI/10、epsilon<GCI/10、c_Q=0.1の自動採用はいずれも不可。直接数値適用の根拠不足により、今回はqualitative hierarchyとして採用する。

長所はverificationの誤差階層と整合すること。短所はU_disc推定の妥当性、grid依存、共通baseline誤差、成分の重複に依存すること。U_discが大きいだけでquotaを緩めたり、偶然小さいgrid差からゼロquotaを要求したりしない。independent science/comparison capとmeasurement resolutionを別に管理する。

## 10. Quota Scheme D

研究結論を変えない最小差を科学的effect sizeとして指定する。物理的な閾値や意思決定が明確なら、離散化誤差の大きさに依存しないquotaを与えられる。

今回の目的は古典Boussinesq cavity solverのverificationであり、設計性能の二者択一等のscientific effect sizeは提示されていない。「結論が変わらない」だけでは数値agreementの品質を規定できず、biasを隠す危険もある。Nu/velocity/positionそれぞれについて結果非依存の意味を定義できる場合にだけ追加capの根拠となる。単独推奨せず、数値はUNRESOLVED。

## 11. Comparison

| Scheme | quota形式の適合 | 主な長所 | 主な問題 | 今回の判断 |
|---|---|---|---|---|
| A | value共通relative＋position absolute | 最小自由度 | QoI間の同一数値根拠、zero scale | 比較候補。単独推奨なし |
| B | QoI別/物理class別 | 物理的意味に整合 | 自由度と事後選択の危険 | 推奨の形式部分 |
| C | same-QoI uncertainty hierarchy | D/E/F/Gとの整合 | valid U_disc、重複、適用factor | 推奨の根拠・監査部分 |
| D | scientific effect size | 独立した研究上の意味 | 今回のeffect size未定義 | 根拠が提供された場合の追加cap |

どのschemeも現在のformal結果なしに構造は選べる。しかし、提示された研究要求と確認した公開guidanceだけでは全7QoIの数値allowanceは一意に定まらない。

## 12. Recommended quota architecture

**HYBRID = B + C**を1つの推奨案とする。各QoIのquotaを適切なunitsで事前登録し、同じQoIのverification error hierarchyとcomparison目的に照らしてレビューする。独立したscientific-significance要求が得られればDを追加根拠として使えるが、Dは現在の採用構成ではない。

登録項目は、QoI/抽出法/units/scale、independent rationale、b_Q、hierarchy factorを用いるならc_Q、valid U_discの推定法、comparison allowanceの割当、resolution envelope、対象state/grid/pattern、confirmation用holdoutである。単一のb_Q scalarではなく7要素のquota recordを持つ。群内同値は根拠がある場合のみ。

architecture READYはこのrecord構造と判断順序についての結論である。数値を選んだり、Formal Gate Gの新しいPASS条件を確定したりしたものではない。探索実験はresponse evidenceを作る段階、quotaの科学的許容性は別の研究判断、threshold confirmationはquota確定後の段階として分ける。

## 13. Numerical quota status

`QOI_IMPACT_QUOTA_VALUE = UNRESOLVED`、全QoIのb_Q=null、c_Q=null、b_rel/b_pos=null。tau_mean、max/boundary trigger cutoff、defect amplitude range、same-mean matching toleranceも未決定。

数値の不足根拠は、continuity成分へ割り当てる独立研究要求、QoI別の必要resolution/科学的差、validな独立same-QoI uncertainty study、測定可能性、scope別の感度である。Gate Eの1%、Gate FのGCI限度/観測値、現在のepsilon、accepted Ra1e3結果を数値quotaへコピー・逆算しない。ASMEの1 orderを0.1%/0.01%等へ転換しない。

将来数値提案には「formal結果を一切見なくても同じ値を選ぶ」という根拠、published guidanceの適用条件、研究目的との対応が必要。独立sensitivity実験もresponseを示すだけでは許容差の科学的根拠を自動生成しない。

## 14. Independent sensitivity experiment hypotheses

| Hypothesis | 検証する比較 | 支持されない場合の解釈 |
|---|---|---|
| H1 | epsilon_mean低下と各QoI impactの低下・単調性 | 単一threshold/power lawの根拠が不足 |
| H2 | actual epsilon_meanを揃えたlocation/pattern間のimpact | meanだけではoutput impactを特徴付けられない |
| H3 | same-meanの集中/分散、max、max/mean、max locationとimpact | mean-only予測にlocal情報が必要か評価。max cutoffは別研究 |
| H4 | Arm 1の自然residual patternとArm 2のcontrolled pattern | 相互代用・同一responseを仮定しない |

共通domainは**Ra_test=30000、Pr=0.71、20²/40²/80²、1 depth cell、serial/DP/ASCII16**。既存Case Cに合わせL=0.01m、depth=0.001m、hot/cold=301/300K、TRef=300.5K、gravity magnitude=9.81m/s²、nu=1e-6m²/s、alpha=nu/Pr、beta=Ra_test nu²/(Pr g L³)、laminar、4 impermeable walls、front/back emptyとする。位置はbenchmarkのX/Zラベルとphysical mesh軸の対応を登録する。

formal Ra=1e3/1e4/1e5/1e6は対象外。160²は独立grid studyが不足した場合の将来追加案のみ。320²は設計範囲外。初期U=0、T=300.5K等の共通初期状態、mesh/schemes/BC/relaxation/solver versionをrun manifestで固定する。開始時Up=0のepsilonはundefinedとして扱い、任意floorを置かない。

## 15. Experiment Arm 1 — pressure tolerance

目的は自然に発生するpressure残差patternで、epsilonとQoI responseの関係・他方程式との交絡を調べること。候補はp_rgh absolute tolerance=1e-6/1e-8/1e-10、relTol=0、各gridにつき3条件、全9条件。最もtightな条件を各gridのbaseline候補にする。

physics、mesh、BC、scheme、relaxation、初期状態、momentum/T solver設定を固定する。**各条件を十分steadyまで進める将来計画**であり、Case Cの最初の10 SIMPLE iterationsをQoI感度結果として流用しない。

将来実施前に、全equation residual、QoI Rwin、field change norm、temperature convergence、momentum residual、heat/section balanceのmonitor、window長、追加iterationによる安定確認、最大iteration/未収束停止条件を登録する。既存Gate Dを最低限のmonitor設計の参考にし、quota評価のresolutionが得られるかを追加確認する。新しい数値収束cutoffは今回は作らない。数値quota未定段階ではsteady evidenceとresolutionを報告し、quota PASSを出さない。

保存対象は全7QoIとtime/iteration history、epsilon_mean/max、P95/P99(raw/normalized)、global signed、B_net/B_abs、patch signed/absolute flux、closure、local signed q_i/V_i/location、max/mean、max cell/location、Up、pressure initial/final recursive residual・stopping reason、利用可能なreference-aware true residual/Np、U/T/p_rgh/phi field change、restart/serialization evidence、epsilon_v/legacy epsilon_m diagnostics。

pressure tolerance差はtrajectoryとcoupled convergence stateも変える。Arm 1のDelta Qはconservation-related differenceでありpure continuity effectとは断定しない。十分steadyでないrun、他方程式の差がresolution envelopeに収まらないrun、branchが異なるrunを閾値支持データへ含めない。

## 16. Experiment Arm 2 — controlled internal defects

目的はglobal netを変えずに残差の強さ・位置・集中を制御し、coupled U/T/p/QoI responseを測ること。将来、**別のverification-only solver**を作る案とし、production solver/formal case/現在のaudit solverは変更しない。

| Coupling候補 | 測れるもの | 評価 |
|---|---|---|
| 1. final phiのfrozen-field one-shot | incidence/operator/metricの反応 | U/T/pが応答せず、coupled QoI impactを測れない |
| 2. SIMPLE中のmaintained phi defect | 定義したflux改変への応答 | 投入timing次第でprojectionが消去、Uとの不整合、追加forcingの交絡。明示的整合が必要 |
| 3. modified continuity RHS | 指定continuity residual sourceに対する十分収束したcoupled応答 | **推奨**。sourceを各iterationで維持し、zero-source controlで実装を検証 |
| 4. manufactured source formulation | known solution/operator verification | 有用な補助試験。複数方程式sourceや熱源が入ると元のcontinuity-only responseと解釈が異なる |

推奨3の離散定義を固定する。元のunreferenced physical pressure systemをA0 p*=b0と定義し、corrected fluxのintegrated divergenceをq=b0−A0 p*とする。cell integrated source g_i[m³/s]、s_i=g_i/V_i[s⁻¹]、sum g_i=0を与え、

\[
\operatorname{laplacian}_h(rAUf,p^*)=
\operatorname{div}_h(\phiHbyA)-s,
\quad A_0p^*=b_0-g,
\quad q=g+r_{forced}.
\]

sourceはpressure equationのRHSに各SIMPLE iterationで同じ定義・符号で入り、corrected phi、pressure relaxation、U correction、T convectionの元のcoupling順序を維持する。元のmomentum/T operators・relaxationを変えない。Neumann solvabilityにはsum g=0が必要である。reference rowの処理を別に監査し、**solverのforced-system residualと元のphysical residual qは区別**する。q、g、q−g、reference cell、true/recursive residualを保存する。Case Cの元のresidual-to-phi mappingをforced residualへそのまま転用しない。

このsource付き状態は意図的に元のcontinuity方程式を満たさない。元のzero-source方程式に対するdiscrete-residual sensitivity experimentと位置付け、物理的mass injection解や元問題のaccepted solutionとは呼ばない。g=0 controlはstock solverと同条件で最終fields/metricsの同等性を確認してからnonzero試験へ進む。

**Pattern設計:** internal face perturbation vector aからg=B_h aを構成し、境界faceは0とする。単一internal faceでもowner/neighbourへ±deltaのcell pairが生じる。+delta_phi/−delta_phiのface pairを使う場合は、overlap/cancellation後のcell sourceでnormを評価する。faceのabs sumをmeanの代理にしない。

| Family | 登録する位置・分布 |
|---|---|
| A | localized centre、1 site |
| B | localized near-wall、hot-wall側とcold-wall側 |
| C | natural-convection boundary-layer band。zero-source独立baselineからの選択規則をimpact閲覧前に固定 |
| D | 4 disjoint sitesのspread defect。同じactual meanをA/B/Cと比較 |
| E | pressure reference-cell vicinity。reference row artifactとphysical sourceを区別 |

各familyを両符号で調べる。interior/near-wall、hot/cold、1 site/4 sitesの対比を含める。中心・壁からの距離は無次元座標とdeterministic cell/face selection/tie ruleを登録する。1-face localized supportはmesh refinementで物理サイズが変わるため、mesh-scaled familyとfixed-physical-support familyを区別し、未試験のfamilyへ外挿しない。

**Amplitude設計:** zero-netのpattern pをcell L1でnormalizeし、

\[
g_i=\sigma a\frac{p_i}{\sum_j|p_j|},\qquad
a=\eta_{nom}\frac{U_{p,base}V_\Omega}{L},\quad \sigma\in\{-1,+1\}.
\]

eta_nomを独立pilotで識別可能な複数decadeへ配置する。今回その数値range、point数、cutoffは未決定。baseline Upをsource設計で固定し、iteration内でsource amplitudeをUp_runに追随させない。Case Cのcapability/floorはpilotの測定可能性の参考に限り、quotaには使わない。floor plateauは未確立なのでuniversal floorと呼ばない。

**Same-meanの厳密な比較:** 同じsum abs(g)でもUp_runとr_forcedがpatternごとに変わるため、実際のepsilon_meanが同じとは限らない。eta_nom、Up_base、Up_run、actual epsilonを保存し、各patternを十分steadyにした後、別run間のamplitude調整/bracketingでactual meanをmatchする。matching toleranceは測定uncertaintyに基づく事前登録項目であり今回UNRESOLVED。amplitudeとactual epsilonの単調性も仮定しない。matchできなければH2/H3のsame-mean比較はinconclusiveとする。amplitude変更後は再収束させる。

**Temperature operatorの注意:** 元のTEqnはdiv(phi,T)を含む。q≠0では温度offsetに伴うT div(phi)項が無視できず、単にthetaへ置き換えたりcompensating heat sourceを追加したりすると別実験になる。absolute T/TRefと元TEqnを固定し、このsource実験のresponseがその離散定式化に依存すると明記する。sum g=0だけで熱輸送/QoI impactがゼロになるわけではない。

meanに加えmax、max/mean、max cell/location、P99、局所q_i/V_iを追跡する。P99は少数cellの孤立異常を見落としうるため、P99が小さいことでmax investigationを解除しない。maxをHardへ昇格させず、trigger cutoffは決めない。

## 17. Optional Arm 3 — boundary leakage

internal calibrationから独立したoptional BC/operator diagnosticとして、known single-wall leakage、equal-opposite wall leakage、nonzero net leakageを設計する。対象は4 physical wallsでempty front/backは別扱い。

\[
B_{net}=\sum_{f\in walls}\phi_f,\quad
B_{abs}=\sum_{f\in walls}|\phi_f|,\quad
C_{closure}=\sum_iq_i-B_{net}.
\]

patchごとのsigned/absolute flux、leak face/locationも保存する。equal-opposite leakageはB_net=0でもB_abs>0・個別patch flux≠0となり、global netだけではimpermeabilityを検証できない。closure=0もwall impermeabilityの保証ではない。

initial scopeではfrozen synthetic face fieldsによる検出性能試験で十分であり、coupled boundary sensitivityは必須にしない。**nonzero net leakageはclosed steady incompressible/source-free cavityと両立しない**。元問題のsteady解を要求する計画にしない。将来physical responseを調べるならvolume source/open BC/transient formulation等の整合した別問題を定義し、internal zero-netのtau_mean calibrationには混ぜない。boundary trigger cutoffは未決定。

## 18. Baseline and uncertainty

各gridで、独立microcaseの最もtightなtested pressure設定（初期候補1e-10）を使い、U/T/p/QoIを十分steadyに収束させたzero-source解を**highest-fidelity tested numerical baseline**とする。tightest toleranceだけでは十分条件にならず、other equation convergence/field stability/true residual等を確認する。真値・exact solutionとは呼ばない。Arm 2にはg=0実装controlとの同等性も必要。

primary differenceはsame-grid test−baseline。cross-grid baseline studyは離散化依存の別評価であり、80²baselineを全gridの真値として差し引かない。grid比較には同じ抽出法・有効な収束挙動が必要で、非単調/peak switchingではGCIを強制計算しない。same-grid差で離散化誤差が完全相殺するとも仮定しない。

| Uncertainty source | 将来の評価法・解釈 |
|---|---|
| iterative / steady | tail histories、追加iteration、field/QoI drift、他equation residual。Rwinだけを誤差boundとみなさない |
| pressure tolerance | Arm 1 sweep/true residual。同じbaselineを共有する差の相関を記録。smallest toleranceをexact扱いしない |
| grid dependence | zero-source baselineの20/40/80 studyと必要なvalidity確認。same-grid responseのgrid依存も別に保存 |
| serialization | in-memoryとASCII16再読比較。write/read差とsolver errorを分離 |
| restart | uninterruptedとrestartのpaired comparison。IO＋再初期化＋trajectoryを含み、純粋round-off floorと呼ばない |
| QoI extraction | 積分/断面sampling、interpolation、velocity peakとpositionのresolution、tie/flat/multiple peak |
| matching / forcing | actual epsilon matchingの幅、q−g、reference handling、source pattern/support、mesh anchor |

baselineだけでなくtest側の誤差も含め、Delta Qのuncertainty envelope u_Deltaを定義する。相関を説明できる場合はpaired cancellationを評価し、説明できない場合は保守的包絡とする。独立性の根拠なくRSSしない。同じ変動をiteration/pressure/continuity uncertaintyへ重複加算しない。

観測差D_Q=abs(Q_test−Q_base)がbaseline uncertainty以下なら**effect not resolved**とする。より厳密にはpaired u_Delta以下でも同様である。effect not resolvedはimpact=0やquota PASSを意味しない。quotaがmeasurement resolutionより小さい場合は評価不能としてbaseline/抽出精度を改善する。

## 19. QoI response metrics

value QoIは `E_Q = abs(Q_test−Q_base)/scale_Q`。scale候補1のabs(Q_base)は非zero量のfractional differenceを解釈しやすいが、baseline uncertaintyに対して小さい/zeroな量には適さない。候補2の独立characteristic scaleはzero近傍でも有限だが、選び方がquotaの意味を変える。

Nuのconductive characteristic scale、velocityのalpha/L等は独立physicsから定義できる候補である。採用scaleとzero-near分岐はimpact閲覧前に登録し、選択根拠を記録する。現段階で任意denominator floorは設けない。testごとに分母を変えず、各gridのbaseline scaleを固定する。cross-gridでscaleが異なる場合はraw Delta Qと共通characteristic-scale版も併記する。scale自体の不確かさもupper estimateに含める。

positionはs=Z/L、X/Lとして `E_pos=abs(s_test−s_base)`。中心線・component・符号・抽出interpolationを固定する。flat/multiple peaksではpeak candidate set/position intervalと抽出uncertaintyを報告し、任意tie-breakだけの位置jumpを精密な感度として扱わない。quota確認には位置のupper envelopeを用いる。

raw unitsで `D_Q^- = max(0,D_Q−u_Delta)`、`D_Q^+ = D_Q+u_Delta` を保存し、valueは固定scaleで規格化、positionはabsolute unitsとする。これは指定uncertainty envelope内の推定区間であり、統計的confidence levelを勝手に付けない。

各QoIでactual epsilon_mean vs E_Q/E_Q^+をpattern/grid/sign別に整理する。log-log trend/local slopeはresolved positive differencesのみで評価し、unresolved点は区間/censored observationとして表示する。zeroを任意floorへ置換してslopeを作らない。単一power lawを仮定せず、非単調性・pattern scatter・max/mean・peak locationとの関係を調べる。

## 20. Threshold inference rule

将来のtau_mean候補は、事前登録されたb_Qとscopeの下で、全required QoI・pattern・sign・state・gridについて `estimated conservation-related impact + uncertainty <= b_Q` を満たすepsilon領域から推定する。

1. 数値b_Q、scale、uncertainty法、収束/branch条件、required pattern/state/grid、boundary/local investigation手順をconfirmation前に固定する。
2. quota未定で探索実験を先行する場合は、得たresponseをcalibration evidenceとするだけでPASS/thresholdを付けない。quotaの独立研究根拠を記録し、その後にholdout/amplitude/patternのconfirmationを用意する。同じdataでquota選択と最終threshold保証を完結させない。
3. zero-source control、same-grid steady baseline、boundary compatibility、q/source/reference consistency、other equation convergenceとmeasurement resolutionを満たすrunだけを有効とする。未収束/branch change/run失敗は支持証拠から除き、単に無害とはみなさない。
4. 各epsilon levelで全required testのE_Q^+の上包絡を使う。Arm 1とArm 2は区別して確認し、一方から他方への同等性を仮定しない。
5. **zero側から連続して支持される領域**の上端を候補にする。低いepsilonでquota違反があれば、その先の孤立PASS levelを選ばない。H1が支持されなければ単一mean thresholdの適合性を再検討する。
6. finite sampled levelsだけで連続領域を保証しない。level間のinterpolation/boundを独立に正当化できなければ「tested levelsに限定した候補」とし、tau_meanの正式採用には不足とする。未試験patternへの保証も与えない。
7. local max/boundary/closureのinvestigationが完了し、scopeへの適用性を確認した後、別の仕様採用判断へ進む。cutoffがない現段階では自動clearance規則は完成していない。

今回はb_Qも実験結果もなく、tau_meanはUNRESOLVED。数値threshold推定・正式採用・Ra1e3再評価はしていない。

## 21. Applicability scope

最初の実験が支持できるのは、Ra_test=30000/Pr=0.71、指定closed cavity、20²/40²/80² mesh family、v6と登録したsolver/operators、serial/DP/ASCII16、tested steady branch、登録したsource sign/support/location/amplitudeと自然residual patternの範囲に限る。

Formal Ra=1e3/1e4/1e5/1e6、160²/320²、parallel、binary、異なるprecision/mesh/operator/BC/temperature offset、未試験defect patternへの自動転用は不可。Ra=0/Up=0、非steady state、branch changeも外挿対象外。formal matrixへの適用にはscope extensionの独立根拠と正式仕様レビューが別途必要である。

## 22. Limitations

- 数値quotaの独立科学的要求、c_Q、trigger cutoff、amplitude range、actual-mean matching tolerance、追加steady/resolution判定値は未定。設計を実行する前に必要項目を登録する。
- 実験・adjoint・source実装・steady baseline生成をしていない。Case Cの10-iteration mapping/operator証拠はcoupled QoI impact証拠ではない。
- Arm 1にはcoupled trajectory交絡、Arm 2には意図的なcontinuity方程式摂動とtemperature operator依存がある。両者は同じimpactを与えると仮定しない。
- meanは位置情報を失い、P99は孤立defectを見落とし、global netはzero-net internal defect/相殺wall leakageを見落とす。
- 同じepsilonで異なるimpactがあれば、scope限定・local investigation強化・metric/architecture再検討が必要になりうる。max Hardの必要性や数値はまだ結論できない。
- Baselineは有限grid/finite toleranceのnumerical referenceであり、paired differencesにも不確かさがある。effect not resolvedとscientifically negligibleは異なる。
- 全文未確認のAIAA/ASME標準・査読paperの詳細定理へ適合済みという主張はしない。確認した公開guidanceからclosed-cavityの数値b_Qは得られていない。
- finite experimentsで未試験pattern全体を保証しない。quotaを観測差に合わせて選ぶことは結果非依存の科学的許容性を作らない。

## 23. Required user decision

**A. Architecture:** HYBRID（B＋C）のQoI別quota recordとsame-QoI hierarchy reviewを次段階の基準とするか。READYはこの設計についての状態である。

**B. Numerical value:** 研究目的から独立のallowable QoI impactを先に指定できるか。現在は全b_Q/c_Q=UNRESOLVED。Gate E/Fの数値やformal結果から補完しない。

**C. Experiment scope:** Bが未解決のまま、**Ra_test=30000、20²/40²/80²の独立sensitivity experimentをquota-calibration evidenceとして先に行うか**が次の判断である。実施するならArm 1＋verification-only source Arm 2を中心に、Arm 3はoptional BC診断と分離する。探索pilotで測定可能なamplitude/matching/steady条件を決め、数値quotaの独立根拠とconfirmation段階を別途確定する。今回はこの判断を提示するだけで実行しない。

変更成果物は本Markdownと対応JSONのみ。開始時git statusは `?? cases/routeA/Ra0_medium/`、`?? cases/routeA/Ra1e4_coarse/`、`?? verification/`。これら既存untracked内容は変更していない。終了確認では既存tracked差分なし、対象2ファイルのみ新規追加、保護した6資料のSHA256一致を確認する。

```text
CURRENT_FORMAL_RA1E3_GATE_G = FAIL
GATE_G_CRITERIA_MODIFIED = NO
BUDGET_C_ARCHITECTURE = READY
RECOMMENDED_QUOTA_SCHEME = HYBRID
QOI_IMPACT_QUOTA_VALUE = UNRESOLVED
QOI_IMPACT_QUOTA_STATUS = UNRESOLVED
SENSITIVITY_EXPERIMENT_REQUIRED = YES
SENSITIVITY_EXPERIMENT_EXECUTED = NO
TAU_MEAN = UNRESOLVED
CANDIDATE_B_STATUS = PROVISIONAL
NEW_SPEC_RA1E3_GATE_G = NOT_EVALUATED
FORMAL_BENCHMARK_RESULTS_USED_FOR_QUOTA = NO
SPEC_CHANGE_EXECUTED = NO
USER_DECISION_REQUIRED = YES
```
