#!/usr/bin/env python3
import json,hashlib,csv,ast,re,datetime,subprocess
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;ROOT=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark');SOURCE=ROOT/'results/routeA/transient_cfd_scaling_pilot/plain_20261006_0710';failed=P/'attempt_01_time_precision_failure'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
for f in P.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
report=json.loads((P/'RouteA_plain_transient_late_window_performance_pilot.json').read_text());receipt=report['process_receipt'];current=json.loads((P/'step_history.json').read_text())
# Reuse only the read-only parser prefix; no CFD and no writes inside the preserved failed attempt.
parser=(P/'analyze.py').read_text().split('row_fields=',1)[0];scope={'__file__':str(failed/'offline_parser_read_only.py'),'__name__':'failed_read_only_parser'};exec(compile(parser,str(P/'analyze.py'),'exec'),scope);old=scope['rows'];assert len(old)==402 and len(current)==598
fields=[k for k in current[0] if k!='outer_indices']
with (P/'failed_attempt_step_history.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in old)
combined=[]
for attempt,rows in [(1,old),(2,current)]:
 for r in rows:combined.append({'attempt_id':attempt,'cumulative_compute_step':len(combined)+1,**{k:v for k,v in r.items() if k!='outer_indices'}})
with (P/'step_history_all_attempts.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['attempt_id','cumulative_compute_step']+fields);w.writeheader();w.writerows(combined)
prior=json.loads((SOURCE/'artifact_manifest_sha256.json').read_text());assert all(sha(SOURCE/k)==v for k,v in prior.items())
for k,v in json.loads((P/'authorization_receipt.json').read_text())['authority_hashes'].items():assert sha(ROOT/k)==v
inputs=json.loads((P/'input_manifest.json').read_text());assert all(sha(P/'case'/k)==v for k,v in inputs.items())
for relative in ['0/U','0/T','0/p','0/p_rgh','system/fvSolution','system/fvSchemes']:assert sha(P/'case'/relative)==sha(SOURCE/'common_input'/relative)
for relative,h in json.loads((P/'physical_input_manifest.json').read_text()).items():assert sha(P/'case'/relative)==h
log=(P/'log.foamRun').read_text();bindings=re.findall(r'MCW rank (\d+) bound to socket 0\[core (\d+)\[hwt 0-1\]\]',log);assert len(bindings)==12 and {int(core) for rank,core in bindings}==set(range(12))
assert receipt['returncode']==0 and receipt['completed_steps']==598 and receipt['started_steps']==598 and receipt['max_observed_solver_processes']==12
assert '\nEnd\n' in log and 'FOAM FATAL' not in log
assert len(current)+len(old)==1000 and report['cumulative_CFD_wall_seconds']<600
assert all(r['outer_iteration_count']==24 and r['pressure_solve_count']==48 and r['energy_solve_count']==24 for r in combined)
assert all(r['pressure_max_final_residual']<=1e-12 and r['energy_max_final_residual']<=1e-12 for r in combined)
assert all(r['native_dt_error_s']==0 for r in combined)
assert all(not (Path('/proc')/str(pid)).exists() for pid in receipt['solver_PIDs']), 'Unexpected remaining solver PID'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='fd62fb9f5458532a7ebd684b73baf1ea9b415d7e'
# Compare actual checkpoint fields at matching physical steps across the operational-format repair.
read_scalar=scope['read_scalar'];read_vector=scope['read_vector'];differences=[]
for step in [100,250]:
 def name_at(case):
  for t in (case/'processor0').iterdir():
   if t.is_dir() and (t/'uniform/time').is_file():
    if int(re.search(r'\bindex\s+(\d+);',(t/'uniform/time').read_text())[1])==step:return t.name
  raise AssertionError(step)
 oldname=name_at(failed/'case');newname=name_at(P/'case');oldU=np.empty((25600,3));newU=np.empty((25600,3));oldT=np.empty(25600);newT=np.empty(25600)
 for rank in range(12):
  a=failed/f'case/processor{rank}'/oldname;b=P/f'case/processor{rank}'/newname
  oldids=scope['labels'](failed/f'case/processor{rank}/constant/polyMesh/cellProcAddressing');newids=scope['labels'](P/f'case/processor{rank}/constant/polyMesh/cellProcAddressing')
  oldU[oldids]=read_vector(a/'U',len(oldids));newU[newids]=read_vector(b/'U',len(newids));oldT[oldids]=read_scalar(a/'T',len(oldids));newT[newids]=read_scalar(b/'T',len(newids))
 umax=float(np.abs(oldU-newU).max());tmax=float(np.abs(oldT-newT).max())
 assert umax<1e-10 and tmax<1e-8
 differences.append({'physical_step':step,'U_component_Linf_difference_m_s':umax,'T_Linf_difference_K':tmax,'old_time_name':oldname,'new_time_name':newname,'gross_same_state_after_output_name_repair':True,'comparison_method':'assemble each separate scotch decomposition into global cell order using its own cellProcAddressing'})
dump(P/'output_name_repair_field_comparison.json',differences)
report['decomposition_note']='Standard scotch decomposition was rerun for the logging-repair attempt and produced a different partition. Both use12ranks, identical global inputs/numerics and binding; comparisons use each addressing, never rank-local arrays. No decomposition or solver tuning.'
report['source_pilot_immutable_verified']=True;report['authority_hashes_verified']=True;report['post_run_input_hashes_verified']=True;report['binding_verified']=True;report['all_attempts_raw_step_csv']='step_history_all_attempts.csv';report['failed_attempt_raw_step_csv']='failed_attempt_step_history.csv';report['operational_repair_checkpoint_comparison']=differences
report['solver_log_summary']={'all_attempts_completed_steps':1000,'all_completed_steps24outer':True,'all_completed_steps48pressure24energy_solves':True,'max_pressure_single_solve_iterations':max(r['pressure_max_iterations_per_solve'] for r in current),'max_energy_single_solve_iterations':max(r['energy_max_iterations_per_solve'] for r in current),'max_pressure_final_residual':max(r['pressure_max_final_residual'] for r in current),'max_energy_final_residual':max(r['energy_max_final_residual'] for r in current),'max_local_continuity_sum':max(r['continuity_max_sum_local'] for r in current),'max_abs_global_continuity':max(r['continuity_max_abs_global'] for r in current),'final_cumulative_continuity':current[-1]['continuity_cumulative_last'],'fatal_in_accepted_attempt':False,'fatal_in_initial_attempt':'native time-name precision; repaired operational output setting only; preserved evidence'}
report['coverage']={'complete_primary_windows':['31–50','51–100','101–250','251–500'],'partial_primary_window':'501–598 of requested501–750','unreached_primary_window':'751–1000 because cumulative compute budget was preserved across logging repair','last200_non_write_proxy_step_range':report['late_proxy']['step_range'],'interpretation':'598-step final continuous state; initial402-step trajectory was recomputed and not added to final physical age. Total1000 completed compute steps is resource accounting only.'}
report['runtime_projection_clarification']='Adaptive projection includes accepted71.184s continuous trajectory wall, excludes earlier failed49.435s duplicate work; total pilot CFD receipt includes both attempts. No diagnostic proxy included.'
report['planning_thresholds']={'Co05_200061_steps_24h_cost_s':86400/200061,'Co025_400122_steps_24h_cost_s':86400/400122,'Co05_late_cost_headroom_factor':86400/200061/report['late_proxy']['wall_stats']['median'],'Co025_late_cost_headroom_factor':86400/400122/report['late_proxy']['wall_stats']['median']}
dump(P/'RouteA_plain_transient_late_window_performance_pilot.json',report)
p=P/'RouteA_plain_transient_late_window_performance_pilot.md';text=p.read_text();text=text.replace('## Decision',f'''## Coverage and final verification

The accepted trajectory contains598 continuous steps; first402 steps were recomputed after the allowed output-name repair. Resource accounting totals1000 completed compute steps and120.618 s; this is not a1000-step physical trajectory. Requested windows31–50,51–100,101–250 and251–500 are complete;501–750 has501–598 coverage;751–1000 was not reached because the cumulative budget was preserved. The last200 non-write proxy is fully available.

step_history.csv contains598 accepted steps; failed_attempt_step_history.csv contains402 prior steps; step_history_all_attempts.csv includes all1000 with attempt_id and cumulative_compute_step. Every completed step has24 outer,48 pressure and24 energy solves; every pressure/energy final residual<=1e-12, exact logged native-controller formula match. Prior pilot artifact hashes, authority hashes and all copied original physical/numerical input hashes remain unchanged. Binding logs prove12 distinct physical cores; all worker PIDs exited.

Both attempts used standard scotch; independently generated partitions differ, so comparisons assemble global cell order using each cellProcAddressing. Checkpoint100/250 U/T after the output-name repair agree within recorded tiny floating-point differences: {differences}. No bitwise or full parallel/scientific equivalence claim.

![Later window medians]({P}/late_window_medians.png)

Adaptive runtime projections use accepted continuous-attempt wall; initial failed duplicate compute is retained in total pilot wall accounting but excluded from a future normally prepared production-run estimate.

## Decision''')
p.write_text(text)
verification={'status':'PASS','source_pilot_and_authorities_unchanged':True,'accepted598_plus_initial402_steps_equals1000':True,'cumulative_CFD_wall_under600_seconds':True,'native_stop_at_accepted_step_cap':True,'actual_native_controller_law_every_completed_step':True,'all_outer_and_pressure_energy_solve_counts_correct':True,'pressure_energy_final_linear_residuals_within_registered_tolerance':True,'accepted_attempt_no_fatal_nan_fpe_and_saved_field_sanity_pass':True,'initial_operational_time_precision_failure_preserved':True,'same_physics_numerics_after_logging_repair':True,'12distinct_physical_cores':True,'no_remaining_worker_processes':True,'no_production_Q3_GateJ':True,'no_git_mutations':True,'history_policy':'continuous cold native history; checkpoint restart not certified','verified_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};dump(P/'verification.json',verification)
seal={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact_manifest_sha256.json'};dump(P/'artifact_manifest_sha256.json',seal)
print(json.dumps({'verification':verification,'log_summary':report['solver_log_summary'],'coverage':report['coverage'],'checkpoint_comparison':differences,'artifact_files':len(seal)},indent=2))
