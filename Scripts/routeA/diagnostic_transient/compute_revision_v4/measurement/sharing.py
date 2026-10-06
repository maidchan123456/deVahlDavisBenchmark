"""Exact Writer.share implementation with bulk copies of immutable numbers.
Static registration/hashes/publication remain identical to frozen Writer.share.
"""
def share(writer,value,encode,sha,need):
 keys={'geometry','volumes','Cv','g','owner','neighbour'}
 def walk(x):
  if isinstance(x,dict):
   result={}
   for key,v in x.items():
    if key in keys:
     raw=encode(v);digest=sha(raw);need(key not in writer.immutable_keys or writer.immutable_keys[key]==digest,'STATIC_BLOB_CHANGED: '+key);writer.immutable_keys[key]=digest
     if digest not in writer.immutable:writer.immutable[digest]=v;writer.publish('immutable_'+digest+'.bin',raw,'immutable')
     result[key]={'$immutable':digest}
    else:result[key]=walk(v)
   return result
  if isinstance(x,list):
   if x and all(type(v) in (int,float) for v in x):return x.copy()
   if x and all(isinstance(v,list) and all(type(n) in (int,float) for n in v) for v in x):return [v.copy() for v in x]
   return [walk(v) for v in x]
  return x
 return walk(value)
