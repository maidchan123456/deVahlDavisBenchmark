#!/usr/bin/env python3
"""Write preparation decision records only; never launch CFD."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
read=lambda n:json.loads((P/n).read_text())
def save(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n')
plan=read('production_execution_plan.json');storage=read('storage_and_cadence_decision.json');proof=read('final_write_arithmetic_validation.json')
save('output_cadence_decision_ledger.json',storage)
(P/'output_cadence_decision_ledger.md').write_text('''# Output cadence decision

Selected `writeControl runTime; writeInterval 5; purgeWrite 0; writeFormat ascii; writeCompression off; writePrecision 17; timePrecision 12;`. Numeric time-directory precision can increase natively if needed; field values stay at17 digits.

| interval | regular snapshots | with10 startup requests, upper bound | allocated field bytes | field files |
|---|---:|---:|---:|---:|
'''+''.join(f"| {r['interval_seconds']}s | {r['regular_snapshots']} | {r['expected_snapshots_upper_bound']} | {r['field_allocated_bytes_estimate']} | {r['expected_field_files_upper_bound']} |\n" for r in storage['cadence_comparison'])+f'''
The 5s default preserves284 later samples and permits approach-to-steady/profile comparisons. It gives t* spacing0.00704225352. Ten native SIGUSR1 write requests target steps2,5,10,20,30,39,60,100,250,500. Requests go to the verified master during the preceding step after native handler activation. Actual write indices/times are read from uniform/time after the run; signals and asynchronous observation can shift the requested step. These are extra native full fields, with no online field analysis, no function objects, no end-time signal, no deltaT adjustment. Duplicate requests/regular writes coalesce, so294 is an upper bound. Cold0 is retained separately.

Startup sampling matters: the pilot speed maximum changed from0.0225 to0.0397m/s between1.49 and2.93s. Five-second-only output would miss that startup. Five-second later output is adequate for planned evolution analysis; resolving every possible oscillation is not claimed. The 2s alternative costs2.45 times as many fields;10s halves later temporal resolution. No format conversion, purge, or every-step output is needed.

Actual pilot measurements:12 rank filesets form one snapshot; each contains144 files and at most{storage['checkpoint_peak_allocated_bytes']} allocated bytes.294 snapshots use{storage['selected']['field_allocated_bytes_estimate']} allocated bytes; at200000 completed steps the measured native log rate gives{storage['expected_log_bytes_at200000_steps']} bytes. Combined expectation is{storage['expected_total_output_allocated_bytes_including_log']} bytes (~7.77GiB), plus cold case and offline tables. Expected output files:42336 native field/state files + one combined stdout/stderr log + a small metadata set. Profiles may add294 CSVs. This is a planning estimate based on real early/late ASCII fields, not a hard capacity bound; field string lengths and step count can vary.

Disk reserve:32GiB before launch,8GiB low-watermark during run; preparation free capacity{storage['free_bytes_at_preparation']} bytes. The reserve exceeds3 times the estimate and covers inputs, decomposition, postprocessing and margin.200000 is used only for capacity estimation, never as a timestep stopping rule.

Installed Time::setDeltaT invokes write-time adjustment only for adjustableRunTime. Plain runTime output and native writeOnce flags only select writes. Output does not modify the frozen Co/controller/BDF trajectory.
''')
source=[{'path':'/opt/openfoam13/src/OpenFOAM/db/Time/Time.C','lines':'70-119;884-886;1052-1060;1196-1214','meaning':'adjustableRunTime adjusts dt; runTime does not; native running and write bin predicates'},
{'path':'/opt/openfoam13/src/OpenFOAM/db/Time/TimeIO.C','lines':'210-249;254-282','meaning':'uniform/time has actual value,index,deltaT,deltaT0; writeTime gates native AUTO_WRITE objects'},
{'path':'/opt/openfoam13/applications/solvers/foamRun/foamRun.C','lines':'188-200','meaning':'postSolve then runTime.write before loop termination; End alone does not force write'},
{'path':'/opt/openfoam13/applications/solvers/foamRun/setDeltaT.C','lines':'55-80','meaning':'native bounded growth and solver CFL policy'},
{'path':'/opt/openfoam13/src/OSspecific/POSIX/signals/sigWriteNow.C','lines':'58-65;102-120','meaning':'native writeOnce flag, no dt change'}]
proof.update(source_evidence=source,installed_sources_sha256=read('production_input_manifest.json')['installed_source_sha256'],writeAtEnd_option_found=False,method='NATIVE_RUN_TIME_BIN_ENDTIME_MULTIPLE')
save('final_write_decision_ledger.json',proof)
(P/'final_write_decision_ledger.md').write_text('''# Native final-write decision

Use ordinary `runTime` writes at5s with beginTime0 and endTime1420. Do not add an assumed writeAtEnd option: the installed Time/TimeIO/foamRun sources have no such control. Do not force a final timestep, change maxCo, use adjustableRunTime, or signal early termination during normal completion.

The native running predicate is `t < E - 0.5*dt`. The native write bin is `int(((t-beginTime)+0.5*dt)/interval)`. With E=1420 and interval5, the first non-running completed step crosses bin284. maxDeltaT0.027734375 is far smaller than5, so it cannot skip a write bin. foamRun writes after postSolve, before the next running test. Thus the final computed state is saved by the regular output policy.

This saves the final native state near1420; it does not force an exact1420 timestamp. Native variable dt endTime semantics permit a final physical time in [1419.9861328125,1420.0161783854167) under the frozen maxDeltaT and growth1.2. Actual t,t*,time index,dt are read from each rank's uniform/time.value; directory names and ordinary printed Time headers are not treated as exact physical time. Atconstant dt the half-step interval is tighter. No state at exactly t=1420 is interpolated or invented.

Three million non-CFD floating-point boundary evaluations passed, including representable values at/above the native termination boundary. This is source/arithmetic verification, not execution of a physical timestep. Final postflight requires all12 rank states match, have all native fields/histories and satisfy the termination/bin predicates. A missing/partial final write becomes STOP_AND_REVIEW, not silent success.

Sources (installed source hashes pinned in production_input_manifest.json):
'''+''.join(f"- {s['path']}:{s['lines']} — {s['meaning']}\n" for s in source))
restart={'strict_restart':'NOT_RELIED_UPON','primary_production':'CONTINUOUS_COLD_START','pilot_restart':False,'synthetic_oldTime':False,'interruption_status':'INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN','interruption_policy':'STOP_AND_REVIEW','automatic_retry':False,'automatic_restart':False,'automatic_cold_rerun':False,'reason':'Native e/K histories are not fully stored; U_0/rho_0/phi_0 and uniform/time alone do not establish identical variable-step BDF2 continuation. Keep native oldTime state in memory continuously from cold start.','write_retention':'All native AUTO_WRITE fields and native _0 output preserved without thinning; retained states are analysis evidence and are not claimed strict-BDF restart certificates.'}
save('restart_decision_ledger.json',restart)
(P/'restart_decision_ledger.md').write_text('''# Continuous cold-start decision

Strict restart = NOT RELIED UPON. Primary production = CONTINUOUS_COLD_START, one uninterrupted native run from validated cold0 to endTime1420. No pilot state, synthetic oldTime, injected pressure/energy history, or restart research is used.

Native e/K histories are incomplete on disk. Stored U_0/rho_0/phi_0 and uniform/time do not establish identical variable-step backward continuation. All native state outputs are retained, but no strict-BDF restart claim is made.

Interruption, timeout, fatal/nonfinite log, disk low-watermark, observer failure or partial final output => INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN and STOP_AND_REVIEW. Preserve logs, return code, metadata and whatever states were actually written. No automatic restart/retry/cold rerun. A later explicit task must review restart limitations or authorize a new cold rerun in a fresh namespace. Do not overwrite this execution directory. A24h wall guard is operational protection, not the6.1h projection; there is no step-count or online steady stopping rule.
''')
post={'preparation_id':P.name,'execution':'AFTER_PRODUCTION_ONLY','script':str(P/'postprocess_production.py'),'command_argv':['python3','-B',str(P/'postprocess_production.py'),'--case',plan['case'],'--output',str(P/'postprocessing'),'--times','all','--log',str(P/'execution/log.foamRun')],
'cold_and_saved_state_selection':'all fully saved rank-consistent states including cold0; use actual uniform/time.value and index',
'QoI':['Nu_hot(t)','Nu_cold(t)','Umax(t)','Wmax(t)','speed_max_m_s(t)','Uz_absmax_m_s(t)'],
'normalization':{'L_m':.1,'alpha_m2_s':1e-5/.71,'DeltaT_K':1,'time':'tstar=alpha*t/L^2','velocity':'Umax/Wmax use L/alpha, benchmark positive component centreline maxima,4097 samples'},
'profiles':['dimensionless centreline Ux at x/L=.5','dimensionless centreline Uy at y/L=.5','theta=T-300 along horizontal/vertical centrelines'],
'symmetry':'180-degree temperature antisymmetry about300K and vector velocity antisymmetry, RMS descriptors',
'conservation_coverage':'native rho volume mass, rho*Cv*(T-Tstd) internal-energy proxy, kinetic energy, wall heat flux and coarse saved-state secants; no native BDF conservation residual or missing e/K history reconstruction',
'log_outputs':['deltaT','Co_mean/max on pre-advance state','pressure/energy/momentum iterations and solves','initial/final residual maxima','continuity local/global/cumulative','native CPU/ClockTime','external per-step launcher markers'],
'baseline_metrics':str(ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000/metrics.json'),'baseline_profiles':str(ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000/centreline_4097.csv'),
'comparison':['relative differences Nu_hot/Nu_cold/Umax/Wmax','centreline velocity RMS/Linf differences','inspect late trajectories and temperature profiles without assuming final=steady'],
'approach_assessment':{'window':'last10% of physical span, at leastlast5 available saved states','descriptors':['relative range','linear slope','relative slope change across window'],'descriptive_stationary_candidate_threshold':.001,'insufficient_history_allowed':True,'not_a_formal_arrival_or_convergence_certificate':True},
'next_review':['verify normal end/final state completeness','verify actual startup and5s write schedule and tstar coverage','generate offline scientific QoI/profile/evolution plots from CSVs','review late stationary/evolving descriptors and final baseline differences','compare mass and energy descriptors with explicitly stated missing-stage-history limitations'],
'validation':'offline late checkpoint reproduces Nu_hot6.2249983769413575 and speed0.03805799912427893;598-step log solves48pressure/24energy perstep; analytic coldstate velocity0 and Nu_hot=Nu_cold=160',
'Q3_EXECUTED':'NO','FORMAL_GATE_J_EXECUTED':'NO','FULL_CONSERVATION_AUDIT':'NO'}
save('production_postprocessing_plan.json',post)
(P/'production_postprocessing_plan.md').write_text(f'''# Offline postprocessing plan

After authorized production completion, run:

```bash
{' '.join(post['command_argv'])}
```

The script reads saved native fields and standard logs, writes to a new analysis directory outside the case, and invokes no CFD/decomposition/reconstruction/exact-evidence backend. Partial interrupted data may be analyzed under a separate output namespace with explicit coverage labels; they are not a completed production result.

Output:transient_QoI.csv with physical time and t*=alpha*t/L²; Nu_hot/cold from fixed-wall adjacent-cell orthogonal gradients; Umax/Wmax as dimensionless positive Ux/Uy centreline maxima by the same4097-point interpolation as the160² steady baseline. Speed norm and out-of-plane Uz are separate quantities. Save4097-point velocity/temperature profiles at each retained state,180-degree symmetry RMS, volume mass, kinetic energy and the reconstructable eConst sensible-energy proxy. Native rho is used when written; cold0 rho alone is reconstructed from the frozen EOS.

The native standard-log parser streams the large log, aggregates pressure/energy/momentum iteration counts, maximum initial/final residuals, local/global/cumulative continuity, dt, and pre-advance Co. Native ClockTime has integer-second granularity; launcher step-start/end monotonic markers give external wall timing. Retain the full log for detailed outer/linear-residual review.

Compare final Nu and centreline maxima/profiles to frozen Route A Ra1e6/160² end_9000 metrics and centreline CSV, with relative QoI and RMS/Linf profile differences. Do not assume final≈steady. Evaluate late trajectories using range and slope over the last10% and at leastlast5 snapshots. A0.1% descriptor threshold only labels STATIONARY_CANDIDATE; short/insufficient history is explicit. This is a diagnostic description, not proof of stationarity, nonlinear convergence, or benchmark validity. Inspect plots afterwards; the script produces reusable CSVs and does not silently advance any scientific gate.

Energy scope: Cv1000*(T-298.15) with native rho and volume, kinetic energy and conductive wall heat at k=mu*Cv/Pr. Saved-state energy secants/trapezoidal heat input are coarse descriptors. Missing native e/K histories and intermediate BDF stages prohibit an exact BDF energy balance or full conservation certificate. No artificial histories are generated. Mass totals and native continuity are reported; processor face conservation was geometrically verified during preparation, not promoted to a transient full audit.

Offline preparation validation used an existing late pilot saved state and598 standard-log steps, plus analytic cold0. Nu_hot and speed reproduce known pilot values; dimensional/component definitions are checked separately. No new physical timestep was executed. A floating-point cell-coordinate sorting issue found during offline validation was corrected using a verified bijective integer lattice mapping.

Q3 and formal GateJ are not run. Formal historical statuses remain unchanged. Post-run tasks are final output/schedule review, QoI/profile/evolution plotting, baseline comparison and coverage-limited mass/energy review.
''')
print('Decision ledgers and postprocessing plans written; no CFD executed.')
