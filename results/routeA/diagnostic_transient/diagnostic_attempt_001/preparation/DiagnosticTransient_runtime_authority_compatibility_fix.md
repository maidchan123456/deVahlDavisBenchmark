# DiagnosticTransient runtime authority compatibility fix

## 1. Executive summary

v1.5 canonical authority → exact compatibility adapter → frozen v1.4 resource implementationを検証しPASS。resource readiness=NO、execution authorized=NOは維持。production/Q1/Q2/Q3は実行せず、新layerはread-only検証・preflight bridge・permission declaration validatorのみ。

## 2. Authority verification

開始HEAD90183094936266183e1e1fb4487f0f0a512c512bは指定と一致。canonical v1.5 SHA06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d、formal v1.7 SHAfbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60を検証。timing plan/compute review/consistency report/diffをexact SHAでpin。依頼#82のformal SHAには余分なdが入っているため、#3と実ファイルの一致する64桁を使用した。

## 3. Current incompatibility

旧launcher.py version1.4 pinは変更しない。旧runtimeの直接v1.5入力拒否は残る。current PASSは新v1_5_runtime layerによる明示mappingの結果で、旧launcherが直接v1.5をacceptするという意味ではない。旧timing planのREQUIRES_FIXも過去状態として変更せず、新receiptで解決を記録。

## 4. Why simple version-pin relaxation is unsafe

version>=1.4 /unknown version /resource guard bypassを許可しない。canonical SHA、全source SHA、lineage/evidence、numeric/retention equivalence、production guardとmode separationの検証が必要。

## 5. Compatibility architecture

新namespace Scripts/routeA/diagnostic_transient/v1_5_runtime/。authority.pyはexact manifest/authority/implementation/semantic verification。production.pyはdouble guardとread-only旧prepare bridge。qualification.pyはpermission宣言だけを検証しlauncher/process/dispatchへ到達しない。verify CLIは固定git rev-parseによるHEAD付きreceipt表示のみ。

## 6. Canonical authority → executable implementation mapping

manifestのrule EXACT_V15_MACHINE_METADATA_TO_FROZEN_V14_RESOURCE_RUNTIMEを登録。1.4 historical direct /1.5 exact registered mapping /unknown STOP。全36v1.4source files、source mappingの同一性、native source set810filesとdigest、resource instrumentation digest、parent instrumentation digest/実source、replacement observer c6d89ab1f34761f881743adfee279cc65cd73a4bd67c1550c27e8a4ae5bf4c4aをverify。scientific17sectionsに加えcapacity/retention/lifecycle/seal/purge/source setのequality、全leaf semantic diffを再計算。

## 7. Production guard preservation

runはauthority PASS AND canonical resource_ready YES AND explicit authorizationを要求。現在のexact authorityはNOのためspecやqualification flagに関係なくRESOURCE_READY_NO_NO_EXECUTIONで停止。synthetic ready=YESかつauthなしも拒否。prepareはcanonical contractを検証して旧v1.4authorityを明示mappingし、凍結された旧prepare bodyを実行するread-only bridge。resource/namespace/capacity/C3/prior-seal guardsを保持し、canonical/implementation provenanceを両方返す。実際のproduction preflightは今回未実行、unit bridgeはmock使用。新layerにproduction executorはなくfuture bindingは別task。

## 8. Qualification/production separation

Q0 read-only /Q1 target nonCFD /Q2 diagnostic U03 memory IO nonCFD /Q3 boundedCFD /PRODUCTIONを独立authority scopeで定義。qualificationはproduction moduleをimportしない。validatorはdeclared task reference/prior statusを受け取るだけで外部user permissionを証明しない。結果は常にexecution_authorized=false。新taskの実許可とharness/watchdog/実stage receiptの統合が必要。

## 9. Permission matrix

