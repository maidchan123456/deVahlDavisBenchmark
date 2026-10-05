"""Read-only v1.5 authority audit. Never imports a launcher or executes CFD."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = 'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/'
SCOPE = 'MACHINE_AUTHORITY_CONSISTENCY_ONLY'
TASK = 'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_V1_4_AUTHORITY_CONSISTENCY'
NEXT = 'REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY'
GUARD = 'DIAGNOSTIC_TRANSIENT_RESOURCE_QUALIFICATION_PENDING_NO_RUN_AUTHORIZATION'
HASHES = {
    '1.2': '7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd',
    '1.3': '212c1dc5056775e1825e13f29336ce51483679862e5e41c1e164f8c724db21b3',
    '1.4': 'c58096f1b6422003c16884e7b8d3c0bb828d9ea797ae59fca9605229af597a82',
    'formal': 'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60',
}
COMPONENTS = {'STORAGE': 'READY', 'LIVE_BINDING': 'READY',
              'EVIDENCE_LIFECYCLE': 'READY', 'MEMORY': 'UNRESOLVED',
              'IO': 'UNRESOLVED', 'COMPUTE': 'UNRESOLVED',
              'OVERALL_RESOURCE': 'NOT_READY'}
SCIENTIFIC = ('physical_problem governing_equations transient_algorithm initial_condition '
              'spatial_discretization temporal_discretization courant_control series '
              'inner_convergence dimensionless_time duration steady_arrival QoIs '
              'mass_diagnostic energy_diagnostic thermo_rho_synchronization temporal_comparison').split()
# Exact leaf allowlist; newly added metadata objects have explicit namespaces.
ALLOWED = {
    '/version': 'STATUS_METADATA', '/prepared_at': 'PROVENANCE_METADATA',
    '/task': 'STATUS_METADATA', '/document_state': 'STATUS_METADATA',
    '/decision_type': 'PROVENANCE_METADATA',
    '/diagnostic_execution_guard': 'GUARD_METADATA',
    '/authority_provenance/HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/HEAD_equals_requested': 'PROVENANCE_METADATA',
    '/sampling/full_fields/production_binding_qualified': 'READINESS_METADATA',
    '/resource_revision/U04_scope': 'STATUS_METADATA',
    '/resource_revision/commit/normal_discard': 'STATUS_METADATA',
    '/resource_revision/trust_basis/6': 'GUARD_METADATA',
    '/resource_revision/resource_guards/native_primary_binding_complete': 'READINESS_METADATA',
    '/pre_run_resource_review/revision_complete': 'STATUS_METADATA',
    '/pre_run_resource_review/next_single_task': 'STATUS_METADATA',
    '/pre_run_resource_review/planning_model': 'PROVENANCE_METADATA',
    '/final_status/DIAGNOSTIC_CONTRACT_VERSION': 'STATUS_METADATA',
    '/final_status/FINAL_DIAGNOSTIC_CONTRACT_VERSION': 'STATUS_METADATA',
    '/final_status/PARENT_DIAGNOSTIC_CONTRACT_SHA256': 'PROVENANCE_METADATA',
    '/final_status/SAMPLING_RULE': 'STATUS_METADATA',
}
for index in (23, 24, 25):
    for leaf in ('item', 'status', 'blocker', 'evidence'):
        ALLOWED[f'/readiness_checklist/{index}/{leaf}'] = 'READINESS_METADATA'
NEW_METADATA = {
    '/readiness_checklist/23/evidence': 'READINESS_METADATA',
    '/readiness_checklist/24/evidence': 'READINESS_METADATA',
    '/revision_scope': 'STATUS_METADATA',
    '/consistency_revision': 'PROVENANCE_METADATA',
    '/resource_readiness_components': 'READINESS_METADATA',
    '/current_execution_blockers': 'GUARD_METADATA',
    '/resource_revision/resource_guards/storage_guard_authority': 'RESOURCE_GUARD_CLARIFICATION',
    '/authority_provenance/original_preparation_HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/original_contract_fix_input_HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/original_contract_fix_HEAD_equals_requested': 'PROVENANCE_METADATA',
    '/authority_provenance/resource_revision_parent_HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/v1_4_fix_input_HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/current_consistency_fix_input_HEAD': 'PROVENANCE_METADATA',
    '/authority_provenance/HEAD_semantics': 'PROVENANCE_METADATA',
    '/pre_run_resource_review/resource_revision_complete': 'STATUS_METADATA',
    '/pre_run_resource_review/storage_revision_complete': 'STATUS_METADATA',
    '/pre_run_resource_review/overall_resource_ready': 'READINESS_METADATA',
    '/pre_run_resource_review/compute_review_required': 'READINESS_METADATA',
    '/pre_run_resource_review/review_scope': 'STATUS_METADATA',
    '/final_status/PARENT_DIAGNOSTIC_CONTRACT_PATH': 'PROVENANCE_METADATA',
    '/final_status/FORMAL_ROUTE_A_CONTRACT_SHA256': 'PROVENANCE_METADATA',
    '/final_status/CURRENT_EXECUTION_GUARD': 'GUARD_METADATA',
    '/final_status/EXECUTION_AUTHORIZED': 'GUARD_METADATA',
    '/final_status/COMPLETE_EXECUTION_CONFIGURATION_FROZEN': 'READINESS_METADATA',
    '/final_status/ROUTE_A_DIAGNOSTIC_TRANSIENT_AUTHORITY_CONSISTENCY_FIX': 'STATUS_METADATA',
    '/final_status/REVISION_SCOPE': 'STATUS_METADATA',
    '/final_status/LEGACY_0P55_GUARD_STATUS': 'RESOURCE_GUARD_CLARIFICATION',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    # Duplicate JSON keys must fail instead of silently replacing authority.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def leaves(value, path=''):
    if isinstance(value, dict) and value:
        for key, child in value.items():
            yield from leaves(child, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from leaves(child, path + '/' + str(index))
    else:
        yield path, value


def semantic_diff(old, new):
    a, b = dict(leaves(old)), dict(leaves(new))
    rows = []
    for path in sorted(a.keys() | b.keys()):
        if path in a and path in b and type(a[path]) is type(b[path]) and a[path] == b[path]:
            continue
        category = ALLOWED.get(path)
        if category is None and path not in a:
            category = next((cat for prefix, cat in NEW_METADATA.items()
                             if path == prefix or path.startswith(prefix + '/')), None)
        rows.append({'path': path, 'category': category or 'OUT_OF_SCOPE',
                     'operation': 'ADD' if path not in a else 'REMOVE' if path not in b else 'CHANGE',
                     'before': a.get(path), 'after': b.get(path)})
    return rows


def check(c, root=ROOT):
    errors, checks = [], []
    def require(ok, code, detail=''):
        checks.append({'check': code, 'pass': bool(ok)})
        if not ok:
            errors.append({'code': code, 'detail': detail})

    s, rr, pre = c['final_status'], c['resource_revision'], c['pre_run_resource_review']
    guards, q = rr['resource_guards'], rr['qualification']
    source_path = root / 'docs/routeA_diagnostic_transient_contract_v1.4.json'
    old = load(source_path)
    require(c['version'] == '1.5' and c['task'] == TASK and c['revision_scope'] == SCOPE,
            'REVISION_IDENTITY')
    require(s['DIAGNOSTIC_CONTRACT_VERSION'] == c['version']
            and s['FINAL_DIAGNOSTIC_CONTRACT_VERSION'] == c['version']
            and s['REVISION_SCOPE'] == c['revision_scope']
            and s['ROUTE_A_DIAGNOSTIC_TRANSIENT_AUTHORITY_CONSISTENCY_FIX'] == 'COMPLETE',
            'DUPLICATE_CURRENT_REVISION_STATUS')
    revision = c['consistency_revision']
    require(revision['source_version'] == '1.4'
            and revision['source_path'] == 'docs/routeA_diagnostic_transient_contract_v1.4.json'
            and revision['source_sha256'] == HASHES['1.4']
            and revision['source_preserved_byte_for_byte'] is True
            and revision['scope'] == SCOPE, 'SOURCE_REVISION_PROVENANCE')
    require(sha(source_path) == HASHES['1.4'], 'IMMUTABLE_V1_4_HASH')
    for label, section, version, path, digest in (
        ('PARENT', c['parent_diagnostic_authority'], '1.2',
         'docs/routeA_diagnostic_transient_contract_v1.2.json', HASHES['1.2']),
        ('FORMAL', c['formal_authority'], '1.7',
         'docs/routeA_execution_contract_v1.7.json', HASHES['formal']),
    ):
        require(section['version'] == version and section['path'] == path
                and section['sha256'] == digest and sha(root / path) == digest,
                label + '_VERSION_PATH_SHA')
    parent = c['parent_diagnostic_authority']
    require(s['PARENT_DIAGNOSTIC_CONTRACT_VERSION'] == parent['version']
            and s['PARENT_DIAGNOSTIC_CONTRACT_SHA256'] == parent['sha256']
            and s['PARENT_DIAGNOSTIC_CONTRACT_PATH'] == parent['path'], 'PARENT_DUPLICATE_STATUS')
    require(s['FORMAL_ROUTE_A_CONTRACT_VERSION'] == c['formal_authority']['version']
            and s['FORMAL_ROUTE_A_CONTRACT_SHA256'] == c['formal_authority']['sha256'],
            'FORMAL_DUPLICATE_STATUS')
    lineage = c['consistency_revision']['lineage']
    require([x['version'] for x in lineage] == ['1.2', '1.3', '1.4', '1.5'], 'VERSION_LINEAGE')
    require(lineage[-1]['path'] == 'docs/routeA_diagnostic_transient_contract_v1.5.json',
            'CURRENT_LINEAGE_PATH')
    for entry in lineage[:3]:
        v = entry['version']
        path = f'docs/routeA_diagnostic_transient_contract_v{v}.json'
        require(entry['path'] == path and entry['sha256'] == HASHES[v]
                and sha(root / path) == HASHES[v], 'LINEAGE_HASH_' + v)
    require(c['resource_candidate_lineage'] == old['resource_candidate_lineage'], 'HISTORICAL_CANDIDATE')
    require(c['resource_readiness_components'] == COMPONENTS, 'READINESS_COMPONENTS')
    require(all(s['DIAGNOSTIC_TRANSIENT_' + key] == 'YES' for key in
                ('SCIENTIFICALLY_ALLOWED', 'TECHNICALLY_READY', 'STORAGE_READY')),
            'SCIENTIFIC_TECHNICAL_STORAGE_READY')
    require(s['STORAGE_FEASIBILITY'] == 'FEASIBLE', 'STORAGE_STATUS')
    require(all(s[x + '_FEASIBILITY'] == 'UNRESOLVED' for x in ('MEMORY', 'IO', 'COMPUTE'))
            and q['memory_IO_compute'] == 'UNRESOLVED', 'UNRESOLVED_RESOURCES')
    require(s['DIAGNOSTIC_TRANSIENT_RESOURCE_READY'] == 'NO'
            and pre['resource_ready'] is False and pre['overall_resource_ready'] is False
            and guards['production_resource_ready'] is False, 'RESOURCE_READINESS_HIERARCHY')
    require(c['execution_authorized'] is False and pre['run_authorized'] is False
            and s['EXECUTION_AUTHORIZED'] == 'NO', 'NO_RUN_AUTHORIZATION')
    require(c['complete_execution_configuration_frozen'] is False
            and s['COMPLETE_EXECUTION_CONFIGURATION_FROZEN'] == 'NO', 'CONFIGURATION_NOT_FROZEN')
    require(c['diagnostic_execution_guard'] == GUARD and s['CURRENT_EXECUTION_GUARD'] == GUARD,
            'CURRENT_EXECUTION_GUARD')
    require(c['current_execution_blockers'] == [
        'COMPUTE_FEASIBILITY_UNRESOLVED', 'MEMORY_FEASIBILITY_UNRESOLVED',
        'IO_FEASIBILITY_UNRESOLVED', 'EXPLICIT_FUTURE_RUN_AUTHORIZATION_REQUIRED'],
        'CURRENT_EXECUTION_BLOCKERS')
    require(rr['complete'] is True and c['resource_revision_fix']['complete'] is True
            and pre['revision_complete'] is True and pre['resource_revision_complete'] is True
            and pre['storage_revision_complete'] is True and pre['compute_review_required'] is True
            and s['RESOURCE_REVISION'] == 'COMPLETE'
            and s['ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION_FIX'] == 'COMPLETE',
            'RESOURCE_REVISION_COMPLETION')
    require(q['live_native_binding'] == 'PASS' and guards['native_primary_binding_complete'] is True
            and c['evaluator_verification']['live_primary_binding_complete'] is True
            and c['sampling']['full_fields']['production_binding_qualified'] is True,
            'LIVE_BINDING_COMPLETION')
    require(q['policy_bindings'] == 'PASS' and q['evidence_lifecycle'] == 'PASS'
            and all(s[key] == 'YES' for key in (
                'EVERY_STEP_PRIMARY_SCALARS', 'CO_CONTROLLER_LIVE_BINDING',
                'LINEAR_RESIDUAL_LIVE_BINDING', 'U01_CERTIFICATE_LIVE_BINDING',
                'U03_ARRIVAL_LIVE_BINDING', 'ANOMALY_TRIGGER_BINDING', 'PRODUCTION_PREFLIGHT_BINDING')),
            'POLICY_PREFLIGHT_LIFECYCLE')
    for i in (23, 24):
        item = c['readiness_checklist'][i]
        require(item['status'] == 'FIXED' and item['blocker'] is None and bool(item['evidence']),
                'CLOSED_CHECKLIST_' + str(i))
    require(c['readiness_checklist'][25]['status'] == 'OPEN', 'RESOURCE_QUALIFICATION_OPEN')
    # Traverse ALL current fields for duplicate next tasks, guard and stale blockers.
    # Frozen scientific annotations and inherited evidence are explicitly historical.
    active = {k: v for k, v in c.items() if not k.startswith('inherited_') and k not in
              ('authority_provenance', 'u04_build_authority', 'consistency_revision')}
    next_tasks, stale = [], []
    for path, value in leaves(active):
        if path.lower().endswith(('/next_single_task', '/next_task')):
            next_tasks.append((path, value))
        if isinstance(value, str) and any(text in value.lower() for text in (
            'resource_unqualified', 'production binding not closed', 'production binding blocked',
            'source unqualified for production', 'live collector not implemented',
            'production classification is currently rejected',
            'binding of every required primary/stage column, co/controller receipts and native per-solve residuals is not implemented',
            'production blocked until complete primary/control/certificate/arrival binding qualification')):
            stale.append(path)
    require(len(next_tasks) >= 2 and all(v == NEXT for _, v in next_tasks),
            'UNIQUE_CURRENT_NEXT_TASK', repr(next_tasks))
    require(not stale, 'NO_STALE_ACTIVE_BLOCKERS', repr(stale))
    require(not rr['qualification_blockers'], 'NO_BINDING_QUALIFICATION_BLOCKERS')
    require(all(not item.get('blocker') for item in c['readiness_checklist']
                if item['status'] in ('FIXED', 'CLOSED')), 'NO_CLOSED_ITEM_BLOCKER')
    require(all('storage' not in str(item).lower() for item in c['readiness_checklist']
                if item['status'] == 'OPEN'), 'NO_ACTIVE_PRIMARY_STORAGE_BLOCKER')
    storage = guards['storage_guard_authority']
    require(guards['peak_fraction_of_verified_free_max'] == .55
            and storage['legacy_0p55_guard_status'] == 'PER_SERIES_ONLY'
            and storage['fraction_rule'] == '0 < current_series_working_peak_bytes <= 0.55 * current_verified_free_bytes'
            and storage['sequential_reserve_rule'] == 'current_verified_free_bytes > current_series_working_peak_bytes + measured_existing_permanent_bytes + max(32 * 2**30, int(0.10 * current_verified_free_bytes))'
            and storage['combination'] == 'BOTH_REQUIRED'
            and storage['cumulative_peak_fraction_is_a_run_gate'] is False
            and s['LEGACY_0P55_GUARD_STATUS'] == storage['legacy_0p55_guard_status'],
            'STORAGE_GUARD_SEMANTICS')
    capacity = c['resource_revision_fix']['capacity']
    free = capacity['free_bytes_at_start']
    permanent = 0
    planning = []
    for co in ('0.5', '0.25'):
        model = capacity['series'][co]
        current_free = free - permanent
        peak = model['working_peak_bytes']
        safety = max(32 * 2**30, int(.10 * current_free))
        planning.append({'Co': co, 'planning_current_free': current_free,
                         'working_peak': peak, 'existing_permanent': permanent,
                         'working_peak_fraction': peak / current_free,
                         'fraction_pass': 0 < peak <= .55 * current_free,
                         'reserve_pass': current_free > peak + permanent + safety})
        permanent += model['permanent_bytes']
    require(all(x['fraction_pass'] and x['reserve_pass'] for x in planning), 'PRIMARY_STORAGE_PLANNING_GUARDS')
    p = c['authority_provenance']
    require('HEAD' not in p and 'HEAD_equals_requested' not in p
            and p['original_preparation_HEAD'] == load(root / 'docs/routeA_diagnostic_transient_contract_v1.0.json')['authority_provenance']['HEAD']
            and p['original_contract_fix_input_HEAD'] == old['authority_provenance']['HEAD']
            and p['resource_revision_parent_HEAD'] == load(root / (PREP + 'resource_revision/authority.json'))['HEAD']
            and p['v1_4_fix_input_HEAD'] == load(root / (PREP + 'resource_revision_fix/start_guard.json'))['HEAD']
            and p['current_consistency_fix_input_HEAD'] == '8707aa00785f83b0620fdc6b8847c200f59b3522',
            'HEAD_SEMANTICS')
    for label, path in c['resource_revision_fix']['test_evidence'].items():
        evidence = load(root / path)
        require(evidence['status'] == 'PASS', 'V1_4_EVIDENCE_' + label)
        require(c['consistency_revision']['evidence_sha256'].get(path) == sha(root / path),
                'EVIDENCE_HASH_' + label)
    for path, digest in c['consistency_revision']['evidence_sha256'].items():
        require(sha(root / path) == digest, 'PINNED_EVIDENCE_' + path)
    for key in SCIENTIFIC:
        require(c[key] == old[key], 'SCIENTIFIC_INVARIANT_' + key)
    require(c['resource_revision_fix'] == old['resource_revision_fix'], 'PERSISTENCE_CAPACITY_LIFECYCLE_INVARIANT')
    require(c['formal_status_preserved'] == old['formal_status_preserved'], 'FORMAL_STATUS_INVARIANT')
    for key in old:
        if key.startswith('inherited_'):
            require(c[key] == old[key], 'HISTORICAL_INVARIANT_' + key)
    diff = semantic_diff(old, c)
    require(all(row['category'] != 'OUT_OF_SCOPE' for row in diff), 'SCOPED_SEMANTIC_DIFF',
            repr([row['path'] for row in diff if row['category'] == 'OUT_OF_SCOPE']))
    for path, digest in old['resource_revision_fix']['source_SHA256'].items():
        require(sha(root / path) == digest, 'UNCHANGED_V1_4_SOURCE_' + path)
    require(sha(root / (PREP + 'resource_revision_fix/native/build_verified/librouteAU04Observer.so'))
            == rr['replacement_library_sha256'], 'UNCHANGED_NATIVE_LIBRARY')
    return {'status': 'PASS' if not errors else 'FAIL', 'contradictions': len(errors),
            'errors': errors, 'checks': checks, 'stale_active_blockers': len(stale),
            'mismatched_parent_hashes': sum(x['code'].startswith('PARENT_') for x in errors),
            'conflicting_current_next_tasks': sum(v != NEXT for _, v in next_tasks),
            'scientific_invariants': {key: c[key] == old[key] for key in SCIENTIFIC},
            'storage_guard_planning_checks': planning, 'semantic_diff': diff,
            'historical_scopes': ['inherited_*', 'authority_provenance', 'u04_build_authority',
                                  'consistency_revision', 'inner_convergence.instrumentation_binding_pending',
                                  'steady_arrival.validity_dependency']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', nargs='?', type=Path,
                        default=ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = check(load(args.contract))
        sidecar = args.contract.with_suffix('.sha256')
        if sidecar.exists() and sidecar.read_text().split() != [sha(args.contract), args.contract.name]:
            result['errors'].append({'code': 'SIDECAR_HASH', 'detail': str(sidecar)})
            result['contradictions'] += 1
            result['status'] = 'FAIL'
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result = {'status': 'FAIL', 'contradictions': 1,
                  'errors': [{'code': 'INVALID_AUTHORITY', 'detail': str(exc)}]}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'semantic_diff')}, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
