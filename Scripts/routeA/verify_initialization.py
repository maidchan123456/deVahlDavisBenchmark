#!/usr/bin/env python3
"""Verify constructor-dumped Route A hydrostatic fields at time zero."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from foam_fields import read_boundary_scalar, read_scalar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("init_case")
    parser.add_argument("output")
    args = parser.parse_args()
    case = Path(args.case).resolve()
    init_case = Path(args.init_case).resolve()
    manifest = json.loads((case / "case_manifest.json").read_text())
    n = int(np.prod(manifest["grid"]))
    p_input = read_scalar(case / "0/p", n)
    prgh_input = read_scalar(case / "0/p_rgh", n)
    p = read_scalar(init_case / "0/p", n)
    prgh = read_scalar(init_case / "0/p_rgh", n)
    rho = read_scalar(init_case / "0/rho", n)
    gh = read_scalar(init_case / "0/gh", n)
    pref = manifest["pRef_Pa"]
    relation = prgh - (p - rho * gh - pref)
    nx, ny, _nz = manifest["grid"]
    patch_sizes = {"hotWall": ny, "coldWall": ny, "bottomWall": nx, "topWall": nx}
    patch_results = {}
    for patch, size in patch_sizes.items():
        p_input_b = read_boundary_scalar(case / "0/p", patch, size)
        prgh_input_b = read_boundary_scalar(case / "0/p_rgh", patch, size)
        p_b = read_boundary_scalar(init_case / "0/p", patch, size)
        prgh_b = read_boundary_scalar(init_case / "0/p_rgh", patch, size)
        rho_b = read_boundary_scalar(init_case / "0/rho", patch, size)
        gh_b = read_boundary_scalar(init_case / "0/gh", patch, size)
        residual_b = prgh_b - (p_b - rho_b * gh_b - pref)
        patch_results[patch] = {
            "max_abs_relation_residual_Pa": float(np.max(np.abs(residual_b))),
            "max_abs_constructor_p_rgh_Pa": float(np.max(np.abs(prgh_b))),
            "max_abs_input_p_rgh_Pa": float(np.max(np.abs(prgh_input_b))),
            "max_abs_constructor_minus_input_p_Pa": float(np.max(np.abs(p_b - p_input_b))),
            "rho_range_kg_m3": [float(rho_b.min()), float(rho_b.max())],
            "gh_range_m2_s2": [float(gh_b.min()), float(gh_b.max())],
        }
    patch_relation_max = max(v["max_abs_relation_residual_Pa"] for v in patch_results.values())
    patch_prgh_max = max(v["max_abs_constructor_p_rgh_Pa"] for v in patch_results.values())
    patch_p_change_max = max(v["max_abs_constructor_minus_input_p_Pa"] for v in patch_results.values())
    result = {
        "case_id": manifest["case_id"],
        "method": "foamRun constructor followed by writeObjects executeAtStart in an isolated one-iteration clone; only clone time 0 is inspected",
        "source_case": str(case),
        "initialization_clone": str(init_case),
        "n_cells": n,
        "max_abs_constructor_relation_residual_Pa": float(np.max(np.abs(relation))),
        "max_abs_constructor_p_rgh_Pa": float(np.max(np.abs(prgh))),
        "max_abs_input_p_rgh_Pa": float(np.max(np.abs(prgh_input))),
        "max_abs_constructor_minus_input_p_Pa": float(np.max(np.abs(p - p_input))),
        "max_abs_constructor_rho_minus_rho0_kg_m3": float(np.max(np.abs(rho - manifest["properties"]["rho0_kg_m3"]))),
        "constructor_gh_range_m2_s2": [float(gh.min()), float(gh.max())],
        "physical_patches": patch_results,
        "max_abs_patch_relation_residual_Pa": patch_relation_max,
        "max_abs_patch_constructor_p_rgh_Pa": patch_prgh_max,
        "max_abs_patch_constructor_minus_input_p_Pa": patch_p_change_max,
        "tolerance_Pa": 1e-12,
    }
    result["pass"] = (
        result["max_abs_constructor_relation_residual_Pa"] <= 1e-12
        and result["max_abs_constructor_p_rgh_Pa"] <= 1e-12
        and result["max_abs_constructor_minus_input_p_Pa"] <= 1e-12
        and patch_relation_max <= 1e-12
        and patch_prgh_max <= 1e-12
        and patch_p_change_max <= 1e-12
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
