"""Native callback scalar/U01/U03 bindings. Frozen policy imported verbatim.
Only current native arrays and evaluator receipts are used; no saved field reads.
"""
import collections,json,math,sys
import numpy as np
from primary_evidence import primary,required_columns,policy
from online_evaluator import storage_mass
from packed import need,encode

class Arrival:
    def __init__(self,physical,contract):
        self.names=('Nu_bar_cavity','Umax','Wmax','rho_min','rho_max','rho_mean','total_mass','energy_storage')
        self.times=collections.deque();self.histories={k:collections.deque() for k in self.names};self.initial=None;self.next=5;self.confirmed=None
        self.scales=contract['steady_arrival']['mass_energy_rho_arrival_policy']['scales'];self.results=[]
    def add(self,row):
        t=row['dimensionless_time'];need(not self.times or t>self.times[-1],'ARRIVAL_TIME_ORDER')
        if self.initial is None:self.initial={k:row[k] for k in self.names};self.initial_time=t
        self.times.append(t)
        for k in self.names:self.histories[k].append(row[k])
        out=[]
        while self.next<=20 and t>=self.next*.1:
            end=self.next*.1
            # Initial baseline preserved independently of the bounded native window.
            times=[self.initial_time]+list(self.times) if self.times[0]>self.initial_time else list(self.times)
            histories={k:[self.initial[k]]+list(vs) if self.times[0]>self.initial_time else list(vs) for k,vs in self.histories.items()}
            ok,windows=policy.arrival_candidate(times,histories,end,self.scales,row['validity'])
            result={'endpoint':end,'candidate':bool(windows),'confirmed':ok,'windows':windows,'final_mean':{k:windows[-1][k]['mean'] for k in ('Nu_bar_cavity','Umax','Wmax')} if ok else None}
            out.append(result);self.results.append(result);self.next+=1
            if ok and self.confirmed is None:self.confirmed=result
        # Retain only the native nodes bracketing the last0.3 window. Full history
        # remains in R0 disk; retain initial baseline separately, no thinning there.
        cutoff=max(0.,min(self.next*.1,2.)-.3)
        while len(self.times)>2 and self.times[1]<cutoff:
            self.times.popleft()
            for k in self.names:self.histories[k].popleft()
        return out

