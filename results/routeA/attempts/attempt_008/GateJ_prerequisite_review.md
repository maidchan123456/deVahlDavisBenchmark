# Route A Gate J prerequisite review

Task: REVIEW_ROUTE_A_GATE_J_PREREQUISITES. Review / synthesis / research-decision support only.
Date: 2026-10-05T00:19:26.115765+09:00
Ownership: REVIEW_ONLY; no execution contract.

## 1. Executive summary

前提監査は **COMPLETE**。formal Gate Jは現在 **実施不可**。Route B core未成立とRoute Aの全Ra Gate F FAILが既知のblockerであり、A/B Gate Kの全要件closureも未確立である。H PASSによる免除は行わない。

**研究判断（INFERENCE）:** 修士研究の thermal natural convection → transient fluid behavior → moving particle/object → tea-leaf jumping という目的には、別ownership **DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION** を準備する順序を推奨する。固定160²上の時間刻み感度とclosed-volume mass/energyを調べる意義は高い。これは formal Gate Jやgrid-independent resultではない。

科学的正当性は **CONDITIONAL**。YESとするのは「formal Jを名乗らない診断研究の経路を設計できる」という判断だけであり、現時点の実行許可・技術準備完了を意味しない。今回はreview4ファイルだけ作成し、solverも次契約も作成しない。

## 2. Authority and provenance

HEAD `dd009cfed3098a74e4cf2344432b10f23c9922b4` は既知HEADと一致。effective v1.7 `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`、Amendment007 `9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592` を照合済み。v1.7はHのみの契約で `authority.Gate_J_authorized=false`。既存の実行destinations-absent条件はH開始前の歴史的guardであり、今回の実行後reviewには適用しない。

v1.7のimmutable hash guards **9973件**とamendment/parent/script/template/referenceを照合し、不一致0。前回H result reviewの保護対象251,521件を再照合し、今回開始時の全保護対象 **251,527件**をsnapshot。12 final segmentのGate A/OQ-02記録、original attempt008 seal 27件を確認。新しいreviewをoriginal sealへ追加しない。詳細なsource hashes、before/after proofはJSONに保存。

本reviewは既存Gate判定を再計算・昇格しない。古いAC§1.1、implementationやworkflowの「未実施」「次段階」は当時の状況であり、最新execution/review証拠を優先する。`BENCHMARK_CORE_PASS=NOT_EVALUATED`という歴史的保存値と、凍結論理で現在成立しないというreadiness NOを分離する。

## 3. Gate J literal specification

規範は `docs/acceptance_criteria.md` §12（373–386行）、参照先§7/9。原文をそのまま以下に抽出する。

### Original Gate J — 非定常拡張（`DOWNSTREAM_TRANSIENT_READY` のみ Hard）

この Gate は `BENCHMARK_CORE_PASS` には不要だが、将来の茶葉・物体運動との **Route A 非定常連成**へ進む前には必須とする。B の主 Verification、A の特性評価、Gate H 合格の後に実施する。

- [ ] $Ra=10^6$、fine 格子、静止・一様 $T_0$ 初期条件から開始している。
- [ ] 二次精度 backward 時間離散を使用している。
- [ ] 最大 Courant 数目標 0.5 と0.25の2系列を実施している。
- [ ] 2系列の最終 $\overline{Nu},U_{max},W_{max}$ の相対差が全て0.5%以下である。
- [ ] 0.5%を超えた場合、最大 Courant 数0.125を追加し、最も細かい2系列で再判定している。
- [ ] 最終値が Gate E と同じ原論文値との1%基準および Gate G の Route A 保存基準を満たす。ここでの原論文比較は A 非定常計算の実用比較であり、B の Verification 判定ではない。
- [ ] 定常到達判定を無次元時間履歴で示している。
- [ ] 初期過渡を含む単純平均で最終値の誤差を隠していない。

全項目合格し、前提ステータスと Gate H 合格が揃った時のみ `DOWNSTREAM_TRANSIENT_READY` とする。



fineは現在の160×160×1。Nuはprimary cavity全領域平均、U/Wは固定中心線の同名極値であり、壁Nuやmonitor samplingへ置き換えない。§7との位置条件は `|Z−Zref|≤0.01`, `|X−Xref|≤0.01`、判定は絶対誤差。scalar1%とposition0.01を混同しない。Coは最大値の目標であって一定deltaTそのものではない。2最細系列の比較分母/時刻整合など実行詳細は未来の契約で固定する。

Gate Jの文字通りの目的はRoute A非定常連成前の時間刻み依存・最終steady practical agreement・保存と定常到達の確認である。定常Table Vは過渡軌道のreferenceではなく、§12の最終値≤0.5%だけで初期過渡全体の時間精度を証明できない。OQ-07 mass/energy evidenceを設計noteから別途必要条件として扱う。

## 4. Formal logical prerequisites

