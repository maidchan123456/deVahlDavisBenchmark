// Four manufactured cells in memory; no OpenFOAM case/mesh files generated.
std::unique_ptr<fvMesh> bindingMesh(Time& time){
 pointField pts(18);auto id=[](int x,int y,int z){return z*9+y*3+x;};
 for(int z=0;z<2;++z)for(int y=0;y<3;++y)for(int x=0;x<3;++x)pts[id(x,y,z)]=point(.05*x,.05*y,.001*z);
 std::vector<face> boundary,internal;std::vector<label> bo,io,nei;std::map<std::vector<label>,int> seen;
 std::vector<face> all;std::vector<label> owners;
 auto add=[&](std::initializer_list<label> vs,int c){face f(vs.size());int j=0;std::vector<label> key;for(auto v:vs){f[j++]=v;key.push_back(v);}std::sort(key.begin(),key.end());auto it=seen.find(key);if(it==seen.end()){seen[key]=all.size();all.push_back(f);owners.push_back(c);}else{internal.push_back(all[it->second]);io.push_back(owners[it->second]);nei.push_back(c);owners[it->second]=-1;}};
 for(int y=0;y<2;++y)for(int x=0;x<2;++x){int c=2*y+x;int a=id(x,y,0),b=id(x+1,y,0),d=id(x,y+1,0),e=id(x+1,y+1,0);int A=a+9,B=b+9,D=d+9,E=e+9;
 add({a,A,D,d},c);add({b,e,E,B},c);add({a,b,B,A},c);add({d,D,E,e},c);add({a,d,e,b},c);add({A,B,E,D},c);}
 for(unsigned i=0;i<all.size();++i)if(owners[i]>=0){boundary.push_back(all[i]);bo.push_back(owners[i]);}
 faceList faces(internal.size()+boundary.size());labelList own(faces.size()),neigh(nei.size());
 for(unsigned i=0;i<internal.size();++i){faces[i]=internal[i];own[i]=io[i];neigh[i]=nei[i];}
 for(unsigned i=0;i<boundary.size();++i){faces[internal.size()+i]=boundary[i];own[internal.size()+i]=bo[i];}
 auto mesh=std::unique_ptr<fvMesh>(new fvMesh(IOobject("bindingSynthetic",time.name(),time,IOobject::NO_READ,IOobject::NO_WRITE,false),std::move(pts),std::move(faces),std::move(own),std::move(neigh),false));
 List<polyPatch*> patches(1);patches[0]=new wallPolyPatch("walls",boundary.size(),internal.size(),0,mesh->boundaryMesh(),"wall");mesh->addFvPatches(patches);return mesh;
}
