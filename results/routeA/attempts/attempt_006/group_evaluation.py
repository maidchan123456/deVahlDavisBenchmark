import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path.cwd();OUT=ROOT/'results/routeA/attempts/attempt_006'
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
contract=json.loads((ROOT/'docs/routeA_execution_contract_v1.5.json').read_text())
protected=json.loads((OUT/'protected_before_sha256.json').read_text())
for p,h in protected.items():assert sha(ROOT/p)==h,('protected mismatch',p)
assert sha(ROOT/'docs/routeA_execution_contract_v1.5.json')=='c33efe4aa81ce0644fd709fe944563e93c7ee2f08304161000784f6418e159c1'
for p,h in contract['implementation_sha256'].items():assert sha(ROOT/p)==h,p
for p,h in contract['template_source']['unchanged_template_sha256'].items():assert sha(ROOT/p)==h,p
for row in state['cases']:
    for seg in row['segments']:
        seal=ROOT/seg['path'];assert sha(seal/'sealed_sha256.json')==seg['sealed_sha256_manifest']
        for p,h in json.loads((seal/'sealed_sha256.json').read_text()).items():assert sha(seal/p)==h,p
rows=[];metrics={};manifests={};symmetries={}
for name,grid in [('coarse',40),('medium',80),('fine',160)]:
    cid='A-Ra1e5-'+name
    row=next((r.copy() for r in state['cases'] if r['case_id']==cid),{'case_id':cid,'grid':[grid,grid,1],'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','Gate_D_failure_components':[],'segments':[],'status':'NOT_STARTED_BATCH_STOP'})
    row.setdefault('Gate_D_failure_components',[])
    row.update(route='A',attempt='006',Ra_target=100000,source_time_or_iteration=row['final_iteration'],method_version='routeA effective execution contract v1.5 / canonical analyzer sha256 e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed')
    if row['computed']:
        path=ROOT/'results/routeA/cases'/cid/'metrics.json'
        m=json.loads(path.read_text());assert m['final_iteration']==row['final_iteration']
        
        for key in analyzer.POSITION_KEYS:
            payload=m['paper_comparison_like_for_like'][key]
            assert 'absolute_position_error' in payload and 'absolute_relative_error' not in payload,key
        metrics[cid]=m;case=ROOT/'cases/routeA'/cid;manifest=json.loads((case/'case_manifest.json').read_text());manifests[cid]=manifest
        symmetries[cid]=symmetry(case,row['final_iteration'],manifest)
        row.update(metrics_path=str(path.relative_to(ROOT)),metrics_sha256=sha(path),Ra_actual=manifest['Ra_actual'],Pr_actual=manifest['Pr_actual'],QoIs={k:m[k] for k in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']},paper_comparison=m['paper_comparison_like_for_like'],symmetry=symmetries[cid],heat_imbalance=m['heat_imbalance'],divergence=m['divergence'])
    else:row.update(Ra_actual=None,Pr_actual=None,QoIs=None,paper_comparison=None,symmetry=None,heat_imbalance=None,divergence=None)
    rows.append(row)
allaccepted=len(rows)==3 and all(r['accepted'] for r in rows)
fine=rows[2];fineid=fine['case_id'];reference=analyzer.read_paper_reference(analyzer.PAPER_REFERENCE)[100000]
gateE={'status':'NOT_EVALUATED','classification':'PRACTICAL_BENCHMARK_COMPARISON','reason':'Fine accepted solution unavailable'}
if fine['accepted']:
    m=metrics[fineid];errors={k:m['paper_comparison_like_for_like'][k]['absolute_relative_error'] for k in ['Nu_bar_cavity','Umax','Wmax']}
    positions={k:m['paper_comparison_like_for_like'][k]['absolute_position_error'] for k in ['Umax_Z','Wmax_X']}
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
    bid=row['case_id'].replace('A-','B-',1);brow=Bmanifest['cases'][bid];bpath=Path(brow['metrics_path']);assert sha(bpath)==brow['metrics_sha256'],('B baseline hash mismatch',bid);bm=json.loads(bpath.read_text());Bhashes[str(bpath.relative_to(ROOT))]=sha(bpath)
    accepted_B=brow['Gate_D']=='PASS' and bool(brow.get('accepted_final_field_sha256'))
    gm=brow['generated_manifest'];assert gm['grid']==row['grid'] and abs(gm['Ra_actual']/100000-1)<=1e-10 and gm['Pr_actual']==.71
    if not row['computed']:
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'status':'NOT_EVALUATED','reason':'A canonical metrics unavailable','quantity':None,'A':None,'B':None,'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_EVALUATED'});continue
    assert accepted_B,('B accepted baseline missing',bid)
    am=metrics[row['case_id']];asym=symmetries[row['case_id']]
    entries=[(key,am[key],bm[key],'POSITION' if key in analyzer.POSITION_KEYS else 'SCALAR','LIKE_FOR_LIKE' if key!='Nu_bar_half' else 'NOT_LIKE_FOR_LIKE') for key in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']]
    entries += [('section_Nu_max_relative_deviation_from_half',am['section_Nu_max_relative_deviation_from_half'],bm['section_Nu_max_relative_deviation_from_half'],'SCALAR','NOT_LIKE_FOR_LIKE'),('heat_imbalance',am['heat_imbalance'],bm['heat_imbalance'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_mean_abs_divergence_1_s',am['divergence']['mean_abs_volume_divergence_1_s'],bm['continuity']['mean_abs_div_U_1_s'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_epsilon_v',am['divergence']['epsilon_v'],bm['continuity']['epsilon_v'],'SCALAR','LIKE_FOR_LIKE'),('temperature_symmetry_L2',asym['theta_L2_relative'],bm.get('symmetry',{}).get('theta_L2_relative'),'SCALAR','LIKE_FOR_LIKE'),('velocity_symmetry_L2',asym['velocity_L2_relative'],bm.get('symmetry',{}).get('velocity_L2_relative'),'SCALAR','LIKE_FOR_LIKE')]
    for key,av,bv,kind,compatibility in entries:
        available=av is not None and bv is not None
        signed=av-bv if available else None
        rel=abs(signed)/abs(bv) if available and kind!='POSITION' and bv!=0 else None
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'Ra_actual':gm['Ra_actual'],'A_iteration':row['final_iteration'],'B_iteration':bm['final_iteration'],'A_accepted':row['accepted'],'B_accepted_baseline':accepted_B,'status':'COMPLETE' if available else 'NOT_EVALUATED','quantity':key,'A':av,'B':bv,'signed_difference':signed,'absolute_difference':abs(signed) if available else None,'relative_difference':rel,'absolute_position_difference':abs(signed) if available and kind=='POSITION' else None,'comparison_class':compatibility,'hard_comparison_allowed':False,'zero_baseline_status':'ABSOLUTE_ONLY' if available and bv==0 else None,'diagnostic_only':not row['accepted'],'reason':'B canonical baseline does not store symmetry; no B recomputation performed' if not available else 'A reconstructed U_f vs B native volume phi: differing section operators' if compatibility=='NOT_LIKE_FOR_LIKE' else None})
    comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'status':'COMPLETE','quantity':'native_phi_continuity','A':am['divergence']['epsilon_m'],'B':bm['continuity']['epsilon_phi'],'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_LIKE_FOR_LIKE','hard_comparison_allowed':False,'reason':'A native mass phi [kg/s] versus B native volume phi [m3/s]; normalized indicators retain distinct operators, no direct numeric gap.'})