```text
BENCHMARK_CORE_PASS = A_B ∧ B_B ∧ C_B ∧ D_B ∧ E_B ∧ F_B ∧ G_B ∧ K_B
ROUTE_A_CHARACTERIZED = BENCHMARK_CORE_PASS ∧ A_A ∧ B_A ∧ C_A ∧ D_A ∧ F_A ∧ G_A ∧ K_A ∧ three-comparison reporting ∧ H performed/reported
DOWNSTREAM_TRANSIENT_READY = ROUTE_A_CHARACTERIZED ∧ H_pass ∧ J_A
```

AC§14の式と一致する。H実施・報告はA characterizationの条件、H数値PASSはdownstreamの条件。A steady Eは報告義務でありcharacterizationの独立Hard項ではないが、future J最終原論文比較はHard。Gate Iの数値目安はDiagnosticであり、I報告/原因分析とK成果物closureを省略できない。

AC§12がさらに実行順序を「B Verification、A characterization、H PASS後」と規定する。J_AはJの結果条件であり、J開始前の自己前提ではない。現在のNOは既知D/F/G未達だけで確定し、Kを仮にPASSとしても変わらない。

## 5. Current prerequisite matrix

FORMAL_PASS＝既存正式判定あり、FORMAL_UNRESOLVED＝全要件成立の証拠未確立、SCIENTIFICALLY_USABLE_WITH_LIMITATION＝限定した問いに使用可、DIAGNOSTICALLY_USEFUL＝診断情報あり、NOT_REQUIRED_FOR_THIS_SPECIFIC_QUESTION＝この固定格子内の問いには必須でない。これらをaccepted statusと混ぜない。

CSVはformal owner、required for what、reason、importance、concept分類まで保持。以下は比較用の短縮表。

| prerequisite | formal_status | scientific_need_for_transient_study | blocks_formal_J | remediation | priority |
| --- | --- | --- | --- | --- | --- |
| A_B | FORMAL_PASS (existing evidence) | A own provenance required; full B provenance not required for within-A question | NO | Preserve existing evidence; no new source audit | P2 |
| B_B | FORMAL_PASS / ROUTE_B_AUDIT_PASS | B equation audit gives comparative context; not needed to measure A time sensitivity | NO | Retain scope limitation | P2 |
| C_B | FORMAL_PASS | Useful calibration; A has its own C PASS | NO | None for current bounded study | P2 |
| D_B | PASS 9/12; FAIL Ra1e6 3/3 | NOT_REQUIRED_FOR_THIS_SPECIFIC_QUESTION; required for accepted B comparison | YES | Future controlled mechanism/remediation plan, preserve original failures and cap | P1 formal / P2 diagnostic |
| E_B | PASS Ra1e3–1e5; NOT_EVALUATED Ra1e6 | Not required for within-A temporal; required for B Verification claim | YES | After accepted B fine evidence, evaluate unchanged E | P1 formal / P2 diagnostic |
| F_B | FAIL Ra1e3–1e5; NOT_EVALUATED Ra1e6 | Not required for fixed A temporal; needed to separate AB continuum errors | YES | 320 and appropriate uncertainty evaluation where required; Ra6 D first; no guaranteed PASS | P1 formal / P2 diagnostic |
| G_B | FAIL Ra1e3; NOT_EVALUATED_UNDER_FROZEN_REVIEW others | Not needed for within-A study; own A transient mass/energy essential | YES | Future operator-consistent review/remediation under unchanged criteria; frozen investigation retained now | P1 formal / P2 diagnostic |
| K_B | FORMAL_UNRESOLVED / final PASS not established | Own diagnostic evidence closure essential; complete B packaging not required | YES (evidence not established) | Review-only future Gate K checklist/equivalent path index, row metadata and visual/diagnostic closure | P1 formal / P2 diagnostic |
| BENCHMARK_CORE_PASS | NOT_ESTABLISHED; historical NOT_EVALUATED | NO for bounded within-A question; PARTIALLY for AB/continuum interpretation | YES | Close all required B components under frozen rules | P1 formal / P2 diagnostic |
| A_A / OQ-02 | FORMAL_PASS (12 recorded final segments) | Required: correct runtime/model/inputs and cold pressure/rho initialization | NO | Future transient-specific initialization/runtime checks, do not reuse steady PASS as transient proof | P0 future design |
| B_A | FORMAL_PASS / ROUTE_A_AUDIT_PASS | Required, with transient active terms and algorithm checked | NO | Future bounded transient algorithm/source-to-observable review; no broad re-audit now | P0 future design |
| C_A | FORMAL_PASS | Required calibration available; not transient validation | NO | Retain; additional transient unit check decision belongs to future design | P0 available |
| D_A | FORMAL_PASS 12/12 | Accepted Ra6 fine baseline important; transient arrival requires separate definition | NO | Future duration/arrival/inner-convergence plan; no steady rerun | P0 available |
| E_A practical comparison | PASS all fine (diagnostic steady) | Useful baseline and final practical comparison; not transient reference trajectory | NO (steady); future J must evaluate | Same scalar/position definitions on future transient final state; no new threshold | P0 future design |
| F_A | FORMAL FAIL all four Ra; needs_320 YES | NOT_REQUIRED_FOR_THIS_SPECIFIC_QUESTION; required for grid-independent/AB claims | YES | Additional 320 per affected Ra + generalized Richardson/uncertainty review; acceptance not guaranteed | P1 formal / P2 diagnostic |
| G_A steady | FORMAL_PASS all four accepted fine | Necessary supporting steady baseline; does not establish transient storage balance | NO | Future transient final G plus full mass/energy evolution checks | P0 future design |
| K_A | FORMAL_UNRESOLVED / final PASS not established | Own transient provenance and evidence closure required | YES (evidence not established) | Future indexed Gate K audit; stale minimal tables must not be treated as full matrix | P1 formal / P0 diagnostic evidence design |
| Three separated comparisons | REPORTED within stated scope; full K closure unresolved | Comparative context useful; diagnostic B row cannot prove model difference causally | NO for reporting separation; K remains unresolved | Preserve labels; Gate K metadata/visual completeness separately audit | P0 available |
| I_A / I_B reporting and cause analysis | DIAGNOSTICALLY_USEFUL; full visual/cause checklist UNKNOWN | Needed to detect axes/artifacts; complete B I not prerequisite to A temporal question | UNRESOLVED through K, not independent Hard I threshold | Future evidence closure of visuals and out-of-guide causes; no new I threshold | P1 formal / P0 own diagnostics |
| H performed/reported | COMPLETE | Available steady formulation sensitivity evidence | NO | None; retain limitations | P0 available |
| H_pass | FORMAL_PASS; review SUPPORTED_WITH_LIMITATIONS | Supporting confidence for selected steady QoIs, not transient mass/energy | NO | None; no waiver | P0 available |
| ROUTE_A_CHARACTERIZED | NOT_ESTABLISHED / readiness NO | Not required as full formal predicate for separately owned diagnostic question | YES | Close every required component; H numerical PASS alone insufficient | P1 formal / P2 diagnostic |
| J_A numeric checklist | NOT_EXECUTED | Temporal sensitivity and final-state comparison scientifically valuable | Execution not allowed now; J_A is outcome, not prerequisite to itself | Only after formal prerequisites + future explicit formal contract/authorization | P1 formal |
| Transient algorithm / startup / dt / arrival | NOT_DESIGNED / technically NOT_READY | Essential to isolate temporal/iterative/truncation effects | YES technical execution readiness; separate from frozen predicate | Future separate contract preparation; no algorithm selection or contract now | P0 future design |
| Transient mass / energy / OQ-07 | NOT_EVALUATED / method tolerances UNRESOLVED | Essential; psi=0 EOS/solver-rho synchronization and total mass need assessment | YES technical execution readiness; not inferred from steady G | Preregister operators/integrals/normalizations and grounded criteria; unresolved means stop before execution | P0 future design |
| New execution authority / ownership | NOT_AUTHORIZED; v1.7 Gate_J_authorized=false | Required reproducible scope, ownership and evidence retention | YES execution authorization | Next prepare-only task after user roadmap decision; later explicit RUN task | P0 future decision |
| Full formal closure first as development sequence | Formal order binding; development preference separable | NOT_REQUIRED_FOR_THIS_SPECIFIC_QUESTION | YES formal; NO inherent scientific need for separate bounded diagnostic | Choose scope; preserve formal failures; no criteria amendment | P0 future decision |
| Particle/FSI readiness | NOT_READY / NOT_EVALUATED | Required before actual coupling claims, later research | Not a prerequisite to fluid-only study; blocks coupling claims | Separate later fluid-condition/force/heat/particle validation; no particle work now | P2 later |

