#!/usr/bin/env python3
"""Write verified preparation acceptance and final seals; no CFD."""
import hashlib,json,subprocess
from pathlib import Path
from head_integrity import reviewed_head_guard,verify_package
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
read=lambda n:json.loads((P/n).read_text())
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
plan=read('production_execution_plan.json');case=Path(plan['case']);head=reviewed_head_guard(plan);verify_package(plan)
assert read('nonCFD_validation_summary.json')['result']=='PASS'
assert read('launcher_guard_validation.json')['result']=='PASS'
assert read('launcher_dry_validation.json')['DRY_VALIDATION']=='PASS'
assert read('postprocessing_dry_validation.json')['result']=='PASS'
assert read('source_Co05_reference_integrity.json')['result']=='PASS'
assert read('co05_vs_co025_input_diff.json')['unintended_differences']==[]
assert read('production_authorization_draft.json')['AUTHORIZED']=='NO'
assert not Path(plan['runtime_output']).exists()
m=read('production_input_manifest.json');assert {str(f.relative_to(case)) for f in case.rglob('*') if f.is_file()}==set(m['case_files_sha256'])
assert all(sha(case/rel)==h for rel,h in m['case_files_sha256'].items())
for base in [case]+[case/f'processor{i}' for i in range(12)]:
 times=[]
 for directory in base.iterdir():
  if not directory.is_dir():continue
  try:times.append(float(directory.name))
  except ValueError:pass
 assert times==[0.]
authority=read('source_Co05_comparison_authority.json');storage=read('storage_projection.json');assert storage['disk_capacity_pass']
central_bytes=round(storage['scenarios'][0]['projected_total_bytes']+(storage['central_steps']-280000)/20000*(storage['scenarios'][1]['projected_total_bytes']-storage['scenarios'][0]['projected_total_bytes']))
status={
 'ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION_PREPARATION':'COMPLETE','PRODUCTION_PREPARATION_ID':P.name,'SOURCE_CO05_PRODUCTION':'co05_20261006_0602','SOURCE_CO05_STATUS':'COMPLETE','SOURCE_CO05_FINAL_TSTAR':2.000006172635985,'CURRENT_REVIEWED_HEAD':head,'PRODUCTION_SENSITIVE_HEAD_CHANGE':'NO',
 'PHYSICAL_MODEL_CHANGED_FROM_CO05':'NO','GRID_CHANGED_FROM_CO05':'NO','FVSCHEMES_CHANGED_FROM_CO05':'NO','FVSOLUTION_CHANGED_FROM_CO05':'NO','TIME_SCHEME_CHANGED_FROM_CO05':'NO','PIMPLE_POLICY_CHANGED_FROM_CO05':'NO','LINEAR_SOLVER_POLICY_CHANGED_FROM_CO05':'NO','OUTPUT_POLICY_CHANGED_FROM_CO05':'AUXILIARY_STARTUP_SAMPLING_ONLY: physical-time targets plus first cap/Co-control; native dictionaries identical',
 'MAX_CO_CO05':.5,'MAX_CO_CO025':.25,'INTENDED_NUMERICAL_DIFFERENCE':'MAX_CO_ONLY','RA':'1e6','PR':.71,'GRID':'160x160x1','MPI_RANKS':12,'MPI_DECOMPOSITION':'scotch','PREF_REFERENCE_METHOD':'pRefPoint','PREF_POINT':'(0.0496875 0.0496875 0.0005)','TIME_SCHEME':'backward_variable_step_BDF2','INITIAL_DELTA_T':2.3111979166666666e-5,'MAX_DELTA_T':.027734375,'END_TIME_SECONDS':1420,'TARGET_TSTAR':2,'PRODUCTION_START_MODE':'CONTINUOUS_COLD_START','STRICT_BDF_RESTART_RELIED_UPON':'NO','HEAVY_DIAGNOSTICS_ENABLED':'NO','FUNCTION_OBJECTS_DURING_PRODUCTION':'NO','OUTPUT_WRITE_CONTROL':'runTime','FULL_FIELD_OUTPUT_INTERVAL_SECONDS':5,'OUTPUT_POLICY_CHANGES_DELTAT':'NO',
 'EXPECTED_PRODUCTION_STEPS':'280000–300000; central286406, frozen-Co05-state proxy286353; unmeasured Co025','EXPECTED_PRODUCTION_RUNTIME_HOURS':'4–6; central4.66710967995 at Co05 mean cost','EXPECTED_OUTPUT_BYTES':central_bytes,'EXPECTED_OUTPUT_BYTES_PLANNING_RANGE':[storage['scenarios'][0]['projected_total_bytes'],storage['scenarios'][1]['projected_total_bytes']],'CONSERVATIVE_320K_OUTPUT_BYTES':storage['scenarios'][2]['projected_total_bytes'],
 'DISK_CAPACITY_PASS':'YES','CHECKMESH':'PASS','DECOMPOSITION_PREPARATION':'PASS','PREF_POINT_MAPPING_VERIFIED':'YES','CO05_TO_CO025_INPUT_DIFF_AUDIT':'PASS','POSTPROCESSING_PLAN_PREPARED':'YES','CO05_VS_CO025_TSTAR_COMPARISON_PREPARED':'YES','PRODUCTION_LAUNCHER_PREPARED':'YES','PRODUCTION_LAUNCHER_DRY_VALIDATED':'YES','PRODUCTION_CFD_EXECUTED':'NO','PRODUCTION_EXECUTION_AUTHORIZED':'NO','Q3_EXECUTED':'NO','FORMAL_GATE_J_EXECUTED':'NO','CO025_PRODUCTION_PREPARATION_READY':'YES','BLOCKER':'NONE','NEXT_SINGLE_TASK':'RUN_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / high','USER_DECISION_REQUIRED':'YES',**authority['scientific_status_unchanged']}
