"""Independent exact numeric canonical tasks; deterministic collection/commit."""
import concurrent.futures,math,pickle,struct,time,hashlib,sys
class Parallel:
 def __init__(self,workers):
  import numeric_parallel
  if sys.byteorder!='little':raise ValueError('STOP_PARALLEL_ENDIAN')
  if workers not in (1,2,4,8,12):raise ValueError('STOP_PARALLEL_WORKERS')
  self.native=numeric_parallel;self.workers=workers;self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=workers) if workers>1 else None;self.jobs=0;self.wall=0;self.cpu=0
 def array(self,value):
  def flatten(x):
   if isinstance(x,(list,tuple)) and x:
    if all(type(v) in (int,float) for v in x):return (len(x),),list(x)
    parts=[flatten(v) for v in x]
    if all(p is not None and p[0]==parts[0][0] for p in parts):return (len(x),)+parts[0][0],[v for p in parts for v in p[1]]
   return None
  rect=flatten(value)
  if rect is None:return None
  shape,flat=rect
  if any(not math.isfinite(v) for v in flat):return None
  return struct.pack('<'+'d'*len(flat),*flat),shape
 def compute(self,prepared):return self.native.canonical(*prepared)
 def prewarm(self,tree,cache):
  unique={};start=time.monotonic();cpu=time.process_time()
  def visit(x):
   if isinstance(x,(list,tuple)) and len(x)>=4:
    content=pickle.dumps(x,protocol=4);key=(cache.epoch,'canonical_array',hashlib.sha256(content).digest())
    if key not in unique:
     prepared=self.array(x)
     if prepared is not None:unique[key]=(content,x,prepared)
    if key in unique:return
   if isinstance(x,dict):
    for v in x.values():visit(v)
   elif isinstance(x,(list,tuple)):
    for v in x:visit(v)
  visit(tree);jobs=[]
  for key,(content,value,prepared) in unique.items():
   if key not in cache.cache:
    if self.pool:jobs.append((key,content,self.pool.submit(self.compute,prepared)))
    else:jobs.append((key,content,self.compute(prepared)))
  for key,content,job in jobs:
   result=job.result() if self.pool else job;size=len(content)+len(result.encode())+256
   if size<=cache.limit:
    while cache.cache and cache.bytes+size>cache.limit:
     _,old=cache.cache.popitem(last=False);cache.bytes-=old[4];cache.stats['evictions']+=1
    # Saved-compute seconds for these precomputed entries remain UNKNOWN(0);
    # wall/CPU are measured for the whole deterministic prewarm, not per task.
    cache.cache[key]=(content,result,0,len(result.encode()),size);cache.bytes+=size;cache.peak=max(cache.peak,cache.bytes);cache.stats['parallel_prewarm_misses']+=1
  self.jobs+=len(jobs);self.wall+=time.monotonic()-start;self.cpu+=time.process_time()-cpu
 def report(self):return {'workers':self.workers,'independent_array_tasks':self.jobs,'prewarm_wall_seconds':self.wall,'prewarm_CPU_seconds':self.cpu,'commit_order':'first logical traversal occurrence; results collected in registered order','batching':False,'async_backend':False}
 def close(self):
  if self.pool:self.pool.shutdown(wait=True)
