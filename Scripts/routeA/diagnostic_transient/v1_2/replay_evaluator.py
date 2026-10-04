"""Fail-closed replay of lossless-enough, atomic native stage records; no CFD."""
import argparse, hashlib, json, math
from pathlib import Path

class EvaluatorFailure(ValueError):pass
def require(condition, message):
    if not condition:raise EvaluatorFailure('EVALUATOR_FAILURE: '+message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):
    # Match C++ std::setprecision(17) JSON, including signed zero. Numbers in
    # this schema are IEEE doubles or exact32-bit native labels, not arbitrary ints.
    if x is None:return 'null'
    if isinstance(x,bool):return 'true' if x else 'false'
    if isinstance(x,str):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
    if isinstance(x,(int,float)):
        require(math.isfinite(x),'NONFINITE_PAYLOAD')
        if x==0 and isinstance(x,float) and math.copysign(1,x)<0:return '-0.0'
        return format(x,'.17g')
    if isinstance(x,(list,tuple)):return '['+','.join(map(canonical,x))+']'
    return '{'+','.join(canonical(k)+':'+canonical(v) for k,v in sorted(x.items()))+'}'
def identity(x,key):return sha(canonical({k:v for k,v in x.items() if k!=key}).encode())
MASS=[1,0,-1,0,0,0,0];ENERGY=[1,2,-3,0,0,0,0]

def finite_tree(x):
    if isinstance(x,float):require(math.isfinite(x),'NONFINITE_PAYLOAD')
    elif isinstance(x,list):
        for y in x:finite_tree(y)
    elif isinstance(x,dict):
        for y in x.values():finite_tree(y)

def field(f,time_index):
    require(f['value_sha256']==identity(f,'value_sha256'),'FIELD_EPOCH_HASH')
    require(f['n_materialized_old_times']>=len(f['old_times']),'OLDTIME_COUNT')
    require(f['time_index']<=time_index,'FIELD_TIME_INDEX')
    last=f['time_index']
    for old in f['old_times']:
        require(old['value_sha256']==sha(canonical({k:old[k] for k in ['name','dimensions','cells','patches','history_level']}).encode()),'OLDTIME_VALUE_HASH')
        require(old['object_epoch_sha256']==identity(old,'object_epoch_sha256'),'OLDTIME_OBJECT_EPOCH')
        require(old['time_index']<=time_index,'OLDTIME_STORAGE_CLOCK')
        require(old['history_level']==f['old_times'].index(old)+1,'OLDTIME_LEVEL')
        if old['represented_time_index'] is not None:require(old['represented_time_index']==time_index-old['history_level'],'OLDTIME_REPRESENTED_EPOCH')
        require(old['dimensions']==f['dimensions'],'OLDTIME_DIMENSIONS')
        require(len(old['cells'])==len(f['cells']),'OLDTIME_SIZE')
        last=old['time_index']

def coefficient_key(m):
    keys=['has_diag','dimensions','psi_name','diag','source','has_upper','has_lower','upper','lower','owner','neighbour','patches']
    return {k:m[k] for k in keys}
