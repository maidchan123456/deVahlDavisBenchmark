# de Vahl Davis 自然対流ベンチマーク合否判定基準

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| 文書ID | DVD-OF13-AC |
| 版 | 1.2 |
| 対象仕様 | `docs/benchmark_spec.md` 版1.2 |
| 対象 | Route B（原論文 Verification）および Foundation v13 Route A（特性評価） |
| 状態 | 受入条件は v1.1 から不変。現在の証拠・付与状況を更新 |
| 更新日 | 2026-10-03 |

### 変更履歴

| 版 | 日付 | 変更内容 |
|---|---|---|
| 1.0 | 2026-09-28 | Foundation v13 標準 route を主判定とする初版 |
| 1.1 | 2026-09-30 | Route B の原論文 Verification と Route A の特性評価を分離。v6 候補の別監査、初期圧力整合、A–B 比較および Gate H の役割を定義 |
| 1.2 | 2026-10-03 | 閾値・Hard/Diagnostic 区分・総合判定論理を変更せず、両 route の監査、Gate C、smoke/minimal implementation の実績と現在の上位ステータスを反映 |

本書は、計算を「動いた／動かなかった」ではなく、方程式、入力、数値誤差、保存則および基準解との一致で判定するための規範である。**Hard** 条件は一つでも不合格なら該当ステータスを付与しない。**Diagnostic** 条件は原因分析を必須とするが、それ単独ではコア不合格にしない。同じ Gate の共通閾値は route ごとに独立判定する。$G_B$ は「Gate G の Route B 判定」、$G_A$ は「Gate G の Route A 判定」を表す。

研究上の比較は、(1) **B 対原論文＝Verification**、(2) **A 対 B＝モデル・定式化差**、(3) **A 対原論文＝実用 benchmark 比較**と区別する。A 対原論文の誤差を純粋な数値誤差と呼ばない。

## 1. 判定ステータス

| ステータス | 意味 |
|---|---|
| `NOT_RUN` | 仕様のみで、実装または計算をまだ行っていない |
| `ROUTE_A_AUDIT_PASS` | v13 Route A のソース監査に合格。OQ-02 の初期圧力実装確認は別 Gate |
| `ROUTE_B_AUDIT_PASS` | 採用候補の該当版ソースで原論文式との対応を確認し、B の採用手段を確定 |
| `BENCHMARK_CORE_PASS` | **Route B のみ**で定常 de Vahl Davis Verification の全 Hard 条件に合格 |
| `ROUTE_A_CHARACTERIZED` | B コア合格を前提に、A の健全性・格子・保存と3種類の比較・Gate H の実施報告が完了 |
| `DOWNSTREAM_TRANSIENT_READY` | B コア合格、A 特性評価、Gate H 合格、A 非定常 Gate J 合格 |
| `FAIL` | 当該 route・当該段階の必須条件を満たさない、または証拠不足。別 route の合格を自動的に取り消さない |

### 1.1 現在の付与状況（2026-10-03）

以下は現在の証拠を v1.1 から不変の定義に適用した結果である。「未付与」は、必要な full-matrix 段階をまだ実行・判定していないことを意味し、実施済みの必須条件に対する `FAIL` とは区別する。

| ステータス | 現在値 | 根拠 |
|---|---|---|
| `ROUTE_A_AUDIT_PASS` | **付与** | `openfoam_design.md` は v13 の continuity、momentum、energy、transport、$p_{rgh}$、pressure reference、heat flux、laminar/active scheme をローカルソースまで追跡し、古典式との差も明示する。OQ-02 は定義上 Gate A の別確認であり、`routeA_implementation.md` で cell/patch とも実測済み |
| `ROUTE_B_AUDIT_PASS` | **付与** | `routeB_design.md` が Foundation v6 ソースで Gate B の各項を確認し、所定条件下の採用を確定 |
| `BENCHMARK_CORE_PASS` | **未付与** | B-COND/B-SMOKE は完了したが、Route B の4 Ra × 3 grids、Gate E/F、formal fine-grid Gate G、Gate K が未実施 |
| `ROUTE_A_CHARACTERIZED` | **未付与** | 前提の `BENCHMARK_CORE_PASS` に加え、A の full matrix、formal D/F/G/K、3比較、Gate H 実施報告が未完了 |
| `DOWNSTREAM_TRANSIENT_READY` | **未付与** | `ROUTE_A_CHARACTERIZED`、Gate H PASS、Gate J がいずれも未成立 |

