# Route A Co0.25 plain transient production preparation

**READY. Preparation only; CFD executed:NO, authorization:NO.** ID:co025_20261006_2117. One future Ra1e6/Pr0.71/160×160×1/12-rank continuous cold-start series targets native endTime1420 / t*≈2. No physical step, pilot, rerun, Q3, GateJ,320 grid or particle coupling was executed.

Co0.5 reference integrity PASS: original cold inputs, installed binaries/sources, canonical authority hashes and all report/execution/postprocessing seals matched. Reviewed HEAD:a1a016f48291bb1678d052e957162c5756b5dd72. Local Git range from83a910 added376 result files and changed.gitignore only to ignore log.foamRun; the full untracked3.870570559GB native log was independently hash-verified. HEAD provenance is distinct from input integrity. Future reviewed results-only descendant commits may proceed after byte verification; sensitive/unknown changes fail closed.

The164-file cold/decomposed input audit found exactly one differing file,system/controlDict, containing only maxCo0.5→0.25. Physical and thermophysical inputs, mesh, initial fields, fvSchemes, fvSolution, backward time scheme, PIMPLE, linear solvers, initial dt,maxdt,endTime and native output policy are byte-identical. No source runtime trajectory was copied. Frozen Co0.5 scotch12 decomposition was reused byte-identically; serial/12-rank checkMesh PASS, addressing covers25600 cells exactly once, pRefPoint lies strictly within rank3/local2107/global12719. Native MPI12 affinity probe confirms12 distinct physical cores and all thread settings1; no scaling study.

Future exact command (through prepared launcher after a separate explicit run-task receipt; do not execute in this preparation):

```bash
mpirun --nooversubscribe --map-by core --bind-to core --report-bindings -np 12 foamRun -case /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/plain_transient_co025_production/co025_20261006_2117 -solver fluid -noFunctionObjects -parallel
```

OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. Heavy/exact/matrix/replay/audit backends OFF; functions{} and-noFunctionObjects. Cold0 is300K and zero velocity; same hot300.5/cold299.5 walls. Ra1e6,Pr0.71,L0.1m,depth0.001m,rho0=1,beta0.001,mu1e-5,Cv1000,nu1e-5,alpha=1e-5/0.71,k0.014084507042253521,g=(0,-140.8450704225352,0), Boussinesq/eConst/Stokes/Fourier/laminar remain unchanged. PIMPLE24 outer/2 correctors/0 nonorthogonal; U/e PBiCGStab+DILU and p_rgh PCG+DIC tol1e-12/relTol0 retain actual maxIter dictionaries, with no relaxation/tuning.

Native adaptive control: backward variable-step BDF2, adjustTimeStep true, maxCo0.25,growth1.2, initial dt2.3111979166666666e-5 unchanged,maxdt0.027734375 unchanged. Co is logged before next-dt adjustment; configured maxCo is not a strict bound on the pre-adjustment printed value. Future offline checks must retain logged values and audit controller alignment. Inference from Co0.5 late Co≈0.5/dt≈0.009929812304467326 predicts late dt≈0.004964906152233663; actual Co0.25 trajectory is unknown. Cold growth regime and transition may differ. Primary scientific stop is native endTime1420 only, not step count or steady-looking behavior. Native final step may be slightly above/below1420 under its half-dt predicate; actual uniform/time values and all-rank final fields must agree.24h guard; interruption STOP_AND_REVIEW with no automatic restart/cold rerun.

Regular output unchanged: runTime5s,ASCII,no compression,timePrecision12,writePrecision17,purgeWrite0. Output never changes dt. Supplemental startup sampling changes only IO: Co0.5 actual physical times [6.1015624999999994e-05, 0.00020638812499999996, 0.0007199478241999998, 0.005177674989526768, 0.03277874664020242, 0.16913457753608538, 0.7514609745502908, 1.4855724052851276, 2.928096339318585, 4.707987914233269], plus first maxdt if reached and first Co-control event. Native SIGUSR1 is sent only to verified rank0 after logged handler activation. Multiple triggered targets can share one request; asynchronous actual saved times/indices must be audited. Maximum12 additional requests plus284 regular bins gives≤296 saved output states, pluscold0. No step-index matching is used for scientific history comparison.

PLANNING estimates:280k–300k steps, central286406; inverse-flux integration on frozen Co0.5 saved log states gives≈286353.355. This is not a Co0.25 controller/trajectory simulation. Runtime4–6h, central4.667110h from measured Co0.5 average; pressure cost fell from early1000 median2383 to late median35 iterations/step, so Co0.25 cost remains uncertain. Planning values are not stopping limits.

MEASURED Co0.5 log bytes/step=27028.557775. Native fields≈2.962GB at≤296 snapshots; extra steps mainly grow logs.

| planning steps | projected log | fields+log+markers+offline budget | runtime at Co05 mean cost |
|---:|---:|---:|---:|
| 280000 | 7.568 GB | 11.008 GB | 4.563 h |
| 300000 | 8.109 GB | 11.555 GB | 4.889 h |
| 320000 | 8.649 GB | 12.101 GB | 5.215 h |


Minimum32GiB free prelaunch and8GiB runtime low watermark retained. Conservative320k estimate plus25% margin plus low watermark=22.088GiB<32GiB. Measured prepared-host free space=729.027GiB. Storage PASS; no purge/thinning is planned. Launcher validates cold fileset, dictionaries, binaries/source/PATH/library identity, MPI version/binding policy, source authorities, no active same-case solver, unused execution namespace, RAM/disk, package hashes and separate explicit authorization. NO draft cannot authorize production; fail-closed negative checks PASS.

