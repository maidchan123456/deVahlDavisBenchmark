# Route A Co0.5 diagnostic transient production v2

**COMPLETE, native returncode0, postprocessing completed.** One continuous cold-start Ra1e6/Pr0.71/160×160×1/maxCo0.5/12-rank plain OpenFOAM series. No model/numerical/controller/output changes, heavy diagnostics, function objects, restart/rerun, extension, Co0.25, Q3 or formal GateJ.

MEASURED: 143203 completed physical steps in 8400.797424s (2.333555h). Final native t=1420.0043825715495s; DERIVED t*=2.000006172635985. endTime1420 was a native threshold, with no timestep adjustment to force exact1420. Native runTime bin284 saved the final step; all284 regular bins and rank snapshot sets match, and final native fields are finite. Full stdout/stderr and bindings remain in execution_v2/log.foamRun.

MEASURED runtime/projected6.112102h=0.381793. The prediction was planning-only; measured cost changed through the production. Late10% dt(min/median/max)={'min': 0.009929812301771384, 'median': 0.009929812304467326, 'max': 0.009929812306989977}; logged Co={'min': 0.4999999999989064, 'median': 0.4999999999999639, 'max': 0.50000000000111}; overall maxloggedCo=0.517217955195. Co is reported for the native pre-advance state; configured maxCo0.5 was unchanged. Late non-write external wall/step={'min': 0.04534474108368158, 'median': 0.05461593548534438, 'max': 0.06680952105671167}. Native ClockTime has integer-second granularity; precise per-step costs use launcher monotonic end markers, excluding actual native write steps.

Pressure iterations/step early1000={'min': 1323.0, 'median': 2383.0, 'max': 4216.0}; last10%={'min': 2.0, 'median': 35.0, 'max': 291.0}. Late energy iterations={'min': 0.0, 'median': 0.0, 'max': 1.0}. Fixed48 pressure and24 energy solves perstep=True. This describes linear solver cost and residuals, not nonlinear convergence or physical validation. No fatal/NaN/FPE was detected; completed native fields/logs support gross solver sanity. Individual residual/continuity/iteration histories remain in production_step_history.csv.

POSTPROCESSED same-grid steady end_9000 comparison, with signed and absolute relative differences kept separate:

| QoI | transient final | steady160² | signed relative difference | absolute relative difference |
|---|---:|---:|---:|---:|
| Nu_hot | 8.86341271991 | 8.86338339241 | +3.30884e-06 | 3.30884e-06 |
| Nu_cold | 8.86341271326 | 8.86338375634 | +3.26703e-06 | 3.26703e-06 |
| Umax | 64.9156325303 | 64.9147345964 | +1.38325e-05 | 1.38325e-05 |
| Wmax | 219.901534473 | 219.900261662 | +5.78813e-06 | 5.78813e-06 |


Umax and Wmax are dimensionless positive Ux/Uy centreline maxima using the same4097-point interpolation as the baseline. They are not the speed norm or out-of-plane component. Final speed=0.0311322809413m/s; |Uz|max=3.22566922174e-24m/s. Centreline RMS/Linf differences are in steady_comparison.json; velocity/temperature profiles at every stored state remain in CSVs.

INFERRED late behavior: ADEQUATE_FOR_CURRENT_DIAGNOSTIC. Last10% of saved history and physical span, with at least5 samples, uses relative range and slope with descriptive0.001 thresholds. Per-QoI descriptors/classifications={"Nu_hot": {"relative_range": 6.765995084659669e-11, "slope_per_second": -9.032413196389882e-15, "relative_slope_per_second": -1.0190672014865507e-15, "relative_slope_change_over_window": 1.477698895683688e-13, "classification": "STATIONARY_CANDIDATE", "threshold_descriptive_only": 0.001, "snapshots": 30, "span_s": 145.0050490809747}, "Nu_cold": {"relative_range": 7.335493065549683e-11, "slope_per_second": 1.5959476432867005e-14, "relative_slope_per_second": 1.8006017489785575e-15, "relative_slope_change_over_window": 2.610963449859246e-13, "classification": "STATIONARY_CANDIDATE", "threshold_descriptive_only": 0.001, "snapshots": 30, "span_s": 145.0050490809747}, "Umax": {"relative_range": 7.105804702987625e-10, "slope_per_second": -1.9341122639044976e-12, "relative_slope_per_second": -2.979424505264091e-14, "relative_slope_change_over_window": 4.320315966188782e-12, "classification": "STATIONARY_CANDIDATE", "threshold_descriptive_only": 0.001, "snapshots": 30, "span_s": 145.0050490809747}, "Wmax": {"relative_range": 5.2696027764336e-10, "slope_per_second": -3.582651318255637e-12, "relative_slope_per_second": -1.629207057188305e-14, "relative_slope_change_over_window": 2.3624324929066046e-12, "classification": "STATIONARY_CANDIDATE", "threshold_descriptive_only": 0.001, "snapshots": 30, "span_s": 145.0050490809747}}. STATIONARY_CANDIDATE means approximate stability under these descriptors; it is not stationarity proof. The final state was compared to steady without assuming agreement. No simulation was extended after the requested horizon.

