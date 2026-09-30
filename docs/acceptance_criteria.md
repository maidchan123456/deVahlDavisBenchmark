# de Vahl Davis 自然対流ベンチマーク合否判定基準

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| 文書ID | DVD-OF13-AC |
| 版 | 1.2 |
| 対象仕様 | `docs/benchmark_spec.md` 版1.2 |
| 対象 | Route B（原論文 Verification）および Foundation v13 Route A（特性評価） |
| 状態 | audit と最小実装確認は完了。full matrix は未実行 |
| 更新日 | 2026-09-30 |

### 変更履歴

| 版 | 日付 | 変更内容 |
|---|---|---|
| 1.0 | 2026-09-28 | Foundation v13 標準 route を主判定とする初版 |
| 1.1 | 2026-09-30 | Route B の原論文 Verification と Route A の特性評価を分離。v6 候補の別監査、初期圧力整合、A–B 比較および Gate H の役割を定義 |
| 1.2 | 2026-09-30 | Route B 採用・最小実装確認、Route A OQ-02、Gate G 離散指標と Gate H の役割を現状に整合 |

本書は、計算を「動いた／動かなかった」ではなく、方程式、入力、数値誤差、保存則および基準解との一致で判定するための規範である。**Hard** 条件は一つでも不合格なら該当ステータスを付与しない。**Diagnostic** 条件は原因分析を必須とするが、それ単独ではコア不合格にしない。同じ Gate の共通閾値は route ごとに独立判定する。$G_B$ は「Gate G の Route B 判定」、$G_A$ は「Gate G の Route A 判定」を表す。

研究上の比較は、(1) **B 対原論文＝Verification**、(2) **A 対 B＝モデル・定式化差**、(3) **A 対原論文＝実用 benchmark 比較**と区別する。A 対原論文の誤差を純粋な数値誤差と呼ばない。

## 1. 判定ステータス

| ステータス | 意味 |
|---|---|
| `NOT_RUN` | 仕様のみで、実装または計算をまだ行っていない |
| `ROUTE_A_AUDIT_PASS` | v13 Route A のソース監査に合格し、OQ-02 の初期圧力確認を完了・記録 |
| `ROUTE_B_AUDIT_PASS` | 監査済み採用実装の Foundation v6 source で原論文式との対応を確認 |
| `BENCHMARK_CORE_PASS` | **Route B のみ**で定常 de Vahl Davis Verification の全 Hard 条件に合格 |
| `ROUTE_A_CHARACTERIZED` | B コア合格を前提に、A の健全性・格子・保存と3種類の比較・Gate H の実施報告が完了 |
| `DOWNSTREAM_TRANSIENT_READY` | B コア合格、A 特性評価、Gate H 合格、A 非定常 Gate J 合格 |
| `FAIL` | 当該 route・当該段階の必須条件を満たさない、または証拠不足。別 route の合格を自動的に取り消さない |

| 現在の項目 | 状態 |
|---|---|
| Route A audit / Route B audit | PASS / PASS |
| Route A Gate C / Route B Gate C | PASS / PASS（A-COND/B-COND） |
| Route A smoke / Route B smoke | PASS / PASS |
| `BENCHMARK_CORE_PASS` / `ROUTE_A_CHARACTERIZED` / `DOWNSTREAM_TRANSIENT_READY` | NOT EVALUATED / NOT EVALUATED / NOT EVALUATED |

A-COND/B-COND は Gate C の証拠であり、full matrix を意味しない。

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

各 route で全項目を満たすこと。Route B は監査済み Foundation v6 `buoyantBoussinesqSimpleFoam` を採用する。build は `6-af7d7f427be7`、Git HEAD は `af7d7f427be78e9b9beb6aceca8fe7d5d4636876`、binary は `/home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam` である。

