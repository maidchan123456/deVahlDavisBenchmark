#define routeAU04 frozen
#include "/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/v1_4/DiagnosticJson.H"
#undef routeAU04
#undef routeA_DiagnosticJson_H
#include "/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/compute_revision_v3/measurement/DiagnosticJson.H"
#include <random>
#include <cstring>
#include <iostream>
template<class J> J make(std::mt19937_64& rng,int depth){int kind=depth==0?rng()%4:rng()%6;if(kind==0)return J();if(kind==1){uint64_t bits=rng();double value;std::memcpy(&value,&bits,8);return J(std::isfinite(value)?value:-0.);}if(kind==2)return J(bool(rng()%2));if(kind==3)return J(std::string("quote\"slash\\line\nutf8é"));if(kind==4){J a=J::arr();for(int i=0,n=rng()%8;i<n;i++)a.push(make<J>(rng,depth-1));return a;}J a=J::obj();for(int i=0,n=rng()%8;i<n;i++)a[std::to_string(i)]=make<J>(rng,depth-1);return a;}
int main(){for(uint64_t seed=0;seed<2000;seed++){std::mt19937_64 a(seed),b(seed);auto old=make<frozen::Json>(a,3);auto neo=make<routeAU04::Json>(b,3);if(old.dump()!=neo.dump())return 2;if(old.kind==frozen::Json::Object){auto c=old;c.object.erase("1");if(c.dump()!=neo.dump_without("1"))return 3;}}std::cout<<"PASS 2000 JSON values + omit-key identity\n";}
