#!/usr/bin/env python3
"""Plain native12-rank CFD; native signals control output/stop, external600s watchdog."""
import os,sys,json,re,hashlib,shutil,subprocess,time,signal,selectors,datetime,threading
from pathlib import Path
ROOT=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark');P=Path(__file__).resolve().parent
SOURCE=ROOT/'results/routeA/transient_cfd_scaling_pilot/plain_20261006_0710';CASE=P/'case'
REPAIR=json.loads((P/'logging_repair_and_cumulative_budget.json').read_text()) if (P/'logging_repair_and_cumulative_budget.json').exists() else None
STEP_CAP=REPAIR['new_step_cap'] if REPAIR else 1000
WALL_CAP=REPAIR['new_wall_cap_seconds'] if REPAIR else 600
REFS={'docs/routeA_diagnostic_transient_contract_v1.5.json':'06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d','docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'}
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def environment():
 e=os.environ.copy()
 for k in list(e):
  if k.startswith(('ROUTE_A_','OMPI_')) or k in ['LD_PRELOAD','FOAM_CONTROLDICT']:del e[k]
 e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 return e
ENV=environment()
def command(cmd,path,cwd=CASE,timeout=60):
 start=time.monotonic();r=subprocess.run(cmd,cwd=cwd,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);path.write_bytes(r.stdout)
 return {'argv':cmd,'cwd':str(cwd),'shell':__import__('shlex').join(cmd),'returncode':r.returncode,'wall_seconds':time.monotonic()-start}
