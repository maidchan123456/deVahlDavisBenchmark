"""Synthetic metadata mutations only; no solver, case, mesh or purge operations."""
import copy
import json
import unittest

from check_contract_consistency import ROOT, check, load


def negative_tests(contract):
    mutations = [
        ('wrong_parent_SHA', ['parent_diagnostic_authority', 'sha256'], '0' * 64, 'PARENT_VERSION_PATH_SHA'),
        ('wrong_duplicate_parent_SHA', ['final_status', 'PARENT_DIAGNOSTIC_CONTRACT_SHA256'], '0' * 64, 'PARENT_DUPLICATE_STATUS'),
        ('wrong_formal_SHA', ['formal_authority', 'sha256'], '0' * 64, 'FORMAL_VERSION_PATH_SHA'),
        ('stale_duplicate_revision_version', ['final_status', 'DIAGNOSTIC_CONTRACT_VERSION'], '1.4', 'DUPLICATE_CURRENT_REVISION_STATUS'),
        ('wrong_source_revision_SHA', ['consistency_revision', 'source_sha256'], '0' * 64, 'SOURCE_REVISION_PROVENANCE'),
        ('binding_PASS_binding_complete_false', ['resource_revision', 'resource_guards', 'native_primary_binding_complete'], False, 'LIVE_BINDING_COMPLETION'),
        ('storage_ready_active_storage_blocker', ['readiness_checklist', 0], {'item': 'primary storage', 'status': 'OPEN', 'blocker': 'storage capacity pending'}, 'NO_ACTIVE_PRIMARY_STORAGE_BLOCKER'),
        ('authorized_resource_not_ready', ['execution_authorized'], True, 'NO_RUN_AUTHORIZATION'),
        ('two_active_next_tasks', ['pre_run_resource_review', 'next_single_task'], 'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION', 'UNIQUE_CURRENT_NEXT_TASK'),
        ('extra_active_next_task', ['extra_status'], {'next_task': 'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION'}, 'UNIQUE_CURRENT_NEXT_TASK'),
        ('old_v1_3_guard', ['diagnostic_execution_guard'], 'DIAGNOSTIC_TRANSIENT_CONTRACT_v1.3_RESOURCE_UNQUALIFIED', 'CURRENT_EXECUTION_GUARD'),
        ('revision_complete_false', ['pre_run_resource_review', 'revision_complete'], False, 'RESOURCE_REVISION_COMPLETION'),
        ('resource_ready_unresolved_compute', ['final_status', 'DIAGNOSTIC_TRANSIENT_RESOURCE_READY'], 'YES', 'RESOURCE_READINESS_HIERARCHY'),
        ('closed_checklist_stale_blocker', ['readiness_checklist', 23, 'blocker'], 'live collector not implemented', 'NO_STALE_ACTIVE_BLOCKERS'),
        ('sampling_binding_false', ['sampling', 'full_fields', 'production_binding_qualified'], False, 'LIVE_BINDING_COMPLETION'),
        ('configuration_frozen_before_qualification', ['complete_execution_configuration_frozen'], True, 'CONFIGURATION_NOT_FROZEN'),
        ('relaxed_55_percent', ['resource_revision', 'resource_guards', 'peak_fraction_of_verified_free_max'], .60, 'STORAGE_GUARD_SEMANTICS'),
        ('cumulative_55_percent_gate', ['resource_revision', 'resource_guards', 'storage_guard_authority', 'cumulative_peak_fraction_is_a_run_gate'], True, 'STORAGE_GUARD_SEMANTICS'),
        ('ambiguous_HEAD_reintroduced', ['authority_provenance', 'HEAD'], '8707aa00785f83b0620fdc6b8847c200f59b3522', 'HEAD_SEMANTICS'),
        ('science_changed', ['transient_algorithm', 'status'], 'CHANGED', 'SCIENTIFIC_INVARIANT_transient_algorithm'),
        ('capacity_changed', ['resource_revision_fix', 'capacity', 'primary_permanent_bytes'], 1, 'PERSISTENCE_CAPACITY_LIFECYCLE_INVARIANT'),
        ('historical_status_changed', ['inherited_v1_3_evaluator_verification', 'live_primary_binding_complete'], True, 'HISTORICAL_INVARIANT_inherited_v1_3_evaluator_verification'),
    ]
    results = []
    for name, path, value, expected in mutations:
        mutated = copy.deepcopy(contract)
        node = mutated
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = value
        report = check(mutated)
        codes = [x['code'] for x in report['errors']]
        results.append({'test': name, 'status': 'PASS' if report['status'] == 'FAIL' and expected in codes else 'FAIL',
                        'expected_failure': expected, 'detected_failures': codes})
    return results


class ConsistencyTests(unittest.TestCase):
    def test_current_authority(self):
        result = check(load(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json'))
        self.assertEqual(result['errors'], [])

    def test_negative_mutations(self):
        contract = load(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json')
        for result in negative_tests(contract):
            with self.subTest(result['test']):
                self.assertEqual(result['status'], 'PASS', json.dumps(result))

    def test_duplicate_json_key_rejected(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duplicate.json'
            path.write_text('{"execution_authorized":false,"execution_authorized":true}')
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
                load(path)


if __name__ == '__main__':
    unittest.main()