ABstatus='COMPLETE' if all(r['computed'] for r in rows) and all(x['status']=='COMPLETE' for x in comparisons) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED'
for item in comparisons:
    source=next(r for r in rows if r['case_id']==item['A_case_id'])
    brow=Bmanifest['cases'][item['B_case_id']]
    item.update(B_source_case_id=brow['source_case_id'],B_metrics_path=brow['metrics_path'],case_id=item['A_case_id'],route='A vs B',Ra_target=100000,Ra_actual=source['Ra_actual'],Pr_actual=source['Pr_actual'],source_time_or_iteration=source['final_iteration'],method_version=source['method_version'])
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
dump(OUT/'RouteB_baseline_sha256.json',Bhashes)
complete=state['overall']=='COMPLETE' and len(state['cases'])==3
characterized=complete and allaccepted and gateF['status']=='PASS' and gateG['status']=='PASS' and ABstatus=='COMPLETE'
# v1.5 review linkage: ordinary numerical/Gate/paper/auxiliary AB limitations are nonblocking.
scientifically_allowed=complete and state['stop_reason'] is None
nextready=False # A separately prepared Ra1e6 snapshot is required; v1.5 specifies Ra1e5/attempt006.
nexttask='PREPARE_ROUTE_A_RA1E6_EXECUTION_CONTRACT' if scientifically_allowed else 'FIX_ROUTE_A_EXECUTION_ISSUE'
statuslines={'ROUTE_A_RA1E5_ATTEMPT':'006','ROUTE_A_RA1E5_TRIO':state['overall'],'EFFECTIVE_CONTRACT_VERSION':'1.5','EFFECTIVE_CONTRACT_HASH_VERIFIED':'YES','EFFECTIVE_CONTRACT_SHA256':'c33efe4aa81ce0644fd709fe944563e93c7ee2f08304161000784f6418e159c1','ANALYZER_HASH_VERIFIED':'YES','ANALYZER_SHA256':'e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed','RUNTIME_CHECKER_HASH_VERIFIED':'YES','RUNTIME_CHECKER_SHA256':'5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a'}
for row,name in zip(rows,['COARSE','MEDIUM','FINE']):
    for key,value in [('COMPUTED','YES' if row['computed'] else 'NO'),('ACCEPTED','YES' if row['accepted'] else 'NO'),('FINAL_ITERATION',str(row['final_iteration']) if row['final_iteration'] else 'NONE'),('GATE_D',row['Gate_D'])]:statuslines['A_RA1E5_'+name+'_'+key]=value
    statuslines['A_RA1E5_'+name+'_GATE_D_FAILURE_COMPONENTS']=','.join(row['Gate_D_failure_components']) or 'NONE'
