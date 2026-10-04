# Ra=1e6 post-matrix Gate D review

開始 HEAD: `1929734cdf7f691cb9c6133fab826502d40ab030`。既存結果のみを使用。computed **12/12**、accepted **9/12**。全3ケースは30000反復で正常終了、既存 fatal/NaN 検出フラグなし。正式判定・accepted・既存報告・ケース・field は変更しない。

**推奨: Option A — Original Gate D を維持。追加 Ra1e6 反復は必須としない。** 定常性を支持する診断を報告するが、残差停滞が無害であるとの誤差保証は得られていない。coarse/medium は residual と heat trend の2条件で FAIL、fine は residual のみ FAIL。

## Original Gate D と既存 Gate E

`Scripts/routeB/publish_matrix_case.py:16–25` と `Scripts/routeB/analyze_case.py:119–120,281–288,361` の実装を確認。

- 監視量: Nu_bar_0、Umax、Wmax（実装キー Vmax は legacy alias）。Nu_bar_cavity は現行 Gate D の監視量ではない。
- Rwin = (窓内最大−最小) / max(|窓内平均|, 1.0)。各監視量 <= 5e-4。
- 窓長 >= 200反復、samples >= 21。今回全ケース 29800–30000、10反復間隔21点。
- 最終 initial residual Ux/Uy/T/p_rgh がすべて有限かつ <= 1e-7。final residual と取り違えない。
- 熱不均衡 = |Nu_hot_B1−Nu_cold_B1| / ((Nu_hot_B1+Nu_cold_B1)/2)。窓内線形回帰傾き <= 0。絶対 heat imbalance の独立 hard threshold は Gate D にない。
- normal_exit、not fatal_or_nan を要求。既存の検出結果を用い、新たな log 全文検査は行っていない。

既存 Gate E (`publish_matrix_case.py:122–130`) は accepted fine を対象に、Nu_bar_cavity/Umax/Wmax の絶対相対誤差 <= 1%、Umax_Z/Wmax_X の絶対位置誤差 <= 0.01。今回は数値条件の診断的照合だけを行う。local Nu などへ新しい hard threshold を加えない。

## 3格子比較

残差は最終 initial residual。数値の全文精度と全 Table V 誤差は CSV/JSON に保存。

| 指標 | coarse | medium | fine |
|---|---:|---:|---:|
| 格子 | 40x40x1 | 80x80x1 | 160x160x1 |
| 最終反復 | 30000 | 30000 | 30000 |
| Original Gate D | FAIL | FAIL | FAIL |
| 残差分類 | PLATEAU_OR_OSCILLATORY | PLATEAU_OR_OSCILLATORY | PLATEAU_OR_OSCILLATORY |
| Ux residual | 1.54083007e-07 | 1.03102916e-08 | 6.98054626e-10 |
| Uy residual | 7.96842324e-08 | 7.40685695e-09 | 7.07940472e-10 |
| T residual | 4.03873499e-08 | 6.48264372e-09 | 1.71549886e-09 |
| p_rgh residual | 7.37512087e-07 | 3.14037898e-07 | 2.714749e-07 |
| Rwin Nu_bar_0 | 1.06979149e-07 | 1.64808198e-08 | 2.78912113e-09 |
| Rwin Umax | 1.50757618e-06 | 1.09653452e-07 | 3.64087504e-09 |
| Rwin Wmax | 1.15829068e-07 | 9.19551792e-09 | 8.47741822e-10 |
| 最大 Rwin / 5e-4 | 0.00301515235 | 0.000219306903 | 7.28175007e-06 |
| heat imbalance | 4.59208039e-08 | 4.68060814e-09 | 1.69550357e-09 |
| heat slope / iteration | 7.41812459e-11 | 9.78668292e-12 | -1.7493486e-12 |
| epsilon_phi mean | 7.39542145e-10 | 4.40807839e-10 | 3.95478642e-10 |
| epsilon_phi max | 5.96933705e-09 | 8.47621608e-09 | 4.99794215e-09 |
| reconstructed epsilon_v | 0.0164051276 | 0.00365010055 | 0.000902218244 |
| legacy epsilon_m | 0.0164051276 | 0.00365010055 | 0.000902218244 |
| temperature symmetry | 5.93240098e-08 | 8.3627878e-09 | 1.23677168e-09 |
| velocity symmetry | 4.12877982e-07 | 3.88789175e-08 | 5.59506275e-09 |
| Nu_bar_cavity | 9.43481135 | 8.98383427 | 8.86512123 |
| Umax | 65.6151315 | 65.1029928 | 64.8995125 |
| Wmax | 222.678394 | 218.307954 | 219.873471 |
| Table V Nu_bar_cavity 絶対相対誤差 [%] | 7.21376531 | 2.08902585 | 0.740013945 |
| Table V Nu_bar_0 絶対相対誤差 [%] | 6.63861083 | 1.80926409 | 0.526227362 |
| Table V Nu_bar_half 絶対相対誤差 [%] | 6.85675987 | 2.0175322 | 0.731872625 |
| Table V Umax 絶対相対誤差 [%] | 1.52426355 | 0.731847159 | 0.417008429 |
| Table V Wmax 絶対相対誤差 [%] | 1.51276148 | 0.479598084 | 0.234076858 |

