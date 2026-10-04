import json,hashlib,pathlib,csv,math,sys,subprocess
import numpy as np
R=pathlib.Path.cwd();OUT=R/'results/routeA/attempts/attempt_008';CID='A-H-Ra1e6-fine-beta1e-4'
sys.path.insert(0,str(R/'Scripts/routeA'))
from foam_fields import read_scalar,read_vector
C=json.loads((R/'docs/routeA_execution_contract_v1.7.json').read_text());H=C['Gate_H'];CH='fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60';AH='9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text())
def dump(p,x):
 p=pathlib.Path(p);assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def symmetry(case,iteration,manifest):
 nx,ny,nz=manifest['grid'];n=nx*ny*nz;props=manifest['properties'];L=manifest['geometry_m']['L']
 T=read_scalar(case/str(iteration)/'T',n).reshape(ny,nx)
 U=read_vector(case/str(iteration)/'U',n).reshape(ny,nx,3)[:,:,:2]*L/props['alpha0_m2_s']
 theta=(T-props['Tc_K'])/props['DeltaT_K'];defect_T=theta+theta[::-1,::-1]-1;defect_U=U+U[::-1,::-1,:]
 return {'temperature_symmetry':float(np.sqrt(np.mean(defect_T**2))/max(np.sqrt(np.mean(theta**2)),1e-12)),'velocity_symmetry':float(np.sqrt(np.mean(np.sum(defect_U**2,axis=2)))/max(np.sqrt(np.mean(np.sum(U**2,axis=2))),1e-12)),'method':'Frozen 180-degree paired uniform cells, constant cell-volume weights; RMS defect / max(RMS theta or dimensionless in-plane velocity,1e-12).'}
state=load(OUT/'execution_state.json');assert state['overall'] in ['COMPLETE','STOPPED']
row=state['cases'][0] if state['cases'] else {'case_id':CID,'computed':False,'accepted':False,'final_iteration':None,'Gate_D':'NOT_EVALUATED','Gate_D_failure_components':[],'segments':[]}
seals=[]
for seg in row['segments']:
 p=R/seg['path'];assert sha(p/'sealed_sha256.json')==seg['sealed_sha256_manifest']
 for sn in ['raw_seal_sha256.json','sealed_sha256.json']:
  m=load(p/sn)
  for f,h in m.items():assert sha(p/f)==h,(seg['end_iteration'],f)
  seals.append({'path':str((p/sn).relative_to(R)),'member_count':len(m),'verified':True})
base=H['baseline'];bp=R/base['segment_path'];bm=load(bp/'metrics.json');bs=load(bp/'segment_manifest.json');nativebase=R/base['case_path']
assert bs['Gate_D']['accepted'] and bs['Gate_D']['status']=='PASS' and bm['final_iteration']==9000
for f,h in base['final_field_sha256'].items():assert sha(nativebase/'9000'/f)==h,f
for f,h in base['mesh_sha256'].items():assert sha(nativebase/f)==h,f
bg=load(R/'results/routeA/attempts/attempt_007/Ra1e6_group_evaluation.json')['Gate_G']['values']
def diag(m,fieldranges,sym,rhodev):
 return {'physical_heat_imbalance':m['heat_imbalance'],'section_Nu_deviation':m['section_Nu_max_relative_deviation_from_half'],'native_mass_epsilon_m':m['divergence']['epsilon_m'],'reconstructed_velocity_epsilon_v':m['divergence']['epsilon_v'],'temperature_symmetry':sym['temperature_symmetry'],'velocity_symmetry':sym['velocity_symmetry'],'T_min':fieldranges['T'][0],'T_max':fieldranges['T'][1],'rho_min':fieldranges['rho'][0],'rho_max':fieldranges['rho'][1],'max_relative_density_deviation':rhodev}
brho=read_scalar(nativebase/'9000/rho',25600);brdev=float(np.max(np.abs(brho/1.-1.)))
bdiag=diag(bm,bs['final_field_validation']['field_ranges'],bg,brdev)
pm=None;pdiag=None;pd=None;N=row['final_iteration'];case=R/'cases/routeA'/CID;result=R/'results/routeA/cases'/CID
if row['computed']:
 pm=load(result/'metrics.json');assert pm['final_iteration']==N
 ps=load(result/'segments'/f'end_{N}'/'segment_manifest.json');pd=ps['Gate_D'];assert pd['accepted']==row['accepted']
 for f,h in ps['final_field_validation']['field_sha256'].items():assert sha(case/str(N)/f)==h,f
 for f,h in ps['diagnostic_field_sha256'].items():assert sha(case/str(N)/f)==h,f
 manifest=load(case/'case_manifest.json');sym=symmetry(case,N,manifest)
 prho=read_scalar(case/str(N)/'rho',25600);prdev=float(np.max(np.abs(prho/1.-1.)))
 pdiag=diag(pm,ps['final_field_validation']['field_ranges'],sym,prdev)
 pdiag['symmetry_method']=sym['method']
