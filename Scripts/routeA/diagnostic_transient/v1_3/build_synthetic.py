"""Compile only the replacement observer library; run only the saved native fixture."""
import hashlib,json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
P=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/u04_verification/final/build'
def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);a=json.loads((P/'build_provenance.json').read_text())
    for name,expected in a['native_source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected,name
    cmd=next(c for c in a['commands'] if '-c' in c and any(v.endswith('/NativeStageObserver.C') for v in c))
    cmd=[v.replace(str(H.parent/'v1_2'),str(H)) for v in cmd]
    cmd[cmd.index('-o')+1]=str(out/'NativeStageObserver.o')
    with (out/'compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    link=next(c for c in a['commands'] if str(P/'librouteAU04Observer.so') in c)
    link=[v.replace(str(P/'NativeStageObserver.o'),str(out/'NativeStageObserver.o')).replace(str(P/'librouteAU04Observer.so'),str(out/'librouteAU04Observer.so')) for v in link]
    with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True)
    (out/'build_provenance.json').write_text(json.dumps({'classification':'SYNTHETIC_RESOURCE_PIPELINE_TEST_NOT_CFD_RESULT','parent_build':str(P),'parent_native_source_sha256':a['native_source_sha256'],'commands':[cmd,link],'replacement_observer_sha256':hashlib.sha256((out/'librouteAU04Observer.so').read_bytes()).hexdigest(),'implementation_sha256':{str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(H.iterdir()) if p.suffix in {'.py','.H','.C'}},'production_binary_built':False},indent=2)+'\n')
if __name__=='__main__':build(sys.argv[1])
