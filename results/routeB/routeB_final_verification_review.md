# Route B Final Verification Review

開始HEAD: 69d715d61391f39a8e197fb7f83bd8b8ed1bf7cc（想定一致）。既存結果のみ。**COMPLETE_WITH_DOCUMENTED_LIMITATIONS**を推奨。computed12/12、accepted9/12。完全検証済み・全Hard Gate PASSを宣言しない。既存formal completion NO / BENCHMARK_CORE_PASS NOT_EVALUATEDを保持。

## Gate A–G

| Gate / purpose | status | evidence | limitation | 本線blocker / thesis |
|---|---|---|---|---|
| A / 環境・input・mesh・物性・Ra/Pr・hash | PASS (既存記録) | manifest preflight/generated_manifest; status; run_manifest | 歴史的binary digest保存なし。既存provenanceを引用、再監査なし。 | NO / Foundation v6設定とprovenanceを記述 |
| B / 方程式/solver対応 | PASS / ROUTE_B_AUDIT_PASS | docs/routeB_design.md:213,268–281,302 | 定常laminar/Newtonian/Boussinesq・零放射/源/MRF等の条件。粒子連成を含まない。 | NO / 既存source-to-equation audit結論を引用 |
| C / Ra=0伝導・Nu unit test | PASS | run_manifest statuses; B-COND metrics | 伝導極限のみ。高Ra/粒子連成保証ではない。 | NO / Nu≈1、U=0、線形温度場を報告 |
| D / 反復収束・QoI定常性・熱傾き | PASS 9/12; Ra1e6 FAIL 3/3 | current manifest; Ra1e6 post-matrix review | floor likely、機構UNKNOWN。coarse/medium熱傾きもFAIL。 | NO (限界開示) / Original維持、computed/accepted分離 |
| E / accepted fine Table V一致 | PASS Ra1e3–1e5; Ra1e6 NOT_EVALUATED | formal_Ra_gates; manifest E; reference CSV | Ra1e6はdiagnostic-only。実現象Validationではない。 | NO / formal/diagnosticを分離 |
| F / 3格子・order・GCI | FAIL Ra1e3–1e5; Ra1e6 NOT_EVALUATED | manifest F; criteria.md:238–278 | 速度極値非単調、p/GCI未定義。needs_320 YES保持。 | NO (320 deferred) / fine一致と漸近性不足を区別 |
| G / 保存則・対称性 | FAIL Ra1e3; others frozen NOT_EVALUATED | manifest Ra1e3 G; freeze JSON; metrics | tau UNRESOLVED、Candidate B PROVISIONAL。phi/Uは別演算子。 | NO (known limitation) / formal FAIL/未評価と診断を別記 |

Gate Aは既存Foundation v6環境・mesh/input・物性・Ra/Pr・hash/provenanceを引用。全Ra_actual=target、Pr=0.71。歴史的binary digest欠落は開示。新しい監査なし。

Gate Bは既存ROUTE_B_AUDIT_PASSを引用。native v6 solverは定常laminar/Newtonian/Boussinesq・零放射/源/MRF等の条件で原論文方程式に十分対応するという監査結論。QoI一致や粒子連成の代用証拠ではない。

Gate Cは既存B-COND（Ra=0、80²、3000反復）PASS。Nu_cavity=1、Nu0=1.0000394、Nuhalf=0.99996063、Nu1=1.0000394、最大無次元速度0、線形温度場最大誤差6.3283322e-06。伝導極限・温度場・Nu定義/壁後処理のunit test。再実行なし。

## Master matrix

全指定列・数値精度はCSV/JSON。E/Gはfineのみ（他レベルNOT_APPLICABLE）、F/needs_320はRa-group判定を併記。誤差は絶対相対[%]。

