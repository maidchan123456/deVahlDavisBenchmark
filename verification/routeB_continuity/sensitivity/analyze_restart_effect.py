#!/usr/bin/env python3
"""Amendment002 comparisons; uses only new runs and preregistered microcase evidence."""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
from restart_effect_diagnostic import (
    AMEND, AUDIT, FIELDS, HERE, OUT, PARENT, PREVIOUS, ROOT, WORK,
    check_hashes, compare_fields, dump, git, guard, load, now, numeric_payload,
    save_csv, sha, tree_hashes,
)
from experiment import QOIS, extract


def read_csv(path):
    with Path(path).open() as stream:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def field_differences(iteration, scales):
    rows = []
    for field in FIELDS:
        _, cb, cm = numeric_payload(WORK / 'snapshots/C' / str(iteration) / field, field)
        _, rb, rm = numeric_payload(WORK / 'snapshots/R' / str(iteration) / field, field)
        if cm != rm:
            raise RuntimeError('STOP: comparison metadata mismatch')
        differences = [(name, r - c) for (name, c), (_, r) in zip(cb, rb)]
        values = np.concatenate([array for name, array in differences if not name.endswith('/gradient')], axis=0)
        internal = differences[0][1]
        magnitude = np.linalg.norm(values, axis=1) if field == 'U' else np.abs(values)
        internal_magnitude = np.linalg.norm(internal, axis=1) if field == 'U' else np.abs(internal)
        scale_key = {'U': 'U_Up_reference_m_s', 'T': 'T_DeltaT_K', 'p_rgh': 'p_rgh_parent_centered_internal_RMS_m2_s2', 'phi': 'phi_characteristic_face_flux_m3_s'}[field]
        scale = scales[scale_key]
        gradients = np.concatenate([array for name, array in differences if name.endswith('/gradient')]) if field == 'p_rgh' else np.empty(0)
        rows.append({'iteration': iteration, 'field': field, 'max_abs_difference': float(magnitude.max()),
            'RMS_difference': float(np.sqrt(np.mean(magnitude ** 2))), 'component_max_abs_difference': float(np.abs(values).max()),
            'normalized_max_difference': float(magnitude.max() / scale), 'normalized_RMS_difference': float(np.sqrt(np.mean(magnitude ** 2)) / scale),
            'normalization_scale': scale, 'scale_definition': scale_key,
            'units': {'U': 'm/s', 'T': 'K', 'p_rgh': 'm2/s2', 'phi': 'm3/s'}[field],
            'internal_max_abs_difference': float(internal_magnitude.max()), 'internal_RMS_difference': float(np.sqrt(np.mean(internal_magnitude ** 2))),
            'scalar_components_compared': int(values.size), 'value_locations_compared': int(len(values)),
            'L1_difference': float(np.sum(magnitude)) if field == 'phi' else None,
            'normalized_L1_difference': float(np.sum(magnitude) / scale) if field == 'phi' else None,
            'gradient_max_abs_difference': float(np.abs(gradients).max()) if gradients.size else None,
            'gradient_RMS_difference': float(np.sqrt(np.mean(gradients ** 2))) if gradients.size else None,
            'gradient_units': 'm/s2' if gradients.size else None})
    return rows


def difference_row(iteration, name, c, r, mode='absolute', reference=None):
    absolute = abs(r - c)
    relative = absolute / abs(c) if c else None
    normalized = relative if mode == 'relative' else absolute
    return {'iteration': iteration, 'quantity': name, 'C_value': c, 'R_value': r,
            'R_minus_C': r - c, 'absolute_difference': absolute, 'relative_difference': relative,
            'comparison_mode': mode, 'normalized_difference': normalized,
            'existing_reference_magnitude': reference,
            'difference_to_existing_reference_ratio': normalized / reference if reference else None}


def stats(values):
    values = np.asarray(values, dtype=float)
    return {'min': float(values.min()), 'median': float(np.median(values)), 'max': float(values.max()), 'P95': float(np.percentile(values, 95)), 'samples': len(values)}


