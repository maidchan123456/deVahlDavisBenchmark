"""Read-only benchmark adapters; no analyzer main(), solver, or case writes."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / 'results/visualization_all_cases'
A_REVIEW = ROOT / 'results/routeA/attempts/attempt_007'
RAS = (1000, 10000, 100000, 1000000)
LEVELS = ('coarse', 'medium', 'fine')
QOIS = ('Nu_bar_cavity', 'Umax', 'Wmax')
COLORS = {'A': '#0072B2', 'B': '#D55E00', 'paper': '#222222', 'H': '#009E73'}
CHECKS = []
INPUTS = set()


def track(path):
    p = Path(path).resolve()
    INPUTS.add(p)
    return p


def read_json(path):
    return json.loads(track(path).read_text())


def read_csv(path):
    with track(path).open(newline='') as f:
        return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()})


def check(case_id, quantity, actual, expected, rtol=5e-12, atol=5e-12):
    import numpy as np
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    ok = a.shape == b.shape and bool(np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=False))
    error = float(np.max(np.abs(a-b))) if a.shape == b.shape and a.size else None
    CHECKS.append(dict(case_id=case_id, quantity=quantity, max_absolute_difference=error,
                       rtol=rtol, atol=atol, status='PASS' if ok else 'STOP'))
    if not ok:
        raise ValueError(f'STOP: {case_id} {quantity} differs from stored authority; max abs={error}')


def load_module(route, name):
    path = track(ROOT / f'Scripts/route{route}/{name}.py')
    spec = importlib.util.spec_from_file_location(f'visualization_route{route}_{name}', path)
    module = importlib.util.module_from_spec(spec)
    if name == 'analyze_case':
        previous = sys.modules.get('foam_fields')
        sys.modules['foam_fields'] = READERS[route]
        try:
            spec.loader.exec_module(module)
        finally:
            if previous is None:
                del sys.modules['foam_fields']
            else:
                sys.modules['foam_fields'] = previous
    else:
        spec.loader.exec_module(module)
    return module


READERS = {r: load_module(r, 'foam_fields') for r in ('A', 'B')}
ANALYZERS = {r: load_module(r, 'analyze_case') for r in ('A', 'B')}
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.size': 10, 'axes.titlesize': 10, 'axes.labelsize': 11,
    'legend.fontsize': 9, 'figure.dpi': 110, 'savefig.dpi': 300, 'pdf.fonttype': 42,
    'axes.spines.top': False, 'axes.spines.right': False})


@dataclass
class Case:
    case_id: str
    source_case_id: str
    route: str
    category: str
    case_path: Path
    metrics_path: Path
    manifest: dict
    metrics: dict
    status: dict
    theta: np.ndarray
    velocity: np.ndarray
    density: np.ndarray
    centre: dict
    local: dict
    section: dict
    summary: dict

    @property
    def ra(self): return int(round(self.manifest['Ra_target']))
    @property
    def n(self): return self.manifest['grid'][0]
    @property
    def x(self): return (np.arange(self.n)+0.5)/self.n
    @property
    def z(self): return (np.arange(self.manifest['grid'][1])+0.5)/self.manifest['grid'][1]
    @property
    def speed(self): return np.linalg.norm(self.velocity, axis=2)
    @property
    def accepted(self): return self.status.get('accepted', '').lower() in ('true', 'yes')
    @property
    def label(self):
        if self.category == 'auxiliary': return 'auxiliary (outside formal matrix)'
        return 'accepted' if self.accepted else 'diagnostic-only / unaccepted'
    @property
    def title(self): return f'{self.case_id}\nRoute {self.route} | Ra={self.ra:g} | {self.n}x{self.n}x1 | {self.label}'


def audit_status():
    a = read_csv(A_REVIEW/'RouteA_full_steady_matrix_summary.csv')
    g = read_csv(A_REVIEW/'RouteA_full_steady_matrix_gate_summary.csv')
    b = read_csv(ROOT/'results/routeB/routeB_master_matrix.csv')
    # Read all requested current authorities, preserving their classifications.
    for path in [A_REVIEW/'RouteA_full_steady_matrix_review.md',
                 ROOT/'results/routeB/routeB_final_verification_review.md']:
        track(path).read_text()
    read_csv(ROOT/'results/routeB/benchmark_summary.csv')
    read_csv(ROOT/'results/routeB/grid_convergence.csv')
    read_csv(A_REVIEW/'RouteA_full_steady_matrix_gate_F_detail.csv')
    assert len(a) == len(b) == 12
    assert all(r['computed']=='true' and r['accepted']=='true' and r['Gate_D']=='PASS' for r in a)
    assert all(r['Gate_E_diagnostic']=='PASS' and r['Gate_G']=='PASS' and r['Gate_F']=='FAIL' and r['needs_320']=='YES' for r in g)
    assert len(g) == 4
    assert all(r['computed']=='YES' and r['accepted']==('NO' if int(r['Ra'])==1000000 else 'YES')
               and r['Gate_D']==('FAIL' if int(r['Ra'])==1000000 else 'PASS') for r in b)
    assert next(r for r in b if r['case_id']=='B-Ra1e4-coarse')['source_case_id']=='B-SMOKE'
    for r in (a+b):
        rt = r['case_id'][0]
        ra = int(r.get('Ra_target', r.get('Ra')))
        level = r['case_id'].rsplit('-', 1)[1]
        expected_n = dict(zip(LEVELS, (40,80,160)))[level]
        grid = json.loads(r['grid']) if rt=='A' else [int(v) for v in r['grid'].split('x')]
        assert ra in RAS and grid == [expected_n,expected_n,1]
    assert {r['case_id'] for r in a+b} == {f'{rt}-Ra1e{e}-{l}' for rt in 'AB' for e in range(3,7) for l in LEVELS}
    return a, b, g


def mesh_centres(case, size):
    """Read existing ASCII hexahedral mesh; no mesh/postProcess executable."""
    import re
    mesh = case/'constant/polyMesh'
    txt = track(mesh/'points').read_text()
    match = re.search(r'\n\s*(\d+)\s*\(\s*((?:\([^()]*\)\s*)+)\)' ,txt,re.S)
    points = np.array([np.fromstring(v,sep=' ') for v in re.findall(r'\(([^()]*)\)',match[2])])
    assert len(points)==int(match[1])
    txt = track(mesh/'faces').read_text()
    faces = [np.fromstring(v,sep=' ',dtype=int) for v in re.findall(r'4\s*\(([^()]*)\)',txt)]
    owners = READERS['B'].read_label_list(track(mesh/'owner'))
    neighbours = READERS['B'].read_label_list(track(mesh/'neighbour'))
    assert len(faces)==len(owners), 'Only uniform quadrilateral hexahedral benchmark meshes are supported'
    fc = points[np.array(faces)].mean(axis=1)
    c = np.zeros((size,3)); counts = np.zeros(size)
    np.add.at(c,owners,fc); np.add.at(counts,owners,1)
    np.add.at(c,neighbours,fc[:len(neighbours)]); np.add.at(counts,neighbours,1)
    assert np.all(counts==6)
    return c/counts[:,None]


def load_case(case_id, source_id, route, category, case_path, metrics_path, status, authority=None):
    case_path, metrics_path = Path(case_path), Path(metrics_path)
    mf = read_json(case_path/'case_manifest.json')
    m = read_json(metrics_path)
    assert mf['case_id'] == source_id == m['case_id']
    nx, nz, depth = mf['grid']
    assert nx == nz and nx%2 == 0 and depth == 1
    end = int(m['final_iteration'])
    if 'final_iteration' in status:
        assert end == int(status['final_iteration'])
    final = case_path / str(end)
    latest, _ = READERS[route].latest_time(case_path)
    assert latest == end, f'STOP: {case_id}: latest field time differs from authoritative iteration'
    # Enforce coordinate mapping: OpenFOAM (x,y,z_thickness) -> paper (X,Z,depth).
    cp = final/'C'
    if not cp.exists(): cp = case_path/'0/C'
    c = READERS[route].read_vector(track(cp), nx*nz) if cp.exists() else mesh_centres(case_path, nx*nz)
    L, width = mf['geometry_m']['L'], mf['geometry_m']['W']
    xx, zz = np.meshgrid((np.arange(nx)+.5)*L/nx, (np.arange(nz)+.5)*L/nz)
    check(case_id, 'saved cell ordering X/Z', c[:,:2], np.column_stack((xx.ravel(),zz.ravel())), atol=5e-10)
    check(case_id, 'saved thickness coordinate', c[:,2], np.full(nx*nz,width/2), atol=5e-10)
    prop = mf['properties']; alpha = prop['alpha0_m2_s']; dt = prop['DeltaT_K']
    th, tc = prop['Th_K'], prop['Tc_K']
    T = READERS[route].read_scalar(track(final/'T'), nx*nz).reshape(nz,nx)
    U = READERS[route].read_vector(track(final/'U'), nx*nz).reshape(nz,nx,3)
    theta = (T-tc)/dt
    vel = U*L/alpha
    # Reuse the identical 4097-point extractor (Route A's inline formula is identical).
    centre = ANALYZERS['B'].centreline(U,nx,nz,L,alpha)
    check(case_id,'temperature_range_K',[T.min(),T.max()],m['temperature_range_K'])
    check(case_id,'max_dimensionless_velocity',np.linalg.norm(vel,axis=2).max(),m['max_dimensionless_velocity'])
    for key, ckey in [('Umax','Umax'),('Wmax','Vmax'),('Umax_Z','Umax_Y'),('Wmax_X','Vmax_X')]:
        check(case_id,key,centre[ckey],m[key])
    if route == 'A':
        section = ANALYZERS['A'].paper_nusselt(T,U,nx,nz,L,alpha,dt,th,tc)
        local = {'Nu_hot_primary':section['hot_local'],'Nu_cold_primary':section['cold_local']}
        rho0 = prop['rho0_kg_m3']
        rho = READERS['A'].read_scalar(track(final/'rho'), nx*nz).reshape(nz,nx)
        density = rho/rho0 - 1
        check(case_id,'density_range_kg_m3',[rho.min(),rho.max()],m['density_range_kg_m3'])
        check(case_id,'rho(T) EOS',rho,rho0*(1-prop['beta_1_K']*(T-prop['T0_K'])),atol=5e-12)
        density_stats = dict(rho_min=float(rho.min()),rho_max=float(rho.max()),max_abs_rho_over_rho0_minus_1=float(np.abs(density).max()))
    else:
        wall = ANALYZERS['B'].nusselt(case_path,final,T,nx,nz,L,dt,th,tc)
        for p in [case_path/'constant/polyMesh/owner',case_path/'constant/polyMesh/neighbour',final/'phi']: track(p)
        section = ANALYZERS['B'].paper_nusselt(case_path,final,T,U,nx,nz,L,width,alpha,dt,th,tc,wall)
        local = dict(Nu_hot_primary=wall['hot_b1_local'],Nu_cold_primary=wall['cold_b1_local'],
                     Nu_hot_B2_diagnostic=wall['hot_b2_local'],Nu_cold_B2_diagnostic=wall['cold_b2_local'])
        for k,v in [('Nu_hot_B1','hot_b1'),('Nu_cold_B1','cold_b1'),('Nu_hot_B2','hot_b2'),('Nu_cold_B2','cold_b2')]: check(case_id,k,wall[v],m[k])
        density = 1-prop['beta_1_K']*(T-prop['TRef_K'])
        check(case_id,'rhok_range',[density.min(),density.max()],m['rhok_range'])
        density_stats = dict(rhok_min=float(density.min()),rhok_max=float(density.max()),rhok_source='reconstructed from saved T; buoyancy/hydrostatic factor')
    for k in ('Nu_bar_0','Nu_bar_half','Nu_bar_cavity','Nu_bar_1','Nu_bar_cavity_from_section_trapezoid'):
        check(case_id,k,section[k],m[k])
    for kind in ('max','min'):
        ext_z = ((np.arange(nz)+.5)*(L/nz))/L if route=='A' else (np.arange(nz)+.5)/nz
        ext = ANALYZERS[route].local_quartic_extremum(ext_z,local['Nu_hot_primary'],kind)
        for suffix, ek in [('', 'value'),('_Z','Z')]: check(case_id,'Nu_hot_local_'+kind+suffix,ext[ek],m['Nu_hot_local_'+kind+suffix])
    # Cross-check stored drawing arrays, including the accepted-reuse source owner.
    for fname, calculated in [
        ('centreline_4097.csv', {'coordinate':centre['coordinate'],'U_at_X0.5':centre['U'],'W_at_Z0.5':centre['V']}),
        ('section_nusselt.csv', {'X':section['X'],'Nu_bar_X':section['sections']}),
        ('local_nusselt.csv', {'Z':(np.arange(nz)+.5)/nz})]:
        saved = read_csv(metrics_path.parent/fname)
        for k,values in calculated.items(): check(case_id,fname+':'+k,values,[float(r[k]) for r in saved])
        if fname == 'local_nusselt.csv':
            for k, values in local.items():
                old = {'Nu_hot_primary':'Nu_hot_path1' if route=='A' else 'Nu_hot_B1',
                       'Nu_cold_primary':'Nu_cold_path1' if route=='A' else 'Nu_cold_B1',
                       'Nu_hot_B2_diagnostic':'Nu_hot_B2','Nu_cold_B2_diagnostic':'Nu_cold_B2'}[k]
                check(case_id,fname+':'+old,values,[float(r[old]) for r in saved])
    if authority:
        for k in set(authority)&set(m):
            if k in (*QOIS,'Nu_bar_0','Nu_bar_half','Nu_bar_1','Nu_hot_local_max','Nu_hot_local_min','Umax_Z','Wmax_X'):
                check(case_id,'matrix authority:'+k,m[k],float(authority[k]))
    symmetry_theta = float(np.sqrt(np.mean((theta+theta[::-1,::-1]-1)**2))/max(np.sqrt(np.mean(theta**2)),1e-12))
    inplane = vel[:,:,:2]
    symmetry_velocity = float(np.sqrt(np.mean(np.sum((inplane+inplane[::-1,::-1])**2,axis=2)))/max(np.sqrt(np.mean(np.sum(inplane**2,axis=2))),1e-12))
    if 'symmetry' in m:
        check(case_id,'temperature symmetry',symmetry_theta,m['symmetry']['theta_L2_relative'])
        check(case_id,'velocity symmetry',symmetry_velocity,m['symmetry']['velocity_L2_relative'])
    summary = dict(case_id=case_id,source_case_id=source_id,category=category,route=route,
        Ra=int(mf['Ra_target']),N=nx,grid=f'{nx}x{nz}x1',final_iteration=end,
        computed=status.get('computed','outside_matrix'),accepted=status.get('accepted','outside_matrix'),Gate_D=status.get('Gate_D','outside_matrix'),
        case_path=str(case_path),metrics_path=str(metrics_path),
        theta_min=float(theta.min()),theta_max=float(theta.max()),theta_below_0_count=int(np.sum(theta<0)),theta_above_1_count=int(np.sum(theta>1)),
        out_of_plane_velocity_max=float(np.abs(vel[:,:,2]).max()),
        temperature_symmetry=symmetry_theta,velocity_symmetry=symmetry_velocity,
        **{k:m[k] for k in (*QOIS,'Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax_Z','Wmax_X','Nu_hot_local_max','Nu_hot_local_min')},**density_stats)
    return Case(case_id,source_id,route,category,case_path,metrics_path,mf,m,status,theta,vel,density,centre,local,section,summary)


def load_all():
    a,b,g = audit_status()
    areview={r['case_id']:r for r in read_csv(A_REVIEW/'RouteA_full_steady_matrix_case_review.csv')}
    reports={}
    for att,exponent in zip(('004','005','006','007'),range(3,7)):
        report=read_json(ROOT/f'results/routeA/attempts/attempt_{att}/Ra1e{exponent}_trio_report.json')
        reports.update({r['case_id']:r for r in report['cases']})
    bmanifest=read_json(ROOT/'results/routeB/full_matrix_manifest.json')['cases']
    oldb=read_json(ROOT/'results/routeB/run_manifest.json')['cases']
    cases=[]
    for row in a:
        cid=row['case_id']; owner=reports[cid]; mp=ROOT/owner['metrics_path']
        assert sha(mp)==owner['metrics_sha256'], f'STOP: altered authoritative metrics {cid}'
        cases.append(load_case(cid,cid,'A','matrix',ROOT/'cases/routeA'/cid,mp,row,areview[cid]))
    for row in b:
        cid=row['case_id']; owner=bmanifest[cid]; sid=row['source_case_id']
        mp=Path(owner['metrics_path'])
        if owner.get('metrics_sha256'): assert sha(mp)==owner['metrics_sha256']
        cases.append(load_case(cid,sid,'B','matrix',Path(owner['generated_manifest']['case_path']),mp,row,row))
    for rt in ('A','B'):
        for sid,dirname in [(rt+'-COND','Ra0_medium'),(rt+'-SMOKE','Ra1e4_coarse')]:
            cp=ROOT/'cases/routeA'/dirname if rt=='A' else Path(oldb[sid]['generated_manifest']['case_path'])
            cases.append(load_case(sid,sid,rt,'auxiliary',cp,ROOT/f'results/route{rt}/cases/{sid}/metrics.json',{}))
    hr=read_json(ROOT/'results/routeA/attempts/attempt_008/GateH_report.json')
    hc=hr.get('perturbed',hr.get('case',{}))
    # Read the report's own status, never infer acceptance from visual similarity.
    if not hc:
        hc=next(v for v in hr.values() if isinstance(v,dict) and v.get('case_id')=='A-H-Ra1e6-fine-beta1e-4')
    assert hc['accepted'] and hc['computed'] and hc['Gate_D']=='PASS'
    sid='A-H-Ra1e6-fine-beta1e-4'
    cases.append(load_case(sid,sid,'A','sensitivity',ROOT/'cases/routeA'/sid,ROOT/f'results/routeA/cases/{sid}/metrics.json',
                          dict(computed='true',accepted='true',Gate_D=hc['Gate_D'],final_iteration=hc['final_iteration'])))
    return cases,g


def protected_snapshot():
    """Full protected inventory (content metadata), plus tracked-file git diff.

    Hashes of every actual input are additionally checked before/after plotting.
    No shell solver commands are present in the visualization code.
    """
    roots=[ROOT/p for p in ('results/routeA','results/routeB','cases','docs','reference','Scripts/routeA','Scripts/routeB')]
    roots.append(Path('/home/mirai/OpenFOAM/mirai-6/run/deVahlDavisBenchmark/cases/routeB'))
    inventory={}
    for root in roots:
        for base,dirs,files in os.walk(root):
            for name in files:
                p=Path(base)/name
                st=p.lstat()
                inventory[str(p)]=[st.st_size,st.st_mtime_ns,st.st_ctime_ns]
    return inventory


def git_evidence():
    cmds=[['git','diff','--binary','HEAD','--','.',':(exclude)Scripts/visualization',':(exclude)results/visualization_all_cases'],
          ['git','status','--short','--untracked-files=no'],['git','rev-parse','HEAD']]
    return [subprocess.run(c,cwd=ROOT,check=True,capture_output=True,text=True).stdout for c in cmds]


def save_figure(fig, output, relative, inventory, description, case_ids):
    base=output/relative
    base.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(base.with_suffix('.png'),dpi=300,bbox_inches='tight',facecolor='white')
    fig.savefig(base.with_suffix('.pdf'),bbox_inches='tight',facecolor='white')
    plt.close(fig)
    inventory.append(dict(figure=str(relative),png=str(base.with_suffix('.png').relative_to(output)),
        pdf=str(base.with_suffix('.pdf').relative_to(output)),description=description,case_ids=';'.join(case_ids),png_dpi=300))
