"""Lossless little-endian typed array container, exact in-container dedup only."""
import hashlib,json,math,struct
SCHEMA='routeA_packed/1.3'
class EvidenceFailure(ValueError):pass
def need(ok,reason):
    if not ok:raise EvidenceFailure('EVIDENCE_FAILURE: '+reason)
def sha(x):return hashlib.sha256(x).hexdigest()
def encode(value):
    data=bytearray();arrays=[];seen={}
    def rectangular(x):
        if type(x) in (int,float):return (),[x]
        if not isinstance(x,list) or not x:return None
        # Rank1 array fast path: preserve the same shape, original type mask,
        # finite checks, byte order, hash and in-container identity. No cache.
        if all(type(v) in (int,float) for v in x):return (len(x),),x
        parts=[rectangular(v) for v in x]
        if any(p is None for p in parts) or any(p[0]!=parts[0][0] for p in parts):return None
        return (len(x),)+parts[0][0],[v for p in parts for v in p[1]]
    def walk(x,path=()):
        rect=rectangular(x) if isinstance(x,list) and x else None
        if rect is not None:
            shape,flat=rect;x=flat
            need(all(math.isfinite(v) for v in x),'NONFINITE')
            dtype='i8' if path and path[-1] in {'owner','neighbour','face_cells','labels'} else 'f8'
            if dtype=='i8':need(all(type(v) is int for v in x),'INTEGER_INDEX_TYPE')
            raw=struct.pack('<'+('q' if dtype=='i8' else 'd')*len(x),*x)
            # Include types, shape and exact signed-zero bits in identity.
            mask='i' if all(type(v) is int for v in x) else 'f' if all(type(v) is float for v in x) else ''.join('i' if type(v) is int else 'f' for v in x)
            key=(dtype,shape,mask,sha(raw))
            if key not in seen:
                seen[key]=len(arrays);arrays.append({'dtype':dtype,'shape':list(shape),'types':mask,'offset':len(data),'byte_length':len(raw),'sha256':sha(raw)});data.extend(raw)
            return {'$array':seen[key]}
        if isinstance(x,list):return [walk(v,path) for v in x]
        if isinstance(x,dict):return {k:walk(v,path+(k,)) for k,v in x.items()}
        if isinstance(x,float):need(math.isfinite(x),'NONFINITE')
        need(x is None or isinstance(x,(str,bool,int,float)),'UNSUPPORTED_TYPE')
        return x
    tree=walk(value)
    header={'schema':SCHEMA,'endian':'little','float':'IEEE754-binary64','index':'signed-int64','arrays':arrays,'tree':tree,'data_bytes':len(data),'data_sha256':sha(data),'lossless':True}
    h=json.dumps(header,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return b'RAP13\0'+struct.pack('<Q',len(h))+h+data

def decode(raw):
    need(raw[:6]==b'RAP13\0' and len(raw)>=14,'MAGIC_TRUNCATED')
    n=struct.unpack('<Q',raw[6:14])[0];need(n<=len(raw)-14,'HEADER_TRUNCATED')
    h=json.loads(raw[14:14+n]);data=raw[14+n:]
    need(h['schema']==SCHEMA and h['endian']=='little' and h['float']=='IEEE754-binary64' and h['index']=='signed-int64','SCHEMA_ENDIAN')
    need(h['lossless'] is True and len(data)==h['data_bytes'] and sha(data)==h['data_sha256'],'DATA_LENGTH_HASH')
    decoded=[];offset=0
    for a in h['arrays']:
        need(a['dtype'] in {'i8','f8'} and len(a['shape'])>=1 and all(type(d) is int and d>0 for d in a['shape']),'DTYPE_SHAPE')
        count=math.prod(a['shape']);need(a['offset']==offset and a['byte_length']==8*count and len(a['types']) in (1,count) and set(a['types'])<={'i','f'},'ARRAY_SHAPE_LENGTH')
        block=data[offset:offset+a['byte_length']];need(len(block)==a['byte_length'] and sha(block)==a['sha256'],'ARRAY_HASH')
        values=list(struct.unpack('<'+('q' if a['dtype']=='i8' else 'd')*count,block));need(all(math.isfinite(v) for v in values),'NONFINITE')
        types=a['types']*count if len(a['types'])==1 else a['types']
        values=[int(v) if t=='i' else float(v) for v,t in zip(values,types)]
        def reshape(v,shape):
            if len(shape)==1:return v
            stride=math.prod(shape[1:]);return [reshape(v[i*stride:(i+1)*stride],shape[1:]) for i in range(shape[0])]
        values=reshape(values,a['shape'])
        decoded.append(values);offset+=len(block)
    need(offset==len(data),'ORPHAN_ARRAY_DATA')
    def walk(x):
        if isinstance(x,dict) and set(x)=={'$array'}:
            i=x['$array'];need(type(i) is int and 0<=i<len(decoded),'ARRAY_REFERENCE');return list(decoded[i])
        if isinstance(x,dict):return {k:walk(v) for k,v in x.items()}
        if isinstance(x,list):return [walk(v) for v in x]
        if isinstance(x,float):need(math.isfinite(x),'NONFINITE')
        return x
    return walk(h['tree'])
