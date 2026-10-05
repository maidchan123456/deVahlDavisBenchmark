"""Plan validation and fail-closed stage gates; contains no process launcher."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation'
PLAN = PREP / 'DiagnosticTransient_bounded_timing_qualification_plan.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('STOP_DUPLICATE_AUTHORITY_KEY: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def validate(plan, root=ROOT):
    errors = []
    def need(ok, name):
        if not ok:
            errors.append(name)
    need(plan['schema'] == 'routeA_timing_qualification_plan/1.0', 'SCHEMA')
    need(plan['execution_authorized'] is False and plan['production_execution_authorized'] is False,
         'PREPARATION_NO_RUN_AUTHORIZATION')
    need(plan['stages']['Q3']['execute_in_this_task'] is False, 'NO_Q3_IN_PREPARATION')
    need(plan['current_runtime_compatibility'] == 'REQUIRES_FIX', 'CURRENT_RUNTIME_COMPATIBILITY')
    c = load(root / 'docs/routeA_diagnostic_transient_contract_v1.5.json')
    need(plan['frozen_switches'] == c['transient_algorithm']['frozen_switches'], 'FROZEN_SWITCHES')
    need(plan['linear_solver_dictionary'] == c['transient_algorithm']['linear_solver_dictionary'], 'FROZEN_LINEAR_POLICY')
    need(plan['relaxationFactors'] == c['transient_algorithm']['relaxationFactors'], 'FROZEN_RELAXATION')
    for path, digest in plan['authority_sha256'].items():
        need(sha(root / path) == digest, 'AUTHORITY_HASH:' + path)
    need(sum(x['frequency_per_step'] for x in plan['callback_classes']) == 1144, 'CALLBACK_WEIGHT_SUM')
    need(sum(x['matrix_packets_per_callback'] * x['frequency_per_step']
             for x in plan['callback_classes']) == 701, 'MATRIX_PACKET_WEIGHT_SUM')
    need(plan['solve_counts_per_step'] == {'U_fv': 24, 'e': 24, 'p_rgh': 48, 'rho': 49,
                                         'total_fv': 145, 'scalar_records': 169}, 'SOLVE_COUNTS')
    need(all(x['target_payload_bytes'] == 'NOT_MEASURED_REQUIRED_BY_Q1'
             for x in plan['callback_classes']), 'DO_NOT_INVENT_TARGET_BYTES')
    for name, stage in plan['stages'].items():
        budget = stage['budgets']
        need(all(type(budget[x]) is int and budget[x] > 0 for x in
                 ('stage_wall_seconds', 'single_trial_wall_seconds', 'scratch_bytes', 'files_max')),
             'FINITE_BUDGET:' + name)
        need(budget['single_trial_wall_seconds'] <= budget['stage_wall_seconds'], 'TRIAL_STAGE_BUDGET:' + name)
        need(budget['native_AS_max_bytes'] == 8 * 2**30 and budget['backend_AS_max_bytes'] == 8 * 2**30,
             'UNCHANGED_AS_CAP:' + name)
        need(budget['host_MemAvailable_min_bytes'] == 24 * 2**30, 'UNCHANGED_HOST_MEMORY:' + name)
        need(stage['no_auto_retry'] is True, 'NO_AUTO_RETRY:' + name)
    need(sum(x['budgets']['stage_wall_seconds'] for x in plan['stages'].values()) <= 900,
         'SHORT_AGGREGATE_BUDGET')
    need(plan['Q2_U03']['node_counts'] == [100, 200, 400, 800, 1600, 3200, 6400]
         and plan['Q2_U03']['repeats'] == 3
         and plan['Q2_U03']['single_trial_wall_seconds'] == 15
         and plan['Q2_U03']['suite_wall_seconds'] == 120, 'U03_REGISTERED_BOUNDS')
    need(plan['Q3_design']['steps_per_trial_max'] == 2 and plan['Q3_design']['total_steps_max'] == 8,
         'MINIMAL_Q3_STEP_CAP')
    need(plan['Q3_design']['separate_user_authorization_required'] is True, 'Q3_USER_AUTHORIZATION')
    need(plan['Q3_design']['labels'] == ['NOT_PRODUCTION_RESULT', 'NOT_GATE_J',
                                      'NOT_TEMPORAL_COMPARISON_RESULT', 'NOT_VALIDATION_DATA'], 'Q3_NON_SCIENTIFIC')
    need(plan['Q3_design']['namespace'].startswith('results/routeA/diagnostic_transient/timing_qualification/'),
         'Q3_NAMESPACE')
    need(plan['measurement']['simultaneous_RSS_sample_interval_seconds'] == .02
         and plan['measurement']['combined_peak_formula'] == 'max_t(native_RSS(t) + backend_RSS(t))',
         'SIMULTANEOUS_MEMORY_MEASUREMENT')
    need(plan['repeatability']['minimum_repeats'] == 3 and plan['repeatability']['automatic_extra_repeats'] is False,
         'REPEATABILITY')
    return errors


def gate(plan, stage, receipt, plan_sha256):
    """Validate declared prior decisions, never grants authorization itself."""
    if stage not in ('Q1', 'Q2', 'Q3'):
        raise ValueError('STOP_UNKNOWN_STAGE')
    if plan.get('current_runtime_compatibility') != 'PASS':
        raise ValueError('STOP_CURRENT_RUNTIME_REQUIRES_FIX')
    if receipt.get('plan_sha256') != plan_sha256:
        raise ValueError('STOP_QUALIFICATION_PLAN_HASH')
    if receipt.get('Q0_status') != 'PASS':
        raise ValueError('STOP_Q0_NOT_PASS')
    if receipt.get('runtime_authority_compatibility') != 'PASS':
        raise ValueError('STOP_RUNTIME_AUTHORITY_COMPATIBILITY')
    if not receipt.get('explicit_user_authorization_reference'):
        raise ValueError('STOP_NONCFD_AUTHORIZATION_REQUIRED')
    expected = 'NONCFD_TIMING_QUALIFICATION' if stage != 'Q3' else 'Q3_BOUNDED_CFD_TIMING_QUALIFICATION'
    if receipt.get('authorization_scope') != expected:
        raise ValueError('STOP_AUTHORIZATION_SCOPE')
    if stage in ('Q2', 'Q3') and receipt.get('Q1_status') != 'PASS':
        raise ValueError('STOP_Q1_NOT_PASS')
    if stage == 'Q3':
        for key in ('Q2_status', 'memory_status', 'IO_status'):
            if receipt.get(key) != 'PASS':
                raise ValueError('STOP_' + key.upper() + '_NOT_PASS')
        if receipt.get('Q1_planning_classification') not in ('CLEARLY_PRACTICAL', 'POTENTIALLY_PRACTICAL'):
            raise ValueError('STOP_DIAGNOSTIC_HIGH_RISK_NO_Q3')
        if receipt.get('U03_revision_required') is not False:
            raise ValueError('STOP_U03_REVISION_OR_UNKNOWN')
        if (type(receipt.get('user_runtime_budget_seconds')) not in (int, float)
                or not 0 < receipt['user_runtime_budget_seconds'] < float('inf')
                or receipt.get('continuous_run_risk_accepted') is not True):
            raise ValueError('STOP_PRACTICAL_BUDGET_UNREGISTERED')
    return True


if __name__ == '__main__':
    plan = load(PLAN)
    errors = validate(plan)
    print(json.dumps({'plan_valid': not errors, 'errors': errors,
                      'current_runtime_compatibility': plan['current_runtime_compatibility'],
                      'measurement_stages_executed': [], 'execution_authorized': False}, indent=2))
    raise SystemExit(bool(errors))
