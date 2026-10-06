#!/usr/bin/env python3
"""Bounded plain native CFD launcher; no diagnostic backend or function objects."""
import os,sys,json,hashlib,shutil,re,subprocess,time,signal,selectors,statistics,datetime
from pathlib import Path
ROOT=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark')
OUT=Path(__file__).resolve().parent
SRC=ROOT/'cases/routeA/A-Ra1e6-fine'
RANKS=[1,2,4,6,8,12]
def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p): return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def hdr(obj): return 'FoamFile\n{ format ascii; class dictionary; object '+obj+'; }\n'
def val(v): return ('true' if v else 'false') if isinstance(v,bool) else str(v)
def dictionary(d):
 return '\n'.join(k+'\n{\n'+dictionary(v)+'\n}' if isinstance(v,dict) else k+' '+val(v)+';' for k,v in d.items())
def env():
 e=os.environ.copy()
 for k in list(e):
  if k.startswith(('ROUTE_A_','OMPI_')) or k=='LD_PRELOAD': del e[k]
 e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 return e
ENV=env()
def command(cmd,path,timeout=60):
 t=time.monotonic(); r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=ENV,timeout=timeout)
 path.write_bytes(r.stdout)
 return {'argv':cmd,'shell':__import__('shlex').join(cmd),'returncode':r.returncode,'wall_seconds':time.monotonic()-t}
