#!/usr/bin/env python3
"""Run one Route B matrix point; stop at any Gate A or D failure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

V13 = Path("/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark")
V6 = Path("/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark")
OUT = V13 / "results/routeB"
SCRIPTS = V6 / "Scripts/routeB"
LEVELS = {"coarse": 40, "medium": 80, "fine": 160}
RA_LABELS = {"1e3": 1000, "1e4": 10000, "1e5": 100000, "1e6": 1000000}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_status(case_id: str, stage: str, details: dict) -> None:
    path = OUT / "full_matrix_status.json"
    state = json.loads(path.read_text()) if path.exists() else {"schema": "routeB-full-matrix-status-v1", "cases": {}}
    state["cases"][case_id] = {"stage": stage, "updated_at": datetime.now().astimezone().isoformat(), **details}
    path.write_text(json.dumps(state, indent=2) + "\n")


def run_logged(command: list[str], log: Path) -> int:
    with log.open("w") as stream:
        return subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}).returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ra", choices=RA_LABELS, required=True)
    parser.add_argument("--grid", choices=LEVELS, required=True)
    parser.add_argument("--allow-unconverged-case", action="append", default=[])
    args = parser.parse_args()
    status_path = OUT / "full_matrix_status.json"
    if status_path.exists():
        previous = json.loads(status_path.read_text())
        stopped = [cid for cid, record in previous.get("cases", {}).items()
                   if record.get("stage") in ("CONVERGENCE_NOT_REACHED", "NUMERICAL_FAILURE", "SOLVER_FAILED", "GATE_A_FAIL")
                   and not (cid in args.allow_unconverged_case and record.get("stage") == "CONVERGENCE_NOT_REACHED"
                            and record.get("normal_exit") and not record.get("fatal_or_nan", True))]
        if stopped:
            raise SystemExit(f"Matrix stopped at {stopped}; user decision is required before any additional solver run")
    case_id = f"B-Ra{args.ra}-{args.grid}"
    name = f"Ra{args.ra}_{args.grid}"
    case = V6 / "cases/routeB" / name
    if case.exists():
        raise SystemExit(f"Refusing to overwrite existing case: {case}")
    original = json.loads((OUT / "run_manifest.json").read_text())
    for relative, expected in original["script_sha256"].items():
        if relative.endswith(("foam_fields.py", "run_case.sh")) and sha(V13 / relative) != expected:
            raise SystemExit(f"Accepted baseline changed: {relative}")
    for script in ("generate_case.py", "run_case.sh", "analyze_case.py", "foam_fields.py", "run_full_matrix.py"):
        if sha(V13 / "Scripts/routeB" / script) != sha(SCRIPTS / script):
            raise SystemExit(f"Canonical/execution script mismatch: {script}")
    environment_result = subprocess.run([
        "bash", "-lc", "source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc && foamVersion && command -v buoyantBoussinesqSimpleFoam"
    ], text=True, capture_output=True, check=True)
    environment = (environment_result.stdout + environment_result.stderr).splitlines()
    if "OpenFOAM-6" not in environment or original["environment"]["binary"] not in environment:
        raise SystemExit(f"OpenFOAM environment mismatch: {environment}")
    source_head = subprocess.check_output(["git", "-C", "/home/mirai/OpenFOAM/OpenFOAM-6", "rev-parse", "HEAD"], text=True).strip()
    if source_head != original["environment"]["source_git_head"]:
        raise SystemExit("OpenFOAM source build provenance mismatch")
    generation_log = OUT / f".{case_id}.generation.log"
    command = [sys.executable, str(SCRIPTS / "generate_case.py"), "--case-id", case_id,
               "--name", name, "--nx", str(LEVELS[args.grid]), "--ny", str(LEVELS[args.grid]),
               "--ra", str(RA_LABELS[args.ra])]
    if run_logged(command, generation_log):
        save_status(case_id, "GENERATION_FAILED", {"case_path": str(case)})
        raise SystemExit("Case generation failed")
    manifest = json.loads((case / "case_manifest.json").read_text())
    actual = manifest["Ra_actual"]
    target = manifest["Ra_target"]
    gate_a_numbers = abs(actual-target)/target <= 1e-10 and abs(manifest["Pr_actual"]-.71)/.71 <= 1e-10
    gate_a_numbers &= manifest["grid"] == [LEVELS[args.grid], LEVELS[args.grid], 1]
    gate_a_numbers &= manifest["beta_DeltaT"] == .001 and manifest["endTime_iterations"] == 3000
    gate_a_numbers &= all(sha(case / relative) == digest for relative, digest in manifest["input_sha256"].items())
    gate_a_numbers &= not any(re.search(rb"__[A-Z]+__", (case / relative).read_bytes()) for relative in manifest["input_sha256"])
    if not gate_a_numbers:
        save_status(case_id, "GATE_A_FAIL", {"case_path": str(case), "reason": "generated input/number mismatch"})
        raise SystemExit("Gate A input/number mismatch")
    run_shell = ["bash", "-lc"]
    for command_name in ("blockMesh", "checkMesh"):
        command = f"source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc && {command_name} -case '{case}'"
        if command_name == "checkMesh":
            command += " -allGeometry -allTopology"
        log = case / f"log.{command_name}"
        if run_logged(run_shell + [command], log):
            save_status(case_id, "GATE_A_FAIL", {"case_path": str(case), "reason": f"{command_name} failed"})
            raise SystemExit(f"Gate A: {command_name} failed")
    mesh_log = (case / "log.checkMesh").read_text()
    mesh_ok = all(fragment in mesh_log for fragment in (
        f"cells:            {LEVELS[args.grid] ** 2}",
        "bounding box (0 0 0) (0.1 0.1 0.001)",
        "directions (1 1 0)", "Mesh non-orthogonality Max: 0", "Mesh OK."))
    mesh_ok &= all(f"{wall}" in (case / "constant/polyMesh/boundary").read_text()
                   for wall in ("hotWall", "coldWall", "bottomWall", "topWall", "front", "back"))
    if not mesh_ok:
        save_status(case_id, "GATE_A_FAIL", {"case_path": str(case), "reason": "mesh audit failed"})
        raise SystemExit("Gate A mesh audit failed")
    accepted = json.loads((OUT / "full_matrix_manifest.json").read_text())
    baseline = accepted["cases"]["B-Ra1e3-coarse"]["generated_manifest"]
    fixed_inputs = ("0/U", "0/T", "0/p_rgh", "0/alphat", "constant/hRef",
                    "constant/transportProperties", "constant/turbulenceProperties",
                    "system/fvSchemes")
    if any(manifest["input_sha256"][p] != baseline["input_sha256"][p] for p in fixed_inputs):
        save_status(case_id, "GATE_A_FAIL", {"case_path": str(case), "reason": "accepted physics/BC/scheme inputs differ"})
        raise SystemExit("Gate A: accepted baseline input mismatch")
    boundary = (case / "constant/polyMesh/boundary").read_text()
    empty_ok = all(re.search(rf"\b{patch}\s*\{{[^}}]*\btype\s+empty;", boundary) for patch in ("front", "back"))
    build_ok = original["environment"]["build"] in (case / "log.blockMesh").read_text()[:3000]
    if not empty_ok or not build_ok:
        save_status(case_id, "GATE_A_FAIL", {"case_path": str(case), "reason": "empty patch/build mismatch"})
        raise SystemExit("Gate A: empty patch/build mismatch")
    preflight = {"case_path": str(case), "Ra_target": target, "Ra_actual": actual,
                 "Pr_actual": manifest["Pr_actual"], "beta_DeltaT": manifest["beta_DeltaT"],
                 "gravity_m_s2": manifest["gravity_m_s2"], "grid": manifest["grid"],
                 "pRefCell": manifest["pRefCell"], "pRefCellCentre_m": manifest["pRefCellCentre_m"],
                 "input_sha256": manifest["input_sha256"], "OpenFOAM_version": "OpenFOAM-6",
                 "OpenFOAM_build": original["environment"]["build"], "mesh_check": "Mesh OK",
                 "source_case_id": case_id, "reused_existing_solver_result": False,
                 "Gate_A": "PASS", "geometry_m": manifest["geometry_m"],
                 "front_back_empty": empty_ok, "max_non_orthogonality_deg": 0,
                 "accepted_fixed_input_hashes_match": True,
                 "fvSolution_sha256": sha(case / "system/fvSolution"),
                 "mesh_sha256": {str(p.relative_to(case)): sha(p) for p in (case / "constant/polyMesh").iterdir() if p.is_file()}}
    save_status(case_id, "GATE_A_PASS", preflight)
    if run_logged([str(SCRIPTS / "run_case.sh"), str(case)], case / "log.full_matrix_runner"):
        save_status(case_id, "SOLVER_FAILED", preflight)
        raise SystemExit("Solver failed; inspect the case log")
    if run_logged([sys.executable, str(SCRIPTS / "analyze_case.py"), str(case)], case / "log.analyze_case"):
        save_status(case_id, "ANALYSIS_FAILED", preflight)
        raise SystemExit("Post-processing failed; inspect the case log")
    metrics = json.loads((OUT / "cases" / case_id / "metrics.json").read_text())
    rwin = metrics["Rwin"]
    fatal = metrics["fatal_or_nan"] or not metrics["normal_exit"]
    converged = (not fatal and rwin["samples"] >= 21 and
                 max(rwin["Nu_bar_0"], rwin["Umax"], rwin["Vmax"]) <= 5e-4 and
                 max(metrics["final_initial_residuals"].values()) <= 1e-7 and
                 rwin["heat_imbalance_linear_slope_per_iteration"] <= 0)
    stage = "GATE_D_PASS" if converged else ("NUMERICAL_FAILURE" if fatal else "CONVERGENCE_NOT_REACHED")
    save_status(case_id, stage, {**preflight, "final_iteration": metrics["final_iteration"],
                                 "Rwin": rwin, "final_initial_residuals": metrics["final_initial_residuals"],
                                 "normal_exit": metrics["normal_exit"], "fatal_or_nan": metrics["fatal_or_nan"]})
    print(json.dumps({"matrix_case_id": case_id, "Gate_A": "PASS", "Gate_D": stage,
                      "Nu_bar_cavity": metrics["Nu_bar_cavity"], "Umax": metrics["Umax"],
                      "Wmax": metrics["Wmax"]}))
    if not converged:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
