# Route A 開始前レビュー

レビュー日: 2026-10-04（Asia/Tokyo）。**review / planning only**。solver、mesh生成、case生成、感度・非定常計算は今回実施していない。

結論: **4 Ra × 3 grid = 12ケースを維持**する。Route A は標準 v13 fluid/thermophysical framework のモデル・定式化差を評価する。正式合格を追い続ける計画にはせず、評価の完了と正式 Gate 合格を分ける。最初の solver 実行単位は **Ra=1e3 の40²/80²/160² trio、逐次実行**。ただし現在の実行開始判定は **NO**。Gate D の詳細と実行上限等を先に固定する。

## 1. HEAD・根拠・状態の優先順位

- 開始HEAD: `1961e87718071bafe4ebf74c7508fdd23ae503c5`。指定HEADと一致し、差分history調査は不要。
- 開始時の未追跡物: `cases/routeA/Ra0_medium/`、`cases/routeA/Ra1e4_coarse/`、`verification/`。保持する。
- 根拠: `openfoam_design.md` の既存監査 §2–5、8、10、13、`routeA_implementation.md`、A minimal CSV/manifest/2 metrics、`benchmark_spec.md` v1.4、`acceptance_criteria.md` v1.4、B final review/master CSV。
- ソース式は既存監査の引用。新しい OpenFOAM source audit、原論文の再読、B Gate G研究の再開は行わない。
- 設計書の古い「未実施」「Aを第一候補」等は historical。B現在値は最新 final review/masterを優先し、古い仕様書の状態表を上書きしない。
- 読み取った10 evidence/specファイルのSHA-256は `routeA_execution_plan.json` に保存した。

**仕様との重要な関係:** B final review は computed 12/12、accepted 9/12、`COMPLETE_WITH_DOCUMENTED_LIMITATIONS`を推奨している。Ra1e6 D FAIL、F FAIL/未評価、G FAIL/未評価が残り、formal completion NO、`BENCHMARK_CORE_PASS` NOT_EVALUATEDを保持する。B全正式合格が得られたとは扱わない。

現行規範の `ROUTE_A_CHARACTERIZED` は B core PASS と AのD/F/G等のPASSを必要とする。今回は規範を変更せず、別名の**作業上の到達点**を提案する。作業完了ラベルは正式ステータスの代替ではない。限界付き進行方針の採用、および将来の実行はユーザー判断とする。

## 2. 研究上の3比較

| 比較 | 役割 | 言えること／解釈の限界 |
|---|---|---|
| B vs de Vahl Davis | 古典非圧縮BoussinesqのFVM/SIMPLE Verification | 方程式対応＋数値benchmark。現在のB正式FAIL/未評価も開示 |
| A vs B | モデル・定式化差の評価 | 同一Ra/grid/QoIで比較。格子・反復・sampling・離散演算子差を併記して解釈 |
| A vs de Vahl Davis | practical benchmark comparison | 差はモデル差と数値・後処理差を含む。全てをOpenFOAM numerical errorとは呼ばない |

Route A は今後の流体―粒子連成に近い**標準frameworkを使う流体側の評価ルート**である。frameworkを使えたことは、粒子連成の保存性・力・熱輸送や実現象のValidationを保証しない。

## 3. Governing model: FACT / MODEL DIFFERENCE / POSSIBLE CONSEQUENCE

以下のFACTは `openfoam_design.md` §2–5、8の既存監査に限定する。連続体式の変形は同監査の**解析的推論**であり、離散式の厳密恒等式ではない。

