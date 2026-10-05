#!/usr/bin/env python3
"""Execute only allowlisted independent microcases, preserving all evidence."""
import ast
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RESULTS=ROOT/'results/routeB/gateG_sensitivity_experiment'
RUNS=HERE/'runs'
sys.path.insert(0,str(HERE.parent))
from common import parser, read_case
from run_verification import header

REG=json.loads((HERE/'experiment_preregistration_v1.json').read_text())
QOIS=REG['qois']; VALUES=QOIS[:5]; POSITIONS=QOIS[5:]
# A inherited WM_BASH_FUNCTIONS flag can suppress function definitions in a fresh bash.
# Clear that loading flag; do not change the installation or inherited user paths.
raw_env=subprocess.check_output(['bash','-c','unset WM_BASH_FUNCTIONS; source /home/mirai/OpenFOAM/OpenFOAM-6/etc/bashrc >/dev/null; env -0'])
ENV=dict(item.decode().split('=',1) for item in raw_env.split(b'\0') if b'=' in item)
AUDIT=HERE/'auditSolver/bin/buoyantBoussinesqSimpleFoamContinuitySourceAudit'
L=.01; DEPTH=.001; ALPHA=1e-6/.71
ns={'np':np,'Path':Path,'read_label_list':parser.read_label_list,'read_scalar':parser.read_scalar,'read_boundary_scalar':parser.read_boundary_scalar}
tree=ast.parse((ROOT/'Scripts/routeB/analyze_case.py').read_text())
names={'centreline','nusselt','paper_nusselt','continuity_metrics'}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),str(ROOT/'Scripts/routeB/analyze_case.py'),'exec'),ns)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj): Path(p).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def rows(p):
    with Path(p).open() as f: return list(csv.DictReader(f))
def csvwrite(name,data):
    keys=list(dict.fromkeys(k for row in data for k in row)) or ['status']
    with (RESULTS/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data)

def guard(case):
    p=Path(case).resolve()
    if not p.is_relative_to(RUNS.resolve()): raise RuntimeError('STOP: case outside sensitivity allowlist')
    m=json.loads((p/'case_manifest.json').read_text())
    if m['Ra_test']!=30000 or m['n'] not in (20,40,80): raise RuntimeError('STOP: forbidden physics/grid')
    frozen=json.loads((RESULTS/'preregistration_hashes.json').read_text())
    for name,h in frozen.items():
        if sha(HERE/name)!=h: raise RuntimeError('STOP: immutable preregistration changed')
    if (RESULTS/'confirmation_manifest_v1.json').exists():
        if sha(RESULTS/'confirmation_manifest_v1.json')!=(RESULTS/'confirmation_manifest_v1.sha256').read_text().split()[0]:
            raise RuntimeError('STOP: confirmation manifest modified')

def execute(command,case,log):
    guard(case)
    with Path(log).open('w') as f:
        done=subprocess.run([str(x) for x in command],env=ENV,stdout=f,stderr=subprocess.STDOUT,cwd=HERE)
    text=Path(log).read_text()
    if done.returncode or 'FOAM FATAL' in text or re.search(r'\b(?:nan|inf)\b',text,re.I):
        raise RuntimeError(f'STOP: fatal/nonfinite run {case.name}')
    return text

