# de Vahl Davis 自然対流ベンチマーク研究仕様書

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| 文書ID | DVD-OF13-SPEC |
| 版 | 1.1 |
| 対象 | de Vahl Davis の Verification 用 Route B 候補、および OpenFOAM Foundation v13 の比較用 Route A |
| 状態 | 実装前仕様。今回の更新ではケース、スクリプト、ソルバ改変コードを作成しない |
| 対応する判定基準 | `docs/acceptance_criteria.md` |
| 更新日 | 2026-09-30 |

### 変更履歴

| 版 | 日付 | 変更内容 |
|---|---|---|
| 1.0 | 2026-09-28 | Foundation v13 Route A を第一候補とする初版 |
| 1.1 | 2026-09-30 | Route B を主 Verification、Route A をモデル比較・特性評価に分離。Foundation v6 solver を Route B の未監査候補とし、初期圧力整合、感度試験の解釈、両 route の計算順序を更新 |

本書中の **MUST** は必須、**SHOULD** は合理的理由がない限り採用、**MAY** は任意を意味する。

## 1. 目的と研究上の位置づけ

本研究の主 **verification** は、原論文の古典的 Boussinesq 方程式にできるだけ忠実な **Route B と de Vahl Davis 基準解**の比較である。支配方程式、境界条件、離散化、格子、数値解法、後処理の再現性を検証する。**Route A** は Foundation v13 標準流体モデルの特性評価とし、Route B および原論文との差を定量化して将来のティーカップ・茶葉・粒子・物体連成研究に向けて評価する。Route A と原論文の差をそのまま数値誤差と呼ばず、数値誤差・実装誤差・支配方程式差を分ける。

次の3比較は別の研究目的を持つ。**de Vahl Davis 対 Route B = verification**、**Route A 対 Route B = model/formulation difference**、**Route A 対 de Vahl Davis = practical benchmark comparison**。両 route を実装・評価する研究方針を採るが、Route B の実装手段はソース監査後に決定する。

本研究全体では、茶抽出時の自然対流、物体・茶葉の運動、さらに OpenFOAM と粒子・剛体・変形体計算の連成へ進む前の、単相熱流動部分の段階的な検証問題に位置づける。

本ベンチマークに合格しても、次の事項が確認されたことにはならない。

- 実際のティーカップ内流れの validation
- 温度依存物性、乱流、自由表面、放射、蒸発の妥当性
- 茶葉に働く流体力または流体―粒子・物体連成の妥当性
- 過去の OpenFOAM 5／CFDEM 用カスタム実装が v13 でも正しいこと

## 2. 情報の区分と優先順位

混同を避けるため、本書では条件を次のように区分する。

| ラベル | 意味 |
|---|---|
| **[PAPER]** | de Vahl Davis 原論文が規定した問題、定義または基準値 |
| **[OF13]** | OpenFOAM Foundation v13 の公式資料・公式ソースから確認した実装上の事実 |
| **[OF6-CANDIDATE]** | Foundation v6 の採用候補。v6 ソース未監査のため、実装上の事実を認定するラベルではない |
| **[PROJECT]** | 原論文にはなく、本研究で再現可能な計算にするために定める条件 |
| **[GATE]** | 実装前または計算前に確認し、満たさなければ先へ進まない条件 |
| **[OPEN]** | 現時点で未確定であり、監査結果または計算結果を基に決める事項 |

根拠の優先順位は、(1) 原論文、(2) 該当する OpenFOAM Foundation 版の公式文書・公式ソース、(3) 本プロジェクトに登録された資料、(4) 査読論文・公的研究資料、(5) その他の二次資料とする。v13 の監査結果を v6 の実装事実として転用しない。

## 3. 原論文が規定するベンチマーク

### 3.1 物理問題 **[PAPER]**

- 二次元の単位正方形キャビティである。
- 左壁を高温、右壁を低温とする。
- 上壁と下壁は断熱である。
- 全ての壁で速度は no-slip である。
- 流体はニュートン流体、層流、非圧縮であり、密度変化は浮力項だけに Boussinesq 近似として現れる。
- 物性値は一定である。
- Prandtl 数は $Pr=0.71$ である。
- Rayleigh 数は $Ra=10^3,10^4,10^5,10^6$ の4条件である。
- 求める対象は定常解である。原論文の数値的な定常到達手順と、物理問題としての定常解を区別すること。

### 3.2 無次元化 **[PAPER]**