def replay_matrix(m):
    require(m['matrix_epoch']==sha(canonical(coefficient_key(m)).encode()),'MATRIX_EPOCH_HASH')
    psi=m['psi']['cells'];n=len(psi)
    require(len(m['diag'])==len(m['source'])==len(m['volumes'])==n,'MATRIX_SIZE')
    require(all(v>0 for v in m['volumes']),'NONPOSITIVE_VOLUME')
    rows=[[m['diag'][i]*psi[i],-m['source'][i]] for i in range(n)]
    for owner,neighbour,upper,lower in zip(m['owner'],m['neighbour'],m['upper'],m['lower']):
        rows[owner].append(upper*psi[neighbour]);rows[neighbour].append(lower*psi[owner])
    if m['has_upper'] or m['has_lower']:
        require(len(m['owner'])==len(m['neighbour'])==len(m['upper'])==len(m['lower']),'MATRIX_ADDRESSING_SIZE')
    else:require(not m['upper'] and not m['lower'],'DIAGONAL_OFFDIAGONAL')
    require(len(m['patches'])==len(m['psi']['patches']),'MATRIX_PATCH_COUNT')
    for p,fp in zip(m['patches'],m['psi']['patches']):
        require(p['name']==fp['name'] and p['type']==fp['type'],'BC_PATCH_IDENTITY')
        require(len(p['face_cells'])==len(p['internal_coeffs'])==len(p['boundary_coeffs']),'BC_SIZE')
        for c,ic,bc in zip(p['face_cells'],p['internal_coeffs'],p['boundary_coeffs']):rows[c].extend([ic*psi[c],-bc])
    action=[math.fsum(r) for r in rows]
    require(len(m['native_lhs_minus_rhs'])==n,'RESIDUAL_SIZE')
    defect=max(abs(a-b) for a,b in zip(action,m['native_lhs_minus_rhs']))
    # Captured stored-matrix arithmetic bound plus replay arithmetic allowance;
    # do not use an arbitrary dimensionless tolerance or multiply V again.
    floor=m['arithmetic_bound']+32*math.ulp(1.0)*math.fsum(abs(v) for row in rows for v in row)
    require(defect<=floor,'MATRIX_REPLAY_IDENTITY')
    return action,defect,floor