def prepare():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='de127bda5d4acbb42f03ade7f39780a8ed3bbe1c'
 refs={'docs/routeA_diagnostic_transient_contract_v1.5.json':'06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d','docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'}
 for p,h in refs.items(): assert sha(ROOT/p)==h
 c=json.loads((ROOT/next(iter(refs))).read_text())
 dump(OUT/'authorization_receipt.json',{'authorization_class':'PLAIN_TRANSIENT_CFD_MPI_PERFORMANCE_PILOT','source_request':'/home/mirai/.codex/attachments/3dd6567d-f13e-47bf-9497-58a279e72380/貼り付けたテキスト.txt','CFD_ALLOWED':'YES','SHORT_TRANSIENT_ONLY':'YES','MPI_SCALING_ALLOWED':'YES','MAX_MPI_RANKS_PRIMARY':12,'PRODUCTION_ALLOWED':'NO','Q3_ALLOWED':'NO','PARTICLE_COUPLING_ALLOWED':'NO','authority_hashes':refs})
 original={str(f.relative_to(ROOT)):sha(f) for folder in ('0','constant','system') for f in sorted((SRC/folder).rglob('*')) if f.is_file()}
 original.update(refs);dump(OUT/'immutable_source_manifest.json',original)
 base=OUT/'common_input';base.mkdir();(base/'0').mkdir()
 for field in ('U','T','p','p_rgh'): shutil.copy2(SRC/'0'/field,base/'0'/field)
 shutil.copytree(SRC/'constant',base/'constant');(base/'system').mkdir()
 s=(SRC/'system/fvSchemes').read_text();assert s.count('default steadyState;')==1
 (base/'system/fvSchemes').write_text(s.replace('default steadyState;','default backward;'))
 alg=c['transient_algorithm']; switches=alg['frozen_switches'].copy();switches.pop('runTimeModifiable')
 switches.update(pRefPoint='(0.0496875 0.0496875 0.0005)',pRefValue=0)
 sol={'solvers':alg['linear_solver_dictionary'],'PIMPLE':switches,'relaxationFactors':alg['relaxationFactors']}
 (base/'system/fvSolution').write_text(hdr('fvSolution')+dictionary(sol)+'\n')
 def control(n):
  end=sum(2.3111979166666666e-5*1.2**k for k in range(1,n+1))
  return {'application':'foamRun','solver':'fluid','startFrom':'startTime','startTime':0,'stopAt':'endTime','endTime':format(end,'.17g'),'deltaT':'2.3111979166666666e-5','adjustTimeStep':True,'maxCo':.5,'deltaTFactor':1.2,'maxDeltaT':.027734375,'writeControl':'timeStep','writeInterval':n,'purgeWrite':0,'writeFormat':'ascii','writePrecision':17,'writeCompression':'off','timeFormat':'general','timePrecision':17,'runTimeModifiable':False,'functions':{}}
 (base/'system/controlDict').write_text(hdr('controlDict')+dictionary(control(30))+'\n')
 dump(OUT/'common_input_manifest.json',manifest(base))
 for n in [0]+RANKS:
  d=OUT/('cold_check' if n==0 else f'rank_{n:02d}');d.mkdir();shutil.copytree(base,d/'case')
  if n==0: (d/'case/system/controlDict').write_text(hdr('controlDict')+dictionary(control(5))+'\n')
  (d/'case/system/decomposeParDict').write_text(hdr('decomposeParDict')+dictionary({'numberOfSubdomains':n or 1,'method':'scotch'})+'\n')
  dump(d/'input_manifest.json',manifest(d/'case'))
 cmds=[['lscpu'],['mpirun','--version'],['ompi_info','--param','hwloc','all','--level','9'],['foamRun','-help'],['checkMesh','-case',str(base)]]
 for i,cmd in enumerate(cmds):
  r=command(cmd,OUT/f'environment_{i}.txt');assert r['returncode']==0
 environment='\n'.join((OUT/f'environment_{i}.txt').read_text() for i in range(4))+'\n'+Path('/proc/meminfo').read_text()+'\n'+json.dumps({k:ENV.get(k) for k in ['WM_PROJECT_VERSION','WM_OPTIONS','FOAM_LIBBIN','LD_LIBRARY_PATH','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','LD_PRELOAD']},indent=2)
 (OUT/'environment.txt').write_text(environment)
 for n in [0]+RANKS: shutil.copy2(OUT/'environment.txt',OUT/('cold_check' if n==0 else f'rank_{n:02d}')/'environment.txt')
 dump(OUT/'design.json',{'ranks':RANKS,'steps':30,'cold_check_steps':5,'starting_state':'IDENTICAL_COLD_REST; startup benchmark alternative; no checkpoint restart','warmup_steps_excluded':5,'time_end_rule':'analytical sum of native 1.2 growth increments; verify 30 completed, external guard kills upon step 31','end_time':control(30)['endTime'],'wall_cap_per_condition_seconds':600,'primary_total_cap_seconds':3600,'write_policy':'write only at final step 30, no functions; solver-only-ish secondary excludes final write','binding':'--nooversubscribe --map-by core --bind-to core --report-bindings','native_solver':'foamRun -solver fluid -noFunctionObjects; -parallel only for N>1','sampling':'lightweight /proc RSS 0.5 s, external log marker timestamps; external log completion increments; native ClockTime retained for cross-check'})
 print('PREPARED',OUT,flush=True)
def stats(xs):
 if not xs:return None
 avg=statistics.mean(xs)
 return {'count':len(xs),'median':statistics.median(xs),'mean':avg,'min':min(xs),'max':max(xs),'CV':statistics.pstdev(xs)/avg if avg else None}
def rss(group):
 records={}
 for f in Path('/proc').glob('[0-9]*/stat'):
  try:
   a=f.read_text(); tail=a[a.rfind(')')+2:].split()
   records[int(f.parent.name)]=(int(tail[1]),a[a.find('(')+1:a.rfind(')')],int(tail[21])*os.sysconf('SC_PAGE_SIZE'))
  except (FileNotFoundError,ProcessLookupError,PermissionError,ValueError):pass
 children={group}
 while True:
  new={pid for pid,(ppid,name,r) in records.items() if ppid in children}-children
  if not new:break
  children.update(new)
 selected=[r for pid,(ppid,name,r) in records.items() if pid in children and name=='foamRun']
 return sum(selected),len(selected)