代表長さをキャビティ一辺 $L$、温度差を $\Delta T=T_h-T_c$、温度拡散率を $\alpha=k/(\rho_0 c_p)$ とする。

$$
X=\frac{x}{L},\quad Y=\frac{y}{L},\quad
\theta=\frac{T-T_c}{\Delta T},\quad
\boldsymbol U=\frac{L}{\alpha}\boldsymbol u,\quad
\tau=\frac{\alpha t}{L^2}.
$$

ここで、$x$ は高温壁から低温壁へ向かう水平座標、$y$ は鉛直上向き座標、$\boldsymbol u=(u_x,u_y)$ は有次元速度である。速度尺度が $\alpha/L$ であるため、原論文の $U_{max}$、$V_{max}$ を m/s の速度と直接比較してはならない。

無次元数は

$$
Pr=\frac{\nu}{\alpha},\qquad
Ra=\frac{g\,\beta\,\Delta T\,L^3}{\nu\alpha}
$$

である。$\nu=\mu/\rho_0$ は動粘度、$\beta$ は体膨張係数、$g$ は重力加速度の大きさである。

### 3.3 支配方程式 **[PAPER]**

鉛直上向きを $+Y$ とすると、熱拡散時間と熱拡散速度による無次元方程式は次の形に整理できる。

$$
\nabla\cdot\boldsymbol U=0,
$$

$$
\frac{\partial\boldsymbol U}{\partial\tau}
+(\boldsymbol U\cdot\nabla)\boldsymbol U
=-\nabla P+Pr\,\nabla^2\boldsymbol U
+Ra\,Pr\,\theta\,\boldsymbol e_Y,
$$

$$
\frac{\partial\theta}{\partial\tau}
+\boldsymbol U\cdot\nabla\theta
=\nabla^2\theta.
$$

各項の物理的意味は、順に連続の条件、運動量の非定常・移流・圧力・粘性拡散・浮力、温度の非定常・移流・熱拡散である。圧力には静水圧成分を除いた換算圧力を用いてよいが、その定義を記録しなければならない。

この形が成立する主な仮定は、二次元、層流、非圧縮、一定物性、粘性散逸無視、圧縮仕事無視、放射無視、および $\beta\Delta T\ll1$ である。

### 3.4 無次元境界条件 **[PAPER]**

| 境界 | 速度 | 温度 |
|---|---|---|
| 左壁 $X=0$ | $\boldsymbol U=0$ | $\theta=1$ |
| 右壁 $X=1$ | $\boldsymbol U=0$ | $\theta=0$ |
| 下壁 $Y=0$ | $\boldsymbol U=0$ | $\partial\theta/\partial Y=0$ |
| 上壁 $Y=1$ | $\boldsymbol U=0$ | $\partial\theta/\partial Y=0$ |

原論文は定常基準解を与えるため、非定常計算に必要な初期条件は原論文の比較条件そのものではなく、本研究側で決める。

### 3.5 比較量の定義 **[PAPER]**

高温壁の局所 Nusselt 数を、座標方向の符号を明示して

$$
Nu_h(Y)=-\left.\frac{\partial\theta}{\partial X}\right|_{X=0}
=-\frac{L}{\Delta T}\left.\frac{\partial T}{\partial x}\right|_{x=0}
$$

とする。平均値は

$$
\overline{Nu}_h=\int_0^1 Nu_h(Y)\,dY
$$

である。積分区間長が1なので、これは壁面上の平均値にも一致する。

速度比較量は次のように抽出する。

- $U_{max}$: 鉛直中心線 $X=0.5$ 上の正の水平速度最大値と、その位置 $Y$
- $V_{max}$: 水平中心線 $Y=0.5$ 上の正の鉛直速度最大値と、その位置 $X$

対称な負の極値も別途確認するが、表の基準値は正の極値である。

### 3.6 原論文の基準値 **[PAPER]**

以下を基準値とする。表示桁を超える精度を暗黙に仮定しない。

