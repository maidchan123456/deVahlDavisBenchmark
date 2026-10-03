#!/usr/bin/env python3
"""Publish a stopped Route B matrix without changing minimal-run evidence."""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

V13 = Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark')
V6 = Path('/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark')
OUT = V13 / 'results/routeB'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    state = json.loads((OUT / 'full_matrix_status.json').read_text())
    original = json.loads((OUT / 'run_manifest.json').read_text())
    audit = json.loads((OUT / 'full_matrix_preflight.json').read_text())
    if any(k.endswith('-fine') for k in state['cases']):
        raise SystemExit('This stopped-matrix finalizer requires extension for formal fine-grid E/F/G evaluation.')
    records, summaries, conservation = {}, [], []
    reuse = audit['B_SMOKE_reuse_accepted']
    for label, ra in [('1e3', 1000), ('1e4', 10000), ('1e5', 100000), ('1e6', 1000000)]:
        for level, n in [('coarse', 40), ('medium', 80), ('fine', 160)]:
            cid = f'B-Ra{label}-{level}'
            reused = reuse and cid == 'B-Ra1e4-coarse'
            source = 'B-SMOKE' if reused else cid
            entry = state['cases'].get(cid, {})
            exists = reused or bool(entry)
            row = dict(matrix_case_id=cid, source_case_id=source, reused_existing_solver_result=reused,
                       case_id=source, route='B', Ra_target=ra, Ra_actual='', Pr_actual='',
                       grid=f'{n}x{n}x1', final_iteration='', source_time_or_iteration='',
                       Gate_A='NOT_EVALUATED', Gate_D='NOT_EVALUATED',
                       Gate_E_applicable=level == 'fine', Gate_E='NOT_EVALUATED' if level == 'fine' else 'NOT_APPLICABLE',
                       Gate_G_applicable=level == 'fine', Gate_G='NOT_EVALUATED' if level == 'fine' else 'NOT_APPLICABLE',
                       status='NOT_RUN', method_version='')
            if exists:
                baseline = original['cases']['B-SMOKE'] if reused else None
                case = Path(baseline['generated_manifest']['case_path'] if reused else entry['case_path'])
                generated = baseline['generated_manifest'] if reused else json.loads((case / 'case_manifest.json').read_text())
                metrics_path = OUT / 'cases' / source / 'metrics.json'
                metrics = json.loads(metrics_path.read_text())
                rwin = dict(metrics['Rwin'])
                if reused:
                    with (metrics_path.parent / 'convergence.csv').open() as f:
                        window = [r for r in csv.DictReader(f) if 2800 <= int(r['iteration']) <= 3000]
                    vals = [float(r['Nu_bar_0']) for r in window if r['Nu_bar_0']]
                    if len(vals) < 21:
                        raise SystemExit('B-SMOKE has insufficient saved final-window Nu_bar_0 samples')
                    rwin['Nu_bar_0'] = (max(vals)-min(vals))/max(abs(sum(vals)/len(vals)), 1.0)
                passed = (metrics['normal_exit'] and not metrics['fatal_or_nan'] and
                          rwin['window_end_iteration']-rwin['window_start_iteration'] >= 200 and
                          max(rwin['Nu_bar_0'], rwin['Umax'], rwin['Vmax']) <= 5e-4 and
                          max(metrics['final_initial_residuals'].values()) <= 1e-7 and
                          rwin['heat_imbalance_linear_slope_per_iteration'] <= 0)
                status = 'GATE_D_PASS' if passed else 'CONVERGENCE_NOT_REACHED'
                row.update(Ra_actual=generated['Ra_actual'], Pr_actual=generated['Pr_actual'],
                           final_iteration=metrics['final_iteration'], source_time_or_iteration=metrics['final_iteration'],
                           Gate_A='PASS', Gate_D='PASS' if passed else 'FAIL', status=status,
                           method_version=original['postprocessing_version'] if reused else 'dvd-nusselt-post-v2.1-full-matrix-extension')
                for k in ['Nu_bar_0', 'Nu_bar_half', 'Nu_bar_cavity', 'Nu_bar_1',
                          'Nu_bar_cavity_from_section_trapezoid', 'Nu_bar_cavity_method_absolute_difference',
                          'Nu_bar_cavity_method_relative_difference', 'Umax', 'Umax_Z', 'Wmax', 'Wmax_X',
                          'Nu_hot_local_max', 'Nu_hot_local_max_Z', 'Nu_hot_local_min', 'Nu_hot_local_min_Z']:
                    row[k] = metrics[k]
                for k, comp in (metrics.get('paper_comparison_like_for_like') or {}).items():
                    for error in ['absolute_relative_error', 'absolute_position_error']:
                        if error in comp:
                            row[f'{k}_{error}'] = comp[error]
                row.update(Rwin_Nu_bar_0=rwin['Nu_bar_0'], Rwin_Umax=rwin['Umax'], Rwin_Wmax=rwin['Vmax'],
                           maximum_final_normalized_residual=max(metrics['final_initial_residuals'].values()))
                record = dict(matrix_case_id=cid, source_case_id=source, reused_existing_solver_result=reused,
                              generated_manifest=generated, Rwin=rwin, Gate_D=row['Gate_D'],
                              metrics_path=str(metrics_path), metrics_sha256=sha(metrics_path))
                if reused:
                    record.update(accepted_final_field_sha256=baseline['accepted_final_field_sha256'],
                                  accepted_field_hash_root=str(V6),
                                  historical_manifest='results/routeB/run_manifest.json#/cases/B-SMOKE',
                                  note='Originally executed as B-SMOKE and subsequently accepted as the Route B full-matrix Ra=1e4 coarse point after input/environment/provenance equivalence audit.')
                else:
                    record.update(accepted_final_field_sha256={str(p.relative_to(V6)):sha(p) for p in (case / str(metrics['final_iteration'])).iterdir() if p.is_file()},
                                  input_hashes_verified=all(sha(case / p)==h for p,h in generated['input_sha256'].items()),
                                  mesh_sha256={str(p.relative_to(case)):sha(p) for p in (case / 'constant/polyMesh').iterdir() if p.is_file()},
                                  log_sha256={p.name:sha(p) for p in case.glob('log.*') if p.is_file()},
                                  environment_log=(case/'log.environment').read_text())
                records[cid] = record
                cons = {k: row[k] for k in ['case_id','matrix_case_id','source_case_id','reused_existing_solver_result','Ra_target','Ra_actual','Pr_actual','grid','route','status','source_time_or_iteration','method_version']}
                cons.update({k: metrics[k] for k in ['Nu_bar_0','Nu_bar_half','Nu_bar_cavity','Nu_bar_1','heat_imbalance','section_Nu_max_relative_deviation_from_half']})
                cons.update(metrics['continuity']); cons.update(metrics.get('symmetry', {})); cons['Gate_G'] = row['Gate_G']
                conservation.append(cons)
            summaries.append(row)
    write_csv(OUT/'benchmark_summary.csv', summaries)
    grid_rows = []
    for ra in [1000,10000,100000,1000000]:
        for quantity in ['Nu_bar_cavity','Umax','Wmax']:
            values = {level: next(r for r in summaries if r['Ra_target']==ra and r['grid']==f'{n}x{n}x1').get(quantity,'') for level,n in [('coarse',40),('medium',80),('fine',160)]}
            grid_rows.append(dict(Ra_target=ra, quantity=quantity, **values, fine_medium_difference='', convergence_type='INSUFFICIENT_GRIDS', p_obs='', GCI='', Gate_F='NOT_EVALUATED', needs_320='', reason='Stopped at Gate D failure; three accepted grids unavailable.'))
    write_csv(OUT/'grid_convergence.csv', grid_rows)
    # Preserve minimal rows and columns; replace only previously emitted formal rows.
    with (OUT/'conservation.csv').open() as f:
        minimal = [r for r in csv.DictReader(f) if not r.get('matrix_case_id')]
    write_csv(OUT/'conservation.csv', minimal + conservation)
    failures = [r['matrix_case_id'] for r in summaries if r['Gate_D']=='FAIL']
    state.update(status='STOPPED_CONVERGENCE_NOT_REACHED', stop_cases=failures,
                 solver_finished_matrix_points=len(records), accepted_matrix_points=sum(r['Gate_D']=='PASS' for r in summaries),
                 matrix_points_total=12, preexisting_formal_solver_runs=2, new_solver_runs_this_invocation=0,
                 reused_existing_solver_results=int(reuse), ROUTE_B_FULL_MATRIX_COMPLETE='NO',
                 BENCHMARK_CORE_PASS='NOT_EVALUATED', needs_320=None,
                 needs_320_reason='Insufficient accepted grids; no 320 grid authorized or run.',
                 required_user_decision='Whether to authorize additional iterations for B-Ra1e3-medium; no extension performed.',
                 formal_Ra_gates={str(ra):{g:'NOT_EVALUATED' for g in ['E','F','G']} for ra in [1000,10000,100000,1000000]})
    if reuse:
        state['cases']['B-Ra1e4-coarse'] = dict(stage='GATE_D_PASS', source_case_id='B-SMOKE', reused_existing_solver_result=True, Gate_A='PASS', Gate_D='PASS')
    (OUT/'full_matrix_status.json').write_text(json.dumps(state,indent=2)+'\n')
    manifest = dict(schema='routeB-stopped-full-matrix-v1', generated_at=datetime.now().astimezone().isoformat(),
                    preflight=audit, cases=records, status=state['status'],
                    existing_uncommitted_work_preserved=True, solver_runs_this_invocation=0,
                    script_sha256={str(p.relative_to(V13)):sha(p) for p in (V13/'Scripts/routeB').glob('*') if p.is_file()},
                    canonical_paper_reference={'path':'reference/de_vahl_davis_table_v.csv','sha256':sha(V13/'reference/de_vahl_davis_table_v.csv')},
                    ROUTE_B_FULL_MATRIX_COMPLETE='NO', BENCHMARK_CORE_PASS='NOT_EVALUATED',
                    limitation='Formal fine-grid and three-grid gates remain unevaluated; runner must not resume until user authorizes resolution of the Gate D failure.')
    (OUT/'full_matrix_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:state[k] for k in ['status','solver_finished_matrix_points','accepted_matrix_points','stop_cases','ROUTE_B_FULL_MATRIX_COMPLETE','BENCHMARK_CORE_PASS']}))


if __name__ == '__main__':
    main()
