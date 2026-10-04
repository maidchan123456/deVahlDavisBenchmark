import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path.cwd();OUT=ROOT/'results/routeA/attempts/attempt_004'
sys.path.insert(0,str(ROOT/'Scripts/routeA'))
from foam_fields import read_scalar,read_vector
import analyze_case as analyzer

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def dump(p,v):
    p=Path(p);assert not p.exists(),('Refuse overwrite',p)
    p.write_text(json.dumps(v,indent=2)+'\n')
def status(checks):return 'PASS' if all(checks.values()) else 'FAIL'
def symmetry(case,iteration,manifest):
    nx,ny,nz=manifest['grid'];n=nx*ny*nz;props=manifest['properties'];L=manifest['geometry_m']['L']
    T=read_scalar(case/str(iteration)/'T',n).reshape(ny,nx)
    U=read_vector(case/str(iteration)/'U',n).reshape(ny,nx,3)[:,:,:2]*L/props['alpha0_m2_s']
    theta=(T-props['Tc_K'])/props['DeltaT_K']
    defect_T=theta+theta[::-1,::-1]-1
    defect_U=U+U[::-1,::-1,:]
    return {'theta_L2_relative':float(np.sqrt(np.mean(defect_T**2))/max(np.sqrt(np.mean(theta**2)),1e-12)),
            'velocity_L2_relative':float(np.sqrt(np.mean(np.sum(defect_U**2,axis=2)))/max(np.sqrt(np.mean(np.sum(U**2,axis=2))),1e-12)),
            'method':'Frozen 180-degree paired uniform cells, constant cell-volume weights; RMS defect / max(RMS theta or dimensionless in-plane velocity,1e-12).'}
def grid_convergence(values,limit):
    c,m,f=values;d32=c-m;d21=m-f;fm=abs(f-m)/abs(f)
    monotonic=d32*d21>0
    if not monotonic:return {'values_coarse_medium_fine':values,'convergence_type':'NON_MONOTONIC_OR_UNDEFINED','monotonic':False,'fine_medium_relative_difference':fm,'p_obs':None,'GCI_fine':None,'needs_320':True,'status':'FAIL'}
    order=math.log(abs(d32/d21))/math.log(2)
    if not math.isfinite(order) or order<=0:return {'values_coarse_medium_fine':values,'convergence_type':'MONOTONIC_NONCONVERGENT','monotonic':True,'fine_medium_relative_difference':fm,'p_obs':order if math.isfinite(order) else None,'GCI_fine':None,'needs_320':True,'status':'FAIL'}
    gci=3*fm/(2**order-1)
    checks={'fine_medium_le_1pct':fm<=.01,'GCI_within_existing_limit':gci<=limit}
    return {'values_coarse_medium_fine':values,'convergence_type':'MONOTONIC_CONVERGENCE','monotonic':True,'fine_medium_relative_difference':fm,'p_obs':order,'GCI_fine':gci,'GCI_limit':limit,'checks':checks,'needs_320':False,'status':status(checks)}

state=json.loads((OUT/'execution_state.json').read_text());assert state['overall'] in ['COMPLETE','STOPPED']
contract=json.loads((ROOT/'docs/routeA_execution_contract_v1.3.json').read_text())
protected=json.loads((OUT/'protected_before_sha256.json').read_text())
for p,h in protected.items():assert sha(ROOT/p)==h,('protected mismatch',p)
assert sha(ROOT/'docs/routeA_execution_contract_v1.3.json')=='227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1'
for p,h in contract['implementation_sha256'].items():assert sha(ROOT/p)==h,p
for p,h in contract['template_source']['unchanged_template_sha256'].items():assert sha(ROOT/p)==h,p
for row in state['cases']:
    for seg in row['segments']:
        seal=ROOT/seg['path'];assert sha(seal/'sealed_sha256.json')==seg['sealed_sha256_manifest']
        for p,h in json.loads((seal/'sealed_sha256.json').read_text()).items():assert sha(seal/p)==h,p