| $Ra$ | $U_{max}$ | 位置 $Y$ | $V_{max}$ | 位置 $X$ | $\overline{Nu}$ | $Nu_{max}$ | 位置 $Y$ | $Nu_{min}$ | 位置 $Y$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $10^3$ | 3.649 | 0.813 | 3.697 | 0.178 | 1.118 | 1.505 | 0.092 | 0.692 | 1.000 |
| $10^4$ | 16.178 | 0.823 | 19.617 | 0.119 | 2.243 | 3.528 | 0.143 | 0.586 | 1.000 |
| $10^5$ | 34.73 | 0.855 | 68.59 | 0.066 | 4.519 | 7.717 | 0.081 | 0.729 | 1.000 |
| $10^6$ | 64.63 | 0.850 | 219.36 | 0.038 | 8.800 | 17.925 | 0.038 | 0.989 | 1.000 |

任意診断値として、中心流れ関数の大きさ $|\psi_c|$ は順に 1.174、5.071、9.111、16.32 である。ただし、流れ関数を主判定量にするには、離散速度からの再構成法と符号規約を先に固定する必要がある。

原論文は格子細分化と外挿を用い、最も厳しい $Ra=10^6$ でも精度が概ね1%より良いと報告している。このため、本仕様は原論文値との差が1%未満でも「真値に対して1%未満」とは表現せず、「掲載基準値との一致」と表現する。

## 4. 本研究で定める物理量への写像

この節は全て **[PROJECT]** であり、原論文が指定した有次元物性値ではない。同じ $Ra$ と $Pr$ を両 route で比較可能にするための数値的な実現である。Route B 候補に必要な入力形式と実際に使用する物性は v6 ソース監査で確認する。Route A 固有の $c_v$、分子量、生成エンタルピーを Route B が同じ形で読むと仮定しない。

### 4.1 座標、形状、物性

| 項目 | 採用値 | 理由 |
|---|---:|---|
| $L$ | 0.1 m | 数値の扱いやすい代表長さ。無次元解には影響しない |
| 奥行き $W$ | 0.001 m = $L/100$ | 1セルとし、前後面を二次元境界にする |
| $T_0$ | 300 K | Boussinesq 参照温度 |
| $T_h$ | 300.5 K | 左壁 |
| $T_c$ | 299.5 K | 右壁 |
| $\Delta T$ | 1 K | 無次元化を簡潔にし、密度変化を小さくする |
| $\rho_0$ | 1 kg/m³ | 参照密度 |
| $\beta$ | $1.0\times10^{-3}$ K⁻¹ | $\beta\Delta T=10^{-3}\ll1$ を保証 |
| $\mu$ | $1.0\times10^{-5}$ Pa s | 参照動粘度 $\nu_0=\mu/\rho_0=10^{-5}$ m²/s |
| $Pr$ | 0.71 | 原論文と一致 |
| $\alpha_0=\nu_0/Pr$ | $1.408450704225\times10^{-5}$ m²/s | 参照温度拡散率。$Pr$ から一意に設定 |
| $c_v$ | 1000 J/(kg K) | 定数熱量モデル用。参照 $\alpha_0=\mu/(\rho_0Pr)$ となるよう設定 |
| 分子量 | 28.9 kg/kmol | Foundation の `specie` 入力に必要な形式値。Boussinesq route で解に影響しないことを監査 |
| 生成エンタルピー | 0 J/kg | 化学反応を扱わない定数熱量モデルの基準値 |

この設定では Route A の高温壁と低温壁の密度はそれぞれ約 $0.9995\rho_0$、$1.0005\rho_0$ であり、全温度差に対する密度差は0.1%である。熱拡散速度尺度は $\alpha_0/L=1.408450704225\times10^{-4}$ m/s、熱拡散時間尺度は $L^2/\alpha_0=710$ s である。v13 ソース監査では Route A の局所 $\nu$ と $\alpha$ に密度依存性が確認された。Route B は参照値 $\nu_0,\alpha_0$ を定数として使えるか、候補ソースで検証する。感度試験だけで両 route の一致を主張しない。

### 4.2 Rayleigh 数の設定

物性と温度差を固定し、重力の大きさだけを変えて $Ra$ を設定する。重力ベクトルは $\boldsymbol g=(0,-g,0)$ とする。

$$
g=\frac{Ra\,\nu_0\alpha_0}{\beta\Delta T L^3}
=Ra\times1.408450704225\times10^{-4}\;\mathrm{m/s^2}.
$$

| $Ra$ | $g$ [m/s²] |
|---:|---:|
| $10^3$ | 0.1408450704 |
| $10^4$ | 1.408450704 |
| $10^5$ | 14.08450704 |
| $10^6$ | 140.8450704 |

