"""Read-only and temporary-directory tests; no CFD or qualification benchmarks."""
import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import authority as a
import production as prod
import qualification as q


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = a.verify_authority()
        cls.m = a.manifest()
        cls.old = a.load(a.ROOT / cls.m['implementation_contract_path'])
        cls.canonical = a.load(a.ROOT / cls.m['canonical_path'])
        cls.report = a.load(a.ROOT / a.PREP / 'DiagnosticTransient_v1_4_authority_consistency_fix.json')
        cls.audit = a.checker(a.ROOT)

    def permission(self, mode='Q1'):
        return {'mode': mode, 'output_root': str(a.ROOT / 'results/routeA/diagnostic_transient/timing_qualification/TEST_DECLARATION_ONLY'),
                'plan_sha256': self.m['pinned_repository_files'][a.PREP + 'DiagnosticTransient_bounded_timing_qualification_plan.json'],
                'authorization': {'scope': self.m['permission_matrix'][mode]['authorization_scope'],
                                  'task_reference': 'SYNTHETIC_UNIT_ONLY_NOT_ACTUAL_PERMISSION', 'allowed_stages': [mode]},
                'prerequisites': {'Q0_status': 'PASS', 'Q1_status': 'PASS'}}

    def test_exact_registered_compatibility(self):
        self.assertEqual(self.receipt['RUNTIME_AUTHORITY_COMPATIBILITY'], 'PASS')
        self.assertEqual(self.receipt['RESOURCE_READINESS'], 'NO')
        self.assertFalse(self.receipt['production_run_authorized'])
        self.assertEqual(self.receipt['native_and_library_identities_verified'], 851)

    def test_unknown_or_unversioned_authority(self):
        for version in ('1.6', '2.0', None):
            c = copy.deepcopy(self.canonical)
            c['version'] = version
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_AUTHORITY_VERSION'):
                a.verify_lineage(self.old, c, self.report, self.audit)

    def test_scientific_persistence_capacity_and_seal_mutations(self):
        for path in [('transient_algorithm', 'frozen_switches'),
                     ('sampling', 'full_fields'), ('resource_revision_fix', 'capacity'),
                     ('resource_revision_fix', 'retention'), ('resource_revision_fix', 'lifecycle'),
                     ('resource_revision_fix', 'purge_allowlist_only')]:
            c = copy.deepcopy(self.canonical)
            c[path[0]][path[1]] = 'UNIT_MODIFIED'
            with self.assertRaises(ValueError):
                a.verify_lineage(self.old, c, self.report, self.audit)

    def test_erratum_is_exact_not_blanket_timestamp_exemption(self):
        c = copy.deepcopy(self.canonical)
        c['prepared_at'] = 'unknown timestamp'
        with self.assertRaisesRegex(ValueError, 'UNREGISTERED_REPORT_ERRATUM'):
            a.verify_lineage(self.old, c, self.report, self.audit)

    def test_wrong_canonical_formal_implementation_observer_plan_sha(self):
        paths = [a.ROOT / self.m['canonical_path'], a.ROOT / self.m['formal_path'],
                 a.ROOT / 'Scripts/routeA/diagnostic_transient/v1_4/launcher.py',
                 a.ROOT / self.m['replacement_observer_path'],
                 a.ROOT / a.PREP / 'DiagnosticTransient_bounded_timing_qualification_plan.json']
        original = a.sha
        for target in paths:
            with patch.object(a, 'sha', side_effect=lambda p, t=target: '0'*64 if Path(p) == t else original(p)):
                with self.assertRaisesRegex(ValueError, 'PINNED_SHA256'):
                    a.verify_authority()

    def test_missing_registered_implementation_and_native_change(self):
        target = next(iter(self.canonical['u04_build_authority']['native_source_sha256']))
        original = a.sha
        with patch.object(a, 'sha', side_effect=lambda p: '0'*64 if str(p) == target else original(p)):
            with self.assertRaisesRegex(ValueError, 'PINNED_SHA256'):
                a.verify_authority()

    def test_contract_path_spoof(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / Path(self.m['canonical_path']).name
            fake.write_bytes((a.ROOT / self.m['canonical_path']).read_bytes())
            with self.assertRaisesRegex(ValueError, 'CANONICAL_PATH_SPOOF'):
                a.verify_authority(fake)

    def test_symlink_realpath_and_hash_target_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); f = root / 'file'; f.write_text('UNIT_ONLY'); link = root / 'link';link.symlink_to(f)
            a.verify_file(link, a.sha(f), str(f.resolve()))
            with self.assertRaisesRegex(ValueError, 'REALPATH_IDENTITY'):
                a.verify_file(link, a.sha(f), str(root / 'wrong'))
            with self.assertRaisesRegex(ValueError, 'REPOSITORY_SYMLINK'):
                a.repository_path(root, 'link')
            f.write_text('UNIT_CHANGED')
            with self.assertRaisesRegex(ValueError, 'PINNED_SHA256'):
                a.verify_file(f, '0'*64)

    def test_duplicate_json_field(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'duplicate.json';f.write_text('{"mode":"Q1","mode":"PRODUCTION"}')
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_AUTHORITY_KEY'):
                a.load(f)

    def test_actual_production_run_stops_before_preflight_or_output(self):
        with patch.object(prod, 'prepare', side_effect=AssertionError('MUST_NOT_REACH_PREFLIGHT')):
            for auth in (None, 'UNIT_ONLY'):
                with self.assertRaisesRegex(ValueError, 'RESOURCE_READY_NO_NO_EXECUTION'):
                    prod.run({'qualification': True, 'resource_ready': True}, auth)

    def test_synthetic_ready_without_explicit_authorization_stops(self):
        receipt = dict(self.receipt, resource_ready=True)
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_RUN_AUTHORIZATION_REQUIRED'):
            prod.production_guards(receipt, None)

    def test_preflight_bridge_maps_without_mutating_authority_or_spec(self):
        path = a.ROOT / self.m['canonical_path']
        entry = {'path': str(path), 'realpath': str(path.resolve()), 'sha256': a.sha(path)}
        spec = {'provenance': {'contract': [entry]}, 'case_id': 'UNIT_ONLY',
                'export_root': str(a.ROOT / 'results/routeA/diagnostic_transient/diagnostic_attempt_001/series/UNIT_ONLY')}
        before = copy.deepcopy(spec)
        with patch.object(prod, 'legacy_prepare', return_value={'resource_ready': False}) as legacy:
            result = prod.prepare(spec)
            mapped = legacy.call_args.args[0]
        self.assertEqual(a.load(mapped['provenance']['contract'][0]['path'])['version'], '1.4')
        self.assertEqual(result['contract_path'], str(path))
        self.assertFalse(result['resource_ready'])
        self.assertEqual(spec, before)

    def test_production_namespace_and_override_rejected(self):
        path = a.ROOT / self.m['canonical_path']
        spec = {'provenance': {'contract': [{'path': str(path), 'realpath': str(path.resolve()), 'sha256': a.sha(path)}]},
                'case_id': 'UNIT_ONLY', 'export_root': str(a.ROOT / 'results/routeA/diagnostic_transient/timing_qualification/UNIT_ONLY')}
        with self.assertRaisesRegex(ValueError, 'UNREGISTERED_EXPORT_NAMESPACE'):
            prod.prepare(spec)
        with self.assertRaisesRegex(ValueError, 'PRODUCTION_OVERRIDE'):
            prod.prepare(dict(spec, qualification=True))

    def test_q0_q1_q2_declarations_cannot_execute(self):
        for mode in ('Q0', 'Q1', 'Q2'):
            result = q.validate_permission(self.permission(mode))
            self.assertTrue(result['permission_declaration_valid'])
            self.assertFalse(result['execution_authorized'])
            self.assertFalse(result['execution_implemented'])

    def test_q1_cfd_and_nested_privilege_escalation(self):
        for key in ('command', 'binary', 'case', 'foamRun', 'solver_binary', 'qualification'):
            s = self.permission(); s[key] = 'foamRun'
            with self.assertRaisesRegex(ValueError, 'CFD_OR_PRODUCTION_INPUT'):
                q.validate_permission(s)
            s = self.permission(); s['prerequisites'][key] = 'foamRun'
            with self.assertRaisesRegex(ValueError, 'CFD_OR_PRODUCTION_INPUT'):
                q.validate_permission(s)

    def test_wrong_unknown_mode_scope_stage_and_plan(self):
        for change in ({'mode': 'PRODUCTION'}, {'mode': 'unknown'}, {'unexpected': True}, {'plan_sha256': '0'*64}):
            with self.assertRaises(ValueError):
                q.validate_permission(dict(self.permission(), **change))
        for change in ({'scope': 'PRODUCTION_CFD'}, {'task_reference': ''}, {'allowed_stages': ['Q3']}, {'allowed_stages': ['Q1', 'Q3']}):
            s = self.permission(); s['authorization'].update(change)
            with self.assertRaises(ValueError):
                q.validate_permission(s)

    def test_qualification_production_namespace_traversal_symlink(self):
        s = self.permission();s['output_root'] = str(a.ROOT / 'results/routeA/diagnostic_transient/diagnostic_attempt_001/series/UNIT_ONLY')
        with self.assertRaisesRegex(ValueError, 'QUALIFICATION_NAMESPACE'):
            q.validate_permission(s)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);base = root / 'results/routeA/diagnostic_transient/timing_qualification';base.mkdir(parents=True)
            production = root / 'series';production.mkdir();(base / 'escape').symlink_to(production)
            for output in (str(base / '../series/UNIT_ONLY'),str(base / 'escape/UNIT_ONLY')):
                with self.assertRaises(ValueError):
                    q.validate_output(root, output)

    def test_q3_separate_authorization_and_all_prior_gates(self):
        s = self.permission('Q3');s['authorization']['scope'] = 'NONCFD_TIMING_QUALIFICATION'
        with self.assertRaisesRegex(ValueError, 'AUTHORIZATION_SCOPE'):
            q.validate_permission(s)
        s = self.permission('Q3')
        with self.assertRaisesRegex(ValueError, 'Q3_PREREQUISITES'):
            q.validate_permission(s)
        s['prerequisites'].update(Q2_status='PASS',memory_status='PASS',IO_status='PASS',
                                 Q1_planning_classification='POTENTIALLY_PRACTICAL',U03_revision_required=False,
                                 user_runtime_budget_seconds=3600,continuous_run_risk_accepted=True)
        self.assertFalse(q.validate_permission(s)['execution_authorized'])
        for key,value in [('memory_status','UNRESOLVED'),('Q1_planning_classification','HIGH_RISK'),
                          ('user_runtime_budget_seconds',None),('U03_revision_required',True)]:
            bad = copy.deepcopy(s);bad['prerequisites'][key] = value
            with self.assertRaises(ValueError):
                q.validate_permission(bad)

    def test_qualification_module_has_no_launch_dispatch(self):
        tree = ast.parse(Path(q.__file__).read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names]
        self.assertTrue(set(imports) <= {'math', 'pathlib', 'authority'})
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr in ('run','Popen','system','exec','spawn') for n in ast.walk(tree)))


if __name__ == '__main__':
    unittest.main()