statuslines.update(RA1E5_ACCEPTED_CASE_COUNT=str(sum(r['accepted'] for r in rows)),RA1E5_STEADY_TRIO_COMPLETE='YES' if complete and allaccepted else 'NO',RA1E5_GATE_E_DIAGNOSTIC=gateE['status'],RA1E5_GATE_F=gateF['status'],RA1E5_NEEDS_320=gateF['needs_320'],RA1E5_GATE_G=gateG['status'],ROUTE_A_VS_ROUTE_B_COMPARISON=ABstatus,RA1E5_STEADY_TRIO_CHARACTERIZED='YES' if characterized else 'NO',FORMAL_CRITERIA_CHANGED='NO',REFERENCE_DATA_CHANGED='NO',RA1E3_RESULTS_MODIFIED='NO',POSITION_SEMANTICS_V1_4_USED='YES',NUMERICAL_SETTINGS_CHANGED='NO',PHYSICAL_MODEL_CHANGED='NO',SOLVER_TUNING_PERFORMED='NO',POST_CAP_EXTENSION_PERFORMED='NO',AUTOMATIC_320_PERFORMED='NO',ROUTE_B_MODIFIED='NO',ATTEMPT_001_HISTORY_PRESERVED='YES',ATTEMPT_002_HISTORY_PRESERVED='YES',ATTEMPT_003_HISTORY_PRESERVED='YES',RA1E6_TRIO_TECHNICALLY_READY='NO',NEXT_SINGLE_TASK=nexttask,RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK='gpt-6.1-sol / medium',USER_DECISION_REQUIRED='YES')
statuslines.update(A_B_PRIMARY_QOI_COMPARISON='COMPLETE' if all(r['computed'] for r in rows) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED',A_B_HARD_THRESHOLD_EXISTS='NO',AB_COMPARISON_POLICY_CHANGED='NO',POSITION_SEMANTICS_CHANGED='NO',ITERATION_POLICY_CHANGED='NO',RA1E4_RESULTS_MODIFIED='NO',RA1E6_TRIO_SCIENTIFICALLY_ALLOWED='YES' if scientifically_allowed else 'NO',RA1E6_EXECUTION_CONTRACT_UPDATE_REQUIRED='YES')
report={'schema':'routeA-Ra1e5-trio-report-v1','task':'RUN_ROUTE_A_RA1E5_TRIO','date':'2026-10-04','timezone':'Asia/Tokyo','attempt':'006','overall':state['overall'],'observed_HEAD':state['environment']['HEAD'],'expected_HEAD':'85d7f5ebc76b8be3b840ae31217a457833b5a8d6','environment':state['environment'],'contract':{'version':'1.5','sha256':statuslines['EFFECTIVE_CONTRACT_SHA256'],'all_hash_guards':'PASS','modified':False},'cases':rows,'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'paper_comparison_classification':'PRACTICAL_BENCHMARK_COMPARISON','A_B_comparison':{'status':ABstatus,'baseline_sha256':Bhashes,'quantity_rows':comparisons,'native_flux_rule':'A mass kg/s vs B volume m3/s: NOT_LIKE_FOR_LIKE','section_rule':'A reconstructed U_f vs B native volume phi: NOT_LIKE_FOR_LIKE','no_AB_hard_threshold':True},'STEADY_TRIO_COMPLETE':complete and allaccepted,'RA1E5_STEADY_TRIO_CHARACTERIZED':characterized,'characterized_definition':'Three accepted rows + Gate F/G PASS + completed comparison; separate from mere complete execution and from full Route A characterization.','remaining_matrix_may_proceed':scientifically_allowed,'F_G_block_matrix':False,'Ra1e6_snapshot_required':True,'Ra1e6_scientifically_allowed':scientifically_allowed,'AB_auxiliary_limitation_blocks_matrix':False,'unresolved_issues':{'execution_stop':state['stop_reason'],'comparison_data_gaps':[{'case_id':x['A_case_id'],'B_case_id':x['B_case_id'],'quantity':x['quantity'],'reason':x['reason']} for x in comparisons if x['status']!='COMPLETE'],'Gate_F_limitations':gateF if gateF['status']!='PASS' else None,'Gate_G_limitations':gateG if gateG['status']!='PASS' else None,'additional_research_performed':False},'protected_evidence':{'status':'PASS','hash_entry_count':len(protected),'baseline_path':'results/routeA/attempts/attempt_006/protected_before_sha256.json','all_historical_attempts_intact':True},'final_status':statuslines,'git_add_commit_push_performed':False}
dump(OUT/'Ra1e5_trio_report.json',report)
dump(OUT/'Ra1e5_group_evaluation.json',{'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'symmetry':symmetries})
fields=['attempt','case_id','route','Ra_target','Ra_actual','Pr_actual','grid','status','source_time_or_iteration','method_version','computed','accepted','final_iteration','Gate_D','Gate_D_failure_components','Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','metrics_path','metrics_sha256']
with (OUT/'Ra1e5_trio_matrix.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for row in rows:
        data={k:row.get(k) for k in fields};data.update(row['QoIs'] or {})
        writer.writerow({k:('' if data.get(k) is None else json.dumps(data[k]) if isinstance(data[k],(list,bool)) else data[k]) for k in fields})
with (OUT/'Ra1e5_routeA_vs_routeB.csv').open('w',newline='') as f:
    fields=['case_id','route','Ra_target','Pr_actual','source_time_or_iteration','method_version','A_case_id','B_case_id','B_source_case_id','B_metrics_path','grid','Ra_actual','A_iteration','B_iteration','A_accepted','B_accepted_baseline','status','quantity','A','B','signed_difference','absolute_difference','relative_difference','absolute_position_difference','comparison_class','hard_comparison_allowed','zero_baseline_status','diagnostic_only','reason']
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for item in comparisons:writer.writerow({k:('' if item.get(k) is None else json.dumps(item[k]) if isinstance(item[k],(list,bool)) else item[k]) for k in fields})
qtable='\n'.join('| '+row['case_id']+' | '+str(row['final_iteration'])+' | '+('YES' if row['accepted'] else 'NO')+' | '+row['Gate_D']+' | '+(' | '.join(format(row['QoIs'][k],'.9g') for k in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Wmax']) if row['QoIs'] else '— | — | — | — | — | —')+' |' for row in rows)
ftable='\n'.join('| '+key+' | '+item['convergence_type']+' | '+str(item['p_obs'])+' | '+str(item['GCI_fine'])+' | '+item['status']+' |' for key,item in (gateF.get('quantities') or {}).items())
gtable='\n'.join('| '+key+' | '+format(value,'.9g')+' | '+format(gateG['limits'][key],'.9g')+' | '+('PASS' if gateG['checks'][key] else 'FAIL')+' |' for key,value in gateG.get('values',{}).items() if value is not None)
status_text='\n'.join(k+' = '+value for k,value in statuslines.items())

mainkeys=['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X']
paperkeys=['Nu_bar_cavity','Nu_bar_half','Nu_bar_0','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z','Umax','Umax_Z','Wmax','Wmax_X']
paperrows=[]
for key in paperkeys:
    values=[]
    for row in rows:
        p=(row['paper_comparison'] or {}).get(key,{})
        values.append(p.get('absolute_position_error') if key in analyzer.POSITION_KEYS else p.get('absolute_relative_error'))
    paperrows.append('| '+key+' | '+' | '.join('NOT_EVALUATED' if x is None else format(x,'.9g') for x in values)+' |')
papertable='\n'.join(paperrows)
abrows=[]
for key in ['Nu_bar_cavity','Nu_bar_0','Umax','Umax_Z','Wmax','Wmax_X']:
    values=[]
    for row in rows:
        x=next((x for x in comparisons if x['A_case_id']==row['case_id'] and x['quantity']==key),{})
        value=x.get('absolute_position_difference') if key in analyzer.POSITION_KEYS else x.get('relative_difference')
        values.append('NOT_EVALUATED' if value is None else format(value,'.9g'))
    abrows.append('| '+key+' | '+' | '.join(values)+' |')
abtable='\n'.join(abrows)
segments=[]
for row in rows:
    for seg in row['segments']:
        segments.append('| '+row['case_id']+' | '+str(seg['end_iteration'])+' | '+seg['Gate_D']+' | '+(','.join(seg['failure_components']) or 'NONE')+' |')
segmenttable='\n'.join(segments)
text=f'''# Route A Ra1e5 attempt 006

**{state['overall']} / accepted {sum(r['accepted'] for r in rows)}/3**。指定HEAD `85d7f5ebc76b8be3b840ae31217a457833b5a8d6`と一致。effective v1.5をsole current guardとしてdigest、implementation/template/caps/reference、parent/amendments001–005、accepted Ra1e3/Ra1e4 history、Ra1e4 review、accepted Route B Ra1e5 baselinesを照合した。物理・numerics・threshold・AB policy・position semantics・iteration policyへの変更なし。

coarse→medium→fineの順にcanonical generatorのA-SMOKE roleからNEW formal casesを生成。raw generated_manifest_original.jsonを保存し、formal metadataのみ変更した。歴史field/caseのpromotion/reuseは行っていない。input hashes/template expansion、blockMesh/checkMesh、既存initialization clone、canonical runtime provenance、OQ-02、Gate Aを確認後primary実行。solver concurrency=1。

initial3000、increment3000、absolute cap30000。normal finite segmentはraw evidence seal→canonical analyzer→六項目Gate D→final checksum sealの順に保存した。FAIL継続ではstartFrom/endTimeだけを変更、sealed latestTimeからrestartし、cold retryは行わない。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
{qtable}

| Case | Segment end | Gate D | Failure components |
|---|---:|---|---|
{segmenttable}

Paper comparisonはPRACTICAL_BENCHMARK_COMPARISON。scalar欄はabsolute relative error、position欄はabsolute coordinate error。canonical POSITION_KEYSを使用し、Nu_bar_1は独立paper referenceがない既存handlingを保持する。観測された差は純粋numerical errorやphysical/model causeの証明ではない。

| Paper QoI error | coarse | medium | fine |
|---|---:|---:|---:|
{papertable}

Route A–B比較={ABstatus}、primary coverage={statuslines['A_B_PRIMARY_QOI_COMPARISON']}。accepted B coarse6000/medium9000/fine12000のcanonical evidenceをread-only使用。比較CSVには全QoI、sampling/method/version、source IDs、iteration、operator compatibilityを保存。scalar gap=abs(A-B)/abs(B)、position gap=absolute coordinate difference。AB Hard thresholdなし。Nu_half/sectionのA reconstructed U_f対B corrected native volume phi、native A mass phi対B volume phiはNOT_LIKE_FOR_LIKE。熱・reconstructed U divergence・対称性は定義を区別して診断比較する。欠損はNOT_EVALUATEDとして記録し、補助欠損単独を新しいmatrix blocking条件にしない。

| A–B relative/position gap | coarse | medium | fine |
|---|---:|---:|---:|
{abtable}

Gate E diagnostic={gateE['status']}。fine acceptedの場合のみformal診断を評価。既存scalar relative error/position absolute error criteriaを適用。

Gate F={gateF['status']}、needs_320={gateF['needs_320']}。accepted dataのみ使用。既存fine-medium≤1%、GCI limits Nu1.5%/U2%/W2%、Fs=3。非単調ではp/GCI null、FAIL/needs_320 YESを保存する。320²を実行しない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
{ftable}

Gate G={gateG['status']}。fine acceptedの場合のみformal判定、未acceptedならdiagnostic-only。既存operator/normalization/thresholdを適用し、FAILでも追加研究は行わない。

| Component | Value | Limit | Status |
|---|---:|---:|---|
{gtable}

Unresolved: execution stop={state['stop_reason']}。Gate F/G limitationや比較データ欠損はJSONのunresolved_issuesに保存。previous Ra1e3/Ra1e4 Gate F FAIL/needs_320 YESは変更しない。

RA1E5_STEADY_TRIO_COMPLETE={statuslines['RA1E5_STEADY_TRIO_COMPLETE']}、CHARACTERIZED={statuslines['RA1E5_STEADY_TRIO_CHARACTERIZED']}。execution完了とcharacterization/full verificationは別。

RA1E6_TRIO_SCIENTIFICALLY_ALLOWED={statuslines['RA1E6_TRIO_SCIENTIFICALLY_ALLOWED']}。v1.5はRa1e5/attempt006のsnapshotなのでRa1e6_TRIO_TECHNICALLY_READY=NO、snapshot update required=YES。次task={nexttask}。Ra1e6/320/Gate H/Jを実行せず、Ra1e5 group evaluationまでで終了する。

既存{len(protected)}ファイルhashを保護。全contract/amendments、attempts001–005、Ra1e3/Ra1e4結果/review、Route B、reference、canonical scripts/templates不変。fine図は既存canonical workflowを使用し、新case/figuresとsegment内に保存する。

詳細: [JSON](Ra1e5_trio_report.json)、[matrix](Ra1e5_trio_matrix.csv)、[comparison CSV](Ra1e5_routeA_vs_routeB.csv)、[group evaluation](Ra1e5_group_evaluation.json)。git add/commit/push未実行。

```text
{status_text}
```
'''
(OUT/'Ra1e5_trio_report.md').write_text(text)
for p,h in protected.items():assert sha(ROOT/p)==h,p
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
print('REPORT:',state['overall'],'accepted',sum(r['accepted'] for r in rows),'/3; E/F/G:',gateE['status'],gateF['status'],gateG['status'],'AB:',ABstatus)
print('QoIs:',[{k:r['QoIs'][k] for k in ['Nu_bar_cavity','Umax','Wmax']} if r['QoIs'] else None for r in rows])