| 項目 | FACT（既存監査） | MODEL DIFFERENCE（古典Route B） | POSSIBLE CONSEQUENCE（推論、今回未測定） |
|---|---|---|---|
| continuity | `ddt(rho)+div(phi)=0`、Aの補正phiは質量流束kg/s | Bはvolume-fluxによるdiv(u)=0。A定常はdiv(rho u)=0 | mass closureが良くてもdiv(u)非零。native fluxと再構成Uを別報告 |
| density / EOS | rho=rho0[1-beta(T-T0)]、psi=0、圧力非依存だが非定密度 | Bは慣性・輸送にrho0、密度変化は浮力だけ | 慣性・輸送・保存の係数差、非定常EOS再同期／閉領域質量に注意 |
| momentum | rho付き時間・移流、Paのp_rgh、偏差応力、-grad(p_rgh)-gh grad(rho) | Bは一定nu0、浮力だけbeta(T-T0) | 局所rhoの慣性、mu/rhoとgrad(div u)による速度差 |
| Boussinesq名称 | `incompressible=true`はEOSの圧力非依存、`isochoric=false` | 古典Boussinesq近似の全式同一性を意味しない | EOS名称だけでBと同じモデルと判定できない |
| thermophysical model | heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy、laminar Stokes/Fourier | Bは定物性T式を直接解く | energy/thermo/rhoのcouplingが追加される。Stokesはここでは応力モデル名 |
| transport | Cp=Cv=1000、mu一定、k=Cp mu/Pr一定。nu=mu/rho、alpha=k/(rho Cv) | Bはnu0/alpha0一定 | 収束時の局所Prは0.71でもnu/alphaは温度依存。反復中のsolver/thermo rhoを混同しない |
| energy equation | ddt(rho e)+div(rho u e)+ddt(rho K)+div(rho u K)+div(pu)=div(k grad T)+rho u・g | Bのrho0 cp DT/Dt=k laplacian(T)にはK/圧力/重力仕事がない | Nu、T、定常到達、energy balanceに差が出得る |
| pressure work | e branchの `div(phi,p/rho)` はpsi=0でも有効、dpdt noで消えない | Bの温度式にはない | 圧力基準や相殺の影響。enthalpyへの切替は別モデル変更 |
| kinetic energy transport | K=|u|²/2の時間・移流。steadyでも移流は残る | BのT式にはない | 仕事項との相殺を含めて評価する必要 |
| gravitational work | rho(U・g)、steadyでも残る | BのT式にはない | Gate Hでgを10倍すると個別仕事項が増す。相殺誤差が減る保証なし |
| temperature equation換算 | 質量/運動量式を使う連続体推論ではrho Cv DT/Dt=div(k grad T)-p div u-u・div(tau) | Bに後二項なし | 全差分がO(beta DeltaT)とは言えない。K/圧力/重力の個別大きさを足して「誤差」としない |
| p_rgh / pressure gauge | p_rgh=p-rho gh-pRef。constant/pRefとPIMPLE/pRefValueは別 | Bはkinematic圧力、rho重み付きenergyなし | Aのp→p+Cは-p div uを変え得る。圧力の単位・初期seedをBからコピーしない |
| transient density | continuityのrhoとEOS更新のrhoは反復途中で一致とは限らず、psi=0で圧力は密度を調整できない | 古典一定密度Bと異なる | OQ-07: closed-cavity総質量driftとEOS/solver rho整合をGate Jで確認 |

Aの監査PASSは**差を把握して追跡できる**という意味で、原論文式との同一性PASSではない。新しいgauge/energy-term研究は本phaseの必須caseに追加しない。

## 4. Current Route A evidence

### A-COND: PASS（minimal Gate A/C）

| 項目 | canonical evidence |
|---|---|
| purpose | Ra=0解析解でNuの符号・規格化、2経路、無流動、線形温度を校正 |
| mesh / Ra | 80×80×1、6400 cells、等間隔直交、empty、Mesh OK、g=0/Ra=0 |
| Gate A | minimal版・入力・mesh・OQ-02 PASS。cell/4wallのpressure relation、p_rgh=0確認。full matrix Aは別 |
| Gate C | PASS。両壁誤差≤0.001、2経路差≤0.001、無次元速度≤1e-6、温度誤差≤1e-4 |
| Nu | Nu0=1.000039392478、Nuhalf=0.999960632155、Nu_cavity=1、Nu1=1.000039404051 |
| independent paths | hot A1/A2差の最大相対差4.554e-13。physical wallHeatFluxも校正 |
| velocity / temperature | max(|u|)L/alpha0=0、max|theta-(1-X)|=6.3283355e-6 |
| convergence / exit | 3000反復、窓2801–3000、Nu legacy Rwin=4.14565e-5、e最終initial residual=2.70767e-8、normal_exit=true、fatal_or_nan=false |
| heat balance / status | epsilon_Q=1.1571714e-8。Gate C PASSを維持。formal steady matrix行ではない |

### A-SMOKE: PASS（minimal smoke、formal matrix acceptedではない）