| case | grid | iter | computed | D | accepted | Nu_cavity | Nu0 | Umax | Wmax | Table V error % Nu/U/W |
|---|---|---:|---|---|---|---:|---:|---:|---:|---|
| B-Ra1e3-coarse | 40x40x1 | 3000 | YES | PASS | YES | 1.1187959 | 1.1186122 | 3.6477753 | 3.6889569 | 0.071187002 / 0.03356284 / 0.21755852 |
| B-Ra1e3-medium | 80x80x1 | 6000 | YES | PASS | YES | 1.1180443 | 1.1180014 | 3.6469992 | 3.6963024 | 0.0039621965 / 0.054830121 / 0.018870617 |
| B-Ra1e3-fine | 160x160x1 | 21000 | YES | PASS | YES | 1.1178641 | 1.1178584 | 3.6490796 | 3.6974359 | 0.012154518 / 0.0021820491 / 0.011791521 |
| B-Ra1e4-coarse | 40x40x1 | 3000 | YES | PASS | YES | 2.259326 | 2.2574217 | 16.118437 | 19.595222 | 0.72786624 / 0.36816999 / 0.11101353 |
| B-Ra1e4-medium | 80x80x1 | 6000 | YES | PASS | YES | 2.2484533 | 2.2479853 | 16.170187 | 19.624713 | 0.24312635 / 0.048292706 / 0.039315882 |
| B-Ra1e4-fine | 160x160x1 | 18000 | YES | PASS | YES | 2.2457202 | 2.2456111 | 16.181023 | 19.619331 | 0.12127689 / 0.018687583 / 0.011881343 |
| B-Ra1e5-coarse | 40x40x1 | 6000 | YES | PASS | YES | 4.6243637 | 4.6162878 | 34.81925 | 68.86509 | 2.3315701 / 0.2569824 / 0.40106465 |
| B-Ra1e5-medium | 80x80x1 | 9000 | YES | PASS | YES | 4.5474797 | 4.5455936 | 34.776471 | 68.562469 | 0.63022197 / 0.13380515 / 0.040139065 |
| B-Ra1e5-fine | 160x160x1 | 12000 | YES | PASS | YES | 4.5280628 | 4.5276511 | 34.74628 | 68.64693 | 0.20054801 / 0.046876844 / 0.083000864 |
| B-Ra1e6-coarse | 40x40x1 | 30000 | YES | FAIL | NO | 9.4348113 | 9.4023263 | 65.615132 | 222.67839 | 7.2137653 / 1.5242635 / 1.5127615 |
| B-Ra1e6-medium | 80x80x1 | 30000 | YES | FAIL | NO | 8.9838343 | 8.9765228 | 65.102993 | 218.30795 | 2.0890258 / 0.73184716 / 0.47959808 |
| B-Ra1e6-fine | 160x160x1 | 30000 | YES | FAIL | NO | 8.8651212 | 8.8633975 | 64.899513 | 219.87347 | 0.74001394 / 0.41700843 / 0.23407686 |

Ra1e4 coarseはB-SMOKE再利用。source_case_idを分離し、旧comparisonにないU/W誤差は保存QoIとcanonical CSVから算出。12metricsのmanifest hash一致。accepted9でOriginal residual条件PASS、Ra1e6はPLATEAU_OR_OSCILLATORY。全12は既存normal_exit=true、fatal_or_nan=false。

| Ra | D coarse/medium/fine | E | F | needs_320 | formal G |
|---|---|---|---|---|---|
| 1e3 | PASS/PASS/PASS | PASS | FAIL | YES | FAIL |
| 1e4 | PASS/PASS/PASS | PASS | FAIL | YES | NOT_EVALUATED_UNDER_FROZEN_REVIEW |
| 1e5 | PASS/PASS/PASS | PASS | FAIL | YES | NOT_EVALUATED_UNDER_FROZEN_REVIEW |
| 1e6 | FAIL/FAIL/FAIL | NOT_EVALUATED_DUE_TO_UNACCEPTED_FINE | NOT_EVALUATED_DUE_TO_UNACCEPTED_GRID | NOT_EVALUATED | NOT_EVALUATED_UNDER_FROZEN_REVIEW |

Ra1e6: computed YES、Original D FAIL、accepted NO、QoI stationarity STRONG、residual floor likely、MECHANISM UNKNOWN、heat MODERATE。coarse/mediumはresidual+heat trend FAIL、fineはresidualのみ。Original維持、追加反復は必須でない。解が誤りだともformally convergedだとも断定しない。

## Gate E

accepted fineのRa1e3–1e5はformal PASS。主要量<=1%・Umax_Z/Wmax_X位置誤差<=0.01の既存条件を維持。

