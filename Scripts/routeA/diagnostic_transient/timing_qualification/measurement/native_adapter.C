// RESOURCE_QUALIFICATION_FIXTURE_ONLY. Standard C++/crypto only; no OpenFOAM
// Time, solver, fvMatrix solve or case API. Uses the frozen production Json type.
#include "../../v1_4/DiagnosticJson.H"
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <chrono>
#include <iostream>
#include <cstdlib>
using routeAU04::Json;using routeAU04::digest;using routeAU04::fail;
struct Parser {const std::string& s;size_t p=0;int depth=0;
 void ws(){while(p<s.size()&&std::isspace((unsigned char)s[p]))p++;}
 char get(){if(p>=s.size())fail("TRUNCATED_INPUT");return s[p++];}
 std::string str(){if(get()!='"')fail("STRING");std::string v;while(true){char c=get();if(c=='"')break;if(c=='\\'){c=get();if(c=='n')c='\n';else if(c=='r')c='\r';else if(c=='t')c='\t';else if(c!='\\'&&c!='"'&&c!='/')fail("ESCAPE");}v+=c;}return v;}
 Json value(){ws();if(++depth>100)fail("DEPTH");char c=s.at(p);Json j;
 if(c=='{'){get();j=Json::obj();ws();if(s.at(p)!='}')while(true){ws();std::string k=str();ws();if(get()!=':')fail("COLON");if(j.object.count(k))fail("DUPLICATE_KEY");j[k]=value();ws();char t=get();if(t=='}')break;if(t!=',')fail("COMMA");}else get();}
 else if(c=='['){get();j=Json::arr();ws();if(s.at(p)!=']')while(true){j.push(value());ws();char t=get();if(t==']')break;if(t!=',')fail("COMMA");}else get();}
 else if(c=='"')j=Json(str());else if(s.compare(p,4,"true")==0){p+=4;j=Json(true);}else if(s.compare(p,5,"false")==0){p+=5;j=Json(false);}else if(s.compare(p,4,"null")==0){p+=4;}
 else{char* end=nullptr;double n=std::strtod(s.c_str()+p,&end);if(end==s.c_str()+p)fail("NUMBER");p=end-s.c_str();j=Json(n);}depth--;return j;}
 Json parse(){Json j=value();ws();if(p!=s.size())fail("TRAILING_INPUT");return j;}
};
double now(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
std::string identity(const Json& j,const std::string& key){Json x=j;x.object.erase(key);return digest(x.dump());}
void rehash(Json& j){
 if(j.kind==Json::Array){for(auto& v:j.array)rehash(v);return;}if(j.kind!=Json::Object)return;
 for(auto& kv:j.object)rehash(kv.second);
 if(j.object.count("history_level")&&j.object.count("object_epoch_sha256")){Json v=Json::obj();for(const std::string k:{"name","dimensions","cells","patches","history_level"})v[k]=j.at(k);j["value_sha256"]=digest(v.dump());j["object_epoch_sha256"]=identity(j,"object_epoch_sha256");}
 else if(j.object.count("value_sha256"))j["value_sha256"]=identity(j,"value_sha256");
 if(j.object.count("matrix_epoch")){Json v=Json::obj();for(const std::string k:{"has_diag","dimensions","psi_name","diag","source","has_upper","has_lower","upper","lower","owner","neighbour","patches"})v[k]=j.at(k);j["matrix_epoch"]=digest(v.dump());}
 if(j.object.count("state_epoch"))j["state_epoch"]=identity(j,"state_epoch");
}
void bind(Json& r){Json& p=r["payload"];rehash(p);auto& m=r["metadata"];Json fields=Json::obj(),olds=Json::obj(),bc=Json::obj(),mat=Json::obj();
 for(auto& kv:p.at("native_state_epoch").object){const auto& f=kv.second;if(f.kind!=Json::Object)continue;
 if(f.object.count("value_sha256"))fields[kv.first]=f.at("value_sha256");if(f.object.count("patches"))bc[kv.first]=digest(f.at("patches").dump());
 if(f.object.count("old_times")){Json ids=Json::arr();for(const auto& old:f.at("old_times").array){Json x=Json::obj();x["object_name"]=old.at("name");for(const std::string k:{"time_index","value_sha256","object_epoch_sha256","history_level","represented_time_index"})x[k]=old.at(k);ids.push(x);}olds[kv.first]=ids;}}
 for(auto& kv:p.object)if(kv.second.kind==Json::Object&&kv.second.object.count("matrix_epoch"))mat[kv.first]=kv.second.at("matrix_epoch");
 m["field_epochs"]=fields;m["oldTime_ids"]=olds;m["bc_epochs"]=bc;m["matrix_epochs"]=mat;r["payload_sha256"]=digest(p.dump());
}
void sendall(int fd,const std::string& s){size_t pos=0;while(pos<s.size()){ssize_t n=::send(fd,s.data()+pos,s.size()-pos,MSG_NOSIGNAL);if(n<=0)fail("IPC_SEND");pos+=n;}}
std::string ack(int fd){std::string s;char c;while(::recv(fd,&c,1,0)==1){s+=c;if(c=='\n')return s;if(s.size()>8192)fail("ACK_SIZE");}fail("ACK_TRUNCATED");return s;}
int main(int argc,char**argv){try{if(argc!=4)fail("USAGE fd ON/OFF stage_cap");int fd=std::stoi(argv[1]);bool on=std::string(argv[2])=="ON";if(!on&&std::string(argv[2])!="OFF")fail("MODE");size_t cap=std::stoull(argv[3]);const char* self=std::getenv("ROUTE_A_TIMING_SELF_TEST");bool tiny=self&&std::string(self)=="TINY_SELF_TEST_ONLY";if(!tiny){const char* path=std::getenv("ROUTE_A_TIMING_STAGE_RECEIPT");const char* expected=std::getenv("ROUTE_A_TIMING_STAGE_RECEIPT_SHA256");if(!path||!expected)fail("STAGE_PERMISSION_REQUIRED");std::ifstream f(path);std::string raw((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());if(digest(raw)!=expected)fail("STAGE_RECEIPT_SHA256");const char* auth=std::getenv("ROUTE_A_TIMING_AUTHORIZATION_FILE");if(!auth)fail("AUTHORIZATION_REQUIRED");pid_t verifier=fork();if(verifier<0)fail("PERMISSION_FORK");if(verifier==0){execl("/usr/bin/python3","python3","-B",ROUTE_A_PERMISSION_HELPER,path,auth,(char*)nullptr);_exit(99);}int code=0;if(waitpid(verifier,&code,0)!=verifier||!WIFEXITED(code)||WEXITSTATUS(code)!=0)fail("STAGE_PERMISSION_REJECTED");}std::string line;long count=0,mats=0,bytes=0,ackbytes=0;double parse=0,hash=0,dump=0,wait=0;
 while(std::getline(std::cin,line)){double t=now();Json r=Parser{line}.parse();if(r.at("payload").at("native_state_epoch").at("rho").at("cells").array.size()!=size_t(tiny?4:25600))fail("TARGET_FIXTURE_SHAPE");parse+=now()-t;count++;for(auto& kv:r.at("payload").object)if(kv.second.kind==Json::Object&&kv.second.object.count("matrix_epoch"))mats++;
 // Common native parsing/fixture traversal remains in OFF, without diagnostic work.
 if(on){t=now();bind(r);hash+=now()-t;t=now();std::string raw=r.dump()+"\n";dump+=now()-t;if(raw.size()>cap)fail("STAGE_CAP");t=now();sendall(fd,raw);std::string response=ack(fd);wait+=now()-t;bytes+=raw.size();ackbytes+=response.size();if(response!="OK\n")fail("BACKEND_REJECTED");}
 Json progress=Json::obj();progress["callbacks_including_constructor"]=int(count);progress["matrices"]=int(mats);progress["bytes_IPC"]=double(bytes);progress["ACK_bytes"]=double(ackbytes);progress["native_parse_construct_seconds"]=parse;progress["native_hash_seconds"]=hash;progress["native_serialization_seconds"]=dump;progress["ACK_wait_inclusive_seconds"]=wait;std::cerr<<progress.dump()<<std::endl;
 }
 if(on){sendall(fd,"FINISH\n");if(ack(fd)!="OK\n")fail("BACKEND_FINISH");}return 0;
 }catch(const std::exception& e){std::cerr<<"STOP_NATIVE_ADAPTER "<<e.what()<<std::endl;return 2;}}
