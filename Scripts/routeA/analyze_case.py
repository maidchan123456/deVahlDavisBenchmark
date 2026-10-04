#!/usr/bin/env python3
"""Compute fixed Route A diagnostics and figures from an executed case."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from foam_fields import latest_time, read_scalar, read_vector

ROOT = Path(__file__).resolve().parents[2]
PAPER_REFERENCE = ROOT / "reference/de_vahl_davis_table_v.csv"


def classify_health_lines(lines) -> dict[str, bool]:
    """Keep fatal/nonfinite detection; exclude only known normal FPE banners."""
    normal_fpe_banner = re.compile(
        r"(?:sigFpe\s*:\s*Enabling\s+)?floating point exception trapping"
        r"(?:\s+\(FOAM_SIGFPE\)\.)?", re.I,
    )
    flags = {"fatal": False, "fpe": False, "nonfinite": False}
    for line in lines:
        flags["fatal"] |= bool(re.search(r"FOAM FATAL (?:ERROR|IO ERROR)", line, re.I))
        flags["nonfinite"] |= bool(re.search(r"\bnan\b|\binf\b", line, re.I))
        if not normal_fpe_banner.fullmatch(line.strip()):
            flags["fpe"] |= bool(re.search(r"Floating point exception", line, re.I))
    return flags


def read_wall_heat(path: Path) -> dict[float, dict[str, dict[str, float | str]]]:
    data: dict[float, dict[str, dict[str, float | str]]] = {}
    with path.open() as stream:
        for line in stream:
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split()
            t = float(cols[0])
            if cols[1] in data.get(t, {}):
                raise ValueError("Duplicate wall sample: select one restart segment")
            data.setdefault(t, {})[cols[1]] = {
                "min": float(cols[2]), "max": float(cols[3]),
                "Q": float(cols[4]), "q": float(cols[5]),
                "Q_decimal_token": cols[4],
            }
    return data


def read_sample(path: Path) -> np.ndarray:
    return np.loadtxt(path, comments="#")


def sample_extrema(case: Path, t: float, alpha0: float, L: float) -> tuple[float, float]:
    folder = case / "postProcessing/centrelineMonitor" / format(t, ".12g")
    vertical = read_sample(folder / "vertical.xy")
    horizontal = read_sample(folder / "horizontal.xy")
    return float(np.max(vertical[:, 1]) * L / alpha0), float(np.max(horizontal[:, 2]) * L / alpha0)


def parse_residuals(log: Path) -> dict[int, dict[str, float]]:
    with log.open() as stream:
        return parse_residual_lines(stream)


def parse_residual_lines(lines) -> dict[int, dict[str, float]]:
    """Extract Initial and Final separately; max over correctors per iteration."""
    current = None
    rows: dict[int, dict[str, float]] = {}
    time_re = re.compile(r"^Time = ([0-9.eE+-]+)s")
    solve_re = re.compile(r"Solving for ([^,]+), Initial residual = ([^,]+), Final residual = ([^,]+)")
    for line in lines:
        m = time_re.match(line)
        if m:
            value = float(m.group(1))
            if not math.isfinite(value) or not value.is_integer():
                raise ValueError("Gate D requires integer steady iteration labels")
            current = int(value)
            if current in rows:
                raise ValueError("Duplicate iteration: do not merge restart logs silently")
            rows[current] = {}
            continue
        m = solve_re.search(line)
        if m and current is not None:
            field = m.group(1)
            initial = float(m.group(2))
            final = float(m.group(3))
            if not math.isfinite(initial) or not math.isfinite(final):
                raise ValueError("Nonfinite solver residual")
            rows[current][f"{field}_initial"] = max(initial, rows[current].get(f"{field}_initial", 0.0))
            rows[current][f"{field}_final"] = max(final, rows[current].get(f"{field}_final", 0.0))
    return rows


def evaluate_gate_d_monitors(wall, velocity_by_iteration, residuals,
                             end_iteration: int, conduction_heat_rate) -> dict:
    """Contract v1.0 numerical checks only; no case/result writes or solver calls.

    Heat slope uses exact rationals of the original decimal Q tokens. Its sign
    never depends on a rounded float regression or a positive tolerance.
    Execution/provenance/field-validity flags remain the caller's responsibility.
    """
    if end_iteration < 200 or end_iteration % 10:
        raise ValueError("Endpoint must cover 200 iterations and end on cadence 10")
    start = end_iteration - 199
    times = list(range(start, end_iteration + 1))
    sample_times = [t for t in times if t % 10 == 0]
    if any(t not in wall for t in times):
        raise ValueError("Incomplete 200-sample wall window")
    if set(velocity_by_iteration) != set(sample_times):
        raise ValueError("Expected exactly 20 velocity samples on cadence 10")
    if any(t not in residuals for t in times):
        raise ValueError("Incomplete residual window")
    scale = Fraction(str(conduction_heat_rate))
    if scale <= 0:
        raise ValueError("Invalid conduction heat rate")
    hot, cold, heat = [], [], []
    for t in times:
        tokens = [wall[t][patch]["Q_decimal_token"] for patch in ("hotWall", "coldWall")]
        if any(not re.fullmatch(r"[+-]?\d\.\d{16,}[eE][+-]?\d+", token)
               for token in tokens):
            raise ValueError("HEAT_TREND_EVALUATOR_UNRESOLVED: insufficient source precision")
        h, c = map(Fraction, tokens)
        if h <= 0 or c >= 0:
            raise ValueError("Wall heat sign/normalization invalid")
        hot.append(h / scale)
        cold.append(-c / scale)
        heat.append(2 * abs(h + c) / (h - c))

    def rwin(values):
        values = [Fraction(str(v)) for v in values]
        mean = sum(values) / len(values)
        return (max(values) - min(values)) / max(abs(mean), Fraction(1))

    ranges = {"Nu_bar_0": rwin(hot)}
    for i, name in enumerate(("Umax", "Wmax")):
        ranges[name] = rwin([velocity_by_iteration[t][i] for t in sample_times])
    xmean = Fraction(sum(times), len(times))
    ymean = sum(heat) / len(heat)
    numerator = sum((Fraction(t) - xmean) * (h - ymean)
                    for t, h in zip(times, heat))
    denominator = sum((Fraction(t) - xmean) ** 2 for t in times)
    slope = numerator / denominator
    fields = ("Ux", "Uy", "e", "p_rgh")
    for t in times:
        for field in fields:
            value = residuals[t].get(field + "_initial")
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError(f"Missing/invalid {field} initial residual at {t}")
    final = {field: residuals[end_iteration][field + "_initial"] for field in fields}
    residual_pass = all(value <= 1e-7 for value in final.values())
    qoi_pass = all(value <= Fraction("5e-4") for value in ranges.values())
    return {
        "contract_version": "1.0",
        "window_start_iteration": start, "window_end_iteration": end_iteration,
        "window_inclusive": True, "Nu_samples": len(times),
        "velocity_samples": len(sample_times),
        "velocity_sample_iterations": sample_times,
        "Rwin": {key: float(value) for key, value in ranges.items()},
        "Nu_monitor": "hot-wall Q/(k*DeltaT*W), not the hot/cold pair average",
        "Nu_bar_0_last": float(hot[-1]), "Nu_bar_1_last": float(cold[-1]),
        "heat_imbalance_start": float(heat[0]),
        "heat_imbalance_end": float(heat[-1]),
        "heat_trend_method": "OLS exact rational arithmetic on original decimal Q tokens",
        "heat_slope_per_iteration_display": float(slope),
        "heat_slope_sign_exact": (slope > 0) - (slope < 0),
        "heat_trend_pass": slope <= 0,
        "residual_fields": list(fields), "final_initial_residuals": final,
        "residual_pass": residual_pass, "qoi_rwin_pass": qoi_pass,
        "numerical_checks_pass": qoi_pass and residual_pass and slope <= 0,
        "formal_Gate_D_requires_external_execution_and_provenance_flags": True,
    }


def relative_range(values: np.ndarray, scale: float) -> float:
    return float((values.max() - values.min()) / max(abs(values.mean()), scale))


def read_paper_reference(path: Path) -> dict[int, dict[str, float]]:
    """Read the single canonical machine-readable source for Table V."""
    table: dict[int, dict[str, float]] = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            table[int(row["Ra"])] = {
                key: float(value) for key, value in row.items()
                if key not in ("Ra", "source_note") and value not in (None, "")
            }
    return table


def paper_difference(calculated: float, reference: float, position: bool) -> dict[str, float | str]:
    signed = calculated - reference
    if position:
        return {
            "calculated": calculated, "reference": reference,
            "signed_position_difference": signed,
            "absolute_position_error": abs(signed),
            "error": signed,
            "error_legacy_semantics": "signed position difference; do not use for Gate judgement",
        }
    signed_relative = signed / reference
    return {
        "calculated": calculated, "reference": reference,
        "signed_relative_difference": signed_relative,
        "absolute_relative_error": abs(signed) / abs(reference),
        "error": signed_relative,
        "error_legacy_semantics": "signed relative difference; do not use for Gate judgement",
    }


def local_quartic_extremum(z: np.ndarray, values: np.ndarray, kind: str) -> dict[str, float | str]:
    """Return raw and benchmark extrema using one fixed local quartic rule.

    Five consecutive face-centre values around the raw extremum define the
    quartic.  Interior stationary points are accepted only inside that local
    five-point interval.  If the interval touches Z=0 or Z=1, the corresponding
    endpoint is also evaluated by the same polynomial (explicit extrapolation).
    """
    raw_index = int(np.argmax(values) if kind == "max" else np.argmin(values))
    start = min(max(raw_index - 2, 0), len(z) - 5)
    zs = z[start:start + 5]
    vs = values[start:start + 5]
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
    return {
        "raw_value": float(values[raw_index]), "raw_Z": float(z[raw_index]),
        "value": selected[1], "Z": selected[0], "method": selected[2],
    }


def paper_nusselt(T: np.ndarray, U: np.ndarray, nx: int, ny: int, L: float,
                   alpha0: float, dT: float, th: float, tc: float) -> dict[str, object]:
    """de Vahl Davis diagnostic Q=U*theta-dtheta/dX on the FV mesh.

    Internal vertical faces use the active linear interpolation and orthogonal
    two-cell gradient.  The cavity integral uses cell-volume quadrature; its
    conductive contribution is exactly theta(X=0)-theta(X=1)=1.
    """
    dx = L / nx
    theta = (T - tc) / dT
    sections = np.empty(nx + 1)
    hot_local = L * (th - T[:, 0]) / (0.5 * dx) / dT
    cold_local = L * (T[:, -1] - tc) / (0.5 * dx) / dT
    sections[0], sections[-1] = hot_local.mean(), cold_local.mean()
    for plane in range(1, nx):
        theta_face = 0.5 * (theta[:, plane - 1] + theta[:, plane])
        ux_face = 0.5 * (U[:, plane - 1, 0] + U[:, plane, 0])
        convective = (L / alpha0) * ux_face * theta_face
        conductive = -L * (T[:, plane] - T[:, plane - 1]) / dx / dT
        sections[plane] = np.mean(convective + conductive)
    cavity = 1.0 + float(np.mean((L / alpha0) * U[:, :, 0] * theta))
    cavity_from_sections = float(np.trapz(sections, np.linspace(0.0, 1.0, nx + 1)))
    return {
        "X": np.linspace(0.0, 1.0, nx + 1), "sections": sections,
        "Nu_bar_0": float(sections[0]), "Nu_bar_half": float(sections[nx // 2]),
        "Nu_bar_cavity": cavity, "Nu_bar_1": float(sections[-1]),
        "Nu_bar_cavity_from_section_trapezoid": cavity_from_sections,
        "hot_local": hot_local, "cold_local": cold_local,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("--segment-start", type=int, default=0,
                        help="Restart segment start; wall monitor directory (default: 0)")
    parser.add_argument("--solver-log", type=Path,
                        help="Immutable log for this segment (default: CASE/log.foamRun)")
    args = parser.parse_args()
    case = Path(args.case).resolve()
    solver_log = args.solver_log or case / "log.foamRun"
    manifest = json.loads((case / "case_manifest.json").read_text())
    case_id = manifest["case_id"]
    nx, ny, nz = manifest["grid"]
    n = nx * ny * nz
    L = manifest["geometry_m"]["L"]
    W = manifest["geometry_m"]["W"]
    alpha0 = manifest["properties"]["alpha0_m2_s"]
    k = manifest["properties"]["k_W_mK"]
    rho0 = manifest["properties"]["rho0_kg_m3"]
    dT = manifest["properties"]["DeltaT_K"]
    th = manifest["properties"]["Th_K"]
    tc = manifest["properties"]["Tc_K"]
    final_t, final_dir = latest_time(case)
    T = read_scalar(final_dir / "T", n).reshape((ny, nx))
    U = read_vector(final_dir / "U", n).reshape((ny, nx, 3))
    rho = read_scalar(final_dir / "rho", n).reshape((ny, nx))
    dx = L / nx
    dy = L / ny
    x = (np.arange(nx) + 0.5) * dx
    y = (np.arange(ny) + 0.5) * dy
    X, Y = np.meshgrid(x, y)

    # Path A1 and the separate de Vahl Davis paper-definition diagnostic.
    paper_nu = paper_nusselt(T, U, nx, ny, L, alpha0, dT, th, tc)
    nu_hot_local = paper_nu["hot_local"]
    nu_cold_local = paper_nu["cold_local"]
    nu_hot_a1 = float(nu_hot_local.mean())
    nu_cold_a1 = float(nu_cold_local.mean())

    wall_file = (case / "postProcessing/wallHeatFluxMonitor"
                 / str(args.segment_start) / "wallHeatFlux.dat")
    wall = read_wall_heat(wall_file)
    final_wall = wall[max(wall)]
    q_hot = final_wall["hotWall"]["Q"]
    q_cold = final_wall["coldWall"]["Q"]
    nu_hot_a2 = q_hot / (k * dT * W)
    nu_cold_a2 = -q_cold / (k * dT * W)
    heat_imbalance = abs(nu_hot_a2 - nu_cold_a2) / ((nu_hot_a2 + nu_cold_a2) / 2)
    path_relative_difference = max(
        abs(nu_hot_a1 - nu_hot_a2) / ((abs(nu_hot_a1) + abs(nu_hot_a2)) / 2),
        abs(nu_cold_a1 - nu_cold_a2) / ((abs(nu_cold_a1) + abs(nu_cold_a2)) / 2),
    )
    z_faces = y / L
    nu_maximum = local_quartic_extremum(z_faces, nu_hot_local, "max")
    nu_minimum = local_quartic_extremum(z_faces, nu_hot_local, "min")
    reference = read_paper_reference(PAPER_REFERENCE).get(int(round(manifest["Ra_target"])))
    paper_comparison = None
    if reference:
        calculated = {
            "Nu_bar_0": paper_nu["Nu_bar_0"], "Nu_bar_half": paper_nu["Nu_bar_half"],
            "Nu_bar_cavity": paper_nu["Nu_bar_cavity"],
            "Nu_hot_local_max": nu_maximum["value"], "Nu_hot_local_max_Z": nu_maximum["Z"],
            "Nu_hot_local_min": nu_minimum["value"], "Nu_hot_local_min_Z": nu_minimum["Z"],
        }
        paper_comparison = {
            key: paper_difference(calculated[key], value, key.endswith("_Z"))
            for key, value in reference.items()
        }
        paper_comparison["Nu_bar_1"] = {
            "calculated": paper_nu["Nu_bar_1"], "reference": None, "error": None,
            "note": "Table V contains no independent cold-wall mean reference",
        }

    # Exact x=L/2 and y=L/2 centreline interpolation, then fixed 4097 points.
    line_n = 4097
    yq = np.linspace(0, L, line_n)
    xq = np.linspace(0, L, line_n)
    ux_mid_cells = 0.5 * (U[:, nx // 2 - 1, 0] + U[:, nx // 2, 0])
    vy_mid_cells = 0.5 * (U[ny // 2 - 1, :, 1] + U[ny // 2, :, 1])
    uq = np.interp(yq, np.r_[0, y, L], np.r_[0, ux_mid_cells, 0]) * L / alpha0
    vq = np.interp(xq, np.r_[0, x, L], np.r_[0, vy_mid_cells, 0]) * L / alpha0
    ui = int(np.argmax(uq))
    vi = int(np.argmax(vq))
    uimin = int(np.argmin(uq))
    vimin = int(np.argmin(vq))
    umax = float(uq[ui])
    vmax = float(vq[vi])
    umax_loc = float(yq[ui] / L)
    vmax_loc = float(xq[vi] / L)

    speed = np.linalg.norm(U, axis=2)
    max_dim_speed = float(speed.max() * L / alpha0)
    theta = (T - tc) / dT
    theta_error = float(np.max(np.abs(theta - (1 - X / L))))

    residuals = parse_residuals(solver_log)
    end_iter = int(round(final_t))
    if end_iter - args.segment_start < 200:
        raise ValueError("Do not evaluate a Gate D window across restart segments")
    final_res = residuals[end_iter]
    final_initial_residuals = {
        "Ux": final_res.get("Ux_initial", math.nan),
        "Uy": final_res.get("Uy_initial", math.nan),
        "e": final_res.get("e_initial", math.nan),
        "p_rgh": final_res.get("p_rgh_initial", math.nan),
    }

    start_window = end_iter - 199
    wall_times = np.array(sorted(t for t in wall if start_window <= t <= end_iter))
    nu_series = np.array([
        0.5 * (wall[t]["hotWall"]["Q"] - wall[t]["coldWall"]["Q"]) / (k * dT * W)
        for t in wall_times
    ])
    paper_window: dict[int, dict[str, object]] = {}
    paper_times = sorted(
        int(round(float(folder.name))) for folder in case.iterdir()
        if folder.is_dir() and folder.name.replace(".", "", 1).isdigit()
        and start_window <= float(folder.name) <= end_iter
        and (folder / "T").exists() and (folder / "U").exists()
    )
    for t in paper_times:
        folder = case / str(t)
        Ti = read_scalar(folder / "T", n).reshape((ny, nx))
        Ui = read_vector(folder / "U", n).reshape((ny, nx, 3))
        paper_window[t] = paper_nusselt(Ti, Ui, nx, ny, L, alpha0, dT, th, tc)
    half_series = np.array([paper_window[t]["Nu_bar_half"] for t in paper_times])
    heat_series = np.array([
        abs(wall[t]["hotWall"]["Q"] + wall[t]["coldWall"]["Q"])
        / max(0.5 * abs(wall[t]["hotWall"]["Q"] - wall[t]["coldWall"]["Q"]), 1e-300)
        for t in wall_times
    ])
    sample_times = sorted(
        float(p.name) for p in (case / "postProcessing/centrelineMonitor").iterdir()
        if p.is_dir() and start_window <= float(p.name) <= end_iter
    )
    sampled_extrema = [sample_extrema(case, t, alpha0, L) for t in sample_times]
    us = np.array([v[0] for v in sampled_extrema])
    vs = np.array([v[1] for v in sampled_extrema])
    rwin = {
        "window_start_iteration": start_window,
        "window_end_iteration": end_iter,
        "Nu": relative_range(nu_series, 1.0),
        "Nu_legacy_wall_pair_monitor": relative_range(nu_series, 1.0),
        "Nu_bar_half": relative_range(half_series, 1.0),
        "Nu_bar_half_sample_times": paper_times,
        "Umax": relative_range(us, 1.0),
        "Vmax": relative_range(vs, 1.0),
        "Nu_samples": int(nu_series.size),
        "velocity_samples": int(us.size),
        "scales": {"Nu": 1.0, "Umax": 1.0, "Vmax": 1.0},
        "primary_mean_Nu_candidate": "Nu_bar_half; legacy Gate D remains unchanged",
        "heat_imbalance_start": float(heat_series[0]),
        "heat_imbalance_end": float(heat_series[-1]),
    }
    gate_d_monitors = evaluate_gate_d_monitors(
        wall, {int(t): values for t, values in zip(sample_times, sampled_extrema)},
        residuals, end_iter, k * dT * W,
    )

    div_mass_mean = None
    div_volume_mean = None
    epsilon_m = None
    epsilon_v = None
    if (final_dir / "div(phi)").exists():
        div_mass_mean = float(np.mean(np.abs(read_scalar(final_dir / "div(phi)", n))))
    if (final_dir / "div(U)").exists():
        div_volume_mean = float(np.mean(np.abs(read_scalar(final_dir / "div(U)", n))))
    up = float(speed.max())
    if up > 0:
        if div_mass_mean is not None:
            epsilon_m = L * div_mass_mean / (rho0 * up)
        if div_volume_mean is not None:
            epsilon_v = L * div_volume_mean / up

    result_dir = ROOT / "results/routeA/cases" / case_id
    figure_dir = ROOT / "results/routeA/figures"
    result_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    with (result_dir / "local_nusselt.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["Z", "Nu_hot_path1", "Nu_cold_path1", "Y_legacy_alias"])
        writer.writerows(zip(y / L, nu_hot_local, nu_cold_local, y / L))
    with (result_dir / "section_nusselt.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["X", "Nu_bar_X", "definition"])
        writer.writerows(zip(paper_nu["X"], paper_nu["sections"],
                             ["U*theta-dtheta/dX"] * (nx + 1)))
    with (result_dir / "centreline_4097.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["index", "coordinate", "U_at_X0.5", "W_at_Z0.5", "V_at_Y0.5_legacy_alias"])
        writer.writerows(zip(range(line_n), yq / L, uq, vq, vq))

    conv_path = result_dir / "convergence.csv"
    with conv_path.open("w", newline="") as stream:
        fields = ["case_id", "iteration", "Ux_initial", "Uy_initial", "e_initial", "p_rgh_initial",
                  "Nu_bar_0", "Nu_bar_0_path1_snapshot", "Nu_bar_half", "Nu_bar_cavity", "Nu_bar_1",
                  "Nu_hot_path2", "Nu_cold_path2", "heat_imbalance", "Umax_monitor", "Wmax_monitor", "Vmax_monitor_legacy_alias"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        sample_map = {int(round(t)): sample_extrema(case, t, alpha0, L) for t in sample_times}
        for iteration in sorted(residuals):
            row = {"case_id": case_id, "iteration": iteration}
            row.update({key: residuals[iteration].get(key, "") for key in fields if key.endswith("_initial")})
            if float(iteration) in wall:
                h = wall[float(iteration)]
                nh = h["hotWall"]["Q"] / (k * dT * W)
                nc = -h["coldWall"]["Q"] / (k * dT * W)
                row.update(Nu_bar_0=nh, Nu_hot_path2=nh, Nu_cold_path2=nc,
                           heat_imbalance=abs(nh-nc)/((nh+nc)/2))
            if iteration in paper_window:
                pn = paper_window[iteration]
                row.update(Nu_bar_0_path1_snapshot=pn["Nu_bar_0"], Nu_bar_half=pn["Nu_bar_half"],
                           Nu_bar_cavity=pn["Nu_bar_cavity"], Nu_bar_1=pn["Nu_bar_1"])
            if iteration in sample_map:
                row["Umax_monitor"], row["Wmax_monitor"] = sample_map[iteration]
                row["Vmax_monitor_legacy_alias"] = row["Wmax_monitor"]
            writer.writerow(row)

    result = {
        "case_id": case_id, "final_iteration": end_iter,
        "Nu_bar_0": paper_nu["Nu_bar_0"], "Nu_bar_half": paper_nu["Nu_bar_half"],
        "Nu_bar_cavity": paper_nu["Nu_bar_cavity"], "Nu_bar_1": paper_nu["Nu_bar_1"],
        "Nu_bar_cavity_from_section_trapezoid": paper_nu["Nu_bar_cavity_from_section_trapezoid"],
        "Nu_bar_cavity_discrete_method_difference": paper_nu["Nu_bar_cavity"] - paper_nu["Nu_bar_cavity_from_section_trapezoid"],
        "Nu_bar_cavity_discrete_method_difference_legacy_semantics": "signed primary minus section-trapezoid; use the explicit absolute/relative fields for diagnostics",
        "Nu_bar_cavity_method_absolute_difference": abs(paper_nu["Nu_bar_cavity"] - paper_nu["Nu_bar_cavity_from_section_trapezoid"]),
        "Nu_bar_cavity_method_relative_difference": abs(paper_nu["Nu_bar_cavity"] - paper_nu["Nu_bar_cavity_from_section_trapezoid"]) / abs(paper_nu["Nu_bar_cavity"]),
        "Nu_bar_cavity_method_relative_difference_denominator": "abs(Nu_bar_cavity), where Nu_bar_cavity is the primary cell-volume quadrature",
        "Nu_bar_0_path1": paper_nu["Nu_bar_0"], "Nu_bar_1_path1": paper_nu["Nu_bar_1"],
        "Nu_bar_0_path2": nu_hot_a2, "Nu_bar_1_path2": nu_cold_a2,
        "Nu_hot_path1": nu_hot_a1, "Nu_cold_path1": nu_cold_a1,
        "Nu_hot_path2": nu_hot_a2, "Nu_cold_path2": nu_cold_a2,
        "Nu_path_relative_difference": path_relative_difference,
        "wallHeatFlux_Q_W": {"hotWall": q_hot, "coldWall": q_cold},
        "wall_area_m2": L * W,
        "wallHeatFlux_sign": "wallHeatFlux=-q; hot Q positive, cold Q negative; cold Nu uses -Q",
        "radiation_contribution": "absent (no radiation field/model selected)",
        "heat_imbalance": heat_imbalance,
        "section_Nu_max_relative_deviation_from_half": float(
            np.max(np.abs(paper_nu["sections"] - paper_nu["Nu_bar_half"]))
            / abs(paper_nu["Nu_bar_half"])
        ),
        "paper_Nu_definition": "Q=U*theta-dtheta/dX; Route A diagnostic only because its governing equations differ from the paper",
        "paper_reference_file": str(PAPER_REFERENCE.relative_to(ROOT)),
        "paper_Nu_discretization": "walls: orthogonal patch face gradient; internal vertical faces: linear U/theta interpolation plus two-cell orthogonal temperature gradient and face-area integration; cavity: cell-volume U*theta quadrature plus exact imposed-wall conductive integral 1",
        "Nu_hot_local_max": nu_maximum["value"], "Nu_hot_local_max_Z": nu_maximum["Z"],
        "Nu_hot_local_min": nu_minimum["value"], "Nu_hot_local_min_Z": nu_minimum["Z"],
        "Nu_max": nu_maximum["value"], "Z_at_Nu_max": nu_maximum["Z"],
        "Nu_min": nu_minimum["value"], "Z_at_Nu_min": nu_minimum["Z"],
        "Nu_hot_local_raw_max": nu_maximum["raw_value"], "Nu_hot_local_raw_max_Z": nu_maximum["raw_Z"],
        "Nu_hot_local_raw_min": nu_minimum["raw_value"], "Nu_hot_local_raw_min_Z": nu_minimum["raw_Z"],
        "Nu_hot_local_extrema_method": "fixed local quartic through five adjacent face-centre values; derivative root inside the local interval; endpoint evaluated by the same quartic only when the five-point window touches it",
        "paper_comparison_like_for_like": paper_comparison,
        "Umax": umax, "Umax_Z": umax_loc, "Wmax": vmax, "Wmax_X": vmax_loc,
        "Umax_Y": umax_loc, "Vmax": vmax, "Vmax_X": vmax_loc,
        "Umin": float(uq[uimin]), "Umin_Y": float(yq[uimin] / L),
        "Wmin": float(vq[vimin]), "Wmin_X": float(xq[vimin] / L),
        "Vmin": float(vq[vimin]), "Vmin_X": float(xq[vimin] / L),
        "centreline_method": "linear interpolation to exact centreline from the two bracketing cell-centre lines, then 4097 uniform points including no-slip endpoints",
        "max_dimensionless_velocity": max_dim_speed,
        "max_theta_analytic_error": theta_error,
        "temperature_range_K": [float(T.min()), float(T.max())],
        "density_range_kg_m3": [float(rho.min()), float(rho.max())],
        "final_initial_residuals": final_initial_residuals,
        "Rwin": rwin,
        "Gate_D_monitor_evaluation": gate_d_monitors,
        "divergence": {
            "mean_abs_mass_divergence_kg_m3_s": div_mass_mean,
            "mean_abs_volume_divergence_1_s": div_volume_mean,
            "epsilon_m": epsilon_m, "epsilon_v": epsilon_v,
            "definitions": "mass: volume mean |fvc::div(phi)| using solver mass flux; volume: volume mean |fvc::div(U)| using Gauss linear; normalized per acceptance_criteria 9.2",
        },
        "normal_exit": bool(re.search(r"^End\s*$", solver_log.read_text(), re.M)),
        "fatal_or_nan": any(classify_health_lines(solver_log.read_text().splitlines()).values()),
    }
    (result_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")

    plt.figure(figsize=(6.2, 4.2))
    if case_id == "A-COND":
        plt.plot(x / L, theta[ny // 2], "o", ms=2.5, label="Route A cell centres")
        plt.plot([0, 1], [1, 0], "k--", label="analytic $1-X$")
        plt.xlabel("X"); plt.ylabel(r"$\theta$"); plt.legend(); plt.grid(True, alpha=.3)
        plt.tight_layout(); plt.savefig(figure_dir / "A-COND_theta_analytic.png", dpi=180); plt.close()
        plt.figure(figsize=(6.2, 4.2))
        plt.plot(wall_times, nu_series)
        plt.xlabel("steady iteration"); plt.ylabel(r"mean $Nu$"); plt.grid(True, alpha=.3)
        plt.tight_layout(); plt.savefig(figure_dir / "A-COND_Nu_final_window.png", dpi=180); plt.close()
    else:
        plt.contourf(X / L, Y / L, theta, levels=30, cmap="coolwarm")
        plt.colorbar(label=r"$\theta$"); plt.xlabel("X"); plt.ylabel("Z"); plt.axis("equal")
        plt.tight_layout(); plt.savefig(figure_dir / "A-SMOKE_theta.png", dpi=180); plt.close()
        plt.figure(figsize=(6.2, 5.2))
        plt.streamplot(x / L, y / L, U[:, :, 0], U[:, :, 1], density=1.3, color=speed, cmap="viridis")
        plt.colorbar(label="|U| [m/s]"); plt.xlabel("X"); plt.ylabel("Z"); plt.axis("equal")
        plt.tight_layout(); plt.savefig(figure_dir / "A-SMOKE_velocity_streamlines.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.plot(yq / L, uq, label=r"$U(X=0.5,Z)$")
    plt.plot(xq / L, vq, label=r"$W(X,Z=0.5)$")
    plt.xlabel("dimensionless centreline coordinate"); plt.ylabel("dimensionless velocity")
    plt.legend(); plt.grid(True, alpha=.3); plt.tight_layout()
    plt.savefig(figure_dir / f"{case_id}_centrelines.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.plot(paper_nu["X"], paper_nu["sections"], label=r"$\overline{Nu}_X$")
    plt.axhline(paper_nu["Nu_bar_cavity"], color="k", ls="--", label=r"$\overline{Nu}$ (cell volume)")
    plt.xlabel("X"); plt.ylabel("paper-definition mean Nu"); plt.legend(); plt.grid(True, alpha=.3)
    plt.tight_layout(); plt.savefig(figure_dir / f"{case_id}_section_Nu.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.plot(y / L, nu_hot_local, label="hot wall")
    plt.plot(y / L, nu_cold_local, label="cold wall")
    plt.xlabel("Z"); plt.ylabel("local Nu, path A1"); plt.legend(); plt.grid(True, alpha=.3)
    plt.tight_layout(); plt.savefig(figure_dir / f"{case_id}_local_Nu.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.imshow(speed * L / alpha0, origin="lower", extent=(0, 1, 0, 1), aspect="equal", cmap="magma")
    plt.colorbar(label="dimensionless |U|"); plt.xlabel("X"); plt.ylabel("Z")
    plt.tight_layout(); plt.savefig(figure_dir / f"{case_id}_velocity_magnitude.png", dpi=180); plt.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