## 残差、QoI、熱収支の解釈

coarse は Ux と p_rgh、medium/fine は p_rgh が基準を超える。grid refinement に伴い Ux/Uy/T の最終残差は低下し、p_rgh は 7.3751e-7 → 3.1404e-7 → 2.7147e-7 と低下するが、fine でも閾値の約2.71倍。grid-dependent level と整合するが floor の原因を特定していない。**MECHANISM = UNKNOWN**。

既存 checkpoint の15000–30000を使った範囲（連続時系列の極値ではない）:

| 格子 | Ux min–max | p_rgh min–max | p_rgh 最後/最初 |
|---|---:|---:|---:|
| coarse | 1.192279e-07–1.543157e-07 | 6.079278e-07–9.367683e-07 | 0.825813 |
| medium | 8.460206e-09–1.031029e-08 | 3.140379e-07–3.357792e-07 | 0.949911 |
| fine | 6.649710e-10–7.027961e-10 | 1.999009e-07–2.759741e-07 | 1.35805 |

coarse/medium の checkpoint は概ね同じ桁で変動する。fine は3000–12000に大きく減衰した後、15000–30000の圧力残差は持続的減衰を示さない。PLATEAU_OR_OSCILLATORY_FLOOR_LIKELY は経験的な挙動分類で、周期振動・不可避な下限・物理的非定常の証明ではない。

QoI stationarity は **STRONG**。最大 Rwin は閾値に対し coarse 0.3015%、medium 0.02193%、fine 0.0007282%（約332、4559、137330倍の余裕）。ただし監視量と200反復窓での結果であり、全場定常性や代数誤差の上限は証明しない。

熱収支支持は **MODERATE**。不均衡は全格子で極小だが、最終窓の coarse/medium 傾きは正で Original heat trend FAIL、fine は負で PASS。checkpoint により符号が変わる:

- coarse: 正傾き checkpoint [3000, 6000, 12000, 30000]、非正 [9000, 15000, 18000, 21000, 24000, 27000]。
- medium: 正傾き checkpoint [9000, 12000, 15000, 18000, 27000, 30000]、非正 [3000, 6000, 21000, 24000]。
- fine: 正傾き checkpoint [9000, 12000, 21000, 27000]、非正 [3000, 6000, 15000, 18000, 24000, 30000]。

最終窓の正傾きだけで全 trajectory の非定常や熱不均衡の持続的増加は断定しない。一方、小さい不均衡を理由に既存 slope 条件を無視しない。都合のよい過去 checkpoint を選び直して accept しない。

