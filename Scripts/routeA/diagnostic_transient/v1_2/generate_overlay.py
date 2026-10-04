"""Generate isolated diagnostic clones; verify wrapper erasure restores native tokens.

No /opt writes. Source mutations consist of observation blocks, identity tmp taps,
and mechanically renamed class/module identifiers. Native operator calls execute
once in the same expression tree. This command never builds or executes CFD.
"""
import hashlib,json,re,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
AUTH=Path('/opt/openfoam13/applications/modules')
PLAN=json.loads((HERE.parent/'v1_1/instrumentation_stage_plan.json').read_text())
PARENT=json.loads((ROOT/'docs/routeA_diagnostic_transient_contract_v1.1.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(text):return '\n// ROUTE_A_OBSERVATION_BEGIN\n'+text+'\n// ROUTE_A_OBSERVATION_END\n'
def insert(s,anchor,text,before=False,count=1):
 if s.count(anchor)!=count:raise ValueError(('ANCHOR_COUNT',anchor,s.count(anchor)))
 return s.replace(anchor,block(text)+anchor if before else anchor+block(text))
def tap(s,expression,name,count=1):
 if s.count(expression)!=count:raise ValueError(('TERM_COUNT',expression,s.count(expression)))
 return s.replace(expression,'routeAU04::tap("'+name+'", '+expression+')')
def erase(s):
 s=re.sub(r'\n// ROUTE_A_OBSERVATION_BEGIN\n.*?\n// ROUTE_A_OBSERVATION_END\n','',s,flags=re.S)
 while 'routeAU04::tap(' in s:
  start=s.index('routeAU04::tap(');first=s.index(',',start);depth=1;quoted=False;escaped=False;end=first+1
  while depth:
   c=s[end]
   if quoted:
    if escaped:escaped=False
    elif c=='\\':escaped=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':depth-=1
   end+=1
  s=s[:start]+s[first+1:end-1].lstrip()+s[end:]
 return s
def tokens(s):
 s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 return re.findall(r'"(?:\\.|[^"\\])*"|\w+|[^\s]',s)
def generate(dest):
 dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
 for e in PLAN['entries']:
  if sha(Path(e['source']))!=e['sha256']:raise ValueError('STOP_U04_PARENT_OR_SOURCE_MISMATCH')
 files={}
 for module in ['isothermalFluid','fluid']:
  for p in (AUTH/module).glob('*'):
   if p.suffix in ['.C','.H']:files[str(p)]=p.read_text()
 files['/opt/openfoam13/applications/solvers/foamRun/foamRun.C']=Path('/opt/openfoam13/applications/solvers/foamRun/foamRun.C').read_text()
 fourier=Path('/opt/openfoam13/src/ThermophysicalTransportModels/fluid/laminar/Fourier/Fourier.C')
 files[str(fourier)]=fourier.read_text()
 transformations=[]
 for name,original in files.items():
  s=original;base=Path(name).name
  changed=False
  if base=='thermophysicalPredictor.C':
   s=insert(s,'volScalarField& he = thermo_.he();','routeAU04::stage("energy_begin", mesh);\nrouteAU04::history("S_K", K);\nif (buoyancy.valid()) routeAU04::thermal(thermo_.Cpv()(), buoyancy->g);')
   for expr,term in [('fvm::ddt(rho, he)','S_e'),('fvm::div(phi, he)','F_e'),('fvc::ddt(rho, K)','S_K'),('fvc::div(phi, K)','F_K'),('thermophysicalTransport->divq(he)','H_out'),('fvModels().source(rho, he)','S_models'),('rho*(U & buoyancy->g)','W_g')]:
    s=tap(s,expr,term,count=2 if term=='S_models' else 1)
   # Capture complete pressureWork result (static e branch), not its input only.
   expr='pressureWork\n        (\n            he.name() == "e"\n          ? fvc::div(phi, p/rho)()\n          : -dpdt\n        )'
   s=tap(s,expr,'W_p')
   s=insert(s,'EEqn.relax();','routeAU04::total("energy_unrelaxed_assembly", EEqn);',before=True)
   s=insert(s,'EEqn.relax();','routeAU04::total("energy_after_relax", EEqn);')
   s=insert(s,'EEqn.solve();','routeAU04::solved("energy_after_solve", EEqn);')
   s=insert(s,'thermo_.correct();','routeAU04::stage("before_thermo_correct", mesh);',before=True)
   s=insert(s,'thermo_.correct();','routeAU04::stage("after_thermo_correct", mesh);')
   changed=True
  elif base=='correctDensity.C':
   s=insert(s,'volScalarField& rho(rho_);','routeAU04::stage("before_correctDensity", mesh);')
   s=tap(s,'fvm::ddt(rho)','D_B_rho');s=tap(s,'fvc::div(phi)','div_phi');s=tap(s,'fvModels().source(rho)','mass_models')
   s=insert(s,'fvConstraints().constrain(rhoEqn);','routeAU04::total("mass_unrelaxed_assembly", rhoEqn);',before=True)
   s=insert(s,'rhoEqn.solve();','routeAU04::solved("mass_after_solve", rhoEqn);')
   s=insert(s,'fvConstraints().constrain(rho);','routeAU04::stage("after_correctDensity", mesh);')
   changed=True
  elif base=='correctBuoyantPressure.C':
   # Only the first unconditional EOS copy; conditional copies remain untouched.
   anchor='    rho = thermo.rho();';pos=s.index(anchor)
   s=s[:pos]+block('routeAU04::stage("before_pressure_EOS_copy", mesh);')+anchor+block('routeAU04::stage("after_pressure_EOS_copy", mesh);')+s[pos+len(anchor):]
   # Both native reference sites are connected; frozen transonic=no selectselse.
   anchor='            p_rghEqn.setReference\n            (\n                pressureReference.refCell(),\n                pressureReference.refValue()\n            );'
   s=insert(s,anchor,'routeAU04::reference("pressure_pre_reference", p_rghEqn, pressureReference.refCell(), pressureReference.refValue());',before=True,count=2)
   s=insert(s,anchor,'routeAU04::reference("pressure_post_reference", p_rghEqn, pressureReference.refCell(), pressureReference.refValue());',count=2)
   s=insert(s,'            p_rghEqn.solve();','routeAU04::reference("pressure_solved", p_rghEqn, pressureReference.refCell(), pressureReference.refValue());',count=2)
   s=insert(s,'    continuityErrors();','routeAU04::stage("native_continuity_report", mesh);')
   changed=True
  elif base=='isothermalFluid.C':
   s=insert(s,'    while (pimple.correct())\n    {','routeAU04::stage("pressure_start", mesh);')
   s=insert(s,'        rho_ = thermo.rho();','routeAU04::stage("before_postSolve_EOS_copy", mesh);',before=True)
   s=insert(s,'        rho_ = thermo.rho();','routeAU04::stage("after_postSolve_EOS_copy", mesh);')
   changed=True
  elif base=='foamRun.C':
   s=insert(s,'    solver& solver = solverPtr();','routeAU04::bootstrap(mesh);')
   s=insert(s,'        solver.preSolve();','routeAU04::stage("preSolve_before", mesh);',before=True)
   s=insert(s,'        solver.preSolve();','routeAU04::stage("preSolve_after", mesh);')
   s=insert(s,'        adjustDeltaT(runTime, solver);','routeAU04::stage("controller_complete", mesh);')
   s=insert(s,'        runTime++;','routeAU04::stage("time_start", mesh);')
   s=insert(s,'        while (pimple.loop())\n        {','routeAU04::stage("outer_start", mesh);')
   s=insert(s,'            solver.prePredictor();','routeAU04::stage("density_predictor_complete", mesh);')
   # Ends outer after transport correction, before leaving loop.
   anchor='        }\n\n        solver.postSolve();'
   s=insert(s,anchor,'routeAU04::stage("outer_end", mesh);',before=True)
   # Previous insertion sits just BEFORE outer brace, correct lexical loop scope.
   s=insert(s,'        solver.postSolve();','routeAU04::stage("before_postSolve", mesh);',before=True)
   s=insert(s,'        solver.postSolve();','routeAU04::stage("after_postSolve", mesh);\nrouteAU04::stage("time_end", mesh);')
   s=insert(s,'    Info<< "End\\n" << endl;','if (routeAU04::current()) routeAU04::current()->finish();')
   changed=True
  elif base=='Fourier.C':
   expr='fvc::laplacian(this->alpha()*thermo.kappa(), thermo.T())'
   s=tap(s,expr,'Fourier_laplacian')
   expr='fvm::laplacianCorrection\n         (\n             this->alpha()*thermo.kappa()/thermo.Cpv(),\n             he\n         )'
   s=tap(s,expr,'Fourier_correction');changed=True
  if tokens(erase(s))!=tokens(original):raise ValueError(('STRUCTURAL_ERASURE_FAILURE',name))
  if changed:s=block('#include "NativeStageObserver.H"')+s
  # Class/library isolation only; restore names for structural comparison.
  s=re.sub(r'\bisothermalFluid\b','routeADiagnosticIsothermalFluid',s)
  s=re.sub(r'\bfluid\b','routeADiagnosticFluid',s) if '/modules/fluid/' in name else s
  if base=='Fourier.C':target=dest/'Fourier'/'Fourier.C'
  elif base=='foamRun.C':target=dest/'driver'/'foamRunDiagnostic.C'
  else:target=dest/('fluid' if '/modules/fluid/' in name else 'isothermalFluid')/Path(name).name
  target=target.with_name(target.name.replace('isothermalFluid','routeADiagnosticIsothermalFluid').replace('fluid.C','routeADiagnosticFluid.C').replace('fluid.H','routeADiagnosticFluid.H'))
  target.parent.mkdir(exist_ok=True,parents=True);target.write_text(s)
  transformations.append({'native_source':name,'native_sha256':sha(Path(name)),'overlay_file':str(target.relative_to(dest)),'overlay_sha256':sha(target),'observation_added':changed,'native_tokens_restored_after_erasure':True})
 # Template resolution picks local Fourier.H and its instrumented SourceFile.
 shutil.copyfile(fourier.with_suffix('.H'),dest/'Fourier/Fourier.H')
 authority={'parent_contract_sha256':sha(ROOT/'docs/routeA_diagnostic_transient_contract_v1.1.json'),'transformations':transformations,'stage_plan_sha256':sha(HERE.parent/'v1_1/instrumentation_stage_plan.json'),'source_only':True,'production_executed':False}
 (dest/'overlay_manifest.json').write_text(json.dumps(authority,indent=2)+'\n')
 print(json.dumps({'overlay_sources':len(transformations),'native_tokens_restored_after_erasure':True}))
if __name__=='__main__':generate(sys.argv[1])
