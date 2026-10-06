from pathlib import Path
import sys,os,json,subprocess,copy
m=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/exact_evidence_compute_revision/exact_20261006T131936+0900');scope='route-a-exact-parallel-scaling-c3.scope'
if os.environ.get('ROUTE_A_CPU_SCOPE')!=scope:
 log=(m/'parallel_scaling_scope.log').open('xb');env=dict(os.environ,ROUTE_A_CPU_SCOPE=scope);p=subprocess.run(['systemd-run','--user','--scope','--quiet','--unit',scope.removesuffix('.scope'),'-p','CPUAccounting=yes',sys.executable,'-B',__file__],env=env,stdout=log,stderr=log,timeout=188);sys.exit(p.returncode)
sys.path.insert(0,str(Path.cwd()/'Scripts/routeA/diagnostic_transient/compute_revision_v4/measurement'))
from common import plan,atomic
from watchdog import launch
out=m/'parallel_scaling';out.mkdir();b=copy.deepcopy(plan()['stages']['Q1']['budgets']);b.update(scratch_bytes=256*2**20,files_max=128)
r=launch({'command':[sys.executable,'-B',str(m/'parallel_scaling_worker.py')],'budget':b,'trial_wall':180,'interval':.02},out);atomic(m,'parallel_scaling_supervisor_result.json',r)
print(r['status'],r['STOP_reason'])
