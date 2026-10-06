#!/usr/bin/env python3
"""Offline plain-field/log analysis; never invokes a CFD or reconstruction command."""
import argparse
import csv
import json
from pathlib import Path
import re
import sys
import numpy as np
from mesh_geometry import labels

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT/'Scripts/routeA'))
from foam_fields import read_scalar,read_vector
L=.1
ALPHA=1e-5/.71

def save(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def table(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def reconstruct(case,name):
    fields={'T':np.empty(25600),'U':np.empty((25600,3)),'rho':np.empty(25600)}
    times=[]; indices=[]; count=np.zeros(25600,dtype=int); native_rho=True
    for rank in range(12):
        base=case/('processor'+str(rank)); ids=labels(base/'constant/polyMesh/cellProcAddressing')
        count[ids]+=1; directory=base/name
        fields['T'][ids]=read_scalar(directory/'T',len(ids))
        fields['U'][ids]=read_vector(directory/'U',len(ids))
        if (directory/'rho').exists(): fields['rho'][ids]=read_scalar(directory/'rho',len(ids))
        else:
            assert float(name)==0,'rho only reconstructed from EOS at cold initial time'
            fields['rho'][ids]=1-.001*(fields['T'][ids]-300); native_rho=False
        if (directory/'uniform/time').exists():
            text=(directory/'uniform/time').read_text()
            times.append(float(re.search(r'\bvalue\s+([^;]+);',text)[1]))
            indices.append(int(re.search(r'\bindex\s+([^;]+);',text)[1]))
        else:
            assert float(name)==0;times.append(0.);indices.append(0)
    assert np.all(count==1) and len(set(times))==1 and len(set(indices))==1
    assert all(np.isfinite(v).all() for v in fields.values())
    return fields,times[0],indices[0],native_rho

def qoi(fields,t,index,native_rho,geo):
    centres=geo['centres']; ij=np.rint(centres[:,:2]*160/L-.5).astype(int)
    linear=ij[:,1]*160+ij[:,0]
    assert np.array_equal(np.sort(linear),np.arange(25600)),'cell lattice mapping is not bijective'
    order=np.argsort(linear)
    pos=centres[order].reshape(160,160,3)
    assert np.allclose(pos[0,:,0],(.5+np.arange(160))*.1/160,atol=1e-13,rtol=0)
    assert np.allclose(pos[:,0,1],(.5+np.arange(160))*.1/160,atol=1e-13,rtol=0)
    T=fields['T'];U=fields['U'];rho=fields['rho'];vol=geo['volumes']
    Tg=T[order].reshape(160,160);Ug=U[order].reshape(160,160,3)
    coords=np.linspace(0,L,4097); cc=(.5+np.arange(160))*L/160
    ux=.5*(Ug[:,79,0]+Ug[:,80,0]); uy=.5*(Ug[79,:,1]+Ug[80,:,1])
    uq=np.interp(coords,np.r_[0,cc,L],np.r_[0,ux,0])*L/ALPHA
    wq=np.interp(coords,np.r_[0,cc,L],np.r_[0,uy,0])*L/ALPHA
    # Centreline temperatures: y line has zero normal derivative at its endpoints;
    # x line uses exact imposed hot/cold wall temperatures.
    ty=.5*(Tg[:,79]+Tg[:,80]);tx=.5*(Tg[79,:]+Tg[80,:])
    theta_y=np.interp(coords,np.r_[0,cc,L],np.r_[ty[0],ty,ty[-1]])-300
    theta_x=np.interp(coords,np.r_[0,cc,L],np.r_[300.5,tx,299.5])-300
    hot=(300.5-T[geo['hot_cells']])*L/(L/160/2)
    cold=(T[geo['cold_cells']]-299.5)*L/(L/160/2)
    st=Tg+Tg[::-1,::-1]-600;su=Ug+Ug[::-1,::-1]
    speed=np.linalg.norm(U,axis=1)
    row={'time_s':t,'tstar':ALPHA*t/L**2,'time_index':index,
         'Nu_hot':float(hot.mean()),'Nu_cold':float(cold.mean()),
         'Umax':float(uq.max()),'Umax_Y':float(coords[uq.argmax()]/L),
         'Wmax':float(wq.max()),'Wmax_X':float(coords[wq.argmax()]/L),
         'speed_max_m_s':float(speed.max()),'Uz_absmax_m_s':float(np.abs(U[:,2]).max()),
         'Tmin_K':float(T.min()),'Tmax_K':float(T.max()),
         'symmetry_T_RMS_K':float(np.sqrt(np.mean(st**2))),
         'symmetry_U_RMS_m_s':float(np.sqrt(np.mean(su**2))),
         'mass_kg':float(np.sum(rho*vol)),
         'sensible_internal_energy_proxy_J':float(np.sum(rho*1000*(T-298.15)*vol)),
         'kinetic_energy_J':float(np.sum(.5*rho*speed**2*vol)),
         'Q_hot_W':float(.01/.71*.001*hot.mean()),
         'Q_cold_W':float(.01/.71*.001*cold.mean()),'native_rho_read':native_rho}
    profiles=[{'index':i,'coordinate':float(c/L),'U_at_X0.5':float(uq[i]),'W_at_Z0.5':float(wq[i]),
               'theta_vertical':float(theta_y[i]),'theta_horizontal':float(theta_x[i])} for i,c in enumerate(coords)]
    return row,profiles

def native_log(path,out):
    """Stream 5GB-class logs; aggregate iterations while retaining full log as evidence."""
    rows=[]; pending={}; current=None
    n=r'([\d.eE+-]+)'
    solve=re.compile(r'Solving for (\w+), Initial residual = '+n+r', Final residual = '+n+r', No Iterations (\d+)')
    with path.open(errors='replace') as f:
        for line in f:
            m=re.search(r'Courant Number mean: '+n+r' max: '+n,line)
            if m: pending['Co_mean']=float(m[1]);pending['Co_max']=float(m[2])
            m=re.match(r'deltaT = '+n,line)
            if m: pending['deltaT_s']=float(m[1])
            m=re.match(r'Time = (\S+)',line)
            if m:
                assert current is None,'missing end-step marker'
                current={'step':len(rows)+1,'time_s':float(m[1].rstrip('s')),**pending,
                         'pressure_solves':0,'pressure_iterations':0,'energy_solves':0,'energy_iterations':0,
                         'momentum_solves':0,'momentum_iterations':0,'max_initial_residual':0.,'max_final_residual':0.,
                         'continuity_local_max_abs':0.,'continuity_global_max_abs':0.}
                pending={}
            m=solve.search(line)
            if m and current:
                field,initial,final,it=m.groups();initial=float(initial);final=float(final);it=int(it)
                current['max_initial_residual']=max(current['max_initial_residual'],initial)
                current['max_final_residual']=max(current['max_final_residual'],final)
                group='pressure' if field=='p_rgh' else 'energy' if field=='e' else 'momentum' if field in ['Ux','Uy','Uz'] else None
                if group:
                    current[group+'_solves']+=1;current[group+'_iterations']+=it
            m=re.search(r'continuity errors : sum local = '+n+r', global = '+n+r', cumulative = '+n,line)
            if m and current:
                current['continuity_local_max_abs']=max(current['continuity_local_max_abs'],abs(float(m[1])))
                current['continuity_global_max_abs']=max(current['continuity_global_max_abs'],abs(float(m[2])))
                current['continuity_cumulative_last']=float(m[3])
            m=re.match(r'ExecutionTime = '+n+r' s\s+ClockTime = '+n+r' s',line)
            if m and current:
                current['ExecutionTime_s']=float(m[1]);current['ClockTime_s']=float(m[2]);rows.append(current);current=None
    if rows: table(out/'native_step_diagnostics.csv',rows)
    save(out/'native_log_coverage.json',{'completed_steps':len(rows),'last_started_step_incomplete':current,
         'Co_alignment':'Co on standard pre-advance state; do not treat as post-solve Co',
         'wall_timing':'native ClockTime has integer-second granularity; use launcher external markers for per-step timing'})

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--case',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a.add_argument('--times',choices=['all','last'],default='all');a.add_argument('--log',type=Path)
    args=a.parse_args();case=args.case.resolve();out=args.output.resolve()
    assert out!=case and case not in out.parents,'analysis output must be outside case'
    out.mkdir(exist_ok=False,parents=True)
    geo=np.load(P/'mesh_geometry.npz')
    names=sorted([x.name for x in (case/'processor0').iterdir() if x.is_dir() and re.fullmatch(r'[0-9.eE+-]+',x.name)],key=float)
    if args.times=='last':names=names[-1:]
    rows=[];last_profiles=None
    for name in names:
        fields,t,index,native_rho=reconstruct(case,name);row,profiles=qoi(fields,t,index,native_rho,geo);rows.append(row)
        table(out/('centreline_'+name+'.csv'),profiles);last_profiles=profiles
    assert rows
    table(out/'transient_QoI.csv',rows)
    base=json.loads((ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000/metrics.json').read_text())
    final=rows[-1];comparison={}
    for k,b in {'Nu_hot':base['Nu_hot_path1'],'Nu_cold':base['Nu_cold_path1'],'Umax':base['Umax'],'Wmax':base['Wmax']}.items():
        comparison[k]={'transient_final':final[k],'steady_baseline':b,'relative_difference':(final[k]-b)/abs(b)}
    with (ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000/centreline_4097.csv').open() as f:baseline=list(csv.DictReader(f))
    for k in ['U_at_X0.5','W_at_Z0.5']:
        diff=np.array([r[k] for r in last_profiles])-np.array([float(r[k]) for r in baseline])
        comparison[k]={'RMS_difference':float(np.sqrt(np.mean(diff**2))),'Linf_difference':float(np.abs(diff).max())}
    save(out/'final_steady_baseline_comparison.json',comparison)
    assessment={'classification':'INSUFFICIENT_LATE_HISTORY','formal_validation':False,'baseline_agreement_assumed':False}
    if len(rows)>=5:
        late=[r for r in rows if r['time_s']>=min(.9*rows[-1]['time_s'],rows[-5]['time_s'])]
        assessment['late_history_samples']=len(late);assessment['late_history_span_s']=late[-1]['time_s']-late[0]['time_s']
        assessment['late_QoI_descriptors']={}
        for k in ['Nu_hot','Nu_cold','Umax','Wmax']:
            values=np.array([r[k] for r in late]);scale=max(abs(values.mean()),1e-30)
            slope=float(np.polyfit([r['time_s'] for r in late],values,1)[0])
            assessment['late_QoI_descriptors'][k]={'relative_range':float(np.ptp(values)/scale),'slope_per_second':slope,'relative_change_over_window':float(abs(slope)*assessment['late_history_span_s']/scale)}
        assessment['classification']='STATIONARY_CANDIDATE' if all(v['relative_range']<=.001 and v['relative_change_over_window']<=.001 for v in assessment['late_QoI_descriptors'].values()) else 'STILL_EVOLVING'
    save(out/'evolution_assessment.json',assessment)
    energy=[]
    for before,after in zip(rows,rows[1:]):
        elapsed=after['time_s']-before['time_s'];assert elapsed>0
        de=(after['sensible_internal_energy_proxy_J']-before['sensible_internal_energy_proxy_J'])/elapsed
        q=.5*((before['Q_hot_W']-before['Q_cold_W'])+(after['Q_hot_W']-after['Q_cold_W']))
        energy.append({'time_before_s':before['time_s'],'time_after_s':after['time_s'],'dE_dt_secant_W':de,'wall_heat_net_trapezoid_W':q,'difference_W':de-q})
    if energy:table(out/'coarse_energy_descriptors.csv',energy)
    save(out/'coverage.json',{'case':str(case),'snapshot_count':len(rows),'final_time_s':final['time_s'],'final_tstar':final['tstar'],
         'energy_scope':'eConst Cv*(T-298.15) volume proxy; coarse saved-state secants, no native BDF balance or missing e/K history reconstruction',
         'Umax_Wmax_semantics':'dimensionless positive horizontal Ux and vertical Uy maxima on centre lines; speed and Uz separate',
         'Q3_EXECUTED':'NO','FORMAL_GATE_J_EXECUTED':'NO','FULL_CONSERVATION_AUDIT':'NO'})
    if args.log:native_log(args.log,out)
    print(json.dumps({'output':str(out),'snapshots':len(rows),'final':final},indent=2))

if __name__=='__main__':main()
