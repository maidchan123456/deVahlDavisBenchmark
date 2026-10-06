"""Read-only Git review plus production-sensitive byte identity guard."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

V2=Path(__file__).resolve().parent
PREP=V2.parent
ROOT=PREP.parents[3]
OLD='f57d60d85e36ea9928e4bc481d3cbde586496f58'
AUTHORITY={
 'docs/routeA_diagnostic_transient_contract_v1.5.json':'06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d',
 'docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def changes(base,head):
    fields=git('diff','--name-status','--no-renames','-z',base+'..'+head).decode().split('\0')
    records=[]
    for i in range(0,len(fields)-1,2):
        status,path=fields[i:i+2]
        if path in AUTHORITY or path.startswith('cases/') or path.startswith(('Scripts/','src/')):
            kind='PRODUCTION_SENSITIVE'
        elif path.startswith('results/'):
            name=Path(path).name
            kind='EXECUTION_EVIDENCE_ONLY' if any(x in name.lower() for x in ['launch','execution','preflight','authorization','manifest','git_','review','failure','prepare','finalize','validation','postprocess']) else 'RESULTS_ONLY'
        elif path.startswith('docs/') and Path(path).suffix in ['.md','.txt','.png','.pdf']:
            kind='DOCUMENTATION_ONLY_NONAUTHORITY'
        else:kind='OTHER'
        records.append({'change':status,'path':path,'classification':kind})
    return records

def verify_sensitive():
    m=json.loads((V2/'production_sensitive_manifest_v2.json').read_text())
    comparisons=[]
    for path,expected in m['files_sha256'].items():
        actual=sha(path)
        if actual!=expected:raise RuntimeError('BLOCKED_PRODUCTION_SENSITIVE_CHANGE: '+path)
        comparisons.append({'path':path,'prepared_or_reviewed_sha256':expected,'current_sha256':actual,'match':True})
    return comparisons

def reviewed_head_guard(plan):
    """Git HEAD is provenance; scientific/runtime/script byte hashes are authority."""
    comparisons=verify_sensitive()
    current=git('rev-parse','HEAD').decode().strip()
    reviewed=plan['reviewed_current_HEAD']
    if subprocess.run(['git','merge-base','--is-ancestor',reviewed,current],cwd=ROOT).returncode:
        raise RuntimeError('BLOCKED_PRODUCTION_SENSITIVE_CHANGE: current HEAD is not a descendant of reviewed provenance')
    delta=changes(reviewed,current) if current!=reviewed else []
    if any(r['classification'] in ['PRODUCTION_SENSITIVE','OTHER'] for r in delta):
        raise RuntimeError('BLOCKED_PRODUCTION_SENSITIVE_CHANGE: unreviewed sensitive/unknown Git path drift')
    if current!=reviewed:
        receipt=V2/('head_drift_review_'+current+'.json')
        record={'reviewed_base_HEAD':reviewed,'actual_launch_HEAD':current,'paths':delta,'sensitive_manifest_match':'PASS','equivalent':True,'reviewed_under_current_user_authorization':True,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if not receipt.exists():save(receipt,record)
    return current

def verify_package_and_authorization(plan):
    seal=json.loads((V2/'execution_package_seal_v2.json').read_text())
    for name,expected in seal.items():
        if sha(V2/name)!=expected:raise RuntimeError('BLOCKED_PRODUCTION_SENSITIVE_CHANGE: v2 package changed '+name)
    if sha(V2/'production_sensitive_manifest_v2.json')!=plan['production_sensitive_manifest_sha256']:
        raise RuntimeError('sensitive manifest changed')
    a=json.loads((V2/'production_authorization_v2.json').read_text())
    expected={'AUTHORIZED':'YES','authorization_class':'ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION',
      'preparation_id':PREP.name,'reviewed_HEAD':plan['reviewed_current_HEAD'],
      'production_sensitive_manifest_sha256':plan['production_sensitive_manifest_sha256'],
      'execution_plan_sha256':sha(V2/'production_execution_plan_v2.json'),'MPI_RANKS':12,'maxCo':.5,'endTime_s':1420,
      'CO05_ALLOWED':'YES','CO025_ALLOWED':'NO','AUTOMATIC_RESTART':'NO','AUTOMATIC_RERUN':'NO','Q3_ALLOWED':'NO','FORMAL_GATE_J_ALLOWED':'NO'}
    for key,value in expected.items():
        if a.get(key)!=value:raise RuntimeError('v2 authorization mismatch: '+key)
    source=Path(a['source_user_authorization_reference'])
    if sha(source)!=a['source_user_authorization_sha256']:raise RuntimeError('user authorization source changed')
    return a