class StageLedger:
    """Exact native graph for frozen24outer/2pressure/0additional nonorthogonal."""
    def __init__(self):
        self.phase='initial';self.outer=self.pressure=self.energy=self.rho=self.nonorth=0
        self.time=None;self.last_time=None;self.sequence=0;self.terms=set();self.epochs={};self.before_relax=None
    def accept(self,r):
        m=r['metadata'];stage=m['stage'];self.sequence+=1
        require(r['sequence']==self.sequence,'SEQUENCE_DUPLICATE_MISSING_REORDERED')
        for key in ['time_index','outer','pressure','nonOrthogonal','energy_solve','rho_solve']:
            require(type(m[key]) is int and m[key]>=0,'INVALID_COUNTER')
        require(m['deltaT']>0,'TIME_STEP')
        startup=stage in {'constructor_complete','preSolve_before','preSolve_after','controller_complete'}
        require(m['previous_deltaT']>=0 if startup else m['previous_deltaT']>0,'TIME_HISTORY')
        if stage=='time_start':
            require(self.last_time is None or m['time_index']>self.last_time,'TIME_INDEX_NOT_ADVANCING')
            self.last_time=m['time_index'];self.time=m['time_index'];self.outer=self.pressure=self.nonorth=self.energy=self.rho=0;self.epochs={}
        if stage=='outer_start':self.outer+=1;self.pressure=self.nonorth=0
        if stage=='pressure_start':self.pressure+=1;self.nonorth=0
        if stage=='pressure_pre_reference':self.nonorth+=1
        if stage=='energy_begin':self.energy+=1;self.terms=set()
        if stage=='before_correctDensity':self.rho+=1;self.terms=set()
        require((m['outer'],m['pressure'],m['nonOrthogonal'],m['energy_solve'],m['rho_solve'])==(self.outer,self.pressure,self.nonorth,self.energy,self.rho),'WRONG_CORRECTOR_INDEX')
        if self.time is not None and stage not in ['preSolve_before','preSolve_after','controller_complete']:
            require(m['time_index']==self.time,'WRONG_TIME_INDEX')
        if stage=='term_capture':
            require(self.phase in ['energy_begin','before_correctDensity'],'TERM_OUTSIDE_ASSEMBLY')
            term=r['payload']['term'];require(term not in self.terms,'DUPLICATE_TERM');self.terms.add(term);return
        edges={
            'initial':{'constructor_complete'},'constructor_complete':{'preSolve_before'},'time_end':{'preSolve_before','auxiliary_fixture'},
            'preSolve_before':{'preSolve_after'},'preSolve_after':{'controller_complete'},'controller_complete':{'time_start'},
            'time_start':{'outer_start'},'outer_start':{'before_correctDensity'} if self.outer==1 else {'density_predictor_complete'},
            'before_correctDensity':{'mass_unrelaxed_assembly'},'mass_unrelaxed_assembly':{'mass_after_solve'},'mass_after_solve':{'after_correctDensity'},
            'after_correctDensity':{'density_predictor_complete'} if self.pressure==0 else {'native_continuity_report'},
            'density_predictor_complete':{'energy_begin'},'energy_begin':{'energy_unrelaxed_assembly'},'energy_unrelaxed_assembly':{'energy_after_relax'},
            'energy_after_relax':{'energy_after_solve'},'energy_after_solve':{'before_thermo_correct'},'before_thermo_correct':{'after_thermo_correct'},
            'after_thermo_correct':{'pressure_start'},'pressure_start':{'before_pressure_EOS_copy'},'before_pressure_EOS_copy':{'after_pressure_EOS_copy'},
            'after_pressure_EOS_copy':{'pressure_pre_reference'},'pressure_pre_reference':{'pressure_post_reference'},'pressure_post_reference':{'pressure_solved'},
            'pressure_solved':{'before_correctDensity'},'native_continuity_report':{'pressure_start'} if self.pressure==2 and stage=='pressure_start' else {'outer_end'},
            'outer_end':{'outer_start'} if stage=='outer_start' and self.outer<=24 else {'before_postSolve'},
            'before_postSolve':{'before_postSolve_EOS_copy'},'before_postSolve_EOS_copy':{'after_postSolve_EOS_copy'},'after_postSolve_EOS_copy':{'after_postSolve'},'after_postSolve':{'time_end'}}
        require(stage in edges.get(self.phase,set()),'EVALUATOR_STAGE_IDENTITY_FAILURE: '+self.phase+' -> '+stage)
        if stage=='outer_start':require(self.outer<=24,'TOO_MANY_OUTERS')
        if stage=='pressure_start':require(self.pressure<=2,'TOO_MANY_PRESSURES')
        if stage=='pressure_pre_reference':require(self.nonorth==1,'NONORTH_INDEX')
        if stage=='before_postSolve':require(self.outer==24,'OUTER_COUNT_INCOMPLETE')
        if stage=='time_end':require((self.outer,self.pressure,self.energy,self.rho)==(24,2,24,49),'SOLVE_COUNTS_INCOMPLETE')
        if stage=='energy_unrelaxed_assembly':require(self.terms=={'S_e','F_e','S_K','F_K','W_p','H_out','Fourier_laplacian','Fourier_correction','W_g','S_models'},'ENERGY_TERM_SET')
        if stage=='mass_unrelaxed_assembly':require(self.terms=={'D_B_rho','div_phi','mass_models'},'MASS_TERM_SET')
        self.phase=stage if stage!='auxiliary_fixture' else 'time_end'
    def finish(self):require(self.phase=='time_end','INCOMPLETE_FINAL_STAGE')

