# DiagnosticTransient bounded timing qualification plan

## 1. Executive summary

本書は事前登録であり、計測・CFD実行の許可ではない。準備 COMPLETE。Q0のruntime compatibilityは REQUIRES_FIX、Q1/Q2/Q3は NOT_MEASURED。compute/memory/I/Oは前回同様 UNRESOLVED。target native adapterと独立watchdogは未実装、U03 bounded harnessは準備済みだが実行不可。

## 2. Authority verification

開始HEAD 344702e9648f86bd69aecec6b2e89a05030c8d5a は指定と一致。v1.5、formal v1.7、compute review JSON/MDおよびv1.4実装のSHAを検証しJSON authority_sha256へ登録。既存untracked casesは触らない。formal authority/readiness、過去結果、既存source/contractを変更しない。

## 3. Why qualification is required

145 fv solves /169scalar recordsと1144 recurring callbacksは削減不可。serialization/replay/historyの実target-size cost未計測のため、physical pilotより先にdiagnostic architectureを有限時間で判定する。

## 4. Current high-risk findings

既存reviewのみ：core0.8–9s/stepはrough proxy。four-cell OFF0.365s /ON22.3sはSYNTHETIC_ONLY。target-shape primitive和はpipeline実測ではない。U03の101→201→401で約4倍、15001trialは打切り。serial-only、diagnostic、U03はHIGH; memory/IOはUNKNOWN。これらを本taskの測定値と呼ばない。

## 5. Qualification philosophy

Q0→Q1→Q2→Q3。前段FAIL/REQUIRES_FIX/UNRESOLVEDで後段STOP。current taskで実行可能なのはread-only preflightとtiny unit sanityのみ。Q1/Q2にも新しいNONCFD計測taskの明示許可、Q3は別の明示許可が必要。QUALIFICATION_PASS != RUN_AUTHORIZATION。

## 6. Q0 authority/runtime preflight

JSON Q0_requirementsがchecklist。launcher.py:26はversion1.4を要求しv1.5を拒否するためREQUIRES_FIX。:49はproduction namespaceを固定、:76はresource_ready=YES要求。metadata-only改訂であってもpreflightを迂回しない。compiler/build/source/runtime binary、instrumentation、replacement/linked librariesのSHA/realpath/ABI/import pathsをfuture receiptへ。欠けたidentityはPASS不可。修正後は新protocol revision/source pinsをレビューし、現在のblocked validatorも更新してから計測する。

## 7. Q1 target-size diagnostic-only benchmark

既存160x160x1 meshをread-only使用。25600cells/50880internal/102720faces/640active+51200empty facesをassert。新case/meshを作らずprivate memoryにresource-only manufactured fields/matricesを構築。b=Apsi、component/BC/oldTime/epoch/hashを検証。foamRun/fv solve/time incrementは禁止。native adapterは未実装; adapter acceptanceまでQ1開始不可。callback taxonomy CSVは既存tiny selected bundleのtime_index2をstage+term+matrix schema+field shapeで分類し1141、controller3で1144。target bytesは全てNOT_MEASURED_REQUIRED_BY_Q1。current/unrelaxed/physical/referencedを含む全matrix slotで701packetsを確認。U vector solvesは145fv/169recordsに含むが、このgraphのmatrix packetsはscalarである; vector primitive stressを追加する場合はauxiliaryとして1144から除外。constructor1とauxiliary7を別扱い。実装時はcontrollerはpreSolve_before/preSolve_after/controller_complete、各meshState10fields。volScalar8/Uvector1/phiSurfaceScalar1を区別。単一payloadを1144回掛けない。archetype screening≤10s/trialの後、全順序mixをOFF/ON/ON/OFF/OFF/ONの6trial、各30sまで。startup別計上、persist/audit cadenceを変更しない。complete mixのみmeasured diagnostic s/physical-step-equivalent。cutoffはlower bound; weighted archetype costはPLANNING_ONLY。

