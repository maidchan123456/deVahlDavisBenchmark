"""Individual publication figures and exported plot arrays."""
from pathlib import Path
from common import plt, np, COLORS, write_csv, save_figure


def field(ax, case, kind, vmax=None, density_limit=None, title=True):
    """Cell-centre plots; no clipping or alteration of saved numerical arrays."""
    x,z=case.x,case.z
    if kind=='streamlines':
        vmax=vmax or float(case.speed.max()) or 1
        if np.max(case.speed)==0:
            artist=ax.contourf(x,z,np.zeros_like(case.theta),levels=np.linspace(0,vmax,25),cmap='magma')
            ax.text(.5,.5,'Zero velocity (conduction)',ha='center',va='center',transform=ax.transAxes)
        else:
            stream=ax.streamplot(x,z,case.velocity[:,:,0],case.velocity[:,:,1],color=case.speed,
                cmap='magma',norm=plt.Normalize(0,vmax),density=1.25,linewidth=.9,arrowsize=.8)
            artist=stream.lines
        label=r'$|\mathbf{U}^*|$'
    else:
        if kind=='temperature':
            values=case.theta; levels=np.linspace(0,1,31); cmap='coolwarm';label=r'$\theta$'
            # Known wall temperatures and adiabatic boundary extension for display only.
            values=np.pad(values,((1,1),(1,1)),mode='edge');values[:,0]=1;values[:,-1]=0
        elif kind=='velocity_magnitude':
            values=np.pad(case.speed,1,mode='constant');levels=np.linspace(0,vmax or float(case.speed.max()) or 1,31);cmap='magma';label=r'$|\mathbf{U}^*|$'
        elif kind=='density_deviation':
            assert case.route=='A'
            lim=density_limit or max(float(np.abs(case.density).max()),1e-12)
            values=np.pad(case.density,1,mode='edge')
            prop=case.manifest['properties']; beta=prop['beta_1_K']; tref=prop['T0_K']
            values[:,0]=-beta*(prop['Th_K']-tref);values[:,-1]=-beta*(prop['Tc_K']-tref)
            levels=np.linspace(-lim,lim,31);cmap='RdBu_r';label=r'$\rho(T)/\rho_0-1$ (EOS; $\psi=0$)'
        elif kind=='buoyancy_factor':
            assert case.route=='B'
            values=np.pad(case.density,1,mode='edge');prop=case.manifest['properties'];beta=prop['beta_1_K']
            values[:,0]=1-beta*(prop['Th_K']-prop['TRef_K']);values[:,-1]=1-beta*(prop['Tc_K']-prop['TRef_K'])
            levels=np.linspace(1-.5*beta*prop['DeltaT_K'],1+.5*beta*prop['DeltaT_K'],31);cmap='RdBu_r';label='rhok (buoyancy / hydrostatic factor)'
        else: raise ValueError(kind)
        artist=ax.contourf(np.r_[0,x,1],np.r_[0,z,1],values,levels=levels,cmap=cmap,extend='both')
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='X',ylabel='Z',aspect='equal')
    if title: ax.set_title(case.title)
    return artist,label


def profiles(axs, cases, kind, paper=None):
    for c in cases:
        color=COLORS['H'] if c.category=='sensitivity' else COLORS[c.route]
        label=c.case_id + (' (diagnostic-only)' if c.category=='matrix' and not c.accepted else '')
        ls='--' if c.category=='matrix' and not c.accepted else '-'
        if kind=='centreline':
            for ax,key,coord in zip(axs,('U','V'),('Z','X')):
                ax.plot(c.centre['coordinate'],c.centre[key],color=color,ls=ls,label=label)
                ax.set(xlabel=coord,ylabel=r'$U(X=0.5,Z)$' if key=='U' else r'$W(X,Z=0.5)$',xlim=(0,1))
        elif kind=='local_Nu':
            for ax,wall in zip(axs,('hot','cold')):
                ax.plot(c.z,c.local[f'Nu_{wall}_primary'],color=color,ls=ls,label=label+' primary'+(' B1' if c.route=='B' else ' A1'))
                if c.route=='B': ax.plot(c.z,c.local[f'Nu_{wall}_B2_diagnostic'],color=color,ls=':',label=label+' B2 diagnostic')
                ax.set(xlabel='Z',ylabel=f'{wall}-wall local Nu',xlim=(0,1))
        elif kind=='section_Nu':
            ax=axs[0]
            ax.plot(c.section['X'],c.section['sections'],color=color,ls=ls,label=label+r' $\overline{Nu}_X$')
            ax.axhline(c.metrics['Nu_bar_cavity'],color=color,ls=':',label=label+r' $\overline{Nu}_{cavity}$')
            ax.set(xlabel='X',ylabel=r'$\overline{Nu}_X$',xlim=(0,1))
    if paper and kind=='centreline':
        for ax,key,loc in zip(axs,('Umax','Wmax'),('Umax_Z','Wmax_X')):
            ax.scatter([float(paper[loc])],[float(paper[key])],marker='*',s=95,color=COLORS['paper'],label='de Vahl Davis Table V')
    if paper and kind=='local_Nu':
        for k in ('max','min'):
            axs[0].scatter([float(paper[f'Nu_hot_local_{k}_Z'])],[float(paper[f'Nu_hot_local_{k}'])],marker='*',s=90,color=COLORS['paper'],label='Table V '+k)
    for ax in axs:
        ax.grid(alpha=.22);ax.legend(loc='best',fontsize=7)


