理論編

# 第5章 OpenFOAM のための 数値流体力学入門

本章では、OpenFOAM をよりよく理解するために必要な数値流体力学の知識について概説する。

## 5.1 熱流体の支配方程式

### **5.1.1** 圧縮性と非圧縮性 🖙 4.2.1 項 (p.60), 4.2.2 項 (p.62)

流体を数学的に取り扱う場合,密度変化の小さな流体を非圧縮性流体 (incompressible fluid) として扱う. 一方,密度変化を無視できない場合は圧縮性流体 (compressible fluid) とする. 一般に、速度がマッハ数 0.3 以下 (密度変化が 5 %以下) であれば非圧縮性流体とみなされる.

OpenFOAM では、温度を扱う場合は一般に圧縮性流体として扱われる。熱物性 (thermophysical properties) を扱えるのは、圧縮性流体ソルバーだけである。

#### 5.1.2 連続の式

連続の式 (質量保存の式) は次式で表される.

$$\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{u}) = 0 \tag{5.1}$$

ここで、u は速度、 $\rho$  は密度である。定常状態では時間微分項が省かれる。非圧縮性流体の場合は、次式のようになる。

$$\nabla \cdot \boldsymbol{u} = 0 \tag{5.2}$$

**5.1.3 運動方程式** 🖙 4.2.1 項 (p.60), 4.2.2 項 (p.62) 運動方程式 (ナビエ-ストークス方程式) は次式で表される.

$$\frac{\partial \rho \boldsymbol{u}}{\partial t} + \nabla \cdot (\rho \boldsymbol{u} \boldsymbol{u}) = -\nabla p + \nabla \cdot \left[ \mu \{ \nabla \boldsymbol{u} + (\nabla \boldsymbol{u})^T \} \right] - \nabla \left( \frac{2}{3} \mu \nabla \cdot \boldsymbol{u} \right)$$
 (5.3)

ここで、 $\mu$  は粘性係数である.

135

OpenFOAM の圧縮性流体ソルバーでは、次式が解かれる.

$$\frac{\partial \rho \boldsymbol{u}}{\partial t} + \nabla \cdot (\rho \boldsymbol{u} \boldsymbol{u}) = -\nabla p + \nabla \cdot (\mu \nabla \boldsymbol{u}) + \nabla \cdot \left[ \mu \left\{ (\nabla \boldsymbol{u})^T - \frac{2}{3} \nabla \cdot \boldsymbol{u} I \right\} \right] \quad (5.4)$$

右辺第 2 項はラプラシアンとみなされる。右辺第 3 項の発散の中は,速度勾配の転置の偏差テンソルのようなものとして表現され (偏差テンソルの場合は係数が 2/3 ではなく 1/3),陽的に計算される.定常状態の場合は時間微分項が省かれる.

非圧縮性流体ソルバーでは, 次式が解かれる.

$$\frac{\partial \boldsymbol{u}}{\partial t} + \nabla \cdot (\boldsymbol{u}\boldsymbol{u}) = -\nabla p + \nabla \cdot (\nu \nabla \boldsymbol{u}) + \nabla \cdot \left[ \nu \left\{ (\nabla \boldsymbol{u})^T - \frac{2}{3} \nabla \cdot \boldsymbol{u}I \right\} \right]$$
(5.5)

ここで、p は密度で割られた圧力である (出力もこのままなので、評価の際には注意が必要).  $\nu$  は動粘性係数である。右辺第 3 項の発散の中は、圧縮性流体ソルバーと同様に、陽的に計算される。

#### 5.1.4 エネルギー方程式 19 4.2.1 項 (p.60), 4.2.2 項 (p.62)

単位質量あたりの全エネルギー Eの方程式は、次式で表される.

$$\frac{\partial}{\partial t}(\rho E) + \nabla \cdot (\rho E \boldsymbol{u}) = -\nabla \cdot (p \boldsymbol{u}) + \nabla \cdot (k \nabla T)$$
 (5.6)

ここで、k は熱伝導率、T は絶対温度である。ここでは、応力と重力の項は無視した。 全エネルギー E は、単位質量あたりの内部エネルギー e と運動エネルギー K の和で表される。

$$E = e + K \tag{5.7}$$

運動エネルギーは次式で表される.

$$K = \frac{1}{2}\boldsymbol{u} \cdot \boldsymbol{u} \tag{5.8}$$

式 (5.6) を内部エネルギーと運動エネルギーで表すと、次式のようになる.

$$\frac{\partial}{\partial t}(\rho e) + \nabla \cdot (\rho e \boldsymbol{u}) + \frac{\partial}{\partial t}(\rho K) + \nabla \cdot (\rho K \boldsymbol{u}) = -\nabla \cdot (p \boldsymbol{u}) + \nabla \cdot (k \nabla T) \quad (5.9)$$

単位質量あたりのエンタルピールを

$$h = e + \frac{p}{\rho} \tag{5.10}$$

とすると、式 (5.9) は

$$\frac{\partial}{\partial t}(\rho h) + \nabla \cdot (\rho h u) + \frac{\partial}{\partial t}(\rho K) + \nabla \cdot (\rho K u) = \frac{\partial p}{\partial t} + \nabla \cdot (k \nabla T)$$
 (5.11)

となる. エンタルピー h は、定圧比熱を  $c_p$  として

$$h = h_a - h_0 = \int_{T_0}^{T} c_p dT \tag{5.12}$$

と表される. ここで、 $h_a$  は絶対エンタルピー、 $h_0$  は温度が  $T_0$  のときのエンタルピーで、一般には  $T_0=298.15$  [K] とした標準生成エンタルピーが用いられる.

比熱が一定の場合, h は次式で表される.

$$h = c_p(T - T_0) (5.13)$$

これを式 (5.11) に代入し、密度を一定とすると、次式が得られる.

$$\frac{\partial T}{\partial t} + \nabla \cdot (Tu) = \nabla \cdot (\alpha \nabla T) \tag{5.14}$$

ここで、  $\alpha = k/(\rho c_p)$  は熱拡散率である.

OpenFOAM の圧縮性流体ソルバーでは、設定によって式 (5.9) あるいは式 (5.11) が解かれる. 温度の拡散項は次式で表される.

$$\nabla \cdot (k\nabla T) = \nabla \cdot (\alpha \nabla e) = \nabla \cdot (\alpha \nabla h) \tag{5.15}$$

ここで、 $\alpha=k/c_p$  は熱拡散率に密度をかけたものである.

浮力を扱うために Boussinesq 近似を用いるソルバー buoyantBoussinesqSimple-Foam, buoyantBoussinesqPimpleFoam の場合は,流体は非圧縮性流体として扱われ,温度は式 (5.14) から求められる.

#### 5.1.5 状態方程式 ☞ 4.2.2 項 (p.62)

圧縮性流体においては、密度を求めるために状態方程式 (equation of state) を用いる必要がある. 流体が気体の場合は、理想気体 (ideal gas, 完全気体 perfect gas ともいう) の状態方程式が用いられることが多い.

$$\rho = \frac{pW}{RT} \tag{5.16}$$

ここで、W は分子量 [kg/kmol]、R は気体定数 [J/kmol-K] である.

液体の場合は、密度を多項式などで表す.

OpenFOAM の場合、 $\psi = \rho/p$  を圧縮率 (compressibility) とよんでいる。完全気

137

体 (perfectGas) の場合,圧縮率は  $\psi=1/RT$  である.ただし,OpenFOAM の熱物性モデルの気体定数は分子量で割られたもの [J/kg-K] である.

**5.1.6** 浮力の扱い 塚 4.2.1 項 (p.60), 4.2.2 項 (p.62), 4.3 節 (p.67) 浮力を考慮するには、重力を考慮する必要がある.

$$\frac{\partial \rho \boldsymbol{u}}{\partial t} + \nabla \cdot (\rho \boldsymbol{u} \boldsymbol{u}) = -\nabla p + \nabla \cdot \left[ \mu \{ \nabla \boldsymbol{u} + (\nabla \boldsymbol{u})^T \} \right] - \nabla \left( \frac{2}{3} \mu \nabla \cdot \boldsymbol{u} \right) + \rho \boldsymbol{g} \quad (5.17)$$

ここで、g は重力加速度である.

OpenFOAM では、圧力勾配と重力の項を次のように扱う.

$$-\nabla p + \rho \mathbf{g} = -\nabla p_{\text{rgh}} - \mathbf{g} \cdot \mathbf{x} \nabla \rho \tag{5.18}$$

ここで、 $p_{\text{rgh}} = p - \rho g \cdot x$  である。 $p_{\text{rgh}}$  を圧力 p の代わりに求める。p は  $p = p_{\text{rgh}} + \rho g \cdot x$  から計算する。

密度変化を無視できる場合、基準密度を  $\rho_0$ 、基準温度を  $T_0$ 、体積膨張率を  $\beta$  として、密度を次式で表すことができる。

$$\rho = \{1 - \beta(T - T_0)\}\rho_0 \tag{5.19}$$

これは Boussinesq 近似とよばれる。密度変化を無視できるため、非圧縮性流体とみなすことができ、運動方程式は次式のように表すことができる。

$$\frac{\partial \boldsymbol{u}}{\partial t} + \nabla \cdot (\boldsymbol{u}\boldsymbol{u}) = -\nabla p + \nabla \cdot \left[\nu \{\nabla \boldsymbol{u} + (\nabla \boldsymbol{u})^T\}\right] + \frac{\rho}{\rho_0} \boldsymbol{g}$$
 (5.20)

p は密度で割られた圧力である. Boussinesq 近似を用いた圧力勾配と重力の項は,  $\rho_k = 1 - \beta(T - T_0)$  として

$$-\nabla p + \frac{\rho}{\rho_0} \mathbf{g} = -\nabla p_{\text{rgh}} - \mathbf{g} \cdot \mathbf{x} \nabla \rho_k$$
 (5.21)

となる. ここで、 $p_{\text{rgh}} = p - \rho_k g \cdot x$  である.

#### 5.1.7 乱流の効果 **3** 4.4 節 (p.67)

二乱流解析では、乱流モデルの方程式とともに、平均化された運動方程式やエネルギー式などが解かれる。それらは形式的にはもとの方程式と同じ形をしており、乱流の効果は粘性係数や熱拡散率に乱流の成分を足しこむことで表現される。乱流を考慮した運動方程式およびエネルギー方程式は、以下のように表される。

$$\frac{\partial \rho \boldsymbol{u}}{\partial t} + \nabla \cdot (\rho \boldsymbol{u} \boldsymbol{u}) = -\nabla p + \nabla \cdot \left[ \mu_{\text{eff}} \{ \nabla \boldsymbol{u} + (\nabla \boldsymbol{u})^T \} \right] - \nabla \left( \frac{2}{3} \mu_{\text{eff}} \nabla \cdot \boldsymbol{u} \right)$$
(5.22)

$$\frac{\partial}{\partial t}(\rho h) + \nabla \cdot (\rho h \boldsymbol{u}) + \frac{\partial}{\partial t}(\rho K) + \nabla \cdot (\rho K \boldsymbol{u}) = \frac{\partial p}{\partial t} + \nabla \cdot (\alpha_{\text{eff}} \nabla h)$$
 (5.23)

ここで、 $\mu_{\text{eff}} = \mu + \mu_t$ 、 $\alpha_{\text{eff}} = \alpha + \alpha_t$  であり、 $\mu_t$  は乱流粘性係数、 $\alpha_t$  は乱流熱拡散率である。

 $\mu_t$  は乱流モデルによるが、k- $\epsilon$  モデルであれば

$$\mu_t = \rho C_\mu \frac{k^2}{\varepsilon} \tag{5.24}$$

となる. ここで,  $C_{\mu} = 0.09$  である.

 $\alpha_t$  については、乱流拡散係数から

$$\alpha_t = \frac{\mu_t}{Pr_t} \tag{5.25}$$

となる. ここで  $Pr_t$  は乱流プラントル数で、値は経験的に 0.85 が用いられる.