def variation(branch, history):
    rows = []
    for index, current in enumerate(history):
        iteration = int(current['iteration'])
        if iteration < 15240:
            continue
        window = history[index - 10:index + 1]
        if len(window) != 11 or window[-1]['iteration'] - window[0]['iteration'] != 200:
            raise RuntimeError('STOP: incomplete matched window')
        row = {'branch': branch, 'iteration': iteration, 'window_start': int(window[0]['iteration']), 'window_samples': 11,
               'QoI_max_range': current['window_value_range'], 'position_max_range': current['window_position_range'],
               'U_window_max': max(x['U_change'] for x in window), 'T_window_max': max(x['T_change'] for x in window),
               'heat_window_range': current['window_heat_range'], 'epsilon_phi_mean': current['epsilon_phi_mean'], 'epsilon_phi_max': current['epsilon_phi_max'],
               'epsilon_phi_mean_window_range': float(np.ptp([x['epsilon_phi_mean'] for x in window])),
               'epsilon_phi_max_window_range': float(np.ptp([x['epsilon_phi_max'] for x in window])),
               'heat_imbalance': current['heat_imbalance'], 'native_qualified': int(current['qualified']),
               'U_change_20': current['U_change'], 'T_change_20': current['T_change']}
        for key in QOIS:
            raw_range = float(np.ptp([x[key] for x in window]))
            row[key + '_range'] = raw_range / max(abs(current[key]), 1.) if key in QOIS[:5] else raw_range
        # Verify computed window values against the unchanged compiled definitions.
        if not np.isclose(max(row[k + '_range'] for k in QOIS[:5]), row['QoI_max_range'], rtol=1e-12, atol=0):
            raise RuntimeError('STOP: window definition differs from native monitor')
        rows.append(row)
    if [row['iteration'] for row in rows] != list(range(15240, 18001, 20)):
        raise RuntimeError('STOP: missing matched-window samples')
    return rows


def markdown_table(rows, columns):
    def fmt(value):
        return f'{value:.8e}' if isinstance(value, float) else ('null' if value is None else str(value))
    return '\n'.join(['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |'] +
                     ['| ' + ' | '.join(fmt(row.get(key)) for key in columns) + ' |' for row in rows])


