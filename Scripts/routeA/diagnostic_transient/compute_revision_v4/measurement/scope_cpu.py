"""Dedicated qualification cgroup CPU accounting; 10% host rule unchanged.

Only an exact preregistered transient user scope is accepted. Its lifetime CPU
includes every process/thread and child that exits between proc samples, plus
both nested observers. A shared login/session cgroup is never accepted.
"""
import math,os,time
from pathlib import Path
from common import need

def scope_path():
 rows=Path('/proc/self/cgroup').read_text().splitlines();need(len(rows)==1 and rows[0].startswith('0::/'),'STOP_CPU_CGROUP_V2_REQUIRED');return Path('/sys/fs/cgroup')/rows[0].split('::',1)[1].lstrip('/')
def verify_scope(expected):
 need(expected.startswith('route-a-') and expected.endswith('.scope') and '/' not in expected,'STOP_CPU_SCOPE_SCHEMA');path=scope_path();need(path.name==expected and os.environ.get('ROUTE_A_CPU_SCOPE')==expected,'STOP_SHARED_OR_WRONG_CPU_SCOPE');return path

def endpoint():
 expected=os.environ.get('ROUTE_A_CPU_SCOPE')
 if not expected:return None # tiny compatibility tests only; target verifier requires it
 path=verify_scope(expected);start=time.perf_counter();before=Path('/proc/stat').read_text().splitlines()[0];values={k:int(v) for k,v in (x.split() for x in (path/'cpu.stat').read_text().splitlines())};after=Path('/proc/stat').read_text().splitlines()[0]
 return {'scope':expected,'cgroup':str(path),'usage_usec':values['usage_usec'],'user_usec':values['user_usec'],'system_usec':values['system_usec'],'host_before':before,'host_after':after,'sample_monotonic':time.monotonic(),'query_seconds':time.perf_counter()-start,'CLK_TCK':os.sysconf('SC_CLK_TCK'),'membership':'all measurement processes and observers; shared session rejected'}
def stats(line):
 v=list(map(int,line.split()[1:9]));return sum(v),sum(v)-v[3]-v[4]
def scope_interval(prev,cur):
 need(prev['scope']==cur['scope'] and prev['cgroup']==cur['cgroup'],'STOP_CPU_SCOPE_CHANGED');pt,pb=stats(prev['host_before']);pat,pab=stats(prev['host_after']);ct,cb=stats(cur['host_before']);cat,cab=stats(cur['host_after']);dt=ct-pat;db=cab-pb;du=cur['usage_usec']-prev['usage_usec'];reasons=[]
 if dt<=0 or du<0:reasons.append('CPU counter discontinuity or insufficient bookend separation')
 # Floor own continuous CPU to Linux tick units: never credit the uncompleted
 # fractional tick. Host busy uses extended endpoints, denominator the inner
 # endpoints, a conservative bound for the few microseconds of query latency.
 own=math.floor(max(0,du)*cur['CLK_TCK']/1e6)
 upper=max(0,db-own)/dt if dt>0 else 1.
 return {'other_fraction_upper':upper,'own_ticks_lower':own,'own_usage_delta_usec':du,'host_total_ticks_lower':dt,'host_busy_ticks_upper':db,'uncertainty':reasons}
