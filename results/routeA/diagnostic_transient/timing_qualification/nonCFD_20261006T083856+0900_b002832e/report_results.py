"""Read-only evaluation of the single censored campaign; never launches a trial."""
import csv, io, json, math, os, re, statistics, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
HERE = ROOT / 'Scripts/routeA/diagnostic_transient/timing_qualification/measurement'
sys.path.insert(0, str(HERE))
from common import atomic, authority, footprint, host, load, need, plan, sha, PREP
from archive import recover, artifact_blocks
import runner, watchdog

def save_text(name, value):
    path = OUT / name
    with path.open('x', encoding='utf-8') as f:
        f.write(value); f.flush(); os.fsync(f.fileno())

def table(name, rows, fields):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(rows)
    save_text(name, buffer.getvalue())

q1 = OUT / 'Q1'
result = load(q1 / 'stage_result.json')
need(result['status'] == 'STOPPED' and result['STOP_reason'] == 'STOP_WALL_TIME', 'STOP_UNEXPECTED_REPORT_INPUT')
need(len(result['trials']) == 1 and result['completed_repeats'] == 0, 'STOP_UNEXPECTED_TRIALS')
need(not (OUT / 'Q2').exists(), 'STOP_Q2_UNEXPECTED_EXECUTION')
records, tail = recover(q1 / 'archive', verify=True)
need(not tail and len(records) == 1, 'STOP_ARCHIVE_EVIDENCE')
trial = records[0]['metadata']
need(trial['status'] == 'CENSORED', 'STOP_CENSORED_LABEL_MISSING')
artifacts = {a['path']: a for a in records[0]['artifacts']}

def artifact_text(name):
    return b''.join(artifact_blocks(q1 / 'archive', artifacts[name])).decode()

trace = [json.loads(x) for x in artifact_text('resource_trace.jsonl').splitlines()]
progress = [json.loads(x) for x in artifact_text('native_progress.jsonl').splitlines() if x.startswith('{')]
outer_trace = [json.loads(x) for x in (q1 / 'resource_trace.jsonl').read_text().splitlines()]
need(all(not watchdog.alive(pid) for pid in trial['tracked_pids']), 'STOP_ORPHAN_AFTER_RUN')
stage_guard = load(q1 / 'trial_result.json')
need(not stage_guard['remaining_live_pids'], 'STOP_STAGE_ORPHAN_AFTER_RUN')
stage_manifest = load(q1 / 'qualification_manifest.json')
for a in stage_manifest['artifacts']:
    need(sha(q1 / a['path']) == a['sha256'], 'STOP_STAGE_MANIFEST_HASH:' + a['path'])
guard = load(OUT / 'start_guard.json')
for path, digest in guard['source_and_authority_SHA256'].items():
    need(sha(ROOT / path) == digest, 'STOP_FROZEN_SOURCE_CHANGED:' + path)
runner.verify_harness()
runtime = authority.verify_authority()
need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == guard['HEAD'], 'STOP_HEAD_CHANGED')

prior = {'Q0_status': 'PASS', 'Q1_status': 'CENSORED'}
try:
    runner.verify_authorization(OUT / 'authorization.json', 'Q2', OUT / 'Q2', prior)
except ValueError as e:
    q2_rejection = str(e)
else:
    raise ValueError('STOP_Q2_GATE_FAILED_OPEN')
need(q2_rejection == 'STOP_Q1_NOT_PASS', 'STOP_UNEXPECTED_Q2_GATE')
atomic(OUT, 'Q1_evaluation_Q2_gate.json', {
    'Q1_status': 'STOPPED', 'critical_trial_status': 'CENSORED',
    'Q1_classification': 'UNRESOLVED', 'Q1_STOP_reason': 'STOP_WALL_TIME',
    'Q2_user_authorized': True, 'Q2_progression_allowed': False,
    'frozen_permission_validator_rejection': q2_rejection,
    'reason': 'Frozen Q2 requires Q1 PASS; startup-only incomplete graph supplies neither recurring cost nor a U03 dominance diagnosis',
    'prior_stage_evidence': prior, 'Q2_executed': False,
    'no_retry': True, 'no_additional_repeats': True, 'no_budget_change': True,
})

