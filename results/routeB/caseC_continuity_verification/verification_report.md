# Route B Case C Continuity Verification

## 1. Purpose

2026-10-04。Route B Candidate Bのepsilon_phiについて、operator、v6 pressure残差との対応、serialization/restart、local conservationを独立検証した。**operator PASS、stock/audit同値、referenceを考慮したmappingは検証できたが、tolerance単独の直接変換は不可。numerical floorはPARTIAL、tau_phiはUNRESOLVED、Candidate BはPROVISIONAL。**

## 2. Independence from benchmark results

正式matrixのcase/field/metricsを読み込まず、正式Ra=1e3/1e4/1e5/1e6、320²、Route Aのsolverを実行していない。指定された既存reviewの背景値は導出に使用せず、post-hoc比較も実施しない。reference CSV・paper比較なし。現行Gate G FAILと新案NOT_EVALUATEDを保持する。

コード・microcase・binaryはverification/routeB_continuity内、summaryはresults/routeB/caseC_continuity_verification内に限定。raw field/log/build objectはlocal .gitignoreで除外し、再現用設定・sourceとcompact CSV/hashを保存する。

## 3. epsilon_phi operator verification

q_i=sum_f s_if phi_f、d_i=q_i/Vi、M=sum_i|q_i|/Vtotal、epsilon_phi=(L/Up)M。phi/qはm³/s、divergenceはs⁻¹。actual production foam_fields parserとanalyze_case.pyの**continuity_metrics関数そのもの**を使った。ASTでその関数だけ読み込み、production mainやpaper reference処理を実行しない。owner/neighbour、4物理壁、empty front/back、uniform volumeを検証した。

解析qとの差はcellごとの32-operation unit-roundoff modelと実測ASCII roundingのincidence伝播で評価し、20条件がPASS。これはimplementation testの誤差budgetであって物理acceptance thresholdではない。最初の完全一致assertでは検証側の1/n²とproductionの(1/n)(1/n)の体積計算順が異なり、20²でV差4.34e-19が出た。検証側を修正して完全一致を確認し、production bugの証拠はなかった。

## 4. Synthetic exact-flux tests

20²/40²/80²/160²。L=depth=1m、Up=1m/sをprescribed cell U=(1,0,0)から与え、phiとは独立のnormalization入力とした。合成場はhydrodynamic solutionではない。psi=sin²(pi x)sin²(2pi y)、境界vertex psi=0。vertical face fluxはy方向psi差、horizontal fluxは負のx方向psi差で、正確算術ではtelescopingする。

| grid | ASCII16 mean | ASCII16 max | ASCII6 mean |
| --- | --- | --- | --- |
| 20² | 7.96065e-15 | 4.996e-14 | 3.856e-05 |
| 40² | 1.57633e-14 | 1.83187e-13 | 8.4704e-05 |
| 80² | 1.74995e-14 | 1.33227e-13 | 0.000175399 |
| 160² | 5.60093e-14 | 3.77476e-13 | 0.000545935 |


表のdivergence単位はs⁻¹。L/Up=1sなのでepsilon値も同じ数値。in-memory値・P95/P99・globalはserialization CSVのmemory_*列へ保存。ASCII16でmean 7.96065e-15–5.60093e-14、max 4.996e-14–3.77476e-13という、この構成の丸め水準を測定した。

single internal faceにdelta_phi=1e-6/1e-8/1e-9を注入した試験はzero baselineを用い、隣接cellの±delta、sum|q|=2|delta|、mean=2|delta|/Vtotal、max=|delta|/Vi、global=0に一致。絶対・相対誤差をoperator CSVへ記録した。1つのhotWall faceへの1e-8漏れはsum q=net boundary flux=1e-8m³/sとして検出された。empty patchは0-length scalar listで読み飛ばすことも確認した。

## 5. Serialization and parser effects

同一合成phiのin-memory float64、ASCII相当precision16/6、actual parser read-backを比較。parser値はPythonのserialized significant-digit conversionと完全一致し、parser独自の追加誤差を認めなかった。precision6のexact-flux meanは3.856e-05–0.000545935s⁻¹へ増大した。precision6は感度診断だけでありproduction設定を変更しない。

実microcaseでも各iterationのaudit in-memory metricと実OpenFOAM ASCII16 field read-backを比較した。sweep 90 solvesの最大absolute mean差は7.53713e-17s⁻¹、max差は2.99853e-15s⁻¹、epsilon mean差は1.84974e-16。CSVへP99/globalの差も収録。faceのsignificant-digit quantumを両隣cellへ伝播した保守的IO budget内であることを確認した。微小なuniform mesh volume計算差・加算順も差の一部であり、全差をserializationだけと断定しない。

