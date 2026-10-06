#!/usr/bin/env python3
"""Fail-closed production launcher. --check never starts a solver."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import threading

V2 = Path(__file__).resolve().parent
P = V2.parent
from head_integrity_v2 import reviewed_head_guard, verify_package_and_authorization
ROOT = P.parents[3]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(name):
    return json.loads(((V2 / 'production_execution_plan_v2.json') if name == 'production_execution_plan.json' else (P / name)).read_text())

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def entry(text, key):
    m = re.search(r'\b' + re.escape(key) + r'\s+([^;{}]+);', text)
    require(m is not None, 'missing entry: ' + key)
    return m[1].strip()

def semantics(case, plan):
    c = (case / 'system/controlDict').read_text()
    require(not re.search(r'\b(?:libs|#include|#codeStream)\b', c), 'dynamic control configuration forbidden')
    require(re.search(r'\bfunctions\s*\{\s*\}', c), 'functions must be empty')
    for k, v in {'application':'foamRun','solver':'fluid','startFrom':'startTime',
                 'stopAt':'endTime','writeControl':'runTime','purgeWrite':'0',
                 'adjustTimeStep':'true','runTimeModifiable':'false','writeCompression':'off',
                 'writeFormat':'ascii','timePrecision':'12','writePrecision':'17'}.items():
        require(entry(c,k)==v, 'wrong '+k)
    for k,v in {'startTime':0,'endTime':1420,'writeInterval':5,'maxCo':.5,
                'deltaT':2.3111979166666666e-5,'maxDeltaT':.027734375,
                'deltaTFactor':1.2,'writeNowSignal':10,'stopAtWriteNowSignal':12}.items():
        require(float(entry(c,k))==v, 'wrong '+k)
    f = (case / 'system/fvSolution').read_text()
    require('pRefCell' not in f, 'parallel pRefCell forbidden')
    require([float(x) for x in entry(f,'pRefPoint').strip('() ').split()]==[.0496875,.0496875,.0005], 'pRefPoint mismatch')
    for k,v in {'nOuterCorrectors':'24','nCorrectors':'2','nNonOrthogonalCorrectors':'0',
                'momentumPredictor':'true','simpleRho':'false','transonic':'false','consistent':'false'}.items():
        require(entry(f,k)==v,'wrong '+k)
    d = (case / 'system/decomposeParDict').read_text()
    require(entry(d,'numberOfSubdomains')=='12' and entry(d,'method')=='scotch','decomposition mismatch')
    require(plan['ranks']==12 and plan['endTime_s']==1420 and plan['maxCo']==.5, 'plan policy mismatch')
    require('-noFunctionObjects' in plan['command_argv'], 'missing -noFunctionObjects')
    require(plan['command_argv']==['mpirun','--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings','-np','12','foamRun','-case',str(case),'-solver','fluid','-noFunctionObjects','-parallel'], 'command policy mismatch')
    for base in [case]+[case/('processor'+str(i)) for i in range(12)]:
        require(base.is_dir(), 'missing processor directory')
        times=[]
        for sub in base.iterdir():
            if sub.is_dir():
                try: times.append(float(sub.name))
                except ValueError: pass
        require(times==[0.0], 'cold case only; existing physical times detected')
    require(len(list(case.glob('processor[0-9]*')))==12, 'wrong processor count')

def authorization(path, plan):
    require(Path(path).resolve()==(V2/'production_authorization_v2.json').resolve(),'use pinned v2 authorization receipt')
    a=verify_package_and_authorization(plan)
    require(a.get('AUTHORIZED')=='YES', 'PRODUCTION_EXECUTION_NOT_AUTHORIZED: draft AUTHORIZED=NO')
    for key,value in {'authorization_class':'ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION',
                      'preparation_id':plan['preparation_id'],'expected_HEAD':plan['expected_HEAD'],
                      'execution_plan_sha256':sha(V2/'production_execution_plan_v2.json'),
                      'input_manifest_sha256':plan['input_manifest_sha256'],
                      'MPI_RANKS':12,'endTime_s':1420}.items():
        require(a.get(key)==value,'authorization mismatch: '+key)
    require(isinstance(a.get('source_user_authorization_reference'),str) and a['source_user_authorization_reference'].strip(), 'explicit user authorization reference required')
    return a

def check():
    plan=read('production_execution_plan.json'); case=Path(plan['case'])
    reviewed_head_guard(plan)
    verify_package_and_authorization(plan)
    require(sha(plan['input_manifest_file'])==plan['input_manifest_sha256'],'input manifest changed')
    m=read('production_input_manifest.json')
    require(sha(P/'source_reference_guard.json')==m['source_reference_guard_sha256'],'source guard changed')
    for rel,h in read('source_reference_guard.json').items():
        require(sha(ROOT/rel)==h,'source changed: '+rel)
    for rel,h in m['case_files_sha256'].items():
        require(sha(case/rel)==h,'case changed: '+rel)
    require({str(x.relative_to(case)) for x in case.rglob('*') if x.is_file()}==set(m['case_files_sha256']), 'unexpected case files')
    for name,v in m['binary_provenance'].items():
        require(sha(v['path'])==v['sha256'],'binary changed: '+name)
        if name!='libfluid.so':
            require(Path(shutil.which(name) or '/missing').resolve()==Path(v['path']).resolve(),'PATH resolves wrong '+name)
    for path,h in m['installed_source_sha256'].items():
        require(sha(path)==h,'installed source changed: '+path)
    require(not os.environ.get('LD_PRELOAD'),'LD_PRELOAD forbidden')
    require(not os.environ.get('FOAM_CONTROLDICT'),'FOAM_CONTROLDICT override forbidden')
    require(not any(k.startswith(('ROUTE_A_','OMPI_')) for k in os.environ),'diagnostic/nested MPI environment forbidden')
    for libdir in os.environ.get('LD_LIBRARY_PATH','').split(':'):
        candidate=Path(libdir or '.')/'libfluid.so'
        if candidate.exists():
            require(candidate.resolve()==Path(m['binary_provenance']['libfluid.so']['path']).resolve(),'shadow libfluid')
    require(sha(P/'launcher_artifact_manifest.json')==plan['launcher_artifact_manifest_sha256'],'launcher guard changed')
    for rel,h in read('launcher_artifact_manifest.json').items():
        require(sha(P/rel)==h,'launcher artifact changed: '+rel)
    semantics(case,plan)
    require(not Path(plan['runtime_output']).exists(),'execution namespace already exists; STOP_AND_REVIEW')
    require(shutil.disk_usage(case).free>=plan['disk_required_free_bytes'],'disk reserve insufficient')
    available=int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1])*1024
    require(available>=4*1024**3,'less than 4GiB available RAM')
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            require(not ('foamRun ' in cmd and ('-case '+str(case)) in cmd and int(proc.name)!=os.getpid()), 'existing solver for this case')
        except (FileNotFoundError,ProcessLookupError,PermissionError): pass
    return plan

def descendants(root):
    parent={}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            stat=(proc/'stat').read_text(); tail=stat[stat.rfind(')')+2:].split()
            parent[int(proc.name)]=int(tail[1])
        except (FileNotFoundError,ProcessLookupError,PermissionError): pass
    result={root}
    while True:
        more={pid for pid,ppid in parent.items() if ppid in result}-result
        if not more: return result
        result.update(more)

def kill_tree(root, sig):
    for pid in sorted(descendants(root)-{root},reverse=True):
        try: os.kill(pid,sig)
        except ProcessLookupError: pass
    try: os.killpg(root,sig)
    except ProcessLookupError: pass

def verified_master(pid, root):
    require(pid in descendants(root),'master is not in launched process tree')
    env=(Path('/proc')/str(pid)/'environ').read_bytes().split(b'\0')
    cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
    require(b'OMPI_COMM_WORLD_RANK=0' in env and Path(os.fsdecode(cmd[0])).name=='foamRun','master rank/executable mismatch')
    return pid

def fatal_line(line):
    return bool(re.search(r'FOAM FATAL|\b(?:nan|[-+]?inf)\b',line,re.I) or ('floating point exception' in line.lower() and 'trapping' not in line.lower()))

def final_state(case):
    states=[]
    for rank in range(12):
        base=case/('processor'+str(rank))
        choices=[(float(x.name),x) for x in base.iterdir() if x.is_dir() and re.fullmatch(r'[0-9.eE+-]+',x.name)]
        name,folder=max(choices)
        tdict=(folder/'uniform/time').read_text()
        t=float(entry(tdict,'value')); delta=float(entry(tdict,'deltaT')); index=int(entry(tdict,'index'))
        require(t >= 1420-.5*delta and int((t+.5*delta)/5)==284,'native final write/termination condition not satisfied')
        for field in ['T','U','p','p_rgh','rho','phi','U_0','p_0','p_rgh_0','rho_0','phi_0']:
            require((folder/field).is_file(),'missing final field '+field)
        states.append({'rank':rank,'folder':folder.name,'value':t,'deltaT':delta,'index':index})
    require(len({(s['folder'],s['value'],s['index']) for s in states})==1,'rank final state mismatch')
    return states

def execute(plan, auth):
    out=Path(plan['runtime_output']); out.mkdir() # exclusive; never reuse an interrupted run
    save(out/'authorization_receipt.json',auth)
    save(out/'launch.json',{'start_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'host':os.uname().nodename,'launcher_pid':os.getpid(),'command':plan['command_argv'],'environment':plan['environment_overrides'],'input_manifest_sha256':plan['input_manifest_sha256']})
    env=os.environ.copy(); env.update(plan['environment_overrides'])
    started=time.monotonic(); proc=None; reason=None; step=0; ended=False; pending=b''; requests=[]; master=None; activated=False; watchdog=None
    rows=[]; completed=0; metadata={'PRODUCTION_CFD_EXECUTED':'NO','status':'STARTING'}
    try:
        proc=subprocess.Popen(plan['command_argv'],cwd=plan['cwd'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True,bufsize=0)
        metadata['PRODUCTION_CFD_EXECUTED']='YES'
        def hard_wall_stop():
            nonlocal reason
            reason='24h wall guard exceeded'; kill_tree(proc.pid,signal.SIGKILL)
        watchdog=threading.Timer(plan['planned_wall_limit_seconds'],hard_wall_stop); watchdog.daemon=True; watchdog.start()
        save(out/'pid.json',{'mpirun_pid':proc.pid,'process_group':proc.pid})
        sel=selectors.DefaultSelector(); sel.register(proc.stdout,selectors.EVENT_READ)
        next_disk_check=0
        with (out/'log.foamRun').open('wb',buffering=0) as log:
            while sel.get_map():
                now=time.monotonic()
                if now-started>plan['planned_wall_limit_seconds']: reason='24h wall guard exceeded'
                if now>=next_disk_check:
                    if shutil.disk_usage(plan['case']).free<plan['disk_low_watermark_bytes']: reason='disk low watermark'
                    next_disk_check=now+10
                if reason and proc.poll() is None:
                    kill_tree(proc.pid,signal.SIGTERM)
                    try: proc.wait(timeout=15)
                    except subprocess.TimeoutExpired: kill_tree(proc.pid,signal.SIGKILL)
                for key,_ in sel.select(timeout=1):
                    chunk=os.read(key.fd,65536)
                    if not chunk: sel.unregister(key.fileobj); continue
                    log.write(chunk); pending+=chunk
                    lines=pending.split(b'\n'); pending=lines.pop()
                    for raw in lines:
                        line=raw.decode(errors='replace')
                        if fatal_line(line): reason='fatal/nonfinite standard log'
                        if line.startswith('PID    :'): master=int(line.split(':',1)[1])
                        if 'sigWriteNow :' in line and 'Enabling' in line: activated=True
                        if line.strip()=='End': ended=True
                        match=re.match(r'Time = (\S+)',line)
                        if match:
                            step+=1; rows.append({'event':'step_start','step':step,'time_logged':float(match[1].rstrip('s')),'elapsed_wall_s':time.monotonic()-started})
                            if step+1 in plan['startup_write_steps']:
                                require(activated and master is not None,'native write handler/master not confirmed')
                                pid=verified_master(master,proc.pid)
                                os.kill(pid,signal.SIGUSR1)
                                requests.append({'requested_after_Time_header_step':step,'target_next_step':step+1,'master_pid':pid,'wall_elapsed':time.monotonic()-started})
                        if line.startswith('ExecutionTime = '):
                            completed+=1
                            rows.append({'event':'step_end','step':step,'elapsed_wall_s':time.monotonic()-started,'native_execution_line':line})
                        # Preserve all iteration/residual/Co lines in full log; no expensive field reads online.
        rc=proc.wait(timeout=30)
        metadata.update(returncode=rc,normal_End_marker=ended)
        require(not reason and rc==0 and ended,'interrupted/failed: '+str(reason or rc))
        require(completed==step,'incomplete last step')
        metadata['final_states']=final_state(Path(plan['case']))
        require(metadata['final_states'][0]['index']==completed,'last computed step was not stored')
        snapshots=[]
        for directory in (Path(plan['case'])/'processor0').iterdir():
            if not (directory/'uniform/time').is_file(): continue
            text=(directory/'uniform/time').read_text()
            snapshots.append({'directory':directory.name,'index':int(entry(text,'index')),'value':float(entry(text,'value'))})
        metadata['saved_snapshot_times_and_indices']=sorted(snapshots,key=lambda s:s['index'])
        metadata['startup_write_request_review']='Compare requested targets with actual saved uniform/time indices; signal observation is asynchronous.'
        metadata['status']='COMPLETED_NATIVE_ENDTIME'
    except BaseException as e:
        reason=reason or (type(e).__name__+': '+str(e))
        metadata.update(status='INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN',reason=reason,policy='STOP_AND_REVIEW',automatic_retry=False)
        if proc and proc.poll() is None:
            kill_tree(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                kill_tree(proc.pid,signal.SIGKILL); proc.wait()
        metadata['returncode']=proc.returncode if proc else None
    finally:
        if watchdog: watchdog.cancel()
        metadata.update(end_UTC=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_wall_s=time.monotonic()-started,last_started_step=step,completed_steps=completed,startup_write_requests=requests)
        save(out/'execution_result.json',metadata)
        save(out/'time_header_wall_markers.json',rows)
    print(json.dumps(metadata,indent=2))
    return 0 if metadata['status']=='COMPLETED_NATIVE_ENDTIME' else 2

def main():
    def interrupt(signum,frame):
        raise KeyboardInterrupt('received signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupt)
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check',action='store_true'); modes.add_argument('--execute',action='store_true')
    parser.add_argument('--authorization-file',type=Path)
    args=parser.parse_args()
    try:
        if args.execute:
            require(args.authorization_file is not None,'explicit authorization file required')
            auth=authorization(args.authorization_file,read('production_execution_plan.json'))
        plan=check()
        if args.check:
            print(json.dumps({'DRY_VALIDATION':'PASS','CFD_EXECUTED':'NO','AUTHORIZED':'YES','case':plan['case'],'command':plan['command_shell'],'disk_free_bytes':shutil.disk_usage(plan['case']).free},indent=2)); return 0
        return execute(plan,auth)
    except Exception as e:
        print('STOP_AND_REVIEW: '+str(e),file=sys.stderr); return 2

if __name__=='__main__':
    sys.exit(main())
