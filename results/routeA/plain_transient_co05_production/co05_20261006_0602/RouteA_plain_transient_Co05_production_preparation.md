# Route A Co0.5 production preparation

**COMPLETE; CO05_PRODUCTION_PREPARATION_READY=YES; PRODUCTION_EXECUTION_AUTHORIZED=NO.** PreparationID:co05_20261006_0602. No foamRun invocation, pilot, physical timestep, Q3 or GateJ was executed. The new case and12 native processor cases contain cold0 only; the execution namespace is absent.

Frozen HEAD:f57d60d85e36ea9928e4bc481d3cbde586496f58. Both specified authority hashes match. The complete2982-file late_20261006_0531 seal and selected source/baseline/input hashes were reverified. Physical inputs, original160×160×1 mesh, cold fields, fvSolution/fvSchemes and scotch12 policy are frozen. Only the inherited controlDict endTime and output cadence were changed. The authority and all historical cases/results remain unmodified.

Case:/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/plain_transient_co05_production/co05_20261006_0602

Exact future command (cwd=/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/plain_transient_co05_production/co05_20261006_0602, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1):

```bash
mpirun --nooversubscribe --map-by core --bind-to core --report-bindings -np 12 foamRun -case /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/plain_transient_co05_production/co05_20261006_0602 -solver fluid -noFunctionObjects -parallel
```

Ra1e6,Pr0.71,0.1×0.1×0.001m, original Boussinesq/eConst/Stokes/Fourier, backward variable-step BDF2, nOuter24,nCorrectors2,nNonOrthogonal0,momentumPredictortrue,simpleRhofalse,transonicfalse,consistentfalse and original tight solver dictionaries remain unchanged. maxCo0.5,initialinputdt2.3111979166666666e-5,maxdt0.027734375,growth1.2,adjustTimeSteptrue. The first native controller update can grow the input dt, as it did in the pilot; no new timestep policy is imposed.

Non-CFD checkMesh passed both global and12-rank parallel. Native scotch decomposition covers25600 global cells once, with884 processor-interface face pairs of opposite orientation. Exact prior MPI flags were verified with a12-rank non-CFD affinity probe:each rank has a distinct physical core, with both SMT siblings included by native core binding. Thread counts are1. Reference point(0.0496875,0.0496875,0.0005) maps uniquely inside rank3/local2107/global12719, away from cell planes; no parallel pRefCell is used.

Production ends by native endTime1420 (targett*=2), continuously from cold rest. There is no timestep-count cap, pilot continuation, online stationarity termination, retry, or strict restart dependency. Expected~180000–200000 steps and~6.1121h are late-window projections, not promises or stop limits. The operational guard is24h. Interruption/fatal/nonfinite output/low disk/observer failure/partial final output => INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN, STOP_AND_REVIEW, preserve evidence, await a separate reviewed restart or explicitly authorized fresh cold rerun. Native missing e/K histories preclude a strict-BDF restart claim.

Output:runTime5s, no compression,purgeWrite0,writePrecision17,timePrecision12. Native naming precision may increase automatically.284 regular snapshots plus at most10 native startup write requests =294 output snapshots; cold0 is additional. Startup requests target2,5,10,20,30,39,60,100,250,500, from the preceding Time header using SIGUSR1 after native handler/master verification. Actual saved times/indices are reviewed after execution. Signals only request writes; no dt alteration or normal-end stop signal is used.

Disk estimate:2,943,123,456 allocated field bytes plus5,394,465,552 log bytes =8,337,589,008 bytes (~7.77GiB), with small launcher metadata and offline tables extra. Up to42336 field/state files +1 complete combined stdout/stderr log +5 execution metadata files =42342; postprocessing adds its own CSV/JSON files. Measurement uses actual12-rank late-pilot ASCII snapshots and native log bytes per step. Prelaunch32GiB reserve and runtime8GiB low-watermark passed (~737GiB free). The 2/5/10s comparison and early-time sampling rationale are in output_cadence_decision_ledger.md/json.

Final state:ordinary runTime bin284. The native Time.running threshold and runTime write bin use t+0.5dt;1420 is exactly5×284. foamRun calls runTime.write after postSolve before the next termination check. maxdt is much smaller than the output interval, so no bin is skipped. Installed source and3million non-CFD boundary arithmetic evaluations verify the method. No writeAtEnd option is assumed. No adjustableRunTime or exact-time timestep adjustment is introduced. Final actual t can lie near1420 in [1419.9861328125,1420.0161783854167); actual high-precision uniform/time.value and t* are reported. Native normal completion must have matching12-rank final fields, matching finalindex/completedstep, and satisfy both termination and write-bin conditions.

Launcher:/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/run_production.sh. Dry command:`/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/run_production.sh --check`. It verifies HEAD, authority/source hashes, every input/decomposition file and exact file set, binary/native source and launcher hashes, runtime environment/PATH/libfluid resolution,12/scotch,pRefPoint,output/end/dt/precision/functions policy,cold0-only state, disk/RAM, no same-case solver, and unused execution namespace. Future --execute additionally requires a separate AUTHORIZED=YES receipt tied to plan/input hashes and explicit user instruction. The current draft is AUTHORIZED=NO and rejection was tested before Popen. This task does not authorize changing that flag.

