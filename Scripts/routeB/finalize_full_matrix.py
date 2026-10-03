#!/usr/bin/env python3
"""Publish Route B partial matrix results without changing historical evidence."""
import csv
import hashlib
import math
import re
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


def finalize_ra1e3(state):
    """Update this authorized Ra only, preserving all historical records."""
    manifest_path = OUT / 'full_matrix_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    cid = 'B-Ra1e3-fine'
    entry = state['cases'][cid]
    case = Path(entry['case_path'])
    generated = json.loads((case / 'case_manifest.json').read_text())
    metrics_path = OUT / 'cases' / cid / 'metrics.json'
    metrics = json.loads(metrics_path.read_text())
    r = metrics['Rwin']
    previous_record = manifest['cases'].get(cid, {})
    continuation = previous_record.get('continuation')
    expected_inputs = dict(generated['input_sha256'])
    if continuation:
        expected_inputs['system/controlDict'] = continuation['continuation_controlDict_sha256']
    inputs_ok = all(sha(case / p) == h for p, h in expected_inputs.items())
    mesh_ok = all(sha(case / p) == h for p, h in entry['mesh_sha256'].items())
    preserved_start_fields = True
    if continuation:
        preserved_start_fields = all(sha(case / str(continuation['continuation_started_from']) / p) == h
                                    for p, h in continuation['iteration_3000_field_sha256'].items())
        continuation_log = case / 'log.buoyantBoussinesqSimpleFoam.continuation3000-6000'
        with continuation_log.open() as stream:
            logged_iterations = [int(match.group(1)) for line in stream
                                 if (match := re.match(r'Time = (\d+)', line))]
        if logged_iterations != list(range(3001, 6001)):
            raise SystemExit('Continuation log is not the authorized 3001 through 6000 sequence')
        continuation.update(first_logged_iteration=logged_iterations[0], last_logged_iteration=logged_iterations[-1],
                            continuation_ended_at=metrics['final_iteration'], completed_at=datetime.now().astimezone().isoformat(),
                            continuation_log_sha256=sha(continuation_log), preserved_iteration_3000_fields=preserved_start_fields,
                            unchanged_other_inputs=inputs_ok, unchanged_mesh=mesh_ok)

    with (case / 'log.buoyantBoussinesqSimpleFoam').open() as stream:
        divergence = any(re.search(r'\bdivergence warning\b|\bsolution diverging\b|FOAM FATAL|Floating point exception \(core dumped\)', line, re.I) for line in stream)
    passed = (metrics['normal_exit'] and not metrics['fatal_or_nan'] and not divergence and inputs_ok and mesh_ok and preserved_start_fields
              and r['window_end_iteration'] - r['window_start_iteration'] >= 200 and r['samples'] >= 21
              and all(math.isfinite(x) and x <= 5e-4 for x in [r['Nu_bar_0'], r['Umax'], r['Vmax']])
              and all(math.isfinite(x) and x <= 1e-7 for x in metrics['final_initial_residuals'].values())
              and r['heat_imbalance_linear_slope_per_iteration'] <= 0)
    stage = 'GATE_D_PASS' if passed else ('NUMERICAL_FAILURE' if divergence or metrics['fatal_or_nan'] or not metrics['normal_exit'] else 'CONVERGENCE_NOT_REACHED')
    entry.update(stage=stage, Gate_D='PASS' if passed else 'FAIL', final_iteration=metrics['final_iteration'],
                 Rwin=r, final_initial_residuals=metrics['final_initial_residuals'], normal_exit=metrics['normal_exit'],
                 fatal_or_nan=metrics['fatal_or_nan'])
    formal = {'E': 'NOT_EVALUATED', 'F': 'NOT_EVALUATED', 'G': 'NOT_EVALUATED'}
    evaluations = {}
    with (OUT / 'benchmark_summary.csv').open() as stream:
        summaries = list(csv.DictReader(stream))
    row = next(row for row in summaries if row['matrix_case_id'] == cid)
    row.update(Ra_actual=generated['Ra_actual'], Pr_actual=generated['Pr_actual'], final_iteration=metrics['final_iteration'],
               source_time_or_iteration=metrics['final_iteration'], Gate_A='PASS' if inputs_ok else 'FAIL',
               Gate_D=entry['Gate_D'], status=stage, method_version='dvd-nusselt-post-v2.1-full-matrix-extension')
    for key, value in metrics.items():
        if key in row and not isinstance(value, (dict, list)):
            row[key] = value
    for key, comp in metrics['paper_comparison_like_for_like'].items():
        for error in ['absolute_relative_error', 'absolute_position_error']:
            if error in comp:
                row[f'{key}_{error}'] = comp[error]
    row.update(Rwin_Nu_bar_0=r['Nu_bar_0'], Rwin_Umax=r['Umax'], Rwin_Wmax=r['Vmax'],
               maximum_final_normalized_residual=max(metrics['final_initial_residuals'].values()))
    with (OUT / 'grid_convergence.csv').open() as stream:
        grid_rows = list(csv.DictReader(stream))
    ra_metrics = {level: json.loads((OUT / 'cases' / f'B-Ra1e3-{level}' / 'metrics.json').read_text()) for level in ['coarse', 'medium']}
    ra_metrics['fine'] = metrics
    if passed:
        comparisons = metrics['paper_comparison_like_for_like']
        e_checks = {key: comparisons[key]['absolute_relative_error'] <= .01 for key in ['Nu_bar_cavity', 'Umax', 'Wmax']}
        e_checks.update({key: comparisons[key]['absolute_position_error'] <= .01 for key in ['Umax_Z', 'Wmax_X']})
        formal['E'] = 'PASS' if all(e_checks.values()) else 'FAIL'
        evaluations['E'] = {'checks': e_checks, 'absolute_errors': {key: row[key] for key in row if 'absolute_' in key and 'error' in key},
                            'note': 'Nu_bar_0 and Nu_bar_half errors reported; no added Hard condition or Nu_bar_1 reference.'}
        f_checks = []
        for g in grid_rows:
            if int(g['Ra_target']) != 1000:
                continue
            quantity = g['quantity']
            c, m, f = [ra_metrics[level][quantity] for level in ['coarse', 'medium', 'fine']]
            d32, d21 = c-m, m-f
            fm = abs((f-m)/f)
            monotonic = d32*d21 > 0
            kind = 'monotonic' if monotonic else ('oscillatory' if d32*d21 < 0 else 'other')
            p = math.log(abs(d32/d21), 2) if monotonic else None
            valid = p is not None and math.isfinite(p) and p > 0
            gci = 3*fm/(2**p-1) if valid else None
            needs = not valid
            limit = .015 if quantity == 'Nu_bar_cavity' else .02
            ok = valid and fm <= .01 and gci <= limit
            g.update(coarse=c, medium=m, fine=f, fine_medium_difference=fm,
                     convergence_type=kind, p_obs=p if p is not None else '', GCI=gci if gci is not None else '',
                     Gate_F='PASS' if ok else 'FAIL', needs_320=needs,
                     reason='Nonmonotonic or undefined/nonpositive observed order; no 320 run performed.' if needs else 'Monotonic convergence; existing fine-medium and GCI thresholds applied.')
            f_checks.append(ok)
        formal['F'] = 'PASS' if all(f_checks) else 'FAIL'
        evaluations['F'] = [g for g in grid_rows if int(g['Ra_target']) == 1000]
        continuity, symmetry = metrics['continuity'], metrics['symmetry']
        g_checks = dict(heat_imbalance=metrics['heat_imbalance'] <= .002,
                        section_conservation=metrics['section_Nu_max_relative_deviation_from_half'] <= .005,
                        reconstructed_mass_divergence=continuity['epsilon_m'] <= 1e-6,
                        reconstructed_volume_divergence=continuity['epsilon_v'] <= .002,
                        temperature_symmetry=symmetry['theta_L2_relative'] <= .002,
                        velocity_symmetry=symmetry['velocity_L2_relative'] <= .002)
        formal['G'] = 'PASS' if all(g_checks.values()) else 'FAIL'
        evaluations['G'] = {'checks':g_checks, 'continuity':continuity, 'symmetry':symmetry,
                            'heat_imbalance':metrics['heat_imbalance'], 'section_Nu_max_relative_deviation_from_half':metrics['section_Nu_max_relative_deviation_from_half'],
                            'note':'Saved solver volume-flux epsilon_phi reported separately; epsilon_m=epsilon_v from reconstructed U is compared to both existing criteria without substitution.'}
    else:
        for g in grid_rows:
            if int(g['Ra_target']) == 1000:
                g.update(**{level:ra_metrics[level][g['quantity']] for level in ['coarse','medium','fine']},
                         reason='Fine Gate D failed; values are unaccepted diagnostics; formal three-grid evaluation not performed.')
    row.update(Gate_E=formal['E'], Gate_G=formal['G'])
    record = dict(matrix_case_id=cid, source_case_id=cid, reused_existing_solver_result=False,
                  generated_manifest=generated, final_iteration=metrics['final_iteration'], Gate_D=entry['Gate_D'],
                  Rwin=r, metrics_path=str(metrics_path), metrics_sha256=sha(metrics_path), input_hashes_verified=inputs_ok,
                  final_field_sha256={str(p.relative_to(V6)):sha(p) for p in (case/str(metrics['final_iteration'])).iterdir() if p.is_file()},
                  mesh_sha256=entry['mesh_sha256'], log_sha256={p.name:sha(p) for p in case.glob('log.*') if p.is_file()},
                  environment_log=(case/'log.environment').read_text())
    if passed:
        record['accepted_final_field_sha256'] = record['final_field_sha256']
    else:
        record['unaccepted_reason'] = 'Gate D not reached; final fields retained for diagnostics and possible authorized continuation.'
    residual_window = {}
    current_iteration = None
    with (case / 'log.buoyantBoussinesqSimpleFoam').open() as stream:
        for line in stream:
            match = re.match(r'Time = (\d+)', line)
            if match:
                current_iteration = int(match.group(1))
            match = re.search(r'Solving for (Ux|Uy|T|p_rgh), Initial residual = ([^,]+)', line)
            if match and current_iteration is not None and current_iteration >= metrics['final_iteration'] - 200:
                residual_window.setdefault(current_iteration, {})[match.group(1)] = float(match.group(2))
    first = min(residual_window)
    record['final_window_residual_trend'] = {key:{'window_start_iteration':first,
        'start':residual_window[first][key], 'end':value,
        'end_to_start_ratio':value/residual_window[first][key] if residual_window[first][key] else None}
        for key,value in metrics['final_initial_residuals'].items()}
    record['failure_classification'] = None if passed else ('numerical failure' if stage == 'NUMERICAL_FAILURE' else 'iteration convergence not reached; no input changes or automatic extension')
    history = [item for item in previous_record.get('iteration_history', [])
               if item['iteration'] != metrics['final_iteration']]
    result = {'iteration':metrics['final_iteration'], 'stage':stage, 'Gate_D':entry['Gate_D'],
              'Rwin':r, 'final_initial_residuals':metrics['final_initial_residuals'],
              'heat_imbalance':metrics['heat_imbalance'], 'residual_trend':record['final_window_residual_trend']}
    record['iteration_history'] = history + [result]
    entry['iteration_history'] = record['iteration_history']
    if continuation:
        record['continuation'] = continuation
        record['executed_continuation_input_sha256'] = expected_inputs
        entry['continuation'] = continuation
        before = next(item['metrics'] for item in history if item['iteration'] == 3000)
        record['improvement_since_3000'] = {
            'Rwin':{key:{'before':before['Rwin'][key], 'after':r[key],
                         'reduction_factor':before['Rwin'][key]/r[key] if r[key] else None}
                    for key in ['Nu_bar_0','Umax','Vmax']},
            'final_initial_residuals':{key:{'before':before['final_initial_residuals'][key], 'after':value,
                                          'reduction_factor':before['final_initial_residuals'][key]/value if value else None}
                                      for key,value in metrics['final_initial_residuals'].items()}}

    manifest['cases'][cid] = record
    with (OUT / 'conservation.csv').open() as stream:
        conservation = list(csv.DictReader(stream))
    conservation = [c for c in conservation if c.get('matrix_case_id') != cid]
    cons = {k:row[k] for k in ['case_id','matrix_case_id','source_case_id','reused_existing_solver_result','Ra_target','Ra_actual','Pr_actual','grid','route','status','source_time_or_iteration','method_version']}
    cons.update({k:metrics[k] for k in ['Nu_bar_0','Nu_bar_half','Nu_bar_cavity','Nu_bar_1','heat_imbalance','section_Nu_max_relative_deviation_from_half']})
    cons.update(metrics['continuity']); cons.update(metrics['symmetry']); cons['Gate_G'] = formal['G']; conservation.append(cons)
    write_csv(OUT/'benchmark_summary.csv',summaries); write_csv(OUT/'grid_convergence.csv',grid_rows); write_csv(OUT/'conservation.csv',conservation)
    needs = any(g['needs_320'] is True for g in grid_rows if int(g['Ra_target'])==1000) if passed else None
    state['formal_Ra_gates']['1000'] = formal
    state.update(status='READY_TO_RESUME_AWAITING_USER' if passed else 'STOPPED_CONVERGENCE_NOT_REACHED',
                 stop_cases=[] if passed else [cid], accepted_matrix_points=sum(r['Gate_D']=='PASS' for r in summaries),
                 solver_finished_matrix_points=sum(r['final_iteration']!='' for r in summaries),
                 FULL_MATRIX_RESUME='YES' if passed else 'NO', B_RA1E3_FINE_GATE_D=entry['Gate_D'],
                 needs_320=needs, needs_320_reason='See Ra=1000 grid_convergence rows.' if passed else 'Fine Gate D failed; formal grid evaluation not performed.',
                 new_solver_runs_this_invocation=1,
                 required_user_decision='Authorize remaining cases; this invocation executed only B-Ra1e3-fine.' if passed else 'Decide whether to authorize further steady iterations for B-Ra1e3-fine; no extension beyond the authorized limit.',
                 BENCHMARK_CORE_PASS='NOT_EVALUATED')
    manifest.update(schema='routeB-full-matrix-v1',generated_at=datetime.now().astimezone().isoformat(),
                    status=state['status'], FULL_MATRIX_RESUME=state['FULL_MATRIX_RESUME'], formal_Ra_gates=state['formal_Ra_gates'],
                    Ra1e3_gate_evaluations=evaluations, solver_runs_this_invocation=1,
                    script_sha256={str(p.relative_to(V13)):sha(p) for p in (V13/'Scripts/routeB').glob('*') if p.is_file()},
                    canonical_execution_scripts_match=all(sha(p)==sha(V6/'Scripts/routeB'/p.name) for p in (V13/'Scripts/routeB').glob('*') if p.is_file()),
                    limitation='Full 12-point matrix incomplete. Other Ra formal gates remain unevaluated. No automatic iteration extension or other case execution.')
    manifest['Ra1e3_cavity_method_diagnostic'] = {level:{key:v[key] for key in ['Nu_bar_cavity','Nu_bar_cavity_from_section_trapezoid','Nu_bar_cavity_method_absolute_difference','Nu_bar_cavity_method_relative_difference']} for level,v in ra_metrics.items()}
    (OUT/'full_matrix_status.json').write_text(json.dumps(state,indent=2)+'\n')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'Gate_D':entry['Gate_D'],'formal_gates':formal,'needs_320':needs,'accepted_matrix_points':state['accepted_matrix_points']}))


def main():
    state = json.loads((OUT / 'full_matrix_status.json').read_text())
    original = json.loads((OUT / 'run_manifest.json').read_text())
    audit = json.loads((OUT / 'full_matrix_preflight.json').read_text())
    if 'B-Ra1e3-fine' in state['cases']:
        return finalize_ra1e3(state)
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
