// Read registered residual objects only: never DemandDriven::New on a missing object.
Json liveBinding(const fvMesh& mesh,const std::string& stage){
 Json c=Json::obj(),linear=Json::arr();
 std::string field;
 if(stage=="energy_after_solve")field="e";
 if(stage=="mass_after_solve")field="rho";
 if(stage=="pressure_solved")field="p_rgh";
 if(!field.empty() && mesh.foundObject<Residuals<scalar>>(Residuals<scalar>::typeName)){
  const auto& r=mesh.lookupObject<Residuals<scalar>>(Residuals<scalar>::typeName);
  if(static_cast<const HashTable<DynamicList<SolverPerformance<scalar>>>&>(r).found(field)){const auto& list=r[field];if(!list.empty()){
   const auto& p=list.last();Json x=Json::obj();x["field"]=field;x["initial"]=p.initialResidual();x["final"]=p.finalResidual();x["iterations"]=p.nIterations();x["solver"]=std::string(p.solverName());x["native_count"]=list.size();linear.push(x);
  }}
 }
 if(stage=="energy_begin" && mesh.foundObject<Residuals<vector>>(Residuals<vector>::typeName)){
  const auto& r=mesh.lookupObject<Residuals<vector>>(Residuals<vector>::typeName);
  if(static_cast<const HashTable<DynamicList<SolverPerformance<vector>>>&>(r).found("U")){const auto& list=r["U"];if(!list.empty()){
   const auto& p=list.last();for(int k=0;k<2;++k){Json x=Json::obj();x["field"]=k==0?"Ux":"Uy";x["initial"]=p.initialResidual()[k];x["final"]=p.finalResidual()[k];x["iterations"]=int(p.nIterations()[k]);x["solver"]=std::string(p.solverName());x["native_count"]=list.size();linear.push(x);}
  }}
 }
 c["linear"]=linear;
 if(stage=="constructor_complete"){
  Json xyz=Json::arr();for(const vector& v:mesh.C().primitiveField()){Json a=Json::arr();for(int k=0;k<3;++k)a.push(v[k]);xyz.push(a);}c["centres"]=xyz;
  Json sf=Json::arr();for(const vector& v:mesh.Sf().primitiveField()){Json a=Json::arr();for(int k=0;k<3;++k)a.push(v[k]);sf.push(a);}c["Sf"]=sf;
  Json patches=Json::arr();for(const auto& patch:mesh.boundary()){
   Json x=Json::obj(),faces=Json::arr();x["name"]=std::string(patch.name());x["face_cells"]=labels(patch.faceCells());x["delta"]=scalars(patch.deltaCoeffs());
   for(const vector& v:patch.Sf()){Json a=Json::arr();for(int k=0;k<3;++k)a.push(v[k]);faces.push(a);}x["Sf"]=faces;patches.push(x);
  }c["patch_geometry"]=patches;
  c["target_Co"]=mesh.time().controlDict().lookupOrDefault<scalar>("maxCo",0.5);
  c["maxDeltaT"]=mesh.time().controlDict().lookupOrDefault<scalar>("maxDeltaT",710.0/25600);
  c["adjustTimeStep"]=mesh.time().controlDict().lookupOrDefault<bool>("adjustTimeStep",false);
 }
 return c;
}