| 項目 | canonical evidence |
|---|---|
| purpose | fluid/thermo/steady SIMPLE、自然対流方向、monitorと後処理の実装health |
| Ra / grid / exit | Ra_actual=1e4、Pr=0.71、40×40×1、3000反復、normal_exit=true、fatal_or_nan=false |
| Nu | Nu_cavity=2.259954629404、Nu0=2.257421422258、Nuhalf=2.258514696997、Nu1=2.257421471853 |
| Umax / Wmax | Umax=16.1213350963 at Z=0.8125、Wmax=19.5973334630 at X=0.112548828125 |
| local Nu | quartic max=3.5771345173 at Z=0.1396609745、min=0.5821556111 at Z=1。raw extremaは別保存 |
| convergence | 窓2801–3000、legacy Nu Rwin=0（出力精度内）、Umax=2.78517e-11、Wmax legacy V=1.94180e-11。最大最終initial residual=1.17105e-10 |
| conservation | epsilon_Q=2.19704e-8、section中央比最大偏差=5.67415e-4、native epsilon_m=2.83318e-11、reconstructed epsilon_v=4.3650864e-3 |
| paper diagnostic | Nu_cavity絶対相対差0.755891%、Umax 0.350%、Wmax 0.100%、位置絶対差0.0105/0.00645117。Nu0↔2.238、Nu_cavity/half↔2.243を分離 |
| current status | smoke PASSのみ。fine用epsilon_v閾値超過はcoarse diagnosticで、formal G FAILでもformal matrix PASSでもない |

旧「Nu hot=2.25742をpaper cavity=2.243と比較」は無効で、保存field再後処理によって訂正済み。A-SMOKE attempt1はpatch初期化不整合により `INVALIDATED_OQ02_PATCH_CHECK`、canonical resultは修正後attempt2。failed attemptやA-CONDのsampleType/postprocessing errorを合格resultと混ぜない。今回はfailed logs全文を読まず実装summary/manifestだけを参照した。

## 5. Route Bから再利用するもの／しないもの

**再利用:** canonical `reference/de_vahl_davis_table_v.csv`、X/Z・U/Wの無次元化、同名QoI、40/80/160とcoarse/medium/fine、Rwin最終200反復とscale=1、manifest/hash/provenance、4097点最終centreline/257点monitor区別、局所Nuのraw/5点quartic区別、図・表の構造、computed/accepted/diagnosticの分離。

**自動転用しない:** Bのaccepted status、B Gate Bの式同一性、B Gate G結果/暫定threshold研究、B residual floorの解釈、Bのphi単位・圧力単位、全Hard合格という主張。既存plot/report scriptsは概念とレイアウトを再利用するが、Aのfield/e/thermo/mass fluxに適合することを未来の契約で確認する。今回scriptは読込拡張・変更・生成しない。

B master CSVのaccepted YESの9行（Ra1e3–1e5）をaccepted comparison baselineとする。Ra1e6の3行は**computed／unaccepted diagnostic B baseline**と明記する。B-SMOKEがB正式coarseに再利用された履歴は、A-SMOKE昇格の根拠にならない。

B masterにはNu_half/Nu_1、全位置・局所Nu等の全比較列がない。このreviewでは値の出所をすべて照合済みとはしない。将来のcomparisonで既存canonical B出力を必要列だけread-onlyで取得し、B results/statusは変更しない。不足をゼロやPASSで補わない。

## 6. 12ケースの科学的必要性

| 問い | 推奨 |
|---|---|
| Q1: Aも全12必要か | **YES**。現行計画を維持。Hは別1case、Jは別study |
| Q2: A–B characterizationで全12の価値 | 4Raで伝導寄りから境界層の強い流れまで、3gridで見かけのモデル差と空間・sampling差を識別。高Raのみ／fineのみでは交絡が残る |
| Q3: 一部caseへ削減は妥当か | pilotや対象Raを限定した論旨には可。ただし全Ra評価／現行F/K完了の代替にしない。今は削減理由が科学的に不足 |
| Q4: 修論のminimum | **現行の4Ra全域のモデル差を説明する論旨では12がminimum**。狭い論旨なら事前に対象Raを限定して3grid/Ra＋Hは可能だが別研究計画。今回は採用しない |

Nu/U/Wのmodel gapがgrid差より小さく、p/GCIが未確定なら、符号やRa依存の観測は報告できても「grid-independent model errorを測定した」と主張しない。単なるtoken/計算量節約で比較を弱めない。

## 7. Gate A–K と適用時期

formal区分とworkflow policyを分離する。全表は `routeA_gate_plan.csv` / JSONにも保存。

