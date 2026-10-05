#!/usr/bin/env python3
"""Only amendment 002's three serial microcase processes; never production cases."""
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'results/routeB/gateG_sensitivity_experiment/restart_effect_diagnostic'
WORK = HERE / 'runs/restart_effect_002'
PARENT = HERE / 'runs/baseline_n20'
PREVIOUS = OUT.parent / 'baseline_convergence_qualification.json'
EXPECTED_HEAD = '769a7ae274266e511ab21931ae8becd9d1d55a0c'
FIELDS = ('U', 'T', 'p_rgh', 'phi')
PATCHES = ('hotWall', 'coldWall', 'bottomWall', 'topWall', 'front', 'back')
AMEND = HERE / 'preregistration_amendment_002.json'
sys.path.insert(0, str(HERE))
from experiment import AUDIT, ENV, QOIS, parser


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


def check_hashes(folder, expected):
    for name, digest in expected.items():
        if sha(folder / name) != digest:
            raise RuntimeError('STOP: hash changed: ' + str(folder / name))


def input_hashes(case):
    return {str(p.relative_to(case)): sha(p)
            for sub in ('constant', 'system')
            for p in sorted((case / sub).rglob('*')) if p.is_file()}


def control(target):
    original = (PARENT / 'system/controlDict').read_text()
    return re.sub(r'\bendTime\s+\d+;', f'endTime {target};',
                  original.replace('startFrom startTime;', 'startFrom latestTime;'))


def numeric_payload(path, field):
    """No rounding: typed/shaped blocks followed by little-endian IEEE754 doubles."""
    text = path.read_text()
    internal = parser.read_vector(path, 400) if field == 'U' else parser.read_scalar(path, 760 if field == 'phi' else 400)
    blocks = [('internalField', internal)]
    boundary = parser._block(text, 'boundaryField')
    metadata = {'field': field, 'dimensions': re.search(r'\bdimensions\s+(\[[^]]+\])\s*;', text).group(1), 'patches': []}
    for patch_index, patch in enumerate(PATCHES):
        block = parser._block(boundary, patch)
        kind = re.search(r'\btype\s+(\w+)\s*;', block).group(1)
        metadata['patches'].append({'name': patch, 'type': kind})
        if patch in ('front', 'back'):
            if kind != 'empty':
                raise RuntimeError('STOP: changed empty boundary')
            # Empty patches have no represented numerical values, even though mesh nFaces=400.
            if re.search(r'\bvalue\s+', block):
                if not re.search(r'\bvalue\s+nonuniform\s+(?:List<(?:scalar|vector)>\s+)?0\s*\(\s*\)\s*;', block):
                    raise RuntimeError('STOP: unsupported/nonempty empty-patch payload')
            blocks.append((patch + '/value', np.empty((0, 3)) if field == 'U' else np.empty(0)))
            continue
        reader = parser.read_boundary_vector if field == 'U' else parser.read_boundary_scalar
        if re.search(r'\bvalue\s+', block):
            values = reader(path, patch, 20)
            metadata['patches'][-1]['value_origin'] = 'stored'
        elif kind == 'zeroGradient' and field != 'phi':
            owner = parser.read_label_list(PARENT / 'constant/polyMesh/owner')
            values = internal[owner[760 + patch_index * 20:780 + patch_index * 20]]
            metadata['patches'][-1]['value_origin'] = 'implicit_zeroGradient_owner_internal'
        else:
            raise RuntimeError('STOP: unsupported implicit boundary values')
        blocks.append((patch + '/value', values))
        # Include stored fixedFluxPressure gradients, not just its boundary value.
        gradient = re.search(r'\bgradient\s+uniform\s+([^;]+);', block)
        if gradient:
            blocks.append((patch + '/gradient', np.full(20, float(gradient.group(1)))))
        elif re.search(r'\bgradient\s+nonuniform\s+', block):
            gradient = re.search(r'\bgradient\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(\s*(.*?)\s*\)\s*;', block, re.S)
            if not gradient:
                raise RuntimeError('STOP: unsupported gradient list')
            values = np.fromstring(gradient.group(2), sep=' ')
            if int(gradient.group(1)) != 20 or values.size != 20:
                raise RuntimeError('STOP: wrong gradient list count')
            blocks.append((patch + '/gradient', values))
        elif re.search(r'\bgradient\s+', block):
            raise RuntimeError('STOP: unsupported gradient payload; do not silently omit')
    metadata['blocks'] = [{'name': name, 'shape': list(arr.shape)} for name, arr in blocks]
    payload = json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode() + b'\0'
    for _, arr in blocks:
        if not np.isfinite(arr).all():
            raise RuntimeError('STOP: nonfinite numerical payload ' + str(path))
        payload += np.ascontiguousarray(arr, dtype='<f8').tobytes()
    return hashlib.sha256(payload).hexdigest(), blocks, metadata