def replay(root,guard,source,instrument):
    root=Path(root);done=json.loads((root/'complete.json').read_text());raw=(root/'manifest.jsonl').read_bytes()
    require(done['complete'] and done['manifest_sha256']==sha(raw),'INCOMPLETE_MANIFEST')
    lines=raw.splitlines();require(len(lines)==done['records'],'MANIFEST_RECORD_COUNT')
    expected={'manifest.jsonl','complete.json'}|{json.loads(line)['file'] for line in lines}
    require({p.name for p in root.iterdir()}==expected,'PARTIAL_OR_ORPHAN_PACKET')
    ledger=StageLedger();matrices=0;max_defect=0.;max_floor=0.;energy_checks=mass_checks=reference_checks=sync_checks=polynomial_checks=isolated_checks=0
    energy_before=None;term_packets={};pressure_before=None;pressure_after=None;pre_sync=None;events=[];assembly_epoch=None;stream_identity=None;last_energy=None;last_mass=None;synchronization=[]
    for line in lines:
        commit=json.loads(line);require(commit['sequence']==len(events)+1 and commit['file']==f'{len(events)+1:08}.json','MANIFEST_SEQUENCE_IDENTITY');data=(root/commit['file']).read_bytes();require(sha(data)==commit['sha256'],'FILE_SHA256')
        r=json.loads(data);finite_tree(r);m=r['metadata'];p=r['payload'];stage=m['stage']
        require(m['schema']=='routeA_native_stage/1.2','SCHEMA')
        current_identity=(m['case_identity'],m['classification'])
        require(stream_identity is None or current_identity==stream_identity,'CASE_OR_CLASSIFICATION_CHANGED')
        stream_identity=current_identity
        require(m['classification'] in {'SYNTHETIC_EVALUATOR_TEST','DIAGNOSTIC_OBSERVATION'},'CLASSIFICATION')
        require((m['study_guard_sha256'],m['source_set_sha256'],m['instrumentation_sha256'])==(guard,source,instrument),'WRONG_AUTHORITY_HASH')
        require(sha(canonical(p).encode())==r['payload_sha256'],'PAYLOAD_SHA256')
        ledger.accept(r);events.append((m['time_index'],m['outer'],m['pressure'],stage))
        state=p['native_state_epoch']
        require(m['field_epochs']=={name:f['value_sha256'] for name,f in state.items() if isinstance(f,dict) and 'value_sha256' in f},'FIELD_METADATA_EPOCH')
        require(m['oldTime_ids']=={name:[{'object_name':old['name'],'time_index':old['time_index'],'value_sha256':old['value_sha256'],'object_epoch_sha256':old['object_epoch_sha256'],'history_level':old['history_level'],'represented_time_index':old['represented_time_index']} for old in f['old_times']] for name,f in state.items() if isinstance(f,dict) and 'old_times' in f},'OLDTIME_METADATA_EPOCH')
        require(m['bc_epochs']=={name:sha(canonical(f['patches']).encode()) for name,f in state.items() if isinstance(f,dict) and 'patches' in f},'BC_METADATA_EPOCH')
        require(m['matrix_epochs']=={name:f['matrix_epoch'] for name,f in p.items() if isinstance(f,dict) and 'matrix_epoch' in f},'MATRIX_METADATA_EPOCH')
        if state:
            require(state['state_epoch']==identity(state,'state_epoch'),'STATE_EPOCH')
            for f in state.values():
                if isinstance(f,dict) and 'old_times' in f:
                    field(f,m['time_index'])
                    if f['has_stored_old_times']:
                        for level,old in enumerate(f['old_times']):
                            key=(f['name'],level)
                            epoch=(old['history_level'],old['value_sha256'])
                            require(key not in ledger.epochs or ledger.epochs[key]==epoch,'OLDTIME_CHANGED_WITHIN_STEP')
                            ledger.epochs[key]=epoch
        for key in ['matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix']:
            if key in p:
                packet=p[key];field(packet['psi'],m['time_index']);action,defect,floor=replay_matrix(packet);matrices+=1;max_defect=max(max_defect,defect);max_floor=max(max_floor,floor)
                require(packet['dimensions']==(ENERGY if stage.startswith('energy') else MASS if stage.startswith('mass') or stage.startswith('pressure') else packet['dimensions']),'WRONG_MATRIX_UNITS')
        if stage in ['energy_begin','before_correctDensity']:term_packets={}
        if stage=='term_capture':
            term=p['term'];term_packets[term]=p
            dims=p['matrix']['dimensions'] if 'matrix' in p else p['dimensions']
            require(dims==(MASS if term in {'D_B_rho','div_phi','mass_models'} else ENERGY),'WRONG_TERM_DIMENSIONS')
        if stage in ['energy_unrelaxed_assembly','mass_unrelaxed_assembly']:assembly_epoch=p['matrix']['matrix_epoch']
        if stage=='energy_unrelaxed_assembly':
            energy_before=p['matrix']['matrix_epoch'];last_energy={'assembly':p,'terms':dict(term_packets)}
        if stage=='mass_unrelaxed_assembly':last_mass={'assembly':p,'terms':dict(term_packets)}
        if stage=='energy_after_relax':require(p['matrix']['matrix_epoch']==energy_before,'REGISTERED_NO_RELAX_VIOLATED')
        if stage in ['energy_after_solve','mass_after_solve']:
            if stage=='energy_after_solve':last_energy['solved']=p
            packet=p['unrelaxed_matrix'];require(packet['matrix_epoch']==assembly_epoch,'WRONG_ASSEMBLY_MATRIX_IDENTITY');require(packet['psi']['value_sha256']==state[packet['psi_name']]['value_sha256'],'SOLVED_PSI_FIELD_EPOCH');a,_,floor=replay_matrix(packet);actions=p['term_actions'];n=len(a)
            expected_names={'S_e','F_e','S_K','F_K','W_p','H_out','Fourier_laplacian','Fourier_correction','W_g','S_models'} if stage.startswith('energy') else {'D_B_rho','div_phi','mass_models'}
            require(set(actions)==expected_names,'SOLVED_TERM_SET')
            for term,tp in term_packets.items():
                if 'matrix' in tp:
                    frozen=tp['matrix'];require(frozen['psi_name']==packet['psi_name'],'TERM_PSI_IDENTITY')
                    updated=dict(frozen);updated['psi']=packet['psi']
                    # Native action recorded earlier is assembly-time; recompute
                    # at current solved psi using frozen coefficients.
                    replayed=matrix_action(updated)
                    allowance=32*math.ulp(1.0)*sum(abs(v) for v in replayed)+packet['arithmetic_bound']+frozen['arithmetic_bound']
                    require(max(abs(x-y) for x,y in zip(replayed,actions[term]))<=allowance,'FROZEN_TERM_REPLAY')
                else:require(tp['integrated_cells']==actions[term],'EXPLICIT_TERM_CHANGED')
            if stage.startswith('energy'):
                term_sum=[math.fsum([actions[k][i] for k in ['S_e','F_e','S_K','F_K','W_p','H_out']]+[-actions['W_g'][i],-actions['S_models'][i]]) for i in range(n)]
                heat=[-actions['Fourier_laplacian'][i]-actions['Fourier_correction'][i] for i in range(n)]
                require(max(abs(x-y) for x,y in zip(heat,actions['H_out']))<=floor+term_allowance(actions),'FOURIER_TERM_IDENTITY');energy_checks+=1
            else:
                term_sum=[math.fsum([actions['D_B_rho'][i],actions['div_phi'][i],-actions['mass_models'][i]]) for i in range(n)]
                flux=p['state']['phi'];boundary=math.fsum(v for patch in flux['patches'] for v in patch['values'])
                require(abs(math.fsum(actions['div_phi'])-boundary)<=term_allowance(actions),'MASS_INTERNAL_FLUX_CANCELLATION');mass_checks+=1
            require(max(abs(x-y) for x,y in zip(a,term_sum))<=floor+term_allowance(actions),'TOTAL_TERM_SUM')
        if stage=='auxiliary_fixture':
            action,defect,floor=replay_matrix(p['matrix']);matrices+=1
            if 'polynomial_degree' in p:
                require(abs(math.fsum(action)-p['expected_integrated_derivative'])<=floor+32*math.ulp(1.)*abs(p['expected_integrated_derivative']),'VARIABLE_STEP_POLYNOMIAL_DERIVATIVE')
                polynomial_checks+=1
            else:
                require(p['matrix']['dimensions']==ENERGY,'ISOLATED_ENERGY_UNIT')
                require(max(abs(a-b) for a,b in zip(action,p['expected_integrated_cells']))<=floor+32*math.ulp(1.)*sum(abs(v) for v in p['expected_integrated_cells']),'ISOLATED_ENERGY_IDENTITY')
                isolated_checks+=1
        if stage=='pressure_pre_reference':pressure_before=p['matrix']
        if stage=='pressure_post_reference':
            b=pressure_before;a=p['matrix'];pressure_after=a;cell=p['ref_cell'];value=p['ref_value']
            for i in range(len(a['diag'])):
                require(a['diag'][i]==b['diag'][i]*(2 if i==cell else 1),'REFERENCE_DIAGONAL')
                require(a['source'][i]==b['source'][i]+(b['diag'][i]*value if i==cell else 0),'REFERENCE_SOURCE')
            for key in ['upper','lower','patches']:require(a[key]==b[key],'REFERENCE_OTHER_COEFFICIENT_CHANGED')
            reference_checks+=1
        if stage=='pressure_solved':
            require(p['physical_matrix']['matrix_epoch']==pressure_before['matrix_epoch'],'PRESSURE_PHYSICAL_MATRIX_EPOCH')
            require(p['referenced_matrix']['matrix_epoch']==pressure_after['matrix_epoch'],'PRESSURE_REFERENCED_MATRIX_EPOCH')
        if stage=='before_postSolve_EOS_copy':pre_sync=p
        if stage=='after_postSolve_EOS_copy':
            before=pre_sync;after=p;v=before['volumes'];rhoC=before['rho']['cells'];rhoEnd=after['rho']['cells'];rhoT=after['rhoFluidThermo:rho']['cells']
            require(rhoEnd==rhoT,'POSTSOLVE_EOS_COPY')
            require(before['phi']==after['phi'],'SYNC_PHI_CHANGED')
            require(before['rho']['old_times']==after['rho']['old_times'],'SYNC_OLDTIME_CHANGED')
            mass_jump=math.fsum(vv*(r2-r1) for vv,r1,r2 in zip(v,rhoC,rhoEnd))
            # Native storage coefficient inferred from captured mass operator,
            # preserving effective startup vsBDF history instead of guessing.
            h=m['deltaT'];k=m['previous_deltaT'];a=1+h/(h+k)
            db_before=storage_mass(before,h,k);db_after=storage_mass(after,h,k)
            bound=64*math.ulp(1.0)*(storage_magnitude(before,h,k)+storage_magnitude(after,h,k)+abs(a*mass_jump/h))
            require(abs((db_after-db_before)-a*mass_jump/h)<=bound,'RHO_SYNC_STORAGE_IDENTITY')
            for pp,pr,r1,r2,gg in zip(after['p']['cells'],after['p_rgh']['cells'],rhoC,rhoEnd,after['gh']['cells']):
                require(abs((pp-pr-r2*gg)-(r1-r2)*gg)<=64*math.ulp(1.0)*(abs(pp)+abs(pr)+abs(r1*gg)+abs(r2*gg)),'PRESSURE_RELATION_DEFECT')
            require(last_mass is not None and last_energy is not None,'END_MISSING_ASSEMBLY')
            end_mass=mass_end(last_mass,after)
            end_energy=energy_end(last_energy,after,m)
            synchronization.append({'time_index':m['time_index'],'M_before_postSolve':math.fsum(x*y for x,y in zip(v,rhoC)),
                'M_after_postSolve':math.fsum(x*y for x,y in zip(v,rhoEnd)),'deltaM_postSolve':mass_jump,
                'rho_s_minus_rho_T_before':[x-y for x,y in zip(rhoC,before['rhoFluidThermo:rho']['cells'])],
                'rho_s_minus_rho_T_after':[x-y for x,y in zip(rhoEnd,rhoT)],
                'mass_C':norms([x+y for x,y in zip(matrix_action(dict(last_mass['terms']['D_B_rho']['matrix'],psi=before['rho'])),last_mass['terms']['div_phi']['integrated_cells'])],v),'mass_end':norms(end_mass,v),
                'mass_sync_storage_change':a*mass_jump/h,
                'energy_assembly':norms(last_energy['solved']['unrelaxed_matrix']['native_lhs_minus_rhs'],v),'energy_end':norms(end_energy['total'],v),'energy_end_terms':end_energy['terms'],
                'pressure_relation_defect':[pp-pr-rr*gg for pp,pr,rr,gg in zip(after['p']['cells'],after['p_rgh']['cells'],rhoEnd,after['gh']['cells'])],
                'end_evaluation':'OFFLINE_REGISTERED_CONSTANT_PROPERTY_GOVERNING_STATE; no additional native assembly; separate from frozen assembly residual'})
            sync_checks+=1
    ledger.finish()
    return {'status':'PASS','records':len(lines),'matrix_replays':matrices,'max_matrix_replay_defect':max_defect,'max_stored_arithmetic_allowance':max_floor,'mass_term_identities':mass_checks,'energy_term_identities':energy_checks,'reference_identities':reference_checks,'rho_sync_identities':sync_checks,'variable_step_polynomial_checks':polynomial_checks,'isolated_energy_checks':isolated_checks,'synchronization':synchronization,'stage_sequence_sha256':sha(canonical(events).encode()),'classification':stream_identity[1],'floor_scope':'SYNTHETIC_ONLY'}