# 5.2 境界条件

### 5.2.1 基本境界条件 🖙 4.5.1 項 (p.70)

基本的な境界条件は、値指定境界条件(ディリクレ境界条件)と勾配指定境界条件(ノイマン境界条件)である。OpenFOAMでは、境界条件タイプとしてそれぞれfixedValue とfixedGradientが対応する。勾配指定境界条件はゼロ勾配境界条件としてよく用いられ、OpenFOAMでは境界条件タイプ zeroGradient として別途用意されている。

## 5.2.2 流入条件 ☞ 4.5.3 項 (p.76)

流入条件としては、速度は値指定条件、圧力はゼロ勾配条件とする. 温度は値指定とする.

### 5.2.3 流出条件 ☞ 4.5.3 項 (p.76)

流出条件としては、速度についてはゼロ勾配条件が用いられる。ただし、これは十分に発達した流れを想定することになるため、出口を障害物から十分に離した場所に設定する必要がある。

圧力については、値指定条件を用いる. 圧力方程式を解くためには、どこかで圧力

値を指定する必要があるが、流出条件において指定することが多い。出口のない領域を解く場合は、領域内のどこかに適当な圧力値を設定する必要がある。OpenFOAMでは、pRefValue、pRefPoint (または pRefCell) の設定がこれにあたる。

温度などのスカラー値はゼロ勾配条件とする.

## **5.2.4** 壁の条件 🐷 4.5.6 項 (p.80), 4.5.7 項 (p.80), 4.12.3 項 (p.110)

壁の条件には、固着 (non-slip) 境界条件とスリップ (slip) 境界条件がある。前者は壁面で流速を 0 とするもので、壁では通常この条件が使われる。壁で流体がすべって流速が 0 にならない場合は、後者の条件を用いる。圧力についてはゼロ勾配条件とする。温度についてはいくつかの条件がある。

固着条件では、流速を値指定条件で0とする.壁が動いている場合は、壁の速度を 指定すればよい.スリップ条件では、壁方向の速度勾配を0とする.OpenFOAMでは、固着条件には直接速度を指定するか、noSlipという境界条件タイプを用いる.これに対し、スリップ条件には slipという境界条件タイプを用いる.温度については、まず値指定条件と勾配指定条件がある.値指定条件はそのまま温度を指定するものである.勾配指定条件は、熱流束の指定に相当する.熱流束は.フーリエの法則から

$$q = -k\nabla T \tag{5.26}$$

であるので、これより、温度勾配は次式で表される.

$$\nabla T = -\frac{1}{k}q\tag{5.27}$$

断熱条件の場合は、ゼロ勾配条件を用いればよい.また、熱伝達境界条件および外部 輻射境界条件は次式のように表される.

$$q = -h(T - T_{\text{ext}}) - \varepsilon(T^4 - T_{\text{ext}}^4)$$
 (5.28)

ここで、h は熱伝達率、 $\varepsilon$  は放射率 (emissivity)、 $T_{\rm ext}$  は外部温度である。この条件は未知数を含むため、勾配指定条件では与えられず、別途専用の条件を用いる必要がある。

OpenFOAM の場合、熱流束、熱伝達条件および外部輻射条件を設定する境界条件タイプとして externalWallHeatFluxTemperature がある.

#### 140

# **5.3 有限体積法による離散化** ☞ 4.6 節 (p.83), 4.7 節 (p.90)

OpenFOAMでは、偏微分方程式の離散化手法として主に有限体積法が用いられている。有限体積法はコントロールボリューム法ともよばれ、連続体の偏微分方程式を離散化して解く手法の一つである。連続体をコントロールボリュームあるいはセルともよばれる多面体で分割し、方程式をセルの体積積分の形で表す(図 5.1).

![](_page_2_Picture_4.jpeg)

図 5.1 セル

離散点をセルの中心に置き、セル内部の値をセル中心の値で代表させる。P は注目セルの中心の点、N は隣接セルの中心の点、f は注目セルと隣接セルが共有する面の中心の点である。これらの点における値をそれぞれ P, N, f という添字で表す。たとえば、それぞれの点の位置を  $x_P$ ,  $x_N$ ,  $x_f$  のように表す。

たとえば、次のようなスカラー量 φの輸送方程式を考える.

$$\frac{\partial \rho \phi}{\partial t} + \nabla \cdot (\rho \phi \mathbf{u}) = \nabla \cdot (k \nabla \phi) + S \tag{5.29}$$

ここで、 $\rho$  は密度、u は流速ベクトル、k は拡散係数、S はソース項である。これを有限体積法で離散化する。まず、方程式をセルにおいて積分する。

$$\int \frac{\partial \rho \phi}{\partial t} dV + \int \nabla \cdot (\rho \phi \mathbf{u}) dV = \int \nabla \cdot (k \nabla \phi) dV + \int S dV$$
 (5.30)

これは次式のように書ける.

$$\frac{\partial \rho \phi}{\partial t} V_P + \int \nabla \cdot (\rho \phi \mathbf{u}) dV = \int \nabla \cdot (k \nabla \phi) dV + SV_P$$
 (5.31)

ここで、 $V_P$  は注目セルの体積である。時間微分は差分法で離散化するとして、空間微分の離散化について考える。

発散を、ガウスの発散定理により次のように表す.

$$\int \nabla \cdot (\phi \mathbf{u}) dV = \int (\phi \mathbf{u}) \cdot \mathbf{n} dS \approx \sum \phi_f \mathbf{u}_f \cdot S_f$$
 (5.32)

ここで、n は領域表面の法線ベクトルを表す。 $S_f$  はセルを構成するそれぞれの面について垂直で、それぞれの面積を大きさとしてもつベクトル (面積ベクトル) である。ラプラシアンについても同様である。

$$\int \nabla \cdot (k\nabla \phi)dV = \int (k\nabla \phi) \cdot \boldsymbol{n}dS \approx \sum k_f (\nabla \phi)_f \cdot \boldsymbol{S}_f$$
 (5.33)

勾配についても、同様の考え方で次のように表される.

$$\int \nabla \phi dV = \int \phi \mathbf{n} dS \approx \sum \phi_f \mathbf{S}_f \tag{5.34}$$

さて、ここで未知なのは  $\phi_f$  や  $(\nabla \phi)_f$  といった面中心の値である。これらの表し方で離散化の精度が決まる。これらの補間や離散化の方法のことを、補間スキーム (interpolation scheme) とか離散化スキーム (discretization scheme) などという。 $\phi_f$  を次式で表す。

$$\phi_f = w\phi_P + (1 - w)\phi_N \tag{5.35}$$

ここで w は 重みで、線形補間を考えた場合、w は N-f 間の距離と P-N 間の距離の比で表される.

$$w = \frac{|x_f - x_N|}{|x_N - x_P|} \tag{5.36}$$

線形補間は差分法でいうところの中心差分にあたり、対流項で使うには問題がある. 対流項には、次の風上差分スキームなどを用いる.

$$\phi_f = \begin{cases} \phi_P & (\boldsymbol{u}_f \cdot \boldsymbol{S}_f \ge 0) \\ \phi_N & (\boldsymbol{u}_f \cdot \boldsymbol{S}_f < 0) \end{cases}$$
 (5.37)

面中心の勾配  $(\nabla \phi)_f$  については、 $(\nabla \phi)_f \cdot S_f$  の形で面の法線方向の勾配として離散化する。

$$(\nabla \phi)_f \cdot S_f = \frac{\phi_N - \phi_P}{|\mathbf{x}_N - \mathbf{x}_P|} |S_f|$$
 (5.38)

ただし、これは隣接するセルの中心間を結んだ線と面が直交している (orthogonal) 場合の式である。一般には直交しないため、OpenFOAM では補正が行われる。詳しくは Jasak の博士論文[14]を参照。

以上の方法で方程式 (5.29) を離散化すると、一般に次のような形で表せる.

$$A_P \phi_P + \sum A_N \phi_N = b \tag{5.39}$$

ここで  $A_P$ ,  $A_N$  は代数方程式の係数行列に相当するもの,b は代数方程式の右辺に

### 142 第5章 OpenFOAM のための数値流体力学入門

相当するものである. これを全セルで合成すると, 偏微分方程式に対応した代数方程式ができる.

# 5.4 圧力-速度連成

## 5.4.1 圧力方程式 🖙 4.7 節 (p.90)

運動方程式を半離散化すると、次式のように表される.

$$A_P u_P + \sum A_N u_N = -\nabla p \tag{5.40}$$

ここで A は係数で、添字の P は注目セルを、 N は注目セルの隣接セルを表す。 OpenFOAM では、右辺を除いて

$$A_P u_P + \sum A_N u_N = 0 \tag{5.41}$$

として、これを次式のように表す.

$$Au = H \tag{5.42}$$

これより、運動方程式は

$$Au = H - \nabla p \tag{5.43}$$

速度は次のように書ける.

$$u = \frac{H}{A} - \frac{1}{A} \nabla p \tag{5.44}$$

これを連続の式 (5.1) に代入すると

$$\frac{\partial \rho}{\partial t} + \nabla \cdot \left(\frac{\rho}{A} \mathbf{H} - \frac{\rho}{A} \nabla p\right) = 0 \tag{5.45}$$

となる. したがって

$$\nabla \cdot \left(\frac{\rho}{A} \nabla p\right) = \frac{\partial \rho}{\partial t} + \nabla \cdot \left(\frac{\rho}{A} \mathbf{H}\right) \tag{5.46}$$

を得る. これを圧力方程式という. 定常状態の場合は, 右辺の時間微分項が省かれる. 非圧縮性流体の場合は, 次式のようになる.

$$\nabla \cdot \left(\frac{1}{A} \nabla p\right) = \nabla \cdot \left(\frac{H}{A}\right) \tag{5.47}$$

圧力方程式を解いて得られた圧力から、式 (5.44) により新しい速度が求められる.

## **5.4.2** SIMPLE 法 \$\mathbb{G} \pi 4.8.1 \bar{q} (p.96)

OpenFOAM の定常解析ソルバーでは、圧力 – 速度連成手法として SIMPLE 法が 用いられている。一般的である Patankar による形式 [21] とは異なり、いくぶん単純 である。計算手順は以下のとおりである。

- 1. 運動方程式 (5.43) を解き、仮の速度を求める.
- 2. 圧力方程式 (5.46) あるいは (5.47) を解き、圧力を求める.
- 3. 式 (5.44) により速度を更新する.

以上の手順を残差が小さくなるまで繰り返す。これをイテレーションループという。 上の手順でそのまま計算すると、圧力の計算が発散しがちなため、ふつうは速度と 圧力の更新を緩和する不足緩和が用いられる。そのための不足緩和係数 (relaxation factor) は、問題に合わせてユーザーが調整する必要がある。

### **5.4.3** SIMPLEC 法 \$\mathbb{G} \pi 4.8.1 \bar{\pi} (p.96)

OpenFOAMでは、SIMPLE 法の収束性を改善した SIMPLEC 法に対応したソルバーもある。SIMPLEC 法は、圧力方程式などの式が少し異なるだけで、アルゴリズムは SIMPLE 法と同じである。SIMPLE 法と異なり、不足緩和は必要ないとされているが、一般的には必要になることが多い。

### **5.4.4** PISO 法 \$\mathbb{B}\mathbb{4.8.2}\mathbb{I}(p.98)

OpenFOAM の非定常解析ソルバーの一部では、PISO 法が用いられている。 Open-FOAM の形式では、計算手順は以下のとおりである.

- 1. 運動方程式 (5.43) を解き、仮の速度を求める.
- 2. 圧力方程式 (5.46) あるいは (5.47) を解き, 圧力を求める.
- 3. 式 (5.44) により速度を更新する.
- 4. 上記の圧力の計算および速度の更新を指定回数だけ繰り返す (通常は 2 回). これを圧力補正ループという.

以上の手順を必要な時間ステップ分繰り返す.

