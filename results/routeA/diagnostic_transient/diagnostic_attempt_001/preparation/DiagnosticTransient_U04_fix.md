# DiagnosticTransient U04 fix

U04のみを完了し、診断契約v1.2を作成しました。U01〜U03は変更なし。
実CFD・case/mesh生成・初期化・formal Gate Jは実行していません。
resourceの重大な懸念を分離し、次taskは実行前のfeasibility reviewです。

## Parent and protected authority

Known/current HEAD `38349f12b33145514857178560f67355535b154a` matches. Parent v1.1 SHA256 `574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675`
verified before/after. Formal v1.7 SHA256 `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`
unchanged. 105protected files and27
initial native sources remain byte-identical. Frozen numerical/statistical/model
sections and diagnostic definitions/thresholds are equal in value and canonical bytes
(the two U04 evaluator_method_ready flags become true); all inherited numerical status
entries remain identical. Git tracked diff is empty; no add/commit/push.

## Implementation and actual connection

Repository-local native module clones were selected because they expose the exact
assembly/relax/solve/thermo/EOS/reference boundaries while leaving installed code
read-only.13native source transformations pass token restoration.14inherited
source sites plus added endpoint/term hooks are compiled. Actual native transport
instantiation resolves the local instrumented Fourier provider, verified by ldd.
Native clone methods were not executed on an actual CFD case; source structure,
compilation/linkage, and native-object hook callbacks establish the authorized
synthetic/native structural proof. See `source_stage_binding.json` and
`final/build/build_provenance.json` under `u04_verification`.

Read-only captures preserve unrelaxed energy and mass coefficient/source/BC
matrices, actual fields/history, solved psi epochs, native LHS-RHS, Fourier terms,
pressure pre/post-reference/solved physical matrices and EOS stages. Operator
expressions execute once in native association. Observer adds no BC/thermo/history
update. Existing oldTimes are privately copied; raw storage clock versus history
level/value/represented epoch are separate, including explicit null/startup states.
Current BC flags and immutable assembly coefficients are recorded separately.
Native residual is negated and integrated units are never multiplied by V again.

## End-to-end native evidence

Authoritative evidence is `u04_verification/final/` (fresh final source-pinned
build and verification). Earlier `u04_verification/build/` and `tests/` retain the
preceding verification. Final normalization follows the unchanged inherited
volume-weighted mean local L1; absolute global integral is separate.

| Check | Result |
|---|---|
| Native stream records |1152|
| Stored matrix action replays |715PASS|
| Mass/energy term sums |49/24PASS|
| Pressure reference identities |48PASS|
| EOS synchronization |PASS|
| Variable step h=0.1,k=0.2 constant/linear/quadratic |3PASS|
| Isolated storage/wall/gravity/pressure energy |4PASS|
| End terms versus native exported fixture/history |30PASS|
| Native/online/offline/atomic intentional failures |18FAIL CLOSED|
| OFF/ON physical state/matrix/source/BC/history/time/iterations/residual |BITWISE|
| Two observed exports, manifests, summaries, stage sequence |BITWISE|

Cases A-H are covered by stationary mass, manufactured histories, inward/outward
boundary flux, isolated D-G terms and mixed24outer/2pressure sequence on native
nonuniform2cell V=1,2. No disk case is created.121native linear solves occur per
healthy synthetic sequence. Existing v1.1 75native/12policy/14anchor evidence is
reused, untouched and not re-evaluated or redesigned.

Independent end audit compares S_e,H_out,W_g,W_p against actual isolated native
end operators, F_e/F_K against matching last native assembly, and24actual S_K
outputs against captured old products/effective native intervals. This verifies
end reconstruction without a second assembly of the observed solver equation.

## Synchronization, defects and interpretation

Synthetic M_before=3.0382500000000001,
M_after=2.9999402548698511,
deltaM=-0.038309745130149175.
C mass residual is about-3.76e-15kg/s, whereas synchronized end residual is
about-0.5108kg/s in this manufactured fixture. Their difference equals a*deltaM/h
within product-based arithmetic allowance. rho_s-rho_T becomes zero by assignment;
that is not mass conservation. The pressure defect equals (rho_C-rho_end)*gh.
Assembly energy residual is near stored-action floor while end defect is about
-3.0863W in the same synthetic sequence; the two are not conflated. All fixture
numbers are NOT_CFD_RESULT and say nothing about benchmark conservation behavior.

Maximum matrix replay defect=6.2172489379008766e-15;
maximum stored/replay allowance=1.0184130315356815e-11.
Per-record product-based bounds plus compensated sums are retained. No invented
large tolerance. Scope is SYNTHETIC_ONLY; actual CFD floors unmeasured. Mass/energy
hard thresholds remain DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION.

## Failures and development repairs

18intentional cases include missing/duplicate/reordered stages, nonfinite payload,
wrong dimensions/units/source/guard/history/BC/matrix/time/corrector identity,
partial orphan and missing completion. Native exceptions/abort return nonzero;
no completion/recovery/filling/dropping follows. Offline failures invalidate the
whole stream. Detailed final failures are in `final/tests/verification_summary.json`.