def compare_fields(iteration):
    rows = []
    for field in FIELDS:
        cp = WORK / 'snapshots/C' / str(iteration) / field
        rp = WORK / 'snapshots/R' / str(iteration) / field
        ch, cb, cm = numeric_payload(cp, field)
        rh, rb, rm = numeric_payload(rp, field)
        if cm != rm:
            raise RuntimeError('STOP: field metadata/BC difference')
        rows.append({'iteration': iteration, 'field': field,
                     'C_raw_sha256': sha(cp), 'R_raw_sha256': sha(rp),
                     'C_payload_sha256': ch, 'R_payload_sha256': rh,
                     'raw_identical': sha(cp) == sha(rp), 'payload_identical': ch == rh,
                     'values_exactly_equal': all(np.array_equal(c, r) for (_, c), (_, r) in zip(cb, rb))})
    return rows


def save_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader()
        writer.writerows(rows)


def prepare():
    if OUT.exists() or WORK.exists() or AMEND.exists() or AMEND.with_suffix('.md').exists():
        raise RuntimeError('Refuse to overwrite existing diagnostic/amendment')
    head = git('rev-parse', 'HEAD')
    if head != EXPECTED_HEAD:
        raise RuntimeError('STOP: unexpected HEAD; inspect only subsequent diff before preparation')
    previous = load(PREVIOUS)
    original = previous['startup_provenance']
    check_hashes(PARENT, original['original_case_input_hashes'])
    if tree_hashes(PARENT / '12000') != original['12000_restart_tree_hashes']:
        raise RuntimeError('STOP: original common parent tree differs')
    if sha(AUDIT) != original['binary']['sha256']:
        raise RuntimeError('STOP: binary differs from recorded qualification digest')
    reg = load(HERE / 'experiment_preregistration_v1.json')
    check_hashes(ROOT, reg['source_hashes'])
    manifest = load(PARENT / 'case_manifest.json')
    if not (manifest['n'] == 20 and manifest['Ra_test'] == 30000 and manifest['tolerance'] == 1e-10 and
            manifest['relTol'] == 0 and manifest['eta_nom'] == 0 and manifest['sum_abs_g'] == 0 and
            manifest['temperature_offset'] == 0):
        raise RuntimeError('STOP: parent outside allowed scope')
    if np.any(parser.read_scalar(PARENT / 'constant/continuitySource', 400)):
        raise RuntimeError('STOP: nonzero source')
    protected_paths = set(original['protected_hashes']) | set(reg['source_hashes'])
    protected_paths.update(str(p.relative_to(ROOT)) for p in OUT.parent.rglob('*') if p.is_file())
    protected_paths.update(str(p.relative_to(ROOT)) for pattern in ('experiment_preregistration_v1.*', 'preregistration_amendment_001.*') for p in HERE.glob(pattern))
    protected_paths.update(str(p.relative_to(ROOT)) for p in (HERE / 'experiment.py', HERE / 'analyze.py', HERE / 'steadyMonitor.H', HERE.parent / 'common.py', ROOT / 'Scripts/routeB/foam_fields.py', ROOT / 'Scripts/routeB/analyze_case.py'))
    protected = {p: sha(ROOT / p) for p in sorted(protected_paths)}
    up = float(np.max(np.linalg.norm(parser.read_vector(PARENT / '12000/U', 400), axis=1)))
    pressure = parser.read_scalar(PARENT / '12000/p_rgh', 400)
    pscale = float(np.sqrt(np.mean((pressure - np.mean(pressure)) ** 2)))
    if up <= 0 or pscale <= 0:
        raise RuntimeError('STOP: undefined reference scale')
    references = {key: float(np.median(value['amplitude_medians'])) for key, value in previous['classification_evidence'].items()}
    references.update({key: float(np.median(value['amplitude_medians'])) for key, value in previous['individual_monitor_classifications'].items()})
    OUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    for branch, target in [('C', 18000), ('R', 15000)]:
        case = WORK / ('branch_' + branch)
        case.mkdir()
        for folder in ('constant', 'system', '12000'):
            shutil.copytree(PARENT / folder, case / folder)
        shutil.copy2(PARENT / 'case_manifest.json', case / 'case_manifest.json')
        (case / 'system/controlDict').write_text(control(target))
        if tree_hashes(case / '12000') != original['12000_restart_tree_hashes']:
            raise RuntimeError('STOP: copied parent mismatch')
        expected_inputs = dict(original['original_case_input_hashes'])
        expected_inputs['system/controlDict'] = sha(case / 'system/controlDict')
        if input_hashes(case) != expected_inputs:
            raise RuntimeError('STOP: copied inputs differ')
    startup = {'created_utc': now(), 'HEAD': head, 'git_status_short': git('status', '--short'),
               'common_parent_path': str(PARENT), 'common_parent_tree_hashes': original['12000_restart_tree_hashes'],
               'parent_input_hashes': original['original_case_input_hashes'], 'case_manifest_sha256': sha(PARENT / 'case_manifest.json'),
               'solver_binary': original['binary'], 'solver_source_hashes': reg['source_hashes'],
               'protected_hashes': protected, 'branch_starting_inputs': {b: input_hashes(WORK / ('branch_' + b)) for b in ('C', 'R')},
               'branch_parent_tree_hashes': {b: tree_hashes(WORK / ('branch_' + b) / '12000') for b in ('C', 'R')}}
    dump(OUT / 'startup_provenance.json', startup)
    amendment = {
        'schema': 'routeB-gateG-restart-effect-preregistration-amendment-002', 'created_utc': now(),
        'purpose': 'Isolate additional restart at iteration 15000; common restart at 12000 is shared, not separately estimated.',
        'research_questions': ['Does the additional restart change U/T/p_rgh/phi at 18000?', 'What are field/QoI/continuity differences relative to previous variation magnitudes?', 'Does the continuous branch retain a similar variation band? Primary cause remains distinct from detected effect.'],
        'parent': {'path': str(PARENT), 'iteration': 12000, 'Ra_test': 30000, 'grid': [20, 20, 1], 'source': 'zero', 'tree_hashes': startup['common_parent_tree_hashes']},
        'original_preregistration_sha256': sha(HERE / 'experiment_preregistration_v1.json'),
        'previous_amendment_sha256': sha(HERE / 'preregistration_amendment_001.json'),
        'startup_provenance_sha256': sha(OUT / 'startup_provenance.json'),
        'driver_sha256': sha(Path(__file__)), 'analysis_sha256': sha(HERE / 'analyze_restart_effect.py'),
        'branches': {'C': {'kind': 'continuous', 'process_intervals': [[12000, 18000]], 'intermediate_restart': False},
                     'R': {'kind': 'restart', 'process_intervals': [[12000, 15000], [15000, 18000]], 'intermediate_restart': True}},
        'execution_order': ['R12000-15000', 'C12000-18000', 'R15000-18000'], 'maximum_solver_calls': 3,
        'continuous_snapshot_capture': 'Read stdout ExecutionTime after completed write at each multiple of 20 from 15000 onward; copy already-written fields to external ignored snapshots. No signal/pause/control edit/restart at 15000. Verify C/R15000 during C process before R second process.',
        'unchanged': ['p tolerance 1e-10', 'U/T tolerance 1e-12', 'all relTol 0', 'relaxation', 'fvSchemes', 'mesh', 'physics', 'BC', 'zero source', 'all 12000 state', 'solver source/binary', 'QoI definitions', 'monitor definitions', 'original steady criteria', 'writeInterval 20', 'purgeWrite 14', 'ASCII precision16'],
        'sole_input_edits': ['startFrom latestTime in both copied cases', 'endTime 15000 or 18000 in copied cases'],
        'solver_binary_sha256': sha(AUDIT),
        'canonicalization': {'version': 1, 'encoding': 'UTF8 sorted compact JSON metadata, NUL byte, then ordered contiguous little-endian float64 arrays; no rounding/tolerances',
            'metadata': 'field name, dimensions, patch names/types, block names/shapes; omit FoamFile header and formatting only',
            'block_order': ['internalField', *PATCHES], 'patch_values': 'Physical patches expanded to mesh size20, vectors component x/y/z. zeroGradient without stored value uses adjacent owner internal values from the common verified mesh; metadata marks this implicit origin. Empty front/back zero-length arrays with type empty, not invented values for mesh faces. Include stored uniform/nonuniform scalar gradients for fixedFluxPressure patches after that patch value; STOP for unsupported gradients/implicit BC.',
            'raw_hashes_always_saved': True, 'raw_mismatch_rule': 'If numerical hashes identical, remove only FoamFile header and whitespace/comments and require all remaining tokens equal. Otherwise STOP at15000; do not blame metadata without proving it.'},
        'field_comparison': {'checkpoints': [15000, 18000], 'intermediate': 'All written samples 15020:20:18000 if captured; never reconstruct unavailable fields',
            'U': 'max Euclidean vector norm, RMS of vector norm; internal+physical boundary values; also component max and internal-only metrics',
            'scalars': 'max abs, RMS over internal+physical boundary value arrays; stored gradients hash/equality checked separately',
            'phi': 'also L1 sum of internal+physical boundary differences; normalized max/RMS/L1 using same characteristic face flux, not epsilon or actual flux denominator'},
        'normalization_scales': {'U_Up_reference_m_s': up, 'T_DeltaT_K': 1., 'p_rgh_parent_centered_internal_RMS_m2_s2': pscale,
            'phi_characteristic_face_flux_m3_s': up * .01 / 20 * .001, 'rule': 'All scales frozen from common12000: Up=max internal |U|, pscale=centered internal RMS. Same gauge/reference in both branches. Flux=Up*(L/20)*depth.'},
        'qoi_comparison': {'names': QOIS, 'value_relative_difference': '|R-C|/|C|; if C exactly zero report null, retain absolute difference, do not introduce floor', 'position_difference': 'absolute nondimensional; no inferred sub-sampling peak accuracy', 'definitions': 'existing experiment.extract / native monitor, 4097 centreline samples'},
        'continuity_comparison': ['epsilon_phi_mean', 'epsilon_phi_max', 'heat_imbalance', 'boundary_flux', 'closure', 'pressure audit'],
        'branch_variation': {'sample_interval': 20, 'window_iterations': 200, 'samples': 11, 'matched_valid_interval': [15240, 18000],
            'warmup': 'R15020 U/T change is restart sentinel; exclude all windows until15240. C uses the identical matched interval, retaining original native definitions.',
            'statistics': 'min/median/max/P95; QoI ranges divided by max(abs(current),1), positions absolute; U/T window max20-step changes, heat absolute range; epsilon mean/max absolute level and window range. Native monitor remains authoritative and unchanged.'},
        'existing_band_reference': {'source': str(PREVIOUS.relative_to(ROOT)), 'rule': 'median of previously saved amplitude_medians for18000/24000/30000, fixed before calls', 'magnitudes': references,
            'ratios': 'endpoint and trajectory max/median absolute restart difference divided by the matching fixed magnitude; positions with zero reference -> null, no floor; epsilon references are level magnitudes, not variation amplitudes; pressure/phi lack prior like-for-like band -> null'},
        'classification': {'NOT_DETECTED': 'All four18000 numerical hashes equal or every field value difference exactly zero; restart effect NOT_SUPPORTED at endpoint, inspect history separately.',
            'DETECTED': 'Any nonzero18000 field value difference with verified common12000 and pre-restart15000 equivalence; restart effect exists, not automatically primary cause.',
            'INCONCLUSIVE': 'Insufficient provenance, setup equivalence or comparison resolution.',
            'continuous_retains_band': 'Descriptive only: median C matched-window max value-QoI range nonzero and nearest power-of-ten order equals previous QoI reference (floor(log10(x)+0.5)); report unrounded ratio and all component ranges. This is an order label, never scientific acceptance/steady PASS.',
            'necessary_condition': 'If continuous retains band: additional15000 restart is NOT_SUPPORTED as a necessary condition in this interval. Otherwise INCONCLUSIVE, not proof of necessity.',
            'primary_cause': 'INCONCLUSIVE: single matched3000-iteration post-factor interval lacks independent replicated/long-term distributions; no primary-cause claim from difference magnitude alone.',
            'trajectory': 'Report exact-zero samples, first nonzero, first/last values, early15020-15200 and late17800-18000 medians, maxima and ratios. Label zero/decaying/amplifying/persistent irregular qualitatively from these observations; no causal fit or new acceptance cutoff.'},
        'STOP': ['12000 parent/input mismatch', 'branch input inequivalence beyond permitted start/end fields', '15000 numerical mismatch or unproved raw mismatch', 'binary/source hash mismatch', 'numerical settings changed', 'NaN/Inf/fatal or failure to reach target normally', 'formal data or existing preregistration edits needed', 'any factor other than restart needed'],
        'research_quota': None, 'qoi_impact_quota_value': None, 'tau_mean': None, 'criteria_changed': False,
        'arm1_restarted': False, 'arm2_executed': False, 'formal_benchmark_used': False, 'spec_change_executed': False,
        'next_action': 'Stop after restart diagnostic. Any tolerance or relaxation study needs a separate task.'}
    dump(AMEND, amendment)
    md = '''# Preregistration Amendment 002 — Additional Restart at Iteration 15000

This diagnostic estimates only the effect of adding a process termination/write-read/reinitialization bundle at15000. Both branches share the existing12000 state and its restart. It does not estimate restart in general.

## Design fixed before execution

Ra_test30000,20×20×1,zero source; p tolerance1e-10, U/T1e-12,relTol0. All numerical inputs, BC, mesh, source, solver source/binary, native monitor/QoI definitions and original steady criteria are frozen. Only copied controlDict startFrom/latestTime and endTime are edited. No Arm1/Arm2 continuation, other grids, stock equivalence repeat, formal benchmark data or solver execution.

C:12000→18000 in one process. R:12000→15000 normal exit, then15000→18000 in a fresh process. Execution order R first half,C,R second half, exactly three solver calls. Completed C writes are archived while stdout is read, without stopping C; at15000 all four fields must match R before accepting any post-factor comparison. All restart fields including alphat,p,uniform/time and all parent inputs are checked against recorded provenance.

## Canonicalization and comparisons

Raw whole-file SHA256 is always retained. Numerical hash: sorted compact UTF8 JSON metadata (field, dimensions, patch types/value origins and block shapes), NUL, ordered little-endian Float64 numerical arrays; no rounding. Internal values first, then hotWall,coldWall,bottomWall,topWall,front,back. Expand physical patch values to20 entries; for zeroGradient without stored values use the adjacent owner internal values from the verified common mesh and label that implicit origin. Preserve vector x/y/z order, record empty patches as zero-length arrays. Include fixedFluxPressure stored uniform/nonuniform scalar gradients in the hash. For a raw-only mismatch, prove all non-header tokens identical after excluding comments/formatting; otherwise STOP at15000.

U max/RMS use Euclidean vector norms; T/p/phi max/RMS use scalar differences, over internal plus represented physical boundary values. Also retain internal-only differences, pressure absolute units/scale and phi L1. Reference scales are frozen from12000: max internal speed, DeltaT1K, centered pressure internal RMS, characteristic face flux Up*(L/20)*depth. Report gradients separately and never subtract a different pressure gauge.

At18000 compare seven existing QoIs; value relative difference is abs(R-C)/abs(C), positions absolute nondimensional. Zero denominator yields null, with absolute difference retained. Compare epsilon_phi_mean/max and heat imbalance plus audit/closure. Capture intermediate written fields if available; no reconstruction.

## Windows and reference magnitudes

Both branches use the original11-sample/200-iteration window and20-iteration sample interval. For matched branch variation use15240–18000: this excludes R's15020 restart sentinel and incomplete windows. Report min/median/max/P95 for QoI ranges, U/T change window maxima, heat ranges and epsilon levels/ranges. The native monitor is unchanged.

Prior reference magnitudes are the median of previously saved late-checkpoint amplitude medians at18000/24000/30000; their exact values and scales are frozen in the JSON. Endpoint and trajectory difference/reference ratios are diagnostic, never acceptance thresholds. Position reference zero yields null; no invented floor. Epsilon reference uses level, not variation amplitude; no prior pressure/phi band is fabricated.

## Interpretation and stopping

With verified12000 and15000 equality: nonzero18000 fields -> DETECTED; exact identical numerical payloads/all-zero field differences -> NOT_DETECTED (endpoint). Insufficient provenance/setup/resolution -> INCONCLUSIVE. Detection and magnitude do not establish a primary cause. The latter remains INCONCLUSIVE for this single3000-iteration comparison.

Continuous-band presence is a descriptive decimal-order label: nearest power-of-ten of median C max value-QoI window range equals that of the fixed prior reference, with nonzero values. All exact ratios are shown; this does not change any scientific acceptance or steady criterion. If the continuous branch retains this band, the additional15000 restart is NOT_SUPPORTED as its necessary condition within this interval. A missing band alone does not establish necessity.

Trajectory diagnostics retain first nonzero/first/last/max, early15020–15200 and late17800–18000 medians/ratios, and exact-zero counts. Describe zero, decay, amplification or persistent irregular response without a new PASS cutoff. Serialization and solver reinitialization are treated as one bundle.

Immediate STOP on parent/branch/pre-restart numerical mismatch, binary/source/settings mismatch, NaN/Inf/fatal/abnormal target, or need for formal data, existing preregistration changes or another factor. Preserve partial evidence. Existing v1/amendment001 and results are immutable. Quota/tau remain unresolved; Candidate B remains PROVISIONAL and formal Ra1e3 Gate G remains FAIL (declared prior state, no formal reevaluation). Stop after this diagnostic; a tolerance study belongs to a separate user decision.

## Immutable registration

The companion JSON records exact parent hashes, solver digest, driver/analysis digests, scales, reference magnitudes and startup provenance hash. Both amendment hashes are saved before the first solver call, checked before every call and after analysis, and never edited after execution.
'''
    AMEND.with_suffix('.md').write_text(md)
    provenance = {'schema': 'routeB-restart-effect-provenance-v1', 'startup': startup,
                  'amendment_sha256': sha(AMEND), 'amendment_md_sha256': sha(AMEND.with_suffix('.md')),
                  'registered_utc': now(), 'solver_calls': [], 'pre_restart_equivalence': None}
    dump(OUT / 'restart_provenance.json', provenance)
    print('PREPARED', 'parent/binary/input checks PASS', 'amendment', provenance['amendment_sha256'], flush=True)


