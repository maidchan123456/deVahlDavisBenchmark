"""Matrix, grid, reference, model, and fixed-grid sensitivity comparisons."""
from pathlib import Path
from common import (plt,np,RAS,LEVELS,QOIS,COLORS,A_REVIEW,ROOT,read_csv,read_json,
                    write_csv,save_figure,check)
from plot_case import field, profiles


def lookup(cases, route, ra, level='fine'):
    return next(c for c in cases if c.category=='matrix' and c.route==route and c.ra==ra and c.case_id.endswith(level))


def montage(cases,out,inventory,scales):
    for route in 'AB':
        for kind in ('temperature','streamlines'):
            fig,axs=plt.subplots(4,3,figsize=(15,18),layout='constrained')
            ids=[]
            for j,ra in enumerate(RAS):
                artists=[]
                for k,level in enumerate(LEVELS):
                    c=lookup(cases,route,ra,level);ids.append(c.case_id)
                    artist,label=field(axs[j,k],c,kind,scales[ra]);artists.append(artist)
                    axs[j,k].set_title(f'Ra={ra:g} | {c.n}x{c.n} | {c.label}',fontsize=10)
                fig.colorbar(artists[-1],ax=axs[j,:].tolist(),label=label,shrink=.8)
            fig.suptitle(f'Route {route}: {kind} | rows: Ra; columns: 40, 80, 160',fontsize=15)
            save_figure(fig,out,Path('montage')/f'Route{route}_{kind}_12panels',inventory,f'4 Ra x 3 grid {kind}',ids)
    for kind in ('temperature','streamlines','velocity_magnitude'):
        fig,axs=plt.subplots(4,2,figsize=(12,18),layout='constrained');ids=[]
        for j,ra in enumerate(RAS):
            for k,route in enumerate('AB'):
                c=lookup(cases,route,ra);ids.append(c.case_id)
                artist,label=field(axs[j,k],c,kind,scales[ra])
            fig.colorbar(artist,ax=axs[j,:].tolist(),label=label,shrink=.8)
        fig.suptitle(f'Fine 160x160x1: Route A / Route B | {kind}',fontsize=15)
        save_figure(fig,out,Path('montage')/f'fine_AB_{kind}_8panels',inventory,kind+' fine A/B matrix',ids)
        for ra in RAS:
            pair=[lookup(cases,rt,ra) for rt in 'AB']
            pair_fields(pair,kind,out,inventory,Path('comparison')/f'fine_Ra{ra}_AB_{kind}',scales[ra])


def pair_fields(pair,kind,out,inventory,name,vmax=None,density_limit=None):
    fig,axs=plt.subplots(1,2,figsize=(12,6.2),layout='constrained')
    for ax,c in zip(axs,pair): artist,label=field(ax,c,kind,vmax,density_limit)
    fig.colorbar(artist,ax=axs.tolist(),label=label,shrink=.8)
    if pair[-1].category=='sensitivity': fig.suptitle('Gate H: fixed-grid sensitivity (160x160x1)',fontsize=13)
    save_figure(fig,out,name,inventory,kind+' pair',[c.case_id for c in pair])


