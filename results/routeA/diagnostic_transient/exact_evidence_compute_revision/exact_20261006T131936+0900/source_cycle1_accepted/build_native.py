"""Build standalone diagnostic adapter only. No solver/OpenFOAM linkage or execution."""
import json,shutil,subprocess
from common import HERE,ROOT,PREP,sha,plan

def build(destination):
 plan();destination.mkdir(exist_ok=False)
 compiler=shutil.which('g++');need=__import__('common').need;need(compiler,'STOP_COMPILER_MISSING')
 binary=destination/'native_adapter'
 cmd=[compiler,'-std=c++14','-O2','-DROUTE_A_PERMISSION_HELPER='+json.dumps(str(HERE/'native_permission.py')),str(HERE/'native_adapter.C'),'/usr/lib/x86_64-linux-gnu/libcrypto.so.3','-o',str(binary)]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);(destination/'build.log').write_text(p.stdout+p.stderr);need(p.returncode==0,'STOP_ADAPTER_BUILD')
 receipt={'command':cmd,'compiler_realpath':str(__import__('pathlib').Path(compiler).resolve()),'compiler_SHA256':sha(compiler),'compiler_version':subprocess.check_output([compiler,'--version'],text=True),'source_SHA256':sha(HERE/'native_adapter.C'),'serializer_SHA256':sha(HERE/'DiagnosticJson.H'),'binary_SHA256':sha(binary),'classification':'RESOURCE_QUALIFICATION_FIXTURE_ONLY','CFD_linkage':False}
 (destination/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return binary
if __name__=='__main__':
 from pathlib import Path
 build(Path(__import__('sys').argv[1]))