def guard(case, target, provenance):
    amendment = load(AMEND)
    for path, key in [(AMEND, 'amendment_sha256'), (AMEND.with_suffix('.md'), 'amendment_md_sha256')]:
        if sha(path) != provenance[key]:
            raise RuntimeError('STOP: immutable amendment changed')
    for path, key in [(Path(__file__), 'driver_sha256'), (HERE / 'analyze_restart_effect.py', 'analysis_sha256'), (OUT / 'startup_provenance.json', 'startup_provenance_sha256')]:
        if sha(path) != amendment[key]:
            raise RuntimeError('STOP: registered method changed')
    check_hashes(ROOT, provenance['startup']['protected_hashes'])
    check_hashes(PARENT, provenance['startup']['parent_input_hashes'])
    if tree_hashes(PARENT / '12000') != provenance['startup']['common_parent_tree_hashes']:
        raise RuntimeError('STOP: common parent changed')
    if sha(AUDIT) != amendment['solver_binary_sha256']:
        raise RuntimeError('STOP: binary changed')
    expected = dict(provenance['startup']['parent_input_hashes'])
    expected['system/controlDict'] = hashlib.sha256(control(target).encode()).hexdigest()
    if input_hashes(case) != expected or sha(case / 'case_manifest.json') != provenance['startup']['case_manifest_sha256']:
        raise RuntimeError('STOP: working input changed')