- [ ] Route A は **OpenFOAM Foundation v13**、Route B は Gate B で採用確定した Foundation の版・実装である。OpenCFD/ESI fork や版違いを同一 route に混在させていない。
- [ ] OpenFOAM の版、ビルド情報、実行環境、ホスト、実行日時を manifest に保存している。
- [ ] 各ケースの入力辞書と格子のハッシュまたは同等の一意な識別情報を保存している。
- [ ] 実際に読み込まれた route 固有の入力と、監査で定義した参照値 $L,\rho_0,T_0,T_h,T_c,\beta,\mu,Pr,g$ の対応から $\nu_0,\alpha_0,Pr,Ra,\beta\Delta T$ を再計算している。Route B は監査済みの定数 $\nu_0,\alpha_0$ を使用する。
- [ ] 再計算した $Pr$ と目標値0.71、各 $Ra$ と目標値の相対差が $10^{-10}$ 以下である。
- [ ] 4つの物理壁と2つの前後面の名前、種類、面積、法線方向を機械可読な記録に残している。
- [ ] 40²、80²、160² の面内セル数と奥行き1セルを確認している。
- [ ] mesh check に fatal error がなく、格子が構造・等間隔・直交であることを記録している。
- [ ] front/back は二次元用 `empty` であり、面外速度・面外勾配が導入されていない。
- [x] Route A OQ-02 は解決済み。内部は $p=\rho_0gh+p_{Ref}$、fixed-T壁は $p=\rho(T_{wall})gh+p_{Ref}$ とし、$p_{rgh}=p-\rho gh-p_{Ref}$ を cell+4 physical walls で確認した。`pRefValue` は $p_{Ref}$ と別に記録する。

## 4. Gate B — 方程式監査（Hard）

**Route B の Hard 監査は完了:** Foundation v6 のローカル公式ソースを read-only で追跡し、`buoyantBoussinesqSimpleFoam` を採用した。監査結果は版・ファイル・処理・式・入力辞書・後処理の対応表として `docs/routeB_design.md` に残す。

- [x] 体積流束と連続式が $\nabla\cdot\boldsymbol u=0$ に対応することを確認した。
- [x] 慣性、移流、粘性の係数に温度依存密度が入り込まず、密度変化は浮力項だけに現れることを確認した。
- [x] 定物性の $T$ 対流拡散式を直接解き、$\alpha_0$ と $Pr$ が計画値となることを確認した。
- [x] $p_{rgh}$・$gh$・圧力基準・浮力符号が $y$ 上向き、$g_y<0$ と整合することを確認した。
- [x] 定常 SIMPLE、laminar、放射・体積発熱・粒子結合の無効化、全 active scheme を確認した。
- [x] 壁面熱流束の符号、単位、積分値、面積平均値、独立 Nu 経路を確認した。
- [x] 原論文式との差を列挙し、主 Verification の解釈に記録した。

Route B audit は PASS である。v13 Route A 監査と v6 Route B 監査は別の証拠である。

**Route A の Hard 監査:** `docs/openfoam_design.md` に v13 ソース位置と式対応、連続式・運動量・エネルギー・輸送・$p_{rgh}$・圧力基準・熱流束・定常連成・laminar と active scheme を記録済みである。密度重み付き連続式・運動量、局所密度依存輸送、運動エネルギー・圧力仕事・重力仕事を含む差を明記した。OQ-02 は内部 $p=\rho_0gh+p_{Ref}$、fixed-T壁 $p=\rho(T_{wall})gh+p_{Ref}$、cell+4壁の $p_{rgh}=p-\rho gh-p_{Ref}$ 確認として完了・記録済みである。**OQ-03 の A–B 非同一性は比較研究の対象である**。A の監査は B の式監査の代わりにならない。

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

stored internal/boundary face flux（empty contribution はゼロ）に対し、$D_h(\phi)_i=V_i^{-1}\sum_{f\in i}\phi_f^{out}$、$\langle|D_h|\rangle_V=\sum_iV_i|D_h(\phi)_i|/\sum_iV_i$、$U_p=\max|\boldsymbol u|$ と定義する。$Ra=0$ は Gate C の絶対速度基準を用いる。

