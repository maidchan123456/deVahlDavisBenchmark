# Preregistration amendment 001 — baseline convergence qualification

The v1 registration stays immutable (JSON SHA256: 567af0e99595d20cb6aeecc99788c4d4b7d36e2f5f33bec05dc4093bde07d0e3). Previous STOP: zero-source Ra30000/grid20 baseline did not reach the original1e-8 steady conditions by12000.

This authorizes only continuation from verified12000 fields to checkpoints15000,18000,24000,30000, at the same numerical conditions. Only startFrom latestTime and endTime change; no tolerance, relTol, relaxation, scheme, mesh, physics, BC, source, binary, monitor or QoI definition changes. All original stopping thresholds/windows/sample/confirmation requirements remain. No cold start, no other Arm1 tolerance, Arm2,40/80 grid, temperature diagnostic or formal benchmark.

The companion JSON fixes all classification cutoffs before execution. Last3 checkpoint medians of final2000-iteration nonoverlapping200 windows classify continuing decay (strict decline and<=0.5 ratio/log-fit ratio), plateau (within factor2 and log-fit ratio0.8..1.25), or coherent oscillation with repeated ACF/sign reversal evidence. Missing/zero/mixed evidence is inconclusive; no artificial log floor. These numerical diagnostic cutoffs are not research quotas or replacement steady criteria.

Original compiled monitor confirmation needs sustained qualification for200 iterations, plus original equation residual/finite/normal-exit checks. Additional200 confirmation is permitted if required, at most30200 for first qualification at30000. Stop upon accepted numerical baseline; otherwise finish at30000, retaining NOT_CONVERGED. Restart monitor warmup is unavailable evidence, not a passed window. Each checkpoint is saved before the next call; prior outputs and original run remain unchanged.

Provenance:12000 U/T/p_rgh/phi match saved SHA256, all restart fields/mesh/input and registered source hashes are checked. Same logged binary path with build timestamp preceding the original run is used without rebuild; its current hash is frozen. A prior binary SHA256 was not saved, so historical binary identity is supported by source/path/build provenance, not a nonexistent past digest. Exact evidence appears in JSON.

STOP on invalid provenance, changed numerical input/binary/mesh/physics, NaN/Inf/fatal, need for formal data/original registration edits/non-baseline solver calls. This amendment is immutable after the first continuation call. Quota, tau_mean and formal status remain unresolved/unchanged. Linear precision as primary cause is not inferred without a contrast experiment.
