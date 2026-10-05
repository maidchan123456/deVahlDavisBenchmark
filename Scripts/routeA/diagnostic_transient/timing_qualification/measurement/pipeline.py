"""Fixed non-CFD native/backend process topology. Never accepts an external command."""
import ctypes,json,os,resource,signal,socket,subprocess,sys,time
from pathlib import Path
from common import HERE,PREP,plan,atomic,before_write,sha,load,need
from fixture import packets,topology,tiny_topology,graph

BINARY=PREP/'timing_harness_build_v4/native_adapter'

def child_guards(cap):
 parent=os.getppid();ctypes.CDLL(None).prctl(1,signal.SIGKILL,0,0,0)
 if os.getppid()!=parent:os._exit(99)
 resource.setrlimit(resource.RLIMIT_AS,(cap,cap))

def read_time_v(path):
 result={}
 for line in path.read_text().splitlines():
  for text,key,factor in [('Maximum resident set size (kbytes):','peak_RSS_bytes',1024),('User time (seconds):','CPU_user_seconds',1),('System time (seconds):','CPU_system_seconds',1)]:
   if text in line:result[key]=float(line.split(text)[1].strip())*factor
 return result

def roles(out,values):
 p=out/'roles.json.partial';p.write_text(json.dumps(values));os.replace(p,out/'roles.json')

def run(out,mode,budget,tiny=False,purpose='full',sample_class=None,event=None,receipt_path=None,authorization_file=None):
 if not tiny:
  from runner import verify_stage_execution
  need(receipt_path and authorization_file,'STOP_STAGE_PERMISSION_REQUIRED');verify_stage_execution(receipt_path,authorization_file)
 need(mode in ('ON','OFF'),'STOP_DIAGNOSTIC_MODE');build=load(BINARY.parent/'build_receipt.json');need(sha(BINARY)==build['binary_SHA256'],'STOP_NATIVE_BINARY_HASH')
 t=topology() if not tiny else tiny_topology();cfg=plan();limits=cfg['stages']['Q1']['budgets'];s1,s2=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM);backend=None;native=None
 budgetfile=out/'worker_budget.json';atomic(out,budgetfile.name,budget,budget)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1')
 for key in ('ROUTE_A_TIMING_SELF_TEST','ROUTE_A_BIND_LIVE','ROUTE_A_SYNTHETIC_LIVE','ROUTE_A_PREFLIGHT_RECEIPT','ROUTE_A_SERIES_RETAINED_CAP_BYTES'):env.pop(key,None)
 if tiny:env['ROUTE_A_TIMING_SELF_TEST']='TINY_SELF_TEST_ONLY'
 else:env.update(ROUTE_A_TIMING_STAGE_RECEIPT=str(receipt_path),ROUTE_A_TIMING_STAGE_RECEIPT_SHA256=sha(receipt_path),ROUTE_A_TIMING_AUTHORIZATION_FILE=str(authorization_file))
 log=(out/'backend.log').open('xb');native_log=(out/'native_progress.jsonl').open('xb')
 try:
  if mode=='ON':backend=subprocess.Popen(['/usr/bin/time','-v','-o',str(out/'backend_time_v.txt'),sys.executable,'-B',str(HERE/'backend.py'),str(s2.fileno()),str(out),str(budgetfile),purpose,event or 'NONE','TINY' if tiny else 'TARGET'],pass_fds=(s2.fileno(),),stdout=log,stderr=log,env=env,preexec_fn=lambda:child_guards(limits['backend_AS_max_bytes']))
  else:s2.close()
  native=subprocess.Popen(['/usr/bin/time','-v','-o',str(out/'native_time_v.txt'),str(BINARY),str(s1.fileno()),mode,str(cfg['Q1_design']['packet_limit_bytes'])],pass_fds=(s1.fileno(),),stdin=subprocess.PIPE,stdout=native_log,stderr=native_log,env=env,preexec_fn=lambda:child_guards(limits['native_AS_max_bytes']))
  roles(out,{'driver':os.getpid(),'native':native.pid,**({'backend':backend.pid} if backend else {})});s1.close();s2.close()
  nodes=graph()
  if purpose!='full':
   candidates=nodes[1:]
   if sample_class=='matrix':candidates=[r for r in candidates if 'matrix' in r['payload']]
   elif sample_class=='term':candidates=[r for r in candidates if 'integrated_cells' in r['payload']]
   elif sample_class=='selected':candidates=[r for r in candidates if r['metadata']['stage']=='energy_after_solve']
   elif sample_class=='scalar':candidates=[r for r in candidates if r['metadata']['stage']=='controller_complete']
   else:candidates=[r for r in candidates if r['metadata']['stage']=='time_start']
   if purpose=='memory' and event=='selected512MiB bundle':
    selected=[r for r in nodes[1:] if r['metadata']['outer']==24 or (r['metadata']['outer']==1 and r['metadata']['pressure']==0 and (r['metadata']['stage'] in ('before_correctDensity','mass_unrelaxed_assembly','mass_after_solve','after_correctDensity') or (r['metadata']['stage']=='term_capture' and r['payload'].get('term') in ('D_B_rho','div_phi','mass_models'))))];nodes=[nodes[0]]+selected
   elif purpose=='memory' and event=='U01 last5 states':nodes=[nodes[0]]+[r for r in nodes if r['metadata']['stage']=='outer_end'][-5:]
   elif purpose=='memory' and event in ('rolling buffer full including join/transient copy','full raw audit preparation as streaming path'):nodes=[nodes[0]]+nodes[-16:]
   else:nodes=[nodes[0],candidates[0]]
  for r in packets(t,nodes):
   raw=(json.dumps(r,separators=(',',':'),allow_nan=False)+'\n').encode();native.stdin.write(raw)
  native.stdin.close();rc=native.wait();brc=backend.wait() if backend else None
  need(rc==0 and (brc is None or brc==0),'STOP_NATIVE_OR_BACKEND_EXIT')
  progress=[json.loads(line) for line in (out/'native_progress.jsonl').read_text().splitlines() if line.startswith('{')]
  need(progress and progress[-1]['callbacks_including_constructor']==len(nodes),'STOP_NATIVE_CALLBACK_COUNT')
  expected_matrices=sum(sum(k in r['payload'] for k in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix')) for r in nodes)
  need(progress[-1]['matrices']==expected_matrices,'STOP_NATIVE_MATRIX_COUNT')
  if mode=='ON' and purpose=='full':
   backend_result=load(out/'backend_result.json');need(backend_result['callbacks_including_constructor']==len(nodes) and backend_result['matrix_packets']==expected_matrices,'STOP_BACKEND_GRAPH_COUNT')
  result={'native_spans':progress[-1],'status':'COMPLETE','classification':'TINY_SELF_TEST_ONLY' if tiny else 'TARGET_SIZE_DIAGNOSTIC_REPLAY','callbacks_recurring':len(nodes)-1,'matrix_packets':sum(sum(k in r['payload'] for k in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix')) for r in nodes),'purpose':purpose,'topology':t['counts'],'mode':mode,'native_exit':rc,'backend_exit':brc,'native_time_v':read_time_v(out/'native_time_v.txt'),'backend_time_v':read_time_v(out/'backend_time_v.txt') if backend else None,'no_CFD':True,'no_physical_time_advance':True}
  atomic(out,'worker_result.json',result,budget);return result
 finally:
  for child in (native,backend):
   if child and child.poll() is None:child.kill();child.wait()
  log.close();native_log.close();s1.close();s2.close()