def plot_grid_and_paper(cases,paper,out,inventory):
    rows=[]
    for ra in RAS:
        fig,axs=plt.subplots(1,3,figsize=(14.5,5.4),layout='constrained')
        ids=[]
        for ax,qoi in zip(axs,QOIS):
            for rt in 'AB':
                cs=[lookup(cases,rt,ra,l) for l in LEVELS];ids.extend(c.case_id for c in cs)
                diagnostic=not cs[-1].accepted
                ax.plot([c.n for c in cs],[c.metrics[qoi] for c in cs],color=COLORS[rt],marker='o' if rt=='A' else 's',
                        ls='--' if diagnostic else '-',mfc='none' if diagnostic else COLORS[rt],label=f'Route {rt}'+(' diagnostic-only' if diagnostic else ' accepted'))
            ax.axhline(float(paper[ra][qoi]),color=COLORS['paper'],ls=':',label='de Vahl Davis Table V')
            ax.set(xlabel='grid N (NxNx1)',ylabel=qoi,xticks=(40,80,160));ax.grid(alpha=.22);ax.legend(fontsize=8)
        fig.suptitle(f'Grid dependence | Ra={ra:g} (Gate F status retained)',fontsize=13)
        save_figure(fig,out,Path('comparison')/f'grid_dependence_Ra{ra}',inventory,'Nu/Umax/Wmax versus grid',sorted(set(ids)))
        for rt in 'AB':
            for l in LEVELS:
                c=lookup(cases,rt,ra,l)
                for q in QOIS:
                    ref=float(paper[ra][q]); val=c.metrics[q]
                    rows.append(dict(route=rt,Ra=ra,N=c.n,case_id=c.case_id,quantity=q,value=val,paper_value=ref,
                                     absolute_relative_error_pct=100*abs(val-ref)/abs(ref),status=c.label))
    write_csv(out/'data/grid_convergence.csv',rows)
    fine=[r for r in rows if r['N']==160]
    write_csv(out/'data/paper_comparison_fine.csv',fine)
    for qoi in QOIS:
        for error in (False,True):
            fig,ax=plt.subplots(figsize=(8.6,5.4),layout='constrained')
            for rt in 'AB':
                rr=[r for r in fine if r['route']==rt and r['quantity']==qoi]
                yy=[r['absolute_relative_error_pct'] if error else r['value'] for r in rr]
                # A is accepted at all Ra; B's final point is not joined as an accepted segment.
                n=4 if rt=='A' else 3
                ax.plot(RAS[:n],yy[:n],color=COLORS[rt],marker='o' if rt=='A' else 's',label='Route '+rt+' accepted')
                if rt=='B':
                    ax.plot(RAS[2:],yy[2:],color=COLORS[rt],ls='--')
                    ax.scatter([RAS[-1]],[yy[-1]],facecolors='none',edgecolors=COLORS[rt],marker='s',s=60,label='Route B Ra=1e6 diagnostic-only')
            if not error: ax.plot(RAS,[float(paper[ra][qoi]) for ra in RAS],color=COLORS['paper'],ls=':',marker='*',label='de Vahl Davis Table V')
            ax.set(xscale='log',xlabel='Ra',ylabel='absolute relative difference [%]' if error else qoi,
                   title=f'Fine 160x160x1 | {qoi}'+(' | vs Table V' if error else ''))
            ax.set_xticks(RAS);ax.grid(alpha=.22);ax.legend(fontsize=8)
            save_figure(fig,out,Path('comparison')/f'paper_fine_{qoi}_{"error" if error else "value"}',inventory,'paper '+('absolute relative difference' if error else 'QoI'),[lookup(cases,rt,ra).case_id for rt in 'AB' for ra in RAS])


def table_figure(rows,fields,headers,out,name,inventory,description):
    height=max(4, .28*len(rows)+1.5)
    fig,ax=plt.subplots(figsize=(15,height));ax.axis('off')
    def fmt(v):
        if isinstance(v,float): return f'{v:.6g}'
        return str(v)
    table=ax.table(cellText=[[fmt(r.get(k,'')) for k in fields] for r in rows],colLabels=headers,loc='center',cellLoc='center')
    table.auto_set_font_size(False);table.set_fontsize(8);table.scale(1,1.35)
    for (r,c),cell in table.get_celld().items():
        if r==0: cell.set_facecolor('#e4eaf1');cell.set_text_props(weight='bold')
        elif r%2==0: cell.set_facecolor('#f5f7f9')
    ax.set_title(description,pad=15)
    save_figure(fig,out,name,inventory,description,[])