## 8. Q2 diagnostic primitive/U03 benchmark

Q1PASS後、small receipt/field/matrix/term/selected payloadでnative JSON→AF_UNIX ACK→decode→canonical→replay→pack→SHAを各3repeat。ACK待ちはbackend処理を含むためspan和で二重計上しない。startup/per-callback/stage/step/selected auditを分離。U03はunchanged v1_1 contract_policy.py、N100,200,400,800,1600,3200,6400、各3repeat、trial15s、suite120s。8constant histories/0..0.6/end0.5で全3windowを強制評価。timeoutでlargerN停止、censoredをfitへ混ぜない。>=3 completed sizeのmedianからa,pをfit、local slopes/residualsも保存。source nested traversalとtiming fitを分離。production nodes30011/60021/120039はPLANNING_ONLY / LOW_CONFIDENCE_PROJECTION。arrivalの累積評価回数を含める。dominanceはrevision候補、アルゴリズム修正は禁止。

## 9. Memory qualification

normal compact/rolling-full/selected512MiB/field16MiB/raw-audit preparation/U01last5/U03historyを別測定。native/backendを20ms同時サンプリングしmax_t(nativeRSS+backendRSS)、各time-v高水位とVmSizeも保存。sum(individual peaks)は保守的上界で同時peakではない。RSS samplingの短いpeak欠落を明記。full9GiBをRAM展開せず32MiB stage chunksをstream、ring上限1GiBと実stage16x32MiBの他にobject/temporary join overheadを観察。部分streamだけではfull audit memory coverageをPASSにしない。

## 10. I/O qualification

同じlocal filesystemでactual publish/fsync/manifest/log rotate/readback hashを3repeat。64step receipt/primary chunk、4MiB log、16MiB field、512MiB bundle、32MiB stage chunks→各trial最大256MiB、系列最大1GiB audit prefix、Q2総4GiBまで。real bytesをwriteしsparse/preallocateはallocation probeのみ。9GiB sustained throughputはprefixだけでは保証しない。cached/cold-uncontrolled/warmを区別、root cache drop不要。logical bytes/wcharとproc io write_bytes/device writesを別列。wall/CPU/MBps/fsync/hash readを保存。retention capacity primary428653979016B /peak445833848200B /conditional-inclusive838611250408Bは変更せず、tiny timingでcapacity reviewを置換しない。

## 11. Q3 bounded whole-step CFD design

今回設計のみ。Q0-Q2/memory/IOPASS、diagnostic practical、U03 revision不要、user runtime budgetとcontinuous-risk受容、別Q3許可が揃った場合のみ。OFFcoldA→ONcoldA→ONcoldB→OFFcoldB、4trial各最大2complete steps/30s、suite120s/全8steps、startupもwall cap内。最初のstep/wall capで終了。全24outer/2pressure/0nonOrthogonalとfrozen switches/linear/Co/persistenceそのまま。初期rest/uniformT0、ON/OFF state/BC/oldTimes/time trajectoriesを既存期待に従い比較。145fv/169scalar/iterations、ON-OFFoverhead/RSS/IPC/writesを保存。未完stepはs/step分母に入れない。2pairsだけなのでrepeatability provisional。

## 12. Q3 isolation/non-scientific status

専用 results/routeA/diagnostic_transient/timing_qualification/<authorized_id>/Q3/。production series/input namespaceへの上書き・result登録不可。NOT_PRODUCTION_RESULT /NOT_GATE_J /NOT_TEMPORAL_COMPARISON_RESULT /NOT_VALIDATION_DATAを全manifestへ。Nu/arrival/Co/physical mass-energyの結論禁止。namespace対応はfuture qualification wrapperのreviewが必要、production launcherを強引に迂回しない。

## 13. Resource guards

