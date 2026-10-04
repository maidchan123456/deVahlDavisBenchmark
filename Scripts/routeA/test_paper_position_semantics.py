"""Amendment 004: actual comparison dispatch and frozen numerical helpers."""

import ast
import importlib.util
import inspect
from pathlib import Path
import unittest

import numpy as np
import analyze_case as analyzer


class PaperPositionSemanticsTests(unittest.TestCase):
    def payload(self, key):
        # Exercise the comprehension used by main, including its classification.
        node = next(n for n in ast.walk(ast.parse(inspect.getsource(analyzer.main)))
                    if isinstance(n, ast.DictComp) and isinstance(n.value, ast.Call)
                    and isinstance(n.value.func, ast.Name)
                    and n.value.func.id == "paper_difference")
        expression = ast.fix_missing_locations(ast.Expression(node))
        return eval(compile(expression, "<canonical-comparison>", "eval"),
                    {**vars(analyzer), "calculated": {key: 0.1},
                     "reference": {key: 0.2}})[key]

    def position(self, key):
        payload = self.payload(key)
        self.assertEqual(payload["signed_position_difference"], -0.1)
        self.assertEqual(payload["absolute_position_error"], 0.1)
        self.assertEqual(payload["error"], -0.1)
        self.assertNotIn("signed_relative_difference", payload)
        self.assertNotIn("absolute_relative_error", payload)

    def scalar(self, key):
        payload = self.payload(key)
        self.assertEqual(payload["signed_relative_difference"], -0.5)
        self.assertEqual(payload["absolute_relative_error"], 0.5)
        self.assertNotIn("signed_position_difference", payload)
        self.assertNotIn("absolute_position_error", payload)

    def test_Wmax_X_position(self): self.position("Wmax_X")
    def test_Umax_Z_position(self): self.position("Umax_Z")
    def test_Nu_hot_local_max_Z_position(self): self.position("Nu_hot_local_max_Z")
    def test_Nu_hot_local_min_Z_position(self): self.position("Nu_hot_local_min_Z")
    def test_Umax_scalar(self): self.scalar("Umax")
    def test_Wmax_scalar(self): self.scalar("Wmax")
    def test_Nu_bar_cavity_scalar(self): self.scalar("Nu_bar_cavity")

    def test_other_scalars_and_suffix_is_not_classification(self):
        for key in ("Nu_bar_half", "Nu_bar_0", "Nu_hot_local_max",
                    "Nu_hot_local_min", "future_scalar_X", "future_scalar_Z"):
            with self.subTest(key=key): self.scalar(key)


class NumericalHelperRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = analyzer.ROOT
        snapshot = root / "results/routeA/attempts/attempt_004/position_semantics_reanalysis/source_before/analyze_case_before.py"
        spec = importlib.util.spec_from_file_location("position_semantics_before", snapshot)
        cls.before = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.before)
        cls.case = root / "cases/routeA/A-Ra1e3-fine"
        cls.log = root / "results/routeA/cases/A-Ra1e3-fine/segments/end_18000/solver.log"

    def equal(self, before, after):
        if isinstance(before, dict):
            self.assertEqual(set(before), set(after))
            for key in before: self.equal(before[key], after[key])
        elif isinstance(before, (list, tuple)):
            self.assertEqual(len(before), len(after))
            for left, right in zip(before, after): self.equal(left, right)
        elif isinstance(before, np.ndarray): np.testing.assert_array_equal(before, after)
        else: self.assertEqual(before, after)

    def test_numerical_helper_outputs_unchanged(self):
        n = 160 * 160
        T = analyzer.read_scalar(self.case / "18000/T", n).reshape(160, 160)
        U = analyzer.read_vector(self.case / "18000/U", n).reshape(160, 160, 3)
        wall = analyzer.read_wall_heat(self.case / "postProcessing/wallHeatFluxMonitor/15000/wallHeatFlux.dat")
        velocity = {t: analyzer.sample_extrema(self.case, t, 1e-5/.71, .1)
                    for t in range(17810, 18001, 10)}
        residuals = analyzer.parse_residuals(self.log)
        z = np.linspace(.05, .95, 10)
        fixtures = {
            "paper_nusselt": [(T, U, 160, 160, .1, 1e-5/.71, 1., 300.5, 299.5)],
            "local_quartic_extremum": [(z, 2-(z-.3)**2, "max"), (z, (z-.7)**2, "min")],
            "sample_extrema": [(self.case, 18000, 1e-5/.71, .1)],
            "evaluate_gate_d_monitors": [(wall, velocity, residuals, 18000, .0001)],
            "parse_residuals": [(self.log,)],
            "classify_health_lines": [(["sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).", "End"],), (["Floating point exception", "FOAM FATAL IO ERROR", "nan"],)],
            "paper_difference": [(0.1, 0.2, True), (3., 2., False), (1., -2., False)],
        }
        for name, arguments in fixtures.items():
            with self.subTest(helper=name):
                self.assertEqual(inspect.getsource(getattr(self.before, name)),
                                 inspect.getsource(getattr(analyzer, name)))
                for args in arguments:
                    self.equal(getattr(self.before, name)(*args), getattr(analyzer, name)(*args))

    def test_only_classification_changed_in_analyzer_AST(self):
        before = ast.parse(inspect.getsource(self.before))
        after = ast.parse(inspect.getsource(analyzer))
        after.body = [node for node in after.body
                      if not (isinstance(node, ast.Assign) and any(
                          isinstance(t, ast.Name) and t.id == "POSITION_KEYS" for t in node.targets))]
        for node in ast.walk(after):
            if isinstance(node, ast.DictComp) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == "paper_difference":
                    node.value.args[2] = ast.parse('key.endswith("_Z")', mode="eval").body
        self.assertEqual(ast.dump(before), ast.dump(after))


if __name__ == "__main__":
    unittest.main()
