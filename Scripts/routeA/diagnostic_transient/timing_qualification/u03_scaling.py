"""Prepared bounded U03 harness. Default is dry-run; never launches CFD."""
import argparse
import importlib.util
import json
import math
import os
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

from protocol import PLAN, ROOT, gate, load, sha, validate


def inputs(n, contract):
    if n not in (4, 100, 200, 400, 800, 1600, 3200, 6400):
        raise ValueError('STOP_UNREGISTERED_HISTORY_SIZE')
    times = [i * .6 / (n - 1) for i in range(n)]
    names = ('Nu_bar_cavity', 'Umax', 'Wmax', 'rho_min', 'rho_max', 'rho_mean', 'total_mass', 'energy_storage')
    histories = {name: [1.] * n for name in names}
    scales = contract['steady_arrival']['mass_energy_rho_arrival_policy']['scales']
    return times, histories, scales


def worker(n, plan_path):
    # Only the unchanged Python estimator is imported. No OpenFOAM library,
    # native fixture, launcher, field file or physical time advancement.
    plan = load(plan_path)
    path = ROOT / 'Scripts/routeA/diagnostic_transient/v1_1/contract_policy.py'
    if sha(path) != plan['authority_sha256'][str(path.relative_to(ROOT))]:
        raise ValueError('STOP_U03_SOURCE_HASH')
    resource.setrlimit(resource.RLIMIT_AS, (8 * 2**30, 8 * 2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    spec = importlib.util.spec_from_file_location('frozen_U03_policy', path)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    contract = load(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json')
    times, histories, scales = inputs(n, contract)
    begin = time.perf_counter()
    ok, windows = policy.arrival_candidate(times, histories, .5, scales, True)
    elapsed = time.perf_counter() - begin
    if not math.isfinite(elapsed) or len(windows) != 3:
        raise ValueError('STOP_NONFINITE_OR_INVALID_U03_FIXTURE')
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {'classification': 'RESOURCE_QUALIFICATION_FIXTURE_NOT_CFD_RESULT', 'N': n,
            'kernel_wall_seconds': elapsed, 'CPU_user_seconds': usage.ru_utime,
            'CPU_system_seconds': usage.ru_stime, 'process_peak_RSS_KiB': usage.ru_maxrss,
            'fixture_stationarity_result': ok, 'windows': 3,
            'scientific_arrival_claim_allowed': False}


def run(receipt_path, output):
    plan = load(PLAN)
    errors = validate(plan)
    if errors:
        raise ValueError('STOP_PLAN_INVALID:' + repr(errors))
    gate(plan, 'Q2', load(receipt_path), sha(PLAN))
    base = ROOT / 'results/routeA/diagnostic_transient/timing_qualification'
    output = Path(output).resolve()
    if output.parent != base.resolve() or output.exists():
        raise ValueError('STOP_OUTPUT_NAMESPACE_OR_EXISTING_OUTPUT')
    # Future authorized operation only; this preparation does not call run().
    output.mkdir(parents=True, exist_ok=False)
    end = time.monotonic() + 120
    rows = []
    for n in plan['Q2_U03']['node_counts']:
        for trial in range(3):
            remaining = end - time.monotonic()
            if remaining <= 0:
                status = 'STOP_U03_SUITE_LIMIT'
                write_result(output, rows, status)
                return 1
            try:
                proc = subprocess.run([sys.executable, '-B', __file__, '--worker', str(n)],
                                      capture_output=True, text=True,
                                      timeout=min(15, remaining),
                                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                                               ROUTE_A_TIMING_Q2_RECEIPT=str(Path(receipt_path).resolve())))
            except subprocess.TimeoutExpired:
                rows.append({'N': n, 'trial': trial, 'censored': True,
                             'elapsed_lower_bound_seconds': min(15, remaining)})
                write_result(output, rows, 'STOP_U03_BENCHMARK_LIMIT')
                return 1
            if proc.returncode:
                write_result(output, rows, 'STOP_U03_PROCESS_FAILURE')
                return 1
            row = json.loads(proc.stdout)
            row.update(trial=trial, load_average=os.getloadavg())
            rows.append(row)
            write_result(output, rows, 'IN_PROGRESS')
    write_result(output, rows, 'MEASURED_NOT_PRODUCTION_AUTHORIZED')
    return 0


def write_result(output, rows, status):
    # At most 21 tiny rows; no large log or data deletion.
    (output / 'u03_results.json').write_text(json.dumps({'status': status, 'rows': rows,
                                                       'execution_authorized': False}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=int, choices=(100, 200, 400, 800, 1600, 3200, 6400), help=argparse.SUPPRESS)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.worker is not None:
        # An internal worker must also be authorized before any timed kernel.
        receipt_env = os.environ.get('ROUTE_A_TIMING_Q2_RECEIPT')
        if not receipt_env:
            raise ValueError('STOP_WORKER_AUTHORIZATION_REQUIRED')
        gate(load(PLAN), 'Q2', load(receipt_env), sha(PLAN))
        print(json.dumps(worker(args.worker, PLAN)))
        return 0
    if args.receipt is None:
        print(json.dumps({'mode': 'DRY_RUN', 'stage': 'Q2_U03', 'node_counts': [100, 200, 400, 800, 1600, 3200, 6400],
                          'repeats': 3, 'single_trial_wall_seconds': 15, 'suite_wall_seconds': 120,
                          'execution_authorized': False, 'current_Q0_status': 'REQUIRES_FIX'}, indent=2))
        return 0
    if args.output is None:
        raise ValueError('STOP_OUTPUT_REQUIRED')
    return run(args.receipt, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