| fine Ra | Nu error % | U error % | W error % | Umax_Z abs.error | Wmax_X abs.error | scope |
|---|---:|---:|---:|---:|---:|---|
| 1000 | 0.012154518 | 0.0021820491 | 0.011791521 | 0.0024296875 | 0.00022265625 | formal PASS |
| 10000 | 0.12127689 | 0.018687583 | 0.011881343 | 0.00097851562 | 0.0028261719 | formal PASS |
| 100000 | 0.20054801 | 0.046876844 | 0.083000864 | 0.0017285156 | 0.00032617188 | formal PASS |
| 1000000 | 0.74001394 | 0.41700843 | 0.23407686 | 0.0030273438 | 0.0026273437 | DIAGNOSTIC_ONLY: numeric checks satisfied |

Ra1e6 EはNOT_EVALUATED_DUE_TO_UNACCEPTED_FINE。数値条件は診断的に満たす。Nu0/half・local極値/位置は既存reviewの診断扱い。local Nu min誤差1.3502%は既存E hard conditionでない。原論文再読なし。

## Gate F

既存formal値を転記。差/GCIは[%]、未定義p/GCIをゼロ/PASSに置換しない。

| Ra | QoI | type | fine-medium % | p_obs | GCI % | F | reason |
|---|---|---|---:|---:|---:|---|---|
| 1000 | Nu_bar_cavity | monotonic | 0.016118674 | 2.060436 | 0.015248861 | PASS | Monotonic convergence; existing fine-medium and GCI thresholds applied. |
| 1000 | Umax | oscillatory | 0.057010926 | NOT_EVALUATED (undefined) | NOT_EVALUATED (undefined) | FAIL | Nonmonotonic or undefined/nonpositive observed order; no 320 run performed. |
| 1000 | Wmax | monotonic | 0.030658523 | 2.6959739 | 0.016784138 | PASS | Monotonic convergence; existing fine-medium and GCI thresholds applied. |
| 10000 | Nu_bar_cavity | monotonic | 0.12170186 | 1.992111 | 0.12259324 | PASS | Existing three-grid thresholds applied; no 320 run performed. |
| 10000 | Umax | monotonic | 0.066967774 | 2.2557101 | 0.053209657 | PASS | Existing three-grid thresholds applied; no 320 run performed. |
| 10000 | Wmax | oscillatory | 0.02743128 | NOT_EVALUATED (undefined) | NOT_EVALUATED (undefined) | FAIL | Nonmonotonic or undefined/nonpositive observed order; no 320 run performed. |
| 100000 | Nu_bar_cavity | monotonic | 0.42881398 | 1.9853642 | 0.43466369 | PASS | Existing three-grid thresholds applied; no 320 run performed. |
| 100000 | Umax | monotonic | 0.086887578 | 0.50283788 | 0.62509325 | PASS | Existing three-grid thresholds applied; no 320 run performed. |
| 100000 | Wmax | oscillatory | 0.12303781 | NOT_EVALUATED (undefined) | NOT_EVALUATED (undefined) | FAIL | Nonmonotonic or undefined/nonpositive observed order; no 320 run performed. |

Ra1e3 Umax、Ra1e4/1e5 Wmaxが非単調でFAIL。Ra1e5 Wmaxは68.86509→68.56247→68.64693、p/GCI未定義。Ra1e5 Umaxは既存F PASSだがp≈0.503で、全量の2次漸近性は確認していない。全主要量のfine-medium差は既存1%以内。fine一致とthree-grid asymptotic evidenceを分け、F FAILをfine解不正確と同義にしない。

Ra1e6 formal Fは未評価。以下DIAGNOSTIC_ONLY、Richardson/order/GCIを新規計算しない。

| QoI | trend | fine-medium % |
|---|---|---:|
| Nu_bar_cavity | MONOTONIC_TOWARD_REFERENCE | 1.3391024 |
| Umax | MONOTONIC_TOWARD_REFERENCE | 0.31353128 |
| Wmax | NON_MONOTONIC | 0.7120083 |

W値はreferenceを跨いで非単調だが絶対reference誤差は低下。Nu/Uは単調にreferenceへ近づく。

## 320² decision

