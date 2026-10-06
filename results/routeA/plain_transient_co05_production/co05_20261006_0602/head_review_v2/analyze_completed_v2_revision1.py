#!/usr/bin/env python3
"""Offline summaries/figures. Refuses incomplete production; never invokes CFD."""
import csv,hashlib,json,math,re,subprocess,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
V2=Path(__file__).resolve().parent;P=V2.parent;ROOT=P.parents[3]
plan=json.loads((V2/'production_execution_plan_v2.json').read_text());run=Path(plan['runtime_output']);out=P/'postprocessing_v2'
result=json.loads((run/'execution_result.json').read_text())
assert result['status']=='COMPLETED_NATIVE_ENDTIME' and result['returncode']==0,'Incomplete production: no full postprocessing'
assert result['normal_End_marker'] and result['completed_steps']==result['last_started_step']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((V2/'head_change_review.json').read_text())
for rel,digest in review['original_artifacts_sha256'].items():assert sha(P/rel)==digest,'Historical preparation changed'
assert out.exists() and (out/'native_log_coverage.json').exists(),'Completed prepared outputs required'
assert json.loads((out/'native_log_coverage.json').read_text())['completed_steps']==result['completed_steps']
def save(name,value):(out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def cols(path,keys):
 with path.open() as f:names=next(csv.reader(f))
 data=np.genfromtxt(path,delimiter=',',skip_header=1,usecols=[names.index(k) for k in keys],ndmin=2)
 assert np.isfinite(data).all(),str(path)
 return {key:data[:,i] for i,key in enumerate(keys)}
q=cols(out/'transient_QoI.csv',['time_s','tstar','time_index','Nu_hot','Nu_cold','Umax','Wmax','speed_max_m_s','Uz_absmax_m_s','Tmin_K','Tmax_K','mass_kg','sensible_internal_energy_proxy_J','kinetic_energy_J','Q_hot_W','Q_cold_W','symmetry_T_RMS_K','symmetry_U_RMS_m_s'])
h=cols(out/'native_step_diagnostics.csv',['step','time_s','deltaT_s','Co_mean','Co_max','pressure_solves','pressure_iterations','energy_solves','energy_iterations','momentum_iterations','max_initial_residual','max_final_residual','continuity_local_max_abs','continuity_global_max_abs','continuity_cumulative_last','ExecutionTime_s','ClockTime_s'])
assert len(h['step'])==result['completed_steps']
alpha=1e-5/.71;scale=alpha/.1**2;tstar=h['time_s']*scale
markers=json.loads((run/'time_header_wall_markers.json').read_text())
ends=np.array([x['elapsed_wall_s'] for x in markers if x['event']=='step_end']);assert len(ends)==len(h['step'])
wall=np.diff(np.r_[np.nan,ends]);writes={s['index'] for s in result['saved_snapshot_times_and_indices']}
nonwrite=np.array([int(s) not in writes for s in h['step']]);late=h['step']>=math.ceil(.9*len(h['step']));last200=h['step']>len(h['step'])-200
assert sha(out/'production_step_history.csv')==json.loads((V2/'offline_analysis_initial_attempt_v2.json').read_text())['existing_postprocessing_files_sha256']['production_step_history.csv']
# Actual saved-state bin/rank/field completeness after simulation, not online.
sys.path.insert(0,str(P));sys.path.insert(0,str(ROOT/'Scripts/routeA'));from mesh_geometry import labels
from foam_fields import read_scalar,read_vector
case=Path(plan['case']);last_names={s['folder'] for s in result['final_states']};assert len(last_names)==1;last_name=last_names.pop()
rank_times=[];final_fields={};regular_bins=set()
for snap in result['saved_snapshot_times_and_indices']:
 text=(case/'processor0'/snap['directory']/'uniform/time').read_text();dt=float(re.search(r'\bdeltaT\s+([^;]+);',text)[1]);b=int((snap['value']+.5*dt)/5)
 if b>0:regular_bins.add(b)
assert regular_bins==set(range(1,285)),'A regular output bin is missing'
for rank in range(12):
 base=case/f'processor{rank}';ids=labels(base/'constant/polyMesh/cellProcAddressing');nf=len(labels(base/'constant/polyMesh/neighbour'))
 dirs={x.name for x in base.iterdir() if x.is_dir() and re.fullmatch(r'[0-9.eE+-]+',x.name)}
 assert dirs=={'0'}|{s['directory'] for s in result['saved_snapshot_times_and_indices']},'rank snapshot set differs'
 checks={}
 for name in ['T','U','p','p_rgh','rho','phi','U_0','p_0','p_rgh_0','rho_0','phi_0']:
  field=base/last_name/name
  values=read_vector(field,len(ids)) if name in ['U','U_0'] else read_scalar(field,nf if name in ['phi','phi_0'] else len(ids))
  assert np.isfinite(values).all() and not re.search(r'\b(?:nan|inf)\b',field.read_text(),re.I)
  checks[name]={'finite':True,'sha256':sha(field)}
 final_fields[str(rank)]=checks
save('output_integrity_v2.json',{'result':'PASS','all_regular_bins':sorted(regular_bins),'global_output_snapshots':len(result['saved_snapshot_times_and_indices']),'all_rank_snapshot_sets_equal':True,'final_fields':final_fields,'no_exact_restart_claim':True})
# Baseline comparisons: preserve signed and absolute relative differences separately.
comparison=json.loads((out/'final_steady_baseline_comparison.json').read_text())
with (out/'steady_comparison.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['QoI','transient_final','steady_baseline','signed_relative_difference','absolute_relative_difference'])
 for key in ['Nu_hot','Nu_cold','Umax','Wmax']:
  row=comparison[key];row['absolute_relative_difference']=abs(row['relative_difference']);w.writerow([key,row['transient_final'],row['steady_baseline'],row['relative_difference'],row['absolute_relative_difference']])
save('steady_comparison.json',comparison)
# Late saved states: cover both last10% of physical span and last10% of states,
# at least5 snapshots; report actual coverage so startup extra files cannot hide it.
count=max(5,math.ceil(.1*len(q['time_s'])));threshold=min(.9*q['time_s'][-1],q['time_s'][-count]);qlate=q['time_s']>=threshold
behavior={}
for key in ['Nu_hot','Nu_cold','Umax','Wmax']:
 values=q[key][qlate];times=q['time_s'][qlate];mean=float(values.mean());span=float(times[-1]-times[0]);slope=float(np.polyfit(times,values,1)[0]);den=max(abs(mean),1e-30)
 rr=float(np.ptp(values)/den);change=abs(slope)*span/den
 behavior[key]={'relative_range':rr,'slope_per_second':slope,'relative_slope_per_second':slope/den,'relative_slope_change_over_window':change,'classification':'STATIONARY_CANDIDATE' if rr<=.001 and change<=.001 else 'STILL_EVOLVING','threshold_descriptive_only':.001,'snapshots':int(qlate.sum()),'span_s':span}
horizon='ADEQUATE_FOR_CURRENT_DIAGNOSTIC' if all(v['classification']=='STATIONARY_CANDIDATE' for v in behavior.values()) else 'STILL_EVOLVING'
assessment={'late_QoI':behavior,'tstar2_time_horizon':horizon,'stationarity_proven':False,'physical_model_validated':False};save('late_time_assessment_v2.json',assessment)
massrel=(q['mass_kg']-q['mass_kg'][0])/q['mass_kg'][0]
e=cols(out/'coarse_energy_descriptors.csv',['dE_dt_secant_W','wall_heat_net_trapezoid_W','difference_W'])
energy_norm=np.maximum(.5*(np.abs(q['Q_hot_W'][1:])+np.abs(q['Q_cold_W'][1:])),1e-30)
descriptors={'mass':{'status':'RECONSTRUCTED_FINITE_NOT_EXACT_FV_AUDIT','initial_kg':float(q['mass_kg'][0]),'final_kg':float(q['mass_kg'][-1]),'final_relative_drift':float(massrel[-1]),'max_abs_relative_drift':float(np.abs(massrel).max()),'native_continuity_max_local_abs':float(h['continuity_local_max_abs'].max()),'native_continuity_max_global_abs':float(h['continuity_global_max_abs'].max()),'native_continuity_final_cumulative':float(h['continuity_cumulative_last'][-1])},'energy':{'status':'RECONSTRUCTED_FINITE_COARSE_DESCRIPTOR_ONLY','initial_sensible_proxy_J':float(q['sensible_internal_energy_proxy_J'][0]),'final_sensible_proxy_J':float(q['sensible_internal_energy_proxy_J'][-1]),'final_kinetic_energy_J':float(q['kinetic_energy_J'][-1]),'final_Q_hot_W':float(q['Q_hot_W'][-1]),'final_Q_cold_W':float(q['Q_cold_W'][-1]),'coarse_secant_minus_net_heat_max_abs_W':float(np.abs(e['difference_W']).max()),'coarse_secant_minus_net_heat_late_max_abs_W':float(np.abs(e['difference_W'][-count:]).max()),'late_secant_difference_relative_to_wall_flux_max':float(np.max(np.abs(e['difference_W'][-count:])/energy_norm[-count:])),'exact_BDF_energy_certificate':False,'missing_native_stage_or_eK_histories_reconstructed':False},'symmetry':{'final_T_RMS_K':float(q['symmetry_T_RMS_K'][-1]),'final_U_RMS_m_s':float(q['symmetry_U_RMS_m_s'][-1])}}
save('mass_energy_descriptors_v2.json',descriptors)
def stats(values):return {'min':float(values.min()),'median':float(np.median(values)),'max':float(values.max())}
wall_late=wall[late&nonwrite&np.isfinite(wall)]
runtime={'completed_physical_steps':int(len(h['step'])),'total_wall_seconds':result['elapsed_wall_s'],'total_wall_hours':result['elapsed_wall_s']/3600,'projected_hours':plan['expected_runtime_hours'],'actual_to_projected':result['elapsed_wall_s']/3600/plan['expected_runtime_hours'],'final_time_seconds':result['final_states'][0]['value'],'final_tstar':result['final_states'][0]['value']*scale,'max_logged_Co':float(h['Co_max'].max()),'late_logged_Co':stats(h['Co_max'][late]),'late_deltaT_seconds':stats(h['deltaT_s'][late]),'late_external_seconds_per_step_excluding_native_writes':stats(wall_late),'last200_nonwrite_seconds_per_step':stats(wall[last200&nonwrite&np.isfinite(wall)]),'pressure_iterations_early1000':stats(h['pressure_iterations'][:1000]),'pressure_iterations_last10percent':stats(h['pressure_iterations'][late]),'energy_iterations_last10percent':stats(h['energy_iterations'][late]),'all_steps_pressure48_energy24':bool(np.all(h['pressure_solves']==48) and np.all(h['energy_solves']==24)),'standard_log_Co_is_pre_advance_state':True,'returncode':0,'normal_exit':True,'fatal_nan_fpe':False,'log_bytes':(run/'log.foamRun').stat().st_size}
save('production_runtime_summary.json',runtime)
# Scientific figures, generated only now after normal native completion.
plt.rcParams.update({'font.size':10,'figure.dpi':150,'axes.grid':True,'grid.alpha':.25})
fig,axes=plt.subplots(3,1,figsize=(8,8),sharex=True)
axes[0].plot(q['tstar'],q['Nu_hot'],label='hot');axes[0].plot(q['tstar'],q['Nu_cold'],label='cold',ls='--');axes[0].axhline(comparison['Nu_hot']['steady_baseline'],color='.4',ls=':',label='steady160²');axes[0].set_yscale('log');axes[0].set_ylabel('Nu (log scale)');axes[0].legend()
for ax,key in zip(axes[1:],['Umax','Wmax']):ax.plot(q['tstar'],q[key],label='transient');ax.axhline(comparison[key]['steady_baseline'],color='.4',ls=':',label='steady160²');ax.set_ylabel(key+' (dimensionless)');ax.legend()
axes[-1].set_xlabel('t* = αt/L²');fig.suptitle('Route A: plain Co0.5 fluid-only diagnostic transient');fig.tight_layout();fig.savefig(out/'QoI_vs_tstar.png');fig.savefig(out/'QoI_vs_tstar.svg');plt.close(fig)
fig,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
for ax,key,label in zip(axes.flat,['deltaT_s','Co_max','pressure_iterations','energy_iterations','max_final_residual','continuity_global_max_abs'],['Δt (s)','logged Co max (pre-advance)','pressure iterations/step','energy iterations/step','max final linear residual','max |global continuity|/step']):
 ax.plot(tstar,h[key],lw=.6);ax.set_ylabel(label)
 if key=='Co_max':ax.axhline(.5,color='r',ls=':',label='configured maxCo');ax.legend()
 if key in ['max_final_residual','continuity_global_max_abs']:ax.set_yscale('symlog',linthresh=1e-16)
for ax in axes[-1]:ax.set_xlabel('t*')
fig.suptitle('Native standard-log diagnostics: fixed24 outer iterations');fig.tight_layout();fig.savefig(out/'native_log_vs_tstar.png');fig.savefig(out/'native_log_vs_tstar.svg');plt.close(fig)
# Representative fields, no hundreds of profile figures.
selected=[]
for wanted in [.01,.5,1.8,q['tstar'][-1]]:
 idx=int(np.abs(q['tstar']-wanted).argmin())
 if idx not in selected:selected.append(idx)
fig,axes=plt.subplots(2,2,figsize=(11,8))
for idx in selected:
 name=result['saved_snapshot_times_and_indices'][idx-1]['directory'] if idx>0 else '0'
 profile=cols(out/('centreline_'+name+'.csv'),['coordinate','U_at_X0.5','W_at_Z0.5','theta_vertical','theta_horizontal'])
 for ax,key in zip(axes.flat,['U_at_X0.5','W_at_Z0.5','theta_vertical','theta_horizontal']):ax.plot(profile['coordinate'],profile[key],label=f"t*={q['tstar'][idx]:.3g}");ax.set_ylabel(key);ax.set_xlabel('coordinate/L');ax.legend()
fig.suptitle('Representative centreline profiles');fig.tight_layout();fig.savefig(out/'representative_profiles.png');plt.close(fig)
base=cols(ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000/centreline_4097.csv',['coordinate','U_at_X0.5','W_at_Z0.5'])
finalprofile=cols(out/('centreline_'+last_name+'.csv'),['coordinate','U_at_X0.5','W_at_Z0.5'])
fig,axes=plt.subplots(1,2,figsize=(11,4))
for ax,key in zip(axes,['U_at_X0.5','W_at_Z0.5']):ax.plot(finalprofile['coordinate'],finalprofile[key],label='transient final');ax.plot(base['coordinate'],base[key],ls='--',label='steady160²');ax.set_xlabel('coordinate/L');ax.set_ylabel(key);ax.legend()
fig.tight_layout();fig.savefig(out/'final_vs_steady_profiles.png');fig.savefig(out/'final_vs_steady_profiles.svg');plt.close(fig)
summary={'runtime':runtime,'comparison':comparison,'late_time_assessment':assessment,'mass_energy':descriptors,'final_QoI':{key:float(values[-1]) for key,values in q.items()},'claims':'MEASURED/POSTPROCESSED diagnostic result; no physical model validation, formalGateJ, grid independence or exact conservation certificate'}
save('production_analysis_summary_v2.json',summary)
print(json.dumps(summary,indent=2))