1. Route A native mass flux: $\epsilon_{native,m}=L\langle|D_h(\phi_m)|\rangle_V/(\rho_0U_p)\le10^{-6}$（Hard）。Route B native volume flux: $\epsilon_{native,v}=L\langle|D_h(\phi_v)|\rangle_V/U_p\le10^{-6}$（Hard）。
2. Route A solver-consistent volume fluxは、native stored mass flux $\phi_m$ から、v13 `correctBuoyantPressure` が用いる同じ face-density definition $\rho_f=fvc::interpolate(\rho)$ により派生する diagnostic $\phi_v=\phi_m/\rho_f$ とし、$\epsilon_{sc,v}\le2\times10^{-3}$（Hard）とする。Route B は native $\phi_v$ が同じ check を満たし、その $10^{-6}$ native limit がより厳しい。
3. reconstructed cell-U divergence は Diagnostic のみで、Hard threshold を置かない。

連続体の $\rho_0\nabla\cdot u$ の等価性は、異なる離散演算子の数値的一致を意味しない。旧 Route B manifest の `epsilon_m` は reconstructed `epsilon_v` を複写した legacy compatibility label であり、native mass conservation ではない。manifest は不変である。

### 9.3 中心対称性

180°回転対応点で

$$
e_\theta=\theta(X,Y)+\theta(1-X,1-Y)-1,
$$

$$
\boldsymbol e_U=\boldsymbol U(X,Y)+\boldsymbol U(1-X,1-Y)
$$

を作る。$||e_\theta||_{2,V}/\max(||\theta||_{2,V},10^{-12})\le0.2\%$、$||e_U||_{2,V}/\max(||U||_{2,V},10^{-12})\le0.2\%$ とする。Ra=0 は Gate C と absolute velocity defect を用いる。

## 10. Gate H — Route A の Boussinesq 小パラメータ感度（特性評価・下流判定）

Foundation v13 Route A に必須の実施・報告項目である。**既存の 0.2% 閾値は維持する**。Gate H は `BENCHMARK_CORE_PASS` の条件ではない。`ROUTE_A_CHARACTERIZED` には実施・報告を必要とし、Hard PASS は `DOWNSTREAM_TRANSIENT_READY` でのみ必要とする。

- 条件: $Ra=10^6$、fine 格子。
- 基準: $\beta\Delta T=10^{-3}$。
- 感度条件: $\beta\Delta T=10^{-4}$。$Ra$ と $Pr$ を固定するため、$\beta$ を1/10、$g$ を10倍とする。
- 空間スキーム、solver 設定、格子、温度差、他の物性は同一とする。

次の相対差が全て0.2%以下であること。

- $\overline{Nu}$
- $U_{max}$
- $V_{max}$

加えて、両感度点で Route A native mass conservation が Gate G に適合し、solver-consistent $\epsilon_{sc,v}$ が減少または悪化しないことを確認する。reconstructed cell-U divergence は Diagnostic として別報告する。

この試験が測るのは **A の観測量の $\beta\Delta T$ 感度**である。$\beta\Delta T$ の低下で差が小さくても A と B の一致を証明しない。A のエネルギー式には小パラメータで消失すると限らない項がある。solver-consistent $\epsilon_{sc,v}$ が減少せず悪化する、native mass conservation が Gate G に適合しない、または観測量の差が0.2%を超える場合は、連続式・運動量・エネルギー・後処理を切り分け、A–B と A–原論文の比較へ影響を記録する。reconstructed $\epsilon_{Urec}$ は独立した Diagnostic として報告する。B のコア合否には波及させない。

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

`BENCHMARK_CORE_PASS` の宣言には **Route B の**次の証拠が必要である。`ROUTE_A_CHARACTERIZED` には A の対応する証拠と、3種類の比較を分離した表・解釈が必要である。v6 Route B の監査記録を v13 設計書の結論だけで代替しない。

既存の最小成果物は `docs/routeA_implementation.md`、`docs/routeB_implementation.md`、`results/routeA/`、`results/routeB/` であり、audit、Gate C、coarse smoke の証拠である。以下の full-matrix 証拠は将来の core/characterization 判定に必要であり、まだ揃っていない。