## 6. OpenFOAM microcase

Foundation v6、buoyantBoussinesqSimpleFoam、laminar、closed cavity、Pr=0.71、**Ra_test=30000**。L=0.01m、depth=0.001m、1 depth cell、front/back empty。hot/cold=301/300K、TRef=300.5K、g=(0,-9.81,0)m/s²、nu=1e-6m²/s、alpha=nu/Pr、beta=Ra_test nu²/(Pr g L³)。beta deltaTは約0.00431。開始U=0、T=300.5K。gravityによるnonzero convectionを得た。

20²/40²/80²、p_rgh PCG/DICのtolerance=1e-6/1e-8/1e-10、relTol=0、maxIter=10000。他の設定・初期条件・relaxationは同一。10 SIMPLE iterationsだけを実行し、**steady convergenceを主張しない**。初期各pressure solveを調べる目的に限定する。stock/audit代表、restart、reference cornerの補助条件も20²で実施した。

## 7. Audit solver verification

通常のstock logにはNp、true residual、local percentile、physical reference residualがないため、v6 solver sourceを専用auditSolverへコピーし、別名buoyantBoussinesqSimpleFoamContinuityAuditとしてwmakeした。installation source/binaryは変更しない。

追加はコピーしたmatrixのboundary/reference assembly、installed PCG::normFactor呼び出し、solve後のb−Ap再評価、phiのincidenceとmetric出力だけ。PCG内部や支配方程式・discretization・relaxationは変更していない。solve return valueを保存し、p relaxation前のtrue residualを取得する。診断用PCG objectはnormFactorを呼ぶだけでsolveしない。

20²、tolerance=1e-8、10 iterationsでstockとauditをserial実行し、**U/T/p_rgh/phiの最終fieldファイル全体がSHA-256一致**。patch値もhash対象である。internal差も全て0。証拠hashはsummaryとartifact_hashesに保存。代表条件以外の同値性を実証したとはしない。

## 8. Pressure residual to flux-imbalance mapping

physical pressure matrix（reference追加前）A0/b0、referenceとBC込みAs/bsをコピーし、同じunrelaxed p*についてr0=b0−A0p*とrtrue=bs−As p*を再計算した。actual corrected phiからqを別に集計する。

$$q\simeq r_0,\quad R_{true}=\|r_{true}\|_1/N_p,\quad K_p=LN_p/(U_pV_\Omega).$$

Npはinstalled PCGのactual normFactorで取得。全sweepのKpは3.13214–24.6799。q−r0のL1評価差は2.34499e-23–2.95761e-19m³/sであり、matrix/face評価のcancellation・丸めが残る。したがってepsilon_phi=toleranceという直接関係は成立しない。

epsilon/(Kp R_recursive)は0.992383–1.11076、true residualでのratioは0.992396–1.00852。ratioが1に近いことだけで無条件同一視しない。

reference-aware予測は

$$\epsilon_{pred}=\frac L{U_pV_\Omega}\left(\sum_{i\ne j}|r_{true,i}|+|q_j|\right).$$

そのepsilonとの最大absolute差は3.3551e-12。reference行のalgebraic residualとq_jを別々に記録し、非reference行・net boundary Bを使ったsum|q|≤2 sum_(i≠j)|rtrue_i|+|B|という前回の条件付き上界を、実測operator discrepancyとtelescoping roundoffを加えて全rowで確認した。これは今回の有限suiteでの量的検証であり、全matrixへの認証上界ではない。別のreference corner runでも関係を確認し、Np・reference寄与が変わることを記録した。

## 9. True vs recursive residual

reported finalはrecursive residual norm、trueはsolve直後にassembled matrixのAmulで再評価した値。L1 norm差の最大は3.52302e-19m³/s、true L1に対する差の最大比は0.100215。80²、1e-10、iteration10ではR_recursive=7.98321e-11に対しR_true=8.87236e-11。

取得したのは**L1 normの差**であり、recursive residual vectorそのものは取得していない。abs(||rtrue||₁−||rrec||₁)と||rtrue−rrec||₁は同じではなく、前者は後者の下界にしかならない。再計算true residual自体にもcancellation/roundingがあり、全差をPCG再帰driftだけに帰属できない。前reviewのE_recの認証上界を今回取得したとはしない。

## 10. Grid dependence

以下は**iteration10のin-memory audit値**。P99はs⁻¹、epsilonは無次元。全iteration1–10はsolver_mapping.csvにある。

