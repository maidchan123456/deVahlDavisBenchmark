# 既存 CFD 結果の統一可視化（Route A / Route B）

本成果物は保存済み結果のみを読み込んだ可視化・比較です。solver、mesh 生成、OpenFOAM postProcess は実行していません。既存の判定・契約・場・metrics を更新していません。

## 正式判定と対象

- Route A：computed **12/12**、accepted **12/12**、Gate D PASS **12/12**。各 Ra の fine practical paper comparison と Gate G は既存 PASS。Gate F は全4 Raで FAIL、needs_320=YES を保持。
- Route B：computed **12/12**、accepted **9/12**。Ra=10³～10⁵は全格子 accepted。Ra=10⁶は全格子 Gate D FAIL / accepted NO の **diagnostic-only**。
- B-Ra1e4-coarse は独立したケースを作らず、正式 matrix が再利用を認めた **B-SMOKE** の field/result を使用。`case_id` と `source_case_id` を各表で分離。補助 B-SMOKE は同じ solver result の別表示であり、独立した追加計算ではありません。
- A-Ra1e3-coarse の metrics は attempt_004 の `accepted_reuse/metrics.json` と付属 CSV を使用。
- 正式24表示条件、補助 A/B-COND・A/B-SMOKE の4表示ケース、Gate H 1ケースの計29表示ケース（独立した solver result は28）。補助図・感度図は `comparison/auxiliary/`・`comparison/sensitivity/` に分離。

## 入力ケース・結果の一覧

|表示 case ID|source case ID|分類|Ra|grid|accepted|最終反復|入力ケース|metrics|
|---|---|---|---:|---|---|---:|---|---|
|A-Ra1e3-coarse|A-Ra1e3-coarse|matrix|1000|40x40x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e3-coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/attempts/attempt_004/cases/A-Ra1e3-coarse/accepted_reuse/metrics.json|
|A-Ra1e3-medium|A-Ra1e3-medium|matrix|1000|80x80x1|true|6000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e3-medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e3-medium/metrics.json|
|A-Ra1e3-fine|A-Ra1e3-fine|matrix|1000|160x160x1|true|18000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e3-fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e3-fine/metrics.json|
|A-Ra1e4-coarse|A-Ra1e4-coarse|matrix|10000|40x40x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e4-coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e4-coarse/metrics.json|
|A-Ra1e4-medium|A-Ra1e4-medium|matrix|10000|80x80x1|true|6000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e4-medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e4-medium/metrics.json|
|A-Ra1e4-fine|A-Ra1e4-fine|matrix|10000|160x160x1|true|15000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e4-fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e4-fine/metrics.json|
|A-Ra1e5-coarse|A-Ra1e5-coarse|matrix|100000|40x40x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e5-coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e5-coarse/metrics.json|
|A-Ra1e5-medium|A-Ra1e5-medium|matrix|100000|80x80x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e5-medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e5-medium/metrics.json|
|A-Ra1e5-fine|A-Ra1e5-fine|matrix|100000|160x160x1|true|12000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e5-fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e5-fine/metrics.json|
|A-Ra1e6-coarse|A-Ra1e6-coarse|matrix|1000000|40x40x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e6-coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e6-coarse/metrics.json|
|A-Ra1e6-medium|A-Ra1e6-medium|matrix|1000000|80x80x1|true|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e6-medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e6-medium/metrics.json|
|A-Ra1e6-fine|A-Ra1e6-fine|matrix|1000000|160x160x1|true|9000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-Ra1e6-fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-Ra1e6-fine/metrics.json|
|B-Ra1e3-coarse|B-Ra1e3-coarse|matrix|1000|40x40x1|YES|3000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e3_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e3-coarse/metrics.json|
|B-Ra1e3-medium|B-Ra1e3-medium|matrix|1000|80x80x1|YES|6000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e3_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e3-medium/metrics.json|
|B-Ra1e3-fine|B-Ra1e3-fine|matrix|1000|160x160x1|YES|21000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e3_fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e3-fine/metrics.json|
|B-Ra1e4-coarse|B-SMOKE|matrix|10000|40x40x1|YES|3000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e4_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-SMOKE/metrics.json|
|B-Ra1e4-medium|B-Ra1e4-medium|matrix|10000|80x80x1|YES|6000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e4_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e4-medium/metrics.json|
|B-Ra1e4-fine|B-Ra1e4-fine|matrix|10000|160x160x1|YES|18000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e4_fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e4-fine/metrics.json|
|B-Ra1e5-coarse|B-Ra1e5-coarse|matrix|100000|40x40x1|YES|6000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e5_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e5-coarse/metrics.json|
|B-Ra1e5-medium|B-Ra1e5-medium|matrix|100000|80x80x1|YES|9000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e5_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e5-medium/metrics.json|
|B-Ra1e5-fine|B-Ra1e5-fine|matrix|100000|160x160x1|YES|12000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e5_fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e5-fine/metrics.json|
|B-Ra1e6-coarse|B-Ra1e6-coarse|matrix|1000000|40x40x1|NO|30000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e6_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e6-coarse/metrics.json|
|B-Ra1e6-medium|B-Ra1e6-medium|matrix|1000000|80x80x1|NO|30000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e6_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e6-medium/metrics.json|
|B-Ra1e6-fine|B-Ra1e6-fine|matrix|1000000|160x160x1|NO|30000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e6_fine|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-Ra1e6-fine/metrics.json|
|A-COND|A-COND|auxiliary|0|80x80x1|正式 matrix 外|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/Ra0_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-COND/metrics.json|
|A-SMOKE|A-SMOKE|auxiliary|10000|40x40x1|正式 matrix 外|3000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/Ra1e4_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-SMOKE/metrics.json|
|B-COND|B-COND|auxiliary|0|80x80x1|正式 matrix 外|3000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra0_medium|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-COND/metrics.json|
|B-SMOKE|B-SMOKE|auxiliary|10000|40x40x1|正式 matrix 外|3000|/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e4_coarse|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/cases/B-SMOKE/metrics.json|
|A-H-Ra1e6-fine-beta1e-4|A-H-Ra1e6-fine-beta1e-4|sensitivity|1000000|160x160x1|true|12000|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/A-H-Ra1e6-fine-beta1e-4|/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/cases/A-H-Ra1e6-fine-beta1e-4/metrics.json|

## 無次元化・座標・描画

`X=x/L`, `Z=z/L`, `theta=(T-Tc)/(Th-Tc)`, `(U,W)=(L/alpha0)*(ux,uz)`。`alpha0` は各 manifest の既存 benchmark 値を使用。実 mesh は OpenFOAM `(x,y,z)` の第2成分が鉛直なので、論文 `Z` と `W` は OpenFOAM `y` と `U[:, :, 1]` に対応します。第3成分は厚み方向で、流線には用いません。保存 C または保存 mesh の points/faces/owner/neighbour から cell 配置と並び順を検証しています。

中心線速度は既存 B extractor を A にも適用し、A の同一の式と照合。2本の隣接 cell-centre line の平均で正確な X=0.5 / Z=0.5 を取り、壁 no-slip のゼロ endpoint を加えて線形補間した **4097点**です。正の Umax/Wmax と位置を保存 metrics と照合。局所 Nu 極値は既存の5点 quartic 法をそのまま呼び出します。Route A の quartic に渡す座標は既存 analyzer と同じ有次元座標/L の計算順序を保持します。Table V の星印は参照極値と位置で、参照の全プロファイルは捏造していません。

温度は contourf、共通 0≤theta≤1、aspect=1。セル値をクリップしません。overshoot は `data/all_case_summary.csv` と `data/temperature_overshoot.csv` の範囲・セル数に保存し、色範囲外は extend に表示します。温度・速度絶対値・密度図は表示のためだけに既知の壁温度/no-slip・断熱境界を付加します。元の CSV field は cell centre の値を保持。流線は均一 cell-centre grid 上の streamplot を使用し、壁から半セル以内は描画補外しません。

流線の色は in-plane の U/W で運ばれる3成分速度絶対値 |U*|（厚み成分の最大値も CSV に記録）。各 Ra 内では両 Route・3格子の最大速度を共通上限に使用。異なる Ra は別の上限で、montage では各行の colorbar を確認してください。温度は coolwarm、速度は magma、密度偏差は RdBu_r。

線図は Route A=青、Route B=朱、paper=黒の点線・星、Gate H perturbed=緑。accepted は実線/塗りつぶし marker、B Ra=10⁶ は破線/中抜き marker。field は各パネルタイトルに accepted / diagnostic-only を記載。補助ケースは outside formal matrix と記載。

## Nu の定義と比較範囲

原論文熱輸送密度は `Q=U*theta-dtheta/dX`。`Nu_bar_0` は高温壁、`Nu_bar_half` は中央 X=0.5 断面、`Nu_bar_1` は低温壁、`Nu_bar_cavity = 1 + volume_mean(U*theta)` は領域積分です。断面曲線の台形積分は独立診断であり、primary cavity 値を置き換えません。`local Nu(Z)` は壁 face の局所値であり、平均 Nu と区別します。

- Route A：壁は直交 patch gradient A1、内部断面は linear cell-U/theta face interpolation + 2-cell 温度勾配。物理熱収支は保存 wallHeatFlux Q による A2 を使用。
- Route B：正式壁値 B1 は fixedValue patch snGrad、内部断面の移流は **保存済み volume flux phi** × linear theta。B2 は壁温度と第1/第2セル温度から独立二次再構成した診断値で、点線で表示。B2 で正式 B1 を置き換えません。
- A/B の Nu_bar_half・section consistency は演算子が異なり、**NOT_LIKE_FOR_LIKE**。これらは同じ比較誤差曲線へ入れません。既存 AB CSV の comparison_class・diagnostic_only 等は保持し、Nu_bar_cavity、Nu_bar_0、Umax、Wmax、局所 Nu max/min の6量だけを AB 相対差図に使用。
- 原論文対 A は practical benchmark difference、A対Bは model/formulation difference。Aの差を純粋な数値誤差と解釈しません。paper 相対差は 100|computed-reference|/|reference|、AB は 100|A-B|/|B|。