minimal implementation の実施状況は次のとおり。これらは上表の上位ステータスを代替しない。

| 証拠 | Route A | Route B |
|---|---|---|
| ソース Gate B | PASS | PASS |
| minimal-case Gate A | OQ-02、版・入力・mesh を A-COND/A-SMOKE で確認 | 版・入力・mesh・kinematic pressure・`alphat=0` を B-COND/B-SMOKE で確認 |
| Gate C | A-COND PASS | B-COND PASS |
| coarse smoke | A-SMOKE PASS | B-SMOKE PASS |
| minimal implementation | PASS | PASS |

## 2. 誤差と規格化の定義

### 2.1 基準値誤差

非零の原論文値 $\phi_{ref}$ に対し、

$$
E_{ref}(\phi)=\frac{|\phi-\phi_{ref}|}{|\phi_{ref}|}
$$

とする。百分率表示では100を掛ける。位置は絶対誤差

$$
E_{pos}=|s-s_{ref}|
$$

を用いる。$s$ は $X$ または $Y$ で、範囲は0から1である。

### 2.2 格子間差

fine 値 $\phi_f$ と medium 値 $\phi_m$ に対し、

$$
E_{fm}=\frac{|\phi_f-\phi_m|}{|\phi_f|}
$$

とする。分母が実質ゼロの量には、この相対誤差を適用せず、別途絶対許容値を定める。

### 2.3 反復定常性

最終200反復、または実装上これより長い監視窓について、比較量 $\phi$ の相対レンジを

$$
R_{win}(\phi)=\frac{\max(\phi)-\min(\phi)}{\max(|\overline\phi|,\phi_{scale})}
$$

とする。$\phi_{scale}$ はゼロ除算防止のため、監査時に量ごとに定めて記録する。単に残差が下がったことではなく、$\overline{Nu}$、$U_{max}$、$V_{max}$、壁面熱収支が定常であることを確認する。

### 2.4 Route 間差（Diagnostic）

同条件の非零の B の量 $Q_B$ に対し $D_{AB}(Q)=|Q_A-Q_B|/|Q_B|$ とする。位置は絶対差を用いる。$Q_B\simeq0$ の規格化は計算前に固定する。平均 Nu、$U_{max}$・位置、$V_{max}$・位置、局所 Nu、保存量、対称性を比較する。**A–B 差に Hard な一致閾値を設けない**。両 route の格子・反復・後処理誤差を併記し、差をモデル・定式化差と解釈できる範囲を限定する。

## 3. Gate A — 出所、版、入力の再現性（Hard）

各 route で全項目を満たすこと。実行版の出所を必ず確認する。Route B は Gate B の別監査に合格した Foundation v6 `buoyantBoussinesqSimpleFoam` を採用済みであるが、今後の各実行ケースでも版・build・入力の一致を再確認する。

- [ ] Route A は **OpenFOAM Foundation v13**、Route B は Gate B で採用確定した Foundation の版・実装である。OpenCFD/ESI fork や版違いを同一 route に混在させていない。
- [ ] OpenFOAM の版、ビルド情報、実行環境、ホスト、実行日時を manifest に保存している。
- [ ] 各ケースの入力辞書と格子のハッシュまたは同等の一意な識別情報を保存している。
- [ ] 実際に読み込まれた route 固有の入力と、監査で定義した参照値 $L,\rho_0,T_0,T_h,T_c,\beta,\mu,Pr,g$ の対応から $\nu_0,\alpha_0,Pr,Ra,\beta\Delta T$ を再計算している。v6 候補がこれらを同名・同形式で読むとは仮定しない。
- [ ] 再計算した $Pr$ と目標値0.71、各 $Ra$ と目標値の相対差が $10^{-10}$ 以下である。
- [ ] 4つの物理壁と2つの前後面の名前、種類、面積、法線方向を機械可読な記録に残している。
- [ ] 40²、80²、160² の面内セル数と奥行き1セルを確認している。
- [ ] mesh check に fatal error がなく、格子が構造・等間隔・直交であることを記録している。
- [ ] front/back は二次元用 `empty` であり、面外速度・面外勾配が導入されていない。
- [ ] Route A の初期場 $\boldsymbol u=0,T=T_0,\rho=\rho_0,p_{rgh}=0$ と $p=\rho_0gh+p_{Ref}$ が、v13 の初期化後の場および基準 cell/value と整合している。`pRefValue` と $p_{Ref}$ を混同せず、初期場と確認方法を記録している（OQ-02）。Route B の初期圧力は採用版の監査結果に従う。

