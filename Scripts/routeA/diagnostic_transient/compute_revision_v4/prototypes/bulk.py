"""RAEB4 exact numeric transport decoder, bounded verified static registry.
Scientific evaluator/Writer still receive the original full logical object.
"""
import copy,hashlib,json,math,struct
SCHEMA='routeA_exact_bulk/1'
MAGIC=b'RAEB4\0\0\0';FINISH=b'RAEF4\0\0\0'
class BulkFailure(ValueError):pass
def need(ok,code):
 if not ok:raise BulkFailure('STOP_BULK_'+code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def static_path(path):
 parts=path.split('/');return parts[-1] in ('owner','neighbour','volumes','Cv','g') or 'geometry' in parts or 'live_binding' in parts
class Bulk:
 def __init__(self,cap=32*2**20,cache_cap=64*2**20):self.cap=cap;self.cache_cap=cache_cap;self.registry={};self.cache_bytes=0;self.peak=0;self.hits=0;self.registrations=0
 def decode(self,raw):
  need(len(raw)>=24 and raw[:8]==MAGIC,'MAGIC_TRUNCATED');nh,nd=struct.unpack('<QQ',raw[8:24]);need(nh+nd+24==len(raw) and len(raw)<=self.cap,'LENGTH')
  try:h=json.loads(raw[24:24+nh])
  except (ValueError,UnicodeError) as e:raise BulkFailure('STOP_BULK_HEADER') from e
  data=raw[24+nh:];need(h['schema']==SCHEMA and h['endian']=='little','SCHEMA_ENDIAN');need(h['data_sha256']==sha(data),'DATA_HASH');arrays=[];offset=0;field_ids=set()
  for a in h['arrays']:
   need(a['epoch']==h['epoch'],'EPOCH');need(a['field_id'] not in field_ids,'DUPLICATE_FIELD');field_ids.add(a['field_id'])
   need(a['dtype'] in ('f8','i8') and isinstance(a['shape'],list) and len(a['shape'])>=1 and all(type(x) is int and x>0 for x in a['shape']),'DTYPE_SHAPE');count=math.prod(a['shape']);need(type(a['count']) is int and a['count']==count and a['byte_length']==count*8,'SHAPE_LENGTH');mask=a['types'];need(len(mask) in (1,count) and set(mask)<=set('if'),'TYPES')
   if a['reference']:
    need(a['static'] and static_path(a['field_id']) and a['offset'] is None and a['stable_id'] in self.registry,'REFERENCE')
    saved=self.registry[a['stable_id']];need(saved[:5]==(a['field_id'],a['dtype'],a['shape'],mask,a['sha256']),'REFERENCE_IDENTITY');block=saved[5];self.hits+=1
   else:
    need(a['offset']==offset,'OFFSET');block=data[offset:offset+a['byte_length']];offset+=len(block);need(len(block)==a['byte_length'],'MISSING_BYTES')
   need(len(block)==a['byte_length'] and sha(block)==a['sha256'],'CONTENT_HASH')
   if a['static']:
    need(static_path(a['field_id']) and a['stable_id']==sha(a['field_id'].encode()),'STATIC_ID')
    entry=(a['field_id'],a['dtype'],a['shape'],mask,a['sha256'],block)
    if a['stable_id'] in self.registry:need(self.registry[a['stable_id']]==entry,'STATIC_CHANGED')
    else:
     need(self.cache_bytes+len(block)<=self.cache_cap,'CACHE_BOUND');self.registry[a['stable_id']]=entry;self.cache_bytes+=len(block);self.peak=max(self.peak,self.cache_bytes);self.registrations+=1
   values=list(struct.unpack('<'+('q' if a['dtype']=='i8' else 'd')*count,block));need(all(math.isfinite(v) for v in values),'NONFINITE');types=mask*count if len(mask)==1 else mask
   for i,t in enumerate(types):
    if t=='i':need(values[i]==int(values[i]),'INTEGER_VALUE');values[i]=int(values[i])
    else:values[i]=float(values[i])
   def reshape(v,shape):
    if len(shape)==1:return v
    stride=math.prod(shape[1:]);return [reshape(v[i:i+stride],shape[1:]) for i in range(0,len(v),stride)]
   arrays.append(reshape(values,a['shape']))
  need(offset==len(data),'EXTRA_BYTES');used=set()
  def walk(x,path=''):
   if isinstance(x,dict) and set(x)=={'$raeb4'}:
    i=x['$raeb4'];need(type(i) is int and 0<=i<len(arrays),'ARRAY_REFERENCE');need(h['arrays'][i]['field_id']==path,'FIELD_ID');used.add(i);return copy.deepcopy(arrays[i])
   if isinstance(x,dict):return {k:walk(v,path+'/'+k.replace('~','~0').replace('/','~1')) for k,v in x.items()}
   if isinstance(x,list):return [walk(v,path+'/'+str(i)) for i,v in enumerate(x)]
   return x
  tree=walk(h['tree']);need(used==set(range(len(arrays))),'MISSING_ARRAY');need(tree['sequence']==h['sequence'],'SEQUENCE')
  from online_evaluator import canonical
  need(sha(canonical(tree['metadata']).encode())==h['epoch'],'EPOCH_CONTENT');return tree
 def receive(self,stream):
  def exact(n):
   raw=stream.reader.read(n);need(len(raw)==n,'TRUNCATED');return raw
  magic=exact(8)
  if magic==FINISH:return None,8
  need(magic==MAGIC,'SCHEMA_MAGIC');sizes=exact(16);nh,nd=struct.unpack('<QQ',sizes);need(nh+nd+24<=self.cap,'FRAME_BOUND');raw=magic+sizes+exact(nh+nd);return self.decode(raw),len(raw)
 def report(self):return {'schema':SCHEMA,'static_registry_peak_bytes':self.peak,'reference_hits':self.hits,'registrations':self.registrations,'bound':self.cache_cap}