### **5.4.5** PIMPLE 法 ■ 4.8.3 項 (p.99)

OpenFOAM の非定常解析ソルバーでは、PISO 法と SIMPLE 法を組み合わせた "PIMPLE 法" が用いられている。これは、時間ステップの間に SIMPLE 法のループを入れたものである。

#### 144 第5章 OpenFOAM のための数値流体力学入門

- 1. 運動方程式 (5.43) を解き、仮の速度を求める.
- 2. 圧力方程式 (5.46) あるいは (5.47) を解き、圧力を求める.
- 3. 式 (5.44) により速度を更新する.
- 4. 上記の圧力の計算および速度の更新を指定回数だけ繰り返す (通常は2回).
- 5. 以上の手順を残差が小さくなるまで繰り返す.

以上の手順を必要な時間ステップ分繰り返す.

#### 5.4.6 圧力振動の回避

速度と圧力の値を同じ位置でもつコロケート格子 (co-located grid) では、単純な離散化方法だと圧力振動が起こることが知られている。これを避ける方法として、速度と圧力の値をもつ位置をずらしたスタッガード格子 (staggered grid) を用いる方法と、コロケート格子で Rhie-Chow 補間 (Rhie-Chow interpolation) [24] を用いる方法があり、OpenFOAM では後者の方法が採用されている。

圧力振動は、圧力勾配の離散化の方法から生じる。セル界面に補間された速度  $u_f$ は、式 (5.44) から次式で表される。

$$\boldsymbol{u}_f = \left(\frac{H}{A}\right)_f - \left(\frac{1}{A}\nabla p\right)_f \tag{5.48}$$

Rhie と Chow の方法では、上式を次式のように修正する.

$$\boldsymbol{u}_f = \left(\frac{H}{A}\right)_f - \left(\frac{1}{A}\right)_f (\nabla p)_f \tag{5.49}$$

これにより新たな項が加えられたことになるが、その項が圧力振動を抑制するはたらきをする.

OpenFOAM では、上式を流束  $\phi$  として表現している。ここで流束  $\phi$  は、セル界面の面積ベクトルを S として、圧縮性流体ソルバーでは  $\phi = \rho u \cdot S$ 、非圧縮性流体ソルバーでは  $\phi = u \cdot S$  である。OpenFOAM のソルバーにおいて、運動方程式の構築に  $\phi$  が用いられていたり、速度の更新とは別に  $\phi$  が更新されていたりするのは、この Rhie と Chow による補間法を用いているためである。

## 5.5 代数方程式の解法

### **5.5.1** 代数方程式の解法 15 4.7 節 (p.90), 5.4.1 項 (p.142)

偏微分方程式を有限体積法で離散化すると,次式のような代数方程式 (連立方程式) の形になる.

(5.50)

A は係数行列,b は右辺ベクトル,x は解ベクトルである.代数方程式を数値的に解く手法は,係数行列の性質に応じて使い分けられる.係数行列についての重要な性質の一つは,係数行列が対称(symmetric)であるかどうかである.対称性を利用できれば,計算時間や使用メモリ量を短縮できる可能性がある.圧力方程式のようなポアソン方程式の係数行列は対称,運動方程式のような対流項を含む方程式の係数行列は非対称である.

代数方程式を解く手法は、直接法 (direct method) と反復法 (iterative method) に分けられる。直接法は、連立方程式を手で解くときに用いるものと同じ系統の方法である。数値計算では LU 分解法や対称行列用の Cholesky 分解法などが用いられる。反復法は、反復計算によって x を真の解に収束させていく方法である。Gauss—Seidel 法などの手法がある。

有限体積法による離散化により得られる係数行列は、一般に値が 0 の要素を多く含む疎行列 (sparse matrix) になる.この性質を利用できれば、計算上の使用メモリ量を大幅に減らすことができる.直接法では、計算の途中で値が 0 の要素が非 0 になる (これを fill-in という) ことがあるため、使用メモリ量をあまり減らすことができない.反復法では fill-in は関係ないため、非 0 要素だけを記憶すればよく、使用メモリ量を大幅に減らすことができる.このため、流体解析では反復法がよく用いられる.

流体解析では共役勾配 (conjugate gradient: CG) 法および双共役勾配 (bi-conjugate gradient: BiCG) 法 (または、これを安定化した BiCGStab 法) が使われることが多い。 CG 法は対称行列用の手法で、BiCG 法は非対称行列用に対応した手法である。 CG 法は反復法の一種とされるが、反復計算の形式で表された直接法的な手法である。 n 元の方程式であれば、理論的には n 回の反復で解が求められる。ふつうは反復回数を減らす手法が一緒に用いられ、これを前処理 (preconditioning) という。前処理手法 (preconditioner) としては、fill-in を無視した Cholesky 分解法や、 LU 分解法である不完全 Cholesky 分解法、および不完全 LU 分解法が用いられる。不完全Cholesky 分解付き CG 法は、ICCG (incomplete Cholesky conjugate gradient) 法とよばれることがある。OpenFOAMでは、前処理付き CG 法/BiCG 法を一般化して PCG/PBiCG (preconditioned CG/BiCG) とよんでいる。

また、流体解析ではマルチグリッド (multigrid) 法 (多重格子法) という手法も用いられる。Gauss-Seidel 法などの反復法は、計算格子が細かいほど収束が遅くなることが知られている。この性質を利用して、細かさを変えた複数の計算格子を用いて反復法の収束性を改善しようというのがマルチグリッド法での考え方である。格子を

直接処理せずに代数的に行う、代数的マルチグリッド (algebraic multigrid: AMG) 法もある。これに対して、格子を直接処理する手法は幾何学的マルチグリッド (geometric multigrid) 法とよばれる。OpenFOAM では、これらを一般化して GAMG (geometric-algebraic multigrid) とよんでいる。

### 5.5.2 計算の収束 🖙 4.7 節 (p.90)

代数方程式の残差 (residual) ベクトルr を次式で定義する.

$$r = b - Ax \tag{5.51}$$

x が真の解であれば r=0 だが,数値計算では計算誤差が入り,r は 0 にはならない. 反復法では r がある程度 0 に近くなったら計算を打ち切り,そのときの x を解として採用する.ベクトルでは判断しにくいので,残差ベクトルのノルムが残差として用いられる. OpenFOAM では, $L_1$  ノルム(各成分の絶対値の和)を正規化したものが用いられている.

残差が小さくなり解が求められることを収束 (convergence) という. 収束の判定方法として 2 種類考えられる. 残差がある値以下になった場合と, 残差が初期残差に比べてある程度以下になった場合である. 前者の判定値を (絶対) 許容値 (tolerance), 後者の判定値を相対許容値 (relative tolerance) とよぶ.

流体解析の方程式は一般に非線形であり、反復計算が用いられることが多い、その場合、代数方程式は線形化された方程式である。反復計算の途中の方程式であるため、きちんと解く必要はなく、ほどほどで計算を打ち切ればよい、非定常解析の場合は、それぞれの時間ステップで解を求める必要があるため、反復計算の最後の残差をそれなりに小さくする必要がある。OpenFOAM の非定常解析ソルバーの場合、反復計算中と反復計算最後とで代数方程式ソルバーの判定値を別々に設定することができるようになっており、反復計算の最後だけ計算をより厳密にすることができる。

SIMPLE 法などにおける反復計算の収束判定には、代数方程式を解く前の残差である初期残差が用いられる。つくられた方程式の残差が解くまでもないほど小さければ、それを解いて得られる解は十分に方程式を満たすと判断する。反復計算の収束判定にも許容値と相対許容値があり、相対許容値は非定常解析で用いられる。

# 5.6 離散化スキーム F 4.6 節 (p.83)

離散化スキームについては、有限体積法の説明の中で簡単に述べた、数値解析の安定性や結果の精度に影響するため、本節で基本的なことを少し詳しく説明する、離散

化スキームはもともと差分法において開発されたものであるため、主に差分法における離散化スキームについて述べ、最後に有限体積法への適用について述べる.

# 5.6.1 差分近似

関数の微分を、有限個の点列上で表された変数による代数式で近似することを考える。 関数  $\phi(x)$  を考え、これを  $x+\Delta x$  でテーラー展開すると次式になる.

$$\phi(x + \Delta x) = \phi(x) + \frac{d\phi(x)}{dx} \Delta x + \cdots$$
 (5.52)

展開を2項で打ち切ると、次式を得る.

$$\frac{d\phi(x)}{dx} \approx \frac{\phi(x + \Delta x) - \phi(x)}{\Delta x} \tag{5.53}$$

これを関数  $\phi(x)$  の微分の差分近似という.

ここで、点の座標をそれぞれ  $x_1$ ,  $x_2$ , …,  $x_n$  と表す。これを格子点という。その中で注目している点を  $x_i$  とし、その前の点を  $x_{i+1}$ , その後の点を  $x_{i-1}$  などと表す (図 5.2)。点どうしの距離は  $\Delta x$  とする。また、 $\phi_i = \phi(x_i)$  と表す。 $\phi_{i+1}$  でテーラー展開すると次式になる。

$$\phi_{i+1} = \phi_i + \frac{d\phi_i}{dx} \Delta x + O(\Delta x^2)$$
 (5.54)

ここで、 $O(\Delta x^2)$  をオーダーといい、だいたいこの程度の大きさ (ここではせいぜい  $\Delta x^2$  くらい) という程度の意味である。テーラー展開を打ち切る場合、このオーダー が打ち切り誤差であり、近似精度を表す指標となる。上式を変形する。

$$\frac{d\phi_i}{dx} = \frac{\phi_{i+1} - \phi_i}{\Delta x} + O(\Delta x) \tag{5.55}$$

右辺第2項を無視して

$$\frac{d\phi_i}{dx} \approx \frac{\phi_{i+1} - \phi_i}{\Delta x} \tag{5.56}$$

とすると、ここで無視した  $O(\Delta x)$  は  $\Delta x$  の 1 乗のオーダーなので、この差分近似の精度は 1 次 (first-order) であるとか、1 次精度 (first-order accurate) であるという。この差分は  $x_i$  の前の  $x_{i+1}$  を使ったものなので、前進差分 (forward difference) という。同様に、後退差分 (backward difference) が次式で表される。

$$x_{i-1}$$
  $x_i$   $x_{i+1}$ 

図 5.2 格子点

$$\frac{d\phi_i}{dx} \approx \frac{\phi_i - \phi_{i-1}}{\Delta x} \tag{5.57}$$

関数  $\phi(x)$  について、 $\phi_{i+1}$ 、 $\phi_{i-1}$  でそれぞれテーラー展開を行うと、次のようになる。

$$\phi_{i+1} = \phi_i + \frac{d\phi_i}{dx} \Delta x + \frac{1}{2} \frac{d^2 \phi_i}{dx^2} \Delta x^2 + O(\Delta x^3)$$

$$\phi_{i-1} = \phi_i - \frac{d\phi_i}{dx} \Delta x + \frac{1}{2} \frac{d^2 \phi_i}{dx^2} \Delta x^2 + O(\Delta x^3)$$
(5.58)

ここで、 $\phi_{i+1} - \phi_{i-1}$  をとると

$$\frac{d\phi_i}{dx} = \frac{\phi_{i+1} - \phi_{i-1}}{2\Delta x} + O(\Delta x^2) \tag{5.59}$$

となり、これより次式を得る.

$$\frac{d\phi_i}{dx} \approx \frac{\phi_{i+1} - \phi_{i-1}}{2\Delta x} \tag{5.60}$$

これを中心差分 (central difference) といい, 2 次精度である.

また、 $\phi_{i+1} + \phi_{i-1}$  をとると

$$\phi_{i+1} = \phi_i + \frac{d\phi_i}{dx} \Delta x + \frac{1}{2} \frac{d^2 \phi_i}{dx^2} \Delta x^2 + \frac{1}{6} \frac{d^3 \phi_i}{dx^3} + O(\Delta x^4)$$

