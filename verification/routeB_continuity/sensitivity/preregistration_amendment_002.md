# Preregistration Amendment 002 — Additional Restart at Iteration 15000

This diagnostic estimates only the effect of adding a process termination/write-read/reinitialization bundle at15000. Both branches share the existing12000 state and its restart. It does not estimate restart in general.

## Design fixed before execution

Ra_test30000,20×20×1,zero source; p tolerance1e-10, U/T1e-12,relTol0. All numerical inputs, BC, mesh, source, solver source/binary, native monitor/QoI definitions and original steady criteria are frozen. Only copied controlDict startFrom/latestTime and endTime are edited. No Arm1/Arm2 continuation, other grids, stock equivalence repeat, formal benchmark data or solver execution.

C:12000→18000 in one process. R:12000→15000 normal exit, then15000→18000 in a fresh process. Execution order R first half,C,R second half, exactly three solver calls. Completed C writes are archived while stdout is read, without stopping C; at15000 all four fields must match R before accepting any post-factor comparison. All restart fields including alphat,p,uniform/time and all parent inputs are checked against recorded provenance.

## Canonicalization and comparisons

Raw whole-file SHA256 is always retained. Numerical hash: sorted compact UTF8 JSON metadata (field, dimensions, patch types/value origins and block shapes), NUL, ordered little-endian Float64 numerical arrays; no rounding. Internal values first, then hotWall,coldWall,bottomWall,topWall,front,back. Expand physical patch values to20 entries; for zeroGradient without stored values use the adjacent owner internal values from the verified common mesh and label that implicit origin. Preserve vector x/y/z order, record empty patches as zero-length arrays. Include fixedFluxPressure stored uniform/nonuniform scalar gradients in the hash. For a raw-only mismatch, prove all non-header tokens identical after excluding comments/formatting; otherwise STOP at15000.

U max/RMS use Euclidean vector norms; T/p/phi max/RMS use scalar differences, over internal plus represented physical boundary values. Also retain internal-only differences, pressure absolute units/scale and phi L1. Reference scales are frozen from12000: max internal speed, DeltaT1K, centered pressure internal RMS, characteristic face flux Up*(L/20)*depth. Report gradients separately and never subtract a different pressure gauge.

At18000 compare seven existing QoIs; value relative difference is abs(R-C)/abs(C), positions absolute nondimensional. Zero denominator yields null, with absolute difference retained. Compare epsilon_phi_mean/max and heat imbalance plus audit/closure. Capture intermediate written fields if available; no reconstruction.

## Windows and reference magnitudes

Both branches use the original11-sample/200-iteration window and20-iteration sample interval. For matched branch variation use15240–18000: this excludes R's15020 restart sentinel and incomplete windows. Report min/median/max/P95 for QoI ranges, U/T change window maxima, heat ranges and epsilon levels/ranges. The native monitor is unchanged.

Prior reference magnitudes are the median of previously saved late-checkpoint amplitude medians at18000/24000/30000; their exact values and scales are frozen in the JSON. Endpoint and trajectory difference/reference ratios are diagnostic, never acceptance thresholds. Position reference zero yields null; no invented floor. Epsilon reference uses level, not variation amplitude; no prior pressure/phi band is fabricated.

## Interpretation and stopping

With verified12000 and15000 equality: nonzero18000 fields -> DETECTED; exact identical numerical payloads/all-zero field differences -> NOT_DETECTED (endpoint). Insufficient provenance/setup/resolution -> INCONCLUSIVE. Detection and magnitude do not establish a primary cause. The latter remains INCONCLUSIVE for this single3000-iteration comparison.

Continuous-band presence is a descriptive decimal-order label: nearest power-of-ten of median C max value-QoI window range equals that of the fixed prior reference, with nonzero values. All exact ratios are shown; this does not change any scientific acceptance or steady criterion. If the continuous branch retains this band, the additional15000 restart is NOT_SUPPORTED as its necessary condition within this interval. A missing band alone does not establish necessity.

Trajectory diagnostics retain first nonzero/first/last/max, early15020–15200 and late17800–18000 medians/ratios, and exact-zero counts. Describe zero, decay, amplification or persistent irregular response without a new PASS cutoff. Serialization and solver reinitialization are treated as one bundle.

Immediate STOP on parent/branch/pre-restart numerical mismatch, binary/source/settings mismatch, NaN/Inf/fatal/abnormal target, or need for formal data, existing preregistration changes or another factor. Preserve partial evidence. Existing v1/amendment001 and results are immutable. Quota/tau remain unresolved; Candidate B remains PROVISIONAL and formal Ra1e3 Gate G remains FAIL (declared prior state, no formal reevaluation). Stop after this diagnostic; a tolerance study belongs to a separate user decision.

## Immutable registration

The companion JSON records exact parent hashes, solver digest, driver/analysis digests, scales, reference magnitudes and startup provenance hash. Both amendment hashes are saved before the first solver call, checked before every call and after analysis, and never edited after execution.