## 密度・保存則・Gate H の注意

Route A は温度依存 Boussinesq EOS `rho=rho0[1-beta(T-T0)]`, `psi=0`。密度偏差図は圧力依存 compressibility を示しません。`rho_min`, `rho_max`, `max|rho/rho0-1|` は cell-centre 値として表に記録し、壁での振幅 beta DeltaT/2 を別表示。

Route B rhok は `1-beta(T-TRef)` を保存 T から再構成した **buoyancy / hydrostatic factor**。v6 createFields.H / TEqn.H / pEqn.H と docs/routeB_design.md を確認しました。浮力と静水圧分離 `p=p_rgh+rhok*gh` に使用され、慣性・温度輸送・連続式に温度依存の質量密度として入る場ではありません。A rho と B rhok の単純差分は作成していません。

A native phi は mass flux [kg/s]、B native phi は volume flux [m³/s]。normalized native continuity indicator は Route 別の図・operator metadata に分離。速度再構成 divergence は native face flux divergence と別量です。既存 epsilon 値を転記して判定は変えません。温度・速度対称性は保存場の180度回転対応セルから算出し、保存済み定義・値がある場合に照合しています。ゼロ値は対数図で 0 と明記し、未保存値は not stored と表示します。

Gate H は共通160²で beta/10, g×10、Ra/Pr を固定した感度比較。**grid independence、Route A=Route B、格子とモデルの影響の完全分離の証明ではありません。** 密度偏差の左右比較は共通±0.0005で、個別 H 図では小さい密度振幅も確認できます。

|Gate H primary QoI|相対差 [%]|
|---|---:|
|Nu_bar_cavity|0.03920392|
|Umax|0.02391669|
|Wmax|0.01105015|

## 図から確認できる観察・解釈・未解決事項

**観察：** Ra増加に伴って Nu・速度極値が増加し、高Raでは壁近くの温度変化と鉛直流れが集中します。正式3格子の Nu_bar_cavity は両 Route の全Raで格子細分化とともに低下。速度極値の一部は非単調で、Gate F の未定義 p/GCI を「未定義」と保持。A Ra=10⁶ の Nu fine-medium 差は約1.3402%。

|Ra|A fine Nu|B fine Nu|A fine Umax|B fine Umax|A fine Wmax|B fine Wmax|B区分|
|---:|---:|---:|---:|---:|---:|---:|---|
|1000|1.117942492|1.117864112|3.6500951|3.6490796|3.6986873|3.6974359|accepted|
|10000|2.246385203|2.245720241|16.1845829|16.1810233|19.6219614|19.6193308|accepted|
|100000|4.529825749|4.528062765|34.7549843|34.7462803|68.6552097|68.6469303|accepted|
|1000000|8.868989456|8.865121227|64.9147346|64.8995125|219.9002617|219.8734710|diagnostic-only / unaccepted|

**観察：** fine の3主要量 Nu_cavity/Umax/Wmax では既存 AB CSV の相対差の最大値は 0.043634%（B Ra=10⁶を含む診断比較）。Gate H の3量は既存値約0.0392/0.0239/0.0111%と一致し、密度振幅は約1/10。温度 overshoot の有無は次の表で判定可能です。

全29表示ケースのセル温度範囲は theta=0.0018274829～0.998172292。範囲外セル総数は 0。

**推論：** 小さい fine 主要量差と密度振幅の低下は、今回の共通格子・固定条件での感度が小さいことを支持します。原論文・Route B との物理方程式差、格子誤差、離散 operator 差の寄与はこの図だけで分離できません。

**未解決：** A Gate F 全4Ra FAIL/needs_320 YES、B Ra=10⁶ Gate D FAIL、B Gate F 非単調/未評価、B Gate G の正式 FAIL/未評価・閾値未解決は既存結論を維持。図生成・fineの参照一致だけで Verification 完了や grid independent と結論しません。

## 数値照合と read-only 保護

全 1585 照合項目 PASS。保存場→既存 analyzer の純粋関数による再計算→metrics/中心線/局所Nu/断面Nu CSV→正式 matrix/AB/Gate H の順に整合を確認。既存値は上書きしません。rtol=atol=5e-12（geometry coordinate のみ atol=5e-10 m）。検出した不一致は例外 STOP で終了し、その原因を logs/STOP.json に記録する実装です。

開発時、A-Ra1e6-medium の quartic 最小値に7.2759576e-11の差が出て停止しました。原因は等価な座標式の浮動小数点計算順序。Route A analyzer と同じ座標式に修正後、許容差を緩和せず一致。既存 metrics は変更していません。

実行前後で protected roots と外部 v6 Route B cases の全 403344 ファイルの size/mtime_ns/ctime_ns を比較し、変更・追加・削除はゼロ。実入力 359 ファイルの SHA-256 も不変。git diff/status は開始時と一致。入力全量をhashしたわけではなく、全領域 metadata inventory と実入力 content hashes の組合せです。

`logs/protection.json` に範囲・件数・git比較結果、`logs/input_sha256.csv` に実入力 hash、`logs/numerical_checks.csv` に照合差、`logs/run_summary.json` に件数を保存。solver 実行は0回、mesh生成0回、既存 analyzer main() 呼出し0回。

## 図一覧（PNG 300 dpi + PDF）

各行の PNG と PDF は同じ図です。PDF の field/線はベクトル出力で、論文掲載時の拡大に適します。