clock_ticks = os.sysconf('SC_CLK_TCK')
resources = {
    'scope': 'CENSORED_STARTUP_ONLY_NOT_FULL_EVENT_QUALIFICATION',
    'classification': 'MEASURED_PEAK_SAMPLED',
    'samples': len(trace), 'outer_samples': len(outer_trace),
    'peak_native_RSS_bytes': trial['peak_RSS_bytes']['native'],
    'peak_backend_RSS_bytes': trial['peak_RSS_bytes']['backend'],
    'max_simultaneous_combined_RSS_bytes': trial['peak_RSS_bytes']['combined_simultaneous'],
    'sum_individual_native_backend_peaks_upper_bound': trial['sum_individual_native_backend_peaks_upper_bound'],
    'host_MemAvailable_min_bytes': min(x['host']['MemAvailable'] for x in trace),
    'peak_file_count_sampled': max(x['file_count'] for x in trace + outer_trace),
    'peak_scratch_bytes_sampled': max(x['scratch_bytes'] for x in trace + outer_trace),
    'min_disk_free_bytes_sampled': min(x['disk_free'] for x in trace + outer_trace),
    'maximum_sampling_gap_seconds': max(b['timestamp_monotonic'] - a['timestamp_monotonic'] for a, b in zip(trace, trace[1:])),
    'host_stability': trial['host_stability'],
    'memory_guard_violated': False, 'full_memory_event_coverage': False,
    'sampling_caveat': '20ms nominal sampling can miss short peaks; killed time-v wrappers did not publish high-water results',
    'role_caveat': 'Native/backend role RSS includes registered time wrappers and native permission helper; individual and role VmSize are distinguished',
}
role_rows = []
for role in ('native', 'backend', 'driver'):
    procs = [p for x in trace for p in x['processes'] if p['role'] == role]
    pids = sorted({p['pid'] for p in procs})
    peak_vm = max((p['VmSize'] for p in procs), default=None)
    peak_role_vm = max((sum(p['VmSize'] for p in x['processes'] if p['role'] == role) for x in trace), default=None)
    cpu = {}
    counters = {}
    for pid in pids:
        samples = [p for p in procs if p['pid'] == pid]
        cpu[str(pid)] = {k: max(p[k] for p in samples) / clock_ticks for k in ('CPU_user_ticks', 'CPU_system_ticks')}
        counters[str(pid)] = {k: max(p['io'][k] for p in samples) for k in ('wchar', 'write_bytes', 'rchar', 'read_bytes')}
    resources[role] = {'PIDs': pids, 'peak_individual_process_VmSize_bytes': peak_vm, 'peak_role_total_VmSize_bytes': peak_role_vm, 'sampled_CPU_lower_bound_by_PID': cpu, 'sampled_proc_IO_lower_bound_by_PID': counters}
    role_rows.append({'trial_id': trial['trial_id'], 'role': role, 'scope': resources['scope'], 'peak_role_RSS_bytes': trial['peak_RSS_bytes'].get(role, max(sum(p['RSS'] for p in x['processes'] if p['role'] == role) for x in trace)), 'peak_individual_VmSize_bytes': peak_vm, 'peak_role_total_VmSize_bytes': peak_role_vm, 'sampled_user_CPU_seconds_lower_bound': sum(v['CPU_user_ticks'] for v in cpu.values()), 'sampled_system_CPU_seconds_lower_bound': sum(v['CPU_system_ticks'] for v in cpu.values()), 'proc_wchar_sampled_lower_bound': sum(v['wchar'] for v in counters.values()), 'proc_write_bytes_sampled_lower_bound': sum(v['write_bytes'] for v in counters.values()), 'samples': len(trace), 'time_v_complete': False})
atomic(OUT, 'Q1_resource_summary.json', resources)
table('Q1_resource_trace_summary.csv', role_rows, list(role_rows[0]))

callback_rows = []
previous_bytes = previous_ack = previous_count = previous_matrices = 0
for x in progress:
    callback_rows.append({
        'trial_id': trial['trial_id'], 'trial_status': 'CENSORED',
        'payload_class': x['payload_class'], 'parent_span_id': x['parent_span_id'],
        'scope': 'COMPLETED_CALLBACK_PREFIX_INSIDE_CENSORED_STARTUP',
        'callback_count': x['callbacks_including_constructor'] - previous_count,
        'matrix_packets': x['matrices'] - previous_matrices,
        'JSON_IPC_bytes': x['bytes_IPC'] - previous_bytes,
        'ACK_bytes': x['ACK_bytes'] - previous_ack,
        'logical_bytes': 'UNRESOLVED', 'packed_bytes': 'UNRESOLVED', 'retained_bytes': 'UNRESOLVED',
        'callback_inclusive_seconds': x['callback_inclusive_seconds'],
        'native_construct_exclusive_seconds': x['construct_exclusive_seconds'],
        'native_hash_exclusive_seconds': x['hash_exclusive_seconds'],
        'native_serialization_exclusive_seconds': x['serialization_exclusive_seconds'],
        'socket_send_exclusive_seconds': x['socket_send_exclusive_seconds'],
        'ACK_wait_exclusive_seconds': x['ACK_exclusive_seconds'],
        'send_ACK_inclusive_seconds': x['send_ACK_inclusive_seconds'],
        'backend_children_available': False,
        'ACK_backend_nonadditive': True,
    })
    previous_bytes, previous_ack = x['bytes_IPC'], x['ACK_bytes']
    previous_count, previous_matrices = x['callbacks_including_constructor'], x['matrices']