def run(n,cold=False):
 d=OUT/('cold_check' if cold else f'rank_{n:02d}');case=d/'case';expected=5 if cold else 30
 assert not (d/'timing.json').exists(),'No automatic retry'
 before=manifest(case);common=json.loads((OUT/'common_input_manifest.json').read_text())
 if not cold: assert {k:v for k,v in before.items() if k!='system/decomposeParDict'}==common
 commands=[];condition_start=time.monotonic()
 previous=0
 prior=OUT/'superseded_cell_reference_attempts'/f'rank_{n:02d}'/'timing.json'
 if not cold and prior.exists():
  old=json.loads(prior.read_text());previous=old['wall_seconds_total']+sum(x.get('wall_seconds',0) for x in old.get('commands',[]))
 budget=json.loads((OUT/'budget.json').read_text()) if (OUT/'budget.json').exists() else None
 remaining_global=3600 if budget is None else datetime.datetime.fromisoformat(budget['all_pilot_CFD_start_UTC']).timestamp()+3600-time.time()
 deadline=time.monotonic()+min(600-previous,remaining_global)
 if deadline<=time.monotonic():raise RuntimeError('Pilot budget exhausted; no launch')
 if n>1:
  r=command(['decomposePar','-case',str(case),'-force'],d/'log.decomposePar',timeout=max(1,deadline-time.monotonic()));commands.append(r)
  if r['returncode']!=0:dump(d/'timing.json',{'status':'DECOMPOSITION_FAILED','commands':commands});return False
 else:(d/'log.decomposePar').write_text('NOT_REQUIRED: serial native case, no decomposition.\n')
 cmd=['mpirun','--nooversubscribe','--bind-to','core','--map-by','core','--report-bindings','-np',str(n),'foamRun','-case',str(case),'-solver','fluid','-noFunctionObjects']
 if n>1:cmd+=['-parallel']
 commands.append({'argv':cmd,'shell':__import__('shlex').join(cmd)})
 dump(d/'commands.json',commands)
 print('START',d.name,datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
 start=time.monotonic();p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=ENV,start_new_session=True)
 sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);buf=b'';markers=[];steps=[];peak=0;peakworkers=0;lastsample=-1;stopreason=None;first=None
 with (d/'log.foamRun').open('wb') as log:
  while sel.get_map():
   now=time.monotonic()
   if now>=deadline and stopreason is None:stopreason='WALL_LIMIT'
   if stopreason and p.poll() is None:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   if now-lastsample>=.5:
    r,w=rss(p.pid);peak=max(peak,r);peakworkers=max(peakworkers,w);lastsample=now
   for key,_ in sel.select(.1):
    data=os.read(key.fileobj.fileno(),65536)
    if not data:sel.unregister(key.fileobj);continue
    log.write(data);buf+=data
    lines=buf.split(b'\n');buf=lines.pop()
    for b in lines:
     line=b.decode(errors='replace');elapsed=time.monotonic()-start
     if line.startswith('Time = '):
      markers.append({'event':'step_start','wall':elapsed,'time':line[7:].strip()})
      if first is None:first=elapsed
      if len([x for x in markers if x['event']=='step_start'])>expected:stopreason='STEP_COUNT_CAP'
     if line.startswith('ExecutionTime = '):
      m=re.search(r'ExecutionTime = ([\d.eE+-]+) s\s+ClockTime = ([\d.eE+-]+) s',line)
      if m:
       steps.append({'step':len(steps)+1,'external_completion_wall':elapsed,'execution_time':float(m[1]),'clock_time':float(m[2])})
       markers.append({'event':'step_end','wall':elapsed})
  if buf:log.write(buf)
 rc=p.wait();total=time.monotonic()-start
 dump(d/'timestamp_markers.json',markers)
 dump(d/'process_receipt.json',{'returncode':rc,'wall_seconds_total':total,'peak_summed_solver_RSS_bytes':peak,'max_solver_processes_observed':peakworkers,'steps':steps,'stopreason':stopreason,'first':first})
 return finish(d,n,cold,steps,markers,rc,total,peak,peakworkers,stopreason,first,commands)