|図|説明|ケース|
|---|---|---|
|[PNG](individual/A-Ra1e3-coarse_temperature.png) / [PDF](individual/A-Ra1e3-coarse_temperature.pdf)|temperature|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_streamlines.png) / [PDF](individual/A-Ra1e3-coarse_streamlines.pdf)|streamlines|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_velocity_magnitude.png) / [PDF](individual/A-Ra1e3-coarse_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_density_deviation.png) / [PDF](individual/A-Ra1e3-coarse_density_deviation.pdf)|density_deviation|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_centreline.png) / [PDF](individual/A-Ra1e3-coarse_centreline.pdf)|centreline|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_local_Nu.png) / [PDF](individual/A-Ra1e3-coarse_local_Nu.pdf)|local_Nu|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_section_Nu.png) / [PDF](individual/A-Ra1e3-coarse_section_Nu.pdf)|section_Nu|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-coarse_temperature_centreline.png) / [PDF](individual/A-Ra1e3-coarse_temperature_centreline.pdf)|temperature centreline|A-Ra1e3-coarse|
|[PNG](individual/A-Ra1e3-medium_temperature.png) / [PDF](individual/A-Ra1e3-medium_temperature.pdf)|temperature|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_streamlines.png) / [PDF](individual/A-Ra1e3-medium_streamlines.pdf)|streamlines|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_velocity_magnitude.png) / [PDF](individual/A-Ra1e3-medium_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_density_deviation.png) / [PDF](individual/A-Ra1e3-medium_density_deviation.pdf)|density_deviation|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_centreline.png) / [PDF](individual/A-Ra1e3-medium_centreline.pdf)|centreline|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_local_Nu.png) / [PDF](individual/A-Ra1e3-medium_local_Nu.pdf)|local_Nu|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_section_Nu.png) / [PDF](individual/A-Ra1e3-medium_section_Nu.pdf)|section_Nu|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-medium_temperature_centreline.png) / [PDF](individual/A-Ra1e3-medium_temperature_centreline.pdf)|temperature centreline|A-Ra1e3-medium|
|[PNG](individual/A-Ra1e3-fine_temperature.png) / [PDF](individual/A-Ra1e3-fine_temperature.pdf)|temperature|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_streamlines.png) / [PDF](individual/A-Ra1e3-fine_streamlines.pdf)|streamlines|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_velocity_magnitude.png) / [PDF](individual/A-Ra1e3-fine_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_density_deviation.png) / [PDF](individual/A-Ra1e3-fine_density_deviation.pdf)|density_deviation|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_centreline.png) / [PDF](individual/A-Ra1e3-fine_centreline.pdf)|centreline|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_local_Nu.png) / [PDF](individual/A-Ra1e3-fine_local_Nu.pdf)|local_Nu|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_section_Nu.png) / [PDF](individual/A-Ra1e3-fine_section_Nu.pdf)|section_Nu|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e3-fine_temperature_centreline.png) / [PDF](individual/A-Ra1e3-fine_temperature_centreline.pdf)|temperature centreline|A-Ra1e3-fine|
|[PNG](individual/A-Ra1e4-coarse_temperature.png) / [PDF](individual/A-Ra1e4-coarse_temperature.pdf)|temperature|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_streamlines.png) / [PDF](individual/A-Ra1e4-coarse_streamlines.pdf)|streamlines|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_velocity_magnitude.png) / [PDF](individual/A-Ra1e4-coarse_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_density_deviation.png) / [PDF](individual/A-Ra1e4-coarse_density_deviation.pdf)|density_deviation|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_centreline.png) / [PDF](individual/A-Ra1e4-coarse_centreline.pdf)|centreline|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_local_Nu.png) / [PDF](individual/A-Ra1e4-coarse_local_Nu.pdf)|local_Nu|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_section_Nu.png) / [PDF](individual/A-Ra1e4-coarse_section_Nu.pdf)|section_Nu|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-coarse_temperature_centreline.png) / [PDF](individual/A-Ra1e4-coarse_temperature_centreline.pdf)|temperature centreline|A-Ra1e4-coarse|
|[PNG](individual/A-Ra1e4-medium_temperature.png) / [PDF](individual/A-Ra1e4-medium_temperature.pdf)|temperature|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_streamlines.png) / [PDF](individual/A-Ra1e4-medium_streamlines.pdf)|streamlines|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_velocity_magnitude.png) / [PDF](individual/A-Ra1e4-medium_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_density_deviation.png) / [PDF](individual/A-Ra1e4-medium_density_deviation.pdf)|density_deviation|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_centreline.png) / [PDF](individual/A-Ra1e4-medium_centreline.pdf)|centreline|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_local_Nu.png) / [PDF](individual/A-Ra1e4-medium_local_Nu.pdf)|local_Nu|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_section_Nu.png) / [PDF](individual/A-Ra1e4-medium_section_Nu.pdf)|section_Nu|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-medium_temperature_centreline.png) / [PDF](individual/A-Ra1e4-medium_temperature_centreline.pdf)|temperature centreline|A-Ra1e4-medium|
|[PNG](individual/A-Ra1e4-fine_temperature.png) / [PDF](individual/A-Ra1e4-fine_temperature.pdf)|temperature|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_streamlines.png) / [PDF](individual/A-Ra1e4-fine_streamlines.pdf)|streamlines|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_velocity_magnitude.png) / [PDF](individual/A-Ra1e4-fine_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_density_deviation.png) / [PDF](individual/A-Ra1e4-fine_density_deviation.pdf)|density_deviation|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_centreline.png) / [PDF](individual/A-Ra1e4-fine_centreline.pdf)|centreline|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_local_Nu.png) / [PDF](individual/A-Ra1e4-fine_local_Nu.pdf)|local_Nu|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_section_Nu.png) / [PDF](individual/A-Ra1e4-fine_section_Nu.pdf)|section_Nu|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e4-fine_temperature_centreline.png) / [PDF](individual/A-Ra1e4-fine_temperature_centreline.pdf)|temperature centreline|A-Ra1e4-fine|
|[PNG](individual/A-Ra1e5-coarse_temperature.png) / [PDF](individual/A-Ra1e5-coarse_temperature.pdf)|temperature|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_streamlines.png) / [PDF](individual/A-Ra1e5-coarse_streamlines.pdf)|streamlines|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_velocity_magnitude.png) / [PDF](individual/A-Ra1e5-coarse_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_density_deviation.png) / [PDF](individual/A-Ra1e5-coarse_density_deviation.pdf)|density_deviation|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_centreline.png) / [PDF](individual/A-Ra1e5-coarse_centreline.pdf)|centreline|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_local_Nu.png) / [PDF](individual/A-Ra1e5-coarse_local_Nu.pdf)|local_Nu|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_section_Nu.png) / [PDF](individual/A-Ra1e5-coarse_section_Nu.pdf)|section_Nu|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-coarse_temperature_centreline.png) / [PDF](individual/A-Ra1e5-coarse_temperature_centreline.pdf)|temperature centreline|A-Ra1e5-coarse|
|[PNG](individual/A-Ra1e5-medium_temperature.png) / [PDF](individual/A-Ra1e5-medium_temperature.pdf)|temperature|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_streamlines.png) / [PDF](individual/A-Ra1e5-medium_streamlines.pdf)|streamlines|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_velocity_magnitude.png) / [PDF](individual/A-Ra1e5-medium_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_density_deviation.png) / [PDF](individual/A-Ra1e5-medium_density_deviation.pdf)|density_deviation|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_centreline.png) / [PDF](individual/A-Ra1e5-medium_centreline.pdf)|centreline|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_local_Nu.png) / [PDF](individual/A-Ra1e5-medium_local_Nu.pdf)|local_Nu|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_section_Nu.png) / [PDF](individual/A-Ra1e5-medium_section_Nu.pdf)|section_Nu|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-medium_temperature_centreline.png) / [PDF](individual/A-Ra1e5-medium_temperature_centreline.pdf)|temperature centreline|A-Ra1e5-medium|
|[PNG](individual/A-Ra1e5-fine_temperature.png) / [PDF](individual/A-Ra1e5-fine_temperature.pdf)|temperature|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_streamlines.png) / [PDF](individual/A-Ra1e5-fine_streamlines.pdf)|streamlines|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_velocity_magnitude.png) / [PDF](individual/A-Ra1e5-fine_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_density_deviation.png) / [PDF](individual/A-Ra1e5-fine_density_deviation.pdf)|density_deviation|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_centreline.png) / [PDF](individual/A-Ra1e5-fine_centreline.pdf)|centreline|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_local_Nu.png) / [PDF](individual/A-Ra1e5-fine_local_Nu.pdf)|local_Nu|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_section_Nu.png) / [PDF](individual/A-Ra1e5-fine_section_Nu.pdf)|section_Nu|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e5-fine_temperature_centreline.png) / [PDF](individual/A-Ra1e5-fine_temperature_centreline.pdf)|temperature centreline|A-Ra1e5-fine|
|[PNG](individual/A-Ra1e6-coarse_temperature.png) / [PDF](individual/A-Ra1e6-coarse_temperature.pdf)|temperature|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_streamlines.png) / [PDF](individual/A-Ra1e6-coarse_streamlines.pdf)|streamlines|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_velocity_magnitude.png) / [PDF](individual/A-Ra1e6-coarse_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_density_deviation.png) / [PDF](individual/A-Ra1e6-coarse_density_deviation.pdf)|density_deviation|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_centreline.png) / [PDF](individual/A-Ra1e6-coarse_centreline.pdf)|centreline|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_local_Nu.png) / [PDF](individual/A-Ra1e6-coarse_local_Nu.pdf)|local_Nu|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_section_Nu.png) / [PDF](individual/A-Ra1e6-coarse_section_Nu.pdf)|section_Nu|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-coarse_temperature_centreline.png) / [PDF](individual/A-Ra1e6-coarse_temperature_centreline.pdf)|temperature centreline|A-Ra1e6-coarse|
|[PNG](individual/A-Ra1e6-medium_temperature.png) / [PDF](individual/A-Ra1e6-medium_temperature.pdf)|temperature|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_streamlines.png) / [PDF](individual/A-Ra1e6-medium_streamlines.pdf)|streamlines|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_velocity_magnitude.png) / [PDF](individual/A-Ra1e6-medium_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_density_deviation.png) / [PDF](individual/A-Ra1e6-medium_density_deviation.pdf)|density_deviation|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_centreline.png) / [PDF](individual/A-Ra1e6-medium_centreline.pdf)|centreline|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_local_Nu.png) / [PDF](individual/A-Ra1e6-medium_local_Nu.pdf)|local_Nu|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_section_Nu.png) / [PDF](individual/A-Ra1e6-medium_section_Nu.pdf)|section_Nu|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-medium_temperature_centreline.png) / [PDF](individual/A-Ra1e6-medium_temperature_centreline.pdf)|temperature centreline|A-Ra1e6-medium|
|[PNG](individual/A-Ra1e6-fine_temperature.png) / [PDF](individual/A-Ra1e6-fine_temperature.pdf)|temperature|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_streamlines.png) / [PDF](individual/A-Ra1e6-fine_streamlines.pdf)|streamlines|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_velocity_magnitude.png) / [PDF](individual/A-Ra1e6-fine_velocity_magnitude.pdf)|velocity_magnitude|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_density_deviation.png) / [PDF](individual/A-Ra1e6-fine_density_deviation.pdf)|density_deviation|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_centreline.png) / [PDF](individual/A-Ra1e6-fine_centreline.pdf)|centreline|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_local_Nu.png) / [PDF](individual/A-Ra1e6-fine_local_Nu.pdf)|local_Nu|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_section_Nu.png) / [PDF](individual/A-Ra1e6-fine_section_Nu.pdf)|section_Nu|A-Ra1e6-fine|
|[PNG](individual/A-Ra1e6-fine_temperature_centreline.png) / [PDF](individual/A-Ra1e6-fine_temperature_centreline.pdf)|temperature centreline|A-Ra1e6-fine|
|[PNG](individual/B-Ra1e3-coarse_temperature.png) / [PDF](individual/B-Ra1e3-coarse_temperature.pdf)|temperature|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_streamlines.png) / [PDF](individual/B-Ra1e3-coarse_streamlines.pdf)|streamlines|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_velocity_magnitude.png) / [PDF](individual/B-Ra1e3-coarse_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_buoyancy_factor.png) / [PDF](individual/B-Ra1e3-coarse_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_centreline.png) / [PDF](individual/B-Ra1e3-coarse_centreline.pdf)|centreline|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_local_Nu.png) / [PDF](individual/B-Ra1e3-coarse_local_Nu.pdf)|local_Nu|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_section_Nu.png) / [PDF](individual/B-Ra1e3-coarse_section_Nu.pdf)|section_Nu|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-coarse_temperature_centreline.png) / [PDF](individual/B-Ra1e3-coarse_temperature_centreline.pdf)|temperature centreline|B-Ra1e3-coarse|
|[PNG](individual/B-Ra1e3-medium_temperature.png) / [PDF](individual/B-Ra1e3-medium_temperature.pdf)|temperature|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_streamlines.png) / [PDF](individual/B-Ra1e3-medium_streamlines.pdf)|streamlines|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_velocity_magnitude.png) / [PDF](individual/B-Ra1e3-medium_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_buoyancy_factor.png) / [PDF](individual/B-Ra1e3-medium_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_centreline.png) / [PDF](individual/B-Ra1e3-medium_centreline.pdf)|centreline|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_local_Nu.png) / [PDF](individual/B-Ra1e3-medium_local_Nu.pdf)|local_Nu|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_section_Nu.png) / [PDF](individual/B-Ra1e3-medium_section_Nu.pdf)|section_Nu|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-medium_temperature_centreline.png) / [PDF](individual/B-Ra1e3-medium_temperature_centreline.pdf)|temperature centreline|B-Ra1e3-medium|
|[PNG](individual/B-Ra1e3-fine_temperature.png) / [PDF](individual/B-Ra1e3-fine_temperature.pdf)|temperature|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_streamlines.png) / [PDF](individual/B-Ra1e3-fine_streamlines.pdf)|streamlines|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_velocity_magnitude.png) / [PDF](individual/B-Ra1e3-fine_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_buoyancy_factor.png) / [PDF](individual/B-Ra1e3-fine_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_centreline.png) / [PDF](individual/B-Ra1e3-fine_centreline.pdf)|centreline|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_local_Nu.png) / [PDF](individual/B-Ra1e3-fine_local_Nu.pdf)|local_Nu|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_section_Nu.png) / [PDF](individual/B-Ra1e3-fine_section_Nu.pdf)|section_Nu|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e3-fine_temperature_centreline.png) / [PDF](individual/B-Ra1e3-fine_temperature_centreline.pdf)|temperature centreline|B-Ra1e3-fine|
|[PNG](individual/B-Ra1e4-coarse_temperature.png) / [PDF](individual/B-Ra1e4-coarse_temperature.pdf)|temperature|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_streamlines.png) / [PDF](individual/B-Ra1e4-coarse_streamlines.pdf)|streamlines|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_velocity_magnitude.png) / [PDF](individual/B-Ra1e4-coarse_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_buoyancy_factor.png) / [PDF](individual/B-Ra1e4-coarse_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_centreline.png) / [PDF](individual/B-Ra1e4-coarse_centreline.pdf)|centreline|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_local_Nu.png) / [PDF](individual/B-Ra1e4-coarse_local_Nu.pdf)|local_Nu|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_section_Nu.png) / [PDF](individual/B-Ra1e4-coarse_section_Nu.pdf)|section_Nu|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-coarse_temperature_centreline.png) / [PDF](individual/B-Ra1e4-coarse_temperature_centreline.pdf)|temperature centreline|B-Ra1e4-coarse|
|[PNG](individual/B-Ra1e4-medium_temperature.png) / [PDF](individual/B-Ra1e4-medium_temperature.pdf)|temperature|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_streamlines.png) / [PDF](individual/B-Ra1e4-medium_streamlines.pdf)|streamlines|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_velocity_magnitude.png) / [PDF](individual/B-Ra1e4-medium_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_buoyancy_factor.png) / [PDF](individual/B-Ra1e4-medium_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_centreline.png) / [PDF](individual/B-Ra1e4-medium_centreline.pdf)|centreline|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_local_Nu.png) / [PDF](individual/B-Ra1e4-medium_local_Nu.pdf)|local_Nu|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_section_Nu.png) / [PDF](individual/B-Ra1e4-medium_section_Nu.pdf)|section_Nu|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-medium_temperature_centreline.png) / [PDF](individual/B-Ra1e4-medium_temperature_centreline.pdf)|temperature centreline|B-Ra1e4-medium|
|[PNG](individual/B-Ra1e4-fine_temperature.png) / [PDF](individual/B-Ra1e4-fine_temperature.pdf)|temperature|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_streamlines.png) / [PDF](individual/B-Ra1e4-fine_streamlines.pdf)|streamlines|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_velocity_magnitude.png) / [PDF](individual/B-Ra1e4-fine_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_buoyancy_factor.png) / [PDF](individual/B-Ra1e4-fine_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_centreline.png) / [PDF](individual/B-Ra1e4-fine_centreline.pdf)|centreline|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_local_Nu.png) / [PDF](individual/B-Ra1e4-fine_local_Nu.pdf)|local_Nu|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_section_Nu.png) / [PDF](individual/B-Ra1e4-fine_section_Nu.pdf)|section_Nu|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e4-fine_temperature_centreline.png) / [PDF](individual/B-Ra1e4-fine_temperature_centreline.pdf)|temperature centreline|B-Ra1e4-fine|
|[PNG](individual/B-Ra1e5-coarse_temperature.png) / [PDF](individual/B-Ra1e5-coarse_temperature.pdf)|temperature|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_streamlines.png) / [PDF](individual/B-Ra1e5-coarse_streamlines.pdf)|streamlines|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_velocity_magnitude.png) / [PDF](individual/B-Ra1e5-coarse_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_buoyancy_factor.png) / [PDF](individual/B-Ra1e5-coarse_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_centreline.png) / [PDF](individual/B-Ra1e5-coarse_centreline.pdf)|centreline|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_local_Nu.png) / [PDF](individual/B-Ra1e5-coarse_local_Nu.pdf)|local_Nu|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_section_Nu.png) / [PDF](individual/B-Ra1e5-coarse_section_Nu.pdf)|section_Nu|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-coarse_temperature_centreline.png) / [PDF](individual/B-Ra1e5-coarse_temperature_centreline.pdf)|temperature centreline|B-Ra1e5-coarse|
|[PNG](individual/B-Ra1e5-medium_temperature.png) / [PDF](individual/B-Ra1e5-medium_temperature.pdf)|temperature|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_streamlines.png) / [PDF](individual/B-Ra1e5-medium_streamlines.pdf)|streamlines|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_velocity_magnitude.png) / [PDF](individual/B-Ra1e5-medium_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_buoyancy_factor.png) / [PDF](individual/B-Ra1e5-medium_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_centreline.png) / [PDF](individual/B-Ra1e5-medium_centreline.pdf)|centreline|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_local_Nu.png) / [PDF](individual/B-Ra1e5-medium_local_Nu.pdf)|local_Nu|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_section_Nu.png) / [PDF](individual/B-Ra1e5-medium_section_Nu.pdf)|section_Nu|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-medium_temperature_centreline.png) / [PDF](individual/B-Ra1e5-medium_temperature_centreline.pdf)|temperature centreline|B-Ra1e5-medium|
|[PNG](individual/B-Ra1e5-fine_temperature.png) / [PDF](individual/B-Ra1e5-fine_temperature.pdf)|temperature|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_streamlines.png) / [PDF](individual/B-Ra1e5-fine_streamlines.pdf)|streamlines|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_velocity_magnitude.png) / [PDF](individual/B-Ra1e5-fine_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_buoyancy_factor.png) / [PDF](individual/B-Ra1e5-fine_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_centreline.png) / [PDF](individual/B-Ra1e5-fine_centreline.pdf)|centreline|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_local_Nu.png) / [PDF](individual/B-Ra1e5-fine_local_Nu.pdf)|local_Nu|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_section_Nu.png) / [PDF](individual/B-Ra1e5-fine_section_Nu.pdf)|section_Nu|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e5-fine_temperature_centreline.png) / [PDF](individual/B-Ra1e5-fine_temperature_centreline.pdf)|temperature centreline|B-Ra1e5-fine|
|[PNG](individual/B-Ra1e6-coarse_temperature.png) / [PDF](individual/B-Ra1e6-coarse_temperature.pdf)|temperature|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_streamlines.png) / [PDF](individual/B-Ra1e6-coarse_streamlines.pdf)|streamlines|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_velocity_magnitude.png) / [PDF](individual/B-Ra1e6-coarse_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_buoyancy_factor.png) / [PDF](individual/B-Ra1e6-coarse_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_centreline.png) / [PDF](individual/B-Ra1e6-coarse_centreline.pdf)|centreline|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_local_Nu.png) / [PDF](individual/B-Ra1e6-coarse_local_Nu.pdf)|local_Nu|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_section_Nu.png) / [PDF](individual/B-Ra1e6-coarse_section_Nu.pdf)|section_Nu|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-coarse_temperature_centreline.png) / [PDF](individual/B-Ra1e6-coarse_temperature_centreline.pdf)|temperature centreline|B-Ra1e6-coarse|
|[PNG](individual/B-Ra1e6-medium_temperature.png) / [PDF](individual/B-Ra1e6-medium_temperature.pdf)|temperature|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_streamlines.png) / [PDF](individual/B-Ra1e6-medium_streamlines.pdf)|streamlines|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_velocity_magnitude.png) / [PDF](individual/B-Ra1e6-medium_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_buoyancy_factor.png) / [PDF](individual/B-Ra1e6-medium_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_centreline.png) / [PDF](individual/B-Ra1e6-medium_centreline.pdf)|centreline|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_local_Nu.png) / [PDF](individual/B-Ra1e6-medium_local_Nu.pdf)|local_Nu|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_section_Nu.png) / [PDF](individual/B-Ra1e6-medium_section_Nu.pdf)|section_Nu|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-medium_temperature_centreline.png) / [PDF](individual/B-Ra1e6-medium_temperature_centreline.pdf)|temperature centreline|B-Ra1e6-medium|
|[PNG](individual/B-Ra1e6-fine_temperature.png) / [PDF](individual/B-Ra1e6-fine_temperature.pdf)|temperature|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_streamlines.png) / [PDF](individual/B-Ra1e6-fine_streamlines.pdf)|streamlines|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_velocity_magnitude.png) / [PDF](individual/B-Ra1e6-fine_velocity_magnitude.pdf)|velocity_magnitude|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_buoyancy_factor.png) / [PDF](individual/B-Ra1e6-fine_buoyancy_factor.pdf)|buoyancy_factor|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_centreline.png) / [PDF](individual/B-Ra1e6-fine_centreline.pdf)|centreline|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_local_Nu.png) / [PDF](individual/B-Ra1e6-fine_local_Nu.pdf)|local_Nu|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_section_Nu.png) / [PDF](individual/B-Ra1e6-fine_section_Nu.pdf)|section_Nu|B-Ra1e6-fine|
|[PNG](individual/B-Ra1e6-fine_temperature_centreline.png) / [PDF](individual/B-Ra1e6-fine_temperature_centreline.pdf)|temperature centreline|B-Ra1e6-fine|
|[PNG](comparison/auxiliary/individual/A-COND_temperature.png) / [PDF](comparison/auxiliary/individual/A-COND_temperature.pdf)|temperature|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_streamlines.png) / [PDF](comparison/auxiliary/individual/A-COND_streamlines.pdf)|streamlines|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_velocity_magnitude.png) / [PDF](comparison/auxiliary/individual/A-COND_velocity_magnitude.pdf)|velocity_magnitude|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_density_deviation.png) / [PDF](comparison/auxiliary/individual/A-COND_density_deviation.pdf)|density_deviation|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_centreline.png) / [PDF](comparison/auxiliary/individual/A-COND_centreline.pdf)|centreline|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_local_Nu.png) / [PDF](comparison/auxiliary/individual/A-COND_local_Nu.pdf)|local_Nu|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_section_Nu.png) / [PDF](comparison/auxiliary/individual/A-COND_section_Nu.pdf)|section_Nu|A-COND|
|[PNG](comparison/auxiliary/individual/A-COND_temperature_centreline.png) / [PDF](comparison/auxiliary/individual/A-COND_temperature_centreline.pdf)|temperature centreline|A-COND|
|[PNG](comparison/auxiliary/individual/A-SMOKE_temperature.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_temperature.pdf)|temperature|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_streamlines.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_streamlines.pdf)|streamlines|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_velocity_magnitude.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_velocity_magnitude.pdf)|velocity_magnitude|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_density_deviation.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_density_deviation.pdf)|density_deviation|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_centreline.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_centreline.pdf)|centreline|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_local_Nu.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_local_Nu.pdf)|local_Nu|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_section_Nu.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_section_Nu.pdf)|section_Nu|A-SMOKE|
|[PNG](comparison/auxiliary/individual/A-SMOKE_temperature_centreline.png) / [PDF](comparison/auxiliary/individual/A-SMOKE_temperature_centreline.pdf)|temperature centreline|A-SMOKE|
|[PNG](comparison/auxiliary/individual/B-COND_temperature.png) / [PDF](comparison/auxiliary/individual/B-COND_temperature.pdf)|temperature|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_streamlines.png) / [PDF](comparison/auxiliary/individual/B-COND_streamlines.pdf)|streamlines|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_velocity_magnitude.png) / [PDF](comparison/auxiliary/individual/B-COND_velocity_magnitude.pdf)|velocity_magnitude|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_buoyancy_factor.png) / [PDF](comparison/auxiliary/individual/B-COND_buoyancy_factor.pdf)|buoyancy_factor|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_centreline.png) / [PDF](comparison/auxiliary/individual/B-COND_centreline.pdf)|centreline|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_local_Nu.png) / [PDF](comparison/auxiliary/individual/B-COND_local_Nu.pdf)|local_Nu|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_section_Nu.png) / [PDF](comparison/auxiliary/individual/B-COND_section_Nu.pdf)|section_Nu|B-COND|
|[PNG](comparison/auxiliary/individual/B-COND_temperature_centreline.png) / [PDF](comparison/auxiliary/individual/B-COND_temperature_centreline.pdf)|temperature centreline|B-COND|
|[PNG](comparison/auxiliary/individual/B-SMOKE_temperature.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_temperature.pdf)|temperature|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_streamlines.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_streamlines.pdf)|streamlines|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_velocity_magnitude.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_velocity_magnitude.pdf)|velocity_magnitude|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_buoyancy_factor.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_buoyancy_factor.pdf)|buoyancy_factor|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_centreline.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_centreline.pdf)|centreline|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_local_Nu.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_local_Nu.pdf)|local_Nu|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_section_Nu.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_section_Nu.pdf)|section_Nu|B-SMOKE|
|[PNG](comparison/auxiliary/individual/B-SMOKE_temperature_centreline.png) / [PDF](comparison/auxiliary/individual/B-SMOKE_temperature_centreline.pdf)|temperature centreline|B-SMOKE|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_temperature.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_temperature.pdf)|temperature|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_streamlines.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_streamlines.pdf)|streamlines|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_velocity_magnitude.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_velocity_magnitude.pdf)|velocity_magnitude|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_density_deviation.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_density_deviation.pdf)|density_deviation|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_centreline.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_centreline.pdf)|centreline|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_local_Nu.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_local_Nu.pdf)|local_Nu|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_section_Nu.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_section_Nu.pdf)|section_Nu|A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_temperature_centreline.png) / [PDF](comparison/sensitivity/individual/A-H-Ra1e6-fine-beta1e-4_temperature_centreline.pdf)|temperature centreline|A-H-Ra1e6-fine-beta1e-4|
|[PNG](montage/RouteA_temperature_12panels.png) / [PDF](montage/RouteA_temperature_12panels.pdf)|4 Ra x 3 grid temperature|A-Ra1e3-coarse;A-Ra1e3-medium;A-Ra1e3-fine;A-Ra1e4-coarse;A-Ra1e4-medium;A-Ra1e4-fine;A-Ra1e5-coarse;A-Ra1e5-medium;A-Ra1e5-fine;A-Ra1e6-coarse;A-Ra1e6-medium;A-Ra1e6-fine|
|[PNG](montage/RouteA_streamlines_12panels.png) / [PDF](montage/RouteA_streamlines_12panels.pdf)|4 Ra x 3 grid streamlines|A-Ra1e3-coarse;A-Ra1e3-medium;A-Ra1e3-fine;A-Ra1e4-coarse;A-Ra1e4-medium;A-Ra1e4-fine;A-Ra1e5-coarse;A-Ra1e5-medium;A-Ra1e5-fine;A-Ra1e6-coarse;A-Ra1e6-medium;A-Ra1e6-fine|
|[PNG](montage/RouteB_temperature_12panels.png) / [PDF](montage/RouteB_temperature_12panels.pdf)|4 Ra x 3 grid temperature|B-Ra1e3-coarse;B-Ra1e3-medium;B-Ra1e3-fine;B-Ra1e4-coarse;B-Ra1e4-medium;B-Ra1e4-fine;B-Ra1e5-coarse;B-Ra1e5-medium;B-Ra1e5-fine;B-Ra1e6-coarse;B-Ra1e6-medium;B-Ra1e6-fine|
|[PNG](montage/RouteB_streamlines_12panels.png) / [PDF](montage/RouteB_streamlines_12panels.pdf)|4 Ra x 3 grid streamlines|B-Ra1e3-coarse;B-Ra1e3-medium;B-Ra1e3-fine;B-Ra1e4-coarse;B-Ra1e4-medium;B-Ra1e4-fine;B-Ra1e5-coarse;B-Ra1e5-medium;B-Ra1e5-fine;B-Ra1e6-coarse;B-Ra1e6-medium;B-Ra1e6-fine|
|[PNG](montage/fine_AB_temperature_8panels.png) / [PDF](montage/fine_AB_temperature_8panels.pdf)|temperature fine A/B matrix|A-Ra1e3-fine;B-Ra1e3-fine;A-Ra1e4-fine;B-Ra1e4-fine;A-Ra1e5-fine;B-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](comparison/fine_Ra1000_AB_temperature.png) / [PDF](comparison/fine_Ra1000_AB_temperature.pdf)|temperature pair|A-Ra1e3-fine;B-Ra1e3-fine|
|[PNG](comparison/fine_Ra10000_AB_temperature.png) / [PDF](comparison/fine_Ra10000_AB_temperature.pdf)|temperature pair|A-Ra1e4-fine;B-Ra1e4-fine|
|[PNG](comparison/fine_Ra100000_AB_temperature.png) / [PDF](comparison/fine_Ra100000_AB_temperature.pdf)|temperature pair|A-Ra1e5-fine;B-Ra1e5-fine|
|[PNG](comparison/fine_Ra1000000_AB_temperature.png) / [PDF](comparison/fine_Ra1000000_AB_temperature.pdf)|temperature pair|A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](montage/fine_AB_streamlines_8panels.png) / [PDF](montage/fine_AB_streamlines_8panels.pdf)|streamlines fine A/B matrix|A-Ra1e3-fine;B-Ra1e3-fine;A-Ra1e4-fine;B-Ra1e4-fine;A-Ra1e5-fine;B-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](comparison/fine_Ra1000_AB_streamlines.png) / [PDF](comparison/fine_Ra1000_AB_streamlines.pdf)|streamlines pair|A-Ra1e3-fine;B-Ra1e3-fine|
|[PNG](comparison/fine_Ra10000_AB_streamlines.png) / [PDF](comparison/fine_Ra10000_AB_streamlines.pdf)|streamlines pair|A-Ra1e4-fine;B-Ra1e4-fine|
|[PNG](comparison/fine_Ra100000_AB_streamlines.png) / [PDF](comparison/fine_Ra100000_AB_streamlines.pdf)|streamlines pair|A-Ra1e5-fine;B-Ra1e5-fine|
|[PNG](comparison/fine_Ra1000000_AB_streamlines.png) / [PDF](comparison/fine_Ra1000000_AB_streamlines.pdf)|streamlines pair|A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](montage/fine_AB_velocity_magnitude_8panels.png) / [PDF](montage/fine_AB_velocity_magnitude_8panels.pdf)|velocity_magnitude fine A/B matrix|A-Ra1e3-fine;B-Ra1e3-fine;A-Ra1e4-fine;B-Ra1e4-fine;A-Ra1e5-fine;B-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](comparison/fine_Ra1000_AB_velocity_magnitude.png) / [PDF](comparison/fine_Ra1000_AB_velocity_magnitude.pdf)|velocity_magnitude pair|A-Ra1e3-fine;B-Ra1e3-fine|
|[PNG](comparison/fine_Ra10000_AB_velocity_magnitude.png) / [PDF](comparison/fine_Ra10000_AB_velocity_magnitude.pdf)|velocity_magnitude pair|A-Ra1e4-fine;B-Ra1e4-fine|
|[PNG](comparison/fine_Ra100000_AB_velocity_magnitude.png) / [PDF](comparison/fine_Ra100000_AB_velocity_magnitude.pdf)|velocity_magnitude pair|A-Ra1e5-fine;B-Ra1e5-fine|
|[PNG](comparison/fine_Ra1000000_AB_velocity_magnitude.png) / [PDF](comparison/fine_Ra1000000_AB_velocity_magnitude.pdf)|velocity_magnitude pair|A-Ra1e6-fine;B-Ra1e6-fine|
|[PNG](comparison/grid_dependence_Ra1000.png) / [PDF](comparison/grid_dependence_Ra1000.pdf)|Nu/Umax/Wmax versus grid|A-Ra1e3-coarse;A-Ra1e3-fine;A-Ra1e3-medium;B-Ra1e3-coarse;B-Ra1e3-fine;B-Ra1e3-medium|
|[PNG](comparison/grid_dependence_Ra10000.png) / [PDF](comparison/grid_dependence_Ra10000.pdf)|Nu/Umax/Wmax versus grid|A-Ra1e4-coarse;A-Ra1e4-fine;A-Ra1e4-medium;B-Ra1e4-coarse;B-Ra1e4-fine;B-Ra1e4-medium|
|[PNG](comparison/grid_dependence_Ra100000.png) / [PDF](comparison/grid_dependence_Ra100000.pdf)|Nu/Umax/Wmax versus grid|A-Ra1e5-coarse;A-Ra1e5-fine;A-Ra1e5-medium;B-Ra1e5-coarse;B-Ra1e5-fine;B-Ra1e5-medium|
|[PNG](comparison/grid_dependence_Ra1000000.png) / [PDF](comparison/grid_dependence_Ra1000000.pdf)|Nu/Umax/Wmax versus grid|A-Ra1e6-coarse;A-Ra1e6-fine;A-Ra1e6-medium;B-Ra1e6-coarse;B-Ra1e6-fine;B-Ra1e6-medium|
|[PNG](comparison/paper_fine_Nu_bar_cavity_value.png) / [PDF](comparison/paper_fine_Nu_bar_cavity_value.pdf)|paper QoI|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/paper_fine_Nu_bar_cavity_error.png) / [PDF](comparison/paper_fine_Nu_bar_cavity_error.pdf)|paper absolute relative difference|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/paper_fine_Umax_value.png) / [PDF](comparison/paper_fine_Umax_value.pdf)|paper QoI|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/paper_fine_Umax_error.png) / [PDF](comparison/paper_fine_Umax_error.pdf)|paper absolute relative difference|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/paper_fine_Wmax_value.png) / [PDF](comparison/paper_fine_Wmax_value.pdf)|paper QoI|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/paper_fine_Wmax_error.png) / [PDF](comparison/paper_fine_Wmax_error.pdf)|paper absolute relative difference|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](tables/gate_F_detail.png) / [PDF](tables/gate_F_detail.pdf)|Existing Gate F evidence; *B Ra=1e6: unaccepted grid (full status in source CSV)||
|[PNG](comparison/routeA_vs_routeB_fine.png) / [PDF](comparison/routeA_vs_routeB_fine.pdf)|six comparable QoIs A vs B|A-Ra1e3-fine;A-Ra1e4-fine;A-Ra1e5-fine;A-Ra1e6-fine;B-Ra1e3-fine;B-Ra1e4-fine;B-Ra1e5-fine;B-Ra1e6-fine|
|[PNG](comparison/sensitivity/GateH_temperature.png) / [PDF](comparison/sensitivity/GateH_temperature.pdf)|temperature pair|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_streamlines.png) / [PDF](comparison/sensitivity/GateH_streamlines.pdf)|streamlines pair|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_velocity_magnitude.png) / [PDF](comparison/sensitivity/GateH_velocity_magnitude.pdf)|velocity_magnitude pair|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_density_deviation.png) / [PDF](comparison/sensitivity/GateH_density_deviation.pdf)|density_deviation pair|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_centreline.png) / [PDF](comparison/sensitivity/GateH_centreline.pdf)|Gate H centreline|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_local_Nu.png) / [PDF](comparison/sensitivity/GateH_local_Nu.pdf)|Gate H local_Nu|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_section_Nu.png) / [PDF](comparison/sensitivity/GateH_section_Nu.pdf)|Gate H section_Nu|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/sensitivity/GateH_primary_relative_difference.png) / [PDF](comparison/sensitivity/GateH_primary_relative_difference.pdf)|Gate H three primary differences|A-Ra1e6-fine;A-H-Ra1e6-fine-beta1e-4|
|[PNG](comparison/RouteA_convergence_conservation.png) / [PDF](comparison/RouteA_convergence_conservation.pdf)|separate-route convergence/conservation indicators|A-Ra1e3-coarse;A-Ra1e3-medium;A-Ra1e3-fine;A-Ra1e4-coarse;A-Ra1e4-medium;A-Ra1e4-fine;A-Ra1e5-coarse;A-Ra1e5-medium;A-Ra1e5-fine;A-Ra1e6-coarse;A-Ra1e6-medium;A-Ra1e6-fine|
|[PNG](comparison/RouteB_convergence_conservation.png) / [PDF](comparison/RouteB_convergence_conservation.pdf)|separate-route convergence/conservation indicators|B-Ra1e3-coarse;B-Ra1e3-medium;B-Ra1e3-fine;B-Ra1e4-coarse;B-Ra1e4-medium;B-Ra1e4-fine;B-Ra1e5-coarse;B-Ra1e5-medium;B-Ra1e5-fine;B-Ra1e6-coarse;B-Ra1e6-medium;B-Ra1e6-fine|
|[PNG](comparison/RouteA_density_amplitude.png) / [PDF](comparison/RouteA_density_amplitude.pdf)|Route A density amplitude|A-Ra1e3-coarse;A-Ra1e3-medium;A-Ra1e3-fine;A-Ra1e4-coarse;A-Ra1e4-medium;A-Ra1e4-fine;A-Ra1e5-coarse;A-Ra1e5-medium;A-Ra1e5-fine;A-Ra1e6-coarse;A-Ra1e6-medium;A-Ra1e6-fine|
|[PNG](comparison/auxiliary/COND_AB_temperature.png) / [PDF](comparison/auxiliary/COND_AB_temperature.pdf)|temperature pair|A-COND;B-COND|
|[PNG](comparison/auxiliary/COND_AB_streamlines.png) / [PDF](comparison/auxiliary/COND_AB_streamlines.pdf)|streamlines pair|A-COND;B-COND|
|[PNG](comparison/auxiliary/SMOKE_AB_temperature.png) / [PDF](comparison/auxiliary/SMOKE_AB_temperature.pdf)|temperature pair|A-SMOKE;B-SMOKE|
|[PNG](comparison/auxiliary/SMOKE_AB_streamlines.png) / [PDF](comparison/auxiliary/SMOKE_AB_streamlines.pdf)|streamlines pair|A-SMOKE;B-SMOKE|
|[PNG](tables/formal_matrix_status.png) / [PDF](tables/formal_matrix_status.pdf)|Existing matrix statuses (no reclassification)||