**DEFERはformal要件免除ではない。** 既存criteria:276–278の320追加要件・needs_320 YES・F FAILを保った日程判断。各RaのQ1–Q5、scientific/verification value、cost、thesis necessityはJSON。

| Ra | Q1 fine一致 | Q2 最大fine-medium | Q3 F不足 | recommendation | Q4 gain / Q5 schedule |
|---|---|---:|---|---|---|
| 1000 | E PASS | 0.057010926% | Umax NON_MONOTONIC。p/GCI未定義。fine解が大誤差という意味ではない。 | **DEFER** | 速度極値の漸近性/不確かさ評価に価値。今の本線移行論旨に必須でない。 |
| 10000 | E PASS | 0.12170186% | Wmax NON_MONOTONIC。p/GCI未定義。fine解が大誤差という意味ではない。 | **DEFER** | 速度極値の漸近性/不確かさ評価に価値。今の本線移行論旨に必須でない。 |
| 100000 | E PASS | 0.42881398% | Wmax NON_MONOTONIC。p/GCI未定義。fine解が大誤差という意味ではない。 | **DEFER** | 速度極値の漸近性/不確かさ評価に価値。今の本線移行論旨に必須でない。 |
| 1000000 | E numeric条件diagnostic | 上記診断値 | formal F未評価、D未達 | **NOT_NEEDED** (現段階) | 320だけでD/floor解決保証なし。 |

320²は160²の4倍セル数、時間/反復数未知。formal F完了・速度極値不確かさ保証を主張するなら追加評価が必要だが、限定的benchmark根拠を報告して本線へ進む今の論旨には必須でない。320生成/実行なし。

## Gate G positioning

freeze維持: FROZEN_PENDING_POST_MATRIX_REVIEW、Ra1e3 formal FAIL、criteria modified NO、tau_mean UNRESOLVED、Candidate B PROVISIONAL。review後も解決していないためstatus名保持。

Ra1e3既存FAILはreconstructed_mass_divergence。他のheat/section/reconstructed_volume/温度・速度symmetry checksはPASS。native pressure-corrected face phiと再構成U divergenceは別演算子。rho0一定でepsilon_v=legacy epsilon_m。同値指標に異なる既存基準を適用したFAILをnative phiで置換しない。既存phi operator independent verification PASSはtau確定ではない。

A（未解決だから継続）は正式G解決に価値があるがscope/schedule costが高い。**B（known limitationとしてfreeze、一区切り）を推奨**。criteria変更・microcase追加/再解析・tau解決なし。診断的native closure/symmetryとformal FAIL/未評価を別記し、本線を止めないworkflow判断とする。

## Verified / unresolved

確認範囲: 既存方程式対応、伝導/Nu unit test、Ra1e3–1e5 accepted自然対流とfine一致、全12反復挙動、格子依存性（FAIL含む）、native continuity/symmetry診断。全Ra漸近性・formal保存則・全場収束を確認したとは言わない。

| 未解決 | 分類 | criticalとなる主張 | 本線blocker |
|---|---|---|---|
| Ra1e6 Gate D FAIL | DEFERRED | 全12 formal convergence/acceptance宣言 | NO |
| Gate F non-monotonic / undefined p,GCI | DEFERRED | 全Ra格子収束・速度極値の不確かさ保証 | NO |
| 320² follow-up | DEFERRED | formal Gate F completion | NO |
| Gate G / tau_mean / Candidate B | DEFERRED | 全Hard Gate PASS・正式保存基準完了宣言 | NO |
| floor mechanism UNKNOWN | NON_CRITICAL | 因果説明・残差緩和正当化 | NO |
| historical binary digest missing | NON_CRITICAL | 歴史的binary完全同一性のhash立証 | NO |

**Verification vs Validation:** 数値benchmark参照一致はcredibility evidenceで、茶葉ジャンピング・粒子/非球形相互作用そのものの物理Validationではない。連成保存性/精度にも独立した根拠が必要。

## Thesis structure / conclusion

1. benchmark定義と方程式対応
2. numerical conditions/provenance
3. Original Gate D、computed/accepted区別
4. 格子study・F FAIL・320未実施
5. Table V：formal EとRa1e6 diagnostic
6. 未解決D/F/G・floor mechanism
7. 限定的credibilityと研究移行、Verification vs Validation