| Gate | Route Aで必要／今すぐ | full matrix内 | coupling前へ延期 | 既存formal区分／今回のworkflow |
|---|---|---|---|---|
| A | YES／minimalを引用、全case再確認契約 | 各case版・input・Ra/Pr・mesh・OQ-02 | 不可 | Hard |
| B | YES／既存A audit PASSを引用 | auditしたmodel/solver一致のみ | 不可 | Hard、再source auditなし |
| C | YES／A-COND完了 | 同じ定義を使用 | 完了済み | Hard、再solver不要 |
| D | YES／DETAIL_UNRESOLVED解消 | 全12＋Hを個別判定 | 詳細は延期不可 | Hard。有限正常threshold FAILでbatch停止はしない |
| E | YES／Table V定義固定 | 全量報告、fineで既存目安照合 | Level1後へ不可 | A steadyはDiagnostic、JではHard |
| F | YES／scope policy固定 | Raごと3grid判定 | 追加320のみdefer可 | formal Hardを維持、Level1は限界付き非blocking |
| G | YES／operator/scope固定 | fine formal、全grid native診断 | 高度研究のみdefer可 | formal Hardを維持、Level1は限界付き非blocking。JのA GはHard |
| H | YES／計画のみ | matrix外の別1case | matrix後、coupling前必須 | 実施報告必須、Level2ではPASS Hard |
| I | YES／方法固定 | 各case局所量、fine場の診断 | Level1報告まで不可 | Diagnostic・報告必須 |
| J | YES／計画のみ | steady matrix外 | steady/H後、動く粒子前必須 | 下流Hard |
| K | YES／今からprovenance | 各case保護＋最終集約 | 不可 | Hard |

## 8. Gate D: 既知事項と不足

既存AC §6、design §10、implementation §6を優先する。

| 対象 | Aで固定できる既存事項 | 実行前に不足を閉じる項目 |
|---|---|---|
| velocity residual | 全active U成分のsolver-reported normalized **initial residual**。最終値1e-7以下目標 | linear final residualと混同しないreport/parser対応 |
| energy residual | 直接未知量はe。T equation residualを架空に作らない。e initial residual1e-7目標 | 複数solveがある場合の既存集約法を契約に明記 |
| pressure residual | Paのp_rgh initial residual1e-7目標 | B kinematic p/phiの判定をコピーしない |
| density / thermo | positive/finite rho、EOS/solver rho整合、T範囲、native mass診断 | 新しいrho residual閾値は作らない。非定常の整合はJ |
| QoI stationarity | 最終200反復以上、Nu_bar_0/Umax/WmaxのRwin≤5e-4、scale各1 | minimal記録の `Nu` / `Nu_legacy_wall_pair_monitor` と**正確なNu_bar_0 trace**の対応が未確定 |
| heat balance | 同じ窓のheat imbalanceが増加傾向にない | minimalのstart/end値だけでは窓全体の再現可能な傾向判定・出力丸め扱いを固定できない |
| exit / validity | normal End、input一致、NaN/Inf/fatal/divergenceなし | 上限到達を収束と扱わない |

**ROUTE_A_GATE_D_DETAIL_UNRESOLVED**。新thresholdを作らず、exact monitor definition、heat-trend evaluatorと既存数値精度の扱い、残差parser/aggregationを次タスクで事前固定する。baselineのsolver tolerance/relaxation/schemeは変更しない。Bで疑われたfloor機構をAへ自動移植しない。

反復上限もminimalの3000を全gridへ流用しない。B fineが18000–21000反復、Ra1e6が30000でもD FAILだった実績は**budget planningの参考**で、Aの収束保証ではない。全12のcase別上限・保存頻度を契約に固定する。未固定をJSONではnullとし、自動延長・retryは認めない。

## 9. E/F/Gの事前policy

**E:** A steadyではpractical comparison。既存1%（Nu_cavity/Umax/Wmax）、位置0.01を同条件で照合・報告するが、A steady characterizationにPASSを要求しない。JではAC §12がEの1%条件とGを要求するので、steadyのDiagnostic扱いをJへ機械的に持ち込まない。Nu0/halfのlike-for-like差も報告し、Nu1のpaper独立referenceを作らない。

**F: NON_BLOCKING_WITH_DOCUMENTED_LIMITATION（Level1 workflow）**

1. 各RaのNu_cavity/Umax/Wmax、fine–medium≤1%、Nu単調、p_obs/GCI（Fs=3、Nu≤1.5%、速度≤2%）を既存通り判定。
2. non-monotonic／p未定義・負・不合理ならFAILまたは上流D不合格によるNOT_EVALUATEDを保存し、p/GCIをnullにする。
3. 該当量の `needs_320=YES` を保存し**DEFER**。320²を生成・実行しない。
4. AC §8の320追加要件は免除しない。正式F完了を主張するなら追加評価が必要。Level1で主張する範囲を限定し、F FAILをfine解の大誤差と即断しない。
5. model differenceをdiscretization uncertaintyと分離できない量は観測差として報告。主張の核がgrid uncertainty保証ならdeferでは足りず別判断。