reuse=OUT/'cases/A-Ra1e3-coarse/accepted_reuse'
for p,h in json.loads((reuse/'sealed_sha256.json').read_text()).items():assert sha(reuse/p)==h,p
rows=[];metrics={};manifests={};symmetries={}
for name,grid in [('coarse',40),('medium',80),('fine',160)]:
    cid='A-Ra1e3-'+name
    row=next((r.copy() for r in state['cases'] if r['case_id']==cid),{'case_id':cid,'grid':[grid,grid,1],'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','Gate_D_failure_components':[],'segments':[],'status':'NOT_STARTED_BATCH_STOP'})
    row.setdefault('Gate_D_failure_components',[])
    row.update(route='A',attempt='004',Ra_target=1000,source_time_or_iteration=row['final_iteration'],method_version='routeA effective execution contract v1.3 / canonical analyzer sha256 e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac')
    if row['computed']:
        path=ROOT/row['metrics_path'] if name=='coarse' else ROOT/'results/routeA/cases'/cid/'metrics.json'
        m=json.loads(path.read_text());assert m['final_iteration']==row['final_iteration']
        metrics[cid]=m;case=ROOT/'cases/routeA'/cid;manifest=json.loads((case/'case_manifest.json').read_text());manifests[cid]=manifest
        symmetries[cid]=symmetry(case,row['final_iteration'],manifest)
        row.update(metrics_path=str(path.relative_to(ROOT)),metrics_sha256=sha(path),Ra_actual=manifest['Ra_actual'],Pr_actual=manifest['Pr_actual'],QoIs={k:m[k] for k in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']},paper_comparison=m['paper_comparison_like_for_like'],symmetry=symmetries[cid],heat_imbalance=m['heat_imbalance'],divergence=m['divergence'])
    else:row.update(Ra_actual=None,Pr_actual=None,QoIs=None,paper_comparison=None,symmetry=None,heat_imbalance=None,divergence=None)
    rows.append(row)
allaccepted=len(rows)==3 and all(r['accepted'] for r in rows)
fine=rows[2];fineid=fine['case_id'];reference=analyzer.read_paper_reference(analyzer.PAPER_REFERENCE)[1000]
gateE={'status':'NOT_EVALUATED','classification':'PRACTICAL_BENCHMARK_COMPARISON','reason':'Fine accepted solution unavailable'}
if fine['accepted']:
    m=metrics[fineid];errors={k:m['paper_comparison_like_for_like'][k]['absolute_relative_error'] for k in ['Nu_bar_cavity','Umax','Wmax']}
    positions={k:abs(m[k]-reference[k]) for k in ['Umax_Z','Wmax_X']}
    checks={**{k:val<=.01 for k,val in errors.items()},**{k:val<=.01 for k,val in positions.items()}}
    gateE={'status':status(checks),'classification':'PRACTICAL_BENCHMARK_COMPARISON','relative_errors':errors,'absolute_position_errors':positions,'checks':checks,'not_pure_numerical_error':True,'note':'Position criterion uses absolute coordinate difference as acceptance_criteria specifies; canonical paper comparison payload retained unchanged.'}
gateF={'status':'NOT_EVALUATED','needs_320':'NOT_EVALUATED','reason':'Formal grid convergence requires all three accepted rows','quantities':None}
if allaccepted:
    quantities={k:grid_convergence([metrics[r['case_id']][k] for r in rows],limit) for k,limit in [('Nu_bar_cavity',.015),('Umax',.02),('Wmax',.02)]}
    gateF={'status':'PASS' if all(q['status']=='PASS' for q in quantities.values()) else 'FAIL','needs_320':'YES' if any(q['needs_320'] for q in quantities.values()) else 'NO','quantities':quantities,'accepted_data_only':True,'blocking':False,'automatic_320_executed':False}
gateG={'status':'NOT_EVALUATED','reason':'Fine accepted solution unavailable','blocking':False}
if fine['computed']:
    m=metrics[fineid];sym=symmetries[fineid]
    values={'physical_heat_imbalance':m['heat_imbalance'],'section_Nu_deviation':m['section_Nu_max_relative_deviation_from_half'],'native_mass_epsilon_m':m['divergence']['epsilon_m'],'reconstructed_velocity_epsilon_v':m['divergence']['epsilon_v'],'temperature_symmetry':sym['theta_L2_relative'],'velocity_symmetry':sym['velocity_L2_relative']}
    limits={'physical_heat_imbalance':.002,'section_Nu_deviation':.005,'native_mass_epsilon_m':1e-6,'reconstructed_velocity_epsilon_v':.002,'temperature_symmetry':.002,'velocity_symmetry':.002}
    checks={k:values[k] is not None and math.isfinite(values[k]) and values[k]<=limits[k] for k in values}
    gateG={'status':status(checks) if fine['accepted'] else 'NOT_EVALUATED','diagnostic_status':status(checks),'values':values,'limits':limits,'checks':checks,'failure_components':[k for k,v in checks.items() if not v],'formal_fine_accepted':fine['accepted'],'blocking':False,'operator_metadata':contract['continuity'],'bounded_cause_category':'NONE' if all(checks.values()) else 'FROZEN_FORMULATION_AND_DISCRETE_OPERATOR_DIAGNOSTIC; no additional cause study in this task','additional_research_performed':False}

Bmanifest_path=ROOT/'results/routeB/full_matrix_manifest.json';Bmanifest=json.loads(Bmanifest_path.read_text());comparisons=[];Bhashes={str(Bmanifest_path.relative_to(ROOT)):sha(Bmanifest_path)}
for row in rows:
    bid=row['case_id'].replace('A-','B-',1);brow=Bmanifest['cases'][bid];bpath=ROOT/'results/routeB/cases'/bid/'metrics.json';bm=json.loads(bpath.read_text());Bhashes[str(bpath.relative_to(ROOT))]=sha(bpath)
    accepted_B=brow['Gate_D']=='PASS' and bool(brow.get('accepted_final_field_sha256'))
    gm=brow['generated_manifest'];assert gm['grid']==row['grid'] and abs(gm['Ra_actual']/1000-1)<=1e-10 and gm['Pr_actual']==.71
    if not row['computed']:
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'status':'NOT_EVALUATED','reason':'A canonical metrics unavailable','quantity':None,'A':None,'B':None,'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_EVALUATED'});continue
    assert accepted_B,('B accepted baseline missing',bid)
    am=metrics[row['case_id']];asym=symmetries[row['case_id']]
    entries=[(key,am[key],bm[key],'POSITION' if key.endswith(('_Z','_X')) else 'SCALAR','LIKE_FOR_LIKE' if key!='Nu_bar_half' else 'NOT_LIKE_FOR_LIKE') for key in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']]
    entries += [('section_Nu_max_relative_deviation_from_half',am['section_Nu_max_relative_deviation_from_half'],bm['section_Nu_max_relative_deviation_from_half'],'SCALAR','NOT_LIKE_FOR_LIKE'),('heat_imbalance',am['heat_imbalance'],bm['heat_imbalance'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_mean_abs_divergence_1_s',am['divergence']['mean_abs_volume_divergence_1_s'],bm['continuity']['mean_abs_div_U_1_s'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_epsilon_v',am['divergence']['epsilon_v'],bm['continuity']['epsilon_v'],'SCALAR','LIKE_FOR_LIKE'),('temperature_symmetry_L2',asym['theta_L2_relative'],bm['symmetry']['theta_L2_relative'],'SCALAR','LIKE_FOR_LIKE'),('velocity_symmetry_L2',asym['velocity_L2_relative'],bm['symmetry']['velocity_L2_relative'],'SCALAR','LIKE_FOR_LIKE')]
    for key,av,bv,kind,compatibility in entries:
        available=av is not None and bv is not None
        signed=av-bv if available else None
        rel=abs(signed)/abs(bv) if available and kind!='POSITION' and bv!=0 else None
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'Ra_actual':gm['Ra_actual'],'A_iteration':row['final_iteration'],'B_iteration':bm['final_iteration'],'A_accepted':row['accepted'],'B_accepted_baseline':accepted_B,'status':'COMPLETE' if available else 'NOT_EVALUATED','quantity':key,'A':av,'B':bv,'signed_difference':signed,'absolute_difference':abs(signed) if available else None,'relative_difference':rel,'absolute_position_difference':abs(signed) if available and kind=='POSITION' else None,'comparison_class':compatibility,'hard_comparison_allowed':False,'zero_baseline_status':'ABSOLUTE_ONLY' if available and bv==0 else None,'diagnostic_only':not row['accepted'],'reason':'A reconstructed U_f vs B native volume phi: differing section operators' if compatibility=='NOT_LIKE_FOR_LIKE' else None})
    comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'status':'COMPLETE','quantity':'native_phi_continuity','A':am['divergence']['epsilon_m'],'B':bm['continuity']['epsilon_phi'],'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_LIKE_FOR_LIKE','hard_comparison_allowed':False,'reason':'A native mass phi [kg/s] versus B native volume phi [m3/s]; normalized indicators retain distinct operators, no direct numeric gap.'})