def tokens_without_header(path):
    text = path.read_text()
    header = parser._block(text, 'FoamFile')
    text = text.replace('FoamFile' + text.split('FoamFile', 1)[1].split('{', 1)[0] + '{' + header + '}', '', 1)
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    return re.findall(r'[^\s{}();]+|[{}();]', text)


def snapshot(branch, iteration, provenance):
    source = WORK / ('branch_' + branch) / str(iteration)
    destination = WORK / 'snapshots' / branch / str(iteration)
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    for field in FIELDS:
        numeric_payload(destination / field, field)
    if branch == 'C' and iteration == 15000:
        comparisons = compare_fields(15000)
        save_csv(OUT / 'field_hash_comparison.csv', comparisons)
        if not all(row['payload_identical'] and row['values_exactly_equal'] for row in comparisons):
            raise RuntimeError('STOP:15000 pre-restart numerical inequivalence')
        raw_equal = all(row['raw_identical'] for row in comparisons)
        if not raw_equal and not all(tokens_without_header(destination / f) == tokens_without_header(WORK / 'snapshots/R/15000' / f) for f in FIELDS):
            raise RuntimeError('STOP: unexplained raw15000 hash mismatch')
        provenance['pre_restart_equivalence'] = 'BITWISE_IDENTICAL' if raw_equal else 'NUMERICALLY_IDENTICAL'
        provenance['pre_restart_comparisons'] = comparisons
        provenance['pre_restart_verification_utc'] = now()
        dump(OUT / 'restart_provenance.json', provenance)
        print('15000 PRE-RESTART', provenance['pre_restart_equivalence'], 'C process remains continuous', flush=True)


