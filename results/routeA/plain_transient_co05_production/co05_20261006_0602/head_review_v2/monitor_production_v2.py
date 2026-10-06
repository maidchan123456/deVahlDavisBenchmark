#!/usr/bin/env python3
"""Supervise exactly one authorized launcher; inspect standard log only, never fields."""
import datetime,json,os,re,shutil,signal,subprocess,time
from pathlib import Path
V2=Path(__file__).resolve().parent;P=V2.parent
plan=json.loads((V2/'production_execution_plan_v2.json').read_text());runtime=Path(plan['runtime_output'])
assert not runtime.exists(),'No automatic retry/reuse'
cmd=[str(V2/'run_production_v2.sh'),'--execute','--authorization-file',str(V2/'production_authorization_v2.json')]
# Preflight is captured separately immediately before the actual execute command.
pre=subprocess.run([cmd[0],'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
(V2/'preflight_v2.stdout.txt').write_text(pre.stdout);(V2/'preflight_v2.stderr.txt').write_text(pre.stderr)
assert pre.returncode==0,pre.stderr
(V2/'preflight_v2.json').write_text(json.dumps({'status':'PASS','command_argv':[cmd[0],'--check'],'returncode':pre.returncode,'stdout':json.loads(pre.stdout),'reviewed_HEAD':plan['reviewed_current_HEAD'],'actual_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=P.parents[3],text=True).strip(),'execution_package_seal_sha256':__import__('hashlib').sha256((V2/'execution_package_seal_v2.json').read_bytes()).hexdigest(),'launch_time_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
started=time.monotonic();offset=0;pending=b'';step=0;completed=0;current={};last={};next_report=started;child=None;error=None
pattern=re.compile(rb'^(Time = [^\n]+|deltaT = [^\n]+|Courant Number[^\n]+|ExecutionTime = [^\n]+)',re.M)
def consume():
 global offset,pending,step,completed,current,last
 log=runtime/'log.foamRun'
 if not log.exists():return
 with log.open('rb') as stream:
  stream.seek(offset);data=stream.read();offset=stream.tell()
 data=pending+data;split=data.rfind(b'\n')
 if split<0:pending=data;return
 pending=data[split+1:];data=data[:split+1]
 for match in pattern.finditer(data):
  line=match[0].decode()
  if line.startswith('deltaT = '):current['deltaT_s']=float(line.split('=',1)[1])
  elif line.startswith('Courant Number'):
   co=re.search(r'mean: ([\d.eE+-]+) max: ([\d.eE+-]+)',line)
   if co:current['Co_mean']=float(co[1]);current['Co_max']=float(co[2])
  elif line.startswith('Time = '):
   step+=1;current['time_s']=float(line.split('=',1)[1].strip().rstrip('s'));current['step']=step
  elif line.startswith('ExecutionTime = '):
   completed+=1;last=dict(current);last['completed_step']=completed;last['external_observer_wall_s']=time.monotonic()-started
   times=re.search(r'ExecutionTime = ([\d.eE+-]+) s\s+ClockTime = ([\d.eE+-]+) s',line)
   if times:last['native_ExecutionTime_s']=float(times[1]);last['native_ClockTime_s']=float(times[2])

def report():
 value={'state':'RUNNING' if child.poll() is None else 'LAUNCHER_EXITED','completed_steps':completed,'last_completed':last,'wall_hours':(time.monotonic()-started)/3600,'free_disk_GiB':shutil.disk_usage(P).free/1024**3,'launcher_pid':child.pid,'monitor_pid':os.getpid(),'log_bytes_observed':offset,'fields_read_online':False}
 if last:value['last_completed_tstar']=last['time_s']*(1e-5/.71)/.1**2
 temp=V2/'live_progress_v2.json.tmp';temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(V2/'live_progress_v2.json')
 print(json.dumps(value),flush=True)

def interrupt(signum,frame):raise KeyboardInterrupt('monitor received signal '+str(signum))
for sig in [signal.SIGTERM,signal.SIGINT,signal.SIGHUP]:signal.signal(sig,interrupt)
try:
 with (V2/'launcher_stdout_v2.log').open('wb',buffering=0) as stdout:
  child=subprocess.Popen(cmd,stdout=stdout,stderr=subprocess.STDOUT)
  print('AUTHORIZED_PRODUCTION_LAUNCHER_STARTED pid='+str(child.pid),flush=True)
  while True:
   consume();now=time.monotonic()
   if now>=next_report:report();next_report=now+60
   if child.poll() is not None:break
   time.sleep(2)
  consume();report();rc=child.wait()
except BaseException as exc:
 error=type(exc).__name__+': '+str(exc)
 if child and child.poll() is None:
  child.terminate()
  try:child.wait(timeout=30)
  except subprocess.TimeoutExpired:child.kill();child.wait()
 rc=child.returncode if child else None
finally:
 (V2/'monitor_receipt_v2.json').write_text(json.dumps({'start_end_task':'one authorized launch only','command_argv':cmd,'returncode':rc,'wall_seconds':time.monotonic()-started,'last_completed':last,'completed_steps_observed':completed,'error':error,'automatic_rerun':False,'automatic_restart':False,'fields_read_online':False},indent=2)+'\n')
if error:raise RuntimeError(error)
raise SystemExit(rc)