**現在の証拠:** A-COND/A-SMOKE と B-COND/B-SMOKE の個別ケースで上記の入力・版・mesh を manifest に保存した。Route A OQ-02 は internal cell と4物理壁で確認済み。ただし40²/80²/160²の full matrix 全体の Gate A は未完了である。

## 4. Gate B — 方程式監査（Hard）

**Route B の採用前 Hard 監査:** 実際に用いる Foundation v6 のローカル公式ソースを read-only で追跡する。`buoyantBoussinesqSimpleFoam` という名前だけで適合と判定しない。監査結果はソースの版・ファイル・該当処理・式・入力辞書・後処理を対応表にし、設計記録へ残す。

- [ ] 体積流束と連続式が $\nabla\cdot\boldsymbol u=0$ に対応する。
- [ ] 慣性、移流、粘性の係数に温度依存密度が入り込まず、密度変化は浮力項だけに現れる。
- [ ] 定物性の $T$ 対流拡散式を直接解き、$\alpha_0$ と $Pr$ が計画値となる。
- [ ] $p_{rgh}$・$gh$・圧力基準・浮力符号が $y$ 上向き、$g_y<0$ と整合する。
- [ ] 定常 SIMPLE の連成、laminar、放射・体積発熱・粒子結合の無効化、全 active scheme を確認する。
- [ ] 壁面熱流束の符号、単位、積分値、面積平均値、独立な Nu 算出経路を確認する。
- [ ] 原論文式との差が残るなら列挙し、その差が主 Verification に許容できるかを採用前に判断する。

満たせない候補は B として採用しない。必要なら最小代替実装を別途設計し、ユーザーの実装指示を得る。v13 新規 solver を初めから必須としない。

**Route A の Hard 監査:** 既存 `docs/openfoam_design.md` の v13 ソース位置と式対応を確認し、連続式・運動量・エネルギー・輸送・$p_{rgh}$・圧力基準・熱流束・定常連成・laminar と active scheme の設計を追跡可能にする。密度重み付き連続式・運動量、局所密度依存の輸送、運動エネルギー・圧力仕事・重力仕事を含むエネルギー差を明記する。初期場の OQ-02 は Gate A の実装時 Hard 確認とする。**OQ-03 の A–B 非同一性は監査不合格や実装停止の理由にせず、比較研究の対象とする**。A の監査は B の式監査の代わりにならない。

**現在の証拠:** `routeB_design.md` の Gate B checklist は全項をソース上で満たし、`openfoam_design.md` は Route A 要件と原論文式との差を全て追跡する。したがって `ROUTE_A_AUDIT_PASS` と `ROUTE_B_AUDIT_PASS` を付与する。この判定は計算 Gate の合格を意味しない。

## 5. Gate C — 純熱伝導単体試験 $Ra=0$（Hard）

両 route で別々に、定常解析と後処理の符号・規格化を対流から切り離して確認する。A の合格は B の合格の代わりにならない。

解析解は

$$
\boldsymbol U=0,\qquad \theta=1-X,\qquad \overline{Nu}=1
$$

である。少なくとも medium 格子で次を満たすこと。

| 判定量 | 許容値 |
|---|---:|
| 高温壁 $|\overline{Nu}_h-1|$ | ≤ 0.001 |
| 低温壁 $|\overline{Nu}_c-1|$ | ≤ 0.001 |
| 2つの独立な Nu 算出経路の差 | ≤ 0.1% |
| $\max|\boldsymbol U|L/\alpha$ | ≤ $10^{-6}$ |
| 全 cell 中心での $\max|\theta-(1-X)|$ | ≤ $10^{-4}$ |

壁面熱流束の符号を絶対値で処理してこの試験を通してはならない。高温側から低温側へ向かう熱輸送が正になる変換を明文化する。

