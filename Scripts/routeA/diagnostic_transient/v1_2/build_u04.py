"""Build isolated diagnostic overlay/driver only, never execute foamRun or a case."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,shlex,subprocess,sys,time,shutil
HERE=Path(__file__).resolve().parent
SOURCE=Path('/opt/openfoam13');LIB=SOURCE/'platforms/linux64GccDPInt32Opt/lib'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build(destination):
 out=Path(destination).resolve();out.mkdir(parents=True,exist_ok=False)
 overlay=out/'overlay'
 if (HERE/'overlay').exists():shutil.copytree(HERE/'overlay',overlay)
 else:subprocess.run([sys.executable,str(HERE/'generate_overlay.py'),str(overlay)],check=True)
 manifest=json.loads((overlay/'overlay_manifest.json').read_text())
 for x in manifest['transformations']:
  assert sha(x['native_source'])==x['native_sha256'],'SOURCE_HASH_CHANGED'
  assert sha(overlay/x['overlay_file'])==x['overlay_sha256'],'OVERLAY_HASH_CHANGED'
 native={x['native_source']:x['native_sha256'] for x in manifest['transformations']}
 # Include the native transport-instantiation source and metadata APIs.
 inst=SOURCE/'src/ThermophysicalTransportModels/fluidThermo/fluidThermoThermophysicalTransportModels.C'
 extras=[inst,SOURCE/'src/ThermophysicalTransportModels/fluid/laminar/Fourier/Fourier.H',HERE.parent/'v1_1/NativeMatrixObserver.H',HERE.parent/'v1_1/TestNativeMatrixObserver.C',SOURCE/'src/OpenFOAM/fields/OldTimeField/OldTimeField.C',SOURCE/'src/OpenFOAM/fields/OldTimeField/OldTimeField.H',SOURCE/'src/OpenFOAM/fields/GeometricFields/GeometricField/GeometricFieldI.H',SOURCE/'src/finiteVolume/fields/fvPatchFields/fvPatchField/fvPatchField.H']
 native.update({str(p):sha(p) for p in extras})
 source_hash=hashlib.sha256(json.dumps(native,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 implementation={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.suffix in {'.H','.C','.py','.sh','.json'} and '__pycache__' not in p.parts}
 instrument_hash=hashlib.sha256(json.dumps(implementation,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 inc=[HERE,overlay/'Fourier',overlay/'fluid',overlay/'isothermalFluid',SOURCE/'applications/modules/fluidSolver/lnInclude',SOURCE/'applications/solvers/foamRun']
 inc+=sorted((SOURCE/'src').rglob('lnInclude'))
 flags=['-std=c++14','-O2','-fPIC','-DWM_DP','-DWM_LABEL_SIZE=32','-DNoRepository',f'-DROUTE_A_PINNED_SOURCE_SET="{source_hash}"',f'-DROUTE_A_PINNED_INSTRUMENTATION="{instrument_hash}"']
 flags+=['-I'+str(p) for p in inc]+['-I'+str(SOURCE/'src/OSspecific/POSIX/lnInclude')]
 commands=[]
 def compile_one(src):
  obj=out/(str(src.relative_to(overlay)) if overlay in src.parents else src.name)
  obj=obj.with_suffix('.o');obj.parent.mkdir(parents=True,exist_ok=True)
  cmd=['g++',*flags,'-c',str(src),'-o',str(obj)];commands.append(cmd)
  with obj.with_suffix('.compile.log').open('w') as log:
   r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError('COMPILE_FAILED '+str(obj.with_suffix('.compile.log')))
  return obj
 sources=[HERE/'NativeStageObserver.C',inst]
 sources+=list((overlay/'isothermalFluid').glob('*.C'))+list((overlay/'fluid').glob('*.C'))
 sources+=[overlay/'driver/foamRunDiagnostic.C',SOURCE/'applications/solvers/foamRun/setDeltaT.C',HERE/'synthetic_native_driver.C']
 # Dependency discovery reads only this diagnostic build's source graph.
 for unit in sources:
  text=subprocess.check_output(['g++',*flags,'-MM',str(unit)],text=True)
  dependencies=shlex.split(text.replace('\\\n',' ').split(':',1)[1])
  for name in dependencies:
   dependency=Path(name).resolve()
   if str(dependency).startswith(str(SOURCE)) and dependency.is_file():native[str(dependency)]=sha(dependency)
 source_hash=hashlib.sha256(json.dumps(native,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 flags=[arg if not arg.startswith('-DROUTE_A_PINNED_SOURCE_SET=') else f'-DROUTE_A_PINNED_SOURCE_SET=\"{source_hash}\"' for arg in flags]
 objects={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(compile_one,p):p for p in sources}
  for future in concurrent.futures.as_completed(futures):
   p=futures[future];objects[str(p)]=future.result();print('COMPILED',p.name,flush=True)
 links=['-L'+str(out),'-L'+str(LIB),'-L'+str(LIB/'openmpi-system'),'-Wl,-rpath,'+str(out),'-Wl,-rpath,'+str(LIB),'-Wl,-rpath,'+str(LIB/'openmpi-system')]
 libs=['-lfiniteVolume','-lmeshTools','-lOpenFOAM','-lPstream','-ldl']
 def link(name,objs,extra,shared=True,soname=None):
  cmd=['g++',*(['-shared'] if shared else []),*map(str,objs),*links,*extra,*libs,'-o',str(out/name)]
  if soname:cmd.insert(1,'-Wl,-soname,'+soname)
  commands.append(cmd)
  with (out/(name+'.link.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError('LINK_FAILED '+name)
  return out/name
 observer=link('librouteAU04Observer.so',[objects[str(HERE/'NativeStageObserver.C')]],['-l:libcrypto.so.3'])
 transport=link('libfluidThermoThermophysicalTransportModels.so',[objects[str(inst)]],['-lrouteAU04Observer','-lfluidThermophysicalTransportModel','-lfluidThermophysicalModels','-lsolidThermo','-lmomentumTransportModels','-lspecie'],soname='libfluidThermoThermophysicalTransportModels.so')
 iso=link('librouteADiagnosticIsothermalFluid.so',[objects[str(p)] for p in (overlay/'isothermalFluid').glob('*.C')],['-lrouteAU04Observer','-lfluidSolver','-lfluidThermophysicalModels','-lmomentumTransportModels','-lcompressibleMomentumTransportModels','-lsampling','-lfvModels','-lfvConstraints'])
 fluid=link('librouteADiagnosticFluid.so',[objects[str(p)] for p in (overlay/'fluid').glob('*.C')],['-lrouteAU04Observer','-lrouteADiagnosticIsothermalFluid','-lfluidSolver','-lfluidThermophysicalModels','-lcompressibleMomentumTransportModels','-lcoupledThermophysicalTransportModels','-lfluidThermoThermophysicalTransportModels'])
 foam=link('foamRunDiagnostic',[objects[str(overlay/'driver/foamRunDiagnostic.C')],objects[str(SOURCE/'applications/solvers/foamRun/setDeltaT.C')]],['-lrouteAU04Observer','-lfluidSolver'],shared=False)
 driver=link('synthetic_native_driver',[objects[str(HERE/'synthetic_native_driver.C')]],['-lrouteAU04Observer','-l:libcrypto.so.3'],shared=False)
 env=dict(os.environ);env['LD_LIBRARY_PATH']=str(out)+':'+str(LIB)+':'+str(LIB/'openmpi-system')+':'+env.get('LD_LIBRARY_PATH','')
 library_hashes={}
 for binary in [observer,transport,iso,fluid,foam,driver]:
  ldd=subprocess.check_output(['ldd',str(binary)],env=env,text=True);(out/(binary.name+'.ldd.log')).write_text(ldd)
  if 'not found' in ldd:raise RuntimeError('UNRESOLVED_LINKED_LIBRARY')
  for line in ldd.splitlines():
   if '=>' in line:
    path=Path(line.split('=>',1)[1].strip().split()[0])
    if path.is_file():library_hashes[str(path)]=sha(path)
 assert str(transport) in library_hashes,'Instrumented Fourier transport provider not linked'
 provenance={'classification':'DIAGNOSTIC_OVERLAY_AND_SYNTHETIC_BUILD_ONLY','source_set_sha256':source_hash,'instrumentation_sha256':instrument_hash,'native_source_sha256':native,'implementation_sha256':implementation,'compiler':subprocess.check_output(['g++','--version'],text=True),'environment':{k:os.environ.get(k) for k in ['WM_PROJECT_DIR','WM_PROJECT_VERSION','WM_OPTIONS','FOAM_LIBBIN','FOAM_MODULES']},'commands':commands,'binary_sha256':{str(p):sha(p) for p in [observer,transport,iso,fluid,foam,driver]},'linked_library_sha256':library_hashes,'official_binaries_modified':False,'production_run':False,'foamRunDiagnostic_executed':False}
 (out/'build_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print(json.dumps({'build':'PASS','source_set_sha256':source_hash,'instrumentation_sha256':instrument_hash}),flush=True)
if __name__=='__main__':build(sys.argv[1])
