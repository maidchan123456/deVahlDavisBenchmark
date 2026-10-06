#!/usr/bin/env python3
"""Offline fixed-grid Co0.5/Co0.25 comparison. --validate never invokes CFD."""
import argparse,csv,hashlib,json,math,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
KEYS=['Nu_hot','Nu_cold','Umax','Wmax']
def read_table(path):
 with Path(path).open() as f:rows=list(csv.DictReader(f))
 return {k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k!='native_rho_read'}
def compare_histories(a,b):
 for data in [a,b]:
  assert np.isfinite(data['tstar']).all() and np.all(np.diff(data['tstar'])>0)
  assert all(np.isfinite(data[k]).all() for k in KEYS)
 lo=max(a['tstar'][0],b['tstar'][0]);hi=min(a['tstar'][-1],b['tstar'][-1]);assert hi>lo
 axis=np.unique(np.r_[lo,lo+.9*(hi-lo),hi,a['tstar'][(a['tstar']>=lo)&(a['tstar']<=hi)],b['tstar'][(b['tstar']>=lo)&(b['tstar']<=hi)]])
 late=axis>=lo+.9*(hi-lo);assert late.sum()>=2
 metrics={};values={}
 for k in KEYS:
  av=np.interp(axis,a['tstar'],a[k]);bv=np.interp(axis,b['tstar'],b[k]);diff=bv-av;den=max(float(np.max(np.abs(av))),1e-30)
  values[k]={'Co05':av,'Co025':bv,'signed_difference':diff}
  metrics[k]={'maximum_absolute_history_difference':float(np.max(np.abs(diff))),'sample_RMS_history_difference':float(np.sqrt(np.mean(diff**2))),'time_weighted_RMS_history_difference':float(np.sqrt(np.trapz(diff**2,axis)/(hi-lo))),'relative_maximum_history_difference_using_reference_peak':float(np.max(np.abs(diff))/den),'late_window_maximum_absolute_difference':float(np.max(np.abs(diff[late]))),'late_window_RMS_difference':float(np.sqrt(np.mean(diff[late]**2))),'late_window_mean_signed_difference':float(np.mean(diff[late])),'late_window_relative_difference_using_reference_mean':float(np.max(np.abs(diff[late]))/max(float(np.mean(np.abs(av[late]))),1e-30))}
 return axis,values,{'axis':'tstar','interpolation':'piecewise linear at sorted union of saved tstar values and common endpoints','common_range':[float(lo),float(hi)],'extrapolation':False,'comparison_by_step_index':False,'late_window_start_tstar':float(axis[late][0]),'sampling_limitation':'History metrics include interpolation and saved-state sampling differences; they do not quantify unsaved trajectory extrema.','QoI':metrics}