def run_process(branch, start, end, provenance):
    case = WORK / ('branch_' + branch)
    guard(case, end, provenance)
    latest = max(int(p.name) for p in case.iterdir() if p.is_dir() and p.name.isdigit())
    if latest != start:
        raise RuntimeError('STOP: unexpected latestTime')
    if start == 12000 and tree_hashes(case / '12000') != provenance['startup']['common_parent_tree_hashes']:
        raise RuntimeError('STOP: branch parent changed')
    if start == 15000:
        if not provenance['pre_restart_equivalence']:
            raise RuntimeError('STOP: missing live C15000 equivalence guard')
        if tree_hashes(case / '15000') != tree_hashes(WORK / 'snapshots/R/15000'):
            raise RuntimeError('STOP: R15000 restart state changed')
    archive = WORK / f'segment_{branch}_{start}_{end}'
    archive.mkdir()
    for name in ('controlDict', 'fvSchemes', 'fvSolution'):
        shutil.copy2(case / 'system' / name, archive / name)
    call = {'branch': branch, 'start': start, 'end': end, 'started_utc': now(), 'normal_exit': False,
            'command': [str(AUDIT), '-case', str(case)], 'before_input_hashes': input_hashes(case),
            'before_binary_sha256': sha(AUDIT), 'before_starting_state_hashes': tree_hashes(case / str(start)), 'archive': str(archive)}
    provenance['solver_calls'].append(call)
    dump(OUT / 'restart_provenance.json', provenance)
    print('RUN', branch, start, end, flush=True)
    process = subprocess.Popen(call['command'], cwd=case, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    call['pid'] = process.pid
    dump(OUT / 'restart_provenance.json', provenance)
    current = None
    exited = False
    try:
        with (archive / 'log.solver').open('w') as log:
            for line in process.stdout:
                log.write(line)
                match = re.fullmatch(r'Time = (\d+)\s*', line)
                if match:
                    current = int(match.group(1))
                if 'FOAM FATAL' in line or re.search(r'(?<![A-Za-z])(?:nan|[+-]?inf)(?![A-Za-z])', line, re.I):
                    raise RuntimeError('STOP: nonfinite/fatal solver output')
                if line.startswith('ExecutionTime = ') and current is not None and current >= 15000 and current % 20 == 0:
                    snapshot(branch, current, provenance)
                if line.strip() == 'End':
                    exited = True
        code = process.wait()
        call['exit_code'] = code
        if code != 0 or not exited or current != end:
            raise RuntimeError(f'STOP: abnormal exit/target: code={code}, current={current}, expected={end}')
        snapshot(branch, end, provenance)
        for file in ('steadyMonitor.csv', 'continuityAudit.csv', 'sourceCells.csv'):
            shutil.copy2(case / file, archive / file)
            for row in csv.DictReader((archive / file).open()):
                if any(not np.isfinite(float(value)) for value in row.values()):
                    raise RuntimeError('STOP: nonfinite diagnostic CSV')
        call.update({'normal_exit': True, 'finished_utc': now(), 'last_iteration': current,
                     'after_input_hashes': input_hashes(case), 'after_binary_sha256': sha(AUDIT),
                     'final_state_hashes': tree_hashes(case / str(end)), 'archive_hashes': tree_hashes(archive)})
        guard(case, end, provenance)
        dump(OUT / 'restart_provenance.json', provenance)
        print('DONE', branch, end, 'normal exit', flush=True)
    except BaseException:
        process.terminate()
        process.wait(timeout=10)
        call.update({'finished_utc': now(), 'last_iteration': current, 'exit_code': process.returncode})
        dump(OUT / 'restart_provenance.json', provenance)
        raise


def run():
    provenance = load(OUT / 'restart_provenance.json')
    if provenance['solver_calls']:
        raise RuntimeError('Refuse duplicate/repeated solver calls')
    try:
        run_process('R', 12000, 15000, provenance)
        run_process('C', 12000, 18000, provenance)
        # The only between-process input mutation: permitted endTime, no numerical setting.
        case = WORK / 'branch_R'
        guard(case, 15000, provenance)
        (case / 'system/controlDict').write_text(control(18000))
        run_process('R', 15000, 18000, provenance)
        if len(provenance['solver_calls']) != 3:
            raise RuntimeError('STOP: unexpected process count')
        provenance['execution_complete_utc'] = now()
        dump(OUT / 'restart_provenance.json', provenance)
    except BaseException as error:
        provenance['STOP_reason'] = str(error)
        dump(OUT / 'restart_provenance.json', provenance)
        dump(OUT / 'restart_effect_summary.json', {'schema': 'routeB-gateG-restart-effect-diagnostic-v1', 'diagnostic_status': 'INCONCLUSIVE', 'STOP_reason': str(error), 'restart_effect_class': 'INCONCLUSIVE', 'numerical_settings_changed': False, 'formal_benchmark_used': False, 'arm1_restarted': False, 'arm2_executed': False, 'tau_mean': None, 'candidate_B_status': 'PROVISIONAL', 'spec_change_executed': False, 'user_decision_required': True})
        (OUT / 'restart_effect_report.md').write_text('# Restart-Effect Controlled Diagnostic\n\nSTOP: ' + str(error) + '\n\nPartial evidence preserved; no causal inference.\n')
        raise


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('prepare', 'run'):
        raise SystemExit('Usage: restart_effect_diagnostic.py prepare|run')
    {'prepare': prepare, 'run': run}[sys.argv[1]]()
