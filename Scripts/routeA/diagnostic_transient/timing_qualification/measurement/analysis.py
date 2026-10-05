"""Frozen completed-only U03 fit and registered repeat/host stability decisions."""
import collections,math,re,statistics
from common import plan

def fit(rows):
 cfg=plan();minimum=cfg['repeatability']['minimum_repeats'];groups=collections.defaultdict(list);censored=[]
 for row in rows:
  if row.get('status')!='COMPLETE' or row.get('censored'):censored.append(row);continue
  t=row['kernel_wall_seconds']
  if t>0 and math.isfinite(t):groups[row['N']].append(t)
 points=sorted((n,statistics.median(v)) for n,v in groups.items() if len(v)>=minimum)
 match=re.search(r'completed sizes>=(\d+)',cfg['Q2_U03']['fit']);need_sizes=int(match[1])
 if len(points)<need_sizes:return {'status':'UNRESOLVED','completed_sizes':points,'censored':censored,'reason':'insufficient completed sizes/repeats'}
 xs=[math.log(n) for n,t in points];ys=[math.log(t) for n,t in points];mx=statistics.mean(xs);my=statistics.mean(ys);p=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs);loga=my-p*mx
 return {'status':'FIT_FOR_RESOURCE_PLANNING_ONLY','a':math.exp(loga),'p':p,'completed_sizes':points,'local_slopes':[math.log(t2/t1)/math.log(n2/n1) for (n1,t1),(n2,t2) in zip(points,points[1:])],'log_residuals':[y-(loga+p*x) for x,y in zip(xs,ys)],'censored':censored,'projection_label':cfg['Q2_U03']['projection_label'],'algorithmic_complexity_proof':False}

def thresholds():
 cfg=plan();s=cfg['repeatability']['stability_low_rule']
 return {'minimum_repeats':cfg['repeatability']['minimum_repeats'],'CV':float(re.search(r'CV>([\d.]+)',s)[1]),'ratio':float(re.search(r'max/min>([\d.]+)',s)[1]),'other_busy_fraction':float(re.search(r'>(\d+)percent',s)[1])/100}

def stability(values,host_reports=None):
 limits=thresholds()
 if len(values)<limits['minimum_repeats']:return {'status':'UNRESOLVED','TIMING_STABILITY':'LOW','reason':'insufficient completed repeats','automatic_extra_repeats':False}
 mean=statistics.mean(values);cv=statistics.pstdev(values)/mean if mean>0 else None
 numeric_low=cv is None or cv>limits['CV'] or min(values)<=0 or max(values)/min(values)>limits['ratio']
 host_low=host_reports is not None and (len(host_reports)!=len(values) or any(r.get('status')!='STABLE' for r in host_reports))
 return {'min':min(values),'median':statistics.median(values),'max':max(values),'CV_population':cv,'CV':cv,'TIMING_STABILITY':'LOW' if numeric_low or host_low else 'STABLE_NUMERIC_ONLY_HOST_TRACE_STILL_REQUIRED' if host_reports is None else 'STABLE','status':'UNRESOLVED' if numeric_low or host_low else 'STABLE_NUMERIC_ONLY_HOST_TRACE_STILL_REQUIRED' if host_reports is None else 'STABLE','automatic_extra_repeats':False}

def host_stability(rows):
 limits=thresholds();reasons=[];other=[]
 if len(rows)<2:return {'status':'UNRESOLVED','reason':'trace missing/too short'}
 previous=None
 for row in rows:
  h=row.get('host',{});procs=row.get('processes',[])
  if not all(k in h for k in ('CPU_stat','MemAvailable','loadavg','CPU_governor','CPU_frequency','CPU_count')):reasons.append('incomplete host trace');continue
  if h['CPU_governor']=='UNKNOWN' or any(x=='UNKNOWN' for x in h['CPU_frequency'].values()):reasons.append('missing governor/frequency')
  # Linux /proc/stat total excludes guest/guest_nice (already included in user).
  v=[int(x) for x in h['CPU_stat'].split()[1:9]];total=sum(v);idle=v[3]+v[4];busy=total-idle
  ticks={p['pid']:p['CPU_user_ticks']+p['CPU_system_ticks'] for p in procs};stamp=row['timestamp_monotonic']
  if previous:
   dt=total-previous[0];db=busy-previous[1];own=sum(max(0,t-previous[2].get(pid,t)) for pid,t in ticks.items())
   if dt>0:other.append(max(0.,db-own)/dt)
   else:reasons.append('CPU attribution missing')
   if stamp-previous[3]>.1:reasons.append('memory sampling gap over100ms')
  previous=(total,busy,ticks,stamp)
  if not all(k in row for k in ('disk_free','file_count','scratch_bytes')):reasons.append('disk trace missing')
 if not other:reasons.append('other CPU utilization missing')
 if other and max(other)>limits['other_busy_fraction']:reasons.append('other CPU busy exceeds registered10percent')
 governors={r.get('host',{}).get('CPU_governor') for r in rows}
 if len(governors)>1:reasons.append('governor changed')
 return {'status':'UNRESOLVED' if reasons else 'STABLE','reasons':sorted(set(reasons)),'other_CPU_fraction_max':max(other) if other else None,'other_CPU_method':'delta host busy minus tracked process tick deltas; conservative for short-lived/missing process attribution','no_additional_repeats':True}
