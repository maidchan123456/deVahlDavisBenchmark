// SYNTHETIC_EVALUATOR_TEST / NOT_CFD_RESULT / NOT_DIAGNOSTIC_TRANSIENT_EXECUTION.
// Reuse existing v1.1 mesh/operator fixtures; never create or write a CFD case.
#define main routeA_existing_unit_main
#include "../v1_1/TestNativeMatrixObserver.C"
#undef main
#include "NativeStageObserver.H"
#include <chrono>
using routeAU04::Json;

Json performance(const SolverPerformance<scalar>& p){Json j=Json::obj();j["initial_residual"]=p.initialResidual();j["final_residual"]=p.finalResidual();j["iterations"]=p.nIterations();return j;}
Json physicalFingerprint(const Time& t,const std::vector<const volScalarField*>& fields,const std::vector<const fvScalarMatrix*>& matrices,const std::vector<Json>& solves){
 Json j=Json::obj();j["time"]=t.value();j["time_index"]=t.timeIndex();j["dt"]=t.deltaTValue();j["previous_dt"]=t.deltaT0Value();Json f=Json::obj();
 for(auto p:fields)f[std::string(p->name())]=routeAU04::scalarState(*p);j["fields"]=f;Json m=Json::arr();for(auto p:matrices)m.push(routeAU04::matrixPacket(*p));j["matrices"]=m;Json s=Json::arr();for(auto x:solves)s.push(x);j["solves"]=s;if(!fields.empty())j["native_mesh_state"]=routeAU04::meshState(fields.front()->mesh());return j;
}
void run(const std::string& root,const std::string& guard,const std::string& src,const std::string& inst,bool observed,const std::string& inject){
 Time t(fileName("/tmp"),fileName("routeA-u04-in-memory-no-case"),false);t.setDeltaT(.2);++t;
 auto mp=memoryMesh(t,2);fvMesh& mesh=*mp;
 auto io=[&](const word& n){return IOobject(n,t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE);};
 volScalarField rho(io("rho"),mesh,dimensionedScalar("rho",dimDensity,1),"zeroGradient");
 volScalarField rhoT(io("rhoFluidThermo:rho"),mesh,dimensionedScalar("rhoT",dimDensity,1),"zeroGradient");
 volScalarField e(io("e"),mesh,dimensionedScalar("e",dimEnergy/dimMass,6),"fixedValue");
 volScalarField T(io("T"),mesh,dimensionedScalar("T",dimTemperature,3),"fixedValue");
 volScalarField K(io("K"),mesh,dimensionedScalar("K",dimEnergy/dimMass,.002),"zeroGradient");
 volScalarField p(io("p"),mesh,dimensionedScalar("p",dimPressure,2),"zeroGradient");
 volScalarField prgh(io("p_rgh"),mesh,dimensionedScalar("p",dimPressure,0),"zeroGradient");
 volScalarField gh(io("gh"),mesh,dimensionedScalar("gh",dimEnergy/dimMass,-.01),"zeroGradient");
 volVectorField U(io("U"),mesh,dimensionedVector("U",dimVelocity,vector(0,.02,0)),"zeroGradient");
 surfaceScalarField phi(io("phi"),mesh,dimensionedScalar("phi",dimMass/dimTime,0));
 surfaceScalarField kappa(io("kappa"),mesh,dimensionedScalar("k",dimPower/dimLength/dimTemperature,1));
 const dimensionedScalar Cv("Cv",dimEnergy/dimMass/dimTemperature,2);
 const dimensionedVector g("g",dimAcceleration,vector(0,-.03,0));
 for(volScalarField* f:{&rho,&e,&K}){
  f->oldTimeRef();f->oldTimeRef().oldTimeRef();
  f->oldTimeRef().timeIndex()=0;f->oldTimeRef().oldTimeRef().timeIndex()=-1;
 }
 rho.oldTimeRef().primitiveFieldRef()=inject=="stationary"?1:.9;rho.oldTimeRef().oldTimeRef().primitiveFieldRef()=inject=="stationary"?1:.8;
 e.oldTimeRef().primitiveFieldRef()=5.5;e.oldTimeRef().oldTimeRef().primitiveFieldRef()=5.1;
 K.oldTimeRef().primitiveFieldRef()=.001;K.oldTimeRef().oldTimeRef().primitiveFieldRef()=.0005;
 e.boundaryFieldRef()[0]==scalarField(e.boundaryField()[0].size(),6);
 e.boundaryFieldRef()[0][0]=2;e.boundaryFieldRef()[0][1]=8;
 T=e/Cv;rho.correctBoundaryConditions();e.correctBoundaryConditions();K.correctBoundaryConditions();
 std::unique_ptr<routeAU04::Observer> observer;
 if(observed){observer.reset(new routeAU04::Observer(root,guard,src,inst,"SYNTHETIC_IN_MEMORY", "SYNTHETIC_EVALUATOR_TEST"));routeAU04::install(observer.get());}
 if(observed)routeAU04::bootstrap(mesh); // OFF performs no exporter/bootstrap.
 routeAU04::stage("preSolve_before",mesh);routeAU04::stage("preSolve_after",mesh);
 t.setDeltaT(.1);routeAU04::stage("controller_complete",mesh);++t;
 rho.primitiveFieldRef()=inject=="stationary"?1:1.03;e.primitiveFieldRef()[0]=6.1;e.primitiveFieldRef()[1]=6.3;K.primitiveFieldRef()=.0021;
 routeAU04::stage("time_start",mesh);
 if(inject=="missing")routeAU04::stage("density_predictor_complete",mesh);
 if(inject=="duplicate"){routeAU04::stage("outer_start",mesh);routeAU04::stage("outer_start",mesh);}
 if(inject=="nan"){rho.primitiveFieldRef()[0]=std::numeric_limits<double>::quiet_NaN();routeAU04::stage("outer_start",mesh);}
 if(inject=="wrongdimensions"){
  routeAU04::stage("outer_start",mesh);routeAU04::stage("before_correctDensity",mesh);fvScalarMatrix wrong(e,dimPower);routeAU04::tap("D_B_rho",tmp<fvScalarMatrix>(new fvScalarMatrix(wrong)));
 }
 fv::backwardDdtScheme<scalar> backward(mesh);
 fv::gaussConvectionScheme<scalar> conv(mesh,phi,tmp<surfaceInterpolationScheme<scalar>>(new linear<scalar>(mesh)));
 fv::gaussLaplacianScheme<scalar,scalar> lap(mesh,tmp<surfaceInterpolationScheme<scalar>>(new linear<scalar>(mesh)),tmp<fv::snGradScheme<scalar>>(new fv::orthogonalSnGrad<scalar>(mesh)));
 dictionary energyControls(IStringStream("solver PBiCGStab; preconditioner DILU; tolerance 1e-12; relTol 0; maxIter 2000;")());
 dictionary pressureControls(IStringStream("solver PCG; preconditioner DIC; tolerance 1e-12; relTol 0; maxIter 4000;")());
 dictionary densityControls(IStringStream("solver diagonal; tolerance 1e-14; relTol 0; maxIter 1;")());
 std::vector<Json> solves;Json fingerprints=Json::arr();
 auto density=[&]{
  routeAU04::stage("before_correctDensity",mesh);
  auto d=routeAU04::tap("D_B_rho",backward.fvmDdt(rho));
  auto f=routeAU04::tap("div_phi",fvc::div(phi));
  auto source=routeAU04::tap("mass_models",tmp<fvScalarMatrix>(new fvScalarMatrix(rho,dimMass/dimTime)));
  fvScalarMatrix eqn(d()+f()==source());
  routeAU04::total("mass_unrelaxed_assembly",eqn);
  const auto perf=eqn.solve(densityControls);solves.push_back(performance(perf));
  routeAU04::solved("mass_after_solve",eqn);routeAU04::stage("after_correctDensity",mesh);
  fingerprints.push(physicalFingerprint(t,{&rho,&e,&K},{&eqn},solves));
 };
 // Every field/flux update below is part of the manufactured driver, identical
 // with observation OFF/ON. The observer itself performs no update/solve.
 for(int outer=1;outer<=24;++outer){
  routeAU04::stage("outer_start",mesh);if(outer==1)density();
  routeAU04::stage("density_predictor_complete",mesh);
  routeAU04::stage("energy_begin",mesh);
  volScalarField cvField(IOobject("fixtureCv",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,Cv);routeAU04::thermal(cvField(),g);routeAU04::history("S_K",K);
  auto se=routeAU04::tap("S_e",backward.fvmDdt(rho,e));
  auto fe=routeAU04::tap("F_e",conv.fvmDiv(phi,e));
  auto sk=routeAU04::tap("S_K",backward.fvcDdt(rho,K));
  auto fk=routeAU04::tap("F_K",conv.fvcDiv(phi,K));
  volScalarField specific(IOobject("specific_pressure",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),p/rho);
  auto wp=routeAU04::tap("W_p",conv.fvcDiv(phi,specific));
  auto fourierExplicit=routeAU04::tap("Fourier_laplacian",lap.fvcLaplacian(kappa,T));
  auto fourierCorrection=routeAU04::tap("Fourier_correction",fvm::laplacianCorrection(kappa/Cv,e));
  auto heat=routeAU04::tap("H_out",-fourierExplicit()-fourierCorrection());
  auto work=routeAU04::tap("W_g",rho*(U&g));
  auto models=routeAU04::tap("S_models",tmp<fvScalarMatrix>(new fvScalarMatrix(e,dimPower)));
  fvScalarMatrix eqn(se()+fe()+sk()+fk()+wp()+heat()==models()+work());
  routeAU04::total("energy_unrelaxed_assembly",eqn);
  const std::string beforeNoop=routeAU04::digest(routeAU04::matrixPacket(eqn).dump());
  eqn.relax(0); // exact registered native no-op; no dictionary/case needed
  if(routeAU04::digest(routeAU04::matrixPacket(eqn).dump())!=beforeNoop)routeAU04::fail("NO_RELAX_MATRIX_CHANGED");
  routeAU04::total("energy_after_relax",eqn);
  const auto perf=eqn.solve(energyControls);solves.push_back(performance(perf));
  routeAU04::solved("energy_after_solve",eqn);
  fingerprints.push(physicalFingerprint(t,{&rho,&e,&K},{&eqn},solves));
  routeAU04::stage("before_thermo_correct",mesh);
  T=e/Cv;rhoT=dimensionedScalar("one",dimDensity,1)*(scalar(1)-dimensionedScalar("beta",dimless/dimTemperature,.001)*(T-dimensionedScalar("T0",dimTemperature,3)));
  routeAU04::stage("after_thermo_correct",mesh);
  for(int pressure=1;pressure<=2;++pressure){
   routeAU04::stage("pressure_start",mesh);routeAU04::stage("before_pressure_EOS_copy",mesh);rho=rhoT;routeAU04::stage("after_pressure_EOS_copy",mesh);
   fvScalarMatrix pressureEq(prgh,dimMass/dimTime);pressureEq.diag()=2;pressureEq.diag()[1]=3;pressureEq.upper()=-1;pressureEq.source()[0]=.01;pressureEq.source()[1]=-.02;
   pressureEq.internalCoeffs()[0][0]=.5;pressureEq.boundaryCoeffs()[0][0]=.002;
   routeAU04::reference("pressure_pre_reference",pressureEq,0,0);
   pressureEq.setReference(0,0);
   routeAU04::reference("pressure_post_reference",pressureEq,0,0);
   const auto pp=pressureEq.solve(pressureControls);solves.push_back(performance(pp));
   routeAU04::reference("pressure_solved",pressureEq,0,0);
   phi.primitiveFieldRef()[0]=.03;phi.boundaryFieldRef()[0][0]=-.02;phi.boundaryFieldRef()[0][1]=.01;
   density();routeAU04::stage("native_continuity_report",mesh);
   p=prgh+rho*gh; // native pressure relation before postSolve EOS assignment
   fingerprints.push(physicalFingerprint(t,{&rho,&e,&K,&prgh,&p},{&pressureEq},solves));
  }
  routeAU04::stage("outer_end",mesh);
 }
 routeAU04::stage("before_postSolve",mesh);routeAU04::stage("before_postSolve_EOS_copy",mesh);
 rho=rhoT;routeAU04::stage("after_postSolve_EOS_copy",mesh);routeAU04::stage("after_postSolve",mesh);routeAU04::stage("time_end",mesh);
 fingerprints.push(physicalFingerprint(t,{&rho,&rhoT,&e,&T,&K,&p,&prgh},{},solves));
 // Independent native manufactured polynomial operators, assembled once each.
 // These are fixture equations, not an extra assembly of any production equation.
 for(int degree=0;degree<=2;++degree){
  volScalarField f(IOobject("polynomial"+Foam::name(degree),t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedScalar("rho",dimDensity,1),"zeroGradient");
  auto value=[&](double x){return 1+(degree>=1?2*x:0)+(degree==2?3*x*x:0);};
  f.oldTimeRef().primitiveFieldRef()=value(t.value()-t.deltaTValue());
  f.oldTimeRef().timeIndex()=t.timeIndex()-1;
  f.oldTimeRef().oldTimeRef().primitiveFieldRef()=value(t.value()-t.deltaTValue()-t.deltaT0Value());
  f.oldTimeRef().oldTimeRef().timeIndex()=t.timeIndex()-2;
  f.primitiveFieldRef()=value(t.value());
  const auto derivative=backward.fvmDdt(f);Json fixture=Json::obj();fixture["polynomial_degree"]=degree;
  fixture["matrix"]=routeAU04::matrixPacket(derivative());
  fixture["expected_integrated_derivative"]=(degree==0?0:degree==1?2:2+6*t.value())*sum(mesh.V().primitiveField());
  if(observed)observer->emit("auxiliary_fixture",mesh,fixture);
 }
 // Independent isolated energy fixtures: actual native operator once each.
 auto isolated=[&](const char* kind,const fvScalarMatrix& matrix,const scalarField& expected){
  Json fixture=Json::obj();fixture["fixture_kind"]=kind;fixture["matrix"]=routeAU04::matrixPacket(matrix);fixture["expected_integrated_cells"]=routeAU04::scalars(expected);
  if(observed)observer->emit("auxiliary_fixture",mesh,fixture);
 };
 const auto storage=backward.fvmDdt(rho,e);const auto storagePacket=routeAU04::matrixPacket(storage());
 const scalar sh=t.deltaTValue(),sk0=t.deltaT0Value(),sa=1+sh/(sh+sk0),sc=sh*sh/(sk0*(sh+sk0)),sb=sa+sc;
 const scalarField expectedStorage=mesh.V().primitiveField()/sh*(sa*rho.primitiveField()*e.primitiveField()-sb*rho.oldTime().primitiveField()*e.oldTime().primitiveField()+sc*rho.oldTime().oldTime().primitiveField()*e.oldTime().oldTime().primitiveField());
 isolated("D_energy_storage_only",storage(),expectedStorage);
 const auto wallLap=lap.fvcLaplacian(kappa,T);const auto wallCorrection=fvm::laplacianCorrection(kappa/Cv,e);const auto wall=-wallLap()-wallCorrection();
 isolated("E_wall_conduction",wall(),-wallLap().primitiveField()*mesh.V().primitiveField());
 const auto gravity=rho*(U&g);fvScalarMatrix gravityMatrix(fvScalarMatrix(e,dimPower)==gravity());
 isolated("F_gravity_work",gravityMatrix,-gravity().primitiveField()*mesh.V().primitiveField());
 volScalarField specificEnd(IOobject("specificEnd",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),p/rho);const auto pressureWork=conv.fvcDiv(phi,specificEnd);
 fvScalarMatrix workMatrix(fvScalarMatrix(e,dimPower)+pressureWork());isolated("G_pressure_work",workMatrix,pressureWork().primitiveField()*mesh.V().primitiveField());
 if(observed)observer->finish();
 std::ofstream fp(root+".physical.json");fp<<fingerprints.dump()<<'\n';fp.close();
 Json summary=Json::obj();summary["physical_fingerprint_sha256"]=routeAU04::digest(fingerprints.dump());summary["linear_solves"]=int(solves.size());summary["outer"]=24;summary["pressure_per_outer"]=2;summary["h"]=t.deltaTValue();summary["k"]=t.deltaT0Value();summary["classification"]="SYNTHETIC_EVALUATOR_TEST";summary["observed"]=observed;
 std::cout<<"U04_SUMMARY "<<summary.dump()<<std::endl;
}
int main(int argc,char**argv){try{
 if(argc<7)routeAU04::fail("USAGE root guard source instrument on/off injection");
 const bool observed=std::string(argv[5])=="on";
 // OFF driver must bypass bootstrap; no production environment exists.
 run(argv[1],argv[2],argv[3],argv[4],observed,argv[6]);return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 2;}}
