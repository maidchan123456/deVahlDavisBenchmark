import importlib.util,contextlib,ast,hashlib,json,os,re,shutil,subprocess,sys,time,traceback
from datetime import datetime
from pathlib import Path
from decimal import Decimal
import numpy as np
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'Scripts/routeA'))
import analyze_case as a
from foam_fields import read_scalar,read_vector,latest_time,_named_block
C=json.loads((ROOT/'docs/routeA_execution_contract_v1.7.json').read_text())
CH='fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'
OUT=ROOT/'results/routeA/attempts/attempt_008'
PROTECTED=json.loads(Path('/tmp/gate_h_attempt008_protected.json').read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)

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
    T=read_scalar(folder/'T',n);rho=read_scalar(folder/'rho',n);eos=1*(1-.0001*(T-300))
    return {'all_required_fields_finite':True,'rho_positive':True,'field_ranges':ranges,'max_relative_density_deviation':float(np.max(np.abs(rho/1.-1.))),'EOS_proxy_max_absolute_difference':float(np.max(np.abs(rho-eos))),'EOS_proxy_max_relative_difference':float(np.max(np.abs(rho-eos)/np.abs(eos))),'independent_thermo_rho_dump':'NOT_AVAILABLE','field_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}}

def guard():
    assert sha(ROOT/'docs/routeA_execution_contract_v1.7.json')==CH,'contract digest'
    for p,h in C['implementation_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in C['template_source']['unchanged_template_sha256'].items():assert sha(ROOT/p)==h,p
    for x in [C['iteration_caps_csv'],C['amendment'],C['amendment']['parent']]+C['amendment_chain']:assert sha(ROOT/x['path'])==x['sha256'],x
    for x in C['amendment_chain']:
        assert sha(ROOT/x['parent']['path'])==x['parent']['sha256']
    for x in [C['current_protected_evidence'],{'path':C['position_semantics_reassessment']['check_path'],'sha256':C['position_semantics_reassessment']['check_sha256']}]:assert sha(ROOT/x['path'])==x['sha256']
    for p,h in C['start_guard_hashes']['required_existing_artifacts'].items():assert sha(ROOT/p)==h,('start guard',p)
    baseline=C['Gate_H']['baseline'];sm=json.loads((ROOT/baseline['segment_path']/'segment_manifest.json').read_text())
    assert sm['Gate_D']['computed'] and sm['Gate_D']['accepted'] and sm['Gate_D']['status']=='PASS' and sm['end_iteration']==9000,'baseline status mismatch'
    assert C['Gate_H']['limitations']['all_Ra_Gate_F']=='FAIL' and C['Gate_H']['limitations']['all_Ra_needs_320']=='YES'
    for p,h in PROTECTED.items():
        assert sha(ROOT/p)==h,('protected',p)

def runtime_check(log,output):
    step=run([sys.executable,ROOT/'Scripts/routeA/runtime_provenance.py','--log',log,'--contract',ROOT/'docs/routeA_execution_contract_v1.7.json','--max-lines','120'],output)
    evidence=json.loads(Path(output).read_text())
    assert step['exit_code']==0 and evidence['status']=='PASS',('canonical runtime provenance failure',evidence)
    return evidence

assert not OUT.exists(),'unexpected attempt008 destination'
cid='A-H-Ra1e6-fine-beta1e-4'
for p in [ROOT/'cases/routeA'/cid,ROOT/'results/routeA/cases'/cid,ROOT/'results/routeA/initialization_check'/cid]:assert not p.exists(),('unexpected destination',p)
for p,h in PROTECTED.items():assert sha(ROOT/p)==h,('initial protected baseline',p)
guard()
OUT.mkdir(parents=True,exist_ok=True)
shutil.copy2(__file__,OUT/'execution_runner.py')
shutil.copy2('/tmp/gate_h_attempt008_start.json',OUT/'start_guard_verification.json')
dump(OUT/'protected_before_sha256.json',PROTECTED)
env={'WM_PROJECT':os.environ.get('WM_PROJECT'),'WM_PROJECT_VERSION':os.environ.get('WM_PROJECT_VERSION'),'WM_PROJECT_DIR':os.environ.get('WM_PROJECT_DIR'),'WM_OPTIONS':os.environ.get('WM_OPTIONS'),'foamRun':shutil.which('foamRun'),'host':os.uname().nodename,'started':datetime.now().astimezone().isoformat(),'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'contract_version':'1.7','contract_sha256':CH,'analyzer_sha256':C['implementation_sha256']['Scripts/routeA/analyze_case.py'],'runtime_checker_sha256':C['implementation_sha256']['Scripts/routeA/runtime_provenance.py'],'attempt':'008','primary_solver_concurrency':1}
assert env['WM_PROJECT']=='OpenFOAM' and env['WM_PROJECT_VERSION']=='13' and env['WM_PROJECT_DIR']=='/opt/openfoam13'
help_step=run(['foamRun','-help'],OUT/'log.foamRun.help')
help_text=(OUT/'log.foamRun.help').read_text()
assert help_step['exit_code']==0 and '13-441953dfbb42' in help_text and re.search(r'^Using:\s+OpenFOAM-13\b',help_text,re.M),'environment/build mismatch'
env['actual_build']='13-441953dfbb42'
dump(OUT/'environment.json',env)
STATE={'overall':'RUNNING','attempt':'008','cases':[],'environment':env,'stop_reason':None}
dump(OUT/'execution_state.json',STATE)
try:
    for grid,name in [(160,'fine')]:
        cid='A-H-Ra1e6-fine-beta1e-4';case=ROOT/'cases/routeA'/cid;result=ROOT/'results/routeA/cases'/cid;phase=OUT/'cases'/cid
        phase.mkdir(parents=True)
        row={'case_id':cid,'grid':[grid,grid,1],'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','Gate_D_failure_components':[],'segments':[],'status':'PREPARING','case_reused':False,'runtime_provenance':'NOT_EVALUATED','OQ02':'NOT_EVALUATED'}
        STATE['cases'].append(row);dump(OUT/'execution_state.json',STATE)
        guard()
        print(cid,'new case generation + mesh + initialization',flush=True)
        generator=ROOT/'Scripts/routeA/generate_case.py'
        spec=importlib.util.spec_from_file_location('gate_h_canonical_generator',generator)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.BETA=module.Decimal('1e-4')
        sys.argv=[str(generator),'--case-id','A-SMOKE','--name',cid,'--nx',str(grid),'--ny',str(grid),'--ra','1000000','--end-time','3000']
        with (phase/'log.generation').open('w') as stream,contextlib.redirect_stdout(stream):module.main()
        result.mkdir(parents=True)
        raw=case/'generated_manifest_original.json';shutil.copy2(case/'case_manifest.json',raw)
        rawhash=sha(raw);dump(phase/'raw_generator_manifest_seal.json',{'path':str(raw),'sha256':rawhash,'generator_sha256':sha(generator),'in_memory_BETA':'1e-4'})
        physical=case/'constant/physicalProperties';text=physical.read_text()
        count=text.count('beta 1e-3;');assert count==1,'STOP_GATE_H_BETA_OVERLAY_AMBIGUOUS'
        prehash=sha(physical);physical.write_text(text.replace('beta 1e-3;','beta 1e-4;'))
        overlay={'path':'constant/physicalProperties','count':count,'before_literal':'beta 1e-3;','after_literal':'beta 1e-4;','before_sha256':prehash,'after_sha256':sha(physical),'template_modified':False}
        dump(phase/'beta_overlay.json',overlay)
        m=json.loads((case/'case_manifest.json').read_text())
        m.update(case_id=cid,generator_role='A-SMOKE',attempt='008',contract_version='1.7',contract_sha256=CH,amendment007_sha256=C['amendment']['sha256'],generator_sha256=sha(generator),in_memory_BETA_override='1e-4',physicalProperties_overlay=overlay,raw_generated_manifest_sha256=rawhash,raw_generator_input_sha256=m['input_sha256'].copy(),baseline_field_copy=False,initialization_owner='NEW_CANONICAL_COLD_INITIALIZATION')
        m['input_sha256']=inputs(case,m)
        dump(case/'case_manifest.json',m);shutil.copy2(case/'case_manifest.json',phase/'final_input_manifest.json')
        assert m['properties']['beta_1_K']==.0001 and m['beta_DeltaT']==.0001 and m['properties']['DeltaT_K']==1.
        props=m['properties'];assert props['rho0_kg_m3']==1 and props['mu_Pa_s']==1e-5 and props['Cv_J_kgK']==1000 and props['Pr_input']==.71
        baseline=C['Gate_H']['baseline'];bp=baseline['reference_properties']
        for key,value in bp.items():
            if key!='beta_1_K':assert props[key]==value,('held property mismatch',key)
        assert abs(m['gmag_m_s2']/abs(baseline['gravity_m_s2'][1])-10)<1e-10
        assert read_scalar(case/'0/T',grid*grid).tolist()==[300.]* (grid*grid)
        assert not np.any(read_vector(case/'0/U',grid*grid))
        assert not np.any(read_scalar(case/'0/p_rgh',grid*grid)) and m['pRef_Pa']==0 and m['hRef_m']==0
        assert m['grid']==[grid,grid,1] and m['Ra_target']==1000000
        initial_hashes=inputs(case,m);assert initial_hashes==m['input_sha256'],'initial inputs'
        gy=Decimal(re.search(r'value\s*\(\s*0\s+([^\s]+)\s+0\s*\)',(case/'constant/g').read_text()).group(1))
        Ra=abs(gy)*Decimal('.0001')*Decimal('1')*Decimal('.1')**3/(Decimal('1e-5')*(Decimal('1e-5')/Decimal('.71')))
        props=m['properties'];Pr=props['nu0_m2_s']/props['alpha0_m2_s']
        assert abs(Ra/1000000-1)<=Decimal('1e-10') and abs(Pr/.71-1)<=1e-10
        substitutions={'__NX__':str(grid),'__NY__':str(grid),'__GY__':format(gy,'.17g'),'__PREFCELL__':str(m['pRefCell']),'__ENDTIME__':'3000'}
        for source,h in C['template_source']['unchanged_template_sha256'].items():
            rel=Path(source).relative_to('cases/routeA/template');expected=(ROOT/source).read_text()
            for key,value in substitutions.items():expected=expected.replace(key,value)
            if str(rel)=='constant/physicalProperties':expected=expected.replace('beta 1e-3;','beta 1e-4;')
            assert (case/rel).read_text()==expected,('template mismatch',rel)
        dump(phase/'pre_mesh_input_verification.json',{'status':'PASS','input_sha256':initial_hashes,'Ra_actual_from_g':str(Ra),'Pr_actual':Pr,'template_expansion':'PASS'})
        meshsteps=[]
        for binary,options in [('blockMesh',[]),('checkMesh',['-allGeometry','-allTopology'])]:
            step=run([binary,'-case',case]+options,case/('log.'+binary));meshsteps.append(step);assert step['exit_code']==0,step
        step=run([sys.executable,ROOT/'Scripts/routeA/prepare_initialization_check.py',case],phase/'log.prepare_initialization')
        assert step['exit_code']==0,step
        init=Path((phase/'log.prepare_initialization').read_text().strip())
        step=run(['foamRun','-case',init],init/'log.foamRun.initialization');ih=health(init/'log.foamRun.initialization',step['exit_code'])
        dump(phase/'initialization_execution.json',{'process':step,'health':ih})
        assert ih['normal_exit'] and ih['no_fatal_or_nan'],ih
        assert inputs(case,m)==initial_hashes,'primary initial input changed during isolated constructor check'
        meshtext=(case/'log.checkMesh').read_text();assert 'Mesh OK.' in meshtext and re.search(r'cells:\s*'+str(grid*grid)+r'\b',meshtext),'mesh check'
        boundary=(case/'constant/polyMesh/boundary').read_text();patches={}
        for patch,faces,kind,normal,area in [('hotWall',grid,'wall',[-1,0,0],.0001),('coldWall',grid,'wall',[1,0,0],.0001),('bottomWall',grid,'wall',[0,-1,0],.0001),('topWall',grid,'wall',[0,1,0],.0001),('front',grid*grid,'empty',[0,0,-1],.01),('back',grid*grid,'empty',[0,0,1],.01)]:
            block=_named_block(boundary,patch);assert re.search(r'\btype\s+'+kind+r'\s*;',block)
            assert int(re.search(r'nFaces\s+(\d+)',block).group(1))==faces
            patches[patch]={'type':kind,'nFaces':faces,'area_m2':area,'outward_normal':normal,'geometry_source':'generated uniform block vertices and validated patch topology'}
        for key,value in C['Gate_H']['baseline']['mesh_sha256'].items():assert sha(case/key)==value,('common-grid mesh hash mismatch',key)
        init_seal={str(p.relative_to(init)):sha(p) for p in init.rglob('*') if p.is_file()}
        dump(phase/'initialization_clone_sealed_sha256.json',init_seal)
        rp=runtime_check(init/'log.foamRun.initialization',phase/'runtime_provenance_initialization.json');row['runtime_provenance']='PASS'
        step=run([sys.executable,ROOT/'Scripts/routeA/verify_initialization.py',case,init,phase/'initialization_verification.json'],phase/'log.verify_initialization')
        oq=json.loads((phase/'initialization_verification.json').read_text())
        assert step['exit_code']==0 and oq['pass'],'OQ-02 failure';row['OQ02']='PASS'
        attempt_m=copy_m=dict(m);attempt_m.update(attempt='008',contract_version='1.7',contract_sha256=CH,runtime_checker_sha256=env['runtime_checker_sha256'],underlying_case_manifest_sha256=sha(case/'case_manifest.json'),case_reused_from_attempt_002=False)
        dump(phase/'attempt_case_manifest.json',attempt_m)
        gateA={'status':'PASS','Ra_actual_from_g_dictionary':str(Ra),'Pr_actual':Pr,'relative_tolerance':1e-10,'beta_actual':.0001,'g_actual_m_s2':str(gy),'DeltaT_actual':1,'grid_matches_baseline':True,'numerics_match_baseline':True,'generated_inputs_match':True,'input_sha256':initial_hashes,'mesh_processes':meshsteps,'mesh_sha256':{str(p.relative_to(case)):sha(p) for p in (case/'constant/polyMesh').iterdir() if p.is_file()},'patches':patches,'OQ_02':'PASS','initialization_verification_sha256':sha(phase/'initialization_verification.json'),'runtime_provenance':rp,'environment':env,'template_sha256':C['template_source']['unchanged_template_sha256']}
        dump(phase/'gate_A.json',gateA);dump(OUT/'execution_state.json',STATE)
        initial_control=(case/'system/controlDict').read_text();start=0
        for N in range(3000,30001,3000):
            guard();assert latest_time(case)[0]==start,('restart state',latest_time(case),start)
            if start:
                prior=result/'segments'/('end_'+str(start))
                for p,h in json.loads((prior/'sealed_sha256.json').read_text()).items():assert sha(prior/p)==h,('prior seal corruption',p)
                prior_m=json.loads((prior/'segment_manifest.json').read_text())
                for field,h in prior_m['final_field_validation']['field_sha256'].items():assert sha(case/str(start)/field)==h,('restart field mismatch',field)
            seal=result/'segments'/('end_'+str(N));assert not seal.exists();seal.mkdir(parents=True)
            for p,h in initial_hashes.items():
                if p!='system/controlDict':assert sha(case/p)==h,('input mutation',p)
            for p,h in gateA['mesh_sha256'].items():assert sha(case/p)==h,('mesh mutation',p)
            control=(case/'system/controlDict').read_text()
            normalized=re.sub(r'(?m)^startFrom\s+\S+;', 'startFrom startTime;',control)
            normalized=re.sub(r'(?m)^endTime\s+\S+;', 'endTime 3000;',normalized)
            assert normalized==initial_control,'unpermitted control change'
            print(cid,f'primary {start} -> {N}',flush=True)
            row['status']='RUNNING';dump(OUT/'execution_state.json',STATE)
            step=run(['foamRun','-case',case],case/('log.foamRun.segment_'+str(N)))
            log=Path(step['log']);h=health(log,step['exit_code']);dump(seal/'execution_health.json',{'process':step,'health':h})
            shutil.copy2(log,seal/'solver.log');shutil.copy2(case/'case_manifest.json',seal/'case_manifest.json');shutil.copy2(phase/'attempt_case_manifest.json',seal/'attempt_case_manifest.json');shutil.copy2(case/'system/controlDict',seal/'controlDict');shutil.copy2(phase/'gate_A.json',seal/'gate_A.json');shutil.copy2(phase/'initialization_verification.json',seal/'initialization_verification.json')
            for file in ['generated_manifest_original.json']:shutil.copy2(case/file,seal/file)
            for file in ['beta_overlay.json','raw_generator_manifest_seal.json','final_input_manifest.json']:shutil.copy2(phase/file,seal/file)
            assert h['normal_exit'] and h['no_fatal_or_nan'],('primary health failure',h)
            rp=runtime_check(seal/'solver.log',seal/'runtime_provenance.json')
            assert latest_time(case)[0]==N,'wrong final checkpoint'
            ff=finite_fields(case,N,grid*grid)
            raw_manifest={'attempt':'008','case_id':cid,'segment_start':start,'end_iteration':N,'contract_version':'1.7','contract_sha256':CH,'amendment007_sha256':C['amendment']['sha256'],'amendment_chain':C['amendment_chain'],'analyzer_sha256':env['analyzer_sha256'],'runtime_checker_sha256':env['runtime_checker_sha256'],'input_sha256':inputs(case,m),'mesh_sha256':gateA['mesh_sha256'],'controlDict_sha256':sha(case/'system/controlDict'),'permitted_control_diff':{} if start==0 else {'startFrom':{'initial':'startTime','current':'latestTime'},'endTime':{'initial':3000,'current':N}},'process':step,'health':h,'runtime_provenance':rp,'gate_A':'PASS','OQ_02':'PASS','final_field_validation':ff}
            wall=case/'postProcessing/wallHeatFluxMonitor'/str(start)/'wallHeatFlux.dat';shutil.copy2(wall,seal/'wallHeatFlux.dat')
            for t in range(N-190,N+1,10):shutil.copytree(case/'postProcessing/centrelineMonitor'/str(t),seal/'centrelineMonitor'/str(t))
            residuals=a.parse_residuals(seal/'solver.log');dump(seal/'residuals_initial_final.json',residuals)
            dump(seal/'raw_segment_manifest.json',raw_manifest)
            dump(seal/'raw_seal_sha256.json',{str(p.relative_to(seal)):sha(p) for p in seal.rglob('*') if p.is_file()})
            # Raw evidence sealed before canonical numerical evaluation.
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
            for key in a.POSITION_KEYS:
                payload=metrics['paper_comparison_like_for_like'][key]
                assert 'absolute_position_error' in payload and 'signed_position_difference' in payload and 'absolute_relative_error' not in payload and 'signed_relative_difference' not in payload,('position semantics mismatch',key)
            assert not metrics['fatal_or_nan'] and metrics['normal_exit'],'canonical health disagreement'
            for key in ['metrics.json','convergence.csv','local_nusselt.csv','section_nusselt.csv','centreline_4097.csv']:shutil.copy2(result/key,seal/key)
            bools={'NORMAL_EXIT':h['normal_exit'],'NO_FATAL_OR_NAN':h['no_fatal_or_nan'] and ff['all_required_fields_finite'],'INPUT_PROVENANCE_PASS':True,'QOI_RWIN_PASS':mon['qoi_rwin_pass'],'RESIDUAL_PASS':mon['residual_pass'],'HEAT_TREND_PASS':mon['heat_trend_pass']}
            accepted=all(bools.values());fail=[k for k,value in bools.items() if not value]
            gd={'status':'PASS' if accepted else 'FAIL','booleans':bools,'failure_components':fail,'computed':True,'accepted':accepted,'numerical_evaluation':mon,'formal_criteria_unchanged':True}
            dump(seal/'gate_D_status.json',gd)
            dump(seal/'segment_manifest.json',dict(raw_manifest,Gate_D=gd,diagnostic_field_sha256={field:sha(case/str(N)/field) for field in ['div(phi)','div(U)']},plot_output_routing='Canonical main/source unchanged; savefig redirected to new fine case/figures only; historical plots protected.'))
            if name=='fine':shutil.copytree(result/'figures',seal/'figures')
            dump(seal/'sealed_sha256.json',{str(p.relative_to(seal)):sha(p) for p in seal.rglob('*') if p.is_file()})
            for p,value in json.loads((seal/'sealed_sha256.json').read_text()).items():assert sha(seal/p)==value
            row.update(computed=True,accepted=accepted,final_iteration=N,Gate_D=gd['status'],Gate_D_failure_components=fail,status='ACCEPTED' if accepted else ('CONVERGENCE_NOT_REACHED' if N==30000 else 'CONTINUATION_REQUIRED'))
            row['segments'].append({'end_iteration':N,'path':str(seal.relative_to(ROOT)),'Gate_D':gd['status'],'failure_components':fail,'sealed_sha256_manifest':sha(seal/'sealed_sha256.json')})
            dump(phase/'case_status.json',row);dump(OUT/'execution_state.json',STATE)
            print(cid,N,gd['status'],fail,'SEALED',flush=True);guard()
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
    try:guard();dump(OUT/'protected_after_check.json',{'status':'PASS','count':len(PROTECTED),'sha256':PROTECTED,'allowed_exception':'None for pre-existing files. New Gate H primary startFrom/endTime only, normalized exact comparison before every segment.'})
    except Exception as exc:dump(OUT/'protected_after_check.json',{'status':'FAIL','reason':str(exc)})
print('ATTEMPT OVERALL:',STATE['overall'],flush=True)
