#!/usr/bin/env python3
"""Compute fixed Route A diagnostics and figures from an executed case."""

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

from foam_fields import latest_time, read_scalar, read_vector

ROOT = Path(__file__).resolve().parents[2]


def read_wall_heat(path: Path) -> dict[float, dict[str, dict[str, float]]]:
    data: dict[float, dict[str, dict[str, float]]] = {}
    with path.open() as stream:
        for line in stream:
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split()
            t = float(cols[0])
            data.setdefault(t, {})[cols[1]] = {
                "min": float(cols[2]), "max": float(cols[3]),
                "Q": float(cols[4]), "q": float(cols[5]),
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
    current = None
    rows: dict[int, dict[str, float]] = {}
    time_re = re.compile(r"^Time = ([0-9.eE+-]+)s")
    solve_re = re.compile(r"Solving for ([^,]+), Initial residual = ([^,]+), Final residual = ([^,]+)")
    for line in log.read_text().splitlines():
        m = time_re.match(line)
        if m:
            current = int(round(float(m.group(1))))
            rows.setdefault(current, {})
            continue
        m = solve_re.search(line)
        if m and current is not None:
            field = m.group(1)
            initial = float(m.group(2))
            final = float(m.group(3))
            rows[current][f"{field}_initial"] = max(initial, rows[current].get(f"{field}_initial", 0.0))
            rows[current][f"{field}_final"] = max(final, rows[current].get(f"{field}_final", 0.0))
    return rows


def relative_range(values: np.ndarray, scale: float) -> float:
    return float((values.max() - values.min()) / max(abs(values.mean()), scale))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    args = parser.parse_args()
    case = Path(args.case).resolve()
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

    # Path A1: direct orthogonal boundary face gradient from T and geometry.
    nu_hot_local = L * (th - T[:, 0]) / (0.5 * dx) / dT
    nu_cold_local = L * (T[:, -1] - tc) / (0.5 * dx) / dT
    nu_hot_a1 = float(nu_hot_local.mean())
    nu_cold_a1 = float(nu_cold_local.mean())

    wall_file = case / "postProcessing/wallHeatFluxMonitor/0/wallHeatFlux.dat"
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

    residuals = parse_residuals(case / "log.foamRun")
    end_iter = int(round(final_t))
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
        "Umax": relative_range(us, 1.0),
        "Vmax": relative_range(vs, 1.0),
        "Nu_samples": int(nu_series.size),
        "velocity_samples": int(us.size),
        "scales": {"Nu": 1.0, "Umax": 1.0, "Vmax": 1.0},
        "heat_imbalance_start": float(heat_series[0]),
        "heat_imbalance_end": float(heat_series[-1]),
    }

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
        writer = csv.writer(stream)
        writer.writerow(["Y", "Nu_hot_path1", "Nu_cold_path1"])
        writer.writerows(zip(y / L, nu_hot_local, nu_cold_local))
    with (result_dir / "centreline_4097.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["index", "coordinate", "U_at_X0.5", "V_at_Y0.5"])
        writer.writerows(zip(range(line_n), yq / L, uq, vq))

    conv_path = result_dir / "convergence.csv"
    with conv_path.open("w", newline="") as stream:
        fields = ["case_id", "iteration", "Ux_initial", "Uy_initial", "e_initial", "p_rgh_initial",
                  "Nu_hot_path2", "Nu_cold_path2", "heat_imbalance", "Umax_monitor", "Vmax_monitor"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        sample_map = {int(round(t)): sample_extrema(case, t, alpha0, L) for t in sample_times}
        for iteration in sorted(residuals):
            row = {"case_id": case_id, "iteration": iteration}
            row.update({key: residuals[iteration].get(key, "") for key in fields if key.endswith("_initial")})
            if float(iteration) in wall:
                h = wall[float(iteration)]
                nh = h["hotWall"]["Q"] / (k * dT * W)
                nc = -h["coldWall"]["Q"] / (k * dT * W)
                row.update(Nu_hot_path2=nh, Nu_cold_path2=nc,
                           heat_imbalance=abs(nh-nc)/((nh+nc)/2))
            if iteration in sample_map:
                row["Umax_monitor"], row["Vmax_monitor"] = sample_map[iteration]
            writer.writerow(row)

    result = {
        "case_id": case_id, "final_iteration": end_iter,
        "Nu_hot_path1": nu_hot_a1, "Nu_cold_path1": nu_cold_a1,
        "Nu_hot_path2": nu_hot_a2, "Nu_cold_path2": nu_cold_a2,
        "Nu_path_relative_difference": path_relative_difference,
        "wallHeatFlux_Q_W": {"hotWall": q_hot, "coldWall": q_cold},
        "wall_area_m2": L * W,
        "wallHeatFlux_sign": "wallHeatFlux=-q; hot Q positive, cold Q negative; cold Nu uses -Q",
        "radiation_contribution": "absent (no radiation field/model selected)",
        "heat_imbalance": heat_imbalance,
        "Umax": umax, "Umax_Y": umax_loc, "Vmax": vmax, "Vmax_X": vmax_loc,
        "Umin": float(uq[uimin]), "Umin_Y": float(yq[uimin] / L),
        "Vmin": float(vq[vimin]), "Vmin_X": float(xq[vimin] / L),
        "centreline_method": "linear interpolation to exact centreline from the two bracketing cell-centre lines, then 4097 uniform points including no-slip endpoints",
        "max_dimensionless_velocity": max_dim_speed,
        "max_theta_analytic_error": theta_error,
        "temperature_range_K": [float(T.min()), float(T.max())],
        "density_range_kg_m3": [float(rho.min()), float(rho.max())],
        "final_initial_residuals": final_initial_residuals,
        "Rwin": rwin,
        "divergence": {
            "mean_abs_mass_divergence_kg_m3_s": div_mass_mean,
            "mean_abs_volume_divergence_1_s": div_volume_mean,
            "epsilon_m": epsilon_m, "epsilon_v": epsilon_v,
            "definitions": "mass: volume mean |fvc::div(phi)| using solver mass flux; volume: volume mean |fvc::div(U)| using Gauss linear; normalized per acceptance_criteria 9.2",
        },
        "normal_exit": "End" in (case / "log.foamRun").read_text(),
        "fatal_or_nan": bool(re.search(r"FOAM FATAL (?:ERROR|IO ERROR)|Floating point exception \(core dumped\)|\bnan\b|\binf\b", (case / "log.foamRun").read_text(), re.I)),
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
        plt.colorbar(label=r"$\theta$"); plt.xlabel("X"); plt.ylabel("Y"); plt.axis("equal")
        plt.tight_layout(); plt.savefig(figure_dir / "A-SMOKE_theta.png", dpi=180); plt.close()
        plt.figure(figsize=(6.2, 5.2))
        plt.streamplot(x / L, y / L, U[:, :, 0], U[:, :, 1], density=1.3, color=speed, cmap="viridis")
        plt.colorbar(label="|U| [m/s]"); plt.xlabel("X"); plt.ylabel("Y"); plt.axis("equal")
        plt.tight_layout(); plt.savefig(figure_dir / "A-SMOKE_velocity_streamlines.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.plot(yq / L, uq, label=r"$U(X=0.5,Y)$")
    plt.plot(xq / L, vq, label=r"$V(X,Y=0.5)$")
    plt.xlabel("dimensionless centreline coordinate"); plt.ylabel("dimensionless velocity")
    plt.legend(); plt.grid(True, alpha=.3); plt.tight_layout()
    plt.savefig(figure_dir / f"{case_id}_centrelines.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.plot(y / L, nu_hot_local, label="hot wall")
    plt.plot(y / L, nu_cold_local, label="cold wall")
    plt.xlabel("Y"); plt.ylabel("local Nu, path A1"); plt.legend(); plt.grid(True, alpha=.3)
    plt.tight_layout(); plt.savefig(figure_dir / f"{case_id}_local_Nu.png", dpi=180); plt.close()
    plt.figure(figsize=(6.2, 4.2))
    plt.imshow(speed * L / alpha0, origin="lower", extent=(0, 1, 0, 1), aspect="equal", cmap="magma")
    plt.colorbar(label="dimensionless |U|"); plt.xlabel("X"); plt.ylabel("Y")
    plt.tight_layout(); plt.savefig(figure_dir / f"{case_id}_velocity_magnitude.png", dpi=180); plt.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