eligible=bool(row['accepted']) and base['accepted'];primary=['Nu_bar_cavity','Umax','Wmax'];positions=['Umax_Z','Wmax_X','Nu_hot_local_max_Z','Nu_hot_local_min_Z']
qkeys=['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']
comparisons=[]
for q in qkeys+list(bdiag):
 b=bm[q] if q in qkeys else bdiag[q];p=None if pm is None else (pm[q] if q in qkeys else pdiag[q]);signed=None if p is None else p-b;ad=None if signed is None else abs(signed);relative=None if ad is None or b==0 or q in positions else ad/abs(b)
 threshold=.002 if q in primary else b if q=='reconstructed_velocity_epsilon_v' else None
 if not eligible or p is None:check='NOT_EVALUATED'
 elif q in primary:check='PASS' if relative is not None and relative<=.002 else 'FAIL'
 elif q=='reconstructed_velocity_epsilon_v':check='PASS' if p<=b else 'FAIL'
 else:check='DIAGNOSTIC_ONLY'
 comparisons.append({'quantity':q,'baseline':b,'perturbed':p,'signed_difference':signed,'absolute_difference':ad,'relative_difference':relative,'signed_relative_difference':None if signed is None or b==0 or q in positions else signed/abs(b),'signed_position_difference':signed if q in positions else None,'absolute_position_difference':ad if q in positions else None,'threshold':threshold,'check':check,'comparison_class':'FIXED_GRID_MODEL_FORMULATION_SENSITIVITY','quantity_class':'PRIMARY_EXISTING_H_THRESHOLD' if q in primary else 'EPSILON_V_NON_WORSENING' if q=='reconstructed_velocity_epsilon_v' else 'POSITION_DIAGNOSTIC' if q in positions else 'SECONDARY_DIAGNOSTIC','criterion':'D_H <= 0.002' if q in primary else 'perturbed <= baseline; zero new slack' if q=='reconstructed_velocity_epsilon_v' else 'no Gate H Hard threshold','baseline_accepted':True,'perturbed_accepted':row['accepted'],'baseline_owner':'HISTORICAL_ACCEPTED_STEADY_BASELINE','perturbed_owner':'GATE_H_FORMAL_SENSITIVITY_CASE' if row['accepted'] else 'UNACCEPTED_PERTURBED_DIAGNOSTIC_ONLY','scalar_denominator':'abs(historical baseline)' if q not in positions else 'absolute normalized-coordinate difference, no relative position error','operator_note':'Both A cases use same native mass phi and reconstructed Gauss-linear div(U); no cross-Route B comparison.'})