上表は表示値であり、Gate A の $Ra$ 精度判定には丸め値をそのまま入力せず上式から十分な桁数で算出する。Route B の候補が入力した $g,\beta,\nu_0,\alpha_0$ をどう使うかは別途監査する。

これは空気を地球重力下で再現する物性設定ではなく、相似則に基づく無次元問題の実現である。物理的な空気物性との一致を主張してはならない。

## 5. Route A / Route B の役割と実装前監査

### 5.1 Route A: Foundation v13 標準モデル **[OF13]/[PROJECT]**

- 実行系は Foundation v13 の `foamRun` + `fluid` solver module + `equationOfState Boussinesq` とする。熱力学モデルは監査済みの定物性・内部エネルギー系を候補とする。
- v13 の Boussinesq 状態方程式は $\rho=\rho_0[1-\beta(T-T_0)]$ を実装する。ただしこの密度は浮力だけに限定されず、質量保存、運動量、輸送係数、エネルギーにも現れる。
- `docs/openfoam_design.md` のソース監査により、density-weighted continuity/momentum、局所密度依存の $\nu,\alpha$、運動エネルギー、圧力仕事、重力仕事等が原論文式と異なることを確認した。全差分が $O(\beta\Delta T)$ で消えるとは仮定しない。
- 乱流モデルは使用せず、laminar とする。
- 圧力は重力静水圧を分離した $p_{rgh}$ を用い、圧力の基準セルと基準値を記録する。
- 高温・低温壁は温度固定、上下壁は温度勾配ゼロ、全壁は no-slip とする。
- 前後面は Foundation の二次元計算用 `empty` 境界とする。
- 放射、体積発熱、粒子、剛体、自由表面、乱流モデルは使用しない。

Route A は Foundation v13 標準モデルが原論文値をどの程度再現するか、Route B とどれだけ異なるか、将来の標準流体 route としてどの特性を持つかを調べる。古典的 Boussinesq 方程式そのものの Verification route と呼ばない。

実装時の Route A 境界条件は次を基本とする。Route B 候補での $p_{rgh}$ の定義・単位・境界処理は v6 監査まで確定しない。

| 境界 | 速度 $\boldsymbol u$ | 温度 $T$ | $p_{rgh}$ |
|---|---|---|---|
| 左・高温壁 | no-slip | fixed value $T_h$ | `fixedFluxPressure` |
| 右・低温壁 | no-slip | fixed value $T_c$ | `fixedFluxPressure` |
| 上・下断熱壁 | no-slip | zero normal gradient | `fixedFluxPressure` |
| 前・後面 | empty | empty | empty |

閉領域の圧力の任意定数を固定するため、キャビティ中心に最も近い cell を基準 cell、基準値を0とする。格子ごとの実 cell ID と座標を manifest に保存する。`fixedFluxPressure` と浮力項の整合、`pRefCell/pRefValue` が $p_{rgh}$ 補正式へ渡る処理は `openfoam_design.md` 7節に記録済み。

**[PROJECT]/[GATE] OQ-02 の解決方針:** Route A の初期場は全領域 $\boldsymbol u=0$、$T=T_0$、$\rho=\rho_0$、$p_{rgh}=0$ とする。v13 の $p_{rgh}=p-\rho gh-p_{Ref}$ に対し、初期 $p=\rho_0gh+p_{Ref}$ の静水圧場を与える。ここで $gh=\boldsymbol g\cdot\boldsymbol x-gh_{ref}$、$p_{Ref}$ は一様圧力であり、圧力基準の `pRefValue` と区別する。$p=0$ と $p_{rgh}=0$ を同時に設定して整合したとみなさない。実装時に必須の `0/p` と `0/p_rgh`、v13 の初期化処理後の関係、基準 cell/value を再確認し、manifest に保存する。

### 5.2 Route B: 原論文方程式の Verification 候補 **[PROJECT]/[OF6-CANDIDATE]/[GATE]**

Route B は原論文の $\nabla\cdot\boldsymbol u=0$、一定密度の慣性・移流・粘性、温度依存密度は浮力だけ、定数物性の温度対流拡散をできるだけ忠実に再現する。Foundation v13 の新規 solver/module 作成を最初から必須としない。

**第一実装候補は OpenFOAM Foundation v6 `buoyantBoussinesqSimpleFoam`**。これは未監査の候補であり、**「Route B = v6」と確定しない**。採用前に実際の Foundation v6 ソースで以下を追跡し、式・処理・入力・境界条件の対応表を作成する。

