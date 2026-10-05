"""Read-only resource audit from existing artifacts. Never invokes a CFD/test solver.
Writes only new resource-review artifacts; v1.2/its code/evidence remain immutable.
"""
from pathlib import Path
import collections,csv,datetime,gzip,hashlib,json,math,os,re,runpy,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/resource_review'
PREP=OUT.parent
U04=PREP/'u04_verification/final';STREAM=U04/'tests/observed_1'
N=25600;NF=50880;NB=640
EXPECTED={'docs/routeA_diagnostic_transient_contract_v1.2.json':'7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd','docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'}
CATS={'A':'Primary scalar histories','B':'Full CFD field snapshots','C':'Outer-iteration field/state copies','D':'Pressure-corrector fields/matrices','E':'Mass total matrix payload','F':'Energy total matrix payload','G':'Term-separated payload','H':'StageLedger metadata','I':'Hash/manifest/provenance','J':'Raw solver logs'}
CELL={'cells','diag','source','volumes','native_lhs_minus_rhs','integrated_cells','Cv'}
FACE={'upper','lower','owner','neighbour','internal','linear_weights'}
BND={'values','face_cells','internal_coeffs','boundary_coeffs'}
LABEL={'owner','neighbour','face_cells'}
SKIP={'constructor_complete','preSolve_before','preSolve_after','controller_complete','auxiliary_fixture'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def numeric_count(x):
 if isinstance(x,bool):return 0
 if isinstance(x,(int,float)):return 1
 if isinstance(x,list):return sum(map(numeric_count,x))
 if isinstance(x,dict):return sum(numeric_count(y) for y in x.values())
 return 0
def projected(x,path=()):
 if isinstance(x,list):
  key=path[-1] if path else ''
  if x and (key in CELL or 'term_actions' in path):return numeric_count(x)*N/len(x)*8
  if x and key in FACE:return numeric_count(x)*NF/len(x)*(4 if key in LABEL else 8)
  if x and key in BND:return numeric_count(x)*NB/len(x)*(4 if key in LABEL else 8)
  return sum(projected(y,path) for y in x)
 if isinstance(x,dict):return sum(projected(y,path+(k,)) for k,y in x.items())
 return 8 if isinstance(x,(int,float)) and not isinstance(x,bool) else 0

def category(key,stage,pressure):
 if key in {'metadata','sequence'}:return 'H'
 if key in {'payload_sha256','manifest','hash'}:return 'I'
 if key=='thermal_context':return 'C'
 if stage=='term_capture' and key in {'matrix','integrated_cells','term','dimensions','operator_dimensions','pre_operator_n_old_times','effective_previous_deltaT'}:return 'G'
 if stage.startswith('mass') and key in {'matrix','current_matrix','unrelaxed_matrix'}:return 'E'
 if stage.startswith('energy') and key in {'matrix','current_matrix','unrelaxed_matrix'}:return 'F'
 if key=='term_actions':return 'G'
 if stage.startswith('pressure') or pressure>0 and stage in {'term_capture','before_pressure_EOS_copy','after_pressure_EOS_copy','before_correctDensity','mass_unrelaxed_assembly','mass_after_solve','after_correctDensity','native_continuity_report'}:return 'D'
 return 'C'
def parts(record):
 m=record['metadata'];s=m['stage'];pc=m['pressure']
 yield 'H',record['metadata'],('metadata',)
 yield 'H',record['sequence'],('sequence',)
 yield 'I',record['payload_sha256'],('payload_sha256',)
 for k,v in record['payload'].items():yield category(k,s,pc),v,('payload',k)
def compression_sample(name,paths):
 raw=b''.join(Path(p).read_bytes() for p in paths);t=time.perf_counter();gz=gzip.compress(raw,compresslevel=6,mtime=0);elapsed=time.perf_counter()-t
 x={'sample':name,'input_bytes':len(raw),'gzip6_bytes':len(gz),'gzip_fraction':len(gz)/len(raw),'gzip_elapsed_s':elapsed,'scope':'EXISTING_SAMPLE_ONLY_NOT_PRODUCTION_RATIO','uncompressed_sha256':hashlib.sha256(raw).hexdigest()}
 tool=shutil.which('zstd')
 if tool:
  t=time.perf_counter();z=subprocess.run([tool,'-q','-3','-c'],input=raw,stdout=subprocess.PIPE,check=True).stdout;x.update(zstd3_bytes=len(z),zstd_fraction=len(z)/len(raw),zstd_elapsed_s=time.perf_counter()-t)
 else:x['zstd_available']=False
 return x

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for name,h in EXPECTED.items():assert sha(ROOT/name)==h,'AUTHORITY_HASH_MISMATCH'
 contract=json.loads((ROOT/'docs/routeA_diagnostic_transient_contract_v1.2.json').read_text())
 original=json.loads((U04/'resource_estimate.json').read_text());assert original['primary_numeric_payload_equivalent_bytes']==5825629244755728
 verify=json.loads((U04/'tests/verification_summary.json').read_text())
 known='4986b1a4fbf3219aebfbc7938665c0b74680a2ed';head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();ancestor=subprocess.run(['git','merge-base','--is-ancestor',known,head],cwd=ROOT).returncode==0
 assert ancestor,'UNKNOWN_AUTHORITY_LINEAGE'
 protected={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'Scripts/routeA/diagnostic_transient').rglob('*')) if p.is_file()}
 protected.update(EXPECTED)
 for pat in ['routeA_diagnostic_transient_contract_v1.*','routeA_execution_contract_v1.7.*']:
  for p in (ROOT/'docs').glob(pat):protected[str(p.relative_to(ROOT))]=sha(p)
 sv=os.statvfs(ROOT);free=sv.f_bavail*sv.f_frsize
 authority={'client_timestamp':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds'),'known_HEAD':known,'actual_HEAD':head,'known_HEAD_is_ancestor':ancestor,'HEAD_difference_explained':'Subsequent visualization commit; required diagnostic/formal contract hashes unchanged.','contract_hashes':EXPECTED,'protected_code_and_contract_sha256':protected,'start_git_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),'filesystem':{'block_size':sv.f_frsize,'total_bytes':sv.f_blocks*sv.f_frsize,'free_user_bytes':free,'free_all_bytes':sv.f_bfree*sv.f_frsize,'total_inodes':sv.f_files,'free_inodes':sv.f_favail,'df_h':subprocess.check_output(['df','-h',str(ROOT)],text=True),'df_B1':subprocess.check_output(['df','-B1',str(ROOT)],text=True),'df_i':subprocess.check_output(['df','-i',str(ROOT)],text=True)},'hardware_lscpu':json.loads(subprocess.check_output(['lscpu','-J'],text=True)),'affinity_logical_cpus':len(os.sched_getaffinity(0)),'proc_meminfo':Path('/proc/meminfo').read_text(),'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,'solver_executed':False}
 write(OUT/'authority_and_host.json',authority)
 legacy=runpy.run_path(str(ROOT/'Scripts/routeA/diagnostic_transient/v1_2/resource_estimator.py'))['projected_numeric_bytes']
 rawcat=collections.Counter();corr=collections.Counter();bytes_actual=collections.Counter();contributors=collections.defaultdict(set);stages={};rows=[];duplicates=[];payloads=[];physical=[]
 for p in sorted(STREAM.glob('[0-9]*.json')):
  r=json.loads(p.read_text());m=r['metadata'];s=m['stage'];payloads.append((p,r))
  if s in SKIP:continue
  physical.append(r);entry=stages.setdefault(s,{'records':0,'actual_bytes':0,'legacy_numeric_bytes':0,'corrected_numeric_bytes':0});entry['records']+=1;entry['actual_bytes']+=p.stat().st_size;entry['legacy_numeric_bytes']+=legacy(r);entry['corrected_numeric_bytes']+=projected(r)
  rows.append({'sequence':r['sequence'],'stage':s,'outer':m['outer'],'pressure':m['pressure'],'actual_json_bytes':p.stat().st_size,'legacy_numeric_projection_bytes':legacy(r),'corrected_numeric_projection_bytes':projected(r)})
  for cat,v,path in parts(r):rawcat[cat]+=legacy(v,path);corr[cat]+=projected(v,path);bytes_actual[cat]+=len(json.dumps(v,separators=(',',':')).encode());contributors[cat].add(r['sequence'])
  pl=r['payload'];ns=pl['native_state_epoch'];candidate=pl.get('state')
  if candidate is None and 'state_epoch' in pl:candidate={k:v for k,v in pl.items() if k not in {'native_state_epoch','thermal_context'}}
  if candidate==ns:duplicates.append({'sequence':r['sequence'],'legacy_bytes':legacy(ns),'corrected_bytes':projected(ns)})
 assert len(physical)==1141 and sum(rawcat.values())==original['diagnostic_numeric_payload_Float64_equivalent_bytes_per_step']
 rawcat['B']=original['full_field_numeric_bytes_per_step'];corr['B']=rawcat['B']
 nsteps=sum(v['planning_steps'] for k,v in original['series_planning_envelope'].items() if k in {'0.5','0.25'})
 assert nsteps==600183 and sum(rawcat.values())*nsteps==5825629244755728
 breakdown=[]
 for k,label in CATS.items():
  count=1 if k=='B' else len(contributors[k]);per=rawcat[k]
  breakdown.append({'category':k,'name':label,'legacy_numeric_bytes_per_record_mean':per/count if count else 0,'records_per_step':count,'legacy_numeric_bytes_per_step':per,'primary_steps':nsteps,'legacy_primary_bytes':per*nsteps,'legacy_fraction':per/sum(rawcat.values()),'corrected_numeric_bytes_per_step':corr[k],'corrected_primary_bytes':corr[k]*nsteps,'reencoded_synthetic_fragment_json_bytes':bytes_actual[k],'legacy_exclusions':'A production scalar series,J logs,I string hashes/manifests are absent from numerical baseline; metadata strings excluded; corrected arrays still not actual JSON.' if k in {'A','H','I','J'} else ''})
 ranked=sorted(breakdown,key=lambda x:x['legacy_primary_bytes'],reverse=True)
 complete=[]
 for t in ['3000','6000','9000']:
  p=ROOT/'cases/routeA/A-Ra1e6-fine'/t;files=[q for q in p.rglob('*') if q.is_file()];entries=[{'path':str(q.relative_to(ROOT)),'bytes':q.stat().st_size,'sha256':sha(q)} for q in files]
  du=int(subprocess.check_output(['du','-sb',str(p)],text=True).split()[0]);essential={'U','T','p','p_rgh','rho','phi'}
  complete.append({'time_directory':str(p.relative_to(ROOT)),'iteration_not_physical_transient_time':int(t),'du_sb_bytes':du,'file_content_bytes':sum(q['bytes'] for q in entries),'base_U_T_p_p_rgh_rho_phi_bytes':sum(q['bytes'] for q in entries if Path(q['path']).name in essential),'files':entries,'format':'actual existing steady ASCII writePrecision16, not future binary transient measurement','complete_directory_includes':'base fields plus postProcess div(U),div(phi),wallHeatFlux'})
 logs=[]
 for p in sorted((ROOT/'cases/routeA/A-Ra1e6-fine').glob('log.foamRun.segment_*')):
  s=p.read_text();ts=re.findall(r'^Time = ([0-9.e+-]+)',s,re.M);cl=re.findall(r'ExecutionTime = ([0-9.e+-]+) s  ClockTime = ([0-9.e+-]+) s',s)
  logs.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'iterations':len(ts),'first_iteration':float(ts[0]),'last_iteration':float(ts[-1]),'ExecutionTime_s':float(cl[-1][0]),'ClockTime_s':float(cl[-1][1]),'ClockTime_s_per_SIMPLE_iteration':float(cl[-1][1])/len(ts),'bytes_per_iteration':p.stat().st_size/len(ts),'classification':'ROUGH_PLANNING_SCALE_ONLY'})
 hardware=authority['hardware_lscpu'];mem={line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in authority['proc_meminfo'].splitlines() if 'kB' in line}
 scenarios=[]
 for title,star in [('B_EARLIEST_ALLOWED_ARRIVAL',.5),('C_INTERMEDIATE_SCENARIO',1.),('A_MAX_DURATION_SCENARIO',2.)]:
  series=[]
  for co in ['0.5','0.25','0.125']:
   h=contract['courant_control']['scales']['prospective_h_by_Co_s'][co];steps=math.ceil(star*710/h)
   solves={'U_vector_calls':24*steps,'U_scalar_component_calls_2D':48*steps,'e_calls':24*steps,'p_calls':48*steps,'rho_diagonal_calls':49*steps,'all_native_fv_solve_calls':145*steps,'scalar_component_total_2D':169*steps}
   series.append({'Co':co,'h_s':h,'planning_steps':steps,'solve_counts':solves,'baseline_storage_bytes':steps*sum(rawcat.values()),'conditional_series':co=='0.125'})
  steps=sum(v['planning_steps'] for v in series if not v['conditional_series']);cpu=[]
  for cost in [.1,1.,10.]:cpu.append({'assumed_seconds_per_complete_physical_step':cost,'primary_seconds':steps*cost,'primary_days':steps*cost/86400,'classification':'PLANNING_SENSITIVITY_NOT_MEASURED_RUNTIME'})
  steady=[{'reference_SIMPLE_s':v['ClockTime_s_per_SIMPLE_iteration'],'primary_days_at_24x_steady_scale':steps*24*v['ClockTime_s_per_SIMPLE_iteration']/86400} for v in logs]
  scenarios.append({'scenario':title,'t_star':star,'physical_time_s':star*710,'series':series,'primary_planning_steps':steps,'runtime_sensitivity':cpu,'steady_24x_scale_only':steady,'arrival_prediction':False})
 on=verify['native_driver_runs']['observed_1']['elapsed_s'];off=verify['native_driver_runs']['observer_off']['elapsed_s'];peak=max(rows,key=lambda x:x['corrected_numeric_projection_bytes'])
 subset=[r for r in physical if r['metadata']['outer']==24 or r['metadata']['outer']==1 and r['metadata']['pressure']==0 and (r['metadata']['stage'] in {'before_correctDensity','mass_unrelaxed_assembly','mass_after_solve','after_correctDensity'} or r['metadata']['stage']=='term_capture' and r['payload']['term'] in {'D_B_rho','div_phi','mass_models'})]
 numeric_full=sum(projected(r) for r in physical);numeric_bundle=sum(projected(r) for r in subset)
 pack_caps={'full_audit_step_bytes':12*2**30,'selected_outer_bundle_bytes':2**30,'field_snapshot_bytes':16*2**20,'fixed_provenance_bytes':2**30,'rationale':'Uncompressed lossless packed-array budget caps, not measured production sizes. Full-step/bundle caps exceed corrected numeric projection; field cap exceeds largest existing complete ASCII directory. Explicit future quota STOP if exceeded; no silent retention reduction.'}
 policies=[]
 for scenario in scenarios:
  star=scenario['t_star'];steps=scenario['primary_planning_steps']
  for policy in ['P0_CURRENT_MAXIMAL','P1_CONSERVATIVE_REDUCED','P2_AGGRESSIVE_DEFENSIBLE']:
   if policy=='P0_CURRENT_MAXIMAL':
    amount=steps*sum(rawcat.values());policies.append({'policy':policy,'scenario':scenario['scenario'],'t_star':star,'primary_bytes':amount,'fraction_of_free':amount/free,'field_snapshots':steps,'raw_matrix_replay':'all1141physical-stage records, all matrices at all steps','raw_audit_steps':steps,'physical_stage_records':steps*1141,'format':'historical Float64-equivalent numeric projection only; actual JSON/hash/log overhead excluded','feasible_as_is':False});continue
   if policy=='P1_CONSERVATIVE_REDUCED':
    periodic_full=sum(x<=star for x in [.5,1.,1.5,1.99]);nfull_per=3+periodic_full
    selected_per=math.floor(star/.05+1e-9)+16 # final/anomaly reserve included
    fields_per=51+math.floor((star-.05)/.005+1e-9)+64
    step_bytes={'A_primary':8192,'C_outer':24*1024,'D_pressure':48*512,'H_ledger_commit':4096,'I_manifest':512,'J_log':65536}
   else:
    nfull_per=1+sum(x<=star for x in [.5,1.99]);selected_per=math.floor(star/.1+1e-9)+8
    fields_per=21+math.floor((star-.02)/.02+1e-9)+32
    step_bytes={'A_primary':4096,'C_outer':24*512,'D_pressure':48*256,'H_ledger_commit':2048,'I_manifest':256,'J_log':65536}
   field_n=2*fields_per;raw_n=2*nfull_per;selected_n=2*selected_per
   parts2={'every_step_scalar_norm_ledger_log_bytes':steps*sum(step_bytes.values()),'full_step_audit_bytes':raw_n*pack_caps['full_audit_step_bytes'],'selected_outer_bundle_bytes':selected_n*pack_caps['selected_outer_bundle_bytes'],'field_snapshot_bytes':field_n*pack_caps['field_snapshot_bytes'],'fixed_provenance_bytes':pack_caps['fixed_provenance_bytes']};amount=sum(parts2.values())
   policies.append({'policy':policy,'scenario':scenario['scenario'],'t_star':star,'primary_bytes':amount,'fraction_of_free':amount/free,'parts':parts2,'step_byte_budget':step_bytes,'field_snapshots':field_n,'full_raw_audit_steps':raw_n,'selected_raw_bundles':selected_n,'retained_raw_record_slots':raw_n*1141+selected_n*len(subset),'matrix_replay_coverage_full_steps_fraction':raw_n/steps,'physical_stage_online_checks':'all1141 events per step; persisted outer/pressure/step receipts with folded stage commitments; selected full payloads','format':'proposed lossless packed arrays + metadata; no compression assumed','condition':'Not current exporter; needs v1.3 namespace/implementation/replay/online checks requalification. All caps planning, not actual target-case measurements.','feasible_as_is':False,'within_proposed_50_percent_capacity_budget':amount<=.5*free})
 compression=[compression_sample('actual_complete_9000_directory',[ROOT/x['path'] for x in complete[-1]['files']]),compression_sample('existing_U04_complete_synthetic_stream',[p for p,r in payloads]+[STREAM/'manifest.jsonl',STREAM/'complete.json'])]
 memory={'measured_host_total_bytes':mem['MemTotal'],'measured_host_available_bytes':mem['MemAvailable'],'synthetic_peak_RSS_KiB':verify['peak_children_rss_KiB'],'synthetic_memory_not_scaled_as_whole_process':True,'largest_corrected_record_numeric_bytes':peak['corrected_numeric_projection_bytes'],'largest_record_stage':peak['stage'],'full_step_numeric_bytes':numeric_full,'selected_bundle_numeric_bytes':numeric_bundle,'ring_1_2_4_full_step_packed_bytes':{str(k):k*numeric_full for k in [1,2,4]},'full_step_JSON_value_object_estimate_16x_32x_bytes':[16*numeric_full,32*numeric_full],'JSON_factor_basis':'DiagnosticJson Json contains enum/double/bool/string/vector/map even for every scalar; typical128-byte object versus8-byte double and vector capacity slack. ABI estimate, not measured target RSS.','candidate_ring':'One final-outer+initial-density bundle <=1GiB, plus16 recent stage payloads at the measured schema peak; packed buffers, not JSON trees. No promise of complete previous-step replay for anomalies.','candidate_bundle_plus_16_stages_bytes':pack_caps['selected_outer_bundle_bytes']+16*peak['corrected_numeric_projection_bytes'],'candidate_total_RSS_budget_bytes':8*2**30,'current_target_case_peak_RSS':'UNMEASURED','parallel_support':'NOT_VALIDATED; observer rejects coupled patches, global state serial, no per-rank protocol'}
 total=sum(rawcat.values());pareto={str(k):sum(x['legacy_fraction'] for x in ranked[:k]) for k in [1,3,5]}
 result={'classification':'PLANNING_ESTIMATE_ONLY','authority':authority,'literal_original_projection':original,'original_projection_reconstructed_bytes':total*nsteps,'legacy_per_step_bytes':total,'corrected_per_step_numeric_bytes':sum(corr.values()),'correction_explanation':'Old estimator did not scale thermal_context.Cv cell arrays or geometry.linear_weights internal-face arrays; audit corrects these shapes without editing v1.2/source/evidence. Strings/logs/JSON overhead still separate, not measured production size.','corrected_primary_numeric_equivalent_bytes':sum(corr.values())*nsteps,'breakdown':breakdown,'ranked_contributors':ranked,'pareto':pareto,'exact_duplicate_state_blocks':{'records':len(duplicates),'legacy_bytes_per_step':sum(x['legacy_bytes'] for x in duplicates),'corrected_bytes_per_step':sum(x['corrected_bytes'] for x in duplicates),'scope':'Exact repeated payload.state or root meshState versus native_state_epoch in existing synthetic packets. Shape scaling only; no speculative cross-step equality.'},'actual_fields':complete,'steady_log_evidence':logs,'step_solve_scenarios':scenarios,'synthetic_IO':{'on_s':on,'off_s':off,'ratio':on/off,'records':1152,'physical_records':1141,'raw_bytes':verify['output_bytes'],'mean_bytes_per_record':verify['output_bytes']/1152,'fsync_per_record':3,'fsync_per_physical_step':3*1141,'physical_record_publications_primary_max_duration':1141*nsteps,'record_fsync_calls_primary_max_duration':3*1141*nsteps,'timing_extrapolation_to_production':False,'stages':stages,'per_outer1_24_actual_bytes':{str(o):sum(q.stat().st_size for q,r in payloads if r['metadata']['outer']==o and r['metadata']['stage'] not in SKIP) for o in range(1,25)}},'memory':memory,'selected_bundle_records':len(subset),'packed_caps':pack_caps,'policy_scenarios':policies,'compression_samples':compression,'budget_candidates':{'50_percent_free_bytes':.5*free,'70_percent_free_bytes':.7*free,'proposal_not_adopted':'50% candidate ceiling leaves ~0.40TB for OS/other studies/temp/anomalies; selected conservative packed policy only just meets it, so uncertainties remain material.70% is comparison-only and not adopted.'},'source_script_sha256':sha(__file__),'no_solver_execution':True,'no_contract_modification':True}
 write(OUT/'resource_accounting.json',result)
 for name,data in [('stage_record_accounting.csv',rows),('component_storage_breakdown.csv',breakdown)]:
  with (OUT/name).open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 print(json.dumps({'literal_bytes':total*nsteps,'corrected_numeric_bytes':sum(corr.values())*nsteps,'ranked':[(x['category'],x['legacy_fraction']) for x in ranked[:5]],'pareto':pareto,'selected_bundle_records':len(subset),'full_numeric_GB':numeric_full/1e9,'bundle_numeric_GB':numeric_bundle/1e9,'policies':[(v['policy'],v['scenario'],v['primary_bytes']/1e9,v['fraction_of_free']) for v in policies],'compression':compression},indent=2))
if __name__=='__main__':main()