CSV/manifestにCFD/time advance/production namespace/resource ready/auth scopeを全5modeで登録。Q1/Q2はNONCFD_TIMING_QUALIFICATION。Q3はQ3_BOUNDED_CFD_TIMING_QUALIFICATIONかつallowed_stages=[Q3]、Q0-Q2/memory/IOPASS、practical cost、U03revisionなし、finite user budget/risk受容。Q1/Q2permissionからQ3へ昇格不可。すべてexecution_implemented=false。

## 10. Namespace isolation

qualificationはresults/routeA/diagnostic_transient/timing_qualification/<id>/のみ、productionはdiagnostic_attempt_001/series/<registeredcase>/。absolute lexical path +realpath +全component symlink拒否、..、symlink→series、production outputをnegative test。validatorはoutput作成/書込をしない。production prepareもcase basename/namespace/symlinkを検証。

## 11. Provenance/hash binding

manifestはpins.pyのexact SHAでbind。repo authority/source91pins、critical native/system library851identitiesを検証。外部system symlinkはregistered target realpath+SHA一致のみ可、repo paths/output symlinkは不可。未来Q0 compiler/binary/ABI/WM_OPTIONS/linked librariesのactual receipt schemaを定義; historical linkage検証はfuture actual executable linkage captureを代替しない。既存semantic reportの/ prepared_atだけにtimestamp差あり:report22:15:07.015846+09:00 vs canonical22:12:28.543211+09:00。両exact値をmanifest erratumとして登録。他133rowsは完全一致、時刻一般免除なし、元evidence修正なし。

## 12. Positive compatibility tests

exact registered v1.5 + all registered v1.4/observer/native/hash evidenceでPASS。resource=NO/run auth=falseをassert。透明preflight mappingがinput spec/contractをmutateせずcanonical receiptを維持するmock unit。Q0/Q1/Q2 permission宣言がvalidation可能でもexecution不可を確認。

## 13. Negative authority tests

unknown1.6/2.0/unversioned、scientific/sampling/retention/capacity/lifecycle/purge変更、canonical/formal/source/observer/plan SHA mismatch、native source mismatch、contract path spoof、symlink target realpath mismatch/changed target、duplicate JSONkey、未登録timestampを全て拒否。SHA failure injectionは読取hashのmockで既存source/libraryを書き換えない。

## 14. Production guard tests

actual verify PASSに対するproduction run拒否をauth無し/有りで確認、prepare未到達assert。synthetic ready=true/auth無しの拒否。production namespace/qualification override拒否。旧v1.4source SHA不変のため元disk/series/seal/C3/bodyは変更なし。実CFD/subprocess solverなし。

## 15. Qualification privilege-escalation tests

modeQ1+command/binary/case/foamRun/solver_binary、nested execution key、unknownmode/unknownfield、PRODUCTION auth reuse、stage mismatch、Q1permission内Q3をreject。Q3 separate auth/prerequisites/risk/budget gateをunitで確認。production namespace/path traversal/symlink escapeをtempdirでreject。ASTでqualification importsがmath/pathlib/authorityのみ、launch/dispatchなしを確認。

## 16. Remaining timing-preparation blockers

target-size native adapter=NO、independent watchdog=INTERFACE_ONLY。既存Q1/Q2/Q3 definitionsとbudgetsは凍結のまま。元protocolのREQUIRES_FIX hard gateも未変更であり新adapterへのintegrationが次task。watchdog hard wall/process group、AS/RSS/host memory/disk/file traces、actual stage receipt、target fixture validation/fit/measurement-ready result captureが必要。RUN Q1/Q2には進まない。

## 17. Final readiness

compatibility PASS、scientific/technical/storage readinessは既存YES、compute/memory/IO UNRESOLVED、overallresourceNO、configuration frozenNO、executionauthorizedNO。formalGateJ未許可/未実行、GateF FAIL/320needsYES、downstream/particleNOを維持。19unit tests PASS、timing benchmark/CFD/case/mesh/init/seal/purgeなし。

## 18. Exact next task

FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION。既存Q1/Q2/Q3定義を保持してtarget adapter+independent watchdog+このmapping+実stage/auth receiptsをintegrationしmeasurement-ready preparationを完成する。推奨gpt-6.1-sol /medium。今回のcompatibility PASSはproduction/Q1/Q2/Q3実行許可ではない。