report={'status':status,'scientific_purpose':'fixed-grid time-step sensitivity between Co0.5 and Co0.25','classification':'PREPARATION_ONLY_NO_PHYSICAL_ADVANCEMENT','source_reference_integrity':read('source_Co05_reference_integrity.json'),'source_Co05_QoI_authority':authority,'case_diff':read('co05_vs_co025_input_diff.json'),'input_manifest':str(P/'production_input_manifest.json'),'sensitive_manifest':str(P/'production_sensitive_manifest.json'),'head_review':read('head_review.json'),'validation':read('nonCFD_validation_summary.json'),'launcher_dry':read('launcher_dry_validation.json'),'launcher_guards':read('launcher_guard_validation.json'),'postprocessing_dry':read('postprocessing_dry_validation.json'),'storage_projection':storage,'startup_sampling':{'physical_targets_s':plan['startup_write_physical_times_s'],'additional_events':plan['startup_additional_events'],'regular_native_output_unchanged':True,'signals_IO_only':True,'asynchronous_actual_times_must_be_reviewed_after_run':True,'maximum_additional_requests':12},'execution_plan':plan,'postprocessing_plan':read('production_postprocessing_plan.json'),'limits':['two levels do not prove temporal convergence or time-step independence','no full BDF conservation certificate','strict restart identity not relied upon','formal statuses unchanged','actual Co025 dt/steps/runtime/QoIs unknown until separately authorized production']}
(P/'RouteA_plain_transient_Co025_production_preparation.json').write_text(json.dumps(report,indent=2)+'\n')
block='\n'.join(f'{k} = {v}' for k,v in status.items())
scenarios=''.join(f"| {x['steps']} | {x['projected_log_bytes']/1e9:.3f} GB | {x['projected_total_bytes']/1e9:.3f} GB | {x['hours_at_Co05_mean_seconds_per_step']:.3f} h |\n" for x in storage['scenarios'])
body=f'''# Route A Co0.25 plain transient production preparation

**READY. Preparation only; CFD executed:NO, authorization:NO.** ID:{P.name}. One future Ra1e6/Pr0.71/160×160×1/12-rank continuous cold-start series targets native endTime1420 / t*≈2. No physical step, pilot, rerun, Q3, GateJ,320 grid or particle coupling was executed.

Co0.5 reference integrity PASS: original cold inputs, installed binaries/sources, canonical authority hashes and all report/execution/postprocessing seals matched. Reviewed HEAD:{head}. Local Git range from83a910 added376 result files and changed.gitignore only to ignore log.foamRun; the full untracked3.870570559GB native log was independently hash-verified. HEAD provenance is distinct from input integrity. Future reviewed results-only descendant commits may proceed after byte verification; sensitive/unknown changes fail closed.

The164-file cold/decomposed input audit found exactly one differing file,system/controlDict, containing only maxCo0.5→0.25. Physical and thermophysical inputs, mesh, initial fields, fvSchemes, fvSolution, backward time scheme, PIMPLE, linear solvers, initial dt,maxdt,endTime and native output policy are byte-identical. No source runtime trajectory was copied. Frozen Co0.5 scotch12 decomposition was reused byte-identically; serial/12-rank checkMesh PASS, addressing covers25600 cells exactly once, pRefPoint lies strictly within rank3/local2107/global12719. Native MPI12 affinity probe confirms12 distinct physical cores and all thread settings1; no scaling study.

Future exact command (through prepared launcher after a separate explicit run-task receipt; do not execute in this preparation):

```bash
{plan['command_shell']}
```

OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1. Heavy/exact/matrix/replay/audit backends OFF; functions{{}} and-noFunctionObjects. Cold0 is300K and zero velocity; same hot300.5/cold299.5 walls. Ra1e6,Pr0.71,L0.1m,depth0.001m,rho0=1,beta0.001,mu1e-5,Cv1000,nu1e-5,alpha=1e-5/0.71,k0.014084507042253521,g=(0,-140.8450704225352,0), Boussinesq/eConst/Stokes/Fourier/laminar remain unchanged. PIMPLE24 outer/2 correctors/0 nonorthogonal; U/e PBiCGStab+DILU and p_rgh PCG+DIC tol1e-12/relTol0 retain actual maxIter dictionaries, with no relaxation/tuning.

Native adaptive control: backward variable-step BDF2, adjustTimeStep true, maxCo0.25,growth1.2, initial dt2.3111979166666666e-5 unchanged,maxdt0.027734375 unchanged. Co is logged before next-dt adjustment; configured maxCo is not a strict bound on the pre-adjustment printed value. Future offline checks must retain logged values and audit controller alignment. Inference from Co0.5 late Co≈0.5/dt≈0.009929812304467326 predicts late dt≈{storage['Co025_expected_late_dt_s']:.17g}; actual Co0.25 trajectory is unknown. Cold growth regime and transition may differ. Primary scientific stop is native endTime1420 only, not step count or steady-looking behavior. Native final step may be slightly above/below1420 under its half-dt predicate; actual uniform/time values and all-rank final fields must agree.24h guard; interruption STOP_AND_REVIEW with no automatic restart/cold rerun.

Regular output unchanged: runTime5s,ASCII,no compression,timePrecision12,writePrecision17,purgeWrite0. Output never changes dt. Supplemental startup sampling changes only IO: Co0.5 actual physical times {plan['startup_write_physical_times_s']}, plus first maxdt if reached and first Co-control event. Native SIGUSR1 is sent only to verified rank0 after logged handler activation. Multiple triggered targets can share one request; asynchronous actual saved times/indices must be audited. Maximum12 additional requests plus284 regular bins gives≤296 saved output states, pluscold0. No step-index matching is used for scientific history comparison.

PLANNING estimates:280k–300k steps, central286406; inverse-flux integration on frozen Co0.5 saved log states gives≈{storage['Co05_fixed_state_inverse_flux_step_proxy']:.3f}. This is not a Co0.25 controller/trajectory simulation. Runtime4–6h, central{storage['central_hours_at_Co05_average_cost']:.6f}h from measured Co0.5 average; pressure cost fell from early1000 median2383 to late median35 iterations/step, so Co0.25 cost remains uncertain. Planning values are not stopping limits.

MEASURED Co0.5 log bytes/step={storage['Co05_measured_log_bytes_per_step']:.6f}. Native fields≈{storage['scenarios'][0]['projected_native_fields_allocated_bytes']/1e9:.3f}GB at≤296 snapshots; extra steps mainly grow logs.

| planning steps | projected log | fields+log+markers+offline budget | runtime at Co05 mean cost |
|---:|---:|---:|---:|
{scenarios}

Minimum32GiB free prelaunch and8GiB runtime low watermark retained. Conservative320k estimate plus25% margin plus low watermark={storage['conservative_projection_with_25percent_margin_plus_low_watermark_bytes']/1024**3:.3f}GiB<32GiB. Measured prepared-host free space={storage['current_free_bytes']/1024**3:.3f}GiB. Storage PASS; no purge/thinning is planned. Launcher validates cold fileset, dictionaries, binaries/source/PATH/library identity, MPI version/binding policy, source authorities, no active same-case solver, unused execution namespace, RAM/disk, package hashes and separate explicit authorization. NO draft cannot authorize production; fail-closed negative checks PASS.

Offline comparison command after normal completion: `{' '.join(read('production_postprocessing_plan.json')['command_argv'])}`. First reconstruct all fully saved fields using the unchanged prepared Co0.5 postprocessor. Match physical time/t*,never step index. Piecewise linear interpolation uses union of both saved t* axes and overlap endpoints/late boundary, with extrapolation:NO; record actual common time range. Report direct final signed/absolute/relative Nu_hot,Nu_cold,Umax,Wmax differences and final-native time mismatch; maximum/sample-RMS/time-weighted-RMS histories, last10% common-window differences, final U/W/theta profile RMS/Linf. Sparse output interpolation does not measure unsaved extrema. Retain same-grid end_9000 steady comparison. Last10% and≥5 snapshots uses range/slope with descriptive0.001 threshold for STATIONARY_CANDIDATE/STILL_EVOLVING; it is not a stationarity proof.

Mass/energy follow the same coverage-limited method: native rho-volume mass, Cv*(T−298.15) sensible proxy, kinetic energy, wall heat, coarse saved-state secants and native continuity. Missing native intermediate/e-K histories prohibit exact BDF conservation certification. Original source/postprocessing evidence remains unchanged. Dry checks verified analytic coldNu160/U=W=0, zero Co0.5 self-comparison, staggered linear interpolation, no extrapolation and fail-closed sensitive/draft/rank/maxCo guards. Preparation-only corrections are documented in preparation_dry_corrections.json.

This two-level study can describe fixed-grid sensitivity; it cannot prove full temporal convergence/time-step independence. If measured final/late QoIs, profiles or resolved transient histories materially differ (descriptive0.1% trigger, not formal acceptance), or sensitivity remains unresolved, review whether Co0.125 is useful after excluding sampling/horizon uncertainty. Co0.125 is not predetermined or authorized. Formal statuses stay frozen.

Next exact task:RUN_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION, recommended gpt-6.1-sol/high. User decision required:YES. Production has not started.

```text
{block}
```
'''
(P/'RouteA_plain_transient_Co025_production_preparation.md').write_text(body)
(P/'final_status.txt').write_text(block+'\n')
(P/'git_status_final.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
(P/'git_diff_stat_final.txt').write_text(subprocess.check_output(['git','diff','--stat'],cwd=ROOT,text=True))
seal={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='preparation_artifact_manifest_sha256.json'}
(P/'preparation_artifact_manifest_sha256.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(status,indent=2))
