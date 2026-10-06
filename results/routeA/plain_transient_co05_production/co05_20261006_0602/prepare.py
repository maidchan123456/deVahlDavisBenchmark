#!/usr/bin/env python3
"""Non-CFD preparation only: clone cold input, parse dictionaries, mesh/decompose/probe."""
import os,json,hashlib,shutil,subprocess,re,datetime,math
from pathlib import Path
import numpy as np
from mesh_geometry import geometry,labels,patch_cells
ROOT=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark');P=Path(__file__).resolve().parent;ID=P.name;CASE=ROOT/'cases/routeA/plain_transient_co05_production'/ID
LATE=ROOT/'results/routeA/transient_cfd_late_window_pilot/late_20261006_0531';HEAD='f57d60d85e36ea9928e4bc481d3cbde586496f58';REFS={'docs/routeA_diagnostic_transient_contract_v1.5.json':'06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d','docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'}
def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(folder):return {str(f.relative_to(folder)):sha(f) for f in sorted(folder.rglob('*')) if f.is_file()}
def env():
 e=os.environ.copy()
 for key in list(e):
  if key.startswith(('ROUTE_A_','OMPI_')) or key in ['LD_PRELOAD','FOAM_CONTROLDICT']:del e[key]
 e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');return e
ENV=env();commands=[]
def run(cmd,name,cwd=ROOT):
 assert not any(Path(word).name=='foamRun' for word in cmd),'foamRun absolutely prohibited in preparation'
 t=__import__('time').monotonic();r=subprocess.run(cmd,cwd=cwd,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(P/name).write_bytes(r.stdout);commands.append({'argv':cmd,'cwd':str(cwd),'returncode':r.returncode,'wall_seconds':__import__('time').monotonic()-t});assert r.returncode==0,(cmd,r.stdout[-2000:]);return r.stdout.decode()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
for f,h in REFS.items():assert sha(ROOT/f)==h
prior=json.loads((LATE/'artifact_manifest_sha256.json').read_text());assert all(sha(LATE/f)==h for f,h in prior.items())
CASE.parent.mkdir(parents=True,exist_ok=True);CASE.mkdir()
for folder in ['0','constant','system']:shutil.copytree(LATE/'case'/folder,CASE/folder)
control=CASE/'system/controlDict';s=control.read_text();s=re.sub(r'endTime\s+[^;]+;','endTime 1420;',s);s=s.replace('writeControl timeStep;','writeControl runTime;');s=re.sub(r'writeInterval\s+[^;]+;','writeInterval 5;',s);control.write_text(s)
assert 'timePrecision 12;' in s and 'writePrecision 17;' in s and 'purgeWrite 0;' in s
for folder in ['0','constant']:
 for f in (CASE/folder).rglob('*'):
  if f.is_file():assert sha(f)==sha(LATE/'case'/f.relative_to(CASE))
for name in ['fvSolution','fvSchemes','decomposeParDict']:assert sha(CASE/'system'/name)==sha(LATE/'case/system'/name)
assert sorted(f.name for f in (CASE/'0').iterdir())==['T','U','p','p_rgh']
requests=Path('/home/mirai/.codex/attachments/b4c0f0f0-de39-4e86-9b41-35539313e8a5/貼り付けたテキスト.txt')
dump(P/'preparation_authorization_receipt.json',{'authorization_class':'PLAIN_TRANSIENT_CO05_PRODUCTION_PREPARATION_ONLY','PRODUCTION_PREPARATION':'AUTHORIZED','PRODUCTION_CFD_EXECUTION':'NOT_AUTHORIZED','ACTUAL_CFD_ALLOWED':'NO','source_request':str(requests),'source_request_sha256':sha(requests),'expected_HEAD':HEAD,'authority_hashes':REFS})
# Native dictionary parser, no solver or time advance.
semantic={}
for name,entries in {'controlDict':['solver','startFrom','startTime','endTime','deltaT','maxCo','maxDeltaT','deltaTFactor','adjustTimeStep','writeControl','writeInterval','timePrecision','writePrecision','purgeWrite','functions'],'fvSolution':['PIMPLE/pRefPoint','PIMPLE/nOuterCorrectors','PIMPLE/nCorrectors','PIMPLE/nNonOrthogonalCorrectors','PIMPLE/simpleRho'],'decomposeParDict':['numberOfSubdomains','method'],'fvSchemes':['ddtSchemes/default']}.items():
 for entry in entries:semantic[name+'/'+entry]=run(['foamDictionary',str(CASE/'system'/name),'-entry',entry,'-value'],'dictionary_parse_last.txt',cwd=CASE).strip()
dump(P/'dictionary_semantics.json',semantic)
run(['checkMesh','-case',str(CASE)],'log.checkMesh',cwd=CASE)
run(['decomposePar','-case',str(CASE),'-force'],'log.decomposePar',cwd=CASE)
# Non-CFD MPI affinity probe uses exact prior MPI flags, replacing solver with Python only.
probe='import os,json; print(json.dumps({"rank":int(os.environ["OMPI_COMM_WORLD_RANK"]),"pid":os.getpid(),"affinity":sorted(os.sched_getaffinity(0))}),flush=True)'
probe_cmd=['mpirun','--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings','-np','12','/usr/bin/python3','-c',probe]
text=run(probe_cmd,'log.MPI_non_CFD_binding_probe',cwd=CASE);data=[json.loads(line) for line in text.splitlines() if line.startswith('{')];assert len(data)==12 and {r['rank'] for r in data}==set(range(12))
cpu={int(p.name[3:]):int((p/'topology/core_id').read_text()) for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*')};cores=[]
for row in data:
 c={cpu[x] for x in row['affinity']};assert len(c)==1;row['physical_core']=c.pop();cores.append(row['physical_core'])
assert len(set(cores))==12;dump(P/'MPI_binding_verification.json',{'status':'PASS','non_CFD_probe':True,'physical_cores_distinct':True,'ranks':data,'command':probe_cmd})
run(['mpirun','--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings','-np','12','checkMesh','-case',str(CASE),'-parallel'],'log.checkMesh.parallel',cwd=CASE)
# Native mesh mapping and processor interface signs, all without solving.
g=geometry(CASE/'constant/polyMesh');assert len(g['centres'])==25600;assert np.allclose(g['volumes'],.1*.1*.001/25600,rtol=1e-12,atol=0)
point=np.array([.0496875,.0496875,.0005]);where=np.where(np.all((g['lo']<point-1e-13)&(g['hi']>point+1e-13),axis=1))[0];assert where.tolist()==[12719]
rank_of=np.full(25600,-1,dtype=int);reference=[];face_counts=np.zeros(g['face_count'],dtype=int);face_signed=np.zeros(g['face_count'],dtype=int);counts=[];decomp_hashes={}
for rank in range(12):
 mesh=CASE/f'processor{rank}/constant/polyMesh';ids=labels(mesh/'cellProcAddressing');local=geometry(mesh);assert len(ids)==len(local['centres']);assert np.all(rank_of[ids]==-1);rank_of[ids]=rank
 assert np.max(np.abs(local['centres']-g['centres'][ids]))<1e-13;counts.append(len(ids))
 fids=labels(mesh/'faceProcAddressing');np.add.at(face_counts,np.abs(fids)-1,1);np.add.at(face_signed,np.abs(fids)-1,np.sign(fids))
 mask=np.where(np.all((local['lo']<point-1e-13)&(local['hi']>point+1e-13),axis=1))[0]
 for cell in mask:reference.append({'rank':rank,'local_cell':int(cell),'global_cell':int(ids[cell]),'centre_m':local['centres'][cell].tolist(),'strictly_inside_cell_bounds':True,'distance_from_each_cell_plane_m':np.minimum(point-local['lo'][cell],local['hi'][cell]-point).tolist()})
 decomp_hashes.update({str(f.relative_to(CASE)):sha(f) for f in mesh.iterdir() if f.is_file()})
assert len(reference)==1 and reference[0]['global_cell']==12719 and np.all(rank_of>=0)
expected=np.ones(g['face_count'],dtype=int);ninternal=len(g['neighbour']);expected[:ninternal]+=(rank_of[g['owner'][:ninternal]]!=rank_of[g['neighbour']]);assert np.array_equal(face_counts,expected);assert np.all(face_signed[face_counts==2]==0)
dump(P/'processor_topology_verification.json',{'status':'PASS','cells_per_rank':counts,'total_cells':sum(counts),'all_global_cells_covered_once':True,'processor_geometry_maps_to_same_global_cells':True,'duplicated_interface_faces':int(np.sum(face_counts==2)),'processor_face_pair_signs_opposed':True,'pRefPoint_mapping':reference})
dump(P/'decomposition_output_manifest.json',decomp_hashes)
np.savez(P/'mesh_geometry.npz',centres=g['centres'],volumes=g['volumes'],hot_cells=patch_cells(CASE/'constant/polyMesh','hotWall',g['owner']),cold_cells=patch_cells(CASE/'constant/polyMesh','coldWall',g['owner']))
# Checkpoint and raw-log capacity evidence from actual accepted late pilot.
measure=[]
for t in (LATE/'case/processor0').iterdir():
 if not (t/'uniform/time').is_file():continue
 files=[f for rank in range(12) for f in (LATE/f'case/processor{rank}'/t.name).rglob('*') if f.is_file()];measure.append({'time_name':t.name,'logical_bytes':sum(f.stat().st_size for f in files),'allocated_bytes':sum(f.stat().st_blocks*512 for f in files),'files':len(files)})
maximum=max(r['allocated_bytes'] for r in measure);logical=max(r['logical_bytes'] for r in measure);nf=max(r['files'] for r in measure);log_per_step=(LATE/'log.foamRun').stat().st_size/598;startup=[2,5,10,20,30,39,60,100,250,500]
options=[]
for interval in [2,5,10]:
 regular=1420//interval;snapshots=regular+len(startup);options.append({'interval_seconds':interval,'regular_snapshots':regular,'extra_startup_snapshot_upper_bound':len(startup),'expected_snapshots_upper_bound':snapshots,'field_logical_bytes_estimate':snapshots*logical,'field_allocated_bytes_estimate':snapshots*maximum,'expected_field_files_upper_bound':snapshots*nf,'transient_resolution':'2s later samples; startup checkpoints retained' if interval==2 else '5s approach-to-steady history plus dense startup checkpoints' if interval==5 else '10s coarse later evolution; startup checkpoints retained'})
chosen=options[1];log_estimate=math.ceil(log_per_step*200000);output=chosen['field_allocated_bytes_estimate']+log_estimate;reserve=max(32*2**30,math.ceil(output*3));disk=shutil.disk_usage(CASE)
assert disk.free>reserve
dump(P/'storage_and_cadence_decision.json',{'actual_checkpoint_measurements':measure,'checkpoint_peak_allocated_bytes':maximum,'checkpoint_peak_logical_bytes':logical,'checkpoint_files_per_global_snapshot':nf,'cadence_comparison':options,'selected_interval_seconds':5,'selected':chosen,'startup_write_steps':startup,'startup_reason':'late pilot Umax changes from0.0225 to0.0397m/s between1.49 and2.93s;5s-only output misses early dynamics. Add10 native signal-requested startup snapshots without changing dt. Later5s spacing supports approach/profile evolution but is not a guarantee of resolving all oscillations.','selected_reason':'default5s retained with explicitly resolved startup sampling; full fields around2.75GiB plus native log around5.0GiB;2s is2.45times more state files,10s halves later resolution; ample capacity and no need for format conversion or purge','representation':'ASCII,no compression,writePrecision17','purgeWrite':0,'log_bytes_per_completed_step_measured':log_per_step,'expected_log_bytes_at200000_steps':log_estimate,'expected_total_output_allocated_bytes_including_log':output,'expected_fullfield_output_files':chosen['expected_field_files_upper_bound'],'prelaunch_required_free_bytes':reserve,'runtime_free_disk_low_watermark_bytes':8*2**30,'free_bytes_at_preparation':disk.free,'total_disk_bytes':disk.total,'RAM_MemTotal_and_MemAvailable':[line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))],'RSS_note':'pilot sampled summed worker RSS~1.63GiB; includes shared pages, not unique-memory use','storage_scope':'field snapshots and full stdout/stderr log; case/decomposition and small postprocess tables extra;32GiB reserve covers these and margin;200k steps is a capacity estimate, never a timestep stop'})
# Pin only explicitly relevant primary evidence and source; no repository-wide audit.
guard={str(LATE.relative_to(ROOT)/name):sha(LATE/name) for name in ['artifact_manifest_sha256.json','RouteA_plain_transient_late_window_performance_pilot.md','RouteA_plain_transient_late_window_performance_pilot.json','run_command.json','production_preparation_handoff_NOT_EXECUTED.json']};guard.update(REFS)
for f in (LATE/'case/0').iterdir():guard[str(f.relative_to(ROOT))]=sha(f)
for name in ['fvSolution','fvSchemes']:guard[str((LATE/'case/system'/name).relative_to(ROOT))]=sha(LATE/'case/system'/name)
for name in ['metrics.json','centreline_4097.csv']:f=ROOT/'results/routeA/cases/A-Ra1e6-fine/segments/end_9000'/name;guard[str(f.relative_to(ROOT))]=sha(f)
dump(P/'source_reference_guard.json',guard)
binaries={}
for name in ['foamRun','decomposePar','checkMesh','foamDictionary','mpirun']:
 path=Path(shutil.which(name)).resolve();binaries[name]={'path':str(path),'sha256':sha(path)}