Offline comparison command after normal completion: `/usr/bin/python3 -B /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co025_production/co025_20261006_2117/postprocess_and_compare.py --execute`. First reconstruct all fully saved fields using the unchanged prepared Co0.5 postprocessor. Match physical time/t*,never step index. Piecewise linear interpolation uses union of both saved t* axes and overlap endpoints/late boundary, with extrapolation:NO; record actual common time range. Report direct final signed/absolute/relative Nu_hot,Nu_cold,Umax,Wmax differences and final-native time mismatch; maximum/sample-RMS/time-weighted-RMS histories, last10% common-window differences, final U/W/theta profile RMS/Linf. Sparse output interpolation does not measure unsaved extrema. Retain same-grid end_9000 steady comparison. Last10% and≥5 snapshots uses range/slope with descriptive0.001 threshold for STATIONARY_CANDIDATE/STILL_EVOLVING; it is not a stationarity proof.

Mass/energy follow the same coverage-limited method: native rho-volume mass, Cv*(T−298.15) sensible proxy, kinetic energy, wall heat, coarse saved-state secants and native continuity. Missing native intermediate/e-K histories prohibit exact BDF conservation certification. Original source/postprocessing evidence remains unchanged. Dry checks verified analytic coldNu160/U=W=0, zero Co0.5 self-comparison, staggered linear interpolation, no extrapolation and fail-closed sensitive/draft/rank/maxCo guards. Preparation-only corrections are documented in preparation_dry_corrections.json.

This two-level study can describe fixed-grid sensitivity; it cannot prove full temporal convergence/time-step independence. If measured final/late QoIs, profiles or resolved transient histories materially differ (descriptive0.1% trigger, not formal acceptance), or sensitivity remains unresolved, review whether Co0.125 is useful after excluding sampling/horizon uncertainty. Co0.125 is not predetermined or authorized. Formal statuses stay frozen.

Next exact task:RUN_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION, recommended gpt-6.1-sol/high. User decision required:YES. Production has not started.

```text
ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION_PREPARATION = COMPLETE
PRODUCTION_PREPARATION_ID = co025_20261006_2117
SOURCE_CO05_PRODUCTION = co05_20261006_0602
SOURCE_CO05_STATUS = COMPLETE
SOURCE_CO05_FINAL_TSTAR = 2.000006172635985
CURRENT_REVIEWED_HEAD = a1a016f48291bb1678d052e957162c5756b5dd72
PRODUCTION_SENSITIVE_HEAD_CHANGE = NO
PHYSICAL_MODEL_CHANGED_FROM_CO05 = NO
GRID_CHANGED_FROM_CO05 = NO
FVSCHEMES_CHANGED_FROM_CO05 = NO
FVSOLUTION_CHANGED_FROM_CO05 = NO
TIME_SCHEME_CHANGED_FROM_CO05 = NO
PIMPLE_POLICY_CHANGED_FROM_CO05 = NO
LINEAR_SOLVER_POLICY_CHANGED_FROM_CO05 = NO
OUTPUT_POLICY_CHANGED_FROM_CO05 = AUXILIARY_STARTUP_SAMPLING_ONLY: physical-time targets plus first cap/Co-control; native dictionaries identical
MAX_CO_CO05 = 0.5
MAX_CO_CO025 = 0.25
INTENDED_NUMERICAL_DIFFERENCE = MAX_CO_ONLY
RA = 1e6
PR = 0.71
GRID = 160x160x1
MPI_RANKS = 12
MPI_DECOMPOSITION = scotch
PREF_REFERENCE_METHOD = pRefPoint
PREF_POINT = (0.0496875 0.0496875 0.0005)
TIME_SCHEME = backward_variable_step_BDF2
INITIAL_DELTA_T = 2.3111979166666666e-05
MAX_DELTA_T = 0.027734375
END_TIME_SECONDS = 1420
TARGET_TSTAR = 2
PRODUCTION_START_MODE = CONTINUOUS_COLD_START
STRICT_BDF_RESTART_RELIED_UPON = NO
HEAVY_DIAGNOSTICS_ENABLED = NO
FUNCTION_OBJECTS_DURING_PRODUCTION = NO
OUTPUT_WRITE_CONTROL = runTime
FULL_FIELD_OUTPUT_INTERVAL_SECONDS = 5
OUTPUT_POLICY_CHANGES_DELTAT = NO
EXPECTED_PRODUCTION_STEPS = 280000–300000; central286406, frozen-Co05-state proxy286353; unmeasured Co025
EXPECTED_PRODUCTION_RUNTIME_HOURS = 4–6; central4.66710967995 at Co05 mean cost
EXPECTED_OUTPUT_BYTES = 11182828096
EXPECTED_OUTPUT_BYTES_PLANNING_RANGE = [11007674274, 11554517302]
CONSERVATIVE_320K_OUTPUT_BYTES = 12101360330
DISK_CAPACITY_PASS = YES
CHECKMESH = PASS
DECOMPOSITION_PREPARATION = PASS
PREF_POINT_MAPPING_VERIFIED = YES
CO05_TO_CO025_INPUT_DIFF_AUDIT = PASS
POSTPROCESSING_PLAN_PREPARED = YES
CO05_VS_CO025_TSTAR_COMPARISON_PREPARED = YES
PRODUCTION_LAUNCHER_PREPARED = YES
PRODUCTION_LAUNCHER_DRY_VALIDATED = YES
PRODUCTION_CFD_EXECUTED = NO
PRODUCTION_EXECUTION_AUTHORIZED = NO
Q3_EXECUTED = NO
FORMAL_GATE_J_EXECUTED = NO
CO025_PRODUCTION_PREPARATION_READY = YES
BLOCKER = NONE
NEXT_SINGLE_TASK = RUN_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / high
USER_DECISION_REQUIRED = YES
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
```
