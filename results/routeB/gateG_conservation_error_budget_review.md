# Route B Gate G Conservation Error Budget Review

## 1. Purpose

レビュー日: 2026-10-04（Asia/Tokyo）。Route B Candidate Bのsolver-level discrete continuityをmean/local/globalへ分解し、研究上のacceptance budgetを設計する。今回solver・microcase・追加testは実行しない。正式benchmark結果を閾値導出にもpost-hoc判定にも使用しない。既存仕様・コード・verification・結果は変更しない。

**推奨はBudget C。Primary Hard候補はepsilon_phi_mean、local maxはmandatory diagnosticとinvestigation trigger、global/boundaryはmandatory diagnosticと整合性調査trigger。** max/globalの独立Hard閾値は今回提案しない。役割と調査workflowのarchitectureはREADYだが、mean数値・trigger条件の定量cutoffはUNRESOLVED。Candidate BはPROVISIONALであり正式採用できない。

CURRENT_FORMAL_RA1E3_GATE_G=FAIL、NEW_SPEC_RA1E3_GATE_G=NOT_EVALUATEDを保持する。READYはレビュー上の役割設計の完了を意味し、実装・運用可能な合否規則の承認ではない。

## 2. Current verification state

[Case C report](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/caseC_continuity_verification/verification_report.md:1) と同行JSONから確認した。

| Evidence | State / scope |
|---|---|
| actual parser・production continuity operator | PASS、合成20²/40²/80²/160² |
| stock/audit同値 | 代表20²・serial・ASCII16条件のU/T/p_rgh/phi最終file hash一致 |
| residual→flux mapping | PARTIAL。reference-aware関係を独立20²/40²/80²・初期10 SIMPLE iterationsで検証。無条件のtolerance直結は不可 |
| numerical floor | PARTIAL。丸め・write/read・restart差を測定したが普遍的floor/plateauは未確定 |
| acceptance budget | 未定。tau_phiはUNRESOLVED、Candidate BはPROVISIONAL |

前回のsingle internal-face defectではmax/meanが20²/40²/80²/160²で200/800/3200/12800、P99は0だった。この**独立operator証拠**をlocalの役割設計へ使うが、最大観測値に余裕を足してthresholdを選ばない。初期10 iterationsのmapping試験はsteady QoI感度試験ではない。

主要ローカル根拠は [acceptance_criteria.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/acceptance_criteria.md:198) のGate D（198–212）、E（214–240）、F（242–279）、G（281–330）、[benchmark_spec.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/benchmark_spec.md:26) の研究目的（26–39）、比較量（128以降）、Route B continuity（265–277）、保存診断（402–408）。現行文書中の過去の進捗文から現在の正式結果を再判定しない。

## 3. Numerical floor vs solver capability vs acceptance budget

| Category | Meaning | 現在分かること / 設計上の扱い |
|---|---|---|
| A: numerical/measurement floor | 有限精度・算術評価・保存・parser・restart等による計測/再現限界 | 一部を独立測定した。floorは許容値ではない。有限toleranceでの残差は全てが不可避floorとは限らない |
| B: solver capability | 条件・grid・tolerance・停止理由・precisionに対して達成できる保存誤差 | pressure tolerance sweepで情報があるが、全Ra・steady解・parallelまで認証していない |
| C: research acceptance budget | conservation-related errorが研究の結論/QoIに与える影響をどこまで許すか | 今回の設計対象。目的、影響、許容不確かさに基づく独立判断が必要 |

linear solve errorは、改善可能な部分はBの管理対象、丸めで改善不能な部分はAに属する。restart差も純粋なserializationだけではなく再初期化を含む。A/Bで観測した水準や任意の安全係数だけからCは定まらない。CがA/Bの測定・達成能力を下回った場合は手法/precisionを改善するか計測不能とする。結果を通すためにCを緩めない。

## 4. Relation to QoI uncertainty