**現在の判定:** A-COND と B-COND は、それぞれ上表の全 Hard 条件に合格した。実測値は各 implementation record と `results/route*/minimal_test_summary.csv` に保存する。

## 6. Gate D — 各計算の健全性と定常収束（Hard）

Route B の12主計算、Route A の12主計算、および A の Gate H 感度計算を、それぞれ独立に判定する。$Ra=0$ と smoke test も正常終了・入力整合・収束を確認する。各該当計算で次を満たすこと。

- [ ] 実行が正常終了し、NaN、Inf、floating-point exception、発散警告、未処理の fatal error がない。
- [ ] 初期条件、境界条件、物性、重力、格子が manifest と一致する。
- [ ] 最終200反復以上で $\overline{Nu}_h,U_{max},V_{max}$ の $R_{win}\le5\times10^{-4}$。
- [ ] 同じ窓で熱収支不釣合いが増加傾向にない。
- [ ] 最終の正規化残差は、速度・温度／エネルギー・圧力の全てで $10^{-7}$ 以下を目標とする。アルゴリズム上この定義を直接適用できない場合、同等以上の収束証拠を route 別の設計記録に定義し、計算前に固定する。
- [ ] 反復上限到達だけを正常収束として扱っていない。
- [ ] 数値安定化、緩和または solver tolerance を変更したケースは、その変更を記録している。

残差に合格しても比較量が定常でなければ不合格とする。逆に、残差形式が異なることを理由に、比較量・保存量の監視を省略してはならない。

**現在の判定:** A-COND/A-SMOKE/B-COND/B-SMOKE は各ケースの正常終了、200反復窓、残差、熱収支を確認し、minimal/smoke 範囲で PASS。ただし両 route の12主計算に対する formal Gate D は未実施である。

## 7. Gate E — 原論文基準値との一致（Hard）

`benchmark_spec.md` 3.6の基準値を使用する。**Route B の主 Verification の Hard 条件**として、各 $Ra$ の **fine 160²** 解について、全ての主比較量が次を満たすこと。Route A でも同じ基準値と誤差を報告するが、A の結果は practical benchmark comparison であり、B のコア合格条件を代替せず、A の特性評価ステータスにこの閾値への合格を要求しない。

| 判定量 | 許容値 |
|---|---:|
| $E_{ref}(\overline{Nu})$ | ≤ 1.0% |
| $E_{ref}(U_{max})$ | ≤ 1.0% |
| $E_{ref}(V_{max})$ | ≤ 1.0% |
| $U_{max}$ の位置誤差 $|Y-Y_{ref}|$ | ≤ 0.01 |
| $V_{max}$ の位置誤差 $|X-X_{ref}|$ | ≤ 0.01 |

判定規則:

1. 4つの $Ra$ の全てで、3主量を個別に判定する。
2. 複数量の平均誤差で、一つの不合格を相殺しない。
3. 基準値の表示桁より細かい差に物理的意味を付与しない。
4. 原論文自身の不確かさがあるため、1%以内の一致を「厳密解に対する1%精度」と言い換えない。

## 8. Gate F — 格子収束と離散化誤差（Hard）

### 8.1 fine–medium 差

各 route の4つの $Ra$ の $\overline{Nu},U_{max},V_{max}$ 全てについて

$$
E_{fm}\le1.0\%
$$

を満たすこと。

### 8.2 3格子の収束性

各 route を別々に評価する。B の合格は主 Verification の Hard 条件、A の合格は信頼できる A–B 特性評価の Hard 条件である。A の格子収束が不十分な場合、モデル差と離散化誤差を分けられないため `ROUTE_A_CHARACTERIZED` を付与しない。

coarse、medium、fine をそれぞれ $\phi_3,\phi_2,\phi_1$、細分化比を $r=2$ とする。単調収束する量について観測次数を

$$
p_{obs}=\frac{\ln| (\phi_3-\phi_2)/(\phi_2-\phi_1) |}{\ln r}
$$

とし、保守的な安全係数 $F_s=3$ を用いて

$$
GCI_{fine}=F_s\frac{|(\phi_1-\phi_2)/\phi_1|}{r^{p_{obs}}-1}
$$

を評価する。