lib=Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib/libfluid.so');binaries['libfluid.so']={'path':str(lib),'sha256':sha(lib)}
sources={str(path):sha(path) for path in [Path('/opt/openfoam13/src/OpenFOAM/db/Time/Time.C'),Path('/opt/openfoam13/src/OpenFOAM/db/Time/TimeIO.C'),Path('/opt/openfoam13/applications/solvers/foamRun/foamRun.C'),Path('/opt/openfoam13/applications/solvers/foamRun/setDeltaT.C'),Path('/opt/openfoam13/src/OSspecific/POSIX/signals/sigWriteNow.C'),Path('/opt/openfoam13/src/OSspecific/POSIX/signals/sigStopAtWriteNow.C')]}
manifest_case=manifest(CASE);dump(P/'production_input_manifest.json',{'preparation_id':ID,'case':str(CASE),'expected_HEAD':HEAD,'case_files_sha256':manifest_case,'source_reference_guard_sha256':sha(P/'source_reference_guard.json'),'binary_provenance':binaries,'installed_source_sha256':sources,'OpenFOAM_build':'13-441953dfbb42','MPI_version':run(['mpirun','--version'],'MPI_version.txt').strip(),'cold_start_only':True,'production_execution_authorized':'NO'})
cmd=json.loads((LATE/'run_command.json').read_text())['argv'];cmd[cmd.index('-case')+1]=str(CASE)
plan={'preparation_id':ID,'case':str(CASE),'prep_results':str(P),'runtime_output':str(P/'execution'),'expected_HEAD':HEAD,'input_manifest_file':str(P/'production_input_manifest.json'),'input_manifest_sha256':sha(P/'production_input_manifest.json'),'command_argv':cmd,'command_shell':__import__('shlex').join(cmd),'cwd':str(CASE),'environment_overrides':{'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'},'ranks':12,'endTime_s':1420,'target_tstar':2,'initial_deltaT_s':2.3111979166666666e-5,'maxDeltaT_s':.027734375,'maxCo':.5,'deltaTFactor':1.2,'production_start':'CONTINUOUS_COLD_START','strict_restart_relied_upon':False,'interruption_status':'INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN','automatic_retry':False,'automatic_cold_rerun':False,'writeControl':'runTime','writeInterval_seconds':5,'startup_write_steps':startup,'timePrecision':12,'writePrecision':17,'functions_disabled':True,'heavy_diagnostics':False,'primary_stop':'native endTime1420 predicate, no timestep-count or online steady stop','planned_wall_limit_seconds':86400,'disk_required_free_bytes':reserve,'disk_low_watermark_bytes':8*2**30,'expected_regular_snapshots':284,'expected_full_field_snapshots_upper_bound':chosen['expected_snapshots_upper_bound'],'expected_steps_planning_range':[180000,200000],'expected_runtime_hours':6.112102039491276,'runtime_classification':'PROJECTED_FROM_LATE_WINDOW','final_write_method':'NATIVE_RUN_TIME_BIN_ENDTIME_MULTIPLE: runTime1420 is bin284 at5s; same t+0.5dt boundary as native termination. No writeAtEnd option or normal-termination signal needed; final actual time recorded, not forced exact1420.','PRODUCTION_EXECUTION_AUTHORIZED':'NO','updated_HEAD_policy':'Any HEAD change after preparation fails launch until an explicitly reviewed preparation refresh pins the new revision; no automatic override.'}
dump(P/'production_execution_plan.json',plan)
dump(P/'production_authorization_draft.json',{'authorization_class':'ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION','AUTHORIZED':'NO','preparation_id':ID,'expected_HEAD':HEAD,'execution_plan_sha256':sha(P/'production_execution_plan.json'),'input_manifest_sha256':sha(P/'production_input_manifest.json'),'MPI_RANKS':12,'endTime_s':1420,'source_user_authorization_reference':None,'note':'Preparation-only user instruction; a later explicit user production instruction is required. Do not change AUTHORIZED during preparation.'})
dump(P/'preparation_commands.json',commands)
run(['git','status','--short'],'git_status_after_case_preparation.txt');run(['git','diff','--stat'],'git_diff_stat_after_case_preparation.txt')
print(json.dumps({'case':str(CASE),'regular_snapshots':284,'snapshots_upper_bound':chosen['expected_snapshots_upper_bound'],'field_allocated_bytes':chosen['field_allocated_bytes_estimate'],'total_output_including_log_bytes':output,'expected_field_files':chosen['expected_field_files_upper_bound'],'disk_reserve_bytes':reserve,'pRef_mapping':reference,'all_preparation_is_non_CFD':True},indent=2))