table('Q1_callback_class_metrics.csv', callback_rows, list(callback_rows[0]))
atomic(OUT, 'Q1_partial_span_accounting.json', {
    'scope': 'FOUR_COMPLETED_STARTUP_CALLBACKS_ONLY',
    'actual_callback_count_including_constructor': previous_count,
    'actual_constructor_callbacks': 1, 'actual_recurring_graph_completed': False,
    'actual_matrix_packets_acknowledged': previous_matrices,
    'scheduled_recurring_callbacks': 1144, 'scheduled_matrix_packets': 701,
    'native_IPC_bytes_acknowledged_prefix': previous_bytes,
    'native_ACK_bytes_acknowledged_prefix': previous_ack,
    'completed_callback_inclusive_seconds_sum': sum(x['callback_inclusive_seconds'] for x in progress),
    'sum_native_construct_exclusive_seconds': sum(x['construct_exclusive_seconds'] for x in progress),
    'sum_native_hash_exclusive_seconds': sum(x['hash_exclusive_seconds'] for x in progress),
    'sum_native_serialization_exclusive_seconds': sum(x['serialization_exclusive_seconds'] for x in progress),
    'sum_socket_send_exclusive_seconds': sum(x['socket_send_exclusive_seconds'] for x in progress),
    'sum_ACK_wait_exclusive_seconds': sum(x['ACK_exclusive_seconds'] for x in progress),
    'sum_send_ACK_inclusive_seconds': sum(x['send_ACK_inclusive_seconds'] for x in progress),
    'cross_process_rule': 'send/ACK contains overlapping backend work; never add backend child wall to ACK',
    'backend_span_tree_status': 'UNRESOLVED_NOT_FINALIZED_BEFORE_KILL',
    'backend_result_status': 'NOT_PUBLISHED', 'time_v_status': 'ZERO_LENGTH_WRAPPERS_KILLED',
    'no_reconstruction_of_unpublished_timings': True,
    'span_parentage': 'Native callback ID is parent of construct/hash/serialize/socket/ACK; backend children were not durably finalized',
})
trial_row = {
    'trial_id': trial['trial_id'], 'mode': 'ON', 'cost_class': 'STARTUP_ONE_TIME',
    'status': 'CENSORED', 'STOP_reason': trial['STOP_reason'],
    'start_monotonic': trial['start_monotonic'], 'end_monotonic': trial['end_monotonic'],
    'external_wall_seconds': trial['wall_seconds'], 'sample_valid': False,
    'completed_callbacks_including_constructor': previous_count,
    'completed_matrix_packets': previous_matrices, 'full_recurring_callbacks_expected': 1144,
    'full_recurring_matrix_packets_expected': 701,
    'native_JSON_IPC_bytes_completed_prefix': previous_bytes,
    'native_CPU_seconds_sampled_lower_bound': sum(r['sampled_user_CPU_seconds_lower_bound'] + r['sampled_system_CPU_seconds_lower_bound'] for r in role_rows if r['role'] == 'native'),
    'backend_CPU_seconds_sampled_lower_bound': sum(r['sampled_user_CPU_seconds_lower_bound'] + r['sampled_system_CPU_seconds_lower_bound'] for r in role_rows if r['role'] == 'backend'),
    'peak_native_RSS_bytes': resources['peak_native_RSS_bytes'],
    'peak_backend_RSS_bytes': resources['peak_backend_RSS_bytes'],
    'max_simultaneous_combined_RSS_bytes': resources['max_simultaneous_combined_RSS_bytes'],
    'peak_native_VmSize_bytes': resources['native']['peak_individual_process_VmSize_bytes'],
    'peak_backend_VmSize_bytes': resources['backend']['peak_individual_process_VmSize_bytes'],
    'host_MemAvailable_min_bytes': resources['host_MemAvailable_min_bytes'],
    'file_count_peak_sampled': resources['peak_file_count_sampled'],
    'scratch_bytes_peak_sampled': resources['peak_scratch_bytes_sampled'],
    'other_CPU_busy_max_fraction': trial['host_stability']['other_CPU_fraction_max'],
    'timing_stability': 'UNRESOLVED', 'startup_sample_completed': False,
    'startup_production_projection_multiplicity': 3,
    'startup_three_distinct_states_measured': False,
}
table('Q1_trial_metrics.csv', [trial_row], list(trial_row))
table('Q1_runtime_projection.csv', [{'Co': co, 'planning_steps': n, 'label': 'NONCFD_DIAGNOSTIC_ONLY_RUNTIME_PROJECTION', 'scope': 'PLANNING_ONLY', 'recurring_seconds': 'UNRESOLVED', 'projected_runtime_seconds': 'UNRESOLVED', 'reason': 'No completed OFF/ON recurring pair'} for co, n in zip(('0.5', '0.25', '0.125'), plan()['planning_classification']['step_scenarios_planning_only'])], ['Co', 'planning_steps', 'label', 'scope', 'recurring_seconds', 'projected_runtime_seconds', 'reason'])
atomic(OUT, 'Q1_stage_manifest.json', {'status': 'STOPPED', 'scope': 'ACTUAL_TARGET_SIZE_NONCFD_Q1', 'stage_manifest_path': 'Q1/qualification_manifest.json', 'stage_manifest_SHA256': sha(q1 / 'qualification_manifest.json'), 'stage_receipt_SHA256': sha(q1 / 'stage_receipt.json'), 'archive_record_hash': records[0]['record_hash'], 'all_stage_artifact_hashes_verified': True, 'all_committed_trial_artifacts_hashes_verified': True, 'uncommitted_tail': False, 'no_orphans': True, 'full_trial_valid': False, 'partial_evidence_valid': True})

