#!/usr/bin/env python3
"""Amendment003: three serial, continuous microcase processes, one changed factor."""
import csv
import difflib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'results/routeB/gateG_sensitivity_experiment/pressure_tolerance_diagnostic'
WORK = HERE / 'runs/pressure_tolerance_003'
PARENT = HERE / 'runs/baseline_n20'
RESTART = OUT.parent / 'restart_effect_diagnostic'
AMEND = HERE / 'preregistration_amendment_003.json'
LEVELS = {'P10': 1e-10, 'P8': 1e-8, 'P12': 1e-12}
ORDER = tuple(LEVELS)
FIELDS = ('U', 'T', 'p_rgh', 'phi')
CHECKPOINTS = (12000, 13000, 14000, 15000, 16000, 17000, 18000)
OF = Path('/home/mirai/OpenFOAM/OpenFOAM-6')
sys.path.insert(0, str(HERE))
from experiment import AUDIT, ENV, QOIS, extract, parser
from restart_effect_diagnostic import numeric_payload


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load(path):
    return json.loads(Path(path).read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def tree_hashes(folder):
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def inputs(case):
    return {str(p.relative_to(case)): sha(p) for sub in ('constant', 'system') for p in sorted((case / sub).rglob('*')) if p.is_file()}


def rows(path):
    with Path(path).open() as stream:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]


def save_csv(path, data):
    if not data:
        return
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(k for row in data for k in row)))
        writer.writeheader()
        writer.writerows(data)


def fvsolution(tol):
    original = (PARENT / 'system/fvSolution').read_text()
    block = parser._block(original, 'p_rgh')
    changed, count = re.subn(r'\btolerance\s+[^;]+;', f'tolerance {tol:.0e};', block)
    if count != 1:
        raise RuntimeError('STOP: ambiguous pressure tolerance')
    return original.replace(block, changed, 1)


def control():
    return (PARENT / 'system/controlDict').read_text().replace('startFrom startTime;', 'startFrom latestTime;').replace('endTime 12000;', 'endTime 18000;')


def monitor_windows(history, start=15000):
    output = []
    for index, row in enumerate(history):
        if row['iteration'] < start:
            continue
        window = history[index - 10:index + 1]
        if len(window) != 11 or window[-1]['iteration'] - window[0]['iteration'] != 200:
            raise RuntimeError('STOP: incomplete window')
        value = dict(row)
        value.update({'QoI_max_range': row['window_value_range'], 'U_change_20': row['U_change'], 'T_change_20': row['T_change'],
                      'U_window_max': max(x['U_change'] for x in window), 'T_window_max': max(x['T_change'] for x in window),
                      'heat_window_range': row['window_heat_range'], 'window_start': int(window[0]['iteration']), 'window_samples': 11})
        for key in QOIS:
            amplitude = float(np.ptp([x[key] for x in window]))
            value[key + '_range'] = amplitude / max(1., abs(row[key])) if key in QOIS[:5] else amplitude
        output.append(value)
    return output


def input_audit():
    result = {'schema': 'routeB-pressure-input-diff-audit-v1', 'sole_branch_input_difference': 'system/fvSolution solvers.p_rgh.tolerance', 'branches': {}, 'diffs_vs_P10': {}, 'PASS': True}
    reference = WORK / 'P10'
    ref_inputs = inputs(reference)
    ref_text = (reference / 'system/fvSolution').read_text()
    for branch, tol in LEVELS.items():
        case = WORK / branch
        actual = inputs(case)
        expected = dict(ref_inputs)
        expected['system/fvSolution'] = hashlib.sha256(fvsolution(tol).encode()).hexdigest()
        if actual != expected or (case / 'system/fvSolution').read_text() != fvsolution(tol):
            raise RuntimeError('STOP: unexpected numerical input difference')
        if tree_hashes(case / '12000') != tree_hashes(PARENT / '12000'):
            raise RuntimeError('STOP: common parent mismatch')
        result['branches'][branch] = {'tolerance': tol, 'input_hashes': actual, 'parent_hashes': tree_hashes(case / '12000'),
                                     'changed_input_files_vs_P10': [k for k in actual if actual[k] != ref_inputs[k]]}
        result['diffs_vs_P10'][branch] = ''.join(difflib.unified_diff(ref_text.splitlines(True), (case / 'system/fvSolution').read_text().splitlines(True), fromfile='P10/system/fvSolution', tofile=branch + '/system/fvSolution'))
        if sha(case / 'case_manifest.json') != sha(PARENT / 'case_manifest.json'):
            raise RuntimeError('STOP: manifest changed (retained baseline manifest is parent provenance; actual tolerance is fvSolution)')
    return result