| 判定量 | 許容値 |
|---|---:|
| $GCI_{fine}(\overline{Nu})$ | ≤ 1.5% |
| $GCI_{fine}(U_{max})$ | ≤ 2.0% |
| $GCI_{fine}(V_{max})$ | ≤ 2.0% |

追加規則:

- $\overline{Nu}$ は3格子で単調収束することを必須とする。
- 速度極値が非単調、振動収束、または漸近域外と判断される場合、160²で打ち切らず320²を追加し、一般化 Richardson 解析または適切な不確かさ評価を行う。
- $p_{obs}$ が数値的に未定義、負、または著しく不合理な場合、GCIを形式的に算出して合格にしない。
- 格子品質の良好さを、格子収束の代用にしない。

## 9. Gate G — 保存則と対称性（Hard）

両 route の各 $Ra$ の fine 解をそれぞれ判定する。B の合格は主 Verification の Hard 条件、A の合格は `ROUTE_A_CHARACTERIZED` の Hard 条件である。

### 9.1 熱収支

高温壁と低温壁の平均 Nusselt 数を正の熱輸送方向へそろえ、

$$
\epsilon_Q=
\frac{|\overline{Nu}_h-\overline{Nu}_c|}
{(\overline{Nu}_h+\overline{Nu}_c)/2}
\le0.2\%.
$$

内部断面 Nu を算出した場合、全評価断面の最大偏差は壁面平均値に対して0.5%以下とする。

### 9.2 質量・体積保存

速度ピークを $U_p=\max|\boldsymbol u|$ とし、体積平均を $\langle\cdot\rangle_V$ とする。

$$
\epsilon_m=\frac{L\langle|\nabla\cdot(\rho\boldsymbol u)|\rangle_V}
{\rho_0 U_p}\le10^{-6},
$$

$$
\epsilon_v=\frac{L\langle|\nabla\cdot\boldsymbol u|\rangle_V}
{U_p}\le2\times10^{-3}.
$$

離散 divergence の定義、境界 face の扱い、体積重みを route ごとに固定して記録する。B が定数 $\rho_0$ を使うと監査で確認された場合は $\epsilon_m=\epsilon_v$ に対応するため、両基準を満たすことを確認する。A では両者を別々に評価する。$U_p$ がゼロとなる $Ra=0$ では Gate C の絶対速度基準を用いる。

**coarse smoke の diagnostic:** A-SMOKE の再構成 $\epsilon_v=4.3650864\times10^{-3}$、B-SMOKE の再構成 $\epsilon_v=\epsilon_m=4.3054223\times10^{-3}$ は上記 fine-grid 閾値を超える。これは coarse case の診断であり formal Gate G failure ではない。A の補正後 mass flux からの $\epsilon_m=2.8332\times10^{-11}$、B の補正後 volume flux からの $\epsilon_\phi=4.2984\times10^{-11}$ と、再構成 U divergence を混同しない。formal Gate G は各 $Ra$ の fine 解で未実施である。

### 9.3 中心対称性

180°回転対応点で

$$
e_\theta=\theta(X,Y)+\theta(1-X,1-Y)-1,
$$

$$
\boldsymbol e_U=\boldsymbol U(X,Y)+\boldsymbol U(1-X,1-Y)
$$

を作る。補間・体積重み付き L2 相対誤差は、温度と速度の双方で0.2%以下とする。ゼロ割を避ける規格化は設計書で固定する。

## 10. Gate H — Route A の Boussinesq 小パラメータ感度（特性評価・下流判定）

Foundation v13 Route A に必須の実施・報告項目である。**既存の 0.2% 閾値は維持する**が、その合格は B の `BENCHMARK_CORE_PASS` や A の `ROUTE_A_CHARACTERIZED` の条件にしない。下流の `DOWNSTREAM_TRANSIENT_READY` では Hard とする。A に対する感度不合格は原因を調べ、A の適用範囲に明記する。

- 条件: $Ra=10^6$、fine 格子。
- 基準: $\beta\Delta T=10^{-3}$。
- 感度条件: $\beta\Delta T=10^{-4}$。$Ra$ と $Pr$ を固定するため、$\beta$ を1/10、$g$ を10倍とする。
- 空間スキーム、solver 設定、格子、温度差、他の物性は同一とする。

