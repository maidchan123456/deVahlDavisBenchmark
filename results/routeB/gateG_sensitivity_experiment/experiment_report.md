# Route B Gate G Independent QoI Sensitivity Experiment

## 1. Purpose

独立continuity defect → QoI responseのcalibration evidenceを取得する。研究acceptance quotaやtau_meanは決めない。 **STOP: STOP: maximum iteration without steady solution: baseline_n20。以後solver実行を停止し、partial evidenceを保存した。**

## 2. Independence from formal benchmark

formal Ra=1e3/1e4/1e5/1e6 field/log/Gate E/F/conservation値、Route A、原論文を使用していない。全solver/mesh callをsensitivity/runsとRa_test=30000/grid20/40/80のallowlistで検証。production/stock installation/仕様を変更していない。

## 3. Preregistration

solver実行前にv1 Markdown/JSONを固定。JSON SHA256: `567af0e99595d20cb6aeecc99788c4d4b7d36e2f5f33bec05dc4093bde07d0e3`。実行中guardでhashを再確認。原登録は編集していない。数値停止条件は研究quotaではない。

## 4. Microcase

Ra_test=30000、Pr=.71、L=.01m、depth=.001m、Th/Tc/TRef=301/300/300.5K、nu=1e-6、alpha=nu/Pr。betaはscriptでRa*nu*alpha/(g*DeltaT*L³)から計算し各run manifestに保存: 0.004307188697936856 1/K。four walls=noSlip/impermeable、left hot/right cold、top/bottom adiabatic、front/back empty、laminar serial DP ASCII16。20/40=exploration、80=holdout。

## 5. Baseline

各gridのzero-source p_rgh tolerance1e-10/relTol0をhighest-fidelity tested numerical baseline候補とする。全primary比較はsame-grid。truth/exactとは呼ばない。Accepted baseline数: 0。取得baseline: なし。NOT_CONVERGED候補をreferenceに採用していない。

## 6. Numerical stopping criteria

minimum400、20 iterationごとに全7QoI、U/T変化、mean/max、heat monitor。200 iteration windowを満たし、さらに200継続確認、maximum12000。value range/U/T change1e-8、position1/4096、heat range1e-8。他equation initial residual<=1e-8、pressure final<=1.1×そのrunのtolerance。圧力1e-6に1e-10を課していない。normal exit/finite必須。max到達未達はNOT_CONVERGEDとSTOP。末尾の個別criterion、全7QoI Rwinとfield変化はconvergence_diagnostics.json / baseline_rwin_history.csvへ記録。

## 7. Verification-only source solver

stock v6 sourceを新規auditSolverへコピーし、別binary buoyantBoussinesqSimpleFoamContinuitySourceAuditを作成。UEqn/TEqn/correction order/relaxationは不変。元physical matrixをcopyして監査、pressure source()からV*s=gを引きreference後solve。v6 fvMatrix.C:1458のmatrix==fieldはsourceへV*fieldを加えるので、元q=b0−A0pに対しq≈+gを狙う。s units1/sをruntime検証。source固定、Up feedbackなし。

## 8. Zero-source stock equivalence

status=PASS。代表20²/cold-start10 iterationsのU/T/p_rgh/phi全ファイルSHA256で比較。詳細はzero_source_equivalence.json。非同値なら非zero試験へ進まない。

## 9. Source realization verification

source sign=NOT_RUN、status=NO、steady valid relative L1(q−g) range={'relative_L1_min': None, 'relative_L1_max': None}。sum/max abs(q−g)、q+g、sum g/q、reference-aware residual、wall/closure、source cell/face supportをCSV/個別JSONへ保存。source purity5%は実験解釈の条件で研究quotaではない。invalid pilot levelsは保持しcurve採用しない。

## 10. Arm 1 design

各gridのpressure absolute tolerance1e-6/1e-8/1e-10、relTol0。physics/BC/schemes/relaxation/U/T solver/cold-startを固定。pressure変更はcoupled trajectoryも変えるためpure continuity-onlyとは主張しない。

## 11. Arm 1 results

Arm1 executed/steady=1/0。epsilon→QoI relation=INCONCLUSIVE。全7QoIとcontinuity/residual/Up/RwinをCSV保存。nonsteadyをcurveへ採用していない。

## 12. Arm 2 design

P1 centre、P2 near_hot、P3 near_cold、P4 four-site spread、P5 reference vicinityを実装。dimensionless anchors、nearest internal X-face、face-ID tie break、pRefCell incident face除外を固定。g=B_h*aでzero-net、4-site L1はsingle-siteと同一。eta_nomはUp_baseで定義、actual epsilonは測定。perturbed discrete numerical systemへのresponseであり、元source-free PDEのaccepted解ではない。

## 13. Pilot amplitude study

