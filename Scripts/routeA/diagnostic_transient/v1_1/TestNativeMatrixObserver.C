// Standalone native-library synthetic test, NOT a solver or a CFD case.
// Time and a 1/2-cell polyhedron are built in memory. No case/mesh is written.
// Native 1/2-cell linear matrix solves characterize evaluator floors only.
// No CFD solver module, thermo, time-evolution solve, foamRun or case utilities.
#include "NativeMatrixObserver.H"
#include "Time.H"
#include "wallPolyPatch.H"
#include "backwardDdtScheme.H"
#include "gaussConvectionScheme.H"
#include "gaussLaplacianScheme.H"
#include "linear.H"
#include "orthogonalSnGrad.H"
#include "fvmLaplacian.H"
#include "fvcDiv.H"
#include "IStringStream.H"
#include <iostream>
#include <iomanip>
#include <memory>

using namespace Foam;
using namespace routeADiagnostic;
int checks=0;
double maxDefect=0;
double massFloor=0, massBound=0, energyFloor=0, energyBound=0, solveFloor=0;
int syntheticLinearSolves=0;
void near(const std::string& name, double got, double expected, double tol=1e-11)
{
    const double err=std::fabs(got-expected);
    maxDefect=std::max(maxDefect,err);
    if (!std::isfinite(got) || err>tol*std::max(1.,std::fabs(expected)))
        throw std::runtime_error(name+": got="+std::to_string(got)
                                  +" expected="+std::to_string(expected));
    ++checks;
}
template<class Fun> void rejects(const std::string& name, Fun fun)
{
    try { fun(); } catch (const std::runtime_error&) { ++checks; return; }
    throw std::runtime_error(name+" did not reject");
}

std::unique_ptr<fvMesh> memoryMesh(Time& time, label n)
{
    pointField pts(4*(n+1));
    const scalar xs[3]={0,1,3};
    for (label i=0;i<=n;++i)
    {
        pts[4*i]=point(xs[i],0,0); pts[4*i+1]=point(xs[i],1,0);
        pts[4*i+2]=point(xs[i],1,1); pts[4*i+3]=point(xs[i],0,1);
    }
    std::vector<face> fl; std::vector<label> owners;
    auto add=[&](std::initializer_list<label> ids,label owner)
    {
        face f(ids.size()); label j=0; for (label p:ids) f[j++]=p;
        fl.push_back(f); owners.push_back(owner);
    };
    if (n==2) add({4,5,6,7},0);
    add({0,3,2,1},0); const label r=4*n;
    add({r,r+1,r+2,r+3},n-1);
    for(label i=0;i<n;++i)
    {
        const label l=4*i, rr=l+4;
        add({l,rr,rr+3,l+3},i); add({l+1,l+2,rr+2,rr+1},i);
        add({l,l+1,rr+1,rr},i); add({l+3,rr+3,rr+2,l+2},i);
    }
    faceList faces(fl.size()); labelList own(owners.size());
    for(label i=0;i<faces.size();++i) { faces[i]=fl[i]; own[i]=owners[i]; }
    labelList nei(n==2?1:0); if(n==2) nei[0]=1;
    auto mesh=std::unique_ptr<fvMesh>(new fvMesh
    (IOobject("syntheticMesh"+Foam::name(n),time.name(),time,
      IOobject::NO_READ,IOobject::NO_WRITE,false),std::move(pts),
      std::move(faces),std::move(own),std::move(nei),false));
    List<polyPatch*> patches(1);
    patches[0]=new wallPolyPatch("walls",fl.size()-(n==2?1:0),
                               n==2?1:0,0,mesh->boundaryMesh(),"wall");
    mesh->addFvPatches(patches);
    return mesh;
}

StageId stage(const Time& t,const std::string& name="energy_assembly")
{
    return {t.timeIndex(),1,0,1,t.value(),t.deltaTValue(),t.deltaT0Value(),
            name,{"rho:old@1","e:old@1","rho:oldold@0","e:oldold@0"}};
}

