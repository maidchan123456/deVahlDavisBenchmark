"""Synthetic parser fixtures, not CFD evidence. Run with python -m unittest."""

import json
import unittest
from pathlib import Path

from runtime_provenance import check_runtime, expected_runtime

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / "docs/routeA_execution_contract_v1.1.json").read_text())
THERMO = """type heRhoThermo;
mixture pureMixture;
transport const;
thermo eConst;
equationOfState Boussinesq;
specie specie;
energy sensibleInternalEnergy;"""
PREFIX = """Version: 13
Build : 13-441953dfbb42
Selecting solver fluid
Selecting thermodynamics package
"""
SUFFIX = """Selecting turbulence model type laminar
Selecting laminar stress model Stokes
Selecting thermophysical transport type laminar
Selecting laminar thermophysical transport model Fourier
PIMPLE: Operating solver in SIMPLE mode
"""


def fixture(thermo=THERMO):
    return PREFIX + "{\n" + thermo + "\n}\n" + SUFFIX


class RuntimeProvenanceTests(unittest.TestCase):
    def check(self, text):
        return check_runtime(text.splitlines(), CONTRACT)

    def test_expected_multiline(self):
        result = self.check(fixture())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["actual"], expected_runtime(CONTRACT))

    def test_type_missing(self):
        result = self.check(fixture(THERMO.replace("type heRhoThermo;", "")))
        self.assertEqual(result["failure_class"], "RUNTIME_EVIDENCE_MISSING")
        self.assertIn("thermo.type", result["missing"])

    def test_wrong_EOS(self):
        result = self.check(fixture(THERMO.replace("Boussinesq", "perfectGas")))
        self.assertEqual(result["failure_class"], "RUNTIME_MODEL_MISMATCH")
        self.assertEqual(result["mismatches"][0]["key"], "thermo.equationOfState")

    def test_reordered(self):
        self.assertEqual(self.check(fixture("\n".join(reversed(THERMO.splitlines()))))["status"], "PASS")

    def test_whitespace(self):
        text = fixture().replace(" ", "\t").replace("\n", "\n  ")
        self.assertEqual(self.check(text)["status"], "PASS")

    def test_normal_runtime_lines(self):
        result = self.check(fixture())
        for key, value in {"stress_model": "Stokes", "thermal_model": "Fourier", "algorithm": "SIMPLE"}.items():
            self.assertEqual(result["actual"][key], value)

    def test_wrong_stress(self):
        result = self.check(fixture().replace("model Stokes", "model wrongStress"))
        self.assertEqual(result["failure_class"], "RUNTIME_MODEL_MISMATCH")
        self.assertEqual(result["mismatches"][0]["key"], "stress_model")

    def test_each_required_key_missing_and_wrong(self):
        for key, value in expected_runtime(CONTRACT).items():
            with self.subTest(key=key):
                if key.startswith("thermo."):
                    text = fixture().replace(key[7:] + " " + value + ";", "")
                else:
                    text = "\n".join(line for line in fixture().splitlines() if value not in line)
                self.assertEqual(self.check(text)["failure_class"], "RUNTIME_EVIDENCE_MISSING")
                if key.startswith("thermo."):
                    wrong = fixture().replace(key[7:] + " " + value + ";", key[7:] + " wrongValue;")
                else:
                    wrong = fixture().replace(value, "wrongValue")
                self.assertEqual(self.check(wrong)["failure_class"], "RUNTIME_MODEL_MISMATCH")

    def test_unclosed_block(self):
        self.assertEqual(self.check(fixture().replace("}\n", ""))["failure_class"], "RUNTIME_EVIDENCE_MISSING")

    def test_duplicate_key(self):
        self.assertEqual(self.check(fixture(THERMO + "\ntype heRhoThermo;"))["failure_class"], "RUNTIME_MODEL_MISMATCH")

    def test_multiple_blocks(self):
        text = fixture() + "Selecting thermodynamics package\n{\n" + THERMO + "\n}\n"
        self.assertEqual(self.check(text)["failure_class"], "RUNTIME_MODEL_MISMATCH")

    def test_unrelated_tokens_do_not_supply_evidence(self):
        result = self.check(THERMO + SUFFIX)
        self.assertEqual(result["failure_class"], "RUNTIME_EVIDENCE_MISSING")
        self.assertIn("thermo.type", result["missing"])


if __name__ == "__main__":
    unittest.main()