native AS8GiB/backend AS8GiB/hostMemAvailable>=24GiBは維持。各RSS8GiB/combined16GiBは追加のqualification STOP boundで緩和ではない。OS RLIMIT_AS+外部20msguard、独立100msdisk/file監視、before-write quotaが必要。wallはprocess-group全体をkill、TERM1s以内→KILL。guard欠落/trace不能でSTOP。noauto retry/purge/seal。partial evidence保存。

## 14. Timing budgets

Q0=30s/16MiB/64files、Q1=300s/12GiB/256、Q2=420s/4GiB/256、Q3=120s/16GiB/256。各trialQ0/Q1/Q3≤30s、Q2primitive≤30s/U03≤15s。全activestage870s=14.5min。Q2内訳120U03+120primitive+60memory+120IO。time budgetsにfixture preparation/startup/writer drain/output flushを含む。保持scratch global32GiB+16MiB/832filesまで、free reserve=max32GiB,10%free plus remaining allocation。次writeがcapを超えるなら停止; cap増量/再実行は別task。raw9GiBイベントがcapsに収まらなければcensored/UNRESOLVED、cadenceを減らさない。予算はbench停止条件でproduction deadlineではない。

## 15. Measurement tooling

protocol.pyはplan validatorとpure gate。u03_scaling.pyはdefault dryrun、future receiptを要求するbounded runner scaffold。target native adapter・external supervision・fit/memory/load integrationはまだ必要で、今はmeasurement-readyではない。time-v/proc status/io/loadavg/statvfs/pidstat/iostatを使用予定。governor snapshot powersave、cpu0min800MHz/max4500MHz、変更なし。taskset/affinityはreviewのみ。compiler/library identityのactual read-only captureをQ0へ。工具不足は記録し必要metricの代替がなければSTOP。

## 16. Repeatability requirements

Q1/Q2各cell/size/event3repeat、min/median/max/populationCV、paired overhead。CV>0.20/max:min>1.5/他CPUbusy>10%/host trace欠落でstability LOW; UNRESOLVED、自動追加repeat禁止。数値はplanning閾値でscientific acceptanceではない。warmupもbudget内、cold cache制御できないことを明記。

## 17. Decision tree

CSV/JSONにexact branches。currentnext=runtime compatibility FIX。adapter/guards不足ならpreparation FIX。Q0PASSと明示NONCFDtaskでQ1→Q2。diagnostic months/years risk→compute revision options review、U03dominance→U03 revision preparation、serializationdominance→diagnostic revision preparation。Q0-Q2PASSかつbudget/riskなら別Q3許可へ。Q3 coredominanceならMPI qualificationとU01outer reviewの情報価値を比較; MPI実装/実行なし。qualified practical→execution authorization preparation、production自動実行なし。user deadline未登録につき7days=FAIL禁止。qualified categoriesとQ1planningclassesはJSONのdecision定義を使用。

## 18. Failure/STOP rules

STOP CSVが全段に適用。authority/compatibility/authscope/fixture/count/finite/memory/disk/wall/U03/IO/noninvasivenessをfailclosed。trial timeoutはpartial lower boundでありactual production infeasibilityの証明ではない。UNKNOWN/UNRESOLVED/MARGINALは次段PASSと扱わない。Q3はhard budget/riskが未登録ならSTOP。

## 19. Output artifacts

plan MD/JSON、stage matrix、metrics、stop rules、decision tree、callback classes CSV、start_guard、unit validation/end_guard evidence。future measurementは別 timing_qualification namespaceへ immutable input/hash manifests、trial/load traces、timing spans、bytes/callback counts、memory/time-v、IO/fsync/hash、partial-stop records、fit/projection and qualification decisionsを保存。既存compute reviewとcontractを書き換えない。

## 20. Exact next task

FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RUNTIME_AUTHORITY_COMPATIBILITY。v1.5 governing authority、production readiness/namespace拒否との整合をreviewableなfixとして別taskで解決後、adapter/watchdog readinessを満たした新protocol revisionを作成。現在はRUN taskを選ばない。USER_DECISION_REQUIRED=YESは次taskの選択/許可に対するstatusで、この準備作業を止める質問ではない。

