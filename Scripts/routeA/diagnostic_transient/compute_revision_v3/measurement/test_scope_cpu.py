"""Controlled dedicated CPU-scope test; short child may exit between samples."""
import os,subprocess,sys,time,json
from pathlib import Path
from common import REVISION_ROOT,atomic
from scope_cpu import endpoint,verify_scope,scope_interval
scope=os.environ['ROUTE_A_CPU_SCOPE'];path=verify_scope(scope);external=int(os.environ['ROUTE_A_EXTERNAL_TEST_PID']);external_cgroup=Path('/proc')/str(external)/'cgroup';assert scope not in external_cgroup.read_text()
first=endpoint();child=subprocess.Popen([sys.executable,'-c','import time; end=time.process_time()+.18\nwhile time.process_time()<end: pass']);child.wait();second=endpoint();assert second['usage_usec']-first['usage_usec']>=180000
r=scope_interval(first,second);assert r['own_usage_delta_usec']>=180000 and r['own_ticks_lower']>=18
# Reject using a shared login/session or unregistered alias.
try:verify_scope('route-a-wrong.scope')
except ValueError as e:negative=str(e)
else:raise AssertionError('wrong scope accepted')
atomic(REVISION_ROOT,'scope_CPU_validation_cycle2.json',{'status':'PASS','scope':scope,'own_short_lived_child_accounted':True,'external_PID':external,'external_cgroup_different':True,'first':first,'second':second,'interval':r,'negative_refusal':negative,'host_rule_changed':False,'query_wall_max_seconds':max(first['query_seconds'],second['query_seconds'])})
print('PASS')