$$\phi_{i-1} = \phi_i - \frac{d\phi_i}{dx} \Delta x + \frac{1}{2} \frac{d^2 \phi_i}{dx^2} \Delta x^2 - \frac{1}{6} \frac{d^3 \phi_i}{dx^3} + O(\Delta x^4)$$
(5.61)

なので、3階微分の項が打ち消されて

$$\phi_{i+1} + \phi_{i-1} = 2\phi_i + \frac{d^2\phi_i}{dx^2} \Delta x^2 + O(\Delta x^4)$$
 (5.62)

となり、これより次式を得る.

$$\frac{d^2\phi_i}{dx^2} = \frac{\phi_{i+1} - 2\phi_i + \phi_{i-1}}{\Delta x^2} + O(\Delta x^2)$$
 (5.63)

したがって

$$\frac{d^2\phi_i}{dx^2} \approx \frac{\phi_{i+1} - 2\phi_i + \phi_{i-1}}{\Delta x^2} \tag{5.64}$$

となり、これは2階微分の中心差分であり、2次精度である.

# 5.6.2 風上差分 ☞ 4.9.2 項 (p.104)

次の移流方程式を考える.

$$\frac{\partial \phi}{\partial t} + u \frac{\partial \phi}{\partial x} = 0 \tag{5.65}$$

ここで u は移流速度で、特に断らない限り u>0 とする、これを差分近似で表す、時間微分の項を前進差分、空間微分の項 (移流項) を中心差分で近似する。

$$\frac{\phi_i^{n+1} - \phi_i^n}{\Delta t} + u \frac{\phi_{i+1}^n - \phi_{i-1}^n}{2\Delta x} = 0$$
 (5.66)

ここで、変数の右肩のnなどは時間ステップを表す、変形して次のように表す、

$$\phi_i^{n+1} = \phi_i^n - \frac{1}{2}c(\phi_{i+1}^n - \phi_{i-1}^n)$$
 (5.67)

ここで  $c=u\Delta t/\Delta x$  であり、クーラン数 (Courant number) とよばれる. このように、n+1 の値を n の変数だけで表すことができる方法を時間に関する陽解法 (explicit scheme) という. また、そうでないものを陰解法 (implicit scheme) という. 陽解法は陰解法よりも計算が簡単になる代わりに、クーラン数についての安定条件があり、 $|c| \leq 1$  である必要がある. この条件は CFL (Courant – Friedrich – Lewy) 条件とか、クーラン条件などとよばれる. これは、時間刻み幅  $\Delta t$  が制限されることを意味する. 上式は次のように表される.

$$\phi_i^{n+1} = -\frac{1}{2}c\phi_{i+1}^n + \phi_i^n + \frac{1}{2}c\phi_{i-1}^n$$
 (5.68)

ここでは u>0 を考えているので c>0 であり、右辺第 1 項の係数が負になる.これは、もし  $\phi>0$  だとしても場合によっては  $\phi_i^{n+1}$  の値が負になりうることを意味しており、数値的には不自然な振動として現れる.それでも問題がない場合もあるが、たとえば  $\phi$  が絶対温度の場合は、物理的にあり得ない値を生じることになる.

この問題を回避する単純な方法として、空間微分に後退差分を適用する方法がある、

$$\frac{\phi_i^{n+1} - \phi_i^n}{\Delta t} + u \frac{\phi_i^n - \phi_{i-1}^n}{\Delta x} = 0$$
 (5.69)

変形して

$$\phi_i^{n+1} = \phi_i^n - c(\phi_i^n - \phi_{i-1}^n) \tag{5.70}$$

と表すと, この場合は

$$\phi_i^{n+1} = (1-c)\phi_i^n + c\phi_{i-1} \tag{5.71}$$

となり、c>0 かつ CFL 条件により  $c\le 1$  なので、右辺の係数はすべて正になる。このように、移流項の離散化に後退差分を用いる方法を風上差分という。この名前は風上から値を補間することを意味しており、実際は流速 u の正負を調べて補間方向を切

り替える. 一般に、風上側に補間の重みをつける差分を風上差分 (upwind difference) あるいは上流差分 (upstream difference) とよぶ.

上式は、次式のように変形できる.

$$\phi_i^{n+1} = \phi_i^n - \frac{1}{2}c(\phi_{i+1}^n - \phi_{i-1}^n) + \frac{1}{2}c(\phi_{i+1}^n - 2\phi_i^n + \phi_{i-1}^n)$$
 (5.72)

右辺第2項までは中心差分であり、第3項は空間の2階微分(拡散を意味する)を離散化した形になっている。したがって、風上差分は中心差分に数値的な拡散を加えて安定化したものと考えることができる。それゆえ、解がなまることになる。

上記のように、方程式を差分近似して解く方法を有限差分法 (finite difference method, FDM)、あるいは単純に差分法という。また、方程式の離散化の方法のことを、差分法では差分スキームという。ここでは風上差分として後退差分を用いたので、1 次精度風上差分スキームという。

ここで見たように、移流項 (advection term) の離散化には特別な扱いが必要である。これは、運動方程式では  $\nabla \cdot (\rho u u)$ 、一般化して  $\nabla \cdot (\rho \phi u)$  のような形をした対流項 (convection term) の離散化に特別な扱いが必要であることを意味する.

#### ■流束による表現

移流方程式は、次式のようにも離散化できる.

$$\frac{\phi_i^{n+1} - \phi_i^n}{\Delta t} + \frac{f_{i+1/2}^n - f_{i-1/2}^n}{\Delta x} = 0 \tag{5.73}$$

ここで、 $f=u\phi$  は流束 (flux) であり、i+1/2 は i と i+1 の間の位置  $x_{i+1/2}=x_i+\Delta x/2$  を意味する。これは、格子点を囲む格子を考えたときの格子界面の位置である。この差分は 2 次精度である。ここでは u は一定なので、便宜上、次のように表す。

$$\frac{\phi_i^{n+1} - \phi_i^n}{\Delta t} + u \frac{\phi_{i+1/2}^n - \phi_{i-1/2}^n}{\Delta \tau} = 0 \tag{5.74}$$

整理すると、次のようになる。

$$\phi_i^{n+1} = \phi_i^n - c(\phi_{i+1/2}^n - \phi_{i-1/2}^n)$$
 (5.75)

このように表現した場合、中心差分は以下のようになる.

$$\phi_{i+1/2} = \frac{1}{2}(\phi_{i+1} + \phi_i)$$

$$\phi_{i-1/2} = \frac{1}{2}(\phi_i + \phi_{i-1})$$
(5.76)

これは格子界面の値を格子点の値で線形補間することを意味している.

風上差分の場合は、次のようになる.

$$\phi_{i+1/2} = \phi_i 
\phi_{i-1/2} = \phi_{i-1}$$
(5.77)

これは、格子界面の値を上流の格子点からそのままもってくることを意味している (図5.3 の UD). 流速 u の符号を考慮すると、次式のようになる.

$$\phi_{i+1/2} = \begin{cases} \phi_i & (u \ge 0) \\ \phi_{i+1} & (u < 0) \end{cases}$$
 (5.78)

![](_page_3_Figure_6.jpeg)

図 5.3 風上差分

### 5.6.3 高次精度風上差分

# ■線形風上差分 (2 次精度風上差分)

1 次精度風上差分では、格子界面の値として上流の値をそのままスライドしたが、 それを線形補間する方法が考えられる (図 5.3 の LUD). この方法を線形風上差分 (linear upwind difference) といい、2 次精度である.

$$\phi_{i+1/2} = \phi_i + \frac{\partial \phi_i}{\partial x} (x_{i+1/2} - x_i) = \phi_i + \frac{\phi_i - \phi_{i-1}}{\Delta x} \frac{\Delta x}{2}$$

$$= \phi_i + \frac{1}{2} (\phi_i - \phi_{i-1})$$
(5.79)

流速 u の正負を考慮すると、次のようになる.

$$\phi_{i+1/2} = \begin{cases} \phi_i + \frac{1}{2}(\phi_i - \phi_{i-1}) & (u \ge 0) \\ \phi_{i+1} + \frac{1}{2}(\phi_{i+1} - \phi_{i+2}) & (u < 0) \end{cases}$$
 (5.80)

このスキームは、2次精度風上差分とよばれることが多い。

#### QUICK

QUICK (quadratic upstream interpolation for convective kinematics) [15] は, 2 次多項式を構成して格子界面の値を補間する (図 5.3). 次式を考える.

$$\phi(x) = a_0 + a_1(x - x_i) + a_2(x - x_i)^2$$
(5.81)

係数  $a_0$ ,  $a_1$ ,  $a_2$  を  $\phi_{i-1}$ ,  $\phi_i$ ,  $\phi_{i+1}$  を使って求め,  $\phi_{i+1/2}$  を求める. 最終的に次式が得られる.

$$\phi_{i+1/2} = \frac{1}{8}(3\phi_{i+1} + 6\phi_i - \phi_{i-1}) \tag{5.82}$$

この式は、次式のように表すことができる.

$$\phi_{i+1/2} = \frac{1}{2}(\phi_i + \phi_{i+1}) - \frac{1}{8}(\phi_{i+1} - 2\phi_i + \phi_{i-1})$$
 (5.83)

これは、中心差分に修正項が付加されたものであることを意味している.

流速 u の正負を考慮すると、次のようになる.

$$\phi_{i+1/2} = \begin{cases} \frac{1}{8} (3\phi_{i+1} + 6\phi_i - \phi_{i-1}) & (u \ge 0) \\ \frac{1}{8} (3\phi_i + 6\phi_{i+1} - \phi_{i+2}) & (u < 0) \end{cases}$$
 (5.84)

補間自体は3次精度であるが、差分としては2次精度になる.

## 5.6.4 単調性を保つ高次精度風上差分スキーム

## ■有界性と単調性

離散化スキームについて、物理量の有界性や単調性が問題になる。物理量が増減せずに移流するだけの場合、物理量は初期値の最小値と最大値の範囲内にある。これを有界性 (boundedness) といい、有界性を性質としてもつとき、有界である (bounded) という。定常の現象の場合も同様で、発熱や冷却のない熱伝導問題では、領域内の温度は境界の温度の最小値と最大値の間にある。このような問題に対して有界性をもたない離散化スキームを用いた場合、非物理的な解を生じる可能性がある。

単調性 (monotonicity) は物理量がオーバーシュートやアンダーシュートなどの振動を起こさない性質で、これをもつとき、単調である (monotone) という、単調であるときは振動が起こらず、有界性を破らないので、有界であると考えてよい。

有界性は計算の安定性と関連付けられ、両者はほぼ同じ意味で使われることがある。 中心差分は単調でなく、有界でもない、1次精度風上差分は単調で、有界である。一 般に、単純な高次精度差分スキームは単調でない。

#### ■高解像度スキーム

移流をきれいに解きたい場合、高解像度のスキームが必要になる。まず、高精度なものが必要になるが、一般に高次精度差分スキームは解に振動を生じる。一方で、振動を抑えられる1次精度風上差分では解が減衰してしまう。では、この両者を組み合わせたらどうか。一定の割合で混合するのではなく、必要に応じて両者を切り替えれば、平均的に高精度で有界なスキームを構成できる。

このような考えのもとに構成されたものとして、TVD スキームがある.

#### ■ TVD スキーム

TVD スキーム<sup>[16,17]</sup> は、単調性を保つために全変動 (total variation: TV) という量を用いる. TV は次式で定義される.

$$TV(\phi^n) = \sum_{i} |\phi_{i+1}^n - \phi_i^n|$$
 (5.85)

これは隣どうしの格子点の値の変化の総和であり、全体的な値の凸凹具合を表している。ある形の分布が増減なしで移流するとき、本来は形を変えないので、全体的な値の凸凹具合は変わらないはずであり、少なくとも増えることはないはずである。したがって、単調性を維持する条件として以下の条件が考えられる。

$$TV(\phi^{n+1}) \le TV(\phi^n) \tag{5.86}$$

