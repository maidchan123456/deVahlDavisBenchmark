import hashlib,json,os,re,shutil,subprocess,sys,time,traceback
from datetime import datetime
from pathlib import Path
import numpy as np

ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'Scripts/routeA'))
import analyze_case as a
from foam_fields import read_scalar,read_vector,latest_time,_named_block
C=json.loads((ROOT/'docs/routeA_execution_contract_v1.1.json').read_text())
CH='dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b'
OUT=ROOT/'results/routeA/attempts/attempt_002'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def guard():
    assert sha(ROOT/'docs/routeA_execution_contract_v1.1.json')==CH,'contract digest'
    for p,h in C['implementation_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in C['template_source']['unchanged_template_sha256'].items():assert sha(ROOT/p)==h,p
    for x in [C['iteration_caps_csv'],C['amendment'],C['amendment']['parent']]:assert sha(ROOT/x['path'])==x['sha256'],x
    for p,h in PROTECTED.items():assert sha(ROOT/p)==h,('protected',p)
def run(cmd,log):
    start=time.time()
    with Path(log).open('w') as f:rc=subprocess.run([str(x) for x in cmd],stdout=f,stderr=subprocess.STDOUT,env=os.environ).returncode
    return {'argv':[str(x) for x in cmd],'exit_code':rc,'elapsed_seconds':time.time()-start,'log':str(log),'log_sha256':sha(log)}
def health(log,rc):
    with Path(log).open() as f:flags=a.classify_health_lines(f)
    end=False;div=[];models=[];banner=False
    with Path(log).open() as f:
        for line in f:
            end|=bool(re.fullmatch(r'End\s*',line))
            banner|='sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).' in line
            if re.search(r'\b(?:solution diverged|divergence detected|DILUPBiCGStab.*singular)\b',line,re.I):div.append(line.strip())
            if 'Selecting ' in line or line.startswith('Build') or 'SIMPLE' in line:models.append(line.strip())
    return {'exit_code':rc,'standalone_End':end,'flags':flags,'normal_banner_present':banner,'normal_banner_misclassified_as_FPE':False if banner and not flags['fpe'] else None,'explicit_divergence_evidence':div,'runtime_selection_lines':models,'normal_exit':rc==0 and end,'no_fatal_or_nan':not any(flags.values()) and not div}
def runtime_check(h):
    text='\n'.join(h['runtime_selection_lines'])
    for token in ['13-441953dfbb42','fluid','heRhoThermo','Boussinesq','Stokes','Fourier']:
        assert token in text,('runtime missing',token,text)
    assert 'steady-state' in text or 'SIMPLE' in text,('steady selection missing',text)
def inputs(case,m):
    return {p:sha(case/p) for p in m['input_sha256']}
def finite_fields(case,N,n):
    folder=case/str(N);ranges={}
    for field in ['T','U','rho','p','p_rgh','phi']+(['e'] if (folder/'e').exists() else []):
        p=folder/field;assert p.exists(),('missing field',p)
        text=p.read_text();assert not re.search(r'\bnan\b|\binf\b',text,re.I),('nonfinite',p)
        if field=='U':v=read_vector(p,n)
        elif field=='phi':
            match=re.search(r'internalField\s+nonuniform\s+List<scalar>\s+(\d+)',text)
            v=read_scalar(p,int(match.group(1))) if match else read_scalar(p,1)
        else:v=read_scalar(p,n)
        assert np.all(np.isfinite(v)),p
        if field=='rho':assert np.all(v>0),'rho not positive'
        ranges[field]=[float(v.min()),float(v.max())]
    T=read_scalar(folder/'T',n);rho=read_scalar(folder/'rho',n);eos=1*(1-.001*(T-300))
    return {'all_required_fields_finite':True,'rho_positive':True,'field_ranges':ranges,'EOS_proxy_max_absolute_difference':float(np.max(np.abs(rho-eos))),'EOS_proxy_max_relative_difference':float(np.max(np.abs(rho-eos)/np.abs(eos))),'independent_thermo_rho_dump':'NOT_AVAILABLE','field_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}}

assert not OUT.exists(),'attempt root already exists'
for cid in C['next_single_task']['case_ids']:
    for p in [ROOT/'cases/routeA'/cid,ROOT/'results/routeA/cases'/cid,ROOT/'results/routeA/initialization_check'/cid]:assert not p.exists(),('unexpected destination',p)
AM=json.loads((ROOT/C['amendment']['path']).read_text())
PROTECTED=dict(AM['protected_before_sha256'])
for p in ['docs/routeA_execution_contract_v1.1.md','docs/routeA_execution_contract_v1.1.json','docs/routeA_execution_contract_amendment_001.md','docs/routeA_execution_contract_amendment_001.json','results/routeA/Ra1e3_preflight_issue_review.md','results/routeA/Ra1e3_preflight_issue_review.json']:
    PROTECTED[p]=sha(ROOT/p)
for p in (ROOT/'results/routeA/figures').glob('*'):
    if p.is_file():PROTECTED[str(p.relative_to(ROOT))]=sha(p)
guard()
OUT.mkdir(parents=True)
shutil.copy2(__file__,OUT/'execution_runner.py')
dump(OUT/'protected_before_sha256.json',PROTECTED)
env={'WM_PROJECT':os.environ.get('WM_PROJECT'),'WM_PROJECT_VERSION':os.environ.get('WM_PROJECT_VERSION'),'WM_PROJECT_DIR':os.environ.get('WM_PROJECT_DIR'),'WM_OPTIONS':os.environ.get('WM_OPTIONS'),'foamRun':shutil.which('foamRun'),'host':os.uname().nodename,'started':datetime.now().astimezone().isoformat(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'contract_version':'1.1','contract_sha256':CH,'analyzer_sha256':C['implementation_sha256']['Scripts/routeA/analyze_case.py'],'attempt':'002','primary_solver_concurrency':1}
assert env['WM_PROJECT']=='OpenFOAM' and env['WM_PROJECT_VERSION']=='13' and env['WM_PROJECT_DIR']=='/opt/openfoam13'
dump(OUT/'environment.json',env)
STATE={'overall':'RUNNING','attempt':'002','cases':[],'environment':env,'stop_reason':None}
dump(OUT/'execution_state.json',STATE)
try:
    for grid,name in [(40,'coarse'),(80,'medium'),(160,'fine')]:
        cid='A-Ra1e3-'+name;case=ROOT/'cases/routeA'/cid;result=ROOT/'results/routeA/cases'/cid
        row={'case_id':cid,'grid':[grid,grid,1],'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','segments':[],'status':'PREPARING'}
        STATE['cases'].append(row);dump(OUT/'execution_state.json',STATE)
        print(cid,'generation + mesh + OQ-02',flush=True);guard()
        step=run([sys.executable,ROOT/'Scripts/routeA/generate_case.py','--case-id','A-SMOKE','--name',cid,'--nx',grid,'--ny',grid,'--ra','1000','--end-time','3000'],OUT/(cid+'_generation.log'))
        assert step['exit_code']==0,step
        result.mkdir(parents=True);m=json.loads((case/'case_manifest.json').read_text())
        shutil.copy2(case/'case_manifest.json',case/'generated_manifest_original.json')
        m.update(case_id=cid,generator_role='A-SMOKE',attempt='002',contract_version='1.1',contract_sha256=CH,generator_sha256=C['implementation_sha256']['Scripts/routeA/generate_case.py'])
        dump(case/'case_manifest.json',m)
        assert m['grid']==[grid,grid,1] and m['Ra_target']==1000
        initial_hashes=inputs(case,m);assert initial_hashes==m['input_sha256']
        gy=float(re.search(r'value\s*\(\s*0\s+([^\s]+)\s+0\s*\)',(case/'constant/g').read_text()).group(1))
        props=m['properties'];Ra=abs(gy)*props['beta_1_K']*props['DeltaT_K']*.1**3/(props['nu0_m2_s']*props['alpha0_m2_s']);Pr=props['nu0_m2_s']/props['alpha0_m2_s']
        assert abs(Ra/1000-1)<=1e-10 and abs(Pr/.71-1)<=1e-10
        meshsteps=[]
        for binary,options in [('blockMesh',[]),('checkMesh',['-allGeometry','-allTopology'])]:
            step=run([binary,'-case',case]+options,case/('log.'+binary));meshsteps.append(step)
            assert step['exit_code']==0,step
        meshtext=(case/'log.checkMesh').read_text();assert 'Mesh OK.' in meshtext and re.search(r'cells:\s*'+str(grid*grid)+r'\b',meshtext),'mesh check'
        boundary=(case/'constant/polyMesh/boundary').read_text();patches={}
        for patch,faces,kind,normal,area in [('hotWall',grid,'wall',[-1,0,0],.0001),('coldWall',grid,'wall',[1,0,0],.0001),('bottomWall',grid,'wall',[0,-1,0],.0001),('topWall',grid,'wall',[0,1,0],.0001),('front',grid*grid,'empty',[0,0,-1],.01),('back',grid*grid,'empty',[0,0,1],.01)]:
            block=_named_block(boundary,patch);assert re.search(r'\btype\s+'+kind+r'\s*;',block)
            assert int(re.search(r'nFaces\s+(\d+)',block).group(1))==faces
            patches[patch]={'type':kind,'nFaces':faces,'area_m2':area,'outward_normal':normal,'geometry_source':'generated uniform block vertices and validated patch topology'}
        initstep=run([sys.executable,ROOT/'Scripts/routeA/prepare_initialization_check.py',case],result/'log.prepare_initialization')
        assert initstep['exit_code']==0,initstep
        init=Path((result/'log.prepare_initialization').read_text().strip())
        step=run(['foamRun','-case',init],init/'log.foamRun.initialization');ih=health(init/'log.foamRun.initialization',step['exit_code'])
        dump(result/'initialization_execution.json',{'process':step,'health':ih})
        assert ih['normal_exit'] and ih['no_fatal_or_nan'],ih
        runtime_check(ih)
        step=run([sys.executable,ROOT/'Scripts/routeA/verify_initialization.py',case,init,result/'initialization_verification.json'],result/'log.verify_initialization')
        assert step['exit_code']==0 and json.loads((result/'initialization_verification.json').read_text())['pass'],'OQ-02 failure'
        gateA={'status':'PASS','Ra_actual_from_g_dictionary':Ra,'Pr_actual':Pr,'relative_tolerance':1e-10,'generated_inputs_match':True,'input_sha256':initial_hashes,'mesh_processes':meshsteps,'mesh_sha256':{str(p.relative_to(case)):sha(p) for p in (case/'constant/polyMesh').iterdir() if p.is_file()},'patches':patches,'OQ_02':'PASS','initialization_verification_sha256':sha(result/'initialization_verification.json'),'runtime_model_evidence':ih['runtime_selection_lines'],'environment':env,'template_sha256':C['template_source']['unchanged_template_sha256']}
        dump(result/'gate_A.json',gateA)
        initial_control=(case/'system/controlDict').read_text();start=0
        for N in range(3000,30001,3000):
            guard();assert latest_time(case)[0]==start,('restart state',latest_time(case),start)
            seal=result/'segments'/('end_'+str(N));assert not seal.exists();seal.mkdir(parents=True)
            for p,h in initial_hashes.items():
                if p!='system/controlDict':assert sha(case/p)==h,('input mutation',p)
            control=(case/'system/controlDict').read_text()
            normalized=re.sub(r'(?m)^startFrom\s+\S+;', 'startFrom startTime;',control)
            normalized=re.sub(r'(?m)^endTime\s+\S+;', 'endTime 3000;',normalized)
            assert normalized==initial_control,'unpermitted control change'
            print(cid,f'primary {start} -> {N}',flush=True)
            row['status']='RUNNING';dump(OUT/'execution_state.json',STATE)
            step=run(['foamRun','-case',case],case/('log.foamRun.segment_'+str(N)))
            log=Path(step['log']);h=health(log,step['exit_code']);dump(seal/'execution_health.json',{'process':step,'health':h})
            shutil.copy2(log,seal/'solver.log');shutil.copy2(case/'case_manifest.json',seal/'case_manifest.json');shutil.copy2(case/'system/controlDict',seal/'controlDict');shutil.copy2(result/'gate_A.json',seal/'gate_A.json');shutil.copy2(result/'initialization_verification.json',seal/'initialization_verification.json')
            raw_manifest={'attempt':'002','case_id':cid,'segment_start':start,'end_iteration':N,'contract_version':'1.1','contract_sha256':CH,'Amendment_001':C['amendment'],'analyzer_sha256':env['analyzer_sha256'],'input_sha256':inputs(case,m),'mesh_sha256':gateA['mesh_sha256'],'controlDict_sha256':sha(case/'system/controlDict'),'permitted_control_diff':{} if start==0 else {'startFrom':{'initial':'startTime','current':'latestTime'},'endTime':{'initial':3000,'current':N}},'process':step,'health':h,'gate_A':'PASS','OQ_02':'PASS'}
            assert h['normal_exit'] and h['no_fatal_or_nan'],('primary health failure',h)
            runtime_check(h);assert latest_time(case)[0]==N,'wrong final checkpoint'
            ff=finite_fields(case,N,grid*grid);raw_manifest['final_field_validation']=ff
            wall=case/'postProcessing/wallHeatFluxMonitor'/str(start)/'wallHeatFlux.dat';shutil.copy2(wall,seal/'wallHeatFlux.dat')
            for t in range(N-190,N+1,10):
                source=case/'postProcessing/centrelineMonitor'/str(t)
                shutil.copytree(source,seal/'centrelineMonitor'/str(t))
            residuals=a.parse_residuals(seal/'solver.log');dump(seal/'residuals_initial_final.json',residuals)
            dump(seal/'raw_segment_manifest.json',raw_manifest)
            dump(seal/'raw_seal_sha256.json',{str(p.relative_to(seal)):sha(p) for p in seal.rglob('*') if p.is_file()})
            # Raw evidence is sealed before evaluating Gate D. Only new working outputs follow.
            for func,label in [('div(phi)','divPhi'),('div(U)','divU')]:
                post=run(['foamPostProcess','-case',case,'-func',func,'-time',N],seal/('log.postProcess.'+label))
                ph=health(post['log'],post['exit_code']);assert ph['normal_exit'] and ph['no_fatal_or_nan'],('diagnostic utility failure',post,ph)
            savefig=a.plt.savefig
            def route_figure(path,*args,**kwargs):
                if name=='fine':
                    d=result/'figures';d.mkdir(exist_ok=True)
                    return savefig(d/Path(path).name.replace('A-SMOKE',cid),*args,**kwargs)
            a.plt.savefig=route_figure
            sys.argv=['analyze_case.py',str(case),'--segment-start',str(start),'--solver-log',str(seal/'solver.log')]
            with (seal/'log.analyzer').open('w') as f:
                oldout=sys.stdout;sys.stdout=f
                try:a.main()
                finally:sys.stdout=oldout;a.plt.savefig=savefig
            metrics=json.loads((result/'metrics.json').read_text());mon=metrics['Gate_D_monitor_evaluation']
            assert not metrics['fatal_or_nan'] and metrics['normal_exit'],'canonical health disagreement'
            for key in ['metrics.json','convergence.csv','local_nusselt.csv','section_nusselt.csv','centreline_4097.csv']:
                shutil.copy2(result/key,seal/key)
            bools={'NORMAL_EXIT':h['normal_exit'],'NO_FATAL_OR_NAN':h['no_fatal_or_nan'] and ff['all_required_fields_finite'],'INPUT_PROVENANCE_PASS':True,'QOI_RWIN_PASS':mon['qoi_rwin_pass'],'RESIDUAL_PASS':mon['residual_pass'],'HEAT_TREND_PASS':mon['heat_trend_pass']}
            accepted=all(bools.values());fail=[k for k,v in bools.items() if not v]
            gd={'status':'PASS' if accepted else 'FAIL','booleans':bools,'failure_components':fail,'computed':True,'accepted':accepted,'numerical_evaluation':mon,'formal_criteria_unchanged':True}
            dump(seal/'gate_D_status.json',gd)
            dump(seal/'segment_manifest.json',dict(raw_manifest,Gate_D=gd,plot_output_routing='Canonical main and source unchanged; savefig output redirected to new case/figures for fine only; historical figures never overwritten.'))
            dump(seal/'sealed_sha256.json',{str(p.relative_to(seal)):sha(p) for p in seal.rglob('*') if p.is_file()})
            for p,v in json.loads((seal/'sealed_sha256.json').read_text()).items():assert sha(seal/p)==v
            row.update(computed=True,accepted=accepted,final_iteration=N,Gate_D=gd['status'],Gate_D_failure_components=fail,status='ACCEPTED' if accepted else ('CONVERGENCE_NOT_REACHED' if N==30000 else 'CONTINUATION_REQUIRED'))
            row['segments'].append({'end_iteration':N,'path':str(seal.relative_to(ROOT)),'Gate_D':gd['status'],'failure_components':fail,'sealed_sha256_manifest':sha(seal/'sealed_sha256.json')})
            dump(result/'case_status.json',row);dump(OUT/'execution_state.json',STATE)
            print(cid,N,gd['status'],fail,'SEALED',flush=True)
            guard()
            if accepted or N==30000:break
            start=N
            changed=re.sub(r'(?m)^startFrom\s+\S+;', 'startFrom latestTime;',control)
            changed=re.sub(r'(?m)^endTime\s+\S+;',f'endTime {N+3000};',changed)
            (case/'system/controlDict').write_text(changed)
    STATE['overall']='COMPLETE'
except Exception as exc:
    STATE['overall']='STOPPED';STATE['stop_reason']=str(exc);STATE['traceback']=traceback.format_exc()
    print('BATCH STOP:',str(exc),flush=True)
finally:
    STATE['finished']=datetime.now().astimezone().isoformat();dump(OUT/'execution_state.json',STATE)
    try:guard();dump(OUT/'protected_after_check.json',{'status':'PASS','count':len(PROTECTED),'sha256':PROTECTED})
    except Exception as exc:dump(OUT/'protected_after_check.json',{'status':'FAIL','reason':str(exc)})
print('ATTEMPT OVERALL:',STATE['overall'],flush=True)
