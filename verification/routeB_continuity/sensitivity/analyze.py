"""Conservative response analysis, including a complete partial/STOP report."""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np

def exploration(e):
    from experiment import QOIS,VALUES,POSITIONS
    chosen=[r for r in e.records if r['phase']=='exploration' and r['status']=='STEADY' and r['source_realization']['validated'] and (r['role']=='arm2' or r.get('included_in_arm2_exploration') or r['role']=='matching')]
    natural=[r for r in e.records if r['phase']=='exploration' and r['status']=='STEADY' and r['role']=='arm1' and r['manifest']['n'] in e.baselines]
    order={'arm1':{'supported':[],'violations':[]},'arm2':{'supported':[],'violations':[]}}
    for arm,group in [('arm1',natural),('arm2',chosen)]:
        groups={}
        for r in group:
            m=r['manifest'];key=(m['n'],m['pattern'] if arm=='arm2' else 'natural',m['sign'])
            groups.setdefault(key,[]).append(r)
        for key,data in groups.items():
            data=sorted(data,key=lambda r:r['metrics']['epsilon_phi_mean'])
            for a,b in zip(data,data[1:]):
                da=e.comparison(a);db=e.comparison(b)
                for q in QOIS:
                    if da[q]['upper_impact']<db[q]['lower_impact']:
                        order[arm]['supported'].append({'a':a['id'],'b':b['id'],'qoi':q})
                    elif da[q]['lower_impact']>db[q]['upper_impact']:
                        order[arm]['violations'].append({'a':a['id'],'b':b['id'],'qoi':q})
    def trend(item):
        return 'NOT_SUPPORTED' if item['violations'] else ('SUPPORTED' if item['supported'] else 'INCONCLUSIVE')
    pairs=[]
    by_id={r['id']:r for r in e.records}
    for r in chosen:
        if r.get('same_mean_matched'):
            a=by_id[r['same_mean_group']];da=e.comparison(a);dr=e.comparison(r)
            differences=[q for q in QOIS if abs(da[q]['Delta_Q']-dr[q]['Delta_Q'])>da[q]['uncertainty']*da[q]['scale']+dr[q]['uncertainty']*dr[q]['scale']]
            pairs.append({'a':a['id'],'b':r['id'],'different_QoIs':differences,'max_ratio_a':a['metrics']['max_over_mean'],'max_ratio_b':r['metrics']['max_over_mean'],'actual_mean_relative_difference':abs(a['metrics']['epsilon_phi_mean']-r['metrics']['epsilon_phi_mean'])/a['metrics']['epsilon_phi_mean']})
    different=[p for p in pairs if p['different_QoIs']]
    local=[p for p in different if 'P4' in p['b'] and abs(p['max_ratio_a']-p['max_ratio_b'])>1]
    sign_pairs=[]
    for r in chosen:
        if r['manifest']['sign']<0:
            same=[a for a in chosen if a['manifest']['n']==r['manifest']['n'] and a['manifest']['pattern']==r['manifest']['pattern'] and a['manifest']['eta_nom']==r['manifest']['eta_nom'] and a['manifest']['sign']>0]
            if same:
                a=same[0];da=e.comparison(a);dr=e.comparison(r)
                resolved=[q for q in QOIS if abs(da[q]['Delta_Q']-dr[q]['Delta_Q'])>da[q]['uncertainty']*da[q]['scale']+dr[q]['uncertainty']*dr[q]['scale']]
                asym=[q for q in QOIS if abs(da[q]['Delta_Q']+dr[q]['Delta_Q'])>da[q]['uncertainty']*da[q]['scale']+dr[q]['uncertainty']*dr[q]['scale']]
                sign_pairs.append({'positive':a['id'],'negative':r['id'],'signed_response_different':resolved,'departure_from_antisymmetry':asym})
    # Natural/artificial equivalence is not inferred from lack of significance.
    cross=[]
    tolerance=0.
    from experiment import RESULTS
    if (RESULTS/'same_mean_matching_rule.json').exists(): tolerance=json.loads((RESULTS/'same_mean_matching_rule.json').read_text())['relative_tolerance']
    for a in natural:
        for r in chosen:
            if a['manifest']['n']!=r['manifest']['n']: continue
            if abs(a['metrics']['epsilon_phi_mean']-r['metrics']['epsilon_phi_mean'])/a['metrics']['epsilon_phi_mean']>tolerance: continue
            da=e.comparison(a);dr=e.comparison(r)
            differences=[q for q in QOIS if abs(da[q]['Delta_Q']-dr[q]['Delta_Q'])>da[q]['uncertainty']*da[q]['scale']+dr[q]['uncertainty']*dr[q]['scale']]
            cross.append({'natural':a['id'],'controlled':r['id'],'different_QoIs':differences})
    h4='NOT_SUPPORTED' if any(p['different_QoIs'] for p in cross) else 'INCONCLUSIVE'
    envelope={}
    for r in chosen:
        eta=r['manifest']['eta_nom'];key=f'{eta:.17g}'
        entry=envelope.setdefault(key,{q:0. for q in QOIS})
        for q,d in e.comparison(r).items(): entry[q]=max(entry[q],d['upper_impact'])
    resolved={q:[r['id'] for r in chosen+natural if e.comparison(r)[q]['resolved']] for q in QOIS}
    return {'grids':[20,40],'status':'PARTIAL' if e.status['stop'] or not chosen else 'PASS','hypotheses':{'H1':trend(order['arm2']),'H2':'SUPPORTED' if different else 'INCONCLUSIVE','H3':'SUPPORTED' if local else 'INCONCLUSIVE','H4':h4},'arm1_response_relation':trend(order['arm1']),'order_comparisons':order,'same_mean_pairs':pairs,'local_max_added_information_basis':local,'sign_pairs':sign_pairs,'natural_controlled_actual_mean_pairs':cross,'resolved_QoIs':resolved,'response_envelope_v1':envelope,'envelope_scope':'Observed required exploratory patterns, signs, two grids at tested nominal levels; not a continuous or universal bound','quota_pass_fail_performed':False}