def norms(integrated,volumes):
    require(len(integrated)==len(volumes) and all(v>0 for v in volumes),'NORM_VOLUME_SIZE')
    return {'signed_global':math.fsum(integrated),'absolute_global':math.fsum(abs(x) for x in integrated),'local_volume_L1':math.fsum(abs(x) for x in integrated)/math.fsum(volumes),'local_Linf':max(abs(x)/v for x,v in zip(integrated,volumes))}
def mass_end(saved,state):
    matrix=dict(saved['terms']['D_B_rho']['matrix']);matrix['psi']=state['rho']
    # Frozen native D_B coefficient/source + unchanged final pressure-corrected
    # phi: coefficients depend on time and static V, not on current rho.
    require(saved['assembly']['state']['phi']==state['phi'],'END_MASS_FLUX_EPOCH')
    db=matrix_action(matrix);div=saved['terms']['div_phi']['integrated_cells']
    return [math.fsum([x,y]) for x,y in zip(db,div)]
def linear_div(state,values,boundary):
    g=state['geometry'];flux=state['phi'];rows=[[] for _ in values]
    require(len(g['neighbour'])==len(g['linear_weights'])==len(flux['internal']),'END_GEOMETRY_SIZE')
    for o,n,w,phi in zip(g['owner'],g['neighbour'],g['linear_weights'],flux['internal']):
        q=phi*(w*values[o]+(1-w)*values[n]);rows[o].append(q);rows[n].append(-q)
    for p,b in zip(flux['patches'],boundary):
        require(len(p['face_cells'])==len(p['values'])==len(b),'END_BOUNDARY_SIZE')
        for c,phi,x in zip(p['face_cells'],p['values'],b):rows[c].append(phi*x)
    return [math.fsum(row) for row in rows]