**G: NON_BLOCKING_WITH_DOCUMENTED_LIMITATION（正常有限のmatrix収集と限定Level1）**

- fine各Raでheat≤0.2%、section≤0.5%、epsilon_m≤1e-6、epsilon_v≤2e-3、theta/velocity symmetry≤0.2%を別componentとして判定。未証拠はUNKNOWN/NOT_EVALUATED、FAILと未評価を混同しない。
- Aのmassはnative corrected mass phi、volumeは既存 `fvc::div(U) Gauss linear` の再構成診断。historical design §13.2のphi/rhof案をcanonicalのdiv(U)へ黙って置き換える根拠にしない。
- native mass closure、physical wallHeatFlux、paper-definition section、U-based volume divergenceを別保存。native PASSでformal FAILを置換しない。
- FAIL時はformal status、native diagnostics、限定的原因候補（model／discretization／iteration／postprocessing）を記録して次caseへ。新continuity threshold研究、microcase、無限tolerance探索へ移行しない。
- **この非blockingはcouplingの保存要件免除ではない。** native質量/energyの異常・未確認はtransient/coupling-readyのblocker。J endpointには既存A G条件PASSが必要。
- 有限のnormal runでG FAILだけならmatrixは続ける。NaN/fatal/divergence/input/provenance異常はSTOP。

現行formal A characterizationはF/G PASSが必要なので、workflow Level1を達成しても `ROUTE_A_CHARACTERIZED` を付与しない。

## 10. Gate H: Route Aのmodel-characterization

Ra=1e6、fine160²のmatrix baseline beta DeltaT=1e-3に対し、感度beta DeltaT=1e-4、**betaを1/10、gを10倍**。Ra/Pr、DeltaT、他物性、mesh、scheme、solver設定を保持する。g beta一定と参照nu0/alpha0からのRa再計算をAで確認する。

- baselineは正式予定 `A-Ra1e6-fine`、smokeは使わない。比較可能なbaselineがない場合、Hを自動実行／PASS認定せず判断する。
- 追加は感度1case。Nu_cavity/Umax/Wmaxのbaseline比絶対差各≤0.2%、epsilon_vは低下または非悪化。両条件のmass/heat/section診断も保存。
- **Level1には実施・報告が必須、0.2%PASSは必須でない。Level2/3にはH PASSが必須。**
- AがRa/Prだけでほぼ決まるか、beta DeltaTやgの個別値に感度が残るかを評価する二点試験。
- H PASSでもA=Bや全energy差が消える証明ではない。監査の固定Ra解析では静水圧膨張仕事の尺度が小パラメータ低下で一定となる成分がある。
- energy項分解/gauge/extra beta点は未承認の追加study。H FAILで自動追加しない。

## 11. A–B comparison contract

非零Bのscalarは D_AB(Q)=|Q_A-Q_B|/|Q_B|。位置は |s_A-s_B| を[0,1]座標で報告する。signed differenceは方向説明用に別欄。B≈0には相対差を適用せずnull/ABSOLUTE_ONLYとし、必要なscaleは実行前に固定する。新しいA–B Hard thresholdは設定しない。

| 比較群 | 固定する量・方法 |
|---|---|
| global Nu | Nu_bar_cavity（cell-volume primary）、Nu_bar_0、Nu_bar_half、Nu_bar_1。全face-plane台形補助値とmethod差は別欄 |
| velocity | Umax on X=0.5とZ位置、Wmax on Z=0.5とX位置。線形補間4097点、no-slip端点。monitor257点をfinal値に代用しない |
| local Nu | hot max/min＋Z、rawと固定5点quartic benchmark/端点外挿を分離 |
| heat | physical hot/cold heat imbalance、paper-definition section conservationを別欄 |
| continuity | native A kg/s mass phiとB m3/s volume phi、再構成Uのdivergenceを区別し、正しい規格化で比較 |
| symmetry | theta / velocityの180°写像L2。既存normalizationが同一定義か契約で確認 |
| provenance | 同Ra_actual/grid/無次元化/QoI/sampling/postprocessing、method_version/field hash/時刻 |

共通のprimary cavity Nuはcell-volume U theta＋固定壁伝導積分1なので同じcontinuum定義で比較できる。一方、**section Aは再構成U_f、Bはnative pressure-corrected volume phi**を使用する。A mass phiをvolume phiとして使わない。同じ名前だけで離散演算子同一と主張しない。

