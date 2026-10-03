#!/usr/bin/env python3
"""Generate one authorized Route A case from the audited template."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "cases/routeA/template"

L = Decimal("0.1")
W = Decimal("0.001")
RHO0 = Decimal("1")
BETA = Decimal("1e-3")
DT = Decimal("1")
MU = Decimal("1e-5")
PR = Decimal("0.71")
NU0 = MU / RHO0
ALPHA0 = NU0 / PR


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar_list(values: list[Decimal]) -> str:
    body = "\n".join(format(v, ".17g") for v in values)
    return f"nonuniform List<scalar>\n{len(values)}\n(\n{body}\n)"


def make_p(nx: int, ny: int, gy: Decimal) -> str:
    dx = L / nx
    dy = L / ny
    internal = [RHO0 * gy * ((Decimal(j) + Decimal("0.5")) * dy)
                for j in range(ny) for _i in range(nx)]
    # The fixed-temperature wall patches already impose their EOS density
    # during thermo construction.  Seed p with that patch density so the
    # constructor relation also gives p_rgh=0 on the physical walls.  The
    # internal cells retain the specified p=rho0*gh state at T=T0.
    rho_hot = RHO0 * (Decimal(1) - BETA * Decimal("0.5"))
    rho_cold = RHO0 * (Decimal(1) + BETA * Decimal("0.5"))
    hot = [rho_hot * gy * ((Decimal(j) + Decimal("0.5")) * dy)
           for j in range(ny)]
    cold = [rho_cold * gy * ((Decimal(j) + Decimal("0.5")) * dy)
            for j in range(ny)]
    bottom = [Decimal(0)] * nx
    top = [RHO0 * gy * L] * nx
    return f"""FoamFile
{{
    format ascii;
    class volScalarField;
    object p;
}}
dimensions [1 -1 -2 0 0 0 0];
internalField {scalar_list(internal)};
boundaryField
{{
    hotWall
    {{
        type calculated;
        value {scalar_list(hot)};
    }}
    coldWall
    {{
        type calculated;
        value {scalar_list(cold)};
    }}
    bottomWall
    {{
        type calculated;
        value {scalar_list(bottom)};
    }}
    topWall
    {{
        type calculated;
        value {scalar_list(top)};
    }}
    front {{ type empty; }}
    back  {{ type empty; }}
}}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True, choices=("A-COND", "A-SMOKE"))
    parser.add_argument("--name", required=True)
    parser.add_argument("--nx", required=True, type=int)
    parser.add_argument("--ny", required=True, type=int)
    parser.add_argument("--ra", required=True, type=Decimal)
    parser.add_argument("--end-time", type=int, default=3000)
    args = parser.parse_args()

    target = ROOT / "cases/routeA" / args.name
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing case: {target}")
    shutil.copytree(TEMPLATE, target)

    gmag = (args.ra * NU0 * ALPHA0) / (BETA * DT * L**3) if args.ra else Decimal(0)
    gy = -gmag
    i = args.nx // 2 - 1
    j = args.ny // 2 - 1
    pref_cell = i + args.nx * j
    pref_centre = [
        float((Decimal(i) + Decimal("0.5")) * L / args.nx),
        float((Decimal(j) + Decimal("0.5")) * L / args.ny),
        float(W / 2),
    ]

    replacements = {
        "__NX__": str(args.nx),
        "__NY__": str(args.ny),
        "__GY__": format(gy, ".17g"),
        "__PREFCELL__": str(pref_cell),
        "__ENDTIME__": str(args.end_time),
    }
    for path in target.rglob("*"):
        if path.is_file():
            data = path.read_text()
            for key, value in replacements.items():
                data = data.replace(key, value)
            path.write_text(data)

    (target / "0/p").write_text(make_p(args.nx, args.ny, gy))

    ra_actual = gmag * BETA * DT * L**3 / (NU0 * ALPHA0) if gmag else Decimal(0)
    manifest = {
        "case_id": args.case_id,
        "route": "A",
        "case_path": str(target),
        "grid": [args.nx, args.ny, 1],
        "geometry_m": {"L": float(L), "W": float(W)},
        "properties": {
            "T0_K": 300.0, "Th_K": 300.5, "Tc_K": 299.5,
            "DeltaT_K": 1.0, "rho0_kg_m3": float(RHO0),
            "beta_1_K": float(BETA), "mu_Pa_s": float(MU),
            "Pr_input": float(PR), "Cv_J_kgK": 1000.0,
            "nu0_m2_s": float(NU0), "alpha0_m2_s": float(ALPHA0),
            "k_W_mK": float(Decimal(1000) * MU / PR),
        },
        "gravity_m_s2": [0.0, float(gy), 0.0],
        "gmag_m_s2": float(gmag),
        "Ra_target": float(args.ra),
        "Ra_actual": float(ra_actual),
        "Pr_actual": float(PR),
        "beta_DeltaT": float(BETA * DT),
        "pRefCell": pref_cell,
        "pRefCellCentre_m": pref_centre,
        "pRefValue_Pa": 0.0,
        "pRef_Pa": 0.0,
        "hRef_m": 0.0,
        "endTime_iterations": args.end_time,
        "model": "foamRun+fluid; heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy; laminar/Fourier",
        "initial_pressure_relation": "internal p=rho0*gh+pRef at T0; physical-wall p=rho(T_patch)*gh+pRef so constructor p_rgh=0 on cells and patches; hRef=pRef=0",
    }
    inputs = [p for p in target.rglob("*") if p.is_file()]
    manifest["input_sha256"] = {
        str(p.relative_to(target)): sha256(p) for p in sorted(inputs)
    }
    (target / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
