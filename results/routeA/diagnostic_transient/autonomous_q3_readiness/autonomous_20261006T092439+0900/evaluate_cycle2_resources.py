"""Conditional source-frequency resource model; no Q1/Q2 or CFD verdict inferred."""
import sys,json,math,statistics,collections,csv
from pathlib import Path
root=Path.cwd();master=Path(Path('/tmp/route_a_master_path').read_text());sys.path.insert(0,str(root/'Scripts/routeA/diagnostic_transient/compute_revision_v3/measurement'))
from common import atomic,load,sha,CONTRACT
from fixture import graph
from analysis import stability
scout=load(master/'Scout_analysis_cycle_2.json');groups=collections.defaultdict(list)
for r in scout['trials']:groups[r['request']['sample_class'] if r['request']['mode']=='ON' else 'OFF'].append(r)
classstats={}
for cls,rows in groups.items():
 values=[r['representative_seconds'] for r in rows];classstats[cls]={'min_seconds':min(values),'median_seconds':statistics.median(values),'max_seconds':max(values),'repeatability':stability(values,[r['host_stability'] for r in rows]),'JSON_packet_bytes_median':statistics.median(r['callback_JSON_bytes'][-1]-r['callback_JSON_bytes'][0] for r in rows),'socket_send_median_seconds':statistics.median(r['representative_native_spans']['socket_send_exclusive_seconds'] for r in rows),'native_hash_median_seconds':statistics.median(r['representative_native_spans']['hash_exclusive_seconds'] for r in rows),'native_serialization_median_seconds':statistics.median(r['representative_native_spans']['serialization_exclusive_seconds'] for r in rows),'ACK_wait_median_seconds':statistics.median(r['representative_native_spans']['ACK_exclusive_seconds'] for r in rows)}
assert all(x['repeatability']['status']=='STABLE' for x in classstats.values())
rows=[];total={'lower':0.,'central':0.,'conservative':0.};subtotal={k:0. for k in total};names=('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix');counts=collections.Counter()
for node in graph()[1:]:
 p=node['payload'];stage=node['metadata']['stage'];term=p.get('term','');m=sum(k in p for k in names)
 state_copies=1+int('state' in p)+int(stage in ('constructor_complete','preSolve_before','preSolve_after','controller_complete') or stage not in ('term_capture','energy_unrelaxed_assembly','energy_after_relax','energy_after_solve','mass_unrelaxed_assembly','mass_after_solve','pressure_pre_reference','pressure_post_reference','pressure_solved'))
 if m==3:cls='pressure_matrix'
 elif m==2:cls='energy_matrix'
 elif m==1:cls='matrix'
 elif stage in ('preSolve_before','preSolve_after','controller_complete'):cls='controller'
 elif 'integrated_cells' in p:cls='term'
 else:cls='field'
 cost=classstats[cls];lo=cost['min_seconds'];mid=cost['median_seconds'];hi=cost['max_seconds']
 if m==1 and state_copies>1:mid+=.5*classstats['field']['median_seconds'];hi=classstats['energy_matrix']['max_seconds']
 extra=max(0,len(p.get('term_actions',{}))-1);mid+=extra*.1*classstats['term']['median_seconds'];hi+=extra*.25*classstats['term']['max_seconds']
 # Full scientific evaluation and all identity checks are omitted from lower
 # and central resource-primitive proxies. Conservative is sensitivity only,
 # not a mathematical upper: expose the omitted work rather than hide it.
 hi*=2
 exact_match=(stage,term) in {('preSolve_before',''),('preSolve_after',''),('controller_complete',''),('time_start',''),('term_capture','D_B_rho'),('term_capture','div_phi'),('energy_after_solve',''),('pressure_solved','')}
 for k,v in [('lower',lo),('central',mid),('conservative',hi)]:total[k]+=v;subtotal[k]+=v if exact_match else 0
 counts[(stage,term,state_copies,m,cls)]+=1
 rows.append({'stage':stage,'term':term,'state_copies':state_copies,'matrix_slots':m,'mapped_scout_class':cls,'lower_seconds':lo,'central_seconds':mid,'conservative_seconds':hi,'exact_stage_class_measured':exact_match})
assert len(rows)==1144 and sum(r['matrix_slots'] for r in rows)==701
contract=load(CONTRACT);dt=contract['native_deltaT_policy']['maxDeltaT_s'] if 'native_deltaT_policy' in contract else .027734375
scenarios=[]
for endpoint,steps,label in [(.5,math.ceil(710*.5/dt),'earliest candidate maximum-dt step-count floor; ignores startup ramp and Co'),(2,51200,'nominal t*=2 maximum-dt planning count; exact endTime rule may stop just short'),(2,200061,'previous Co0.5 prospective-speed planning count'),(2,400122,'previous Co0.25 prospective-speed planning count')]:
 scenarios.append({'endpoint_tstar':endpoint,'steps':steps,'step_count_label':label,'time_scope':'conditional nonCFD primitive proxy; excludes solver/full scientific checks/audits/finalization/U03','lower_days':steps*total['lower']/86400,'central_days':steps*total['central']/86400,'conservative_days':steps*total['conservative']/86400,'measured_classes_only_subtotal_lower_days':steps*subtotal['lower']/86400})
