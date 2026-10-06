#ifndef routeA_DiagnosticJson_H
#define routeA_DiagnosticJson_H
#include <map>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <stdexcept>
#include <fstream>
#include <cstdint>
#include <cstring>
#include <chrono>
extern "C" unsigned char* SHA256(const unsigned char*, std::size_t, unsigned char*);
namespace routeAU04 {
inline void fail(const std::string& why) { throw std::runtime_error("EVALUATOR_FAILURE: "+why); }
inline std::string digest(const std::string& s) {
 unsigned char bytes[32];SHA256(reinterpret_cast<const unsigned char*>(s.data()),s.size(),bytes);
 std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto b:bytes)out<<std::setw(2)<<unsigned(b);return out.str();
}
struct ArrayMemo {
 std::map<std::string,std::pair<std::string,double>> values;
 size_t bytes=0,peak=0,hits=0,misses=0,avoided=0;double identity_seconds=0,saved_seconds=0;
 bool enabled=true;
 void clear(){values.clear();bytes=peak=hits=misses=avoided=0;identity_seconds=saved_seconds=0;}
};
inline ArrayMemo& memo(){static ArrayMemo m;return m;}
struct Json {
 enum Kind{Null,Number,String,Boolean,Array,Object};Kind kind=Null;
 double number=0;bool boolean=false;std::string string;std::vector<Json> array;std::map<std::string,Json> object;
 Json(){} Json(double n):kind(Number),number(n){if(!std::isfinite(n))fail("NONFINITE_PAYLOAD");}
 Json(int n):Json(double(n)){} Json(bool b):kind(Boolean),boolean(b){}
 Json(const char* s):kind(String),string(s){} Json(const std::string& s):kind(String),string(s){}
 static Json obj(){Json j;j.kind=Object;return j;} static Json arr(){Json j;j.kind=Array;return j;}
 Json& operator[](const std::string& key){if(kind!=Object)fail("JSON_OBJECT");return object[key];}
 const Json& at(const std::string& key)const{return object.at(key);}
 void push(Json&& j){if(kind!=Array)fail("JSON_ARRAY");array.push_back(std::move(j));}
 void push(const Json& j){if(kind!=Array)fail("JSON_ARRAY");array.push_back(j);}
 static std::string quote(const std::string& s){std::ostringstream o;o<<'"';for(unsigned char c:s){if(c=='"'||c=='\\'){o.put('\\');o.put(static_cast<char>(c));}else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c);else o.put(static_cast<char>(c));}o<<'"';return o.str();}
 void signature(std::string& s)const {
  s.push_back(char(kind));
  auto length=[&](size_t n){uint64_t v=n;s.append(reinterpret_cast<const char*>(&v),8);};
  switch(kind){case Number:s.append(reinterpret_cast<const char*>(&number),8);break;
   case Boolean:s.push_back(boolean);break;case String:length(string.size());s+=string;break;
   case Array:length(array.size());for(const auto& v:array)v.signature(s);break;
   case Object:length(object.size());for(const auto& v:object){length(v.first.size());s+=v.first;v.second.signature(s);}break;default:break;}
 }
 void dump_into(std::ostream& o,bool allow_cache=true)const {
  if(allow_cache&&memo().enabled&&kind==Array&&array.size()>=64){
   auto start=std::chrono::steady_clock::now();std::string content;signature(content);std::string key=digest(content);
   memo().identity_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
   auto found=memo().values.find(key);
   // SHA is only an index: verify the whole canonical-independent typed content.
   if(found!=memo().values.end()&&found->second.first.substr(0,content.size())==content&&found->second.first[content.size()]=='\0'){
    const auto& retained=found->second.first;o<<retained.substr(content.size()+1);memo().hits++;memo().avoided+=retained.size()-content.size()-1;memo().saved_seconds+=found->second.second;return;
   }
   memo().misses++;start=std::chrono::steady_clock::now();std::ostringstream tmp;tmp<<std::setprecision(17);dump_into(tmp,false);std::string raw=tmp.str();
   double duration=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();o<<raw;
   if(memo().bytes+content.size()+raw.size()+128<=128*1024*1024){memo().values[key]={content+std::string(1,'\0')+raw,duration};memo().bytes+=content.size()+raw.size()+128;memo().peak=std::max(memo().peak,memo().bytes);}return;
  }
  switch(kind){case Null:o<<"null";break;case Number:if(number==0&&std::signbit(number))o<<"-0.0";else o<<number;break;case Boolean:o<<(boolean?"true":"false");break;case String:o<<quote(string);break;
  case Array:{o<<'[';bool first=true;for(const auto& v:array){if(!first)o<<',';first=false;v.dump_into(o);}o<<']';break;}
  case Object:{o<<'{';bool first=true;for(const auto& kv:object){if(!first)o<<',';first=false;o<<quote(kv.first)<<':';kv.second.dump_into(o);}o<<'}';break;}}
 }
 std::string dump()const {std::ostringstream o;o<<std::setprecision(17);dump_into(o);return o.str();}
 std::string dump_without(const std::string& key)const {if(kind!=Object)fail("JSON_OBJECT");std::ostringstream o;o<<std::setprecision(17)<<'{';bool first=true;for(const auto& kv:object){if(kv.first==key)continue;if(!first)o<<',';first=false;o<<quote(kv.first)<<':';kv.second.dump_into(o);}o<<'}';return o.str();}
};
}
#endif