sectionのnative値は各routeの保存診断として保持する。厳密な同一演算子でA–B差を解釈したい場合、将来別欄で同じ再構成operatorを両保存fieldに適用し、formal/native列は保持する。今回は再後処理しない。方法差が未統一なら `OPERATOR_DIFFERENT` と明記し、モデル差だけに帰属させない。

## 12. 実行順序・STOP・結果保護

順序: **Ra1e3 trio → Ra1e4 trio → Ra1e5 trio → Ra1e6 trio**。各trioはcoarse→medium→fineで逐次、各caseのA/D/K/native診断を即時保存。trio終端のE/F/G reviewは定型の記録と分類だけとし、研究拡張を挟まない。

最初のlow-Ra trioは安価な入力からfineの生成／初期化／monitor／出力経路まで確認でき、B accepted比較もある。既存Ra1e4 smokeを追加pilot扱いで再実行せず、A正式coarseは別primary IDで保護して計算する。high-Raを最後に置くのは、既知のB収束難が環境・実装問題と混ざるのを避けるため。high-Ra-only早期pilotや全12parallel batchは採用しない。

並列solverは**1**。同じcaseの同時書込、集約manifest競合、複数fatalの発見遅れ、資源競合があるため。first trioの後も今回の計画は逐次運用を推奨する。

| STOP（batchを止める） | STOPしない（有限正常runのcase結果を保存し次へ） |
|---|---|
| environment/build/distribution mismatch、input/Ra/Pr/BC/hash mismatch | Gate D residual/Rwin/heat-trend閾値FAIL。ただし未収束行をacceptedとしない |
| wrong solver/physics、mesh error、初期化/OQ-02不整合 | A steadyのpaper mismatch |
| NaN/Inf、FATAL、solver divergence | F non-monotonic / undefined p/GCI |
| evidence破損／出所・定義不明、未固定実行契約 | G formal diagnostic issue |

divergenceはsolverの発散通知、有限性・許容状態の喪失等とする。finite stationary residual plateauだけをdivergenceと呼ばない。疑わしい状態を「threshold FAILだから継続」で押し切らず分類不能ならSTOPする。

- primary IDはJSONの12行。既存A-COND/A-SMOKEを上書きしない。
- 開始前input/mesh hashes、正常／異常exit、caseごとのfield/log/metrics/hashを保存してからaggregate。
- batch停止時も完了caseと途中caseを保持する。途中resultはPARTIAL/STOPPED、完了resultを巻き戻さない。
- primary attemptは1/case、計画外restart/retry/iteration延長なし。上限終了でD未達ならcomputed/unacceptedとして保存。
- numerical設定を結果に合わせて変えない。formal結果保存 → failure category → user decision → 別diagnostic task。許可後も新IDと一要因変更。Gate閾値変更やaccepted status昇格を自動化しない。

## 13. Completion levelsと粒子連成前の条件

**現在はいずれもNOT_ACHIEVED。** 3ラベルは提案したworkflow milestoneであり、現行formal statusと独立に保存する。

| Level | 必須条件 | 許容する限界／blocker |
|---|---|---|
| 1: ROUTE_A_STEADY_CHARACTERIZED | A/B/C、12case実施・各D分類、定常として使う主量の既存Rwin/熱傾向条件、3比較、F/Gの判定・限界、H実施報告、I/K | steady E/H数値不一致とF/G formal FAILは開示して非blocking。D residualだけのFAILはA自身の定常証拠と限定的説明があれば診断行として使用可、acceptedへ昇格不可 |
| 2: ROUTE_A_TRANSIENT_READY | Level1、対象Ra1e6 fineの使用可能なfluid-only steady baseline、H PASS、Gate J全数値項目PASS、fluid-only質量/energy、K | H/J FAILはHard blocker。F不足を許容するならgrid保証の主張を限定して別判断。Jで要求するA G PASSは免除しない |
| 3: COUPLING_READY | Level2＋実際の連成予定条件と一致するfluid-only baseline、dt sensitivity、質量/energy証拠、連成研究の主張を損なわない限界整理 | 今回は流体側必要条件のみ。粒子solverの正しさ／選定／連成設計は未評価 |

Level1は「全12を走らせた」だけでは足りない。nonfinite/誤入力、定義不明、非定常行を定常claimに使用、対象条件に使用可能なsteady証拠がない状態では到達ラベルを付与しない。主量非定常や熱収支増加が残る条件はsteady claimから除外し、全Ra steady characterizationを完了したとは言わない。