trace=[r for r in scout['trials']];raw=sum(r['trace_accounting']['uncompressed_bytes'] for r in trace);stored=sum(r['trace_accounting']['stored_bytes'] for r in trace);seconds=sum(r['wall_seconds'] for r in trace)
static_optimistic=sum(min(x['median_seconds'],x['native_hash_median_seconds']+x['native_serialization_median_seconds']+x['socket_send_median_seconds']+x['ACK_wait_median_seconds']) for key,x in classstats.items() if key!='OFF')
review={'schema':'diagnostic_resource_feasibility_scout_review/2','scientific_or_numerical_contract_changed':False,'class_statistics':classstats,'callback_graph':{'callbacks':len(rows),'matrices':sum(r['matrix_slots'] for r in rows)},'source_frequency_mix':[{'stage':k[0],'term':k[1],'state_copies':k[2],'matrix_slots':k[3],'scout_class':k[4],'frequency':v} for k,v in counts.items()],'per_step_primitive_proxy_seconds':total,'measured_exact_stage_subset_seconds':subtotal,'scenarios':scenarios,'not_Q1_timing':True,'not_CFD_runtime_prediction':True,'omitted_full_scientific_processing':['complete field/oldTime/BC identity canonicalization','equation/term reconstruction and multiple replays','U01 terminal state reductions','full startup raw audit9GiB worst case','selected bundle and field/primary publication','native framework fixture generation/OFF fullgraph','finalization and reload/archive costs'],'memory':{'scout_native_peak_bytes':max(r['peak_RSS_bytes']['native'] for r in trace),'scout_backend_peak_bytes':max(r['peak_RSS_bytes']['backend'] for r in trace),'scout_combined_simultaneous_peak_bytes':max(r['peak_RSS_bytes']['combined_simultaneous'] for r in trace),'MemAvailable_min_bytes':min(r['MemAvailable_min'] for r in trace),'full_Q2_memory_event_qualification':'NOT_EXECUTED','formal_feasibility':'UNRESOLVED'},'IO':{'scout_writer_small_commits':'MEASURED_ONLY','full_Q2_IO_qualification':'NOT_EXECUTED','formal_feasibility':'UNRESOLVED'},'trace':{'raw_bytes':raw,'stored_bytes':stored,'lossless_compression_ratio':raw/stored,'raw_rate_bytes_s':raw/seconds,'stored_rate_bytes_s':stored/seconds,'peak_stored_trial_rate_bytes_s':max(r['trace_accounting']['stored_bytes']/r['wall_seconds'] for r in trace),'peak_raw_trial_rate_bytes_s':max(r['trace_accounting']['uncompressed_bytes']/r['wall_seconds'] for r in trace),'all_samples_preserved':True},'static_reference_review':{'implemented':False,'needed_for_receive':False,'socket_send_median_range_seconds':[min(x['socket_send_median_seconds'] for k,x in classstats.items() if k!='OFF'),max(x['socket_send_median_seconds'] for k,x in classstats.items() if k!='OFF')],'reason':'C0 fixed the millisecond socket-send path. Static transport references reconstruct the same full packet; full canonical identity/field evidence/replay remain. It is not defensible to claim static-byte removal fraction as compute-time removal. Source-static formatting/packing cache may help, but cannot certify practical feasibility without a larger compute/evidence reuse design.'},'Q1_Q2':{'new_full_Q1':'NOT_EXECUTED','new_full_Q2':'NOT_EXECUTED','full_Q2_gate_unchanged':True,'historical_Q1':'STOP_WALL_TIME_30s'},'feasibility':{'COMPUTE_FEASIBILITY':'UNRESOLVED','planning_compute_risk':'INFEASIBLE_OR_HIGH_RISK_AT_MONTHS_TO_YEARS_SCALE','MEMORY_FEASIBILITY':'UNRESOLVED','IO_FEASIBILITY':'UNRESOLVED','DIAGNOSTIC_TRANSIENT_RESOURCE_READY':False},'scientific_source_freeze':{'canonical_sha256':sha(CONTRACT),'U03_sha256':sha(root/'Scripts/routeA/diagnostic_transient/v1_1/contract_policy.py')}}
atomic(master,'Cycle2_resource_feasibility_review.json',review)
with (master/'Cycle2_callback_budget_model.csv').open('x') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(json.dumps({'proxy_step_seconds':total,'exact_subset_seconds':subtotal,'scenarios':scenarios,'trace':review['trace']},indent=2))