for name, fields, rows in (
    ('Q2_U03_scaling.csv', ['registered_N', 'repeat', 'status', 'kernel_wall_seconds'], [{'registered_N': n, 'repeat': r, 'status': 'NOT_EXECUTED', 'kernel_wall_seconds': 'UNRESOLVED'} for n in plan()['Q2_U03']['node_counts'] for r in range(3)]),
    ('Q2_primitive_metrics.csv', ['payload_class', 'status', 'reason'], [{'payload_class': c, 'status': 'NOT_EXECUTED', 'reason': q2_rejection} for c in ('compact scalar receipt', 'field-state payload', 'scalar LDU matrix', 'explicit term', 'controller payload', 'selected bundle')]),
    ('Q2_memory_events.csv', ['event', 'status', 'measured_peak', 'accounting_upper_bound', 'guard_limit'], [{'event': e, 'status': 'NOT_EXECUTED', 'measured_peak': 'UNRESOLVED', 'accounting_upper_bound': 'NOT_A_MEASUREMENT', 'guard_limit': 'NOT_A_MEASUREMENT'} for e in plan()['memory_events'] + ['chunk publication']]),
    ('Q2_io_metrics.csv', ['status', 'bytes', 'MBps', 'fsync_seconds', 'reason'], [{'status': 'NOT_EXECUTED', 'bytes': 'UNRESOLVED', 'MBps': 'UNRESOLVED', 'fsync_seconds': 'UNRESOLVED', 'reason': q2_rejection}]),
):
    table(name, rows, fields)
atomic(OUT, 'Q2_U03_fit.json', {'status': 'UNRESOLVED', 'reason': 'Q2 NOT_EXECUTED: ' + q2_rejection, 'completed_sizes': [], 'censored_trials': [], 'a': None, 'p': None, 'local_exponents': [], 'production_node_projection_confidence': 'NONE', 'source_reasoning': plan()['Q2_U03']['source_reasoning'], 'empirical_measurement_performed': False, 'no_tiny_timings_substituted': True})
atomic(OUT, 'Q2_stage_manifest.json', {'status': 'NOT_EXECUTED', 'stage_directory_created': False, 'actual_stage_receipt_created': False, 'actual_trials': 0, 'user_authorized': True, 'progression_allowed': False, 'reason': q2_rejection, 'registered_file_limit': 256, 'registered_layout_upper_bound': 149, 'upper_bound_is_not_observed_file_count': True})

ranking = [{'component': c, 'campaign_rank': 'UNKNOWN', 'risk': 'UNKNOWN', 'reason': 'No completed recurring graph or Q2 breakdown; prefix spans cannot establish production dominance'} for c in ('serialization', 'canonicalization', 'matrix replay', 'packing', 'IPC', 'U03', 'memory', 'I/O', 'other')]
table('bottleneck_ranking.csv', ranking, ['component', 'campaign_rank', 'risk', 'reason'])
review = load(PREP / 'DiagnosticTransient_compute_feasibility_review.json')['native_summary_SYNTHETIC_ONLY']
atomic(OUT, 'comparison_with_previous_synthetic_review.json', {
    'previous_review_path': str((PREP / 'DiagnosticTransient_compute_feasibility_review.json').relative_to(ROOT)),
    'previous_review_SHA256': sha(PREP / 'DiagnosticTransient_compute_feasibility_review.json'),
    'previous_four_cell_ON_median_seconds': review['ON']['median_wall_s'],
    'previous_four_cell_OFF_median_seconds': review['OFF']['median_wall_s'],
    'current_target_size_startup_external_elapsed_seconds': trial['wall_seconds'],
    'current_status': 'CENSORED', 'current_complete_graph_measured': False,
    'direct_runtime_ratio': None,
    'interpretation': 'Different data shapes and scope: previous complete four-cell graph versus target-size incomplete startup, no current OFF baseline. Counts and event coverage differ; no direct ratio or whole-step speed claim is valid.',
    'frozen_harness_features': ['separate startup/recurring cost', 'actual 25600-cell/50880-internal-face topology', 'separate compact scalar receipts and controller payloads', 'immutable chunk archive', 'compacted profiling span trees'],
    'observed_current_prefix_classes': [x['payload_class'] for x in progress],
    'numerical_pattern_and_cache_limits': 'Manufactured resource fixtures and uncontrolled cache remain limitations; no cache drop, frequency or affinity change',
})

