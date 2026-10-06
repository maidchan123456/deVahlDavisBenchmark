# Route A plain transient CFD MPI scaling pilot

COMPLETE — `plain_20261006_0710`. Plain native OpenFOAM13 fluid; heavy diagnostics and function objects OFF. Every primary condition completed30 steps with identical cold input except decomposeParDict. No production/Q3/GateJ execution.

Measured serial median **0.667612 s/step**; fastest MPI **12 ranks, 0.096146 s/step**, speedup **6.944**, efficiency **57.9%**.

| ranks | cells/rank | median s/step | mean | min | max | CV | speedup | efficiency | sampled peak summed RSS MiB | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 25600.0 | 0.667612 | 0.674380 | 0.586221 | 0.860380 | 0.0945 | 1.000 | 100.0% | 160.0 | PASS |
| 2 | 12800.0 | 0.378685 | 0.382842 | 0.331568 | 0.480866 | 0.0853 | 1.763 | 88.1% | 311.7 | PASS |
| 4 | 6400.0 | 0.194819 | 0.200637 | 0.176306 | 0.250840 | 0.0816 | 3.427 | 85.7% | 575.5 | PASS |
| 6 | 4266.7 | 0.153767 | 0.155456 | 0.142619 | 0.192375 | 0.0779 | 4.342 | 72.4% | 842.8 | PASS |
| 8 | 3200.0 | 0.121743 | 0.124346 | 0.113283 | 0.153643 | 0.0740 | 5.484 | 68.5% | 1117.4 | PASS |
| 12 | 2133.3 | 0.096146 | 0.097920 | 0.089695 | 0.119999 | 0.0758 | 6.944 | 57.9% | 1658.1 | PASS |

Primary: external monotonic completion-to-completion wall increments for steps6–30; native ClockTime is integer seconds in this build. Initialization excluded. First-step and all raw timing/logs retained. One final field write included; `timing.json/solver_only_ish` excludes step30. Worker RSS sampled every0.5 s; shared pages can be counted repeatedly.

| scenario | steps | serial hours / days | best MPI hours / days | best MPI <24h? |
|---|---:|---:|---:|---|
| t*=0.5 ideal maxDeltaT floor | 12800 | 2.374 h / 0.099 d | 0.342 h / 0.014 d | YES |
| t*=2 ideal maxDeltaT planning count | 51200 | 9.495 h / 0.396 d | 1.367 h / 0.057 d | YES |
| Co0.5 prior prospective planning count | 200061 | 37.101 h / 1.546 d | 5.343 h / 0.223 d | YES |
| Co0.25 prior prospective planning count | 400122 | 74.202 h / 3.092 d | 10.686 h / 0.445 d | YES |

**PROJECTED_FROM_SHORT_PILOT**: supplied step scenarios × measured median. These are planning estimates, not an adaptive-step count or production guarantee. Co0.25 is a supplied count scenario; Co0.25 CFD was not run.

## System and budget

Intel(R) Xeon(R) w5-2545;12 physical cores /24 logical CPUs; 62.04 GiB RAM. OpenFOAM13 build13-441953dfbb42, DP/Int32; OpenMPI4.1.6. Binding logs verify every primary MPI rank occupies a different physical core; OMP/BLAS/MKL thread counts1.

Primary solver wall sum 52.885 s; including decomposition 54.134 s. Preserved preliminary attempts 34.196 s plus cold-check last-completion 4.298 s. No600 s rank cap or3600 s total cap hit; no timeout retry. Post-run original-input and authority hashes unchanged; all current input hashes still match their preregistered manifests.

![Measured scaling and step cost](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/transient_cfd_scaling_pilot/plain_20261006_0710/scaling_and_step_cost.png)

## Scientific and execution contract

Ra1e6, Pr0.71,160×160×1; original Boussinesq eConst/Stokes/Fourier, cold rest and wall temperatures unchanged. Backward variable BDF2 native startup; nOuter24, pressure correctors2, nonorthogonal0, momentumPredictortrue, simpleRhofalse, transonicfalse, consistentfalse; U/e PBiCGStab-DILU and p_rgh PCG-DIC with tolerance1e-12, relTol0; rho diagonal1e-14; no relaxation or residual early-stop. maxCo0.5, growth1.2, inputdt2.3111979166666666e-5, maxdt0.027734375. Authority hashes match and original0/constant/system files remain unchanged.

Source case contains steady dictionaries, historical times and `0/uniform/time` with dt1. Copy only four cold fields U/T/p/p_rgh, full constant mesh/physical properties; make transient dictionaries from contract; exclude inherited time metadata and old function objects. No checkpoint or fabricated oldTime histories.

MPI scotch decomposition; `--nooversubscribe --map-by core --bind-to core --report-bindings`; one rank per physical core through12, OMP/BLAS/MKL threads1. OpenMPI default (local ompi_info): core for np<=2, NUMA for np>2. Exact commands and environment in each rank directory; CPU/MPI/OpenFOAM versions in environment.txt and executable/library hashes in binary_provenance.json.

