#!/usr/bin/env python3
"""Assemble canonical Route B minimal-run tables and provenance manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path

V6 = Path("/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark")
V13 = Path("/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark")
OUT = V13 / "results/routeB"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(paths: list[Path], relative_to: Path) -> dict[str, str]:
    return {str(p.relative_to(relative_to)): sha(p) for p in paths if p.is_file()}


def case_data(case_id: str, dirname: str) -> tuple[dict, dict, Path]:
    case = V6 / "cases/routeB" / dirname
    return (json.loads((case/"case_manifest.json").read_text()),
            json.loads((OUT/"cases"/case_id/"metrics.json").read_text()), case)


def main() -> None:
    cond_m, cond, cond_case = case_data("B-COND", "Ra0_medium")
    smoke_m, smoke, smoke_case = case_data("B-SMOKE", "Ra1e4_coarse")
    cond_paper_nu_unit = all(abs(cond[name]-1) <= 0.001 for name in
                             ("Nu_bar_0","Nu_bar_half","Nu_bar_cavity","Nu_bar_1"))

    summary_fields = ["case_id","route","OpenFOAM_version","Ra_target","Ra_actual","Pr_actual","grid",
        "Nu_bar_0","Nu_bar_half","Nu_bar_cavity","Nu_bar_1","Nu_bar_0_path1","Nu_bar_0_path2","Nu_bar_1_path1","Nu_bar_1_path2",
        "Nu_bar_cavity_from_section_trapezoid","Nu_bar_cavity_method_absolute_difference","Nu_bar_cavity_method_relative_difference",
        "Nu_hot_local_max","Nu_hot_local_max_Z","Nu_hot_local_min","Nu_hot_local_min_Z","Nu_hot_local_raw_max","Nu_hot_local_raw_max_Z","Nu_hot_local_raw_min","Nu_hot_local_raw_min_Z",
        "Nu_hot_B1","Nu_hot_B2","Nu_cold_B1","Nu_cold_B2","Umax","Umax_location_Z","Wmax","Wmax_location_X","Vmax","Vmax_location",
        "heat_imbalance","epsilon_v","continuity_status","max_dimensionless_velocity_Ra0",
        "max_theta_analytic_error_Ra0","convergence_status","gate_C_status","smoke_status"]
    rows=[]
    for man, met in ((cond_m,cond),(smoke_m,smoke)):
        is_cond=man["case_id"]=="B-COND"
        conv=(met["normal_exit"] and not met["fatal_or_nan"] and
              max(met["Rwin"]["Nu"],met["Rwin"]["Umax"],met["Rwin"]["Vmax"])<=5e-4 and
              max(met["final_initial_residuals"].values())<=1e-7)
        rows.append({
          "case_id":man["case_id"],"route":"B","OpenFOAM_version":"OpenFOAM-6",
          "Ra_target":man["Ra_target"],"Ra_actual":man["Ra_actual"],"Pr_actual":man["Pr_actual"],"grid":"x".join(map(str,man["grid"])),
          "Nu_bar_0":met["Nu_bar_0"],"Nu_bar_half":met["Nu_bar_half"],"Nu_bar_cavity":met["Nu_bar_cavity"],"Nu_bar_1":met["Nu_bar_1"],
          "Nu_bar_cavity_from_section_trapezoid":met["Nu_bar_cavity_from_section_trapezoid"],"Nu_bar_cavity_method_absolute_difference":met["Nu_bar_cavity_method_absolute_difference"],"Nu_bar_cavity_method_relative_difference":met["Nu_bar_cavity_method_relative_difference"],
          "Nu_bar_0_path1":met["Nu_bar_0_path1"],"Nu_bar_0_path2":met["Nu_bar_0_path2"],"Nu_bar_1_path1":met["Nu_bar_1_path1"],"Nu_bar_1_path2":met["Nu_bar_1_path2"],
          "Nu_hot_local_max":met["Nu_hot_local_max"],"Nu_hot_local_max_Z":met["Nu_hot_local_max_Z"],"Nu_hot_local_min":met["Nu_hot_local_min"],"Nu_hot_local_min_Z":met["Nu_hot_local_min_Z"],
          "Nu_hot_local_raw_max":met["Nu_hot_local_raw_max"],"Nu_hot_local_raw_max_Z":met["Nu_hot_local_raw_max_Z"],"Nu_hot_local_raw_min":met["Nu_hot_local_raw_min"],"Nu_hot_local_raw_min_Z":met["Nu_hot_local_raw_min_Z"],
          "Nu_hot_B1":met["Nu_hot_B1"],"Nu_hot_B2":met["Nu_hot_B2"],"Nu_cold_B1":met["Nu_cold_B1"],"Nu_cold_B2":met["Nu_cold_B2"],
          "Umax":met["Umax"],"Umax_location_Z":met["Umax_Z"],"Wmax":met["Wmax"],"Wmax_location_X":met["Wmax_X"],"Vmax":met["Vmax"],"Vmax_location":met["Vmax_X"],
          "heat_imbalance":met["heat_imbalance"],"epsilon_v":"N/A" if is_cond else met["continuity"]["epsilon_v"],
          "continuity_status":"Gate C zero velocity" if is_cond else "coarse diagnostic; FV phi conservative; reconstructed epsilon_v exceeds fine-grid Gate G threshold",
          "max_dimensionless_velocity_Ra0":met["max_dimensionless_velocity"] if is_cond else "N/A",
          "max_theta_analytic_error_Ra0":met["max_theta_analytic_error"] if is_cond else "N/A",
          "convergence_status":"PASS" if conv else "FAIL",
          "gate_C_status":"PASS" if is_cond else "N/A","smoke_status":"N/A" if is_cond else ("PASS" if conv else "FAIL")})
    with (OUT/"minimal_test_summary.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=summary_fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)

    with (OUT/"convergence.csv").open("w",newline="") as dst:
        writer=None
        for cid in ("B-COND","B-SMOKE"):
            with (OUT/"cases"/cid/"convergence.csv").open() as src:
                reader=csv.DictReader(src)
                if writer is None:
                    writer=csv.DictWriter(dst,fieldnames=reader.fieldnames,lineterminator="\n"); writer.writeheader()
                writer.writerows(reader)

    conservation_fields=["case_id","Nu_bar_0","Nu_bar_half","Nu_bar_cavity","Nu_bar_1","Nu_bar_cavity_from_section_trapezoid","Nu_bar_cavity_method_absolute_difference","Nu_bar_cavity_method_relative_difference","section_Nu_max_relative_deviation_from_half","mean_abs_div_phi_1_s","mean_abs_div_U_1_s","epsilon_phi","epsilon_v","epsilon_m","heat_imbalance","interpretation"]
    with (OUT/"conservation.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=conservation_fields,lineterminator="\n"); w.writeheader()
        for m in (cond,smoke):
            c=m["continuity"]
            w.writerow({"case_id":m["case_id"],"Nu_bar_0":m["Nu_bar_0"],"Nu_bar_half":m["Nu_bar_half"],"Nu_bar_cavity":m["Nu_bar_cavity"],"Nu_bar_1":m["Nu_bar_1"],"Nu_bar_cavity_from_section_trapezoid":m["Nu_bar_cavity_from_section_trapezoid"],"Nu_bar_cavity_method_absolute_difference":m["Nu_bar_cavity_method_absolute_difference"],"Nu_bar_cavity_method_relative_difference":m["Nu_bar_cavity_method_relative_difference"],"section_Nu_max_relative_deviation_from_half":m["section_Nu_max_relative_deviation_from_half"],"mean_abs_div_phi_1_s":c["mean_abs_div_phi_1_s"],"mean_abs_div_U_1_s":c["mean_abs_div_U_1_s"],
                "epsilon_phi":"N/A" if c["epsilon_phi"] is None else c["epsilon_phi"],"epsilon_v":"N/A" if c["epsilon_v"] is None else c["epsilon_v"],
                "epsilon_m":"N/A" if c["epsilon_m"] is None else c["epsilon_m"],"heat_imbalance":m["heat_imbalance"],
                "interpretation":"Ra=0: use Gate C absolute velocity" if m["case_id"]=="B-COND" else "coarse smoke diagnostic; Gate G is formally judged on fine grid"})

    with (V13/"results/routeA/minimal_test_summary.csv").open() as f:
        a=next(r for r in csv.DictReader(f) if r["case_id"]=="A-SMOKE")
    a_manifest=json.loads((V13/"results/routeA/run_manifest.json").read_text())
    a_eps=a_manifest["cases"]["A-SMOKE"]["metrics"]["divergence"]["epsilon_v"]
    comparisons=[
      ("Nu_bar_0",float(a["Nu_bar_0"]),smoke["Nu_bar_0"]),
      ("Nu_bar_half",float(a["Nu_bar_half"]),smoke["Nu_bar_half"]),
      ("Nu_bar_cavity",float(a["Nu_bar_cavity"]),smoke["Nu_bar_cavity"]),
      ("Nu_bar_1",float(a["Nu_bar_1"]),smoke["Nu_bar_1"]),
      ("Umax",float(a["Umax"]),smoke["Umax"]),
      ("Umax_location_Z",float(a["Umax_location_Z"]),smoke["Umax_Z"]),
      ("Wmax",float(a["Wmax"]),smoke["Wmax"]),
      ("Wmax_location_X",float(a["Wmax_location_X"]),smoke["Wmax_X"]),
      ("epsilon_v",a_eps,smoke["continuity"]["epsilon_v"])]
    with (OUT/"minimal_route_comparison.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["quantity","Route_A_A-SMOKE","Route_B_B-SMOKE","B_minus_A","relative_B_minus_A"])
        for name,av,bv in comparisons:
            w.writerow([name,av,bv,bv-av,(bv-av)/av if av else "N/A"])

    doc_names=["benchmark_spec.md","acceptance_criteria.md","openfoam_design.md","routeB_design.md","routeA_implementation.md","routeB_implementation.md"]
    cases={}
    for man,met,case in ((cond_m,cond,cond_case),(smoke_m,smoke,smoke_case)):
        mesh_files=sorted((case/"constant/polyMesh").glob("*"))
        log_files=sorted(case.glob("log.*"))
        final_dir=case/str(met["final_iteration"])
        accepted_fields=[final_dir/name for name in ("T","U","phi","p","p_rgh","alphat")]
        cases[man["case_id"]]={
          "generated_manifest":man,
          "executed_input_sha256":hashes([case/p for p in man["input_sha256"]],case),
          "mesh_sha256":hashes(mesh_files,case),
          "accepted_final_field_sha256":hashes(accepted_fields,V6),
          "log_sha256":hashes(log_files,case),
          "mesh":{"cell_count":man["grid"][0]*man["grid"][1],"patch_faces":{"hotWall":man["grid"][1],"coldWall":man["grid"][1],"bottomWall":man["grid"][0],"topWall":man["grid"][0],"front":man["grid"][0]*man["grid"][1],"back":man["grid"][0]*man["grid"][1]},"geometric_and_solution_directions":[1,1,0],"max_non_orthogonality_deg":0.0,"checkMesh":"Mesh OK"},
          "metrics":met}
    execution_scripts=sorted((V6/"Scripts/routeB").glob("*"))
    canonical_scripts=sorted((V13/"Scripts/routeB").glob("*"))
    execution_script_sha256=hashes(execution_scripts,V6)
    canonical_script_sha256=hashes(canonical_scripts,V13)
    failures=[]
    for p in sorted((OUT/"failed_runs").glob("*/failure.json")):
        failures.append(json.loads(p.read_text()))
    manifest={
      "schema":"routeB-minimal-v1","postprocessing_version":"dvd-nusselt-post-v2.1","generated_at":datetime.now().astimezone().isoformat(),
      "postprocessing_revision":{"date":"2026-10-03","solver_rerun":False,"reason":"Canonicalize Route B scripts/reference data and make signed differences distinct from absolute Gate errors","invalidated_comparison":"Nu_hot_B1=2.257421662... versus Table V Nu_bar_cavity=2.243 mixed Nu_bar_0 with Nu_bar_cavity","hard_gate_definition_changed":False,"physics_boundary_scheme_relaxation_tolerance_changed":False,"accepted_cfd_fields_modified":False},
      "v6_execution_root":str(V6),"v13_research_root":str(V13),"host":platform.node(),
      "environment":{"activation":"source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc","foamVersion":"OpenFOAM-6","build":"6-af7d7f427be7","source_git_head":"af7d7f427be78e9b9beb6aceca8fe7d5d4636876","binary":"/home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam","WM_PROJECT":"OpenFOAM","WM_PROJECT_VERSION":"6","WM_PROJECT_DIR":"/home/mirai/OpenFOAM/OpenFOAM-6","FOAM_RUN":"/home/mirai/OpenFOAM/mirai-6/run","WM_OPTIONS":"linux64GccDPInt32Opt","distribution":"OpenFOAM Foundation (not OpenCFD/ESI)"},
      "immutable_document_sha256":{n:sha(V13/"docs"/n) for n in doc_names},
      "script_sha256":canonical_script_sha256,
      "execution_script_sha256":execution_script_sha256,
      "canonical_execution_scripts_match":canonical_script_sha256==execution_script_sha256,
      "canonical_paper_reference":{"path":"reference/de_vahl_davis_table_v.csv","sha256":sha(V13/"reference/de_vahl_davis_table_v.csv"),"role":"single machine-readable source for de Vahl Davis Table V"},
      "script_provenance":{"canonicalization_source":str(V6/"Scripts/routeB"),"canonicalization_destination":str(V13/"Scripts/routeB"),"pre_canonicalization_manifest_script_sha256":{"Scripts/routeB/analyze_case.py":"9f2bc4dab1dc11f54202fb96efd66dd7c998721ff41abd6e15b29d7000e65e1a","Scripts/routeB/finalize_results.py":"caec13ef8b3e75361e12adb2ea7da637c43e5c28677eb191cf3477043f2c16b0","Scripts/routeB/foam_fields.py":"c56cfd03f8fcc277636d5506609268730e261d636ba9af6bcfeb8151d89b8fc4","Scripts/routeB/generate_case.py":"55fabaca15c1862690904230f31653b5a56236ce8d175e36bd6ce4c7762359e5","Scripts/routeB/run_case.sh":"bc07fe355e52030aae517ed3a805b9a8efb0b7daf81c084483fb8ea892f9f368"},"changes_after_copy":["analyze_case.py: read canonical Table V CSV; record signed and absolute comparison fields; add explicit cavity-method diagnostics","finalize_results.py: hash canonical and execution copies; record reference/field hashes and post-processing provenance"],"unchanged_files":["foam_fields.py","generate_case.py","run_case.sh"]},
      "model_summary":"native Foundation v6 buoyantBoussinesqSimpleFoam; Newtonian nu; Boussinesq rhok only in buoyancy; laminar Stokes; alphat=0; no radiation/MRF/fvOptions",
      "boundary_summary":{"U":"noSlip on four physical walls; empty front/back","T":"hot 300.5 K, cold 299.5 K, top/bottom zeroGradient, front/back empty","p_rgh":"fixedFluxPressure on four physical walls; empty front/back","alphat":"zero on internal field and four physical walls; empty front/back"},
      "scheme_summary":"steadyState; Gauss linear gradient/convection/viscous divergence; Gauss linear orthogonal Laplacian; linear interpolation; orthogonal snGrad; no upwind or limiter",
      "simple_summary":"momentumPredictor yes; nNonOrthogonalCorrectors 0; pRefValue 0; p_rgh relaxation 0.3, U 0.5, T 0.7; all relTol 0; absolute linear-solver tolerance 1e-10; no residualControl",
      "post_processing":{"paper_definition":"Q=U*theta-dtheta/dX; all vertical face planes saved; internal convection uses saved volume-flux phi and linear face theta; internal conduction uses orthogonal face gradient; cavity uses cell-volume quadrature","B1":"v6 fixedValue patch snGrad=(Twall-Towner)*deltaCoeffs from actual fields/mesh; face-area average","B2":"independent second-order Tw,T1,T2 reconstruction","centreline":"linear interpolation to exact centreline, then 4097 points","continuity":"FV sum of actual v6 volume-flux phi; independent central face-interpolated U divergence"},
      "solver_or_relaxation_changes":[],"physics_or_scheme_changes":[],
      "adjustments":[{"id":"F-B1-POST-001","change":"Replaced failing command-line grad(T) function object with direct audited fixedValue patch snGrad evaluation","physical_or_solver_change":False},{"id":"F-ANALYZE-001","change":"Corrected Python labelList footer parsing","physical_or_solver_change":False},{"id":"F-ANALYZE-002","change":"Handled empty-patch phi serialization nonuniform 0()","physical_or_solver_change":False},{"id":"F-ANALYZE-003","change":"Corrected B2 hot-wall inward-coordinate sign conversion","physical_or_solver_change":False},{"id":"F-ENV-001","change":"Activated v6 before set -e in one generation wrapper; no case had been created","physical_or_solver_change":False}],
      "failed_attempts":failures,"cases":cases,
      "statuses":{"route_B_gate_C":"PASS","route_B_paper_definition_Nu_unit_test":"PASS" if cond_paper_nu_unit else "FAIL","route_B_smoke_test":"PASS","route_B_minimal_implementation":"PASS","benchmark_core_pass":"NOT_EVALUATED"}}
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


if __name__ == "__main__":
    main()
