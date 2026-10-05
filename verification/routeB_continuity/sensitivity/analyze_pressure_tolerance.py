#!/usr/bin/env python3
"""Analyze only amendment003 branches with rules frozen before their execution."""
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
from pressure_tolerance_diagnostic import (
    AMEND, AUDIT, CHECKPOINTS, FIELDS, HERE, LEVELS, ORDER, OUT, PARENT, ROOT, WORK,
    dump, git, guard, load, monitor_windows, now, numeric_payload, rows, save_csv, sha, tree_hashes,
)
from experiment import QOIS

MAJOR = ('QoI_max_range', 'U_change_20', 'T_change_20', 'heat_window_range')
PRIMARY = ('R_recursive', 'epsilon_phi_mean', 'epsilon_phi_max', *MAJOR)


def statistics(values):
    a = np.asarray(values, dtype=float)
    if not len(a) or not np.isfinite(a).all():
        raise RuntimeError('STOP: missing/nonfinite analysis data')
    return {'min': float(a.min()), 'median': float(np.median(a)), 'max': float(a.max()), 'P95': float(np.percentile(a, 95)), 'samples': len(a)}


def equation_residuals(path):
    result = []
    iteration = None
    pattern = re.compile(r'Solving for (Ux|Uy|Uz|T|p_rgh), Initial residual = ([\deE+.-]+), Final residual = ([\deE+.-]+), No Iterations (\d+)')
    with Path(path).open() as stream:
        for line in stream:
            match = re.fullmatch(r'Time = (\d+)\s*', line)
            if match:
                iteration = int(match.group(1))
            match = pattern.search(line)
            if match:
                result.append({'iteration': iteration, 'equation': match.group(1), 'initial_residual': float(match.group(2)), 'final_residual': float(match.group(3)), 'linear_iterations': int(match.group(4))})
    return result


def field_comparison(branch, iteration, scales):
    output = []
    for field in FIELDS:
        cp = WORK / 'snapshots/P10' / str(iteration) / field
        tp = WORK / 'snapshots' / branch / str(iteration) / field
        ch, cb, cm = numeric_payload(cp, field)
        th, tb, tm = numeric_payload(tp, field)
        if cm != tm:
            raise RuntimeError('STOP: numerical field structure differs')
        differences = [(key, t - c) for (key, c), (_, t) in zip(cb, tb)]
        data = np.concatenate([a for key, a in differences if not key.endswith('/gradient')], axis=0)
        mag = np.linalg.norm(data, axis=1) if field == 'U' else np.abs(data)
        internal = differences[0][1]
        im = np.linalg.norm(internal, axis=1) if field == 'U' else np.abs(internal)
        scale_key = {'U': 'U_Up_reference_m_s', 'T': 'T_DeltaT_K', 'p_rgh': 'p_rgh_parent_centered_internal_RMS_m2_s2', 'phi': 'phi_characteristic_face_flux_m3_s'}[field]
        scale = scales[scale_key]
        gradients = np.concatenate([a for key, a in differences if key.endswith('/gradient')]) if field == 'p_rgh' else np.empty(0)
        output.append({'branch': branch, 'reference': 'P10', 'iteration': iteration, 'field': field,
            'max_abs_difference': float(mag.max()), 'RMS_difference': float(np.sqrt(np.mean(mag ** 2))),
            'normalized_max_difference': float(mag.max() / scale), 'normalized_RMS_difference': float(np.sqrt(np.mean(mag ** 2)) / scale),
            'normalization_scale': scale, 'scale_definition': scale_key, 'units': {'U': 'm/s', 'T': 'K', 'p_rgh': 'm2/s2', 'phi': 'm3/s'}[field],
            'internal_max_abs_difference': float(im.max()), 'internal_RMS_difference': float(np.sqrt(np.mean(im ** 2))),
            'component_max_abs_difference': float(np.abs(data).max()), 'value_locations': len(data),
            'L1_difference': float(mag.sum()) if field == 'phi' else None,
            'gradient_max_abs_difference': float(np.abs(gradients).max()) if gradients.size else None,
            'gradient_RMS_difference': float(np.sqrt(np.mean(gradients ** 2))) if gradients.size else None,
            'P10_raw_sha256': sha(cp), 'branch_raw_sha256': sha(tp), 'P10_payload_sha256': ch, 'branch_payload_sha256': th,
            'raw_identical': sha(cp) == sha(tp), 'payload_identical': ch == th})
    return output


def table(data, keys):
    def fmt(value):
        return f'{value:.7e}' if isinstance(value, float) else ('null' if value is None else str(value))
    return '\n'.join(['| ' + ' | '.join(keys) + ' |', '| ' + ' | '.join('---' for _ in keys) + ' |'] + ['| ' + ' | '.join(fmt(row.get(key)) for key in keys) + ' |' for row in data])