void tests(Time& t,label n)
{
    auto mp=memoryMesh(t,n); fvMesh& mesh=*mp;
    const scalarField V(mesh.V().primitiveField());
    near("volume0",V[0],1); if(n==2) near("volume1",V[1],2);
    const IOobject io("e",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false);
    volScalarField e(io,mesh,dimensionedScalar("e",dimEnergy/dimMass,3),"zeroGradient");
    if(n==2) e.primitiveFieldRef()[1]=4;
    e.correctBoundaryConditions();
    fvScalarMatrix A(e,dimPower);
    A.diag()=4; A.source()=1;
    A.upper()=0; A.lower()=0;
    if(n==2) { A.diag()[1]=5; A.source()[1]=2; A.lower()=-1; A.upper()=-2; }
    A.internalCoeffs()[0][0]=0.5; A.boundaryCoeffs()[0][0]=7;
    if(n==2) { A.internalCoeffs()[0][1]=1.5; A.boundaryCoeffs()[0][1]=8; }
    const scalarField beforeD(A.diag()),beforeS(A.source());
    ScalarMatrixSnapshot snapshot(A,stage(t),dimPower);
    const scalarField native=A.residual()(), action=snapshot.lhsMinusRhs();
    for(label i=0;i<n;++i) near("native sign",action[i],-native[i]);
    near("boundary-aware row0",action[0],n==1?5.5:-2.5);
    if(n==2) near("boundary-aware row1",action[1],13);
    near("integrated global no double volume",snapshot.evaluate().signedSum,n==1?5.5:10.5);
    for(label i=0;i<n;++i) {near("observer unchanged diag",A.diag()[i],beforeD[i]);near("observer unchanged source",A.source()[i],beforeS[i]);}
    A.diag()[0]+=100;
    near("deep unrelaxed copy",snapshot.lhsMinusRhs()[0],action[0]);
    e.primitiveFieldRef()[0]+=1;
    near("snapshot evaluates updated psi",snapshot.lhsMinusRhs()[0],action[0]+4.5);
    e.primitiveFieldRef()[0]-=1; e.correctBoundaryConditions();
    rejects("wrong matrix dimensions",[&]{ScalarMatrixSnapshot bad(A,stage(t),dimMass/dimTime);});
    auto badid=stage(t); badid.oldTimeIds.clear();
    rejects("missing oldTime IDs",[&]{ScalarMatrixSnapshot bad(A,badid,dimPower);});
    surfaceScalarField phi(IOobject("phi",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),
                           mesh,dimensionedScalar("phi",dimMass/dimTime,0));
    if(n==2) phi.primitiveFieldRef()[0]=3;
    phi.boundaryFieldRef()[0][0]=-2; phi.boundaryFieldRef()[0][1]=1;
    const auto div=fvc::div(phi);
    const auto fluxCells=integrateExplicit(div(),dimMass/dimTime);
    near("mass internal cancellation",sum(fluxCells),outwardBoundarySum(phi));
    near("boundary outward sign",outwardBoundarySum(phi),-1);
    if(n==2) {near("local face row0",fluxCells[0],1);near("local face row1",fluxCells[1],-2);}
    fv::gaussConvectionScheme<scalar> convection(mesh,phi,tmp<surfaceInterpolationScheme<scalar>>(new linear<scalar>(mesh)));
    const auto adv=convection.fvmDiv(phi,e);
    ScalarMatrixSnapshot advection(adv(),stage(t),dimPower);
    near("native advective boundary transport",advection.evaluate().signedSum,n==1?-3:-2);
    const auto explicitAdv=convection.fvcDiv(phi,e);
    near("implicit vs explicit advection",sum(integrateExplicit(explicitAdv(),dimPower)),advection.evaluate().signedSum);
    volScalarField pressureSpecific(IOobject("p_over_rho",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),2*e);
    const auto pw=convection.fvcDiv(phi,pressureSpecific);
    near("pressure work sign/units",sum(integrateExplicit(pw(),dimPower)),n==1?-6:-4);
    volScalarField rho(IOobject("rho",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedScalar("rho",dimDensity,1),"zeroGradient");
    rho.oldTimeRef().primitiveFieldRef()=1.1;
    rho.oldTimeRef().oldTimeRef().primitiveFieldRef()=0.9;
    fv::backwardDdtScheme<scalar> backward(mesh);
    const auto massStorage=backward.fvmDdt(rho);
    const double h=t.deltaTValue(),k=t.deltaT0Value(),a=1+h/(h+k),c=h*h/(k*(h+k)),b=a+c;
    ScalarMatrixSnapshot ms(massStorage(),stage(t,"after_correctDensity"),dimMass/dimTime);
    const double derivative=(a*1-b*1.1+c*.9)/h;
    near("native variable BDF density",ms.evaluate().signedSum,derivative*sum(V));
    e.oldTimeRef().primitiveFieldRef()=2;
    e.oldTimeRef().oldTimeRef().primitiveFieldRef()=1;
    const auto internalStorage=backward.fvmDdt(rho,e);
    ScalarMatrixSnapshot se(internalStorage(),stage(t),dimPower);
    double directInternal=0;
    for(label i=0;i<n;++i) directInternal+=V[i]*(a*e[i]-b*1.1*2+c*.9*1)/h;
    near("native rho-e old products",se.evaluate().signedSum,directInternal);
    volScalarField kinetic(IOobject("K",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedScalar("K",dimEnergy/dimMass,2),"zeroGradient");
    kinetic.oldTimeRef().primitiveFieldRef()=1;
    kinetic.oldTimeRef().oldTimeRef().primitiveFieldRef()=.5;
    const auto sk=backward.fvcDdt(rho,kinetic);
    near("kinetic storage sign/units",sum(integrateExplicit(sk(),dimPower)),sum(V)*(a*2-b*1.1+c*.9*.5)/h);
    const auto fk=convection.fvcDiv(phi,kinetic);
    near("kinetic transport sign/units",sum(integrateExplicit(fk(),dimPower)),-2);
    volVectorField U(IOobject("U",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedVector("U",dimVelocity,vector(0,2,0)),"zeroGradient");
    const dimensionedVector g("g",dimAcceleration,vector(0,-3,0));
    volScalarField work(IOobject("gravityWork",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),rho*(U&g));
    near("gravity RHS sign",-sum(integrateExplicit(work,dimPower)),6*sum(V));
    rejects("explicit dimensions reject",[&]{integrateExplicit(work,dimMass/dimTime);});
    // Fourier: capture a lagged explicit T term plus actual correction matrix.
    volScalarField heatE(IOobject("heatE",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedScalar("e",dimEnergy/dimMass,3),"fixedValue");
    if(n==2) heatE.primitiveFieldRef()[1]=4;
    heatE.boundaryFieldRef()[0]==scalarField(heatE.boundaryField()[0].size(),3);
    heatE.boundaryFieldRef()[0][0]=1;heatE.boundaryFieldRef()[0][1]=7;
    const dimensionedScalar Cv("Cv",dimEnergy/dimMass/dimTemperature,2);
    volScalarField T(IOobject("T",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),heatE/Cv);
    surfaceScalarField kappa(IOobject("kappa",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),mesh,dimensionedScalar("kappa",dimPower/dimLength/dimTemperature,1));
    fv::gaussLaplacianScheme<scalar,scalar> lap(mesh,tmp<surfaceInterpolationScheme<scalar>>(new linear<scalar>(mesh)),tmp<fv::snGradScheme<scalar>>(new fv::orthogonalSnGrad<scalar>(mesh)));
    const auto lapT=lap.fvcLaplacian(kappa,T);
    const scalarField explicitHeat=-integrateExplicit(lapT(),dimPower);
    const auto correction=-fvm::laplacianCorrection(kappa/Cv,heatE);
    ScalarMatrixSnapshot heatCorrection(correction(),stage(t),dimPower);
    near("Fourier correction zero at assembly psi",heatCorrection.evaluate().signedSum,0);
    heatE.primitiveFieldRef()+=1;
    const scalarField heatAction=explicitHeat+heatCorrection.lhsMinusRhs();
    volScalarField Tnew(IOobject("Tnew",t.name(),mesh,IOobject::NO_READ,IOobject::NO_WRITE,false),heatE/Cv);
    const auto lapNew=lap.fvcLaplacian(kappa,Tnew);
    const scalarField refreshedHeat=-integrateExplicit(lapNew(),dimPower);
    for(label i=0;i<n;++i) near("Fourier lagged plus correction identity",heatAction[i],refreshedHeat[i]);
    // Full synthetic energy assembly on ONE energy unknown, without solve or
    // relaxation. The Fourier matrix references heatE, so its other implicit
    // terms must reference that same field as in the native EEqn.
    heatE.oldTimeRef().primitiveFieldRef()=2;
    heatE.oldTimeRef().oldTimeRef().primitiveFieldRef()=1;
    const auto heatStorage=backward.fvmDdt(rho,heatE);
    const auto heatAdv=convection.fvmDiv(phi,heatE);
    ScalarMatrixSnapshot hs(heatStorage(),stage(t),dimPower);
    ScalarMatrixSnapshot ha(heatAdv(),stage(t),dimPower);
    const auto assembled=heatStorage()+heatAdv()+correction()+lapT()*(-1)+sk()+fk()+pw()-work;
    ScalarMatrixSnapshot full(assembled(),stage(t),dimPower);
    const double direct=hs.evaluate().signedSum+ha.evaluate().signedSum
      +heatCorrection.evaluate().signedSum+sum(explicitHeat)
      +sum(integrateExplicit(sk(),dimPower))+sum(integrateExplicit(fk(),dimPower))
      +sum(integrateExplicit(pw(),dimPower))-sum(integrateExplicit(work,dimPower));
    near("matrix vs termwise energy identity",full.evaluate().signedSum,direct);
    const scalarField z(n,0),badV(n,-1);
    rejects("nonpositive volume",[&]{summarizeIntegrated(z,badV,dimPower);});
    scalarField nonfinite(z);nonfinite[0]=std::numeric_limits<double>::quiet_NaN();
    rejects("nonfinite residual",[&]{summarizeIntegrated(nonfinite,V,dimPower);});
    rho.primitiveFieldRef()=1;rho.oldTimeRef().primitiveFieldRef()=1;
    rho.oldTimeRef().oldTimeRef().primitiveFieldRef()=1;
    e.primitiveFieldRef()=1850;e.oldTimeRef().primitiveFieldRef()=1850;
    e.oldTimeRef().oldTimeRef().primitiveFieldRef()=1850;
    const auto stationaryM=backward.fvmDdt(rho);
    const auto stationaryE=backward.fvmDdt(rho,e);
    ScalarMatrixSnapshot fm(stationaryM(),stage(t),dimMass/dimTime);
    ScalarMatrixSnapshot fe(stationaryE(),stage(t),dimPower);
    massFloor=std::max(massFloor,fm.evaluate().absoluteSum);
    energyFloor=std::max(energyFloor,fe.evaluate().absoluteSum);
    massBound=std::max(massBound,fm.matrixActionRoundoffBound());
    energyBound=std::max(energyBound,fe.matrixActionRoundoffBound());
    near("stationary mass within stored-matrix floor",fm.evaluate().absoluteSum,0,
         std::max(1e-30,fm.matrixActionRoundoffBound()));
    near("stationary energy within stored-matrix floor",fe.evaluate().absoluteSum,0,
         std::max(1e-30,fe.matrixActionRoundoffBound()));
    for (const std::string solver: {"PCG","PBiCGStab"})
    {
        fvScalarMatrix linearA(e,dimPower);
        linearA.diag()=4;linearA.upper()=-1;
        if(solver=="PBiCGStab") linearA.lower()=-2;
        if(n==2)linearA.diag()[1]=5;
        linearA.internalCoeffs()[0][0]=.5;linearA.boundaryCoeffs()[0][0]=7;
        if(n==2){linearA.internalCoeffs()[0][1]=1.5;linearA.boundaryCoeffs()[0][1]=8;}
        // Manufactured exact solution [0.3,-0.7], including boundary source.
        linearA.source()[0]=4.5*.3-7+(n==2?.7:0);
        if(n==2) linearA.source()[1]=6.5*(-.7)-8+(solver=="PCG"?-.3:-.6);
        e.primitiveFieldRef()=0;e.correctBoundaryConditions();
        ScalarMatrixSnapshot solveSnapshot(linearA,stage(t),dimPower);
        IStringStream settings("solver "+solver+"; preconditioner "+
            (solver=="PCG"?std::string("DIC"):std::string("DILU"))+
            "; tolerance 1e-12; relTol 0; maxIter 4000;");
        dictionary controls(settings);
        const auto performance=linearA.solve(controls);++syntheticLinearSolves;
        near("synthetic linear solution0",e[0],.3);
        if(n==2)near("synthetic linear solution1",e[1],-.7);
        if(performance.finalResidual()>1e-12)throw std::runtime_error("synthetic linear residual");
        const double residual=solveSnapshot.evaluate().absoluteSum;
        solveFloor=std::max(solveFloor,residual);
        near("synthetic solve integrated residual floor",residual,0,
             std::max(1e-12,solveSnapshot.matrixActionRoundoffBound()));
    }
}

int main()
{
    try
    {
        Time time(fileName("/tmp"),fileName("routeA-in-memory-synthetic-no-case"),false);
        time.setDeltaT(.2);++time; time.setDeltaT(.1);++time;
        tests(time,1);tests(time,2);
        // Cancellation/reduction conditioning, not a physical conservation limit.
        scalarField vals(3); vals[0]=1e16;vals[1]=1;vals[2]=-1e16;
        const auto reduction=summarizeIntegrated(vals,scalarField(3,1),dimPower);
        near("compensated cancellation",reduction.signedSum,1);
        std::cout<<std::setprecision(17)<<"{\"status\":\"PASS\",\"checks\":"<<checks
          <<",\"max_absolute_identity_defect\":"<<maxDefect
          <<",\"cancellation_bound\":"<<reduction.summationRoundoffBound
          <<",\"stationary_mass_floor_kg_s\":"<<massFloor
          <<",\"stationary_mass_stored_matrix_bound_kg_s\":"<<massBound
          <<",\"stationary_energy_floor_W\":"<<energyFloor
          <<",\"stationary_energy_stored_matrix_bound_W\":"<<energyBound
          <<",\"synthetic_linear_solve_residual_floor_W\":"<<solveFloor
          <<",\"synthetic_linear_solves\":"<<syntheticLinearSolves
          <<",\"production_solver_executed\":false,\"case_written\":false}"<<std::endl;
        return 0;
    }
    catch(const std::exception& e)
    { std::cerr<<"SYNTHETIC_TEST_FAILURE: "<<e.what()<<std::endl;return 1; }
}
