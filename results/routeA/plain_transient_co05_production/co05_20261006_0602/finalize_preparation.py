#!/usr/bin/env python3
"""Finalize preparation-only reports and read-only final verification."""
import ast,datetime,hashlib,json,os,subprocess
from pathlib import Path
import production_launcher as launch
P=Path(__file__).resolve().parent;ROOT=P.parents[3];CASE=Path(launch.read('production_execution_plan.json')['case'])
LATE=ROOT/'results/routeA/transient_cfd_late_window_pilot/late_20261006_0531'
sha=launch.sha
save=lambda n,v:(P/n).write_text(json.dumps(v,indent=2)+'\n')
plan=launch.check();dry=launch.read('production_launcher_dry_validation.json');assert dry['result']=='PASS'
for f in P.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
assert subprocess.run(['bash','-n',str(P/'run_production.sh')]).returncode==0
check=subprocess.run([str(P/'run_production.sh'),'--check'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(P/'log.launcher_check').write_text(check.stdout);assert check.returncode==0
# All prior late-pilot artifacts remain untouched, not only the selected report hashes.
late_seal=json.loads((LATE/'artifact_manifest_sha256.json').read_text())
assert all(sha(LATE/rel)==expected for rel,expected in late_seal.items())
assert launch.read('production_authorization_draft.json')['AUTHORIZED']=='NO'
assert not (P/'execution').exists()
assert all(float(sub.name)==0 for base in [CASE]+list(CASE.glob('processor[0-9]*')) for sub in base.iterdir() if sub.is_dir() and __import__('re').fullmatch(r'[0-9.eE+-]+',sub.name))
commands=launch.read('preparation_commands.json')
assert not any(Path(arg).name=='foamRun' for record in commands for arg in record['argv'])
assert all(record['returncode']==0 for record in commands)
assert 'Mesh OK.' in (P/'log.checkMesh').read_text() and 'Mesh OK.' in (P/'log.checkMesh.parallel').read_text()
status={'ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION_PREPARATION':'COMPLETE','PRODUCTION_PREPARATION_ID':P.name,'SOURCE_LATE_PILOT':'late_20261006_0531',
'CANONICAL_AUTHORITY_HASH_VERIFIED':'YES','FORMAL_AUTHORITY_HASH_VERIFIED':'YES','PHYSICAL_MODEL_CHANGED':'NO','NUMERICAL_POLICY_CHANGED':'NO',
'GRID':'160x160x1','RA':'1e6','PR':.71,'MAX_CO':.5,'MPI_RANKS':12,'MPI_DECOMPOSITION':'scotch','MPI_BINDING_VERIFIED':'YES',
'PREF_REFERENCE_METHOD':'pRefPoint','PREF_POINT':'(0.0496875 0.0496875 0.0005)','PREF_POINT_MAPPING_VERIFIED':'YES',
'TIME_SCHEME':'backward_variable_step_BDF2','INITIAL_DELTA_T':2.3111979166666666e-5,'MAX_DELTA_T':.027734375,'END_TIME_SECONDS':1420,'TARGET_TSTAR':2,
'TIME_PRECISION':12,'WRITE_PRECISION':17,'HEAVY_DIAGNOSTICS_ENABLED':'NO','EXACT_EVIDENCE_BACKEND_ENABLED':'NO','FUNCTION_OBJECTS_DURING_PRODUCTION':'NO',
'PRODUCTION_START_MODE':'CONTINUOUS_COLD_START','STRICT_BDF_RESTART_RELIED_UPON':'NO','INTERRUPTION_POLICY':'STOP_AND_REVIEW',
'OUTPUT_WRITE_CONTROL':'runTime','FULL_FIELD_OUTPUT_INTERVAL_SECONDS':5,'OUTPUT_POLICY_CHANGES_DELTAT':'NO','EXPECTED_FULL_FIELD_SNAPSHOTS':'284 regular + up to10 startup =294 upper bound, cold0 additional',
'EXPECTED_OUTPUT_BYTES':'8337589008 fields+log estimate; small metadata/postprocessing extra','EXPECTED_OUTPUT_FILES':'42336 field/state files +1 log +5 metadata =42342 upper bound; postprocessing additional',
'DISK_CAPACITY_PASS':'YES','FINAL_STATE_WRITE_METHOD':'NATIVE_RUN_TIME_BIN_ENDTIME_MULTIPLE(bin284)','FINAL_STATE_WRITE_VERIFIED_BY_SOURCE_REVIEW':'YES',
'CHECKMESH':'PASS','DECOMPOSITION_PREPARATION':'PASS','PRODUCTION_LAUNCHER_PREPARED':'YES','PRODUCTION_LAUNCHER_DRY_VALIDATED':'YES','POSTPROCESSING_PLAN_PREPARED':'YES',
'EXPECTED_PRODUCTION_STEPS':'~180000-200000 planning only, not a stopping rule','EXPECTED_PRODUCTION_RUNTIME_HOURS':'~6.1 (late-window projection, not guarantee)',
'PRODUCTION_CFD_EXECUTED':'NO','PRODUCTION_EXECUTION_AUTHORIZED':'NO','Q3_EXECUTED':'NO','FORMAL_GATE_J_EXECUTED':'NO','CO05_PRODUCTION_PREPARATION_READY':'YES',
'BLOCKER':'NONE','NEXT_SINGLE_TASK':'RUN_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / high','USER_DECISION_REQUIRED':'YES'}
history=json.loads((LATE/'RouteA_plain_transient_late_window_performance_pilot.json').read_text())['scientific_status_unchanged'];history['FORMAL_GATE_J_PASS']='NOT_EVALUATED'
checks={k:'PASS' for k in ['authority_hashes','expected_HEAD','late_full_artifact_seal_unchanged','cold_initial_field_hashes','physical_constants_and_grid_pinned','fvSolution_fvSchemes_bytes_frozen','backward_BDF2','PIMPLE24_2_0','pressure_pRefPoint_only','12rank_scotch_decomposition','all_cells_mapped_once','processor_interface_pair_geometry','MPI12_distinct_physical_cores','global_and_parallel_checkMesh','heavy_diagnostics_absent','functions_empty_and_cli_disabled','precision12_17','endTime1420_Co05_frozen_dt','runTime_output_does_not_adjust_dt','storage_capacity','source_and_arithmetic_final_write','continuous_cold_policy','restart_limitations','dry_launcher_preflight_and_rejection','offline_postprocessing_validation','no_solver_or_physical_timestep','authorization_remains_NO','execution_namespace_absent']}
report={'preparation_id':P.name,'created_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'scientific_status_unchanged':history,
'expected_HEAD':plan['expected_HEAD'],'case':str(CASE),'results':str(P),'checks':checks,'source_late_artifact_count_reverified':len(late_seal),
'authority_hashes':{k:v for k,v in launch.read('source_reference_guard.json').items() if k.startswith('docs/')},
'exact_production_command':plan['command_shell'],'command_cwd':plan['cwd'],'environment_overrides':plan['environment_overrides'],
'execution_plan':str(P/'production_execution_plan.json'),'execution_plan_sha256':sha(P/'production_execution_plan.json'),
'input_manifest_sha256':sha(P/'production_input_manifest.json'),'output_decision':launch.read('storage_and_cadence_decision.json'),
'final_write':launch.read('final_write_decision_ledger.json'),'restart':launch.read('restart_decision_ledger.json'),
'launcher_validation':dry,'postprocessing':launch.read('production_postprocessing_plan.json'),
'preparation_only_changes':['isolated validated cold case cloned','controlDict endTime/writeControl/writeInterval only changed relative to accepted pilot','native non-CFD decomposition','new preparation/launcher/postprocessing artifacts'],
'minor_preparation_fixes':['floating-point geometry centre sorting replaced by verified integer lattice mapping during offline postprocessing validation','native Time header unit suffix s accepted by launcher parser','floating-point exception trapping startup message distinguished from actual FPE','required final AUTO_WRITE fields match native pilot; e/K intentionally not assumed written'],
'limitations':['No production trajectory or transient stationarity evidence yet','6.1121h and~189795 steps are late-window extrapolations; cost/dt can evolve','5s output does not guarantee resolution of all temporal oscillations; startup writes mitigate initial undersampling','Final native time is near1420, not forciblyexact1420','Stored native outputs do not certify full-BDF restart or exact mass/energy audit','Formal benchmark/grid-independence/downstream readiness remain unchanged']}
save('RouteA_plain_transient_Co05_production_preparation.json',report)
finalblock='\n'.join(f'{k} = {v}' for k,v in status.items())
(P/'final_status.txt').write_text(finalblock+'\n')
body=f'''# Route A Co0.5 production preparation

**COMPLETE; CO05_PRODUCTION_PREPARATION_READY=YES; PRODUCTION_EXECUTION_AUTHORIZED=NO.** PreparationID:{P.name}. No foamRun invocation, pilot, physical timestep, Q3 or GateJ was executed. The new case and12 native processor cases contain cold0 only; the execution namespace is absent.

Frozen HEAD:{plan['expected_HEAD']}. Both specified authority hashes match. The complete{len(late_seal)}-file late_20261006_0531 seal and selected source/baseline/input hashes were reverified. Physical inputs, original160×160×1 mesh, cold fields, fvSolution/fvSchemes and scotch12 policy are frozen. Only the inherited controlDict endTime and output cadence were changed. The authority and all historical cases/results remain unmodified.

Case:{CASE}

Exact future command (cwd={CASE}, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1):

```bash
{plan['command_shell']}
```

Ra1e6,Pr0.71,0.1×0.1×0.001m, original Boussinesq/eConst/Stokes/Fourier, backward variable-step BDF2, nOuter24,nCorrectors2,nNonOrthogonal0,momentumPredictortrue,simpleRhofalse,transonicfalse,consistentfalse and original tight solver dictionaries remain unchanged. maxCo0.5,initialinputdt2.3111979166666666e-5,maxdt0.027734375,growth1.2,adjustTimeSteptrue. The first native controller update can grow the input dt, as it did in the pilot; no new timestep policy is imposed.

Non-CFD checkMesh passed both global and12-rank parallel. Native scotch decomposition covers25600 global cells once, with884 processor-interface face pairs of opposite orientation. Exact prior MPI flags were verified with a12-rank non-CFD affinity probe:each rank has a distinct physical core, with both SMT siblings included by native core binding. Thread counts are1. Reference point(0.0496875,0.0496875,0.0005) maps uniquely inside rank3/local2107/global12719, away from cell planes; no parallel pRefCell is used.

Production ends by native endTime1420 (targett*=2), continuously from cold rest. There is no timestep-count cap, pilot continuation, online stationarity termination, retry, or strict restart dependency. Expected~180000–200000 steps and~6.1121h are late-window projections, not promises or stop limits. The operational guard is24h. Interruption/fatal/nonfinite output/low disk/observer failure/partial final output => INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN, STOP_AND_REVIEW, preserve evidence, await a separate reviewed restart or explicitly authorized fresh cold rerun. Native missing e/K histories preclude a strict-BDF restart claim.

Output:runTime5s, no compression,purgeWrite0,writePrecision17,timePrecision12. Native naming precision may increase automatically.284 regular snapshots plus at most10 native startup write requests =294 output snapshots; cold0 is additional. Startup requests target2,5,10,20,30,39,60,100,250,500, from the preceding Time header using SIGUSR1 after native handler/master verification. Actual saved times/indices are reviewed after execution. Signals only request writes; no dt alteration or normal-end stop signal is used.

Disk estimate:2,943,123,456 allocated field bytes plus5,394,465,552 log bytes =8,337,589,008 bytes (~7.77GiB), with small launcher metadata and offline tables extra. Up to42336 field/state files +1 complete combined stdout/stderr log +5 execution metadata files =42342; postprocessing adds its own CSV/JSON files. Measurement uses actual12-rank late-pilot ASCII snapshots and native log bytes per step. Prelaunch32GiB reserve and runtime8GiB low-watermark passed (~737GiB free). The 2/5/10s comparison and early-time sampling rationale are in output_cadence_decision_ledger.md/json.

Final state:ordinary runTime bin284. The native Time.running threshold and runTime write bin use t+0.5dt;1420 is exactly5×284. foamRun calls runTime.write after postSolve before the next termination check. maxdt is much smaller than the output interval, so no bin is skipped. Installed source and3million non-CFD boundary arithmetic evaluations verify the method. No writeAtEnd option is assumed. No adjustableRunTime or exact-time timestep adjustment is introduced. Final actual t can lie near1420 in [1419.9861328125,1420.0161783854167); actual high-precision uniform/time.value and t* are reported. Native normal completion must have matching12-rank final fields, matching finalindex/completedstep, and satisfy both termination and write-bin conditions.

Launcher:{P/'run_production.sh'}. Dry command:`{P/'run_production.sh'} --check`. It verifies HEAD, authority/source hashes, every input/decomposition file and exact file set, binary/native source and launcher hashes, runtime environment/PATH/libfluid resolution,12/scotch,pRefPoint,output/end/dt/precision/functions policy,cold0-only state, disk/RAM, no same-case solver, and unused execution namespace. Future --execute additionally requires a separate AUTHORIZED=YES receipt tied to plan/input hashes and explicit user instruction. The current draft is AUTHORIZED=NO and rejection was tested before Popen. This task does not authorize changing that flag.

It keeps full stdout/stderr, command/start/end/host/PID/returncode/bindings in native log, monotonic step markers, startup signal requests, completed steps and final saved times. Low-cost log monitoring catches fatal/nonfinite/FPE; disk is checked every10s. A separate24h timer and interruption handling stop the launched process tree. There is no field-reading diagnostic during timestepping. The empty functions dictionary and -noFunctionObjects plus frozen native binary protect the plain run; heavy/full-audit/exact-evidence libraries are absent.

Postprocessing script/plan:{P/'production_postprocessing_plan.md'} and postprocess_production.py. Offline reads give Nu_hot/cold(t), benchmark centreline Umax/Wmax(t), physical time/t*, velocity/temperature profiles, symmetry, reconstructable mass/energy descriptors, and dt/Co/iterations/residuals/continuity/native and external wall timing. Compare final160² state with Route A end_9000 baseline without assuming agreement; assess late range/slope for stationary-candidate versus still-evolving behavior. Stored-state energy secants are coverage-limited descriptors, not a native BDF/full conservation certificate. Existing final pilot Nu_hot and speed were reproduced; its598-step log was parsed offline with48pressure/24energy solves perstep. Analytic cold0 velocity and wall-gradient Nu were checked. A floating-point centre sorting issue was corrected using integer lattice indices, with no physics change.

Dry validation passed:complete preflight, actual newly prepared cold field tamper rejection with byte-exact restoration, HEAD mismatch, pre-existing execution namespace, draft-NO pre-Popen rejection, native log/fatal parsing, final-write source arithmetic, offline field/log postprocessing. Historical status is retained:

```text
'''+ '\n'.join(f'{k} = {v}' for k,v in history.items())+f'''
```

No git add/commit/push/reset/checkout mutation was used. git_status_final.txt and git_diff_stat_final.txt record the final state. Existing15 historical untracked case directories remain; only the new case/results preparation namespaces were added, and tracked diffstat is empty. Hash seal excludes itself and otherwise covers all preparation artifacts.

The next single task is RUN_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION with gpt-6.1-sol / high after an explicit production instruction from the user. Preparation is complete and this task stops here.

```text
{finalblock}
```
'''
(P/'RouteA_plain_transient_Co05_production_preparation.md').write_text(body)
# Keep a concrete non-CFD end receipt.
save('preparation_final_verification.json',{'result':'PASS','HEAD':plan['expected_HEAD'],'authority_hashes_verified':True,'late_source_files_reverified':len(late_seal),'case_hashes_reverified':True,'launcher_check':json.loads(check.stdout),'CFD_EXECUTED':'NO','physical_steps_executed':0,'AUTHORIZATION':'NO','execution_namespace_exists':False,'checks':checks})
for args,name in [(['git','status','--short'],'git_status_final.txt'),(['git','diff','--stat'],'git_diff_stat_final.txt')]:
 r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert r.returncode==0;(P/name).write_text(r.stdout)
assert not (P/'git_diff_stat_final.txt').read_text()
save('artifact_manifest_sha256.json',{str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact_manifest_sha256.json'})
assert launch.check()==plan
print(json.dumps({'PREPARATION':'COMPLETE','READY':'YES','AUTHORIZED':'NO','CFD_EXECUTED':'NO','report':str(P/'RouteA_plain_transient_Co05_production_preparation.md'),'late_files_unchanged':len(late_seal),'tracked_diff':'EMPTY'},indent=2))