対象QoIはNu_bar_cavity、Nu_bar_0、Nu_bar_half、Umax、Wmax、極値位置。**epsilon_phiとこれらのrelative/position errorに一般的な直接比例保証はない。conservation budgetをQoI budgetへ直接変換できない。** divergence-freeであることだけでは運動量・温度方程式を満たす保証もない。

この理由はcoupled discrete systemでも明確。圧力ゲージを固定した同一branchの十分smoothな非特異系F(z)=0を考え、近傍の近似解zの残差をr=F(z)、fully converged discrete解をz*とする。適切な方程式scaling/単位を用い、J=∂F/∂z、g_Q=∂Q/∂z、Jᵀlambda_Q=g_Qとすれば、一次近似で

$$Q(z)-Q(z^*)\simeq\lambda_Q^T r.$$

continuity blockが物理的なintegrated imbalance qと整合する場合、その寄与は

$$
|\delta Q_{\mathrm{cont}}|\lesssim
\|\lambda_{Q,c}\|_\infty\|q\|_1
=\|\lambda_{Q,c}\|_\infty\frac{U_pV_\Omega}{L}\epsilon_{\phi,mean}.
$$

感度lambdaはQoI・grid・Ra・状態・BC・branchに依存し、他方程式の残差寄与、非線形remainder、抽出誤差も必要。式は本レビューの条件付き線形化による説明で、adjoint計算や認証上界を取得したわけではない。scalar meanはdefectの場所・符号分布を捨てるため、同じmeanでQoI影響は異なり得る。極値位置はflat/multiple maximaで非smoothになり、relative位置誤差ではなく固定抽出法によるabsolute位置差とambiguityを扱う。

Gateとの整合は、同じQoI単位の誤差に変換してから行う。

| Gate | 既存の役割 | conservation budgetとの関係 |
|---|---|---|
| D | steady/iterative健全性、200反復窓、主要量R_win≤5e-4、残差目標1e-7 | 小さい残差や小さい窓内変動は真のQoI反復誤差を単独保証しない。Gのphi判定と併用 |
| E | Nu_bar_cavity/Umax/Wmaxのpaper agreement 1%、位置差0.01。Nu_0/Nu_halfはlike-for-like報告 | 1%はcontinuity閾値ではなく比較tolerance。reference uncertaintyも含み、自由に使えるconservation quotaではない |
| F | fine–medium差、QoIごとのgrid uncertainty/GCI、収束性 | GCIは各QoIの離散化不確かさ。epsilonと直接大小比較せず、同じQoIに対するiterative/conservation影響を評価する |
| G | 保存・対称性 | 離散方程式の整合性検証。D/E/Fの代替でも総合精度の証明でもない |

したがって `epsilon_phi < GCI/10`、`tau_mean=1%`、`epsilon_phi=1e-4 => Nu error<=1e-4` は採用しない。Nu_0/Nu_halfを感度試験で追跡しても既存Gate E/DのHard対象は増やさない。

## 5. Verification literature review

全Web資料のaccessed date: 2026-10-04。一次公開資料を優先し、長い引用はしない。以下の記述は資料の要約と、本研究への解釈を区別する。