def energy_end(saved,state,metadata):
    # Constant Cv,kappa,static mesh/Gauss linear are frozen v1.1 model/schemes.
    # Reconstruct algebra from actual coefficients/addressing/old products;
    # never execute a second native ddt/div/laplacian or update a boundary.
    assembly=saved['assembly'];terms=dict(saved['terms']);base=assembly['state'];context=assembly['thermal_context']
    require(base['geometry']==state['geometry'] and base['volumes']==state['volumes'],'END_STATIC_GEOMETRY')
    require('Cv' in context and 'g' in context,'END_THERMAL_CONTEXT_MISSING')
    cv=context['Cv'];require(all(c>0 and c==cv[0] for c in cv),'END_CONSTANT_CV')
    for name in ['rho','e','K']:
        require([x['value_sha256'] for x in base[name]['old_times']]==[x['value_sha256'] for x in state[name]['old_times']],'END_OLD_HISTORY_EPOCH')
    for ta,te,ea,ee,c in zip(base['T']['cells'],state['T']['cells'],base['e']['cells'],state['e']['cells'],cv):
        require(abs((te-ta)-(ee-ea)/c)<=64*math.ulp(1.)*(abs(te)+abs(ta)+abs(ee/c)+abs(ea/c)),'END_THERMAL_AFFINE_REFERENCE')
    for name in ['T','e']:
        require([{k:p[k] for k in ['name','type','values']} for p in base[name]['patches']]==[{k:p[k] for k in ['name','type','values']} for p in state[name]['patches']],'END_THERMAL_BOUNDARY_EPOCH')
    se=dict(terms['S_e']['matrix']);se['diag']=[d*r2/r1 for d,r1,r2 in zip(se['diag'],base['rho']['cells'],state['rho']['cells'])];se['psi']=state['e']
    h=metadata['deltaT'];k=terms['S_K']['effective_previous_deltaT'];a=1+h/(h+k);c=h*h/(k*(h+k));b=a+c
    oldrho=state['rho']['old_times'];oldK=state['K']['old_times'];v=state['volumes']
    sk=[vv*math.fsum([a*r*kk,-b*r0*k0,c*r00*k00])/h for vv,r,kk,r0,k0,r00,k00 in zip(v,state['rho']['cells'],state['K']['cells'],oldrho[0]['cells'],oldK[0]['cells'],oldrho[1]['cells'],oldK[1]['cells'])]
    rho=state['rho']['cells'];require(all(r!=0 for r in rho),'END_ZERO_RHO')
    e=state['e'];K=state['K'];p=state['p'];rhob=[x['values'] for x in state['rho']['patches']]
    wpb=[[x/y for x,y in zip(pp['values'],rr)] for pp,rr in zip(p['patches'],rhob)]
    heat=dict(terms['Fourier_correction']['matrix']);heat['psi']=e
    heat_action=matrix_action(heat)
    result={'S_e':matrix_action(se),'S_K':sk,
        'F_e':linear_div(state,e['cells'],[x['values'] for x in e['patches']]),
        'F_K':linear_div(state,K['cells'],[x['values'] for x in K['patches']]),
        'W_p':linear_div(state,[x/y for x,y in zip(p['cells'],rho)],wpb),
        'H_out':[-x-y for x,y in zip(terms['Fourier_laplacian']['integrated_cells'],heat_action)],
        'W_g':[vv*r*math.fsum(x*y for x,y in zip(u,context['g'])) for vv,r,u in zip(v,rho,state['U']['cells'])],
        'S_models':[0.]*len(v)}
    total=[math.fsum([result[k][i] for k in ['S_e','S_K','F_e','F_K','W_p','H_out']]+[-result['W_g'][i],-result['S_models'][i]]) for i in range(len(v))]
    return {'total':total,'terms':result}

