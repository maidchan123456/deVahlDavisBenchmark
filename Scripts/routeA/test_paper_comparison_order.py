"""Synthetic key/order fixtures and unchanged paper-difference semantics."""

import ast
import inspect
import unittest

import analyze_case as analyzer


class PaperComparisonOrderTests(unittest.TestCase):
    def setUp(self):
        self.reference = analyzer.read_paper_reference(analyzer.PAPER_REFERENCE)[1000]
        main = ast.parse(inspect.getsource(analyzer.main)).body[0]
        self.main = main
        self.calculated_node = next(
            node.value for node in ast.walk(main)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "calculated" for target in node.targets)
        )
        self.keys = {key.value for key in self.calculated_node.keys}

    def test_reference_key_coverage(self):
        self.assertLessEqual(set(self.reference), self.keys)
        analyzer.require_paper_comparison_keys(dict.fromkeys(self.keys, 1.0), self.reference)

    def test_velocity_keys_available_before_comparison(self):
        mapping = {key.value: value.id for key, value in zip(self.calculated_node.keys, self.calculated_node.values)
                   if isinstance(value, ast.Name)}
        self.assertEqual(mapping, {"Umax": "umax", "Umax_Z": "umax_loc", "Wmax": "vmax", "Wmax_X": "vmax_loc"})
        guard = next(node for node in ast.walk(self.main) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "require_paper_comparison_keys")
        for name in mapping.values():
            assignment = next(node for node in ast.walk(self.main) if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
            self.assertLess(assignment.lineno, guard.lineno)

    def test_missing_Umax_controlled_failure(self):
        calculated = dict.fromkeys(self.keys, 1.0)
        del calculated["Umax"]
        with self.assertRaisesRegex(ValueError, "PAPER_COMPARISON_CALCULATED_KEY_MISSING: Umax"):
            analyzer.require_paper_comparison_keys(calculated, self.reference)

    def test_blank_Nu_bar_1_special_handling(self):
        self.assertNotIn("Nu_bar_1", self.reference)
        text = inspect.getsource(analyzer.main)
        self.assertIn('paper_comparison["Nu_bar_1"]', text)
        self.assertIn('"reference": None', text)
        self.assertIn('"Table V contains no independent cold-wall mean reference"', text)

    def test_paper_difference_semantics(self):
        scalar = analyzer.paper_difference(3.0, 2.0, False)
        self.assertEqual(scalar["absolute_relative_error"], 0.5)
        self.assertEqual(scalar["signed_relative_difference"], 0.5)
        position = analyzer.paper_difference(0.1, 0.2, True)
        self.assertEqual(position["absolute_position_error"], 0.1)
        self.assertEqual(position["signed_position_difference"], -0.1)
        negative = analyzer.paper_difference(1.0, -2.0, False)
        self.assertEqual(negative["absolute_relative_error"], 1.5)
        self.assertEqual(negative["signed_relative_difference"], -1.5)
        # Preserve the existing comparison dispatch in this order-only fix.
        self.assertIn('key.endswith("_Z")', inspect.getsource(analyzer.main))


if __name__ == "__main__":
    unittest.main()