**正式statusの条件は不変:**

- `ROUTE_A_CHARACTERIZED` = B core PASS ∧ AのA/B/C/D/F/G/K PASS ∧3比較報告∧H実施報告。
- `DOWNSTREAM_TRANSIENT_READY` = 上記 ∧H PASS∧J PASS。
- 既存B core未付与のため、作業ラベルLevel1/2を正式statusへ自動変換しない。
- AC §12はJをB Verification/A formal characterization/H PASS後と規定する。限界付きworkflowでJへ進むなら、その**実行順序の例外はユーザーが明示判断**し、formal前提が未達であることを保存する。J数値要件・Gate閾値の免除ではない。

| coupling前の問い | 回答 |
|---|---|
| Q1: full steady12が必要か | 現行の全4Ra characterization計画ではYES。限定Raだけの連成研究なら縮小可能だが、今は別計画へ変更しない |
| Q2: H必要か | YES。実施・報告はLevel1、PASSはLevel2/3 |
| Q3: J必要か | YES。粒子が動けば非定常流体になる。steady solver evidenceは時間精度を保証しない |
| Q4: F/G未解決で進めるか | Fの非漸近性／再構成G等の限界を保持し、モデル差・force/heatの精度claimを限定してLevel1まで進める。formal readyは不可。JのA Gやnative質量/energy異常・不明はcouplingのblocker |
| Q5: 最小fluid-only evidence | 12steady評価＋H PASS、使用可能な対象baseline、J backward/Co系列差/定常到達/原論文比較/G、closed-cavity全質量とEOS整合、energy storage/work/壁熱の整合、全provenance |

## 14. Gate JとLevel2の終了条件

別taskでv13 `fluid` のtransient algorithmを固定する。既存監査ではPIMPLE辞書でouter=1はPISO、複数outerはPIMPLE。今回outer/corrector設定を選定・変更しない。

- Ra=1e6、fine160²、静止U=0／一様T0、監査済みpressure/rho初期関係から開始。
- 二次精度backward。初回履歴不足と可変dtを記録。
- Co_max目標0.5/0.25の2系列。最終Nu_cavity/Umax/Wmax差各≤0.5%。
- 超過なら既存Jの条件付きCo0.125を追加する計画。別の実行指示で事前登録し、最fine2系列で判定。
- 原論文1%の実用比較、ACの参照位置条件、A G保存基準、無次元時間履歴の定常到達。初期過渡平均で未収束を隠さない。
- steady baselineにも同一定義で照合する。新しいsteady–transient Hard閾値は作らない。
- 過渡massはddt(rho)+div(phi)、総質量履歴、solver/EOS rho再同期を確認。div(phi)単独や定常の小さいepsilon_mを過渡保存の証明にしない。
- energyは壁熱だけでなく蓄積・監査した仕事項を含める。定常のhot=coldを過渡全体に適用しない。
- OQ-07／過渡mass-energyの評価法・許容値が既存仕様だけで足りなければUNKNOWNとして、J実行前の別契約で物理・数値根拠を固定する。新thresholdを今回作らない。

## 15. Priority・scope boundary

| 優先度 | 対象 |
|---|---|
| P0 必須、今すぐ | D/monitor/熱傾向/上限/出力/operator契約、workflow方針確認。契約後の12steadyをtrio単位、各A/D/K・保存診断 |
| P1 必須、matrix後 | D/E/F/G/I/K集約、3比較、Hの1感度caseと報告、Level1 closure |
| P2 coupling前 | H PASS、J2系列（条件付き第3）、fluid-only transient mass/energyとdt、formal前提とworkflow例外の判断 |
| P3 optional/deferred | 320²、高度G研究、追加tolerance/relaxation/gauge/energy-term study |

扱わない: Project Chrono実装、CFDEM比較、particle drag、非球形粒子、deformable leaf、FSI、contact、tea-leaf geometry。Level1終了までこれらへ広げない。その後も本planは選定・設計の依頼ではない。

## 16. Exact roadmap