def confirmation_analysis(e,manifest):
    from experiment import QOIS
    runs=[r for r in e.records if r['phase']=='confirmation' and r['role']=='arm2']
    v1=manifest['exploration_model_v1']['response_envelope_v1']
    comparisons=[]
    for r in runs:
        key=f"{r['manifest']['eta_nom']:.17g}";frozen=v1[key]
        response=e.comparison(r)
        outside=[q for q in QOIS if response[q]['lower_impact']>frozen[q]]
        comparisons.append({'id':r['id'],'outside_exploration_envelope':outside,'response':response})
    complete=len(runs)==8 and all(r['status']=='STEADY' and r['source_realization']['validated'] for r in runs)
    any_outside=any(c['outside_exploration_envelope'] for c in comparisons)
    return {'status':'PASS' if complete and not any_outside else 'PARTIAL','execution_complete':complete,'exploration_envelope_supported_at_tested_conditions':complete and not any_outside,'outside_envelope_runs':[c['id'] for c in comparisons if c['outside_exploration_envelope']],'comparisons':comparisons,'exploration_model_modified_after_confirmation':False,'scientific_quota_pass_fail':False,'interpretation':'Envelope compatibility is finite-scope evidence, not equivalence proof. Concentrated physical support changes with grid refinement.'}

