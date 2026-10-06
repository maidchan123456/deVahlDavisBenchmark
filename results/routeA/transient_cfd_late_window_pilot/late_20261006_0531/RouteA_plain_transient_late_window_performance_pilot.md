# Route A plain transient late-window performance pilot

**COMPLETE** — `late_20261006_0531`. 12 physical-core MPI ranks, native OpenFOAM13 fluid, heavy diagnostics/function objects OFF. Continuous native cold start, no unsafe restart.

Completed **598 steps** in **71.184 s** for the accepted attempt; cumulative CFD wall **120.618 s**, reached t=5.46664267804 s, t*=0.0076994967. Last 200 non-write steps (393–595) median **0.115924 s/step**, **1.206×** prior cold median0.0961465. Pressure iterations median **2373.0/step** (range2236–2393).

maxDeltaT first reached at step **39**; Courant controller first active at step **60**. Final dt=0.00784581575004 s, regime=COURANT, maximum logged preSolve Co=0.51721796. Native controller law verified for every completed step.

## Window performance

| steps | non-write count | median s/step | mean | min | max | CV | median dt s | max dt s | median Co | max Co | pressure iterations median | energy iterations median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 31–50 | 20 | 0.138395 | 0.135429 | 0.108799 | 0.154916 | 0.1085 | 0.02773437 | 0.02773437 | 0.13053 | 0.31331 | 3115.5 | 26.0 |
| 51–100 | 47 | 0.128549 | 0.131253 | 0.123764 | 0.148624 | 0.0499 | 0.01886289 | 0.02773437 | 0.50661 | 0.51722 | 2794.0 | 19.0 |
| 101–250 | 147 | 0.118122 | 0.119374 | 0.095762 | 0.146131 | 0.0501 | 0.00913365 | 0.01386625 | 0.50186 | 0.50448 | 2441.0 | 13.0 |
| 251–500 | 247 | 0.115612 | 0.116224 | 0.091637 | 0.146948 | 0.0464 | 0.00709524 | 0.00750907 | 0.49987 | 0.50089 | 2362.0 | 11.0 |
| 501–750 | 95 | 0.115991 | 0.115964 | 0.093466 | 0.136601 | 0.0501 | 0.00781570 | 0.00785747 | 0.49957 | 0.50008 | 2385.0 | 11.0 |

Primary uses external monotonic completion increments and excludes actual field-write steps. First-step startup and all write-including timing retained in step_history.csv; window_performance.csv also retains write-including summaries. Native ClockTime integer seconds, native ExecutionTime is CPU, neither substituted for high-resolution wall timing.

![Late-window performance](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/transient_cfd_late_window_pilot/late_20261006_0531/late_window_performance.png)

## Controller and cost trend

Controller counts: {'GROWTH': 38, 'MAXDELTAT': 21, 'COURANT': 539}. Logged Co is previous-state Co at previous dt. Formula=min(1.2dt_old,maxDeltaT,0.5/Co_old*dt_old), checked against native setDeltaT.C and fluidSolver.C; no hidden function-object or model caps. Growth control ends after step38; maxDeltaT is not the sustained late regime.

Cost trend **FLAT**. Last200 non-write first100 median=0.115709, last100=0.116019 s/step (ratio1.0027); fitted slope=-3.5704057e-06 s/step-index, fitted relative change=-0.0062. Plot, broad window and rolling50 medians are saved; descriptive classification combines median direction and slope rather than the old15% rule alone.

Pressure median is2373.0 versus prior cold1551.0 iterations/step (1.530×). Late energy median=11.0 iterations/step. Pearson correlations of non-write step wall vs pressure/energy/dt/Co: {'pressure_total_iterations': 0.7649669314006066, 'energy_total_iterations': 0.7141302651767486, 'deltaT_s': 0.7434955308448479, 'logged_Co_max': -0.3434462282657963}. These are correlations, not causal isolation of pressure, communication or I/O.

Last200 mean dt=0.007476539705 s; last50 mean=0.007847966548 s (1.0497×); late dt min/max=0.007000613291/0.007857466868. The forward model assumes representative future dt; later flow can change it.

## Fixed planning scenarios