## Reference-cell repair and preserved trials

Initial cell-ID reference trials preserved separately; rank4 failed before any physical timestep because pRefCell is master-local. Primary series uses proven identical global physical reference via pRefPoint for every rank. No timeout retry, tolerance or physics tuning.

Proof from source mesh: globalcell12719 centre=(0.0496875,0.0496875,0.0005). Native findRefCell.C treats pRefCell as rank0-local; pRefPoint searches physical location. All primary dictionaries use identical pRefPoint and pRefValue0. `reference_cell_proof.json` and final field sanity record the per-rank global-to-local mapping. The initial2rank pRefCell run is excluded because it selects a different global cell; initialserial/2rank/failed4rank trials remain under superseded_cell_reference_attempts.

## Timestep and field sanity

Final t=0.032778746640202423 s, t*=4.6167249e-05; dt grows from 2.7734375e-05 to 0.0054862364 s. Same dt and end time across ranks; all30 dt growth-limited. maxDeltaT is not yet reached (unconstrained startup would reach it near step38). Logged Co is preSolve previous-state Co; no end-state Co measurement or claim.

| ranks | max logged Co | Tmin / Tmax K | Umax m/s | Wmax m/s | offline Nu hot | U Linf difference vs serial |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 0 |
| 2 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 4.91e-15 |
| 4 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 1.52e-14 |
| 6 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 3.83e-15 |
| 8 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 1.47e-14 |
| 12 | 0.0035861631 | 299.63782719 / 300.36222358 | 0.00057913654 | 1.26e-24 | 44.18580617 | 1.35e-14 |

Offline Nu uses orthogonal wall-normal gradient from hot-wall adjacent cell with distance dx/2, normalized by L/DeltaT. Field comparison is gross pilot sanity, not scientific validation or bitwise equivalence. Every step executes exactly24 outer iterations,24 energy solves and48 pressure solves; no early outer convergence stop. No NaN/FPE/fatal in primary runs; detailed linear iteration counts, residuals and continuity errors are in per-rank files. Fixed24 is not a nonlinear convergence certificate.

## Cost evolution and interpretation

| ranks | median steps6–15 | median steps20–29 | late/early | trend | pressure iterations total/step min–max | energy iterations total/step min–max |
|---:|---:|---:|---:|---|---:|---:|
| 1 | 0.606136 | 0.722637 | 1.192 | INCREASING | [1064, 3527] | [3, 24] |
| 2 | 0.353127 | 0.406067 | 1.150 | STABLE | [1224, 3967] | [4, 25] |
| 4 | 0.185773 | 0.213241 | 1.148 | STABLE | [1237, 4011] | [4, 25] |
| 6 | 0.144891 | 0.164527 | 1.136 | STABLE | [1288, 4065] | [4, 25] |
| 8 | 0.115879 | 0.130654 | 1.128 | STABLE | [1272, 4112] | [3, 25] |
| 12 | 0.090485 | 0.102432 | 1.132 | STABLE | [1315, 3718] | [3, 25] |

Serial late/early median rises19.2%; best12rank rises13.2%. The best-rank descriptive15% threshold labels this STABLE, but a modest upward tendency is visible and constant-cost extrapolation remains uncertain.

Descriptive trend rule: late/early >1.15 increasing, <0.85 decreasing; final scheduled output excluded. This is not a confidence-tested trend. Mature flow and larger adaptive dt may increase linear iterations substantially.

12 ranks improve over8: **True**. 24 ranks were not tested. Not a priority: only12 physical cores; 24 shares SMT resources and halves cells/rank again. No24 run; mature-state behavior may change the recommendation.

The old exact-evidence proxy does not measure plain CFD and is not applicable. Plain CFD measured here is much faster; no matched instrumented/native mature-state pair was measured, so the complete causal overhead fraction is not established.

Previous rough steady estimate:0.85–9.2 s/step, central2.5 (`ROUGH_STEADY_BASED_PRE_ESTIMATE`); new serial is0.667612 (`ACTUAL_TRANSIENT_CFD_SHORT_RUN_MEASUREMENT`). This early cold window is faster than that rough range; it does not establish mature-flow cost.

Serial projects to1.55 and3.09 days for200061/400122. BestMPI is below1 day in this cold-window projection; for400122, later step cost2.25–11.23 times higher would imply1–5 days. This is a sensitivity calculation, not a measured mature-flow range.

## Planning sensitivity

For400122 steps, the24 h threshold is0.215934 s/step, about2.25 times the measured12-rank median. A1–5 day result would correspond to about2.25–11.23 times the current cold-window cost. This sensitivity is not a measured uncertainty interval.

## Next single task

`RUN_ROUTE_A_PLAIN_TRANSIENT_LATE_WINDOW_BOUNDED_PERFORMANCE_PILOT`: User-authorized bounded continuation with valid native oldTime histories through the maxDeltaT/Co-controlled regime, using12 physical-core ranks, at most1000 completed steps and600 s wall, with no automatic retry or extension. Obtain a later window and compare its step and linear-iteration costs before committing to production. This next run is not authorized by the present pilot receipt. No series was started.

