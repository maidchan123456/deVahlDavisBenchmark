#include "NativeStageObserver.H"
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <cerrno>
#include <cstring>
#include <cstdlib>
#include <algorithm>
#include "PersistenceBridge.H"
#ifndef ROUTE_A_PINNED_SOURCE_SET
#define ROUTE_A_PINNED_SOURCE_SET "UNPINNED"
#endif
#ifndef ROUTE_A_PINNED_INSTRUMENTATION
#define ROUTE_A_PINNED_INSTRUMENTATION "UNPINNED"
#endif
namespace routeAU04 {
namespace {Observer* sink=nullptr;
void atomic(const std::string& path,const std::string& bytes){
 const std::string tmp=path+".partial";
 int fd=::open(tmp.c_str(),O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)fail("EXPORT_OPEN: "+path);
 std::size_t offset=0;while(offset<bytes.size()){ssize_t n=::write(fd,bytes.data()+offset,bytes.size()-offset);if(n<=0){::close(fd);fail("EXPORT_WRITE");}offset+=n;}
 if(::fsync(fd)!=0){::close(fd);fail("EXPORT_FSYNC");}if(::close(fd)!=0)fail("EXPORT_CLOSE");
 // Atomic publish without overwriting an earlier immutable record.
 if(::link(tmp.c_str(),path.c_str())!=0)fail("EXPORT_PUBLISH: "+std::string(std::strerror(errno)));
 if(::unlink(tmp.c_str())!=0)fail("EXPORT_TMP_REMOVE");
 const auto pos=path.find_last_of('/');int d=::open(path.substr(0,pos).c_str(),O_RDONLY|O_DIRECTORY);
 if(d<0||::fsync(d)!=0){if(d>=0)::close(d);fail("EXPORT_DIRECTORY_FSYNC");}::close(d);
}
Json patches(const volScalarField& f,bool flags){Json a=Json::arr();for(const auto& p:f.boundaryField()){
 Json x=Json::obj();x["name"]=std::string(p.patch().name());x["type"]=std::string(p.type());x["values"]=scalars(p);
 if(flags){x["updated"]=p.updated();x["manipulated_matrix"]=p.manipulatedMatrix();}a.push(x);}return a;}
Json scalarValues(const volScalarField& f,bool flags){Json x=Json::obj();x["name"]=std::string(f.name());x["time_index"]=f.timeIndex();x["dimensions"]=dimensions(f.dimensions());x["cells"]=scalars(f.primitiveField());x["patches"]=patches(f,flags);return x;}
Json fieldPacket(const volScalarField& f){Json x=scalarValues(f,true);x["n_old_times"]=f.nOldTimes();x["n_materialized_old_times"]=f.nOldTimes(false);x["has_stored_old_times"]=f.hasStoredOldTimes();
 // OldTimeField::oldTime() can lazily mutate even a const ORIGINAL. Traverse
 // only a private, non-registered deep copy; prevent its automatic rollover.
 // Existing old values/indexes are copied before adjusting private flags.
 volScalarField copy(IOobject(f.name(),f.time().name(),f.mesh(),IOobject::NO_READ,IOobject::NO_WRITE,false),f);
 if(copy.nOldTimes(false)!=f.nOldTimes(false))fail("OLDTIME_COPY_LOST_IDENTITY");
 Json old=Json::arr();const volScalarField* node=&copy;
 for(label i=0;i<std::min(label(2),f.nOldTimes(false));++i){
  const_cast<volScalarField*>(node)->timeIndex()=f.time().timeIndex();
  node=&node->oldTime();Json entry=scalarValues(*node,false);entry["history_level"]=i+1;
  const int represented=f.time().timeIndex()-i-1;
  entry["represented_time_index"]=f.hasStoredOldTimes()&&represented>=0?Json(represented):Json();
  entry["represented_physical_time"]=f.hasStoredOldTimes()&&represented>=0?Json(f.time().value()-f.time().deltaTValue()-(i?f.time().deltaT0Value():0)):Json();
  Json value=Json::obj();for(const std::string key:{"name","dimensions","cells","patches","history_level"})value[key]=entry.at(key);
  entry["value_sha256"]=digest(value.dump());entry["object_epoch_sha256"]=digest(entry.dump());old.push(entry);
 }
 x["old_times"]=old;x["value_sha256"]=digest(x.dump());return x;
}
std::string seqName(int n){std::ostringstream o;o<<std::setw(8)<<std::setfill('0')<<n<<".json";return o.str();}
}
Json dimensions(const dimensionSet& d){Json a=Json::arr();for(int i=0;i<7;++i)a.push(double(d[i]));return a;}
Json scalars(const scalarField& f){Json a=Json::arr();for(scalar v:f)a.push(v);return a;}
Json labels(const labelUList& f){Json a=Json::arr();for(label v:f)a.push(int(v));return a;}
Json scalarState(const volScalarField& f){return fieldPacket(f);}
Json matrixPacket(const fvScalarMatrix& live){
 // Native boundary coefficient accessors are mutable-only: use private copy.
 fvScalarMatrix m(live);Json x=Json::obj();x["dimensions"]=dimensions(live.dimensions());x["psi_name"]=std::string(live.psi().name());
 x["has_diag"]=live.hasDiag();x["diag"]=scalars(m.diag());x["source"]=scalars(m.source());x["has_upper"]=m.hasUpper();x["has_lower"]=m.hasLower();
 const fvScalarMatrix& cm=m;
 x["upper"]=m.diagonal()?Json::arr():scalars(cm.upper());x["lower"]=m.diagonal()?Json::arr():scalars(cm.lower());
 x["owner"]=labels(m.lduAddr().lowerAddr());x["neighbour"]=labels(m.lduAddr().upperAddr());
 Json b=Json::arr();for(label i=0;i<m.internalCoeffs().size();++i){
  if(live.psi().boundaryField()[i].coupled())fail("COUPLED_PATCH_NOT_REGISTERED");
  Json p=Json::obj();p["name"]=std::string(live.psi().mesh().boundary()[i].name());p["type"]=std::string(live.psi().boundaryField()[i].type());p["face_cells"]=labels(live.psi().mesh().boundary()[i].faceCells());p["internal_coeffs"]=scalars(m.internalCoeffs()[i]);p["boundary_coeffs"]=scalars(m.boundaryCoeffs()[i]);p["updated"]=live.psi().boundaryField()[i].updated();p["manipulated_matrix"]=live.psi().boundaryField()[i].manipulatedMatrix();b.push(p);
 }
 x["patches"]=b;x["matrix_epoch"]=digest(x.dump());x["psi"]=fieldPacket(live.psi());x["volumes"]=scalars(live.psi().mesh().V().primitiveField());
 routeADiagnostic::StageId id{live.psi().time().timeIndex(),0,0,0,live.psi().time().value(),live.psi().time().deltaTValue(),live.psi().time().deltaT0Value(),"native_capture",{x.at("psi").at("value_sha256").string}};
 routeADiagnostic::ScalarMatrixSnapshot snap(m,id,live.dimensions());x["native_lhs_minus_rhs"]=scalars(snap.lhsMinusRhs());x["arithmetic_bound"]=snap.matrixActionRoundoffBound();return x;
}
Json meshState(const fvMesh& mesh){Json state=Json::obj();
 for(const word& name:wordList({"rho","rhoFluidThermo:rho","T","e","K","p","p_rgh","gh"}))if(mesh.foundObject<volScalarField>(name))state[std::string(name)]=fieldPacket(mesh.lookupObject<volScalarField>(name));
 if(mesh.foundObject<volVectorField>("U")){const auto& f=mesh.lookupObject<volVectorField>("U");Json u=Json::obj(),a=Json::arr();for(const vector& v:f.primitiveField()){Json xyz=Json::arr();for(int k=0;k<3;++k)xyz.push(v[k]);a.push(xyz);}u["cells"]=a;u["time_index"]=f.timeIndex();u["dimensions"]=dimensions(f.dimensions());Json b=Json::arr();for(const auto& patch:f.boundaryField()){Json p=Json::obj(),vals=Json::arr();p["name"]=std::string(patch.patch().name());p["updated"]=patch.updated();p["manipulated_matrix"]=patch.manipulatedMatrix();for(const vector& v:patch){Json xyz=Json::arr();for(int k=0;k<3;++k)xyz.push(v[k]);vals.push(xyz);}p["values"]=vals;b.push(p);}u["patches"]=b;u["value_sha256"]=digest(u.dump());state["U"]=u;}
 if(mesh.foundObject<surfaceScalarField>("phi")){const auto& f=mesh.lookupObject<surfaceScalarField>("phi");Json phi=Json::obj();phi["dimensions"]=dimensions(f.dimensions());phi["internal"]=scalars(f.primitiveField());Json b=Json::arr();for(const auto& patch:f.boundaryField()){Json p=Json::obj();p["name"]=std::string(patch.patch().name());p["values"]=scalars(patch);p["face_cells"]=labels(patch.patch().faceCells());b.push(p);}phi["patches"]=b;phi["value_sha256"]=digest(phi.dump());state["phi"]=phi;}
 Json geometry=Json::obj();geometry["owner"]=labels(mesh.lduAddr().lowerAddr());geometry["neighbour"]=labels(mesh.lduAddr().upperAddr());geometry["linear_weights"]=scalars(mesh.weights().primitiveField());state["geometry"]=geometry;
 state["volumes"]=scalars(mesh.V().primitiveField());state["state_epoch"]=digest(state.dump());return state;
}
Observer::Observer(const std::string& path,const std::string& guard,const std::string& src,const std::string& inst,const std::string& id,const std::string& kind):root(path),studyGuard(guard),sourceHash(src),instrumentHash(inst),caseId(id),classification(kind){
 if(guard.size()!=64||src.size()!=64||inst.size()!=64)fail("GUARD_HASH_FORMAT");
 if(src!=ROUTE_A_PINNED_SOURCE_SET||inst!=ROUTE_A_PINNED_INSTRUMENTATION)fail("SOURCE_OR_INSTRUMENTATION_HASH_MISMATCH");
 if(kind!="SYNTHETIC_EVALUATOR_TEST"&&kind!="DIAGNOSTIC_OBSERVATION")fail("WRONG_CLASSIFICATION");
 if(::mkdir(root.c_str(),0700)!=0)fail("EXPORT_ROOT_MUST_BE_NEW");
 persistence::start(root,guard,src,inst);
}
Observer::~Observer(){if(sink==this)sink=nullptr;}
Json Observer::metadata(const std::string& name,const fvMesh& mesh)const{
 Json m=Json::obj();m["schema"]="routeA_native_stage/1.2";m["study_guard_sha256"]=studyGuard;m["source_set_sha256"]=sourceHash;m["instrumentation_sha256"]=instrumentHash;m["case_identity"]=caseId;m["classification"]=classification;m["not_cfd_result"]=(classification=="SYNTHETIC_EVALUATOR_TEST");m["not_diagnostic_transient_execution"]=(classification=="SYNTHETIC_EVALUATOR_TEST");m["time_index"]=mesh.time().timeIndex();m["physical_time"]=mesh.time().value();m["deltaT"]=mesh.time().deltaTValue();m["previous_deltaT"]=mesh.time().deltaT0Value();m["outer"]=outer;m["pressure"]=pressure;m["nonOrthogonal"]=nonOrthogonal;m["energy_solve"]=energySolve;m["rho_solve"]=rhoSolve;m["stage"]=name;return m;
}
void Observer::transition(const std::string& name,const Json& payload){
 if(name=="auxiliary_fixture"&&phase=="time_end")return;
 if(name=="term_capture"){
  if(phase!="energy_begin"&&phase!="before_correctDensity")fail("TERM_OUTSIDE_ASSEMBLY");
  const auto term=payload.at("term").string;
  if(std::find(capturedTerms.begin(),capturedTerms.end(),term)!=capturedTerms.end())fail("DUPLICATE_TERM_EPOCH");
  capturedTerms.push_back(term);return;
 }
 if(name=="energy_unrelaxed_assembly"||name=="mass_unrelaxed_assembly"){
  std::vector<std::string> required=name=="energy_unrelaxed_assembly"?
   std::vector<std::string>{"S_e","S_K","F_e","F_K","W_p","H_out","Fourier_laplacian","Fourier_correction","W_g","S_models"}:
   std::vector<std::string>{"D_B_rho","div_phi","mass_models"};
  std::sort(required.begin(),required.end());std::sort(capturedTerms.begin(),capturedTerms.end());
  if(required!=capturedTerms)fail("SINGLE_ASSEMBLY_TERMS_MISSING");
 }
 bool ok=false;
 if(phase=="initial")ok=name=="constructor_complete";
 else if(phase=="constructor_complete"||phase=="time_end")ok=name=="preSolve_before";
 else if(phase=="preSolve_before")ok=name=="preSolve_after";
 else if(phase=="preSolve_after")ok=name=="controller_complete";
 else if(phase=="controller_complete")ok=name=="time_start";
 else if(phase=="time_start")ok=name=="outer_start"&&outer==1;
 else if(phase=="outer_start")ok=name==(outer==1?"before_correctDensity":"density_predictor_complete");
 else if(phase=="before_correctDensity")ok=name=="mass_unrelaxed_assembly";
 else if(phase=="mass_unrelaxed_assembly")ok=name=="mass_after_solve";
 else if(phase=="mass_after_solve")ok=name=="after_correctDensity";
 else if(phase=="after_correctDensity")ok=name==(pressure==0?"density_predictor_complete":"native_continuity_report");
 else if(phase=="density_predictor_complete")ok=name=="energy_begin";
 else if(phase=="energy_begin")ok=name=="energy_unrelaxed_assembly";
 else if(phase=="energy_unrelaxed_assembly")ok=name=="energy_after_relax";
 else if(phase=="energy_after_relax")ok=name=="energy_after_solve";
 else if(phase=="energy_after_solve")ok=name=="before_thermo_correct";
 else if(phase=="before_thermo_correct")ok=name=="after_thermo_correct";
 else if(phase=="after_thermo_correct")ok=name=="pressure_start"&&pressure==1;
 else if(phase=="pressure_start")ok=name=="before_pressure_EOS_copy";
 else if(phase=="before_pressure_EOS_copy")ok=name=="after_pressure_EOS_copy";
 else if(phase=="after_pressure_EOS_copy")ok=name=="pressure_pre_reference"&&nonOrthogonal==1;
 else if(phase=="pressure_pre_reference")ok=name=="pressure_post_reference";
 else if(phase=="pressure_post_reference")ok=name=="pressure_solved";
 else if(phase=="pressure_solved")ok=name=="before_correctDensity";
 else if(phase=="native_continuity_report")ok=(name=="pressure_start"&&pressure==2)||(name=="outer_end"&&pressure==2);
 else if(phase=="outer_end")ok=(name=="outer_start"&&outer<=24)||(name=="before_postSolve"&&outer==24);
 else if(phase=="before_postSolve")ok=name=="before_postSolve_EOS_copy";
 else if(phase=="before_postSolve_EOS_copy")ok=name=="after_postSolve_EOS_copy";
 else if(phase=="after_postSolve_EOS_copy")ok=name=="after_postSolve";
 else if(phase=="after_postSolve")ok=name=="time_end"&&rhoSolve==49&&energySolve==24;
 if(!ok)fail("EVALUATOR_STAGE_IDENTITY_FAILURE: "+phase+" -> "+name);
 if(name=="energy_begin"||name=="before_correctDensity")capturedTerms.clear();phase=name;
}
void Observer::emit(const std::string& name,const fvMesh& mesh,Json payload){
 if(completed)fail("EXPORT_AFTER_FINISH");
 payload["native_state_epoch"]=meshState(mesh);
 payload["thermal_context"]=thermalContext;
 transition(name,payload);Json record=Json::obj();Json meta=metadata(name,mesh);
 Json fields=Json::obj(),olds=Json::obj(),bc=Json::obj(),matrixEpochs=Json::obj();
 for(const auto& kv:payload.at("native_state_epoch").object){
  if(kv.second.kind==Json::Object&&kv.second.object.count("value_sha256"))fields[kv.first]=kv.second.at("value_sha256");
  if(kv.second.kind==Json::Object&&kv.second.object.count("old_times")){Json ids=Json::arr();for(const auto& old:kv.second.at("old_times").array){Json id=Json::obj();id["object_name"]=old.at("name");id["time_index"]=old.at("time_index");id["value_sha256"]=old.at("value_sha256");id["object_epoch_sha256"]=old.at("object_epoch_sha256");id["history_level"]=old.at("history_level");id["represented_time_index"]=old.at("represented_time_index");ids.push(id);}olds[kv.first]=ids;}
  if(kv.second.kind==Json::Object&&kv.second.object.count("patches"))bc[kv.first]=digest(kv.second.at("patches").dump());
 }
 for(const auto& kv:payload.object)if(kv.second.kind==Json::Object&&kv.second.object.count("matrix_epoch"))matrixEpochs[kv.first]=kv.second.at("matrix_epoch");
 meta["field_epochs"]=fields;meta["oldTime_ids"]=olds;meta["bc_epochs"]=bc;meta["matrix_epochs"]=matrixEpochs;
 record["metadata"]=meta;record["payload"]=payload;record["payload_sha256"]=digest(payload.dump());record["sequence"]=++sequence;
 persistence::send(record.dump()+"\n");
}
void Observer::stage(const std::string& name,const fvMesh& mesh){
 if(name=="time_start"){outer=pressure=nonOrthogonal=energySolve=rhoSolve=0;if(mesh.time().timeIndex()<=lastTime)fail("TIME_INDEX_NOT_ADVANCING");lastTime=mesh.time().timeIndex();}
 if(name=="outer_start"){++outer;pressure=nonOrthogonal=0;activeEquation.clear();matrices.clear();explicitTerms.clear();matrixPayloads.clear();}
 if(name=="pressure_start"){++pressure;nonOrthogonal=0;}
 if(name=="pressure_pre_reference")++nonOrthogonal;
 if(name=="before_correctDensity"){++rhoSolve;activeEquation="mass";matrices.clear();explicitTerms.clear();matrixPayloads.clear();}
 if(name=="energy_begin"){++energySolve;activeEquation="energy";matrices.clear();explicitTerms.clear();matrixPayloads.clear();}
 emit(name,mesh,meshState(mesh));
}
void Observer::term(const std::string& name,const fvScalarMatrix& m){
 const auto expected=(name=="D_B_rho"||name=="mass_models")?dimMass/dimTime:dimPower;
 if(m.dimensions()!=expected)fail("TERM_DIMENSION_FAILURE");
 if(matrices.count(name)||explicitTerms.count(name))fail("DUPLICATE_TERM");
 routeADiagnostic::StageId id{m.psi().time().timeIndex(),outer,pressure,energySolve,m.psi().time().value(),m.psi().time().deltaTValue(),m.psi().time().deltaT0Value(),"term",{scalarState(m.psi()).at("value_sha256").string}};
 fvScalarMatrix normalized(m);normalized.diag();
 matrices[name].reset(new routeADiagnostic::ScalarMatrixSnapshot(normalized,id,m.dimensions()));
 if(name=="S_models"||name=="mass_models"){const auto action=matrices.at(name)->lhsMinusRhs();if(gMax(mag(action))!=0||gMax(mag(normalized.diag()))!=0||gMax(mag(normalized.source()))!=0)fail("WRONG_MODEL_NONZERO_SOURCE");}
 Json x=Json::obj();x["term"]=name;x["matrix"]=matrixPacket(m);matrixPayloads[name]=x.at("matrix");emit("term_capture",m.psi().mesh(),x);
}
void Observer::term(const std::string& name,const volScalarField& f){
 const auto expected=name=="div_phi"?dimMass/dimTime:dimPower;
 if(f.dimensions()*dimVolume!=expected)fail("TERM_DIMENSION_FAILURE");
 if(matrices.count(name)||explicitTerms.count(name))fail("DUPLICATE_TERM");Json x=Json::obj();x["term"]=name;x["dimensions"]=dimensions(f.dimensions()*dimVolume);x["integrated_cells"]=scalars(f.primitiveField()*f.mesh().V().primitiveField());x["operator_dimensions"]=dimensions(f.dimensions());if(historyCounts.count(name)){x["pre_operator_n_old_times"]=historyCounts.at(name);x["effective_previous_deltaT"]=historyCounts.at(name)<2?double(Foam::great):f.time().deltaT0Value();}explicitTerms[name]=x;emit("term_capture",f.mesh(),x);
}
void Observer::term(const std::string& name,const volScalarField::Internal& f){
 const auto expected=name=="div_phi"?dimMass/dimTime:dimPower;
 if(f.dimensions()*dimVolume!=expected)fail("TERM_DIMENSION_FAILURE");
 if(matrices.count(name)||explicitTerms.count(name))fail("DUPLICATE_TERM");Json x=Json::obj();x["term"]=name;x["dimensions"]=dimensions(f.dimensions()*dimVolume);x["integrated_cells"]=scalars(static_cast<const scalarField&>(f)*f.mesh().V().primitiveField());x["operator_dimensions"]=dimensions(f.dimensions());if(historyCounts.count(name)){x["pre_operator_n_old_times"]=historyCounts.at(name);x["effective_previous_deltaT"]=historyCounts.at(name)<2?double(Foam::great):f.mesh().time().deltaT0Value();}explicitTerms[name]=x;emit("term_capture",f.mesh(),x);
}
void Observer::total(const std::string& name,const fvScalarMatrix& m){
 if(name=="mass_unrelaxed_assembly"){activeEquation="mass";}
 Json x=Json::obj();x["matrix"]=matrixPacket(m);x["state"]=meshState(m.psi().mesh());emit(name,m.psi().mesh(),x);
 routeADiagnostic::StageId id{m.psi().time().timeIndex(),outer,pressure,energySolve,m.psi().time().value(),m.psi().time().deltaTValue(),m.psi().time().deltaT0Value(),name,{x.at("matrix").at("matrix_epoch").string}};
 if(name.find("after_relax")==std::string::npos){matrices["__total"].reset(new routeADiagnostic::ScalarMatrixSnapshot(m,id,m.dimensions()));matrixPayloads["__total"]=x.at("matrix");}
 else if(x.at("matrix").at("matrix_epoch").string!=matrixPayloads.at("__total").at("matrix_epoch").string)fail("NO_RELAX_MATRIX_OR_BC_EPOCH_CHANGED");
}
namespace {Json frozenEvaluation(Json packet,routeADiagnostic::ScalarMatrixSnapshot& snap){
 packet["psi"]=scalarState(snap.coefficients().psi());
 packet["native_lhs_minus_rhs"]=scalars(snap.lhsMinusRhs());
 packet["arithmetic_bound"]=snap.matrixActionRoundoffBound();
 packet["evaluation_field_epoch"]=packet.at("psi").at("value_sha256");
 return packet;
}}
void Observer::solved(const std::string& name,const fvScalarMatrix& m){
 if(!matrices.count("__total"))fail("MISSING_ASSEMBLY");Json x=Json::obj();x["current_matrix"]=matrixPacket(m);x["unrelaxed_matrix"]=frozenEvaluation(matrixPayloads.at("__total"),*matrices.at("__total"));Json terms=Json::obj();
 for(const auto& kv:matrices)if(kv.first!="__total")terms[kv.first]=scalars(kv.second->lhsMinusRhs());
 for(const auto& kv:explicitTerms)terms[kv.first]=kv.second.at("integrated_cells");x["term_actions"]=terms;x["state"]=meshState(m.psi().mesh());emit(name,m.psi().mesh(),x);
 matrices.clear();explicitTerms.clear();matrixPayloads.clear();activeEquation.clear();
}
void Observer::finish(){if(phase!="time_end")fail("INCOMPLETE_STAGE_SEQUENCE");if(completed)fail("DUPLICATE_FINISH");persistence::send("FINISH\n");persistence::close();completed=true;}
Observer* current(){return sink;}
void install(Observer* o){if(sink&&o&&sink!=o)fail("SECOND_OBSERVER");sink=o;}
void stage(const char* n,const fvMesh& mesh){if(sink)sink->stage(n,mesh);}
void total(const char* n,const fvScalarMatrix& m){if(sink)sink->total(n,m);}
void solved(const char* n,const fvScalarMatrix& m){if(sink)sink->solved(n,m);}
void reference(const char* n,const fvScalarMatrix& m,label cell,scalar value){if(sink){
 const std::string name(n);if(name=="pressure_pre_reference")++sink->nonOrthogonal;
 Json x=Json::obj();x["matrix"]=matrixPacket(m);x["ref_cell"]=cell;x["ref_value"]=value;
 if(name=="pressure_pre_reference"||name=="pressure_post_reference"){
 routeADiagnostic::StageId id{m.psi().time().timeIndex(),sink->outer,sink->pressure,sink->energySolve,m.psi().time().value(),m.psi().time().deltaTValue(),m.psi().time().deltaT0Value(),name,{x.at("matrix").at("matrix_epoch").string}};
 sink->matrices[name].reset(new routeADiagnostic::ScalarMatrixSnapshot(m,id,m.dimensions()));sink->matrixPayloads[name]=x.at("matrix");
 }
 if(name=="pressure_solved"){
  if(!sink->matrices.count("pressure_pre_reference")||!sink->matrices.count("pressure_post_reference"))fail("PRESSURE_EPOCH_MISSING");
  x["physical_matrix"]=frozenEvaluation(sink->matrixPayloads.at("pressure_pre_reference"),*sink->matrices.at("pressure_pre_reference"));
  x["referenced_matrix"]=frozenEvaluation(sink->matrixPayloads.at("pressure_post_reference"),*sink->matrices.at("pressure_post_reference"));
 }
 sink->emit(name,m.psi().mesh(),x);
}}
void history(const char* name,const volScalarField& f){if(sink)sink->historyCounts[name]=f.nOldTimes();}
void thermal(const volScalarField::Internal& cv,const dimensionedVector& g){if(sink){Json j=Json::obj();j["Cv"]=scalars(static_cast<const scalarField&>(cv));j["Cv_dimensions"]=dimensions(cv.dimensions());Json xyz=Json::arr();for(int i=0;i<3;++i)xyz.push(g.value()[i]);j["g"]=xyz;j["g_dimensions"]=dimensions(g.dimensions());sink->thermalContext=j;}}
void bootstrap(const fvMesh& mesh){
 if(sink){stage("constructor_complete",mesh);return;}
 const char *path=std::getenv("ROUTE_A_DIAGNOSTIC_EXPORT_ROOT"),*guard=std::getenv("ROUTE_A_DIAGNOSTIC_GUARD_SHA256"),*src=std::getenv("ROUTE_A_DIAGNOSTIC_SOURCE_SHA256"),*inst=std::getenv("ROUTE_A_DIAGNOSTIC_INSTRUMENTATION_SHA256"),*id=std::getenv("ROUTE_A_DIAGNOSTIC_CASE_ID");
 const char* authority=std::getenv("ROUTE_A_DIAGNOSTIC_CONTRACT_FILE");
 if(!path||!guard||!src||!inst||!id||!authority)fail("DIAGNOSTIC_BOOTSTRAP_AUTHORITY_MISSING");
 std::ifstream contract(authority,std::ios::binary);if(!contract)fail("CONTRACT_READ");std::string raw((std::istreambuf_iterator<char>(contract)),{});if(digest(raw)!=guard)fail("CONTRACT_GUARD_MISMATCH");
 static std::unique_ptr<Observer> owned;owned.reset(new Observer(path,guard,src,inst,id,"DIAGNOSTIC_OBSERVATION"));install(owned.get());stage("constructor_complete",mesh);
}
}