## CSV一覧

- `data/all_case_summary.csv`：ケース対応・正式状態・主要量・温度範囲・密度振幅。
- `data/paper_comparison_fine.csv`：fine の3量と Table V 絶対相対差[%]。
- `data/routeA_vs_routeB_fine.csv`：既存 AB 比較CSVを分類・原精度付きで保存（NOT_LIKE_FOR_LIKE含む；図の対象からは除外）。
- `data/grid_convergence.csv`：全正式ケースの格子依存・参照差。
- `data/gate_F_detail.csv`：既存 fine-medium差[%]・p_obs・GCI[%]・判定。未定義/未評価を文字列のまま保存。
- `data/convergence_conservation.csv`：residual、Rwin、熱収支、section偏差、native/再構成divergence、対称性。
- `data/routeA_density_summary.csv` / `data/GateH_density_diagnostics.csv`：EOS密度範囲・感度。
- `data/GateH_comparison.csv`：既存 Gate H 比較と分類。
- `data/temperature_overshoot.csv`：温度範囲と範囲外セル数。
- `data/centreline_<case>.csv`：4097点 U/W。
- `data/local_Nu_<case>.csv`：壁局所Nu；B2診断値を別列。
- `data/section_Nu_<case>.csv`：断面 Nu と cavity 水平線値・operator。
- `data/temperature_centreline_<case>.csv`：4097点温度線（追加の表示用定義；原論文硬判定には使用しない）。
- `data/field_<case>.csv`：実セルの X/Z/theta/U*/W*/速度絶対値・密度偏差または rhok。
- `tables/figure_inventory.csv`, `tables/csv_inventory.csv`, `tables/case_status.csv`, `tables/gate_summary.csv`：全ファイル対応表・既存判定一覧。