def prepare():
    if OUT.exists() or WORK.exists() or AMEND.exists() or AMEND.with_suffix('.md').exists():
        raise RuntimeError('Refuse to overwrite diagnostic or amendment')
    head, status = git('rev-parse', 'HEAD'), git('status', '--short')
    if head != '3095039ec002b288a0c4000f9ccc788761cb0048':
        raise RuntimeError('STOP: unexpected HEAD; inspect only subsequent changes')
    previous = load(OUT.parent / 'baseline_convergence_qualification.json')
    old = previous['startup_provenance']
    for name, digest in old['original_case_input_hashes'].items():
        if sha(PARENT / name) != digest:
            raise RuntimeError('STOP: changed original input')
    if tree_hashes(PARENT / '12000') != old['12000_restart_tree_hashes'] or sha(AUDIT) != old['binary']['sha256']:
        raise RuntimeError('STOP: parent/binary mismatch')
    reg = load(HERE / 'experiment_preregistration_v1.json')
    for name, digest in reg['source_hashes'].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('STOP: original solver source mismatch')
    manifest = load(PARENT / 'case_manifest.json')
    if not (manifest['n'] == 20 and manifest['Ra_test'] == 30000 and manifest['eta_nom'] == 0 and manifest['relTol'] == 0):
        raise RuntimeError('STOP: parent outside scope')
    if np.any(parser.read_scalar(PARENT / 'constant/continuitySource', 400)):
        raise RuntimeError('STOP: nonzero source')
    protected = {str(p.relative_to(ROOT)): sha(p) for p in OUT.parent.rglob('*') if p.is_file()}
    for pattern in ('experiment_preregistration_v1.*', 'preregistration_amendment_00[12].*'):
        protected.update({str(p.relative_to(ROOT)): sha(p) for p in HERE.glob(pattern)})
    protected.update({name: sha(ROOT / name) for name in reg['source_hashes']})
    for p in (HERE / 'experiment.py', HERE / 'analyze.py', HERE / 'steadyMonitor.H', HERE / 'restart_effect_diagnostic.py', HERE / 'analyze_restart_effect.py', HERE.parent / 'common.py', ROOT / 'Scripts/routeB/foam_fields.py', ROOT / 'Scripts/routeB/analyze_case.py'):
        protected[str(p.relative_to(ROOT))] = sha(p)
    pcg = OF / 'src/OpenFOAM/matrices/lduMatrix/solvers/PCG/PCG.C'
    controls = OF / 'src/OpenFOAM/matrices/lduMatrix/lduMatrix/lduMatrixSolver.C'
    performance = OF / 'src/OpenFOAM/matrices/LduMatrix/LduMatrix/SolverPerformance.C'
    if not all(p.exists() for p in (pcg, controls, performance)):
        raise RuntimeError('STOP: installed-v6 preflight sources unavailable')
    casec_path = ROOT / 'results/routeB/caseC_continuity_verification/verification_summary.json'
    casec = load(casec_path)
    prior_audit = rows(HERE / 'runs/restart_effect_002/segment_C_12000_18000/continuityAudit.csv')
    preflight = {'schema': 'routeB-pressure-feasibility-preflight-v1', 'P12': 'READY_TO_ATTEMPT_NOT_PREVIOUSLY_VERIFIED',
        'source_hashes': {str(p): sha(p) for p in (pcg, controls, performance)},
        'source_evidence': ['readControls reads scalar tolerance directly; no 1e-12 clamp/rejection', 'PCG compares normalized recursive finalResidual against absolute tolerance, relTol0 disables relative stopping', 'PCG checks singularity and maxIter10000 remains unchanged; these do not certify attainable accuracy', 'solver normFactor is state dependent, epsilon is not the solver tolerance'],
        'CaseC_evidence_file': str(casec_path), 'CaseC_evidence_sha256': sha(casec_path),
        'CaseC_limit': casec['numerical_floor']['basis'], 'prior_serialization_epsilon_error_max': casec['serialization']['microcase_epsilon_mean_error_absolute_max'],
        'prior_n20_continuous_evidence': {k: {'min': min(x[k] for x in prior_audit), 'max': max(x[k] for x in prior_audit)} for k in ('R_recursive', 'R_true', 'Np', 'Kp', 'abs_L1_norm_drift', 'mapping_defect_L1', 'linear_iterations')},
        'interpretation': 'Source permits P12, but no direct prior1e-12 PCG test or certified floor. Norm drift/mapping discrepancies make true residual audit essential. Attempt only preregistered P12; no1e-11 substitute, no additional preflight solver call.',
        'NOT_FEASIBLE_rule': 'P12 pressure solve not converged, maxIter10000 exhaustion, singular/breakdown or stall; preserve and stop without restart or alternate tolerance.'}
    OUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    dump(OUT / 'feasibility_preflight.json', preflight)
    for branch, tol in LEVELS.items():
        case = WORK / branch
        case.mkdir()
        for folder in ('constant', 'system', '12000'):
            shutil.copytree(PARENT / folder, case / folder)
        shutil.copy2(PARENT / 'case_manifest.json', case / 'case_manifest.json')
        (case / 'system/controlDict').write_text(control())
        (case / 'system/fvSolution').write_text(fvsolution(tol))
        shutil.copytree(case / '12000', WORK / 'snapshots' / branch / '12000')
    diff = input_audit()
    dump(OUT / 'input_diff_audit.json', diff)
    variation_keys = ('QoI_max_range', 'U_change_20', 'T_change_20', 'U_window_max', 'T_window_max', 'heat_window_range', 'epsilon_phi_mean', 'epsilon_phi_max')
    # Observed between-trajectory median shifts, fixed before examining new P8/P12 data.
    scatter = {}
    with (RESTART / 'branch_variation.csv').open() as stream:
        oldvariation = list(csv.DictReader(stream))
    for key in variation_keys:
        c = float(np.median([float(x[key]) for x in oldvariation if x['branch'] == 'C']))
        r = float(np.median([float(x[key]) for x in oldvariation if x['branch'] == 'R']))
        scatter[key] = {'C_median': c, 'R_median': r, 'historical_resolution_proxy': abs(c - r)}
    scatter['R_recursive'] = {'historical_resolution_proxy': 0., 'note': 'Native audit quantity, no certified residual-vector roundoff uncertainty claimed; true residual separately retained.'}
    dump(OUT / 'classification_reference.json', {'historical_scatter': scatter, 'source': str(RESTART / 'branch_variation.csv'), 'source_sha256': sha(RESTART / 'branch_variation.csv'), 'scope': 'Empirical prior restart-trajectory median shifts, not IID repeatability or confidence intervals.'})
    startup = {'created_utc': now(), 'HEAD': head, 'git_status_short': status, 'hostname': socket.gethostname(),
        'OpenFOAM_version': ENV.get('WM_PROJECT_VERSION'), 'WM_OPTIONS': ENV.get('WM_OPTIONS'),
        'solver_binary': {'path': str(AUDIT), 'sha256': sha(AUDIT)}, 'source_hashes': reg['source_hashes'], 'parent_path': str(PARENT),
        'parent_tree_hashes': old['12000_restart_tree_hashes'], 'parent_input_hashes': old['original_case_input_hashes'],
        'parent_manifest_sha256': sha(PARENT / 'case_manifest.json'), 'protected_hashes': protected,
        'branch_input_hashes': {b: inputs(WORK / b) for b in ORDER}, 'P10_expected_C18000': {f: {key: value for key, value in load(RESTART / 'restart_effect_summary.json')['iteration_18000'][f].items() if key.startswith('C_') and 'sha256' in key} for f in FIELDS}}
    if startup['OpenFOAM_version'] != '6' or 'DP' not in startup['WM_OPTIONS']:
        raise RuntimeError('STOP: not Foundationv6 double precision')
    dump(OUT / 'startup_provenance.json', startup)
    amendment = {'schema': 'routeB-gateG-pressure-tolerance-preregistration-amendment-003', 'created_utc': now(),
        'research_questions': ['Does tightening p_rgh absolute tolerance reduce epsilon_phi_mean/max?', 'Do QoI/U/T/heat variation bands systematically decrease?', 'Is pressure precision a meaningful, negligible or unresolved contributor to current band?', 'Does preserved tight-branch band weaken the primary-cause hypothesis?'],
        'single_factor': 'p_rgh_absolute_tolerance', 'common_parent': {'Ra_test': 30000, 'grid': [20, 20, 1], 'source': 'zero', 'iteration': 12000, 'tree_hashes': startup['parent_tree_hashes']},
        'levels': LEVELS, 'relTol': 0, 'execution_order': list(ORDER), 'run_interval': [12000, 18000], 'one_process_per_branch': True, 'parallel': False, 'additional_restart_allowed': False,
        'unchanged': ['U/T tolerances1e-12 and relTol0', 'p relTol0', 'PCG/DIC and maxIter10000', 'relaxation', 'SIMPLE structure', 'discretization/fvSchemes', 'mesh', 'physics/properties', 'BC', 'initial complete12000 state', 'zero source', 'solver source/binary', 'native monitor definitions', 'QoI definitions', 'original steady criteria', 'ASCII precision16/writeInterval20/purgeWrite14', 'controlDict auditPressureTolerance1e-10'],
        'monitor_capacity_parameter': 'Keep auditPressureTolerance1e-10 fixed; it supplies original native epsilon stability criteria, not actual PCG tolerance. Actual PCG tolerance is fvSolution.p_rgh.tolerance. Do not retune native criteria per branch.',
        'copy_control_changes': ['startFrom latestTime', 'endTime18000'], 'branch_input_difference': 'Only fvSolution.solvers.p_rgh.tolerance token; parent case_manifest retained byte-identical for provenance, actual branch settings recorded separately.',
        'feasibility_preflight_sha256': sha(OUT / 'feasibility_preflight.json'), 'input_diff_audit_sha256': sha(OUT / 'input_diff_audit.json'),
        'classification_reference_sha256': sha(OUT / 'classification_reference.json'), 'startup_provenance_sha256': sha(OUT / 'startup_provenance.json'),
        'driver_sha256': sha(Path(__file__)), 'analysis_sha256': sha(HERE / 'analyze_pressure_tolerance.py'), 'solver_binary_sha256': sha(AUDIT),
        'checkpoint_iterations': list(CHECKPOINTS), 'field_capture': 'Preserve each completed write from12020 to18000 outside working case; no change to write/purge settings, no field reconstruction. Minimum12000/15000/18000 ensured.',
        'late_statistics': {'interval_inclusive': [15000, 18000], 'sample_interval': 20, 'sample_count': 151, 'window_iterations': 200, 'window_samples': 11,
            'warmup': 'Only first restart at12000; first U/T sentinel12020 and incomplete windows until12240 excluded; late15000 onward has complete history.',
            'metrics': list(variation_keys) + ['R_recursive', 'R_true', 'Np', 'Kp', 'P95_normalized', 'P99_normalized', 'heat_imbalance'], 'statistics': ['min', 'median', 'max', 'P95'],
            'empirical_uncertainty': '15 disjoint200-iteration blocks (15000,15200],...,(17800,18000],10 samples/block. Min/max of block medians = empirical variability envelope, not a confidence interval; the inclusive15000 sample belongs to overall151 statistics only.'},
        'primary': 'P12 vsP10; P8 directional diagnostic',
        'resolved_change_rule': 'Effective block-median envelopes must not overlap, and absolute overall median change must exceed the fixed matching historical_resolution_proxy from prior C/R median shift. Where no historical proxy exists, use zero and explicitly no certified uncertainty bound. No arbitrary factor2 or percentage cutoff.',
        'classification': {'STRONG_EFFECT': 'Resolved P12 reductions in recursive pressure residual, epsilon mean and max, plus all four QoI_max_range/U_change_20/T_change_20/heat_window_range; all corresponding medians non-increasing P8→P10→P12.',
            'LIMITED_EFFECT': 'Resolved pressure-residual decrease and at least one epsilon mean/max decrease, but not all four major bands resolve decreases; remaining bands are nonzero and no major-band resolved increase. Non-monotone medians within overlapping scatter may coexist with LIMITED_EFFECT; disclose this rather than treat them as resolved causal reversals.',
            'NO_RESOLVED_EFFECT': 'Pressure residual resolves a decrease, but neither epsilon nor any major band resolves a decrease/increase; finite experiment has insufficient resolution, not proof of zero effect.',
            'INCONCLUSIVE': 'Incomplete/nonfeasible branches, unresolved pressure change, resolved contrary responses, or any case not meeting the above rules. Preserve all nonmonotone/worsened data.',
            'monotonicity': 'Per metric descriptive median order: FLAT if exactly equal, MONOTONIC if P8>=P10>=P12, otherwise NON_MONOTONIC (including tightening-induced increase). Overall seven primary metrics: any NON_MONOTONIC ->NON_MONOTONIC; all FLAT ->FLAT; otherwise MONOTONIC; missing ->INCONCLUSIVE. Separate empirical resolved-change assessment.',
            'primary_cause': 'NOT_SUPPORTED only if epsilon improves with resolved pressure response, none of QoI/U20/T20 decreases resolves, and all three retain median above unchanged1e-8 with overlapping block envelopes and median shifts within prior scatter proxy. STRONG_EFFECT supports pressure precision as a contributor but primary cause remains INCONCLUSIVE without replicated/longer evidence. All other cases INCONCLUSIVE.',
            'contributor': 'Do not call coupled-solver response pure continuity. A resolved pressure/epsilon effect alone does not establish meaningful or negligible contribution to QoI/U/T band.'},
        'ratios': 'Report P12/P10 and P8/P10 median ratios for every metric; zero denominator ->null, no floor',
        'normalization_scales': load(HERE / 'preregistration_amendment_002.json')['normalization_scales'],
        'field_canonicalization': 'Reuse immutable amendment002 Float64/internal+physical patch values/pressure gradients/empty patch canonicalization; U max/RMS vector norm, scalars max/RMS, gradients separate. Frozen common12000 Up/T/p/phi scales.',
        'qoi_differences': 'At18000 existing extract, values abs(branch-P10)/abs(P10) or null for zero reference, positions absolute nondimensional; no formal paper values',
        'mapping': 'Audit true and recursive pressure residuals, Np,Kp, epsilon/(Kp*R), reference/mapping defects and physical-flux evidence. Report deviations; solver tolerance is never epsilon threshold.',
        'steady_evaluation': 'Native criteria unchanged with capacity parameter1e-10; postprocess original U/T initial<=1e-8 and pressure final<=1.1*branch tolerance (unchanged preregistered functional rule). Record qualification, never resume Arm1/Arm2. If original native monitor auto-terminates before18000, preserve/STOP without disabling it or restarting.',
        'STOP': ['parent/input/binary/source mismatch', 'any unexpected factor difference', 'NaN/Inf/fatal/unstable/abnormal exit', 'P10 cannot reproduce previous continuous C18000 raw/payload hashes', 'P12 linear stall/breakdown ->NOT_FEASIBLE, no alternate', 'need formal data, existing preregistration edit, U/T/relaxation/other factor change', 'failure to reach18000 in one original-settings process; no retry/restart'],
        'old_preregistration_hashes': {p.name: sha(p) for p in HERE.glob('experiment_preregistration_v1.*')}, 'old_amendment_hashes': {p.name: sha(p) for p in HERE.glob('preregistration_amendment_00[12].*')},
        'quota': None, 'qoi_impact_quota_value': None, 'tau_mean': None, 'new_Gate_threshold': None, 'criteria_changed': False,
        'arm1_restarted': False, 'arm2_executed': False, 'formal_benchmark_used': False, 'spec_change_executed': False, 'next_action': 'Stop after this diagnostic; any U/T tolerance or relaxation study is a separate task.'}
    dump(AMEND, amendment)
    md = '# Preregistration Amendment 003 — Pressure-Tolerance Single-Factor Diagnostic\n\n'
    md += 'All rules and exact values below are fixed before the first solver call. Existing v1/001/002 are immutable. This is a diagnostic, not a quota, Gate threshold or steady-criterion change.\n\n'
    for key in ('research_questions', 'single_factor', 'common_parent', 'levels', 'execution_order', 'run_interval', 'unchanged', 'monitor_capacity_parameter', 'branch_input_difference', 'late_statistics', 'primary', 'resolved_change_rule', 'classification', 'ratios', 'normalization_scales', 'field_canonicalization', 'mapping', 'steady_evaluation', 'STOP'):
        md += '## ' + key.replace('_', ' ') + '\n\n```json\n' + json.dumps(amendment[key], indent=2) + '\n```\n\n'
    md += 'P12 preflight permits only an attempt, not a guarantee: no prior1e-12 feasibility evidence or universal floor. A stalled/broken P12 is preserved as NOT_FEASIBLE, never replaced by1e-11. Each branch has one fresh process at12000, no intermediate restart. P10 must reproduce previous continuous C18000 before P8/P12 start. Run and environment/source/input digests are retained. No other grid, formal data, Arm1/Arm2, git add/commit/push. Stop here; later factors require a separate task.\n'
    AMEND.with_suffix('.md').write_text(md)
    provenance = {'schema': 'routeB-pressure-tolerance-provenance-v1', 'startup': startup, 'registered_utc': now(), 'amendment_sha256': sha(AMEND), 'amendment_md_sha256': sha(AMEND.with_suffix('.md')), 'solver_calls': [], 'execution': {b: 'NOT_RUN' for b in ORDER}, 'P10_control_reproducibility': 'NOT_RUN', 'STOP_reason': None}
    dump(OUT / 'pressure_tolerance_provenance.json', provenance)
    print('PREPARED', provenance['amendment_sha256'], 'parent/binary/sole-factor checks PASS', flush=True)


