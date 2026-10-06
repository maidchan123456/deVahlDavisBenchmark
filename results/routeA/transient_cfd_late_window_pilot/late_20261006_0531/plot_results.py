from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).resolve().parent
j=json.loads((P/'RouteA_plain_transient_late_window_performance_pilot.json').read_text());r=json.loads((P/'step_history.json').read_text());x=np.array([z['step'] for z in r]);write=np.array([z['is_field_write'] for z in r]);wall=np.array([z['step_wall_s'] for z in r]);dt=[z['deltaT_s'] for z in r];co=[z['logged_Co_max'] for z in r];pressure=[z['pressure_total_iterations'] for z in r]
fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
a=axes[0,0];a.plot(x[~write],wall[~write],'.',ms=2,alpha=.45,label='Non-write steps');a.scatter(x[write],wall[write],s=25,marker='x',color='red',label='Native checkpoint writes');a.axhline(j['late_proxy']['wall_stats']['median'],color='black',ls='--',label='Last200 non-write median');a.set(ylabel='Wall seconds / step',title='Accepted continuous cold-start trajectory');a.legend(fontsize=8);a.set_ylim(0,min(max(wall[1:])*1.1,1));a.text(.03,.94,f'Step1 includes startup: {wall[0]:.3f} s (outside scale)',transform=a.transAxes,fontsize=8)
a=axes[0,1];a.plot(x,dt,lw=1.2);a.axhline(.027734375,color='gray',ls='--',label='maxDeltaT');a.axvline(j['controller']['maxDeltaT_first_step'],ls=':',color='green',label='First maxDeltaT');a.axvline(j['controller']['Courant_first_step'],ls=':',color='orange',label='First Courant limit');a.set(ylabel='deltaT (s)',title='Native adaptive timestep');a.legend(fontsize=8)
a=axes[1,0];a.plot(x,co,lw=1.2);a.axhline(.5,color='gray',ls='--',label='maxCo0.5');a.set(ylabel='Logged preSolve max Co',title='Previous-state Courant number');a.legend(fontsize=8)
a=axes[1,1];a.plot(x,pressure,lw=1,alpha=.7);a.set(ylabel='Pressure linear iterations / step',title='48 pressure solves per completed step')
for a in axes.flat:a.set_xlabel('Accepted completed physical step');a.grid(alpha=.2)
fig.suptitle('Route A plain CFD,12 physical-core MPI ranks,24 outer, heavy diagnostics OFF',fontsize=12);fig.savefig(P/'late_window_performance.png',dpi=180)
fig,ax=plt.subplots(figsize=(8,4.3),constrained_layout=True);w=j['windows'];valid=[z for z in w if z['non_write_steps']];ax.plot([(z['start_step']+min(z['end_step'],len(r)))/2 for z in valid],[z['median_s_per_step'] for z in valid],'o-',label='Broad non-write window median');late=j['trend']['last250_rolling50_nonwrite_windows'];ax.plot([(z['start_step']+min(z['end_step'],len(r)))/2 for z in late],[z['median_s_per_step'] for z in late],'s--',label='Later50-step window median');ax.axhline(.09614649903960526,color='gray',ls=':',label='Prior30-step cold median');ax.set(xlabel='Window midpoint step',ylabel='Median wall seconds / step',title='Window medians and later cost trend');ax.grid(alpha=.2);ax.legend();fig.savefig(P/'late_window_medians.png',dpi=180)
