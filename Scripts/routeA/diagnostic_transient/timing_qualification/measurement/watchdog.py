"""Independent supervisor process: plan-based guards and process-group termination."""
import ctypes,json,os,resource,signal,subprocess,sys,time
from pathlib import Path
from common import HERE,atomic,host,footprint,need,load


def heartbeat(path):
 tmp=path.with_name(path.name+'.partial');tmp.write_text(str(time.monotonic()));os.replace(tmp,path)

def parent_death(cap):
 parent=os.getppid();ctypes.CDLL(None).prctl(1,signal.SIGKILL,0,0,0)
 if os.getppid()!=parent:os._exit(99)
 resource.setrlimit(resource.RLIMIT_AS,(cap,cap))

def status(pid):
 text=Path('/proc')/str(pid)/'status';values={}
 for row in text.read_text().splitlines():
  key,_,value=row.partition(':');values[key]=value.strip()
 if values['State'].startswith('Z'):return None
 io={k:int(v) for k,v in (line.split(':') for line in (Path('/proc')/str(pid)/'io').read_text().splitlines())}
 fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
 return {'CPU_user_ticks':int(fields[11]),'CPU_system_ticks':int(fields[12]),'VmHWM':int(values.get('VmHWM','0 kB').split()[0])*1024,'pid':pid,'PPid':int(values['PPid']),'RSS':int(values.get('VmRSS','0 kB').split()[0])*1024,'VmSize':int(values.get('VmSize','0 kB').split()[0])*1024,'io':io,'pgid':os.getpgid(pid)}

def descendants(parent):
 result={parent};allp={}
 for path in Path('/proc').iterdir():
  if path.name.isdigit():
   try:row=status(int(path.name))
   except (OSError,ValueError,ProcessLookupError):continue
   if row:allp[row['pid']]=row
 while True:
  nextp={pid for pid,row in allp.items() if row['PPid'] in result}
  if nextp<=result:break
  result|=nextp
 return {pid:allp[pid] for pid in result if pid in allp}

def group_members(pgid):
 result=set()
 for path in Path('/proc').iterdir():
  if path.name.isdigit():
   try:
    pid=int(path.name)
    if os.getpgid(pid)==pgid and alive(pid):result.add(pid)
   except (OSError,ValueError):pass
 return result

def terminate_group(pgid,tracked,grace=1.,pulse=None):
 for sig in (signal.SIGTERM,signal.SIGKILL):
  try:os.killpg(pgid,sig)
  except ProcessLookupError:pass
  for pid in tracked:
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:
   end=time.monotonic()+min(grace,1.)
   while time.monotonic()<end:
    if all(not alive(pid) for pid in tracked) and not group_members(pgid):return
    if pulse:pulse()
    time.sleep(.01)

 end=time.monotonic()+.5
 while time.monotonic()<end and (group_members(pgid) or any(alive(pid) for pid in tracked)):time.sleep(.01)

def alive(pid):
 try:return status(pid) is not None
 except OSError:return False

