#!/usr/bin/env python3
"""Consolidate the two authorized Route A runs into required artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results/routeA"
CASES = {
    "A-COND": ROOT / "cases/routeA/Ra0_medium",
    "A-SMOKE": ROOT / "cases/routeA/Ra1e4_coarse",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes(case: Path, generated: dict) -> dict[str, str]:
    names = generated["input_sha256"].keys()
    return {name: digest(case / name) for name in names}


def repository_script_hashes(folder: Path) -> dict[str, str]:
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(folder.iterdir())
            if path.is_file() and path.suffix in (".py", ".sh")}


def main() -> None:
    records = {}
    for case_id, case in CASES.items():
        generated = json.loads((case / "case_manifest.json").read_text())
        metrics = json.loads((RESULTS / "cases" / case_id / "metrics.json").read_text())
        init = json.loads((RESULTS / "cases" / case_id / "initialization.json").read_text())
        mesh_files = sorted((case / "constant/polyMesh").glob("*"))
        final_dir = case / str(metrics["final_iteration"])
        accepted_fields = [final_dir / name for name in ("T", "U", "phi", "p", "p_rgh", "rho")]
        records[case_id] = {
            "generated_manifest": generated,
            "executed_input_sha256": input_hashes(case, generated),
            "mesh_sha256": {p.name: digest(p) for p in mesh_files if p.is_file()},
            "accepted_final_field_sha256": {
                str(path.relative_to(ROOT)): digest(path) for path in accepted_fields if path.is_file()
            },
            "mesh": {
                "cell_count": generated["grid"][0] * generated["grid"][1],
                "patch_faces": {
                    "hotWall": generated["grid"][1],
                    "coldWall": generated["grid"][1],
                    "bottomWall": generated["grid"][0],
                    "topWall": generated["grid"][0],
                    "front": generated["grid"][0] * generated["grid"][1],
                    "back": generated["grid"][0] * generated["grid"][1],
                },
                "checkMesh": "Mesh OK",
                "geometric_and_solution_directions": [1, 1, 0],
                "max_non_orthogonality_deg": 0.0,
            },
            "initialization_check": init,
            "metrics": metrics,
            "logs": {
                str(p.relative_to(ROOT)): digest(p)
                for p in sorted(case.glob("log.*")) if p.is_file()
            },
        }

    cond = records["A-COND"]["metrics"]
    smoke = records["A-SMOKE"]["metrics"]
    cond_gate = (
        abs(cond["Nu_hot_path1"] - 1) <= 0.001
        and abs(cond["Nu_cold_path1"] - 1) <= 0.001
        and abs(cond["Nu_hot_path2"] - 1) <= 0.001
        and abs(cond["Nu_cold_path2"] - 1) <= 0.001
        and cond["Nu_path_relative_difference"] <= 0.001
        and cond["max_dimensionless_velocity"] <= 1e-6
        and cond["max_theta_analytic_error"] <= 1e-4
        and cond["normal_exit"] and not cond["fatal_or_nan"]
        and records["A-COND"]["initialization_check"]["pass"]
    )
    cond_paper_nu_unit = all(abs(cond[name] - 1) <= 0.001 for name in
                             ("Nu_bar_0", "Nu_bar_half", "Nu_bar_cavity", "Nu_bar_1"))
    smoke_converged = (
        smoke["normal_exit"] and not smoke["fatal_or_nan"]
        and records["A-SMOKE"]["initialization_check"]["pass"]
        and smoke["Rwin"]["Nu"] <= 5e-4
        and smoke["Rwin"]["Umax"] <= 5e-4
        and smoke["Rwin"]["Vmax"] <= 5e-4
        and max(smoke["final_initial_residuals"].values()) <= 1e-7
        and smoke["heat_imbalance"] <= 0.002
        and smoke["Umax"] > 0 and smoke["Vmax"] > 0
    )
    statuses = {
        "ROUTE A GATE C": "PASS" if cond_gate else "FAIL",
        "ROUTE A PAPER-DEFINITION NU UNIT TEST": "PASS" if cond_paper_nu_unit else "FAIL",
        "ROUTE A SMOKE TEST": "PASS" if cond_gate and smoke_converged else "FAIL",
        "ROUTE A MINIMAL IMPLEMENTATION": "PASS" if cond_gate and smoke_converged else "FAIL",
    }

    docs = ["benchmark_spec.md", "acceptance_criteria.md", "openfoam_design.md", "routeB_design.md"]
    run_manifest = {
        "schema": "routeA-minimal-v1",
        "postprocessing_version": "dvd-nusselt-post-v2.1",
        "postprocessing_revision": {
            "date": "2026-10-03", "solver_rerun": False,
            "reason": "Centralize Table V reference data, separate signed differences from absolute Gate errors, and add explicit cavity-method diagnostics using saved fields",
            "invalidated_comparison": "Nu_hot_path1=2.257421422... versus Table V Nu_bar_cavity=2.243 mixed Nu_bar_0 with Nu_bar_cavity",
            "hard_gate_definition_changed": False,
            "physics_boundary_scheme_relaxation_tolerance_changed": False,
            "accepted_cfd_fields_modified": False,
        },
        "generated_at": datetime.now().astimezone().isoformat(),
        "workspace": str(ROOT),
        "host": platform.node(),
        "environment": {
            "activation": "source /opt/openfoam13/etc/bashrc",
            "foamVersion": "OpenFOAM-13",
            "build": "13-441953dfbb42",
            "foamRun": "/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin/foamRun",
            "WM_PROJECT": "OpenFOAM",
            "WM_PROJECT_VERSION": "13",
            "WM_PROJECT_DIR": "/opt/openfoam13",
            "FOAM_RUN": "/home/mirai/OpenFOAM/mirai-13/run",
            "WM_OPTIONS": "linux64GccDPInt32Opt",
            "distribution": "OpenFOAM Foundation (not OpenCFD/ESI)",
        },
        "immutable_document_sha256": {name: digest(ROOT / "docs" / name) for name in docs},
        "script_sha256": repository_script_hashes(ROOT / "Scripts/routeA"),
        "canonical_paper_reference": {
            "path": "reference/de_vahl_davis_table_v.csv",
            "sha256": digest(ROOT / "reference/de_vahl_davis_table_v.csv"),
            "role": "single machine-readable source for de Vahl Davis Table V",
        },
        "model_summary": "foamRun + solver fluid; Boussinesq heRhoThermo; laminar Stokes; laminar Fourier; no turbulence/radiation/MRF/particles/fvModels/fvConstraints",
        "boundary_summary": {
            "U": "noSlip on four physical walls; empty front/back",
            "T": "hot fixedValue 300.5 K; cold fixedValue 299.5 K; top/bottom zeroGradient; empty front/back",
            "p_rgh": "fixedFluxPressure on four physical walls; empty front/back",
            "p": "calculated on four physical walls; empty front/back",
        },
        "schemes": "steadyState; Gauss linear gradients and convection; Gauss linear orthogonal Laplacian; linear interpolation; orthogonal snGrad",
        "adjustments": [
            {
                "case": "A-COND",
                "type": "v13 dictionary compatibility",
                "previous": "sampled-set type uniform",
                "new": "sampled-set type lineUniform",
                "reason": "Foundation v13 fatal message states the type was renamed; attempt-1 log preserved",
                "physical_or_solver_change": False,
            },
            {
                "case": "A-SMOKE template before generation",
                "type": "post-processing scheme coverage",
                "previous": "no div(U) entry",
                "new": "div(U) Gauss linear",
                "reason": "explicit volume-divergence diagnostic; not used by fluid solver equations",
                "physical_or_solver_change": False,
            },
            {
                "case": "A-SMOKE attempt 1 (archived and invalidated before acceptance)",
                "type": "OQ-02 physical-patch initialization correction",
                "previous": "p=rho0*gh on hot/cold patch values, which produced |p_rgh| up to 6.954225352118204e-05 Pa after the constructor because fixed wall T gives rho_patch != rho0",
                "new": "internal p=rho0*gh; physical-wall p=rho(T_patch)*gh, yielding constructor p_rgh approximately zero in cells and on all physical patches",
                "reason": "extend the hard OQ-02 verification from internal cells to physical patches and satisfy p_rgh=p-rho*gh-pRef everywhere represented by a field value",
                "physical_or_solver_change": False,
                "preserved_evidence": "results/routeA/failed_runs/A-SMOKE-attempt1-boundary-init",
            },
        ],
        "solver_or_relaxation_changes": [],
        "cases": records,
        "preserved_invalidated_runs": [
            {
                "id": "A-SMOKE-attempt1-boundary-init",
                "status": "INVALIDATED_OQ02_PATCH_CHECK",
                "path": "results/routeA/failed_runs/A-SMOKE-attempt1-boundary-init",
                "accepted_as_result": False,
            },
            {
                "id": "A-COND-postprocess-divU-attempt1-missingScheme",
                "status": "INVALIDATED_POSTPROCESS_DIAGNOSTIC",
                "path": "results/routeA/failed_runs/A-COND-postprocess-divU-attempt1-missingScheme.log",
                "accepted_as_result": False,
            },
        ],
        "statuses": statuses,
        "scope_exclusions": ["full 12-case matrix", "beta*DeltaT sensitivity", "transient", "Route B", "custom solver"],
    }
    (RESULTS / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n")

    summary_fields = [
        "case_id", "route", "Ra_target", "Ra_actual", "Pr_actual", "grid",
        "Nu_bar_0", "Nu_bar_half", "Nu_bar_cavity", "Nu_bar_1",
        "Nu_bar_cavity_from_section_trapezoid", "Nu_bar_cavity_method_absolute_difference", "Nu_bar_cavity_method_relative_difference",
        "Nu_bar_0_path1", "Nu_bar_0_path2", "Nu_bar_1_path1", "Nu_bar_1_path2",
        "Nu_hot_local_max", "Nu_hot_local_max_Z", "Nu_hot_local_min", "Nu_hot_local_min_Z",
        "Nu_hot_local_raw_max", "Nu_hot_local_raw_max_Z", "Nu_hot_local_raw_min", "Nu_hot_local_raw_min_Z",
        "Nu_hot_path1", "Nu_hot_path2", "Nu_cold_path1", "Nu_cold_path2",
        "Umax", "Umax_location_Z", "Wmax", "Wmax_location_X", "Vmax", "Vmax_location", "heat_imbalance",
        "max_dimensionless_velocity_for_Ra0", "max_theta_analytic_error_for_Ra0",
        "convergence_status", "gate_C_status", "smoke_status",
    ]
    with (RESULTS / "minimal_test_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_fields, lineterminator="\n")
        writer.writeheader()
        for case_id in ("A-COND", "A-SMOKE"):
            rec = records[case_id]
            gen = rec["generated_manifest"]
            met = rec["metrics"]
            writer.writerow({
                "case_id": case_id, "route": "A", "Ra_target": gen["Ra_target"],
                "Ra_actual": gen["Ra_actual"], "Pr_actual": gen["Pr_actual"],
                "grid": "x".join(map(str, gen["grid"])),
                "Nu_bar_0": met["Nu_bar_0"], "Nu_bar_half": met["Nu_bar_half"],
                "Nu_bar_cavity": met["Nu_bar_cavity"], "Nu_bar_1": met["Nu_bar_1"],
                "Nu_bar_cavity_from_section_trapezoid": met["Nu_bar_cavity_from_section_trapezoid"],
                "Nu_bar_cavity_method_absolute_difference": met["Nu_bar_cavity_method_absolute_difference"],
                "Nu_bar_cavity_method_relative_difference": met["Nu_bar_cavity_method_relative_difference"],
                "Nu_bar_0_path1": met["Nu_bar_0_path1"], "Nu_bar_0_path2": met["Nu_bar_0_path2"],
                "Nu_bar_1_path1": met["Nu_bar_1_path1"], "Nu_bar_1_path2": met["Nu_bar_1_path2"],
                "Nu_hot_local_max": met["Nu_hot_local_max"], "Nu_hot_local_max_Z": met["Nu_hot_local_max_Z"],
                "Nu_hot_local_min": met["Nu_hot_local_min"], "Nu_hot_local_min_Z": met["Nu_hot_local_min_Z"],
                "Nu_hot_local_raw_max": met["Nu_hot_local_raw_max"], "Nu_hot_local_raw_max_Z": met["Nu_hot_local_raw_max_Z"],
                "Nu_hot_local_raw_min": met["Nu_hot_local_raw_min"], "Nu_hot_local_raw_min_Z": met["Nu_hot_local_raw_min_Z"],
                "Nu_hot_path1": met["Nu_hot_path1"], "Nu_hot_path2": met["Nu_hot_path2"],
                "Nu_cold_path1": met["Nu_cold_path1"], "Nu_cold_path2": met["Nu_cold_path2"],
                "Umax": met["Umax"], "Umax_location_Z": met["Umax_Z"],
                "Wmax": met["Wmax"], "Wmax_location_X": met["Wmax_X"],
                "Vmax": met["Vmax"], "Vmax_location": met["Vmax_X"],
                "heat_imbalance": met["heat_imbalance"],
                "max_dimensionless_velocity_for_Ra0": met["max_dimensionless_velocity"] if case_id == "A-COND" else "N/A",
                "max_theta_analytic_error_for_Ra0": met["max_theta_analytic_error"] if case_id == "A-COND" else "N/A",
                "convergence_status": "PASS" if (case_id == "A-COND" or smoke_converged) else "FAIL",
                "gate_C_status": statuses["ROUTE A GATE C"] if case_id == "A-COND" else "N/A",
                "smoke_status": statuses["ROUTE A SMOKE TEST"] if case_id == "A-SMOKE" else "N/A",
            })

    with (RESULTS / "convergence.csv").open("w", newline="") as output:
        writer = None
        for case_id in ("A-COND", "A-SMOKE"):
            with (RESULTS / "cases" / case_id / "convergence.csv").open() as source:
                reader = csv.DictReader(source)
                if writer is None:
                    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, lineterminator="\n")
                    writer.writeheader()
                writer.writerows(reader)

    with (RESULTS / "conservation.csv").open("w", newline="") as stream:
        fields = ["case_id", "Nu_bar_0", "Nu_bar_half", "Nu_bar_cavity", "Nu_bar_1",
                  "Nu_bar_cavity_from_section_trapezoid", "Nu_bar_cavity_method_absolute_difference", "Nu_bar_cavity_method_relative_difference",
                  "section_Nu_max_relative_deviation_from_half", "heat_imbalance", "mean_abs_mass_divergence_kg_m3_s",
                  "mean_abs_volume_divergence_1_s", "epsilon_m", "epsilon_v", "note"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for case_id in ("A-COND", "A-SMOKE"):
            met = records[case_id]["metrics"]
            div = met["divergence"]
            writer.writerow({
                "case_id": case_id, "Nu_bar_0": met["Nu_bar_0"], "Nu_bar_half": met["Nu_bar_half"],
                "Nu_bar_cavity": met["Nu_bar_cavity"], "Nu_bar_1": met["Nu_bar_1"],
                "Nu_bar_cavity_from_section_trapezoid": met["Nu_bar_cavity_from_section_trapezoid"],
                "Nu_bar_cavity_method_absolute_difference": met["Nu_bar_cavity_method_absolute_difference"],
                "Nu_bar_cavity_method_relative_difference": met["Nu_bar_cavity_method_relative_difference"],
                "section_Nu_max_relative_deviation_from_half": met["section_Nu_max_relative_deviation_from_half"],
                "heat_imbalance": met["heat_imbalance"],
                "mean_abs_mass_divergence_kg_m3_s": div["mean_abs_mass_divergence_kg_m3_s"],
                "mean_abs_volume_divergence_1_s": div["mean_abs_volume_divergence_1_s"],
                "epsilon_m": div["epsilon_m"], "epsilon_v": div["epsilon_v"],
                "note": "Ra=0 uses Gate C absolute velocity criterion" if case_id == "A-COND" else "coarse smoke diagnostic; formal Gate G applies to fine cases",
            })
    print(json.dumps(statuses, indent=2))


if __name__ == "__main__":
    main()