1. 体積流束と連続式が $\nabla\cdot\boldsymbol u=0$ に対応するか。
2. 運動量の慣性・移流・粘性に温度依存密度を使わず、密度変化は浮力だけに現れるか。
3. $T$ を直接解き、$\alpha_0$ 一定の温度対流拡散式と対応するか。放射・体積発熱・乱流の hook が零にできるか。
4. laminar momentum transport、$p_{rgh}$ と $gh$、浮力の符号、圧力基準、SIMPLE の処理。
5. 実際の transport properties と $\nu_0,\alpha_0,Pr,Ra$、境界条件、熱流束の符号・単位。

差異または必要な未解決事項があれば記録し、候補の採否を決める。採用できない場合は原論文式に必要な最小限の別実装を設計し、無断で solver を作らない。Route B の OpenFOAM 版・入力・後処理を Route A と混在させない。

### 5.3 Route 間比較と既存 v13 監査 **[PROJECT]/[GATE]**

`docs/openfoam_design.md` は v13 Route A の既存ソース監査であり、v6 候補の監査結果ではない。Route A の equation/transport/heat-flux 差分を保持した上で Route B の別監査を実施する。Route A の $\epsilon=\beta\Delta T\to0$ と Route B の厳密一致を Route B の採用条件にしない。Route A 固有の energy equation 差の全てが $\epsilon$ とともに消失するとは限らない。

両 route を同じ $Ra,Pr,L,\Delta T$、対応する格子・抽出手順で評価する。少なくとも平均 Nu、$U_{max}$ と位置、$V_{max}$ と位置、局所 Nu、保存量、対称性を比較し、(a) B 対原論文、(b) A 対 B、(c) A 対原論文を別表・別解釈で報告する。原論文に掲載のない保存量・対称性の数値は創作せず、支配方程式からの理論的条件と両 route の診断値を示す。非零の比較量 $Q$ について

$$
D_{AB}(Q)=\frac{|Q_A-Q_B|}{|Q_B|}
$$

を診断量の候補とする。位置は絶対差を用い、$Q_B\simeq0$ なら規格化を計算前に決める。**A–B 差には新たな Hard 閾値を設けない**。各 route の格子・反復誤差と後処理差を評価してから、差をモデル差として解釈する。

実装可否は route ごとに判定する。Route B の v6 候補が原論文式に一致するかは未確認であり、ソース監査合格前に Verification ケースを作成しない。Route A の既存設計書は v1.0 時点の意思決定を含むため、本 v1.1 の研究上の役割・判定規則を優先する。Route A の初期圧力条件など実行時にしか確定しない事項は、別途実装ゲートで確認する。

## 6. 数値計算仕様 **[PROJECT]**

### 6.1 主計算

- 主判定は定常計算とする。
- 初期推定値は全領域 $\boldsymbol u=0$、$T=T_0$ とする。Route A の圧力・密度は5.1の OQ-02 に従う。Route B 候補では初期圧力と基準処理を v6 監査後に固定する。
- 空間離散は、原論文との比較に適した二次精度中心差分相当を基本とする。
- 対流項は `Gauss linear` 相当、勾配は linear、拡散項は uniform orthogonal mesh 上で linear/orthogonal を基本とする。
- 一次精度 upwind を主結果に使ってはならない。安定化のため limiter 等を使う場合は、その影響を別ケースで定量化する。
- 全ての active term に対するスキームを明示し、デフォルトへの暗黙依存を避ける。
- 線形ソルバ、緩和、圧力補正回数は、収束解を変えないことを確認しつつ実装段階で定める。

### 6.2 格子

構造・等間隔・直交格子を用い、次の3水準を必須とする。

| 名称 | 面内セル数 | 奥行き | 細分化比 |
|---|---:|---:|---:|
| coarse | 40 × 40 | 1 | — |
| medium | 80 × 80 | 1 | 2 |
| fine | 160 × 160 | 1 | 2 |

前後面を `empty` とし、計算結果が二次元であることを保証する。壁近傍だけを寄せた非一様格子は、主判定に合格した後の追加検討とする。格子品質の合格は格子独立性の合格を意味しない。

### 6.3 段階的な監査・計算行列 **[PROJECT]/[GATE]**

この版では計算を実行しない。後続段階の順序は次のとおりとし、先行する Route A 計算は Route B 検証の代用にしない。