def guard(branch, provenance):
    a = load(AMEND)
    for path, digest in [(AMEND, provenance['amendment_sha256']), (AMEND.with_suffix('.md'), provenance['amendment_md_sha256']), (Path(__file__), a['driver_sha256']), (HERE / 'analyze_pressure_tolerance.py', a['analysis_sha256']), (AUDIT, a['solver_binary_sha256'])]:
        if sha(path) != digest:
            raise RuntimeError('STOP: immutable source/binary/method changed: ' + str(path))
    for name in ('startup_provenance', 'input_diff_audit', 'classification_reference', 'feasibility_preflight'):
        if sha(OUT / (name + '.json')) != a[name + '_sha256']:
            raise RuntimeError('STOP: pre-run evidence changed')
    for name, digest in provenance['startup']['protected_hashes'].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('STOP: protected previous file changed')
    for name, digest in provenance['startup']['parent_input_hashes'].items():
        if sha(PARENT / name) != digest:
            raise RuntimeError('STOP: original parent input changed')
    if tree_hashes(PARENT / '12000') != provenance['startup']['parent_tree_hashes']:
        raise RuntimeError('STOP: original parent changed')
    if inputs(WORK / branch) != provenance['startup']['branch_input_hashes'][branch] or sha(WORK / branch / 'case_manifest.json') != provenance['startup']['parent_manifest_sha256']:
        raise RuntimeError('STOP: numerical input changed')


