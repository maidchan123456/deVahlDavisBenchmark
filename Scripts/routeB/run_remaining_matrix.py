#!/usr/bin/env python3
"""Serial remaining-matrix orchestration using the existing case helpers."""
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from publish_matrix_case import OUT, V6, gate_d, sha

ROOT = OUT.parent.parent
ORDER = [('1e5','medium'),('1e5','fine'),('1e6','coarse'),('1e6','medium'),('1e6','fine')]
BATCH = OUT/'remaining_matrix_batch'


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


def main():
    BATCH.mkdir(exist_ok=False)
    state,manifest = read(OUT/'full_matrix_status.json'),read(OUT/'full_matrix_manifest.json')
    assert state['accepted_matrix_points']==7
    policy=read(OUT/'formal_resume_B-Ra1e5-coarse/startup_provenance.json')['continuation_policy']
    mutable=('full_matrix_status.json','full_matrix_manifest.json','benchmark_summary.csv','grid_convergence.csv','conservation.csv')
    protected={}
    for rec in manifest['cases'].values():
        protected.update({str(V6/f):h for f,h in rec.get('accepted_final_field_sha256',{}).items()})
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
            code=execute('run_full_matrix.py',['--ra',ra,'--grid',level],run/'initial_runner.log')
            metrics_path=OUT/'cases'/cid/'metrics.json'
            if not metrics_path.exists():raise RuntimeError(cid+': initial pipeline failed, exit '+str(code))
            metrics=read(metrics_path)
            if not metrics['normal_exit'] or metrics['fatal_or_nan']:raise RuntimeError(cid+': numerical failure')
            entry=read(OUT/'full_matrix_status.json')['cases'][cid]
            if entry['stage'] not in ('GATE_D_PASS','CONVERGENCE_NOT_REACHED'):raise RuntimeError(cid+': unexpected pipeline stage '+entry['stage'])
            code=execute('continue_matrix_case.py',['--case-id',cid],run/'continuation_driver.log')
            if code:raise RuntimeError(cid+': continuation helper failed, exit '+str(code))
            code=execute('publish_matrix_case.py',['--case-id',cid],run/'publish.log')
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
            if not passed:raise RuntimeError(cid+': CONVERGENCE_NOT_REACHED at existing cap '+str(policy['maximum_endTime']))
            protected.update({str(V6/f):h for f,h in record['accepted_final_field_sha256'].items()})
            for f in metrics_path.parent.iterdir():
                if f.is_file():protected[str(f)]=sha(f)
    except Exception as error:
        reason=str(error)
    finish(reason)


if __name__=='__main__':
    main()
