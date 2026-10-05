"""Completed-only U03 scaling fit and timing stability; no scientific decisions."""
import collections,math,statistics

def fit(rows):
 groups=collections.defaultdict(list);censored=[]
 for row in rows:
  if row.get('status')!='COMPLETE' or row.get('censored'):censored.append(row);continue
  t=row['kernel_wall_seconds']
  if t>0 and math.isfinite(t):groups[row['N']].append(t)
 points=sorted((n,statistics.median(v)) for n,v in groups.items() if len(v)>=3)
 if len(points)<3:return {'status':'UNRESOLVED','completed_sizes':points,'censored':censored,'reason':'fewer than3 completed sizes with3repeats'}
 xs=[math.log(n) for n,t in points];ys=[math.log(t) for n,t in points];mx=statistics.mean(xs);my=statistics.mean(ys);p=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs);loga=my-p*mx
 return {'status':'FIT_FOR_RESOURCE_PLANNING_ONLY','a':math.exp(loga),'p':p,'completed_sizes':points,'local_slopes':[math.log(t2/t1)/math.log(n2/n1) for (n1,t1),(n2,t2) in zip(points,points[1:])],'log_residuals':[y-(loga+p*x) for x,y in zip(xs,ys)],'censored':censored,'projection_label':'LOW_CONFIDENCE_PROJECTION','algorithmic_complexity_proof':False}

def stability(values):
 if len(values)<3:return {'status':'UNRESOLVED'}
 mean=statistics.mean(values);cv=statistics.pstdev(values)/mean if mean>0 else None
 return {'min':min(values),'median':statistics.median(values),'max':max(values),'CV':cv,'status':'LOW' if cv is None or cv>.20 or min(values)<=0 or max(values)/min(values)>1.5 else 'STABLE_NUMERIC_ONLY_HOST_TRACE_STILL_REQUIRED'}
