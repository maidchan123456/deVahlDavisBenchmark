#!/usr/bin/env python3
"""Report measured completed production and preserve all original evidence."""
import hashlib,json,subprocess
from pathlib import Path
V2=Path(__file__).resolve().parent;P=V2.parent;ROOT=P.parents[3];OUT=P/'postprocessing_v2';RUN=P/'execution_v2'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(OUT/'production_analysis_summary_v2.json');r=s['runtime'];q=s['final_QoI'];c=s['comparison'];a=s['late_time_assessment'];d=s['mass_energy'];review=read(V2/'head_change_review.json');plan=read(V2/'production_execution_plan_v2.json')
assert read(RUN/'execution_result.json')['status']=='COMPLETED_NATIVE_ENDTIME'
for rel,digest in review['original_artifacts_sha256'].items():assert sha(P/rel)==digest
inputs=read(P/'production_input_manifest.json');case=Path(inputs['case']);assert all(sha(case/rel)==digest for rel,digest in inputs['case_files_sha256'].items())
for path,digest in read(V2/'production_sensitive_manifest_v2.json')['files_sha256'].items():assert sha(Path(path))==digest
history=read(P/'RouteA_plain_transient_Co05_production_preparation.json')['scientific_status_unchanged']
next_task='REVIEW_ROUTE_A_TRANSIENT_TIME_HORIZON' if a['tstar2_time_horizon']=='STILL_EVOLVING' else 'ANALYZE_ROUTE_A_CO05_TRANSIENT_VS_STEADY' if max(c[k]['absolute_relative_difference'] for k in ['Nu_hot','Nu_cold','Umax','Wmax'])>.01 else 'PREPARE_ROUTE_A_PLAIN_TRANSIENT_CO025_PRODUCTION_RUN'
status={'ROUTE_A_CO05_HEAD_CHANGE_REVIEW':'PASS','OLD_PREPARATION_HEAD':review['old_preparation_head'],'REVIEWED_EXECUTION_HEAD':review['current_reviewed_head'],'HEAD_CHANGED':'YES','HEAD_CHANGE_PRODUCTION_SENSITIVE':'NO','PRODUCTION_SENSITIVE_MANIFEST_MATCH':'PASS','HEAD_REPINNED':'YES','V2_PREFLIGHT':'PASS','PRODUCTION_EXECUTION_AUTHORIZED':'YES','ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION':'COMPLETE','PRODUCTION_CFD_EXECUTED':'YES','PRODUCTION_NORMAL_EXIT':'YES','PHYSICAL_MODEL_CHANGED':'NO','NUMERICAL_POLICY_CHANGED':'NO','GRID':'160x160x1','RA':'1e6','PR':.71,'MAX_CO':.5,'MPI_RANKS':12,'HEAVY_DIAGNOSTICS_ENABLED':'NO','FUNCTION_OBJECTS_DURING_PRODUCTION':'NO','PRODUCTION_START_MODE':'CONTINUOUS_COLD_START','STRICT_BDF_RESTART_RELIED_UPON':'NO','ACTUAL_FINAL_TIME_SECONDS':r['final_time_seconds'],'ACTUAL_FINAL_TSTAR':r['final_tstar'],'COMPLETED_PHYSICAL_STEPS':r['completed_physical_steps'],'TOTAL_PRODUCTION_WALL_HOURS':r['total_wall_hours'],'EXPECTED_RUNTIME_HOURS':plan['expected_runtime_hours'],'RUNTIME_RATIO_ACTUAL_TO_PROJECTED':r['actual_to_projected'],'MAX_LOGGED_CO':r['max_logged_Co'],'LATE_MEDIAN_DELTA_T':r['late_deltaT_seconds']['median'],'LATE_MEDIAN_SECONDS_PER_STEP':r['late_external_seconds_per_step_excluding_native_writes']['median'],'FINAL_NU_HOT':q['Nu_hot'],'FINAL_NU_COLD':q['Nu_cold'],'FINAL_UMAX':q['Umax'],'FINAL_WMAX':q['Wmax'],'FINAL_VS_STEADY_NU_RELATIVE_DIFFERENCE':c['Nu_hot']['relative_difference'],'FINAL_VS_STEADY_UMAX_RELATIVE_DIFFERENCE':c['Umax']['relative_difference'],'FINAL_VS_STEADY_WMAX_RELATIVE_DIFFERENCE':c['Wmax']['relative_difference'],'LATE_NU_BEHAVIOR':a['late_QoI']['Nu_hot']['classification'],'LATE_UMAX_BEHAVIOR':a['late_QoI']['Umax']['classification'],'LATE_WMAX_BEHAVIOR':a['late_QoI']['Wmax']['classification'],'TSTAR2_TIME_HORIZON_ASSESSMENT':a['tstar2_time_horizon'],'POSTPROCESSING_COMPLETED':'YES',**history,'Q3_EXECUTED':'NO','NEXT_SINGLE_TASK':next_task,'USER_DECISION_REQUIRED':'YES'}
field_files=[f for base in case.glob('processor[0-9]*') for directory in base.iterdir() if directory.is_dir() and directory.name not in ['0','constant','system'] for f in directory.rglob('*') if f.is_file()]
actual_storage={'native_output_files':len(field_files),'native_output_logical_bytes':sum(f.stat().st_size for f in field_files),'native_output_allocated_bytes':sum(f.stat().st_blocks*512 for f in field_files),'full_stdout_stderr_log_bytes':(RUN/'log.foamRun').stat().st_size}
actual_storage['fields_plus_log_allocated_bytes']=actual_storage['native_output_allocated_bytes']+(RUN/'log.foamRun').stat().st_blocks*512
report={'status':status,'classification':['PLAIN_TRANSIENT_CO05_PRODUCTION','FLUID_ONLY_DIAGNOSTIC_TRANSIENT_RESULT'],'runtime':r,'final_QoI':q,'baseline_comparison':c,'late_time':a,'mass_energy_symmetry_descriptors':d,'head_review':str(V2/'head_change_review.json'),'previous_0step_blocked_attempt_preserved':True,'all_original_package_hashes_unchanged':True,'initial_sensitive_case_files_unchanged':True,'actual_storage':actual_storage,'scientific_status_unchanged':history,'claim_labels':{'MEASURED':['native normal exit/returncode','completed physical steps','external total/perstep wall','full standard log/Co/dt/iterations/continuity'],'POSTPROCESSED':['native saved-state QoIs','profiles','mass/energy/symmetry descriptors','steady comparison'],'DERIVED':['dimensionless time','signed/absolute relative differences'],'INFERRED':['stationary-candidate/evolving descriptors and current diagnostic horizon adequacy'],'UNKNOWN':['grid-independent transient','time-step sensitivity','formal benchmark validity','exact BDF conservation certificate','strict restart identity']},'next_task_reason':'Review evolving horizon first' if a['tstar2_time_horizon']=='STILL_EVOLVING' else 'Inspect material transient-versus-steady differences first' if next_task=='ANALYZE_ROUTE_A_CO05_TRANSIENT_VS_STEADY' else 'A stationary candidate close to the same-grid baseline makes a separate Co0.25 preparation a useful next time-step sensitivity task; no second run is authorized or started.'}
report['native_Co_controller_alignment']=read(OUT/'native_Co_controller_alignment_v2.json')
report['offline_analysis_repair']={'initial_error':read(V2/'offline_analysis_initial_attempt_v2.json')['failure'],'repaired_source':'analyze_completed_v2_revision1.py','prepared_postprocessor_returncode':0,'prepared_postprocessor_repeated':False,'original_sources_preserved':True,'CFD_repeated':False}
(V2/'RouteA_plain_transient_Co05_production_report_v2.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
block='\n'.join(f'{k} = {v}' for k,v in status.items())
rows=''.join(f"| {key} | {c[key]['transient_final']:.12g} | {c[key]['steady_baseline']:.12g} | {c[key]['relative_difference']:+.6g} | {c[key]['absolute_relative_difference']:.6g} |\n" for key in ['Nu_hot','Nu_cold','Umax','Wmax'])
body=f'''# Route A Co0.5 diagnostic transient production v2

**COMPLETE, native returncode0, postprocessing completed.** One continuous cold-start Ra1e6/Pr0.71/160×160×1/maxCo0.5/12-rank plain OpenFOAM series. No model/numerical/controller/output changes, heavy diagnostics, function objects, restart/rerun, extension, Co0.25, Q3 or formal GateJ.

MEASURED: {r['completed_physical_steps']} completed physical steps in {r['total_wall_seconds']:.6f}s ({r['total_wall_hours']:.6f}h). Final native t={r['final_time_seconds']:.17g}s; DERIVED t*={r['final_tstar']:.17g}. endTime1420 was a native threshold, with no timestep adjustment to force exact1420. Native runTime bin284 saved the final step; all284 regular bins and rank snapshot sets match, and final native fields are finite. Full stdout/stderr and bindings remain in execution_v2/log.foamRun.

MEASURED runtime/projected6.112102h={r['actual_to_projected']:.6g}. The prediction was planning-only; measured cost changed through the production. Late10% dt(min/median/max)={r['late_deltaT_seconds']}; logged Co={r['late_logged_Co']}; overall maxloggedCo={r['max_logged_Co']:.12g}. Co is reported for the native pre-advance state; configured maxCo0.5 was unchanged. Late non-write external wall/step={r['late_external_seconds_per_step_excluding_native_writes']}. Native ClockTime has integer-second granularity; precise per-step costs use launcher monotonic end markers, excluding actual native write steps.

Pressure iterations/step early1000={r['pressure_iterations_early1000']}; last10%={r['pressure_iterations_last10percent']}. Late energy iterations={r['energy_iterations_last10percent']}. Fixed48 pressure and24 energy solves perstep={r['all_steps_pressure48_energy24']}. This describes linear solver cost and residuals, not nonlinear convergence or physical validation. No fatal/NaN/FPE was detected; completed native fields/logs support gross solver sanity. Individual residual/continuity/iteration histories remain in production_step_history.csv.

POSTPROCESSED same-grid steady end_9000 comparison, with signed and absolute relative differences kept separate:

| QoI | transient final | steady160² | signed relative difference | absolute relative difference |
|---|---:|---:|---:|---:|
{rows}

Umax and Wmax are dimensionless positive Ux/Uy centreline maxima using the same4097-point interpolation as the baseline. They are not the speed norm or out-of-plane component. Final speed={q['speed_max_m_s']:.12g}m/s; |Uz|max={q['Uz_absmax_m_s']:.12g}m/s. Centreline RMS/Linf differences are in steady_comparison.json; velocity/temperature profiles at every stored state remain in CSVs.

INFERRED late behavior: {a['tstar2_time_horizon']}. Last10% of saved history and physical span, with at least5 samples, uses relative range and slope with descriptive0.001 thresholds. Per-QoI descriptors/classifications={json.dumps(a['late_QoI'])}. STATIONARY_CANDIDATE means approximate stability under these descriptors; it is not stationarity proof. The final state was compared to steady without assuming agreement. No simulation was extended after the requested horizon.

POSTPROCESSED mass: {json.dumps(d['mass'])}. These are native rho-volume totals and standard continuity descriptors, not an exact transient FV mass audit. Energy: {json.dumps(d['energy'])}. Native intermediate stages and e/K histories are missing on disk; coarse stored-state energy secants/wall heat are limited descriptors, not an exact BDF conservation certificate. No artificial histories were generated. Symmetry: {json.dumps(d['symmetry'])}.

HEAD lesson: old preparation {review['old_preparation_head']} remains intact, including its historical fixed HEAD and NO authorization draft. Local Git range to {review['current_reviewed_head']} added63 preparation/blocked evidence files only; independent sensitive hashes matched. V2 safely reviewed/pinned current provenance and hashes without changing native execution-loop AST. HEAD provenance and production input integrity are separate guards: a reviewed results-only commit does not require stopping CFD automatically; altered physics/numerics/runtime/script identities fail closed. Original0step blocked evidence remains unchanged.

Actual storage: {json.dumps(actual_storage)}. All native output fields/histories were retained; no purge/thinning. Formal historical statuses remain unchanged; simulation completion does not validate the physical model, provide grid/time-step independence, authorize formalGateJ, or make downstream/particles ready.

Figures:

![QoI history]({OUT/'QoI_vs_tstar.png'})

![Native log history]({OUT/'native_log_vs_tstar.png'})

![Representative profiles]({OUT/'representative_profiles.png'})

![Final vs steady profiles]({OUT/'final_vs_steady_profiles.png'})

Next single task: {next_task}. {report['next_task_reason']} User decision required:YES.

```text
{block}
```
'''
body+=f'''
Offline analysis repair: the first added summary script omitted the existing Scripts/routeA module search path. The prepared postprocessor had already completed with returncode0. A separate revision1 completed field-integrity checks and summaries using the retained prepared CSVs; neither CFD nor prepared postprocessing was repeated. Original source, exception record, pre-repair output hashes and revision source hashes remain in head_review_v2.

Native Co alignment: maximum logged Co=0.5172179551948343 was reported before step62 at pre-advance t≈0.778190853453s with previous dt=0.026729878902837508s. Native preSolve reports Co before adjusting dt; selected new dt=0.02584005314816309s rescales the same pre-advance-state Co to0.5. All143203 selected dt values exactly match min(1.2×previous_dt, maxDeltaT, maxCo/logged_Co×previous_dt) in the parsed floating values. There are6539 logged values above0.5+1e-9, the last before step13839 (new-step t≈135.444142532231s); late Co remains≈0.5. This derived pre-advance rescaling is not a post-solve Courant guarantee. No controller, physics or numerical policy was changed. Evidence: postprocessing_v2/native_Co_controller_alignment_v2.json.
'''
(V2/'RouteA_plain_transient_Co05_production_report_v2.md').write_text(body)
(V2/'final_status_v2.txt').write_text(block+'\n')
for args,name in [(['git','status','--short'],'git_status_final_v2.txt'),(['git','diff','--stat'],'git_diff_stat_final_v2.txt')]:
 (V2/name).write_text(subprocess.check_output(args,cwd=ROOT,text=True))
for folder,name in [(RUN,'execution_artifact_manifest_sha256.json'),(OUT,'postprocessing_artifact_manifest_sha256.json'),(V2,'final_v2_artifact_manifest_sha256.json')]:
 (folder/name).write_text(json.dumps({str(f.relative_to(folder)):sha(f) for f in sorted(folder.rglob('*')) if f.is_file() and f.name!=name},indent=2)+'\n')
print(json.dumps(status,indent=2))
