// RESOURCE_QUALIFICATION_FIXTURE_ONLY. Standard C++/crypto only; no OpenFOAM
// Time, solver, fvMatrix solve or case API. Uses the frozen production Json type.
#include "DiagnosticJson.H"
#include "BulkTransport.H"
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
std::string identity(const Json& j,const std::string& key){return digest(j.dump_without(key));}
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
int main(int argc,char**argv){try{bool bulk=!(std::getenv("ROUTE_A_BULK")&&std::string(std::getenv("ROUTE_A_BULK"))=="OFF");bool references=!(std::getenv("ROUTE_A_STATIC_REFS")&&std::string(std::getenv("ROUTE_A_STATIC_REFS"))=="OFF");if(argc!=4)fail("USAGE fd ON/OFF stage_cap");int fd=std::stoi(argv[1]);bool on=std::string(argv[2])=="ON";if(!on&&std::string(argv[2])!="OFF")fail("MODE");size_t cap=std::stoull(argv[3]);const char* self=std::getenv("ROUTE_A_TIMING_SELF_TEST");bool tiny=self&&std::string(self)=="TINY_SELF_TEST_ONLY";if(!tiny){const char* path=std::getenv("ROUTE_A_TIMING_STAGE_RECEIPT");const char* expected=std::getenv("ROUTE_A_TIMING_STAGE_RECEIPT_SHA256");if(!path||!expected)fail("STAGE_PERMISSION_REQUIRED");std::ifstream f(path);std::string raw((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());if(digest(raw)!=expected)fail("STAGE_RECEIPT_SHA256");const char* auth=std::getenv("ROUTE_A_TIMING_AUTHORIZATION_FILE");if(!auth)fail("AUTHORIZATION_REQUIRED");pid_t verifier=fork();if(verifier<0)fail("PERMISSION_FORK");if(verifier==0){execl("/usr/bin/python3","python3","-B",ROUTE_A_PERMISSION_HELPER,path,auth,(char*)nullptr);_exit(99);}int code=0;if(waitpid(verifier,&code,0)!=verifier||!WIFEXITED(code)||WEXITSTATUS(code)!=0)fail("STAGE_PERMISSION_REJECTED");}std::string line;long count=0,mats=0,bytes=0,ackbytes=0;double parse=0,hash=0,dump=0,wait=0;
 while(std::getline(std::cin,line)){routeAU04::memo().clear();routeAU04::memo().enabled=!(std::getenv("ROUTE_A_REUSE")&&std::string(std::getenv("ROUTE_A_REUSE"))=="OFF");double callback_start=now(),p0=parse,h0=hash,d0=dump,w0=wait;double send_seconds=0,ack_seconds=0;double t=now();Json r=Parser{line}.parse();bool compact=r.object.count("resource_payload_class")&&r.at("resource_payload_class").string=="compact_scalar_receipt";size_t cells=compact?size_t(r.at("fixture_cells").number):r.at("payload").at("native_state_epoch").at("rho").at("cells").array.size();if(cells!=size_t(tiny?4:25600))fail("TARGET_FIXTURE_SHAPE");parse+=now()-t;count++;for(auto& kv:r.at("payload").object)if(kv.second.kind==Json::Object&&kv.second.object.count("matrix_epoch"))mats++;
 // Common native parsing/fixture traversal remains in OFF, without diagnostic work.
 if(on){t=now();if(compact)r["payload_sha256"]=digest(r.at("payload").dump());else bind(r);hash+=now()-t;t=now();std::string logical=r.dump()+"\n";if(logical.size()>cap)fail("STAGE_CAP");std::string raw=bulk?exactBulk::encode(r,references):logical;dump+=now()-t;if(raw.size()>cap)fail("STAGE_CAP");t=now();sendall(fd,raw);send_seconds=now()-t;double astart=now();std::string response=ack(fd);ack_seconds=now()-astart;wait+=now()-t;bytes+=raw.size();ackbytes+=response.size();if(response!="OK\n")fail("BACKEND_REJECTED");}
 Json progress=Json::obj();progress["static_registry_bytes"]=double(exactBulk::registry().bytes);progress["static_reference_hits"]=double(exactBulk::registry().hits);progress["reuse_hits"]=double(routeAU04::memo().hits);progress["reuse_misses"]=double(routeAU04::memo().misses);progress["reuse_peak_cache_bytes"]=double(routeAU04::memo().peak);progress["reuse_bytes_avoided"]=double(routeAU04::memo().avoided);progress["reuse_identity_seconds"]=routeAU04::memo().identity_seconds;progress["reuse_compute_seconds_avoided"]=routeAU04::memo().saved_seconds;progress["payload_class"]=compact?"compact_scalar_receipt":r.at("metadata").at("stage").string;progress["callback_start_monotonic"]=callback_start;progress["callback_inclusive_seconds"]=now()-callback_start;progress["construct_exclusive_seconds"]=parse-p0;progress["hash_exclusive_seconds"]=hash-h0;progress["serialization_exclusive_seconds"]=dump-d0;progress["send_ACK_inclusive_seconds"]=wait-w0;progress["socket_send_exclusive_seconds"]=send_seconds;progress["ACK_exclusive_seconds"]=ack_seconds;progress["parent_span_id"]=std::to_string(getpid())+":"+std::to_string(count);progress["callbacks_including_constructor"]=int(count);progress["matrices"]=int(mats);progress["bytes_IPC"]=double(bytes);progress["ACK_bytes"]=double(ackbytes);progress["native_parse_construct_seconds"]=parse;progress["native_hash_seconds"]=hash;progress["native_serialization_seconds"]=dump;progress["ACK_wait_inclusive_seconds"]=wait;std::cerr<<progress.dump()<<std::endl;
 }
 if(on){double final_start=now();sendall(fd,bulk?std::string("RAEF4\0\0\0",8):std::string("FINISH\n"));if(ack(fd)!="OK\n")fail("BACKEND_FINISH");Json f=Json::obj();f["phase"]="FINALIZATION";f["inclusive_seconds"]=now()-final_start;std::cerr<<f.dump()<<std::endl;}return 0;
 }catch(const std::exception& e){std::cerr<<"STOP_NATIVE_ADAPTER "<<e.what()<<std::endl;return 2;}}