## Continuity、対称性、格子・参照比較

native continuity 支持は **STRONG**（保存 phi の離散閉鎖に限定）。epsilon_phi は pressure-corrected face phi の各セル向き付き総和 / cell volume を L / 最大セル速度で正規化した指標。epsilon_v は cell-centred U から再構成した別演算子の divergence。rho0 一定のため既存 legacy epsilon_m と epsilon_v は一致する。両者の差は演算子の差であり、epsilon_phi が小さいだけでは圧力残差が QoI に無害と証明できない。

epsilon_v は格子細分化で約4倍ずつ低下。epsilon_phi mean は低下するが max は medium で増え、単調ではない。対称性の180度回転 RMS defect は温度・速度とも低下し、定常解の対称性を支持する。これらは最終診断であり、continuity/symmetry の時間安定性を今回独立検証していない。Gate G の判定・threshold は変更しない。

格子傾向は **MODERATE / DIAGNOSTIC_ONLY**。Nu_bar_cavity と Umax は単調に参照値へ近づく。Wmax は222.6784 → 218.3080 → 219.8735で非単調、参照219.36を跨ぐが絶対誤差は1.5128% → 0.4796% → 0.2341%と減る。3格子とも unaccepted のため formal Gate F、Richardson、observed order、GCI は評価しない。

fine の参照一致は主要既存 Gate E 数値条件について **STRONG / DIAGNOSTIC_ONLY**。Table V の全値・位置比較:

| 量 | fine | reference | 絶対相対誤差 [%] または絶対位置誤差 |
|---|---:|---:|---:|
| Nu_bar_cavity | 8.86512123 | 8.8 | 0.740013945 |
| Nu_bar_0 | 8.86339747 | 8.817 | 0.526227362 |
| Nu_bar_half | 8.86339747 | 8.799 | 0.731872625 |
| Umax | 64.8995125 | 64.63 | 0.417008429 |
| Wmax | 219.873471 | 219.36 | 0.234076858 |
| Umax_Z | 0.853027344 | 0.85 | 0.00302734375 |
| Wmax_X | 0.0405273438 | 0.0379 | 0.00262734375 |
| Nu_hot_local_max | 17.8241761 | 17.925 | 0.562476212 |
| Nu_hot_local_max_Z | 0.0371450776 | 0.0378 | 0.000654922357 |
| Nu_hot_local_min | 0.975646289 | 0.989 | 1.35022356 |
| Nu_hot_local_min_Z | 1 | 1 | 0 |

既存 Gate E の3相対誤差・2位置誤差は数値的にはすべて範囲内。local Nu min の1.3502%誤差は残るが、既存 Gate E の hard condition ではない。formal Gate E PASS には変更しない。

## Q1–Q5

- **Q1**: 単なる反復不足の証拠は弱い。fine は初期に減衰したが、後半 15000–30000 では圧力残差の持続的減衰が見られない。
- **Q2**: 停滞・checkpoint 間の変動に整合する証拠は強い。ただし連続周期振動や数学的下限を証明せず、発生機構は UNKNOWN。
- **Q3**: 監視 QoI の定常性、小さい熱不均衡、native phi の閉鎖、対称性、格子・参照傾向は定常数値解としての利用を支持する。全場定常性・代数誤差の上限・Original Gate D PASS の証明ではない。
- **Q4**: 残差条件が Ra1e6 の監視 QoI に対して過度に厳しい可能性はある。ただし残差と QoI 誤差の対応は未確立で、安全な緩和幅は決められない。
- **Q5**: plateau 経路の検討理由は揃うが、再現可能な正式 acceptance amendment の採用を正当化する証拠は不足。Original 維持を推奨する。

## A / B / C の比較と推奨