完全な CSV ファイル一覧：

- [data/GateH_comparison.csv](data/GateH_comparison.csv)
- [data/GateH_density_diagnostics.csv](data/GateH_density_diagnostics.csv)
- [data/all_case_summary.csv](data/all_case_summary.csv)
- [data/centreline_A-COND.csv](data/centreline_A-COND.csv)
- [data/centreline_A-H-Ra1e6-fine-beta1e-4.csv](data/centreline_A-H-Ra1e6-fine-beta1e-4.csv)
- [data/centreline_A-Ra1e3-coarse.csv](data/centreline_A-Ra1e3-coarse.csv)
- [data/centreline_A-Ra1e3-fine.csv](data/centreline_A-Ra1e3-fine.csv)
- [data/centreline_A-Ra1e3-medium.csv](data/centreline_A-Ra1e3-medium.csv)
- [data/centreline_A-Ra1e4-coarse.csv](data/centreline_A-Ra1e4-coarse.csv)
- [data/centreline_A-Ra1e4-fine.csv](data/centreline_A-Ra1e4-fine.csv)
- [data/centreline_A-Ra1e4-medium.csv](data/centreline_A-Ra1e4-medium.csv)
- [data/centreline_A-Ra1e5-coarse.csv](data/centreline_A-Ra1e5-coarse.csv)
- [data/centreline_A-Ra1e5-fine.csv](data/centreline_A-Ra1e5-fine.csv)
- [data/centreline_A-Ra1e5-medium.csv](data/centreline_A-Ra1e5-medium.csv)
- [data/centreline_A-Ra1e6-coarse.csv](data/centreline_A-Ra1e6-coarse.csv)
- [data/centreline_A-Ra1e6-fine.csv](data/centreline_A-Ra1e6-fine.csv)
- [data/centreline_A-Ra1e6-medium.csv](data/centreline_A-Ra1e6-medium.csv)
- [data/centreline_A-SMOKE.csv](data/centreline_A-SMOKE.csv)
- [data/centreline_B-COND.csv](data/centreline_B-COND.csv)
- [data/centreline_B-Ra1e3-coarse.csv](data/centreline_B-Ra1e3-coarse.csv)
- [data/centreline_B-Ra1e3-fine.csv](data/centreline_B-Ra1e3-fine.csv)
- [data/centreline_B-Ra1e3-medium.csv](data/centreline_B-Ra1e3-medium.csv)
- [data/centreline_B-Ra1e4-coarse.csv](data/centreline_B-Ra1e4-coarse.csv)
- [data/centreline_B-Ra1e4-fine.csv](data/centreline_B-Ra1e4-fine.csv)
- [data/centreline_B-Ra1e4-medium.csv](data/centreline_B-Ra1e4-medium.csv)
- [data/centreline_B-Ra1e5-coarse.csv](data/centreline_B-Ra1e5-coarse.csv)
- [data/centreline_B-Ra1e5-fine.csv](data/centreline_B-Ra1e5-fine.csv)
- [data/centreline_B-Ra1e5-medium.csv](data/centreline_B-Ra1e5-medium.csv)
- [data/centreline_B-Ra1e6-coarse.csv](data/centreline_B-Ra1e6-coarse.csv)
- [data/centreline_B-Ra1e6-fine.csv](data/centreline_B-Ra1e6-fine.csv)
- [data/centreline_B-Ra1e6-medium.csv](data/centreline_B-Ra1e6-medium.csv)
- [data/centreline_B-SMOKE.csv](data/centreline_B-SMOKE.csv)
- [data/convergence_conservation.csv](data/convergence_conservation.csv)
- [data/field_A-COND.csv](data/field_A-COND.csv)
- [data/field_A-H-Ra1e6-fine-beta1e-4.csv](data/field_A-H-Ra1e6-fine-beta1e-4.csv)
- [data/field_A-Ra1e3-coarse.csv](data/field_A-Ra1e3-coarse.csv)
- [data/field_A-Ra1e3-fine.csv](data/field_A-Ra1e3-fine.csv)
- [data/field_A-Ra1e3-medium.csv](data/field_A-Ra1e3-medium.csv)
- [data/field_A-Ra1e4-coarse.csv](data/field_A-Ra1e4-coarse.csv)
- [data/field_A-Ra1e4-fine.csv](data/field_A-Ra1e4-fine.csv)
- [data/field_A-Ra1e4-medium.csv](data/field_A-Ra1e4-medium.csv)
- [data/field_A-Ra1e5-coarse.csv](data/field_A-Ra1e5-coarse.csv)
- [data/field_A-Ra1e5-fine.csv](data/field_A-Ra1e5-fine.csv)
- [data/field_A-Ra1e5-medium.csv](data/field_A-Ra1e5-medium.csv)
- [data/field_A-Ra1e6-coarse.csv](data/field_A-Ra1e6-coarse.csv)
- [data/field_A-Ra1e6-fine.csv](data/field_A-Ra1e6-fine.csv)
- [data/field_A-Ra1e6-medium.csv](data/field_A-Ra1e6-medium.csv)
- [data/field_A-SMOKE.csv](data/field_A-SMOKE.csv)
- [data/field_B-COND.csv](data/field_B-COND.csv)
- [data/field_B-Ra1e3-coarse.csv](data/field_B-Ra1e3-coarse.csv)
- [data/field_B-Ra1e3-fine.csv](data/field_B-Ra1e3-fine.csv)
- [data/field_B-Ra1e3-medium.csv](data/field_B-Ra1e3-medium.csv)
- [data/field_B-Ra1e4-coarse.csv](data/field_B-Ra1e4-coarse.csv)
- [data/field_B-Ra1e4-fine.csv](data/field_B-Ra1e4-fine.csv)
- [data/field_B-Ra1e4-medium.csv](data/field_B-Ra1e4-medium.csv)
- [data/field_B-Ra1e5-coarse.csv](data/field_B-Ra1e5-coarse.csv)
- [data/field_B-Ra1e5-fine.csv](data/field_B-Ra1e5-fine.csv)
- [data/field_B-Ra1e5-medium.csv](data/field_B-Ra1e5-medium.csv)
- [data/field_B-Ra1e6-coarse.csv](data/field_B-Ra1e6-coarse.csv)
- [data/field_B-Ra1e6-fine.csv](data/field_B-Ra1e6-fine.csv)
- [data/field_B-Ra1e6-medium.csv](data/field_B-Ra1e6-medium.csv)
- [data/field_B-SMOKE.csv](data/field_B-SMOKE.csv)
- [data/gate_F_detail.csv](data/gate_F_detail.csv)
- [data/grid_convergence.csv](data/grid_convergence.csv)
- [data/local_Nu_A-COND.csv](data/local_Nu_A-COND.csv)
- [data/local_Nu_A-H-Ra1e6-fine-beta1e-4.csv](data/local_Nu_A-H-Ra1e6-fine-beta1e-4.csv)
- [data/local_Nu_A-Ra1e3-coarse.csv](data/local_Nu_A-Ra1e3-coarse.csv)
- [data/local_Nu_A-Ra1e3-fine.csv](data/local_Nu_A-Ra1e3-fine.csv)
- [data/local_Nu_A-Ra1e3-medium.csv](data/local_Nu_A-Ra1e3-medium.csv)
- [data/local_Nu_A-Ra1e4-coarse.csv](data/local_Nu_A-Ra1e4-coarse.csv)
- [data/local_Nu_A-Ra1e4-fine.csv](data/local_Nu_A-Ra1e4-fine.csv)
- [data/local_Nu_A-Ra1e4-medium.csv](data/local_Nu_A-Ra1e4-medium.csv)
- [data/local_Nu_A-Ra1e5-coarse.csv](data/local_Nu_A-Ra1e5-coarse.csv)
- [data/local_Nu_A-Ra1e5-fine.csv](data/local_Nu_A-Ra1e5-fine.csv)
- [data/local_Nu_A-Ra1e5-medium.csv](data/local_Nu_A-Ra1e5-medium.csv)
- [data/local_Nu_A-Ra1e6-coarse.csv](data/local_Nu_A-Ra1e6-coarse.csv)
- [data/local_Nu_A-Ra1e6-fine.csv](data/local_Nu_A-Ra1e6-fine.csv)
- [data/local_Nu_A-Ra1e6-medium.csv](data/local_Nu_A-Ra1e6-medium.csv)
- [data/local_Nu_A-SMOKE.csv](data/local_Nu_A-SMOKE.csv)
- [data/local_Nu_B-COND.csv](data/local_Nu_B-COND.csv)
- [data/local_Nu_B-Ra1e3-coarse.csv](data/local_Nu_B-Ra1e3-coarse.csv)
- [data/local_Nu_B-Ra1e3-fine.csv](data/local_Nu_B-Ra1e3-fine.csv)
- [data/local_Nu_B-Ra1e3-medium.csv](data/local_Nu_B-Ra1e3-medium.csv)
- [data/local_Nu_B-Ra1e4-coarse.csv](data/local_Nu_B-Ra1e4-coarse.csv)
- [data/local_Nu_B-Ra1e4-fine.csv](data/local_Nu_B-Ra1e4-fine.csv)
- [data/local_Nu_B-Ra1e4-medium.csv](data/local_Nu_B-Ra1e4-medium.csv)
- [data/local_Nu_B-Ra1e5-coarse.csv](data/local_Nu_B-Ra1e5-coarse.csv)
- [data/local_Nu_B-Ra1e5-fine.csv](data/local_Nu_B-Ra1e5-fine.csv)
- [data/local_Nu_B-Ra1e5-medium.csv](data/local_Nu_B-Ra1e5-medium.csv)
- [data/local_Nu_B-Ra1e6-coarse.csv](data/local_Nu_B-Ra1e6-coarse.csv)
- [data/local_Nu_B-Ra1e6-fine.csv](data/local_Nu_B-Ra1e6-fine.csv)
- [data/local_Nu_B-Ra1e6-medium.csv](data/local_Nu_B-Ra1e6-medium.csv)
- [data/local_Nu_B-SMOKE.csv](data/local_Nu_B-SMOKE.csv)
- [data/paper_comparison_fine.csv](data/paper_comparison_fine.csv)
- [data/routeA_density_summary.csv](data/routeA_density_summary.csv)
- [data/routeA_vs_routeB_fine.csv](data/routeA_vs_routeB_fine.csv)
- [data/section_Nu_A-COND.csv](data/section_Nu_A-COND.csv)
- [data/section_Nu_A-H-Ra1e6-fine-beta1e-4.csv](data/section_Nu_A-H-Ra1e6-fine-beta1e-4.csv)
- [data/section_Nu_A-Ra1e3-coarse.csv](data/section_Nu_A-Ra1e3-coarse.csv)
- [data/section_Nu_A-Ra1e3-fine.csv](data/section_Nu_A-Ra1e3-fine.csv)
- [data/section_Nu_A-Ra1e3-medium.csv](data/section_Nu_A-Ra1e3-medium.csv)
- [data/section_Nu_A-Ra1e4-coarse.csv](data/section_Nu_A-Ra1e4-coarse.csv)
- [data/section_Nu_A-Ra1e4-fine.csv](data/section_Nu_A-Ra1e4-fine.csv)
- [data/section_Nu_A-Ra1e4-medium.csv](data/section_Nu_A-Ra1e4-medium.csv)
- [data/section_Nu_A-Ra1e5-coarse.csv](data/section_Nu_A-Ra1e5-coarse.csv)
- [data/section_Nu_A-Ra1e5-fine.csv](data/section_Nu_A-Ra1e5-fine.csv)
- [data/section_Nu_A-Ra1e5-medium.csv](data/section_Nu_A-Ra1e5-medium.csv)
- [data/section_Nu_A-Ra1e6-coarse.csv](data/section_Nu_A-Ra1e6-coarse.csv)
- [data/section_Nu_A-Ra1e6-fine.csv](data/section_Nu_A-Ra1e6-fine.csv)
- [data/section_Nu_A-Ra1e6-medium.csv](data/section_Nu_A-Ra1e6-medium.csv)
- [data/section_Nu_A-SMOKE.csv](data/section_Nu_A-SMOKE.csv)
- [data/section_Nu_B-COND.csv](data/section_Nu_B-COND.csv)
- [data/section_Nu_B-Ra1e3-coarse.csv](data/section_Nu_B-Ra1e3-coarse.csv)
- [data/section_Nu_B-Ra1e3-fine.csv](data/section_Nu_B-Ra1e3-fine.csv)
- [data/section_Nu_B-Ra1e3-medium.csv](data/section_Nu_B-Ra1e3-medium.csv)
- [data/section_Nu_B-Ra1e4-coarse.csv](data/section_Nu_B-Ra1e4-coarse.csv)
- [data/section_Nu_B-Ra1e4-fine.csv](data/section_Nu_B-Ra1e4-fine.csv)
- [data/section_Nu_B-Ra1e4-medium.csv](data/section_Nu_B-Ra1e4-medium.csv)
- [data/section_Nu_B-Ra1e5-coarse.csv](data/section_Nu_B-Ra1e5-coarse.csv)
- [data/section_Nu_B-Ra1e5-fine.csv](data/section_Nu_B-Ra1e5-fine.csv)
- [data/section_Nu_B-Ra1e5-medium.csv](data/section_Nu_B-Ra1e5-medium.csv)
- [data/section_Nu_B-Ra1e6-coarse.csv](data/section_Nu_B-Ra1e6-coarse.csv)
- [data/section_Nu_B-Ra1e6-fine.csv](data/section_Nu_B-Ra1e6-fine.csv)
- [data/section_Nu_B-Ra1e6-medium.csv](data/section_Nu_B-Ra1e6-medium.csv)
- [data/section_Nu_B-SMOKE.csv](data/section_Nu_B-SMOKE.csv)
- [data/temperature_centreline_A-COND.csv](data/temperature_centreline_A-COND.csv)
- [data/temperature_centreline_A-H-Ra1e6-fine-beta1e-4.csv](data/temperature_centreline_A-H-Ra1e6-fine-beta1e-4.csv)
- [data/temperature_centreline_A-Ra1e3-coarse.csv](data/temperature_centreline_A-Ra1e3-coarse.csv)
- [data/temperature_centreline_A-Ra1e3-fine.csv](data/temperature_centreline_A-Ra1e3-fine.csv)
- [data/temperature_centreline_A-Ra1e3-medium.csv](data/temperature_centreline_A-Ra1e3-medium.csv)
- [data/temperature_centreline_A-Ra1e4-coarse.csv](data/temperature_centreline_A-Ra1e4-coarse.csv)
- [data/temperature_centreline_A-Ra1e4-fine.csv](data/temperature_centreline_A-Ra1e4-fine.csv)
- [data/temperature_centreline_A-Ra1e4-medium.csv](data/temperature_centreline_A-Ra1e4-medium.csv)
- [data/temperature_centreline_A-Ra1e5-coarse.csv](data/temperature_centreline_A-Ra1e5-coarse.csv)
- [data/temperature_centreline_A-Ra1e5-fine.csv](data/temperature_centreline_A-Ra1e5-fine.csv)
- [data/temperature_centreline_A-Ra1e5-medium.csv](data/temperature_centreline_A-Ra1e5-medium.csv)
- [data/temperature_centreline_A-Ra1e6-coarse.csv](data/temperature_centreline_A-Ra1e6-coarse.csv)
- [data/temperature_centreline_A-Ra1e6-fine.csv](data/temperature_centreline_A-Ra1e6-fine.csv)
- [data/temperature_centreline_A-Ra1e6-medium.csv](data/temperature_centreline_A-Ra1e6-medium.csv)
- [data/temperature_centreline_A-SMOKE.csv](data/temperature_centreline_A-SMOKE.csv)
- [data/temperature_centreline_B-COND.csv](data/temperature_centreline_B-COND.csv)
- [data/temperature_centreline_B-Ra1e3-coarse.csv](data/temperature_centreline_B-Ra1e3-coarse.csv)
- [data/temperature_centreline_B-Ra1e3-fine.csv](data/temperature_centreline_B-Ra1e3-fine.csv)
- [data/temperature_centreline_B-Ra1e3-medium.csv](data/temperature_centreline_B-Ra1e3-medium.csv)
- [data/temperature_centreline_B-Ra1e4-coarse.csv](data/temperature_centreline_B-Ra1e4-coarse.csv)
- [data/temperature_centreline_B-Ra1e4-fine.csv](data/temperature_centreline_B-Ra1e4-fine.csv)
- [data/temperature_centreline_B-Ra1e4-medium.csv](data/temperature_centreline_B-Ra1e4-medium.csv)
- [data/temperature_centreline_B-Ra1e5-coarse.csv](data/temperature_centreline_B-Ra1e5-coarse.csv)
- [data/temperature_centreline_B-Ra1e5-fine.csv](data/temperature_centreline_B-Ra1e5-fine.csv)
- [data/temperature_centreline_B-Ra1e5-medium.csv](data/temperature_centreline_B-Ra1e5-medium.csv)
- [data/temperature_centreline_B-Ra1e6-coarse.csv](data/temperature_centreline_B-Ra1e6-coarse.csv)
- [data/temperature_centreline_B-Ra1e6-fine.csv](data/temperature_centreline_B-Ra1e6-fine.csv)
- [data/temperature_centreline_B-Ra1e6-medium.csv](data/temperature_centreline_B-Ra1e6-medium.csv)
- [data/temperature_centreline_B-SMOKE.csv](data/temperature_centreline_B-SMOKE.csv)
- [data/temperature_overshoot.csv](data/temperature_overshoot.csv)
- [logs/input_sha256.csv](logs/input_sha256.csv)
- [logs/numerical_checks.csv](logs/numerical_checks.csv)
- [tables/case_status.csv](tables/case_status.csv)
- [tables/csv_inventory.csv](tables/csv_inventory.csv)
- [tables/figure_inventory.csv](tables/figure_inventory.csv)
- [tables/gate_summary.csv](tables/gate_summary.csv)

## 再生成

Python 3 / numpy / matplotlib を使用。既存 field readers/analyzer をread-only importし、main()は呼びません。既存出力を上書きしないため、未使用の出力ディレクトリを指定してください。書込み先は `results/visualization_all_cases/` 内に制限しています。

```bash
cd /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark
OPENBLAS_NUM_THREADS=1 python3 -B Scripts/visualization/plot_all_cases.py --output results/visualization_all_cases/regenerated_001
```

`--case CASE_ID` で対象ケースの個別図だけを生成できます。その場合も正式状態・全ケース入力・比較sourceの検証と read-only 保護を実施し、`--output` に未使用パスを指定します。全図の一覧は本 full run の inventory を参照してください。

追加検査：全279 PNGの整合性・300 dpi表示、279 PDFのヘッダー、ケース別CSV行数・中心線壁endpointを確認し欠落ゼロ。数値照合の最大絶対差は1.7551e-12です。`logs/artifact_validation.json`、`logs/runtime_provenance.json`、`logs/generation.log` に検査・実行環境・処理ログを記録。Gate F図中の `NOT EVALUATED*` はB Ra=10⁶のunaccepted gridによる未評価の短縮表示で、CSVの元のstatus文字列を保持しています。