| Phase | 条件 | 目的・次段階への条件 |
|---:|---|---|
| 0 | 既存 v13 Route A ソース監査を確認 | `docs/openfoam_design.md` の実装事実を使用し、OQ-02 は実装時確認事項として保持 |
| 1 | Foundation v6 Route B 候補の read-only ソース監査 | 5.2の全項目を確認して採否を判断。未合格なら B の実装に進まない |
| 2 | Route A、$Ra=0$、medium 80²以上 | 温度境界、熱流束符号、後処理、初期静水圧整合を確認 |
| 3 | Route A、$Ra=10^4$、40² | 初期実装の smoke test。benchmark 合格とは判定しない |
| 4 | Route B、$Ra=0$、medium 80²以上、および $Ra=10^4$、40² | B 固有の入力・境界・Nu と実行健全性を確認 |
| 5 | Route B、4 Ra × 3格子 = 12ケース | 原論文値との主 Verification、格子収束、保存則、対称性 |
| 6 | Route A、4 Ra × 3格子 = 12ケース | A 対 B、A 対原論文の別々の比較と A の数値誤差評価 |
| 7 | Route A、$Ra=10^6$、fine、$\beta\Delta T$ 感度 | A の観測量感度を評価。A–B 同一性の証明とはしない |
| 8 | 必要な場合の非定常、可変物性、茶葉等 | 主 Verification とは別の下流研究 |

Route B が Phase 1 で不適合なら、その理由と最小代替案を示し、採用手段の再決定後に B の Phase 4 へ進む。Route A は Phase 2–3 まで先行できるが、B の主判定を飛ばして A の基準値一致を Verification と呼ばない。

### 6.4 Boussinesq 小パラメータ感度 **[PROJECT]/[GATE]**

Route A について、$Ra=10^6$ の fine 格子で $\beta\Delta T=10^{-3}$ と $10^{-4}$ を比較する。$Pr$ と $Ra$ は固定し、$\beta$ を1/10にした分だけ $g$ を10倍して相似条件を維持する。他の物性と数値条件は変えない。

この試験は **Route A の観測量が小パラメータの変更にどれだけ敏感か**を測る。v13 のエネルギー式には $O(\beta\Delta T)$ と限らない原論文との差分があるため、$\beta\Delta T\to0$ により Route A と B が一致するという証明にはならない。結果は A–B 比較と分離し、0.2% の既存目安および下流研究の判定上の役割は `acceptance_criteria.md` に従う。

### 6.5 非定常拡張 **[PROJECT]**

非定常拡張は、将来の茶葉運動との連成に必要な時間精度を別途確認するためのものであり、原論文の定常 benchmark 合格と混同しない。

- 初期条件は $\boldsymbol u=0$、$T=T_0$。
- 時間離散は二次精度 backward を基本とする。
- $Ra=10^6$、fine 格子を最も厳しい代表条件とする。
- 最大 Courant 数の目標を 0.5 と 0.25 の2水準以上とし、差が許容値を超える場合は0.125を追加する。
- 十分な定常到達後の量を比較する。時間平均で未収束を隠してはならない。

## 7. 後処理仕様 **[PROJECT]**

### 7.1 Nusselt 数

主値は有限体積法の壁面 face 値から面積重み付きで積分する。等間隔節点データを仮定する Simpson 則を、cell-face データへ機械的に適用しない。

独立した2経路を用いる。

1. 温度の壁面法線勾配から、3.5の座標符号に変換して $Nu$ を計算する。
2. 該当 route・版で監査済みの wall heat-flux 機能または独立な face flux 積分で得た熱流束を $k\Delta T/L$ で無次元化する。v13 の機能を v6 候補へ無条件に転用しない。

$Ra=0$ の純熱伝導解で両経路の符号と規格化を校正する。高温壁・低温壁とも、キャビティ内を高温側から低温側へ流れる熱量を正として報告する。

内部断面の保存診断として

$$
Nu_x(X)=\int_0^1\left(U\theta-\frac{\partial\theta}{\partial X}\right)dY
$$

を計算 MAY とする。定常かつ保存が成立すれば、断面位置によらず壁面平均値と一致する。

### 7.2 速度極値

- 格子解を中心線 $X=0.5$、$Y=0.5$ へ補間する。
- 抽出点列、補間方式、端点の扱いを固定し、全格子で同じ無次元手順を用いる。
- 任意の最近傍 cell 中心だけから極値を採らない。
- 値と位置を同時に報告する。
- 正の極値に加え、180°回転対称性に対応する負の極値も保存診断として報告する。