def build_figures(histories, residuals, summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder = OUT / 'figures'
    folder.mkdir(exist_ok=True)
    colors = {'P8': '#d97706', 'P10': '#2563eb', 'P12': '#15803d'}
    def plot_grid(keys, filename, title, log=False):
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
        for ax, key in zip(axes.flat, keys):
            for branch in ('P8', 'P10', 'P12'):
                selected = histories[branch]
                x = [row['iteration'] for row in selected]
                y = [row[key] for row in selected]
                if log:
                    # No invented log floor: exact zero measurements are explicitly omitted on log axes.
                    pairs = [(i, v) for i, v in zip(x, y) if v > 0]
                    ax.semilogy([i for i, _ in pairs], [v for _, v in pairs], color=colors[branch], label=branch, lw=1)
                else:
                    ax.plot(x, y, color=colors[branch], label=branch, lw=1)
                    ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
            ax.set(title=key, xlabel='Outer iteration, inclusive late interval', ylabel=key)
            ax.grid(alpha=.25)
            ax.legend(fontsize=8)
        fig.suptitle(title)
        fig.savefig(folder / filename, dpi=180)
        plt.close(fig)
    plot_grid(('R_initial', 'R_recursive', 'R_true', 'linear_iterations'), 'pressure_tolerance_residuals.png', 'Pressure solve: fixed PCG/DIC, relTol0; exact zeros omitted on log axes', True)
    plot_grid(('epsilon_phi_mean', 'epsilon_phi_max', 'P95_normalized', 'P99_normalized'), 'pressure_tolerance_continuity.png', 'Saved native flux continuity metrics, fixed definitions; positive values on log axes', True)
    plot_grid(MAJOR, 'pressure_tolerance_variation.png', 'Coupled solver variation: same200-iteration windows; U/T20-step normalized changes', True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    diffs = summary['qoi_response']
    x = np.arange(5)
    for offset, branch in [(-.18, 'P8'), (.18, 'P12')]:
        axes[0].bar(x + offset, [diffs[branch][key]['relative_difference'] for key in QOIS[:5]], width=.36, label=branch + ' vsP10', color=colors[branch])
    axes[0].set_xticks(x, QOIS[:5])
    axes[0].set(ylabel='Absolute relative QoI difference at18000')
    axes[0].set_yscale('linear')
    axes[0].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
    axes[0].legend()
    x = np.arange(2)
    for offset, branch in [(-.18, 'P8'), (.18, 'P12')]:
        axes[1].bar(x + offset, [diffs[branch][key]['absolute_difference'] for key in QOIS[5:]], width=.36, label=branch + ' vsP10', color=colors[branch])
    axes[1].set_xticks(x, QOIS[5:])
    axes[1].set(ylabel='Absolute nondimensional position difference')
    axes[1].legend()
    if all(diffs[b][key]['absolute_difference'] == 0 for b in ('P8', 'P12') for key in QOIS[5:]):
        axes[1].text(.5, .65, 'Both positions exactly unchanged at4097 sampling resolution', ha='center', transform=axes[1].transAxes)
    fig.suptitle('Final QoI sensitivity to pressure tolerance; no formal reference values')
    fig.savefig(folder / 'pressure_tolerance_qoi.png', dpi=180)
    plt.close(fig)


def main():
    p = load(OUT / 'pressure_tolerance_provenance.json')
    a = load(AMEND)
    complete = all(p['execution'][branch] == 'PASS' for branch in ORDER) and not p['STOP_reason']
    for branch in ORDER:
        guard(branch, p)
    residual_rows, continuity_rows, mapping_rows, variation_rows, checkpoints, manifest = [], [], [], [], [], []
    joined = {}
    stats = {}
    block_rows = []
    original_steady = {}
    for call in p['solver_calls']:
        branch = call['branch']
        archive = Path(call['archive'])
        manifest.append({key: call.get(key) for key in ('branch', 'tolerance', 'start', 'planned_end', 'last_iteration', 'pid', 'hostname', 'OpenFOAM_version', 'WM_OPTIONS', 'started_utc', 'finished_utc', 'exit_code', 'normal_exit', 'binary_sha256_before', 'binary_sha256_after', 'runtime_environment_sha256', 'archive')})
        if not (archive / 'steadyMonitor.csv').exists() or not (archive / 'continuityAudit.csv').exists():
            continue
        monitor = rows(archive / 'steadyMonitor.csv')
        audit = rows(archive / 'continuityAudit.csv')
        residual = equation_residuals(archive / 'log.solver')
        for row in residual:
            residual_rows.append({'branch': branch, 'actual_tolerance': LEVELS[branch], 'source': 'solver log printed precision', **row})
        for row in audit:
            residual_rows.append({'branch': branch, 'actual_tolerance': LEVELS[branch], 'source': 'native pressure audit17 digits', 'iteration': int(row['iteration']), 'equation': 'p_rgh', 'initial_residual': row['R_initial'], 'final_residual': row['R_recursive'], 'linear_iterations': int(row['linear_iterations']), 'converged': int(row['converged']), 'R_true': row['R_true'], 'Np': row['Np']})
            continuity_rows.append({'branch': branch, 'tolerance': LEVELS[branch], 'iteration': int(row['iteration']),
                **{key: row[key] for key in ('epsilon_phi_mean', 'epsilon_phi_max', 'P95_abs_div_phi', 'P99_abs_div_phi', 'signed_volume_mean_div_phi', 'net_boundary_flux', 'sum_abs_q', 'max_abs_q', 'Up', 'native_sum_local', 'native_global')},
                'P95_normalized': .01 / row['Up'] * row['P95_abs_div_phi'], 'P99_normalized': .01 / row['Up'] * row['P99_abs_div_phi'],
                'max_over_mean': row['epsilon_phi_max'] / row['epsilon_phi_mean'] if row['epsilon_phi_mean'] else None,
                'signed_global_epsilon': .01 / row['Up'] * row['signed_volume_mean_div_phi'],
                'cell_boundary_closure': row['signed_volume_mean_div_phi'] * (.01 ** 2 * .001) - row['net_boundary_flux'],
                'closure_note': 'Net cell residual minus net boundary flux, audit arithmetic; boundary absolute leakage additionally saved at checkpoints/final fields.'})
            mapping_rows.append({'branch': branch, 'tolerance': LEVELS[branch], 'iteration': int(row['iteration']),
                **{key: row[key] for key in ('R_recursive', 'R_true', 'Np', 'Kp', 'epsilon_phi_mean', 'ratio_recursive', 'ratio_true', 'abs_L1_norm_drift', 'true_nonreference_L1', 'true_reference_residual', 'physical_reference_residual', 'q_reference', 'mapping_defect_L1', 'mapping_defect_max')},
                'Kp_times_R_recursive': row['Kp'] * row['R_recursive'], 'Kp_times_R_true': row['Kp'] * row['R_true'],
                'physical_mapping_epsilon_proxy': .01 / row['Up'] / (.01 ** 2 * .001) * row['mapping_defect_L1']})
        if not monitor or max(row['iteration'] for row in monitor) < 15000:
            continue
        windows = monitor_windows(monitor, 12240)
        audit_index = {int(row['iteration']): row for row in audit}
        monitor_index = {int(row['iteration']): row for row in windows}
        eq_index = {}
        for row in residual:
            eq_index.setdefault(row['iteration'], {})[row['equation']] = row
        for row in windows:
            iteration = int(row['iteration'])
            variation_rows.append({'branch': branch, 'actual_tolerance': LEVELS[branch], **row})
        for iteration in CHECKPOINTS:
            if iteration == 12000:
                prior = next(row for row in load(OUT.parent / 'baseline_convergence_qualification.json')['checkpoints'] if row['iteration'] == 12000)
                checkpoints.append({'branch': branch, 'iteration': 12000, 'state_kind': 'COMMON_PARENT_NO_BRANCH_SOLVE', 'epsilon_phi_mean': prior['epsilon_phi_mean'], 'epsilon_phi_max': prior['epsilon_phi_max'], 'QoI_max_range': prior['qoi_max_variation'], 'U_window_max': prior['U_change'], 'T_window_max': prior['T_change'], 'heat_window_range': prior['heat_range'], **{key: value['value'] for key, value in prior['qois'].items()}})
            elif iteration in monitor_index:
                m, d = monitor_index[iteration], audit_index[iteration]
                checkpoints.append({'branch': branch, 'iteration': iteration, 'state_kind': 'BRANCH_NATIVE_MONITOR', **m, 'p_initial': d['R_initial'], 'p_final': d['R_recursive'], 'p_linear_iterations': d['linear_iterations'], 'R_true': d['R_true'], 'Np': d['Np'], 'Kp': d['Kp'],
                    **{equation + '_' + suffix: eq_index[iteration][equation][suffix + '_residual'] for equation in ('Ux', 'Uy', 'T') for suffix in ('initial', 'final') if equation in eq_index.get(iteration, {})}})
        late = []
        for row in windows:
            if 15000 <= row['iteration'] <= 18000:
                d = audit_index[int(row['iteration'])]
                late.append({**row, **d, 'P95_normalized': .01 / d['Up'] * d['P95_abs_div_phi'], 'P99_normalized': .01 / d['Up'] * d['P99_abs_div_phi']})
        joined[branch] = late
        metric_keys = (*PRIMARY, 'U_window_max', 'T_window_max', 'heat_imbalance', 'R_initial', 'R_true', 'Np', 'Kp', 'linear_iterations', 'P95_normalized', 'P99_normalized', 'ratio_recursive', 'ratio_true', 'physical_reference_residual')
        stats[branch] = {}
        for key in metric_keys:
            if not late:
                continue
            value = statistics([row[key] for row in late])
            medians = []
            for start in range(15000, 18000, 200):
                block = [row[key] for row in late if start < row['iteration'] <= start + 200]
                if len(block) == 10:
                    median = float(np.median(block))
                    medians.append(median)
                    block_rows.append({'branch': branch, 'metric': key, 'block_left_exclusive': start, 'block_right_inclusive': start + 200, 'samples': 10, 'median': median})
            value['block_median_envelope'] = {'min': min(medians), 'max': max(medians), 'blocks': len(medians), 'statistical_confidence_interval': False} if medians else None
            stats[branch][key] = value
        qualified = []
        all_original = []
        for m in monitor:
            i = int(m['iteration'])
            if m['qualified']:
                qualified.append(i)
                equations = eq_index.get(i, {})
                if all(name in equations and equations[name]['initial_residual'] <= 1e-8 for name in ('Ux', 'Uy', 'T')) and audit_index[i]['R_recursive'] <= 1.1 * LEVELS[branch]:
                    all_original.append(i)
        log = (archive / 'log.solver').read_text()
        original_steady[branch] = {'native_qualified_sample_count': len(qualified), 'all_original_criteria_sample_count': len(all_original), 'compiled_200_iteration_confirmation_marker': 'SENSITIVITY_STEADY_CONFIRMED' in log, 'baseline_accepted': False, 'capacity_audit_pressure_tolerance': 1e-10,
            'residual_rule': 'unchanged functional rule Ux/Uy/T initial<=1e-8; p final<=1.1*actual branch tolerance', 'qualified_iterations': qualified, 'all_original_qualified_iterations': all_original}
    save_csv(OUT / 'branch_manifest.csv', manifest)
    save_csv(OUT / 'pressure_residuals.csv', residual_rows)
    save_csv(OUT / 'continuity_metrics.csv', continuity_rows)
    save_csv(OUT / 'mapping_diagnostics.csv', mapping_rows)
    save_csv(OUT / 'variation_band.csv', variation_rows)
    save_csv(OUT / 'checkpoints.csv', checkpoints)
    save_csv(OUT / 'block_median_variability.csv', block_rows)
    field_rows, qoi_rows = [], []
    for branch in ('P8', 'P12'):
        if p['execution'][branch] != 'PASS' or p['execution']['P10'] != 'PASS':
            continue
        field_rows.extend(field_comparison(branch, 18000, a['normalization_scales']))
        c = load(OUT / 'P10_18000.json')['qoi']
        t = load(OUT / (branch + '_18000.json'))['qoi']
        for key in QOIS:
            qoi_rows.append({'branch': branch, 'reference': 'P10', 'iteration': 18000, 'qoi': key, 'P10_value': c[key], 'branch_value': t[key], 'branch_minus_P10': t[key] - c[key], 'absolute_difference': abs(t[key] - c[key]), 'relative_difference': abs(t[key] - c[key]) / abs(c[key]) if c[key] else None, 'primary_difference_type': 'relative' if key in QOIS[:5] else 'absolute_nondimensional'})
    save_csv(OUT / 'field_difference.csv', field_rows)
    save_csv(OUT / 'qoi_difference.csv', qoi_rows)
    response_ratios, monotonicities, resolved = {}, {}, {}
    prior_scatter = load(OUT / 'classification_reference.json')['historical_scatter']
    if complete:
        for branch in ORDER:
            if len(joined[branch]) != 151 or any(v['block_median_envelope']['blocks'] != 15 for v in stats[branch].values()):
                raise RuntimeError('STOP: missing151 late samples/15 blocks')
        for key in stats['P10']:
            control = stats['P10'][key]['median']
            response_ratios[key] = {branch + '_over_P10': stats[branch][key]['median'] / control if control else None for branch in ('P8', 'P12')}
            sequence = [stats[branch][key]['median'] for branch in ('P8', 'P10', 'P12')]
            monotonicities[key] = 'FLAT' if sequence[0] == sequence[1] == sequence[2] else ('MONOTONIC' if sequence[0] >= sequence[1] >= sequence[2] else 'NON_MONOTONIC')
            resolved[key] = {}
            c = stats['P10'][key]
            proxy = prior_scatter.get(key, {}).get('historical_resolution_proxy', 0.)
            for branch in ('P8', 'P12'):
                t = stats[branch][key]
                median_difference = t['median'] - c['median']
                decrease = t['block_median_envelope']['max'] < c['block_median_envelope']['min'] and -median_difference > proxy
                increase = t['block_median_envelope']['min'] > c['block_median_envelope']['max'] and median_difference > proxy
                resolved[key][branch] = {'classification': 'RESOLVED_DECREASE' if decrease else ('RESOLVED_INCREASE' if increase else 'NO_RESOLVED_CHANGE'), 'median_difference': median_difference, 'historical_resolution_proxy': proxy,
                    'block_envelopes_overlap': not (t['block_median_envelope']['max'] < c['block_median_envelope']['min'] or t['block_median_envelope']['min'] > c['block_median_envelope']['max']),
                    'difference_within_historical_proxy': abs(median_difference) <= proxy, 'certified_measurement_uncertainty_claimed': False}
        dec = lambda key: resolved[key]['P12']['classification'] == 'RESOLVED_DECREASE'
        inc = lambda key: resolved[key]['P12']['classification'] == 'RESOLVED_INCREASE'
        ordered = all(monotonicities[key] in ('MONOTONIC', 'FLAT') for key in PRIMARY)
        if dec('R_recursive') and dec('epsilon_phi_mean') and dec('epsilon_phi_max') and all(dec(key) for key in MAJOR) and ordered:
            effect = 'STRONG_EFFECT'
        elif dec('R_recursive') and (dec('epsilon_phi_mean') or dec('epsilon_phi_max')) and not all(dec(key) for key in MAJOR) and not any(inc(key) for key in MAJOR):
            effect = 'LIMITED_EFFECT'
        elif dec('R_recursive') and not any(dec(key) or inc(key) for key in ('epsilon_phi_mean', 'epsilon_phi_max', *MAJOR)):
            effect = 'NO_RESOLVED_EFFECT'
        else:
            effect = 'INCONCLUSIVE'
        weak_primary = dec('R_recursive') and (dec('epsilon_phi_mean') or dec('epsilon_phi_max')) and all(not dec(key) and stats['P12'][key]['median'] > 1e-8 and resolved[key]['P12']['block_envelopes_overlap'] and resolved[key]['P12']['difference_within_historical_proxy'] for key in MAJOR[:3])
        primary = 'NOT_SUPPORTED' if weak_primary else 'INCONCLUSIVE'
        monotonicity = 'NON_MONOTONIC' if any(monotonicities[key] == 'NON_MONOTONIC' for key in PRIMARY) else ('FLAT' if all(monotonicities[key] == 'FLAT' for key in PRIMARY) else 'MONOTONIC')
    else:
        effect = primary = monotonicity = 'INCONCLUSIVE'
    summary = {'schema': 'routeB-gateG-pressure-tolerance-diagnostic-v1', 'diagnostic_status': 'PASS' if complete else 'INCONCLUSIVE',
        'parent_case': {'Ra_test': 30000, 'grid': 20, 'source': 'zero', 'parent_iteration': 12000},
        'amendment_sha256': p['amendment_sha256'], 'amendment_md_sha256': p['amendment_md_sha256'], 'single_factor': 'p_rgh_absolute_tolerance',
        'branches': {b: {'tolerance': LEVELS[b], 'start': 12000, 'end': 18000, 'process_count': 1 if any(c['branch'] == b for c in p['solver_calls']) else 0, 'intermediate_restart': False} for b in ORDER},
        'unchanged_factors_verified': True, 'parent_equivalence': 'PASS', 'execution': p['execution'], 'P10_control_reproducibility': p['P10_control_reproducibility'],
        'late_interval': [15000, 18000], 'sample_interval': 20, 'window_iterations': 200, 'late_statistics': stats,
        'pressure_residual_response': {b: {k: value for k, value in metrics.items() if k in ('R_initial', 'R_recursive', 'R_true', 'linear_iterations')} for b, metrics in stats.items()},
        'continuity_response': {b: {k: value for k, value in metrics.items() if k in ('epsilon_phi_mean', 'epsilon_phi_max', 'P95_normalized', 'P99_normalized')} for b, metrics in stats.items()},
        'variation_response': {b: {k: value for k, value in metrics.items() if k in (*MAJOR, 'U_window_max', 'T_window_max', 'heat_imbalance')} for b, metrics in stats.items()},
        'median_response_ratios': response_ratios, 'resolved_change_assessment': resolved,
        'qoi_response': {b: {r['qoi']: r for r in qoi_rows if r['branch'] == b} for b in ('P8', 'P12')},
        'field_differences': {b: {r['field']: r for r in field_rows if r['branch'] == b} for b in ('P8', 'P12')},
        'mapping_diagnostics': {b: {k: value for k, value in metrics.items() if k in ('Np', 'Kp', 'ratio_recursive', 'ratio_true')} for b, metrics in stats.items()},
        'per_metric_monotonicity': monotonicities, 'tolerance_response_monotonicity': monotonicity, 'pressure_tolerance_effect': effect, 'pressure_precision_as_primary_band_cause': primary,
        'pressure_precision_as_QoI_band_contributor': 'INCONCLUSIVE' if effect != 'STRONG_EFFECT' else 'SUPPORTED_WITHIN_THIS_FINITE_EXPERIMENT',
        'original_steady_evaluation': original_steady, 'original_steady_criterion_changed': False, 'original_steady_criteria_changed': False,
        'U_tolerance_changed': False, 'T_tolerance_changed': False, 'relaxation_changed': False, 'monitor_capacity_parameter_changed': False,
        'arm1_restarted': False, 'arm2_executed': False, 'tau_mean': None, 'qoi_impact_quota_value': None, 'candidate_B_status': 'PROVISIONAL', 'current_formal_Ra1e3_gate_G': 'FAIL',
        'formal_benchmark_used': False, 'formal_benchmark_solver_executed': False, 'spec_change_executed': False, 'user_decision_required': True,
        'STOP_reason': p['STOP_reason'], 'interpretation': 'Coupled solver sensitivity to pressure linear-solve precision, not a pure-continuity perturbation. Empirical envelopes and prior C/R proxies are finite observed scatter, not rigorous uncertainty bounds or replicated causal inference.',
        'next_decision': 'Separately preregister a single-factor U or T linear tolerance experiment if the user chooses; change one at a time, before considering relaxation.'}
    dump(OUT / 'pressure_tolerance_summary.json', summary)
    if complete:
        build_figures(joined, residual_rows, summary)
    else:
        build_partial_figures(p)
    report(summary, p)
    for branch in ORDER:
        guard(branch, p)
    p.update({'analysis_completed_utc': now(), 'protected_files_unchanged': True, 'common_parent_unchanged': True,
        'final_git_status_short': git('status', '--short'), 'final_git_diff_stat': git('diff', '--stat'), 'final_git_diff_names': git('diff', '--name-only'), 'final_HEAD': git('rev-parse', 'HEAD'),
        'output_hashes_except_provenance': {str(f.relative_to(OUT)): sha(f) for f in sorted(OUT.rglob('*')) if f.is_file() and f.name != 'pressure_tolerance_provenance.json'}})
    dump(OUT / 'pressure_tolerance_provenance.json', p)
    print('ANALYZED', 'diagnostic', summary['diagnostic_status'], 'effect', effect, 'response', monotonicity, 'primary', primary, flush=True)
    print(json.dumps({'late_medians': {b: {k: {'median': stats[b][k]['median'], 'P95': stats[b][k]['P95']} for k in PRIMARY} for b in stats}, 'ratios': {k: response_ratios.get(k) for k in PRIMARY}, 'monotonicities': {k: monotonicities.get(k) for k in PRIMARY}}, indent=2))


def build_partial_figures(provenance):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder = OUT / 'figures'
    folder.mkdir(exist_ok=True)
    for name in ('residuals', 'continuity', 'variation', 'qoi'):
        fig, ax = plt.subplots(figsize=(9, 3))
        ax.axis('off')
        ax.text(.05, .5, 'INCOMPLETE CONTROLLED EXPERIMENT\n' + str(provenance['STOP_reason']) + '\nSee preserved partial CSV/log/provenance; no missing data reconstructed.', va='center', wrap=True)
        fig.savefig(folder / ('pressure_tolerance_' + name + '.png'), dpi=150)
        plt.close(fig)


def report(s, p):
    sections = []
    def add(title, content):
        sections.append('## ' + title + '\n\n' + content + '\n')
    def comparison(keys):
        data = [{'branch': b, 'metric': k, **s['late_statistics'][b][k]} for b in ('P8', 'P10', 'P12') if b in s['late_statistics'] for k in keys if k in s['late_statistics'][b]]
        return table(data, ['branch', 'metric', 'min', 'median', 'max', 'P95', 'samples'])
    add('1. Purpose', '20²/zero-source/Ra_test30000 のpressure linear-solve precisionだけをfactorとするcoupled solver sensitivity。PrimaryはP12 vsP10、P8は方向性診断。Diagnostic PASSは単一factor実験の成立を意味する。Scientific acceptanceやGate threshold、steady基準は変更していない。')
    add('2. Previous convergence and restart evidence', '元baselineは12000→30000でも1e-8条件未達。QoI/heatのlate variationはPLATEAU、U/TはINCONCLUSIVE。Restart experimentでは15000追加restartの軌道差を検出したが、continuous CにもO(1e-7) bandが残り、additional restart必要条件NOT_SUPPORTED、primary causeINCONCLUSIVE。今回は途中restartを行わない。これらは独立microcaseの既存evidenceのみ。')
    add('3. Amendment and hashes', f"Solver前に固定：JSON `{s['amendment_sha256']}`、MD `{s['amendment_md_sha256']}`。開始HEAD `{p['startup']['HEAD']}`。Startup/preflight/diff/scatter/source/method digestを保存し、各call前と分析後に確認。元v1/amendments001/002、以前の全成果物不変。git add/commit/push未実施。start/end status/diffをpressure_tolerance_provenance.jsonに保存。")
    add('4. Common 12000 parent', '既存qualificationと同じ完全12000 tree、U/T/p_rgh/phi/alphat/p/uniform/timeのSHA256一致。mesh/physical properties/fvSchemes等inputs/solver binaryも照合。元fieldは不変。全branchへ同一stateをcopy。\n\n' + table([{'field': k, 'sha256': v} for k, v in p['startup']['parent_tree_hashes'].items()], ['field', 'sha256']))
    add('5. Single-factor design', '順序P10(1e-10)→P8(1e-8)→P12(1e-12)、pressure relTol0。各branchは12000→18000単一process、serial DP、途中restartなし。U/T tolerance1e-12、relTol0、PCG/DIC/maxIter10000、relaxation、SIMPLE、scheme、mesh、physics、BC、source、source/binary、QoI/monitor/steady criteria不変。\n\nP12 preflight: installedv6 sourceは1e-12を拒否しないが、既存Case Cは1e-10まででfeasibility/floor未確定。norm drift/reference/physical mappingの不確かさを認識し、true residualを保存。1e-11へ代替しない。feasibility_preflight.json参照。')
    add('6. Input equivalence', 'Machine-checkでbranch間diffがsystem/fvSolution.solvers.p_rgh.tolerance tokenだけであることを確認し、unified diffと全hashをinput_diff_audit.jsonへ保存。Copied controlDictのstartFrom/latestTimeとendTime18000は全branch共通。auditPressureToleranceは1e-10に固定し、nativecontinuity stability criterionを変えていない。case_manifest.jsonはparent provenanceとしてbyte-identicalに保持し、branch実toleranceを別manifest/JSONに明記。\n\nSolver binary SHA256 `' + p['startup']['solver_binary']['sha256'] + '`。')
    execution = [{'branch': b, 'tolerance': LEVELS[b], 'status': s['execution'][b]} for b in ('P8', 'P10', 'P12')]
    add('7. Branch execution', table(execution, ['branch', 'tolerance', 'status']) + f"\n\nP10_CONTROL_REPRODUCIBILITY={s['P10_control_reproducibility']}。Existing continuous C18000の4 raw/payload SHAと比較し、PASSを次branchのgateに使用。各processのPID、開始終了timestamp、hostname、Foundationversion/DP、environment digest、load average、input/binary前後hash、連続iteration列を保存。STOP={s['STOP_reason']}。途中restart/retry/追加solver callなし。")
    add('8. Pressure residual response', comparison(('R_initial', 'R_recursive', 'R_true', 'linear_iterations')) + '\n\n全iterationのpressure/Ux/Uy/Uz/T initial/final/countをpressure_residuals.csvに保存。Pressure統計はnative audit17digitsを使い、logの表示precisionと区別。True residualはrecursive residualと同一とは仮定しない。\n\n![Pressure residual response](figures/pressure_tolerance_residuals.png)')
    add('9. Continuity response', comparison(('epsilon_phi_mean', 'epsilon_phi_max', 'P95_normalized', 'P99_normalized')) + '\n\nMax/mean、global signed、cell-boundary closure、Up、net boundary fluxを全iterationに保存。Boundary absolute leakageとfield continuityは各final JSONにも保存。epsilon thresholdをpressure toleranceと等置しない。\n\n![Continuity response](figures/pressure_tolerance_continuity.png)')
    add('10. QoI variation response', comparison(('QoI_max_range',)) + '\n\n全7QoI値と個別window range、position range、元nativequalified flagをvariation_band.csv、12000/13000/.../18000をcheckpoints.csvに保存。Late intervalは事前登録15000–18000 inclusive、20刻み151samples、window200/11samples。First12020 restart sentinelはlate intervalへ混入しない。')
    add('11. U/T field variation response', comparison(('U_change_20', 'T_change_20', 'U_window_max', 'T_window_max')) + '\n\nPrimaryはnormalized20-step field changeのlate中央値/P95。元steady criterionで使うwindow maxも別保存し、これらを同じ統計として混同しない。Uはnative currentUp、TはDeltaT1K。Full written fieldsを外部archiveし、write/purge設定を変えずprocessを継続。')
    add('12. Heat-balance response', comparison(('heat_imbalance', 'heat_window_range')) + '\n\n各branchの元steady評価：\n\n```json\n' + json.dumps({b: {k: v for k, v in d.items() if not k.endswith('iterations')} for b, d in s['original_steady_evaluation'].items()}, indent=2) + '\n```\n\nNative capacity parameter1e-10は不変。式residual条件は元functional rule、U/Tinitial<=1e-8・p final<=1.1*branch自身のtolerance。Baseline acceptedやArm再開には使わない。\n\n![Variation response](figures/pressure_tolerance_variation.png)')
    add('13. Pressure residual to epsilon mapping', comparison(('Np', 'Kp', 'ratio_recursive', 'ratio_true')) + '\n\nKp= L*Np/(Up*Vtotal)。epsilon/(Kp R_final)とepsilon/(Kp R_true)、reference residual、physical mapping L1/max、norm driftをmapping_diagnostics.csvへ保存。Solver reported normalized residualにはreference/recursion/physical mappingの差があり、単純な等式・普遍floorを保証しない。1e-12 solve≠epsilon<=1e-12。')
    ratio_rows = [{'metric': key, **value, 'monotonicity': s['per_metric_monotonicity'].get(key)} for key, value in s['median_response_ratios'].items() if key in (*PRIMARY, 'U_window_max', 'T_window_max', 'Kp')]
    add('14. Monotonicity', table(ratio_rows, ['metric', 'P12_over_P10', 'P8_over_P10', 'monotonicity']) + f"\n\nOverall descriptive median response={s['tolerance_response_monotonicity']}。Tighteningで増える量も削除しない。Raw median orderとresolved effectを分離：事前固定15 non-overlapping200-iteration block mediansのenvelope非重複、かつ既存C/R中央値差proxy超過を要件とする。Envelopeはconfidence intervalではなく、prior restart差はIID repeatabilityでもない。各量のmin/median/max/P95、block medians、重複判定を保存。Cutoffの後付け変更なし。\n\n```json\n" + json.dumps({key: value for key, value in s['resolved_change_assessment'].items() if key in PRIMARY}, indent=2) + '\n```')
    final_fields = [r for branch in ('P8', 'P12') for r in s['field_differences'][branch].values()]
    final_qois = [r for branch in ('P8', 'P12') for r in s['qoi_response'][branch].values()]
    add('15. Final field differences', table(final_fields, ['branch', 'field', 'max_abs_difference', 'RMS_difference', 'normalized_max_difference', 'normalized_RMS_difference']) + '\n\nInternal+physical boundary値の比較。U vector norm、scalar absolute difference。Scalesはcommon12000から事前固定（amendment002と同じ）、pressure gradientは別unitsで保存しRMSへ混ぜない。raw/payload hashとinternal-only/L1もCSV。\n\n' + table(final_qois, ['branch', 'qoi', 'P10_value', 'branch_value', 'absolute_difference', 'relative_difference']) + '\n\n値QoIはP10基準relative、position primaryはabsolute nondimensional。4097位置samplingの不変からpeak exact不変を主張しない。Formal paper値なし。\n\n![Final QoI difference](figures/pressure_tolerance_qoi.png)')
    add('16. Interpretation', f"Pressure tolerance effect={s['pressure_tolerance_effect']}。Pressure precision as primary band cause={s['pressure_precision_as_primary_band_cause']}。QoI/U/T band contributor={s['pressure_precision_as_QoI_band_contributor']}。圧力residual/continuity変化とouter variation変化を別に評価し、単なるendpoint差をband縮小とみなさない。非単調なmedianとscatterに対して未解像な差を保持。Original1e-8基準を緩めていない。各level一回のfinite6000反復なので、primary因果・寄与率への過大解釈を避ける。")
    add('17. What is NOT concluded', 'Pure continuity effect、true/exact solution、圧力tolerance=epsilon threshold、普遍的roundoff floor、scientific quota/tau/Gate threshold、新steady基準、他Ra/grid、formal Gate再評価、Candidate B正式採用、U/T precisionやrelaxationの原因確定は結論しない。P12の悪化/非単調性からroundoff/inner iterations/SIMPLE nonlinear sensitivityのどれかを断定しない。Formal結果/fields/logsは使用していない。')
    add('18. Next decision', 'このtaskで停止。次候補はUまたはT linear solver absolute toleranceを一つずつ変更する別のsingle-factor事前登録実験。どちらを先にするかは保存したU/T残差とvariationを踏まえて別taskで決める。Relaxation調査はその後。Arm1/Arm2再開なし、quota/tauUNRESOLVED、Candidate B PROVISIONAL、formalRa1e3GateGFAILは従来状態の宣言、SPEC_CHANGE_EXECUTED=NO、USER_DECISION_REQUIRED=YES。')
    (OUT / 'pressure_tolerance_report.md').write_text('# Pressure-Tolerance Single-Factor Diagnostic\n\n' + '\n'.join(sections))


if __name__ == '__main__':
    main()