## Frozen authority SHA-256

- `docs/routeA_diagnostic_transient_contract_v1.5.json`: `06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d`
- `docs/routeA_diagnostic_transient_contract_v1.5.md`: `105e4932f7abdb6e5bf2a5f81e0c115e1b50fd5a0bfb5c2bca68b01710ee4c1e`
- `docs/routeA_diagnostic_transient_contract_v1.5.sha256`: `700f9dc488107bcd074b36db318a4b559acd7b29b8a0e037dad1328756496f9c`
- `docs/routeA_execution_contract_v1.7.json`: `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`
- `results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_compute_feasibility_review.json`: `669f2fcca81bca1e1c6c36dd249e70fa880549478134cadf9b3d26bb94d1e499`
- `results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_compute_feasibility_review.md`: `c0c37a44f36a87d416fc3c15020e2227cab05d0af57e7d4d250285f310f421f6`

## Required final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_BOUNDED_TIMING_QUALIFICATION_PREPARATION = COMPLETE
DIAGNOSTIC_CONTRACT_VERSION = 1.5
DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
DIAGNOSTIC_CONTRACT_SHA256 = 06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d
COMPUTE_REVIEW_AUTHORITY_VERIFIED = YES
QUALIFICATION_STAGES_DEFINED = YES
Q0_AUTHORITY_PREFLIGHT_DEFINED = YES
Q1_TARGET_SIZE_DIAGNOSTIC_ONLY_DEFINED = YES
Q2_U03_DIAGNOSTIC_PRIMITIVE_DEFINED = YES
Q3_BOUNDED_WHOLE_STEP_CFD_DEFINED = YES
Q3_EXECUTED = NO
PRODUCTION_SOLVER_EXECUTED = NO
PILOT_CFD_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
TARGET_SIZE_DIAGNOSTIC_HARNESS_PREPARED = NO
U03_SCALING_HARNESS_PREPARED = YES
MEMORY_MEASUREMENT_PLAN_DEFINED = YES
IO_MEASUREMENT_PLAN_DEFINED = YES
IPC_MEASUREMENT_PLAN_DEFINED = YES
REPEATABILITY_POLICY_DEFINED = YES
QUALIFICATION_WALL_BUDGETS_DEFINED = YES
QUALIFICATION_MEMORY_GUARDS_DEFINED = YES
QUALIFICATION_DISK_GUARDS_DEFINED = YES
Q1_STOP_RULES_DEFINED = YES
Q2_STOP_RULES_DEFINED = YES
Q3_STOP_RULES_DEFINED = YES
Q1_CAN_RUN_WITHOUT_CFD = YES
Q2_CAN_RUN_WITHOUT_CFD = YES
Q3_REQUIRES_SEPARATE_USER_AUTHORIZATION = YES
CURRENT_LAUNCHER_V15_RUNTIME_COMPATIBILITY = REQUIRES_FIX
CURRENT_DIAGNOSTIC_COMPUTE_RISK = HIGH
CURRENT_U03_COMPUTE_RISK = HIGH
CURRENT_SERIAL_ONLY_RISK = HIGH
CURRENT_MEMORY_RISK = UNKNOWN
CURRENT_IO_RISK = UNKNOWN
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
EXECUTION_AUTHORIZED = NO
COMPLETE_EXECUTION_CONFIGURATION_FROZEN = NO
U01_CHANGED = NO
U02_CHANGED = NO
U03_CHANGED = NO
U04_EQUATION_SEMANTICS_CHANGED = NO
N_OUTER_CORRECTORS_CHANGED = NO
PERSISTENCE_POLICY_CHANGED = NO
SEAL_PURGE_POLICY_CHANGED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RUNTIME_AUTHORITY_COMPATIBILITY
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