### 7.3 場の可視化

各 $Ra$ の fine 解について、最低限、次を同一の範囲・座標・無次元量で出力する。

- 無次元温度の等高線
- 速度ベクトルまたは流線
- 高温壁と低温壁の局所 $Nu$
- 中心線上の $U(Y)$ と $V(X)$

見た目の一致は定量判定の代わりにしない。

## 8. 保存則と対称性の診断

- 高温壁から流入する熱量と低温壁から流出する熱量を比較する。
- 複数の鉛直断面で $Nu_x$ を比較する。
- 質量保存について、両 route の $\nabla\cdot(\rho\boldsymbol u)$ と、原論文が要求する $\nabla\cdot\boldsymbol u$ の両方を評価する。Route B の $\rho$ の扱いは候補ソースで確定し、定数 $\rho_0$ なら両者が比例することを記録する。
- 問題は中心 $(0.5,0.5)$ まわりの180°回転に対して、$\theta(X,Y)=1-\theta(1-X,1-Y)$、$\boldsymbol U(X,Y)=-\boldsymbol U(1-X,1-Y)$ の対称性を持つ。離散解の対称誤差を定量化する。

保存則・対称性に失敗した結果は、原論文の表と偶然一致しても合格にしない。

## 9. 実装時に Codex が作成すべき成果物

本段階では作成しない。次の実装段階で、少なくとも以下を作成する。

1. `docs/openfoam_design.md`: v13 Route A の既存監査。後続の実装設計では Route B の別監査記録も追跡可能にする。**本 v1.1 更新では変更しない**。
2. `cases/`: route・版を分離した共通テンプレートと、Ra・格子別の再現可能なケース。
3. `Scripts/`: ケース生成、実行、監視、後処理、表・図生成。大文字小文字を含む現行ディレクトリ名を維持する。
4. `results/run_manifest.json`: OpenFOAM版、Git情報、日時、ホスト、辞書ハッシュ、格子、物性、無次元数。
5. `results/benchmark_summary.csv`: B 対原論文の Verification 判定、A 対原論文の実用比較を区別した基準値・計算値・誤差・判定。
6. `results/route_comparison.csv`: 同一条件の A–B 差。モデル差と数値誤差を分けて考察。
7. `results/grid_convergence.csv`: route 別の格子差、観測次数、GCI。
8. `results/conservation.csv`: route 別の熱・質量・対称性診断。
9. `results/figures/`: 規定した場と中心線・壁面分布。

各数値は、どのケース、時刻／反復、抽出方法、単位または無次元化で得たか追跡可能でなければならない。

## 10. 実装時の禁止事項

- OpenFOAM Foundation v13 と OpenCFD/ESI 系の同名機能を混在させない。
- Foundation v6 と v13 の辞書・ソルバ・後処理を、版ごとの監査なしに同一視しない。
- 公式 tutorial の乱流モデル、upwind、物性値を、benchmark に適切か確認せずコピーしない。
- 原論文の有効桁を超えて基準値を補間・創作しない。
- $U_{max},V_{max}$ を有次元速度のまま比較しない。
- 壁面熱流束の法線符号を確認せず、絶対値だけで不整合を隠さない。
- 単一格子の原論文一致だけで格子独立と判断しない。
- 定常残差だけで収束を判断せず、比較量と保存量の定常化を確認する。
- benchmark 合格を、実際の茶抽出現象の validation と表現しない。
- Route A の原論文値との差を、モデル差の検討なしに純粋な数値誤差と断定しない。

## 11. 現時点の未確定事項 **[OPEN]**

