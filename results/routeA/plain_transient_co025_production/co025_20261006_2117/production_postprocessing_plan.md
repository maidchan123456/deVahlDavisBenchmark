# Co0.25 offline comparison preparation

Primary purpose: fixed-grid timestep sensitivity between Co0.5 and Co0.25. Future command: `/usr/bin/python3 -B /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co025_production/co025_20261006_2117/postprocess_and_compare.py --execute`. Requires a completed normal native result. No CFD is invoked by postprocessing.

Histories are compared by t*, using piecewise linear interpolation onto the union of saved t* values in the common overlap; extrapolation is forbidden. Record axis/range, sample and time-weighted RMS, maximum differences and last10% common-window metrics. Direct final-native QoIs and profiles retain actual final-time differences; no forced exact1420 assumption. Sparse saved-time interpolation cannot recover unsaved extrema. A descriptive0.1% criterion may label small final/late sensitivity; inspect full history/profile metrics before a broader statement. Two levels cannot prove temporal convergence or independence. Co0.125 is a post-data review option, not predetermined.

Shared Co05 scientific methodology retained below as historical reference; its old command is not the Co025 execution command.

# Offline postprocessing plan

After authorized production completion, run:

```bash
python3 -B /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocess_production.py --case /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/cases/routeA/plain_transient_co05_production/co05_20261006_0602 --output /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/postprocessing --times all --log /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/plain_transient_co05_production/co05_20261006_0602/execution/log.foamRun
```

The script reads saved native fields and standard logs, writes to a new analysis directory outside the case, and invokes no CFD/decomposition/reconstruction/exact-evidence backend. Partial interrupted data may be analyzed under a separate output namespace with explicit coverage labels; they are not a completed production result.

Output:transient_QoI.csv with physical time and t*=alpha*t/L²; Nu_hot/cold from fixed-wall adjacent-cell orthogonal gradients; Umax/Wmax as dimensionless positive Ux/Uy centreline maxima by the same4097-point interpolation as the160² steady baseline. Speed norm and out-of-plane Uz are separate quantities. Save4097-point velocity/temperature profiles at each retained state,180-degree symmetry RMS, volume mass, kinetic energy and the reconstructable eConst sensible-energy proxy. Native rho is used when written; cold0 rho alone is reconstructed from the frozen EOS.

The native standard-log parser streams the large log, aggregates pressure/energy/momentum iteration counts, maximum initial/final residuals, local/global/cumulative continuity, dt, and pre-advance Co. Native ClockTime has integer-second granularity; launcher step-start/end monotonic markers give external wall timing. Retain the full log for detailed outer/linear-residual review.

Compare final Nu and centreline maxima/profiles to frozen Route A Ra1e6/160² end_9000 metrics and centreline CSV, with relative QoI and RMS/Linf profile differences. Do not assume final≈steady. Evaluate late trajectories using range and slope over the last10% and at leastlast5 snapshots. A0.1% descriptor threshold only labels STATIONARY_CANDIDATE; short/insufficient history is explicit. This is a diagnostic description, not proof of stationarity, nonlinear convergence, or benchmark validity. Inspect plots afterwards; the script produces reusable CSVs and does not silently advance any scientific gate.

Energy scope: Cv1000*(T-298.15) with native rho and volume, kinetic energy and conductive wall heat at k=mu*Cv/Pr. Saved-state energy secants/trapezoidal heat input are coarse descriptors. Missing native e/K histories and intermediate BDF stages prohibit an exact BDF energy balance or full conservation certificate. No artificial histories are generated. Mass totals and native continuity are reported; processor face conservation was geometrically verified during preparation, not promoted to a transient full audit.

Offline preparation validation used an existing late pilot saved state and598 standard-log steps, plus analytic cold0. Nu_hot and speed reproduce known pilot values; dimensional/component definitions are checked separately. No new physical timestep was executed. A floating-point cell-coordinate sorting issue found during offline validation was corrected using a verified bijective integer lattice mapping.

Q3 and formal GateJ are not run. Formal historical statuses remain unchanged. Post-run tasks are final output/schedule review, QoI/profile/evolution plotting, baseline comparison and coverage-limited mass/energy review.
