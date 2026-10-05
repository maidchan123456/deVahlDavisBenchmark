"""Delete only newly created synthetic copies in resource_revision_fix/lifecycle_test."""
import copy,hashlib,json,os,shutil
from pathlib import Path
import lifecycle,series_validation,selected_replay
from live_collector import Arrival
from launcher import LogPublisher
from log_rotation import RawLog
H=Path(__file__).resolve().parent;R=H.parents[3];PREP=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';OUT=PREP/'resource_revision_fix';BASE=OUT/'live_native_sealed_input/on';ROOT=OUT/'lifecycle_test_verified'

def main():
    ROOT.mkdir(exist_ok=False);contract=json.loads((R/'docs/routeA_diagnostic_transient_contract_v1.2.json').read_text());build=json.loads((PREP/'u04_verification/final/build/build_provenance.json').read_text());guard='574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675';source=build['source_set_sha256'];inst=build['instrumentation_sha256']
    failures=[]
    def reject(label,fn):
        try:fn()
        except (ValueError,OSError,KeyError,AssertionError,RuntimeError) as e:failures.append({'test':label,'status':'FAIL_CLOSED','reason':str(e)[:180]})
        else:raise AssertionError('NOT_FAIL_CLOSED '+label)
    def fixture(label,co=.5):
        path=ROOT/label;shutil.copytree(BASE,path)
        log=LogPublisher(path);raw=RawLog(log,1024);raw.write((OUT/'live_native_sealed_input/on.log').read_bytes());raw.flush();log.finish(0)
        row=series_validation.primary_rows(path)[0];arrival=Arrival(contract['physical_problem'],contract)
        for i in range(52):
            r=dict(row,dimensionless_time=i/100);arrival.add(r)
        assert arrival.confirmed and abs(arrival.confirmed['endpoint']-.5)<1e-15
        (path/'synthetic_arrival_fixture.json').write_text(json.dumps({'classification':'MANUFACTURED_CONSTANT_SCALAR_WINDOW_TEST_NOT_NATIVE_TRAJECTORY','confirmed':arrival.confirmed,'policy':'unmodified frozen U03'},sort_keys=True)+'\n')
        (path/'final_statistics.json').write_text(json.dumps(series_validation.final_analysis(path,True),sort_keys=True)+'\n')
        provenance={k:hashlib.sha256((k+':'+label).encode()).hexdigest() for k in lifecycle.PROVENANCE}
        # Synthetic provenance is explicitly test identity; actual native build/source/code hashes separately retained.
        (path/'provenance.json').write_text(json.dumps(provenance,sort_keys=True)+'\n')
        (path/'native_build_provenance.json').write_bytes((OUT/'native/build_retry/build_provenance.json').read_bytes())
        for name in ('validation_copy_1.bin','validation_copy_2.bin'):(path/name).write_bytes(b'SYNTHETIC_ONLY_TEMPORARY\0'*65536)
        classification={p.name:'R0' for p in path.iterdir()}
        for name in classification:
            if name.startswith(('full_','bundle_','anomaly_')) and name.endswith('.bin') or name=='final_bundle.bin':classification[name]='R1'
            if name in ('initial_state.bin','final_fields.bin') or name.startswith(('fields_','trigger_fields_')):classification[name]='R2'
            if name.startswith('validation_copy_'):classification[name]='R3'
        s=lifecycle.Series(path);s.begin()
        validator=lambda p:series_validation.validate(p,classification,guard,source,inst,True)
        return path,s,classification,provenance,validator,{'case_id':label,'Co':co,'start_time':row['time'],'end_time':row['time'],'classification':'SYNTHETIC_LIFECYCLE_TEST_NOT_CFD_RESULT'}
    def seal(f):
        p,s,c,prov,v,identity=f;sid=s.seal(c,identity,prov,v);return sid
    fA=fixture('seriesA');sid=seal(fA);plan=fA[1].dry_run(sid);before=series_validation.final_analysis(fA[0],True);sealbytes=(fA[0]/'series_seal_manifest.json').read_bytes()
    reject('missing_user_authorization',lambda:fA[1].purge(sid,plan['dry_run_id'],'',False))
    result=fA[1].purge(sid,plan['dry_run_id'],'cf611ff2-synthetic-only-explicit-task-authorization',True)
    fA[1].verify(sid);assert before==series_validation.final_analysis(fA[0],True);assert (fA[0]/'series_seal_manifest.json').read_bytes()==sealbytes
    extra={p.name for p in fA[0].iterdir()};replay=selected_replay.replay(fA[0],'final_bundle.bin',guard,source,inst,extra);assert replay['status']=='PASS'
    fB=fixture('seriesB',.25);sidB=seal(fB);comparison=series_validation.compare(fA[0],fB[0],True);assert not comparison['C3_trigger']
    mutated=copy.deepcopy(before);mutated['registered_final_mean']['Umax']+=1 # C3 test kept separate; no sealed core mutation.
    # Safety mutations operate on separately generated synthetic fixtures only.
    for label in ('missing_seal','invalid_seal_hash','unknown_file','R0_marked','R1_marked','symlink_escape','parent_traversal','changed_after_seal','partial_purge','interrupted_purge','missing_validation','R2_marked','changed_after_dry_run'):
        f=fixture(label);p,s,c,prov,v,identity=f
        if label=='missing_validation':reject(label,lambda:s.seal(c,identity,prov,lambda p:{'checks':{},'limitations':[]}));continue
        sealid=seal(f)
        if label=='missing_seal':(p/'series_seal_manifest.json').unlink()
        elif label=='invalid_seal_hash':(p/'series_seal_manifest.json').chmod(0o600);(p/'series_seal_manifest.json').write_bytes(b'{}\n')
        elif label=='unknown_file':(p/'unknown.bin').write_bytes(b'x')
        elif label in ('R0_marked','R1_marked','R2_marked','parent_traversal'):
            manifest=json.loads((p/'purge_manifest.json').read_text());manifest['entries'][0]['classification']={'R0_marked':'R0','R1_marked':'R1','R2_marked':'R2','parent_traversal':'R3'}[label]
            if label=='parent_traversal':manifest['entries'][0]['path']='../outside'
            (p/'purge_manifest.json').chmod(0o600);(p/'purge_manifest.json').write_text(json.dumps(manifest))
        elif label=='symlink_escape':(p/'validation_copy_1.bin').unlink();(p/'validation_copy_1.bin').symlink_to('/etc/passwd')
        elif label=='changed_after_seal':(p/'validation_copy_1.bin').write_bytes(b'changed')
        elif label=='partial_purge':(p/'validation_copy_1.bin').unlink()
        elif label=='interrupted_purge':
            pl=s.dry_run(sealid);reject('injected_interrupt',lambda:s.purge(sealid,pl['dry_run_id'],'synthetic-injection',True,inject_interrupt_after=1));reject(label,lambda:s.verify(sealid));reject('interrupted_no_auto_resume',lambda:s.dry_run(sealid));continue
        elif label=='changed_after_dry_run':
            pl=s.dry_run(sealid);(p/'validation_copy_2.bin').write_bytes(b'changed');reject(label,lambda:s.purge(sealid,pl['dry_run_id'],'synthetic-injection',True));assert (p/'validation_copy_1.bin').exists();continue
        reject(label,lambda:s.dry_run(sealid))
    reject('outside_registered_allowed_root',lambda:lifecycle.Series(R/'docs'))
    for unsafe in ('../x','a/b','..','/etc/passwd'):reject('path_'+unsafe,lambda:lifecycle.name(unsafe))
    report={'status':'PASS','scope':'NEW_SYNTHETIC_FIXTURES_ONLY','series_seal_test':'PASS','synthetic_purge_test':'PASS','post_purge_core_integrity':'PASS','post_purge_final_analysis_reproducible':True,'post_purge_selected59_replay':'PASS','cross_series_comparison_after_purge':'PASS','comparison':comparison,'bytes_reclaimed':result['bytes_reclaimed'],'retained_evidence':plan['retained_evidence'],'seal_id':sid,'immutable_seal_after_purge':True,'failure_injections':failures,'production_data_purged':False,'historical_data_purged':False,'limitations':'The native fixture is one manufactured step; the frozen U03 window test is a separate constant scalar fixture, never a production arrival claim.'}
    (OUT/'lifecycle_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('failure_injections','retained_evidence')},indent=2))
if __name__=='__main__':main()