| 項目 | 決定方法 |
|---|---|
| OQ-01 作業領域名 | 既存設計書は依頼時の `deVahlDavis` と実測 `deVahlDavisBenchmark` の差を記録。実装前に使用領域を確定し、既存ファイルを無断で移動しない |
| Route B の v6 候補採否 | Foundation v6 ローカルソースで5.2の項を監査し、原論文式との対応を判定 |
| Route A の OQ-02 初期圧力実装整合 | Phase 2 の開始前に $p$, $p_{rgh}$, $\rho$, $gh$, 参照値と v13 初期化処理を確認 |
| Route A の OQ-03 方程式差の定量化 | A–B の同条件比較、各 route の格子・保存診断、Gate H の観測量感度を組み合わせて評価。実装停止条件ではない |
| Route A の下流研究への適用範囲 | A 特性評価と Gate H、必要なら非定常試験の結果から別途判断 |
| 線形ソルバ、前処理、緩和係数 | 方程式監査後、解の不変性と計算効率を確認して設計書に記載 |
| 反復上限 | 比較量・保存量の収束に十分な値を smoke test 後に固定 |
| 非定常の最終終了時刻 | 無次元時間履歴から定常判定できる値を予備計算で決定 |
| 局所 $Nu$ 角部極値の補間方法 | face 値の定義と原論文比較の整合性を確認して固定 |
| 320²格子の追加 | 3格子で単調・漸近収束が確認できない量に限り追加 |
| OQ-07 Route A 非定常の閉領域質量 | 下流 Phase 8 へ進む場合、EOS 密度更新・全質量履歴・圧力補正の整合を別途確認 |
| 過去研究の v5/custom 実装との差 | v5 の正確な版と改変内容を確認できた場合にのみ同一性を議論 |

## 12. 根拠資料

### 一次資料・公式資料

1. G. de Vahl Davis, “Natural convection of air in a square cavity: A bench mark numerical solution,” *International Journal for Numerical Methods in Fluids*, 3(3), 249–264, 1983. [DOI: 10.1002/fld.1650030305](https://doi.org/10.1002/fld.1650030305)
2. OpenFOAM Foundation, [OpenFOAM v13 User Guide — Introduction](https://doc.cfd.direct/openfoam/user-guide-v13/introduction)
3. OpenFOAM Foundation, [OpenFOAM v13 Solver Modules](https://doc.cfd.direct/openfoam/user-guide-v13/solvers-modules)
4. OpenFOAM Foundation, [Boussinesq equation-of-state class, v13](https://cpp.openfoam.org/v13/classFoam_1_1Boussinesq.html)
5. OpenFOAM Foundation, [Numerical schemes, v13](https://doc.cfd.direct/openfoam/user-guide-v13/fvschemes)
6. OpenFOAM Foundation, [Boundary conditions, v13](https://doc.cfd.direct/openfoam/user-guide-v13/boundary-conditions)
7. OpenFOAM Foundation, [Official v13 `hotRoomBoussinesq` tutorial](https://github.com/OpenFOAM/OpenFOAM-13/tree/master/tutorials/fluid/hotRoomBoussinesq)
8. 本プロジェクト、[`docs/openfoam_design.md`](openfoam_design.md)（Foundation v13 Route A のローカルソース監査、2026-09-29、v1.0 仕様に対する記録。本 v1.1 では参照専用）
8. OpenFOAM Foundation, [Official v13 `fluid` module source](https://github.com/OpenFOAM/OpenFOAM-13/tree/master/applications/modules/fluid)
9. OpenFOAM Foundation, [Official v13 `isothermalFluid` module source](https://github.com/OpenFOAM/OpenFOAM-13/tree/master/applications/modules/isothermalFluid)
10. OpenFOAM Foundation, [Official v13 `wallHeatFlux` source](https://cpp.openfoam.org/v13/wallHeatFlux_8C_source.html)

### 本プロジェクトの登録資料・議論

1. 石井健太「CFD-DEMを用いた茶葉の運動の数値シミュレーション」卒業論文、2026年（登録ファイル `sources/b1022021.pdf`）。Boussinesq 近似、旧 OpenFOAM 5／CFDEM 実装、および本研究への接続を確認した。
2. `sources/OpenFOAMによる熱移動と流れの数値解析第2版_理論編.md`。温度輸送式、Boussinesq 近似、$p_{rgh}$ の理論的対応を参照した。
3. `sources/数値流体力学_第2版.md`。verification/validation の区別、格子・時間刻み依存性、Richardson 外挿と GCI、保存則確認を参照した。
4. プロジェクト内の議論「deVahlDavisの自然体流のベンチ」「deVahlDavisの自然体流のベンチ（計算格子関係の質問）」「deVahlDavisの自然体流のベンチ（Nu関連の質問）」「自然対流の検証」。段階的検証、格子系列、Nu の定義、定常・非定常の分離を反映した。

原論文の数表は原論文を基準とし、公開環境での転記誤りを避けるため、学術機関・公的研究機関による再掲表とも照合した。実装後の報告では、原論文値と計算値をこの表の表示桁で比較する。
