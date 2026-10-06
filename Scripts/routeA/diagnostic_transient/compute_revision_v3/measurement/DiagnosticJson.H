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
extern "C" unsigned char* SHA256(const unsigned char*, std::size_t, unsigned char*);
namespace routeAU04 {
inline void fail(const std::string& why) { throw std::runtime_error("EVALUATOR_FAILURE: "+why); }
inline std::string digest(const std::string& s) {
 unsigned char bytes[32];SHA256(reinterpret_cast<const unsigned char*>(s.data()),s.size(),bytes);
 std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto b:bytes)out<<std::setw(2)<<unsigned(b);return out.str();
}
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
 void dump_into(std::ostream& o)const {
  switch(kind){case Null:o<<"null";break;case Number:if(number==0&&std::signbit(number))o<<"-0.0";else o<<number;break;case Boolean:o<<(boolean?"true":"false");break;case String:o<<quote(string);break;
  case Array:{o<<'[';bool first=true;for(const auto& v:array){if(!first)o<<',';first=false;v.dump_into(o);}o<<']';break;}
  case Object:{o<<'{';bool first=true;for(const auto& kv:object){if(!first)o<<',';first=false;o<<quote(kv.first)<<':';kv.second.dump_into(o);}o<<'}';break;}}
 }
 std::string dump()const {std::ostringstream o;o<<std::setprecision(17);dump_into(o);return o.str();}
 std::string dump_without(const std::string& key)const {if(kind!=Object)fail("JSON_OBJECT");std::ostringstream o;o<<std::setprecision(17)<<'{';bool first=true;for(const auto& kv:object){if(kv.first==key)continue;if(!first)o<<',';first=false;o<<quote(kv.first)<<':';kv.second.dump_into(o);}o<<'}';return o.str();}
};
}
#endif
