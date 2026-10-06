"""Offline source/evidence review. No target adapter or stage runner dispatch."""
import csv, inspect, io, json, math, os, re, socket, statistics, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
HERE = ROOT / 'Scripts/routeA/diagnostic_transient/timing_qualification/measurement'
sys.path.insert(0, str(HERE))
from common import atomic, authority, load, need, plan, sha, PREP, CONTRACT
from archive import recover, artifact_blocks
from fixture import graph
import runner, packed, online_evaluator as oe

FAILED_ID = 'nonCFD_20261006T083856+0900_b002832e'
FAILED = ROOT / 'results/routeA/diagnostic_transient/timing_qualification' / FAILED_ID
guard = load(OUT / 'start_guard.json')
need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == guard['HEAD'], 'STOP_HEAD_CHANGED')
for path, entry in guard['failed_campaign_files'].items():
    f = FAILED / path
    need(sha(f) == entry['sha256'] and f.stat().st_mtime_ns == entry['mtime_ns'], 'STOP_FAILED_EVIDENCE_CHANGED:' + path)
need({str(f.relative_to(FAILED)) for f in FAILED.rglob('*') if f.is_file()} == set(guard['failed_campaign_files']), 'STOP_FAILED_DIRECTORY_CHANGED')
for path, digest in guard['frozen_source_and_artifact_SHA256'].items():
    need(sha(ROOT / path) == digest, 'STOP_SOURCE_CHANGED:' + path)
authority_receipt = authority.verify_authority()
runner.verify_harness()
regression = load(OUT / 'regression.json')
need(regression['status'] == 'PASS' and regression['tests_run'] == 46 and regression['source_unchanged_during_tests'], 'STOP_REGRESSION')

def textfile(directory, name, value):
    with (directory / name).open('x', encoding='utf-8') as f:
        f.write(value); f.flush(); os.fsync(f.fileno())

def write_csv(name, rows):
    buffer = io.StringIO()
    w = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
    textfile(PREP, name, buffer.getvalue())

required_reads = ['DiagnosticTransient_nonCFD_timing_qualification.md', 'DiagnosticTransient_nonCFD_timing_qualification.json', 'Q1_partial_span_accounting.json', 'Q1_callback_class_metrics.csv', 'Q1_trial_metrics.csv', 'Q1_resource_summary.json', 'Q1_resource_trace_summary.csv', 'Q1/stage_result.json', 'Q1/trial_result.json', 'Q1/resource_trace.jsonl', 'final_verification.json', 'campaign_evidence_manifest.json']
read_receipt = {name: {'bytes': len((FAILED / name).read_bytes()), 'sha256': sha(FAILED / name)} for name in required_reads}
manifest = load(FAILED / 'campaign_evidence_manifest.json')
need(sha(FAILED / 'campaign_evidence_manifest.json') == load(FAILED / 'final_verification.json')['campaign_manifest_SHA256'], 'STOP_FAILED_MANIFEST_PIN')
for a in manifest['artifacts']:
    need(sha(FAILED / a['path']) == a['sha256'], 'STOP_FAILED_MANIFEST_ARTIFACT')
for a in load(FAILED / 'Q1/qualification_manifest.json')['artifacts']:
    need(sha(FAILED / 'Q1' / a['path']) == a['sha256'], 'STOP_FAILED_STAGE_MANIFEST')
records, tail = recover(FAILED / 'Q1/archive', verify=True)
need(not tail and len(records) == 1, 'STOP_ARCHIVE_INTEGRITY')
artifacts = {a['path']: a for a in records[0]['artifacts']}
def raw(name):
    return b''.join(artifact_blocks(FAILED / 'Q1/archive', artifacts[name]))
trial = records[0]['metadata']
need(trial['status'] == 'CENSORED' and trial['STOP_reason'] == 'STOP_WALL_TIME', 'STOP_WRONG_FAILED_TRIAL')
progress = [json.loads(x) for x in raw('native_progress.jsonl').splitlines() if x.startswith(b'{')]
trace = [json.loads(x) for x in raw('resource_trace.jsonl').splitlines()]
outer = [json.loads(x) for x in (FAILED / 'Q1/resource_trace.jsonl').read_text().splitlines()]
start = trial['start_monotonic']
tick_hz = os.sysconf('SC_CLK_TCK')

# A 31-byte structural probe of the installed reader. No elapsed benchmark,
# target fields, fixture adapter or Q1/Q2 stage is invoked.
reader_calls = []
original = socket.SocketIO.readinto
left, right = socket.socketpair()
stream = right.makefile('rwb', buffering=0)
try:
    def counted(self, buffer):
        reader_calls.append(len(buffer)); return original(self, buffer)
    socket.SocketIO.readinto = counted
    tiny_message = b'{"tiny_structural_probe":true}\n'
    left.sendall(tiny_message)
    need(stream.readline(1024) == tiny_message, 'STOP_TINY_READBACK')
    need(reader_calls == [1] * len(tiny_message), 'STOP_TINY_READER_SEMANTICS')
    probe = {'classification': 'TINY_STRUCTURAL_ONLY_NOT_PERFORMANCE_MEASUREMENT', 'input_bytes': len(tiny_message), 'readinto_calls': len(reader_calls), 'requested_sizes': reader_calls, 'stream_type': type(stream).__name__, 'blocking': left.getblocking(), 'current_probe_SO_SNDBUF': left.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF), 'current_probe_SO_RCVBUF': left.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF), 'historical_actual_socket_buffer_sizes': 'NOT_CAPTURED', 'socket_python_path': socket.__file__, 'socket_python_SHA256': sha(Path(socket.__file__)), 'SocketIO_readinto_source': inspect.getsource(original), 'python_version': sys.version, 'exact_readback': True, 'target_measurement_executed': False}
finally:
    socket.SocketIO.readinto = original; stream.close(); left.close(); right.close()
atomic(OUT, 'tiny_receiver_structure_probe.json', probe)

def backend_ticks(samples):
    ids = {p['pid'] for r in samples for p in r['processes'] if p['role'] == 'backend'}
    return sum(max(p['CPU_user_ticks'] + p['CPU_system_ticks'] for r in samples for p in r['processes'] if p['pid'] == pid) - min(p['CPU_user_ticks'] + p['CPU_system_ticks'] for r in samples for p in r['processes'] if p['pid'] == pid) for pid in ids) / tick_hz

breakdown = []; critical = []; old_bytes = 0
for n, x in enumerate(progress, 1):
    byte_count = x['bytes_IPC'] - old_bytes; old_bytes = x['bytes_IPC']
    pre = x['construct_exclusive_seconds'] + x['hash_exclusive_seconds'] + x['serialization_exclusive_seconds']
    send_start = x['callback_start_monotonic'] + pre
    send_end = send_start + x['socket_send_exclusive_seconds']
    ack_end = send_end + x['ACK_exclusive_seconds']
    samples = [r for r in trace if x['callback_start_monotonic'] <= r['timestamp_monotonic'] <= x['callback_start_monotonic'] + x['callback_inclusive_seconds']]
    send_samples = [r for r in trace if send_start <= r['timestamp_monotonic'] <= send_end]
    ack_samples = [r for r in trace if send_end <= r['timestamp_monotonic'] <= ack_end]
    breakdown.append({'callback_ordinal': n, 'callback': x['payload_class'], 'JSON_IPC_bytes_observed': byte_count, 'construct_seconds': x['construct_exclusive_seconds'], 'hash_bind_seconds': x['hash_exclusive_seconds'], 'serialization_seconds': x['serialization_exclusive_seconds'], 'socket_send_seconds': x['socket_send_exclusive_seconds'], 'ACK_wait_seconds': x['ACK_exclusive_seconds'], 'inclusive_seconds': x['callback_inclusive_seconds'], 'descriptive_send_MBps_decimal': byte_count / x['socket_send_exclusive_seconds'] / 1e6, 'backend_CPU_seconds_inside_callback_sampled_lower_bound': backend_ticks(samples), 'backend_CPU_seconds_inside_inferred_send_window_sampled_lower_bound': backend_ticks(send_samples), 'backend_CPU_seconds_inside_inferred_ACK_window_sampled_lower_bound': backend_ticks(ack_samples), 'timing_scope': 'COMPLETED_CALLBACK_PREFIX_OF_CENSORED_TRIAL', 'throughput_is_network_bandwidth': False})
    critical.append({'callback_ordinal': n, 'callback': x['payload_class'], 'start_relative_seconds': x['callback_start_monotonic'] - start, 'native_pre_send_seconds': pre, 'inferred_send_start_relative_seconds': send_start - start, 'socket_backpressure_interval_seconds': x['socket_send_exclusive_seconds'], 'post_send_ACK_wait_seconds': x['ACK_exclusive_seconds'], 'end_relative_seconds': x['callback_start_monotonic'] + x['callback_inclusive_seconds'] - start, 'backend_overlap': 'Reader overlaps native send; remaining read/decode/evaluate/Writer/Live overlaps ACK wait', 'backend_child_cost': 'UNRESOLVED_NOT_DURABLE', 'window_boundary_method': 'Native start plus measured pre-send spans; tiny unsampled overhead remains', 'backend_times_additive_to_send_ACK': False})
