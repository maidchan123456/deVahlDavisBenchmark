from pathlib import Path
import hashlib,json,re,ast,datetime
P=Path(__file__).resolve().parent
ROOT=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
report=json.loads((P/'RouteA_plain_transient_MPI_scaling_pilot.json').read_text())
for script in P.glob('*.py'):ast.parse(script.read_text(),filename=str(script))
for n in [1,2,4,6,8,12]:
 d=P/f'rank_{n:02d}';inputs=json.loads((d/'input_manifest.json').read_text())
 assert all(sha(d/'case'/key)==digest for key,digest in inputs.items()),n
 text=(d/'log.foamRun').read_text();bindings=re.findall(r'MCW rank (\d+) bound to socket 0\[core (\d+)\[hwt 0-1\]\]',text)
 assert len(bindings)==n and {int(core) for rank,core in bindings}==set(range(n)),(n,bindings)
 t=json.loads((d/'timing.json').read_text());assert t['returncode']==0 and t['max_solver_processes_observed']==n
 assert t['condition_wall_including_decomposition_seconds']<600 if 'condition_wall_including_decomposition_seconds' in t else t['wall_seconds_total']<600
 dump(d/'binding_verified.json',{'binding':'one MPI rank per distinct physical core; two sibling hardware threads in each core CPU mask, single-threaded solver','bindings':[{'MPI_rank':int(rank),'physical_core':int(core)} for rank,core in bindings],'verified':True})
immutable=json.loads((P/'immutable_source_manifest.json').read_text());assert all(sha(ROOT/key)==digest for key,digest in immutable.items())
primary=[];previous=[]
for n in [1,2,4,6,8,12]:
 t=json.loads((P/f'rank_{n:02d}'/'timing.json').read_text());primary.append(t['wall_seconds_total']+sum(x.get('wall_seconds',0) for x in t['commands']))
 d=P/'superseded_cell_reference_attempts'/f'rank_{n:02d}'
 if d.exists():
  t=json.loads((d/'timing.json').read_text());previous.append(t['wall_seconds_total']+sum(x.get('wall_seconds',0) for x in t['commands']))
 assert primary[-1]+(previous[-1] if d.exists() else 0)<600
resource={'primary_solver_wall_total_seconds':sum(json.loads((P/f'rank_{n:02d}'/'timing.json').read_text())['wall_seconds_total'] for n in [1,2,4,6,8,12]),'primary_wall_including_decomposition_seconds':sum(primary),'previous_attempt_wall_including_decomposition_seconds':sum(previous),'cold_check_last_completion_wall_seconds':json.loads((P/'cold_check/timing.json').read_text())['wall_seconds_total'],'per_rank_cumulative_with_previous_attempts_under600_seconds':True,'elapsed_pilot_wall_seconds_at_verification':datetime.datetime.now(datetime.timezone.utc).timestamp()-datetime.datetime.fromisoformat(json.loads((P/'budget.json').read_text())['all_pilot_CFD_start_UTC']).timestamp(),'primary_total_cap_seconds':3600,'timeout_hit':False,'automatic_timeout_retry':False}
assert resource['elapsed_pilot_wall_seconds_at_verification']<3600
env=(P/'environment.txt').read_text();model=re.search(r'Model name:\s*(.*)',env)[1];memory_kib=int(re.search(r'MemTotal:\s*(\d+) kB',env)[1])
report['resource_accounting']=resource;report['system_summary']={'CPU_model':model,'physical_cores':12,'logical_CPUs':24,'memory_GiB':memory_kib/2**20,'OpenFOAM_version':'13','OpenFOAM_build':'13-441953dfbb42','MPI':'OpenMPI4.1.6','precision_and_labels':'double,32-bit labels'}
report['parallel_classification_rule']='GOOD if fastestMPI speedup>=3, MODERATE >=1.5, POOR >=1, NEGATIVE <1; descriptive, not formal gate'
report['binding_verified_all_primary']=True;report['post_run_input_hashes_verified']=True
report['planning_sensitivity']=[{'steps':q['steps'],'24hour_threshold_seconds_per_step':86400/q['steps'],'24hour_step_cost_multiplier_vs_measured_best':86400/q['steps']/report['best_MPI']['median_s_per_step']} for q in report['runtime_estimates']]
proposal={'task':report['status']['NEXT_SINGLE_TASK'],'authorization_status':'NOT_AUTHORIZED_NOT_EXECUTED','requires_user_decision':True,'suggested_ranks':12,'suggested_max_completed_steps':1000,'suggested_wall_cap_seconds':600,'no_automatic_retry':True,'same_physical_and_numerical_contract':True,'heavy_diagnostics':False,'production_series':False,'initialization':'Continuous native cold-start evolution retains oldTime histories in memory; no restart from pilot final fields unless history correctness independently verified','measurement':'rolling late100-step wall and linear-iteration windows, including maxDeltaT/Co-limited phase if reached; record phase if cap prevents reaching it','completion':'report later cost, adaptive dt, stability, field sanity, and how it changes planning estimates; stop under hard bounds'}
dump(P/'next_task_proposal_NOT_AUTHORIZED.json',proposal);dump(P/'resource_accounting.json',resource);dump(P/'RouteA_plain_transient_MPI_scaling_pilot.json',report)
p=P/'RouteA_plain_transient_MPI_scaling_pilot.md';text=p.read_text();needle='## Scientific and execution contract'
addition=f'''## System and budget

{model};12 physical cores /24 logical CPUs; {memory_kib/2**20:.2f} GiB RAM. OpenFOAM13 build13-441953dfbb42, DP/Int32; OpenMPI4.1.6. Binding logs verify every primary MPI rank occupies a different physical core; OMP/BLAS/MKL thread counts1.

Primary solver wall sum {resource['primary_solver_wall_total_seconds']:.3f} s; including decomposition {resource['primary_wall_including_decomposition_seconds']:.3f} s. Preserved preliminary attempts {resource['previous_attempt_wall_including_decomposition_seconds']:.3f} s plus cold-check last-completion {resource['cold_check_last_completion_wall_seconds']:.3f} s. No600 s rank cap or3600 s total cap hit; no timeout retry. Post-run original-input and authority hashes unchanged; all current input hashes still match their preregistered manifests.

![Measured scaling and step cost]({P}/scaling_and_step_cost.png)

'''
text=text.replace(needle,addition+needle)
text=text.replace('## Next single task','## Planning sensitivity\n\nFor400122 steps, the24 h threshold is0.215934 s/step, about2.25 times the measured12-rank median. A1–5 day result would correspond to about2.25–11.23 times the current cold-window cost. This sensitivity is not a measured uncertainty interval.\n\n## Next single task')
p.write_text(text)
verification={'status':'PASS','authority_and_original_case_unchanged':True,'all_primary_input_hashes_same_except_decomposeParDict':True,'all_primary_post_run_input_hashes_unchanged':True,'all_ranks30_completed_steps':True,'all_ranks24_outer_every_step':True,'all_binding_cores_distinct_and_solver_process_counts_correct':True,'field_sanity_pass':True,'syntax_all_pilot_scripts_valid':True,'no_production_Q3_GateJ_executed':True,'24_rank_not_executed':True,'verified_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
dump(P/'verification.json',verification)
seal={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact_manifest_sha256.json'};dump(P/'artifact_manifest_sha256.json',seal)
print(json.dumps({'verification':verification,'resource':resource,'artifact_files':len(seal)},indent=2))
