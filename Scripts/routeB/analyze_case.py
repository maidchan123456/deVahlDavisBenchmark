#!/usr/bin/env python3
"""Analyze an executed v6 Route B case and write canonical v13-side data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from foam_fields import latest_time, read_boundary_scalar, read_label_list, read_scalar, read_vector

V13_ROOT = Path("/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark")
RESULTS = V13_ROOT / "results/routeB"
PAPER_REFERENCE = V13_ROOT / "reference/de_vahl_davis_table_v.csv"


def residual_history(path: Path) -> tuple[dict[int, dict[str, float]], dict[int, dict[str, float]]]:
    rows: dict[int, dict[str, float]] = {}
    continuity: dict[int, dict[str, float]] = {}
    current = None
    time_re = re.compile(r"^Time = ([0-9.eE+-]+)")
    solve_re = re.compile(r"Solving for ([^,]+), Initial residual = ([^,]+), Final residual = ([^,]+)")
    cont_re = re.compile(r"continuity errors : sum local = ([^,]+), global = ([^,]+), cumulative = ([^ ]+)")
    for line in path.read_text().splitlines():
        match = time_re.match(line)
        if match:
            current = int(round(float(match.group(1))))
            rows.setdefault(current, {})
            continue
        match = solve_re.search(line)
        if match and current is not None:
            field = match.group(1)
            initial, final = float(match.group(2)), float(match.group(3))
            rows[current][f"{field}_initial"] = max(initial, rows[current].get(f"{field}_initial", 0.0))
            rows[current][f"{field}_final"] = max(final, rows[current].get(f"{field}_final", 0.0))
        match = cont_re.search(line)
        if match and current is not None:
            continuity[current] = {"sum_local": float(match.group(1)), "global": float(match.group(2)), "cumulative": float(match.group(3))}
    return rows, continuity


def centreline(U: np.ndarray, nx: int, ny: int, L: float, alpha: float) -> dict[str, object]:
    x = (np.arange(nx) + 0.5) * L / nx
    y = (np.arange(ny) + 0.5) * L / ny
    q = np.linspace(0, L, 4097)
    ux_cells = 0.5 * (U[:, nx//2-1, 0] + U[:, nx//2, 0])
    vy_cells = 0.5 * (U[ny//2-1, :, 1] + U[ny//2, :, 1])
    uq = np.interp(q, np.r_[0, y, L], np.r_[0, ux_cells, 0]) * L / alpha
    vq = np.interp(q, np.r_[0, x, L], np.r_[0, vy_cells, 0]) * L / alpha
    ui, vi, umin, vmin = np.argmax(uq), np.argmax(vq), np.argmin(uq), np.argmin(vq)
    return {
        "coordinate": q / L, "U": uq, "V": vq,
        "Umax": float(uq[ui]), "Umax_Y": float(q[ui]/L),
        "Vmax": float(vq[vi]), "Vmax_X": float(q[vi]/L),
        "Umin": float(uq[umin]), "Umin_Y": float(q[umin]/L),
        "Vmin": float(vq[vmin]), "Vmin_X": float(q[vmin]/L),
    }


def nusselt(case: Path, time_dir: Path, T: np.ndarray, nx: int, ny: int, L: float, dT: float, th: float, tc: float) -> dict[str, object]:
    h = L / nx
    # B1 is the fixedValueFvPatchField::snGrad operation used by v6:
    # (Twall - Towner)*deltaCoeffs.  On this orthogonal mesh deltaCoeffs=2/h.
    # Both arrays below are outward normal gradients with the task's sign convention.
    hot_b1 = L * (th - T[:, 0]) * (2/h) / dT
    cold_b1 = -L * (tc - T[:, -1]) * (2/h) / dT
    # Independent quadratic in inward wall coordinate s=(0,h/2,3h/2).
    hot_dtds = (-8*th/3 + 3*T[:, 0] - T[:, 1]/3) / h
    cold_dtds = (-8*tc/3 + 3*T[:, -1] - T[:, -2]/3) / h
    # Hot-wall inward derivative is negative; Nu_h is defined positive into fluid.
    hot_b2 = -L * hot_dtds / dT
    cold_b2 = L * cold_dtds / dT
    return {
        "hot_b1_local": hot_b1, "cold_b1_local": cold_b1,
        "hot_b2_local": hot_b2, "cold_b2_local": cold_b2,
        "hot_b1": float(hot_b1.mean()), "cold_b1": float(cold_b1.mean()),
        "hot_b2": float(hot_b2.mean()), "cold_b2": float(cold_b2.mean()),
    }


def continuity_metrics(case: Path, time_dir: Path, U: np.ndarray, nx: int, ny: int, L: float, width: float) -> tuple[float, float]:
    """Return FV mean |div(phi)| and independently reconstructed mean |div(U)|."""
    mesh = case / "constant/polyMesh"
    owners = read_label_list(mesh / "owner")
    neighbours = read_label_list(mesh / "neighbour")
    phi_internal = read_scalar(time_dir / "phi", len(neighbours))
    flux_sum = np.zeros(nx*ny)
    np.add.at(flux_sum, owners[:len(neighbours)], phi_internal)
    np.add.at(flux_sum, neighbours, -phi_internal)
    # blockMesh boundary face ordering follows the declared patch ordering.
    offset = len(neighbours)
    for patch, size in (("hotWall",ny),("coldWall",ny),("bottomWall",nx),("topWall",nx),("front",nx*ny),("back",nx*ny)):
        # Empty faces have no solution-direction flux and are serialized as
        # "nonuniform 0()" rather than a face-sized scalar list.
        if patch not in ("front", "back"):
            values = read_boundary_scalar(time_dir / "phi", patch, size)
            np.add.at(flux_sum, owners[offset:offset+size], values)
        offset += size
    cell_volume = (L/nx)*(L/ny)*width
    mean_div_phi = float(np.mean(np.abs(flux_sum/cell_volume)))

    # Independent central face interpolation of cell U with no-slip wall values.
    hx, hy = L/nx, L/ny
    ue = np.zeros((ny,nx+1)); vn = np.zeros((ny+1,nx))
    ue[:,1:nx] = 0.5*(U[:,:-1,0] + U[:,1:,0])
    vn[1:ny,:] = 0.5*(U[:-1,:,1] + U[1:,:,1])
    div_u = (ue[:,1:]-ue[:,:-1])/hx + (vn[1:,:]-vn[:-1,:])/hy
    return mean_div_phi, float(np.mean(np.abs(div_u)))


def rwin(values: np.ndarray, scale: float = 1.0) -> float:
    return float((values.max()-values.min()) / max(abs(values.mean()), scale))


def read_paper_reference(path: Path) -> dict[int, dict[str, float]]:
    """Read the single canonical machine-readable source for Table V."""
    table: dict[int, dict[str, float]] = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            table[int(row["Ra"])] = {key:float(value) for key,value in row.items()
                                      if key not in ("Ra","source_note") and value not in (None,"")}
    return table


def paper_difference(calculated: float, reference: float, position: bool) -> dict[str, float | str]:
    signed=calculated-reference
    if position:
        return {"calculated":calculated,"reference":reference,
                "signed_position_difference":signed,"absolute_position_error":abs(signed),
                "error":signed,"error_legacy_semantics":"signed position difference; do not use for Gate judgement"}
    signed_relative=signed/reference
    return {"calculated":calculated,"reference":reference,
            "signed_relative_difference":signed_relative,"absolute_relative_error":abs(signed)/abs(reference),
            "error":signed_relative,"error_legacy_semantics":"signed relative difference; do not use for Gate judgement"}


def local_quartic_extremum(z: np.ndarray, values: np.ndarray, kind: str) -> dict[str, float | str]:
    """Fixed five-face local quartic rule for benchmark extrema."""
    raw_index = int(np.argmax(values) if kind == "max" else np.argmin(values))
    start = min(max(raw_index - 2, 0), len(z) - 5)
    zs, vs = z[start:start+5], values[start:start+5]
    polynomial = np.polyfit(zs, vs, 4)
    candidates: list[tuple[float, float, str]] = [
        (float(z[raw_index]), float(values[raw_index]), "raw_face_centre")
    ]
    for root in np.roots(np.polyder(polynomial)):
        if abs(root.imag) < 1e-10 and zs[0] <= root.real <= zs[-1]:
            candidates.append((float(root.real), float(np.polyval(polynomial, root.real)),
                               "local_quartic_stationary_point"))
    if start == 0:
        candidates.append((0.0, float(np.polyval(polynomial, 0.0)),
                           "local_quartic_endpoint_extrapolation"))
    if start + 5 == len(z):
        candidates.append((1.0, float(np.polyval(polynomial, 1.0)),
                           "local_quartic_endpoint_extrapolation"))
    selected = (max if kind == "max" else min)(candidates, key=lambda item: item[1])
    return {"raw_value": float(values[raw_index]), "raw_Z": float(z[raw_index]),
            "value": selected[1], "Z": selected[0], "method": selected[2]}


def paper_nusselt(case: Path, time_dir: Path, T: np.ndarray, U: np.ndarray,
                   nx: int, ny: int, L: float, width: float, alpha: float,
                   dT: float, th: float, tc: float, wall: dict[str, object]) -> dict[str, object]:
    """FV evaluation of Q=U*theta-dtheta/dX on every vertical face plane.

    The convective term uses the saved solver volume flux phi and the active
    linear face interpolation of theta.  The conductive term uses the
    orthogonal face-normal two-cell gradient and actual face area.
    """
    dx, dz = L/nx, L/ny
    theta = (T-tc)/dT
    owners_all = read_label_list(case/"constant/polyMesh/owner")
    neighbours = read_label_list(case/"constant/polyMesh/neighbour")
    owners = owners_all[:len(neighbours)]
    phi = read_scalar(time_dir/"phi", len(neighbours))
    flat_T, flat_theta = T.ravel(), theta.ravel()
    sections = np.empty(nx+1)
    sections[0], sections[-1] = wall["hot_b1"], wall["cold_b1"]
    for plane in range(1, nx):
        mask = (neighbours-owners == 1) & (owners % nx == plane-1)
        if int(np.count_nonzero(mask)) != ny:
            raise ValueError(f"Expected {ny} faces on X-plane {plane}/{nx}, found {np.count_nonzero(mask)}")
        theta_face = 0.5*(flat_theta[owners[mask]] + flat_theta[neighbours[mask]])
        convective = float(np.sum(phi[mask]*theta_face)/(alpha*width))
        conductive = float(np.sum(
            -(flat_T[neighbours[mask]]-flat_T[owners[mask]])/dx * (width*dz)
        )/(width*dT))
        sections[plane] = convective + conductive
    cavity = 1.0 + float(np.mean((L/alpha)*U[:, :, 0]*theta))
    cavity_from_sections = float(np.trapz(sections, np.linspace(0.0, 1.0, nx+1)))
    return {"X": np.linspace(0.0, 1.0, nx+1), "sections": sections,
            "Nu_bar_0": float(sections[0]), "Nu_bar_half": float(sections[nx//2]),
            "Nu_bar_cavity": cavity, "Nu_bar_1": float(sections[-1]),
            "Nu_bar_cavity_from_section_trapezoid":cavity_from_sections}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    args = parser.parse_args()
    case = Path(args.case).resolve()
    manifest = json.loads((case / "case_manifest.json").read_text())
    case_id = manifest["case_id"]
    nx, ny, nz = manifest["grid"]
    n = nx*ny*nz
    L = manifest["geometry_m"]["L"]
    alpha = manifest["properties"]["alpha0_m2_s"]
    beta = manifest["properties"]["beta_1_K"]
    tref = manifest["properties"]["TRef_K"]
    th, tc, dT = manifest["properties"]["Th_K"], manifest["properties"]["Tc_K"], manifest["properties"]["DeltaT_K"]
    end, final_dir = latest_time(case)
    T = read_scalar(final_dir / "T", n).reshape((ny, nx))
    U = read_vector(final_dir / "U", n).reshape((ny, nx, 3))
    p = read_scalar(final_dir / "p", n)
    prgh = read_scalar(final_dir / "p_rgh", n)
    alphat = read_scalar(final_dir / "alphat", n)
    nu = nusselt(case, final_dir, T, nx, ny, L, dT, th, tc)
    paper_nu = paper_nusselt(case, final_dir, T, U, nx, ny, L,
                             manifest["geometry_m"]["W"], alpha, dT, th, tc, nu)
    z_faces = (np.arange(ny)+0.5)/ny
    nu_maximum = local_quartic_extremum(z_faces, nu["hot_b1_local"], "max")
    nu_minimum = local_quartic_extremum(z_faces, nu["hot_b1_local"], "min")
    reference = read_paper_reference(PAPER_REFERENCE).get(int(round(manifest["Ra_target"])))
    paper_comparison = None
    if reference:
        calculated = {"Nu_bar_0":paper_nu["Nu_bar_0"],"Nu_bar_half":paper_nu["Nu_bar_half"],
                      "Nu_bar_cavity":paper_nu["Nu_bar_cavity"],
                      "Nu_hot_local_max":nu_maximum["value"],"Nu_hot_local_max_Z":nu_maximum["Z"],
                      "Nu_hot_local_min":nu_minimum["value"],"Nu_hot_local_min_Z":nu_minimum["Z"]}
        paper_comparison = {key:paper_difference(calculated[key],value,key.endswith("_Z"))
                            for key,value in reference.items()}
        paper_comparison["Nu_bar_1"]={"calculated":paper_nu["Nu_bar_1"],"reference":None,"error":None,
                                      "note":"Table V contains no independent cold-wall mean reference"}
    centre = centreline(U, nx, ny, L, alpha)
    speed = np.linalg.norm(U, axis=2)
    x = (np.arange(nx)+0.5)*L/nx
    y = (np.arange(ny)+0.5)*L/ny
    X, Y = np.meshgrid(x, y)
    theta = (T-tc)/dT
    rhok = 1-beta*(T-tref)

    patch_sizes = {"hotWall": ny, "coldWall": ny, "bottomWall": nx, "topWall": nx}
    alphat_patch_max = max(float(np.max(np.abs(read_boundary_scalar(final_dir/"alphat", patch, size)))) for patch, size in patch_sizes.items())
    pref_cell = manifest["pRefCell"]
    cell_centres = np.column_stack((X.ravel(), Y.ravel(), np.full(n, manifest["geometry_m"]["W"]/2)))
    pref_centre_error = float(np.max(np.abs(cell_centres[pref_cell]-np.array(manifest["pRefCellCentre_m"]))))

    mean_div_phi, mean_div_u = continuity_metrics(case, final_dir, U, nx, ny, L, manifest["geometry_m"]["W"])
    up = float(speed.max())
    epsilon_phi = L*mean_div_phi/up if up else None
    epsilon_v = L*mean_div_u/up if up else None

    residuals, continuity = residual_history(case/"log.buoyantBoussinesqSimpleFoam")
    sample_times = sorted(
        int(round(float(path.name))) for path in case.iterdir()
        if path.is_dir() and path.name not in ("constant", "system", "postProcessing")
        and path.name != "0" and (path/"T").exists() and (path/"U").exists()
    )
    monitor = {}
    for time in sample_times:
        folder = case/str(time)
        Ti = read_scalar(folder/"T", n).reshape((ny,nx))
        Ui = read_vector(folder/"U", n).reshape((ny,nx,3))
        nui = nusselt(case, folder, Ti, nx, ny, L, dT, th, tc)
        paper_i = paper_nusselt(case, folder, Ti, Ui, nx, ny, L,
                                manifest["geometry_m"]["W"], alpha, dT, th, tc, nui)
        ci = centreline(Ui, nx, ny, L, alpha)
        monitor[time] = {**{k:nui[k] for k in ("hot_b1","cold_b1","hot_b2","cold_b2")},
                         **{k:paper_i[k] for k in ("Nu_bar_0","Nu_bar_half","Nu_bar_cavity","Nu_bar_1")},
                         "Umax":ci["Umax"], "Vmax":ci["Vmax"],
                         "heat_imbalance":abs(nui["hot_b1"]-nui["cold_b1"])/((nui["hot_b1"]+nui["cold_b1"])/2)}
    window_times = [t for t in sample_times if end-200 <= t <= end]
    nus = np.array([0.5*(monitor[t]["hot_b1"]+monitor[t]["cold_b1"]) for t in window_times])
    half_nus = np.array([monitor[t]["Nu_bar_half"] for t in window_times])
    us = np.array([monitor[t]["Umax"] for t in window_times])
    vs = np.array([monitor[t]["Vmax"] for t in window_times])
    heat = np.array([monitor[t]["heat_imbalance"] for t in window_times])
    final_res = residuals[end]
    final_initial_residuals = {name: final_res.get(f"{name}_initial", math.nan) for name in ("Ux","Uy","T","p_rgh")}
    log_text = (case/"log.buoyantBoussinesqSimpleFoam").read_text()

    result_dir = RESULTS/"cases"/case_id
    fig_dir = RESULTS/"figures"
    result_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    with (result_dir/"local_nusselt.csv").open("w", newline="") as stream:
        writer=csv.writer(stream,lineterminator="\n"); writer.writerow(["Z","Nu_hot_B1","Nu_hot_B2","Nu_cold_B1","Nu_cold_B2","Y_legacy_alias"])
        writer.writerows(zip(y/L,nu["hot_b1_local"],nu["hot_b2_local"],nu["cold_b1_local"],nu["cold_b2_local"],y/L))
    with (result_dir/"section_nusselt.csv").open("w", newline="") as stream:
        writer=csv.writer(stream,lineterminator="\n"); writer.writerow(["X","Nu_bar_X","definition"])
        writer.writerows(zip(paper_nu["X"],paper_nu["sections"],["U*theta-dtheta/dX"]*(nx+1)))
    with (result_dir/"centreline_4097.csv").open("w",newline="") as stream:
        writer=csv.writer(stream,lineterminator="\n"); writer.writerow(["index","coordinate","U_at_X0.5","W_at_Z0.5","V_at_Y0.5_legacy_alias"])
        writer.writerows(zip(range(4097),centre["coordinate"],centre["U"],centre["V"],centre["V"]))
    fields=["case_id","iteration","Ux_initial","Uy_initial","T_initial","p_rgh_initial","continuity_sum_local","continuity_global","continuity_cumulative","Nu_bar_0","Nu_bar_half","Nu_bar_cavity","Nu_bar_1","Nu_hot_B1","Nu_cold_B1","Nu_hot_B2","Nu_cold_B2","heat_imbalance","Umax","Wmax","Vmax_legacy_alias"]
    with (result_dir/"convergence.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n"); writer.writeheader()
        for it in sorted(residuals):
            row={"case_id":case_id,"iteration":it}
            for key in ("Ux_initial","Uy_initial","T_initial","p_rgh_initial"):
                row[key]=residuals[it].get(key,"")
            if it in continuity:
                row.update({f"continuity_{k}":v for k,v in continuity[it].items()})
            if it in monitor:
                row.update({"Nu_bar_0":monitor[it]["Nu_bar_0"],"Nu_bar_half":monitor[it]["Nu_bar_half"],"Nu_bar_cavity":monitor[it]["Nu_bar_cavity"],"Nu_bar_1":monitor[it]["Nu_bar_1"],"Nu_hot_B1":monitor[it]["hot_b1"],"Nu_cold_B1":monitor[it]["cold_b1"],"Nu_hot_B2":monitor[it]["hot_b2"],"Nu_cold_B2":monitor[it]["cold_b2"],"heat_imbalance":monitor[it]["heat_imbalance"],"Umax":monitor[it]["Umax"],"Wmax":monitor[it]["Vmax"],"Vmax_legacy_alias":monitor[it]["Vmax"]})
            writer.writerow(row)

    path_difference=max(abs(nu["hot_b1"]-nu["hot_b2"])/((abs(nu["hot_b1"])+abs(nu["hot_b2"]))/2),abs(nu["cold_b1"]-nu["cold_b2"])/((abs(nu["cold_b1"])+abs(nu["cold_b2"]))/2))
    heat_imbalance=abs(nu["hot_b1"]-nu["cold_b1"])/((nu["hot_b1"]+nu["cold_b1"])/2)
    result={
        "case_id":case_id,"final_iteration":end,
        "Nu_bar_0":paper_nu["Nu_bar_0"],"Nu_bar_half":paper_nu["Nu_bar_half"],"Nu_bar_cavity":paper_nu["Nu_bar_cavity"],"Nu_bar_1":paper_nu["Nu_bar_1"],
        "Nu_bar_cavity_from_section_trapezoid":paper_nu["Nu_bar_cavity_from_section_trapezoid"],"Nu_bar_cavity_discrete_method_difference":paper_nu["Nu_bar_cavity"]-paper_nu["Nu_bar_cavity_from_section_trapezoid"],
        "Nu_bar_cavity_discrete_method_difference_legacy_semantics":"signed primary minus section-trapezoid; use the explicit absolute/relative fields for diagnostics",
        "Nu_bar_cavity_method_absolute_difference":abs(paper_nu["Nu_bar_cavity"]-paper_nu["Nu_bar_cavity_from_section_trapezoid"]),
        "Nu_bar_cavity_method_relative_difference":abs(paper_nu["Nu_bar_cavity"]-paper_nu["Nu_bar_cavity_from_section_trapezoid"])/abs(paper_nu["Nu_bar_cavity"]),
        "Nu_bar_cavity_method_relative_difference_denominator":"abs(Nu_bar_cavity), where Nu_bar_cavity is the primary cell-volume quadrature",
        "Nu_bar_0_path1":nu["hot_b1"],"Nu_bar_0_path2":nu["hot_b2"],"Nu_bar_1_path1":nu["cold_b1"],"Nu_bar_1_path2":nu["cold_b2"],
        "Nu_hot_B1":nu["hot_b1"],"Nu_hot_B2":nu["hot_b2"],"Nu_cold_B1":nu["cold_b1"],"Nu_cold_B2":nu["cold_b2"],
        "Nu_path_relative_difference":path_difference,"heat_imbalance":heat_imbalance,
        "section_Nu_max_relative_deviation_from_half":float(np.max(np.abs(paper_nu["sections"]-paper_nu["Nu_bar_half"]))/abs(paper_nu["Nu_bar_half"])),
        "paper_Nu_definition":"Q=U*theta-dtheta/dX",
        "paper_reference_file":str(PAPER_REFERENCE.relative_to(V13_ROOT)),
        "paper_Nu_discretization":"walls: B1 orthogonal patch snGrad; internal vertical faces: saved volume flux phi times linearly interpolated theta plus two-cell orthogonal conductive flux integrated with face area; cavity: cell-volume U*theta quadrature plus exact imposed-wall conductive integral 1",
        "Nu_hot_local_max":nu_maximum["value"],"Nu_hot_local_max_Z":nu_maximum["Z"],"Nu_hot_local_min":nu_minimum["value"],"Nu_hot_local_min_Z":nu_minimum["Z"],
        "Nu_max":nu_maximum["value"],"Z_at_Nu_max":nu_maximum["Z"],"Nu_min":nu_minimum["value"],"Z_at_Nu_min":nu_minimum["Z"],
        "Nu_hot_local_raw_max":nu_maximum["raw_value"],"Nu_hot_local_raw_max_Z":nu_maximum["raw_Z"],"Nu_hot_local_raw_min":nu_minimum["raw_value"],"Nu_hot_local_raw_min_Z":nu_minimum["raw_Z"],
        "Nu_hot_local_extrema_method":"fixed local quartic through five adjacent face-centre values; derivative root inside the local interval; endpoint evaluated by the same quartic only when the five-point window touches it",
        "paper_comparison_like_for_like":paper_comparison,
        "B1_method":"OpenFOAM v6 fixedValue patch snGrad formula (Twall-Towner)*deltaCoeffs, evaluated from actual patch and owner-cell T; orthogonal mesh deltaCoeffs=2/h; uniform face-area average. Used after postProcess grad(T) failed in the installed v6 OSHA1 dictionary-digest path.",
        "B2_method":"independent quadratic through Tw,T1,T2 at inward coordinates 0,h/2,3h/2; derivative (-8Tw/3+3T1-T2/3)/h; Nu_hot=-L*dT/ds/DeltaT and Nu_cold=+L*dT/ds/DeltaT; face-centre rows only",
        "Umax":centre["Umax"],"Umax_Z":centre["Umax_Y"],"Wmax":centre["Vmax"],"Wmax_X":centre["Vmax_X"],"Umin":centre["Umin"],"Umin_Z":centre["Umin_Y"],"Wmin":centre["Vmin"],"Wmin_X":centre["Vmin_X"],
        **{k:centre[k] for k in ("Umax_Y","Vmax","Vmax_X","Umin_Y","Vmin","Vmin_X")},
        "centreline_method":"linear interpolation from two bracketing cell-centre lines to exact centreline, then 4097 uniform points including no-slip endpoints",
        "max_dimensionless_velocity":float(speed.max()*L/alpha),
        "max_theta_analytic_error":float(np.max(np.abs(theta-(1-X/L)))),
        "temperature_range_K":[float(T.min()),float(T.max())],"rhok_range":[float(rhok.min()),float(rhok.max())],
        "alphat_max_abs_internal_m2_s":float(np.max(np.abs(alphat))),"alphat_max_abs_physical_patches_m2_s":alphat_patch_max,
        "pressure":{"p_dimension":"m2/s2","p_rgh_dimension":"m2/s2","p_min":float(p.min()),"p_max":float(p.max()),"p_rgh_min":float(prgh.min()),"p_rgh_max":float(prgh.max()),"p_at_ref_cell":float(p[pref_cell]),"pRefCell":pref_cell,"actual_pRefCellCentre_m":cell_centres[pref_cell].tolist(),"pRefCellCentre_error_m":pref_centre_error,"pRefValue_m2_s2":manifest["pRefValue_m2_s2"]},
        "continuity":{"mean_abs_div_phi_1_s":mean_div_phi,"mean_abs_div_U_1_s":mean_div_u,"epsilon_phi":epsilon_phi,"epsilon_v":epsilon_v,"epsilon_m":epsilon_v,"mass_relation":"rho0 is constant, so normalized mass- and volume-divergence metrics are identical; solver phi is volume flux"},
        "final_initial_residuals":final_initial_residuals,
        "final_log_continuity":continuity.get(end),
        "Rwin":{"window_start_iteration":end-200,"window_end_iteration":end,"sample_times":window_times,"samples":len(window_times),"Nu":rwin(nus),"Nu_legacy_wall_pair_monitor":rwin(nus),"Nu_bar_half":rwin(half_nus),"primary_mean_Nu_candidate":"Nu_bar_half; legacy Gate D remains unchanged","Umax":rwin(us),"Vmax":rwin(vs),"scales":{"Nu":1.0,"Umax":1.0,"Vmax":1.0},"heat_imbalance_start":float(heat[0]),"heat_imbalance_end":float(heat[-1]),"heat_imbalance_linear_slope_per_iteration":float(np.polyfit(window_times,heat,1)[0])},
        "normal_exit":"End" in log_text,
        "fatal_or_nan":bool(re.search(r"FOAM FATAL (?:ERROR|IO ERROR)|Floating point exception \(core dumped\)|\bnan\b|\binf\b",log_text,re.I)),
    }
    (result_dir/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")

    plt.figure(figsize=(6.2,4.2))
    if case_id=="B-COND":
        plt.plot(x/L,theta[ny//2],"o",ms=2.5,label="Route B cell centres"); plt.plot([0,1],[1,0],"k--",label="analytic $1-X$")
        plt.xlabel("X"); plt.ylabel(r"$\theta$"); plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(fig_dir/"B-COND_theta_analytic.png",dpi=180); plt.close()
        plt.figure(figsize=(6.2,4.2)); plt.plot(window_times,nus); plt.xlabel("steady iteration"); plt.ylabel("mean Nu (B1)"); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(fig_dir/"B-COND_Nu_final_window.png",dpi=180); plt.close()
    else:
        plt.contourf(X/L,Y/L,theta,levels=30,cmap="coolwarm"); plt.colorbar(label=r"$\theta$"); plt.xlabel("X"); plt.ylabel("Z"); plt.axis("equal"); plt.tight_layout(); plt.savefig(fig_dir/"B-SMOKE_theta.png",dpi=180); plt.close()
        plt.figure(figsize=(6.2,5.2)); plt.streamplot(x/L,y/L,U[:,:,0],U[:,:,1],density=1.3,color=speed,cmap="viridis"); plt.colorbar(label="|U| [m/s]"); plt.xlabel("X"); plt.ylabel("Z"); plt.axis("equal"); plt.tight_layout(); plt.savefig(fig_dir/"B-SMOKE_velocity_streamlines.png",dpi=180); plt.close()
    plt.figure(figsize=(6.2,4.2)); plt.plot(centre["coordinate"],centre["U"],label=r"$U(X=0.5,Z)$"); plt.plot(centre["coordinate"],centre["V"],label=r"$W(X,Z=0.5)$"); plt.xlabel("dimensionless centreline coordinate"); plt.ylabel("dimensionless velocity"); plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(fig_dir/f"{case_id}_centrelines.png",dpi=180); plt.close()
    plt.figure(figsize=(6.2,4.2)); plt.plot(paper_nu["X"],paper_nu["sections"],label=r"$\overline{Nu}_X$"); plt.axhline(paper_nu["Nu_bar_cavity"],color="k",ls="--",label=r"$\overline{Nu}$ (cell volume)"); plt.xlabel("X"); plt.ylabel("paper-definition mean Nu"); plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(fig_dir/f"{case_id}_section_Nu.png",dpi=180); plt.close()
    plt.figure(figsize=(6.2,4.2)); plt.plot(y/L,nu["hot_b1_local"],label="hot B1"); plt.plot(y/L,nu["hot_b2_local"],"--",label="hot B2"); plt.plot(y/L,nu["cold_b1_local"],label="cold B1"); plt.plot(y/L,nu["cold_b2_local"],"--",label="cold B2"); plt.xlabel("Z"); plt.ylabel("local Nu"); plt.legend(); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(fig_dir/f"{case_id}_local_Nu.png",dpi=180); plt.close()
    plt.figure(figsize=(6.2,4.2)); plt.imshow(speed*L/alpha,origin="lower",extent=(0,1,0,1),aspect="equal",cmap="magma"); plt.colorbar(label="dimensionless |U|"); plt.xlabel("X"); plt.ylabel("Z"); plt.tight_layout(); plt.savefig(fig_dir/f"{case_id}_velocity_magnitude.png",dpi=180); plt.close()
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