| scenario | steps | hours | days | 24h threshold s/step | <24h plausible? |
|---|---:|---:|---:|---:|---|
| t*=0.5 ideal floor | 12800 | 0.412 | 0.017 | 6.750000 | YES |
| t*=2 ideal planning | 51200 | 1.649 | 0.069 | 1.687500 | YES |
| Co0.5 previous planning | 200061 | 6.442 | 0.268 | 0.431868 | YES |
| Co0.25 previous planning | 400122 | 12.884 | 0.537 | 0.215934 | YES |

**LATE_WINDOW_SHORT_PILOT_PROXY**: supplied step counts × measured late median. Co0.25 is not a measured series;400122 is still a scenario. Old100-day diagnostic proxy is inapplicable and contributes nothing to these estimates.

## Projection from actual adaptive dt

| target | physical seconds | remaining steps | total steps | total using last50 mean dt | conditional late-dt min/max total range | total hours / days |
|---|---:|---:|---:|---:|---|---:|
| t*=0.5 | 355 | 46751 | 47349 | 45137 | [45083, 50527] | 1.525 h / 0.064 d |
| t*=2 | 1420 | 189197 | 189795 | 180841 | [180623, 202657] | 6.112 h / 0.255 d |

**PROJECTED_FROM_LATE_WINDOW**: target t*=alpha*t/L², using alpha=1.4084507042253522e-5 and L=0.1 (target355 and1420 s). Remaining time divided by actual last200 mean dt, rounded up; accepted continuous-attempt measured wall plus remaining steps × late median; the initial failed logging attempt is counted in the pilot CFD wall receipt but excluded from the future normal-run projection. Bounds are conditional min/max-dt sensitivity, not uncertainty intervals or exact future adaptive counts.

## Offline checkpoint sanity

| step | t s | t* | Umax m/s | Tmin K | Tmax K | Nu hot | sanity |
|---:|---:|---:|---:|---:|---:|---:|---|
| 100 | 1.48557241 | 0.00209236 | 0.02250845 | 299.51061720 | 300.48938745 | 6.50621199 | True |
| 250 | 2.92809634 | 0.00412408 | 0.03965702 | 299.50469797 | 300.49530402 | 5.92790797 | True |
| 500 | 4.70798791 | 0.00663097 | 0.03861910 | 299.50342232 | 300.49657811 | 6.19340811 | True |
| 598 | 5.46664268 | 0.00769950 | 0.03805800 | 299.50351030 | 300.49648965 | 6.22499838 | True |

Nu from native orthogonal hot-wall adjacent-cell temperature, distance dx/2 and L/DeltaT normalization; no added function object. Each completed step has24 outer,48 pressure solves and24 energy solves, no early outer stop. Standard continuity/residuals retained. Finite saved fields and bounded T/U support gross pilot sanity only; no mass/energy full audit, nonlinear convergence certificate, validation or GateJ claim.

## Starting state and checkpoints

Read and hash-verified prior validated pilot, including source12-rank final fields and uniform/time at0.032778746640202423. Restart rejected: U_0/rho_0/phi_0 are insufficient; missing e/K histories and native NO_READ/NO_WRITE energy construction prevent a proof of identical backward evolution. The prompt explicitly permits cold start; copied prior common cold inputs and ran continuously, keeping native histories in memory. No fake or synthetic oldTime fields.

Selected checkpoint triplets retain real adjacent native snapshots for100,250,500 and final remaining step cap when reached. No purge or per-step huge output. Native SIGUSR1 requests checkpoint writes; native SIGUSR2 sent during the penultimate accepted step stops and writes at the final accepted step cap. These are operational IO/termination settings, not numerical tuning. Native checkpoint fields and_0 histories retained without thinning; e/K full-history restart remains uncertified. Production preparation must address restart handling or continuous-run constraints; these outputs are not advertised as safe strict-BDF restarts.

## Frozen configuration and authorization

Ra1e6,Pr0.71,160×160×1; original Boussinesq/eConst/Stokes/Fourier and cold/wall fields. Exact prior fvSolution/fvSchemes hashes; backward,nOuter24,nCorrectors2,nNonorth0,tolerance1e-12,relTol0,no relaxation,maxCo0.5,growth1.2,maxdt0.027734375. Reference pRefPoint=(0.0496875,0.0496875,0.0005), no pRefCell. scotch12 MPI, nooversubscribe,map-by core,bind-to core,threads1,-noFunctionObjects. Only controlDict termination, output cadence and native IO signals changed in a new namespace.