def finalize(e):
    from experiment import HERE,ROOT,RESULTS,QOIS,VALUES,POSITIONS,dump,csvwrite,sha,RUNS
    ex=e.status['exploration'] or exploration(e)
    dump(RESULTS/'exploration_summary.json',ex)
    cf=e.status['confirmation'] or {'status':'NOT_RUN','exploration_model_modified_after_confirmation':False}
    dump(RESULTS/'confirmation_results.json',cf)
    dump(RESULTS/'temperature_offset_diagnostic.json',e.status['temperature_offset'])
    run_rows=[];metric_rows=[];source_rows=[];qoi_rows=[];unc_rows=[];baseline_rows=[];arm1=[];arm2=[]
    for r in e.records:
        m=r['manifest'];meta={'run_id':r['id'],'n':m['n'],'role':r['role'],'phase':r['phase'],'status':r['status'],'iteration':r['iteration'],'p_tolerance':m['tolerance'],'eta_nom':m['eta_nom'],'pattern':m['pattern'],'sign':m['sign'],'temperature_offset':m['temperature_offset']}
        row={**meta,**r['qoi'],**r['metrics']}
        metric_rows.append({**meta,**r['metrics'],**{k:r['audit'][k] for k in ['Np','R_recursive','R_true','true_nonreference_L1','true_reference_residual']}})
        source_rows.append({**meta,**{k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r['source_realization'].items()}})
        if r['id'].startswith('baseline_'): baseline_rows.append(row)
        if r['role']=='arm1': arm1.append(row)
        if r['role'] in ('arm2','pilot','matching'): arm2.append(row)
        for q in QOIS:
            unc_rows.append({**meta,'qoi':q,**r['uncertainty'][q]})
        if m['n'] in e.baselines and r['status']=='STEADY' and r['role'] in ('arm1','arm2','pilot','matching'):
            for q,d in e.comparison(r).items():
                qoi_rows.append({**meta,'qoi':q,'source_valid':r['source_realization']['validated'],'included_in_arm2_exploration':r.get('included_in_arm2_exploration',False),'epsilon_phi_mean':r['metrics']['epsilon_phi_mean'],'epsilon_phi_max':r['metrics']['epsilon_phi_max'],'max_over_mean':r['metrics']['max_over_mean'],**d})
    for a in e.status['solver_attempts']:
        if a['status']=='RUNNING': a['status']='STOPPED_WITH_ERROR'
        run_rows.append(a)
    for name,data in [('run_manifest.csv',run_rows),('baseline_summary.csv',baseline_rows),('arm1_results.csv',arm1),('arm2_results.csv',arm2),('qoi_response.csv',qoi_rows),('continuity_metrics.csv',metric_rows),('uncertainty_summary.csv',unc_rows),('source_realization.csv',source_rows)]: csvwrite(name,data)
    valid=[r for r in e.records if r['manifest']['eta_nom'] and r['source_realization']['validated'] and r['status']=='STEADY']
    mapping={'available':bool(valid),'quota_values_selected':False,'tau_mean_selected':False,'rule':'Given an externally justified vector b_Q, select only tested required levels with all same-QoI upper_impact<=b_Q, complete pattern/sign/grid coverage and contiguous lower-level evidence; no interpolation or untested-pattern guarantee. Data are finite scoped candidates only.','rows':[x for x in qoi_rows if x['source_valid']],'scope':'Ra30000 specified grids/operators/profile and observed patterns only'}
    dump(RESULTS/'conditional_mapping.json',mapping)
    arm1_runs=[r for r in e.records if r['role']=='arm1']
    arm2_runs=[r for r in e.records if r['role'] in ('arm2','pilot','matching')]
    errors=[r['source_realization']['actual_source_relative_error'] for r in valid]
    fig_files=figures(qoi_rows)
    summary={'schema':'routeB-gateG-independent-qoi-sensitivity-v1','formal_benchmark_results_used':False,'solver_executed':e.status['solver_executed'],'formal_benchmark_solver_executed':False,
      'preregistration':{'file':str(HERE/'experiment_preregistration_v1.json'),'sha256':sha(HERE/'experiment_preregistration_v1.json'),'markdown_sha256':sha(HERE/'experiment_preregistration_v1.md'),'immutable':True},
      'microcase':{'Ra_test':30000,'Pr':.71,'grids':[20,40,80],'beta':30000*1e-6*(1e-6/.71)/(9.81*.01**3),'serial':True,'precision':'DP','serialization':'ASCII16'},
      'experiment_status':'PARTIAL' if e.status['stop'] else 'YES','STOP_reason':e.status['stop'],
      'exploration':{'grids':[20,40],'status':ex['status'],'arm1':{'executed':len([r for r in arm1_runs if r['phase']=='exploration']),'steady':len([r for r in arm1_runs if r['phase']=='exploration' and r['status']=='STEADY'])},'arm2':{'executed':len([r for r in arm2_runs if r['phase']=='exploration']),'steady':len([r for r in arm2_runs if r['phase']=='exploration' and r['status']=='STEADY'])},'hypotheses':ex['hypotheses']},
      'confirmation':{'grid':80,'manifest_sha256':sha(RESULTS/'confirmation_manifest_v1.json') if (RESULTS/'confirmation_manifest_v1.json').exists() else None,'status':cf['status'],'exploration_model_modified_after_confirmation':False},
      'zero_source_equivalence':e.status['zero_source_equivalence'],
      'source_realization':{'status':'YES' if valid and all(r['source_realization']['validated'] for r in arm2_runs) else ('PARTIAL' if valid or e.status['source_sign']=='PLUS_G' else 'NO'),'source_sign':e.status['source_sign'],'error_range':{'relative_L1_min':min(errors) if errors else None,'relative_L1_max':max(errors) if errors else None},'scope':'Steady valid source runs; invalid pilot levels retained separately'},
      'temperature_offset':e.status['temperature_offset'],
      'qoi_response':{q:{'resolved_runs':[x['run_id'] for x in qoi_rows if x['qoi']==q and x['resolved'] and x['source_valid']],'unresolved_runs':[x['run_id'] for x in qoi_rows if x['qoi']==q and not x['resolved']]} for q in QOIS},
      'arm1_response_relation':ex['arm1_response_relation'],'same_mean_pattern_dependence':ex['hypotheses']['H2'],'local_max_added_information':ex['hypotheses']['H3'],'arm1_arm2_equivalence':ex['hypotheses']['H4'],
      'conditional_mapping_available':bool(valid),'qoi_impact_quota_value':None,'qoi_impact_quota_status':'UNRESOLVED','tau_mean':None,'tau_mean_status':'UNRESOLVED','candidate_B_status':'PROVISIONAL','current_formal_Ra1e3_gate_G':'FAIL','new_spec_Ra1e3_gate_G':'NOT_EVALUATED','criteria_modified':False,'spec_change_executed':False,'user_decision_required':True,'pilot_selection':e.status['pilot'],
      'run_counts':{'all_solver_invocations':len(run_rows),'arm1_executed':len(arm1_runs),'arm1_steady':sum(r['status']=='STEADY' for r in arm1_runs),'arm2_executed':len(arm2_runs),'arm2_steady':sum(r['status']=='STEADY' for r in arm2_runs)},'figures':fig_files,
      'limitations':['No externally justified scientific b_Q','No tau_mean adoption','Finite tested patterns and only Ra30000','Artificial absolute-T source system is not original source-free PDE','Extrema sampling uncertainty can obscure small shifts','Conservative numerical envelope is empirical, not a certified error bound','No formal or Route A results read or executed']}
    summary['accepted_baseline_count']=len(e.baselines)
    summary['baseline_candidates']=[{'id':r['id'],'n':r['manifest']['n'],'status':r['status'],'accepted':r['manifest']['n'] in e.baselines} for r in e.records if r['id'].startswith('baseline_')]
    summary['unexecuted_due_to_STOP']=['source_sign_test','Arm1_remaining_conditions','Arm2_pilot_and_exploration','temperature_offset_diagnostic','confirmation_registration','80_holdout'] if e.status['stop'] else []
    summary['confirmation_manifest_created']=(RESULTS/'confirmation_manifest_v1.json').exists()
    summary['convergence_diagnostics_file']='convergence_diagnostics.json' if (RESULTS/'convergence_diagnostics.json').exists() else None
    report(e,summary,ex,cf,qoi_rows)
    dump(RESULTS/'experiment_summary.json',summary)
    provenance=json.loads((RESULTS/'startup_provenance.json').read_text())
    unchanged={p:sha(ROOT/p)==h for p,h in provenance['protected_hashes'].items()}
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    diff=subprocess.check_output(['git','diff','--stat'],cwd=ROOT,text=True)
    dump(RESULTS/'final_git_validation.json',{'git_status_short':status,'git_diff_stat':diff,'protected_hashes_unchanged':unchanged,'tracked_changes':subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()})
    hashes={p.name:sha(p) for p in RESULTS.iterdir() if p.is_file() and p.name not in ('artifact_hashes.json',)}
    dump(RESULTS/'artifact_hashes.json',hashes)
    print(json.dumps({'experiment_status':summary['experiment_status'],'STOP':e.status['stop'],'counts':summary['run_counts'],'exploration':ex['hypotheses'],'confirmation':cf['status']},indent=2),flush=True)

