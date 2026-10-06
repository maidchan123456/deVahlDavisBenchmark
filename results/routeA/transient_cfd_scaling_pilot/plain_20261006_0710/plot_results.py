from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent
j=json.loads((P/'RouteA_plain_transient_MPI_scaling_pilot.json').read_text());r=j['scaling'];fig,axes=plt.subplots(1,2,figsize=(11,4.1),constrained_layout=True)
N=[z['ranks'] for z in r];med=[z['median_s_per_step'] for z in r]
axes[0].plot(N,med,'o-',lw=2,label='Measured median (steps6–30)')
axes[0].plot(N,[med[0]/n for n in N],'--',color='gray',label='Ideal scaling')
axes[0].set(xlabel='MPI ranks (physical cores)',ylabel='Wall seconds / step',xticks=N,title='Plain transient CFD scaling');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
for n in [1,4,12]:
 z=json.loads((P/f'rank_{n:02d}'/'timing.json').read_text());x=np.arange(1,31);y=[s['external_increment'] for s in z['all_steps']];axes[1].plot(x[1:],y[1:],'o-',ms=3,label=f'{n} rank(s)')
axes[1].axvspan(1,5,color='gray',alpha=.15,label='Excluded warmup');axes[1].axvline(30,color='gray',ls=':');axes[1].set(xlabel='Completed physical step',ylabel='Wall seconds / step',title='Cold startup cost evolution (step1 omitted)');axes[1].legend(fontsize=8);axes[1].grid(alpha=.2)
fig.suptitle('Route A, Ra1e6,160×160×1, fixed24 outer, heavy diagnostics OFF',fontsize=11);fig.savefig(P/'scaling_and_step_cost.png',dpi=180)
