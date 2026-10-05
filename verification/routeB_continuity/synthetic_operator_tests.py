#!/usr/bin/env python3
"""Stages A/B: known fluxes, actual parser and unmodified production function."""
import json
from pathlib import Path

import numpy as np

from common import RESULTS, WORK, incidence, metrics, parser, production_continuity_metrics, write_csv


def topology(n):
    cell = np.arange(n*n).reshape(n, n)
    owner = np.r_[cell[:, :-1].ravel(), cell[:-1, :].ravel()]
    neighbour = np.r_[cell[:, 1:].ravel(), cell[1:, :].ravel()]
    boundary_owner = [cell[:, 0], cell[:, -1], cell[0, :], cell[-1, :], cell.ravel(), cell.ravel()]
    return np.r_[owner, *boundary_owner], neighbour


def write_labels(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('FoamFile { version 2.0; format ascii; class labelList; object '+path.name+'; }\n'
                    +str(len(values))+'\n(\n'+'\n'.join(map(str, values))+'\n)\n')


def write_flux(path, internal, boundary, precision):
    def field(values):
        return 'nonuniform List<scalar> '+str(len(values))+'\n(\n'+'\n'.join(format(float(v), f'.{precision}g') for v in values)+'\n);'
    text = 'FoamFile { version 2.0; format ascii; class surfaceScalarField; object phi; }\n'
    text += 'dimensions [0 3 -1 0 0 0 0];\ninternalField '+field(internal)+'\nboundaryField\n{\n'
    for patch, values in zip(('hotWall', 'coldWall', 'bottomWall', 'topWall'), boundary):
        text += patch+' { type calculated; value '+field(values)+' }\n'
    for patch in ('front', 'back'):
        text += patch+' { type empty; value nonuniform List<scalar> 0(); }\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text+'}\n')


def roundoff_bound(owner, neighbour, internal, boundary):
    # Conservative 32-operation bound covers six-face accumulation and reductions.
    absolute_sum = incidence(owner, neighbour, np.abs(internal), [np.abs(b) for b in boundary])
    # Internal neighbour signs must be positive for the magnitude sum.
    np.add.at(absolute_sum, neighbour, 2*np.abs(internal))
    u = np.finfo(float).eps / 2
    return (32*u/(1-32*u))*absolute_sum


