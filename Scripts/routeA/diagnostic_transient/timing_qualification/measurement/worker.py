"""Private fixed non-CFD worker. Public campaigns are guarded by runner authorization."""
import importlib.util,json,os,resource,sys,time
from pathlib import Path
from common import HERE,ROOT,load,plan,atomic,CONTRACT,need
from pipeline import run


def u03(out,budget,n,tiny=False,result_name='worker_result.json'):
 cfg=plan();from pipeline import roles;roles(out,{'backend':os.getpid()});need(n in ([4] if tiny else cfg['Q2_U03']['node_counts']),'STOP_HISTORY_SIZE')
 path=ROOT/'Scripts/routeA/diagnostic_transient/v1_1/contract_policy.py';spec=importlib.util.spec_from_file_location('unchanged_U03',path);policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
 times=[.6*i/(n-1) for i in range(n)];names=('Nu_bar_cavity','Umax','Wmax','rho_min','rho_max','rho_mean','total_mass','energy_storage');histories={name:[1.]*n for name in names};scales=load(CONTRACT)['steady_arrival']['mass_energy_rho_arrival_policy']['scales']
 begin=time.perf_counter();ok,windows=policy.arrival_candidate(times,histories,.5,scales,True);wall=time.perf_counter()-begin;need(len(windows)==3,'STOP_U03_SHORT_CIRCUIT')
 usage=resource.getrusage(resource.RUSAGE_SELF);result={'status':'COMPLETE','N':n,'kernel_wall_seconds':wall,'CPU_user_seconds':usage.ru_utime,'CPU_system_seconds':usage.ru_stime,'peak_RSS_KiB':usage.ru_maxrss,'fixture_stationarity_result':ok,'windows':3,'scientific_arrival_claim':False,'classification':'TINY_SELF_TEST_ONLY' if tiny else 'RESOURCE_QUALIFICATION_FIXTURE_ONLY'};atomic(out,result_name,result,budget);return result

if __name__=='__main__':
 request=load(sys.argv[1]);out=Path(sys.argv[1]).parent;budget=request['budget'];cfg=plan()
 resource.setrlimit(resource.RLIMIT_AS,(budget['native_AS_max_bytes'],)*2)
 if request.get('tiny'):
  need(request.get('classification')=='TINY_SELF_TEST_ONLY','STOP_TINY_SCOPE')
 else:
  # Internal requests are only valid with an immutable stage receipt AND the
  # explicit authorization file independently revalidated in this child.
  from runner import verify_stage_execution
  verify_stage_execution(request['stage_receipt'],request['authorization_file'])
 kind=request['kind'];tiny=request.get('tiny',False)
 if kind=='pipeline':run(out,request['mode'],budget,tiny,request.get('purpose','full'),request.get('sample_class'),request.get('event'),request.get('stage_receipt'),request.get('authorization_file'))
 elif kind=='u03':u03(out,budget,request['N'],tiny)
 elif kind=='io':
  from io_memory import io_trial
  io_trial(out,budget,tiny)
 else:raise ValueError('STOP_UNIMPLEMENTED_WORKER_KIND:'+str(kind))
