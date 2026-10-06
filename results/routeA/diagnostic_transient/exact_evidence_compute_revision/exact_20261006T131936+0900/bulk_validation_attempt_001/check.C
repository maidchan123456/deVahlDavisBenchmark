#define main frozen_main
#include "/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/compute_revision_v4/measurement/native_adapter.C"
#undef main
int main(int argc,char**argv){try{std::string line;while(std::getline(std::cin,line)){Json j=Parser{line}.parse();if(std::string(argv[1])=="JSON")std::cout<<j.dump()<<"\n";else{std::string raw=exactBulk::encode(j,std::string(argv[1])=="STATIC");std::cout.write(raw.data(),raw.size());}}return 0;}catch(const std::exception&e){std::cerr<<e.what();return 2;}}
