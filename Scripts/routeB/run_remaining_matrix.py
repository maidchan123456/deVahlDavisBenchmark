#!/usr/bin/env python3
"""Serial remaining-matrix orchestration using the existing case helpers."""
import csv
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from publish_matrix_case import OUT, V6, gate_d, sha

ROOT = OUT.parent.parent
ORDER = [('1e5','medium'),('1e5','fine'),('1e6','coarse'),('1e6','medium'),('1e6','fine')]
BATCH = OUT/'remaining_matrix_batch'
COMPUTED_MODE = False


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def execute(script, arguments, log):
    with log.open('w') as stream:
        return subprocess.run([sys.executable,str(ROOT/'Scripts/routeB'/script),*arguments],
                              stdout=stream,stderr=subprocess.STDOUT,
                              env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}).returncode


def finish(reason):
    if COMPUTED_MODE:
        return finish_computed(reason)
    state = read(OUT/'full_matrix_status.json')
    rows = []
    for ra,level in ORDER:
        cid = f'B-Ra{ra}-{level}'
        entry = state['cases'].get(cid,{})
        gates = state['formal_Ra_gates'][str(int(float(ra)))]
        accepted = entry.get('stage') == 'GATE_D_PASS'
        rows.append(dict(case=cid,grid={'coarse':40,'medium':80,'fine':160}[level],
                         final_iteration=entry.get('final_iteration'),
                         Gate_D='PASS' if accepted else ('FAIL' if entry else 'NOT_RUN'),
                         Gate_E=gates['E'] if level=='fine' and accepted else 'NOT_EVALUATED',
                         Gate_F=gates['F'] if level=='fine' and accepted else 'NOT_EVALUATED',
                         needs_320=state.get('Ra'+ra+'_needs_320','NOT_EVALUATED') if level=='fine' else 'NOT_EVALUATED'))
    complete = state['accepted_matrix_points'] == 12
    state.update(FULL_MATRIX_COMPLETE='YES' if complete else 'NO',
                 ROUTE_B_FULL_MATRIX_COMPLETE='YES' if complete else 'NO',
                 BATCH_STOPPED_EARLY='YES' if reason else 'NO',BATCH_STOP_REASON=reason or 'NONE',
                 status='FULL_MATRIX_SOLUTIONS_ACCEPTED' if complete else 'BATCH_STOPPED',
                 required_user_decision='Review the stopped case; numerical tuning was not performed.' if reason
                 else 'Post-matrix review of Gate E/F/G and deferred needs_320 findings.',
                 BENCHMARK_CORE_PASS='NOT_EVALUATED')
    write(OUT/'full_matrix_status.json',state)
    manifest = read(OUT/'full_matrix_manifest.json')
    manifest.update(FULL_MATRIX_COMPLETE=state['FULL_MATRIX_COMPLETE'],
                    ROUTE_B_FULL_MATRIX_COMPLETE=state['ROUTE_B_FULL_MATRIX_COMPLETE'],
                    status=state['status'],BATCH_STOP_REASON=state['BATCH_STOP_REASON'],
                    limitation='Matrix completion denotes twelve Gate D accepted solutions, not universal Gate E/F/G PASS.' if complete
                    else 'Batch stopped; prior accepted solutions retained. '+str(reason))
    write(OUT/'full_matrix_manifest.json',manifest)
    grid_rows=list(csv.DictReader((OUT/'grid_convergence.csv').open()))
    needs={}
    for ra in ('1e3','1e4','1e5','1e6'):
        saved=[g for g in grid_rows if int(g['Ra_target'])==int(float(ra))]
        needs[ra]=any(str(g['needs_320']).lower()=='true' for g in saved) if any(g['Gate_F']!='NOT_EVALUATED' for g in saved) else 'NOT_EVALUATED'
    summary=dict(initial_HEAD=read(BATCH/'startup.json')['HEAD'],cases=rows,
                 accepted_count=state['accepted_matrix_points'],FULL_MATRIX_COMPLETE=state['FULL_MATRIX_COMPLETE'],
                 stopped_early=bool(reason),stop_reason=reason or 'NONE',formal_Ra_gates=state['formal_Ra_gates'],
                 needs_320=needs,
                 next_action='FIX_STOPPED_CASE' if reason else 'POST_MATRIX_REVIEW',
                 Gate_G_investigation='FROZEN_PENDING_POST_MATRIX_REVIEW',
                 formal_numerical_spec_changed=False,microcase_solver_executed=False)
    write(OUT/'full_matrix_completion_summary.json',summary)
    lines=['# Route B remaining matrix batch','', 'Initial HEAD: `'+summary['initial_HEAD']+'`.','',
           '| Case | Grid | Final iteration | Gate D | Gate E | Gate F | needs_320 |',
           '|---|---|---:|---|---|---|---|']
    lines += ['| '+str(r['case'])+' | '+str(r['grid'])+'² | '+str(r['final_iteration'])+' | '+r['Gate_D']+' | '+r['Gate_E']+' | '+r['Gate_F']+' | '+str(r['needs_320'])+' |' for r in rows]
    lines += ['',f"Accepted: {summary['accepted_count']}/12. Full matrix complete: {summary['FULL_MATRIX_COMPLETE']}.",
              'Batch stop reason: '+summary['stop_reason']+'.',
              'Next action: '+summary['next_action']+'.',
              'Gate G review remains frozen; numerical criteria unchanged. No 320 or microcase solver executed.']
    (OUT/'full_matrix_completion_report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary),flush=True)


def computed_count(manifest):
    return sum(bool(rec.get('generated_manifest') and (rec.get('Gate_D')=='PASS' or
               (rec.get('iteration_history') and rec['iteration_history'][-1]['metrics']['normal_exit']
                and not rec['iteration_history'][-1]['metrics']['fatal_or_nan'])))
               for rec in manifest['cases'].values())


def mark_computed(cid):
    state,manifest=read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
    count=computed_count(manifest)
    state.update(computed_matrix_points=count,COMPUTED_MATRIX_COUNT=str(count)+'/12',
                 ACCEPTED_MATRIX_COUNT=str(state['accepted_matrix_points'])+'/12',
                 FULL_COMPUTED_MATRIX_COMPLETE='YES' if count==12 else 'NO',
                 FULL_ACCEPTED_MATRIX_COMPLETE='YES' if state['accepted_matrix_points']==12 else 'NO')
    state['stop_cases']=[key for key,value in state['cases'].items() if value['stage']=='CONVERGENCE_NOT_REACHED']
    state['cases'][cid].update(COMPUTED_CASE=True,ACCEPTED_CASE=state['cases'][cid]['stage']=='GATE_D_PASS')
    manifest['cases'][cid].update(COMPUTED_CASE=True,ACCEPTED_CASE=manifest['cases'][cid]['Gate_D']=='PASS')
    manifest.update({key:state[key] for key in ('COMPUTED_MATRIX_COUNT','ACCEPTED_MATRIX_COUNT','FULL_COMPUTED_MATRIX_COMPLETE','FULL_ACCEPTED_MATRIX_COMPLETE')})
    write(OUT/'full_matrix_status.json',state);write(OUT/'full_matrix_manifest.json',manifest)


def finish_computed(reason):
    state,manifest=read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
    count=computed_count(manifest);rows=[]
    for level in ('coarse','medium','fine'):
        cid='B-Ra1e6-'+level;rec=manifest['cases'].get(cid);entry=state['cases'].get(cid,{})
        if not rec:
            rows.append(dict(case=cid,computed=False,accepted=False,Gate_D='NOT_EVALUATED',final_iteration=None,residual_behavior='NOT_APPLICABLE'));continue
        metrics=read(Path(rec['metrics_path']));accepted=rec['Gate_D']=='PASS';behavior='NOT_APPLICABLE'
        if not accepted:
            if level=='coarse':behavior='PLATEAU_OR_OSCILLATORY'
            else:
                recent=[x['metrics']['final_initial_residuals'] for x in rec['iteration_history'][-6:]]
                trends={field:all(b[field]<a[field] for a,b in zip(recent,recent[1:])) for field in ('Ux','Uy','T','p_rgh')}
                behavior='CONTINUING_DECAY' if len(recent)>=3 and all(trends.values()) else ('PLATEAU_OR_OSCILLATORY' if len(recent)>=3 and not any(trends.values()) else 'INCONCLUSIVE')
                rec['residual_diagnostic']=dict(classification=behavior,checkpoint_residuals=[dict(iteration=x['iteration'],**x['metrics']['final_initial_residuals']) for x in rec['iteration_history']],recent_monotonic_decrease=trends)
                entry['residual_behavior']=behavior
        rows.append(dict(case=cid,computed=metrics['normal_exit'] and not metrics['fatal_or_nan'],accepted=accepted,
                         Gate_D=rec['Gate_D'],final_iteration=metrics['final_iteration'],residual_behavior=behavior,
                         QoI={k:metrics[k] for k in ('Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Umax','Umax_Z','Wmax','Wmax_X')},
                         paper_errors={k:metrics['paper_comparison_like_for_like'][k]['absolute_relative_error'] for k in ('Nu_bar_cavity','Umax','Wmax')},
                         diagnostics_path=rec['Gate_G_diagnostics_path']))
    available=all(row['computed'] for row in rows)
    if available:
        trends=[]
        for q in ('Nu_bar_cavity','Umax','Wmax'):
            c,m,f=[row['QoI'][q] for row in rows];product=(m-c)*(f-m)
            trends.append(dict(quantity=q,coarse=c,medium=m,fine=f,trend='MONOTONIC' if product>0 else ('NON_MONOTONIC' if product<0 else 'INCONCLUSIVE'),status='DIAGNOSTIC_ONLY'))
        write(OUT/'Ra1e6_computed_grid_trend.json',dict(status='DIAGNOSTIC_ONLY',formal_p_obs_or_GCI_computed=False,quantities=trends))
    state.update(computed_matrix_points=count,COMPUTED_MATRIX_COUNT=str(count)+'/12',ACCEPTED_MATRIX_COUNT=str(state['accepted_matrix_points'])+'/12',
                 FULL_COMPUTED_MATRIX_COMPLETE='YES' if count==12 else 'NO',FULL_ACCEPTED_MATRIX_COMPLETE='NO',
                 status='COMPUTED_MATRIX_COMPLETE_PENDING_REVIEW' if count==12 else 'COMPUTED_BATCH_EXECUTION_FAILURE',
                 BATCH_STOPPED_EARLY='YES' if reason else 'NO',BATCH_STOP_REASON=reason or 'NONE',
                 NEXT_ACTION='FIX_EXECUTION_FAILURE' if reason else 'RA1E6_POST_MATRIX_GATE_D_REVIEW',USER_DECISION_REQUIRED='YES',
                 required_user_decision='Separate post-matrix Ra1e6 Gate D review; no policy amendment performed.' if not reason else str(reason))
    manifest.update({key:state[key] for key in ('status','COMPUTED_MATRIX_COUNT','ACCEPTED_MATRIX_COUNT','FULL_COMPUTED_MATRIX_COMPLETE','FULL_ACCEPTED_MATRIX_COMPLETE','BATCH_STOPPED_EARLY','BATCH_STOP_REASON')})
    manifest['limitation']='Computed completion counts normal saved solutions; it does not imply Gate D acceptance or Gate E/F/G PASS.'
    write(OUT/'full_matrix_status.json',state);write(OUT/'full_matrix_manifest.json',manifest)
    summary=dict(cases=rows,computed_count=count,accepted_count=state['accepted_matrix_points'],formal_Ra1e6_gates=state['formal_Ra_gates']['1000000'],
                 grid_trend_diagnostic='AVAILABLE' if available else 'NOT_AVAILABLE',stopped_early=bool(reason),stop_reason=reason or 'NONE',next_action=state['NEXT_ACTION'])
    write(OUT/'Ra1e6_computed_matrix_summary.json',summary)
    lines=['# Ra1e6 computed matrix','', '| Case | Final iteration | Gate D | Residual behavior | Computed | Accepted |','|---|---:|---|---|---|---|']
    lines += ['| '+row['case']+' | '+str(row['final_iteration'])+' | '+row['Gate_D']+' | '+row['residual_behavior']+' | '+str(row['computed'])+' | '+str(row['accepted'])+' |' for row in rows]
    lines += ['',f'Computed {count}/12; accepted '+str(state['accepted_matrix_points'])+'/12.', 'Next action: '+state['NEXT_ACTION']+'. No criterion, numerical specification, coarse result, microcase or 320 changes.']
    (OUT/'Ra1e6_computed_matrix_report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(computed=count,accepted=state['accepted_matrix_points'],stop_reason=reason)),flush=True)


def main():
    global ORDER, BATCH, COMPUTED_MODE
    parser=argparse.ArgumentParser()
    parser.add_argument('--computed-ra1e6', action='store_true')
    COMPUTED_MODE=parser.parse_args().computed_ra1e6
    if COMPUTED_MODE:
        ORDER=[('1e6','medium'),('1e6','fine')]
        BATCH=OUT/'Ra1e6_computed_batch'
    BATCH.mkdir(exist_ok=False)
    state,manifest = read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
    assert state['accepted_matrix_points']==(9 if COMPUTED_MODE else 7)
    policy=read(OUT/'formal_resume_B-Ra1e5-coarse/startup_provenance.json')['continuation_policy']
    if COMPUTED_MODE:
        policy=dict(policy, maximum_endTime=30000, reason='Explicit computed-matrix request: at most 30000, 3000-step checkpoints.')
    mutable=('full_matrix_status.json','full_matrix_manifest.json','benchmark_summary.csv','grid_convergence.csv','conservation.csv')
    protected={}
    for rec in manifest['cases'].values():
        protected.update({str(V6/f):h for f,h in rec.get('accepted_final_field_sha256',rec.get('final_field_sha256',{})).items()})
    for rel in subprocess.check_output(['git','ls-files','results/routeB','reference','cases/routeB/template'],text=True,cwd=ROOT).splitlines():
        if rel in ['results/routeB/'+f for f in mutable]:continue
        path=ROOT/rel
        if path.is_file():protected[str(path)]=sha(path)
    write(BATCH/'startup.json',dict(HEAD=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),
                                  policy=policy,protected_file_sha256=protected))
    reason=None
    try:
        for ra,level in ORDER:
            cid=f'B-Ra{ra}-{level}';case=V6/'cases/routeB'/f'Ra{ra}_{level}';run=OUT/f'formal_resume_{cid}'
            assert not case.exists() and not run.exists(), 'Refusing existing target overwrite: '+cid
            run.mkdir()
            before_state,before_manifest=read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
            for name in mutable:(run/('before_'+name)).write_bytes((OUT/name).read_bytes())
            write(run/'startup_provenance.json',dict(initial_HEAD=read(BATCH/'startup.json')['HEAD'],target=cid,
                  target_case_path=str(case),initial_accepted_count=before_state['accepted_matrix_points'],
                  initial_endTime=3000,continuation_policy=policy))
            print(json.dumps(dict(case=cid,event='INITIAL_RUN')),flush=True)
            arguments=['--ra',ra,'--grid',level]
            if COMPUTED_MODE:
                arguments += ['--allow-unconverged-case','B-Ra1e6-coarse','--allow-unconverged-case','B-Ra1e6-medium']
            code=execute('run_full_matrix.py',arguments,run/'initial_runner.log')
            metrics_path=OUT/'cases'/cid/'metrics.json'
            if not metrics_path.exists():raise RuntimeError(cid+': initial pipeline failed, exit '+str(code))
            metrics=read(metrics_path)
            if not metrics['normal_exit'] or metrics['fatal_or_nan']:raise RuntimeError(cid+': numerical failure')
            entry=read(OUT/'full_matrix_status.json')['cases'][cid]
            if entry['stage'] not in ('GATE_D_PASS','CONVERGENCE_NOT_REACHED'):raise RuntimeError(cid+': unexpected pipeline stage '+entry['stage'])
            code=execute('continue_matrix_case.py',['--case-id',cid],run/'continuation_driver.log')
            if code:raise RuntimeError(cid+': continuation helper failed, exit '+str(code))
            code=execute('publish_matrix_case.py',['--case-id',cid]+(['--computed-matrix'] if COMPUTED_MODE else []),run/'publish.log')
            if code:raise RuntimeError(cid+': publication helper failed, exit '+str(code))
            state,manifest=read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
            for previous in before_state['cases']:
                assert state['cases'][previous]==before_state['cases'][previous], 'Prior status changed: '+previous
                assert manifest['cases'][previous]==before_manifest['cases'][previous], 'Prior manifest changed: '+previous
            assert all(sha(Path(f))==h for f,h in protected.items()), 'Protected result hash mismatch'
            metrics=read(metrics_path);passed=gate_d(metrics)[1]
            rows=[]
            for q,c in metrics['paper_comparison_like_for_like'].items():
                cal,ref=c['calculated'],c['reference']
                rows.append(dict(quantity=q,calculated=cal,reference=ref,
                                 signed_difference=cal-ref if ref is not None else '',
                                 absolute_relative_error=abs((cal-ref)/ref) if ref not in (None,0) else '',
                                 absolute_position_error=c.get('absolute_position_error','')))
            with (metrics_path.parent/'paper_comparison.csv').open('w') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            record=manifest['cases'][cid]
            write(run/'validation.json',dict(protected_hashes='PASS',prior_case_records='UNCHANGED',
                  Gate_D='PASS' if passed else 'FAIL',accepted_count=state['accepted_matrix_points'],
                  workflow_sha256={name:sha(ROOT/'Scripts/routeB'/name) for name in
                                  ('run_remaining_matrix.py','continue_matrix_case.py','publish_matrix_case.py')}))
            print(json.dumps(dict(case=cid,event='SAVED',iteration=metrics['final_iteration'],
                  Gate_D='PASS' if passed else 'FAIL',accepted=state['accepted_matrix_points'])),flush=True)
            if not passed and not COMPUTED_MODE:raise RuntimeError(cid+': CONVERGENCE_NOT_REACHED at existing cap '+str(policy['maximum_endTime']))
            if COMPUTED_MODE:
                mark_computed(cid)
            protected.update({str(V6/f):h for f,h in record.get('accepted_final_field_sha256',record['final_field_sha256']).items()})
            for f in metrics_path.parent.iterdir():
                if f.is_file():protected[str(f)]=sha(f)
    except Exception as error:
        reason=str(error)
    finish(reason)


if __name__=='__main__':
    main()