def matrix_action(m):
    # Residual replay without comparing to pre-solve native action.
    psi=m['psi']['cells'];rows=[[d*x-s] for d,x,s in zip(m['diag'],psi,m['source'])]
    for o,n,u,l in zip(m['owner'],m['neighbour'],m['upper'],m['lower']):rows[o].append(u*psi[n]);rows[n].append(l*psi[o])
    for p in m['patches']:
        for c,ic,bc in zip(p['face_cells'],p['internal_coeffs'],p['boundary_coeffs']):rows[c].extend([ic*psi[c],-bc])
    return [math.fsum(row) for row in rows]
def term_allowance(actions):return 128*math.ulp(1.0)*math.fsum(abs(v) for vals in actions.values() for v in vals)
def storage_magnitude(state,h,k):
    f=state['rho'];a=1+h/(h+k);c=h*h/(k*(h+k));b=a+c
    return math.fsum(abs(v)*math.fsum([abs(a*r),abs(b*old),abs(c*older)])/h for v,r,old,older in zip(state['volumes'],f['cells'],f['old_times'][0]['cells'],f['old_times'][1]['cells']))
def storage_mass(state,h,k):
    f=state['rho'];a=1+h/(h+k);c=h*h/(k*(h+k));b=a+c
    return math.fsum(v*(a*r-b*old+c*older)/h for v,r,old,older in zip(state['volumes'],f['cells'],f['old_times'][0]['cells'],f['old_times'][1]['cells']))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('guard');ap.add_argument('source');ap.add_argument('instrument');a=ap.parse_args()
    try:print(json.dumps(replay(a.root,a.guard,a.source,a.instrument),indent=2))
    except (EvaluatorFailure,OSError,KeyError,ValueError) as exc:raise SystemExit('EVALUATOR_FAILURE: '+str(exc))
