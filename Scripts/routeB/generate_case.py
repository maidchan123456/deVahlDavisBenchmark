#!/usr/bin/env python3
"""Generate a Foundation v6 Route B minimal or full-matrix case."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "cases/routeB/template"
L = Decimal("0.1")
W = Decimal("0.001")
NU = Decimal("1e-5")
PR = Decimal("0.71")
ALPHA = NU / PR
BETA = Decimal("1e-3")
DT = Decimal("1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--nx", type=int, required=True)
    parser.add_argument("--ny", type=int, required=True)
    parser.add_argument("--ra", type=Decimal, required=True)
    parser.add_argument("--end-time", type=int, default=3000)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    matrix_ids = {f"B-Ra{ra}-{level}" for ra in ("1e3", "1e4", "1e5", "1e6")
                  for level in ("coarse", "medium", "fine")}
    if args.case_id not in {"B-COND", "B-SMOKE"} | matrix_ids:
        parser.error("case-id is not an authorized Route B case")
    target = args.output_dir.resolve() if args.output_dir else ROOT / "cases/routeB" / args.name
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing case: {target}")
    shutil.copytree(TEMPLATE, target)
    gmag = args.ra * NU * ALPHA / (BETA * DT * L**3) if args.ra else Decimal(0)
    gy = -gmag
    i = args.nx // 2 - 1
    j = args.ny // 2 - 1
    pref_cell = i + args.nx * j
    centre = [
        float((Decimal(i) + Decimal("0.5")) * L / args.nx),
        float((Decimal(j) + Decimal("0.5")) * L / args.ny),
        float(W / 2),
    ]
    replacements = {
        "__NX__": str(args.nx), "__NY__": str(args.ny),
        "__GY__": format(gy, ".17g"), "__PREFCELL__": str(pref_cell),
        "__ENDTIME__": str(args.end_time),
    }
    for path in target.rglob("*"):
        if path.is_file():
            text = path.read_text()
            for key, value in replacements.items():
                text = text.replace(key, value)
            if any(key in text for key in replacements):
                raise RuntimeError(f"Unreplaced placeholder in {path}")
            path.write_text(text)
    ra_actual = gmag * BETA * DT * L**3 / (NU * ALPHA) if gmag else Decimal(0)
    manifest = {
        "case_id": args.case_id, "route": "B",
        "generated_at": datetime.now().astimezone().isoformat(),
        "case_path": str(target), "grid": [args.nx, args.ny, 1],
        "geometry_m": {"L": float(L), "W": float(W)},
        "properties": {
            "TRef_K": 300.0, "Th_K": 300.5, "Tc_K": 299.5,
            "DeltaT_K": 1.0, "rho0_reference_kg_m3": 1.0,
            "mu_reference_Pa_s": 1e-5, "nu_m2_s": float(NU),
            "beta_1_K": float(BETA), "Pr_input": float(PR), "Prt": 0.85,
            "alpha0_m2_s": float(ALPHA),
        },
        "gravity_m_s2": [0.0, float(gy), 0.0], "gmag_m_s2": float(gmag),
        "Ra_target": float(args.ra), "Ra_actual": float(ra_actual),
        "Pr_actual": float(NU / ALPHA), "beta_DeltaT": float(BETA * DT),
        "pRefCell": pref_cell, "pRefCellCentre_m": centre,
        "pRefValue_m2_s2": 0.0, "hRef_m": 0.0,
        "endTime_iterations": args.end_time,
        "model": "Foundation v6 buoyantBoussinesqSimpleFoam; Newtonian; laminar/Stokes; no radiation/MRF/fvOptions",
        "pressure": "kinematic p and p_rgh; input p_rgh=0; p generated internally as p_rgh+rhok*gh; no 0/p",
    }
    files = [p for p in target.rglob("*") if p.is_file()]
    manifest["input_sha256"] = {str(p.relative_to(target)): sha256(p) for p in sorted(files)}
    (target / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