| phase | objective | solver runs | Gates | completion condition | relative cost |
|---|---|---|---|---|---|
| A0 already completed | audit結論＋minimal単体/smoke | historical A-COND/A-SMOKE、今回0 | minimal A/B/C、smoke D | minimal PASS（formal matrixを代替しない） | LOW |
| A1 next | 正式実行・判定契約を固定 | 0 | A/B、D detail、K、G/operator定義 | D READY YES、case別上限/monitor/trend/出力固定、workflow判断。solver実行なし | LOW |
| A2 | 4Ra×3grid steady評価 | 12、最初Ra1e3 trio、逐次4batch | A/D/E diagnostic/F/G/I/K | 全12保護、formal FAIL保持、3比較と限界報告 | HIGH |
| A3 | H感度とLevel1 closure | 感度1、baselineはA2 | A/D/H/K | H実施報告、Level1条件。H FAILで自動拡張しない | HIGH |
| A4 | transient verificationとfluid-side coupling prerequisites | 2系列、条件付き1は別指示 | H PASS/J/A G/K | Level2、その後Level3流体側条件、formal前提は別確認 | HIGH |

steady/Hは**13 primary runs**の計画で、A0を再実行しない。J最小2、必要条件付き1はsteady matrixに含めない。時間予測はしない。A3の160²/HとA4 transientは反復・物理時間依存が不明なのでHIGH。

## 17. 次のCodexタスクは1つだけ

**NEXT_SINGLE_TASK = FREEZE_ROUTE_A_EXECUTION_CONTRACT**

boundedな既存A monitor/implementation/result定義を確認し、次を同じ3 review文書に固定する。solver/mesh/case/script生成は行わない。

1. exact Nu_bar_0 traceとlegacy Nu/wall-pair、257/4097 samplingの対応。
2. heat-trendの窓全体の決定的評価と精度の扱い、U/e/p_rgh residual集約。thresholdは変更しない。
3. 12caseの反復上限・出力頻度・失敗分類・input/result protection。
4. A G/symmetry normalization、A–Bの定義一致／operator差／B既存出力列の取得先。

完了条件はD READY YES＋実行契約固定。既存証拠で決定できない項目は明確なmissing detailを残し、solverへ自動移行しない。最初の**後続solver実行単位**はRa1e3 trioのみで、いきなり12batchを許可しない。

推奨モデル: **gpt-6.1-sol / high**。boundedな契約整理に対する今回の判断で、repo上のモデル性能測定ではない。公式[Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model)でGPT-6.1 Solの複雑な実装用途とhighのサポートを確認した。アカウントの選択可否はこのreviewでは検証していない。

`USER_DECISION_REQUIRED=YES`は限界付きworkflowの採用と将来のsolver/J実行判断についてであり、このreview作成の追加承認は不要。formal criteria変更を求めていない。

## 18. Required final status

```text
ROUTE_A_PREFLIGHT_REVIEW = COMPLETE
A_COND_STATUS = PASS
A_SMOKE_STATUS = PASS
ROUTE_A_FULL_MATRIX_REQUIRED = YES
ROUTE_A_FULL_MATRIX_CASE_COUNT = 12
ROUTE_A_STEADY_CHARACTERIZATION_REQUIRED = YES
GATE_H_REQUIRED = YES
GATE_J_REQUIRED_BEFORE_PARTICLE_COUPLING = YES
ROUTE_A_GATE_D_READY = DETAIL_UNRESOLVED
ROUTE_A_GATE_F_POLICY = NON_BLOCKING_WITH_DOCUMENTED_LIMITATION
ROUTE_A_GATE_G_POLICY = NON_BLOCKING_WITH_DOCUMENTED_LIMITATION
AUTOMATIC_320_RUN_ALLOWED = NO
AUTOMATIC_SOLVER_TUNING_ALLOWED = NO
ROUTE_B_GATE_G_INVESTIGATION_REOPENED = NO
SOLVER_EXECUTED = NO
CASE_CREATED = NO
FORMAL_CRITERIA_CHANGED = NO
PARTICLE_COUPLING_WORK_STARTED = NO
ROUTE_A_STEADY_COMPLETION_TARGET = A/B/C; 12 steady cases evaluated; steady health; D/F/G limitations disclosed; 3 comparisons; H reported; I/K complete (workflow milestone only)
ROUTE_A_TRANSIENT_COMPLETION_TARGET = Level1 + usable Ra1e6 fine baseline + H PASS + J PASS + fluid-only mass/energy evidence; formal prerequisites remain separate
NEXT_SINGLE_TASK = FREEZE_ROUTE_A_EXECUTION_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / high
USER_DECISION_REQUIRED = YES
```

COMPLETEはreview成果物の完了を意味し、実行開始可能・steady/transient readyを意味しない。既存solver case、B results、規範、閾値、numerical settings、accepted status、source codeは変更せず、git add/commit/pushなし。