request_path = Path('/home/mirai/.codex/attachments/ef2044e4-7525-40f4-93e5-f56a9a8262ab/貼り付けたテキスト.txt')
request = request_path.read_text()
section = request.split('# 109. REQUIRED FINAL STATUS')[1].split('# 110.')[0]
keys = re.findall(r'^([A-Z][A-Z0-9_]+)\s*=\s*$', section, re.M)
status = {k: 'UNRESOLVED' for k in keys}
status.update({
    'ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION': 'STOPPED',
    'QUALIFICATION_ID': OUT.name, 'CANONICAL_DIAGNOSTIC_AUTHORITY_VERSION': '1.5',
    'CANONICAL_AUTHORITY_HASH_VERIFIED': 'YES', 'FORMAL_AUTHORITY_HASH_VERIFIED': 'YES',
    'RUNTIME_AUTHORITY_COMPATIBILITY': 'PASS', 'MEASUREMENT_READINESS_VERIFIED': 'YES',
    'USER_NONCFD_Q1_Q2_AUTHORIZATION': 'YES', 'AUTHORIZATION_SCOPE': 'Q1_Q2_NONCFD_ONLY',
    'Q1_AUTHORIZED': 'YES', 'Q2_AUTHORIZED': 'YES', 'PREMEASUREMENT_REGRESSION': 'PASS',
    'TARGET_CELL_COUNT': 25600, 'TARGET_INTERNAL_FACE_COUNT': 50880,
    'CALLBACKS_PER_STEP_EQUIVALENT': 1144, 'MATRIX_PACKETS_PER_STEP_EQUIVALENT': 701,
    'Q1_EXECUTED': 'YES', 'Q1_STATUS': 'STOPPED', 'Q1_CLASSIFICATION': 'UNRESOLVED',
    'Q1_PEAK_NATIVE_RSS_BYTES': resources['peak_native_RSS_bytes'],
    'Q1_PEAK_BACKEND_RSS_BYTES': resources['peak_backend_RSS_bytes'],
    'Q1_MAX_SIMULTANEOUS_COMBINED_RSS_BYTES': resources['max_simultaneous_combined_RSS_bytes'],
    'Q1_PEAK_NATIVE_VMSIZE_BYTES': resources['native']['peak_individual_process_VmSize_bytes'],
    'Q1_PEAK_BACKEND_VMSIZE_BYTES': resources['backend']['peak_individual_process_VmSize_bytes'],
    'Q2_EXECUTED': 'NO', 'Q2_STATUS': 'NOT_EXECUTED',
    'U03_SOURCE_COMPLEXITY_CLASS': 'QUADRATIC_TENDENCY_SOURCE_REASONING_NOT_EMPIRICAL_FIT',
    'U03_PRODUCTION_NODE_PROJECTION_CONFIDENCE': 'NONE',
    'U03_COMPUTE_RISK': 'UNKNOWN', 'SERIALIZATION_RISK': 'UNKNOWN',
    'CANONICALIZATION_RISK': 'UNKNOWN', 'MATRIX_REPLAY_RISK': 'UNKNOWN',
    'PACKING_RISK': 'UNKNOWN', 'IPC_RISK': 'UNKNOWN',
    'PEAK_NATIVE_RSS_BYTES': resources['peak_native_RSS_bytes'],
    'PEAK_BACKEND_RSS_BYTES': resources['peak_backend_RSS_bytes'],
    'MAX_SIMULTANEOUS_COMBINED_RSS_BYTES': resources['max_simultaneous_combined_RSS_bytes'],
    'MEMORY_GUARDS_RESPECTED': 'YES', 'Q2_FILE_LIMIT': 256,
    'WATCHDOG_STOP_OCCURRED': 'YES', 'STOP_REASON': 'STOP_WALL_TIME',
    'CENSORED_TRIALS_PRESENT': 'YES', 'PARTIAL_EVIDENCE_VALID': 'YES',
    'COMPUTE_CONFIDENCE': 'LOW', 'MEMORY_CONFIDENCE': 'LOW', 'IO_CONFIDENCE': 'LOW',
    'DOMINANT_BOTTLENECK': 'UNKNOWN', 'Q3_BOUNDED_CFD_QUALIFICATION_RECOMMENDED': 'NO',
    'DIAGNOSTIC_TRANSIENT_STORAGE_READY': 'YES', 'DIAGNOSTIC_TRANSIENT_RESOURCE_READY': 'NO',
    'COMPLETE_EXECUTION_CONFIGURATION_FROZEN': 'NO',
    'FORMAL_GATE_J_PASS': 'NOT_EVALUATED', 'ALL_ROUTE_A_GATE_F': 'FAIL', 'ALL_RA_NEEDS_320': 'YES',
    'NEXT_SINGLE_TASK': 'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION',
    'RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK': 'gpt-6.1-sol / high', 'USER_DECISION_REQUIRED': 'YES',
})
for key in ('Q3_AUTHORIZED', 'PRODUCTION_EXECUTION_AUTHORIZED', 'Q3_EXECUTED', 'PRODUCTION_SOLVER_EXECUTED', 'PILOT_CFD_EXECUTED', 'CFD_TRANSIENT_EXECUTED', 'CASE_GENERATED', 'MESH_GENERATED', 'INITIALIZATION_EXECUTED', 'EXECUTION_AUTHORIZED', 'U01_CHANGED', 'U02_CHANGED', 'U03_CHANGED', 'U04_EQUATION_SEMANTICS_CHANGED', 'N_OUTER_CORRECTORS_CHANGED', 'LINEAR_SOLVER_POLICY_CHANGED', 'TEMPORAL_POLICY_CHANGED', 'PERSISTENCE_POLICY_CHANGED', 'SEAL_PURGE_POLICY_CHANGED', 'RETENTION_POLICY_CHANGED', 'CAPACITY_ESTIMATES_CHANGED', 'FORMAL_CRITERIA_CHANGED', 'HISTORICAL_STATUS_CHANGED', 'FORMAL_GATE_J_CURRENTLY_ALLOWED', 'FORMAL_GATE_J_EXECUTED', 'BENCHMARK_CORE_PASS', 'ROUTE_A_CHARACTERIZED', 'GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED', 'DOWNSTREAM_TRANSIENT_READY', 'PARTICLE_COUPLING_READY'):
    status[key] = 'NO'