def figures(data):
    from experiment import RESULTS,VALUES,POSITIONS
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=RESULTS/'figures';folder.mkdir(exist_ok=True)
    files=[]
    specs=[('epsilon_mean_value',VALUES,'epsilon_phi_mean'),('epsilon_mean_position',POSITIONS,'epsilon_phi_mean'),('epsilon_max_response',VALUES,'epsilon_phi_max'),('max_mean_response',VALUES,'max_over_mean'),('arm1_vs_arm2',VALUES,'epsilon_phi_mean'),('pattern_comparison',VALUES,'epsilon_phi_mean'),('exploration_vs_confirmation',VALUES,'epsilon_phi_mean')]
    for name,qois,xkey in specs:
        fig,axes=plt.subplots(len(qois),1,figsize=(8,2.4*len(qois)),squeeze=False)
        for ax,q in zip(axes[:,0],qois):
            selected=[r for r in data if r['qoi']==q and r[xkey] is not None and r[xkey]>0 and r['source_valid']]
            for r in selected:
                color={'arm1':'C0','pilot':'C1','arm2':'C2','matching':'C3'}.get(r['role'],'C4')
                marker='s' if r['phase']=='confirmation' else ('o' if r['resolved'] else 'x')
                ax.errorbar(r[xkey],r['E_Q'],yerr=r['uncertainty'],fmt=marker,color=color,alpha=.7)
            if selected: ax.set_xscale('log')
            else: ax.text(.5,.5,'No eligible sensitivity observations',ha='center',transform=ax.transAxes)
            ax.set_ylabel(q+' impact');ax.set_xlabel(xkey);ax.grid(alpha=.2)
            ax.set_ylim(bottom=0)
        fig.suptitle(name+' (linear impact; no artificial floor)\nblue: Arm1; orange/green: controlled; square: holdout; x: unresolved')
        fig.tight_layout();path=folder/(name+'.png');fig.savefig(path,dpi=130);plt.close(fig);files.append(str(path))
    # Optional log-log resolved-only plot; zero/unresolved values are omitted, never floored.
    fig,ax=plt.subplots(figsize=(8,5))
    for q in VALUES:
        selected=[r for r in data if r['qoi']==q and r['resolved'] and r['E_Q']>0 and r['epsilon_phi_mean']>0 and r['source_valid']]
        if selected: ax.scatter([r['epsilon_phi_mean'] for r in selected],[r['E_Q'] for r in selected],label=q)
    if ax.collections: ax.set_xscale('log');ax.set_yscale('log');ax.legend()
    else: ax.text(.5,.5,'No resolved positive differences',ha='center',transform=ax.transAxes)
    ax.set_xlabel('epsilon_phi_mean');ax.set_ylabel('Relative QoI impact');fig.tight_layout();path=folder/'resolved_log_log.png';fig.savefig(path,dpi=130);plt.close(fig);files.append(str(path))
    return files