def run():
    operator_rows, serialization_rows, local_rows = [], [], []
    for n in (20, 40, 80, 160):
        owner, neighbour = topology(n)
        synthetic_U = np.zeros((n,n,3)); synthetic_U[:,:,0] = 1.0
        up = float(np.max(np.linalg.norm(synthetic_U, axis=2)))
        x = np.arange(n+1)/n
        X, Y = np.meshgrid(x, x)
        psi = np.sin(np.pi*X)**2*np.sin(2*np.pi*Y)**2
        psi[0, :] = psi[-1, :] = psi[:, 0] = psi[:, -1] = 0
        fx = psi[1:, :] - psi[:-1, :]
        fy = -(psi[:, 1:] - psi[:, :-1])
        exact_phi = np.r_[fx[:, 1:-1].ravel(), fy[1:-1, :].ravel()]
        zero_boundary = [np.zeros(n) for _ in range(4)]
        tests = [('A1_exact_flux', exact_phi, zero_boundary, np.zeros(n*n), 0.0)]
        for delta in (1e-6, 1e-8, 1e-9):
            internal = np.zeros_like(exact_phi)
            face = (n//2)*(n-1)+n//2
            internal[face] = delta
            expected = np.zeros(n*n)
            expected[owner[face]] = delta
            expected[neighbour[face]] = -delta
            tests.append(('A2_single_face', internal, zero_boundary, expected, delta))
        boundary = [b.copy() for b in zero_boundary]
        boundary[0][n//2] = 1e-8
        expected = np.zeros(n*n)
        expected[owner[len(neighbour)+n//2]] = 1e-8
        tests.append(('A3_boundary_leak', np.zeros_like(exact_phi), boundary, expected, 1e-8))
        for test, internal, boundary, expected, delta in tests:
            case = WORK / 'synthetic' / f'{n}_{test}_{delta:g}'
            write_labels(case/'constant/polyMesh/owner', owner)
            write_labels(case/'constant/polyMesh/neighbour', neighbour)
            q_memory = incidence(owner, neighbour, internal, boundary)
            memory = metrics(q_memory, (1/n)*(1/n), up, 1.0)
            for precision in (16, 6):
                folder = case / str(precision)
                write_flux(folder/'phi', internal, boundary, precision)
                read_internal = parser.read_scalar(folder/'phi', len(neighbour))
                read_boundary = [parser.read_boundary_scalar(folder/'phi', p, n) for p in ('hotWall','coldWall','bottomWall','topWall')]
                q_read = incidence(owner, neighbour, read_internal, read_boundary)
                observed = metrics(q_read, (1/n)*(1/n), up, 1.0)
                production_mean, _ = production_continuity_metrics(case, folder, synthetic_U, n, n, 1.0, 1.0)
                assert production_mean == observed['mean_abs_div_phi'], 'Production incidence disagrees; STOP'
                assert np.array_equal(read_internal, np.array([float(format(float(v),f'.{precision}g')) for v in internal])), 'Parser effect beyond ASCII rounding; STOP'
                quant = np.abs(read_internal-internal)
                quant_boundary = [np.abs(a-b) for a,b in zip(read_boundary,boundary)]
                io_bound = incidence(owner, neighbour, quant, quant_boundary)
                np.add.at(io_bound, neighbour, 2*quant)
                budget = roundoff_bound(owner, neighbour, read_internal, read_boundary) + io_bound
                if not np.all(np.abs(q_read-expected) <= budget + np.finfo(float).tiny):
                    raise AssertionError(f'{test} known cell imbalance disagrees at n={n}; STOP')
                serialization_rows.append({'stage':'synthetic','n':n,'test':test,'delta_phi':delta,'write_precision':precision,
                    **observed, 'mean_metric_error':observed['mean_abs_div_phi']-memory['mean_abs_div_phi'],
                    'max_metric_error':observed['max_abs_div_phi']-memory['max_abs_div_phi'],
                    'P99_metric_error':observed['P99_abs_div_phi']-memory['P99_abs_div_phi'],
                    'global_signed_error':observed['signed_volume_mean_div_phi']-memory['signed_volume_mean_div_phi'],
                    'max_abs_face_write_read_error':float(np.max(quant)), 'production_mean_match':True,
                    **{'memory_'+k:v for k,v in memory.items()}})
                if precision == 16:
                    analytic = metrics(expected, (1/n)*(1/n), up, 1.0)
                    row={'n':n,'test':test,'delta_phi':delta,'mode':'ASCII16_actual_parser',**observed,
                         'net_boundary_flux':float(sum(np.sum(b) for b in read_boundary)),
                         'expected_sum_abs_q':float(np.sum(abs(expected))),
                         'max_cell_x':(observed['max_cell_id']%n+.5)/n,
                         'max_cell_y':(observed['max_cell_id']//n+.5)/n, 'max_cell_z':.5,
                         'max_cell_q_error':float(np.max(abs(q_read-expected))),
                         'cell_q_error_budget_max':float(np.max(budget)), 'status':'PASS'}
                    for key in ('mean_abs_div_phi','max_abs_div_phi','signed_volume_mean_div_phi','sum_abs_q'):
                        row[key+'_absolute_error']=abs(observed[key]-analytic[key])
                        row[key+'_relative_error']=abs(observed[key]-analytic[key])/abs(analytic[key]) if analytic[key] else None
                    operator_rows.append(row)
                    local_rows.append({'source':'synthetic','case_id':test,'iteration':0,'n':n,'delta_phi':delta,**observed,'net_boundary_flux':row['net_boundary_flux'],
                        'max_cell_x':row['max_cell_x'],'max_cell_y':row['max_cell_y'],'max_cell_z':row['max_cell_z']})
                    if test == 'A2_single_face' and delta == 1e-8:
                        local_rows[-1]['case_id']='A4_local_hiding'
    write_csv('operator_verification.csv', operator_rows)
    write_csv('serialization_test.csv', serialization_rows)
    write_csv('local_metrics.csv', local_rows)
    summary={'status':'PASS','grids':[20,40,80,160],'test_rows':len(operator_rows),
             'actual_production_parser_used':True,'actual_production_continuity_function_used':True,
             'percentile_definition':'numpy linear empirical percentile; equal-volume mesh',
             'known_value_pass_budget':'per-cell 32-operation unit-roundoff model plus measured ASCII rounding propagated through incidence; not acceptance tolerance',
             'exact_zero_flux_test':'PASS','single_face_test':'PASS','boundary_leak_test':'PASS',
             'up_definition':'Up=max|U|=1 m/s from prescribed uniform cell U=(1,0,0), L=1 m; U is normalization input, not a solver solution'
             ,'harness_rounding_correction':'Initial exact-equality assertion used 1/n^2 instead of production (1/n)*(1/n); at n=20 volume differed by 4.34e-19. Corrected harness order, no production change or failed analytic test.'}
    (RESULTS/'operator_stage_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
    return summary


if __name__ == '__main__':
    run()