def gate_f(out,inventory):
    rows=[]
    for rt,path in [('A',A_REVIEW/'RouteA_full_steady_matrix_gate_F_detail.csv'),('B',ROOT/'results/routeB/grid_convergence.csv')]:
        for r in read_csv(path):
            ra=int(r.get('Ra',r.get('Ra_target')))
            p=r['p_obs'];g=r.get('GCI_fine',r.get('GCI'))
            def numeric(v,mult=1):
                if v in ('','None','null','NOT_EVALUATED','NaN','nan'): return '未定義' if ra!=1000000 or rt=='A' else '未評価'
                return float(v)*mult
            rows.append(dict(route=rt,Ra=ra,quantity=r['quantity'],fine_medium_relative_difference_pct=numeric(r.get('fine_medium_relative_difference',r.get('fine_medium_difference')),100),
                p_obs=numeric(p),GCI_fine_pct=numeric(g,100),convergence_type=r['convergence_type'],status=r.get('status',r.get('Gate_F')),
                needs_320=r.get('needs_320',''),source_path=str(path.relative_to(ROOT))))
    write_csv(out/'data/gate_F_detail.csv',rows)
    # Render undefined/non-evaluated text in English for portable scientific fonts; Japanese CSV is explicit.
    display=[{k:('undefined' if v=='未定義' else 'not evaluated' if v=='未評価' else 'NOT EVALUATED*' if k=='status' and str(v).startswith('NOT_EVALUATED_DUE_TO_UNACCEPTED') else v) for k,v in r.items()} for r in rows]
    table_figure(display,['route','Ra','quantity','fine_medium_relative_difference_pct','p_obs','GCI_fine_pct','status'],
                  ['Route','Ra','QoI','fine-medium [%]','p_obs','GCI fine [%]','historical status'],out,Path('tables/gate_F_detail'),inventory,'Existing Gate F evidence; *B Ra=1e6: unaccepted grid (full status in source CSV)')
    return rows


def ab_comparison(cases,out,inventory):
    rows=read_csv(A_REVIEW/'RouteA_AB_Ra_trend.csv')
    for r in rows:
        a=next(c for c in cases if c.case_id==r['A_case_id']);b=next(c for c in cases if c.case_id==r['B_case_id'])
        q=r['quantity']
        if q in a.metrics and q in b.metrics and isinstance(a.metrics[q],(float,int)):
            check(a.case_id+' / '+b.case_id,'AB authority A:'+q,a.metrics[q],float(r['A']))
            check(a.case_id+' / '+b.case_id,'AB authority B:'+q,b.metrics[q],float(r['B']))
        if r['relative_difference']:
            check(r['A_case_id'],'AB relative difference:'+q,float(r['relative_difference']),abs(float(r['A'])-float(r['B']))/abs(float(r['B'])))
    write_csv(out/'data/routeA_vs_routeB_fine.csv',rows)
    selected=('Nu_bar_cavity','Nu_bar_0','Umax','Wmax','Nu_hot_local_max','Nu_hot_local_min')
    fig,axs=plt.subplots(2,3,figsize=(14.5,9),layout='constrained')
    for ax,q in zip(axs.ravel(),selected):
        rr=sorted([r for r in rows if r['quantity']==q],key=lambda r:int(r['Ra']))
        assert len(rr)==4 and all(r['comparison_class']=='LIKE_FOR_LIKE' for r in rr)
        y=[100*float(r['relative_difference']) for r in rr]
        ax.plot(RAS[:3],y[:3],color=COLORS['A'],marker='o',label='accepted A/B pair')
        ax.plot(RAS[2:],y[2:],color=COLORS['A'],ls='--')
        ax.scatter([RAS[-1]],[y[-1]],edgecolor=COLORS['A'],facecolor='none',s=60,label='B diagnostic-only')
        ax.set(xscale='log',xlabel='Ra',ylabel=r'$100|A-B|/|B|$ [%]',title=q);ax.set_xticks(RAS);ax.grid(alpha=.22);ax.legend(fontsize=7)
    fig.suptitle('Fine 160x160x1: model/formulation comparison (not an error bound)',fontsize=13)
    save_figure(fig,out,Path('comparison/routeA_vs_routeB_fine'),inventory,'six comparable QoIs A vs B',[lookup(cases,rt,ra).case_id for rt in 'AB' for ra in RAS])
    return rows


