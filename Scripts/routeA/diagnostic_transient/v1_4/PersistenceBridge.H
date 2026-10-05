#ifndef ROUTE_A_P1_BRIDGE
#define ROUTE_A_P1_BRIDGE
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cstdlib>
#include <sys/resource.h>
namespace routeAU04 { namespace persistence {
static bool arrivalRequested=false;static int socketFd=-1;static pid_t child=-1;
inline void start(const std::string& root,const std::string& guard,const std::string& src,const std::string& inst){
 const char* script=std::getenv("ROUTE_A_P1_SERVER");const char* expected=std::getenv("ROUTE_A_P1_SERVER_SHA256");
 if(!script||!expected)fail("P1_BACKEND_AUTHORITY_MISSING");
 std::ifstream f(script,std::ios::binary);if(!f)fail("P1_BACKEND_READ");std::string raw((std::istreambuf_iterator<char>(f)),{});if(digest(raw)!=expected)fail("P1_BACKEND_HASH");
 struct rlimit memoryLimit;memoryLimit.rlim_cur=memoryLimit.rlim_max=8ULL*1024*1024*1024;if(::setrlimit(RLIMIT_AS,&memoryLimit)!=0)fail("P1_NATIVE_MEMORY_LIMIT");
 int pair[2];if(::socketpair(AF_UNIX,SOCK_STREAM,0,pair)!=0)fail("P1_SOCKET");child=::fork();if(child<0)fail("P1_FORK");
 if(child==0){::close(pair[0]);std::string fd=std::to_string(pair[1]);::execl("/usr/bin/python3","python3",script,fd.c_str(),root.c_str(),guard.c_str(),src.c_str(),inst.c_str(),static_cast<char*>(nullptr));::_exit(127);}
 ::close(pair[1]);socketFd=pair[0];
}
inline void send(const std::string& raw){
 std::size_t offset=0;while(offset<raw.size()){ssize_t n=::send(socketFd,raw.data()+offset,raw.size()-offset,MSG_NOSIGNAL);if(n<=0)fail("P1_BACKEND_WRITE");offset+=n;}
 std::string ack;char c;while(ack.size()<16){ssize_t n=::recv(socketFd,&c,1,0);if(n<=0)fail("P1_BACKEND_DIED");ack+=c;if(c=='\n')break;}
 arrivalRequested=(ack=="ARRIVED\n");
 if(ack!="OK\n"&&!arrivalRequested)fail("P1_EVALUATOR_OR_EVIDENCE_FAILURE");
}
inline void close(){::close(socketFd);socketFd=-1;int status=0;if(::waitpid(child,&status,0)!=child||!WIFEXITED(status)||WEXITSTATUS(status)!=0)fail("P1_BACKEND_EXIT");}
}}
#endif