components = {key: sum(x[key] for x in progress) for key in ('callback_inclusive_seconds', 'construct_exclusive_seconds', 'hash_exclusive_seconds', 'serialization_exclusive_seconds', 'socket_send_exclusive_seconds', 'ACK_exclusive_seconds')}
components['send_ACK_inclusive_seconds'] = sum(x['send_ACK_inclusive_seconds'] for x in progress)
need(math.isclose(components['callback_inclusive_seconds'], load(FAILED / 'Q1_partial_span_accounting.json')['completed_callback_inclusive_seconds_sum'], abs_tol=1e-9), 'STOP_SPAN_RECOMPUTATION')
write_csv('TimingQualification_failed_startup_breakdown.csv', breakdown)
write_csv('TimingQualification_callback_critical_path.csv', critical)

# Review the historical attribution exactly. The sensitivity calculation is
# not a changed acceptance metric and never retroactively passes the trial.
def cpu_stats(r):
    v = list(map(int, r['host']['CPU_stat'].split()[1:9])); return sum(v), sum(v) - v[3] - v[4]
intervals = []
for a, b in zip(trace, trace[1:]):
    ta, ba = cpu_stats(a); tb, bb = cpu_stats(b)
    pa = {p['pid']: p['CPU_user_ticks'] + p['CPU_system_ticks'] for p in a['processes']}
    pb = {p['pid']: p['CPU_user_ticks'] + p['CPU_system_ticks'] for p in b['processes']}
    own = sum(max(0, v - pa.get(pid, v)) for pid, v in pb.items())
    new = sorted(set(pb) - set(pa)); lost = sorted(set(pa) - set(pb))
    new_ticks = sum(pb[pid] for pid in new)
    intervals.append({'start_relative_seconds': a['timestamp_monotonic'] - start, 'wall_delta': b['timestamp_monotonic'] - a['timestamp_monotonic'], 'total_host_ticks': tb - ta, 'busy_host_ticks': bb - ba, 'attributed_ticks': own, 'new_PIDs': new, 'new_initial_ticks_omitted': new_ticks, 'lost_PIDs': lost, 'historical_other_fraction': max(0, bb - ba - own) / (tb - ta) if tb > ta else None, 'new_initial_tick_sensitivity_fraction': max(0, bb - ba - own - new_ticks) / (tb - ta) if tb > ta else None})
worst = max(intervals, key=lambda r: r['historical_other_fraction'] or 0)
observer_pids = sorted({p['pid'] for r in outer for p in r['processes']} - {p['pid'] for r in trace for p in r['processes']})
observer_ticks = {str(pid): max(p['CPU_user_ticks'] + p['CPU_system_ticks'] for r in outer for p in r['processes'] if p['pid'] == pid) for pid in observer_pids}
host_review = {'historical_rule_triggered': True, 'historical_threshold_unchanged': .10, 'worst_interval': worst, 'intervals_over_threshold': sum((r['historical_other_fraction'] or 0) > .10 for r in intervals), 'maximum_excluding_new_PID_intervals': max(r['historical_other_fraction'] for r in intervals if not r['new_PIDs'] and r['historical_other_fraction'] is not None), 'whole_trace_tick_residual_fraction_descriptive': max(0, sum(r['busy_host_ticks'] - r['attributed_ticks'] for r in intervals)) / sum(r['total_host_ticks'] for r in intervals), 'inner_attribution_omits_qualification_observer_PIDs': observer_pids, 'observer_CPU_ticks_visible_in_outer_trace': observer_ticks, 'bias_classification': 'CONFIRMED', 'actual_external_load_at_peak': 'UNRESOLVED', 'sensitivity_is_not_revised_acceptance': True, 'caveats': ['New PID initial ticks need process birth/starttime and aligned sampling before subtracting them as exact interval work', 'Disappearing processes can lose final ticks', 'Host CPU snapshot is collected after sequential process samples', 'Watchdog/coordinator CPU is not external user workload but is omitted from inner own attribution', 'Linux /proc/io rchar/syscr are file-I/O counters; do not infer socket byte/syscall counts from them'], 'future_method': 'Track (PID,starttime), observer and all registered groups; persist final waited CPU or bounded exit attribution; timestamp/bracket samples and report uncertainty. Keep 10percent threshold; formally review metric changes.'}
atomic(OUT, 'host_attribution_review.json', host_review)