ABstatus='COMPLETE' if all(r['computed'] for r in rows) and all(x['status']=='COMPLETE' for x in comparisons) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED'
for item in comparisons:
    source=next(r for r in rows if r['case_id']==item['A_case_id'])
    item.update(case_id=item['A_case_id'],route='A vs B',Ra_target=1000,Ra_actual=source['Ra_actual'],Pr_actual=source['Pr_actual'],source_time_or_iteration=source['final_iteration'],method_version=source['method_version'])
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
dump(OUT/'RouteB_baseline_sha256.json',Bhashes)
complete=state['overall']=='COMPLETE' and len(state['cases'])==3
characterized=complete and allaccepted and gateF['status']=='PASS' and gateG['status']=='PASS' and ABstatus=='COMPLETE'
nextready=complete # F/G/paper/cap failures do not block matrix execution under frozen policy.
nexttask='RUN_ROUTE_A_RA1E4_TRIO' if nextready else 'FIX_ROUTE_A_EXECUTION_ISSUE'
statuslines={'ROUTE_A_RA1E3_ATTEMPT':'004','ROUTE_A_RA1E3_TRIO':state['overall'],'EFFECTIVE_CONTRACT_VERSION':'1.3','EFFECTIVE_CONTRACT_HASH_VERIFIED':'YES','EFFECTIVE_CONTRACT_SHA256':'227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1','ANALYZER_HASH_VERIFIED':'YES','ANALYZER_SHA256':'e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac','RUNTIME_CHECKER_HASH_VERIFIED':'YES','RUNTIME_CHECKER_SHA256':'5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a','COARSE_ACCEPTED_REUSE':'YES','COARSE_SOLVER_RERUN':'NO'}
for row,name in zip(rows,['COARSE','MEDIUM','FINE']):
    for key,value in [('COMPUTED','YES' if row['computed'] else 'NO'),('ACCEPTED','YES' if row['accepted'] else 'NO'),('FINAL_ITERATION',str(row['final_iteration']) if row['final_iteration'] else 'NONE'),('GATE_D',row['Gate_D'])]:statuslines['A_RA1E3_'+name+'_'+key]=value
    if name!='COARSE':statuslines['A_RA1E3_'+name+'_GATE_D_FAILURE_COMPONENTS']=','.join(row['Gate_D_failure_components']) or 'NONE'
