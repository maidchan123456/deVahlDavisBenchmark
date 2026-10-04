# B-Ra1e4-medium formal benchmark report

Initial HEAD: `a685921fadcaa7f43a528e7ba29d2ba871738961`.

Gate G investigation frozen, unresolved; formal Ra1e3 Gate G remains FAIL. Formal criteria, tau_mean (UNRESOLVED), and Candidate B (PROVISIONAL) unchanged. Gate G does not block matrix execution. Freeze note saved before solver execution.

Case: `/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB/Ra1e4_medium`.

Foundation OpenFOAM v6 stock binary, build 6-af7d7f427be7, linux64GccDPInt32Opt; environment/binary/canonical template checks PASS. Grid 80×80×1 (6400 cells), Ra_target=Ra_actual=10000, Pr_actual=0.71; Mesh OK, max nonorthogonality 0°, max skewness 7.77159989388192e-14.

Initial run 0→3000: normal exit; QoI Rwin and heat trend PASS, residual requirement FAIL. Unchanged discrete problem continued 3000→6000. Only startFrom latestTime and endTime changed. Before/after input, mesh, field and log hashes preserved. Bounded cap 24000 was not reached. Accepted iteration 6000; Gate D PASS (5800–6000, 21 samples at 10-iteration intervals).

Rwin Nu_bar_0=3.2116589512494e-08, Umax=2.70626013294421e-08, Wmax=2.27901623549064e-08 (limit 5e-4).

Final initial residuals: Ux=6.0608281503768e-11, Uy=5.25794375038151e-11, T=9.68908567931076e-11, p_rgh=1.71983035330037e-10 (limit 1e-7).

Heat imbalance=4.85832345161908e-09; final-window regression slope=-4.57220407782391e-12 per iteration. No NaN/Inf/fatal; normal exits.

| QoI | Calculated |
|---|---:|
| Nu_bar_cavity | 2.24845332402773 |
| Nu_bar_0 | 2.24798530497083 |
| Nu_bar_half | 2.24798508596464 |
| Nu_bar_1 | 2.24798531589227 |
| Nu_bar_cavity_from_section_trapezoid | 2.24798519235847 |
| Nu_bar_cavity_method_relative_difference | 0.000208201639881521 |
| Umax | 16.1701872059773 |
| Umax_Z | 0.81884765625 |
| Wmax | 19.6247125965898 |
| Wmax_X | 0.11865234375 |
| Nu_hot_local_max | 3.54273004706375 |
| Nu_hot_local_max_Z | 0.142939989656021 |
| Nu_hot_local_min | 0.584278469330329 |
| Nu_hot_local_min_Z | 1 |

Primary cavity Nu uses cell-volume quadrature; section trapezoid is an independent diagnostic.

| Table V quantity | Calculated | Reference | Signed difference | Absolute relative error |
|---|---:|---:|---:|---:|
| Nu_bar_cavity | 2.24845332403 | 2.243 | +0.00545332402773 | 0.0024312634987662942 |
| Nu_bar_half | 2.24798508596 | 2.243 | +0.00498508596464 | 0.002222508232116255 |
| Nu_bar_0 | 2.24798530497 | 2.238 | +0.00998530497083 | 0.004461709102245484 |
| Nu_hot_local_max | 3.54273004706 | 3.528 | +0.0147300470638 | 0.004175183408092507 |
| Nu_hot_local_max_Z | 0.142939989656 | 0.143 | -6.00103439789e-05 | N/A (position) |
| Nu_hot_local_min | 0.58427846933 | 0.586 | -0.00172153066967 | 0.0029377656479032247 |
| Nu_hot_local_min_Z | 1 | 1 | +0 | N/A (position) |
| Umax | 16.170187206 | 16.178 | -0.00781279402274 | 0.00048292706284709956 |
| Umax_Z | 0.81884765625 | 0.823 | -0.00415234375 | N/A (position) |
| Wmax | 19.6247125966 | 19.617 | +0.00771259658983 | 0.0003931588209119489 |
| Wmax_X | 0.11865234375 | 0.119 | -0.00034765625 | N/A (position) |

Position differences are absolute-coordinate differences; all comparisons are medium-grid diagnostics, not formal Gate E judgements. See paper_comparison.csv.

| Gate G diagnostic | Value |
|---|---:|
| heat_imbalance | 4.85832345161908e-09 |
| section_Nu_max_relative_deviation_from_half | 1.02281652101625e-07 |
| theta_L2_relative | 2.85780541605874e-09 |
| velocity_L2_relative | 2.64251211515669e-09 |
| epsilon_phi_mean | 1.56299289345431e-11 |
| epsilon_phi_max | 1.23753319593526e-09 |
| epsilon_phi_P95 | 3.84014998336625e-11 |
| epsilon_phi_P99 | 5.15280617301042e-11 |
| epsilon_v | 0.00109550172161461 |
| epsilon_m | 0.00109550172161461 |
| boundary_net_volume_flux_m3_s | 2.42338070083895e-26 |
| global_signed_div_phi_1_s | -3.30920207764248e-19 |
| flux_balance_closure_m3_s | -3.33343588465087e-24 |

Native final continuity: {"sum_local": 4.334237432026903e-13, "global": 1.01961218632913e-18, "cumulative": -5.621668682766818e-17}. Individual boundary fluxes are in gateG_diagnostics.json. Saved phi divergence and reconstructed U divergence remain distinct operators.

Target Gate G: NOT_EVALUATED_UNDER_FROZEN_REVIEW. Ra1e4 Gate E and Gate F: NOT_EVALUATED; no Richardson extrapolation, observed order or GCI computed.

Accepted matrix count: 5/12. Next case: B-Ra1e4-fine (not generated or executed in this invocation). This single-case request is complete; no user decision required for the completed work.

Validation: 240 protected files retain their startup SHA-256; all four previous case status/manifest records, prior summary/conservation rows and Ra1e3 grid rows remain unchanged. No microcase solver executed; no Git add/commit/push. See validation.json and startup_provenance.json.

Pipeline maintenance: added bounded continuation and case-scoped publication helpers; existing run_full_matrix.py single-case selector, generator, run_case.sh and analyzer were used unchanged. Historical Ra1e3-specific finalizer was not executed.