# Retained real static blobs provide byte reconstruction; complete wire messages
# were not retained, so avoid calling this an instrumented wire-size measurement.
blob_values = {Path(name).stem.removeprefix('immutable_'): packed.decode(raw(name)) for name in artifacts if name.startswith('runtime/immutable_')}
initial = packed.decode(raw('runtime/initial_state.bin'))
geo_id = initial['geometry']['$immutable']; volume_id = initial['volumes']['$immutable']
geo_bytes = len(oe.canonical(blob_values[geo_id]).encode()); volume_bytes = len(oe.canonical(blob_values[volume_id]).encode())
cv_value = next(v for key, v in blob_values.items() if isinstance(v, list) and len(v) == 25600 and all(x == 2 for x in v))
g_value = next(v for key, v in blob_values.items() if isinstance(v, list) and len(v) == 3 and all(x == 0 for x in v))
cv_bytes = len(oe.canonical(cv_value).encode()); g_bytes = len(oe.canonical(g_value).encode())
static_total = 4 * (2 * (geo_bytes + volume_bytes) + cv_bytes + g_bytes)
distinct_static = geo_bytes + volume_bytes + cv_bytes + g_bytes
redundant_static_value_bytes = static_total - distinct_static
redundant_fraction = redundant_static_value_bytes / progress[-1]['bytes_IPC']
static_review = {'status': 'CONFIRMED', 'method': 'Source-proven occurrence counts times canonical bytes of actual retained immutable values; native/canonical codec equivalence is frozen and covered by original tests', 'canonical_geometry_value_bytes': geo_bytes, 'canonical_volume_value_bytes': volume_bytes, 'canonical_Cv_value_bytes': cv_bytes, 'canonical_g_value_bytes': g_bytes, 'geometry_occurrences_in_four_packets': 8, 'volume_occurrences_in_four_packets': 8, 'Cv_occurrences': 4, 'g_occurrences': 4, 'reconstructed_static_value_bytes_prefix': static_total, 'distinct_static_value_bytes': distinct_static, 'redundant_static_value_bytes_lower_bound': redundant_static_value_bytes, 'redundant_static_value_fraction_lower_bound': redundant_fraction, 'intra_message_duplicate_geometry_volume_value_bytes': 4 * (geo_bytes + volume_bytes), 'denominator_observed_prefix_IPC_bytes': progress[-1]['bytes_IPC'], 'full_message_redundancy_fraction': 'UNRESOLVED_RAW_MESSAGES_NOT_RETAINED', 'omissions': ['Repeated JSON keys and delimiters', 'Patch metadata', 'Duplicate dynamic fields and oldTime content', 'Additional matrix owner/neighbour/volume repeats in unmeasured classes'], 'no_transport_optimization_implemented': True, 'no_removal_of_required_hashes': True, 'no_linear_wall_time_saving_claim': True}
atomic(OUT, 'static_value_byte_reconstruction.json', static_review)
payload_rows = [
    {'category': 'mesh topology / owner-neighbour / interpolation weights', 'classification': 'SOURCE_STATIC', 'transport': 'geometry in nested native_state_epoch and top-level control fields; owner/neighbour also in matrix slots later', 'observed_basis': 'Retained actual immutable geometry + accepted prefix + fixture source', 'canonical_value_bytes': geo_bytes, 'prefix_occurrences': 8, 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Retain exact identity/change detection and restore every scientific packet'},
    {'category': 'cell volumes', 'classification': 'SOURCE_STATIC', 'transport': 'Nested and top-level state; matrix volumes later', 'observed_basis': 'Retained actual immutable volume blob', 'canonical_value_bytes': volume_bytes, 'prefix_occurrences': 8, 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Exact content identity; reject static changes before accepting evidence'},
    {'category': 'Cv / g', 'classification': 'FROZEN_CONSTANT_PROPERTIES_IN_THIS_CASE', 'transport': 'thermal_context each callback', 'observed_basis': 'Retained actual immutable blobs', 'canonical_value_bytes': cv_bytes + g_bytes, 'prefix_occurrences': 4, 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Do not assume other thermophysical cases constant'},
    {'category': 'patch names/types/addressing', 'classification': 'PARTLY_STATIC', 'transport': 'State patches and matrix patches; values and update/manipulation flags dynamic', 'observed_basis': 'Source schema; wire subtrees not fully retained', 'canonical_value_bytes': 'UNRESOLVED', 'prefix_occurrences': 'SOURCE_DEPENDENT', 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Separate immutable topology from changing BC state'},
    {'category': '10 fields / oldTime arrays', 'classification': 'DYNAMIC_SCIENTIFIC_STATE', 'transport': 'Native state and copied inline fields or state alias; matrix psi later', 'observed_basis': 'Accepted target prefix and source copies; constant fixture does not make physical fields static', 'canonical_value_bytes': 'UNRESOLVED', 'prefix_occurrences': 'DUPLICATE_STATE_REPRESENTATIONS', 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Full epoch, BC, oldTime and P1 lossless reconstruction required'},
    {'category': 'matrix coefficients / explicit terms', 'classification': 'DYNAMIC', 'transport': 'Up to 3 matrix slots per callback plus term arrays', 'observed_basis': '42-class taxonomy / 701 packets; no matrix acknowledged in failed run', 'canonical_value_bytes': 'UNRESOLVED', 'prefix_occurrences': 0, 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'Preserve every matrix slot, action, epoch and replay result'},
    {'category': 'stage scalars / hashes / provenance', 'classification': 'DYNAMIC_IDENTITY_WITH_PINNED_COMPONENTS', 'transport': 'Every callback identity and timing/loop metadata', 'observed_basis': 'Source and native counters', 'canonical_value_bytes': 'UNRESOLVED', 'prefix_occurrences': 4, 'full_message_byte_fraction': 'UNRESOLVED', 'future_equivalence_requirement': 'No hash removal; equality includes order and all folded identities'},
]
write_csv('TimingQualification_payload_static_dynamic_review.csv', payload_rows)

nodes = graph(); representatives = {}
for r in nodes[1:]:
    representatives.setdefault((r['metadata']['stage'], r['payload'].get('term', '')), r)
cfg = plan(); taxonomy = []; control_byte_mean = statistics.mean(r['JSON_IPC_bytes_observed'] for r in breakdown[1:]); base = control_byte_mean / 2
inline_exclusions = {'term_capture', 'energy_unrelaxed_assembly', 'energy_after_relax', 'energy_after_solve', 'mass_unrelaxed_assembly', 'mass_after_solve', 'pressure_pre_reference', 'pressure_post_reference', 'pressure_solved'}
for c in cfg['callback_classes']:
    key = (c['callback_type'], c['term']); r = representatives[key]
    copies = 1 + int('state' in r['payload']) + int(c['callback_type'] not in inline_exclusions)
    mats = c['matrix_packets_per_callback']; zero_arrays = int('integrated_cells' in r['payload']) + len(r['payload'].get('term_actions', {}))
    measured = c['callback_type'] in {'preSolve_before', 'preSolve_after', 'controller_complete'}
    estimates = {}
    for scenario, factor, matrix_bytes in [('lower_shape_assumption', .7, 500000), ('central_shape_assumption', 1., 1500000), ('conservative_shape_assumption', 1.4, 3000000)]:
        estimates[scenario] = control_byte_mean if measured else copies * base * factor + mats * matrix_bytes + zero_arrays * (2 * 25600 + 1)
    taxonomy.append({'callback': c['callback_type'], 'term': c['term'], 'frequency': c['frequency_per_step'], 'matrix_packets_per_callback': mats, 'state_copy_shapes': copies, 'explicit_zero_array_shapes': zero_arrays, 'measurement_status': 'MEASURED_SINGLE_COMPLETED_PREFIX_CALLBACK' if measured else 'UNMEASURED_TARGET_CLASS', 'observed_JSON_IPC_bytes': next(x['JSON_IPC_bytes_observed'] for x in breakdown if x['callback'] == c['callback_type']) if measured else 'UNRESOLVED', **{k + '_bytes': v for k, v in estimates.items()}, 'model_label': 'SOURCE_SHAPE_WHAT_IF_NOT_MEASURED_PAYLOAD_OR_RUNTIME_BOUND'})
need(len(taxonomy) == 42 and sum(r['frequency'] for r in taxonomy) == 1144 and sum(r['frequency'] * r['matrix_packets_per_callback'] for r in taxonomy) == 701, 'STOP_TAXONOMY_COUNTS')
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(taxonomy[0])); w.writeheader(); w.writerows(taxonomy); textfile(OUT, 'callback_taxonomy_model.csv', buf.getvalue())
prefix_rate = components['callback_inclusive_seconds'] / progress[-1]['bytes_IPC']
trial_trace_rate = artifacts['resource_trace.jsonl']['bytes'] / trial['wall_seconds']
stage_wall = load(FAILED / 'Q1/stage_result.json')['wall_seconds']
outer_trace_rate = (FAILED / 'Q1/resource_trace.jsonl').stat().st_size / stage_wall
trace_rate = trial_trace_rate + outer_trace_rate
accounting = load(FAILED / 'Q1/stage_result.json')['Q1_accounting']
trace_headroom = accounting['manifest_trace_reserve_bytes'] + accounting['registered_scratch_bytes'] - accounting['maximum_simultaneous_bytes']
budget_rows = [{'scenario': 'observed_censored_lower_information', 'scope': 'FAILED_STARTUP_TRIAL', 'model_IPC_bytes': progress[-1]['bytes_IPC'], 'modeled_callback_seconds': components['callback_inclusive_seconds'], 'trial_seconds': '>30 ACTIVE_UNFINISHED_AT_FROZEN_DEADLINE', 'full_stage_seconds': 'UNRESOLVED', 'projected_raw_trace_bytes': 'NOT_A_FULL_STAGE_PROJECTION', 'completion_guarantee': False, 'unmeasured_cost': '1141 physical callbacks, 701 matrix packets, audit, selected events, finalization', 'basis': 'ACTUAL_COMPLETED_PREFIX_AND_CENSORED_TRIAL'}]
model_results = []
for scenario in ('lower_shape_assumption', 'central_shape_assumption', 'conservative_shape_assumption'):
    bytes_model = breakdown[0]['JSON_IPC_bytes_observed'] + sum(r['frequency'] * r[scenario + '_bytes'] for r in taxonomy)
    seconds = breakdown[0]['inclusive_seconds'] + sum(r['frequency'] * r[scenario + '_bytes'] * prefix_rate for r in taxonomy)
    stage_seconds = 4 * seconds
    row = {'scenario': scenario, 'scope': 'ONE_FULL_STARTUP_SOURCE_SHAPE_WHAT_IF', 'model_IPC_bytes': bytes_model, 'modeled_callback_seconds': seconds, 'trial_seconds': 'UNRESOLVED_TOTAL_COMPLETION_BUDGET', 'full_stage_seconds': stage_seconds, 'projected_raw_trace_bytes': stage_seconds * trace_rate, 'completion_guarantee': False, 'unmeasured_cost': 'Matrix replay/term synchronization, class-specific hashes, full startup audit, selected writes, finalization, 3 OFF framework costs, observer persistence; may invalidate linear byte-cost model', 'basis': '42_FREQUENCIES_AND_COPY_SHAPES_PLUS_ASSUMED_MATRIX_BYTES_AND_PREFIX_BYTE_NORMALIZATION_NOT_CLASS_TIMINGS'}
    budget_rows.append(row); model_results.append(row)
for case, cap, stage_cap in [('lower_finite_scout', 60, 90), ('central_finite_scout', 90, 150), ('conservative_finite_scout', 120, 180)]:
    budget_rows.append({'scenario': case, 'scope': 'FUTURE_SEPARATE_FOUR_CONTROL_CALLBACK_OBSERVABILITY_SCOUT_ONLY', 'model_IPC_bytes': progress[-1]['bytes_IPC'], 'modeled_callback_seconds': components['callback_inclusive_seconds'], 'trial_seconds': cap, 'full_stage_seconds': stage_cap, 'projected_raw_trace_bytes': stage_cap * trace_rate, 'completion_guarantee': False, 'unmeasured_cost': 'New observer overhead and load; not the original full startup Q1 sample', 'basis': '26.84s_PREFIX_PLUS_SETUP_AND_FINITE_MARGIN_PROPOSAL_ONLY_NOT_REGISTERED'})
write_csv('TimingQualification_budget_revision_model.csv', budget_rows)
budget_review = {'current_Q1_trial_seconds': 30, 'current_Q1_stage_seconds': 300, 'new_budgets_registered': False, 'recommended_complete_Q1_trial_seconds': 'UNRESOLVED', 'recommended_complete_Q1_stage_seconds': 'UNRESOLVED', 'model_basis': 'MEASURED_PREFIX_PLUS_MODEL', 'measured_target_classes': 3, 'unmeasured_target_classes': 39, 'constructor_measured_once_separately': True, 'taxonomy_callbacks': 1144, 'taxonomy_matrix_packets': 701, 'shape_assumptions': {'state_copy_base_bytes': base, 'reason': 'Half of measured two-state-copy control packet, including envelope uncertainty; not isolated state measurement', 'state_factors': [.7, 1., 1.4], 'matrix_slot_assumed_bytes': [500000, 1500000, 3000000], 'term_array_assumed_bytes': 2 * 25600 + 1, 'cost_per_byte_proxy_seconds': prefix_rate, 'proxy_warning': 'Controls only, host rule triggered; not stable coefficient for all classes', 'missing_class_specific_backend_work': 'UNRESOLVED'}, 'conditional_models': model_results, 'observed_trial_trace_bytes_per_second': trial_trace_rate, 'observed_outer_trace_bytes_per_second': outer_trace_rate, 'combined_descriptive_trace_bytes_per_second': trace_rate, 'current_trace_metadata_reserve_bytes': accounting['manifest_trace_reserve_bytes'], 'registered_Q1_scratch_bytes': accounting['registered_scratch_bytes'], 'accounted_max_simultaneous_bytes': accounting['maximum_simultaneous_bytes'], 'unused_accounting_slack_bytes': accounting['registered_scratch_bytes'] - accounting['maximum_simultaneous_bytes'], 'trace_plus_unused_slack_bytes': trace_headroom, 'trace_reserve_only_duration_at_observed_rate_seconds': accounting['manifest_trace_reserve_bytes'] / trace_rate, 'trace_plus_slack_duration_at_observed_rate_seconds': trace_headroom / trace_rate, 'longer_trial_alone_is_safe': False, 'full_campaign_model_is_production_runtime_projection': False, 'finite_scout_proposals': [{'trial_seconds': x, 'stage_seconds': y, 'scope': 'FOUR_CONTROL_CALLBACK_OBSERVABILITY_ONLY_NOT_FULL_Q1', 'registered': False} for x, y in ((60, 90), (90, 150), (120, 180))], 'preregistration_requirements': ['Class-size/cost screening with timeout-safe spans', 'Reconcile longer raw-trace/file/metadata accounting or approve lossless representation compaction', 'Account observer work and fixture/setup/three OFF trials plus all ON finalizations', 'Keep hard AS/RSS/host/storage guards and independent process-group supervisor', 'Issue a new plan/hash/harness/readiness/authorization and qualification ID; never resume failed archive'], 'no_automatic_timeout_doubling': True}
atomic(OUT, 'budget_model.json', budget_review)

options = [
    {'option': 'A finite budget extension', 'expected_benefit': 'More completion time; does not reduce bytewise reader or multi-MB repeated cost', 'scientific_semantics': 'None if graph/evaluator unchanged', 'evidence_semantics': 'Longer trace and retention/file accounting require new proof', 'difficulty': 'LOW_CODE_MEDIUM_PROTOCOL', 'verification': 'Budget/prerequisites/trace reserve/whole-stage STOP cases', 'risk': 'HIGH_IF_USED_ALONE', 'decision': 'Insufficient as sole change; full completion cap UNRESOLVED'},
    {'option': 'B durable backend observability', 'expected_benefit': 'Separate receive/decode/canonical/replay/pack/hash/persistence for acknowledged callbacks after timeout', 'scientific_semantics': 'None with wrappers only', 'evidence_semantics': 'New qualification-only ledger; ACK ordering stays after scientific work plus ledger commit', 'difficulty': 'MEDIUM', 'verification': 'Tiny timeout/SIGKILL/tail/corruption/quota/observer overhead regressions', 'risk': 'MEDIUM_OBSERVER_EFFECT', 'decision': 'REQUIRED; design supplied, not implemented'},
    {'option': 'C0 bounded buffered line receive', 'expected_benefit': 'Amortize millions of 1-byte receive calls; complete framing and processing-before-ACK remain', 'scientific_semantics': 'Intended unchanged; frozen backend currently uses same bytewise reader', 'evidence_semantics': 'Must preserve exact bytes, limit/newline/truncation/ACK failure and record order', 'difficulty': 'LOW_TO_MEDIUM_IMPLEMENTATION_MEDIUM_REVIEW', 'verification': 'Tiny segmentation/partial send/overflow/FINISH/ACK/deadlock and scientific full regression', 'risk': 'MEDIUM_UNTIL_EQUIVALENCE', 'decision': 'FIRST architecture revision candidate; no change now'},
    {'option': 'C static references / delta transport', 'expected_benefit': 'Reduce confirmed repeated static value bytes; >=45.95percent prefix byte accounting is redundant', 'scientific_semantics': 'Fields stay dynamic; exact identity and restored content required', 'evidence_semantics': 'Dictionary lifetime, change rejection, provenance and P1 lossless replay need new authority', 'difficulty': 'HIGH', 'verification': 'All class/history/BC/hash round trips plus missing/corrupt/static-changed references', 'risk': 'HIGH', 'decision': 'Future option; no performance saving promised'},
    {'option': 'D batch callbacks', 'expected_benefit': 'Potentially amortize transfer/serialization overhead; not measured', 'scientific_semantics': 'Stage-order and failure boundary risk', 'evidence_semantics': 'ACK/atomic retention boundary changes', 'difficulty': 'HIGH', 'verification': 'Intermediate failures, prefix evidence, ordering and finite buffer proof', 'risk': 'HIGH', 'decision': 'Defer'},
    {'option': 'E binary transport', 'expected_benefit': 'Potentially avoid recursive text formatting and copies; not measured', 'scientific_semantics': 'IEEE/epoch/BC/oldTime exact equivalence required', 'evidence_semantics': 'New schema and hash-domain/versioning', 'difficulty': 'HIGH', 'verification': 'Every shape/class/matrix slot plus hashes and signed zero', 'risk': 'HIGH', 'decision': 'Defer'},
    {'option': 'F asynchronous backend', 'expected_benefit': 'Could overlap driver and backend; serial backend work still remains', 'scientific_semantics': 'Non-invasiveness/failure boundaries need review', 'evidence_semantics': 'Bounded queue, durable completion and backpressure become explicit', 'difficulty': 'VERY_HIGH', 'verification': 'No loss/reordering/unstable overwrite; process crash and high-water tests', 'risk': 'VERY_HIGH', 'decision': 'Defer'},
]
write_csv('TimingQualification_architecture_options.csv', options)
observability = {'implemented': False, 'qualification_side_only': True, 'scientific_and_production_sources_unchanged': True, 'next_design': {'location': 'Future qualification instrumentation around current backend; never edit v1_4 in this task', 'durability_boundary': 'Commit bounded per-callback aggregate receipt before ACK; native completed progress remains an independent ACK-delivery witness', 'receipt_fields': ['qualification/stage/trial/sequence/class/payload SHA', 'native/backend PID and original packet identity', 'receive/decode/canonical/replay/packing/hash/persistence/ACK-preparation inclusive/exclusive tree', 'bytes/counters and phase timestamps', 'previous receipt hash and record hash', 'measurement observer overhead and accounting coverage'], 'bounds': {'per_receipt_max_bytes': 65536, 'chunk_max_bytes': 67108864, 'Q1_callback_receipts_max': 1145, 'Q1_ledger_bytes_upper': 1145 * 65536, 'Q1_ledger_chunks_max': 2, 'Q1_extra_files_model': 3, 'Q1_existing_layout_upper': 111, 'Q1_proposed_layout_with_ledger_before_trace_revision': 114}, 'inflight_marker': 'Bounded qualification-only phase marker for next expected callback; never a scientific completed receipt', 'kill_policy': 'No SIGTERM-only reliance: durable completed prefix survives SIGKILL; incomplete tail is invalid, bounded and retained', 'fail_closed': 'Ledger hash/quota/fsync failure prevents success ACK and stops the campaign; reserved STOP evidence remains', 'overhead': 'MEASUREMENT_OBSERVER_OVERHEAD named separately; measure aggregate/encode/hash/write/sync and persist preceding completed publication costs. Final self-publication sync cannot be self-timed in its own receipt; disclose coverage and include external ACK wall, never invent zero.', 'no_per_byte_timer_wrapper': 'Time readline as one receive span; per-byte Python wrappers would materially change a millions-call path', 'periodic_checkpoint_tradeoff': 'Periodic-only K callbacks may lose up to K acknowledged callbacks. Optional batching is acceptable only after new protocol formally permits that bounded loss; it does not meet all-completed-callback durability by itself.'}, 'required_tiny_acceptance': ['Original46 regression unchanged', 'Completed data + SIGTERM/SIGKILL mid-next callback', 'Partial ledger write/chain corruption/record ordering/readback', 'Near-byte/file reserve and ledger failure before ACK', 'Exact payload content/graph/persistence invariance', 'Instrumentation enabled/disabled tiny paired overhead accounting (not target performance)', 'Finalization with no reliance on final backend_result.json'], 'why_not_implemented_now': 'Bytewise receive is also present in frozen production-like v1_4/server.py; the minimal meaningful next change requires a separate compute/equivalence review. This task supplies the observer design without altering the active hash-pinned backend or claiming new readiness.'}
atomic(OUT, 'timeout_safe_observability_design.json', observability)

request = Path('/home/mirai/.codex/attachments/f1202802-fe64-4400-a058-c68d0707917e/貼り付けたテキスト.txt').read_text()
keys = re.findall(r'^([A-Z][A-Z0-9_]+)\s*=\s*$', request.split('# 102. REQUIRED FINAL STATUS')[1].split('# 103.')[0], re.M)
status = {key: 'UNRESOLVED' for key in keys}
status.update({'ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION_FIX_REVIEW': 'COMPLETE', 'FAILED_QUALIFICATION_ID': FAILED_ID, 'FAILED_CAMPAIGN_HASH_VERIFIED': 'YES', 'FAILED_CAMPAIGN_EVIDENCE_INTACT': 'YES', 'CANONICAL_AUTHORITY_HASH_VERIFIED': 'YES', 'FORMAL_AUTHORITY_HASH_VERIFIED': 'YES', 'RUNTIME_AUTHORITY_COMPATIBILITY': 'PASS', 'Q1_STOP_REASON': 'STOP_WALL_TIME', 'Q1_COMPLETED_CALLBACKS': 4, 'Q1_COMPLETED_MATRIX_PACKETS': 0, 'Q1_COMPLETED_PREFIX_IPC_BYTES': 21038037, 'Q1_COMPLETED_CALLBACK_INCLUSIVE_SECONDS': components['callback_inclusive_seconds'], 'Q1_NATIVE_CONSTRUCT_SECONDS': components['construct_exclusive_seconds'], 'Q1_NATIVE_HASH_SECONDS': components['hash_exclusive_seconds'], 'Q1_NATIVE_SERIALIZATION_SECONDS': components['serialization_exclusive_seconds'], 'Q1_SOCKET_SEND_SECONDS': components['socket_send_exclusive_seconds'], 'Q1_ACK_WAIT_SECONDS': components['ACK_exclusive_seconds'], 'SOCKET_BACKPRESSURE_HYPOTHESIS': 'SUPPORTED', 'BACKEND_PROCESSING_DOMINANCE': 'SUPPORTED', 'BACKEND_DETAILED_SPANS_DURABLE_ON_TIMEOUT': 'NO', 'OBSERVABILITY_LIMITATION_CONFIRMED': 'YES', 'STARTUP_FULL_AUDIT_STARTED_BEFORE_TIMEOUT': 'NO', 'STARTUP_FULL_AUDIT_PRIMARY_CAUSE': 'NO', 'STATIC_PAYLOAD_REDUNDANCY': 'CONFIRMED', 'STATIC_PAYLOAD_REDUNDANCY_FRACTION': redundant_fraction, 'HOST_STABILITY_RULE_TRIGGERED': 'YES', 'HOST_STABILITY_METRIC_BIAS': 'CONFIRMED', 'OBSERVABILITY_FIX_REQUIRED': 'YES', 'OBSERVABILITY_FIX_IMPLEMENTED': 'NO', 'OBSERVABILITY_FIX_TINY_TESTS': 'NOT_APPLICABLE', 'TIMING_PROTOCOL_BUDGET_REVISION_REQUIRED': 'YES', 'CURRENT_Q1_TRIAL_BUDGET_SECONDS': 30, 'CURRENT_Q1_STAGE_BUDGET_SECONDS': 300, 'RECOMMENDED_BUDGET_BASIS': 'MEASURED_PREFIX_PLUS_MODEL', 'DIAGNOSTIC_ARCHITECTURE_REVISION_REQUIRED': 'YES', 'Q2_GATE_REVISION_INFORMATION_VALUE': 'HIGH', 'ROOT_CAUSE_CLASSIFICATION': 'MULTIPLE', 'NEXT_SINGLE_TASK': 'PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_DIAGNOSTIC_COMPUTE_REVISION', 'RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK': 'gpt-6.1-sol / high', 'USER_DECISION_REQUIRED': 'YES'})
for key in ('Q1_FAILURE_REPRODUCED', 'Q1_RETRY_EXECUTED', 'Q2_EXECUTED', 'Q3_EXECUTED', 'CFD_EXECUTED', 'Q2_GATE_CHANGED', 'DIAGNOSTIC_TRANSIENT_RESOURCE_READY', 'EXECUTION_AUTHORIZED', 'FORMAL_GATE_J_CURRENTLY_ALLOWED', 'Q3_BOUNDED_CFD_QUALIFICATION_RECOMMENDED', 'U01_CHANGED', 'U02_CHANGED', 'U03_CHANGED', 'U04_EQUATION_SEMANTICS_CHANGED', 'PERSISTENCE_POLICY_CHANGED', 'FORMAL_CRITERIA_CHANGED', 'HISTORICAL_STATUS_CHANGED'):
    status[key] = 'NO'
need(set(keys) == set(status), 'STOP_STATUS_KEYS')
status = {key: status[key] for key in keys}
textfile(OUT, 'required_final_status.txt', '\n'.join(key + ' = ' + str(v) for key, v in status.items()) + '\n')
source_refs = {}
for filename, patterns in {'backend.py': ['makefile', 'readline', 'def ack', 'def save', 'writer.accept', 'live.accept'], 'native_adapter.C': ['void rehash', 'void bind', 'void sendall', 'std::string ack', 'if(on)'], 'spans.py': ['def flush', 'self.nodes=[]'], 'fixture.py': ['for stage in', "if 'state'", 'p.update(current)'], 'analysis.py': ['own=sum'], 'watchdog.py': ['tree=descendants', 'snapshot=host']}.items():
    lines = (HERE / filename).read_text().splitlines(); source_refs[filename] = [{'line': i + 1, 'text': line} for i, line in enumerate(lines) if any(pattern in line for pattern in patterns)]
report = {'schema': 'routeA_nonCFD_failed_qualification_review/1', 'task': 'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION', 'status': 'COMPLETE', 'HEAD': guard['HEAD'], 'generated_UTC': datetime.now(timezone.utc).isoformat(), 'failed_qualification_id': FAILED_ID, 'required_final_status': status, 'authority': authority_receipt, 'failed_evidence': {'all_49_files_SHA_and_mtime_unchanged': True, 'campaign_manifest_pin_verified': True, 'stage_manifest_verified': True, 'archive_chain_and_artifacts_verified': True, 'archive_partial_tail': False, 'required_reads': read_receipt}, 'completed_prefix': {'native_components_recomputed': components, 'callback_rows': breakdown, 'critical_paths': critical, 'actual_IPC_prefix_bytes': 21038037, 'native_send_plus_ACK_fraction_of_completed_callback_wall': components['send_ACK_inclusive_seconds'] / components['callback_inclusive_seconds'], 'backend_CPU_inside_callback_windows_sampled_lower_bound': sum(r['backend_CPU_seconds_inside_callback_sampled_lower_bound'] for r in breakdown), 'ACK_includes_backend_and_is_not_additive': True}, 'socket_semantics': {'blocking': True, 'native_send': 'send remaining complete serialized line until all bytes sent; no application chunk size or nonblocking queue', 'framing': 'One newline-terminated JSON record; ACK newline response after processing', 'buffer_settings_in_source': 'No setsockopt override; inherited defaults, historical values not measured', 'receiver': 'Unbuffered SocketIO.readline; tiny installed-implementation probe confirms one recv_into per byte', 'callbacks_concurrent': False, 'receive_vs_process': 'Read entire current message, decode/evaluate/Writer/Live, ACK, then receive next; no prefetch/asynchronous receiver', 'backpressure': 'SUPPORTED: millions of bytewise receives and backend CPU-bound drain overlap native blocking send; this is not an AF_UNIX bandwidth measurement', 'production_like_source': 'Frozen v1_4/server.py uses the same buffering=0 + readline path', 'probe': probe, 'actual_receive_syscall_count_measured': False}, 'native_hash_inventory': {'hash_span_is_crypto_only': False, 'contents': ['Recursive rehash of fields and oldTime value/object identities', 'State/payload epoch serializations', 'Matrix coefficient identities in unmeasured packets', 'BC hash map and payload SHA; Json deep copies and repeated dump are inside this block'], 'estimated_SHA_calls_from_four_control_shapes': {'constructor': 33, 'each_other_control': 57}, 'inventory_method': 'Source count: two state representations, 10 value hashes each, constructor0/others6 oldTime objects per state with two hashes each, two state_epoch identities, ten BC hashes, one payload hash. Not runtime crypto-call instrumentation.', 'same_content_rehash_confirmed_source': 'Duplicated inline/native state is visited separately; hash identities still required and unchanged', 'unmeasured_crypto_vs_formatting_fraction': 'UNRESOLVED', 'removed_hashes': 0}, 'serialization': {'native_JSON_type': 'std::map/std::vector value ownership', 'float_format': 'setprecision(17)', 'string_strategy': 'Recursive ostringstream per subtree then parent copies emitted text; no static/delta references', 'deep_copies': ['Json::push(const Json&) copies subtree', 'identity creates Json x=j and erases identity key', 'bind constructs field/oldTime/BC/matrix epoch maps', 'matrix coefficient hash selection copies arrays'], 'native_parse_metric_scope': 'Parse received fixture JSON; excludes Python fixture generation and stdin wait before callback_start', 'native_driver_fixture_time': 'Only partial sampled CPU / gaps; not fully decomposed'}, 'startup': {'planned_first_four': [x['payload_class'] for x in progress], 'next_source_order_callback': nodes[4]['metadata']['stage'], 'next_actual_phase': 'UNRESOLVED', 'tail_evidence': 'After controller ACK, native CPU and stdin rchar rise while backend CPU/rchar remain constant; consistent with fifth time_start pre-send preparation, not a published backend stage entry', 'full_audit_started': False, 'proof': 'Writer creates spool first at physical time_start after schedule.begin; four control stages excluded; archive contains no full_audit.scratch/full_*.bin and no branch deletes such a spool on STOP', 'full_audit_primary_cause': False}, 'static_dynamic': static_review, 'host': host_review, 'memory': {'partial_prefix_only': True, 'observed_combined_RSS_bytes': 596127744, 'memory_guard_violation_observed': False, 'selected_U03_audit_memory_not_qualified': True, 'feasibility': 'UNRESOLVED'}, 'budget': budget_review, 'observability': observability, 'options': options, 'Q2_gate_review': {'changed': False, 'information_value': 'HIGH', 'recommended_review': 'Separate diagnostic-only primitive/receiver substage from full Q2 acceptance; isolated U03 is safe in resource-only histories but secondary to startup cause', 'mandatory_future_boundaries': ['New formally reviewed scope/name/prerequisites/authority', 'No Q3/production/time advance', 'Hash-pinned unchanged algorithm and exact payload classes', 'Finite one-shot stage/trial/AS/RSS/storage guards, new ID/auth', 'Isolated diagnostic results never become Q1/Q2 full-stage PASS'], 'execution_now': False}, 'root_cause': {'classification': 'MULTIPLE', 'stop_trigger': 'Finite30s operational cap', 'supported_execution_cost': 'Synchronous bytewise backend receive/backpressure plus post-send evaluation/retention work and native bind/hash formatting', 'diagnosis_limitation': 'Backend child span aggregates remained in RAM and were never durably published', 'external_host_instability_primary_cause': 'UNRESOLVED_NOT_ESTABLISHED', 'budget_alone_sufficient': False, 'production_infeasible_proved': False}, 'source_refs': source_refs, 'regression': {'original_tests': 46, 'status': 'PASS', 'source_unchanged': True, 'observability_fix_tests': 'NOT_APPLICABLE_NO_CODE_FIX', 'tiny_receiver_probe': 'PASS', 'actual_Q1_Q2_campaigns_in_this_task': 0}, 'invariance': {'callback_graph_1144_unchanged': True, 'matrix_graph_701_unchanged': True, 'all_scientific_and_current_harness_sources_unchanged': True, 'production_persistence_unchanged': True, 'plan_and_readiness_unchanged': True, 'failed_campaign_unchanged': True, 'Q2_gate_unchanged': True, 'capacity_estimates_unchanged': True, 'formal_status_preserved': {'ALL_ROUTE_A_GATE_F': 'FAIL', 'ALL_RA_NEEDS_320': 'YES', 'FORMAL_GATE_J_EXECUTED': 'NO', 'FORMAL_GATE_J_PASS': 'NOT_EVALUATED', 'BENCHMARK_CORE_PASS': 'NO', 'ROUTE_A_CHARACTERIZED': 'NO', 'GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED': 'NO', 'DOWNSTREAM_TRANSIENT_READY': 'NO', 'PARTICLE_COUPLING_READY': 'NO'}, 'git_add_commit_push_executed': False}}
atomic(PREP, 'DiagnosticTransient_nonCFD_timing_qualification_fix_review.json', report)

callback_table = '\n'.join(f"| {r['callback']} | {r['JSON_IPC_bytes_observed']} | {r['construct_seconds']:.4f} | {r['hash_bind_seconds']:.4f} | {r['serialization_seconds']:.4f} | {r['socket_send_seconds']:.4f} | {r['ACK_wait_seconds']:.4f} | {r['inclusive_seconds']:.4f} | {r['descriptive_send_MBps_decimal']:.3f} |" for r in breakdown)
model_table = '\n'.join(f"| {r['scenario']} | {r['model_IPC_bytes']/1e9:.3f} GB | {r['modeled_callback_seconds']/3600:.2f} h + unknown | {r['full_stage_seconds']/3600:.2f} h + unknown | {r['projected_raw_trace_bytes']/2**30:.2f} GiB |" for r in model_results)
md = f'''# Diagnostic transient non-CFD timing qualification fix review

## 1. Executive summary

**COMPLETE。根本原因分類はMULTIPLE。** 30秒で停止した直接のresource triggerはtrial capだが、4 callbackの{components['callback_inclusive_seconds']:.6f}秒をbudget artifactだけで片付けることはできない。同期backendのbytewise受信によるsend backpressureと、ACK前のbackend処理、native bind/hash中の再serializationが実行costとして支持される。backend CPUは4 callback内だけでも約{sum(r['backend_CPU_seconds_inside_callback_sampled_lower_bound'] for r in breakdown):.2f}秒で、receiveを含むbackend pathの支配が支持される。具体的なcanonicalization/replay/packing/hash/fsyncの内訳は未保存でUNRESOLVED。

独立した判断は **OBSERVABILITY_FIX_REQUIRED=YES、TIMING_PROTOCOL_BUDGET_REVISION_REQUIRED=YES、DIAGNOSTIC_ARCHITECTURE_REVISION_REQUIRED=YES**。architecture revisionはまずbytewise receiveを対象とした同等性レビューを勧めるもので、scientific definition変更ではない。今回はread-only分析とtiny structural probe、既存46件のtiny regressionのみ実施し、active実装・plan・gate・予算を変更しなかった。Q1/Q2再測定・CFDは実施していない。

## 2. Authority/hash verification

HEAD `{guard['HEAD']}` は指定値と一致。diagnostic v1.5 SHA `{sha(CONTRACT)}`、formal v1.7 SHA `{sha(ROOT / 'docs/routeA_execution_contract_v1.7.json')}` は期待値と一致。runtime compatibility／active harness verifyはPASS。開始前・終了時のsource/artifact hash snapshotを保存し、v1.4・v1.5 runtime・1144/701 graph・plan・readiness・production persistenceを変更していない。

## 3. Failed campaign integrity

`{FAILED_ID}` の49個すべてのfileのSHA・size・mtimeを開始前pinと照合。campaign manifestをfinal_verificationのSHAへ結び、stage manifest、trial archive chain、全21 trial artifactをreadbackした。uncommitted tailはない。指定された12 artifactをすべて読み、historical STOPPED statusもdirectoryも変更していない。再実行・追加許可receipt・purgeはない。

## 4. Timeline of the 30-second startup

trial startを0秒とすると、constructor開始2.164648秒、完了9.610559秒、preSolve_before完了16.170788秒、preSolve_after完了22.687798秒、controller_complete完了29.219309秒。30秒のdeadlineを迎えた後のcleanupを含むexternal wallは30.062141秒。stage wall32.404773秒はarchive移行／summary等も含み、30秒すべてが診断callback workではない。Python fixture生成・stdin待ち等はnative callback_startの前であり、construct spanの0.4127秒に含まれない。

次のsource-order callbackは `time_start`。29.265〜29.339秒のsampleではnative stdin rcharが増え、その後native CPUは増える一方backend CPU/rcharは停止時まで一定。第五callbackのpre-send処理に整合するが、phase-entry markerがないためparse/hash/serializeのどこだったかは **UNKNOWN／UNRESOLVED**。予定stageを実測entryとして扱わない。

## 5. Four completed callback analysis

時間単位は秒、MB/sはdecimal。各値はcensored trial内のACK済みprefixであり、安定したrepeat medianではない。

| Callback | JSON IPC bytes | Construct | Bind/hash | Serialize | Send | ACK wait | Inclusive | Descriptive send MB/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{callback_table}

合計IPC21,038,037 bytes、inclusive26.836615秒。send+ACKは20.601741秒（inclusiveの{100*components['send_ACK_inclusive_seconds']/components['callback_inclusive_seconds']:.2f}%）。constructorはoldTime0かつlive geometryを運び、他3controlはoldTime2のstateを運ぶため、bytesの比だけでcostを説明できない。payload/send時間の比は受信実装・buffer backpressure・schedulingを含む記述指標で、network bandwidthではない。

## 6. Native construct/hash/serialization cost

native hash spanは4.575032秒だが、SHA256計算単体ではない。`bind`／`rehash`でfield/oldTime/state/matrix epochを作り、`identity`はJsonをdeep copyしてhash keyを除き、`dump`はrecursive ostringstreamと17桁float formattingを行う。metadata BC hash、payload hash、コピーとserializationもhash spanに含む。constructはParserとfixture traversalの0.412672秒、最終record serializationは1.247081秒。

source inventoryではconstructor33回、他control各57回のSHA呼出shapeが見込まれる。二つのstate表現を別々にrehashするため同内容のfield/oldTime hashが重複する。ただしこれはsource countで、runtime crypto-call instrumentationではない。required hashは一つも削除していない。hashspanのcrypto対formatting比率、matrix-bearing classの追加hash costは未測定。

## 7. Socket send/backpressure analysis

AF_UNIX SOCK_STREAM socketpairはblocking。nativeは残りのserialized line全体を`send(...,MSG_NOSIGNAL)`へ渡し、短いsendなら残部をloopする。固定application chunk・nonblocking queue・socket buffer overrideはない。historical SO_SNDBUF/SO_RCVBUFは未保存。tiny構造probeの現在値は各212992 bytesだが、過去の実socket実測値とは主張しない。

backendは `sock.makefile('rwb', buffering=0)` のRaw SocketIOで`readline(packet_limit+1)`する。installed SocketIO.readintoはrecv_intoで、31-byteのtiny lineに31回の1-byte readが発生した。実21MBのpacket列でも同じsource pathを通ることからbytewise drainと大量Python/recv呼出が支持されるが、過去の21M syscall count自体を測ったわけではない。

backendは前callbackのACK後に次を読み、現在callbackの全line受信後にdecode/evaluateする。native sendがblockする間は主としてこのslow drainが進む。したがって **backend cannot consume bytes fast enough → buffer fills → native send blocks** はSUPPORTED。単なるAF_UNIX帯域不足、または前callback処理のqueue待ちと同一視しない。重要な点として、frozen `v1_4/server.py` も同じunbuffered readlineを使うため、qualificationだけの人工的な受信方式ではない。

## 8. ACK/backend dependency analysis

critical pathはnative parse→bind/hash→serialize、その後「native sendとbackend receiveが並行」、続いて「remaining receive/decode/evaluate/Writer/Liveとnative ACK待ちが並行」、ACK return。ACK wait8.830804秒は送信後に残ったbackend仕事とschedulingを含む。native send11.770935秒＋ACK8.830804秒はnative同一processの連続した区間として加算可能だが、そこへbackend child wall/CPUを足してcallback wallを作らない。backend CPUはreceive込みのbroad dominanceを支持し、evaluateのみ／canonicalのみのdominanceを証明しない。

## 9. Backend span durability failure

`Span(compact=True).flush()`はclass/path aggregateをRAMへ移すだけでdurable publicationではない。backendは正常finalizationの`save()`でbackend_resultをatomic publishする。timeout/SIGTERMはPython BaseException処理のdurable publicationを保証せず、今回はbackend_result/backend_failureともない。従って詳細span喪失はconfirmed observability defectであり、ACK済み4件の内訳すら失った。observer design JSONにqualification-only ledgerのcommit境界を記載した。

## 10. Startup full-audit involvement

full raw auditは **開始していない**。Writer.schedule.beginはtime_startで起き、spool作成はその後のeligible stageで行う。constructor/preSolve_before/preSolve_after/controller_completeはfull audit streamから明示的に除外される。archiveにfull_audit.scratch／full_*.binはなく、STOP時にspoolを消すbranchもない。initial_state/live_geometry/immutable blobの通常初期publicationはあったが、9GiB auditと混同しない。full auditは今回のprimary causeではない。

## 11. Payload size/static-vs-dynamic analysis

sourceはnative_state_epochとinline stateまたはstate aliasを重複してJSON化し、control callbackごとに10 fields、geometry、volumes、thermal contextを再送する。retained actual immutable blobのcanonical value byte数はgeometry={geo_bytes}、volumes={volume_bytes}、Cv={cv_bytes}、g={g_bytes}。四つのpacketではgeometry/volumesは各8回、Cv/gは各4回現れる。

この実保存値＋source occurrenceによるreconstructionではstatic value bytes={static_total}、そのうちdistinct initial contentを除いたredundant value bytes={redundant_static_value_bytes}。実IPC denominator21,038,037 bytesに対する **冗長static value byteの保守的な下限は{100*redundant_fraction:.4f}%**。JSON key/delimiter、patch metadata、dynamic field重複は含めない。raw transport messagesそのものは未保存なのでfull-message redundancy fractionの直接測定はUNRESOLVEDで、この下限をwall time節約率としない。

mesh addressing／geometry／volumesとfrozen Cv/gはstatic候補、field/oldTime／matrix係数／BC values/flags／stage scalarsはdynamic。resource fixtureのconstant field値を理由にphysical fieldをstatic扱いしない。Writer.shareはretained binary evidenceを共有するが、socketへ来る前のJSONを共有していない。static reference案にもexact identity/change rejection、fully restored scientific packet、P1 lossless evidenceの同等性検証が必要。

## 12. Host stability metric review

12.2222%の最大値はstart0.858753〜0.895597秒の区間。host total90 ticks、busy15 ticks、own4 ticksで、同区間に5個のnew PIDが現れ、その初期4 CPU ticksを現行式 `previous.get(pid,current)` が差分0として除外した。全4初期ticksを同区間内と仮定したsensitivityでは7/90=7.7778%になる。ただしbirth timestampとsample alignment不足のため、これをexact external busyの修正値として扱わない。

10%超はこの1 intervalのみ。new PIDのない区間の最大は{100*host_review['maximum_excluding_new_PID_intervals']:.4f}%、全trace tick residualの記述値は{100*host_review['whole_trace_tick_residual_fraction_descriptive']:.4f}%。inner own attributionはqualification observer PID {observer_pids} も除外し、outer traceではそのCPU tick最大{observer_ticks}を観測している。新規/短命process、未追跡observer、host counter後採取によるbiasはCONFIRMED。実外部負荷が30秒STOPのprimary causeだったかはUNRESOLVED。historical10% trigger/statusはそのまま残し、閾値を緩和も遡及PASSもしない。

## 13. Memory observations

partial startup combined RSS peak596,127,744 bytes、native432,934,912、backend170,524,672。memory guard違反は観測されていない。role RSSにはtime wrapper等が入り、sum individual peaksは同時peakと区別する。selected bundle、rolling buffer、U03、raw auditのRAM event peakは未測定なのでMEMORY_FEASIBILITY=UNRESOLVEDを維持する。

## 14. Current 30s/300s budget adequacy

30秒はoperational boundでscientific criterionではない。この試行はphysical graphに入る前に約29.22秒を使い、30秒では意義ある全step測定を完了できなかった。一方、その事実だけではproduction INFEASIBLEは証明されない。full Q1はstartup＋3 ON＋3 OFF＋finalizationで、per-trialだけを延長して300秒stage capを残すことは整合しない。

さらにinner raw trace生成率は約{trial_trace_rate:.0f}B/s、outerは{outer_trace_rate:.0f}B/s。二重traceの記述率合計{trace_rate:.0f}B/sに対し、現行trace/metadata計上384MiBを使い切る時間は約{accounting['manifest_trace_reserve_bytes']/trace_rate:.0f}秒。会計上のunused slackもすべてtraceへ充当した感度値で約{trace_headroom/trace_rate:.0f}秒。これはhard watchdogの新上限ではなく、既存12GiB会計proofを長時間へそのまま使えないことのmodelである。

## 15. Finite revised budget model

42 classesの頻度を使い、3 control classesのsingle prefix sampleと未測定39 classesを分離した。stateコピーshape数、matrix slots701、explicit arraysをsourceから数えた。以下はbyte-cost what-ifで、central state baseはcontrol mean/2、matrix slot bytesは0.5/1.5/3.0MBの**仮定**、state factorは0.7/1.0/1.4。これらは測定payloadでも真正なruntime下界/上界でもない。全1144へ4control平均を単純乗算したモデルではない。

| Conditional case | Modeled IPC | One startup callback path | Four ON paths portion of full stage | Projected two raw traces |
|---|---:|---:|---:|---:|
{model_table}

tableは未測定matrix replay/term同期、異なるhash/domain、audit/selected write、finalization、3 OFF／Python driver、observer costを除いており、合計completion timeは各caseともUNRESOLVED。conservative shape caseも安全なtotal upper boundではない。raw trace modelは384MiB計上を超えるので、これを根拠にhours-longのQ1 capを登録してはいけない。

有限の次段情報収集案は、別scopeの**4-control-callback observability scout**にtrial60/90/120秒、stage90/150/180秒というlower/central/conservative safety envelopeを先に登録すること。これは26.84秒prefix＋launch/publication余裕に基づく有限提案で、今回実行も登録もしていない。元Q1のfull startup sampleを短く置換する案ではない。full Q1の推奨trial／stage秒数はクラスscreening・観測改修・trace会計後に決めるためUNRESOLVED。timeout→倍増→retryは禁止。

## 16. Observability revision need

YES。設計はper-callback compact span treeを科学処理完了後・ACK前にdurable commitし、sequence/payload SHAでnative progressと結ぶ。64KiB/receipt、64MiB/chunkをfinite candidateとし、Q1は最大1145 receipts≈75MiB、2chunks＋metadata計3filesの追加モデル。既存layout111→114という暫定計上はtrace revisionを含まず、新proofが必要。

receive/decode/canonical/replay/pack/hash/persistence/ACK preparationを親子関係で保持し、native ACKと加算しない。inflight phase markerで次のcallbackを識別し、SIGKILL後のdurable prefixとinvalid tailを区別する。ledger quota/hash/fsync失敗時は成功ACKを出さずSTOP。計測追加costはMEASUREMENT_OBSERVER_OVERHEADへ分離する。自分自身の最終sync時間を同じreceiptへ記録する循環は避け、lagged cost／外部ACK wallとcoverage不足を明示する。

per-byte read wrapper/timerを21M回追加する案はobserver effectが大きいため採用しない。periodic-only checkpointは最大K件のACK済みspansを失い得て、all-completed-callback durabilityを満たさない。今taskではdesignのみでactive codeへ実装していないため、OBSERVABILITY_FIX_IMPLEMENTED=NO／fix tiny tests=NOT_APPLICABLE。既存46 regressionと31-byte reader structural probeはPASSである。

## 17. Architecture revision need

YES。priorityはC0の**bounded buffered line receiverの同等性準備**とBのdurable instrumentation。frozen production-like serverとqualificationの両方でbytewise receiveが確認されたため、片方だけを性能上都合よく変えて再測定することはできない。current backendやv1.4を変更せず、正式な新reviewでexact bytes、newline/limit/truncation、ACK ordering、STOP/evidence semanticsを検証する。

static/dynamic redundancy改善C、batchingD、binaryE、asyncFは比較のみ。必要なepoch/hash、1144/701 graph、U01/U02/U03/U04、production persistenceを削らない。architecture revision requiredはproduction実行不能の結論ではなく、次の測定を意味あるものにするためのtransport-equivalence reviewである。

## 18. Q2 gate information-value review

HIGH。孤立primitive／receiver decompositionはQ1 full PASS前でもSTOP原因の情報価値が高い。U03 isolated historiesはCFD/time進行なしに評価可能だが、今回のreceive原因に直接答える優先度は低い。新substage scope・authority・prerequisites・有限boundsをformal reviewする候補として分離し、full Q2 PASS／Q3前提へ代用しない。現在のQ1 PASS gateは変更せず、Q2も実行していない。

## 19. Candidate future options

architecture_options.csvにA〜FとC0のbenefit、scientific/evidence impact、difficulty、verification、riskを比較した。Aだけではobservabilityとper-byte costを直せず、trace reserveも悪化する。Bは診断可能性を改善するがsync observer costのtiny enabled/disabled検証が必須。C0はcontent/orderingを保った受信amortizationを狙える最小candidate。Cはstatic identity/restore proofが必要でHIGH、D/E/Fは変更面とverification burdenが大きいため後順位。

## 20. Minimal recommended change

最小の推奨セットは「C0の同等性設計＋Bのtimeout-safe backend spans＋host process attributionの方法レビュー」。実装は別taskで、まずtiny segmentation/truncation/overflow/ACK/deadlock／SIGKILL/durable chain／quota reserve／observer overheadを検証する。その後、new finite scoutでclass情報を増やし、全Q1のsource/mix/trace会計を作る。budget alone is sufficientとは判定しない。

## 21. New preparation/authorization requirements

新protocolでtarget information収集substageとfull Q1/Q2 acceptanceを区別する。plan／source／manifest／readinessの新pin、trace/ledger/scratch/file accounting、watchdog/STOP reserve、finite per-phase upper限、新qualification IDと新user authorizationが必要。old failed campaignや一回限りのold authorizationを再利用しない。正式ユーザーruntime deadlineは未登録のため任意7-day ruleは作らない。全compute/memory/I/O feasibility、resource ready、Gate J、Q3/production permissionは未解決／禁止のまま。

## 22. Exact next task

**PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_DIAGNOSTIC_COMPUTE_REVISION**（gpt-6.1-sol / high）。まずbounded receiverのcontent/order/evidence equivalenceとdurable observabilityを準備し、実装・tiny検証・protocol再登録に必要な変更範囲を固める。次のtarget Q1再測定は今回のtaskに含めない。

## Required final status

STATIC_PAYLOAD_REDUNDANCY_FRACTIONは実retained static valueから再構成した重複byte下限で、raw full-message fractionの直接計測ではない。

```text
{(OUT / 'required_final_status.txt').read_text().rstrip()}
```
'''
textfile(PREP, 'DiagnosticTransient_nonCFD_timing_qualification_fix_review.md', md)
for path, entry in guard['failed_campaign_files'].items():
    f = FAILED / path; need(sha(f) == entry['sha256'] and f.stat().st_mtime_ns == entry['mtime_ns'], 'STOP_HISTORY_CHANGED_AFTER_REVIEW')
for path, digest in guard['frozen_source_and_artifact_SHA256'].items():
    need(sha(ROOT / path) == digest, 'STOP_SOURCE_CHANGED_AFTER_REVIEW')
atomic(OUT, 'end_guard.json', {'status': 'PASS', 'failed_campaign_SHA_mtime_and_file_set_unchanged': True, 'active_source_artifact_manifest_unchanged': True, 'authority_verified': True, 'regression_tests': 46, 'regression': 'PASS', 'tiny_reader_structural_probe': 'PASS', 'new_actual_Q1_Q2_measurements': 0, 'CFD_executed': False, 'code_fix_implemented': False, 'git_HEAD': guard['HEAD'], 'git_status_short': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True), 'git_diff_stat': subprocess.check_output(['git', 'diff', '--stat'], cwd=ROOT, text=True), 'git_add_commit_push_executed': False})
report_paths = [PREP / name for name in ['DiagnosticTransient_nonCFD_timing_qualification_fix_review.md', 'DiagnosticTransient_nonCFD_timing_qualification_fix_review.json', 'TimingQualification_failed_startup_breakdown.csv', 'TimingQualification_callback_critical_path.csv', 'TimingQualification_payload_static_dynamic_review.csv', 'TimingQualification_budget_revision_model.csv', 'TimingQualification_architecture_options.csv']]
report_paths += [p for p in OUT.rglob('*') if p.is_file()]
atomic(OUT, 'review_evidence_manifest.json', {'schema': 'nonCFD_failure_review_evidence/1', 'status': 'COMPLETE', 'artifacts': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(report_paths)], 'actual_target_measurement': False, 'CFD_executed': False})
print(json.dumps({'status': 'COMPLETE', 'root_cause': 'MULTIPLE', 'regression': '46 PASS', 'static_redundant_value_fraction_lower_bound': redundant_fraction, 'model_hours': [r['modeled_callback_seconds'] / 3600 for r in model_results], 'observer_fix_implemented': False, 'actual_measurement_repeated': False, 'status_fields': len(status)}, indent=2))