| 成果物 | 必須内容 |
|---|---|
| `docs/openfoam_design.md` と Route B の監査記録 | A の v13 監査に加え、採用 B の該当版ソース・方程式・辞書・スキーム・後処理を追跡できること。既存設計書は今回変更しない |
| `results/run_manifest.json` | route ごとの版、環境、ケースID、入力ハッシュ、物性、無次元数、格子、実行状態 |
| `results/benchmark_summary.csv` | route ごとの4 Ra × 3格子の主量、基準値、誤差。B の Verification 合否と A の実用比較を分離 |
| `results/route_comparison.csv` | 対応する A–B の主量・位置・局所 Nu・保存・対称性、差と解釈。A–B Hard 閾値は設けない |
| `results/grid_convergence.csv` | route ごとの3格子値、差、収束型、$p_{obs}$、GCI、追加格子の有無 |
| `results/conservation.csv` | route ごとの壁面熱収支、断面熱収支、質量・体積保存、対称誤差 |
| `results/figures/` | route ごとの温度、流れ、中心線速度、局所 Nu、格子収束図 |
| 実行ログ | 全ケースの収束履歴と異常の有無 |

各表の各行は最低限、`case_id`, `Ra_target`, `Ra_actual`, `Pr_actual`, `grid`, `route`, `status`, `source_time_or_iteration`, `method_version` を持つこと。数値の手入力だけで出所が追えない表は受け入れない。

## 14. 総合判定手順

1. Phase 0--4は完了：A/B audit、A-COND/B-COND Gate C、両 coarse smoke、minimal A/B diagnostic を記録済みである。
2. Phase 5は次であり、自動的には開始しない。B の12主計算で Gate D、E、F、G、K を量・Raごとに判定し、Gate Iを診断する。全Hard合格時のみ `BENCHMARK_CORE_PASS` とする。
3. A の12主計算で Gate D、F、G、K を判定し、Gate E 相当の原論文値差と Gate I を報告する。A–B の対応比較を実施する。
4. A の Gate H 感度試験を行い、数値閾値への合否とモデル差への解釈を報告する。B コア合格と A の必須評価が揃った場合に `ROUTE_A_CHARACTERIZED` とする。
5. 下流研究が必要な場合のみ、Gate H 合格を確認して A の Gate J を実施し、合格時に `DOWNSTREAM_TRANSIENT_READY` とする。

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

ここで Gate A の OQ-02 と Gate B の v6 audit は完了済みである。H の 0.2% 閾値を超えても A の観測結果と原因を報告すれば特性評価は完了し得るが、下流非定常準備には合格が必要である。A の E 相当の誤差および A–B 差は数値を省略できないが、Hard な一致条件にはしない。

## 15. 不合格時の扱い

- 不合格を削除、平均化、丸めで隠さない。
- 「計算でその値が得られたこと」と「物理・数値モデルが正しいこと」を分けて報告する。
- 原因候補を、入力、方程式、境界条件、離散化、反復収束、格子、時間刻み、後処理に分類する。
- 変更は一度に一要因とし、修正前後のケースIDを保持する。
- 基準値に合うよう物性や $Ra$ を事後調整してはならない。
- 許容値を変更する場合は計算結果を見てから緩和せず、物理的・数値的根拠、影響範囲、版更新履歴を記録し、ユーザーの判断を得る。

## 16. 次段階開始前チェック

Codex は Phase 5 full matrix を開始する前に、次をユーザーへ提示する。

- 両 route の役割、完了済み A/B audit と最小実装確認、Phase 5 の実行計画
- 作成・変更予定ファイルの一覧
- A/B それぞれの4 Ra × 3格子、単体試験、A 感度試験、非定常拡張の実行順序
- 想定計算量と、320²追加が必要になる条件
- 本基準に残る未確定事項と、その決定方法

ユーザーが次段階の実行を指示するまでは、full matrix を開始しない。
