#!/usr/bin/env python3
"""Publish one evaluated matrix case while preserving other case records."""
import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np

from finalize_full_matrix import OUT, V6, sha, write_csv
from foam_fields import read_boundary_scalar, read_label_list, read_scalar, read_vector


def gate_d(metrics):
    r = metrics['Rwin']
    residuals = np.array(list(metrics['final_initial_residuals'].values()))
    checks = dict(normal_exit=metrics['normal_exit'], finite_execution=not metrics['fatal_or_nan'],
                  window=r['window_end_iteration']-r['window_start_iteration'] >= 200,
                  samples=r['samples'] >= 21,
                  QoI=max(r[k] for k in ('Nu_bar_0', 'Umax', 'Vmax')) <= 5e-4,
                  residuals=bool(np.all(np.isfinite(residuals)) and np.max(residuals) <= 1e-7),
                  heat_trend=r['heat_imbalance_linear_slope_per_iteration'] <= 0)
    return checks, all(checks.values())


def flux_diagnostics(case, generated, metrics):
    nx, ny, _ = generated['grid']
    L, width = generated['geometry_m']['L'], generated['geometry_m']['W']
    folder = case/str(metrics['final_iteration'])
    owner = read_label_list(case/'constant/polyMesh/owner')
    neighbour = read_label_list(case/'constant/polyMesh/neighbour')
    internal = read_scalar(folder/'phi', len(neighbour))
    balance = np.zeros(nx*ny)
    np.add.at(balance, owner[:len(neighbour)], internal)
    np.add.at(balance, neighbour, -internal)
    offset = len(neighbour)
    patches = {}
    for name, size in [('hotWall', ny), ('coldWall', ny), ('bottomWall', nx),
                       ('topWall', nx), ('front', nx*ny), ('back', nx*ny)]:
        if name in ('front', 'back'):
            patches[name] = {'type': 'empty', 'net_volume_flux_m3_s': 0.0}
        else:
            values = read_boundary_scalar(folder/'phi', name, size)
            np.add.at(balance, owner[offset:offset+size], values)
            patches[name] = dict(net_volume_flux_m3_s=float(values.sum()),
                                 absolute_volume_flux_m3_s=float(np.abs(values).sum()))
        offset += size
    volume = (L/nx)*(L/ny)*width
    U = read_vector(folder/'U', nx*ny)
    Uscale = float(np.linalg.norm(U, axis=1).max())
    epsilon = L*np.abs(balance/volume)/Uscale
    assert np.isclose(epsilon.mean(), metrics['continuity']['epsilon_phi'], rtol=1e-12, atol=1e-20)
    net_boundary = sum(p['net_volume_flux_m3_s'] for p in patches.values())
    return dict(epsilon_phi_mean=float(epsilon.mean()), epsilon_phi_max=float(epsilon.max()),
                epsilon_phi_P95=float(np.percentile(epsilon, 95)),
                epsilon_phi_P99=float(np.percentile(epsilon, 99)),
                definition='L*abs(sum oriented saved pressure-corrected face phi / cell volume)/max cell speed',
                normalization_Umax_m_s=Uscale, boundary_patches=patches,
                boundary_net_volume_flux_m3_s=net_boundary,
                global_signed_div_phi_1_s=float(balance.sum()/(volume*nx*ny)),
                flux_balance_closure_m3_s=float(balance.sum()-net_boundary),
                final_solver_log_continuity=metrics['final_log_continuity'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-id', required=True)
    args = parser.parse_args()
    cid = args.case_id
    state_path, manifest_path = OUT/'full_matrix_status.json', OUT/'full_matrix_manifest.json'
    state = json.loads(state_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    entry = state['cases'][cid]
    case = Path(entry['case_path'])
    generated = json.loads((case/'case_manifest.json').read_text())
    metrics_path = OUT/'cases'/cid/'metrics.json'
    metrics = json.loads(metrics_path.read_text())
    checks, passed = gate_d(metrics)
    expected = dict(generated['input_sha256'])
    run_dir = OUT/f'formal_resume_{cid}'
    history = json.loads((run_dir/'iteration_history.json').read_text())
    if len(history) > 1:
        expected['system/controlDict'] = history[-1]['input_sha256']['system/controlDict']
    assert all(sha(case/rel) == h for rel, h in expected.items()), 'Input provenance mismatch'
    assert all(sha(case/rel) == h for rel, h in entry['mesh_sha256'].items()), 'Mesh changed'
    diagnostics = dict(flux_diagnostics(case, generated, metrics), **metrics['continuity'],
                       **metrics['symmetry'], heat_imbalance=metrics['heat_imbalance'],
                       section_Nu_max_relative_deviation_from_half=metrics['section_Nu_max_relative_deviation_from_half'],
                       GATE_G_FORMAL_STATUS='NOT_EVALUATED_UNDER_FROZEN_REVIEW')
    (metrics_path.parent/'gateG_diagnostics.json').write_text(json.dumps(diagnostics, indent=2)+'\n')
    summaries = list(csv.DictReader((OUT/'benchmark_summary.csv').open()))
    row = next(r for r in summaries if r['matrix_case_id'] == cid)
    row.update(Ra_actual=generated['Ra_actual'], Pr_actual=generated['Pr_actual'],
               final_iteration=metrics['final_iteration'], source_time_or_iteration=metrics['final_iteration'],
               Gate_A='PASS', Gate_D='PASS' if passed else 'FAIL',
               Gate_E='NOT_EVALUATED', Gate_G=diagnostics['GATE_G_FORMAL_STATUS'],
               status='GATE_D_PASS' if passed else 'CONVERGENCE_NOT_REACHED',
               method_version='dvd-nusselt-post-v2.1-full-matrix-extension')
    for key in row:
        if key in metrics and isinstance(metrics[key], (int, float)):
            row[key] = metrics[key]
    for key, comparison in metrics['paper_comparison_like_for_like'].items():
        for error in ('absolute_relative_error', 'absolute_position_error'):
            if error in comparison:
                row[f'{key}_{error}'] = comparison[error]
    row.update(Rwin_Nu_bar_0=metrics['Rwin']['Nu_bar_0'], Rwin_Umax=metrics['Rwin']['Umax'],
               Rwin_Wmax=metrics['Rwin']['Vmax'],
               maximum_final_normalized_residual=max(metrics['final_initial_residuals'].values()))
    grids = list(csv.DictReader((OUT/'grid_convergence.csv').open()))
    fine = cid.endswith('-fine')
    ra_key = str(int(generated['Ra_target']))
    evaluations = {}
    for g in grids:
        if not fine and int(g['Ra_target']) == int(generated['Ra_target']):
            g.update(medium=metrics[g['quantity']] if passed else '', Gate_F='NOT_EVALUATED',
                     reason='Two accepted grids available; fine not executed. Three-grid evaluation deferred.' if passed
                     else 'Medium Gate D failed; no three-grid evaluation.')
    if fine and passed:
        comparisons = metrics['paper_comparison_like_for_like']
        e_checks = {key:comparisons[key]['absolute_relative_error'] <= .01
                    for key in ('Nu_bar_cavity','Umax','Wmax')}
        e_checks.update({key:comparisons[key]['absolute_position_error'] <= .01
                         for key in ('Umax_Z','Wmax_X')})
        row['Gate_E'] = 'PASS' if all(e_checks.values()) else 'FAIL'
        evaluations['E'] = dict(checks=e_checks, criteria_source='Scripts/routeB/finalize_full_matrix.py',
                                comparisons=comparisons)
        prefix = cid.rsplit('-',1)[0]
        levels = {}
        for level in ('coarse','medium'):
            rec = manifest['cases'][prefix+'-'+level]
            assert rec['Gate_D'] == 'PASS', 'Three accepted grids required'
            levels[level] = json.loads(Path(rec['metrics_path']).read_text())
        f_checks = []
        for g in grids:
            if str(g['Ra_target']) != ra_key:
                continue
            quantity = g['quantity']
            c,m,f = levels['coarse'][quantity],levels['medium'][quantity],metrics[quantity]
            d32,d21 = c-m,m-f
            monotonic = d32*d21 > 0
            p = math.log(abs(d32/d21),2) if monotonic else None
            valid = p is not None and math.isfinite(p) and p > 0
            fm = abs((f-m)/f)
            gci = 3*fm/(2**p-1) if valid else None
            passed_f = valid and fm <= .01 and gci <= (.015 if quantity=='Nu_bar_cavity' else .02)
            g.update(coarse=c,medium=m,fine=f,fine_medium_difference=fm,
                     convergence_type='monotonic' if monotonic else ('oscillatory' if d32*d21 < 0 else 'other'),
                     p_obs=p if valid else '',GCI=gci if valid else '',
                     Gate_F='PASS' if passed_f else 'FAIL',needs_320=not valid,
                     reason='Existing three-grid thresholds applied; no 320 run performed.' if valid
                     else 'Nonmonotonic or undefined/nonpositive observed order; no 320 run performed.')
            f_checks.append(passed_f)
        evaluations['F'] = [g.copy() for g in grids if str(g['Ra_target']) == ra_key]
        state['formal_Ra_gates'][ra_key] = dict(E=row['Gate_E'],F='PASS' if all(f_checks) else 'FAIL',
                                             G=diagnostics['GATE_G_FORMAL_STATUS'])
    conservation = list(csv.DictReader((OUT/'conservation.csv').open()))
    conservation = [r for r in conservation if r.get('matrix_case_id') != cid]
    cons = {k: row[k] for k in ['case_id','matrix_case_id','source_case_id','reused_existing_solver_result',
                               'Ra_target','Ra_actual','Pr_actual','grid','route','status','source_time_or_iteration','method_version']}
    cons.update({k:metrics[k] for k in ['Nu_bar_0','Nu_bar_half','Nu_bar_cavity','Nu_bar_1',
                                     'heat_imbalance','section_Nu_max_relative_deviation_from_half']})
    cons.update(metrics['continuity']); cons.update(metrics['symmetry']); cons['Gate_G'] = row['Gate_G']
    conservation.append(cons)
    field_hashes = {str(p.relative_to(V6)):sha(p) for p in (case/str(metrics['final_iteration'])).iterdir() if p.is_file()}
    record = dict(matrix_case_id=cid, source_case_id=cid, reused_existing_solver_result=False,
                  generated_manifest=generated, final_iteration=metrics['final_iteration'], Gate_D=row['Gate_D'],
                  Rwin=metrics['Rwin'], Gate_D_checks=checks, metrics_path=str(metrics_path), metrics_sha256=sha(metrics_path),
                  final_field_sha256=field_hashes, input_hashes_verified=True, executed_input_sha256=expected,
                  mesh_sha256=entry['mesh_sha256'], log_sha256={p.name:sha(p) for p in case.glob('log.*') if p.is_file()},
                  environment_log=(case/'log.environment').read_text(), iteration_history=history,
                  Gate_G_formal_status=row['Gate_G'], Gate_G_diagnostics_path=str(metrics_path.parent/'gateG_diagnostics.json'))
    if passed:
        record['accepted_final_field_sha256'] = field_hashes
    manifest['cases'][cid] = record
    entry.update(stage=row['status'], Gate_D=row['Gate_D'], Gate_D_checks=checks,
                 final_iteration=metrics['final_iteration'], iteration_history=history, Gate_G_formal_status=row['Gate_G'])
    state.update(status='READY_TO_RESUME_AWAITING_USER' if passed else 'STOPPED_CONVERGENCE_NOT_REACHED',
                 stop_cases=[] if passed else [cid], accepted_matrix_points=sum(r['Gate_D']=='PASS' for r in summaries),
                 solver_finished_matrix_points=sum(str(r['final_iteration'])!='' for r in summaries),
                 FULL_MATRIX_RESUME='YES' if passed else 'NO', new_solver_runs_this_invocation=1,
                 continuation_solver_runs_this_invocation=len(history)-1,
                 GATE_G_INVESTIGATION_STATUS='FROZEN_PENDING_POST_MATRIX_REVIEW', GATE_G_BLOCKS_MATRIX_EXECUTION='NO',
                 required_user_decision=('Authorize the next case separately; this invocation ran only '+cid+'.') if passed
                 else 'Gate D not reached within the bounded continuation policy; review before further work.')
    manifest.update(generated_at=datetime.now().astimezone().isoformat(), status=state['status'],
                    FULL_MATRIX_RESUME=state['FULL_MATRIX_RESUME'], solver_runs_this_invocation=1,
                    continuation_solver_runs_this_invocation=len(history)-1,
                    GATE_G_INVESTIGATION_STATUS=state['GATE_G_INVESTIGATION_STATUS'], GATE_G_BLOCKS_MATRIX_EXECUTION='NO')
    if fine and passed:
        manifest['formal_Ra_gates'] = state['formal_Ra_gates']
        manifest[cid.rsplit('-',1)[0].removeprefix('B-')+'_gate_evaluations'] = evaluations
        state[cid.rsplit('-',1)[0].removeprefix('B-')+'_needs_320'] = any(g['needs_320'] for g in evaluations['F'])
        record.update(Gate_E=state['formal_Ra_gates'][ra_key]['E'],
                      Gate_F=state['formal_Ra_gates'][ra_key]['F'],
                      needs_320=state[cid.rsplit('-',1)[0].removeprefix('B-')+'_needs_320'])
        if record['needs_320']:
            state['needs_320'] = True
            state['needs_320_reason'] = 'Existing Ra=1000 findings retained; Ra='+ra_key+' has a nonmonotonic or invalid-order quantity. See grid_convergence.csv; no 320 run performed.'
            state['required_user_decision'] = 'Review the 320-grid follow-up in a separate task; this invocation executed only '+cid+'.'
        manifest['limitation'] = 'Full 12-point matrix incomplete. Accepted fine case '+cid+' has Gate E '+record['Gate_E']+' and Gate F '+record['Gate_F']+'. Gate G review remains frozen; no extra grid or other case executed.'
    assert state['formal_Ra_gates']['1000']['G'] == 'FAIL'
    if not fine:
        assert state['formal_Ra_gates'][ra_key]['E'] == state['formal_Ra_gates'][ra_key]['F'] == 'NOT_EVALUATED'
    write_csv(OUT/'benchmark_summary.csv', summaries)
    write_csv(OUT/'grid_convergence.csv', grids)
    write_csv(OUT/'conservation.csv', conservation)
    state_path.write_text(json.dumps(state,indent=2)+'\n')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(case_id=cid, Gate_D=row['Gate_D'], accepted=state['accepted_matrix_points'])))


if __name__ == '__main__':
    main()
