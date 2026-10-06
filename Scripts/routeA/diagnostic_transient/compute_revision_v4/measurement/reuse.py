"""Callback-scoped exact memoization: verified typed content AND explicit epoch.

No pointer is a cache key. Every lookup re-encodes actual content using CPython's
lossless pickle protocol; SHA collisions are also checked against retained bytes.
Unknown/unpickleable input recomputes. Results returned by replay are copied.
Cache entries and claimed saved times describe repeated measured computation,
not an estimate of end-to-end wall savings. Eviction never changes results.
"""
import collections,copy,hashlib,json,pickle,time

class Reuse:
 def __init__(self,limit=128*2**20):
  self.limit=limit;self.epoch=None;self.cache=collections.OrderedDict();self.bytes=0;self.peak=0
  self.stats=collections.Counter();self.seconds=collections.Counter();self.reasons=collections.Counter()
 def begin(self,metadata,sequence):
  # Includes every scientific counter; never infer equality across callbacks.
  self.epoch=(sequence,tuple((k,metadata[k]) for k in ('time_index','outer','pressure','nonOrthogonal','energy_solve','rho_solve')))
  self.cache.clear();self.bytes=0;self.reasons['callback_boundary_clear']+=1
 def apply(self,kind,value,fn,clone=False):
  t=time.monotonic()
  if self.epoch is None:
   self.reasons['unknown_epoch']+=1;return fn(value)
  try:content=pickle.dumps(value,protocol=4)
  except (TypeError,pickle.PicklingError):
   self.reasons['unknown_content']+=1;return fn(value)
  self.seconds['identity_check']+=time.monotonic()-t
  t=time.monotonic();key=(self.epoch,kind,hashlib.sha256(content).digest());entry=self.cache.get(key)
  if entry is not None and entry[0]==content:
   self.stats['hits']+=1;self.stats[kind+'_hits']+=1;self.stats['bytes_avoided']+=entry[3];self.seconds['compute_seconds_avoided']+=entry[2]
   self.cache.move_to_end(key);self.seconds['reuse_lookup']+=time.monotonic()-t
   return copy.deepcopy(entry[1]) if clone else entry[1]
  self.seconds['reuse_lookup']+=time.monotonic()-t;self.stats['misses']+=1;self.stats[kind+'_misses']+=1;self.reasons['content_or_kind_miss']+=1
  t=time.monotonic();result=fn(value);duration=time.monotonic()-t
  result_size=len(result.encode()) if isinstance(result,str) else len(result) if isinstance(result,bytes) else len(pickle.dumps(result,protocol=4))
  size=len(content)+result_size+256
  if size<=self.limit:
   while self.cache and self.bytes+size>self.limit:
    _,old=self.cache.popitem(last=False);self.bytes-=old[4];self.stats['evictions']+=1
   self.cache[key]=(content,copy.deepcopy(result) if clone else result,duration,result_size,size);self.bytes+=size;self.peak=max(self.peak,self.bytes)
  else:self.reasons['entry_exceeds_bound']+=1
  return result
 def report(self):
  return {'lifetime':'callback','identity':'actual typed content pickle4 + SHA256 + byte equality + sequence/scientific counters','limit_bytes':self.limit,'peak_cache_bytes':self.peak,'stats':dict(self.stats),'seconds':dict(self.seconds),'recompute_reasons':dict(self.reasons),'hit_rate':self.stats['hits']/max(1,self.stats['hits']+self.stats['misses'])}

def install(oe,persist):
 cache=Reuse();original_canonical=oe.canonical;original_encode=persist.encode;original_replay=oe.replay_matrix
 def canonical(value):
  if isinstance(value,(list,tuple)):
   if len(value)>=4:return cache.apply('canonical_array',value,original_canonical)
   return '['+','.join(canonical(v) for v in value)+']'
  if isinstance(value,dict):return '{'+','.join(canonical(k)+':'+canonical(v) for k,v in sorted(value.items()))+'}'
  return original_canonical(value)
 oe.canonical=canonical;persist.canonical=canonical
 oe.replay_matrix=lambda value:cache.apply('matrix_replay',value,original_replay,clone=True)
 persist.encode=lambda value:cache.apply('packed_evidence',value,original_encode)
 return cache
