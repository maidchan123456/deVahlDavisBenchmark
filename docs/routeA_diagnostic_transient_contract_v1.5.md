# Route A diagnostic transient contract v1.5

Revision scope: `MACHINE_AUTHORITY_CONSISTENCY_ONLY`. Canonical machine authority is [v1.5 JSON](routeA_diagnostic_transient_contract_v1.5.json); its SHA is in the companion sidecar.

Lineage: v1.2 U01–U04 closed → incomplete v1.3 resource candidate → finalized v1.4 resource/binding/lifecycle fix → v1.5 authority consistency fix. All previous versions remain immutable.

## Execution guard correction

DIAGNOSTIC_TRANSIENT_RESOURCE_QUALIFICATION_PENDING_NO_RUN_AUTHORIZATION. Remaining blockers: compute, memory, I/O qualification and explicit future run authorization. execution_authorized=false.

## Resource-review status correction

revision_complete/resource_revision_complete/storage_revision_complete=true. resource_ready/overall_resource_ready=false; compute_review_required=true. Completed review scope is storage/evidence revision, not overall resource qualification.

## Live-binding flag correction

Stored live_native_validation PASS: complete required columns, 145 fv solves/169 component records, U01 PASS, controller PASS, bitwise non-invasiveness. live_policy_validation PASS verifies U03/controller/anomaly bindings; lifecycle validation retains selected fields. Native-primary and field-binding status flags now agree. Evidence was inspected, not re-executed.

## Authority HEAD semantics

v1.0 actual preparation input fd129af05d43e3551cf0d4a037b5dd8f54ccbe4a. Inherited 74b1f7b2c0e844ac559997277ce30dde2450b3f8 is v1.1 fix input HEAD, as confirmed by v1.0/v1.1 contracts and git show of the v1.0 commit. v1.3 input ed2371e88c2d728bfbf8fffd21cd99497c1b9afc comes from resource_revision/authority.json; v1.4 fix input 7369926b5517ce1da49829759653224489614575 from start_guard.json. Current v1.5 input HEAD is recorded separately. Historical inventories and U04 build authority remain unchanged.

## Storage guard 0.55 vs sequential 0.5603 resolution

PER_SERIES_ONLY, retained at 0.55. resource_guard.preflight receives each series working peak, current statvfs free and file budget. launcher.prepare additionally checks current free > working peak + measured existing permanent + max(32 GiB, int(10% current free)). BOTH_REQUIRED. Current free already excludes retained bytes; existing permanent is an additional conservative reserve. Cumulative 0.560285624635319 uses initial free and is descriptive, not the per-series gate numerator. Primary planning guard checks below pass; no threshold, capacity, safety reserve, lifecycle or code changes. Fresh measurements and checks are still required before each future series. Co0.125 remains conditional, infeasible at the current worst-case planning caps, and requires separate review/authorization.

## Historical/current-state separation

Preserved every inherited_* section, resource_candidate_lineage, original v1.3 INCOMPLETE fact, U04 build authority, and frozen scientific annotation strings. Explicit scope descriptions identify their historical meaning. v1.5 readiness is current. Unchanged v1.4 launcher is version-pinned to 1.4; this metadata-only revision does not migrate it or claim executable v1.5 support.

## Scientific-section invariance

All 17 required scientific sections semantically equal; remaining non-allowlisted contract leaves are also equal. resource_revision_fix is wholly equal, including capacity, P1 evidence/cadence, R0–R4, seal/purge lifecycle and source hashes. Formal authority/status and all historical sections equal. U01/U02/U03/U04 equation semantics unchanged.

## Final readiness

Scientific/technical/storage/live binding/evidence lifecycle READY. Memory/I/O/compute UNRESOLVED. Overall resource NOT_READY; complete execution configuration remains unfrozen; execution unauthorized. Formal Gate J, Gate F, 320 need and downstream/particle status unchanged.

## Exact next task

REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY. Recommended gpt-6.1-sol / medium. USER_DECISION_REQUIRED=YES refers to selecting/authorizing a future task; this completed fix grants no run authorization.

Detailed report, changed paths, invariants and synthetic mutation results are in `results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_v1_4_authority_consistency_fix.{md,json}`.

## Required final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_AUTHORITY_CONSISTENCY_FIX = COMPLETE
SOURCE_CONTRACT_VERSION = 1.4
SOURCE_CONTRACT_SHA256 = c58096f1b6422003c16884e7b8d3c0bb828d9ea797ae59fca9605229af597a82
SOURCE_CONTRACT_HASH_VERIFIED = YES
NEW_DIAGNOSTIC_CONTRACT_CREATED = YES
NEW_DIAGNOSTIC_CONTRACT_VERSION = 1.5
NEW_DIAGNOSTIC_CONTRACT_SHA256 = 06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d
REVISION_SCOPE = MACHINE_AUTHORITY_CONSISTENCY_ONLY
PARENT_DIAGNOSTIC_CONTRACT_VERSION = 1.2
PARENT_DIAGNOSTIC_CONTRACT_SHA256 = 7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd
PARENT_VERSION_SHA_CONSISTENT = YES
FORMAL_ROUTE_A_VERSION = 1.7
FORMAL_ROUTE_A_SHA256 = fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60
FORMAL_AUTHORITY_CONSISTENT = YES
STALE_V1_3_EXECUTION_GUARD_REMOVED = YES
CURRENT_EXECUTION_GUARD = DIAGNOSTIC_TRANSIENT_RESOURCE_QUALIFICATION_PENDING_NO_RUN_AUTHORIZATION
LIVE_PRIMARY_BINDING_STATUS_CONSISTENT = YES
PRODUCTION_PREFLIGHT_STATUS_CONSISTENT = YES
READINESS_CHECKLIST_STALE_ITEMS_FIXED = YES
RESOURCE_REVISION_COMPLETE_STATUS_CONSISTENT = YES
NEXT_SINGLE_TASK_CONSISTENT = YES
AUTHORITY_HEAD_SEMANTICS_RESOLVED = YES
LEGACY_0P55_GUARD_SEMANTICS_RESOLVED = YES
LEGACY_0P55_GUARD_STATUS = PER_SERIES_ONLY
SEQUENTIAL_PRIMARY_PEAK_FRACTION = 0.560285624635319
STORAGE_FEASIBILITY = FEASIBLE
DIAGNOSTIC_TRANSIENT_STORAGE_READY = YES
MEMORY_FEASIBILITY = UNRESOLVED
IO_FEASIBILITY = UNRESOLVED
COMPUTE_FEASIBILITY = UNRESOLVED
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = YES
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = YES
COMPLETE_EXECUTION_CONFIGURATION_FROZEN = NO
EXECUTION_AUTHORIZED = NO
CONSISTENCY_CHECKER_IMPLEMENTED = YES
CONSISTENCY_CHECKER_PASS = YES
ACTIVE_CURRENT_STATE_CONTRADICTIONS = 0
NEGATIVE_TESTS = PASS
SCIENTIFIC_SECTIONS_CHANGED = NO
U01_CHANGED = NO
U02_CHANGED = NO
U03_CHANGED = NO
U04_EQUATION_SEMANTICS_CHANGED = NO
PERSISTENCE_POLICY_CHANGED = NO
SEAL_PURGE_POLICY_CHANGED = NO
CAPACITY_ESTIMATES_CHANGED = NO
PRODUCTION_SOLVER_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
PRODUCTION_DATA_PURGED = NO
HISTORICAL_DATA_PURGED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
NEXT_SINGLE_TASK = REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
