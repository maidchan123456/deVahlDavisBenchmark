# Route A U04 diagnostic observation, v1.2

This directory builds isolated diagnostic clones and a native synthetic driver.
`run_u04_verification.sh NEW_DIRECTORY` performs **only** diagnostic builds,
native in-memory fixtures, fail-closed replay, injected failures, and a read-only
resource estimate. It never executes foamRunDiagnostic, blockMesh, initialization,
a physical benchmark case, or CFD time evolution. Synthetic metadata explicitly
says SYNTHETIC_EVALUATOR_TEST, NOT_CFD_RESULT, NOT_DIAGNOSTIC_TRANSIENT_EXECUTION.

## Source connection and isolation

`overlay/` is generated from hash-verified native v13 source and the immutable
v1.1 stage plan. Erasing observation blocks and identity `tmp` taps restores the
original tokens before mechanically renaming diagnostic module/class identifiers.
All native ddt/div/pressureWork/divq/model/gravity operators remain once in their
original expression tree; C++ unspecified term evaluation order is accepted
within one assembly, while missing/duplicate terms are rejected.

The actual fluid/isothermalFluid clones and foamRunDiagnostic are compiled.
The Fourier template provider is compiled from the actual native transport
instantiation against the local instrumented Fourier.H/C. Its isolated library
retains the native provider SONAME to satisfy dependent native libraries exactly
once; it exists only in the isolated build directory. Loader provenance verifies
that provider. No installed source/library/binary is overwritten. The native
module methods are not executed against a CFD case in this task: connection
proof is source token restoration + compilation/linkage + native-object callbacks.

## Read-only capture

The observer copies native coefficients, source, internal/boundary coefficients,
actual BC flags, dimensions, mesh addressing/volumes, and current fields. Original
fields/matrices are never solved, relaxed, constrained, assigned, BC-updated,
thermo-corrected, or history-updated by the observer. A field's existing oldTimes
are copied privately without calling original oldTime(). Native oldTime storage
`timeIndex` can advance without changing historical values; raw storage clock,
object epoch, history level/value hash, and represented epoch are distinct.
Missing/null history is explicit. History is never fabricated for observation.

Matrix coefficients/BC epochs are immutable assembly snapshots. The snapshot's
native psi reference is used at post-solve evaluation, and that actual evaluation
field is also copied/exported. No second equation is assembled. Empty/diagonal
matrices receive zero scratch coefficient allocations only in private copies;
native `residual=b-Apsi` is negated and integrated units never receive another V.
Positive Fourier child operators are observed under the original native minus
signs. Nonzero fvModels matrix sources fail the registered wrong-model guard.

Stages cover constructor, preSolve/control/time, all24outer and2pressure solves,
density/energy before and after solve, no-op relaxation, thermo correction, EOS
copies, pressure reference before/after and solved physical/referenced residuals,
continuity, and postSolve. One ordinary nonorthogonal solve has index1 although
there are0 *additional* nonorthogonal correctors. StageLedger enforces this graph.

## Export/replay

17-significant-digit JSON preserves IEEE double roundtrip and signed zero. Every
payload/file has SHA256, with case/study/source/instrumentation/field/oldTime/BC/
matrix/time/corrector identities. Exclusive temporary write, fsync, no-overwrite
atomic hardlink publish, directory fsync, and fsynced manifest commit prevent
accepting partial writes. A completed hashed manifest is mandatory. No repair,
record filling/dropping, overwrite, or continuation on evaluator failure.

`replay_evaluator.py STREAM GUARD SOURCE_SHA INSTRUMENT_SHA` checks all identities
and ordering, replays frozen stored matrix actions including actual boundary
coefficients, term sums, Fourier children, variable-step polynomial derivatives,
reference additions and rho synchronization. Offline end-state mass/energy
calculations remain distinct from assembly residuals. End energy uses captured
native coefficient/old products, mesh Gauss linear weights, actual composite
p/rho boundary values, Cv/g, and Fourier affine-reference identity under the
frozen static constant-property model; different geometry/history/thermal BC
values/affine reference fail. No additional native operator or BC update is made.
The original e reference is retained. Defects and floors are diagnostics and
never conservation PASS/FAIL evidence.

## Authority and practical limits

Build provenance pins native dependency graph, implementation/schema/overlay,
compiler flags/commands/environment, isolated binaries, linked libraries, and
actual loader paths. Verification refuses drift before invoking the synthetic
binary. Two observed runs must match bitwise (including manifest/export), and
OFF/ON physical fingerprints include all captured scalar histories, U/phi,
geometry, BC flags, matrix coefficients/sources, native residuals, time and
actual native solve iteration counts. Cases A-H include stationary mass, known
histories/boundary signs, isolated storage/wall/gravity/pressure operators and a
mixed24outer/2pressure manufactured sequence on nonuniform2cell volumes. These
are evaluator fixtures; physical synthetic values are not the benchmark model.

The diagnostic module is built but not run. Future diagnostic invocation must
validate the sealed contract, build/library hashes and case inputs and set
ROUTE_A_DIAGNOSTIC_EXPORT_ROOT (new), ROUTE_A_DIAGNOSTIC_CONTRACT_FILE,
ROUTE_A_DIAGNOSTIC_GUARD_SHA256 (actual file SHA), SOURCE_SHA256,
INSTRUMENTATION_SHA256, CASE_ID with the full ROUTE_A_DIAGNOSTIC_ prefix.
Bootstrap reads the authority file and refuses a hash mismatch. This describes
interfaces, grants no run authorization, and supplies no production launch script.

Resource figures are PLANNING_ESTIMATE_ONLY, with Float64 numerical-payload
projection, not actual adaptive step counts, measured JSON size, runtime or CFD
floors. The registered24outer, cadence, durations, tolerances and U01-U03 remain
unchanged. Material resource concerns require a separate pre-run review.