def gate_h(cases,out,inventory,paper):
    pair=[lookup(cases,'A',1000000),next(c for c in cases if c.category=='sensitivity')]
    vmax=max(float(c.speed.max()) for c in pair)
    lim=max(c.manifest['properties']['beta_1_K']*c.manifest['properties']['DeltaT_K']/2 for c in pair)
    for kind in ('temperature','streamlines','velocity_magnitude','density_deviation'):
        pair_fields(pair,kind,out,inventory,Path('comparison/sensitivity')/f'GateH_{kind}',vmax,lim)
    for kind in ('centreline','local_Nu','section_Nu'):
        count=1 if kind=='section_Nu' else 2
        fig,axs=plt.subplots(1,count,figsize=(12 if count==2 else 8,5.5),squeeze=False,layout='constrained')
        profiles(axs[0],pair,kind,paper[1000000]);fig.suptitle('Gate H: fixed-grid sensitivity; no grid independence claim')
        save_figure(fig,out,Path('comparison/sensitivity')/f'GateH_{kind}',inventory,'Gate H '+kind,[c.case_id for c in pair])
    rows=read_csv(ROOT/'results/routeA/attempts/attempt_008/GateH_comparison.csv')
    for r in rows:
        q=r['quantity']
        if q in QOIS:
            a,b=pair[0].metrics[q],pair[1].metrics[q]
            check(pair[1].case_id,'GateH baseline:'+q,a,float(r['baseline']))
            check(pair[1].case_id,'GateH perturbed:'+q,b,float(r['perturbed']))
            check(pair[1].case_id,'GateH relative difference:'+q,abs(a-b)/abs(a),float(r['relative_difference']))
    write_csv(out/'data/GateH_comparison.csv',rows)
    primary=[r for r in rows if r['quantity'] in QOIS]
    fig,ax=plt.subplots(figsize=(8,5.4),layout='constrained')
    values=[100*float(r['relative_difference']) for r in primary]
    bars=ax.bar([r['quantity'] for r in primary],values,color=COLORS['H'],width=.55)
    for b,y in zip(bars,values): ax.text(b.get_x()+b.get_width()/2,y,f'{y:.5f}%',ha='center',va='bottom')
    ax.set(ylabel=r'$100|perturbed-baseline|/|baseline|$ [%]',ylim=(0,max(values)*1.4),title='Gate H | fixed 160x160x1 | beta / 10, g x 10')
    ax.grid(axis='y',alpha=.22)
    save_figure(fig,out,Path('comparison/sensitivity/GateH_primary_relative_difference'),inventory,'Gate H three primary differences',[c.case_id for c in pair])
    diagnostics=read_json(ROOT/'results/routeA/attempts/attempt_008/GateH_diagnostics.json')
    for key,c in zip(('baseline','perturbed'),pair):
        for k,summarykey in [('rho_min','rho_min'),('rho_max','rho_max'),('max_relative_density_deviation','max_abs_rho_over_rho0_minus_1'),('temperature_symmetry','temperature_symmetry'),('velocity_symmetry','velocity_symmetry')]:
            check(c.case_id,'GateH saved diagnostic:'+k,c.summary[summarykey],diagnostics[key][k])
    write_csv(out/'data/GateH_density_diagnostics.csv',[dict(case_id=c.case_id,**diagnostics[key]) for key,c in zip(('baseline','perturbed'),pair)])
    return primary


