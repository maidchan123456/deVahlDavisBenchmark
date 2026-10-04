#!/usr/bin/env python3
"""Bounded steady continuation of a single generated formal matrix case."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from publish_matrix_case import OUT, V6, gate_d, sha
from run_full_matrix import save_status


def snapshot(case, generated, iteration):
    return dict(iteration=iteration,
                field_sha256={p.name:sha(p) for p in (case/str(iteration)).iterdir() if p.is_file()},
                input_sha256={rel:sha(case/rel) for rel in generated['input_sha256']},
                mesh_sha256={str(p.relative_to(case)):sha(p) for p in (case/'constant/polyMesh').iterdir() if p.is_file()},
                log_sha256={p.name:sha(p) for p in case.glob('log.*') if p.is_file()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--maximum-end-time', type=int)
    args = parser.parse_args()
    cid = args.case_id
    run_dir = OUT/f'formal_resume_{cid}'
    startup = json.loads((run_dir/'startup_provenance.json').read_text())
    assert startup['target'] == cid
    case = Path(startup['target_case_path'])
    generated = json.loads((case/'case_manifest.json').read_text())
    entry = json.loads((OUT/'full_matrix_status.json').read_text())['cases'][cid]
    entry.pop('stage', None)
    entry.pop('updated_at', None)
    metrics_path = OUT/'cases'/cid/'metrics.json'
    metrics = json.loads(metrics_path.read_text())
    checks, passed = gate_d(metrics)
    initial = dict(snapshot(case, generated, metrics['final_iteration']), Gate_D_checks=checks,
                   Gate_D='PASS' if passed else 'FAIL', metrics=metrics)
    history_path = run_dir/'iteration_history.json'
    main_log = case/'log.buoyantBoussinesqSimpleFoam'
    if args.resume:
        history = json.loads(history_path.read_text())
        assert history[-1]['iteration'] == metrics['final_iteration'], 'Resume history mismatch'
        assert history[-1]['field_sha256'] == initial['field_sha256'], 'Resume field mismatch'
        assert history[-1]['input_sha256'] == initial['input_sha256'], 'Resume input mismatch'
    else:
        assert not history_path.exists(), 'Refusing to overwrite continuation history'
        history = [initial]
        history_path.write_text(json.dumps(history, indent=2)+'\n')
        shutil.copy2(metrics_path, run_dir/f'metrics_{metrics["final_iteration"]}.json')
        shutil.copy2(main_log, case/f'log.buoyantBoussinesqSimpleFoam.initial0-{metrics["final_iteration"]}')
    policy = dict(startup['continuation_policy'])
    if args.maximum_end_time is not None:
        assert args.resume and args.maximum_end_time > metrics['final_iteration']
        policy['maximum_endTime'] = args.maximum_end_time
        authorization = run_dir/f'authorized_resume_{metrics["final_iteration"]}-{args.maximum_end_time}.json'
        assert not authorization.exists(), 'Resume already recorded'
        authorization.write_text(json.dumps(dict(before=initial, policy=policy),indent=2)+'\n')
    while not passed and metrics['final_iteration'] < policy['maximum_endTime']:
        assert metrics['normal_exit'] and not metrics['fatal_or_nan'], 'STOP: numerical failure'
        start = metrics['final_iteration']
        end = min(start+policy['checkpoint_increment'], policy['maximum_endTime'])
        before = snapshot(case, generated, start)
        for rel,h in generated['input_sha256'].items():
            if rel != 'system/controlDict':
                assert before['input_sha256'][rel] == h, rel
        assert before['mesh_sha256'] == entry['mesh_sha256']
        control = case/'system/controlDict'
        shutil.copy2(control, run_dir/f'controlDict_before_{start}-{end}')
        text = control.read_text()
        text, count = re.subn(r'\bstartFrom\s+\w+;', 'startFrom latestTime;', text)
        assert count == 1
        text, count = re.subn(r'\bendTime\s+[0-9.eE+-]+;', f'endTime {end};', text)
        assert count == 1
        control.write_text(text)
        continuation_log = case/f'log.buoyantBoussinesqSimpleFoam.continuation{start}-{end}'
        provenance_path = run_dir/f'continuation_{start}-{end}.json'
        provenance = dict(before=before, executed_input_sha256={rel:sha(case/rel) for rel in generated['input_sha256']},
                          permitted_changes=['startFrom latestTime', 'endTime extension'], log_path=str(continuation_log))
        provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
        command = ['bash','-lc', 'unset WM_BASH_FUNCTIONS; source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc && exec buoyantBoussinesqSimpleFoam -case '+str(case)]
        with continuation_log.open('w') as stream:
            code = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT).returncode
        provenance['solver_exit_code'] = code
        if code:
            provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
            save_status(cid, 'NUMERICAL_FAILURE', {**entry, 'reason':'Continuation solver failed'})
            raise SystemExit('STOP: continuation solver failed')
        with main_log.open('ab') as stream:
            stream.write(b'\n'); stream.write(continuation_log.read_bytes())
        with (case/f'log.analyze_case.{end}').open('w') as stream:
            code = subprocess.run([sys.executable,str(V6/'Scripts/routeB/analyze_case.py'),str(case)],
                                  stdout=stream, stderr=subprocess.STDOUT,
                                  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}).returncode
        assert code == 0, 'Postprocessing failed'
        metrics = json.loads(metrics_path.read_text())
        assert metrics['final_iteration'] == end
        checks, passed = gate_d(metrics)
        after = snapshot(case, generated, end)
        assert all(sha(case/str(start)/name)==h for name,h in before['field_sha256'].items())
        assert after['mesh_sha256'] == before['mesh_sha256']
        assert after['input_sha256'] == provenance['executed_input_sha256']
        provenance.update(after=after, preserved_start_field_hashes=True, Gate_D_checks=checks)
        provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
        history.append(dict(after, Gate_D='PASS' if passed else 'FAIL', Gate_D_checks=checks, metrics=metrics))
        history_path.write_text(json.dumps(history,indent=2)+'\n')
        shutil.copy2(metrics_path,run_dir/f'metrics_{end}.json')
        fatal = metrics['fatal_or_nan'] or not metrics['normal_exit']
        stage = 'GATE_D_PASS' if passed else ('NUMERICAL_FAILURE' if fatal else 'CONVERGENCE_NOT_REACHED')
        save_status(cid, stage, {**entry,'final_iteration':end,'Rwin':metrics['Rwin'],
                                'final_initial_residuals':metrics['final_initial_residuals'],
                                'normal_exit':metrics['normal_exit'],'fatal_or_nan':metrics['fatal_or_nan']})
        print(json.dumps(dict(iteration=end, stage=stage, failed_checks=[k for k,v in checks.items() if not v])),flush=True)
        if fatal:
            raise SystemExit('STOP: numerical failure')
    print(json.dumps(dict(case_id=cid, Gate_D='PASS' if passed else 'FAIL', final_iteration=metrics['final_iteration'])))


if __name__ == '__main__':
    main()