これを TVD (total variation diminishing) 条件という. この条件を満たすスキームを, TVD スキームとよぶ.

格子界面の値について、1 次風上差分による値を  $\phi_{\mathrm{UD}}$ 、中心差分による値を  $\phi_{\mathrm{CD}}$  として、次式のように構成する.

$$\phi_{i+1/2} = \phi_{\text{UD}} + \psi(\phi_{\text{CD}} - \phi_{\text{UD}})$$
 (5.87)

整理すると、次式になる.

$$\phi_{i+1/2} = \phi_i + \frac{1}{2}\psi(\phi_{i+1} - \phi_i)$$
 (5.88)

ここで、 $\psi$  はスキームを調整する関数で、流束制限関数 (flux limiter function) とよばれる。これを何の関数にするかが問題だが、ここでは、解の振動を抑えつつ減衰も抑えたい。また、解の変化が大きいところだけで減衰が効けばよいので、解の変化を検出できればよい。解の変化の大きさを測るパラメタとして、連続する格子点の値の変化の比 (consecutive gradient)  $r_i$  を考える。

$$r_i = \frac{\Delta \phi_{i-1/2}}{\Delta \phi_{i+1/2}} \tag{5.89}$$

 $\psi$  はこの  $r_i$  の関数とする.

スキームが TVD 条件を満たすための  $\psi(r)$  の条件を求めると、以下のようになる.

$$\begin{cases} \psi(r) = 0 & (r \le 0) \\ \psi(r) \le 2r & (0 < r < 1) \\ \psi(r) \le 2 & (r \ge 1) \end{cases}$$
 (5.90)

1 次精度風上差分,中心差分,2 次精度風上差分,QUICK をそれぞれ制限関数の 形で次のように表すことができる.

1 次精度風上差分 
$$\psi(r) = 0 \tag{5.91}$$

中心差分 
$$\psi(r) = 1 \tag{5.92}$$

2 次精度風上差分 
$$\psi(r) = r \tag{5.93}$$

QUICK 
$$\psi(r) = \frac{3+r}{4} \tag{5.94}$$

1 次精度風上差分は TVD 条件を満たすが、中心差分、2 次精度風上差分、QUICK は部分的にしか満たさない (図 5.4).

任意の 2 次精度差分スキームを中心差分と 2 次精度風上差分の混合で表すと, 2 次精度 TVD スキームの領域を限定することができる.

さまざまな制限関数が提案されている.以下に、代表的なものを挙げる[18].

![](_page_1_Figure_13.jpeg)

UD:1次精度風上差分

CD:中心差分

LUD: 2次精度風上差分

図 5.4 TVD 条件

$$\mathbf{minmod} \qquad \qquad \psi(r) = \max(0, \min(r, 1)) \tag{5.95}$$

**superbee** 
$$\psi(r) = \max(0, \min(2r, 1), \min(r, 2))$$
 (5.96)

van Leer 
$$\psi(r) = \frac{r + |r|}{1 + r} \tag{5.97}$$

van Albada 
$$\psi(r) = \frac{r + r^2}{1 + r^2}$$
 (5.98)

**UMIST** 
$$\psi(r) = \max\left(0, \min\left(2r, \frac{1+3r}{4}, \frac{3+r}{4}, 2\right)\right)$$
 (5.99)

$$\mathbf{MUSCL}^{[19]} \qquad \psi(r) = \max\left(0, \min\left(2r, \frac{1+r}{2}, 2\right)\right) \tag{5.100}$$

ここで、 $\min(a,b,...)$  は引数のうちで最小の値をとり、 $\max(a,b,...)$  は引数のうちで最大の値をとる。上記はすべて TVD 条件を満たし、2 次精度である (図 5.5). minmod は 2 次精度領域の下限を与え、superbee は上限を与える.

![](_page_2_Figure_8.jpeg)

図 5.5 2 次精度 TVD スキーム

OpenFOAM では、次のような単純な制限付き線形差分スキーム (limited linear difference scheme) が用意されている.

$$\psi(r) = \max\left(0, \min\left(\frac{2}{k}r, 1\right)\right) \tag{5.101}$$

k は 0 から 1 の間の値をとるパラメタで、k が小さいほど中心差分スキームに近づき、k が大きいほど TVD スキームに近づく、k=1 で TVD 条件を満たす。

## ■勾配制限

高次精度スキームの数値振動を抑制する方法として、勾配を制限するという考え方

もある。たとえば、線形風上差分は勾配制限関数 (slope limiter)  $\psi_f$  を用いて以下のように書ける。

 $\phi_{i+1/2} = \phi_i + \psi_f \left(\frac{\partial \phi}{\partial x}\right)_i (x_{i+1/2} - x_i) \tag{5.102}$ 

勾配制限関数はいくつか提案されているが、Barth and Jespersen の方法  $^{[20]}$  がベースになっている。これは、 $\phi_{i+1/2}$  が次式を満たすようにするものである。

$$\min(\phi_i, \phi_{i+1}) \le \phi_{i+1/2} \le \max(\phi_i, \phi_{i+1}) \tag{5.103}$$

要するに、格子界面の値が両側の格子点の値を超えないようにするということである. 制限関数を用いると

$$\min(\phi_i, \phi_{i+1}) \le \phi_i + \psi_f \left(\frac{\partial \phi}{\partial x}\right)_i (x_{i+1/2} - x_i) \le \max(\phi_i, \phi_{i+1}) \tag{5.104}$$

となり、上式から φ<sub>i</sub> を引いて

$$\min(0, \phi_{i+1} - \phi_i) \le \psi_f \left(\frac{\partial \phi}{\partial x}\right)_i (x_{i+1/2} - x_i) \le \max(0, \phi_{i+1} - \phi_i)$$
 (5.105)

が得られる. ここで、勾配制限を用いない格子界面の値を  $\phi_{i+1/2}^*$  とすると

$$\phi_{i+1/2}^* - \phi_i = \left(\frac{\partial \phi}{\partial x}\right)_i (x_{i+1/2} - x_i)$$
 (5.106)

と書けるので

$$\frac{\min(0,\phi_{i+1}-\phi_i)}{\phi_{i+1/2}^*-\phi_i} \le \psi_f \le \frac{\max(0,\phi_{i+1}-\phi_i)}{\phi_{i+1/2}^*-\phi_i}$$
 (5.107)

である. また,

$$\begin{cases} \delta \phi^{\max} = \max(0, \phi_{i+1} - \phi_i) \\ \delta \phi^{\min} = \min(0, \phi_{i+1} - \phi_i) \end{cases}$$
 (5.108)

とすると、 $\psi_f$  は 1 を超えないものとして、次式が得られる.

$$\psi_{f} = \begin{cases}
\min\left(1, \frac{\delta\phi^{\max}}{\phi_{i+1/2}^{*} - \phi_{i}}\right) & \phi_{i+1/2}^{*} > \phi_{i} \\
\min\left(1, \frac{\delta\phi^{\min}}{\phi_{i+1/2}^{*} - \phi_{i}}\right) & \phi_{i+1/2}^{*} < \phi_{i} \\
1 & \phi_{i+1/2}^{*} = \phi_{i}
\end{cases} (5.109)$$

これを格子界面ごとに計算して、その最小値を格子点勾配の制限関数とする.

制限関数は界面ごとに計算するが、求めたいものは格子点についての制限関数である。したがって、格子点のすべての隣接格子点の値を考慮して制限関数を求める方法も考えられる。格子点 i の界面 j に面する隣接格子点の値を  $\phi_{ij}$  と書くことにすると、 $\delta\phi^{\max}$ 、 $\delta\phi^{\min}$  を次のように決めることもできる。

$$\begin{cases} \delta \phi^{\max} = \max(0, \max_{j} (\phi_{ij} - \phi_{i})) \\ \delta \phi^{\min} = \min(0, \min_{j} (\phi_{ij} - \phi_{i})) \end{cases}$$
 (5.110)

ここで  $\max_j$ ,  $\min_j$  は格子点 i のすべての界面についての最大値および最小値を求める関数である.

### 5.6.5 有限体積法における風上差分スキーム

これまでは差分法の離散化スキームについて考えてきたが、ここでは有限体積法における離散化スキームについて考える。有限体積法ではセルの面の値を補間する必要があり、これまで述べてきた格子界面の値の考え方を使うことができる。以下では、3次元の非構造メッシュを想定し、注目セル、隣接セル、注目セルと隣接セルに挟まれた面をそれぞれP,N,fで表し、それぞれの中心位置を $x_P$ , $x_N$ , $x_f$ , それぞれの位置での値を $\phi_P$ , $\phi_N$ , $\phi_f$  などと表す (図 5.1).

## ■中心差分

有限体積法において差分法の中心差分にあたるものは、次の線形補間である.

$$\phi_f = w\phi_P + (1 - w)\phi_N \tag{5.111}$$

ここでwは重みで、N-f間の距離とP-N間の距離の比で表される.

$$w = \frac{|\boldsymbol{x}_f - \boldsymbol{x}_N|}{|\boldsymbol{x}_N - \boldsymbol{x}_P|} \tag{5.112}$$

# ■ 1 次精度風上差分

1 次精度風上差分では、面中心の値を風上側からもってくる.

$$\phi_f = \begin{cases} \phi_P & (\boldsymbol{u} \cdot \boldsymbol{S}_f > 0) \\ \phi_N & (\boldsymbol{u} \cdot \boldsymbol{S}_f < 0) \end{cases}$$
 (5.113)

ここで、 $S_f$  は面の法線方向ベクトルである.

### ■線形風上差分

線形風上差分は、次式のように表現できる.

$$\phi_f = \begin{cases} \phi_P + (\nabla \phi)_P \cdot (\boldsymbol{x}_f - \boldsymbol{x}_P) & (\boldsymbol{u} \cdot \boldsymbol{S}_f > 0) \\ \phi_N + (\nabla \phi)_N \cdot (\boldsymbol{x}_f - \boldsymbol{x}_N) & (\boldsymbol{u} \cdot \boldsymbol{S}_f < 0) \end{cases}$$
(5.114)

### ■ TVD スキーム

TVD スキームは、1 次風上差分による値を  $\phi_{\mathrm{UD}}$ 、中心差分による値を  $\phi_{\mathrm{CD}}$  とすると、次式のように表される。

$$\phi_f = \phi_{\rm UD} + \psi(\phi_{\rm CD} - \phi_{\rm UD}) \tag{5.115}$$

rの計算には格子点が三つ必要になるが、非構造メッシュでは一般に面を挟んだ二つのセル値を考え、三つのセル値は扱いにくいため、計算には工夫が必要である.

# 5.7 乱流モデル 1 4.4 節 (p.67), 5.1.7 項 (p.137)

乱流現象の解析には、乱流モデルというものが用いられる。本節では、乱流モデル について概説する。

## 5.7.1 層流と乱流

水道の蛇口を少しだけ開くと、なめらかな水の筋ができる。蛇口を大きく開いていくと、表面の荒れた流れになる。あるいは、タバコや線香から立ち上る煙は、周りの空気を動かさないようにそっとしておけば、真上に向かってきれいな層をつくる。周りの空気を動かすと、煙は無数の渦をつくり、複雑な模様を描く。落ち着いていてきれいな様相を示す流れを層流 (laminar flow) といい、乱れて複雑な様相を示す流れを乱流 (turbulence) という。

層流と乱流を区別するパラメタとして、レイノルズ数 (Reynolds number) がある. レイノルズ数 Re は、代表速度を U、代表長さを L、流体の密度を  $\rho$ 、粘性係数を  $\mu$ 、動粘性係数を  $\nu$  とすると、次式で定義される.

$$Re = \frac{\rho UL}{\mu} = \frac{UL}{\nu} \tag{5.116}$$

流速を大きくしていくとレイノルズ数は大きくなっていき、あるところで乱流状態になる。乱流状態になるときのレイノルズ数を、臨界レイノルズ数という。臨界レイノルズ数の値は流れによるが、一般に、レイノルズ数が 1000 のオーダー以上であれば乱流と見なすことができる。