need(set(status) == set(keys) and len(keys) == len(set(keys)), 'STOP_FINAL_STATUS_KEY_MISMATCH')
status = {k: status[k] for k in keys}
save_text('required_final_status.txt', '\n'.join(k + ' = ' + str(v) for k, v in status.items()) + '\n')

report = {
    'schema': 'routeA_nonCFD_timing_qualification_result/1',
    'task': 'RUN_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION',
    'qualification_id': OUT.name, 'status': 'STOPPED', 'timestamp': datetime.now(timezone.utc).isoformat(),
    'HEAD': guard['HEAD'], 'required_final_status': status,
    'authorization': {'actual_nonCFD_authorization_created': True, 'scope_path': 'authorization_scope.json', 'scope_SHA256': sha(OUT / 'authorization_scope.json'), 'runner_exact_schema_path': 'authorization.json', 'runner_exact_schema_SHA256': sha(OUT / 'authorization.json'), 'production_execution_authorized': False, 'Q3_authorized': False},
    'regression': {'status': 'PASS', 'tests': 46, 'source_unchanged': True, 'path': 'premeasurement_regression.json'},
    'Q1': {'status': 'STOPPED', 'critical_trial_status': 'CENSORED', 'trial': trial_row, 'planned_graph_verified_before_launch': True, 'graph_fully_executed': False, 'recurring_trials_attempted': 0, 'paired_ON_minus_OFF': [], 'completed_startup_samples': 0, 'startup_projection_multiplicity_registered': 3, 'startup_three_distinct_states_measured': False, 'selected_audit_completed': False, 'finalization_completed': False, 'full_startup_audit_completed': False},
    'Q2': {'status': 'NOT_EXECUTED', 'reason': q2_rejection, 'user_authorized': True, 'no_target_U03_primitive_memory_IO_measurements': True, 'registered_trials': 66, 'actual_trials': 0},
    'resources': resources,
    'feasibility': {name: {'classification': 'UNRESOLVED', 'confidence': 'LOW', 'reason': reason} for name, reason in {'compute': 'Censored startup with no full graph, no recurring OFF/ON pair or target U03 fit', 'memory': 'Observed prefix respected all guards; required rolling/bundle/audit/U01/U03 events unqualified', 'IO': 'Q2 bounded I/O unexecuted; initial runtime writes are not selected/audit sustained I/O qualification'}.items()},
    'bottleneck_ranking': ranking,
    'interpretation': {'timeout_is_not_production_infeasibility_proof': True, 'no_formal_user_deadline': True, 'no_new_months_years_projection_from_incomplete_data': True, 'no_full_graph_extrapolation_from_four_callbacks': True, 'host_instability_rule_triggered': trial['host_stability']['reasons'], 'actual_partial_observations_not_guard_limits': True, 'startup_or_guard_cost_not_substituted_for_recurring_cost': True, 'no_tiny_timings_substituted': True, 'cache_uncertainty': 'Uncontrolled existing caches; no cache drop; warm/cold sustained I/O unknown'},
    'next_task_scope': 'Inspect the failed target startup path and durable incomplete span evidence; any implementation or bound/schedule revision requires a separate task and new preparation/authorization. Do not retry this campaign.',
    'historical_harness_metadata_caveat': {'stage_result_actual_authorization_created_false': 'Frozen stage_summary hardcodes false for preparation-era reporting. Real authorization exists and is hash-bound by actual stage receipt; parent report records true without rewriting frozen output.', 'stage_result_execution_authorized_false': 'Production permission remains false; separate exact-schema authorization enables only Q1/Q2 nonCFD launches.'},
    'evidence': {'stage_manifest_verified': True, 'archive_artifacts_verified': True, 'partial_trial_addressable': True, 'no_uncommitted_index_tail': True, 'no_orphan_processes': True, 'no_actual_evidence_purged': True, 'regression_tiny_fixtures': 'Original regression TemporaryDirectory cleanup; actual campaign archive and evidence never removed', 'frozen_source_and_authority_SHA_unchanged': True},
}
atomic(OUT, 'DiagnosticTransient_nonCFD_timing_qualification.json', report)
md = f'''# Route A non-CFD timing qualification — {OUT.name}

結果は **STOPPED**。Q1の最初のtarget-size startup trialが30秒上限で`STOP_WALL_TIME`となった。全46件の事前回帰試験はPASSし、凍結source・契約・readiness・buildのhashも一致した。実Q1を一度実行し、追加測定・予算変更・実装変更は行っていない。

Q1 stage wallは{result['wall_seconds']:.6f}秒、censored trial wallは{trial['wall_seconds']:.6f}秒。native完了通知はconstructorを含む{previous_count} callback、matrix packetは{previous_matrices}件。1144 callback／701 matrix packetは事前検証された予定graphであり、実行完了数ではない。OFF/ONのrecurring trialには到達せず、Q1のmedian・signed ON−OFF・diagnostic fraction・全step projectionはUNRESOLVED。startup sampleも未完了で、3つの異なるstartup stateを測定したとは主張しない。

Q2はユーザー許可済みだが、凍結validatorがQ1 PASSを要求し`STOP_Q1_NOT_PASS`で進行を拒否した。U03、primitive、memory event、bounded I/Oのtarget測定は実施していない。Q2 CSVのNOT_EXECUTED行は予定項目の明示であり測定値ではない。tiny回帰試験の性能値を代用していない。

| Quantity | Result | Confidence |
|---|---:|---|
| Q1 OFF median | UNRESOLVED | No recurring trial |
| Q1 ON median | UNRESOLVED | Startup censored |
| recurring diagnostic overhead | UNRESOLVED | No completed pair |
| peak native role RSS | {resources['peak_native_RSS_bytes']} bytes | Sampled incomplete startup only |
| peak backend role RSS | {resources['peak_backend_RSS_bytes']} bytes | Sampled incomplete startup only |
| max simultaneous combined RSS | {resources['max_simultaneous_combined_RSS_bytes']} bytes | Sampled; not sum of separate maxima |
| U03 exponent p | UNRESOLVED | Q2 not executed |
| max stable U03 N | UNRESOLVED | Q2 not executed |
| selected I/O throughput | UNRESOLVED | Q2 not executed |
| fsync latency | UNRESOLVED | No finalized fsync spans |

native/backendの個別process VmSize peakは{resources['native']['peak_individual_process_VmSize_bytes']}／{resources['backend']['peak_individual_process_VmSize_bytes']} bytes、host MemAvailable最小は{resources['host_MemAvailable_min_bytes']} bytes。個別最大RSSの合計{resources['sum_individual_native_backend_peaks_upper_bound']} bytesは同時peakとは別の上界として保存した。role RSSはtime wrapper／native permission helperを含む。821個のtrial sampleを保存し、memory/AS/host-memory/storage guard違反は観測されなかった。rolling buffer、selected bundle、9GiB audit、U01/U03の全event peakは未測定であり、guard限度や会計上界を測定peakとして扱わない。

host traceのother CPU最大は{trial['host_stability']['other_CPU_fraction_max']:.6f}で、登録済み10%超のruleもUNRESOLVEDを要求する。名目20ms観測には短いpeakを取り逃がす限界がある。time-v wrapperは停止時にkillされ、出力が空であるため、proc CPU/I/O counterをsampled lower boundとして保存した。

完了prefixのnative IPCは{previous_bytes} bytes、ACKは{previous_ack} bytes。class別native construct/hash/serialization/socket/ACKはQ1_callback_class_metrics.csvとQ1_partial_span_accounting.jsonへ保存した。send/ACK inclusiveはbackend作業と重複するため加算しない。backendは最終span treeをpublishする前に停止し、canonicalization/replay/packing/fsyncのcampaign rankはUNKNOWN。完了prefixの4 callbackからrecurring全graphやproduction bottleneckを推定しない。

前reviewの4-cell ON medianは{review['ON']['median_wall_s']:.6f}秒、OFFは{review['OFF']['median_wall_s']:.6f}秒。今回は25600-cell実topologyの未完了startupでscope・payload shape・完了graph数が異なり、速度比は比較不能。startup分離、compact receipt/controller分離、chunk archive、profiling compactionは凍結済み特徴として記録したが、今回の停止を性能改善や悪化の定量比較へ変換しない。

compute／memory／I/O feasibilityはすべて **UNRESOLVED、confidence LOW**。有限のtiming capによるSTOPだけではproduction INFEASIBLEの証明にならない。正式なユーザーwall deadlineは未登録で、7日等の任意閾値も用いていない。diagnostic-only runtime projectionとU03大N projectionは作成できず、CFD costも測定していない。

authorization.jsonは凍結runnerのexact schema、authorization_scope.jsonはHEAD・timestamp・user attachment／契約／readiness／runtime mapping hash・Q1/Q2のみの許可・Q3/production等の禁止を記録する。凍結stage_summaryにはpreparation由来のactual_authorization_created=falseという定数が残るが、実authorizationはstage_receiptのSHAで検証されている。本reportはその差を明示し、元summaryを変更していない。

STOP後もauthorization・stage receipt・resource traces・trial index・21個のtrial artifact・manifestをretainした。全hash読戻し、chain、source不変、残存processなしを検証済み。実測証拠のpurgeは行っていない。case/mesh/initialization、foamRun、Q3/pilot/production CFD、物理時間進行、PIMPLE/fv solveは実行していない。git add/commit/pushも行っていない。

次の単一taskは **FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION**。failed target startupと未publish spanの問題を別taskで検討し、変更が必要なら新しい準備・検証・許可を経る。このcampaignの再試行や限度拡張は行わない。Q3推奨はNO、resource-ready／execution authorizationはNOのまま。

## Required final status

```text
{(OUT / 'required_final_status.txt').read_text().rstrip()}
```
'''
save_text('DiagnosticTransient_nonCFD_timing_qualification.md', md)
atomic(OUT, 'end_guard.json', {
    'timestamp': datetime.now(timezone.utc).isoformat(), 'HEAD': guard['HEAD'],
    'frozen_source_and_authority_SHA_unchanged': True,
    'runtime_authority': runtime,
    'harness_readiness_still_verified': True,
    'stage_artifact_manifest_verified': True, 'archive_readback_verified': True,
    'no_live_trial_pids': True, 'no_live_stage_pids': True,
    'Q1_actual_campaigns': 1, 'Q2_actual_campaigns': 0,
    'no_retry': True, 'no_harness_or_plan_edit': True,
    'production_execution_authorized': False, 'Q3_authorized': False,
    'host_snapshot_after': host(),
    'git_status_short': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
    'git_diff_stat': subprocess.check_output(['git', 'diff', '--stat'], cwd=ROOT, text=True),
    'git_diff_check': subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True).returncode,
    'git_add_commit_push_executed': False,
})
rows = [{'path': str(p.relative_to(OUT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
atomic(OUT, 'campaign_evidence_manifest.json', {'schema': 'nonCFD_campaign_evidence/1', 'qualification_id': OUT.name, 'status': 'STOPPED', 'artifacts': rows, 'production_result': False, 'Q3_authorized': False})
print(json.dumps({'qualification_id': OUT.name, 'status': report['status'], 'Q1_status': status['Q1_STATUS'], 'Q2_status': status['Q2_STATUS'], 'STOP_reason': status['STOP_REASON'], 'source_unchanged': True, 'no_orphans': True, 'artifacts': len(rows), 'status_fields': len(status)}, indent=2))