def validation():
 reference=json.loads((P/'source_Co05_comparison_authority.json').read_text());source=Path(reference['report']).parent.parent/'postprocessing_v2'
 a=read_table(source/'transient_QoI.csv');_,_,m=compare_histories(a,a)
 assert all(v['maximum_absolute_history_difference']==0 for v in m['QoI'].values())
 grids=[np.array([0.,1.,2.]),np.array([0.,.5,1.5,2.])];synthetic=[{'tstar':g,**{k:2+3*g for k in KEYS}} for g in grids]
 _,_,m=compare_histories(*synthetic);assert all(v['maximum_absolute_history_difference']<1e-14 for v in m['QoI'].values())
 trunc={'tstar':np.array([.5,1.,1.5]),**{k:np.array([3.5,5.,6.5]) for k in KEYS}}
 axis,_,m=compare_histories(synthetic[0],trunc);assert axis[0]==.5 and axis[-1]==1.5 and not m['extrapolation']
 import postprocess_production as pp
 plan=json.loads((P/'production_execution_plan.json').read_text());fields,t,index,native=pp.reconstruct(Path(plan['case']),'0');geo=np.load(P/'mesh_geometry.npz');q,_=pp.qoi(fields,t,index,native,geo)
 assert t==0 and index==0 and q['Nu_hot']==160 and q['Nu_cold']==160 and q['Umax']==0 and q['Wmax']==0
 result={'result':'PASS','source_self_comparison_zero':True,'staggered_linear_history_exact':True,'common_range_no_extrapolation':True,'cold_native_field_read_and_analytic_QoI':'PASS','cold_QoI':q,'production_steps_advanced':0,'CFD_EXECUTED':'NO'}
 (P/'postprocessing_dry_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
def execute():
 plan=json.loads((P/'production_execution_plan.json').read_text());run=Path(plan['runtime_output']);result=json.loads((run/'execution_result.json').read_text())
 assert result['status']=='COMPLETED_NATIVE_ENDTIME' and result['returncode']==0 and result['normal_End_marker'],'Incomplete run: completed comparison not allowed'
 assert result['completed_steps']==result['last_started_step']
 out=P/'postprocessing';assert not out.exists(),'Preserve existing output; review before offline retry'
 guard=json.loads((P/'source_reference_guard.json').read_text())
 for path,h in guard.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
 cmd=['/usr/bin/python3','-B',str(P/'postprocess_production.py'),'--case',plan['case'],'--output',str(out),'--times','all','--log',str(run/'log.foamRun')]
 r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);(P/'postprocessing_stdout.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 source=Path(json.loads((P/'source_Co05_comparison_authority.json').read_text())['report']).parent.parent/'postprocessing_v2'
 a=read_table(source/'transient_QoI.csv');b=read_table(out/'transient_QoI.csv');axis,values,history=compare_histories(a,b)
 final={}
 for k in KEYS:
  diff=float(b[k][-1]-a[k][-1]);den=max(abs(float(a[k][-1])),1e-30);final[k]={'Co05_final':float(a[k][-1]),'Co025_final':float(b[k][-1]),'signed_difference':diff,'absolute_difference':abs(diff),'signed_relative_difference':diff/den,'absolute_relative_difference':abs(diff)/den}
 final['actual_final_tstar']={'Co05':float(a['tstar'][-1]),'Co025':float(b['tstar'][-1]),'difference':float(b['tstar'][-1]-a['tstar'][-1]),'final_native_states_compared_directly':True}
 with (out/'Co05_vs_Co025_history.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['tstar']+[k+'_'+suffix for k in KEYS for suffix in ['Co05','Co025','signed_difference']])
  for i,t in enumerate(axis):w.writerow([t]+[values[k][suffix][i] for k in KEYS for suffix in ['Co05','Co025','signed_difference']])
 import postprocess_production as pp
 a_names=list(csv.DictReader((source/'transient_QoI.csv').open()));final_time_name=result['final_states'][0]['folder']
 authority=json.loads((P/'source_Co05_comparison_authority.json').read_text());old_case=Path(json.loads((Path(authority['report']).parent.parent/'production_input_manifest.json').read_text())['case']);old_final=json.loads((Path(authority['report']).parent.parent/'execution_v2/execution_result.json').read_text())['final_states'][0]['folder']
 ap=read_table(source/('centreline_'+old_final+'.csv'));bp=read_table(out/('centreline_'+final_time_name+'.csv'));assert np.array_equal(ap['coordinate'],bp['coordinate'])
 profiles={}
 for k in ['U_at_X0.5','W_at_Z0.5','theta_vertical','theta_horizontal']:
  diff=bp[k]-ap[k];profiles[k]={'RMS_difference':float(np.sqrt(np.mean(diff**2))),'Linf_difference':float(np.max(np.abs(diff))),'relative_RMS_using_reference_RMS':float(np.sqrt(np.mean(diff**2))/max(float(np.sqrt(np.mean(ap[k]**2))),1e-30))}
 late=b['time_s']>=min(.9*b['time_s'][-1],b['time_s'][-max(5,math.ceil(.1*len(b['time_s'])))])
 behavior={}
 for k in KEYS:
  y=b[k][late];t=b['time_s'][late];den=max(abs(float(y.mean())),1e-30);span=float(t[-1]-t[0]);slope=float(np.polyfit(t,y,1)[0]);rr=float(np.ptp(y)/den);rs=abs(slope)*span/den
  behavior[k]={'relative_range':rr,'slope_per_second':slope,'relative_slope_change_over_window':rs,'samples':len(y),'span_s':span,'status':'STATIONARY_CANDIDATE' if rr<=.001 and rs<=.001 else 'STILL_EVOLVING'}
 small=all(final[k]['absolute_relative_difference']<=.001 and history['QoI'][k]['late_window_relative_difference_using_reference_mean']<=.001 and history['QoI'][k]['relative_maximum_history_difference_using_reference_peak']<=.001 for k in KEYS) and all(v['status']=='STATIONARY_CANDIDATE' for v in behavior.values()) and all(v['relative_RMS_using_reference_RMS']<=.001 for v in profiles.values())
 summary={'purpose':'fixed-grid timestep sensitivity between Co0.5 and Co0.25','final_QoI':final,'history':history,'final_profiles':profiles,'Co025_late_behavior':behavior,'descriptive_threshold':.001,'classification':'TIME_STEP_SENSITIVITY_SMALL_BETWEEN_CO05_AND_CO025' if small else 'REVIEW_TIME_STEP_SENSITIVITY','classification_scope':'final and late sampled QoIs only; whole-history maximum/RMS and profile differences must also be reviewed before a broad statement','full_temporal_convergence_proven':False,'time_step_independent_claim_allowed':False,'Co0125_decision':'Review materially different final/late QoIs, profiles or sampled transients; resolve sampling/horizon uncertainty before deciding. Not predetermined.','mass_energy_descriptors':{'initial_mass_kg':float(b['mass_kg'][0]),'final_mass_kg':float(b['mass_kg'][-1]),'mass_relative_drift':float((b['mass_kg'][-1]-b['mass_kg'][0])/b['mass_kg'][0]),'initial_sensible_proxy_J':float(b['sensible_internal_energy_proxy_J'][0]),'final_sensible_proxy_J':float(b['sensible_internal_energy_proxy_J'][-1]),'final_kinetic_energy_J':float(b['kinetic_energy_J'][-1]),'exact_BDF_certificate':False},'steady_baseline_comparison':json.loads((out/'final_steady_baseline_comparison.json').read_text())}
 (out/'Co05_vs_Co025_comparison.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(2,2,figsize=(11,8))
 for ax,k in zip(axes.flat,KEYS):ax.plot(a['tstar'],a[k],label='Co0.5');ax.plot(b['tstar'],b[k],ls='--',label='Co0.25');ax.set_xlabel('t*');ax.set_ylabel(k);ax.legend();ax.grid(alpha=.25)
 fig.tight_layout();fig.savefig(out/'Co05_vs_Co025_QoI.png',dpi=150);plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);m=parser.add_mutually_exclusive_group(required=True);m.add_argument('--validate',action='store_true');m.add_argument('--execute',action='store_true');args=parser.parse_args()
 validation() if args.validate else execute()