| ID | Title / authors or provider / DOI or URL | Supports / applicability |
|---|---|---|
| L01 | ASME Journal of Fluids Engineering, Statement on the Control of Numerical Accuracy、および同じ公開bundle中の Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications。後者のPDF記載authors: Ismail B. Celik, Urmila Ghia, Patrick J. Roache, Christopher J. Freitas。[ASME公開PDF](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf)、PDF pp.1–2/3–15、Appendix A p.14（zero-based page13）。DOI: このbundle版として未確認 | stopping criterionと収束誤差推定を要求。残差の桁低下だけでは不十分とし、推定iteration errorをdiscretization errorより少なくとも1桁小さくする指針を示す。この因子は文献の**推定解誤差同士**の指針であり、epsilon/GCIへの直結ではない。本研究のbudget因子として自動採用しない |
| L02 | Examining Iterative Convergence — NASA Glenn / NPARC Alliance, John W. Slater。[公式tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/iterconv.html)、DOIなし | normalized residualに加え、目的量の収束を監視する考え方。量ごとの収束速度が異なる。epsilon_phiの数値閾値を規定しない |
| L03 | Examining Spatial (Grid) Convergence — NASA Glenn / NPARC Alliance, John W. Slater。[公式tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)、DOIなし | grid refinementと対象量のdiscretization estimate/GCI。continuity residualと同じ誤差とは扱わない |
| L04 | Verification Assessment — NASA Glenn / NPARC Alliance, John W. Slater。[公式tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html)、DOIなし | iterative/spatial convergence、mass-conservation consistency、code/calculation verificationを分離。global・local continuityの本規格化に対する共通閾値なし |
| L05 | Notes on Computational Fluid Dynamics: General Principles, 5.4 Residual — Chris Greenshields / Henry Weller, CFD Direct。[OpenFOAM authorsによる解説](https://doc.cfd.direct/notes/cfd-general-principles/residual)、DOIなし | residualのscale normalizationとabsolute/relative停止規則。solver residualをQoI誤差やepsilon_phiへ数値同一視する根拠ではない |
| L06 | An Introduction to Adjoints and Output Error Estimation in Computational Fluid Dynamics — Steven M. Kast, 2017。[author preprint](https://arxiv.org/abs/1712.00693)、DOI 10.48550/arXiv.1712.00693 | 今回はabstract/metadataのみ確認。output-specific adjoint研究の参考であり、査読済み標準とは扱わない。§4の式は本レビューの線形化で、本文の定理を検証済みと主張しない |

L01は「iterative errorをdiscretization uncertaintyに対して無視できるよう管理する」というhierarchyを支持する。**比較すべきものは同じ解量の推定誤差**であり、epsilonはその誤差推定量として未較正。1桁という具体的指針が存在することは記録するが、QoI感度やscopeを確認せずfactor1/10をGate Gへ移植しない。ASME V&V20やAIAA規格原本を精読したという主張はしない。Roache等の原本はL01/L03の参照として区別し、未閲覧の著作から新しい数値を引用しない。

検討した一次guidanceから、今回のoperator・Up規格化・closed cavityに直接移植できるtau_mean/tau_max/tau_globalの数値は得ていない。forumや別solverのmass-flow百分率を根拠にしない。

## 6. Mean conservation metric

$$q_i=\sum_f s_{if}\phi_f,\quad d_i=q_i/V_i,\quad
\epsilon_{\phi,mean}=\frac L{U_p}\frac{\sum_i|q_i|}{V_\Omega},\quad U_p=\max_{cell}|U|.$$

全領域L1の無次元continuity budgetで、solverが直接補正するface volume fluxを評価する。rho0一定のRoute Bでは同じ演算子のmass metricと等価。uniform meshで算術平均と体積平均が一致する。L/Upはadvective scale。有限割合のcellで滑らかな誤差分布ならgrid比較の意味を維持しやすいが、floor・Up・pressure matrix・局所defectのgrid依存まで消すわけではない。

弱点は局所異常を希釈することとQoI感度の場所依存を捨てること。Hard数値の根拠は独立した保存性の研究要求、またはscopeを定めたQoI-impact推定とquotaでなければならない。measurement floorや現在結果からは選べない。Ra=0ではUp=0となるためGate Cの絶対速度/伝導へ分岐し、任意Up floorを追加しない。

## 7. Maximum local metric

$$\epsilon_{\phi,max}=\frac L{U_p}\max_i|q_i|/V_i.$$

孤立defectを直接捉え、最大cell ID/座標と合わせてref cell、壁、面接続、parser/出力の問題を調べられる。反面、同じqの欠陥でもViが小さくなると増大し、全Ra/全格子共通のfixed tau_maxは「同じlocal source-rateを許す」という特定の研究要求になる。その要求は今回独立に正当化されていない。

単一outlierがpressure reference/算術評価に関連する場合も、見ただけで無害と判断しない。場所、signed q、reference-aware true residual、境界、近傍分布、出力再現性、QoI感度を調査する。現時点ではmax Hardを提案せず、mandatory diagnostic + triggerの設計を推奨する。

## 8. Percentile metrics

P95/P99はfield-distribution diagnostic。uniform meshでは前回のlinear empirical percentileを維持し、将来非一様格子ではvolume-weighted quantileの定義・補間を別途事前登録する。無次元化するなら(L/Up)P95/P99(|d|)を保存する。

2cellだけが異常な20²以上の前回testではP99=0だった。従ってpercentile単独をlocal Hard guardにする案は支持しない。maxは孤立異常、percentileは広がり、meanは全領域の量を測る。それぞれを保存し、P99が小さいことでmax調査を解除しない。

## 9. Global boundary imbalance

physical boundaryのoutward volume fluxについて

$$B=\sum_{f\in\partial\Omega}\phi_f,\quad
\epsilon_{\phi,global}=\frac L{U_pV_\Omega}|\sum_iq_i|,\quad
\epsilon_{B,net}=\frac L{U_pV_\Omega}|B|.$$

同じfaceを共有するincidenceではinternal faceが相殺され、正確算術でsum_i q_i=B。emptyはsolution-direction fluxから除外する。符号付き値は方向を診断し、閾値形式を検討するときは絶対値を使う。cumulative signed native continuityで代替しない。

三角不等式から

$$\epsilon_{\phi,global}\le\epsilon_{\phi,mean}.$$

従ってtau_global≥tau_meanならglobal Hardは数学的に冗長。tau_global<tau_meanなら追加のboundary leakage要求になるが、その独立budgetが必要。直接boundary Bとcell sumには丸め・加算順の差があるため、closure discrepancy |sum q−B|を別に報告する。両者を単に同じ数値であると仮定しない。

さらに**net=0は個々の壁のimpermeabilityを保証しない**。左壁から入り右壁から同量出る定常throughflowのface fluxはmean=global=0にもなり得る。closed cavityのBCを破っているがnetだけでは検出できない。将来のmandatory diagnosticに

$$B_{abs}=\sum_{physical\ walls}|\phi_f|,\qquad
\epsilon_{B,abs}=\frac L{U_pV_\Omega}B_{abs}$$

およびpatch別signed/absolute fluxを加える案を推奨する。これらは未実装であり、新しいHard数値を設定しない。閉壁にはゼロnormal fluxという物理条件があるが、保存値の厳密ゼロを普遍的な浮動小数点Hardとして即採用しない。global/absolute wall/closureはboundary問題のinvestigationに使う。

## 10. Grid scaling

同一L・depth W、square in-plane cell幅h=L/n、Vi=h²W、active side-face area=hWを考える。

| Metric | Smooth continuum defect d=s(x) | 固定1 internal-face flux defect delta_phi | Meaning |
|---|---|---|---|
| mean | volume quadratureで有限値へ収束 | 2|delta_phi|/Vtotal、gridによらず同じ | whole-domain L1 budget |
| max | bounded smooth sなら有限値へ収束 | |delta_phi|/(h²W)、n²で増大 | single-cell source-rate budget |
| global | signed integral / boundary integral | 0。境界defectなら|delta_phi|/Vtotal | boundary integral budget、local不可 |

固定delta_phi testのmax/meanはn²/2。20/40/80/160の実測比は200/800/3200/12800。将来320²なら同じ数学構成で51200と予測されるが、**320² test/solverを今回行ったわけではない**。mean/globalの定義はgrid-independentな積分要求として共通化できるが、数値floor・Up誤差・局所分布への適用性は別途確認する。

cell flux budgetの別表現も研究候補となる。例えばactive physical-direction faceの代表面積A_char,iを事前定義し、ell_i=Vi/A_char,iとすると

$$\chi_i=\frac{|q_i|}{U_p A_{char,i}}
=\frac{\ell_i}{L}\epsilon_{\phi,i}.$$

square extruded gridでA_char=hWならell=h、chi=(h/L)epsilon_local。chi固定はlocal source-rate固定とは異なり、epsilon_localの許容値がL/hに比例する。global Upはstagnation cellの実throughputではなくreference scaleである。実face throughputで割る案は零throughput/cancellationで特異になる。前後empty面をA_charへ含めない。非正方・非一様格子ではorientation/aspect ratio、active faceの選び方を再定義する。

別の候補は|q_i|≤Vi a_i、または|q_i|≤Up A_char,i gamma_iで、a_i（s⁻¹）・gamma_i（無次元）は未定。どちらも何を許すかが異なる。metric変更だけでphysical budgetが得られたとは扱わず、今回はchiを正式metricやHardへ追加しない。

## 11. Candidate Budget A

Hard候補: epsilon_phi_mean≤tau_mean。max/P95/P99/global/BはDiagnosticのみ。簡単でCandidate Bと直接対応するが、孤立異常が既知である現在の証拠に対し、保存だけで調査義務を設けない理由が弱い。mean-onlyでも原理的にwhole-domain要件として一貫するが、local影響が無害という根拠は未取得。Aを単独推奨しない。

## 12. Candidate Budget B

mean≤tau_mean、max≤tau_maxをともにHardとする。孤立defectを直接制限する利点がある。fixed maxはsource-rate品質を全cellに要求する強い仕様であり、Vi⁻¹増幅があること自体が数学的な欠陥ではない。しかしその品質要求、common grid/Up scope、floor、QoIへの必要性を定量化していない。現時点ではmax Hardの正当化が不足。cell-size-aware budgetとlocal sensitivityを研究した後の選択肢として残す。

## 13. Candidate Budget C

mean Hard候補 + max mandatory diagnostic/investigation trigger。triggerとDiagnosticは異なる。trigger発生時には原因・位置・影響を調査し記録するが、超過だけで自動Gate FAILにはしない。調査未完了で問題が解消したとして自動PASSも出さない。

数値未確定のtrigger family案:

- epsilon_max>T_max(h,Up,precision,operator,state)。T_maxは未定で、観測最大値から余裕付きで作らない。
- mean>0のときrho_loc=epsilon_max/epsilon_meanを保存し、事前のT_ratio(n/Vi distribution)に対して調査する。T_ratio未定。ratioだけをHardや無害判定にしない。
- local q、max位置、近傍分布、reference/boundaryとの関係を用いた事前登録の異常pattern判定。具体的なregion/ruleは今後固定する。
- 独立に確認したsolver/serialization/operator envelopeを超える局所不整合を調査する。前回のPARTIAL floorを認証envelopeと呼ばない。

mean=max=0ならrho_locはundefinedとしてabsolute情報を使う。任意のratio denominator floorは導入しない。Cはlocal原因を見逃さないworkflowを与え、根拠のないmax Hardを避けられる。ただしtrigger cutoff未定の現在は運用規則として未完成。

## 14. Candidate Budget D

mean Hard + global/boundary net Hard。closed cavityでboundary netがゼロという物理要求に対応する利点があるが、§9の冗長性、signed相殺、wall間相殺、丸めを考慮する必要がある。global Hardだけでは閉壁条件を十分検証できない。

C+Dを組み合わせる案は、meanとは別にboundary netをより厳しく制約したい研究上のquotaを定められた場合に可能。ただし現時点でtau_globalを選ぶ独立根拠がなく、absolute wall flux診断も必要。今回はDの独立Hardを推奨しない。Cにglobal/absolute boundary/closureのmandatory diagnosticsとinvestigation workflowを組み込む。

## 15. Comparison

| Budget | Whole-domain criterion | Isolated defect | Boundary | 根拠・現時点の判断 |
|---|---|---|---|---|
| A | mean Hard候補 | 保存のみ | 保存のみ | 単純。無害性の根拠がなく調査義務が弱い |
| B | mean Hard候補 | max Hard | 診断 | local物理budget/scale未定で現時点では過剰に未正当化なHard追加 |
| C | mean Hard候補 | max trigger、原因調査 | net/absolute/closure診断 + 調査trigger | **推奨。役割設計READY、cutoff未定** |
| D | mean + net Hard候補 | 検出保証なし | 独立quotaなら追加要求。net相殺/冗長性に注意 | tau_global根拠なし。C+Dは将来の選択肢 |

## 16. Recommended architecture

**RECOMMENDED_BUDGET=C。ARCHITECTURE_STATUS=READY（役割・workflowのみ）。**

| Layer | Proposed Route B conservation role |
|---|---|
| Primary Hard | epsilon_phi_mean≤tau_mean。数値未定なのでまだ判定不能 |
| Investigation trigger | local maxの事前T_max/T_ratio/pattern rule、およびboundary leakage/closureが事前誤差envelopeと整合しない場合。cutoff/判定ruleはUNRESOLVED |
| Mandatory diagnostics | mean/max、local signed qとVi、max location、P95/P99、signed global、B_net/B_absとpatch別値、cell-sum/boundary closure、epsilon_v、epsilon_m_reconstructed_legacy |
| Context diagnostics | Up、grid/precision、pressure residual停止理由、利用できるreference-aware true residual、serialization/restart evidence |

Hardは超過でFAIL、triggerは超過で調査、Diagnosticは記録するだけ。採用時にはtrigger成立→原因/位置/impactの記録→解釈/処置→review完了というworkflowと責任を事前固定する。原因がinput/BC/operator bugなら独立のVerification問題として扱い、max超過を自動FAILへ読み替えない。review待ちの状態を無条件PASSとみなさない。これは今回existing status schemaを変える作業ではない。

Gate Gの熱収支・断面保存・温度/速度対称性の既存Hardはそのまま。reconstructed Uのepsilon_vをsolver continuity Hardへ戻す理由は新たに得られていない。Route Aはvariable-density mass-flux semanticsが違うため自動適用しない。将来共有できるのはroute-native corrected conserved fluxを独立評価する原則までであり、metric/thresholdはroute別である。

## 17. Numerical threshold status

| Parameter | Value / status | Meaning |
|---|---|---|
| tau_mean | null / UNRESOLVED | Hard候補のacceptance budgetを未正当化 |
| tau_max | null / NOT_PROPOSED | 今回max Hardは提案しない。local triggerのT_max/T_ratioは別parameterでUNRESOLVED |
| tau_global | null / NOT_PROPOSED | 今回global Hardは提案しない。boundary/closure triggerのcutoffは別parameterでUNRESOLVED |

MEAN_THRESHOLD=UNRESOLVED、LOCAL_TRIGGER_THRESHOLD=UNRESOLVED、NUMERICAL_THRESHOLDS_STATUS=UNRESOLVED。HardとしてNOT_PROPOSEDであることとDiagnostic/triggerで検討不要であることを混同しない。Candidate Bの正式採用にはmean budgetと運用可能なtrigger protocol、scope、仕様version/後処理設計の判断が残る。

数値選定の将来手順は、(1)研究結論に必要なQoI保存関連quota b_Qを先に指定、(2)同じQoIのiterative/discretization/抽出不確かさとの整合を確認、(3)continuity影響を感度/誤差推定で較正、(4)operator/precisionの実現性を確認、(5)scopeとcutoffを事前登録、の順。b_Qやquota配分係数も現在未定であり、Gate Eの1%やGate FのGCIへ機械的に比例させない。

## 18. Need for sensitivity experiment

**QoI impactに基づくtau_meanを決める今回の方針では、独立sensitivity experiment（または同等の認証された感度/誤差bound）が必要。今回は計画のみ、solver実行なし。**

1. **事前の研究要求:** Nu_bar_cavity/Nu_0/Nu_half/Umax/Wmaxはnonzero量のrelative impact、極値位置はabsolute impactのquota b_Qを定める。Nu_0/Nu_halfは実験監視量であり既存Gate Hardを増やさない。必要なら同じQoIのU_disc,Qに対するquota配分を検討するが、係数は未定。epsilonとの直接比較はしない。
2. **独立problem/scope:** 既存の独立Ra_test=3e4 cavityを起点とし、20²/40²/80²、同じgeometry・Pr・BC・物性・抽出法、serial DP ASCII16を固定。formal benchmark case、formal Ra値、paper referenceを使わない。単一microcaseで得たthresholdを全Raや160²/320²へ無条件に展開しない。scope拡張は独立problem群/解析boundで別途裏付ける。
3. **steady baseline:** initial10 iterationsではなく、QoIの残留変動・外部反復誤差・運動量/温度残差・出力誤差がquotaの評価を妨げない状態まで独立計算を収束させる。tight baseline自身のtrue residual/reference/rounding、restart/serializationを評価し、baselineをexactと呼ばない。収束判定・試験終了条件を計算前に固定する。
4. **Arm 1: algorithmic capability/impact:** 同じgridのpressure absolute tolerance=1e-6/1e-8/1e-10をcontrolled variablesとして比較し、relTol=0、他条件固定。完全に収束したpaired runのQoI差とepsilon、true/recursive residual、local/globalを保存する。toleranceはcontinuity以外のSIMPLE trajectoryにも影響するため、相関だけでcontinuity単独の因果係数を断定しない。
5. **Arm 2: controlled residual pattern:** verification専用実験で、referenceを除く物理continuity blockに既知のzero-net signed residual patternを与える、またはcoupled systemへの既知flux defectを維持する。internal faceの±対、spread-out pattern、壁近傍・中心・reference近傍を事前登録し、meanが同じでも場所/最大値が異なる状態を比較する。これは人工forcingによる独立実験でありproduction PDE/solverを変更しない。stock pressure correctionは単発phi perturbationを消すので、どの方程式・時点へ作用させるかを明記する。frozen-field後処理だけではcoupled QoI応答の証拠にならない。boundary leakageはBC変更を伴う別問題なので、このclosed-domain較正へ混ぜない。
6. **QoI不確かさとの比較:** 同じQoI単位で保存関連impactの上包絡 Delta_Q^+(epsilon,h,pattern,state)を推定し、baseline/iteration/grid/serialization/抽出とpattern未網羅の不確かさを明記する。局所plotや最大位置移動も追跡。再計算GCIを使うなら独立microcaseの有効なgrid studyを用い、正式benchmark GCIを読み込まない。未収束/非漸近ならそのGCIをbudget根拠にしない。
7. **threshold選定:** 事前candidate値とscopeについて、全selected QoIで推定impactと不確かさがb_Qを満たす領域を調べる。有限testから任意のdefect分布への保証を主張しない。measurement/capabilityが不足すればUNRESOLVEDを維持する。trigger cutoffも位置・分布・grid scale・再現性から独立に登録し、現在benchmark値は使わない。

十分小さいiterative/conservation-related **QoI影響**を離散化不確かさや比較要求に対して管理する考え方は妥当。ただしreference agreementの偶然の相殺を許さず、総errorの独立性が未確認ならRSSで自動合成しない。保守的な合成/影響上界とその仮定を明記する。追加experimentは今回の許可内では実行しない。既存benchmark solverのrerunは不要。

## 19. Provisional Gate G specification

**未採用・未実装。Route B専用。**

- Ra>0: corrected face volume fluxを用いたepsilon_phi_mean≤tau_meanをprimary conservation Hard候補とする。tau_mean未定の間は評価不能。
- epsilon_phi_maxはmandatory diagnostic、事前登録triggerによる調査対象。max Hardは追加しない。P95/P99は分布診断。
- signed global、absolute net boundary、absolute total wall leakage、patch別値、telescoping closureはmandatory diagnostic/調査対象。独立global Hardは追加しない。
- epsilon_vとepsilon_m_reconstructed_legacyはDiagnostic候補。legacy keyと旧criteriaの意味を黙って置換しない。
- Ra=0はGate Cの絶対基準へ分岐し、epsilonの分母floorは作らない。
- 既存の熱収支0.2%、断面保存0.5%、温度/速度対称性各0.2%、Gate D/E/Fは変更しない。Route Aへ自動適用しない。

trigger/cutoff/QoI quotaの事前登録、仕様versionと後処理・review workflowの実装は採用後の別作業であり、今回は行わない。正式Ra=1e3判定はFAIL、新案はNOT_EVALUATEDのまま。

## 20. Limitations

direct QoI mapping、continuity-specific adjoint、complete nonlinear error bound、QoI感度試験は未取得。Case Cは短い独立pressure/operator検証でありsteady impactの証拠ではない。local/globalのarchitectureは役割を定めただけで運用cutoffがない。meanのscope共通化は定義の整合を示し、全格子・全Raの測定floorを保証しない。ASMEの解誤差hierarchyをepsilonへ直結しない。L06はabstractのみ、規格原本や全V&V文献を網羅した調査ではない。

開始時git statusは既存の `?? cases/routeA/Ra0_medium/`、`?? cases/routeA/Ra1e4_coarse/`、`?? verification/`。これらに触れない。今回新規作成するのは本Markdownと同行JSONだけ。既存docs/Scripts/reference/verification/results/casesを修正・commitしない。最終git statusで同じ既存3項目と新規2ファイルだけであることを確認する。

## 21. Required user decision

次に判断するのは、(1)Budget Cのmean Hard候補＋local/boundary investigationという役割案を次段階の設計基準とするか、(2)保存関連QoI impactの許容quota・対象量・適用scope、(3)上記独立sensitivity experimentの計画を具体化するか、である。数値や正式採用を承認できる根拠はまだ揃っていない。今回は研究設計の提出まで完了し、既存仕様へ反映しない。

```text
CURRENT_FORMAL_RA1E3_GATE_G = FAIL
GATE_G_CRITERIA_MODIFIED = NO
RECOMMENDED_BUDGET = C
RECOMMENDED_HARD_METRICS = epsilon_phi_mean (other existing Gate G Hard conditions retained)
RECOMMENDED_INVESTIGATION_TRIGGERS = local_max / boundary_leakage / boundary_closure (cutoffs unresolved)
RECOMMENDED_DIAGNOSTICS = max / P95 / P99 / global_signed / boundary_net_abs / boundary_abs_total / patch_flux / local_q_V_location / epsilon_v / epsilon_m_reconstructed_legacy
TAU_MEAN = UNRESOLVED
TAU_MEAN_STATUS = UNRESOLVED
TAU_MAX = NOT_PROPOSED
TAU_MAX_STATUS = NOT_PROPOSED
TAU_GLOBAL = NOT_PROPOSED
TAU_GLOBAL_STATUS = NOT_PROPOSED
ARCHITECTURE_STATUS = READY
NUMERICAL_THRESHOLDS_STATUS = UNRESOLVED
SENSITIVITY_EXPERIMENT_REQUIRED = YES
CANDIDATE_B_STATUS = PROVISIONAL
NEW_SPEC_RA1E3_GATE_G = NOT_EVALUATED
BENCHMARK_SOLVER_RERUN_REQUIRED = NO
SPEC_CHANGE_EXECUTED = NO
USER_DECISION_REQUIRED = YES
```
