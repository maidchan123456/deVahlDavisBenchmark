"""Reviewed provenance plus fail-closed byte integrity, never CFD."""
import hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_package(plan):
 for name,h in json.loads((P/'execution_package_seal.json').read_text()).items():
  if sha(P/name)!=h:raise RuntimeError('package hash mismatch: '+name)
 if sha(P/'production_sensitive_manifest.json')!=plan['production_sensitive_manifest_sha256']:raise RuntimeError('sensitive manifest changed')
 for path,h in json.loads((P/'production_sensitive_manifest.json').read_text())['files_sha256'].items():
  if sha(path)!=h:raise RuntimeError('production-sensitive mismatch: '+path)
def classify(path):
 if path.startswith(('cases/','Scripts/','src/')) or path.startswith('docs/') and Path(path).suffix=='.json':return 'PRODUCTION_SENSITIVE'
 if path.startswith('results/'):return 'RESULTS_ONLY'
 if path.startswith('docs/') and Path(path).suffix in ['.md','.txt','.png','.pdf']:return 'DOCUMENTATION_ONLY_NONAUTHORITY'
 return 'OTHER'
def reviewed_head_guard(plan):
 verify_package(plan)
 current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();reviewed=plan['reviewed_current_HEAD']
 if subprocess.run(['git','merge-base','--is-ancestor',reviewed,current],cwd=ROOT).returncode:raise RuntimeError('HEAD not descended from reviewed provenance')
 rows=[]
 if current!=reviewed:
  fields=subprocess.check_output(['git','diff','--name-status','--no-renames','-z',reviewed+'..'+current],cwd=ROOT).decode().split('\0')
  for i in range(0,len(fields)-1,2):
   status,path=fields[i:i+2];kind=classify(path);rows.append({'change':status,'path':path,'classification':kind})
   if kind not in ['RESULTS_ONLY','DOCUMENTATION_ONLY_NONAUTHORITY']:raise RuntimeError('HEAD change requires sensitive review: '+path)
  receipt=P/('head_drift_review_'+current+'.json')
  if not receipt.exists():receipt.write_text(json.dumps({'reviewed_HEAD':reviewed,'execution_HEAD':current,'changes':rows,'sensitive_hashes':'PASS'},indent=2)+'\n')
 return current