class Live:
    def __init__(self,writer,contract,strict=True):
        self.writer=writer;self.contract=contract;self.physical=contract['physical_problem'];self.strict=strict
        self.geometry=None;self.control=None;self.linear=[];self.last_counts={};self.outer=collections.deque(maxlen=5);self.outer_count=0;self.sync=None;self.mass0=None;self.previous_mass=None;self.continuity=(0.,0.,0.);self.rows=[];self.rows_bytes=0;self.chunk=0;self.steps=0
        self.arrival=Arrival(self.physical,contract);self.previous_diagnostics=None;self.assembly_terms={};self.fourier=0.;self.reference_defect=0.;self.initial_values=None;self.effective_bdf={}
    def alert(self,reason,field_state=None):
        self.writer.anomaly(reason)
        if field_state is not None:self.writer.snapshot(field_state,f'trigger_fields_{self.writer.anomalies:03d}.bin')
    def co(self,state,h):
        v=np.asarray(state['volumes']);rho=np.asarray(state['rho']['cells']);need(np.all(rho>0),'CO_NONPOSITIVE_RHO')
        sums=np.zeros(len(v));g=state['geometry'];phi=state['phi']
        for o,n,f in zip(g['owner'],g['neighbour'],phi['internal']):sums[o]+=abs(f);sums[n]+=abs(f)
        for p in phi['patches']:
            for c,f in zip(p['face_cells'],p['values']):sums[c]+=abs(f)
        sums/=rho
        return float(.5*h*np.sum(sums)/np.sum(v)),float(.5*h*np.max(sums/v))
    def qoi(self,state):return primary(state,self.geometry['centres'],self.physical)
    def outer_certificate(self):
        need(self.outer_count==24 and len(self.outer)==5,'U01_OUTER_COUNT')
        p=self.physical['properties'];L=self.physical['geometry_m']['L'];a=p['alpha0_m2_s'];eps=sys.float_info.epsilon
        transitions=[]
        changes={k:[] for k in self.contract['inner_convergence']['hard_observables']};floors={k:0. for k in changes}
        for previous,current in zip(list(self.outer)[:4],list(self.outer)[1:]):
            s0,q0=previous;s,q=current;trace={'outer_transition_end':21+len(transitions),'fields':{},'primary_previous':q0,'primary_current':q}
            for k,field in [('U','U'),('T','T'),('p_rgh','p_rgh'),('rho_s','rho'),('rho_T','rhoFluidThermo:rho')]:
                x=np.asarray(s[field]['cells']);y=np.asarray(s0[field]['cells'])
                # Infinity norm of vector magnitude for U.
                norm=lambda z:float(np.max(np.linalg.norm(z,axis=1))) if z.ndim==2 else float(np.max(np.abs(z)))
                denom={'U':max(norm(x),a/L),'T':p['DeltaT_K'],'p_rgh':max(norm(x),p['rho0_kg_m3']*.031132117082250315**2),'rho_s':p['rho0_kg_m3']*p['beta_1_K']*p['DeltaT_K'],'rho_T':p['rho0_kg_m3']*p['beta_1_K']*p['DeltaT_K']}[k]
                trace['fields'][k]={'difference_norm':norm(x-y),'current_norm':norm(x),'previous_norm':norm(y),'denominator':denom,'current_epoch':s[field]['value_sha256'],'previous_epoch':s0[field]['value_sha256']}
                changes[k].append(norm(x-y)/denom);floors[k]=max(floors[k],64*eps*(norm(x)+norm(y))/denom)
            for k in ('Nu_bar_cavity','Umax','Wmax'):
                denom=max(abs(q[k]),1.);changes[k].append(abs(q[k]-q0[k])/denom)
                floor=64*eps*(abs(q[k])+abs(q0[k]))/denom
                if k=='Nu_bar_cavity':
                    def bound(s):
                        U=np.asarray(s['U']['cells'])[:,0]*L/a;T=np.asarray(s['T']['cells']);N=len(T);gam=(N+8)*eps/(1-(N+8)*eps)
                        return gam*float(np.sum(np.abs(U*(T-p['Tc_K'])/p['DeltaT_K'])))/N+64*eps*(1+float(np.sum(np.abs(U)*(np.abs(T)+abs(p['Tc_K']))/p['DeltaT_K']))/N)
                    floor+=(bound(s)+bound(s0))/denom
                floors[k]=max(floors[k],floor)
            transitions.append(trace)
        result={'transitions':transitions,'changes':changes,'floors':floors,'ratios':{k:[v[i]/v[i-1] if v[i-1] else (0. if not v[i] else None) for i in range(1,4)] for k,v in changes.items()},'plateau':{k:max(v)<=floors[k] for k,v in changes.items()}}
        try:result.update(status='PASS',tail=policy.certify_outer(changes,floors))
        except ValueError as e:result.update(status='FAIL',reason=str(e),tail=None)
        try:policy.validate_linear([(x['field'],x['initial'],x['final'],x['iterations']) for x in self.linear]);result['linear_status']='PASS'
        except ValueError as e:result['linear_status']='FAIL';result['linear_reason']=str(e)
        need(len(self.linear)==169 or not self.strict,'LINEAR_SOLVE_COUNT_MISSING')
        return result
    def accept(self,r,receipt):
        m=r['metadata'];stage=m['stage'];s=r['payload']['native_state_epoch'];ctx=r.get('live_binding')
        need(ctx is not None,'NATIVE_LIVE_BINDING_MISSING')
        if stage=='constructor_complete':
            self.geometry=ctx;self.writer.publish('live_geometry.bin',encode(ctx),'live_geometry');self.target=ctx['target_Co'];need(self.target in (.5,.25,.125),'CO_TARGET')
            q=self.qoi(s);self.mass0=q['total_mass'];self.previous_mass=q['total_mass'];self.initial_values=q
            initial=dict(q,dimensionless_time=m['physical_time']/710,energy_storage=math.fsum(v*r*(e+K) for v,r,e,K in zip(s['volumes'],s['rho']['cells'],s['e']['cells'],s['K']['cells'])),validity=True)
            self.arrival.add(initial)
            if self.strict:need(self.target==self.expected_Co,'PREFLIGHT_CO_IDENTITY_MISMATCH');need(ctx['adjustTimeStep'] and ctx['maxDeltaT']==policy.MAX_DT,'NATIVE_CONTROL_DICTIONARY_MISMATCH')
            return
        if stage=='preSolve_after':self.control=dict(zip(('mean','max'),self.co(s,m['deltaT'])),h=m['deltaT'])
        if stage=='controller_complete':
            need(self.control is not None,'CONTROLLER_CONTROL_MISSING');expected=policy.controller_step(self.control['h'],self.control['max'],self.target)
            cap=min(policy.MAX_DT,self.target/self.control['max']*self.control['h']) if self.control['max']>sys.float_info.epsilon else policy.MAX_DT
            self.controller={'expected_deltaT':expected,'actual_deltaT':m['deltaT'],'target':self.target,'cap':cap,'cap_source':'registered maxDeltaT / actual preSolve Co','reason':'growth_1.2' if 1.2*self.control['h']<=cap else 'maxDeltaT' if cap==policy.MAX_DT else 'Co','status':'PASS' if abs(expected-m['deltaT'])<=64*math.ulp(expected) else 'FAIL'}
            if self.controller['status']=='FAIL':self.alert('CONTROLLER_ANOMALY')
        if stage=='time_start':self.outer.clear();self.outer_count=0;self.linear=[];self.last_counts={};self.sync=None
        for x in ctx['linear']:
            key=x['field'];need(x['native_count']==self.last_counts.get(key,0)+1,'LINEAR_NATIVE_COUNT_GAP_OR_DUPLICATE');self.last_counts[key]=x['native_count'];self.linear.append(dict(x,outer=m['outer'],pressure=m['pressure']))
        if stage=='outer_end':
            self.outer_count+=1;need(m['outer']==self.outer_count,'U01_OUTER_SEQUENCE');self.outer.append(({k:{'cells':s[k]['cells'],'value_sha256':s[k]['value_sha256']} for k in ('U','T','p_rgh','rho','rhoFluidThermo:rho')},self.qoi(s)))
        if stage=='term_capture' and r['payload']['term'] in ('D_B_rho','S_e','S_K'):
            term=r['payload']['term'];h=m['deltaT']
            if 'matrix' in r['payload']:
                mat=r['payload']['matrix'];rho=s['rho']['cells'] if term=='S_e' else [1.]*len(s['volumes'])
                aa=mat['diag'][0]*h/(s['volumes'][0]*rho[0]);cc=aa-1.;effective_k=r['payload'].get('effective_previous_deltaT')
                if effective_k is None:cc=h*h/(m['previous_deltaT']*(h+m['previous_deltaT'])) if aa!=1. else 0.
            else:
                effective_k=r['payload']['effective_previous_deltaT'];aa=1+h/(h+effective_k);cc=h*h/(effective_k*(h+effective_k))
            self.effective_bdf[term]={'a':aa,'b':aa+cc,'c':cc,'effective_previous_deltaT':effective_k,'history_source':'native captured term diagonal / explicit native history'}
        if stage=='energy_after_solve':self.assembly_terms=receipt['term_metrics'];self.fourier=self.assembly_terms['Fourier_correction']['signed_global']
        if stage=='pressure_solved':self.reference_defect=receipt['matrix_metrics']['physical_matrix']['signed_global']-receipt['matrix_metrics']['referenced_matrix']['signed_global']
        if stage=='native_continuity_report':
            v=np.asarray(s['volumes']);rho=np.asarray(s['rho']['cells']);d=rho-np.asarray(s['rhoFluidThermo:rho']['cells']);mass=float(np.sum(v*rho));local=float(np.sum(v*abs(d))/mass);glob=float(np.sum(v*d)/mass);self.continuity=(local,glob,self.continuity[2]+glob)
        if receipt['synchronization']:self.sync=receipt['synchronization'][-1]
        if stage!='time_end':return
        q=self.qoi(s);z=self.sync;need(z is not None,'LIVE_SYNC_MISSING');v=np.asarray(s['volumes']);rho=np.asarray(s['rho']['cells']);e=np.asarray(s['e']['cells']);K=np.asarray(s['K']['cells']);h=m['deltaT'];k=m['previous_deltaT'];a=1+h/(h+k);c=h*h/(k*(h+k));b=a+c
        terms={key:math.fsum(value) for key,value in z['energy_end_terms'].items()};internal=float(np.sum(v*rho*e));kinetic=float(np.sum(v*rho*K));flux=math.fsum(f for p in s['phi']['patches'] for f in p['values'])
        meanCo,maxCo=self.co(s,h);cert=self.outer_certificate()
        row=dict(q,time=m['physical_time'],dimensionless_time=m['physical_time']/710,time_index=m['time_index'],stage=stage,outer_index=24,pressure_index=2,deltaT=h,deltaT_previous=k,BDF_a=a,BDF_b=b,BDF_c=c,BDF_effective_by_native_storage_term=self.effective_bdf,Co_mean=meanCo,Co_max=maxCo,Co_mean_control=self.control['mean'],Co_max_control=self.control['max'],Co_target=self.target,controller_cap_reason=self.controller['reason'],controller=self.controller,total_mass_C=z['M_before_postSolve'],total_mass_EOS=z['M_after_postSolve'],mass_storage_rate=storage_mass(s,h,k),mass_storage_rate_secant=(q['total_mass']-self.previous_mass)/h,boundary_mass_flux=flux,mass_balance_residual=z['mass_end']['signed_global'],mass_balance_residual_C=z['mass_C']['signed_global'],mass_local_L1=z['mass_end']['local_volume_L1'],mass_local_Linf=z['mass_end']['local_Linf'],mass_drift=q['total_mass']-self.mass0,eos_mass_jump=z['deltaM_postSolve'],sync_mass_rate=z['mass_sync_storage_change'],energy_storage=internal+kinetic,energy_storage_internal=internal,energy_storage_kinetic=kinetic,energy_storage_rate_internal=terms['S_e'],energy_storage_rate_kinetic=terms['S_K'],wall_heat_terms=terms['H_out'],energy_transport_internal=terms['F_e'],energy_transport_kinetic=terms['F_K'],pressure_work=terms['W_p'],gravity_work=terms['W_g'],model_source=terms['S_models'],Fourier_correction_action=self.fourier,energy_balance_residual=z['energy_end']['signed_global'],energy_balance_residual_assembly=z['energy_assembly']['signed_global'],energy_balance_residual_end=z['energy_end']['signed_global'],energy_local_L1=z['energy_end']['local_volume_L1'],energy_local_Linf=z['energy_end']['local_Linf'],rho_EOS_consistency_L1=float(np.sum(v*abs(rho-np.asarray(s['rhoFluidThermo:rho']['cells'])))/np.sum(v)),rho_sync_L1=float(np.sum(v*abs(np.asarray(z['rho_s_minus_rho_T_before'])))/np.sum(v)),rho_sync_Linf=max(abs(x) for x in z['rho_s_minus_rho_T_before']),pressure_relation_defect=max(abs(x) for x in z['pressure_relation_defect']),native_continuity_local=self.continuity[0],native_continuity_global=self.continuity[1],native_continuity_cumulative=self.continuity[2],reference_cell_pressure_defect=self.reference_defect,input_hash=self.contract['live_provenance']['input_hash'],evaluator_hash=self.contract['live_provenance']['evaluator_hash'],validity=receipt['valid'],U01=cert,linear_solves=self.linear,StageLedger_health='PASS_TO_CURRENT_CALLBACK',evaluator_health='PASS_TO_CURRENT_CALLBACK',mass_energy_interpretation='DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION')
        # Wall flux and linear div(U), only from captured geometry and native BC values.
        heat={};div=np.zeros(len(v));g=s['geometry'];U=np.asarray(s['U']['cells'])
        for o,n,w,Sf in zip(g['owner'],g['neighbour'],g['linear_weights'],self.geometry['Sf']):
            f=float(np.dot(w*U[o]+(1-w)*U[n],Sf));div[o]+=f;div[n]-=f
        for geo,Tp,Up in zip(self.geometry['patch_geometry'],s['T']['patches'],s['U']['patches']):
            val=0.
            for ci,dc,sf,Tb,Ub in zip(geo['face_cells'],geo['delta'],geo['Sf'],Tp['values'],Up['values']):val+=self.physical['properties']['k_W_mK']*(Tb-s['T']['cells'][ci])*dc*np.linalg.norm(sf);div[ci]+=np.dot(Ub,sf)
            heat[geo['name']]=float(val)
        need({'hotWall','coldWall'}<=set(heat) or not self.strict,'HOT_COLD_PATCH_BINDING_MISSING')
        row.update(Q_hot=heat.get('hotWall',0.),Q_cold=heat.get('coldWall',0.),wall_heat_by_patch=heat,div_U_dimensional=float(np.sum(abs(div))/np.sum(v)))
        speed=float(np.max(np.linalg.norm(U,axis=1)));row['epsilon_v']=self.physical['geometry_m']['L']*row['div_U_dimensional']/speed if speed else None
        required_columns(row,self.contract)
        if cert['status']=='FAIL':self.alert('U01_FAILURE')
        elif any(max(v)>.8*policy.OUTER_CHANGE_LIMIT for v in cert['changes'].values()):self.alert('U01_NEAR_FAILURE')
        if cert['linear_status']=='FAIL':self.alert('LINEAR_FAILURE')
        if maxCo>self.target*(1+64*sys.float_info.epsilon):self.alert('UNEXPECTED_ACHIEVED_CO')
        diagnostics={key:row[key] for key in ('mass_balance_residual','energy_balance_residual_end','rho_sync_Linf')}
        if self.previous_diagnostics:
            for key,value in diagnostics.items():
                previous=self.previous_diagnostics[key]
                if abs(value-previous)>max(abs(previous),64*math.ulp(max(1.,abs(value)))):self.alert('DIAGNOSTIC_RELATIVE_CHANGE_'+key)
        self.previous_diagnostics=diagnostics;self.previous_mass=q['total_mass']
        row['arrival']=self.arrival.add(row)
        for result in row['arrival']:
            if result['candidate']:self.alert('ARRIVAL_CANDIDATE_TRANSITION',s)
            if result['confirmed']:self.alert('ARRIVAL_CONFIRMED',s)
        raw=(json.dumps(row,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode();need(len(raw)<=64*2**10,'PRIMARY_ROW_REGISTERED_CAP');self.rows.append(raw);self.rows_bytes+=len(raw);need(self.rows_bytes<=16*2**20,'LIVE_HISTORY_CHUNK_MEMORY_QUOTA');self.steps+=1;need(self.steps<=policy.MAX_STEPS,'REGISTERED_STEP_CAP')
        if self.steps%64==0:self.flush()
        if self.strict:need(cert['status']=='PASS' and cert['linear_status']=='PASS' and self.controller['status']=='PASS','U01_OR_CONTROLLER_STOP_NO_RETRY')
    def flush(self):
        if self.rows:self.chunk+=1;self.writer.publish(f'primary_{self.chunk:06d}.jsonl',b''.join(self.rows),'primary_history');self.rows=[];self.rows_bytes=0
    def finish(self):
        self.flush();self.writer.publish('arrival_result.json',json.dumps({'confirmed':self.arrival.confirmed,'candidates':self.arrival.results,'complete_primary_steps':self.steps},sort_keys=True,allow_nan=False).encode(),'arrival')