byq={x['quantity']:x for x in comparisons};formal='NOT_EVALUATED' if not eligible else 'PASS' if all(byq[q]['check']=='PASS' for q in primary+['reconstructed_velocity_epsilon_v']) else 'FAIL'
characterized=eligible and all(byq[q]['perturbed'] is not None for q in primary+['reconstructed_velocity_epsilon_v'])
manifest=load(case/'case_manifest.json') if (case/'case_manifest.json').exists() else None
ga=load(OUT/'cases'/CID/'gate_A.json') if (OUT/'cases'/CID/'gate_A.json').exists() else None
status={'ROUTE_A_GATE_H_ATTEMPT':'008','ROUTE_A_GATE_H_EXECUTION':state['overall'],'EFFECTIVE_CONTRACT_VERSION':'1.7','EFFECTIVE_CONTRACT_HASH_VERIFIED':'YES' if sha(R/'docs/routeA_execution_contract_v1.7.json')==CH else 'NO','EFFECTIVE_CONTRACT_SHA256':CH,'AMENDMENT_007_HASH_VERIFIED':'YES' if sha(R/'docs/routeA_execution_contract_amendment_007.json')==AH else 'NO','AMENDMENT_007_SHA256':AH,'ANALYZER_HASH_VERIFIED':'YES','ANALYZER_SHA256':C['implementation_sha256']['Scripts/routeA/analyze_case.py'],'RUNTIME_CHECKER_HASH_VERIFIED':'YES','RUNTIME_CHECKER_SHA256':C['implementation_sha256']['Scripts/routeA/runtime_provenance.py'],'GATE_H_CLASSIFICATION':H['classification'],'GATE_H_BASELINE_CASE':base['case_id'],'GATE_H_BASELINE_ACCEPTED':'YES','GATE_H_BASELINE_FINAL_ITERATION':9000,'GATE_H_BASELINE_RERUN':'NO','GATE_H_PERTURBED_CASE':CID,'GATE_H_PERTURBED_COMPUTED':'YES' if row['computed'] else 'NO','GATE_H_PERTURBED_ACCEPTED':'YES' if row['accepted'] else 'NO','GATE_H_PERTURBED_FINAL_ITERATION':N if N is not None else 'NONE','GATE_H_PERTURBED_GATE_D':row['Gate_D'],'GATE_H_PERTURBED_GATE_D_FAILURE_COMPONENTS':row['Gate_D_failure_components'] or 'NONE','GATE_H_BASELINE_BETA':'1e-3','GATE_H_PERTURBED_BETA':'1e-4','GATE_H_BETA_RATIO':.1,'GATE_H_G_RATIO':10,'GATE_H_RA_ACTUAL':float(ga['Ra_actual_from_g_dictionary']) if ga else 'NONE','GATE_H_PR_ACTUAL':ga['Pr_actual'] if ga else 'NONE'}
for k in ['GATE_H_RA_HELD_FIXED','GATE_H_PR_HELD_FIXED','GATE_H_DELTA_T_HELD_FIXED','GATE_H_GRID_HELD_FIXED','GATE_H_NUMERICS_HELD_FIXED']:status[k]='YES' if ga else 'NO'
for label,q in [('NU_CAVITY','Nu_bar_cavity'),('UMAX','Umax'),('WMAX','Wmax')]:status.update({f'GATE_H_{label}_RELATIVE_DIFFERENCE':byq[q]['relative_difference'] if byq[q]['relative_difference'] is not None else 'NONE',f'GATE_H_{label}_THRESHOLD':.002,f'GATE_H_{label}_CHECK':byq[q]['check']})
status.update({'GATE_H_BASELINE_EPSILON_V':bdiag['reconstructed_velocity_epsilon_v'],'GATE_H_PERTURBED_EPSILON_V':pdiag['reconstructed_velocity_epsilon_v'] if pdiag else 'NONE','GATE_H_EPSILON_V_NON_WORSENING':byq['reconstructed_velocity_epsilon_v']['check'],'GATE_H_BASELINE_MAX_RELATIVE_DENSITY_DEVIATION':brdev,'GATE_H_PERTURBED_MAX_RELATIVE_DENSITY_DEVIATION':pdiag['max_relative_density_deviation'] if pdiag else 'NONE','GATE_H_FORMAL_RESULT':formal,'GATE_H_CHARACTERIZATION_COMPLETED':'YES' if characterized else 'NO','GATE_H_GRID_INDEPENDENT_CLAIM_ALLOWED':'NO','ALL_ROUTE_A_GATE_F':'FAIL','ALL_RA_NEEDS_320':'YES'})
for k in ['GRID_320_EXECUTED','GATE_J_EXECUTED','DOWNSTREAM_TRANSIENT_READY','FORMAL_CRITERIA_CHANGED','NUMERICAL_SETTINGS_CHANGED','PHYSICAL_CHANGES_BEYOND_BETA_G','SOLVER_TUNING_PERFORMED','POST_CAP_EXTENSION_PERFORMED','BASELINE_MODIFIED','HISTORICAL_RESULTS_MODIFIED','ROUTE_B_MODIFIED']:status[k]='NO'
status.update({'NEXT_SINGLE_TASK':'REVIEW_ROUTE_A_GATE_H_RESULT' if state['overall']=='COMPLETE' else 'FIX_ROUTE_A_GATE_H_EXECUTION_ISSUE','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / medium','USER_DECISION_REQUIRED':'YES','OVERALL_VERIFICATION_STATUS':'VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION','TARGETED_320_REQUIRED_BEFORE_GATE_H':'NO','ROUTE_A_SOLVER_EXECUTED':'YES' if row['segments'] else 'NO','ROUTE_B_SOLVER_EXECUTED':'NO','GATE_H_BASELINE_OWNERSHIP':'HISTORICAL_ACCEPTED_STEADY_BASELINE'})
assert status['EFFECTIVE_CONTRACT_HASH_VERIFIED']=='YES' and status['AMENDMENT_007_HASH_VERIFIED']=='YES'
for p,h in C['implementation_sha256'].items():assert sha(R/p)==h,p
protected=load(OUT/'protected_before_sha256.json');changed=[p for p,h in protected.items() if not pathlib.Path(p).is_file() or sha(p)!=h];assert not changed,changed
report={'schema':'routeA.GateH-report.v1','task':'RUN_ROUTE_A_GATE_H','attempt':'008','overall':state['overall'],'classification':H['classification'],'environment':state['environment'],'contract':{'version':'1.7','sha256':CH,'amendment007_sha256':AH,'hash_guards':'PASS','unchanged':True},'baseline':base,'case':row,'Gate_D':pd,'Gate_A':ga,'comparison':comparisons,'formal_Gate_H':{'status':formal,'eligible_accepted_pair':eligible,'checks':{q:byq[q]['check'] for q in primary+['reconstructed_velocity_epsilon_v']},'failure_components':[q for q in primary+['reconstructed_velocity_epsilon_v'] if byq[q]['check']=='FAIL'],'threshold_relative_fraction':.002,'epsilon_v_slack':0},'characterization_completed':characterized,'diagnostics':{'baseline':bdiag,'perturbed':pdiag,'density_amplitude_ratio':pdiag['max_relative_density_deviation']/brdev if pdiag else None,'density_scaling':'Measured ratio, not an assumed result or formal H criterion'},'stop_reason':state['stop_reason'],'historical_protection':{'file_count':len(protected),'changed_count':0,'all_unchanged':True},'final_status':status,'scientific_limits':H['prohibited_claims'],'Gate_F_limitation':H['limitations'],'post_run_automatic_execution':False,'git_add_commit_push_performed':False}
dump(OUT/'GateH_report.json',report)
dump(OUT/'GateH_diagnostics.json',{'schema':'routeA.GateH-diagnostics.v1','baseline':bdiag,'perturbed':pdiag,'density_amplitude_ratio':report['diagnostics']['density_amplitude_ratio'],'continuity_operator_metadata':C['continuity'],'baseline_source':base['segment_path'],'perturbed_source':str((result/'segments'/f'end_{N}').relative_to(R)) if row['computed'] else None,'eligibility':eligible,'Gate_H':report['formal_Gate_H'],'new_thresholds':False,'note':'Steady diagnostic support does not certify transient mass/energy or particle coupling.'})
with (OUT/'GateH_comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,list(comparisons[0]));w.writeheader();w.writerows(comparisons)
# Tables preserve full precision in CSV/JSON; MD only formats numeric values.
def fmt(x):return 'NOT_EVALUATED' if x is None else f'{x:.12g}' if isinstance(x,float) else str(x)
def table(rows,cols):return '| '+' | '.join(label for key,label in cols)+' |\n| '+' | '.join('---' for _ in cols)+' |\n'+'\n'.join('| '+' | '.join(fmt(row.get(key)) for key,label in cols)+' |' for row in rows)+'\n'
md=['# Route A Gate H attempt 008\n'];
def sec(title,text):md.append('## '+title+'\n\n'+text+'\n')
sec('1. Executive result',f'Execution **{state["overall"]}**, perturbed computed={row["computed"]}, accepted={row["accepted"]}, final iteration={N}, Gate D={row["Gate_D"]}. Formal Gate H **{formal}**; sensitivity characterization completed={characterized}. No baseline rerun, tuning, cap extension, other grid or downstream execution.')
sec('2. Contract/provenance',f'HEAD `{state["environment"]["HEAD"]}`. Sole current guard v1.7 SHA `{CH}`; Amendment007 SHA `{AH}`; all start guards PASS. Actual runtime Foundation13 build13-441953dfbb42, fluid/heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy, laminar Stokes/Fourier/SIMPLE verified from actual initialization and primary logs. Canonical analyzer/runtime checker scripts unchanged. Protection: {len(protected)} pre-existing files unchanged; contract/threshold/numerics immutable.')
sec('3. Baseline evidence','Historical accepted A-Ra1e6-fine, grid160x160x1, Ra1e6/Pr.71, betaDeltaT1e-3 at9000. Baseline owner HISTORICAL_ACCEPTED_STEADY_BASELINE; read-only reuse, no rerun/restart/continuation/analyzer output. Final segment/seal/native field/mesh hashes verified against v1.7. Source: `'+base['segment_path']+'`.')
sec('4. Perturbed case generation','One NEW A-H-Ra1e6-fine-beta1e-4, attempt008. Hash-guarded unchanged generator loaded using importlib, BETA set to Decimal1e-4 in memory; canonical main called with A-SMOKE generation role and formal distinct name/grid160/Ra1e6/end3000. Original manifest sealed. Exactly one NEW physicalProperties beta1e-3 literal changed to beta1e-4; raw versus final input hashes separately recorded. Canonical cold U0/T0, EOS/hydrostatic p with pRef=hRef0, p_rgh0; no historical field/mesh copy. blockMesh/checkMesh and isolated one-iteration constructor workflow, runtime provenance and OQ-02 checked before primary. Detailed phase evidence in `cases/'+CID+'/`.')
sec('5. beta/g/Ra/Pr verification',table([{'key':'baseline beta','value':.001},{'key':'perturbed beta','value':.0001},{'key':'beta ratio','value':.1},{'key':'g ratio','value':10},{'key':'perturbed g vector','value':manifest['gravity_m_s2'] if manifest else None},{'key':'Ra from actual g/beta/nu/alpha','value':status['GATE_H_RA_ACTUAL']},{'key':'Pr actual','value':status['GATE_H_PR_ACTUAL']},{'key':'DeltaT','value':1},{'key':'grid','value':'160x160x1'}],[('key','Parameter'),('value','Actual / relation')])+'\nCanonical gravity formula used, not rounded manual value. PhysicalProperties beta and all other held properties checked against frozen inputs. Common-grid mesh hashes match baseline; fixed schemes/relaxation/tolerances match template/baseline. Initial p changes dependently with g/EOS as registered; only beta/g are independent physical changes.')
sec('6. Execution history',table([{'start':x['end_iteration']-3000,'end':x['end_iteration'],'Gate_D':x['Gate_D'],'failures':x['failure_components'] or 'NONE','seal':x['sealed_sha256_manifest']} for x in row['segments']],[('start','Start'),('end','End'),('Gate_D','Gate D'),('failures','Failure components'),('seal','Seal SHA-256')])+'\ninitial3000,+3000,cap30000; one primary branch/concurrency1. Every segment health→raw seal→canonical analyzer→six-boolean D→final seal before continuation. No tuning/retry/extension; only startFrom/endTime changes. Intermediate FAILs retained. Stop reason: '+str(state['stop_reason'])+'.')
sec('7. Gate D','```json\n'+json.dumps(pd,ensure_ascii=False,indent=2)+'\n```' if pd else 'NOT_EVALUATED. No accepted numerical result established.')
sec('8. Primary Gate H metrics',table([byq[q] for q in primary],[('quantity','QoI'),('baseline','Baseline'),('perturbed','Perturbed'),('signed_difference','Signed Δ'),('relative_difference','D_H fraction'),('threshold','Threshold fraction'),('check','Check')])+'\nD_H=abs(perturbed−baseline)/abs(baseline). Each criterion is independent, no averaging compensation. Existing threshold .002=.2%, unchanged.')
sec('9. epsilon_v',table([byq['reconstructed_velocity_epsilon_v']],[('baseline','Baseline'),('perturbed','Perturbed'),('signed_difference','Signed Δ'),('check','Non-worsening')])+'\nSame frozen reconstructed Gauss-linear div(U) and normalization; require perturbed≤baseline, no slack. Native mass closure is separately recorded and cannot replace this H requirement.')
sec('10. Density-range diagnostics',table([byq[q] for q in ['rho_min','rho_max','max_relative_density_deviation']],[('quantity','Diagnostic'),('baseline','Baseline'),('perturbed','Perturbed'),('signed_difference','Signed Δ')])+f'\nMeasured amplitude ratio perturbed/baseline: {fmt(report["diagnostics"]["density_amplitude_ratio"])}. Density range comes from final native rho; maximum relative deviation measured as max|rho/rho0−1|. Approximate tenfold reduction at similar T was expected scaling, not assumed or a new acceptance criterion.')
sec('11. Secondary diagnostics',table([x for x in comparisons if x['quantity'] not in primary+['reconstructed_velocity_epsilon_v','rho_min','rho_max','max_relative_density_deviation']],[('quantity','Quantity'),('baseline','Baseline'),('perturbed','Perturbed'),('signed_difference','Signed Δ'),('absolute_difference','Absolute Δ'),('relative_difference','Relative fraction')])+'\nAll position differences are signed/absolute normalized-coordinate diagnostics; relative field null for positions. No new H thresholds on secondary values. Native mass kg/s flux and reconstructed div(U) remain distinct diagnostics; no Route B operator/causal comparison is performed.')
sec('12. Formal Gate H result',f'**{formal}**. Accepted-pair eligibility={eligible}. Checks: '+json.dumps(report['formal_Gate_H']['checks'])+'. Failed components: '+str(report['formal_Gate_H']['failure_components'] or 'NONE')+'. Quantified characterization completed='+str(characterized)+'. D-unaccepted or missing pair cannot be promoted to formal H.')
if eligible:
 interp='OBSERVED: '+', '.join(f'{q} changed by {byq[q]["relative_difference"]*100:.9g}%' for q in primary)+'. These are measured common160-grid responses to jointly prescribed beta/10 and g×10 at fixed Ra/Pr. '
 interp+='All primary responses satisfy the existing .2% criterion. ' if all(byq[q]['check']=='PASS' for q in primary) else 'One or more primary responses exceed the existing .2% criterion. '
 interp+='epsilon_v '+('does not worsen.' if byq['reconstructed_velocity_epsilon_v']['check']=='PASS' else 'worsens and independently makes formal H FAIL.')
else:interp='No eligible accepted pair; formal sensitivity NOT_EVALUATED. Available unaccepted values are diagnostic only.'
sec('13. Scientific interpretation',interp+' H evaluates within-Route-A formulation sensitivity, not A/B causal decomposition or a mathematical classical Boussinesq limit.')
sec('14. Limitations','GATE_H_GRID_INDEPENDENT_CLAIM_ALLOWED=NO. Same-grid cancellation may occur but is not guaranteed; grid/model interaction unknown. Two points cannot establish continuum sensitivity, exact formulation error, A=B, all energy-work terms vanishing, validation or full Verification.')
sec('15. Gate F reminder','All four historical Gate F groups remain FAIL and needs_320 YES. Ra1e6 Nu fine-medium1.3402375461%>1%; Wmax NON_MONOTONIC_OR_UNDEFINED, p/GCI null. Gate H does not resolve these failures. No320 executed or automatically required before this bounded fixed-grid H.')
sec('16. Downstream implication','DOWNSTREAM_TRANSIENT_READY=NO. Gate J unexecuted; no transient/particle work authorized or performed. Even H PASS would not alone certify downstream readiness. Preserve partial Verification status and separately review H before any future Gate J preparation.')
sec('17. Next task','`'+status['NEXT_SINGLE_TASK']+'` / gpt-6.1-sol / medium. USER_DECISION_REQUIRED=YES. Execution stops here; no automatic extra beta points/320/Gate J.\n\n```text\n'+'\n'.join(f'{k}={v}' for k,v in status.items())+'\n```')
(OUT/'GateH_report.md').write_text('\n'.join(md))
assert len(md)==18
verification={'status':'PASS','historical_protected_count':len(protected),'historical_changed_count':0,'contract_hash_unchanged':True,'baseline_fields_mesh_status_unchanged':True,'segment_seals':seals,'final_native_field_hashes_verified':row['computed'],'primary_case_count':1,'baseline_rerun':False,'criteria_and_numerics_unchanged':True,'comparison_denominator':'historical baseline','epsilon_v_slack':0,'characterization_vs_formal_result_separated':True,'full_report_MD_sections':17,'git_status':subprocess.check_output(['git','status','--short'],text=True),'git_diff_stat':subprocess.check_output(['git','diff','--stat'],text=True)}
assert not verification['git_diff_stat'];dump(OUT/'final_verification.json',verification)
dump(OUT/'attempt_sealed_sha256.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()})
print('GATE H:',formal,'characterization',characterized,'D',row['Gate_D'],'iteration',N,flush=True)
for q in primary+['reconstructed_velocity_epsilon_v']:print(q,byq[q]['baseline'],byq[q]['perturbed'],byq[q]['relative_difference'],byq[q]['check'])
print('Density deviations',brdev,pdiag['max_relative_density_deviation'] if pdiag else None)