def prepare():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='fd62fb9f5458532a7ebd684b73baf1ea9b415d7e'
 for name,h in REFS.items():assert sha(ROOT/name)==h
 prior=json.loads((SOURCE/'artifact_manifest_sha256.json').read_text());assert all(sha(SOURCE/name)==h for name,h in prior.items())
 dump(P/'source_pilot_guard.json',{'source_pilot':str(SOURCE),'artifact_manifest_sha256':sha(SOURCE/'artifact_manifest_sha256.json'),'artifacts_verified':len(prior),'read_only':True})
 checkpoint=SOURCE/'rank_12/case';source_time='0.032778746640202423';proof=[]
 for rank in range(12):
  folder=checkpoint/f'processor{rank}'/source_time
  proof.append({'rank':rank,'time':source_time,'field_hashes':manifest(folder),'missing_energy_or_K_history':[field for field in ['e','e_0','K','K_0','T_0'] if not (folder/field).is_file()]})
 dump(P/'starting_state_provenance.json',{'source_pilot':'plain_20261006_0710','source_rank_count':12,'candidate_checkpoint_time_s':float(source_time),'candidate_checkpoint_files':proof,'restart_selected':False,'restart_proof':'REJECTED_INCOMPLETE_NATIVE_HISTORY: current e and K plus their prior histories are not saved/read as restart state. Presence of U_0/rho_0/phi_0 and deltaT0 alone does not prove full backward history. Native BasicThermo creates he with NO_READ/NO_WRITE; K is constructed from current U.','native_source_references':['/opt/openfoam13/src/thermophysicalModels/basic/basicThermo/BasicThermo.C:320','/opt/openfoam13/applications/modules/isothermalFluid/isothermalFluid.C:166','/opt/openfoam13/src/OpenFOAM/fields/OldTimeField/OldTimeField.C:125'],'selected_start':'COPY_VALIDATED_COLD_INITIAL_STATE_CONTINUOUS_NATIVE_HISTORY','start_time_s':0,'no_fabricated_oldTime':True,'cold_input_source':str(SOURCE/'common_input')})
 shutil.copytree(SOURCE/'common_input',CASE);shutil.copy2(checkpoint/'system/decomposeParDict',CASE/'system/decomposeParDict')
 c=CASE/'system/controlDict';s=c.read_text();s=re.sub(r'endTime\s+[^;]+;', 'endTime 27.734375;',s);s=s.replace('writeInterval 30;','writeInterval '+str(STEP_CAP)+';');s=s.replace('timePrecision 17;','timePrecision 12;');s+='\nOptimisationSwitches\n{\n writeNowSignal 10;\n stopAtWriteNowSignal 12;\n}\n';c.write_text(s)
 assert 'pRefCell' not in (CASE/'system/fvSolution').read_text()
 assert sha(CASE/'system/fvSolution')==sha(SOURCE/'common_input/system/fvSolution')
 assert sha(CASE/'system/fvSchemes')==sha(SOURCE/'common_input/system/fvSchemes')
 physical={str(f.relative_to(CASE)):sha(f) for folder in ['0','constant'] for f in sorted((CASE/folder).rglob('*')) if f.is_file()}
 dump(P/'input_manifest.json',manifest(CASE));dump(P/'physical_input_manifest.json',physical)
 req=Path('/home/mirai/.codex/attachments/046e6d55-ec66-4f8c-82d7-103d2a2d8e3e/貼り付けたテキスト.txt')
 dump(P/'authorization_receipt.json',{'authorization_class':'PLAIN_TRANSIENT_LATE_WINDOW_BOUNDED_PERFORMANCE_PILOT','source_request':str(req),'source_request_sha256':sha(req),'CFD_ALLOWED':'YES','SHORT_TRANSIENT_ONLY':'YES','MPI_RANKS':12,'MAX_ADDITIONAL_STEPS':1000,'MAX_WALL_SECONDS':600,'PRODUCTION_ALLOWED':'NO','Q3_ALLOWED':'NO','HEAVY_DIAGNOSTICS_ALLOWED':'NO','authority_hashes':REFS,'head':'fd62fb9f5458532a7ebd684b73baf1ea9b415d7e'})
 nativefiles=['/opt/openfoam13/src/OpenFOAM/global/debug/debug.C','/opt/openfoam13/src/OSspecific/POSIX/signals/sigStopAtWriteNow.C','/opt/openfoam13/src/OSspecific/POSIX/signals/sigWriteNow.C','/opt/openfoam13/src/OpenFOAM/db/Time/Time.C','/opt/openfoam13/applications/solvers/foamRun/setDeltaT.C','/opt/openfoam13/applications/modules/isothermalFluid/isothermalFluid.C','/opt/openfoam13/src/thermophysicalModels/basic/basicThermo/BasicThermo.C']
 binaries={str(Path(shutil.which(x)).resolve()):sha(Path(shutil.which(x)).resolve()) for x in ['foamRun','decomposePar','mpirun']};binaries.update({'/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib/libfluid.so':sha(Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib/libfluid.so'))})
 dump(P/'binary_and_source_provenance.json',{'binaries':binaries,'native_sources':{x:sha(Path(x)) for x in nativefiles},'reference_point':[.0496875,.0496875,.0005],'ranks':12})
 commands=[]
 for index,cmd in enumerate([['lscpu'],['mpirun','--version'],['foamRun','-help'],['checkMesh','-case',str(CASE)],['decomposePar','-case',str(CASE),'-force']]):
  path=P/('log.decomposePar' if index==4 else 'log.checkMesh' if index==3 else f'environment_{index}.txt');r=command(cmd,path);commands.append(r);assert r['returncode']==0
 dump(P/'preparation_commands.json',commands)
 (P/'environment.txt').write_text('\n'.join((P/f'environment_{i}.txt').read_text() for i in range(3))+'\n'+Path('/proc/meminfo').read_text()+'\n'+json.dumps({k:ENV.get(k) for k in ['WM_OPTIONS','WM_PROJECT_VERSION','LD_LIBRARY_PATH','LD_PRELOAD','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','FOAM_CONTROLDICT']},indent=2))
 # Retain real adjacent snapshots for each scientific checkpoint; standard native output only.
 writes=sorted(set(v for end in sorted(set([n for n in [100,250,500,750] if n<STEP_CAP]+[STEP_CAP])) for v in [end-2,end-1,end]))
 dump(P/'design.json',{'steps_cap':STEP_CAP,'wall_cap_seconds':WALL_CAP,'total_authorized_step_cap_all_attempts':1000,'total_authorized_wall_cap_all_attempts':600,'logging_repair_and_budget':REPAIR,'ranks':12,'starting_state':'validated cold rest, continuous native oldTime in memory','start_time_s':0,'write_steps':writes,'primary_timing':'external monotonic end-log increments; exclude actual native write steps; native ClockTime integer seconds retained','checkpoint_policy':'real adjacent triplets, no purge; retain all native fields and _0 histories plus uniform/time; strict restart remains uncertified because native e/K histories are not output. No thinning of the intrinsic native restart state.','native_signals':{'writeNowSignal':10,'stopAtWriteNowSignal':12,'activation':'case-local OptimisationSwitches, MPI cwd at case so native debug merges local controlDict','write_signal_rule':'send SIGUSR1 to master during step preceding target write; native Time::operator++ reduces flag to all ranks at next increment','stop_signal_rule':'send SIGUSR2 during penultimate step, native Time::operator++ sets endTime and writes at final STEP_CAP','step_watchdog':'if next step after STEP_CAP detected, kill all workers before an extra completion','wall_watchdog':'terminate every solver/launcher PID at600s, no extension or retry'},'function_objects':False,'heavy_diagnostics':False,'decomposition':'scotch','binding':'--nooversubscribe --bind-to core --map-by core --report-bindings','threads':1,'old_scaling_pilot_immutable':True})
 print('PREPARED',P,flush=True)
def proc_tree(root):
 records={}
 for f in Path('/proc').glob('[0-9]*/stat'):
  try:
   s=f.read_text();tail=s[s.rfind(')')+2:].split();records[int(f.parent.name)]={'ppid':int(tail[1]),'name':s[s.find('(')+1:s.rfind(')')],'rss':int(tail[21])*os.sysconf('SC_PAGE_SIZE')}
  except (OSError,ValueError):pass
 descendants={root}
 while True:
  more={pid for pid,rec in records.items() if rec['ppid'] in descendants}-descendants
  if not more:break
  descendants|=more
 return {pid:rec for pid,rec in records.items() if pid in descendants}
def run():
 assert not (P/'process_receipt.json').exists(),'No automatic retry'
 expected=json.loads((P/'input_manifest.json').read_text());assert all(sha(CASE/k)==v for k,v in expected.items())
 cmd=['mpirun','--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings','-np','12','foamRun','-case',str(CASE),'-solver','fluid','-noFunctionObjects','-parallel']
 dump(P/'run_command.json',{'argv':cmd,'shell':__import__('shlex').join(cmd),'cwd':str(CASE),'environment_overrides':{k:ENV[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}})
 start=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();deadline=start+WALL_CAP
 p=subprocess.Popen(cmd,cwd=CASE,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);buffer=b'';markers=[];signals=[];sampling=[];workers={};master=None;peak=0;completed=0;started=0;reason=None;lastsample=-1;activated=False
 targets=json.loads((P/'design.json').read_text())['write_steps'];first=None
 def kill():
  for pid in set(workers)|set(proc_tree(p.pid)):
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
 def send(sig,target):
  assert master is not None and activated,'Native signal handler/PID must be confirmed before use'
  os.kill(master,sig);signals.append({'signal':sig,'target_write_or_stop_step':target,'during_step':started,'wall_seconds':time.monotonic()-start,'master_pid':master})
 def hard_wall_stop():
  nonlocal reason
  reason=reason or 'CUMULATIVE_WALL_LIMIT_600S';kill()
 watchdog=threading.Timer(max(0,deadline-time.monotonic()),hard_wall_stop);watchdog.daemon=True;watchdog.start()
 try:
  with (P/'log.foamRun').open('wb') as log:
   while sel.get_map():
    now=time.monotonic()
    if now>=deadline and reason is None:reason='CUMULATIVE_WALL_LIMIT_600S';kill()
    if now-lastsample>=.5:
     procs=proc_tree(p.pid);workers.update({pid:rec for pid,rec in procs.items() if rec['name']=='foamRun'});r=sum(rec['rss'] for rec in procs.values() if rec['name']=='foamRun');peak=max(peak,r);sampling.append({'wall_seconds':now-start,'summed_solver_RSS_bytes':r,'solver_processes':sum(rec['name']=='foamRun' for rec in procs.values())});lastsample=now
    for key,_ in sel.select(min(.05,max(0,deadline-time.monotonic()))):
     data=os.read(key.fileobj.fileno(),65536)
     if not data:sel.unregister(key.fileobj);continue
     log.write(data);buffer+=data;lines=buffer.split(b'\n');buffer=lines.pop()
     for line in lines:
      elapsed=time.monotonic()-start
      if line.startswith(b'PID    :'):master=int(line.split(b':',1)[1]);workers[master]={}
      if b'sigStopAtWriteNow :' in line and b'Enabling' in line:activated=True
      if line.startswith(b'Time = '):
       started+=1;value=float(line[7:].strip().rstrip(b's'));markers.append({'event':'step_start','step':started,'physical_time_s':value,'wall_seconds':elapsed});first=first if first is not None else elapsed
       if started>STEP_CAP:reason=reason or 'STEP_COUNT_GUARD';kill()
       elif started==STEP_CAP-1:send(signal.SIGUSR2,STEP_CAP)
       elif started+1 in targets and started+1!=STEP_CAP:send(signal.SIGUSR1,started+1)
      elif line.startswith(b'ExecutionTime = '):
       completed+=1;m=re.search(rb'ExecutionTime = ([\d.eE+-]+) s\s+ClockTime = ([\d.eE+-]+) s',line);assert m,line
       markers.append({'event':'step_end','step':completed,'wall_seconds':elapsed,'native_execution_time_s':float(m[1]),'native_clock_time_s':float(m[2])})
       if completed%100==0:print('PROGRESS',completed,'t',markers[-2].get('physical_time_s'),'wall',round(elapsed,2),flush=True)
       if completed>STEP_CAP:reason='STEP_COUNT_VIOLATION';kill()
      elif b'FOAM FATAL' in line or b'residual = nan' in line.lower() or (b'Floating point exception' in line and b'trapping' not in line):reason=reason or 'SOLVER_FAILURE';kill()
   if buffer:log.write(buffer)
 except BaseException as exc:
  reason=reason or 'OBSERVER_FAILURE';kill()
  (P/'observer_error.txt').write_text(repr(exc)+'\n')
 rc=p.wait();wall=time.monotonic()-start;watchdog.cancel()
 dump(P/'timestamp_markers.json',markers);dump(P/'signal_events.json',signals);dump(P/'RSS_samples.json',sampling)
 dump(P/'process_receipt.json',{'start_UTC':utc,'exit_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':rc,'wall_seconds_total':wall,'completed_steps':completed,'started_steps':started,'stop_reason':reason or ('COMPLETED_STEP_CAP_NATIVE_STOP' if completed==STEP_CAP and rc==0 else 'EARLY_EXIT'),'native_stop_handler_confirmed':activated,'master_pid':master,'startup_to_first_time_seconds':first,'peak_sampled_summed_solver_RSS_bytes':peak,'max_observed_solver_processes':max(x['solver_processes'] for x in sampling),'solver_PIDs':sorted(workers),'sampling_interval_s':.5})
 print('END',completed,started,rc,reason,'wall',wall,flush=True)
 return rc==0 and completed==STEP_CAP and reason is None
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='run':sys.exit(0 if run() else 1)
