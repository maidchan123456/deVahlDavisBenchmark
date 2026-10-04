#!/usr/bin/env python3
"""Read-only Route A runtime model checker; no solver or input mutation."""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path


def expected_runtime(contract: dict) -> dict[str, str]:
    model = contract["frozen_model"]
    thermo_keys = ("type", "mixture", "transport", "thermo", "equationOfState", "specie", "energy")
    thermo_values = model["thermo"].split("/")
    if len(thermo_values) != len(thermo_keys):
        raise ValueError("Unsupported frozen thermo specification")
    regime, stress = model["momentum"].split()
    thermal_regime, thermal_model = model["thermal"].split()
    return {
        "version": model["version"], "build": model["historical_build"],
        "solver": model["solver"].split("solver ", 1)[1],
        **{f"thermo.{key}": value for key, value in zip(thermo_keys, thermo_values)},
        "momentum_regime": regime, "stress_model": stress,
        "thermal_regime": thermal_regime, "thermal_model": thermal_model,
        "algorithm": "SIMPLE",
    }


def collect_runtime_evidence(lines) -> dict:
    """Collect selected runtime records, including the complete thermo block."""
    selections = {}
    blocks = []
    pending = False
    block = None
    patterns = {
        "version": r"\bVersion:\s*(\S+)",
        "build": r"^\s*Build\s*:\s*(\S+)",
        "solver": r"^\s*Selecting\s+solver\s+(\S+)\s*$",
        "momentum_regime": r"^\s*Selecting\s+turbulence\s+model\s+type\s+(\S+)\s*$",
        "stress_model": r"^\s*Selecting\s+laminar\s+stress\s+model\s+(\S+)\s*$",
        "thermal_regime": r"^\s*Selecting\s+thermophysical\s+transport\s+type\s+(\S+)\s*$",
        "thermal_model": r"^\s*Selecting\s+laminar\s+thermophysical\s+transport\s+model\s+(\S+)\s*$",
        "algorithm": r"^\s*PIMPLE:\s*Operating\s+solver\s+in\s+(\S+)\s+mode\s*$",
    }
    for number, line in enumerate(lines, 1):
        for key, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                selections.setdefault(key, []).append({"value": match.group(1), "line": number})
        header = re.search(r"^\s*Selecting\s+thermodynamics\s+package\s*(.*)$", line)
        if header:
            pending = True
            line = header.group(1)
        if pending and "{" in line:
            block = {"start_line": number, "end_line": None, "entries": {}, "duplicates": [], "complete": False}
            blocks.append(block)
            pending = False
            line = line.split("{", 1)[1]
        if block is not None:
            body = line.split("}", 1)[0]
            for key, value in re.findall(r"\b(\w+)\s+(\w+)\s*;", body):
                if key in block["entries"]:
                    block["duplicates"].append(key)
                block["entries"][key] = {"value": value, "line": number}
            if "}" in line:
                block["complete"] = True
                block["end_line"] = number
                block = None
    return {"selections": selections, "thermo_blocks": blocks}


def check_runtime(lines, contract: dict) -> dict:
    evidence = collect_runtime_evidence(lines)
    expected = expected_runtime(contract)
    actual = {}
    missing = []
    mismatches = []
    blocks = evidence["thermo_blocks"]
    if len(blocks) > 1:
        mismatches.append({"key": "thermo_block", "reason": "Multiple selected thermo dictionaries; ambiguous provenance"})
    thermo = blocks[0]["entries"] if len(blocks) == 1 and blocks[0]["complete"] else {}
    if len(blocks) == 1 and blocks[0]["duplicates"]:
        mismatches.append({"key": "thermo_block", "reason": "Duplicate thermo keys", "keys": blocks[0]["duplicates"]})
    for key, wanted in expected.items():
        if key.startswith("thermo."):
            records = [thermo[key[7:]]] if key[7:] in thermo else []
        else:
            records = evidence["selections"].get(key, [])
        values = sorted({record["value"] for record in records})
        if not values:
            missing.append(key)
        else:
            actual[key] = values[0] if len(values) == 1 else values
            if values != [wanted]:
                mismatches.append({"key": key, "expected": wanted, "actual": actual[key]})
    failure = "RUNTIME_MODEL_MISMATCH" if mismatches else "RUNTIME_EVIDENCE_MISSING" if missing else None
    return {
        "status": "FAIL" if failure else "PASS", "failure_class": failure,
        "missing": missing, "mismatches": mismatches,
        "expected": expected, "actual": actual, "evidence": evidence,
        "source": "Actual OpenFOAM runtime log; no fallback to input dictionary or generator manifest",
        "input_provenance_checked": False,
        "health_or_Gate_D_checked": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--max-lines", type=int, default=120,
                        help="Read the startup prefix only (default: 120 lines)")
    args = parser.parse_args()
    if args.max_lines <= 0:
        parser.error("--max-lines must be positive")
    contract = json.loads(args.contract.read_text())
    with args.log.open() as stream:
        result = check_runtime(itertools.islice(stream, args.max_lines), contract)
    result.update(log=str(args.log.resolve()), contract=str(args.contract.resolve()),
                  log_read_scope=f"first {args.max_lines} lines only")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