| n | tolerance | Kp | R_recursive | R_true | epsilon_phi_mean | epsilon_phi_max | P99_abs_div_phi | ratio_recursive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 1e-08 | 3.9241 | 7.32995e-09 | 7.32985e-09 | 2.85444e-08 | 2.16741e-07 | 4.90904e-08 | 0.992383 |
| 20 | 1e-06 | 3.92382 | 9.62371e-07 | 9.62371e-07 | 3.77831e-06 | 1.62696e-05 | 5.71467e-06 | 1.00057 |
| 20 | 1e-10 | 3.92411 | 8.34553e-11 | 8.34012e-11 | 3.29055e-10 | 1.59802e-09 | 4.60157e-10 | 1.00479 |
| 40 | 1e-06 | 6.47159 | 5.46515e-07 | 5.46514e-07 | 3.53897e-06 | 2.83415e-05 | 1.76986e-06 | 1.00061 |
| 40 | 1e-08 | 6.47144 | 9.35773e-09 | 9.35776e-09 | 6.05621e-08 | 3.85392e-07 | 3.07587e-08 | 1.00007 |
| 40 | 1e-10 | 6.47144 | 9.13468e-11 | 9.19918e-11 | 5.98856e-10 | 5.9206e-09 | 2.66432e-10 | 1.01304 |
| 80 | 1e-06 | 11.891 | 9.83203e-07 | 9.83203e-07 | 1.1766e-05 | 0.000493641 | 1.6817e-06 | 1.00639 |
| 80 | 1e-08 | 11.8902 | 9.28531e-09 | 9.28524e-09 | 1.10435e-07 | 1.07688e-06 | 1.74657e-08 | 1.00027 |
| 80 | 1e-10 | 11.8902 | 7.98321e-11 | 8.87236e-11 | 1.05436e-09 | 8.91093e-09 | 1.44999e-10 | 1.11076 |


同じ1e-8でKpは20²/40²/80²で約3.924/6.471/11.890、epsilon meanは約2.854e-8/6.056e-8/1.104e-7。格子細分化で同じnormalized pressure toleranceが同じepsilonを与えるわけではない。pressure operatorとstate、Upのgrid依存を含む。field write/read差もgrid別にsummaryへ保存した。

## 11. Solver-tolerance dependence

全pressure solveはrelTol=0でabsolute toleranceを満たした。各gridでtoleranceを1e-6→1e-8→1e-10にするとepsilonは大きく低下するが、ちょうど100倍則ではない。最終Rのovershoot、linear iteration数、Kp、reference、true残差評価差が影響する。toleranceの違いが後続SIMPLE stateにも影響するので、全run間の比較は完全なfrozen-matrix sweepではない。

1e-10までではplateauを確立していない。tight caseでのtrue/recursive差やoutput/evaluation差は検出できたが、それから下限floorを外挿しない。pressure tolerance自体をtau_phi候補として使用しない。

## 12. Restart/write precision dependence

production templateで確認したASCII writePrecision16を独立caseにも使った。20²、1e-8について10 continuousと5→write/read restart→5を比較。

| quantity | max_absolute_difference | relative_max_difference |
| --- | --- | --- |
| U | 9.26295e-12 | 2.27693e-09 |
| T | 4.75097e-10 | 1.57862e-12 |
| p_rgh | 3.21659e-13 | 6.22657e-12 |
| phi | 1.20178e-18 | 5.90514e-10 |
| epsilon_phi_mean | 1.64306e-12 | 5.75617e-05 |
| epsilon_phi_max | 2.51523e-11 | 0.000116048 |
| P99_abs_div_phi | 1.35393e-11 | 0.000275804 |
| R_recursive | 2.83362e-17 | 3.86581e-09 |
| R_true | 3.92272e-13 | 5.35171e-05 |
| Np | 1.29244e-16 | 8.08309e-10 |
| Up | 1.04976e-12 | 2.57629e-10 |


restartはbitwise同一ではないが、差は表の範囲で定量化された。final U/phiに加えT/p_rgh、epsilon mean/max、P99、R_recursive/R_true/Np/Upを記録した。restartはserializationだけでなく、rhok・pressureゲージ・BC・iteration historyの再初期化を含むため、この差を純粋なIO floorと同一視しない。restart結果はacceptance budgetではない。

## 13. Mean vs local conservation

固定delta_phi=1e-8のinternal defectではmean=2e-8s⁻¹が格子によらず同じだが、maxはVi⁻¹で増大する。20²/40²/80²/160²のmax/meanは200/800/3200/12800。2cellだけの異常なのでP99は全て0。signed globalも0。一方boundary漏れはsigned globalで検出される。

meanは全領域L1 budget、maxは孤立欠陥、percentileは分布、signed globalはboundary整合を測る。各microcase/iterationのmean/max/P95/P99、無次元値、boundary net、max cell ID/coordinateをlocal_metrics.csvに保存。P99をmax guardの代用にはできない。