Development-only compile/link/serializer/history/empty-diagonal failures are
preserved in `development_failures/`. Repairs normalize only private scratch,
use the actual Cpv Internal API, explicitly serialize characters, distinguish
oldTime storage/value identity, preserve native cold-start zero prior interval,
and fix Python serialization/payload shape. No CFD attempt or numerical tuning.

## Resource and synthetic performance

PLANNING_ESTIMATE_ONLY:1141physical-stage records project to roughly9.70GB of
uncompressed Float64-equivalent diagnostic numerical payload per physical step;
minimum full-field payload is2.05MB/step. Inherited prospective h scales imply
200061/400122planning steps for primary Co0.5/0.25, total about5.83PB versus0.80TB
available. The2series maximum-step watchdog envelope is about38.83PB. These are
neither actual CFD counts nor measured JSON sizes/lower bounds; metadata,
compression and actual layout change bytes. Runtime is not extrapolated.

On this synthetic filesystem/run, observed=20.916s versus OFF=0.289s
(ratio=72.48); fsync/export dominates. One export stream is
19023111bytes. Aggregate maximum child RSS is
82612KiB; paired memory overhead was not measured.
No production performance claim. Frozen24outer/cadence/duration/tolerances remain
unchanged. Resource feasibility must be reviewed before RUN.

## Contract, readiness and limits

v1.2 JSON SHA256 `7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd`. Source set `57aacf0e9307d0810a89b6b118680e67b5e1d70214e209070197fa3709e12a58`;
instrumentation set `adb52dc1e68d638ff98f4ffebe4d51746e40f1abb873d71a758b86964ad8f3fc`. 810
native/dependency source hashes,41linked library
hashes and6isolated binary hashes frozen, with schema/replay/stage plan/overlay.
The complete evidence file manifest is `u04_verification/u04_artifacts_sha256.json`.
No self-hash is embedded in the contract.

U04 CLOSED; technical readiness YES; fixed-grid diagnostic scientific allowance
YES. Execution authorization remains false. Actual native CFD module behavior,
actual-CFD floor/conservation, coupling,320grid and all formal claims remain
unmeasured/unauthorized. Serial non-coupled static constant-property model only;
unsupported geometry/history/model/BC/epoch mismatches fail closed. Interruption
invalidates the primary stream; no resume or automatic recovery is implemented.

Next single task: **REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_FEASIBILITY**.
Recommended model: gpt-6.1-sol / medium. User decision required; stop before CFD.

## Final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_CONTRACT_FIX = COMPLETE
STUDY_OWNERSHIP = DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION
PARENT_DIAGNOSTIC_CONTRACT_VERSION = 1.1
PARENT_DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
PARENT_DIAGNOSTIC_CONTRACT_SHA256 = 574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675
U01_STATUS = CLOSED
U02_STATUS = CLOSED
U03_STATUS = CLOSED
U01_U03_CHANGED = NO
U04_STATUS = CLOSED
HOOKS_CONNECTED = YES
SOURCE_STAGE_BINDING_VERIFIED = YES
OLDTIME_BINDING_VERIFIED = YES
BC_EPOCH_BINDING_VERIFIED = YES
ASSEMBLY_STAGE_CAPTURE = YES
UNRELAXED_ENERGY_MATRIX_CAPTURED = YES
MASS_STAGE_CAPTURED = YES
RHO_SYNC_STAGES_CAPTURED = YES
PRESSURE_REFERENCE_CAPTURED = YES
TERM_EXPORT_IMPLEMENTED = YES
EXPORT_REPLAY_PASS = YES
STAGELEDGER_PASS = YES
MASS_EVALUATOR_UNIT_TEST = PASS
ENERGY_EVALUATOR_UNIT_TEST = PASS
VARIABLE_STEP_BACKWARD_TEST = PASS
FOURIER_OPERATOR_TEST = PASS
PRESSURE_REFERENCE_TEST = PASS
RHO_SYNC_TEST = PASS
FAILURE_PROPAGATION_PASS = YES
NON_INVASIVENESS_PASS = YES
NON_INVASIVENESS_LEVEL = BITWISE
REPEATABILITY_PASS = YES
EVALUATOR_FLOOR_CHARACTERIZED = YES
EVALUATOR_FLOOR_SCOPE = SYNTHETIC_ONLY
SYNTHETIC_EVALUATOR_TESTS_EXECUTED = YES
PRODUCTION_SOLVER_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
SOURCE_HASHES_FROZEN = YES
INSTRUMENTATION_HASHES_FROZEN = YES
DIAGNOSTIC_CONTRACT_CREATED = YES
DIAGNOSTIC_CONTRACT_VERSION = 1.2
RESOURCE_PLANNING_ESTIMATE_CREATED = YES
RESOURCE_FEASIBILITY_CONCERN = YES
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = YES
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = YES
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
DIAGNOSTIC_TRANSIENT_EXECUTED = NO
GRID_320_EXECUTED = NO
ROUTE_B_RERUN = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
NEXT_SINGLE_TASK = REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_FEASIBILITY
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
RESOURCE_FEASIBILITY_REVIEW_REQUIRED = YES
DIAGNOSTIC_CONTRACT_SHA256 = 7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd
```