| 案 | 科学的妥当性・限界 | 再現性・論文説明・bias |
|---|---|---|
| A: Original維持（推奨） | computed解の診断的有用性と formal未達を併記。十分定常な解を拒む可能性は残る。 | 既存ルールで再現可能。9/12 accepted と12/12 computedを明示し、結果合わせを避ける。 |
| B: residual単純緩和 | 例の1e-6は全3格子の残差を通すが、coarse/mediumのheat FAILは残る。緩和幅の誤差根拠がない。 | 数値ルールは再現可能でも結果に合わせたpost hoc選択。採用を推奨しない。 |
| C: plateau条件付き | 複数の根拠で慎重に診断できるが、plateau認定・熱許容・時間安定性・代数誤差の定義不足。 | 裁量を残すと再現性が弱い。Originalと別ラベルで説明できるがpost hoc設計であり、採用を推奨しない。 |

C を将来設計する場合の構造例（今回の amendment 推奨・適用ではない）: Primary は Original PASS。Alternative は **Original residual のみ FAIL**、既存 non-residual 条件すべて PASS、既存 history で plateau/変動かつ持続的減衰の証拠なしを要求し、continuity/symmetry・格子/参照は別記。現 final 窓で必要条件を満たし得るのは fine だけで、これも CONDITIONAL acceptance を決定した意味ではない。

C の定量的 plateau 認定や正の熱傾きの許容量が必要なら **THRESHOLD_UNRESOLVED**。残差1e-6、Rwin1e-5などを新しい採用閾値として定めない。推奨 A には新閾値は不要。

将来 amendment を採用するなら **POST_HOC_AMENDMENT = YES** と開示し、論文で Original基準 / Ra1e6のOriginal FAIL / plateau診断 / amendment理由・凍結条件 / amendment後判定を分離する。Ra1e6限定例外は結果選択biasを増す。全12ケースに同じalternativeをretrospectiveに別ラベルで再評価する方が整合的だが、今回その再評価を実施せず、既存PASS/FAIL・acceptedを消さない。

A を推奨する理由は、支持する診断を失わずに既存Verificationの未達も保存でき、再現性・論文説明が明確でpost hoc biasを最小化するため。今回 amendment を推奨・適用しないため **POST_HOC_AMENDMENT = NO**。

## 追加反復と次の行動

**NO_MORE_RA1E6_ITERATIONS**。追加反復が Original PASS をもたらすとの証拠は弱く、閾値の妥当性も反復延長だけでは解決しない。今回のレビューと診断的研究報告に追加solver runを必須とせず、研究本線を進める。これは未達基準を満たしたとの認定ではない。

次は Original Gate D 維持方針のユーザー判断。レビューは完了し、その判断を待って追加作業を開始しない。formal Gate D・accepted・Gate E/F/Gは変更なし。新規3ファイルのみ作成、入力11ファイルのSHA256を保存して不変を検証。Git add/commit/pushなし。

## 最終ステータス

```ini
RA1E6_THREE_GRID_REVIEW = COMPLETE
RESIDUAL_MECHANISM = PLATEAU_OR_OSCILLATORY_FLOOR_LIKELY
QOI_STATIONARITY_SUPPORT = STRONG
HEAT_BALANCE_SUPPORT = MODERATE
CONTINUITY_SUPPORT = STRONG
GRID_TREND_SUPPORT = MODERATE
REFERENCE_AGREEMENT_SUPPORT = STRONG
ORIGINAL_GATE_D_RA1E6 = FAIL
RECOMMENDED_POLICY = A_KEEP_ORIGINAL
POST_HOC_AMENDMENT = NO
NEW_NUMERICAL_THRESHOLD_REQUIRED = NO
FORMAL_GATE_D_CHANGED = NO
ACCEPTED_STATUS_CHANGED = NO
SOLVER_EXECUTED = NO
ADDITIONAL_RA1E6_SOLVER_RUN_REQUIRED = NO
NEXT_ACTION = KEEP_ORIGINAL_GATE_D
USER_DECISION_REQUIRED = YES
```
