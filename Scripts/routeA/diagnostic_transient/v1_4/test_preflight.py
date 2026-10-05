"""Read-only future-launcher guard tests; no native process or case creation."""
import copy,json
from pathlib import Path
import launcher,resource_guard
H=Path(__file__).resolve().parent;R=H.parents[3];OUT=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/resource_revision_fix'
def main():
    contract=R/'docs/routeA_diagnostic_transient_contract_v1.4.json';c=json.loads(contract.read_text());model=c['resource_revision_fix']['capacity']['series']['0.5'];lib=OUT/'native/build_verified/librouteAU04Observer.so'
    # Hash-mechanism fixture, not a claim that future cold-start inputs already exist.
    paths={'contract':contract,'input':R/'docs/routeA_diagnostic_transient_contract_v1.2.json','mesh':R/'cases/routeA/A-Ra1e6-fine/constant/polyMesh/boundary','source':H/'NativeStageObserver.C','instrumentation':H/'server.py','binary':OUT/'native/build_retry/binding_driver','libraries':lib,'compiler':OUT/'native/build_verified/build_provenance.json','analysis':H/'series_validation.py'}
    spec={'case_id':'A-DT-Ra1e6-fine-Co0p5','Co':.5,'export_root':str(R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/series/A-DT-Ra1e6-fine-Co0p5'),'provenance':{k:[{'path':str(p),'sha256':launcher.hash_file(p)}] for k,p in paths.items()},'planned_peak_bytes':model['working_peak_bytes'],'post_seal_bytes':model['permanent_bytes'],'planned_files':model['file_bound'],'existing_permanent_bytes':0,'previous_series_seals':[]}
    result=launcher.prepare(spec);assert result['RESOURCE_PREFLIGHT_PASS'] and not result['resource_ready'];assert not Path(spec['export_root']).exists()
    failures=[]
    def reject(label,fn):
        try:fn()
        except (ValueError,OSError,KeyError,AssertionError) as e:failures.append({'test':label,'status':'FAIL_CLOSED','reason':str(e)})
        else:raise AssertionError(label)
    reject('resource_ready_NO_blocks_run',lambda:launcher.run(spec,'SYNTHETIC_GUARD_TEST_NOT_RUN_AUTHORIZATION'))
    for label,mutate in {'hash_mismatch':lambda s:s['provenance']['source'][0].update(sha256='0'*64),'wrong_series_identity':lambda s:s.update(case_id='WRONG'),'unregistered_working_peak':lambda s:s.update(planned_peak_bytes=1),'unmeasured_previous_footprint':lambda s:s.update(existing_permanent_bytes=1),'missing_prior_Co05_seal':lambda s:s.update(Co=.25,case_id='A-DT-Ra1e6-fine-Co0p25'),'missing_pinned_observer':lambda s:s['provenance']['libraries'].__setitem__(0,s['provenance']['contract'][0])}.items():
        s=copy.deepcopy(spec);mutate(s);reject(label,lambda:launcher.prepare(s))
    reject('free_disk',lambda:resource_guard.preflight(OUT,10**9,100,free_override=1000))
    reject('free_inodes',lambda:resource_guard.preflight(OUT,10**6,100,inodes_override=1))
    reject('C3_stop_before_execution',lambda:resource_guard.preflight(OUT,10**6,100,co=.125))
    assert not Path(spec['export_root']).exists()
    report={'status':'PASS','classification':'READ_ONLY_PREFLIGHT_BINDING_TEST_NO_CFD','provenance_fixture_not_future_case_configuration':True,'read_only_prepare':True,'actual_free_bytes':result['free_bytes'],'actual_free_inodes':result['free_inodes'],'actual_RAM_available_bytes':result['memory_available_bytes'],'Co05_planned_peak':result['planned_peak'],'safety_bytes':result['safety_bytes'],'run_blocked_resource_ready_NO':True,'failure_injections':failures,'case_created':False,'production_solver_executed':False}
    (OUT/'preflight_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