def make_case(run_id,n,tol,eta=0.,pattern='P1',sign=1,up_base=None,offset=0.,fixed_iterations=None):
    case=RUNS/run_id
    if case.exists(): raise RuntimeError('Refuse to overwrite '+run_id)
    shutil.copytree(HERE.parent/'microcase_template',case)
    ref=(n//2)*n+n//2
    for file in ('system/blockMeshDict','system/fvSolution'):
        p=case/file;p.write_text(p.read_text().replace('@N@',str(n)).replace('@TOL@',str(tol)).replace('@REF@',str(ref)))
    beta=30000*1e-6*ALPHA/(9.81*1*L**3)
    p=case/'constant/transportProperties';t=p.read_text()
    t=re.sub(r'beta \[([^\]]+)\] [^;]+;',rf'beta [\1] {beta:.17g};',t)
    t=t.replace('300.5',str(300.5+offset));p.write_text(t)
    p=case/'0/T';t=p.read_text().replace('300.5',str(300.5+offset))
    t=re.sub(r'value uniform 301;',f'value uniform {301+offset};',t)
    t=re.sub(r'value uniform 300;',f'value uniform {300+offset};',t);p.write_text(t)
    control=header('controlDict')+f'''application buoyantBoussinesqSimpleFoamContinuitySourceAudit;
startFrom startTime; startTime 0; stopAt endTime; endTime {fixed_iterations or 12000};
deltaT 1; writeControl timeStep; writeInterval {fixed_iterations or 20}; purgeWrite 14;
writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 10;
runTimeModifiable false; steadyMonitorEnabled {'false' if fixed_iterations else 'true'};
auditPressureTolerance {tol:.17g};
'''
    (case/'system/controlDict').write_text(control)
    manifest={'id':run_id,'n':n,'Ra_test':30000,'Pr':.71,'L':L,'depth':DEPTH,'alpha':ALPHA,'nu':1e-6,'beta':beta,'Th':301+offset,'Tc':300+offset,'TRef':300.5+offset,'DeltaT':1,'tolerance':tol,'relTol':0,'eta_nom':eta,'pattern':pattern,'sign':sign,'Up_base':up_base,'pRefCell':ref,'temperature_offset':offset,'source_faces':[],'source_cells':[],'g':[],'solver':str(AUDIT),'fixed_iterations':fixed_iterations}
    dump(case/'case_manifest.json',manifest)
    execute(['blockMesh','-case',case],case,case/'log.blockMesh')
    owner=parser.read_label_list(case/'constant/polyMesh/owner')
    neigh=parser.read_label_list(case/'constant/polyMesh/neighbour')
    g=np.zeros(n*n)
    if eta:
        if not up_base: raise RuntimeError('Source requires independent Up_base')
        choices=[];used=set()
        for x,z in REG['arm_2']['patterns'][pattern]:
            candidates=[]
            for f,(o,ne) in enumerate(zip(owner,neigh)):
                if ne-o!=1 or ref in (o,ne) or o in used or ne in used: continue
                fx=(o%n+1)/n;fz=(o//n+.5)/n
                candidates.append(((fx-x)**2+(fz-z)**2,f,int(o),int(ne),fx,fz))
            _,f,o,ne,fx,fz=min(candidates)
            choices.append({'face':f,'owner':o,'neighbour':ne,'X':fx,'Z':fz})
            used.update((o,ne))
        magnitude=eta*up_base*(L*L*DEPTH)/L
        for site in choices:
            g[site['owner']]+=sign*magnitude/(2*len(choices))
            g[site['neighbour']]-=sign*magnitude/(2*len(choices))
        if abs(g.sum())>64*np.finfo(float).eps*np.abs(g).sum(): raise RuntimeError('STOP: source nonzero net')
        manifest['source_faces']=choices;manifest['source_cells']=np.flatnonzero(g).tolist()
    manifest['g']=g.tolist();manifest['sum_g']=float(g.sum());manifest['sum_abs_g']=float(abs(g).sum())
    v=L*L*DEPTH/(n*n)
    source=header('continuitySource','volScalarField')+'dimensions [0 0 -1 0 0 0 0];\ninternalField nonuniform List<scalar>\n'+str(n*n)+'\n(\n'+'\n'.join(f'{x/v:.17g}' for x in g)+'\n);\nboundaryField\n{\n'
    source+='\n'.join(p+' { type zeroGradient; }' for p in ('hotWall','coldWall','bottomWall','topWall'))
    source+='\nfront { type empty; }\nback { type empty; }\n}\n'
    (case/'constant/continuitySource').write_text(source)
    dump(case/'case_manifest.json',manifest)
    return case

def centre_at(U,n,count):
    axis=(np.arange(n)+.5)/n;q=np.linspace(0,1,count)
    u=.5*(U[:,n//2-1,0]+U[:,n//2,0])*L/ALPHA
    w=.5*(U[n//2-1,:,1]+U[n//2,:,1])*L/ALPHA
    result={}
    for values,key,pos in [(u,'Umax','Umax_Z'),(w,'Wmax','Wmax_X')]:
        f=np.interp(q,np.r_[0,axis,1],np.r_[0,values,0]);i=int(np.argmax(f))
        tied=q[np.abs(f-f[i])<=64*np.finfo(float).eps*max(1,abs(f[i]))]
        result[key]=float(f[i]);result[pos]=float(q[i]);result[pos+'_tie_width']=float(np.ptp(tied))
    return result

def extract(case,iteration=None):
    m=json.loads((case/'case_manifest.json').read_text());n=m['n']
    if iteration is None: iteration=max(int(float(p.name)) for p in case.iterdir() if p.is_dir() and re.fullmatch(r'\d+',p.name))
    folder=case/str(iteration)
    metric,Uflat,phi,q,boundary=read_case(case,iteration,n)
    U=Uflat.reshape(n,n,3);T=parser.read_scalar(folder/'T',n*n).reshape(n,n)
    if not (np.isfinite(U).all() and np.isfinite(T).all()): raise RuntimeError('STOP: nonfinite fields')
    wall=ns['nusselt'](case,folder,T,n,n,L,1,m['Th'],m['Tc'])
    nu=ns['paper_nusselt'](case,folder,T,U,n,n,L,DEPTH,ALPHA,1,m['Th'],m['Tc'],wall)
    c=centre_at(U,n,4097);fine=centre_at(U,n,8193)
    qoi={k:float(nu[k]) for k in QOIS[:3]};qoi.update({k:c[k] for k in QOIS[3:]})
    ext={k:64*np.finfo(float).eps*max(1,abs(v)) for k,v in qoi.items()}
    for k in QOIS[3:]: ext[k]+=abs(c[k]-fine[k])
    for k in POSITIONS: ext[k]+=1/4096+max(c[k+'_tie_width'],fine[k+'_tie_width'])
    _,divU=ns['continuity_metrics'](case,folder,U,n,n,L,DEPTH)
    metric['epsilon_v']=float(L/metric['Up']*divU)
    metric['legacy_epsilon_m']=metric['epsilon_v']
    metric['max_over_mean']=metric['epsilon_phi_max']/metric['epsilon_phi_mean'] if metric['epsilon_phi_mean'] else None
    metric['absolute_total_wall_flux']=float(sum(abs(b).sum() for b in boundary))
    metric['closure']=float(q.sum()-sum(b.sum() for b in boundary))
    metric['sum_q']=float(q.sum())
    metric['P95_normalized']=L/metric['Up']*metric['P95_abs_div_phi']
    metric['P99_normalized']=L/metric['Up']*metric['P99_abs_div_phi']
    for name,b in zip(('hot','cold','bottom','top'),boundary):
        metric[name+'_patch_signed']=float(b.sum());metric[name+'_patch_absolute']=float(abs(b).sum())
    i=metric['max_cell_id'];metric['max_X']=(i%n+.5)/n;metric['max_Z']=(i//n+.5)/n
    metric['heat_imbalance']=abs(wall['hot_b1']-wall['cold_b1'])/(.5*(abs(wall['hot_b1'])+abs(wall['cold_b1'])))
    audit={k:float(v) for k,v in rows(case/'continuityAudit.csv')[-1].items()}
    g=np.array(m['g']);v=L*L*DEPTH/(n*n)
    cells=rows(case/'sourceCells.csv');rphysical=np.array([float(x['physical_residual']) for x in cells])
    realization={'sum_abs_q_minus_g':float(abs(q-g).sum()),'max_abs_q_minus_g':float(abs(q-g).max()),'sum_abs_q_plus_g':float(abs(q+g).sum()),'sum_g':float(g.sum()),'sum_q':float(q.sum()),'sum_abs_g':float(abs(g).sum()),'physical_mapping_L1':float(abs(q-rphysical).sum()),'reference_q_minus_g':float(q[m['pRefCell']]-g[m['pRefCell']]),'source_rate_units':'1/s','integrated_source_units':'m3/s','source_support':m['source_cells'],'source_faces':m['source_faces'],'actual_source_relative_error':float(abs(q-g).sum()/abs(g).sum()) if abs(g).sum() else None,'boundary_flux':metric['net_boundary_flux'],'boundary_absolute':metric['absolute_total_wall_flux'],'closure':metric['closure'],'reference_aware_true_nonreference_L1':audit['true_nonreference_L1'],'recursive_residual':audit['R_recursive'],'true_residual':audit['R_true']}
    if m['eta_nom']:
        mapping=realization['physical_mapping_L1']/max(abs(g).sum(),abs(q).sum())
        valid=realization['actual_source_relative_error']<=.05 and mapping<=1e-6
        valid=valid and abs(g.sum())<=64*np.finfo(float).eps*abs(g).sum()
        valid=valid and metric['absolute_total_wall_flux']<=64*np.finfo(float).eps*metric['Up']*L*DEPTH
        valid=valid and abs(metric['closure'])<=128*np.finfo(float).eps*(abs(phi).sum()+sum(abs(b).sum() for b in boundary))
        realization['validated']=bool(valid)
        realization['mapping_scaled_error']=float(mapping)
    else: realization['validated']=True
    hist=[{k:float(v) for k,v in x.items()} for x in rows(case/'steadyMonitor.csv')]
    uncertainty={}; serialization={}
    for k in QOIS:
        tail=np.array([h[k] for h in hist[-11:]]) if hist else np.array([qoi[k]])
        it=max(float(np.ptp(tail)),abs(qoi[k]-float(tail[0])))
        serial=abs(qoi[k]-hist[-1][k]) if hist and int(hist[-1]['iteration'])==iteration else 0.
        uncertainty[k]={'iterative':it,'extraction':ext[k],'serialization':serial,'restart':0.,'total':it+ext[k]+serial}
        serialization[k]=serial
    hashes={f:sha(folder/f) for f in ('U','T','p_rgh','phi')}
    return {'id':m['id'],'manifest':m,'iteration':iteration,'qoi':qoi,'metrics':metric,'audit':audit,'source_realization':realization,'uncertainty':uncertainty,'final_hashes':hashes,'steady_history_tail':hist[-21:],'serialization_difference':serialization}

class Experiment:
    def __init__(self):
        self.records=[];self.baselines={};self.status={'solver_executed':False,'solver_attempts':[],'zero_source_equivalence':{'status':'NOT_RUN'},'source_sign':'NOT_RUN','stop':None,'exploration':None,'confirmation':None,'pilot':None,'temperature_offset':{'performed':False}}
    def save(self):
        dump(RESULTS/'working_state.json',{'status':self.status,'records':self.records,'baselines':{str(k):v['id'] for k,v in self.baselines.items()}})
    def run(self,run_id,n,tol,role='arm1',phase='exploration',**kw):
        if (RESULTS/'STOP.json').exists():
            raise RuntimeError('Existing STOP requires a separately authorized task; refusing solver execution')
        case=make_case(run_id,n,tol,**kw)
        self.status['solver_executed']=True
        attempt={'id':run_id,'n':n,'tolerance':tol,'role':role,'phase':phase,'status':'RUNNING'}
        self.status['solver_attempts'].append(attempt);self.save()
        print('RUN',run_id,flush=True)
        text=execute([AUDIT,'-case',case],case,case/'log.solver')
        record=extract(case);record['role']=role;record['phase']=phase
        record['status']='FIXED_ITERATION_DIAGNOSTIC' if kw.get('fixed_iterations') else ('STEADY' if 'SENSITIVITY_STEADY_CONFIRMED' in text else 'NOT_CONVERGED')
        record['normal_exit']='End' in text
        residuals=re.findall(r'Solving for (Ux|Uy|Uz|T|p_rgh), Initial residual = ([\deE+.-]+), Final residual = ([\deE+.-]+)',text)
        last={name:{'initial':float(a),'final':float(b)} for name,a,b in residuals}
        record['equation_residuals']=last
        attempt['status']=record['status'];attempt['iterations']=record['iteration']
        self.records.append(record);dump(RESULTS/(run_id+'.json'),record)
        self.save()
        print('DONE',run_id,record['status'],'iteration',record['iteration'],'epsilon',record['metrics']['epsilon_phi_mean'],'realization',record['source_realization'].get('actual_source_relative_error'),flush=True)
        if record['status']=='NOT_CONVERGED': raise RuntimeError('STOP: maximum iteration without steady solution: '+run_id)
        if not kw.get('fixed_iterations'):
            if any(last[k]['initial']>1e-8 for k in ('Ux','Uy','Uz','T') if k in last): raise RuntimeError('STOP: other equation residual convergence: '+run_id)
            if last.get('p_rgh',{}).get('final',float('inf'))>1.1*tol: raise RuntimeError('STOP: pressure convergence not achieved: '+run_id)
        if kw.get('eta') and not record['source_realization']['validated']:
            raise RuntimeError('STOP: uncontrolled source realization: '+run_id)
        return record
    def equivalence(self):
        if (RESULTS/'STOP.json').exists():
            raise RuntimeError('Existing STOP requires a separately authorized task; refusing solver execution')
        stock=make_case('equivalence_stock20',20,1e-8,fixed_iterations=10)
        self.status['solver_executed']=True
        self.status['solver_attempts'].append({'id':'equivalence_stock20','n':20,'tolerance':1e-8,'role':'equivalence','phase':'verification','status':'RUNNING'});self.save()
        execute(['buoyantBoussinesqSimpleFoam','-case',stock],stock,stock/'log.solver')
        self.status['solver_attempts'][-1]['status']='FIXED_ITERATION_DIAGNOSTIC'
        source=self.run('equivalence_source20',20,1e-8,role='equivalence',phase='verification',fixed_iterations=10)
        comparisons={f:{'stock':sha(stock/'10'/f),'source':source['final_hashes'][f]} for f in ('U','T','p_rgh','phi')}
        same=all(x['stock']==x['source'] for x in comparisons.values())
        self.status['zero_source_equivalence']={'status':'PASS' if same else 'FAIL','basis':'Complete U/T/p_rgh/phi file SHA256 comparison; 20 grid, cold-start ten iterations','fields':comparisons}
        dump(RESULTS/'zero_source_equivalence.json',self.status['zero_source_equivalence']);self.save()
        if not same: raise RuntimeError('STOP: zero-source stock/source solver inequivalence')
    def restart_probe(self,baseline):
        n=baseline['manifest']['n'];base=RUNS/baseline['id'];end=baseline['iteration'];start=end-200
        case=make_case(f'restart_n{n}',n,1e-10,fixed_iterations=end)
        shutil.copytree(base/str(start),case/str(start))
        p=case/'system/controlDict';p.write_text(p.read_text().replace('startFrom startTime; startTime 0;','startFrom latestTime; startTime 0;'))
        self.status['solver_attempts'].append({'id':case.name,'n':n,'tolerance':1e-10,'role':'restart','phase':'diagnostic','status':'RUNNING'});self.save()
        execute([AUDIT,'-case',case],case,case/'log.solver')
        self.status['solver_attempts'][-1]['status']='FIXED_ITERATION_DIAGNOSTIC'
        r=extract(case);r['role']='restart';r['phase']='diagnostic';r['status']='FIXED_ITERATION_DIAGNOSTIC'
        self.records.append(r)
        for k in QOIS:
            delta=abs(r['qoi'][k]-baseline['qoi'][k]);baseline['uncertainty'][k]['restart']=delta
            baseline['uncertainty'][k]['total']+=delta
        dump(RESULTS/(r['id']+'.json'),r);dump(RESULTS/(baseline['id']+'.json'),baseline);self.save()
    def comparison(self,r,baseline=None):
        b=baseline or self.baselines[r['manifest']['n']]
        data={}
        for k in QOIS:
            delta=r['qoi'][k]-b['qoi'][k]
            u=r['uncertainty'][k]['total']+b['uncertainty'][k]['total']
            # Restart observed on same-grid baseline enters once as a shared conservative allowance.
            scale=1. if k in POSITIONS or abs(b['qoi'][k])<=10*b['uncertainty'][k]['total'] else abs(b['qoi'][k])
            data[k]={'Delta_Q':delta,'absolute_difference':abs(delta),'scale':scale,'E_Q':abs(delta)/scale,'uncertainty':u/scale,'upper_impact':(abs(delta)+u)/scale,'lower_impact':max(0,abs(delta)-u)/scale,'resolved':abs(delta)>u,'status':'RESOLVED' if abs(delta)>u else 'EFFECT_NOT_RESOLVED'}
        return data

    def execute_all(self):
        self.equivalence()
        b20=self.run('baseline_n20',20,1e-10);self.baselines[20]=b20;self.restart_probe(b20)
        tiny=self.run('tiny_sign20',20,1e-10,role='sign',phase='verification',eta=1e-7,up_base=b20['metrics']['Up'],fixed_iterations=20)
        real=tiny['source_realization']
        self.status['source_sign']='PLUS_G' if real['sum_abs_q_minus_g']<real['sum_abs_q_plus_g'] else 'INVALID'
        self.save()
        if self.status['source_sign']!='PLUS_G' or not real['validated']: raise RuntimeError('STOP: source sign/dimension/realization test failed')
        for n in (20,40):
            if n==40:
                b=self.run('baseline_n40',40,1e-10);self.baselines[40]=b;self.restart_probe(b)
            for tol in (1e-6,1e-8): self.run(f'arm1_n{n}_p{tol:g}',n,tol)
        pilot=[]
        for eta in REG['pilot']['levels']:
            r=self.run(f'pilot20_eta{eta:g}',20,1e-10,role='pilot',eta=eta,up_base=b20['metrics']['Up'])
            r['response']=self.comparison(r);pilot.append(r)
        valid=[r for r in pilot if r['source_realization']['validated']]
        candidates=[i for i,r in enumerate(valid) if i+2<len(valid) and any(r['response'][k]['resolved'] for k in VALUES)]
        if len(valid)<3: raise RuntimeError('STOP: fewer than three controllable steady pilot levels')
        start=candidates[0] if candidates else len(valid)-3
        selected=valid[start:start+3];levels=[r['manifest']['eta_nom'] for r in selected]
        self.status['pilot']={'levels':levels,'selection_status':'LOWEST_RESOLVED_WITH_TWO_SUCCESSORS' if candidates else 'HIGHEST_THREE_RESOLUTION_INCOMPLETE','valid_levels':[r['manifest']['eta_nom'] for r in valid]}
        dump(RESULTS/'pilot_selection.json',self.status['pilot']);self.save()
        for n in (20,40):
            for pattern in ('P1','P2','P4'):
                for eta in levels:
                    reuse=next((r for r in selected if n==20 and pattern=='P1' and r['manifest']['eta_nom']==eta),None)
                    if reuse:
                        reuse['included_in_arm2_exploration']=True;continue
                    self.run(f'arm2_n{n}_{pattern}_eta{eta:g}_pos',n,1e-10,role='arm2',eta=eta,pattern=pattern,up_base=self.baselines[n]['metrics']['Up'])
            for pattern in ('P1','P2'):
                self.run(f'arm2_n{n}_{pattern}_eta{levels[1]:g}_neg',n,1e-10,role='arm2',eta=levels[1],pattern=pattern,sign=-1,up_base=self.baselines[n]['metrics']['Up'])
        self.match_means(levels)
        shifted=self.run('offset_baseline20',20,1e-10,role='offset',phase='diagnostic',offset=50)
        shift_source=self.run('offset_source20',20,1e-10,role='offset',phase='diagnostic',offset=50,eta=levels[1],up_base=b20['metrics']['Up'])
        original=next(r for r in selected if r['manifest']['eta_nom']==levels[1])
        zero_invariant=all(abs(shifted['qoi'][k]-b20['qoi'][k])<=shifted['uncertainty'][k]['total']+b20['uncertainty'][k]['total'] for k in QOIS)
        off_response=self.comparison(shift_source,shifted);orig_response=self.comparison(original)
        affected=[k for k in QOIS if abs(off_response[k]['Delta_Q']-orig_response[k]['Delta_Q'])>off_response[k]['uncertainty']*off_response[k]['scale']+orig_response[k]['uncertainty']*orig_response[k]['scale']]
        self.status['temperature_offset']={'performed':True,'zero_source_invariant':zero_invariant,'source_response_offset_sensitive':bool(affected),'affected_QoIs':affected,'unshifted_response':orig_response,'shifted_response':off_response,'interpretation_only':True}
        dump(RESULTS/'temperature_offset_diagnostic.json',self.status['temperature_offset'])
        from analyze import exploration
        self.status['exploration']=exploration(self)
        dump(RESULTS/'exploration_summary.json',self.status['exploration']);self.save()
        confirmation={'schema':'routeB-gateG-sensitivity-confirmation-v1','grid':80,'arm1_tolerances':[1e-6,1e-8,1e-10],'arm2_patterns':['P1','P3'],'arm2_amplitudes':[levels[0],levels[-1]],'arm2_signs':[1,-1],'qualitative_prediction':self.status['exploration']['hypotheses'],'exploration_model_v1':self.status['exploration'],'uncertainty_method':REG['uncertainty'],'comparison_rule':'Apply fixed v1 resolved-response monotonicity/sign/pattern interpretation; upper impacts compared against frozen same-QoI exploratory envelope at corresponding nominal level. Out-of-envelope values are retained, not quota FAIL or retroactive refit.','success_criteria':'All frozen runs steady and realized, provenance intact; report whether supported exploratory trends persist; unresolved or extrapolation failure => PARTIAL. No research quota PASS.','same_mean_matching_policy':'Use frozen exploration matching rule; at most two between-run adjustments per condition; include all trials','no_retroactive_v1_edits':True,'qoi_quota':None,'tau_mean':None}
        dump(RESULTS/'confirmation_manifest_v1.json',confirmation)
        h=sha(RESULTS/'confirmation_manifest_v1.json');(RESULTS/'confirmation_manifest_v1.sha256').write_text(h+'  confirmation_manifest_v1.json\n')
        print('FROZEN CONFIRMATION',h,flush=True)
        b80=self.run('baseline_n80',80,1e-10,phase='confirmation');self.baselines[80]=b80;self.restart_probe(b80)
        for tol in (1e-6,1e-8): self.run(f'arm1_n80_p{tol:g}',80,tol,phase='confirmation')
        for pattern in confirmation['arm2_patterns']:
            for eta in confirmation['arm2_amplitudes']:
                for sign in confirmation['arm2_signs']:
                    self.run(f'arm2_n80_{pattern}_eta{eta:g}_{"pos" if sign==1 else "neg"}',80,1e-10,role='arm2',phase='confirmation',eta=eta,pattern=pattern,sign=sign,up_base=b80['metrics']['Up'])
        from analyze import confirmation_analysis
        self.status['confirmation']=confirmation_analysis(self,confirmation)
        dump(RESULTS/'confirmation_results.json',self.status['confirmation']);self.save()

    def match_means(self,levels):
        # Set tolerance from source realization plus within-tail epsilon repeatability only.
        study=[r for r in self.records if r['phase']=='exploration' and (r['role']=='arm2' or r.get('included_in_arm2_exploration'))]
        resolution=max([r['source_realization']['actual_source_relative_error'] for r in study]+[0.])
        repeat=max([np.ptp([h['epsilon_phi_mean'] for h in r['steady_history_tail'][-11:]])/r['metrics']['epsilon_phi_mean'] for r in study]+[0.])
        tolerance=float(2*(resolution+repeat))
        dump(RESULTS/'same_mean_matching_rule.json',{'relative_tolerance':float(tolerance),'basis':'Two conservative source-realization/repeatability envelopes, no QoI response used','max_extra_trials':2})
        for n in (20,40):
            for eta in levels:
                target=next(r for r in study if r['manifest']['n']==n and r['manifest']['pattern']=='P1' and r['manifest']['eta_nom']==eta and r['manifest']['sign']==1)
                for pattern in ('P2','P4'):
                    candidate=next(r for r in study if r['manifest']['n']==n and r['manifest']['pattern']==pattern and r['manifest']['eta_nom']==eta and r['manifest']['sign']==1)
                    for trial in range(2):
                        actual=candidate['metrics']['epsilon_phi_mean'];desired=target['metrics']['epsilon_phi_mean']
                        if abs(actual-desired)/desired<=tolerance: break
                        adjusted=candidate['manifest']['eta_nom']*desired/actual
                        candidate=self.run(f'match_n{n}_{pattern}_eta{eta:g}_trial{trial+1}',n,1e-10,role='matching',eta=adjusted,pattern=pattern,up_base=self.baselines[n]['metrics']['Up'])
                    candidate['same_mean_group']=target['id'];candidate['same_mean_matched']=abs(candidate['metrics']['epsilon_phi_mean']-target['metrics']['epsilon_phi_mean'])/target['metrics']['epsilon_phi_mean']<=tolerance
                    candidate['same_mean_tolerance']=float(tolerance)
        self.save()

def main():
    if (RESULTS/'STOP.json').exists():
        raise SystemExit('STOP is already recorded. No further solver execution or replacement of partial evidence is allowed.')
    experiment=Experiment()
    try:
        experiment.execute_all()
    except Exception as exc:
        experiment.status['stop']=str(exc);experiment.save()
        dump(RESULTS/'STOP.json',{'reason':str(exc),'further_solver_execution_stopped':True})
        print(str(exc),flush=True)
    finally:
        from analyze import finalize
        finalize(experiment)

if __name__=='__main__': main()
