"""Verify candidate/report integrity and frozen parents, without any solver."""
import hashlib,json,math,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];PREP=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';OUT=PREP/'resource_revision';H=R/'Scripts/routeA/diagnostic_transient/v1_3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    r=read(PREP/'DiagnosticTransient_resource_revision.json');c=read(R/'docs/routeA_diagnostic_transient_contract_v1.3.json');p=read(R/'docs/routeA_diagnostic_transient_contract_v1.2.json');a=r['authority'];checks=[]
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==a['HEAD']=='ed2371e88c2d728bfbf8fffd21cd99497c1b9afc'
    assert subprocess.check_output(['git','diff','--stat'],cwd=R,text=True)==''
    assert subprocess.check_output(['git','diff','--cached','--stat'],cwd=R,text=True)==''
    for name,expected in a['protected_sha256'].items():assert sha(R/name)==expected,name
    for name,expected in a['implementation_sha256'].items():assert sha(R/name)==expected,name
    for name,expected in a['native_parent_source_sha256'].items():assert sha(name)==expected,name
    for key in r['invariant_keys']:assert c[key]==p[key],key
    checks.append('Parent contracts, direct review authorities, frozen native sources and semantic invariant sections unchanged')
    # Prove actual native hooks/stage/operator bodies are inherited verbatim.
    old=(H.parent/'v1_2/NativeStageObserver.C').read_text();new=(H/'NativeStageObserver.C').read_text()
    def body(text,signature):
        start=text.index(signature);left=text.index('{',start);depth=1;i=left+1
        while depth:
            depth+=(text[i]=='{')-(text[i]=='}');i+=1
        return text[start:i]
    functions=['void Observer::transition(', 'void Observer::stage(', 'void Observer::term(const std::string& name,const fvScalarMatrix&', 'void Observer::total(', 'void Observer::solved(', 'void reference(', 'void history(', 'void thermal(', 'Json matrixPacket(', 'Json meshState(', 'Json Observer::metadata(']
    # Signature whitespace is inherited; locate term by its actual overload header.
    functions[2]=next(line.split('{')[0] for line in old.splitlines() if line.startswith('void Observer::term(') and 'fvScalarMatrix' in line)
    for signature in functions:assert body(old,signature)==body(new,signature),signature
    checks.append('Native transition/stage/math/operator hook bodies equal parent; only persistence changed')
    contract_sha=sha(R/'docs/routeA_diagnostic_transient_contract_v1.3.json')
    assert contract_sha==r['status']['DIAGNOSTIC_CONTRACT_SHA256']
    assert (R/'docs/routeA_diagnostic_transient_contract_v1.3.sha256').read_text().split()[0]==contract_sha
    assert not c['execution_authorized'] and not c['resource_revision']['complete'] and c['unresolved_items']
    assert r['status']['ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION']=='INCOMPLETE'
    assert r['status']['DIAGNOSTIC_TRANSIENT_STORAGE_READY']==r['status']['DIAGNOSTIC_TRANSIENT_RESOURCE_READY']=='NO'
    checks.append('INCOMPLETE candidate and fail-closed readiness/execution guards remain explicit')
    for s in r['capacity']['scenarios']:
        for series in s['series']:
            assert sum(series['parts'].values())==series['retained_bytes']
            assert series['receipt_chunks']==math.ceil(series['steps']/64)
        assert s['primary_retained_bytes']==sum(v['retained_bytes'] for v in s['series'][:2])
        assert s['three_retained_bytes']==sum(v['retained_bytes'] for v in s['series'])
        assert s['primary_peak_bytes']==s['primary_retained_bytes']+16*2**30
        assert s['three_peak_bytes']==s['three_retained_bytes']+16*2**30
        assert s['primary_file_count']==sum(v['file_count_bound'] for v in s['series'][:2])
    checks.append('Scenario byte/component/step/chunk/file arithmetic consistent')
    md=(PREP/'DiagnosticTransient_resource_revision.md').read_text()
    assert sum(line.startswith('## ') and line[3:4].isdigit() for line in md.splitlines())==23
    status=(OUT/'final_status.txt').read_text()
    for key,value in r['status'].items():assert f'{key} = {value}' in md and f'{key} = {value}' in status
    checks.append('23-section report, JSON, contract SHA and required final status consistent')
    # Check healthy input manifest and the accepted steady arrays actually read.
    stream=PREP/'u04_verification/final/tests/observed_1';inputs={}
    for line in (stream/'manifest.jsonl').read_text().splitlines():
        e=json.loads(line);path=stream/e['file'];assert sha(path)==e['sha256'];inputs[str(path.relative_to(R))]=e['sha256']
    assert len(inputs)==1152
    prior=read(PREP/'resource_review/resource_accounting.json')
    for item in prior['actual_fields']:
        for f in item['files']:assert sha(R/f['path'])==f['sha256'];inputs[f['path']]=f['sha256']
    # OFF/P0/P1 fixture results remain bitwise equal and selected manifests valid.
    import sys
    sys.path.insert(0,str(H));from persistence import verify
    t=OUT/'tests';assert verify(t/'new_P1')['status']=='PASS';assert verify(t/'new_P1_repeat')['status']=='PASS'
    assert (t/'new_P1.physical.json').read_bytes()==(t/'observer_off.physical.json').read_bytes()==(t/'old_P0.physical.json').read_bytes()
    for f in (t/'new_P1').iterdir():assert f.read_bytes()==(t/'new_P1_repeat'/f.name).read_bytes()
    assert r['synthetic_validation']['status']=='PASS' and all(f['status']=='FAIL_CLOSED' for f in r['synthetic_validation']['failure_injections'])
    checks.append('Saved synthetic equality/repeatability/manifest checks PASS; existing inputs unchanged; no CFD executed')
    (OUT/'verified_inputs_sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
    result={'result':'PASS','meaning':'artifact/invariant integrity PASS, not completion of blocked resource revision','checks':checks,'protected_existing_files':len(a['protected_sha256']),'native_source_files':len(a['native_parent_source_sha256']),'healthy_native_input_packets':1152,'resource_revision':'INCOMPLETE','solver_executed':False}
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'end_git_status.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=R,text=True))
    (OUT/'end_git_diff_stat.txt').write_text(subprocess.check_output(['git','diff','--stat'],cwd=R,text=True))
    artifacts=[path for path in OUT.rglob('*') if path.is_file() and path.name!='artifact_sha256.json']+list(H.iterdir())+list((R/'docs').glob('routeA_diagnostic_transient_contract_v1.3.*'))+list(PREP.glob('DiagnosticTransient_resource_revision.*'))+list(PREP.glob('DiagnosticTransient_v1_3_*.csv'))+[Path(__file__),R/'Scripts/routeA/resource_review/prepare_resource_revision.py']
    (OUT/'artifact_sha256.json').write_text(json.dumps({str(path.relative_to(R)):sha(path) for path in sorted(set(artifacts)) if path.is_file()},indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