def report(e,s,ex,cf,data):
    from experiment import RESULTS,QOIS,HERE
    headings=['Purpose','Independence from formal benchmark','Preregistration','Microcase','Baseline','Numerical stopping criteria','Verification-only source solver','Zero-source stock equivalence','Source realization verification','Arm 1 design','Arm 1 results','Arm 2 design','Pilot amplitude study','Arm 2 exploration results','Temperature-offset diagnostic','Mean versus local defect','Pattern and sign sensitivity','QoI uncertainty','Exploration hypotheses','Confirmation preregistration','80² holdout confirmation','Exploration versus confirmation','Conditional epsilon-to-QoI mapping','Implications for Budget C','What this experiment does NOT justify','tau_mean status','Limitations','Required user decision']
    body={
      1:'独立continuity defect → QoI responseのcalibration evidenceを取得する。研究acceptance quotaやtau_meanは決めない。'+(' **STOP: '+str(e.status['stop'])+'。以後solver実行を停止し、partial evidenceを保存した。**' if e.status['stop'] else ''),
      2:'formal Ra=1e3/1e4/1e5/1e6 field/log/Gate E/F/conservation値、Route A、原論文を使用していない。全solver/mesh callをsensitivity/runsとRa_test=30000/grid20/40/80のallowlistで検証。production/stock installation/仕様を変更していない。',
      3:'solver実行前にv1 Markdown/JSONを固定。JSON SHA256: `'+s['preregistration']['sha256']+'`。実行中guardでhashを再確認。原登録は編集していない。数値停止条件は研究quotaではない。',
      4:'Ra_test=30000、Pr=.71、L=.01m、depth=.001m、Th/Tc/TRef=301/300/300.5K、nu=1e-6、alpha=nu/Pr。betaはscriptでRa*nu*alpha/(g*DeltaT*L³)から計算し各run manifestに保存: '+str(s['microcase']['beta'])+' 1/K。four walls=noSlip/impermeable、left hot/right cold、top/bottom adiabatic、front/back empty、laminar serial DP ASCII16。20/40=exploration、80=holdout。',
      5:'各gridのzero-source p_rgh tolerance1e-10/relTol0をhighest-fidelity tested numerical baseline候補とする。全primary比較はsame-grid。truth/exactとは呼ばない。Accepted baseline数: '+str(len(e.baselines))+'。取得baseline: '+(', '.join(r['id'] for r in e.baselines.values()) or 'なし')+'。NOT_CONVERGED候補をreferenceに採用していない。',
      6:'minimum400、20 iterationごとに全7QoI、U/T変化、mean/max、heat monitor。200 iteration windowを満たし、さらに200継続確認、maximum12000。value range/U/T change1e-8、position1/4096、heat range1e-8。他equation initial residual<=1e-8、pressure final<=1.1×そのrunのtolerance。圧力1e-6に1e-10を課していない。normal exit/finite必須。max到達未達はNOT_CONVERGEDとSTOP。末尾の個別criterion、全7QoI Rwinとfield変化はconvergence_diagnostics.json / baseline_rwin_history.csvへ記録。',
      7:'stock v6 sourceを新規auditSolverへコピーし、別binary buoyantBoussinesqSimpleFoamContinuitySourceAuditを作成。UEqn/TEqn/correction order/relaxationは不変。元physical matrixをcopyして監査、pressure source()からV*s=gを引きreference後solve。v6 fvMatrix.C:1458のmatrix==fieldはsourceへV*fieldを加えるので、元q=b0−A0pに対しq≈+gを狙う。s units1/sをruntime検証。source固定、Up feedbackなし。',
      8:'status='+s['zero_source_equivalence']['status']+'。代表20²/cold-start10 iterationsのU/T/p_rgh/phi全ファイルSHA256で比較。詳細はzero_source_equivalence.json。非同値なら非zero試験へ進まない。',
      9:'source sign='+str(s['source_realization']['source_sign'])+'、status='+s['source_realization']['status']+'、steady valid relative L1(q−g) range='+str(s['source_realization']['error_range'])+'。sum/max abs(q−g)、q+g、sum g/q、reference-aware residual、wall/closure、source cell/face supportをCSV/個別JSONへ保存。source purity5%は実験解釈の条件で研究quotaではない。invalid pilot levelsは保持しcurve採用しない。',
      10:'各gridのpressure absolute tolerance1e-6/1e-8/1e-10、relTol0。physics/BC/schemes/relaxation/U/T solver/cold-startを固定。pressure変更はcoupled trajectoryも変えるためpure continuity-onlyとは主張しない。',
      11:'Arm1 executed/steady='+str(s['run_counts']['arm1_executed'])+'/'+str(s['run_counts']['arm1_steady'])+'。epsilon→QoI relation='+ex['arm1_response_relation']+'。全7QoIとcontinuity/residual/Up/RwinをCSV保存。nonsteadyをcurveへ採用していない。',
      12:'P1 centre、P2 near_hot、P3 near_cold、P4 four-site spread、P5 reference vicinityを実装。dimensionless anchors、nearest internal X-face、face-ID tie break、pRefCell incident face除外を固定。g=B_h*aでzero-net、4-site L1はsingle-siteと同一。eta_nomはUp_baseで定義、actual epsilonは測定。perturbed discrete numerical systemへのresponseであり、元source-free PDEのaccepted解ではない。',
      13:'20² P1 positive pilot levels1e-8..1e-4。選定ruleは最低resolved level＋次の2有効level（不足なら最高3とresolution incomplete）。結果: '+str(e.status['pilot'])+'。amplitudeはresearch thresholdではない。',
      14:'Arm2 pilot/exploration/matching/confirmationのexecuted/steady='+str(s['run_counts']['arm2_executed'])+'/'+str(s['run_counts']['arm2_steady'])+'。20/40 P1/P2/P4、3 level、positiveとmid P1/P2 negativeを予定。全trialを保存し、match失敗はinconclusive。',
      15:json.dumps(e.status['temperature_offset'],ensure_ascii=False)+'。20-gridの+50K offsetはinterpretation diagnosticのみ。TEqnのdiv(phi,T)にT*div(phi)応答があり、theta置換やcompensating heat sourceを加えていない。',
      16:'same-mean pattern dependence='+ex['hypotheses']['H2']+'、local max added information='+ex['hypotheses']['H3']+'。actual meanのmatching toleranceはsource realization/repeatabilityだけから作り、QoIを見て決めない。nominal同値だけでsame meanにしない。max/mean/location/P99を保存しmax Hard/trigger cutoffを選ばない。',
      17:'actual-mean matched pairs: '+json.dumps(ex['same_mean_pairs'],ensure_ascii=False)+'\n\nSign pairs: '+json.dumps(ex['sign_pairs'],ensure_ascii=False)+'。差の有意性は保守的uncertainty envelope内でのresolved responseを意味し、科学的許容性ではない。',
      18:'baseline＋testのtail window/continuation差、4097/8193 samplingとpeak tie/position resolution、memory/file差、同grid restart差を保守的に合成。独立RSSを用いない。near-zero branchはbaseline uncertaintyで事前定義。observed difference<=uncertaintyはEFFECT_NOT_RESOLVEDでありZERO_EFFECTではない。細かいsamplingも離散化真値を提供しない。',
      19:'H1-H4='+json.dumps(ex['hypotheses'],ensure_ascii=False)+'。根拠pairとmonotonicityの支持/違反はexploration_summary.jsonに保存。空の比較集合をNOT_SUPPORTEDへ読み替えない。',
      20:'confirmation manifest SHA256='+str(s['confirmation']['manifest_sha256'])+'。探索解析後にだけ作成し、v1を固定。未到達時はmanifestを偽って作らない。予定は80、Arm1全3 tolerance、P1 seen/P3 held-out、2 amplitude×positive/negative。',
      21:'status='+cf['status']+'。80 nonzero結果を探索中に見ていない。固定manifest以外の条件を結果閲覧後に追加していない。',
      22:json.dumps(cf,ensure_ascii=False)+'。outside-envelopeデータを削除せず、exploration_model_v1をretroactiveに変更しない。confirmationはquota PASS/FAILではない。',
      23:'conditional mapping available='+str(s['conditional_mapping_available'])+'。conditional_mapping.jsonにfinite tested response upper envelopesと外部b_Qが与えられた場合のcandidate選択ruleを保存。連続補間や未試験patternを保証せず、今回は数値b_Q/tauを選ばない。',
      24:'Budget Cのmean Hard候補、max/boundary/closure investigationとdiagnosticsという役割を維持する。local/pattern response evidenceはmean-only characterizationの限界を検討する材料。正式Gate Gの変更やmax Hard採用はしない。',
      25:'今回の観測差からquotaを作らない。measurement capability/source-purity rule/steady ruleはresearch acceptance thresholdではない。formal matrixへの適用、任意pattern保証、Candidate B正式採用を正当化しない。',
      26:'TAU_MEAN=UNRESOLVED、QOI_IMPACT_QUOTA_VALUE/STATUS=UNRESOLVED、CANDIDATE_B_STATUS=PROVISIONAL、NEW_SPEC_RA1E3_GATE_G=NOT_EVALUATED。',
      27:'有限grid/有限pattern/人工source/absolute-temperature coupling/uncertaintyに限定。'+('STOPにより非zero source sign/purity、pilot、response、offset、80 holdoutを未検証。unexecuted scheduler/analysis branchesの正しさもsolver evidenceで確認していない。confirmation_manifest_v1は探索が未完了なので作成していない。全curve図はNo eligible sensitivity observationsと明記した空図であり、response dataを意味しない。' if e.status['stop'] else '')+'保存fieldはignored runs内にのみ置き、compact CSV/JSON/hashes/figuresを成果物とする。初回環境取得でWM_BASH_FUNCTIONS継承由来のshell警告が出たが、実行logは全てFoundation v6/serialを確認。fresh-shell環境取得を専用script側で修正した（STOP後solver再実行なし）。',
      28:('STOP理由を解消する別taskと事前登録amendmentを許可するかが次の判断。現taskではこれ以上solverを実行しない。' if e.status['stop'] else '独立研究目的に基づくQoI別b_Qとscope-extension方針を定めるかが次の判断。観測impactだけからquotaを逆算しない。')+'仕様変更、git add/commit/push、formal再評価は実施していない。'
    }
    text='# Route B Gate G Independent QoI Sensitivity Experiment\n\n'
    for i,h in enumerate(headings,1): text+=f'## {i}. {h}\n\n{body[i]}\n\n'
    (RESULTS/'experiment_report.md').write_text(text)
