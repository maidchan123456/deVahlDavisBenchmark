import csv,hashlib,json
from pathlib import Path
v=Path(__file__).resolve().parent;p=v.parent;o=p/'postprocessing_v2'
rows=list(csv.DictReader((o/'native_step_diagnostics.csv').open()));prior_dt=2.3111979166666666e-5;checks=[]
for r in rows:
 co=float(r['Co_max']);dt=float(r['deltaT_s']);pred=min(1.2*prior_dt,.027734375,.5/co*prior_dt) if co>1e-15 else min(1.2*prior_dt,.027734375)
 checks.append({'step':int(r['step']),'logged_Co':co,'pre_advance_logged_time_s':float(rows[int(r['step'])-2]['time_s']) if int(r['step'])>1 else 0.,'new_step_time_s':float(r['time_s']),'previous_dt_s':prior_dt,'new_dt_s':dt,'expected_dt_s':pred,'relative_controller_difference':abs(dt-pred)/max(abs(pred),1e-30),'rescaled_pre_advance_Co_at_new_dt':co*dt/prior_dt});prior_dt=dt
i=max(range(len(checks)),key=lambda i:checks[i]['logged_Co']);over=[c for c in checks if c['logged_Co']>.500000001]
record={'configured_maxCo':.5,'maximum_logged_Co_state':checks[i],'all_steps_controller_relative_difference_max':max(c['relative_controller_difference'] for c in checks),'all_steps_rescaled_pre_advance_Co_max':max(c['rescaled_pre_advance_Co_at_new_dt'] for c in checks),'logged_Co_over_config_plus_1e_9_count':len(over),'last_step_over_config_plus_1e_9':over[-1]['step'],'last_over_new_step_time_s':over[-1]['new_step_time_s'],'meaning':'Native preSolve computes Co from previous completed flux/rho and previous dt, then adjustDeltaT selects new dt before advancing Time. Rescaled Co is DERIVED for that pre-advance state at the selected new dt, not a post-solve Co certificate. Configured maxCo is unchanged; all logged Co values are retained.','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path('/opt/openfoam13/applications/solvers/foamRun/foamRun.C'),Path('/opt/openfoam13/applications/solvers/foamRun/setDeltaT.C'),Path('/opt/openfoam13/applications/modules/fluidSolver/fluidSolver.C'),Path('/opt/openfoam13/applications/modules/isothermalFluid/isothermalFluid.C')]}}
assert record['all_steps_controller_relative_difference_max']<1e-12
assert record['all_steps_rescaled_pre_advance_Co_max']<=.500000000001
record['frozen_native_controller_check']='PASS';(o/'native_Co_controller_alignment_v2.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
