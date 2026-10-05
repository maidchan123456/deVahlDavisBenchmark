# Diagnostic transient timing qualification preparation fix

Status: **INCOMPLETE**. Q1/Q2 measurement readiness: **NO**.

## 1. Executive summary

INCOMPLETE. Native adapter and independent per-trial watchdog are implemented and tiny tests pass. Both stage readiness flags remain NO; future execution is explicitly denied.

## 2. Authority verification

Canonical v1.5 and formal v1.7 SHA verified. Runtime compatibility PASS, 91 repository pins and 851 native/library identities verified. Previous runtime artifact hashes also match; HEAD remains 8135eec17dab5c66082bb25b9e3509ee2cc39ac9.

## 3. Existing preparation blockers

Original target adapter was absent and watchdog interface-only. This new namespace supplies code and tests; the old frozen plan and runtime mapping are unchanged.

## 4. New harness architecture

Read-only mesh and stored graph -> manufactured Python fixture -> original C++ Json representation/serializer -> AF_UNIX -> frozen evaluator/Live/Writer. OFF retains preparation/parsing/graph traversal. No CFD command or time API is used.

## 5. Target-size topology adapter

Read-only existing A-Ra1e6-fine mesh: 25600 cells, 50880 internal faces, 102720 total faces, 640 active boundary faces and 51200 empty faces. Four 160-face wall patches and two 25600-face empty patches. Empty field-patch arrays contain zero values, as the native schema requires.

## 6. Target-size fixture generation

rho/rhoFluidThermo:rho,U,T,e,p,p_rgh,phi,K,gh have target shapes. Constant resource-only values, synthetic volumes/centres/thermal context and zero explicit terms have no physical interpretation. Old histories for rho/e/K have 0/1/2 levels at synthetic indices 0/1/2. b=Apsi and native original hashes/epochs are regenerated; no time is advanced.

## 7. Callback/matrix graph mapping

Registered 42 stage/term classes map to 1144 recurring callbacks (1141 physical +3 controller), with 701 scalar matrix packets; one constructor is excluded. Matrix slots and explicit terms remain class-specific. Vector U field and 169 manufactured scalar solve records are represented; the registered graph has no U vector-matrix callback.

## 8. Qualification authority integration

Every public target worker requires an external future authorization, sealed stage receipt, frozen authority verifier and permission validator. The direct native executable calls a fixed permission helper. Harness manifest readiness=false blocks both stages before execution. No actual authorization receipt was issued.

## 9. Independent watchdog

Separate process samples /proc RSS, VmSize, HWM, CPU ticks, IO and host state around 20ms. Disk/files/statvfs sampling around100ms. Trace overhead and uncertainty are disclosed; missed peaks or invalid samples cannot establish feasibility.

## 10. Process-group supervision

Dedicated groups, registered nested groups, PPid tracking, subreaper and parent-death SIGKILL. TERM grace <=1s then KILL; cleanup pulses keep watchdog heartbeat alive. Escape and supervisor-crash tests pass. Whole-stage nested integration remains B4.

## 11. Memory/AS monitoring

Plan-based native/backend AS and RSS 8GiB, combined RSS16GiB, host MemAvailable24GiB. RLIMIT_AS plus sampled VmSize; aggregate process limits conservative. Simultaneous max(native+backend) is separate from sum of individual peaks. Tests use small limits, never8GiB allocation.

## 12. Disk/file monitoring

Frozen per-stage scratch/file/inode/free-space guards; before-write checks plus independent monitoring, logical/allocated bytes, symlink rejection. No purge. Overall file layout and STOP-publication reserves are not qualified; B2/B4 prevent READY.

## 13. Wall-time enforcement

Plan supplies stage/trial budgets. Q1 order OFF/ON/ON/OFF/OFF/ON. Q2 U03 trial15s/suite120s; whole Q2 420s. External supervisor enforces deadlines; no in-process-only timeout or retry.

## 14. Partial/censored evidence

STOP retains immutable receipt and trace/log/result/manifest where generated, exit/signal and stop reason; watchdog failure invalidates the sample. Timeout is CENSORED, excluded from fit, and stops larger U03 N. Small tests inspect retained partial artifacts before temporary-test cleanup; no real qualification evidence was created.

## 15. Q1 runner readiness

Implemented fixed native/backend runner, graph assertions, original full processing, native/time-v CPU/RSS and class byte summaries. Startup/full-audit schedule and bounded repeat retention remain B1; Q1_MEASUREMENT_READY=NO.

## 16. Q2/U03 runner readiness

Frozen arrival_candidate algorithm for N100..6400 and three repeats, eight histories/all three windows. Completed-only fit requires three sizes/three repeats, records local slopes/residuals and LOW_CONFIDENCE projection. Tiny N4 only was executed. Whole Q2 remains NO because B2-B4.

## 17. IPC/memory/I/O runner readiness

Native parse/hash/serialization/ACK and backend decode/canonical/replay/pack/SHA/publish/QoI/U01 spans implemented. ACK is inclusive. Seven memory-event tiny paths and bounded nonsparse IO with real file/directory fsync and readback tested. Memory-event sizes are actual packets, not theoretical maxima. Full9GiB is streamed, never allocated or claimed qualified. Small scalar/per-class and memory sharing remain B3.

## 18. Namespace/permission safety