POSTPROCESSED mass: {"status": "RECONSTRUCTED_FINITE_NOT_EXACT_FV_AUDIT", "initial_kg": 1.000000000000011e-05, "final_kg": 1.0000000284767312e-05, "final_relative_drift": 2.8476720323976306e-08, "max_abs_relative_drift": 2.8476720832196074e-08, "native_continuity_max_local_abs": 1.4815354670353096e-10, "native_continuity_max_global_abs": 1.4814301717486854e-10, "native_continuity_final_cumulative": -9.18337562761583e-07}. These are native rho-volume totals and standard continuity descriptors, not an exact transient FV mass audit. Energy: {"status": "RECONSTRUCTED_FINITE_COARSE_DESCRIPTOR_ONLY", "initial_sensible_proxy_J": 0.01850000000000043, "final_sensible_proxy_J": 0.018499138166098786, "final_kinetic_energy_J": 4.936543676954308e-10, "final_Q_hot_W": 0.00012483679887198307, "final_Q_cold_W": 0.00012483679877837558, "coarse_secant_minus_net_heat_max_abs_W": 7.711988193962718e-08, "coarse_secant_minus_net_heat_late_max_abs_W": 1.0825197688479826e-13, "late_secant_difference_relative_to_wall_flux_max": 8.671479716224548e-10, "exact_BDF_energy_certificate": false, "missing_native_stage_or_eK_histories_reconstructed": false}. Native intermediate stages and e/K histories are missing on disk; coarse stored-state energy secants/wall heat are limited descriptors, not an exact BDF conservation certificate. No artificial histories were generated. Symmetry: {"final_T_RMS_K": 6.125367480071459e-05, "final_U_RMS_m_s": 2.3011557734149107e-06}.

HEAD lesson: old preparation f57d60d85e36ea9928e4bc481d3cbde586496f58 remains intact, including its historical fixed HEAD and NO authorization draft. Local Git range to 83a910f31a7a26cd91bf15c0eff432f48ff24800 added63 preparation/blocked evidence files only; independent sensitive hashes matched. V2 safely reviewed/pinned current provenance and hashes without changing native execution-loop AST. HEAD provenance and production input integrity are separate guards: a reviewed results-only commit does not require stopping CFD automatically; altered physics/numerics/runtime/script identities fail closed. Original0step blocked evidence remains unchanged.

Actual storage: {"native_output_files": 42336, "native_output_logical_bytes": 2853699892, "native_output_allocated_bytes": 2941976576, "full_stdout_stderr_log_bytes": 3870570559, "fields_plus_log_allocated_bytes": 6812553216}. All native output fields/histories were retained; no purge/thinning. Formal historical statuses remain unchanged; simulation completion does not validate the physical model, provide grid/time-step independence, authorize formalGateJ, or make downstream/particles ready.

Figures:

![QoI history](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocessing_v2/QoI_vs_tstar.png)

![Native log history](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocessing_v2/native_log_vs_tstar.png)

![Representative profiles](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocessing_v2/representative_profiles.png)

![Final vs steady profiles](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocessing_v2/final_vs_steady_profiles.png)

Next single task: PREPARE_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION_RUN. A stationary candidate close to the same-grid baseline makes a separate Co0.25 preparation a useful next time-step sensitivity task; no second run is authorized or started. User decision required:YES.

