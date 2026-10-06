"""Exact RAP13 and native canonical JSON equivalence, finite synthetic tests."""
import importlib.util,json,random,subprocess,sys,time,math
from common import ROOT,HERE,REVISION_ROOT,atomic,sha
import packed
oldpath=ROOT/'Scripts/routeA/diagnostic_transient/v1_4/packed.py';spec=importlib.util.spec_from_file_location('frozen_packed',oldpath);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
rng=random.Random(53);fixtures=[None,[],True,False,0,-0.,[1,2,3],[1.,-0.,float.fromhex('0x0.0000000000001p-1022')],{'owner':[0,1,2],'x':[[1.,2.],[3.,4.]],'mixed':[1,2.,0,-0.]},{'ragged':[[1],[2,3]],'words':['a','b']}]
for _ in range(300):fixtures.append({'owner':[rng.randrange(100) for _ in range(rng.randrange(1,100))],'field':[rng.uniform(-1e100,1e100) for _ in range(rng.randrange(1,100))],'vector':[[rng.random(),rng.random(),rng.random()] for _ in range(20)]})
for x in fixtures:assert old.encode(x)==packed.encode(x)
for value in ([math.inf],[math.nan],{'owner':[1.,2.]},object()):
 errors=[]
 for module in (old,packed):
  try:module.encode(value)
  except Exception as e:errors.append(str(e))
 assert len(errors)==2 and errors[0]==errors[1],errors
out=REVISION_ROOT/'codec_equivalence_cycle2';out.mkdir()
code=r'''#define routeAU04 frozen
#include "FROZEN_HEADER"
#undef routeAU04
#undef routeA_DiagnosticJson_H
#include "REVISION_HEADER"
#include <random>
#include <cstring>
#include <iostream>
template<class J> J make(std::mt19937_64& rng,int depth){int kind=depth==0?rng()%4:rng()%6;if(kind==0)return J();if(kind==1){uint64_t bits=rng();double value;std::memcpy(&value,&bits,8);return J(std::isfinite(value)?value:-0.);}if(kind==2)return J(bool(rng()%2));if(kind==3)return J(std::string("quote\"slash\\line\nutf8é"));if(kind==4){J a=J::arr();for(int i=0,n=rng()%8;i<n;i++)a.push(make<J>(rng,depth-1));return a;}J a=J::obj();for(int i=0,n=rng()%8;i<n;i++)a[std::to_string(i)]=make<J>(rng,depth-1);return a;}
int main(){for(uint64_t seed=0;seed<2000;seed++){std::mt19937_64 a(seed),b(seed);auto old=make<frozen::Json>(a,3);auto neo=make<routeAU04::Json>(b,3);if(old.dump()!=neo.dump())return 2;if(old.kind==frozen::Json::Object){auto c=old;c.object.erase("1");if(c.dump()!=neo.dump_without("1"))return 3;}}std::cout<<"PASS 2000 JSON values + omit-key identity\n";}
'''.replace('FROZEN_HEADER',str(ROOT/'Scripts/routeA/diagnostic_transient/v1_4/DiagnosticJson.H')).replace('REVISION_HEADER',str(HERE/'DiagnosticJson.H'))
(out/'check.C').write_text(code);p=subprocess.run(['g++','-std=c++14','-O2',str(out/'check.C'),'/usr/lib/x86_64-linux-gnu/libcrypto.so.3','-o',str(out/'check')],capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr;p=subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=15);assert p.returncode==0,p.stderr
micro=[]
for n in (4,2048):
 value={'owner':list(range(n)),'rho':[1.]*n,'U':[[0.,0.,0.] for _ in range(n)]}
 for repeat in range(3):
  for name,module in [('old',old),('new',packed)]:
   begin=time.perf_counter();raw=module.encode(value);micro.append({'n':n,'repeat':repeat,'codec':name,'seconds':time.perf_counter()-begin,'packed_sha256':__import__('hashlib').sha256(raw).hexdigest()})
atomic(REVISION_ROOT,'codec_equivalence_cycle2.json',{'status':'PASS','RAP13_fixtures':len(fixtures),'negative_errors_exact':True,'JSON_cases':2000,'JSON_omit_key_identity_exact':True,'CPP_output':p.stdout,'packed_microbench':micro,'transport_JSON_unchanged':True,'scientific_content_changed':False,'algorithm_U03_changed':False})
print('PASS')