def diagnostics(cases,out,inventory):
    rows=[]
    for c in cases:
        if c.category!='matrix': continue
        m=c.metrics;gd=m.get('Gate_D_monitor_evaluation',{})
        residuals=gd.get('final_initial_residuals',m['final_initial_residuals'])
        rwin=gd.get('Rwin',m['Rwin'])
        native=m.get('divergence',{}).get('epsilon_m') if c.route=='A' else m['continuity']['epsilon_phi']
        reconstructed=m.get('divergence',{}).get('epsilon_v') if c.route=='A' else m['continuity']['epsilon_v']
        row=dict(case_id=c.case_id,route=c.route,Ra=c.ra,N=c.n,accepted=c.status['accepted'],Gate_D=c.status['Gate_D'],
                 max_final_initial_residual=max(residuals.values()),residual_fields=residuals,
                 Rwin_Nu_bar_0=rwin.get('Nu_bar_0',rwin.get('Nu')),Rwin_Umax=rwin['Umax'],Rwin_Wmax=rwin.get('Wmax',rwin.get('Vmax')),
                 physical_heat_imbalance=m['heat_imbalance'],section_Nu_deviation=m['section_Nu_max_relative_deviation_from_half'],
                 native_continuity_indicator=native,native_operator='A corrected mass phi [kg/s]' if c.route=='A' else 'B corrected volume phi [m3/s]',
                 reconstructed_velocity_divergence_indicator=reconstructed,reconstructed_operator='Gauss linear div(U), [1/s] normalized with L/max|u|',
                 temperature_symmetry=c.summary['temperature_symmetry'],velocity_symmetry=c.summary['velocity_symmetry'],
                 symmetry_source='saved-field 180 degree paired cells; cross-checked where stored',
                 heat_slope_per_iteration=gd.get('heat_slope_per_iteration_display',m['Rwin'].get('heat_imbalance_linear_slope_per_iteration','not stored')))
        rows.append(row)
    write_csv(out/'data/convergence_conservation.csv',rows)
    for rt in 'AB':
        rr=[r for r in rows if r['route']==rt]
        keys=['max_final_initial_residual','Rwin_Nu_bar_0','Rwin_Umax','Rwin_Wmax','physical_heat_imbalance','section_Nu_deviation',
              'native_continuity_indicator','reconstructed_velocity_divergence_indicator','temperature_symmetry','velocity_symmetry']
        fig,axs=plt.subplots(5,2,figsize=(14,18),layout='constrained')
        for ax,k in zip(axs.ravel(),keys):
            values=[r[k] for r in rr]
            valid=[i for i,v in enumerate(values) if v is not None and v>0]
            zeros=[i for i,v in enumerate(values) if v==0]
            for i in valid:
                c=rr[i];diag=c['accepted'].lower() not in ('true','yes')
                ax.scatter(i,values[i],color=COLORS[rt] if not diag else 'none',edgecolor=COLORS[rt],marker='s' if rt=='B' else 'o',s=35)
            if valid: ax.set_yscale('log')
            for i in zeros: ax.text(i,.025,'0',ha='center',va='bottom',transform=ax.get_xaxis_transform())
            for i,v in enumerate(values):
                if v is None: ax.text(i,.025,'not stored',rotation=90,ha='center',transform=ax.get_xaxis_transform(),fontsize=6)
            ax.set_xticks(range(12),[f'{r["Ra"]:.0e}\nN={r["N"]}' for r in rr],rotation=45,fontsize=7)
            ax.set_title(k.replace('_',' '),fontsize=10);ax.grid(alpha=.22)
            if k=='native_continuity_indicator': ax.set_ylabel('mass-phi normalized (A)' if rt=='A' else 'volume-phi normalized (B)')
        fig.suptitle(f'Route {rt}: convergence and conservation diagnostics\nNative phi indicators have different operators/units between routes; hollow markers = diagnostic-only',fontsize=12)
        save_figure(fig,out,Path('comparison')/f'Route{rt}_convergence_conservation',inventory,'separate-route convergence/conservation indicators',[r['case_id'] for r in rr])
    density=[c.summary for c in cases if c.route=='A']
    write_csv(out/'data/routeA_density_summary.csv',density)
    fig,ax=plt.subplots(figsize=(8.5,5.5),layout='constrained')
    for level,marker in zip(LEVELS,('o','s','^')):
        cc=[lookup(cases,'A',ra,level) for ra in RAS]
        ax.plot(RAS,[c.summary['max_abs_rho_over_rho0_minus_1'] for c in cc],marker=marker,label=level)
    ax.axhline(.0005,color='k',ls=':',label='imposed-wall amplitude beta DeltaT / 2')
    ax.set(xscale='log',xlabel='Ra',ylabel=r'cell-centre max $|\rho(T)/\rho_0-1|$',title=r'Route A: temperature-dependent EOS; $\psi=0$');ax.legend();ax.grid(alpha=.22)
    save_figure(fig,out,Path('comparison/RouteA_density_amplitude'),inventory,'Route A density amplitude',[c.case_id for c in cases if c.route=='A' and c.category=='matrix'])
    return rows


def auxiliary(cases,out,inventory,paper):
    for tag in ('COND','SMOKE'):
        pair=[next(c for c in cases if c.case_id==rt+'-'+tag) for rt in 'AB']
        vmax=max(float(c.speed.max()) for c in pair) or 1
        for kind in ('temperature','streamlines'):
            pair_fields(pair,kind,out,inventory,Path('comparison/auxiliary')/f'{tag}_AB_{kind}',vmax)
    return