## 14. Numerical floor

**PARTIAL。普遍的floorのmean/max値はnull。** 合成fieldのscoped roundoffレベル、ASCII16/6の感度、実phi出力のmetric差、matrix/face算術評価差、restart差を量的に得た。ただし、合成fieldのscale・telescoping構造はpressure-corrected phiとは異なる。microcaseも10 iterations、最小tolerance1e-10だけでfloor plateauを示していない。

machine epsilon=2.220446049250313e-16をphi floorへ直結しない。serial DP ASCII16という範囲に限定し、conditioning、parallel、binary、他mesh family、別Ra/Up scaleへの普遍化をしない。

## 15. Acceptance-budget implications

A numerical measurement floor、B linear solver convergence capability、C research acceptance budgetを区別する。今回Aの一部とBを調べ、qとpressure residualのreference-aware関係を具体化した。しかしCの許容保存誤差を支配方程式だけから唯一の数値として決められず、目的量への許容影響も事前指定されていない。

追加すべき根拠は、mean/local保存欠陥が許容目的量精度に与える影響と、その研究上の許容量の事前定義。数値floorの安全係数だけでHard閾値を選ばない。正式結果の値に合わせてbudgetを逆算しない。

## 16. tau_phi assessment

**tau_phi=null、UNRESOLVED。Candidate BはPROVISIONAL。** Operator実装と条件付きmappingの根拠は強化されたが、共通fixed tauやsolver-linked数値を正式採用できる状態ではない。推奨は独立error budgetに今回のreference-aware mappingとoperator/IO監査を組み合わせる方式。benchmark再計算は不要であり、既存結果の再判定も行っていない。

## 17. Local-guard assessment

孤立cellの品質まで保証したいならmax guardの研究が必要そうであり、L2（mean+max）を優先検討する根拠は得た。L3（percentile）だけでは今回の2cell欠陥を検出できない。ただし**local guardをHardへ採用する判断は今回行わない**。その数値budgetは未定のためrecommended_local_guard=UNRESOLVED、research_preference=MEAN_PLUS_MAX。L1もmean threshold未定なので正式採用しない。

## 18. Limitations

10 iterationsはsteady solutionではない。tolerance間でstateが変わる。recursive vectorは未取得。true residual計算にも丸めがある。restartはIOと再初期化が混在。stock同値性は代表1条件だけ。uniform Cartesian、serial DP、ASCII16、指定scaleの検証であり、binary/parallelや全Raを認証していない。machine epsilonや合成floorはacceptance値ではない。

sourceの主根拠はlocal v6 PCG.C:93–110/172–180、lduMatrixSolver.C:174–196、fvScalarMatrix.C:154–169、fvMatrix.C:507–518/1458–1466、pEqn.H:29–46、continuityErrs.H:33–40、fvcSurfaceIntegrate.C:51–75。absolute source path/lineとコピー元hashはsource_audit.jsonに収録する。公式sourceは[PCG](https://cpp.openfoam.org/v6/PCG_8C_source.html)、[normalization](https://cpp.openfoam.org/v6/lduMatrixSolver_8C_source.html)（前reviewで確認、今回の根拠は実installed source）。長いsource引用は行わない。

## 19. Required user decision

次は結果非依存のmean/local acceptance budgetと適用範囲を定めること。孤立欠陥をHardで抑える目的があるかを確認し、max guardのbudget研究を進めるか判断する。認証されたsolver floorが必要なら、frozen-stateでのよりtightなsolve、残差vector取得、parallel/binary等を別途scopeにする。現行Gate G・production code・reference・正式CSV/status/fieldは変更していない。開始時のRoute A untracked 2directoryは未変更。

```text
CASE_C_OPERATOR_VERIFICATION = PASS
AUDIT_SOLVER_USED = YES
AUDIT_SOLVER_EQUIVALENT_TO_STOCK = YES
RESIDUAL_TO_FLUX_MAPPING_VALIDATED = PARTIAL
NUMERICAL_FLOOR_QUANTIFIED = PARTIAL
TAU_PHI = UNRESOLVED
TAU_PHI_STATUS = UNRESOLVED
RECOMMENDED_LOCAL_GUARD = UNRESOLVED
CANDIDATE_B_STATUS = PROVISIONAL
BENCHMARK_RESULTS_USED_FOR_THRESHOLD_DERIVATION = NO
BENCHMARK_SOLVER_RERUN_REQUIRED = NO
GATE_G_CRITERIA_MODIFIED = NO
SPEC_CHANGE_EXECUTED = NO
USER_DECISION_REQUIRED = YES
```