Gate Kの対応成果物チェック（このreviewの証拠closure所見であり、歴史的Gate KへFAILを追加しない）:

| requirement | Route_A_evidence | Route_B_evidence | audit_finding |
| --- | --- | --- | --- |
| Source/equation audits | docs/openfoam_design.md / routeA_implementation.md | docs/routeB_design.md / routeB_implementation.md | Existing audit PASS; source scope retained; no fresh source audit |
| Run manifest | results/routeA/run_manifest.json is minimal only; final segment manifests carry matrix provenance | results/routeB/run_manifest.json + full_matrix_manifest.json | Literal results/run_manifest.json absent; route-specific equivalent path index/full K signoff not established |
| Benchmark summary | attempts004–007 trio_matrix and group_evaluation; attempt007 full summary/review | results/routeB/benchmark_summary.csv (12 rows) | A summary12 has incomplete AC§13 minimum metadata by itself; distributed sources exist |
| Three route comparisons | attempts004–007/*routeA_vs_routeB.csv (57 rows/group;19 quantities×3grids); paper/group reports | B final review + benchmark_summary.csv | Reporting separation supported; results/route_comparison.csv absent; no accepted B at Ra6 |
| Grid convergence | attempts004–007 group_evaluation.json and attempt007 review#/Gate_F_detailed | results/routeB/grid_convergence.csv (12 QoI rows) | B grid CSV lacks case_id/Ra_actual/Pr_actual/grid/route/status/source iteration/method version; joined provenance exists but full row closure unresolved |
| Conservation | Per-group Gate_G and review; results/routeA/conservation.csv only2 minimal rows | results/routeB/conservation.csv (14rows) | A minimal aggregate is not12case matrix; per-case sources must be indexed as equivalents |
| Figures / Gate I | Case-specific theta/velocity/streamlines/centrelines/localNu/sectionNu; values and positions in metrics | Route B figures and fine diagnostic reports | Plot existence != visual audit. Full visual checklist/cause analysis and grid convergence figure closure not established |
| Execution logs | Sealed raw/final segments with health/normal exit | Full manifest log hashes and external native logs | Source-traceable existing logs; unaccepted cases remain marked |
| Scripts/reference/accepted fields | Versioned segment analyzer/runtime hashes, raw seals, Table V reference; accepted fields | full_matrix_manifest script/reference/metrics/accepted field hashes | Existing traceability supports reuse; final K full checklist has no established PASS |

## 6. Route B blockers

**OBSERVED:** 12/12 computed、9/12 accepted。Ra1e3–1e5の各3grid D PASS、Ra1e6は3/3 D FAIL、0/3 accepted、各最終30000。Ra6は全grid残差条件FAIL、coarse/mediumは熱傾きも正でFAIL。fine熱傾きPASS・小Rwin・paper近接は残差FAILを打ち消さない。plateau/oscillatory floorらしさはあるが機構UNKNOWN。

E_BはRa3–5 PASS、Ra6未acceptedによりNOT_EVALUATED。F_BはRa3 U、Ra4/5 W非単調でFAIL・needs_320 YES、Ra6はunaccepted gridsによりNOT_EVALUATED。Ra6の320 recommendation NOT_NEEDEDは当時の「まずD受入前なのでformal F追加不要」という順序判断であり、空間不確かさ不要という証明ではない。

G_BはRa3 reconstructed mass-divergence FAIL、他Raはfrozen reviewのNOT_EVALUATED。定数rhoでepsilon_m=epsilon_vという既存定義が重要であり、small pressure-corrected native phi divergenceで再構成Uのformal mass基準を置換しない。Candidate B PROVISIONAL、tau UNRESOLVED、調査freezeをPASSとしない。A_B/B_B/C_Bは既存PASS、K_Bは全closure未確立。

`COMPLETE_WITH_DOCUMENTED_LIMITATIONS`と「次研究段階を妨げない」はworkflow判断。全Hard成立・CORE PASSを意味しない。歴史的CORE NOT_EVALUATEDをそのまま保存。

将来のformal remediation候補は、(1) Ra6残差/熱傾きのoperator・solver・formulation・inner convergenceの制御されたmechanism review、(2) unchanged acceptance下で新ID/将来契約に基づく数値対策、(3) accepted evidence後のE/F/G、(4) Ra3–5必要refinement、不確かさ評価、(5) G operator問題とK/I closure。元の上限30000は到達済みで、現在の規則に継続延長・tolerance緩和・post-hoc昇格の許可はない。「further iteration」は新たな事前登録と明示判断がある場合だけ検討可能。今回B再実行・調査再開なし。

## 7. Route A Gate F blockers

**OBSERVED:** 全Ra group F FAIL・needs_320 YES、各D accepted。原記録のFAIL量だけを以下に示す。p/GCIのnullは0ではない。

| Ra | quantity | formal_status | convergence | fine_medium_pct | p_obs | GCI_pct | quantity_needs_320 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | Umax | FAIL | NON_MONOTONIC_OR_UNDEFINED | 0.07664198983060125 | None | None | True |
| 10000 | Wmax | FAIL | NON_MONOTONIC_OR_UNDEFINED | 0.02486051188117872 | None | None | True |
| 100000 | Wmax | FAIL | NON_MONOTONIC_OR_UNDEFINED | 0.12298129528625253 | None | None | True |
| 1000000 | Nu_bar_cavity | FAIL | MONOTONIC_CONVERGENCE | 1.3402375460880518 | 1.9242237858496105 | 1.4383698842540908 | False |
| 1000000 | Wmax | FAIL | NON_MONOTONIC_OR_UNDEFINED | 0.712527632370735 | None | None | True |

Ra6 Nuはmonotonic、p≈1.924、GCI≈1.43837%で既存1.5%内だが、fine-medium1.34024%>1%によりFAIL。Nu単独recordのneeds_320=falseは変更せず、W非単調によるgroup needs_320 YESと区別。Ra3/4/5速度差が小さくてもnon-monotonicをPASSにしない。Ra5 Uはformal PASSでもp≈0.529で全量2次漸近性を意味しない。

AC§8.2は速度非単調なら160²で打ち切らず320²と一般化Richardson/適切な不確かさ評価を要求する。現在全4Raが該当。formal Jの前にはtarget Ra6 refinementも必要だが、Ra6-onlyでは残る3Ra F_AとB coreを閉じない。320を1回追加してもF PASSは保証されず、以降のgrid集合/評価手順はfuture preregistrationで定義する。

## 8. Gate H contribution

Hはaccepted original betaΔT1e-3、Ra6 fine at9000と、perturbed betaΔT1e-4 at12000を同160格子で比較。Ra/Pr固定のbeta/10・g×10というjoint pathであり、betaだけの微分ではない。

| quantity | baseline | perturbed | relative_change_pct |
| --- | --- | --- | --- |
| Nu_bar_cavity | 8.868989455786025 | 8.86551246466168 | 0.039203915414242146 |
| Umax | 64.9147345963897 | 64.89920914350851 | 0.023916685445488674 |
| Wmax | 219.90026166168474 | 219.87596235012782 | 0.01105015127007929 |

epsilon_v `0.000949693061760976` → `0.0009026457665325413`、約4.954%改善。最大primary感度0.039204%は既存0.2%内、formal H PASS / result review SUPPORTED_WITH_LIMITATIONS。

**INFERENCE:** この160²・accepted steady・3主量について、1e-3→1e-4のEOS小パラメータ変更の影響が小さいというconfidenceを高める。診断transientをoriginal baseline条件で検討する有用な支え。空間/time/algorithm誤差と全過渡のmass/energyは検査していない。**H PASS != F PASS**。A–B gap縮小は診断的事実に留まり、B Ra6 unaccepted、work terms等の差、model×grid interaction、2点だけという限界からclassical limit・causal shareは未証明。

## 9. Formal vs scientific prerequisites

**Formal prerequisite:** AC§12/14のB core・A characterization・H PASSはbinding。F/G/K未達を小差・workflow完了・H PASSで免除しない。

**Scientific prerequisite:** この問いは「同じA model/grid/初期条件でtime-control変更によりobservable histories/final valuesやmass-energyがどれだけ変わるか」。A provenance、使用可能なRa6 baseline、過渡algorithm、cold initialization、dt/Co記録、inner収束・終端状態、discrete storage/flux/workの評価、診断ownershipが直接必要。完全B core/全Ra空間closureをこの問いの数学的前提とする必要はない。

**Project sequencing preference:** 過去workflowのB→A→H→J順序は、formal labelでは規範、開発の別問いでは研究優先度として別検討できる。今回提案はJ順序の例外・Gate waiverを付与せず、新しい診断ownershipを今後設計する。既存workflow Level1/2をformal statusへ変換しない。

Scientific question classifications: full B core scientifically required for **bounded within-A temporal/mass-energy question=NO**、B/A continuumモデル比較や検証済み対照には **PARTIALLY / stronger comparative foundation required**。full steady F scientifically required before fixed160 Co comparison=**NO**。粒子力/熱やgrid-independent transient accuracyを主張するなら空間評価は不可欠。総誤差はspatial + temporal + iterative + implementation/modelの相互作用を含み、共通grid誤差が差分で必ず完全相殺するとは仮定しない。

## 10. Need for 320² before transient work

**Before any separately owned bounded transient study: NO. Before formal J under frozen logic: YES**, and not sufficient. AC§8.2による全Ra F remediationが前提なので、target-onlyはformal closureの一部。

| option | scope | cases | information | information_value | formal_benefit | cost | limitation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 320-A | All four Route A Ra | 4 | Broad F remediation and uncertainty across matrix | MEDIUM for current objective; HIGH full formal scope | Necessary refinement evaluation for all current A non-monotonic groups; not sufficient for PASS/core | 4 refined cases;4x cells per160case; wall time unknown | No guarantee monotonicity; no B core closure or temporal/storage evidence |
| 320-B | Ra1e6 only | 1 | Highest target spatial value: Nu fm1.34024% and W non-monotonic | HIGH | Partial A F work; other three Ra and B remain blockers | 1 refined case; wall time unknown | Fixed160 temporal error remains distinct; refinement does not prove particle force/heat accuracy |
| 320-C | Selected Ra (candidate Ra1e6 + Ra1e5) | 2 illustrative, not registered | Target Ra6 plus low-order/oscillatory velocity context at Ra5 | HIGH Ra6; MEDIUM Ra5; selection depends thesis scope | Partial A F evidence; cannot establish all-Ra conjunction | More than target-only, less than all-four; wall time unknown | Not a new case list or execution contract; other blockers persist |
| 320-D | None before separately owned fixed160 transient | 0 | Prioritize temporal/storage/EOS questions with spatial limitations retained | HIGH direct transient relevance, no new spatial information | NONE; all F failures and needs_320 retained | No preceding refinement, future transient2–3series still required | No grid-independent transient claim; formal J remains forbidden |

320は102400cellsで160の25600cellsの4倍。メモリ/反復コスト増は予想されるがwall-clock、反復数、収束率を測定していないため4倍時間とは言わない。全4Ra追加はcell総数409600、target1は102400。これはgeometryコスト指標だけ。

320が直接減らせるのはtarget steadyの空間傾向・格子不確かさ、fixed160 baselineがどれだけshiftするかの解釈。time sensitivityそのもの、過渡のrho/energy storage consistency、Co履歴は測れない。さらに粒子surface/force/heatの局所resolutionを本cavity単相gridで検証したことにはならない。追加320でも単調性・core closure・grid-independent transientを保証しない。情報価値はRa6 HIGH、Ra5 MEDIUM、Ra3/4 LOW（現研究目的に対する周辺価値、formal重要度とは別）。

## 11. Need for Route B core before transient work

**Any separately owned fixed-grid A transient: NO. Formal J: YES.** 完全B coreを先に閉じなくても、within-A Co依存・EOS/solverrho・mass/energyの問いは定義できる。B Ra6 computed rowは既存のdiagnostic contextとしてのみ扱い、accepted temporal trajectoryやclassical transient referenceとして使わない。

B remediationはVerification claim・ABモデル差と離散化差の分離にHIGH value。一方、v6 steady Bの追加反復はv13 transient density-storageやvariable backward/PISO/PIMPLEを直接試験しない。B全closureの現在研究へのmarginal情報価値はMEDIUMで、Ra6 floor/G operator/複数320へ時間が広がるリスクがある。既存B failureを保存したまま診断研究へ進む合理性と、B core宣言不可は両立する。

## 12. Formal Gate J path

1. Route BのA/B/C既存PASSを維持し、D_Ra6 → E/F_Ra6、F_Ra3–5、G全Ra、I報告/K全要件closureを凍結基準で解決する。CORE成立を新しい正式証拠で確認する。
2. Route A全4Ra Fの必要追加格子・不確かさ評価とK/I成果物を閉じ、D/G・3比較・H実施報告を含むcharacterizationの全項を確認する。
3. H PASSを保持した上で、future formal Gate J契約を別taskで事前登録し、実装・algorithm・OQ-07評価法を固定する。現行v1.7はこの権限を含まない。
4. さらに明示RUN指示後、Ra6 fine cold/backward Co.5/.25、条件付.125を実施。Jの数値要件とmass/energy・成果物を評価する。全条件成立時だけdownstream label検討。

失敗の原因やgrid trendが変わらない可能性を残す。Ra6 A320のみ、B Dだけ、Hだけの解決ではformal pathは完了しない。

## 13. Diagnostic transient path

これは**研究concept**であり、case ID、実行commands、complete numerical settings、run budget、実行許可を含むcontractではない。

別ownership **DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION** は、Jの設計数値（Ra6、160²、rest/uniformT0、backward、Co .5/.25と条件付.125）をreferenceにできる。元のaccepted `A-Ra1e6-fine`, betaΔT1e-3 at9000を比較baselineにするのが現仕様と整合。H beta1e-4を新baselineへ無断置換しない。Co系列はcold独立初期値問題であり、steady場のwarm startでは過渡立上りの問いに答えない。

未来のprepare-only taskで必要なのは以下の事前固定・未解決確認:

- v13 fluid transient source/active terms、PISO outer1かPIMPLE複数outerか、pressure/rho/energy correctorsとinner convergence。既存steady設定をddtだけ変えて準備完了としない。
- backward初回history不足、variable-dt係数、initial dt/max dt/Co control、実測Coとdt履歴。Co target差を一定dt比・時間収束次数と同一視しない。
- 無次元時間 `t*=alpha0*t/L²`、比較時間/終端窓/定常到達、durationとcaps、出力sampling、条件付.125のtrigger・停止規則。最終steady値が揃っても過渡軌道は時間依存し得るため、共通t*にhistoryを比較する診断を設計する。
- discrete `ddt(rho_s)+div(phi)`のcell/volume-integral residual、closed-cavity total mass、壁面flux、EOSrhoとsolverrhoの更新時点/再同期差（OQ-07）。psi=0でpressureによるEOSmass調整ができないという既存監査の懸念を評価する。steadyのtiny epsilon_m/div(phi)だけでPASSにしない。
- energy accumulation、audited pressure/kinetic/gravity work、wall heat、solver discrete equation residualを同じsign/units/control volumeで記録する。過渡でhot=coldを全時刻に強制しない。final Gと全過渡budgetを分ける。
- accepted baselineとの同一定義final比較、原論文scalar/position実用比較、native massとreconstructed U divergence、局所fields・plots・health・runtime/input/field/script/referencehash、系列ごとのownership/seals。
- Existing J .5%/paper1%/A Gは設計referenceとして保存できるが、診断ownerの数値比較からFORMAL_J_PASSを付与しない。質量/energy許容値は根拠なしに作らず、既存仕様不足はUNRESOLVEDとしてfuture contract preparationで解決する。未解決のままRUN readiness YESにしない。

現時点のtechnical readiness **NO**、execution authorization **NO**。future diagnostic study後も `GATE_J=NOT_EXECUTED`, `DOWNSTREAM_TRANSIENT_READY=NO` を維持する。そのdataはalgorithm debugging、dt/arrival budget、observables/mass-energy design、後日のformal designに情報を与えるため無駄ではない。同一条件でもhistorical diagnosticを自動昇格しない。再利用可能性は将来authority・preregistration・input/method/hash適合の明示audit次第で、formal rerun不要とは今判断しない。

## 14. Roadmap comparison

| roadmap | work_required | formal_gain | scientific_gain | cost | thesis_relevance | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| A — Strict formal closure first | B D/E/F/G/K → A F/K/I/report closure → formal characterization → formal J contract and runs | HIGH if all closures PASS; preserves frozen logic | HIGH benchmark uncertainty; MEDIUM marginal gain for current transient question | VERY HIGH; unknown wall time and iteration count | HIGH methodology; slower access to main transient objective | Choose if formal completion is thesis deliverable; not first for current objective |
| B — Route A spatial refinement first | Ra6-only/selected/all A320 → F review → remaining A/B blockers → formal J | PARTIAL; Ra6 alone cannot close F_A all four or B core | HIGH target Ra6 spatial information; no temporal or transient storage data | HIGH; each320 has102400 cells vs25600 | HIGH if grid uncertainty/force resolution central | Second priority; Ra6 targeted has highest spatial value |
| C — Diagnostic transient study first | Prepare separate contract → explicit future RUN → fixed160 cold/backward Co histories/mass/energy review | NONE for J/core/characterization; no automatic promotion | HIGH direct Route A temporal/storage/EOS implementation information | MEDIUM/HIGH;2 series conditional3, wall time unknown | HIGH direct thermal→transient→moving-leaf pathway | RECOMMENDED, conditional on future contract and user decision |
| D — Defer transient; methodology development | Offline particle/FSI model requirements and literature/method planning, no coupled simulation | NONE | LOW fluid temporal information; MEDIUM conceptual model value | LOW simulation cost | MEDIUM/HIGH conceptual; fluid gap persists | Fallback if compute/time is unavailable or transient design remains unresolved |

全比較軸の評価（qualitative INFERENCE、実測時間予測ではない）:

| roadmap | formal_rigor | particle_coupling_relevance | compute_cost | implementation_cost | risk | time_efficiency |
| --- | --- | --- | --- | --- | --- | --- |
| A — Strict formal closure first | HIGH | Indirect spatial foundation then direct transient | Multiple B remediations + A/B 320 + 2–3 transient series | HIGH | HIGH detour; closure not guaranteed | LOW for near-term transient question |
| B — Route A spatial refinement first | HIGH if separate future preregistration | Spatial force/heat context; no resolved particle interfaces | 1 to4 A320 cases plus later formal closure and transient | MEDIUM/HIGH | MEDIUM/HIGH; may remain non-monotonic | MEDIUM spatial; LOW immediate temporal |
| C — Diagnostic transient study first | HIGH ownership/provenance discipline; formal verification incomplete | HIGH fluid prerequisite information; readiness remains NO | 2–3 independent160 transient series; smallerCo may cost more steps, ratio unmeasured | HIGH initial transient operators/algorithm audit | MEDIUM/HIGH OQ-07 and no time-resolved reference; bounded scope limits detour | HIGH expected information relevance; no measured runtime advantage |
| D — Defer transient; methodology development | Preserves existing status; no readiness claim | Method planning only, no force/heat validation | LOW/NONE fluid solver | LOW/MEDIUM planning | MEDIUM rework without fluid transient evidence | HIGH planning; LOW fluid uncertainty reduction |

Strict closureはformal claim価値HIGH、現在のfluid-transient問いへのmarginal value MEDIUM。diagnosticはdirect information HIGH、Ra6targeted320はspatial information HIGH。「formal J now / never transient」の二択ではなく、claimと問いの範囲を分けてCを設計し、A/Bを未解決のformal backlogとして残せる。

## 15. Thesis implications

修士研究の主目的はtea-leaf jumpingを支えるthermal convection、transient fluid、将来moving/deformable leafの相互作用。strict closureはdefensible methodology・空間uncertainty・formal benchmark completionを強める。複数Ra320とB floor/G調査は本題までの時間を増やし、成功/終了時刻は不明。

推奨Cは「固定160格子上のRoute A transient実装と時間制御・mass/energyの特性を、既存空間/RouteB限界とともに調べた」という将来claimの土台を直接得る。Table Vはsteady benchmarkであり、茶葉jump現象のValidationやtime-resolved流体の真解比較は提供しない。

formal Verification未完了と、次研究開発用diagnosticの科学的価値は両立する。論文ではB-paper Verification、A-B formulation、A-paper practical、H固定格子感度、diagnostic transientを別に記述する。Cの数値が良好でも全Verification、grid independence、Gate J PASSを主張しない。

## 16. Particle-coupling implications

FULL_FORMAL_VERIFICATION_READINESS=NO、MODEL_DEVELOPMENT_READINESS=CONDITIONAL、PARTICLE_COUPLING_READY=NO。未完了benchmarkを保ちながら、明確な問い・ownership・計測法を備えたfluid solver developmentを進める合理性はある。

fluid-only診断は将来time step、mass/energy、startup/force sampling等の必要情報を得る段階。粒子/物体モデルの正しさ、moving boundary conservation、force/heat transfer、leaf deformation、FSI/contact、実際geometry・Re/thermal条件での空間/時間精度とValidationは未評価。H/steady G/診断transientだけでparticle readinessを宣言しない。Dならoffline methodology planningに限り、coupled executionをreadyとしない。

## 17. Recommended research sequence

1. ユーザーが別ownershipによる診断経路を選択する。既存formal criteria/failures/core未付与を保持する。
2. 次single taskは診断契約の **準備だけ**。transientalgorithm、Co/history、arrival、OQ-07 mass/energy/許容値根拠、ownership/provenance/caps/STOP規則をreview可能にする。準備で不足が出たらexecution readiness NOを維持する。
3. 別途RUN指示と成立した契約が揃ったときだけfluid-only診断を実施し、その後結果review。J=NOT_EXECUTEDとformal predicates未成立を保存。
4. 得られた情報と修論claimに応じRa6targeted320を次のspatial課題として再優先化する。全formal closureがdeliverableなら他Ra A/B refinementとB remediation/K closureを別予算で計画する。
5. formal closureなしでJ名義の契約へ移行しない。粒子couplingにはさらに実条件と一致するfluid evidenceと独立のparticle/FSI検証が必要。

既存前提順序を研究scopeへ合わせて変更する必要が本当に生じた場合のみ、`REVIEW_ROUTE_A_ACCEPTANCE_CRITERIA_SCOPE` を将来別taskとして検討する。今回は変更しないし、推奨Cは変更を前提としない。

## 18. Unsupported claims

以下はいずれも非支持:

- H PASSがF PASSやB core、A characterizationを成立させる。
- fine-medium差が小さいので非単調Fを合格にする。
- B Ra6 paper近接・smallRwin・workflow closureがaccepted/CORE PASSを意味する。
- fixed160 Co感度がgrid-independent transient、完全な時間収束次数、初期過渡精度を証明する。
- steady Gやhot=coldが過渡のmass/energy蓄積・EOS再同期を保証する。
- beta/g2点・Bへの近接からclassical Boussinesq limit/causal mechanismを特定する。
- 320追加が単調性・全GatePASS・時間刻み精度・particleforce/heat精度を保証する。
- diagnosticを自動的にformal Gate Jへ昇格する、future rerun不要を今保証する。
- development readinessがparticle coupling readinessやtea-leaf現象Validationを意味する。
- 本review推奨が新contract/solver実行許可を与える。

## 19. Exact next task

**PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT** — 推奨 `gpt-6.1-sol / medium`。

別ownershipで、solverなしのprepare-only task。Jではないこと、現在のformal status保存、過渡algorithm・mass/energy evaluation・dt/arrival・STOP・source/output protectionを事前固定し、technical/execution readinessを独立判定する。今回そのcontractを作成しない。USER_DECISION_REQUIRED=YESは未来の研究経路選択に対する表示であり、今回のreview完了を保留するものではない。

Review conclusion/status:

```text
ROUTE_A_GATE_J_PREREQUISITE_REVIEW = COMPLETE
EFFECTIVE_CONTRACT_VERSION = 1.7
EFFECTIVE_CONTRACT_HASH_VERIFIED = YES
GATE_H_FORMAL_RESULT = PASS
GATE_H_RESULT_REVIEW = SUPPORTED_WITH_LIMITATIONS
BENCHMARK_CORE_PASS_UNDER_FROZEN_LOGIC = NO
ROUTE_A_CHARACTERIZED_UNDER_FROZEN_LOGIC = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
FORMAL_GATE_J_PREREQUISITES_SATISFIED = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
GATE_J_SCIENTIFICALLY_USEFUL = YES
FIXED_GRID_TRANSIENT_CHARACTERIZATION_SCIENTIFICALLY_JUSTIFIED = CONDITIONAL
DIAGNOSTIC_TRANSIENT_STUDY_CAN_PROCEED_WITHOUT_FORMAL_GATE_J_CLAIM = YES
TARGETED_320_REQUIRED_BEFORE_ANY_TRANSIENT_STUDY = NO
TARGETED_320_REQUIRED_BEFORE_FORMAL_GATE_J = YES
ROUTE_B_CORE_REQUIRED_BEFORE_ANY_TRANSIENT_STUDY = NO
ROUTE_B_CORE_REQUIRED_BEFORE_FORMAL_GATE_J = YES
STRICT_FORMAL_CLOSURE_INFORMATION_VALUE = MEDIUM
DIAGNOSTIC_TRANSIENT_INFORMATION_VALUE = HIGH
TARGETED_320_INFORMATION_VALUE_RA1E6 = HIGH
RECOMMENDED_RESEARCH_ROADMAP = DIAGNOSTIC_TRANSIENT_FIRST
RECOMMENDED_NEXT_STUDY_OWNERSHIP = DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
GRID_320_EXECUTED = NO
GATE_J_EXECUTED = NO
DIAGNOSTIC_TRANSIENT_EXECUTED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
CONTRACT_AMENDMENT_CREATED = NO
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
SOLVER_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
CONTINUATION_EXECUTED = NO
ROUTE_B_RERUN = NO
EFFECTIVE_CONTRACT_CHANGED = NO
ACCEPTANCE_CRITERIA_CHANGED = NO
FORMAL_STATUS_CHANGED = NO
GATE_J_TECHNICALLY_READY = NO
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = NO
DIAGNOSTIC_TRANSIENT_EXECUTION_AUTHORIZED = NO
FULL_FORMAL_VERIFICATION_READINESS = NO
MODEL_DEVELOPMENT_READINESS = CONDITIONAL
```