Production series and external/traversal/symlink paths rejected, unknown mode and Q1-to-Q3 escalation rejected. Source case is read-only. Authorization schema accepts no external execution command. Fresh output and immutable publication prevent historical overwrite.

## 19. Positive tests

26 unittest checks passed, including full four-cell native/backend graph. After startup-history correction, focused full native/backend test passed again. These are correctness/process tests only; no timing values are reported as target performance.

## 20. Negative tests

Wrong authority/topology/callback/matrix counts, missing/tampered permission/receipt, direct native missing permission, prohibited execution inputs/namespace/path/escalation, wall/memory/disk/file limits, group escape and watchdog crash all reject/stop as expected.

## 21. Measurement-readiness decision

Both Q1/Q2 readiness flags are NO. New harness manifest enforces this independently of future external permission. No automatic Q3 or production decision; resource feasibility remains UNRESOLVED.

## 22. Remaining blockers

B1 schedule/startup/scratch reconciliation; B2 bounded file layout; B3 complete scalar/class/memory/stability accounting; B4 tiny whole-stage positive/partial/quota-reserve integration.

## 23. Exact next task

FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION. Do not start RUN_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION until these blockers are closed. Q3 and production remain unauthorized.

## Required final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION_FIX = INCOMPLETE
CANONICAL_DIAGNOSTIC_AUTHORITY_VERSION = 1.5
CANONICAL_DIAGNOSTIC_AUTHORITY_SHA256 = 06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d
CANONICAL_AUTHORITY_HASH_VERIFIED = YES
FORMAL_AUTHORITY_VERSION = 1.7
FORMAL_AUTHORITY_SHA256 = fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60
FORMAL_AUTHORITY_HASH_VERIFIED = YES
RUNTIME_AUTHORITY_COMPATIBILITY = PASS
TARGET_SIZE_DIAGNOSTIC_HARNESS_PREPARED = NO
TARGET_SIZE_NATIVE_ADAPTER_IMPLEMENTED = YES
TARGET_TOPOLOGY_VALIDATED = YES
TARGET_CELL_COUNT = 25600
TARGET_INTERNAL_FACE_COUNT = 50880
CALLBACK_GRAPH_SUPPORTED = YES
CALLBACKS_PER_STEP_EQUIVALENT = 1144
MATRIX_PACKET_GRAPH_SUPPORTED = YES
MATRIX_PACKETS_PER_STEP_EQUIVALENT = 701
INDEPENDENT_RESOURCE_WATCHDOG_PREPARED = YES
WATCHDOG_OUT_OF_PROCESS = YES
PROCESS_GROUP_SUPERVISION = YES
WALL_TIME_GUARD_IMPLEMENTED = YES
NATIVE_RSS_MONITOR_IMPLEMENTED = YES
BACKEND_RSS_MONITOR_IMPLEMENTED = YES
COMBINED_RSS_MONITOR_IMPLEMENTED = YES
VMSIZE_AS_MONITOR_IMPLEMENTED = YES
HOST_MEMORY_MONITOR_IMPLEMENTED = YES
DISK_FREE_MONITOR_IMPLEMENTED = YES
FILE_COUNT_MONITOR_IMPLEMENTED = YES
PROCESS_IO_MONITOR_IMPLEMENTED = YES
LOADAVG_MONITOR_IMPLEMENTED = YES
WATCHDOG_FAILURE_FAILS_CLOSED = YES
PROCESS_GROUP_KILL_TEST = PASS
WALL_TIMEOUT_TEST = PASS
MEMORY_GUARD_TEST = PASS
DISK_GUARD_TEST = PASS
FILE_COUNT_GUARD_TEST = PASS
PARTIAL_EVIDENCE_PRESERVED = YES
CENSORED_TRIAL_POLICY_IMPLEMENTED = YES
QUALIFICATION_STAGE_RECEIPT_IMPLEMENTED = YES
QUALIFICATION_MANIFEST_IMPLEMENTED = YES
Q1_MEASUREMENT_RUNNER_PREPARED = NO
Q2_MEASUREMENT_RUNNER_PREPARED = NO
U03_SCALING_RUNNER_PREPARED = YES
IPC_TIMING_RUNNER_PREPARED = NO
MEMORY_EVENT_RUNNER_PREPARED = NO
IO_RUNNER_PREPARED = YES
Q1_MEASUREMENT_READY = NO
Q2_MEASUREMENT_READY = NO
Q1_Q2_CAN_INVOKE_CFD = NO
Q1_Q2_CAN_ADVANCE_PHYSICAL_TIME = NO
Q1_Q2_CAN_WRITE_PRODUCTION_NAMESPACE = NO
QUALIFICATION_NAMESPACE_ISOLATED = YES
PATH_TRAVERSAL_TEST = PASS
SYMLINK_ESCAPE_TEST = PASS
PRIVILEGE_ESCALATION_TEST = PASS
Q1_EXECUTED = NO
Q2_EXECUTED = NO
Q3_EXECUTED = NO
PRODUCTION_SOLVER_EXECUTED = NO
PILOT_CFD_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
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
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
LINEAR_SOLVER_POLICY_CHANGED = NO
TEMPORAL_POLICY_CHANGED = NO
RETENTION_POLICY_CHANGED = NO
Q1_Q2_ACTUAL_MEASUREMENT_AUTHORIZED = NO
```