20² P1 positive pilot levels1e-8..1e-4。選定ruleは最低resolved level＋次の2有効level（不足なら最高3とresolution incomplete）。結果: None。amplitudeはresearch thresholdではない。

## 14. Arm 2 exploration results

Arm2 pilot/exploration/matching/confirmationのexecuted/steady=0/0。20/40 P1/P2/P4、3 level、positiveとmid P1/P2 negativeを予定。全trialを保存し、match失敗はinconclusive。

## 15. Temperature-offset diagnostic

{"performed": false}。20-gridの+50K offsetはinterpretation diagnosticのみ。TEqnのdiv(phi,T)にT*div(phi)応答があり、theta置換やcompensating heat sourceを加えていない。

## 16. Mean versus local defect

same-mean pattern dependence=INCONCLUSIVE、local max added information=INCONCLUSIVE。actual meanのmatching toleranceはsource realization/repeatabilityだけから作り、QoIを見て決めない。nominal同値だけでsame meanにしない。max/mean/location/P99を保存しmax Hard/trigger cutoffを選ばない。

## 17. Pattern and sign sensitivity

actual-mean matched pairs: []

Sign pairs: []。差の有意性は保守的uncertainty envelope内でのresolved responseを意味し、科学的許容性ではない。

## 18. QoI uncertainty

baseline＋testのtail window/continuation差、4097/8193 samplingとpeak tie/position resolution、memory/file差、同grid restart差を保守的に合成。独立RSSを用いない。near-zero branchはbaseline uncertaintyで事前定義。observed difference<=uncertaintyはEFFECT_NOT_RESOLVEDでありZERO_EFFECTではない。細かいsamplingも離散化真値を提供しない。

## 19. Exploration hypotheses

H1-H4={"H1": "INCONCLUSIVE", "H2": "INCONCLUSIVE", "H3": "INCONCLUSIVE", "H4": "INCONCLUSIVE"}。根拠pairとmonotonicityの支持/違反はexploration_summary.jsonに保存。空の比較集合をNOT_SUPPORTEDへ読み替えない。

## 20. Confirmation preregistration

confirmation manifest SHA256=None。探索解析後にだけ作成し、v1を固定。未到達時はmanifestを偽って作らない。予定は80、Arm1全3 tolerance、P1 seen/P3 held-out、2 amplitude×positive/negative。

## 21. 80² holdout confirmation

status=NOT_RUN。80 nonzero結果を探索中に見ていない。固定manifest以外の条件を結果閲覧後に追加していない。

## 22. Exploration versus confirmation

{"status": "NOT_RUN", "exploration_model_modified_after_confirmation": false}。outside-envelopeデータを削除せず、exploration_model_v1をretroactiveに変更しない。confirmationはquota PASS/FAILではない。

## 23. Conditional epsilon-to-QoI mapping

conditional mapping available=False。conditional_mapping.jsonにfinite tested response upper envelopesと外部b_Qが与えられた場合のcandidate選択ruleを保存。連続補間や未試験patternを保証せず、今回は数値b_Q/tauを選ばない。

## 24. Implications for Budget C

Budget Cのmean Hard候補、max/boundary/closure investigationとdiagnosticsという役割を維持する。local/pattern response evidenceはmean-only characterizationの限界を検討する材料。正式Gate Gの変更やmax Hard採用はしない。

## 25. What this experiment does NOT justify

今回の観測差からquotaを作らない。measurement capability/source-purity rule/steady ruleはresearch acceptance thresholdではない。formal matrixへの適用、任意pattern保証、Candidate B正式採用を正当化しない。

## 26. tau_mean status

TAU_MEAN=UNRESOLVED、QOI_IMPACT_QUOTA_VALUE/STATUS=UNRESOLVED、CANDIDATE_B_STATUS=PROVISIONAL、NEW_SPEC_RA1E3_GATE_G=NOT_EVALUATED。

## 27. Limitations

有限grid/有限pattern/人工source/absolute-temperature coupling/uncertaintyに限定。STOPにより非zero source sign/purity、pilot、response、offset、80 holdoutを未検証。unexecuted scheduler/analysis branchesの正しさもsolver evidenceで確認していない。confirmation_manifest_v1は探索が未完了なので作成していない。全curve図はNo eligible sensitivity observationsと明記した空図であり、response dataを意味しない。保存fieldはignored runs内にのみ置き、compact CSV/JSON/hashes/figuresを成果物とする。初回環境取得でWM_BASH_FUNCTIONS継承由来のshell警告が出たが、実行logは全てFoundation v6/serialを確認。fresh-shell環境取得を専用script側で修正した（STOP後solver再実行なし）。

## 28. Required user decision

STOP理由を解消する別taskと事前登録amendmentを許可するかが次の判断。現taskではこれ以上solverを実行しない。仕様変更、git add/commit/push、formal再評価は実施していない。