def run(command,out,budget,trial_wall,interval=.02,disk_interval=.1,test_injection=None,allow_nested=False):
 ctypes.CDLL(None).prctl(36,1,0,0,0) # reap orphaned qualification descendants
 start=time.monotonic();deadline=start+min(trial_wall,budget['stage_wall_seconds']);last_disk=-float('inf');last_seen={};roles={};tracked=set();reason=None;peaks={'native':0,'backend':0,'combined_simultaneous':0,'all_processes_simultaneous':0};samples=0;proc=None
 trace=(out/'resource_trace.jsonl').open('x');log=(out/'worker.log').open('xb')
 try:
  proc=subprocess.Popen(command,start_new_session=True,stdout=log,stderr=log,preexec_fn=lambda:parent_death(budget['native_AS_max_bytes']),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1'))
  atomic(out,'process_group.json',{'supervisor_pid':os.getpid(),'measurement_root_pid':proc.pid,'pgid':proc.pid})
  while True:
   now=time.monotonic()
   if test_injection=='supervisor_crash' and now-start>.1:os._exit(91)
   try:
    rolefiles=list(out.rglob('roles.json')) if allow_nested else [out/'roles.json']
    for rolefile in rolefiles:
     if rolefile.exists():roles.update(load(rolefile))
    tree=descendants(proc.pid);tracked|=set(tree);allowed_groups={proc.pid}
    if allow_nested:
     for groupfile in out.rglob('process_group.json'):
      group=load(groupfile)
      if group['supervisor_pid'] in tree:allowed_groups.add(group['pgid'])
    snapshot=host();rss={'native':0,'backend':0,'driver':0}
    for pid,row in tree.items():
     ancestor=pid;role='unregistered_child'
     for _ in range(16):
      found=next((name for name,value in roles.items() if value==ancestor),None)
      if found:role=found;break
      if ancestor==proc.pid:role='driver';break
      if ancestor not in tree:break
      ancestor=tree[ancestor]['PPid']
     row['role']=role
     if row['pgid'] not in allowed_groups:reason='STOP_CHILD_PROCESS_ESCAPE'
     if role=='unregistered_child' and now-start>1.:reason='STOP_UNREGISTERED_CHILD'
     cap=budget['backend_AS_max_bytes'] if role=='backend' else budget['native_AS_max_bytes']
     rsscap=budget['backend_RSS_max_bytes'] if role=='backend' else budget['native_RSS_max_bytes']
     if row['VmSize']>cap or row['RSS']>rsscap:reason='STOP_MEMORY_GUARD'
     rss[role if role in rss else 'driver']+=row['RSS']
    for role in ('native','backend'):peaks[role]=max(peaks[role],rss[role])
    peaks['combined_simultaneous']=max(peaks['combined_simultaneous'],rss['native']+rss['backend']);peaks['all_processes_simultaneous']=max(peaks['all_processes_simultaneous'],sum(rss.values()))
    if sum(row['VmSize'] for row in tree.values())>budget['native_AS_max_bytes']+budget['backend_AS_max_bytes']:reason='STOP_MEMORY_GUARD'
    if sum(rss.values())>budget['combined_RSS_max_bytes'] or snapshot['MemAvailable']<budget['host_MemAvailable_min_bytes']:reason='STOP_MEMORY_GUARD'
    if now-last_disk>=disk_interval:
     size,count=footprint(out);v=os.statvfs(out);last_seen={'disk_free':v.f_bavail*v.f_frsize,'file_count':count,'scratch_bytes':size,'free_inodes':v.f_favail};last_disk=now
     if size>budget['scratch_bytes'] or count>budget['files_max']:reason='STOP_STORAGE_GUARD'
     if last_seen['disk_free']<=max(0,budget['scratch_bytes']-size)+max(32*2**30,int(.1*last_seen['disk_free'])):reason='STOP_DISK_FREE_GUARD'
    row={'timestamp_monotonic':now,'supervisor_pid':os.getpid(),'processes':list(tree.values()),'host':snapshot,**last_seen,'native_plus_backend_RSS':rss['native']+rss['backend']}
    raw=json.dumps(row,allow_nan=False)+'\n'
    # Trace reserves count against the same qualification quota.
    if last_seen.get('scratch_bytes',0)+len(raw)>budget['scratch_bytes']:reason='STOP_STORAGE_GUARD'
    trace.write(raw);trace.flush();samples+=1
    heartbeat(out/'watchdog.heartbeat')
    if (out/'runner.heartbeat').exists() and now-float((out/'runner.heartbeat').read_text())>1.:reason='STOP_RUNNER_HEARTBEAT'
   except BaseException as error:
    reason='STOP_WATCHDOG_FAILURE';last_seen['watchdog_error']=repr(error)
   if now>=deadline:reason='STOP_WALL_TIME'
   if reason:terminate_group(proc.pid,tracked,pulse=lambda:heartbeat(out/'watchdog.heartbeat'));break
   if proc.poll() is not None:
    if any(alive(pid) for pid in tracked if pid!=proc.pid):reason='STOP_ORPHAN_CHILD';terminate_group(proc.pid,tracked,pulse=lambda:heartbeat(out/'watchdog.heartbeat'))
    elif proc.returncode!=0:reason='STOP_WORKER_EXIT'
    break
   time.sleep(interval)
  code=proc.wait(timeout=2)
  while True:
   try:
    pid,_=os.waitpid(-1,os.WNOHANG)
    if pid==0:break
   except ChildProcessError:break
  result={'status':'CENSORED' if reason=='STOP_WALL_TIME' else 'STOPPED' if reason else 'COMPLETE','STOP_reason':reason,'exit_code':code,'signal':-code if code<0 else None,'start_monotonic':start,'end_monotonic':time.monotonic(),'wall_seconds':time.monotonic()-start,'samples':samples,'peak_RSS_bytes':peaks,'sum_individual_native_backend_peaks_upper_bound':peaks['native']+peaks['backend'],'tracked_pids':sorted(tracked),'remaining_live_pids':[pid for pid in tracked if alive(pid)],'completed_repeats':0 if reason else 1,'partial_output_retained':True,'sample_valid':reason is None,'disk':last_seen}
  need(not result['remaining_live_pids'],'STOP_ORPHAN_CLEANUP_FAILED')
  atomic(out,'trial_result.json',result);return result
 finally:
  if proc and proc.poll() is None:terminate_group(proc.pid,tracked);proc.wait()
  trace.flush();os.fsync(trace.fileno());trace.close();log.close()

def launch(request,out):
 """Coordinator monitors supervisor itself; no authorization is granted here."""
 ctypes.CDLL(None).prctl(36,1,0,0,0)
 requestfile=out/'supervisor_request.json';atomic(out,requestfile.name,request)
 p=subprocess.Popen([sys.executable,'-B',str(HERE/'watchdog.py'),str(requestfile)],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 start=time.monotonic();failure=None
 while p.poll() is None:
  heartbeat(out/'runner.heartbeat')
  heartbeatfile=out/'watchdog.heartbeat'
  if heartbeatfile.exists() and time.monotonic()-float(heartbeatfile.read_text())>1.:failure='STOP_WATCHDOG_FAILURE';p.kill();break
  if time.monotonic()-start>request['trial_wall']+3.:failure='STOP_WATCHDOG_FAILURE';p.kill();break
  time.sleep(.02)
 stdout,stderr=p.communicate(timeout=2)
 if p.returncode or failure or not (out/'trial_result.json').exists():
  pg=load(out/'process_group.json') if (out/'process_group.json').exists() else None
  if pg:terminate_group(pg['pgid'],descendants(pg['measurement_root_pid']))
  result={'status':'STOPPED','STOP_reason':'STOP_WATCHDOG_FAILURE','sample_valid':False,'partial_output_retained':True,'supervisor_exit':p.returncode,'stderr':stderr.decode(errors='replace')}
  atomic(out,'supervisor_failure.json',result);return result
 return load(out/'trial_result.json')

if __name__=='__main__':
 r=load(sys.argv[1]);out=Path(sys.argv[1]).parent
 run(r['command'],out,r['budget'],r['trial_wall'],r.get('interval',.02),r.get('disk_interval',.1),r.get('test_injection'),r.get('allow_nested',False))