authorization_receipt.json limits cumulative actual CFD to1000 completed steps and600s; one expressly allowed logging-repair attempt, no wall/step budget extension, no production/Q3/GateJ/particles. run_command.json and preparation_commands.json preserve exact commands; input/source/binary manifests and starting_state_provenance.json preserve provenance. Prior pilot and authorities read-only; no git mutation commands.

## Preserved output-name failure and authorized repair

Initial attempt completed402 steps in49.435 s then native Time::operator++ failed a time-name precision check (timePrecision17, rounding tolerance below floating-point subtraction noise). Original logs/case preserved under attempt_01_time_precision_failure. Only output directory-name precision changed to12; writePrecision17 and physical/numerical/timestep policies unchanged. New cold continuous run capped at598 steps and550.565 s, preserving cumulative1000 completed steps/600s. Completed physical trajectory of accepted run is598 steps; accumulated compute across both attempts is1000 steps. The earlier fatal is an operational output-name issue, retained explicitly; accepted attempt stability is reported separately.

## Coverage and final verification

The accepted trajectory contains598 continuous steps; first402 steps were recomputed after the allowed output-name repair. Resource accounting totals1000 completed compute steps and120.618 s; this is not a1000-step physical trajectory. Requested windows31–50,51–100,101–250 and251–500 are complete;501–750 has501–598 coverage;751–1000 was not reached because the cumulative budget was preserved. The last200 non-write proxy is fully available.

step_history.csv contains598 accepted steps; failed_attempt_step_history.csv contains402 prior steps; step_history_all_attempts.csv includes all1000 with attempt_id and cumulative_compute_step. Every completed step has24 outer,48 pressure and24 energy solves; every pressure/energy final residual<=1e-12, exact logged native-controller formula match. Prior pilot artifact hashes, authority hashes and all copied original physical/numerical input hashes remain unchanged. Binding logs prove12 distinct physical cores; all worker PIDs exited.

Both attempts used standard scotch; independently generated partitions differ, so comparisons assemble global cell order using each cellProcAddressing. Checkpoint100/250 U/T after the output-name repair agree within recorded tiny floating-point differences: [{'physical_step': 100, 'U_component_Linf_difference_m_s': 1.8793994138732728e-14, 'T_Linf_difference_K': 1.6484591469634324e-12, 'old_time_name': '1.4855724052851444', 'new_time_name': '1.485572405285', 'gross_same_state_after_output_name_repair': True, 'comparison_method': 'assemble each separate scotch decomposition into global cell order using its own cellProcAddressing'}, {'physical_step': 250, 'U_component_Linf_difference_m_s': 1.986501241280081e-13, 'T_Linf_difference_K': 1.659827830735594e-11, 'old_time_name': '2.9280963393185626', 'new_time_name': '2.928096339318', 'gross_same_state_after_output_name_repair': True, 'comparison_method': 'assemble each separate scotch decomposition into global cell order using its own cellProcAddressing'}]. No bitwise or full parallel/scientific equivalence claim.

![Later window medians](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/transient_cfd_late_window_pilot/late_20261006_0531/late_window_medians.png)

Adaptive runtime projections use accepted continuous-attempt wall; initial failed duplicate compute is retained in total pilot wall accounting but excluded from a future normally prepared production-run estimate.

## Decision

Another performance pilot required: **NO**. FullCo0.5 run now reasonable: **CONDITIONAL**. Recommended next single task: **PREPARE_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION_RUN**.

Preparation should preregister production time/step/wall/storage limits, output/restart handling, late-cost uncertainty and monitoring; preserve scientific labels below. Present authorization does not execute or authorize a production series.

## Limitations

