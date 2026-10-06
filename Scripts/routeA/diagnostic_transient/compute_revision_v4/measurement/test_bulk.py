"""Native old-JSON versus RAEB4 roundtrip and fail-closed transport negatives."""
import hashlib,json,math,random,struct,subprocess,sys
from common import HERE,REVISION_ROOT,atomic,sha
from bulk import Bulk,MAGIC
base=REVISION_ROOT/'bulk_validation_attempt_001';base.mkdir(exist_ok=False)
code=r'''#define main frozen_main
#include "NATIVE"
#undef main
int main(int argc,char**argv){try{std::string line;while(std::getline(std::cin,line)){Json j=Parser{line}.parse();if(std::string(argv[1])=="JSON")std::cout<<j.dump()<<"\n";else{std::string raw=exactBulk::encode(j,std::string(argv[1])=="STATIC");std::cout.write(raw.data(),raw.size());}}return 0;}catch(const std::exception&e){std::cerr<<e.what();return 2;}}
'''.replace('NATIVE',str(HERE/'native_adapter.C'))
(base/'check.C').write_text(code);p=subprocess.run(['g++','-O2','-std=c++14','-DROUTE_A_PERMISSION_HELPER="unused"',str(base/'check.C'),'/usr/lib/x86_64-linux-gnu/libcrypto.so.3','-o',str(base/'check')],capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
rng=random.Random(137);values=[0,-0.,1.,-1,1e16,1e17,1e-9,float.fromhex('0x0.0000000000001p-1022')]+[rng.uniform(-1e100,1e100) for _ in range(100)]
records=[{'sequence':1,'metadata':{'time_index':2,'outer':1},'payload':{'field':values,'U':[[v,-v,0.] for v in values],'owner':[0,1,2],'volumes':[1e-9]*10,'empty':[],'labels':[0,2,1]}},{'sequence':2,'metadata':{'time_index':2,'outer':2},'payload':{'field':list(reversed(values)),'owner':[0,1,2],'volumes':[1e-9]*10}}]
source=''.join(json.dumps(x,separators=(',',':'))+'\n' for x in records).encode()
old=subprocess.check_output([str(base/'check'),'JSON'],input=source);expected=[json.loads(x) for x in old.splitlines()]
results={};frames={}
for mode in ('BULK','STATIC'):
 raw=subprocess.check_output([str(base/'check'),mode],input=source);(base/(mode+'.bin')).write_bytes(raw);frames[mode]=[];decoder=Bulk();offset=0
 for e in expected:
  nh,nd=struct.unpack('<QQ',raw[offset+8:offset+24]);frame=raw[offset:offset+24+nh+nd];offset+=len(frame);actual=decoder.decode(frame);frames[mode].append(frame)
  # Compare the exact original canonical state and type-sensitive JSON tree.
  def typed(x):
   if isinstance(x,(int,float)):return (type(x).__name__,struct.pack('<d',x).hex())
   if isinstance(x,list):return [typed(v) for v in x]
   if isinstance(x,dict):return {k:typed(v) for k,v in x.items()}
   return x
  assert typed(actual)==typed(e)
 assert offset==len(raw);results[mode]={'frames':len(expected),'bytes':len(raw),'old_JSON_bytes':len(old),'registry':decoder.report()}
raw=frames['BULK'][0];nh,nd=struct.unpack('<QQ',raw[8:24]);header=json.loads(raw[24:24+nh]);data=raw[24+nh:]
def frame(h=header,d=data):
 b=json.dumps(h,sort_keys=True,separators=(',',':')).encode();return MAGIC+struct.pack('<QQ',len(b),len(d))+b+d
negatives={'truncation':raw[:-1],'extra_bytes':raw+b'x','missing_bytes':raw[:-8]}
import copy
for name,mut in [('wrong_schema',lambda h:h.update(schema='invalid')),('wrong_dtype',lambda h:h['arrays'][0].update(dtype='f4')),('wrong_shape',lambda h:h['arrays'][0].update(shape=[999])),('wrong_length',lambda h:h['arrays'][0].update(byte_length=1)),('wrong_hash',lambda h:h['arrays'][0].update(sha256='0'*64)),('wrong_epoch',lambda h:h['arrays'][0].update(epoch='0'*64)),('epoch_content',lambda h:h.update(epoch='0'*64)),('wrong_field_id',lambda h:h['arrays'][0].update(field_id='/wrong'))]:
 h=copy.deepcopy(header);mut(h);negatives[name]=frame(h)
errors={}
for name,f in negatives.items():
 try:Bulk().decode(f)
 except ValueError as e:errors[name]=str(e)
 else:raise AssertionError(name)
try:Bulk().decode(frames['STATIC'][1])
except ValueError as e:errors['unregistered_reference']=str(e)
else:raise AssertionError('missing reference')
changed=copy.deepcopy(records);changed[1]['payload']['owner']=[0,2,1];p=subprocess.run([str(base/'check'),'STATIC'],input=''.join(json.dumps(x)+'\n' for x in changed).encode(),capture_output=True);assert p.returncode==2 and b'BULK_STATIC_CHANGED' in p.stderr
errors['static_changed_native']=p.stderr.decode()
atomic(REVISION_ROOT,'bulk_unit_validation.json',{'status':'PASS','roundtrip':'bit/type-exact original native JSON; signedzero, IEEE64 extreme, matrix addressing, vectors, empty arrays','results':results,'negative_fail_closed':errors,'native_source_SHA256':sha(HERE/'BulkTransport.H'),'decoder_SHA256':sha(HERE/'bulk.py'),'scientific_content_changed':False})
print('PASS',results)