It keeps full stdout/stderr, command/start/end/host/PID/returncode/bindings in native log, monotonic step markers, startup signal requests, completed steps and final saved times. Low-cost log monitoring catches fatal/nonfinite/FPE; disk is checked every10s. A separate24h timer and interruption handling stop the launched process tree. There is no field-reading diagnostic during timestepping. The empty functions dictionary and -noFunctionObjects plus frozen native binary protect the plain run; heavy/full-audit/exact-evidence libraries are absent.

Postprocessing script/plan:/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/production_postprocessing_plan.md and postprocess_production.py. Offline reads give Nu_hot/cold(t), benchmark centreline Umax/Wmax(t), physical time/t*, velocity/temperature profiles, symmetry, reconstructable mass/energy descriptors, and dt/Co/iterations/residuals/continuity/native and external wall timing. Compare final160² state with Route A end_9000 baseline without assuming agreement; assess late range/slope for stationary-candidate versus still-evolving behavior. Stored-state energy secants are coverage-limited descriptors, not a native BDF/full conservation certificate. Existing final pilot Nu_hot and speed were reproduced; its598-step log was parsed offline with48pressure/24energy solves perstep. Analytic cold0 velocity and wall-gradient Nu were checked. A floating-point centre sorting issue was corrected using integer lattice indices, with no physics change.

Dry validation passed:complete preflight, actual newly prepared cold field tamper rejection with byte-exact restoration, HEAD mismatch, pre-existing execution namespace, draft-NO pre-Popen rejection, native log/fatal parsing, final-write source arithmetic, offline field/log postprocessing. Historical status is retained:

```text
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
```

No git add/commit/push/reset/checkout mutation was used. git_status_final.txt and git_diff_stat_final.txt record the final state. Existing15 historical untracked case directories remain; only the new case/results preparation namespaces were added, and tracked diffstat is empty. Hash seal excludes itself and otherwise covers all preparation artifacts.

The next single task is RUN_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION with gpt-6.1-sol / high after an explicit production instruction from the user. Preparation is complete and this task stops here.

```text
ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION_PREPARATION = COMPLETE
PRODUCTION_PREPARATION_ID = co05_20261006_0602
SOURCE_LATE_PILOT = late_20261006_0531
CANONICAL_AUTHORITY_HASH_VERIFIED = YES
FORMAL_AUTHORITY_HASH_VERIFIED = YES
PHYSICAL_MODEL_CHANGED = NO
NUMERICAL_POLICY_CHANGED = NO
GRID = 160x160x1
RA = 1e6
PR = 0.71
MAX_CO = 0.5
MPI_RANKS = 12
MPI_DECOMPOSITION = scotch
MPI_BINDING_VERIFIED = YES
PREF_REFERENCE_METHOD = pRefPoint
PREF_POINT = (0.0496875 0.0496875 0.0005)
PREF_POINT_MAPPING_VERIFIED = YES
TIME_SCHEME = backward_variable_step_BDF2
INITIAL_DELTA_T = 2.3111979166666666e-05
MAX_DELTA_T = 0.027734375
END_TIME_SECONDS = 1420
TARGET_TSTAR = 2
TIME_PRECISION = 12
WRITE_PRECISION = 17
HEAVY_DIAGNOSTICS_ENABLED = NO
EXACT_EVIDENCE_BACKEND_ENABLED = NO
FUNCTION_OBJECTS_DURING_PRODUCTION = NO
PRODUCTION_START_MODE = CONTINUOUS_COLD_START
STRICT_BDF_RESTART_RELIED_UPON = NO
INTERRUPTION_POLICY = STOP_AND_REVIEW
OUTPUT_WRITE_CONTROL = runTime
FULL_FIELD_OUTPUT_INTERVAL_SECONDS = 5
OUTPUT_POLICY_CHANGES_DELTAT = NO
EXPECTED_FULL_FIELD_SNAPSHOTS = 284 regular + up to10 startup =294 upper bound, cold0 additional
EXPECTED_OUTPUT_BYTES = 8337589008 fields+log estimate; small metadata/postprocessing extra
EXPECTED_OUTPUT_FILES = 42336 field/state files +1 log +5 metadata =42342 upper bound; postprocessing additional
DISK_CAPACITY_PASS = YES
FINAL_STATE_WRITE_METHOD = NATIVE_RUN_TIME_BIN_ENDTIME_MULTIPLE(bin284)
FINAL_STATE_WRITE_VERIFIED_BY_SOURCE_REVIEW = YES
CHECKMESH = PASS
DECOMPOSITION_PREPARATION = PASS
PRODUCTION_LAUNCHER_PREPARED = YES
PRODUCTION_LAUNCHER_DRY_VALIDATED = YES
POSTPROCESSING_PLAN_PREPARED = YES
EXPECTED_PRODUCTION_STEPS = ~180000-200000 planning only, not a stopping rule
EXPECTED_PRODUCTION_RUNTIME_HOURS = ~6.1 (late-window projection, not guarantee)
PRODUCTION_CFD_EXECUTED = NO
PRODUCTION_EXECUTION_AUTHORIZED = NO
Q3_EXECUTED = NO
FORMAL_GATE_J_EXECUTED = NO
CO05_PRODUCTION_PREPARATION_READY = YES
BLOCKER = NONE
NEXT_SINGLE_TASK = RUN_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / high
USER_DECISION_REQUIRED = YES
```