Foundation v6の定常Boussinesqモデルについて、既存方程式監査とRa=0伝導試験を確認し、Ra=1e3–1e5の9ケースがOriginal Gate D、各fine解がGate Eを満たした。全12ケースを計算したがRa=1e6はformal未達で診断的結果として扱う。速度極値の非単調格子傾向とGate G基準は未解決として残し、全Gate合格とは宣言しない。制限下で研究次段階へ進む数値的根拠は得られたが、茶葉・粒子現象のValidationは別途必要である。

## Completion questions

- **Q1**: 研究移行の主要目的（方程式対応・伝導極限・自然対流QoI再現のcredibility evidence）は限定範囲で達成。全12/全Hard Gate PASSの正式目標は未達。
- **Q2**: YES。Ra1e3–1e5のD/E PASSと小さいfine-medium差を根拠に、320を今実行せず次段階へ進める。完全な格子不確かさ保証は主張しない。
- **Q3**: NO。formal FAIL/未評価とoperator差を開示する限り、G未解決は移行のcritical blockerでない。連成保存性は別途根拠が必要。
- **Q4**: NO。Ra1e6 FAILは完全合格宣言を阻むが、既存9ケースPASSを取り消さず限界付き一区切りを妨げない。
- **Q5**: 今の移行への増分価値はcostに見合わない。正式grid uncertaintyが論旨に必要なら320はdeferred。新規調査/計算を今開始しない。

**COMPLETE_WITH_DOCUMENTED_LIMITATIONS / CAN_BE_CLOSED YES**を推奨。移行前の追加solver不要。全formal PASSの未解決は残り、既存formal flags/core statusは更新しない。

次段階は1つ: **自然対流場と単一粒子の相互作用を扱う最小連成モデルの構築**。詳細設計/計算は今回行わず、方針はユーザー判断。

## Provenance / changes

current status/manifestと完了済みRa1e6 reviewを優先。completion_summaryはcoarse24000停止時の歴史的snapshot。12metrics hashとTable V誤差を照合。既存24入力hash不変、指定新規3ファイルのみ作成。既存criteria/accepted/needs_320/reports/cases/fields無変更。Git add/commit/pushなし。

## Final status

~~~text
ROUTE_B_FINAL_REVIEW = COMPLETE
COMPUTED_MATRIX_COUNT = 12/12
ACCEPTED_MATRIX_COUNT = 9/12
RA1E3_GATE_F = FAIL
RA1E3_NEEDS_320 = YES
RA1E3_320_RECOMMENDATION = DEFER
RA1E4_GATE_F = FAIL
RA1E4_NEEDS_320 = YES
RA1E4_320_RECOMMENDATION = DEFER
RA1E5_GATE_F = FAIL
RA1E5_NEEDS_320 = YES
RA1E5_320_RECOMMENDATION = DEFER
RA1E6_ORIGINAL_GATE_D = FAIL
RA1E6_GATE_E = NOT_EVALUATED
RA1E6_GATE_F = NOT_EVALUATED
RA1E6_320_RECOMMENDATION = NOT_NEEDED
GATE_G_INVESTIGATION_STATUS = FROZEN_PENDING_POST_MATRIX_REVIEW
GATE_G_BLOCKS_NEXT_RESEARCH_STAGE = NO
CRITICAL_UNRESOLVED_ISSUES = NONE_FOR_NEXT_STAGE; ALL_GATE_PASS_NOT_ESTABLISHED
DEFERRED_NONCRITICAL_ISSUES = Ra1e6 Gate D; Gate F/320; Gate G; floor mechanism UNKNOWN
ADDITIONAL_SOLVER_RUN_REQUIRED_BEFORE_NEXT_STAGE = NO
ROUTE_B_COMPLETION_STATUS = COMPLETE_WITH_DOCUMENTED_LIMITATIONS
ROUTE_B_CAN_BE_CLOSED = YES
NEXT_RESEARCH_STEP = 自然対流場と単一粒子の相互作用を扱う最小連成モデルの構築
FORMAL_CRITERIA_CHANGED = NO
ACCEPTED_STATUS_CHANGED = NO
SOLVER_EXECUTED = NO
USER_DECISION_REQUIRED = YES
~~~