次の相対差が全て0.2%以下であること。

- $\overline{Nu}$
- $U_{max}$
- $V_{max}$

加えて、$\epsilon_v$ が $\beta\Delta T$ の低下に伴い減少するか、少なくとも悪化しないことを確認する。

この試験が測るのは **A の観測量の $\beta\Delta T$ 感度**である。$\beta\Delta T$ の低下で差が小さくても A と B の一致を証明しない。A のエネルギー式には小パラメータで消失すると限らない項がある。$\epsilon_v$ が改善しない、または観測量の差が0.2%を超える場合は、連続式・運動量・エネルギー・後処理を切り分け、A–B と A–原論文の比較へ影響を記録する。B のコア合否には波及させない。

## 11. Gate I — 局所量と場の診断（Diagnostic）

局所 Nusselt 数の最大・最小は角部と離散化の影響を強く受けるため、主 Hard 判定と分ける。B と A を別々に全て報告し、A–B の局所分布差も記録する。

| 判定量 | 診断目安 |
|---|---:|
| $Nu_{max}$ の基準値相対誤差 | ≤ 3% |
| $Nu_{min}$ の基準値相対誤差 | ≤ 3% |
| 各極値位置の絶対誤差 | ≤ 0.02 |

目安を超えた場合は、少なくとも以下を切り分ける。

1. 壁 face 勾配と補間方法
2. 角部の境界条件離散化
3. 格子解像度
4. 対流・勾配スキーム
5. 定常未収束

温度等高線、流線、中心線速度、局所 Nu 分布に、非物理的振動、左右上下の取り違え、対称性破れがないことを目視でも確認する。目視のみで合格判定はしない。

## 12. Gate J — 非定常拡張（`DOWNSTREAM_TRANSIENT_READY` のみ Hard）

この Gate は `BENCHMARK_CORE_PASS` には不要だが、将来の茶葉・物体運動との **Route A 非定常連成**へ進む前には必須とする。B の主 Verification、A の特性評価、Gate H 合格の後に実施する。

- [ ] $Ra=10^6$、fine 格子、静止・一様 $T_0$ 初期条件から開始している。
- [ ] 二次精度 backward 時間離散を使用している。
- [ ] 最大 Courant 数目標 0.5 と0.25の2系列を実施している。
- [ ] 2系列の最終 $\overline{Nu},U_{max},V_{max}$ の相対差が全て0.5%以下である。
- [ ] 0.5%を超えた場合、最大 Courant 数0.125を追加し、最も細かい2系列で再判定している。
- [ ] 最終値が Gate E と同じ原論文値との1%基準および Gate G の Route A 保存基準を満たす。ここでの原論文比較は A 非定常計算の実用比較であり、B の Verification 判定ではない。
- [ ] 定常到達判定を無次元時間履歴で示している。
- [ ] 初期過渡を含む単純平均で最終値の誤差を隠していない。

全項目合格し、前提ステータスと Gate H 合格が揃った時のみ `DOWNSTREAM_TRANSIENT_READY` とする。

## 13. Gate K — 成果物と追跡可能性（Hard）

`BENCHMARK_CORE_PASS` の宣言には **Route B の**次の証拠が必要である。`ROUTE_A_CHARACTERIZED` には A の対応する証拠と、3種類の比較を分離した表・解釈が必要である。採用済み v6 Route B の監査記録を v13 設計書の結論だけで代替しない。

| 成果物 | 必須内容 |
|---|---|
| `docs/openfoam_design.md` と Route B の監査記録 | A の v13 監査に加え、採用 B の該当版ソース・方程式・辞書・スキーム・後処理を追跡できること |
| `results/run_manifest.json` | route ごとの版、環境、ケースID、入力ハッシュ、物性、無次元数、格子、実行状態 |
| `results/benchmark_summary.csv` | route ごとの4 Ra × 3格子の主量、基準値、誤差。B の Verification 合否と A の実用比較を分離 |
| `results/route_comparison.csv` | 対応する A–B の主量・位置・局所 Nu・保存・対称性、差と解釈。A–B Hard 閾値は設けない |
| `results/grid_convergence.csv` | route ごとの3格子値、差、収束型、$p_{obs}$、GCI、追加格子の有無 |
| `results/conservation.csv` | route ごとの壁面熱収支、断面熱収支、質量・体積保存、対称誤差 |
| `results/figures/` | route ごとの温度、流れ、中心線速度、局所 Nu、格子収束図 |
| 実行ログ | 全ケースの収束履歴と異常の有無 |