## Limitations

- Single30-step trial per rank, no confidence interval or replicated statistical scaling claim.
- All conditions start at cold-rest. First5 excluded but entire trajectory remains startup; finalt*=4.6167e-5, not developed natural convection.
- Native ClockTime integer seconds; external monotonic end-log markers used. Small log-pipe/observer latency remains; native CPU time retained but not treated as wall timing.
- One scheduled final field write included in primary25 samples; secondary24 samples exclude final write.
- RSS is0.5s sampled sum of worker RSS, includes shared pages and may miss short peaks; not kernel maximum resident set.
- Initial cold check RSS unavailable due observer parser repair; final serial and allMPI RSS recorded with corrected descendant lookup.
- Pressure and energy linear residuals/24outer execution and gross field sanity do not certify nonlinear convergence, GateJ or scientific parallel equivalence.
- 12800/51200/200061/400122 are supplied planning step counts, not measured adaptive production counts; Co0.25 runtime uses the Co0.5 per-step proxy.
- Projected mature-flow pressure/energy iterations, CPU frequency/load, output cadence and MPI scaling can differ.
- No exact-evidence proxy contributes to these estimates.

## Artifacts

`rank_01/02/04/06/08/12`: log.decomposePar, log.foamRun, commands.json, environment.txt, timing.json (all30 steps), timestamp_markers.json, input_manifest.json, field_sanity.json, iteration_and_trend.json, isolated case and final fields. cold_check is the5-step launch check. Heavy diagnostic code never loaded or invoked. Source proof/manifests and authorization_receipt.json are separate.

## Final status

```text
ROUTE_A_PLAIN_TRANSIENT_CFD_MPI_SCALING_PILOT = COMPLETE
PILOT_ID = plain_20261006_0710
CANONICAL_AUTHORITY_HASH_VERIFIED = YES
FORMAL_AUTHORITY_HASH_VERIFIED = YES
PHYSICAL_MODEL_CHANGED = NO
NUMERICAL_POLICY_CHANGED = NO
HEAVY_DIAGNOSTICS_ENABLED = NO
EXACT_EVIDENCE_BACKEND_ENABLED = NO
ACTUAL_TRANSIENT_CFD_EXECUTED = YES
PRODUCTION_CFD_EXECUTED = NO
Q3_BOUNDED_CFD_QUALIFICATION_READY = NO
Q3_AUTHORIZED = NO
Q3_EXECUTED = NO
FORMAL_GATE_J_EXECUTED = NO
GRID = 160x160x1
RA = 1e6
PR = 0.71
RANKS_REQUESTED = 1,2,4,6,8,12
RANKS_COMPLETED = 1,2,4,6,8,12
SERIAL_MEDIAN_SECONDS_PER_STEP = 0.6676124710356817
RANK2_MEDIAN_SECONDS_PER_STEP = 0.3786849119933322
RANK4_MEDIAN_SECONDS_PER_STEP = 0.194818826043047
RANK6_MEDIAN_SECONDS_PER_STEP = 0.15376722894143313
RANK8_MEDIAN_SECONDS_PER_STEP = 0.12174252304248512
RANK12_MEDIAN_SECONDS_PER_STEP = 0.09614649903960526
BEST_MPI_RANKS = 12
BEST_MPI_MEDIAN_SECONDS_PER_STEP = 0.09614649903960526
BEST_MPI_SPEEDUP = 6.943700266825884
BEST_MPI_PARALLEL_EFFICIENCY = 0.578641688902157
RANK24_EXPLORATORY_EXECUTED = NO
RANK24_MEDIAN_SECONDS_PER_STEP = NOT_EXECUTED
ESTIMATED_12800_STEP_BEST_MPI_HOURS = 0.34185421880748534
ESTIMATED_51200_STEP_BEST_MPI_HOURS = 1.3674168752299414
ESTIMATED_200061_STEP_BEST_MPI_DAYS = 0.2226292215782693
ESTIMATED_400122_STEP_BEST_MPI_DAYS = 0.4452584431565386
LESS_THAN_24H_PLAUSIBLE = YES
FEW_DAY_RUNTIME_PLAUSIBLE = YES
PREVIOUS_100_DAY_DIAGNOSTIC_PROXY_APPLICABLE_TO_PLAIN_CFD = NO
STEP_COST_TREND = STABLE
SOLVER_STABILITY = PASS
MPI_SCALING_CLASSIFICATION = GOOD
RECOMMENDED_PRODUCTION_MPI_RANKS = 12
NEXT_SINGLE_TASK = RUN_ROUTE_A_PLAIN_TRANSIENT_LATE_WINDOW_BOUNDED_PERFORMANCE_PILOT
PRODUCTION_EXECUTION_AUTHORIZED = NO
USER_DECISION_REQUIRED = YES
```
