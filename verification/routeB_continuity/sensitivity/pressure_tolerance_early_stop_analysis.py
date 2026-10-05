#!/usr/bin/env python3
"""Post-STOP bookkeeping only; no solver calls or changes to amendment003 inference.

P12's original compiled monitor ended normally at12440. Preserve its early evidence,
explicitly mark unavailable preregistered late data, and plot actual observed runs.
This supplemental script was created after that event and is recorded as such.
"""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
from pressure_tolerance_diagnostic import (
    AMEND, CHECKPOINTS, FIELDS, LEVELS, ORDER, OUT, WORK, QOIS,
    dump, git, guard, load, monitor_windows, now, rows, save_csv, sha,
)
from analyze_pressure_tolerance import equation_residuals, field_comparison, statistics, table
from experiment import extract


def read_csv(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def update_report(summary, early, pairwise):
    path = OUT / 'pressure_tolerance_report.md'
    text = path.read_text()
    prefix = ('**STOP — P12は元native steady monitorにより12440で正常自動終了した。** '
              '指定した12000→18000連続区間は未完了なのでexecution protocol上P12=FAIL、linear solver infeasible/fatalではない。'
              '15000–18000のP12 late dataと18000 field/QoIは未取得。禁止されたmonitor変更・restart・代替toleranceは実行していない。'
              '主effect/monotonicity/primary-cause判定は登録どおりINCONCLUSIVE。\n\n')
    text = text.replace('# Pressure-Tolerance Single-Factor Diagnostic\n\n', '# Pressure-Tolerance Single-Factor Diagnostic\n\n' + prefix, 1)
    execution_note = ('\n\nP12のexit code=0、EndおよびSENSITIVITY_STEADY_CONFIRMEDを確認。440 pressure solvesすべてconverged=true、'
                      '14–29 linear iterations、maxIter到達・stall・NaN/Inf/fatalなし。元native criteriaは12240から12440の11 samplesでqualifyし、'
                      '全11 samplesでUx/Uy/Tinitial<=1e-8、p final<=1.1*actual1e-12も満たした。200反復の追加confirmationが成立。'
                      'P12はbaseline acceptedとはしておらず、Arm1/Arm2も再開しない。Native自動停止を上書きすることは今回許可されていない。\n\n'
                      'Post-STOP supplemental analysisは未登録late区間を代用しないbookkeeping。別source digestと作成時点をprovenanceへ記録。')
    text = text.replace('\n## 8. Pressure residual response', execution_note + '\n\n## 8. Pressure residual response')
    final = early['checkpoint_native']
    metric_rows = [{'metric': key, 'P12_at_12440': final.get(key)} for key in ('R_initial', 'R_recursive', 'R_true', 'linear_iterations', 'epsilon_phi_mean', 'epsilon_phi_max', 'QoI_max_range', 'U_change_20', 'T_change_20', 'U_window_max', 'T_window_max', 'heat_window_range', 'heat_imbalance')]
    text = text.replace('\n## 10. QoI variation response', '\n\nP12の以下は早期停止checkpointの単一時点（late統計ではない）：\n\n' + table(metric_rows, ['metric', 'P12_at_12440']) + '\n\n## 10. QoI variation response')
    ratio_rows = [{'metric': key, **value} for key, value in summary['median_response_ratios'].items() if key in ('R_recursive', 'epsilon_phi_mean', 'epsilon_phi_max', 'QoI_max_range', 'U_change_20', 'T_change_20', 'heat_window_range')]
    text = text.replace('\n## 15. Final field differences', '\n\n利用可能なP8/P10 late median ratios（P12/P10は欠測）：\n\n' + table(ratio_rows, ['metric', 'P8_over_P10', 'P12_over_P10']) + '\n\nP8は各主要bandとepsilonをP10より大きくした。この2水準の結果は解析可能だが、P12欠測を補って3水準response/effect分類には使わない。\n\n## 15. Final field differences')
    text = text.replace('\n## 16. Interpretation', '\n\nP12の18000 field/QoI差はNOT_OBSERVED。P8/P10のみの実測比較を掲載。P12_at_12440.jsonとearly_stop_diagnostics.jsonは正常終了時のstateを保持し、P12_vs_P10_12440.csvは同時点のsupplemental比較（主endpointの代替ではない）。\n\n## 16. Interpretation')
    text = text.replace('各level一回のfinite6000反復なので、', 'P8/P10は6000反復、P12は440反復で正常自動終了。Prespecified late dataが欠けるので、')
    start = text.index('## 18. Next decision')
    text = text[:start] + '''## 18. Next decision

このtaskで停止。まず別taskで、元steady criteriaを保ちながら固定長診断を続ける停止制御を許容するか、confirmation時終了を含む比較設計に改めるかを決める必要がある。Amendment003や元monitor/binaryをこのtaskで変更せず、P12をrestart/再実行していない。早期終了を理由にp tolerance1e-11等の代替値も試していない。

Pressure studyを解決した後のfactor候補はUまたはT absolute tolerance単独（同時変更せず、relaxation固定）。今回のP12早期縮小はpressure contributionの有望な補足証拠だが、登録したlate比較のSTRONG_EFFECT/primary causeへ昇格させない。Arm1/Arm2再開なし、quota/tauUNRESOLVED、Candidate B PROVISIONAL、formalRa1e3GateGFAILは従来状態の宣言、SPEC_CHANGE_EXECUTED=NO、USER_DECISION_REQUIRED=YES。
'''
    path.write_text(text)


def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figroot = OUT / 'figures'
    colors = {'P8': '#d97706', 'P10': '#2563eb', 'P12': '#15803d'}
    audit = {b: rows(WORK / ('execution_' + b) / 'continuityAudit.csv') for b in ORDER}
    for data in audit.values():
        for row in data:
            row['P95_normalized'] = .01 / row['Up'] * row['P95_abs_div_phi']
            row['P99_normalized'] = .01 / row['Up'] * row['P99_abs_div_phi']
    monitors = {b: monitor_windows(rows(WORK / ('execution_' + b) / 'steadyMonitor.csv'), 12240) for b in ORDER}
    for filename, keys, data in [
        ('pressure_tolerance_residuals.png', ('R_initial', 'R_recursive', 'R_true', 'linear_iterations'), audit),
        ('pressure_tolerance_continuity.png', ('epsilon_phi_mean', 'epsilon_phi_max', 'P95_normalized', 'P99_normalized'), audit),
        ('pressure_tolerance_variation.png', ('QoI_max_range', 'U_change_20', 'T_change_20', 'heat_window_range'), monitors),
    ]:
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
        for ax, key in zip(axes.flat, keys):
            for branch in ('P8', 'P10', 'P12'):
                values = [(row['iteration'], row[key]) for row in data[branch] if row[key] > 0]
                ax.semilogy([x for x, _ in values], [v for _, v in values], color=colors[branch], lw=.8, alpha=.85, label=branch + (' (ended12440)' if branch == 'P12' else ''))
            ax.axvline(12440, color='gray', linestyle=':', lw=1)
            ax.set(title=key, xlabel='Actual observed outer iteration', ylabel=key)
            ax.grid(alpha=.2)
            ax.legend(fontsize=8, loc='best')
        fig.suptitle('Incomplete fixed-length diagnostic: P12 native steady stop at12440; no extrapolated tail')
        fig.savefig(figroot / filename, dpi=180)
        plt.close(fig)
    s = load(OUT / 'pressure_tolerance_summary.json')
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    axes[0].bar(QOIS[:5], [s['qoi_response']['P8'][k]['relative_difference'] for k in QOIS[:5]], color=colors['P8'], label='P8 vsP10, actual18000')
    axes[1].bar(QOIS[5:], [s['qoi_response']['P8'][k]['absolute_difference'] for k in QOIS[5:]], color=colors['P8'], label='P8 vsP10, actual18000')
    axes[0].set(ylabel='Relative value QoI difference')
    axes[1].set(ylabel='Absolute nondimensional position difference')
    for ax in axes:
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend()
        ax.grid(axis='y', alpha=.2)
    if all(s['qoi_response']['P8'][k]['absolute_difference'] == 0 for k in QOIS[5:]):
        axes[1].text(.5, .6, 'Positions exactly unchanged at4097 sampling resolution', ha='center', transform=axes[1].transAxes)
    fig.suptitle('18000 endpoint: P12 NOT OBSERVED (normal native steady exit at12440)')
    fig.savefig(figroot / 'pressure_tolerance_qoi.png', dpi=180)
    plt.close(fig)


def main():
    s = load(OUT / 'pressure_tolerance_summary.json')
    p = load(OUT / 'pressure_tolerance_provenance.json')
    a = load(AMEND)
    assert s['execution'] == {'P10': 'PASS', 'P8': 'PASS', 'P12': 'FAIL'}
    assert s['pressure_tolerance_effect'] == 'INCONCLUSIVE'
    for branch in ORDER:
        guard(branch, p)
        shutil.copy2(WORK / ('execution_' + branch) / 'steadyMonitor.csv', OUT / (branch + '_monitor_history.csv'))
    archive = WORK / 'execution_P12'
    log = (archive / 'log.solver').read_text()
    assert '\nEnd\n' in log and 'SENSITIVITY_STEADY_CONFIRMED' in log
    audit = rows(archive / 'continuityAudit.csv')
    assert len(audit) == 440 and all(row['converged'] == 1 and row['R_recursive'] < 1e-12 and row['linear_iterations'] < 10000 for row in audit)
    assert all(np.isfinite(value) for row in audit for value in row.values())
    eq = equation_residuals(archive / 'log.solver')
    eq_index = {}
    for row in eq:
        eq_index.setdefault(row['iteration'], {})[row['equation']] = row
    monitor = rows(archive / 'steadyMonitor.csv')
    qualified = [int(row['iteration']) for row in monitor if row['qualified']]
    assert qualified == list(range(12240, 12441, 20))
    audit_index = {int(row['iteration']): row for row in audit}
    all_original = [i for i in qualified if all(eq_index[i][name]['initial_residual'] <= 1e-8 for name in ('Ux', 'Uy', 'T')) and audit_index[i]['R_recursive'] <= 1.1e-12]
    assert all_original == qualified
    windows = monitor_windows(monitor, 12240)
    checkpoint = {**windows[-1], **audit[-1]}
    record = extract(WORK / 'P12', 12440)
    record.update({'diagnostic_branch': 'P12', 'actual_pressure_tolerance': 1e-12, 'parent_manifest_retained_for_provenance': True, 'primary_late_interval_available': False, 'native_steady_confirmed': True, 'normal_process_exit': True, 'baseline_accepted': False})
    dump(OUT / 'P12_at_12440.json', record)
    early = {'schema': 'routeB-pressure-normal-early-stop-evidence-v1', 'created_after_STOP': True,
        'supplemental_not_replacement_for_preregistered_late_comparison': True, 'branch': 'P12', 'actual_iteration': 12440,
        'process_normal_exit': True, 'process_exit_code': 0, 'planned_target_reached': False, 'P12_EXECUTION_protocol_status': 'FAIL',
        'linear_feasibility_observed': True, 'pressure_solves': len(audit), 'all_pressure_solves_converged': True, 'stall_or_breakdown': False,
        'pressure_linear_iterations_range': [min(x['linear_iterations'] for x in audit), max(x['linear_iterations'] for x in audit)],
        'native_qualified_iterations': qualified, 'all_original_criteria_qualified_iterations': all_original,
        'original_steady_confirmation_completed': True, 'confirmation_start': 12240, 'confirmation_end': 12440, 'confirmation_iterations': 200,
        'checkpoint_native': checkpoint, 'final_equation_residuals': eq_index[12440],
        'prespecified_late_interval': [15000, 18000], 'late_data_status': 'NOT_OBSERVED', 'P12_18000_fields': 'NOT_OBSERVED',
        'solver_rerun_or_restart': False, 'monitor_or_criterion_changed': False, 'alternative_tolerance_tried': False,
        'frozen_classification': 'INCONCLUSIVE', 'reason': 'Original immutable monitor ends process on200-iteration steady confirmation; overriding that stop behavior is outside current authorization.'}
    dump(OUT / 'early_stop_diagnostics.json', early)
    for key, values in s['late_statistics']['P10'].items():
        denominator = values['median']
        s['median_response_ratios'][key] = {'P8_over_P10': s['late_statistics']['P8'][key]['median'] / denominator if denominator else None, 'P12_over_P10': None, 'P12_missing_reason': 'No P12 data in prespecified15000–18000 interval'}
        c, t = values, s['late_statistics']['P8'][key]
        proxy = load(OUT / 'classification_reference.json')['historical_scatter'].get(key, {}).get('historical_resolution_proxy', 0.)
        difference = t['median'] - c['median']
        increase = t['block_median_envelope']['min'] > c['block_median_envelope']['max'] and difference > proxy
        decrease = t['block_median_envelope']['max'] < c['block_median_envelope']['min'] and -difference > proxy
        s['resolved_change_assessment'][key] = {'P8': {'classification': 'RESOLVED_INCREASE' if increase else ('RESOLVED_DECREASE' if decrease else 'NO_RESOLVED_CHANGE'), 'median_difference': difference, 'historical_resolution_proxy': proxy, 'registered_rule_used_without_change': True}, 'P12': {'classification': 'NOT_OBSERVED', 'reason': 'Prespecified late interval unavailable'}}
        s['per_metric_monotonicity'][key] = 'INCONCLUSIVE'
    missing_fields = {field: {'branch': 'P12', 'reference': 'P10', 'iteration': 18000, 'field': field, 'status': 'NOT_OBSERVED', 'max_abs_difference': None, 'RMS_difference': None, 'normalized_max_difference': None, 'normalized_RMS_difference': None, 'reason': 'Normal native steady stop at12440'} for field in FIELDS}
    missing_qois = {key: {'branch': 'P12', 'reference': 'P10', 'iteration': 18000, 'qoi': key, 'status': 'NOT_OBSERVED', 'P10_value': load(OUT / 'P10_18000.json')['qoi'][key], 'branch_value': None, 'absolute_difference': None, 'relative_difference': None, 'reason': 'Normal native steady stop at12440'} for key in QOIS}
    s['field_differences']['P12'] = missing_fields
    s['qoi_response']['P12'] = missing_qois
    field_data = read_csv(OUT / 'field_difference.csv')
    field_data.extend(missing_fields.values())
    save_csv(OUT / 'field_difference.csv', field_data)
    qoi_data = read_csv(OUT / 'qoi_difference.csv')
    qoi_data.extend(missing_qois.values())
    save_csv(OUT / 'qoi_difference.csv', qoi_data)
    pairwise = field_comparison('P12', 12440, a['normalization_scales'])
    save_csv(OUT / 'P12_vs_P10_12440.csv', [{**row, 'analysis_role': 'POST_STOP_SUPPLEMENTAL_SAME_ITERATION_NOT_PRIMARY_ENDPOINT'} for row in pairwise])
    values = read_csv(OUT / 'variation_band.csv')
    for row in values:
        row['primary_late_interval_member'] = float(row['iteration']) >= 15000
    values.extend({'branch': 'P12', 'actual_tolerance': 1e-12, **row, 'primary_late_interval_member': False, 'analysis_role': 'EARLY_NATIVE_CONFIRMATION_OUTSIDE_PRIMARY_LATE_INTERVAL'} for row in windows)
    save_csv(OUT / 'variation_band.csv', values)
    checkpoints = read_csv(OUT / 'checkpoints.csv')
    parent = next(row for row in checkpoints if row['branch'] == 'P10' and float(row['iteration']) == 12000)
    checkpoints.append({**parent, 'branch': 'P12'})
    checkpoints.extend({'branch': 'P12', 'iteration': iteration, 'state_kind': 'NOT_OBSERVED_NORMAL_NATIVE_EARLY_EXIT', 'reason': 'P12 ended12440'} for iteration in CHECKPOINTS if iteration > 12000)
    checkpoints.append({'branch': 'P12', 'iteration': 12440, 'state_kind': 'POST_STOP_EARLY_CHECKPOINT_NOT_PRIMARY_ENDPOINT', **checkpoint})
    save_csv(OUT / 'checkpoints.csv', checkpoints)
    qualification = {'native_qualified_sample_count': 11, 'all_original_criteria_sample_count': 11, 'compiled_200_iteration_confirmation_marker': True, 'original_steady_criterion_reached': True, 'original_confirmation_completed': True, 'confirmation_interval': [12240, 12440], 'baseline_accepted': False, 'capacity_audit_pressure_tolerance': 1e-10, 'qualified_iterations': qualified, 'all_original_qualified_iterations': all_original}
    s['original_steady_evaluation']['P12'] = qualification
    s['P12_normal_early_exit'] = True
    s['P12_linear_feasibility'] = 'FEASIBLE_OBSERVED_OVER_440_ITERATIONS'
    s['P12_original_steady_confirmation'] = 'COMPLETED_AT_12440'
    s['P12_primary_late_interval'] = 'NOT_OBSERVED'
    s['execution_status_note'] = 'P12 FAIL denotes incomplete requested12000–18000 interval, despite normal native steady termination and feasible pressure solves.'
    s['early_stop_evidence_file'] = 'early_stop_diagnostics.json'
    for key in ('pressure_residual_response', 'continuity_response', 'variation_response'):
        s[key]['P12'] = {'late_status': 'NOT_OBSERVED', 'early_checkpoint_iteration': 12440, 'early_checkpoint': checkpoint, 'not_used_as_late_statistic': True}
    s['next_decision'] = 'Resolve fixed-length execution versus native steady-confirmation termination in a separately authorized design, preserving steady criteria. Do not jump to U/T/relaxation factor changes or resume sensitivity arms here.'
    dump(OUT / 'pressure_tolerance_summary.json', s)
    update_report(s, early, pairwise)
    plots()
    for branch in ORDER:
        guard(branch, p)
    p['supplemental_post_STOP_analysis'] = {'script_path': str(Path(__file__)), 'sha256': sha(Path(__file__)), 'completed_utc': now(), 'created_after_P12_stop': True, 'purpose': 'Missing-data labeling, observed native criterion/feasibility evidence, actual-data plots and P8/P10 ratios using existing registered definitions; no primary rule/interval replacement or solver calls.'}
    p.update({'final_git_status_short': git('status', '--short'), 'final_git_diff_stat': git('diff', '--stat'), 'final_git_diff_names': git('diff', '--name-only'),
        'output_hashes_except_provenance': {str(f.relative_to(OUT)): sha(f) for f in sorted(OUT.rglob('*')) if f.is_file() and f.name != 'pressure_tolerance_provenance.json'}})
    dump(OUT / 'pressure_tolerance_provenance.json', p)
    print('P12 normal native confirmation preserved; late comparison remains INCONCLUSIVE; no new solver calls')
    print('P8/P10 median ratios', {key: s['median_response_ratios'][key]['P8_over_P10'] for key in ('R_recursive', 'epsilon_phi_mean', 'epsilon_phi_max', 'QoI_max_range', 'U_change_20', 'T_change_20', 'heat_window_range')})


if __name__ == '__main__':
    main()