def export_case(case, out):
    write_csv(out/'data'/f'centreline_{case.case_id}.csv',
        (dict(index=i,coordinate=q,U_at_X0_5=u,W_at_Z0_5=w) for i,(q,u,w) in enumerate(zip(case.centre['coordinate'],case.centre['U'],case.centre['V']))))
    write_csv(out/'data'/f'local_Nu_{case.case_id}.csv',
        (dict(Z=z,**{k:float(v[i]) for k,v in case.local.items()}) for i,z in enumerate(case.z)))
    write_csv(out/'data'/f'section_Nu_{case.case_id}.csv',
        (dict(X=x,Nu_bar_X=float(nu),Nu_bar_cavity=case.metrics['Nu_bar_cavity'],operator='linear cell U face interpolation' if case.route=='A' else 'native saved volume phi') for x,nu in zip(case.section['X'],case.section['sections'])))
    tm=temperature_lines(case)
    write_csv(out/'data'/f'temperature_centreline_{case.case_id}.csv',
        (dict(coordinate=q,theta_at_X0_5=float(tm['vertical'][i]),theta_at_Z0_5=float(tm['horizontal'][i])) for i,q in enumerate(tm['coordinate'])))
    # Full underlying field arrays are reusable; CSV preserves original cell-centre support.
    speed = case.speed
    write_csv(out/'data'/f'field_{case.case_id}.csv',
        (dict(X=x,Z=z,theta=float(case.theta[j,i]),U_star=float(case.velocity[j,i,0]),W_star=float(case.velocity[j,i,1]),
              depth_velocity_star=float(case.velocity[j,i,2]),speed_star=float(speed[j,i]),
              **({'rho_over_rho0_minus_1':float(case.density[j,i])} if case.route=='A' else {'rhok_buoyancy_factor':float(case.density[j,i])}))
         for j,z in enumerate(case.z) for i,x in enumerate(case.x)))


def temperature_lines(c):
    n=c.n;q=np.linspace(0,1,4097)
    vertical=.5*(c.theta[:,n//2-1]+c.theta[:,n//2])
    horizontal=.5*(c.theta[n//2-1,:]+c.theta[n//2,:])
    return dict(coordinate=q,vertical=np.interp(q,np.r_[0,c.z,1],np.r_[vertical[0],vertical,vertical[-1]]),
                horizontal=np.interp(q,np.r_[0,c.x,1],np.r_[1,horizontal,0]))


def plot_case(c,out,inventory,paper,vmax):
    folder=Path('individual') if c.category=='matrix' else Path('comparison')/c.category/'individual'
    for kind in ('temperature','streamlines','velocity_magnitude','density_deviation' if c.route=='A' else 'buoyancy_factor'):
        fig,ax=plt.subplots(figsize=(6.8,5.6),layout='constrained')
        artist,label=field(ax,c,kind,vmax,density_limit=c.manifest['properties']['beta_1_K']*c.manifest['properties']['DeltaT_K']/2 if c.route=='A' else None)
        fig.colorbar(artist,ax=ax,label=label,shrink=.88)
        save_figure(fig,out,folder/f'{c.case_id}_{kind}',inventory,kind,[c.case_id])
    for kind in ('centreline','local_Nu','section_Nu'):
        count=1 if kind=='section_Nu' else 2
        fig,axs=plt.subplots(1,count,figsize=(11.8 if count==2 else 7.6,5.3),squeeze=False,layout='constrained')
        profiles(axs[0],[c],kind,paper)
        fig.suptitle(c.title)
        if kind=='section_Nu': axs[0,0].set_title('A: interpolated cell U' if c.route=='A' else 'B: saved volume flux phi')
        save_figure(fig,out,folder/f'{c.case_id}_{kind}',inventory,kind,[c.case_id])
    fig,ax=plt.subplots(figsize=(7.6,5.3),layout='constrained');t=temperature_lines(c)
    ax.plot(t['coordinate'],t['vertical'],color=COLORS[c.route],label=r'$\theta(X=0.5,Z)$')
    ax.plot(t['coordinate'],t['horizontal'],color=COLORS[c.route],ls='--',label=r'$\theta(X,Z=0.5)$')
    if c.ra==0: ax.plot([0,1],[1,0],color='k',ls=':',label='conduction: 1-X')
    ax.set(xlabel='dimensionless centreline coordinate (X or Z)',ylabel=r'$\theta$',xlim=(0,1));ax.legend();ax.grid(alpha=.22);ax.set_title(c.title)
    save_figure(fig,out,folder/f'{c.case_id}_temperature_centreline',inventory,'temperature centreline',[c.case_id])
    export_case(c,out)