def plots(divergence, variation_rows, references):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures = OUT / 'figures'
    figures.mkdir(exist_ok=True)
    x = [row['iteration'] for row in divergence]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for ax, field in zip(axes.flat, FIELDS):
        ax.plot(x, [row[field + '_max_normalized'] for row in divergence], label='max difference', lw=1)
        ax.plot(x, [row[field + '_RMS_normalized'] for row in divergence], label='RMS difference', lw=1)
        ax.set(title=f'{field}: C vs R, fixed common-parent normalization', xlabel='Outer iteration', ylabel='Normalized field difference')
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('Additional restart at15000: actual archived internal + boundary fields')
    fig.savefig(figures / 'restart_field_divergence.png', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), constrained_layout=True)
    for key in QOIS[:5]:
        axes[0].plot(x, [row[key + '_difference_normalized'] for row in divergence], label=key, lw=1)
    for key in ('epsilon_phi_mean', 'epsilon_phi_max'):
        axes[1].plot(x, [row[key + '_difference_absolute'] for row in divergence], label=key, lw=1)
    axes[2].plot(x, [row['heat_imbalance_difference_absolute'] for row in divergence], label='heat imbalance', lw=1)
    for ax, ylabel in zip(axes, ('Value QoI relative difference', 'Absolute epsilon difference', 'Absolute heat imbalance difference')):
        ax.set(xlabel='Outer iteration', ylabel=ylabel)
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('Time-aligned unchanged native monitor; exact zeros retained')
    fig.savefig(figures / 'restart_qoi_divergence.png', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for ax, key, ref in zip(axes.flat, ('QoI_max_range', 'U_window_max', 'T_window_max', 'heat_window_range'), ('qoi', 'U', 'T', 'heat')):
        for branch in ('C', 'R'):
            selected = [row for row in variation_rows if row['branch'] == branch]
            ax.plot([row['iteration'] for row in selected], [row[key] for row in selected], label=branch, alpha=.8, lw=1)
        ax.axhline(references[ref], color='black', linestyle='--', label='Prior median magnitude (diagnostic)')
        ax.axhline(1e-8, color='gray', linestyle=':', label='Unchanged steady criterion')
        ax.set(title=key, xlabel='Outer iteration; full matched windows >=15240', ylabel='Window amplitude')
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.grid(alpha=.25)
        ax.legend(fontsize=7)
    fig.suptitle('Same200-iteration windows; restarted history warmup excluded')
    fig.savefig(figures / 'restart_variation_comparison.png', dpi=180)
    plt.close(fig)


def main():
    amendment = load(AMEND)
    provenance = load(OUT / 'restart_provenance.json')
    if provenance.get('STOP_reason') or len(provenance['solver_calls']) != 3 or not all(call['normal_exit'] for call in provenance['solver_calls']):
        raise RuntimeError('STOP: incomplete controlled experiment; keep partial evidence')
    for branch in ('C', 'R'):
        guard(WORK / ('branch_' + branch), 18000, provenance)
    if len({call['pid'] for call in provenance['solver_calls']}) != 3 or [(x['branch'], x['start'], x['end']) for x in provenance['solver_calls']] != [('R', 12000, 15000), ('C', 12000, 18000), ('R', 15000, 18000)]:
        raise RuntimeError('STOP: unexpected process design')
    references = amendment['existing_band_reference']['magnitudes']
    scales = amendment['normalization_scales']
    chistory = read_csv(WORK / 'segment_C_12000_18000/steadyMonitor.csv')
    rfirst = read_csv(WORK / 'segment_R_12000_15000/steadyMonitor.csv')
    rsecond = read_csv(WORK / 'segment_R_15000_18000/steadyMonitor.csv')
    histories = {'C': chistory, 'R': [rfirst[-1], *rsecond]}
    indexed = {branch: {int(row['iteration']): row for row in rows} for branch, rows in histories.items()}
    monitors = [{'branch': branch, **row, 'restart_sentinel': branch == 'R' and int(row['iteration']) == 15020,
                 'matched_full_window_eligible': row['iteration'] >= 15240} for branch, rows in histories.items() for row in rows if row['iteration'] >= 15000]
    save_csv(OUT / 'monitor_history.csv', monitors)
    hashes = [row for iteration in (15000, 18000) for row in compare_fields(iteration)]
    save_csv(OUT / 'field_hash_comparison.csv', hashes)
    primary_fields = [row for iteration in (15000, 18000) for row in field_differences(iteration, scales)]
    save_csv(OUT / 'field_difference.csv', primary_fields)
    records = {branch: extract(WORK / ('branch_' + branch), 18000) for branch in ('C', 'R')}
    for branch, record in records.items():
        dump(OUT / f'branch_{branch}_18000.json', record)
    qoi_rows = []
    continuity_rows = []
    for iteration in (15000, 18000):
        cq = records['C']['qoi'] if iteration == 18000 else indexed['C'][iteration]
        rq = records['R']['qoi'] if iteration == 18000 else indexed['R'][iteration]
        for key in QOIS:
            qoi_rows.append(difference_row(iteration, key, cq[key], rq[key], 'relative' if key in QOIS[:5] else 'position_absolute', references[key]))
        for key in ('epsilon_phi_mean', 'epsilon_phi_max', 'heat_imbalance'):
            c = records['C']['metrics'][key] if iteration == 18000 else indexed['C'][iteration][key]
            r = records['R']['metrics'][key] if iteration == 18000 else indexed['R'][iteration][key]
            row = difference_row(iteration, key, c, r, reference=references['heat'] if key == 'heat_imbalance' else references[key])
            row['reference_kind'] = 'heat_window_amplitude' if key == 'heat_imbalance' else 'prior_epsilon_level_not_variation_amplitude'
            continuity_rows.append(row)
    for key in ('net_boundary_flux', 'absolute_total_wall_flux', 'closure', 'sum_q', 'P95_normalized', 'P99_normalized', 'max_over_mean'):
        continuity_rows.append(difference_row(18000, key, records['C']['metrics'][key], records['R']['metrics'][key]))
    for key in ('R_recursive', 'R_true', 'Np', 'mapping_defect_L1', 'mapping_defect_max'):
        continuity_rows.append(difference_row(18000, 'audit_' + key, records['C']['audit'][key], records['R']['audit'][key]))
    save_csv(OUT / 'qoi_difference.csv', qoi_rows)
    save_csv(OUT / 'continuity_difference.csv', continuity_rows)
    divergence = []
    all_field_rows = []
    for iteration in range(15000, 18001, 20):
        fields = field_differences(iteration, scales)
        all_field_rows.extend(fields)
        row = {'iteration': iteration}
        for field in fields:
            row[field['field'] + '_max_normalized'] = field['normalized_max_difference']
            row[field['field'] + '_RMS_normalized'] = field['normalized_RMS_difference']
        for key in QOIS:
            c, r = indexed['C'][iteration][key], indexed['R'][iteration][key]
            absolute = abs(r - c)
            row[key + '_difference_absolute'] = absolute
            row[key + '_difference_normalized'] = absolute / abs(c) if key in QOIS[:5] and c else absolute
        row['QoI_max_relative_difference'] = max(row[key + '_difference_normalized'] for key in QOIS[:5])
        for key in ('epsilon_phi_mean', 'epsilon_phi_max', 'heat_imbalance'):
            row[key + '_difference_absolute'] = abs(indexed['R'][iteration][key] - indexed['C'][iteration][key])
        divergence.append(row)
    save_csv(OUT / 'field_divergence_history.csv', all_field_rows)
    save_csv(OUT / 'branch_divergence_history.csv', divergence)
    variations = variation('C', chistory) + variation('R', histories['R'])
    save_csv(OUT / 'branch_variation.csv', variations)
    variation_keys = [key for key in variations[0] if key not in ('branch', 'iteration', 'window_start', 'window_samples', 'native_qualified')]
    variation_summary = {branch: {key: stats([row[key] for row in variations if row['branch'] == branch]) for key in variation_keys} for branch in ('C', 'R')}
    amplitude_mapping = {'QoI_max_range': 'qoi', 'U_window_max': 'U', 'T_window_max': 'T', 'heat_window_range': 'heat'}
    for branch in ('C', 'R'):
        for key, ref in amplitude_mapping.items():
            variation_summary[branch][key]['median_to_prior_reference_ratio'] = variation_summary[branch][key]['median'] / references[ref]
    bands = {}
    final_fields = {row['field']: row for row in primary_fields if row['iteration'] == 18000}
    history_key_map = {'U': ('U_max_normalized', 'U'), 'T': ('T_max_normalized', 'T'), 'max_value_QoI': ('QoI_max_relative_difference', 'qoi'), 'heat_imbalance': ('heat_imbalance_difference_absolute', 'heat'), 'epsilon_phi_mean': ('epsilon_phi_mean_difference_absolute', 'epsilon_phi_mean'), 'epsilon_phi_max': ('epsilon_phi_max_difference_absolute', 'epsilon_phi_max')}
    for label, (key, ref) in history_key_map.items():
        values = [row[key] for row in divergence[1:]]
        endpoint = final_fields[label]['normalized_max_difference'] if label in ('U', 'T') else (max(row['normalized_difference'] for row in qoi_rows if row['iteration'] == 18000 and row['quantity'] in QOIS[:5]) if label == 'max_value_QoI' else next(row['absolute_difference'] for row in continuity_rows if row['iteration'] == 18000 and row['quantity'] == label))
        bands[label] = {'reference_magnitude': references[ref], 'endpoint_difference': endpoint, 'endpoint_ratio': endpoint / references[ref],
                        'trajectory_difference_stats': stats(values), 'trajectory_median_ratio': float(np.median(values)) / references[ref], 'trajectory_max_ratio': max(values) / references[ref],
                        'comparison_note': 'Cross-branch difference versus within-trajectory variation amplitude; diagnostic sizes, not the same statistic. U uses frozen12000 Up; native U band uses each sample own Up.' if label in ('U', 'T', 'max_value_QoI', 'heat_imbalance') else 'Difference divided by prior absolute epsilon level; not a prior epsilon variation amplitude.'}
    for row in qoi_rows:
        if row['iteration'] == 18000:
            bands[row['quantity']] = {'reference_magnitude': row['existing_reference_magnitude'], 'endpoint_difference': row['normalized_difference'], 'endpoint_ratio': row['difference_to_existing_reference_ratio'], 'reference_zero': row['existing_reference_magnitude'] == 0}
    for field in ('p_rgh', 'phi'):
        bands[field] = {'reference_magnitude': None, 'endpoint_ratio': None, 'reason': 'No saved like-for-like previous pressure/flux variation amplitude; characteristic normalization reported instead.'}
    cmedian = variation_summary['C']['QoI_max_range']['median']
    decimal_order = lambda value: int(math.floor(math.log10(value) + .5)) if value > 0 else None
    retains = cmedian > 0 and decimal_order(cmedian) == decimal_order(references['qoi'])
    detected = not all(row['payload_identical'] for row in hashes if row['iteration'] == 18000)
    if not detected and any(row['max_abs_difference'] != 0 for row in primary_fields if row['iteration'] == 18000):
        raise RuntimeError('STOP: hash/difference inconsistency')
    trajectory = {}
    for label, (key, _) in history_key_map.items():
        early = [row[key] for row in divergence if 15020 <= row['iteration'] <= 15200]
        late = [row[key] for row in divergence if 17800 <= row['iteration'] <= 18000]
        sequence = [row[key] for row in divergence[1:]]
        changes = np.diff(sequence)
        kind = 'ZERO' if all(value == 0 for value in sequence) else ('MONOTONE_DECAY' if np.all(changes <= 0) else ('MONOTONE_AMPLIFICATION' if np.all(changes >= 0) else 'PERSISTENT_IRREGULAR_RESPONSE'))
        trajectory[label] = {'description': kind, 'first_nonzero_iteration': next((row['iteration'] for row in divergence if row[key] != 0), None), 'first_after_restart': sequence[0], 'last': sequence[-1], 'maximum': max(sequence), 'exact_zero_samples': sum(row[key] == 0 for row in divergence), 'early_median': float(np.median(early)), 'late_median': float(np.median(late)), 'late_to_early_median_ratio': float(np.median(late) / np.median(early)) if np.median(early) else None, 'increases': int(np.sum(changes > 0)), 'decreases': int(np.sum(changes < 0)), 'limitation': 'Non-monotone response label does not certify an asymptotic band or establish a primary cause.'}
    manifest_rows = [{key: call[key] for key in ('branch', 'start', 'end', 'pid', 'started_utc', 'finished_utc', 'normal_exit', 'exit_code', 'last_iteration', 'before_binary_sha256', 'after_binary_sha256', 'archive')} for call in provenance['solver_calls']]
    save_csv(OUT / 'branch_manifest.csv', manifest_rows)
    summary = {'schema': 'routeB-gateG-restart-effect-diagnostic-v1', 'diagnostic_status': 'PASS',
        'parent_case': {'Ra_test': 30000, 'grid': 20, 'source': 'zero', 'parent_iteration': 12000},
        'amendment_sha256': provenance['amendment_sha256'], 'amendment_md_sha256': provenance['amendment_md_sha256'],
        'numerical_settings_changed': False, 'original_steady_criteria_changed': False,
        'branch_C': {'kind': 'continuous', 'start': 12000, 'end': 18000, 'intermediate_restart': False, 'pid': provenance['solver_calls'][1]['pid']},
        'branch_R': {'kind': 'restart', 'start': 12000, 'restart_iteration': 15000, 'end': 18000, 'pids': [provenance['solver_calls'][0]['pid'], provenance['solver_calls'][2]['pid']]},
        'parent_equivalence': 'PASS', 'iteration_15000_equivalence': provenance['pre_restart_equivalence'],
        'iteration_18000': {field: {**final_fields[field], **next(row for row in hashes if row['iteration'] == 18000 and row['field'] == field)} for field in FIELDS},
        'normalization_scales': scales,
        'qoi_differences': {row['quantity']: row for row in qoi_rows if row['iteration'] == 18000},
        'continuity_differences': {row['quantity']: row for row in continuity_rows if row['iteration'] == 18000},
        'restart_effect_detected': detected, 'restart_effect_class': 'DETECTED' if detected else 'NOT_DETECTED',
        'restart_effect_support': 'SUPPORTED' if detected else 'NOT_SUPPORTED',
        'restart_difference_relative_to_band': bands, 'branch_variation_summary': variation_summary, 'trajectory_summary': trajectory,
        'continuous_branch_retains_variation_band': retains, 'continuous_band_order_evidence': {'C_median_QoI_range': cmedian, 'prior_reference': references['qoi'], 'ratio': cmedian / references['qoi'], 'C_nearest_decimal_order': decimal_order(cmedian), 'prior_nearest_decimal_order': decimal_order(references['qoi']), 'descriptive_not_acceptance': True},
        'restart_as_necessary_condition_for_band': 'NOT_SUPPORTED' if retains else 'INCONCLUSIVE', 'restart_as_primary_cause': 'INCONCLUSIVE',
        'native_qualified_samples': {branch: sum(row['qualified'] != 0 for row in history if row['iteration'] >= 15000) for branch, history in histories.items()},
        'original_steady_qualification': 'NOT_ESTABLISHED', 'pressure_tolerance_changed': False, 'U_tolerance_changed': False, 'T_tolerance_changed': False, 'relaxation_changed': False,
        'arm1_restarted': False, 'arm2_executed': False, 'qoi_impact_quota_value': None, 'tau_mean': None, 'candidate_B_status': 'PROVISIONAL', 'current_formal_Ra1e3_gate_G': 'FAIL',
        'formal_benchmark_used': False, 'formal_benchmark_results_used': False, 'formal_benchmark_solver_executed': False, 'spec_change_executed': False, 'user_decision_required': True,
        'solver_call_count': 3, 'full_field_comparison_iterations': list(range(15000, 18001, 20)), 'matched_variation_interval': [15240, 18000], 'matched_variation_windows_per_branch': 139,
        'protected_files_unchanged': True, 'common_parent_fields_unchanged': True, 'STOP_reason': None,
        'next_decision': 'A separately preregistered single-factor tolerance study may be designed next; no tolerance/relaxation factors executed in this task.'}
    dump(OUT / 'restart_effect_summary.json', summary)
    plots(divergence, variations, references)
    build_report(summary, provenance, primary_fields, qoi_rows, continuity_rows, manifest_rows)
    for branch in ('C', 'R'):
        guard(WORK / ('branch_' + branch), 18000, provenance)
    provenance.update({'analysis_complete_utc': now(), 'protected_files_unchanged': True, 'original_parent_unchanged': True,
                       'final_git_status_short': git('status', '--short'), 'final_git_diff_stat': git('diff', '--stat'),
                       'final_git_diff_names': git('diff', '--name-only'), 'final_HEAD': git('rev-parse', 'HEAD'),
                       'output_hashes_except_provenance': {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'restart_provenance.json'}})
    dump(OUT / 'restart_provenance.json', provenance)
    print('ANALYZED', summary['restart_effect_class'], 'continuous band', retains, 'primary cause INCONCLUSIVE', flush=True)
    print(json.dumps({'fields': final_fields, 'band_ratios': {k: v.get('endpoint_ratio') for k, v in bands.items()}, 'variation_medians': {b: {k: variation_summary[b][k]['median'] for k in amplitude_mapping} for b in ('C', 'R')}}, indent=2))


def build_report(s, p, fields, qois, continuity, calls):
    sections = []
    def add(title, body):
        sections.append('## ' + title + '\n\n' + body + '\n')
    add('1. Purpose', 'Ra_test=30000,20×20×1,zero source の additional restart at iteration15000 effect のみを分離した。両枝は12000で共通にrestartする。推定対象は15000で追加される restart / write-read / reinitialization bundle であり、restart一般ではない。Diagnostic PASS は対照実験の成立を意味し、steady qualificationやGate GのPASSではない。')
    previous = load(PREVIOUS)
    prior_rows = [{'iteration': c['iteration'], 'QoI_range': c['qoi_max_variation'], 'U_change': c['U_change'], 'T_change': c['T_change'], 'heat_range': c['heat_range'], 'epsilon_mean': c['epsilon_phi_mean']} for c in previous['checkpoints']]
    add('2. Previous convergence-band evidence', '12000–30000のmicrocase qualificationはFAIL、元1e-8条件未達。QoI/heat PLATEAU、U/Tおよびoverall INCONCLUSIVE。formal benchmarkは参照していない。\n\n' + markdown_table(prior_rows, ['iteration', 'QoI_range', 'U_change', 'T_change', 'heat_range', 'epsilon_mean']))
    add('3. Amendment and hashes', f"実行前に固定し、各call前/分析後に確認。JSON `{s['amendment_sha256']}`、MD `{s['amendment_md_sha256']}`。v1/001および既存results不変。driver/analysis/startup digestと正確な既存band参照値はamendment002 JSONに記録。開始HEAD `{p['startup']['HEAD']}`。開始/終了git statusとdiff statはrestart_provenance.jsonに保存。git add/commit/pushは実行していない。")
    parent_rows = [{'file': k, 'sha256': v} for k, v in p['startup']['common_parent_tree_hashes'].items()]
    add('4. Common 12000 parent', '前回保存された全12000 treeのdigestと一致し、両枝開始stateも完全一致。alphat/p/uniform/timeを含む。mesh/physics/source/system/case manifestも確認。元caseは不変。\n\n' + markdown_table(parent_rows, ['file', 'sha256']))
    add('5. Branch C continuous design', '12000→18000は単一process。15000でprocessを終了していない。標準writeInterval20/purgeWrite14を維持し、stdoutのwrite完了後ExecutionTimeを受けてfieldを外部ignored archiveへcopy。15000–18000全151時点の実fieldを保存し、field reconstructionは行っていない。')
    add('6. Branch R restart design', '12000→15000正常終了。その全保存stateからfresh processで15000→18000。第一segmentのmonitor/audit/sourceCells/logは第二processによる上書き前に外部保存。\n\n' + markdown_table(calls, ['branch', 'start', 'end', 'pid', 'normal_exit', 'exit_code']))
    add('7. Numerical settings equivalence', 'p1e-10、U/T1e-12、relTol0、relaxation、fvSchemes/fvSolution、physics、BC、zero source、mesh、solver source/binary、monitor/QoI/steady criteriaは不変。変更は新copyのstartFrom latestTime/endTimeのみ。各callの前後input/controlDict/binary digestを記録。binary SHA256 `' + sha(AUDIT) + '`。stock equivalenceを再実行していない。')
    pre = [row for row in p['pre_restart_comparisons']]
    add('8. 15000 pre-restart equivalence', s['iteration_15000_equivalence'] + '。C15000 writeをprocess継続中にR15000と比較してguardを通過。数値payloadにはinternal/physical boundary値とpressure gradient、empty patch型を含む。zeroGradientの暗黙値は共通mesh owner値から抽出しoriginを記録。\n\n' + markdown_table(pre, ['field', 'raw_identical', 'payload_identical', 'values_exactly_equal']) + '\n\n完全digestはfield_hash_comparison.csv、canonicalizationは実行前amendment参照。raw hash不一致の後付け解釈は行っていない。')
    add('9. Restart execution', 'R15000正常終了、C15000同等性、Rの15000全restart stateおよび入力不変を確認してから、許可されたendTimeのみ18000に更新し第二processを開始。ちょうど3 solver calls。STOPなし。新case/runのみを使用し、formal data/caseには触れていない。')
    add('10. 18000 field comparison', 'Uはvector norm max/RMS、scalarはabsolute max/RMS。internal+physical boundary値を集計し、internal-only/component maxもCSVに保存。p_rgh gradientは別unitsで比較しfield値RMSに混ぜない。全scaleを共通12000から固定：\n\n' + '\n'.join(f'- {key} = {value}' for key, value in s['normalization_scales'].items()) + '\n\n' + markdown_table([r for r in fields if r['iteration'] == 18000], ['field', 'max_abs_difference', 'RMS_difference', 'normalized_max_difference', 'normalized_RMS_difference', 'L1_difference', 'gradient_max_abs_difference']) + '\n\nwhole-fileとnumerical-payload SHA256はfield_hash_comparison.csv。pressure gaugeは変更していない。phi L1はface differencesの総和でありcell divergence normではない。')
    add('11. QoI comparison', '18000は既存extract関数によるASCII field値。value QoIはabs(R-C)/abs(C)、positionはabsolute nondimensional。4097 samplingの位置不変はsub-grid exact peak不変を証明しない。\n\n' + markdown_table([r for r in qois if r['iteration'] == 18000], ['quantity', 'C_value', 'R_value', 'absolute_difference', 'normalized_difference', 'difference_to_existing_reference_ratio']) + '\n\n中間historyは同じnative monitor値。field extraction/native-memoryとの差はbranch_C/R_18000.jsonのserialization_differenceに保存し、restart-induced差と混同しない。')
    add('12. Continuity comparison', markdown_table([r for r in continuity if r['iteration'] == 18000 and r['quantity'] in ('epsilon_phi_mean', 'epsilon_phi_max', 'heat_imbalance', 'net_boundary_flux', 'absolute_total_wall_flux', 'closure')], ['quantity', 'C_value', 'R_value', 'absolute_difference', 'relative_difference', 'difference_to_existing_reference_ratio']) + '\n\npressure audit/true residual/Np/mapping、P95/P99、max/meanもCSV/branch final JSONに保存。epsilon参照比は前回absolute levelに対する比で、variation amplitude比とは異なる。新しい保存基準・quotaは導入しない。')
    trajectory_rows = [{'quantity': key, **value} for key, value in s['trajectory_summary'].items()]
    add('13. Branch divergence history', '15000と、その後15020:20:18000の151 actual-field/monitor時点を比較。U/T max/RMS、7QoI、epsilon/heat差をCSVへ保存。early15020–15200/late17800–18000の集計：\n\n' + markdown_table(trajectory_rows, ['quantity', 'description', 'first_nonzero_iteration', 'first_after_restart', 'last', 'early_median', 'late_median', 'late_to_early_median_ratio', 'increases', 'decreases']) + '\n\n非単調な残存responseはasymptotic constant-bandやprimary-causeの証明ではない。\n\n![Actual field divergence](figures/restart_field_divergence.png)\n\n![QoI and continuity divergence](figures/restart_qoi_divergence.png)')
    for number, branch, title in [(14, 'C', 'Continuous-branch variation'), (15, 'R', 'Restarted-branch variation')]:
        rows = [{'quantity': key, **value} for key, value in s['branch_variation_summary'][branch].items() if key in ('QoI_max_range', 'U_window_max', 'T_window_max', 'heat_window_range', 'epsilon_phi_mean', 'epsilon_phi_mean_window_range')]
        add(f'{number}. {title}', '同一11 samples/200 iterations、matched15240–18000の139 windows。R15020のU/T初期sentinelと短いhistoryをwindow比較から除外し、Cも同じ期間へ制限。field changeは元native20-step norm/current Up、temperatureはDeltaT1K。\n\n' + markdown_table(rows, ['quantity', 'min', 'median', 'max', 'P95', 'median_to_prior_reference_ratio']) + f"\n\nNative qualified samples (>=15000): {s['native_qualified_samples'][branch]}。Original steady qualificationは確立していない。")
    ratio_rows = [{'quantity': key, 'reference': value.get('reference_magnitude'), 'endpoint_ratio': value.get('endpoint_ratio'), 'trajectory_median_ratio': value.get('trajectory_median_ratio'), 'trajectory_max_ratio': value.get('trajectory_max_ratio')} for key, value in s['restart_difference_relative_to_band'].items()]
    add('16. Restart effect relative to observed band', '前回late18000/24000/30000の既存amplitude medianの中央値を事前固定。Cross-branch差/within-trajectory variation幅は比較可能な診断scaleだが同じ統計量ではない。positionの既存bandゼロはnull、pressure/phiの既存like-for-like band未保存もnull；後付けfloor/閾値はない。\n\n' + markdown_table(ratio_rows, ['quantity', 'reference', 'endpoint_ratio', 'trajectory_median_ratio', 'trajectory_max_ratio']) + '\n\n![Matched branch variation](figures/restart_variation_comparison.png)')
    order = s['continuous_band_order_evidence']
    add('17. Interpretation', f"Restart effect class={s['restart_effect_class']}。15000までは同一で18000は数値差があるかを判定した。Continuous branch median QoI window range={order['C_median_QoI_range']:.8e}、前回reference={order['prior_reference']:.8e}、ratio={order['ratio']:.6g}。事前登録されたnearest-decimal-orderの記述分類でband残存={s['continuous_branch_retains_variation_band']}。これはacceptance thresholdではない。追加15000 restartをbandの必要条件とする仮説={s['restart_as_necessary_condition_for_band']}（この期間/ケースのみ）。Primary cause=INCONCLUSIVE。Bundleは軌道に寄与しうるが、既存bandの原因寄与率はこの差/reference比から求められない。")
    add('18. What is NOT concluded', 'Serialization単独/reinitialization単独への分解、restart一般の全影響、12000共通restartの影響、primary cause、linear precisionの因果、exact/truth solution、他Ra/grid、scientific acceptance、quota/tau、新steady criterion、Candidate B正式化、formal Gate再評価は結論しない。共通12000 restartから6000 iterationsのfinite trajectoryであり、long-term independent distributionsを比較していない。Candidate B PROVISIONAL、formal Ra1e3 Gate G FAILは既存状態の宣言。formal結果は使用していない。')
    add('19. Next decision', 'このrestart診断で停止。次は別taskで、single-factor solver-tolerance studyを事前設計するかをユーザーが決める。今回p/U/T tolerance・relaxationは変更せず、Arm1/Arm2を再開していない。Quota/tau UNRESOLVED、SPEC_CHANGE_EXECUTED=NO、USER_DECISION_REQUIRED=YES。')
    (OUT / 'restart_effect_report.md').write_text('# Restart-Effect Controlled Diagnostic\n\n' + '\n'.join(sections))


if __name__ == '__main__':
    main()
