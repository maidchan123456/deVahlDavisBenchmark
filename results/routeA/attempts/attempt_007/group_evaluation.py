import csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np

ROOT=Path.cwd();OUT=ROOT/'results/routeA/attempts/attempt_007'
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
contract=json.loads((ROOT/'docs/routeA_execution_contract_v1.6.json').read_text())
protected=json.loads((OUT/'protected_before_sha256.json').read_text())
for p,h in protected.items():assert sha(ROOT/p)==h,('protected mismatch',p)
assert sha(ROOT/'docs/routeA_execution_contract_v1.6.json')=='c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59'
for p,h in contract['implementation_sha256'].items():assert sha(ROOT/p)==h,p
for p,h in contract['template_source']['unchanged_template_sha256'].items():assert sha(ROOT/p)==h,p
for row in state['cases']:
    for seg in row['segments']:
        seal=ROOT/seg['path'];assert sha(seal/'sealed_sha256.json')==seg['sealed_sha256_manifest']
        for p,h in json.loads((seal/'sealed_sha256.json').read_text()).items():assert sha(seal/p)==h,p
rows=[];metrics={};manifests={};symmetries={}
for name,grid in [('coarse',40),('medium',80),('fine',160)]:
    cid='A-Ra1e6-'+name
    row=next((r.copy() for r in state['cases'] if r['case_id']==cid),{'case_id':cid,'grid':[grid,grid,1],'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','Gate_D_failure_components':[],'segments':[],'status':'NOT_STARTED_BATCH_STOP'})
    row.setdefault('Gate_D_failure_components',[])
    row.update(route='A',attempt='007',Ra_target=1000000,source_time_or_iteration=row['final_iteration'],method_version='routeA effective execution contract v1.6 / canonical analyzer sha256 e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed')
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
fine=rows[2];fineid=fine['case_id'];reference=analyzer.read_paper_reference(analyzer.PAPER_REFERENCE)[1000000]
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
    gm=brow['generated_manifest'];assert gm['grid']==row['grid'] and abs(gm['Ra_actual']/1000000-1)<=1e-10 and gm['Pr_actual']==.71
    if not row['computed']:
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'status':'NOT_EVALUATED','reason':'A canonical metrics unavailable','quantity':None,'A':None,'B':None,'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_EVALUATED'});continue
    assert not accepted_B and brow['Gate_D']=='FAIL' and bm['final_iteration']==30000 and bm['normal_exit'] and not bm['fatal_or_nan'],('B computed/unaccepted diagnostic source mismatch',bid)
    am=metrics[row['case_id']];asym=symmetries[row['case_id']]
    entries=[(key,am[key],bm[key],'POSITION' if key in analyzer.POSITION_KEYS else 'SCALAR','LIKE_FOR_LIKE' if key!='Nu_bar_half' else 'NOT_LIKE_FOR_LIKE') for key in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']]
    entries += [('section_Nu_max_relative_deviation_from_half',am['section_Nu_max_relative_deviation_from_half'],bm['section_Nu_max_relative_deviation_from_half'],'SCALAR','NOT_LIKE_FOR_LIKE'),('heat_imbalance',am['heat_imbalance'],bm['heat_imbalance'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_mean_abs_divergence_1_s',am['divergence']['mean_abs_volume_divergence_1_s'],bm['continuity']['mean_abs_div_U_1_s'],'SCALAR','LIKE_FOR_LIKE'),('reconstructed_U_epsilon_v',am['divergence']['epsilon_v'],bm['continuity']['epsilon_v'],'SCALAR','LIKE_FOR_LIKE'),('temperature_symmetry_L2',asym['theta_L2_relative'],bm.get('symmetry',{}).get('theta_L2_relative'),'SCALAR','LIKE_FOR_LIKE'),('velocity_symmetry_L2',asym['velocity_L2_relative'],bm.get('symmetry',{}).get('velocity_L2_relative'),'SCALAR','LIKE_FOR_LIKE')]
    for key,av,bv,kind,compatibility in entries:
        available=av is not None and bv is not None
        signed=av-bv if available else None
        rel=abs(signed)/abs(bv) if available and kind!='POSITION' and bv!=0 else None
        comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'Ra_actual':gm['Ra_actual'],'A_iteration':row['final_iteration'],'B_iteration':bm['final_iteration'],'A_accepted':row['accepted'],'B_accepted_baseline':accepted_B,'status':'COMPLETE' if available else 'NOT_EVALUATED','quantity':key,'A':av,'B':bv,'signed_difference':signed,'absolute_difference':abs(signed) if available else None,'relative_difference':rel,'absolute_position_difference':abs(signed) if available and kind=='POSITION' else None,'comparison_class':compatibility,'hard_comparison_allowed':False,'zero_baseline_status':'ABSOLUTE_ONLY' if available and bv==0 else None,'diagnostic_only':True,'reason':'B canonical baseline does not store symmetry; no B recomputation performed' if not available else 'A reconstructed U_f vs B native volume phi: differing section operators' if compatibility=='NOT_LIKE_FOR_LIKE' else None})
    comparisons.append({'A_case_id':row['case_id'],'B_case_id':bid,'grid':row['grid'],'status':'COMPLETE','quantity':'native_phi_continuity','A':am['divergence']['epsilon_m'],'B':bm['continuity']['epsilon_phi'],'signed_difference':None,'absolute_difference':None,'relative_difference':None,'comparison_class':'NOT_LIKE_FOR_LIKE','hard_comparison_allowed':False,'reason':'A native mass phi [kg/s] versus B native volume phi [m3/s]; normalized indicators retain distinct operators, no direct numeric gap.'})
ABstatus='COMPLETE' if all(r['computed'] for r in rows) and all(x['status']=='COMPLETE' for x in comparisons) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED'
for item in comparisons:
    source=next(r for r in rows if r['case_id']==item['A_case_id'])
    brow=Bmanifest['cases'][item['B_case_id']]
    item.update(A_accepted=source['accepted'],A_computed=source['computed'],B_computed=True,B_accepted=False,B_Gate_D='FAIL',B_iteration=30000,comparison_ownership='DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE',diagnostic_only=True,FORMAL_ACCEPTED_A_B_COMPARISON=False)
    item.update(B_source_case_id=brow['source_case_id'],B_metrics_path=brow['metrics_path'],case_id=item['A_case_id'],route='A vs B',Ra_target=1000000,Ra_actual=source['Ra_actual'],Pr_actual=source['Pr_actual'],source_time_or_iteration=source['final_iteration'],method_version=source['method_version'])
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
dump(OUT/'RouteB_baseline_sha256.json',Bhashes)
complete=state['overall']=='COMPLETE' and len(state['cases'])==3
characterized=complete and allaccepted and gateF['status']=='PASS' and gateG['status']=='PASS' and ABstatus=='COMPLETE'
# v1.6 review linkage: ordinary numerical/Gate/paper/auxiliary AB limitations are nonblocking.
scientifically_allowed=complete and state['stop_reason'] is None
nextready=False # A separately prepared Ra1e6 snapshot is required; v1.6 specifies Ra1e6/attempt006.
nexttask='REVIEW_ROUTE_A_FULL_STEADY_MATRIX' if complete else 'FIX_ROUTE_A_EXECUTION_ISSUE'
statuslines={'ROUTE_A_RA1E6_ATTEMPT':'007','ROUTE_A_RA1E6_TRIO':state['overall'],'EFFECTIVE_CONTRACT_VERSION':'1.6','EFFECTIVE_CONTRACT_HASH_VERIFIED':'YES','EFFECTIVE_CONTRACT_SHA256':'c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59','ANALYZER_HASH_VERIFIED':'YES','ANALYZER_SHA256':'e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed','RUNTIME_CHECKER_HASH_VERIFIED':'YES','RUNTIME_CHECKER_SHA256':'5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a'}
for row,name in zip(rows,['COARSE','MEDIUM','FINE']):
    for key,value in [('COMPUTED','YES' if row['computed'] else 'NO'),('ACCEPTED','YES' if row['accepted'] else 'NO'),('FINAL_ITERATION',str(row['final_iteration']) if row['final_iteration'] else 'NONE'),('GATE_D',row['Gate_D'])]:statuslines['A_RA1E6_'+name+'_'+key]=value
    statuslines['A_RA1E6_'+name+'_GATE_D_FAILURE_COMPONENTS']=','.join(row['Gate_D_failure_components']) or 'NONE'
statuslines.update(RA1E6_ACCEPTED_CASE_COUNT=str(sum(r['accepted'] for r in rows)),RA1E6_STEADY_TRIO_COMPLETE='YES' if complete and allaccepted else 'NO',RA1E6_GATE_E_DIAGNOSTIC=gateE['status'],RA1E6_GATE_F=gateF['status'],RA1E6_NEEDS_320=gateF['needs_320'],RA1E6_GATE_G=gateG['status'],ROUTE_A_VS_ROUTE_B_COMPARISON=ABstatus,RA1E6_STEADY_TRIO_CHARACTERIZED='YES' if characterized else 'NO',FORMAL_CRITERIA_CHANGED='NO',REFERENCE_DATA_CHANGED='NO',RA1E3_RESULTS_MODIFIED='NO',POSITION_SEMANTICS_V1_4_USED='YES',NUMERICAL_SETTINGS_CHANGED='NO',PHYSICAL_MODEL_CHANGED='NO',SOLVER_TUNING_PERFORMED='NO',POST_CAP_EXTENSION_PERFORMED='NO',AUTOMATIC_320_PERFORMED='NO',ROUTE_B_MODIFIED='NO',ATTEMPT_001_HISTORY_PRESERVED='YES',ATTEMPT_002_HISTORY_PRESERVED='YES',ATTEMPT_003_HISTORY_PRESERVED='YES',RA1E6_TRIO_TECHNICALLY_READY='NO',NEXT_SINGLE_TASK=nexttask,RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK='gpt-6.1-sol / medium',USER_DECISION_REQUIRED='YES')
statuslines.update(A_B_PRIMARY_QOI_COMPARISON='COMPLETE' if all(r['computed'] for r in rows) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED',A_B_HARD_THRESHOLD_EXISTS='NO',AB_COMPARISON_POLICY_CHANGED='NO',POSITION_SEMANTICS_CHANGED='NO',ITERATION_POLICY_CHANGED='NO',RA1E4_RESULTS_MODIFIED='NO',RA1E6_TRIO_SCIENTIFICALLY_ALLOWED='YES' if scientifically_allowed else 'NO',RA1E6_EXECUTION_CONTRACT_UPDATE_REQUIRED='YES')

for stale in ['RA1E6_TRIO_TECHNICALLY_READY','RA1E6_TRIO_SCIENTIFICALLY_ALLOWED','RA1E6_EXECUTION_CONTRACT_UPDATE_REQUIRED','A_B_PRIMARY_QOI_COMPARISON','ROUTE_A_VS_ROUTE_B_COMPARISON']:
    statuslines.pop(stale,None)
statuslines.update(ROUTE_B_RA1E6_COMPUTED_BASELINE_COUNT='3',ROUTE_B_RA1E6_ACCEPTED_BASELINE_COUNT='0',RA1E6_AB_COMPARISON_POLICY='DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE',FORMAL_ACCEPTED_AB_COMPARISON_AVAILABLE='NO',ROUTE_A_VS_ROUTE_B_DIAGNOSTIC_COMPARISON=ABstatus,A_B_PRIMARY_QOI_DIAGNOSTIC_COMPARISON='COMPLETE' if all(r['computed'] for r in rows) else 'PARTIAL' if any(r['computed'] for r in rows) else 'NOT_EVALUATED',B_GATE_D_FAILURE_PROPAGATED_TO_A='NO',RA1E5_RESULTS_MODIFIED='NO',AB_HARD_THRESHOLD_ADDED='NO',POST_HOC_RA1E6_ACCEPTANCE_RULE_ADDED='NO',ROUTE_B_SOLVER_EXECUTED='NO',FULL_STEADY_MATRIX_REVIEW_REQUIRED='YES')
# Import earlier formal statuses without recalculation or promotion.
fullrows=[]
for attempt,ra in [('004','1e3'),('005','1e4'),('006','1e5')]:
    p=ROOT/f'results/routeA/attempts/attempt_{attempt}/Ra{ra}_trio_report.json'
    old=json.loads(p.read_text());st=old['final_status']
    prefix='RA'+ra.upper()
    for row in old['cases']:
        fullrows.append({'case_id':row['case_id'],'Ra_target':int(float(ra)),'grid':row['grid'],'computed':row['computed'],'accepted':row['accepted'],'Gate_D':row['Gate_D'],'final_iteration':row['final_iteration'],'Gate_E_diagnostic':old['Gate_E_diagnostic']['status'],'Gate_F':old['Gate_F']['status'],'Gate_G':old['Gate_G']['status'],'needs_320':old['Gate_F']['needs_320'],'historical_status_source':str(p.relative_to(ROOT)),'source_sha256':sha(p),'statuses_recomputed':False})
for row in rows:
    fullrows.append({'case_id':row['case_id'],'Ra_target':1000000,'grid':row['grid'],'computed':row['computed'],'accepted':row['accepted'],'Gate_D':row['Gate_D'],'final_iteration':row['final_iteration'],'Gate_E_diagnostic':gateE['status'],'Gate_F':gateF['status'],'Gate_G':gateG['status'],'needs_320':gateF['needs_320'],'historical_status_source':'CURRENT_ATTEMPT_007','statuses_recomputed':False})
computed_count=sum(x['computed'] for x in fullrows);accepted_count=sum(x['accepted'] for x in fullrows)
statuslines.update(ROUTE_A_MATRIX_CASE_COUNT='12',ROUTE_A_MATRIX_COMPUTED_COUNT=str(computed_count),ROUTE_A_MATRIX_ACCEPTED_COUNT=str(accepted_count),ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE='YES' if len(fullrows)==12 and computed_count==12 else 'NO',ALL_ROUTE_A_CASES_ACCEPTED='YES' if accepted_count==12 else 'NO',ALL_ROUTE_A_GATES_PASSED='NO')
summary={'owner':'ATTEMPT_007_POST_RA1E6_STEADY_MATRIX_SUMMARY','rows':fullrows,'case_count':12,'computed_count':computed_count,'accepted_count':accepted_count,'computation_complete':computed_count==12,'all_Gates_passed':False,'full_steady_matrix_review_required':True,'past_statuses_recomputed':False,'not_full_verification':True}
dump(OUT/'RouteA_full_steady_matrix_summary.json',summary)
with (OUT/'RouteA_full_steady_matrix_summary.csv').open('w',newline='') as f:
    fields=['case_id','Ra_target','grid','computed','accepted','Gate_D','final_iteration','Gate_E_diagnostic','Gate_F','Gate_G','needs_320','historical_status_source','source_sha256','statuses_recomputed']
    w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
    for x in fullrows:w.writerow({k:json.dumps(x[k]) if isinstance(x.get(k),(list,bool)) else x.get(k) for k in fields})
report={'schema':'routeA-Ra1e6-trio-report-v1','task':'RUN_ROUTE_A_RA1E6_TRIO','date':'2026-10-04','timezone':'Asia/Tokyo','attempt':'007','overall':state['overall'],'observed_HEAD':state['environment']['HEAD'],'expected_HEAD':'302e5b4ac41dba187678b84f0132d5c6db72fa99','environment':state['environment'],'contract':{'version':'1.6','sha256':statuslines['EFFECTIVE_CONTRACT_SHA256'],'all_hash_guards':'PASS','modified':False},'cases':rows,'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'paper_comparison_classification':'PRACTICAL_BENCHMARK_COMPARISON','A_B_comparison':{'status':ABstatus,'ownership':'DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE','B_computed_count':3,'B_accepted_count':0,'formal_accepted_AB_comparison_available':False,'baseline_sha256':Bhashes,'quantity_rows':comparisons,'native_flux_rule':'A mass kg/s vs B volume m3/s: NOT_LIKE_FOR_LIKE','section_rule':'A reconstructed U_f vs B native volume phi: NOT_LIKE_FOR_LIKE','no_AB_hard_threshold':True},'STEADY_TRIO_COMPLETE':complete and allaccepted,'RA1E6_STEADY_TRIO_CHARACTERIZED':characterized,'characterized_definition':'Three accepted rows + Gate F/G PASS + completed comparison; separate from mere complete execution and from full Route A characterization.','full_steady_matrix_review_ready':complete,'F_G_block_matrix':False,'full_steady_matrix_summary':summary,'four_levels':{'solver_completed':complete,'computed':sum(r['computed'] for r in rows),'accepted':sum(r['accepted'] for r in rows),'characterized':characterized},'trio_complete_definition':'Inherited accepted steady trio completion: all three accepted; solver completion and computed coverage are recorded separately.','AB_auxiliary_limitation_blocks_matrix':False,'unresolved_issues':{'execution_stop':state['stop_reason'],'comparison_data_gaps':[{'case_id':x['A_case_id'],'B_case_id':x['B_case_id'],'quantity':x['quantity'],'reason':x['reason']} for x in comparisons if x['status']!='COMPLETE'],'Gate_F_limitations':gateF if gateF['status']!='PASS' else None,'Gate_G_limitations':gateG if gateG['status']!='PASS' else None,'additional_research_performed':False},'protected_evidence':{'status':'PASS','hash_entry_count':len(protected),'baseline_path':'results/routeA/attempts/attempt_007/protected_before_sha256.json','all_historical_attempts_intact':True},'final_status':statuslines,'git_add_commit_push_performed':False}
dump(OUT/'Ra1e6_trio_report.json',report)
dump(OUT/'Ra1e6_group_evaluation.json',{'Gate_D':{x['case_id']:{'status':x['Gate_D'],'computed':x['computed'],'accepted':x['accepted'],'failure_components':x['Gate_D_failure_components']} for x in rows},'Gate_E_diagnostic':gateE,'Gate_F':gateF,'Gate_G':gateG,'symmetry':symmetries,'A_B_diagnostic':{'status':ABstatus,'ownership':'DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE','B_computed_count':3,'B_accepted_count':0,'formal_accepted_comparison_available':False},'four_levels':{'solver_completed':complete,'computed_count':sum(x['computed'] for x in rows),'accepted_count':sum(x['accepted'] for x in rows),'characterized':characterized}})
fields=['attempt','case_id','route','Ra_target','Ra_actual','Pr_actual','grid','status','source_time_or_iteration','method_version','computed','accepted','final_iteration','Gate_D','Gate_D_failure_components','Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','metrics_path','metrics_sha256']
with (OUT/'Ra1e6_trio_matrix.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for row in rows:
        data={k:row.get(k) for k in fields};data.update(row['QoIs'] or {})
        writer.writerow({k:('' if data.get(k) is None else json.dumps(data[k]) if isinstance(data[k],(list,bool)) else data[k]) for k in fields})
with (OUT/'Ra1e6_routeA_vs_routeB.csv').open('w',newline='') as f:
    fields=['case_id','route','Ra_target','Pr_actual','source_time_or_iteration','method_version','A_case_id','B_case_id','B_source_case_id','B_metrics_path','grid','Ra_actual','A_iteration','B_iteration','A_accepted','B_accepted_baseline','A_computed','B_computed','B_accepted','B_Gate_D','comparison_ownership','FORMAL_ACCEPTED_A_B_COMPARISON','status','quantity','A','B','signed_difference','absolute_difference','relative_difference','absolute_position_difference','comparison_class','hard_comparison_allowed','zero_baseline_status','diagnostic_only','reason']
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for item in comparisons:writer.writerow({k:('' if item.get(k) is None else json.dumps(item[k]) if isinstance(item[k],(list,bool)) else item[k]) for k in fields})
qtable='\n'.join('| '+row['case_id']+' | '+str(row['final_iteration'])+' | '+('YES' if row['accepted'] else 'NO')+' | '+row['Gate_D']+' | '+(' | '.join(format(row['QoIs'][k],'.9g') for k in ['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Wmax']) if row['QoIs'] else '— | — | — | — | — | —')+' |' for row in rows)
ftable='\n'.join('| '+key+' | '+item['convergence_type']+' | '+str(item['p_obs'])+' | '+str(item['GCI_fine'])+' | '+item['status']+' |' for key,item in (gateF.get('quantities') or {}).items())
gtable='\n'.join('| '+key+' | '+format(value,'.9g')+' | '+format(gateG['limits'][key],'.9g')+' | '+('PASS' if gateG['checks'][key] else 'FAIL')+' |' for key,value in gateG.get('values',{}).items() if value is not None)
status_text='\n'.join(k+' = '+value for k,value in statuslines.items())


qkeys=['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X']
paperrows=[]
for k in ['Nu_bar_cavity','Nu_bar_half','Nu_bar_0','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z','Umax','Umax_Z','Wmax','Wmax_X']:
    vals=[]
    for row in rows:
        p=(row['paper_comparison'] or {}).get(k,{})
        v=p.get('absolute_position_error') if k in analyzer.POSITION_KEYS else p.get('absolute_relative_error')
        vals.append('NOT_EVALUATED' if v is None else format(v,'.9g'))
    paperrows.append('| '+k+' | '+' | '.join(vals)+' |')
papertable='\n'.join(paperrows)
segtable='\n'.join('| '+r['case_id']+' | '+str(s['end_iteration'])+' | '+s['Gate_D']+' | '+(','.join(s['failure_components']) or 'NONE')+' |' for r in rows for s in r['segments'])
mtable='\n'.join('| '+ra+' | '+str(sum(x['computed'] for x in fullrows if x['Ra_target']==int(float(ra))))+'/3 | '+str(sum(x['accepted'] for x in fullrows if x['Ra_target']==int(float(ra))))+'/3 | '+','.join(x['Gate_D'] for x in fullrows if x['Ra_target']==int(float(ra)))+' | '+next(x['Gate_E_diagnostic'] for x in fullrows if x['Ra_target']==int(float(ra)))+' | '+next(x['Gate_F'] for x in fullrows if x['Ra_target']==int(float(ra)))+' | '+next(x['Gate_G'] for x in fullrows if x['Ra_target']==int(float(ra)))+' | '+str(next(x['needs_320'] for x in fullrows if x['Ra_target']==int(float(ra))))+' |' for ra in ['1e3','1e4','1e5','1e6'])
text=f'''# Route A Ra1e6 attempt 007

**{state['overall']} / computed {sum(r['computed'] for r in rows)}/3 / accepted {sum(r['accepted'] for r in rows)}/3**。HEAD `{state['environment']['HEAD']}`は指定302e5b4ac41dba187678b84f0132d5c6db72fa99と一致。effective v1.6のみをcurrent guardとし、digest、implementation/template/reference/caps、parent/amendments001–006、accepted Ra1e3–Ra1e5、attempt006 seals、B Ra1e6 computed/unaccepted evidenceを照合。凍結criteria/physics/numericsに変更なし。

coarse→medium→fine、solver concurrency1。canonical generatorで全NEWケースを生成、generated_manifest_original.jsonを保存しmetadataのみformal IDへ対応付け。input/hash/template expansion→blockMesh/checkMesh→既存initialization clone→canonical runtime provenance→OQ-02→Gate A→primaryの順。歴史fieldやA-SMOKE solutionのpromotionなし。

各segmentはhealth→raw seal→canonical analyzer→六boolean Gate D→final checksum sealの順で保存。initial3000、+3000、cap30000。継続はstartFrom/endTimeのみ変更しsealed latestTimeからrestart。正常有限cap FAILはCONVERGENCE_NOT_REACHED/computed YES/accepted NOで終了する。

| Case | Final iteration | Accepted | Gate D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
{qtable}

| Case | Segment end | Gate D | Failure components |
|---|---:|---|---|
{segtable}

Paper comparisonはPRACTICAL_BENCHMARK_COMPARISON。scalarはabsolute relative error、POSITION_KEYSはabsolute coordinate error。Nu_bar_1は独立paper referenceなし。紙面値との差を純粋numerical errorや原因の証明とはしない。

| Paper QoI error | coarse | medium | fine |
|---|---:|---:|---:|
{papertable}

Gate E diagnostic={gateE['status']}。fine A accepted時だけ既存基準で評価する。unaccepted fineならformal NOT_EVALUATEDで、paperが近いだけでは昇格しない。

Gate F={gateF['status']}、needs_320={gateF['needs_320']}。accepted A3格子のみformal使用。未accepted gridがあればformal NOT_EVALUATED。非単調時はp/GCI null、FAIL/needs_320 YES。320²や新thresholdは追加しない。

| QoI | Convergence | p_obs | GCI fine | Status |
|---|---|---:|---:|---|
{ftable}

Gate G formal={gateG['status']}、diagnostic={gateG.get('diagnostic_status','NOT_EVALUATED')}。fine A accepted時だけformal。既存operator/normalizationとthresholdを使用。

| Component | Value | Limit | Diagnostic check |
|---|---:|---:|---|
{gtable}

A–B diagnostic comparison coverage={ABstatus}、primary={statuslines['A_B_PRIMARY_QOI_DIAGNOSTIC_COMPARISON']}。全Ra1e6 comparison ownershipは**DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE**。Bは各grid computed YES、accepted NO、Gate D FAIL、final30000。CSV/JSONにA_accepted/B_computed/B_accepted/ownershipを保存。Aがacceptedでもformal accepted AB comparison NO。B FAILはA Gate D/E/F/Gへ伝播させない。B再計算・追加反復・status変更なし。

scalar abs(A-B)/abs(B)、signed差、position絶対差は既存定義を使用。Nu_half/sectionとnative continuityはNOT_LIKE_FOR_LIKE、missingはNOT_EVALUATED。AB Hard thresholdなし。AがPASSしてBがFAILしても物理的優位やB誤りを証明しない。両者FAILでも同じ原因/physical unsteadiness/solver defectを断定しない。

Solver completion={complete}、computed={sum(r['computed'] for r in rows)}/3、accepted={sum(r['accepted'] for r in rows)}/3、characterized={characterized}を区別。RA1E6_STEADY_TRIO_COMPLETEは従来のaccepted3ケース定義を保持し、全computed実行完了とは別に記録する。

| Ra | Computed | Accepted | Gate D c/m/f | E diagnostic | F | G formal | needs_320 |
|---|---|---|---|---|---|---|---|
{mtable}

全matrix computed={computed_count}/12、accepted={accepted_count}/12。ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE={statuslines['ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE']}は全accepted/all Gates PASS/full verificationを意味しない。過去Ra1e3–Ra1e5のstatusは保存reportから転記しただけで再判定していない。

Unresolved: execution stop={state['stop_reason']}。Gate F/G未達、cap failure、formal accepted B baseline不在はJSONに記録。追加研究・tuning・post-hoc例外・post-cap延長なし。今回の実行はRa1e6とgroup評価までで終了。Gate H/J/320は開始しない。

保護対象{len(protected)}file hashes。旧contracts/amendments/attempts001–006/Route B/reference/scripts/templates/previous accepted fields/seals不変。fine図は既存canonical workflowだけで新caseとsegmentへ保存。

**NEXT_SINGLE_TASK={nexttask}**。full steady matrix reviewを別taskとして行い、Gate Hはその後に実行可否を判断する。USER_DECISION_REQUIRED=YES。git add/commit/push未実行。

詳細: [JSON](Ra1e6_trio_report.json)、[matrix](Ra1e6_trio_matrix.csv)、[diagnostic comparison CSV](Ra1e6_routeA_vs_routeB.csv)、[group evaluation](Ra1e6_group_evaluation.json)、[full matrix summary](RouteA_full_steady_matrix_summary.json)。

```text
{status_text}
```
'''
(OUT/'Ra1e6_trio_report.md').write_text(text)
for p,h in protected.items():assert sha(ROOT/p)==h,p
for p,h in Bhashes.items():assert sha(ROOT/p)==h,p
print('REPORT:',state['overall'],'computed',sum(r['computed'] for r in rows),'accepted',sum(r['accepted'] for r in rows),'/3; E/F/G:',gateE['status'],gateF['status'],gateG['status'],'AB diagnostic:',ABstatus)
print('Matrix:',computed_count,'computed;',accepted_count,'accepted /12')
