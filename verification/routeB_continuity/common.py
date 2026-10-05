"""Independent verification helpers; production modules are read-only."""
import ast
import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = ROOT / 'results/routeB/caseC_continuity_verification'
WORK = HERE / 'work'
L = 0.01
WIDTH = 0.001

spec = importlib.util.spec_from_file_location('verification_production_parser', ROOT / 'Scripts/routeB/foam_fields.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)

# Compile only the existing function, without executing analyzer main/reference code.
tree = ast.parse((ROOT / 'Scripts/routeB/analyze_case.py').read_text())
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'continuity_metrics')
namespace = {'np': np, 'Path': Path, 'read_label_list': parser.read_label_list,
             'read_scalar': parser.read_scalar, 'read_boundary_scalar': parser.read_boundary_scalar}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(ROOT / 'Scripts/routeB/analyze_case.py'), 'exec'), namespace)
production_continuity_metrics = namespace['continuity_metrics']


def write_csv(name, rows):
    RESULTS.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (RESULTS / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def incidence(owner, neighbour, internal, boundary):
    q = np.zeros(int(owner.max()) + 1)
    np.add.at(q, owner[:len(neighbour)], internal)
    np.add.at(q, neighbour, -internal)
    offset = len(neighbour)
    for values in boundary:
        np.add.at(q, owner[offset:offset + len(values)], values)
        offset += len(values)
    return q


def metrics(q, volume, up, length):
    d = q / volume
    absolute = np.abs(d)
    i = int(np.argmax(absolute))
    return {'mean_abs_div_phi': float(np.mean(absolute)),
            'epsilon_phi_mean': float(length / up * np.mean(absolute)) if up else None,
            'max_abs_div_phi': float(absolute[i]),
            'epsilon_phi_max': float(length / up * absolute[i]) if up else None,
            'P95_abs_div_phi': float(np.percentile(absolute, 95, method='linear')),
            'P99_abs_div_phi': float(np.percentile(absolute, 99, method='linear')),
            'signed_volume_mean_div_phi': float(np.sum(q) / (len(q) * volume)),
            'sum_abs_q': float(np.sum(np.abs(q))), 'max_abs_q': float(np.max(np.abs(q))),
            'max_cell_id': i}


def read_case(case, iteration, n, length=L, width=WIDTH):
    mesh = case / 'constant/polyMesh'
    folder = case / str(iteration)
    owner = parser.read_label_list(mesh / 'owner')
    neighbour = parser.read_label_list(mesh / 'neighbour')
    phi = parser.read_scalar(folder / 'phi', len(neighbour))
    patches = [('hotWall', n), ('coldWall', n), ('bottomWall', n), ('topWall', n)]
    boundary = [parser.read_boundary_scalar(folder / 'phi', p, size) for p, size in patches]
    U = parser.read_vector(folder / 'U', n*n)
    up = float(np.max(np.linalg.norm(U, axis=1)))
    q = incidence(owner, neighbour, phi, boundary)
    result = metrics(q, length**2 * width / n**2, up, length)
    result['net_boundary_flux'] = float(sum(np.sum(b) for b in boundary))
    result['Up'] = up
    return result, U, phi, q, boundary
