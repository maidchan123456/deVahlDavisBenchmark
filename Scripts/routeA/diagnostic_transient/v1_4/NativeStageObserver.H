#ifndef routeA_NativeStageObserver_H
#define routeA_NativeStageObserver_H
#include "../v1_1/NativeMatrixObserver.H"
#include "DiagnosticJson.H"
#include "uniformDimensionedFields.H"
#include <memory>
namespace routeAU04 {
using namespace Foam;
Json dimensions(const dimensionSet&);
Json scalars(const scalarField&);
Json labels(const labelUList&);
Json matrixPacket(const fvScalarMatrix&);
Json scalarState(const volScalarField&);
Json meshState(const fvMesh&);
struct Observer {
 std::string root,studyGuard,sourceHash,instrumentHash,caseId,classification;
 int sequence=0,outer=0,pressure=0,nonOrthogonal=0,energySolve=0,rhoSolve=0;
 int lastTime=-1;
 std::map<std::string,std::unique_ptr<routeADiagnostic::ScalarMatrixSnapshot>> matrices;
 std::map<std::string,Json> explicitTerms;
 std::map<std::string,Json> matrixPayloads;
 Json thermalContext=Json::obj();
 std::map<std::string,int> historyCounts;
 std::string activeEquation;
 bool completed=false;
 std::string phase="initial";
 std::vector<std::string> capturedTerms;
 void transition(const std::string&,const Json&);
 Observer(const std::string&,const std::string&,const std::string&,const std::string&,const std::string&,const std::string&);
 ~Observer();
 Json metadata(const std::string&,const fvMesh&) const;
 void emit(const std::string&,const fvMesh&,Json);
 void stage(const std::string&,const fvMesh&);
 void term(const std::string&,const fvScalarMatrix&);
 void term(const std::string&,const volScalarField&);
 void term(const std::string&,const volScalarField::Internal&);
 void total(const std::string&,const fvScalarMatrix&);
 void solved(const std::string&,const fvScalarMatrix&);
 void finish();
};
Observer* current();
void install(Observer*);
void bootstrap(const fvMesh&);
void stage(const char*,const fvMesh&);
void total(const char*,const fvScalarMatrix&);
void solved(const char*,const fvScalarMatrix&);
void reference(const char*,const fvScalarMatrix&,label,scalar);
void history(const char*,const volScalarField&);
void thermal(const volScalarField::Internal&,const dimensionedVector&);
// Exactly one native operator invocation. Copy its result, return the same tmp.
// Never assemble an additional equation or call BC/thermo/history update.
template<class T> tmp<T> tap(const char* name,tmp<T> value) {
 if(current())current()->term(name,value());
 return Foam::move(value);
}
}
#endif