def finish(d,n,cold,steps,markers,rc,total,peak,peakworkers,stopreason,first,commands):
 expected=5 if cold else 30
 text=(d/'log.foamRun').read_text(errors='replace'); blocks=re.split(r'^Time = ',text,flags=re.M)[1:]
 for i,s in enumerate(steps):
  prev=steps[i-1] if i else None
  s['native_increment']=s['clock_time']-(prev['clock_time'] if prev else 0)
  s['external_increment']=s['external_completion_wall']-(prev['external_completion_wall'] if prev else 0)
  block=blocks[i] if i<len(blocks) else ''
  s['physical_time']=float(block.splitlines()[0].rstrip('s'));s['outer_iterations']=[int(x) for x in re.findall(r'PIMPLE: Iteration (\d+)',block)]
  for field in ['p_rgh','e']:
   records=re.findall(r'Solving for '+field+r', Initial residual = ([\d.eE+-]+), Final residual = ([\d.eE+-]+), No Iterations (\d+)',block)
   s[field+'_linear_iterations_total']=sum(int(z) for x,y,z in records);s[field+'_linear_solves']=len(records)
   s[field+'_max_final_residual']=max([float(y) for x,y,z in records],default=None)
  s['dt']=s['physical_time']-(steps[i-1]['physical_time'] if i else 0)
 co=[float(x) for x in re.findall(r'Courant Number mean: [\d.eE+-]+ max: ([\d.eE+-]+)',text)]
 status=stopreason or ('PASS' if rc==0 and len(steps)==expected and '\nEnd\n' in text and all(s['outer_iterations']==list(range(1,25)) for s in steps) else 'FAIL')
 result={'status':status,'rank':n,'cold_check':cold,'returncode':rc,'wall_seconds_total':total,'completed_steps':len(steps),'startup_to_first_time_seconds':first,'total_seconds_per_completed_step':total/len(steps) if steps else None,'peak_summed_solver_RSS_bytes':peak,'max_solver_processes_observed':peakworkers,'RSS_sampling_interval_seconds':.5,'all_steps':steps,'primary_timing_source':'external monotonic log completion increments; native ClockTime integer seconds inadequate; first5 excluded; final scheduled write included','primary':stats([s['external_increment'] for s in steps[5:]]),'solver_only_ish':stats([s['external_increment'] for s in steps[5:-1]]),'external_primary':stats([s['external_increment'] for s in steps[5:]]),'all_step_stats':stats([s['external_increment'] for s in steps]),'max_logged_preSolve_Co':max(co,default=None),'preSolve_Co_sequence':co,'final_physical_time':steps[-1]['physical_time'] if steps else None,'nonfinite_or_fatal_log':bool(re.search(r'FOAM FATAL|Floating point exception(?! trapping)|\bnan\b|\binf\b',text,re.I)),'commands':commands}
 result['condition_wall_including_decomposition_seconds']=sum(x.get('wall_seconds',0) for x in commands)+total
 result['previous_attempt_wall_accounting_seconds']=sum(x.get('wall_seconds',0) for x in json.loads((OUT/'superseded_cell_reference_attempts'/f'rank_{n:02d}'/'commands.json').read_text())) if not cold and (OUT/'superseded_cell_reference_attempts'/f'rank_{n:02d}'/'commands.json').exists() else 0
 dump(d/'timing.json',result)
 print('END',d.name,status,'wall',round(total,3),'median',result['primary'],flush=True)
 return status=='PASS' and not result['nonfinite_or_fatal_log']
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='cold':sys.exit(0 if run(1,True) else 1)
 elif sys.argv[1]=='run':sys.exit(0 if run(int(sys.argv[2])) else 1)