## 5.7.2 レイノルズ平均ナビエーストークス方程式

## ■レイノルズ平均ナビエーストークス方程式

乱流は、大小の渦 (eddy) の非定常的な生成・消滅が生じる複雑な流れであるが、エンジニアリングにおいて興味があるのは、その平均的な挙動である。そのため、乱流の情報を得るために、乱流の支配方程式に対して平均化が施される。

乱流の挙動はきわめて複雑であるが、近年の数値計算による検証により、乱流現象も層流と同様に、ナビエ-ストークス方程式で表現できると考えられている。非圧縮性流体を考えると、ナビエ-ストークス方程式は次式で表される。

$$\frac{\partial \boldsymbol{u}}{\partial t} + \nabla \cdot (\boldsymbol{u}\boldsymbol{u}) = -\nabla p + \nabla \cdot (2\nu D) \tag{5.117}$$

ここで、u は速度、p は密度で割られた圧力である。D は速度勾配の対称部分で、次式で表される。

$$D = \frac{1}{2} \left\{ \nabla \boldsymbol{u} + (\nabla \boldsymbol{u})^T \right\}$$
 (5.118)

また、連続の式は次のようになる.

$$\nabla \cdot \boldsymbol{u} = 0 \tag{5.119}$$

さて、ナビエ-ストークス方程式の平均化を考える。平均化の方法として、時間平均やアンサンブル平均 (個数平均) などが考えられる。ここでは、アンサンブル平均を考える。 速度 u の平均  $\bar{u}$  を次式で定義する。

$$\bar{\boldsymbol{u}} = \frac{1}{n} \sum_{i=1}^{n} \boldsymbol{u}_{i} \tag{5.120}$$

ここで、n は個数である。n 回実験を行い、その平均をとるイメージである。速度 u は平均  $\bar{u}$  と変動成分 u' に分けられる。

$$\boldsymbol{u} = \bar{\boldsymbol{u}} + \boldsymbol{u}' \tag{5.121}$$

これをレイノルズ分解という. アンサンブル平均には、次のような性質がある.

$$\bar{\bar{u}} = \bar{u}$$

$$\bar{\bar{u}}\bar{u} = \bar{u}\bar{u}$$

$$\bar{u}' = \bar{\bar{u}}\bar{u}' = \bar{u}'\bar{u} = \bar{u}'\bar{u}'\bar{u}' = 0$$

$$\bar{u}'\bar{u}' \neq 0$$

$$(5.122)$$

このような性質をもつ平均を、レイノルズ平均 (Reynolds averaging) という.

連続の式の平均化を考える. レイノルズ分解により

$$\nabla \cdot \bar{\boldsymbol{u}} + \nabla \cdot \boldsymbol{u}' = 0 \tag{5.123}$$

となり、これにレイノルズ平均を適用すると

$$\nabla \cdot \bar{\boldsymbol{u}} = 0 \tag{5.124}$$

となる. これより次式を得る.

$$\nabla \cdot \boldsymbol{u}' = 0 \tag{5.125}$$

ナビエ-ストークス方程式の平均化を考える。まず、ナビエ-ストークス方程式に レイノルズ分解を適用する。

$$\frac{\partial \bar{\boldsymbol{u}}}{\partial t} + \frac{\partial \boldsymbol{u}'}{\partial t} + \nabla \cdot (\bar{\boldsymbol{u}}\bar{\boldsymbol{u}} + \bar{\boldsymbol{u}}\boldsymbol{u}' + \boldsymbol{u}'\bar{\boldsymbol{u}} + \boldsymbol{u}'\boldsymbol{u}') 
= -\nabla \bar{\boldsymbol{p}} - \nabla \boldsymbol{p}' + \nabla \cdot (2\nu \bar{D}) + \nabla \cdot (2\nu D')$$
(5.126)

両辺にレイノルズ平均を適用すると、次式を得る.

$$\frac{\partial \bar{u}}{\partial t} + \nabla \cdot (\bar{u}\bar{u}) = -\nabla \bar{p} + \nabla \cdot (2\nu \bar{D} - \overline{u'u'})$$
 (5.127)

もとの式と比較すると、速度や圧力などが平均値に置き換わったのに加え、 $\overline{u'u'}$  の項が加わった形になっている。この項は密度をかけると応力の単位になるため、レイノルズ応力 (Reynolds stress) とよばれる。また、二つの速度の変動成分の積の形をしているので、2 次相関、2 重相関、2 次モーメントなどとよばれる。レイノルズ平均化されたナビエーストークス方程式のことを、レイノルズ平均ナビエーストークス (Reynolds-Averaged Navier – Stokes: RANS) 方程式という。

# ■レイノルズ応力輸送方程式

レイノルズ応力が不明なため、レイノルズ応力の輸送方程式を求めてみる. 式 (5.126) と式 (5.127) の差をとると、次式を得る.

$$\frac{\partial \mathbf{u}'}{\partial t} + \nabla \cdot (\mathbf{u}'\bar{\mathbf{u}}) = -\nabla p' + \nabla \cdot (2\nu D' + \overline{\mathbf{u}'\mathbf{u}'} - \bar{\mathbf{u}}\mathbf{u}' - \mathbf{u}'\mathbf{u}')$$
 (5.128)

これを添字表記 (総和規約を用いる) で表すと

$$\frac{\partial u_i'}{\partial t} + \frac{\partial}{\partial x_k} (u_i' \bar{u_k}) = -\frac{\partial}{\partial x_i} p' + \frac{\partial}{\partial x_k} (2\nu D_{ik}' + \overline{u_i' u_k'} - \bar{u_i} u_k' - u_i' u_k')$$
 (5.129)

となり、これより  $u_i' \frac{\partial u_j'}{\partial t} + u_j' \frac{\partial u_i'}{\partial t}$  を構成し、両辺に対してレイノルズ平均を適用す

161

ると、次式を得る.

$$\frac{\partial}{\partial t}(R_{ij}) + \frac{\partial}{\partial x_k}(R_{ij}\bar{u_k}) = P_{ij} + \Pi_{ij} - \varepsilon_{ij} + \frac{\partial}{\partial x_k}(J_{ijk}^T + J_{ijk}^P + J_{ijk}^V) \quad (5.130)$$

ここで, $R_{ij} = \overline{u_i' u_j'}$  はレイノルズ応力, $P_{ij}$  は生成項

$$P_{ij} = -R_{ik} \frac{\partial \bar{u}_j}{\partial x_k} - R_{jk} \frac{\partial \bar{u}_i}{\partial x_k}$$
 (5.131)

 $\Pi_{ij}$  は圧力 – ひずみ相関項