```text
ROUTE_A_CO05_HEAD_CHANGE_REVIEW = PASS
OLD_PREPARATION_HEAD = f57d60d85e36ea9928e4bc481d3cbde586496f58
REVIEWED_EXECUTION_HEAD = 83a910f31a7a26cd91bf15c0eff432f48ff24800
HEAD_CHANGED = YES
HEAD_CHANGE_PRODUCTION_SENSITIVE = NO
PRODUCTION_SENSITIVE_MANIFEST_MATCH = PASS
HEAD_REPINNED = YES
V2_PREFLIGHT = PASS
PRODUCTION_EXECUTION_AUTHORIZED = YES
ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION = COMPLETE
PRODUCTION_CFD_EXECUTED = YES
PRODUCTION_NORMAL_EXIT = YES
PHYSICAL_MODEL_CHANGED = NO
NUMERICAL_POLICY_CHANGED = NO
GRID = 160x160x1
RA = 1e6
PR = 0.71
MAX_CO = 0.5
MPI_RANKS = 12
HEAVY_DIAGNOSTICS_ENABLED = NO
FUNCTION_OBJECTS_DURING_PRODUCTION = NO
PRODUCTION_START_MODE = CONTINUOUS_COLD_START
STRICT_BDF_RESTART_RELIED_UPON = NO
ACTUAL_FINAL_TIME_SECONDS = 1420.0043825715495
ACTUAL_FINAL_TSTAR = 2.000006172635985
COMPLETED_PHYSICAL_STEPS = 143203
TOTAL_PRODUCTION_WALL_HOURS = 2.333554839975
EXPECTED_RUNTIME_HOURS = 6.112102039491276
RUNTIME_RATIO_ACTUAL_TO_PROJECTED = 0.3817925199706298
MAX_LOGGED_CO = 0.5172179551948343
LATE_MEDIAN_DELTA_T = 0.009929812304467326
LATE_MEDIAN_SECONDS_PER_STEP = 0.05461593548534438
FINAL_NU_HOT = 8.863412719910798
FINAL_NU_COLD = 8.863412713264665
FINAL_UMAX = 64.91563253034387
FINAL_WMAX = 219.9015344727529
FINAL_VS_STEADY_NU_RELATIVE_DIFFERENCE = 3.30883824177394e-06
FINAL_VS_STEADY_UMAX_RELATIVE_DIFFERENCE = 1.3832513677316512e-05
FINAL_VS_STEADY_WMAX_RELATIVE_DIFFERENCE = 5.7881289387474204e-06
LATE_NU_BEHAVIOR = STATIONARY_CANDIDATE
LATE_UMAX_BEHAVIOR = STATIONARY_CANDIDATE
LATE_WMAX_BEHAVIOR = STATIONARY_CANDIDATE
TSTAR2_TIME_HORIZON_ASSESSMENT = ADEQUATE_FOR_CURRENT_DIAGNOSTIC
POSTPROCESSING_COMPLETED = YES
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
Q3_EXECUTED = NO
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION_RUN
USER_DECISION_REQUIRED = YES
```

Offline analysis repair: the first added summary script omitted the existing Scripts/routeA module search path. The prepared postprocessor had already completed with returncode0. A separate revision1 completed field-integrity checks and summaries using the retained prepared CSVs; neither CFD nor prepared postprocessing was repeated. Original source, exception record, pre-repair output hashes and revision source hashes remain in head_review_v2.

Native Co alignment: maximum logged Co=0.5172179551948343 was reported before step62 at pre-advance t≈0.778190853453s with previous dt=0.026729878902837508s. Native preSolve reports Co before adjusting dt; selected new dt=0.02584005314816309s rescales the same pre-advance-state Co to0.5. All143203 selected dt values exactly match min(1.2×previous_dt, maxDeltaT, maxCo/logged_Co×previous_dt) in the parsed floating values. There are6539 logged values above0.5+1e-9, the last before step13839 (new-step t≈135.444142532231s); late Co remains≈0.5. This derived pre-advance rescaling is not a post-solve Courant guarantee. No controller, physics or numerical policy was changed. Evidence: postprocessing_v2/native_Co_controller_alignment_v2.json.
