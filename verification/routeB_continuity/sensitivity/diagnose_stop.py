#!/usr/bin/env python3
"""Read-only diagnosis/finalization of existing STOP evidence. Never runs a solver."""
import csv
import difflib
import json
import shutil
from pathlib import Path
import numpy as np
from experiment import HERE,ROOT,RESULTS,REG,QOIS,RUNS,Experiment,dump,csvwrite,sha

def diagnose():
    if not (RESULTS/'STOP.json').exists(): raise RuntimeError('Expected an existing STOP; no execution permitted')
    p=RUNS/'baseline_n20'
    with (p/'steadyMonitor.csv').open() as f:
        history=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    tail=history[-11:]
    diagnostic={
      'id':'baseline_n20','status':'NOT_CONVERGED','normal_exit':True,
      'iteration':int(history[-1]['iteration']),
      'registered_maximum_iteration':REG['stopping']['maximum_iteration'],
      'last_window_iterations':[int(tail[0]['iteration']),int(tail[-1]['iteration'])],
      'criteria':{},'QoI_Rwin':{},
      'qualified_samples_in_full_history':sum(row['qualified']>0 for row in history),
      'accepted_as_baseline':False,'source_sign_test_executed':False,
      'interpretation':'The measured late variations exceed the preregistered numerical stopping criteria. A persistent fluctuation band is observed, but its cause and a certified numerical floor have not been established. No quota or stopping rule was fitted retrospectively. No solver was rerun after STOP.'}
    for k,label,limit in [('window_value_range','maximum_normalized_QoI_window_range',1e-8),('U_change','maximum_U_change_over_20_iterations_over_Up',1e-8),('T_change','maximum_T_change_over_20_iterations_over_DeltaT',1e-8),('window_heat_range','heat_imbalance_window_range',1e-8),('window_position_range','position_window_range',1/4096)]:
        observed=history[-1][k] if k.startswith('window') else max(row[k] for row in tail)
        diagnostic['criteria'][label]={'observed':observed,'limit':limit,'ratio':observed/limit,'satisfied':observed<=limit}
    rwin_rows=[]
    for i,row in enumerate(history):
        window=history[max(0,i-10):i+1]
        if len(window)<11: continue
        for q in QOIS:
            vals=np.array([a[q] for a in window]);span=float(np.ptp(vals))
            value=span/max(abs(float(vals.mean())),1) if q in QOIS[:5] else span
            rwin_rows.append({'run_id':'baseline_n20','iteration':int(row['iteration']),'qoi':q,'Rwin':value,'raw_range':span,'units':'relative/max(abs(mean),1)' if q in QOIS[:5] else 'absolute_dimensionless_position','window_iterations':200})
            if i==len(history)-1: diagnostic['QoI_Rwin'][q]=value
    r=json.loads((RESULTS/'baseline_n20.json').read_text())
    diagnostic['final_equation_residuals']=r['equation_residuals']
    diagnostic['final_epsilon_phi_mean']=r['metrics']['epsilon_phi_mean']
    diagnostic['final_epsilon_phi_max']=r['metrics']['epsilon_phi_max']
    diagnostic['final_heat_imbalance']=r['metrics']['heat_imbalance']
    diagnostic['final_qoi']=r['qoi']
    diagnostic['future_review_options_not_executed']=['Assess U/T linear tolerance and absolute-temperature conditioning at fixed pressure baseline setting','Independently select numerical measurement-resolution criteria; distinguish from scientific quota','Preregister an amendment/new execution phase and authorize a new task before any further solver call']
    dump(RESULTS/'convergence_diagnostics.json',diagnostic)
    csvwrite('baseline_rwin_history.csv',rwin_rows)
    shutil.copy2(p/'steadyMonitor.csv',RESULTS/'baseline_monitor_history.csv')
    last_audit=[]
    with (p/'continuityAudit.csv').open() as f:
        for row in csv.DictReader(f):
            if int(float(row['iteration']))>=11800: last_audit.append(row)
    csvwrite('baseline_pressure_audit_tail.csv',last_audit)
    lines=(p/'log.solver').read_text().splitlines()
    (RESULTS/'baseline_stop_log_excerpt.txt').write_text('\n'.join(lines[:20]+['[intermediate iterations omitted]']+lines[-25:])+'\n')
    audit=HERE/'auditSolver';stock=Path('/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam')
    source_audit={}
    patch=[]
    for name in ['UEqn.H','TEqn.H','createFields.H','readTransportProperties.H','pEqn.H','buoyantBoussinesqSimpleFoam.C']:
        source_audit[name]={'stock_path':str(stock/name),'stock_sha256':sha(stock/name),'verification_sha256':sha(audit/name),'identical':sha(stock/name)==sha(audit/name)}
        if not source_audit[name]['identical']:
            patch.extend(difflib.unified_diff((stock/name).read_text().splitlines(True),(audit/name).read_text().splitlines(True),fromfile='stock-v6/'+name,tofile='verification-only/'+name))
    dump(RESULTS/'source_audit.json',source_audit)
    (HERE/'auditSolver/source_changes.patch').write_text(''.join(patch))
    # Rehydrate only saved data, then rebuild reports without any solver/mesh call.
    state=json.loads((RESULTS/'working_state.json').read_text())
    e=Experiment();e.records=state['records'];e.status=state['status']
    e.baselines={int(n):next(r for r in e.records if r['id']==name) for n,name in state['baselines'].items()}
    from analyze import finalize
    finalize(e)

if __name__=='__main__': diagnose()