$$\Pi_{ij} = \overline{p'\left(\frac{\partial u_i'}{\partial x_j} + \frac{\partial u_j'}{\partial x_i}\right)}$$
 (5.132)

 $\epsilon_{ij}$  は散逸項

$$\varepsilon_{ij} = 2\nu \frac{\overline{\partial u_i'}}{\partial x_k} \frac{\partial u_j'}{\partial x_k} \tag{5.133}$$

 $J_{ijk}^T$ ,  $J_{ijk}^P$ ,  $J_{ijk}^V$  はそれぞれ速度変動,圧力変動,粘性による拡散流束である.

$$J_{ijk}^{T} = -\overline{u_i'u_j'u_k'}$$

$$J_{ijk}^{P} = -(\overline{p'u_i'}\delta_{jk} + \overline{p'u_j'}\delta_{ik})$$

$$J_{ijk}^{V} = \nu \frac{\partial R_{ij}}{\partial x_k}$$
(5.134)

2 次相関  $\overline{u_i'u_j'}$  を求めるために式 (5.130) を導いたが、新たに 3 次相関  $\overline{u_i'u_j'u_k'}$  の項が現れている。 さらに、3 次相関の方程式を導いても 4 次相関の項が生じ、どこまでやっても終わらないため、どこかでモデル化を行う必要がある。

# ■乱流エネルギー輸送方程式

乱流エネルギー (turbulent energy) を  $k = \overline{u_i'u_i'}/2$  として定義すると、式 (5.130) の縮約から、次式の乱流エネルギーの輸送方程式が得られる.

$$\frac{\partial k}{\partial t} + \frac{\partial k \bar{u}_j}{\partial x_j} = P_k - \varepsilon + \frac{\partial}{\partial x_j} (J_j^{Tk} + J_j^{Pk} + J_j^{Vk})$$
 (5.135)

ここで、 $P_k$  は乱流エネルギー生成項

$$P_k = -R_{ij} \frac{\partial \bar{u_i}}{\partial x_j} \tag{5.136}$$

ε はエネルギー散逸率 (dissipation rate)

$$\varepsilon = \nu \frac{\overline{\partial u_i'}}{\partial x_j} \frac{\partial u_i'}{\partial x_j} \tag{5.137}$$

 $J_j^{Tk}$ ,  $J_j^{Pk}$ ,  $J_j^{Vk}$  はそれぞれ速度変動, 圧力変動, 粘性による拡散流束で

$$J_j^{Tk} = -\frac{1}{2} \overline{u_i' u_i' u_j'}$$

$$J_j^{Pk} = -\overline{p' u_j'}$$

$$J_j^{Vk} = \nu \frac{\partial k}{\partial x_j}$$

$$(5.138)$$

である. 式 (5.135) においては, 式 (5.130) にあった圧力 – ひずみ相関項に関する項が消えている. この項は, 速度変動の大きさには影響せず, 速度変動の各方向成分への分配に寄与する.

## ■運動エネルギー輸送方程式

同様にして、平均流の運動エネルギーの輸送方程式を求める。平均流の運動エネルギーを  $K=\bar{u_i}\bar{u_i}/2$  として、平均流の運動エネルギーの輸送方程式は次式で表される。

$$\frac{\partial K}{\partial t} + \frac{\partial K \bar{u}_j}{\partial x_j} = -P_k - \nu \frac{\partial \bar{u}_i}{\partial x_j} \frac{\partial \bar{u}_i}{\partial x_j} + \frac{\partial}{\partial x_j} (-\bar{u}_i R_{ij} - \bar{p} \bar{u}_i \delta_{ij} + \nu K) \tag{5.139}$$

乱流エネルギー生成項  $P_k$  が,負の符号とともに現れている.上式を領域で積分すると,右辺の拡散項は表面積分に変換できる.これは,領域表面から流入してきたエネルギーが, $P_k$  を通して流れの乱れ成分に伝達されることを意味している.式 (5.135) によると,乱流エネルギーは,エネルギー散逸率  $\varepsilon$  の形で表された分子粘性の効果により散逸する.したがって,式 (5.127) においてレイノルズ応力の形で散逸しているように見えるエネルギーは,実際には大きなスケールの流れから小さなスケールの流れに受け渡され,分子粘性によって散逸していることになる.

乱流の統計理論により、乱流現象は次のように描像される. 外部からのエネルギーは大きな渦に受け渡される. 大きな渦は小さな渦に分裂していき, エネルギーは大き

![](_page_4_Figure_9.jpeg)

図 5.6 エネルギーカスケード

な渦から小さな渦へと受け渡されていく、渦は最終的に分子粘性により消滅し、エネルギーは熱として散逸する。この過程はエネルギーカスケード (energy cascade) とよばれる (図 5.6).

#### 5.7.3 渦の散逸スケール

エネルギーカスケードの考え方から、渦のスケールには、大きなスケールにおけるエネルギーを保有した領域 (エネルギー保有領域) と、小さなスケールにおけるエネルギーが散逸する領域 (散逸領域) があり、それらの間にエネルギーが通過するのみである領域 (慣性小領域) があると考えられる。 慣性小領域における渦の性質は数学的に見積もることができ、その極限として、散逸領域における空間スケールを次式で見積もることができる。

$$\ell_D = \left(\frac{\nu^3}{\varepsilon}\right)^{1/4} \tag{5.140}$$

ℓ<sub>D</sub> は渦の散逸スケールで、コルモゴロフスケールとよばれる。

渦の散逸スケール  $\ell_D$  を、平均流のスケールとの関連で見積もってみよう、流れ場の代表長さを L、代表速度を U とすると、次元解析より、 $\varepsilon$  は次式で表すことができる。

$$\varepsilon = \frac{U^3}{L} \tag{5.141}$$

これより、 $\ell_D/L$  は次式で表される.

$$\frac{\ell_D}{L} = Re^{-3/4} \tag{5.142}$$

たとえば、水道の流れを考えてみよう、 $\nu=10^{-6}~[\mathrm{m}^2/\mathrm{s}],~U=1~[\mathrm{m}/\mathrm{s}],~L=0.01~[\mathrm{m}]$ とすると、 $Re=10^4$  なので、 $\ell_D=10^{-5}~[\mathrm{m}]$  である。渦の散逸がきわめて小さなスケールで起こることがわかる。乱流の数値解析の観点から見ると、計算格子幅を散逸スケール程度にした場合、x 方向の分割数  $N_x$  は次式で見積もられる。

$$N_x = \frac{L}{\ell_D} = Re^{3/4} (5.143)$$

3 方向で考えると, 格子数 N は

$$N = N_x N_y N_z = Re^{9/4} (5.144)$$

となる. 上で挙げた例の場合, 必要な格子数は 10<sup>9</sup> (10億) となる. 比較的遅い流れでこの程度であるので, 一般的な乱流ではさらに多くの格子数が必要になる. 日常的なエンジニアリングで用いられる格子数が, 現状数百万から多くて数千万程度である

ことを考えると、乱流をまともに計算することは現実的ではない。したがって、何らかのモデル化が必要である。

#### 5.7.4 乱流モデル

エンジニアリングにおいて乱流の数値解析を行う場合、乱流をモデル化した乱流モデル (turbulence model) が用いられる。それに対し、乱流モデルを用いない計算は直接数値シミュレーション (direct numerical simulation: DNS) とよばれ、主に研究目的で実施される。

乱流モデルには、レイノルズ平均を用いるものと、空間平均を用いるものがある。 レイノルズ平均を用いるモデルはレイノルズ平均モデルあるいは RANS モデルとよ ばれ、モデル化の種類として RANS 方程式のレイノルズ応力をモデル化するものと、 レイノルズ応力輸送方程式をモデル化するものがある。一方、空間平均を用いるもの としては、ラージエディシミュレーション (large eddy simulation: LES) がある。

RANS モデルは、大きなスケールの乱れをモデル化するため、モデル化のために参照した解析対象の条件も含めてモデル化されていると考えられ、汎用的なものにはなりにくい。したがって、解析対象に合わせてさまざまなモデルが提案されている。レイノルズ平均の性質上、定常計算や2次元計算が可能であり、利用の手軽さからエンジニアリングにおいて多用されるが、流れの詳細な非定常性の再現には向かない。

一方、LES は、大きな渦は直接計算し、流れ場に依存しない普遍的な性質をもつとされる慣性小領域以下のスケールの小さな渦のみをモデル化しており、比較的汎用性のあるモデルと考えられている。しかし、格子幅を慣性小領域に設定しなければならないため格子数が多くなり、また、常に3次元の非定常計算になるため、多くの計算リソースが必要である。近年の計算機の性能向上のため実用例は増えてきているが、いまだ日常的な利用には厳しいところがある。

## 5.7.5 渦粘性モデル

RANS 方程式のレイノルズ応力のモデル化を考える。分子粘性による応力とのアナロジーから、レイノルズ応力  $R_{ij}$  を次式のように表す。

$$-R_{ij} = -\overline{u_i'u_j'} = 2\nu_t \bar{D}_{ij} - \frac{2}{3}k\delta_{ij}$$
 (5.145)

ここで、k は乱流エネルギーである。右辺第 2 項は、 $k = \overline{u_i'u_i'}/2$  を満たすためのものである。 $\nu_t$  は渦粘性係数 (eddy viscosity) あるいは乱流粘性係数 (turbulent viscosity) とよばれる。レイノルズ応力を渦粘性で表現するということで、上のモデルをベースにした乱流モデルは、一般に渦粘性モデル (eddy viscosity model) とよばれる。渦粘

性モデルでは、基本的に乱れが等方的になる.

式 (5.145) を 式 (5.127) に代入し、k の項は圧力に組み込むものとすると、次式を得る.

 $\frac{\partial \bar{\boldsymbol{u}}}{\partial t} + \nabla \cdot (\bar{\boldsymbol{u}}\bar{\boldsymbol{u}}) = -\nabla \bar{p} + \nabla \cdot (2\nu_{\text{eff}}\bar{D})$  (5.146)

ここで  $\nu_{\text{eff}} = \nu + \nu_t$  であり、乱流の効果は乱流粘性係数に集約されている。

乱流粘性の効果は、熱拡散率においても考慮する必要がある。粘性係数同様に熱拡散率を  $\alpha_{\rm eff}=\alpha+\alpha_t$  と表現し、 $\alpha_t=\nu_t/Pr_t$  と見積もる。ここで、 $Pr_t$  は乱流プラントル数 (turbulent Prandtl number) である。経験的に、 $Pr_t=0.85$  とされる。

## 5.7.6 混合長モデル ☞ 4.5.5 項 (p.78)

渦粘性モデルを完成するには、乱流粘性係数を求める必要がある。プラントル (Prandtl) は、気体分子運動とのアナロジーから、分子の平均自由行程に対応する 渦粒子の行程である混合長 (mixing length) というものを考えた。混合長を  $\ell_m$  とし、代表時間スケールを  $\tau$  として、代表速度を  $u_t = \ell_m/\tau$  で定義すると、乱流粘性係数 は次式で表現できる。

$$\nu_t = \ell_m u_t = \frac{\ell_m^2}{\tau} \tag{5.147}$$

時間スケールが平均速度勾配の逆数に比例すると考え、比例定数を  $\ell_m$  に含めるものとすると

$$\nu_t = \ell_m^2 \left| \frac{\partial \bar{u}}{\partial y} \right| \tag{5.148}$$

となる. ここでは $\bar{u}$ を平均速度のx方向成分として、2次元的に考えている.

混合長モデルは、追加の方程式を必要としないため、混合長が指定できる問題では 簡単で有用なモデルであるが、一般的な流れでは混合長を指定しにくいため、汎用的 なものではない。

### 5.7.7 1 方程式モデル

乱流の代表速度を  $u_t=k^{1/2}$  で表し、乱流の長さスケールを  $\ell$  とすると、乱流粘性 係数  $\nu_t$  は次式で表すことができる.

$$\nu_t = \ell u_t = k^{1/2} \ell \tag{5.149}$$

ここで、kを計算することができれば、長さスケールを指定することで乱流粘性係数を計算できる。kの輸送方程式 (5.135) はそのままでは解けないので、これを次式のようにモデル化する。

$$\frac{\partial k}{\partial t} + \frac{\partial k \bar{u}_j}{\partial x_j} = P_k - \varepsilon + D_k \tag{5.150}$$

ここで  $P_k$  は、レイノルズ応力の渦粘性表現から

$$P_k = 2\nu_t \bar{D}_{ij} \frac{\partial \bar{u}_i}{\partial x_j} - \frac{2}{3}k \frac{\partial \bar{u}_i}{\partial x_j} \delta_{ij}$$
 (5.151)

である。また、 $D_k$  は

$$D_k = \frac{\partial}{\partial x_j} \left\{ \left( \nu + \frac{\nu_t}{\sigma_k} \right) \frac{\partial k}{\partial x_j} \right\} \tag{5.152}$$

であり、拡散項をモデル化したものである。 $\sigma_k$  は乱流プラントル数で、一般に 1.0 と される。 $\varepsilon$  は、次元解析より次式でモデル化する。

$$\varepsilon = C_D \frac{k^{3/2}}{\ell} \tag{5.153}$$

 $C_D$  は定数であり、0.08 程度の値である。

長さスケール $\ell$ を与えることができれば、方程式系は閉じる。長さスケールは混合 長  $\ell_m$  に比例するものと考えられるが、一般には値を経験的に設定することになる。

以上のモデルは、プラントルにより提案されたもので、RANS 方程式系に方程式が一つ追加されるため、1 方程式モデルとよばれる。それに対し、追加の方程式が必要ない混合長モデルは 0 方程式モデルとよばれる。その他の 1 方程式モデルとしては、乱流粘性係数を求めるための乱流粘性パラメタ  $\tilde{\nu}$  の輸送方程式を解く Spalart – Allmaras モデルがある。1 方程式モデルは、混合長モデルよりはマシであるが、適用範囲は限定的である。

# **5.7.8** 標準 k-ε モデル 哮 4.5.5 項 (p.78)

プラントルの 1 方程式モデルでは、長さスケールを指定する必要がある。そこで、長さスケールを変数にした 2 方程式モデルが考えられるが、乱流粘性係数が計算できさえすれば、k と組み合わせるものは何でもよい。いずれにしても  $\epsilon$  は計算する必要があるので、変数として  $\epsilon$  を選択するほうが手続き上は自然である。k と  $\epsilon$  を変数とする 2 方程式モデルは、k- $\epsilon$  モデルとよばれる。

乱流粘性係数  $\nu_t$  は,次元解析から k と  $\epsilon$  により次式で表される.

$$\nu_t = C_\mu \frac{k^2}{\varepsilon} \tag{5.154}$$

ここで、 $C_{\mu}$  は定数である.

k の輸送方程式と同様に、式 (5.128) から  $\epsilon$  の輸送方程式を導くことができるが、

煩雑なので、ここでは方程式全体をモデル化するものとして、 $\epsilon$  の輸送方程式を次式で表す。

$$\frac{\partial \varepsilon}{\partial t} + \frac{\partial \varepsilon \bar{u}_j}{\partial x_j} = \frac{\varepsilon}{k} (C_{\varepsilon 1} P_k - C_{\varepsilon 2} \varepsilon) + D_{\varepsilon}$$
 (5.155)

ここで、 $C_{\epsilon 1}$ 、 $C_{\epsilon 2}$  は定数であり、 $D_{\epsilon}$  は

$$D_{\varepsilon} = \frac{\partial}{\partial x_j} \left\{ \left( \nu + \frac{\nu_t}{\sigma_{\varepsilon}} \right) \frac{\partial \varepsilon}{\partial x_j} \right\}$$
 (5.156)

である. σε は定数である.

式 (5.150), (5.154), (5.155) を用いる 2 方程式モデルは, 標準 k- $\varepsilon$  モデルとよばれる. 各定数の値は, 一般に以下のものが用いられる.

$$C_{\mu} = 0.09, \quad \sigma_k = 1.0, \quad \sigma_{\varepsilon} = 1.3, \quad C_{\varepsilon 1} = 1.44, \quad C_{\varepsilon 2} = 1.92$$
 (5.157)

標準 k- $\epsilon$  モデルは広い分野に適用されている。ただし,RANS モデルである以上, 汎用的なモデルではありえないので,標準 k- $\epsilon$  モデルをベースにさまざまな改良モデルが提案されている。

標準 k- $\varepsilon$  モデルは、長さスケールのようなパラメタを必要としないため、エンジニアリングにおいて比較的使いやすいモデルである。とはいえ、初期値や流入条件として k,  $\varepsilon$  の値を指定する必要があり、何らかの値を見積もる必要がある。平均流の代表速度を U として、乱流強度 (turbulent intensity) I を次式で定義する.

$$I = \frac{u'}{U} \tag{5.158}$$

これは平均流に対する乱れの割合で、十分に発達した流れでは、数%の値をとるといわれる.これを用いて、k は次式で見積もられる.

$$k = \frac{3}{2}(UI)^2 \tag{5.159}$$

 $\epsilon$  については、次式で見積もられる。

$$\varepsilon = \frac{C_{\mu}^{3/4} k^{3/2}}{\ell_{m}} \tag{5.160}$$

混合長  $\ell_m$  を与える必要があるが、十分に発達した流れでは次式で見積もることができる。

$$\ell_m = 0.07L \tag{5.161}$$

ここで、Lは代表長さである。ダクト流れでは、代表長さとして水力直径 (hydraulic

${\rm diameter})$  が用いられる、水力直径を D,断面積を A,断面周長を  $\ell$  とすると,  $D=4A/\ell$  である、円形断面では D は円の直径である.

壁境界については、k は壁の法線方向勾配を 0 とし、 $\epsilon$ 、 $\nu_t$  については壁関数を用いる。

# 5.7.9 境界層の取扱い 🐷 4.5.2 項 (p.72), 4.12.4 項 (p.111)

物体表面では流速が0になるため、壁近傍では速度が急激に変化する。数値解析を考えたとき、それを解像するほどの格子を用意するのは計算コストがかかる。また、高レイノルズ数流れを想定している標準k- $\varepsilon$  モデルで壁近傍の低レイノルズ数流れを解くのは適切ではない。それらの問題を避けるため、その部分を直接解く代わりに、壁近傍の流れ(境界層)の普遍的性質を用いて境界条件として考慮することが考えられる。以下ではその方法について述べる。

### ■境界層

流れは粘性により物体表面に付着・静止するが、レイノルズ数が大きい流れの場合、その影響は物体表面の薄い層の中に限られる。この薄い層を境界層 (boundary layer) という。これに対し、境界層外の流れを主流 (external flow) という。境界層は、はじめは層流として発生する。境界層はだんだんと厚みを増し、あるところで乱流になる。層流の境界層を層流境界層、乱流の境界層を乱流境界層という。主流のレイノルズ数が  $10^3 \sim 10^5$  程度の場合、物体は層流境界層に覆われる。レイノルズ数がそれ以上になると、乱流境界層への遷移が起こり始め、レイノルズ数が大きくなるにつれて乱流境界層の割合が増していく。

翼の上面や拡大するダクトなど、主流に沿って圧力上昇が起こる場合、境界層が壁面からはがれるということが起こる。これを境界層のはく離という、以下では、層流境界層から乱流境界層への遷移や、境界層のはく離については考えないものとする。

## ■壁法則

乱流境界層内の速度分布は、次式で表される.

$$u^{+} = \frac{1}{\kappa} \ln E y^{+} \tag{5.162}$$

ここで、 $u^+ = \bar{u}/u_\tau$  は速度の無次元数で、 $u_\tau = \sqrt{\tau_w/\rho}$  は摩擦速度、 $\tau_w$  は壁面せん断応力である。 $y^+ = u_\tau y/\nu$  は壁からの距離 y の無次元数である。 $\kappa$  はカルマン (Karman) 定数とよばれ、値は  $0.40 \sim 0.45$  とされる (だいたい 0.41 が用いられる). なめらかな壁では E = 9.8 とされる。上式は対数則 (log law) とよばれ、乱流境界層の中でこれが成り立つ領域は対数則層 (log law layer) あるいは対数領域 (logarithmic

region) とよばれる.

乱流境界層においても、壁近傍には薄い層流の層がある。これは粘性底層 (viscous sublayer) とよばれ、速度分布は次式で表される。

$$u^+ = y^+ (5.163)$$

粘性底層では、速度が壁からの距離に比例する. これは線形則 (linear law) とよばれる.

粘性底層と対数則層のそれぞれの範囲は、粘性底層がだいたい  $y^+ < 5$  であり、対数則層がだいたい  $30 < y^+ < 500$  である。両者の間はバッファ層 (buffer layer) とよばれ、粘性底層から対数則層への遷移領域である (図 5.7).

![](_page_1_Figure_6.jpeg)

図 5.7 境界層の速度分布

以上のように、境界層内の流れは主流のレイノルズ数とは無関係で、密度、粘性係数、壁面せん断応力、壁からの距離によって支配される。これを壁法則 (law of the wall) という.

#### ■壁関数

数値解析を考えた場合、速度が狭い範囲で急激に変化する境界層を解像しようとすると、壁際に細かい格子を用意する必要があり、格子幅は小さく、格子数は膨大になってしまう。 また、標準 k- $\epsilon$  モデルは高レイノルズ数を想定しており、壁近傍の低レイノルズ数流れに適用するのは適切ではない。これらの問題を避けるため、壁の第 1 格子点を対数則層に入れ、壁法則により境界条件を与える方法が考えられる。これは、壁関数 (wall function) による方法とよばれている。

壁関数による境界条件は、kや $\epsilon$ などの乱流諸量および温度に対して用いられる.

## 5.7.10 その他の渦粘性モデル 🖙 4.4 節 (p.67)

標準 k- $\epsilon$  モデルは、比較的単純な流れ場においては成果を挙げているが、曲率、旋回、はく離などがある流れ場に対しては精度が悪いことが知られている。そのため、さまざまな改良モデルが提案されている。以下では主要な改良モデルについて簡単に述べる。

### ■低レイノルズ数型 k-ε モデル

複雑な流れ場においては、壁近傍で壁関数の前提が成り立たない場合がある。たとえば、層流から乱流への遷移領域を含む流れ、はく離、熱伝達に関する温度境界層についての問題などでは、一般に正しい解を与えない。この場合、壁関数を使わずに壁近傍の低レイノルズ数流れをきちんと解く必要があるが、高レイノルズ数型の標準k- $\epsilon$  モデルでは、壁近傍での低レイノルズ数流れによるレイノルズ応力の減衰効果を正しく表現することができない。そこで、減衰関数 (damping function) により低レイノルズ数効果を表現する低レイノルズ数型 k- $\epsilon$  モデルが提案されている。たとえば、Launder-Sharma モデルや Lam-Bremhorst モデルがある (OpenFOAM ではそれぞれ LaunderSharmaKE、LamBremhorstKE にあたる)。

k- $\epsilon$  モデルに限らず、壁近傍の低レイノルズ数効果を考慮したモデルは一般に、低レイノルズ数型モデル (low-Reynolds number model) とよばれる.

#### ■ RNG k- $\varepsilon$ モデル

RNG k- $\varepsilon$  モデルは、繰り込み群 (renormalization group, RNG) 理論を用いたもので、標準 k- $\varepsilon$  モデルの各モデル定数を理論的に導出し、平均ひずみ効果の補正が加えられている。平均ひずみの大きな流れに有効である。

### ■ Realizable k- $\varepsilon$ モデル

Realizable k- $\varepsilon$  モデルは、 $\overline{u'^2}$ 、k、 $\varepsilon$  などの値は負になりえないという物理的な実現性 (realizability) の制限を課したモデルである。 曲率や旋回がある流れなどに有効とされる.

## ■ k-ω モデル

k- $\omega$  モデルは、変数として k と比散逸率 (specific dissipation rate)  $\omega = \varepsilon/k$  を採用したモデルである。乱流粘性係数は次式で計算される。

$$\nu_t = \frac{k}{\omega} \tag{5.164}$$

"標準 k- $\omega$  モデル"と一般によばれるモデルには、いくつかのバージョンがある。初期のバージョンの k- $\omega$  モデル (OpenFOAM で実装されているモデル) は、壁近傍の

流れについては k- $\varepsilon$  モデルよりも得意だが、自由流れ (freestream) に弱い、この欠点の回避を目的の一つとして、SST k- $\omega$  モデルが提案された.

SST k- $\omega$  モデルは二つのモデルからなる. 一つは BSL (baseline) モデルであり、 壁近傍では k- $\omega$  モデル、その外側では k- $\varepsilon$  モデルから変換した k- $\omega$  モデルを用いる. もう一つは SST (shear stress transport) モデルであり、乱流のせん断応力の輸送効果を考慮する.

k- $\omega$  モデルでは、初期値や流入条件として k,  $\omega$  の値を指定する.  $\omega$  は k と  $\varepsilon$  から計算できるが、k- $\omega$  モデルと k- $\varepsilon$  モデルでは乱流粘性係数の定義が異なるため注意が必要である。 乱流粘性係数を k- $\varepsilon$  モデルに合わせるには、 $\omega = \varepsilon/(C_{\mu}k)$  とする必要がある。

## ■非線形 *k-ε* モデル

標準のレイノルズ応力の渦粘性表現は、レイノルズ応力の線形近似と考えることができる。そのような考え方から、レイノルズ応力の非線形表現がいくつか提案されている。レイノルズ応力の非線形表現を用いたモデルは非線形渦粘性モデル (nonlinear eddy viscosity model) とよばれ、k- $\epsilon$  モデルの場合は非線形 k- $\epsilon$  モデルとよばれる。

乱れの非等方性を考慮するには、レイノルズ応力輸送モデルを用いる方法があるが、レイノルズ応力 6 成分を解く必要があり、計算コストが高い、非線形 k- $\epsilon$  モデルであれば、レイノルズ応力輸送モデルほど計算コストを増加させずに、乱れの非等方性を表現できる可能性がある。ただし、このタイプのモデルの実用例は多くはない。

OpenFOAM では、Lien cubic k-epsilon (LienCubicKE) や Shih quadratic k-epsilon (ShihQuadraticKE) が実装されている。

# 5.7.11 レイノルズ応力輸送モデル F 4.4 節 (p.67)

レイノルズ応力の渦粘性表現を用いる渦粘性モデルには、流れの非等方性を考慮しにくいという問題がある。渦粘性表現を用いる代わりに、レイノルズ応力輸送方程式を解いてレイノルズ応力を求めるモデルが提案されている。このタイプのモデルは、レイノルズ応力モデル (Reynolds stress model: RSM) あるいはレイノルズ応力輸送モデル (Reynolds stress transport model: RSTM) とよばれる。

レイノルズ応力輸送モデルには標準モデルというものはないが、Launder – Reece – Rodi モデル (LRR モデル) が基本的なモデルとして参照される。レイノルズ応力輸送方程式 (5.130) は、以下のようにモデル化される。

$$\frac{\partial}{\partial t}(R_{ij}) + \frac{\partial}{\partial x_k}(R_{ij}\bar{u}_k) = P_{ij} + \Pi_{ij} - \varepsilon_{ij} + D_{ij}$$
 (5.165)

ここで

$$\Pi_{ij} = -C_1 \frac{\varepsilon}{k} \left( R_{ij} - \frac{2}{3} \delta_{ij} k \right) - C_2 \left( P_{ij} - \frac{2}{3} \delta_{ij} P_k \right) 
P_k = \frac{1}{2} P_{ii} 
\varepsilon_{ij} = \frac{2}{3} \delta_{ij} \varepsilon 
D_{ij} = \frac{\partial}{\partial x_k} \left\{ \left( \nu + \frac{\nu_t}{\sigma_k} \right) \frac{\partial R_{ij}}{\partial x_k} \right\} 
k = \frac{1}{2} R_{ii}$$
(5.166)

であり、定数は

$$C_1 = 1.8, \quad C_2 = 0.6 \tag{5.167}$$

である。圧力 – ひずみ相関項  $\Pi_{ij}$  には、壁が圧力変動を反射する効果を考慮するため の壁反射項 (wall reflection term) が付加されることがある。 OpenFOAM の乱流モデル LRR には、Gibson と Launder による壁反射項を考慮するオプションがある(デフォルトで有効)。

式 (5.155) から別途  $\varepsilon$  を求める必要がある。変数の数は、対称テンソルであるレイノルズ応力の 6 成分と  $\varepsilon$  で 7 個なので、レイノルズ応力輸送モデルは 7 方程式モデルである。方程式の数で単純に比較すると、標準 k- $\varepsilon$  モデルの 3 倍以上の計算コストがかかることになる。

レイノルズ応力輸送モデルは、乱れの非等方性を表現できるため、曲率や旋回のある流れなど、複雑な流れに有効とされる.

OpenFOAM では、LRR モデルのほかに Speziale – Sarkar – Gatski (SSG) モデル (SSG) が実装されている。