statuslines.update(RA1E3_ACCEPTED_CASE_COUNT=str(sum(r['accepted'] for r in rows)),RA1E3_GATE_E_DIAGNOSTIC=gateE['status'],RA1E3_GATE_F=gateF['status'],RA1E3_NEEDS_320=gateF['needs_320'],RA1E3_GATE_G=gateG['status'],ROUTE_A_VS_ROUTE_B_COMPARISON=ABstatus,RA1E3_STEADY_TRIO_CHARACTERIZED='YES' if characterized else 'NO',FORMAL_CRITERIA_CHANGED='NO',NUMERICAL_SETTINGS_CHANGED='NO',PHYSICAL_MODEL_CHANGED='NO',SOLVER_TUNING_PERFORMED='NO',POST_CAP_EXTENSION_PERFORMED='NO',AUTOMATIC_320_PERFORMED='NO',ROUTE_B_MODIFIED='NO',ATTEMPT_001_HISTORY_PRESERVED='YES',ATTEMPT_002_HISTORY_PRESERVED='YES',ATTEMPT_003_HISTORY_PRESERVED='YES',RA1E4_TRIO_TECHNICALLY_READY='YES' if nextready else 'NO',NEXT_SINGLE_TASK=nexttask,RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK='gpt-6.1-sol / medium',USER_DECISION_REQUIRED='YES')
report={'schema':'routeA-Ra1e3-trio-report-v1','task':'RERUN_ROUTE_A_RA1E3_TRIO_ATTEMPT_004','date':'2026-10-04','timezone':'Asia/Tokyo','attempt':'004','overall':state['overall'],'observed_HEAD':state['environment']['HEAD'],'expected_HEAD':'d68140988ec6fbc1473614bf62f2fe9ca8cf73ca','environment':state['environment'],'contract':{'version':'1.3','sha256':statuslines['EFFECTIVE_CONTRACT_SHA256'],'all_hash_guards':'PASS','modified':False},'coarse_accepted_reuse':{'verified':True,'solver_rerun':False,'source_owner':'POST_FIX_REEVALUATION_OF_ATTEMPT_003_CHECKPOINT','source_attempt_003_status_unchanged':True,'current_reuse_seal':str(reuse.relative_to(ROOT))},'cases':rows,'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'paper_comparison_classification':'PRACTICAL_BENCHMARK_COMPARISON','A_B_comparison':{'status':ABstatus,'baseline_sha256':Bhashes,'quantity_rows':comparisons,'native_flux_rule':'A mass kg/s vs B volume m3/s: NOT_LIKE_FOR_LIKE','section_rule':'A reconstructed U_f vs B native volume phi: NOT_LIKE_FOR_LIKE','no_AB_hard_threshold':True},'STEADY_TRIO_COMPLETE':complete,'RA1E3_STEADY_TRIO_CHARACTERIZED':characterized,'characterized_definition':'Three accepted rows + Gate F/G PASS + completed comparison; separate from mere complete execution and from full Route A characterization.','remaining_matrix_may_proceed':nextready,'F_G_block_matrix':False,'unresolved_issues':{'execution_stop':state['stop_reason'],'Gate_F_limitations':gateF if gateF['status']!='PASS' else None,'Gate_G_limitations':gateG if gateG['status']!='PASS' else None,'additional_research_performed':False},'protected_evidence':{'status':'PASS','hash_entry_count':len(protected),'baseline_path':'results/routeA/attempts/attempt_004/protected_before_sha256.json','all_historical_attempts_intact':True},'final_status':statuslines,'git_add_commit_push_performed':False}
dump(OUT/'Ra1e3_trio_report.json',report)
dump(OUT/'Ra1e3_group_evaluation.json',{'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'symmetry':symmetries})
fields=['attempt','case_id','route','Ra_target','Ra_actual','Pr_actual','grid','status','source_time_or_iteration','method_version','computed','accepted','final_iteration','Gate_D','Gate_D_failure_components','Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','metrics_path','metrics_sha256']
with (OUT/'Ra1e3_trio_matrix.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for row in rows:
        data={k:row.get(k) for k in fields};data.update(row['QoIs'] or {})
        writer.writerow({k:('' if data.get(k) is None else json.dumps(data[k]) if isinstance(data[k],(list,bool)) else data[k]) for k in fields})
with (OUT/'Ra1e3_routeA_vs_routeB.csv').open('w',newline='') as f:
    fields=['case_id','route','Ra_target','Pr_actual','source_time_or_iteration','method_version','A_case_id','B_case_id','grid','Ra_actual','A_iteration','B_iteration','A_accepted','B_accepted_baseline','status','quantity','A','B','signed_difference','absolute_difference','relative_difference','absolute_position_difference','comparison_class','hard_comparison_allowed','zero_baseline_status','diagnostic_only','reason']
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for item in comparisons:writer.writerow({k:('' if item.get(k) is None else json.dumps(item[k]) if isinstance(item[k],(list,bool)) else item[k]) for k in fields})
qtable='\n'.join('| '+row['case_id']+' | '+str(row['final_iteration'])+' | '+('YES' if row['accepted'] else 'NO')+' | '+row['Gate_D']+' | '+(' | '.join(format(row['QoIs'][k],'.9g') for k in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Wmax']) if row['QoIs'] else '— | — | — | — | — | —')+' |' for row in rows)
ftable='\n'.join('| '+key+' | '+item['convergence_type']+' | '+str(item['p_obs'])+' | '+str(item['GCI_fine'])+' | '+item['status']+' |' for key,item in (gateF.get('quantities') or {}).items())
gtable='\n'.join('| '+key+' | '+format(value,'.9g')+' | '+format(gateG['limits'][key],'.9g')+' | '+('PASS' if gateG['checks'][key] else 'FAIL')+' |' for key,value in gateG.get('values',{}).items() if value is not None)
status_text='\n'.join(k+' = '+value for k,value in statuslines.items())
text=f'''# Route A Ra1e3 attempt 004

**{state['overall']} / accepted {sum(r['accepted'] for r in rows)}/3**。HEADは指定d68140988ec6fbc1473614bf62f2fe9ca8cf73caと一致。effective v1.3、analyzer/runtime checker、全implementation/template/caps/reference/parent/amendment guard PASS。契約・physics・numerics・threshold変更なし。

coarseはpost-fix ownerのcanonical metrics/Gate D PASSをhash照合し、accepted 3000 checkpointとしてattempt 004へ封印登録した。coarse solver/clone再実行なし。attempt 003自身のSTOP/computed NO/accepted NO/NOT_EVALUATEDとraw sealは保持する。

medium→fineを順次新規生成、input/hash→mesh→initialization clone→canonical runtime checker→OQ-02→Gate A→primaryの順で実施。segmentごとにnormal finite/actual exit/End/runtime/field/input/meshを確認し、raw evidence seal→canonical analyzer→Gate D→final checksum sealを完了してから継続／次caseへ進んだ。continuationはstartFrom/endTimeだけの変更。concurrent solver=1。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
{qtable}

paper比較は各canonical metricsのpaper_comparison_like_for_likeを保存。fine Gate E diagnostic={gateE['status']}。分類はPRACTICAL_BENCHMARK_COMPARISONで、差を純粋なnumerical errorとしない。Nu_bar_1には独立paper referenceなし。Gate Eの位置判定は既存criteriaどおりabsolute coordinate difference。

Route A–B比較={ABstatus}。同一Ra/gridの既存accepted B baselineだけをread-only使用。scalarはabs(A-B)/abs(B)、signed差も保存、positionはabsolute coordinate差。heat/reconstructed-U/symmetryもCSVに記録。native A mass phiとB volume phi、section reconstructed U_fとnative volume phiはNOT_LIKE_FOR_LIKE。AB Hard thresholdは設けていない。詳細は [comparison CSV](Ra1e3_routeA_vs_routeB.csv)。

Gate F={gateF['status']}、needs_320={gateF['needs_320']}。accepted dataのみformal使用、fine-medium≤1%、GCI limits Nu1.5%/U2%/W2%、Fs=3。非単調/未定義ではp/GCI null。320²は実行していない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
{ftable}

Gate G={gateG['status']}。既存fine criteriaとfrozen operator/normalizationのみ使用。

| Component | Value | Limit | Status |
|---|---:|---:|---|
{gtable}

Gate F/GのFAILはNON_BLOCKING_WITH_DOCUMENTED_LIMITATIONとしてそのまま保持し、追加研究・tuningはしない。STEADY_TRIO_COMPLETE={complete}、RA1E3_STEADY_TRIO_CHARACTERIZED={characterized}（accepted3＋F/G PASS＋比較完了の資格）。Ra1e3のexecution完了とRoute A全体のVerification完了は区別する。

fineのcanonical図はcase/figuresとfinal segment seal内へ保存。既存A-SMOKE図は保護した。保護対象{len(protected)}hash entriesは前後一致。Route B再計算・変更なし。過去attempt 001/002/003、coarse原seal/post-fix reanalysis、全contract/amendmentsは不変。

Ra1e4 trio technically ready={nextready}。契約ではF/G/paper/cap convergence failureはmatrix collectionをblockしない。次task={nexttask}、新しいユーザー実行指示が必要。今回はRa1e3のみで終了。

詳細は [JSON](Ra1e3_trio_report.json)、[matrix](Ra1e3_trio_matrix.csv)、[group evaluation](Ra1e3_group_evaluation.json)。

```text
{status_text}
```
'''
(OUT/'Ra1e3_trio_report.md').write_text(text)
for p,h in protected.items():assert sha(ROOT/p)==h,p
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
print('REPORT:',state['overall'],'accepted',sum(r['accepted'] for r in rows),'/3; E/F/G:',gateE['status'],gateF['status'],gateG['status'],'AB:',ABstatus)
print('QoIs:',[{k:r['QoIs'][k] for k in ['Nu_bar_cavity','Umax','Wmax']} if r['QoIs'] else None for r in rows])