各表の各行は最低限、`case_id`, `Ra_target`, `Ra_actual`, `Pr_actual`, `grid`, `route`, `status`, `source_time_or_iteration`, `method_version` を持つこと。数値の手入力だけで出所が追えない表は受け入れない。

## 14. 総合判定手順

1. **完了:** v13 Route A と Foundation v6 Route B を別々にソース監査し、route 別 audit status を付与する。
2. **完了:** A の minimal Gate A（OQ-02 を含む）・C と $Ra=10^4$ coarse smoke test を行う。この先行計算は Verification 合格の証拠としない。
3. **完了:** B の minimal Gate A・C と $Ra=10^4$ coarse smoke test を行う。
4. **次段階:** B の12主計算で Gate D、E、F、G、K を量・Ra ごとに判定し、Gate I を診断する。全 Hard 合格時のみ `BENCHMARK_CORE_PASS` とする。
5. A の12主計算で Gate D、F、G、K を判定し、Gate E 相当の原論文値差と Gate I を報告する。A–B の対応比較を実施する。
6. A の Gate H 感度試験を行い、数値閾値への合否とモデル差への解釈を報告する。B コア合格と A の必須評価が揃った場合に `ROUTE_A_CHARACTERIZED` とする。
7. 下流研究が必要な場合のみ、Gate H 合格を確認して A の Gate J を実施し、合格時に `DOWNSTREAM_TRANSIENT_READY` とする。

### コア合格の論理式

$$
\texttt{BENCHMARK\_CORE\_PASS}
=A_B\land B_B\land C_B\land D_B\land E_B\land F_B\land G_B\land K_B.
$$

Gate I は両 route で報告・原因分析を行う Diagnostic である。B の合格に Gate H を含めない。A の特性評価と下流非定常の論理は次のとおり。

$$
\texttt{ROUTE\_A\_CHARACTERIZED}
=\texttt{BENCHMARK\_CORE\_PASS}\land A_A\land B_A\land C_A\land D_A\land F_A\land G_A\land K_A\land (\text{3比較を分離・報告})\land (H\text{を実施・報告}),
$$

$$
\texttt{DOWNSTREAM\_TRANSIENT\_READY}
=\texttt{ROUTE\_A\_CHARACTERIZED}\land H_{pass}\land J_A.
$$

ここで Gate A の OQ-02 は A の実装時 Hard 条件、Gate B の v6 候補監査は B の採用前 Hard 条件である。H の 0.2% 閾値を超えても A の観測結果と原因を報告すれば特性評価は完了し得るが、下流非定常準備には合格が必要である。A の E 相当の誤差および A–B 差は数値を省略できないが、Hard な一致条件にはしない。

## 15. 不合格時の扱い

- 不合格を削除、平均化、丸めで隠さない。
- 「計算でその値が得られたこと」と「物理・数値モデルが正しいこと」を分けて報告する。
- 原因候補を、入力、方程式、境界条件、離散化、反復収束、格子、時間刻み、後処理に分類する。
- 変更は一度に一要因とし、修正前後のケースIDを保持する。
- 基準値に合うよう物性や $Ra$ を事後調整してはならない。
- 許容値を変更する場合は計算結果を見てから緩和せず、物理的・数値的根拠、影響範囲、版更新履歴を記録し、ユーザーの判断を得る。

## 16. 次段階（full matrix）開始前チェック

Codex はコードまたはケースを作成する前に、次をユーザーへ提示する。

- 両 route の役割、v13 Route A の差分監査結果、Foundation v6 Route B の採用監査結果、minimal implementation で得た concern
- 作成・変更予定ファイルの一覧
- A/B それぞれの4 Ra × 3格子、単体試験、A 感度試験、非定常拡張の実行順序
- 想定計算量と、320²追加が必要になる条件
- 本基準に残る未確定事項と、その決定方法

現在の minimal case・script・result は保持する。full matrix 開始の指示があるまで、追加の Ra/grid ケースを実行しない。