## Required final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_RUNTIME_AUTHORITY_COMPATIBILITY_FIX = COMPLETE
CANONICAL_DIAGNOSTIC_AUTHORITY_VERSION = 1.5
CANONICAL_DIAGNOSTIC_AUTHORITY_SHA256 = 06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d
CANONICAL_AUTHORITY_HASH_VERIFIED = YES
FORMAL_AUTHORITY_VERSION = 1.7
FORMAL_AUTHORITY_SHA256 = fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60
FORMAL_AUTHORITY_HASH_VERIFIED = YES
EXECUTABLE_IMPLEMENTATION_GENERATION = v1.4
V14_RUNTIME_IMPLEMENTATION_UNCHANGED = YES
V15_TO_V14_RUNTIME_MAPPING_DEFINED = YES
V15_METADATA_ONLY_COMPATIBILITY_VERIFIED = YES
RUNTIME_AUTHORITY_COMPATIBILITY = PASS
PRODUCTION_RESOURCE_GUARD_PRESERVED = YES
PRODUCTION_EXPLICIT_AUTHORIZATION_GUARD_PRESERVED = YES
PRODUCTION_NAMESPACE_GUARD_PRESERVED = YES
QUALIFICATION_AUTHORITY_SEPARATE_FROM_PRODUCTION = YES
Q0_PERMISSION_DEFINED = YES
Q1_PERMISSION_DEFINED = YES
Q2_PERMISSION_DEFINED = YES
Q3_PERMISSION_DEFINED = YES
Q1_Q2_CAN_INVOKE_CFD = NO
Q1_Q2_CAN_WRITE_PRODUCTION_NAMESPACE = NO
Q3_REQUIRES_SEPARATE_AUTHORIZATION = YES
PRODUCTION_REQUIRES_RESOURCE_READY = YES
PRODUCTION_REQUIRES_EXPLICIT_AUTHORIZATION = YES
CURRENT_RESOURCE_READY = NO
CURRENT_EXECUTION_AUTHORIZED = NO
V15_COMPATIBILITY_PASS_AUTHORIZES_PRODUCTION = NO
UNKNOWN_CONTRACT_VERSION_FAILS_CLOSED = YES
MODIFIED_IMPLEMENTATION_HASH_FAILS_CLOSED = YES
WRONG_AUTHORITY_SHA_FAILS_CLOSED = YES
QUALIFICATION_PRIVILEGE_ESCALATION_TEST = PASS
PRODUCTION_GUARD_NEGATIVE_TEST = PASS
RUNTIME_COMPATIBILITY_TESTS = PASS
TARGET_SIZE_DIAGNOSTIC_HARNESS_PREPARED = NO
INDEPENDENT_RESOURCE_WATCHDOG_PREPARED = INTERFACE_ONLY
Q1_EXECUTED = NO
Q2_EXECUTED = NO
Q3_EXECUTED = NO
PRODUCTION_SOLVER_EXECUTED = NO
PILOT_CFD_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
COMPUTE_FEASIBILITY = UNRESOLVED
MEMORY_FEASIBILITY = UNRESOLVED
IO_FEASIBILITY = UNRESOLVED
DIAGNOSTIC_TRANSIENT_STORAGE_READY = YES
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
COMPLETE_EXECUTION_CONFIGURATION_FROZEN = NO
EXECUTION_AUTHORIZED = NO
U01_CHANGED = NO
U02_CHANGED = NO
U03_CHANGED = NO
U04_EQUATION_SEMANTICS_CHANGED = NO
N_OUTER_CORRECTORS_CHANGED = NO
PERSISTENCE_POLICY_CHANGED = NO
SEAL_PURGE_POLICY_CHANGED = NO
CAPACITY_ESTIMATES_CHANGED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
CURRENT_LAUNCHER_V15_RUNTIME_COMPATIBILITY = PASS
RETENTION_POLICY_CHANGED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
```