- Accepted continuous trajectory stops at the remaining cumulative step cap after an authorized time-name logging repair. It is later than30-step pilot but not arrival, asymptotic steady flow or temporal/grid validation.
- Single12-rank run; no later serial or scaling measurement.
- External log marker timing includes small pipe, monitoring and native signal-flag reduction overhead; no matched observer-free run.
- Primary excludes actual native field-write steps; all write-including timing retained.
- Native output includes some_0 fields but e/K full backward restart histories remain uncertified. Real adjacent snapshots retained; no synthetic histories and no continuation from an unsafe checkpoint. Production preparation should resolve restart handling or explicitly plan continuous native history.
- Standard Co is previous-state preSolve Co, not independently sampled end-state Co.
- Current Co0.5 dt plateau/variation is projected forward conditionally; future U/phi may change adaptive counts substantially.
- Co0.25 not run.400122steps timesCo0.5 late cost is a scenario, not a Co0.25 measurement or exact adaptive-series runtime.
- Pressure/energy iteration correlations do not prove solver or MPI communication causes; no expensive profiling was enabled.
- Fixed24outer and tight linear residuals plus sane fields do not certify nonlinear convergence or GateJ.
- 24h is planning guidance, not a scientific pass/fail or runtime guarantee.

## Historical scientific status unchanged

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
```

## Final status

```text
ROUTE_A_PLAIN_TRANSIENT_LATE_WINDOW_PERFORMANCE_PILOT = COMPLETE
LATE_PILOT_ID = late_20261006_0531
SOURCE_SCALING_PILOT = plain_20261006_0710
CANONICAL_AUTHORITY_HASH_VERIFIED = YES
FORMAL_AUTHORITY_HASH_VERIFIED = YES
PHYSICAL_MODEL_CHANGED = NO
NUMERICAL_POLICY_CHANGED = NO
HEAVY_DIAGNOSTICS_ENABLED = NO
MPI_RANKS = 12
ACTUAL_TRANSIENT_CFD_EXECUTED = YES
MAX_ADDITIONAL_STEPS = 1000
COMPLETED_ADDITIONAL_STEPS = 598
WALL_LIMIT_SECONDS = 600
TOTAL_CFD_WALL_SECONDS = 120.61840858403593
CFD_PHYSICAL_STEPS_ALL_ATTEMPTS = 1000
PRIOR_LOGGING_FAILURE_COMPLETED_STEPS = 402
START_PHYSICAL_TIME_SECONDS = 0
END_PHYSICAL_TIME_SECONDS = 5.466642678038034
END_TSTAR = 0.007699496729631033
MAXDELTAT_REACHED = YES
MAXDELTAT_FIRST_STEP = 39
COURANT_LIMITED_REGIME_REACHED = YES
FINAL_DELTA_T = 0.00784581575003591
MAX_LOGGED_CO = 0.5172179551943793
PREVIOUS_COLD_MEDIAN_SECONDS_PER_STEP = 0.09614649903960526
LATE_WINDOW_MEDIAN_SECONDS_PER_STEP = 0.1159235269878991
LATE_TO_COLD_COST_RATIO = 1.205696807952905
LATE_WINDOW_PRESSURE_ITERATIONS_PER_STEP = 2373.0
STEP_COST_TREND = FLAT
SOLVER_STABILITY = PASS
ESTIMATED_12800_STEP_HOURS = 0.412172540401419
ESTIMATED_51200_STEP_HOURS = 1.648690161605676
ESTIMATED_200061_STEP_HOURS = 6.442160203535022
ESTIMATED_400122_STEP_HOURS = 12.884320407070044
UPDATED_ACTUAL_DT_BASED_STEPS_TO_TSTAR_0P5 = 47349
UPDATED_ACTUAL_DT_BASED_STEPS_TO_TSTAR_2 = 189795
UPDATED_RUNTIME_TO_TSTAR_0P5 = 1.525201282458422 hours
UPDATED_RUNTIME_TO_TSTAR_2 = 6.112102039491276 hours
CO05_LESS_THAN_24H_PLAUSIBLE = YES
CO025_LESS_THAN_24H_PLAUSIBLE = YES
ANOTHER_PERFORMANCE_PILOT_REQUIRED = NO
FULL_CO05_RUN_NOW_REASONABLE = CONDITIONAL
PRODUCTION_CFD_EXECUTED = NO
Q3_EXECUTED = NO
FORMAL_GATE_J_EXECUTED = NO
PREVIOUS_100_DAY_DIAGNOSTIC_PROXY_APPLICABLE = NO
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION_RUN
PRODUCTION_EXECUTION_AUTHORIZED = NO
USER_DECISION_REQUIRED = YES
```
