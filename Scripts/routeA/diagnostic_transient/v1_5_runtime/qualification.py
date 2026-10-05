"""Permission validator only. No launcher, subprocess, solver or dispatch imports."""
import math
from pathlib import Path
from authority import ROOT, manifest, need, repository_path, sha, verify_authority


def validate_output(root, output):
    path = Path(output)
    need(path.is_absolute(), 'STOP_OUTPUT_ABSOLUTE_REQUIRED')
    need('..' not in path.parts, 'STOP_OUTPUT_PATH_ESCAPE')
    base = root / 'results/routeA/diagnostic_transient/timing_qualification'
    need(path != base and base in path.parents, 'STOP_QUALIFICATION_NAMESPACE')
    repository_path(root, str(path.relative_to(root)))
    need(base.resolve() in path.resolve().parents, 'STOP_OUTPUT_REALPATH_ESCAPE')
    return str(path)


def reject_execution_input(value):
    if isinstance(value, dict):
        for key, item in value.items():
            need(key not in {'command', 'binary', 'case', 'case_execution', 'foamRun',
                             'solver', 'solver_binary', 'production_run_authorized', 'qualification'},
                 'STOP_CFD_OR_PRODUCTION_INPUT')
            reject_execution_input(item)
    elif isinstance(value, list):
        for item in value:
            reject_execution_input(item)


def validate_permission(spec):
    reject_execution_input(spec)
    allowed = {'mode', 'output_root', 'authorization', 'plan_sha256', 'prerequisites'}
    need(set(spec) == allowed, 'STOP_UNKNOWN_OR_MISSING_PERMISSION_FIELD')
    mode = spec['mode']
    need(mode in ('Q0', 'Q1', 'Q2', 'Q3'), 'STOP_UNKNOWN_QUALIFICATION_MODE')
    receipt = verify_authority()
    m = manifest()
    plan_rel = 'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_bounded_timing_qualification_plan.json'
    need(spec['plan_sha256'] == m['pinned_repository_files'][plan_rel], 'STOP_QUALIFICATION_PLAN_SHA')
    validate_output(ROOT, spec['output_root'])
    auth = spec['authorization']
    need(set(auth) == {'scope', 'task_reference', 'allowed_stages'}, 'STOP_AUTHORIZATION_SCHEMA')
    need(auth['scope'] == m['permission_matrix'][mode]['authorization_scope'], 'STOP_AUTHORIZATION_SCOPE')
    need(isinstance(auth['task_reference'], str) and auth['task_reference'].strip(), 'STOP_EXPLICIT_AUTHORIZATION_REQUIRED')
    need(isinstance(auth['allowed_stages'], list) and mode in auth['allowed_stages']
         and all(x in ('Q0', 'Q1', 'Q2', 'Q3') for x in auth['allowed_stages']), 'STOP_STAGE_PERMISSION')
    if mode != 'Q3':
        need('Q3' not in auth['allowed_stages'], 'STOP_NONCFD_TO_Q3_ESCALATION')
    else:
        need(auth['allowed_stages'] == ['Q3'], 'STOP_Q3_SEPARATE_AUTHORIZATION')
    prior = spec['prerequisites']
    keys = {'Q0_status', 'Q1_status', 'Q2_status', 'memory_status', 'IO_status',
            'Q1_planning_classification', 'U03_revision_required',
            'user_runtime_budget_seconds', 'continuous_run_risk_accepted'}
    need(isinstance(prior, dict) and set(prior) <= keys, 'STOP_PREREQUISITE_SCHEMA')
    if mode in ('Q1', 'Q2', 'Q3'):
        need(prior.get('Q0_status') == 'PASS', 'STOP_Q0_NOT_PASS')
    if mode in ('Q2', 'Q3'):
        need(prior.get('Q1_status') == 'PASS', 'STOP_Q1_NOT_PASS')
    if mode == 'Q3':
        need(all(prior.get(x) == 'PASS' for x in ('Q2_status', 'memory_status', 'IO_status')), 'STOP_Q3_PREREQUISITES')
        need(prior.get('Q1_planning_classification') in ('CLEARLY_PRACTICAL', 'POTENTIALLY_PRACTICAL')
             and prior.get('U03_revision_required') is False, 'STOP_Q3_DIAGNOSTIC_RISK')
        budget = prior.get('user_runtime_budget_seconds')
        need(type(budget) in (int, float) and math.isfinite(budget) and budget > 0
             and prior.get('continuous_run_risk_accepted') is True, 'STOP_Q3_RUNTIME_BUDGET')
    # A declaration passing validation is neither verified external user permission
    # nor a launch capability. Harness/watchdog receipts and execution remain absent.
    return {'authority_compatibility': receipt['RUNTIME_AUTHORITY_COMPATIBILITY'],
            'mode': mode, 'permission_declaration_valid': True,
            'execution_authorized': False, 'production_run_authorized': False,
            'execution_implemented': False, 'output_root': spec['output_root'],
            'no_write_performed': True,
            'remaining_blockers': ['target native adapter', 'independent watchdog',
                                   'actual stage receipts', 'explicit future measurement task']}