def snapshot(branch, iteration):
    target = WORK / 'snapshots' / branch / str(iteration)
    if target.exists():
        return
    shutil.copytree(WORK / branch / str(iteration), target)
    for field in FIELDS:
        numeric_payload(target / field, field)


def execute(branch, provenance):
    tol = LEVELS[branch]
    case = WORK / branch
    guard(branch, provenance)
    if tree_hashes(case / '12000') != provenance['startup']['parent_tree_hashes']:
        raise RuntimeError('STOP: starting state differs')
    if branch != 'P10' and provenance['P10_control_reproducibility'] != 'PASS':
        raise RuntimeError('STOP: P10 reproduction gate not passed')
    archive = WORK / ('execution_' + branch)
    archive.mkdir()
    for name in ('controlDict', 'fvSolution', 'fvSchemes'):
        shutil.copy2(case / 'system' / name, archive / name)
    call = {'branch': branch, 'tolerance': tol, 'start': 12000, 'planned_end': 18000, 'started_utc': now(), 'hostname': socket.gethostname(), 'OpenFOAM_version': ENV['WM_PROJECT_VERSION'], 'WM_OPTIONS': ENV['WM_OPTIONS'], 'load_average_start': list(os.getloadavg()), 'runtime_environment_sha256': hashlib.sha256(json.dumps(ENV, sort_keys=True).encode()).hexdigest(), 'binary_sha256_before': sha(AUDIT), 'input_hashes_before': inputs(case), 'parent_hashes': tree_hashes(case / '12000'), 'command': [str(AUDIT), '-case', str(case)], 'normal_exit': False, 'archive': str(archive)}
    provenance['solver_calls'].append(call)
    dump(OUT / 'pressure_tolerance_provenance.json', provenance)
    print('RUN', branch, 'tol', tol, 'continuous12000-18000', flush=True)
    process = subprocess.Popen(call['command'], cwd=case, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    call['pid'] = process.pid
    current = None
    end_marker = False
    error = None
    try:
        with (archive / 'log.solver').open('w') as log:
            for line in process.stdout:
                log.write(line)
                match = re.fullmatch(r'Time = (\d+)\s*', line)
                if match:
                    current = int(match.group(1))
                if 'FOAM FATAL' in line or re.search(r'(?<![A-Za-z])(?:nan|[+-]?inf)(?![A-Za-z])', line, re.I):
                    raise RuntimeError('STOP: nonfinite/fatal ' + branch)
                if 'singular' in line.lower() and 'solution' in line.lower():
                    raise RuntimeError('STOP: linear breakdown ' + branch)
                if 'Solving for p_rgh,' in line:
                    match = re.search(r'No Iterations\s+(\d+)', line)
                    if match and int(match.group(1)) >= 10000:
                        if branch == 'P12':
                            provenance['execution'][branch] = 'NOT_FEASIBLE'
                        raise RuntimeError('STOP: pressure linear stall ' + branch)
                if line.startswith('ExecutionTime = ') and current is not None and current % 20 == 0:
                    snapshot(branch, current)
                if line.strip() == 'End':
                    end_marker = True
        code = process.wait()
        call['exit_code'] = code
        if code != 0 or not end_marker or current != 18000:
            raise RuntimeError(f'STOP: {branch} abnormal/short run, code={code}, last={current}')
        audit = rows(case / 'continuityAudit.csv')
        if any(x['converged'] != 1 or x['linear_iterations'] >= 10000 or x['R_recursive'] >= tol for x in audit):
            if branch == 'P12':
                provenance['execution'][branch] = 'NOT_FEASIBLE'
            raise RuntimeError('STOP: pressure linear stall/unconverged ' + branch)
        if any(not np.isfinite(value) for row in audit for value in row.values()):
            raise RuntimeError('STOP: nonfinite audit')
        for name in ('steadyMonitor.csv', 'continuityAudit.csv', 'sourceCells.csv'):
            shutil.copy2(case / name, archive / name)
        record = extract(case, 18000)
        # Keep original parent manifest intact; label actual experimental settings explicitly.
        record.update({'diagnostic_branch': branch, 'actual_pressure_tolerance': tol, 'parent_manifest_retained_for_provenance': True})
        dump(OUT / (branch + '_18000.json'), record)
        if branch == 'P10':
            comparison = {}
            for field in FIELDS:
                path = case / '18000' / field
                payload = numeric_payload(path, field)[0]
                expected = provenance['startup']['P10_expected_C18000'][field]
                comparison[field] = {'P10_raw_sha256': sha(path), 'C_raw_sha256': expected['C_raw_sha256'], 'P10_payload_sha256': payload, 'C_payload_sha256': expected['C_payload_sha256'], 'raw_identical': sha(path) == expected['C_raw_sha256'], 'payload_identical': payload == expected['C_payload_sha256']}
            provenance['P10_control_comparison'] = comparison
            provenance['P10_control_reproducibility'] = 'PASS' if all(v['raw_identical'] and v['payload_identical'] for v in comparison.values()) else 'FAIL'
            dump(OUT / 'P10_control_reproducibility.json', comparison)
            if provenance['P10_control_reproducibility'] != 'PASS':
                raise RuntimeError('STOP: P10 cannot reproduce existing continuous C18000')
            print('P10 CONTROL REPRODUCIBILITY PASS: four raw/payload hashes identical', flush=True)
        call['normal_exit'] = True
        provenance['execution'][branch] = 'PASS'
    except BaseException as caught:
        error = caught
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        if provenance['execution'][branch] != 'NOT_FEASIBLE':
            provenance['execution'][branch] = 'FAIL'
        if branch == 'P12' and ('linear breakdown' in str(caught) or 'pressure linear stall' in str(caught)):
            provenance['execution'][branch] = 'NOT_FEASIBLE'
    finally:
        for name in ('steadyMonitor.csv', 'continuityAudit.csv', 'sourceCells.csv'):
            if (case / name).exists():
                shutil.copy2(case / name, archive / name)
        call.update({'finished_utc': now(), 'load_average_end': list(os.getloadavg()), 'exit_code': process.returncode, 'last_iteration': current, 'binary_sha256_after': sha(AUDIT), 'input_hashes_after': inputs(case), 'archive_hashes': tree_hashes(archive)})
        dump(OUT / 'pressure_tolerance_provenance.json', provenance)
    if error:
        raise error
    guard(branch, provenance)
    print('DONE', branch, 'normal18000', flush=True)


def run():
    provenance = load(OUT / 'pressure_tolerance_provenance.json')
    if provenance['solver_calls']:
        raise RuntimeError('Refuse solver retries or restart')
    try:
        for branch in ORDER:
            execute(branch, provenance)
        provenance['execution_completed_utc'] = now()
    except BaseException as error:
        provenance['STOP_reason'] = str(error)
        print(str(error), flush=True)
    dump(OUT / 'pressure_tolerance_provenance.json', provenance)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('prepare', 'run'):
        raise SystemExit('Usage: pressure_tolerance_diagnostic.py prepare|run')
    {'prepare': prepare, 'run': run}[sys.argv[1]]()
