"""Pure gate tests and a four-node synthetic estimator sanity check; no CFD."""
import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import protocol as p
import u03_scaling as u


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.plan = p.load(p.PLAN)
        self.digest = p.sha(p.PLAN)
        self.receipt = dict(plan_sha256=self.digest, Q0_status='PASS',
                            runtime_authority_compatibility='PASS',
                            explicit_user_authorization_reference='UNIT_TEST_ONLY',
                            authorization_scope='NONCFD_TIMING_QUALIFICATION',
                            Q1_status='PASS')

    def test_registered_plan(self):
        self.assertEqual(p.validate(self.plan), [])
        self.assertEqual(sum(x['frequency_per_step'] for x in self.plan['callback_classes']), 1144)
        self.assertEqual(sum(x['matrix_packets_per_callback'] * x['frequency_per_step']
                             for x in self.plan['callback_classes']), 701)

    def test_current_gate_cannot_be_overridden_by_receipt(self):
        for stage in ('Q1', 'Q2', 'Q3'):
            with self.assertRaisesRegex(ValueError, 'CURRENT_RUNTIME_REQUIRES_FIX'):
                p.gate(self.plan, stage, self.receipt, self.digest)

    def test_future_gate_fail_closed(self):
        # Hypothetical future reviewed plan, pure function only, never a launcher.
        plan = copy.deepcopy(self.plan)
        plan['current_runtime_compatibility'] = 'PASS'
        for field, value, message in [('plan_sha256', 'wrong', 'PLAN_HASH'),
                                      ('Q0_status', 'UNRESOLVED', 'Q0_NOT_PASS'),
                                      ('runtime_authority_compatibility', 'FAIL', 'COMPATIBILITY'),
                                      ('explicit_user_authorization_reference', '', 'AUTHORIZATION_REQUIRED'),
                                      ('authorization_scope', 'Q3_BOUNDED_CFD_TIMING_QUALIFICATION', 'AUTHORIZATION_SCOPE'),
                                      ('Q1_status', 'UNRESOLVED', 'Q1_NOT_PASS')]:
            r = dict(self.receipt, **{field: value})
            with self.assertRaisesRegex(ValueError, message):
                p.gate(plan, 'Q2', r, self.digest)

    def test_q3_risk_and_budget_gates(self):
        plan = copy.deepcopy(self.plan)
        plan['current_runtime_compatibility'] = 'PASS'
        r = dict(self.receipt, authorization_scope='Q3_BOUNDED_CFD_TIMING_QUALIFICATION',
                 Q2_status='PASS', memory_status='PASS', IO_status='PASS',
                 Q1_planning_classification='POTENTIALLY_PRACTICAL',
                 U03_revision_required=False, user_runtime_budget_seconds=3600,
                 continuous_run_risk_accepted=True)
        self.assertTrue(p.gate(plan, 'Q3', r, self.digest))
        for field, value in [('Q2_status', 'UNRESOLVED'), ('memory_status', 'FAIL'),
                             ('IO_status', 'NOT_MEASURED'),
                             ('Q1_planning_classification', 'HIGH_RISK'),
                             ('U03_revision_required', True),
                             ('user_runtime_budget_seconds', None),
                             ('user_runtime_budget_seconds', float('nan')),
                             ('user_runtime_budget_seconds', -1),
                             ('continuous_run_risk_accepted', False)]:
            with self.assertRaises(ValueError):
                p.gate(plan, 'Q3', dict(r, **{field: value}), self.digest)

    def test_budget_and_frozen_policy_mutations(self):
        for key, value in [('stage_wall_seconds', 0), ('single_trial_wall_seconds', 999),
                           ('native_AS_max_bytes', 16 * 2**30)]:
            plan = copy.deepcopy(self.plan)
            plan['stages']['Q1']['budgets'][key] = value
            self.assertTrue(p.validate(plan))
        plan = copy.deepcopy(self.plan)
        plan['frozen_switches']['nOuterCorrectors'] = 2
        self.assertIn('FROZEN_SWITCHES', p.validate(plan))

    def test_duplicate_authority_keys(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'duplicate.json'
            f.write_text('{"version": "1.5", "version": "1.4"}')
            with self.assertRaisesRegex(ValueError, 'DUPLICATE_AUTHORITY_KEY'):
                p.load(f)

    def test_four_node_fixture_exercises_all_three_windows(self):
        path = p.ROOT / 'Scripts/routeA/diagnostic_transient/v1_1/contract_policy.py'
        spec = importlib.util.spec_from_file_location('unit_frozen_policy', path)
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        times, histories, scales = u.inputs(4, p.load(p.ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json'))
        ok, windows = policy.arrival_candidate(times, histories, .5, scales, True)
        self.assertTrue(ok)
        self.assertEqual(len(windows), 3)
        self.assertTrue(all(len(w) == 8 for w in windows))
        with self.assertRaisesRegex(ValueError, 'UNREGISTERED_HISTORY_SIZE'):
            u.inputs(15001, {})

    def test_u03_timeout_stops_before_larger_sizes(self):
        # Mock all permissions and external work; exercise only timeout bookkeeping.
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            with patch.object(u, 'ROOT', base), patch.object(u, 'gate', return_value=True), \
                    patch.object(u.subprocess, 'run', side_effect=subprocess.TimeoutExpired('UNIT_ONLY', 15)) as run:
                receipt = base / 'receipt.json'
                receipt.write_text(json.dumps(self.receipt))
                output = base / 'results/routeA/diagnostic_transient/timing_qualification/unit_only'
                self.assertEqual(u.run(receipt, output), 1)
                self.assertEqual(run.call_count, 1)
                result = p.load(output / 'u03_results.json')
                self.assertEqual(result['status'], 'STOP_U03_BENCHMARK_LIMIT')
                self.assertEqual(result['rows'][0]['N'], 100)
                self.assertTrue(result['rows'][0]['censored'])
                self.assertIn('ROUTE_A_TIMING_Q2_RECEIPT', run.call_args.kwargs['env'])


if __name__ == '__main__':
    unittest.main()
