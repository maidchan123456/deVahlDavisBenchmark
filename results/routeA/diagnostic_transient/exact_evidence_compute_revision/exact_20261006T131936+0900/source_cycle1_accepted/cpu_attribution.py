"""Cumulative subtree CPU: live own ticks + reaped child ticks, identity safe.

Reaped short-lived descendants are represented by ancestor cutime/cstime.
Unreaped zombies remain in the tree. Observer own CPU belongs to measurement,
not external load. Sampling races/late root discovery yield explicit uncertainty,
never a synthetic PASS. The registered external-load threshold stays 10%.
"""
import os,time,math
def subtree_ticks(rows):
 return sum(p['CPU_user_ticks']+p['CPU_system_ticks']+p.get('CPU_children_user_ticks',0)+p.get('CPU_children_system_ticks',0) for p in rows)
def sample(tree,observers,root_pid):
 root=tree.get(root_pid)
 return {'method':'live subtree own+reaped child ticks; observer own ticks','root_identity':[root_pid,root.get('starttime_ticks')] if root else None,'subtree_ticks':subtree_ticks(tree.values()),'observer_ticks':{str(p['pid'])+':'+str(p.get('starttime_ticks')):p['CPU_user_ticks']+p['CPU_system_ticks'] for p in observers},'root_present':root is not None,'boottime':time.clock_gettime(time.CLOCK_BOOTTIME),'CLK_TCK':os.sysconf('SC_CLK_TCK'),'CPU_count':os.cpu_count(),'identities':{str(p['pid'])+':'+str(p.get('starttime_ticks')):{'starttime_ticks':p.get('starttime_ticks'),'own_ticks':p['CPU_user_ticks']+p['CPU_system_ticks']} for p in tree.values()}}
def interval(prev,cur,total_delta,busy_delta):
 reasons=[]
 if not prev.get('snapshot_certified',True) or not cur.get('snapshot_certified',True):reasons.append('exit/reap during CPU snapshot')
 if not prev['root_present'] or not cur['root_present'] or prev['root_identity']!=cur['root_identity']:reasons.append('missing or changed measurement root identity')
 own=cur['subtree_ticks']-prev.get('subtree_ticks_upper',prev['subtree_ticks'])
 if own<0:reasons.append('subtree sampling/reap race or counter discontinuity');own=0
 # Newly seen pre-existing PIDs may have accrued ticks before the previous
 # boundary. Remove a conservative CPU-capacity bound for those ticks.
 for ident,p in cur.get('identities',{}).items():
  if ident not in prev.get('identities',{}) and prev.get('boottime') is not None and p['starttime_ticks'] is not None:
   hz=cur['CLK_TCK'];birth=p['starttime_ticks']/hz
   before=max(0.,prev['boottime']-birth+1/hz)
   own-=min(p['own_ticks'],math.ceil(before*hz)*cur['CPU_count'])
 own=max(0,own)
 for pid,t in cur['observer_ticks'].items():
  if pid not in prev['observer_ticks']:reasons.append('late observer discovery')
  else:own+=max(0,t-prev.get('observer_ticks_upper',prev['observer_ticks'])[pid])
 if total_delta<=0:reasons.append('CPU attribution missing')
 # An asynchronous /proc scan may overcount an exit/reap transition. Upper
 # bound remains host busy when accounting is ambiguous (no false STABLE).
 upper=max(0,busy_delta-own)/total_delta if total_delta>0 else None
 if reasons and total_delta>0:upper=max(0,busy_delta)/total_delta
 return {'other_fraction_upper':upper,'own_ticks':own,'uncertainty':reasons}
