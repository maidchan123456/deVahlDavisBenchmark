#ifndef ROUTE_A_EXACT_BULK
#define ROUTE_A_EXACT_BULK
#include "DiagnosticJson.H"
namespace exactBulk {
using routeAU04::Json;using routeAU04::digest;using routeAU04::fail;
inline void u64(std::string& s,uint64_t n){for(int i=0;i<8;i++)s.push_back(char((n>>(8*i))&255));}
inline std::string escape(const std::string& s){std::string r;for(char c:s){if(c=='~')r+="~0";else if(c=='/')r+="~1";else r+=c;}return r;}
inline bool rectangle(const Json& j,std::vector<size_t>& shape,std::vector<double>& flat){
 if(j.kind==Json::Number){flat.push_back(j.number);return true;}
 if(j.kind!=Json::Array||j.array.empty())return false;
 std::vector<size_t> child;for(size_t i=0;i<j.array.size();i++){std::vector<size_t> sub;if(!rectangle(j.array[i],sub,flat))return false;if(i==0)child=sub;else if(sub!=child)return false;}
 shape.push_back(j.array.size());shape.insert(shape.end(),child.begin(),child.end());return true;
}
inline bool integer_token(double x){return std::trunc(x)==x&&std::fabs(x)<1e17&&!(x==0&&std::signbit(x));}
struct Registry {std::map<std::string,std::string> identities;size_t bytes=0,hits=0;};
inline Registry& registry(){static Registry r;return r;}
inline bool static_path(const std::string& path){auto last=path.substr(path.find_last_of('/')+1);return last=="owner"||last=="neighbour"||last=="volumes"||last=="Cv"||last=="g"||path.find("/geometry/")!=std::string::npos||path.find("/live_binding/")!=std::string::npos;}
inline Json walk(const Json& j,const std::string& path,const std::string& epoch,Json& arrays,std::string& data,bool references){
 if(j.kind==Json::Array&&!j.array.empty()){
  std::vector<size_t> shape;std::vector<double> flat;
  if(rectangle(j,shape,flat)){
   std::string block,types;bool index=path.substr(path.find_last_of('/')+1)=="owner"||path.substr(path.find_last_of('/')+1)=="neighbour"||path.substr(path.find_last_of('/')+1)=="face_cells"||path.substr(path.find_last_of('/')+1)=="labels";
   for(double v:flat){bool integer=integer_token(v);types+=integer?'i':'f';uint64_t bits;if(index){if(!integer)fail("BULK_INDEX_TYPE");int64_t n=int64_t(v);std::memcpy(&bits,&n,8);}else std::memcpy(&bits,&v,8);u64(block,bits);}
   if(types.find_first_not_of(types[0])==std::string::npos)types=types.substr(0,1);
   Json a=Json::obj();a["field_id"]=path;a["epoch"]=epoch;a["dtype"]=index?"i8":"f8";a["shape"]=Json::arr();for(auto n:shape)a["shape"].push(Json(double(n)));a["count"]=double(flat.size());a["byte_length"]=double(block.size());a["types"]=types;a["sha256"]=digest(block);
   bool stat=references&&static_path(path),ref=false;std::string id=digest(path);
   if(stat){std::string identity=a["dtype"].string+":"+a["shape"].dump()+":"+types+":"+a["sha256"].string;auto old=registry().identities.find(id);if(old!=registry().identities.end()){if(old->second!=identity)fail("BULK_STATIC_CHANGED");ref=true;registry().hits++;}else{if(registry().bytes+block.size()>64*1024*1024)fail("BULK_CACHE_BOUND");registry().identities[id]=identity;registry().bytes+=block.size();}}
   a["static"]=stat;a["reference"]=ref;a["stable_id"]=stat?Json(id):Json();a["offset"]=ref?Json():Json(double(data.size()));if(!ref)data+=block;
   size_t ix=arrays.array.size();arrays.push(std::move(a));Json reference=Json::obj();reference["$raeb4"]=double(ix);return reference;
  }
 }
 if(j.kind==Json::Array){Json r=Json::arr();for(size_t i=0;i<j.array.size();i++)r.push(walk(j.array[i],path+"/"+std::to_string(i),epoch,arrays,data,references));return r;}
 if(j.kind==Json::Object){Json r=Json::obj();for(const auto& kv:j.object)r[kv.first]=walk(kv.second,path+"/"+escape(kv.first),epoch,arrays,data,references);return r;}
 return j;
}
inline std::string encode(const Json& r,bool references){
 std::string epoch=digest(r.at("metadata").dump()),data;Json arrays=Json::arr();Json tree=walk(r,"",epoch,arrays,data,references),h=Json::obj();h["schema"]="routeA_exact_bulk/1";h["endian"]="little";h["epoch"]=epoch;h["sequence"]=r.at("sequence");h["arrays"]=std::move(arrays);h["tree"]=std::move(tree);h["data_sha256"]=digest(data);std::string header=h.dump(),raw("RAEB4\0\0\0",8);u64(raw,header.size());u64(raw,data.size());raw+=header;raw+=data;return raw;
}
}
#endif
