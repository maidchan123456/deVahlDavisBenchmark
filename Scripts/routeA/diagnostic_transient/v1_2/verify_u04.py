"""Execute only the synthetic binary; never runs diagnostic foamRun or a case."""
import argparse,copy,hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
import replay_evaluator as replay
HERE=Path(__file__).resolve().parent
PARENT_SHA='574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675'

def verify(build,output):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    build=Path(build).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    prov=json.loads((build/'build_provenance.json').read_text());src=prov['source_set_sha256'];inst=prov['instrumentation_sha256']
    # Refuse drift of the compiled/source/schema/loader authority before execution.
    for group in ['native_source_sha256','binary_sha256','linked_library_sha256']:
        for name,expected in prov[group].items():assert replay.sha(Path(name).read_bytes())==expected,'FROZEN_ARTIFACT_DRIFT '+name
    for name,expected in prov['implementation_sha256'].items():assert replay.sha((HERE/name).read_bytes())==expected,'INSTRUMENTATION_DRIFT '+name
    env=dict(os.environ);env['LD_LIBRARY_PATH']=str(build)+':/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib:/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib/openmpi-system'
    runs={};summaries={}
    def driver(name,on='on',inject='none',source=src):
        root=output/name;cmd=[str(build/'synthetic_native_driver'),str(root),PARENT_SHA,source,inst,on,inject]
        started=time.perf_counter()
        with (output/(name+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        elapsed=time.perf_counter()-started
        runs[name]={'exit_code':r.returncode,'elapsed_s':elapsed,'command':cmd,'classification':'SYNTHETIC_EVALUATOR_TEST'}
        if not inject.startswith('none') and inject!='stationary':
            assert r.returncode!=0 and not (root/'complete.json').exists(),(name,'failure did not propagate')
        else:
            assert r.returncode==0,(name,(output/(name+'.log')).read_text()[-1800:])
            summary=json.loads(next(line[len('U04_SUMMARY '):] for line in (output/(name+'.log')).read_text().splitlines() if line.startswith('U04_SUMMARY ')))
            summaries[name]=summary
        return root
    first=driver('observed_1');second=driver('observed_2');off=driver('observer_off','off')
    assert summaries['observed_1']['physical_fingerprint_sha256']==summaries['observer_off']['physical_fingerprint_sha256']
    assert (output/'observed_1.physical.json').read_bytes()==(output/'observer_off.physical.json').read_bytes(),'NON_INVASIVENESS_FAIL'
    assert summaries['observed_1']==summaries['observed_2'],'SUMMARY_NONDETERMINISM'
    for name in sorted(p.name for p in first.iterdir()):
        assert (first/name).read_bytes()==(second/name).read_bytes(),('EXPORT_NONDETERMINISM',name)
    replays={}
    for name in ['observed_1','observed_2']:
        replays[name]=replay.replay(output/name,PARENT_SHA,src,inst)
        (output/(name+'.replay.json')).write_text(json.dumps(replays[name],indent=2)+'\n')
    assert replays['observed_1']==replays['observed_2']
    stationary=driver('stationary','on','stationary');replays['stationary']=replay.replay(stationary,PARENT_SHA,src,inst)
    (output/'stationary.replay.json').write_text(json.dumps(replays['stationary'],indent=2)+'\n')
    # First stationary mass stage has actual constant native histories andzerophi.
    mass=[]
    for p in sorted(stationary.glob('[0-9]*.json')):
        r=json.loads(p.read_text())
        if r['metadata']['stage']=='mass_after_solve':mass.append(r)
    require=mass[0]['payload'];assert all(abs(v)<=require['unrelaxed_matrix']['arithmetic_bound'] for v in require['term_actions']['D_B_rho'])
    assert sum(v for patch in require['state']['phi']['patches'] for v in patch['values'])==0
    failures=[]
    for name in ['missing','duplicate','nan','wrongdimensions']:
        driver('injected_'+name,'on',name);failures.append({'name':name,'layer':'native_callback','status':'FAIL_CLOSED'})
    driver('injected_wrongsource','on','wrongsource',source='0'*64);failures.append({'name':'wrong_source','layer':'native_bootstrap','status':'FAIL_CLOSED'})
    def rewrite(root,records):
        manifest=[]
        for i,r in enumerate(records,1):
            r['payload_sha256']=replay.sha(replay.canonical(r['payload']).encode())
            raw=(replay.canonical(r)+'\n').encode();name=f'{i:08}.json';(root/name).write_bytes(raw)
            manifest.append({'file':name,'sequence':i,'sha256':replay.sha(raw)})
        raw=('\n'.join(replay.canonical(x) for x in manifest)+'\n').encode();(root/'manifest.jsonl').write_bytes(raw)
        (root/'complete.json').write_text(replay.canonical({'complete':True,'records':len(records),'manifest_sha256':replay.sha(raw)})+'\n')
    original=[json.loads(p.read_text()) for p in sorted(first.glob('[0-9]*.json'))]
    mutations={
        'wrong_epoch':lambda rs:rs[3]['metadata']['oldTime_ids']['rho'][0].update(time_index=999),
        'wrong_matrix_identity':lambda rs:next(r for r in rs if r['metadata']['stage']=='energy_after_solve')['payload']['unrelaxed_matrix'].update(matrix_epoch='0'*64),
        'wrong_units':lambda rs:next(r for r in rs if r['metadata']['stage']=='term_capture' and r['payload']['term']=='S_K')['payload'].update(dimensions=replay.MASS),
        'wrong_corrector_index':lambda rs:next(r for r in rs if r['metadata']['stage']=='outer_start')['metadata'].update(outer=7),
        'wrong_time_index':lambda rs:next(r for r in rs if r['metadata']['stage']=='energy_begin')['metadata'].update(time_index=999),
        'wrong_bc_epoch':lambda rs:rs[4]['metadata']['bc_epochs'].update(rho='0'*64),
        'reordered':lambda rs:rs.__setitem__(slice(5,7),list(reversed(rs[5:7]))),
        'duplicate':lambda rs:rs.insert(5,copy.deepcopy(rs[5])),
        'missing':lambda rs:rs.pop(5),
        'wrong_guard':lambda rs:rs[0]['metadata'].update(study_guard_sha256='0'*64),
        'nan_payload':lambda rs:rs[0]['payload']['native_state_epoch']['rho']['cells'].__setitem__(0,float('nan')),
    }
    for name,mutate in mutations.items():
        root=output/('replay_injected_'+name);shutil.copytree(first,root);records=copy.deepcopy(original);mutate(records)
        if name=='nan_payload':
            raw=json.dumps(records[0],allow_nan=True).encode();path=root/'00000001.json';path.write_bytes(raw)
            # A malformed/nonfinite packet fails file/payload checks; no repair.
        else:rewrite(root,records)
        try:replay.replay(root,PARENT_SHA,src,inst)
        except (replay.EvaluatorFailure,ValueError,KeyError,OSError) as exc:failures.append({'name':name,'layer':'offline_replay','status':'FAIL_CLOSED','reason':str(exc)})
        else:raise AssertionError('SILENT_RECOVERY_'+name)
    # Dedicated interrupted atomic-write evidence (no completion / orphan).
    for name in ['partial_packet','missing_completion']:
        root=output/('replay_injected_'+name);shutil.copytree(first,root)
        if name=='partial_packet':(root/'orphan.partial').write_bytes(b'partial')
        else:(root/'complete.json').unlink()
        try:replay.replay(root,PARENT_SHA,src,inst)
        except (replay.EvaluatorFailure,OSError,ValueError) as exc:failures.append({'name':name,'layer':'atomic_export','status':'FAIL_CLOSED','reason':str(exc)})
        else:raise AssertionError('PARTIAL_WRITE_ACCEPTED')
    summary={'status':'PASS','source_set_sha256':src,'instrumentation_sha256':inst,'native_driver_runs':runs,'native_replay':replays['observed_1'],'non_invasiveness':'BITWISE','matrix_source_boundary_field_oldTime_time_solver_residual_fingerprints_identical':True,'non_invasiveness_fingerprint':summaries['observed_1']['physical_fingerprint_sha256'],'repeatability':'BITWISE_RECORD_PAYLOAD_MANIFEST_AND_SUMMARY','failure_injections':failures,'failure_injection_count':len(failures),'floor_scope':'SYNTHETIC_ONLY','observed_peak_child_rss_KiB_scope':'aggregate children maximum, not paired process-memory overhead','output_bytes':sum(p.stat().st_size for p in first.iterdir()),'peak_children_rss_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'production_solver_executed':False,'diagnostic_transient_executed':False,'synthetic_case_directory_exists':Path('/tmp/routeA-u04-in-memory-no-case').exists()}
    assert not summary['synthetic_case_directory_exists']
    (output/'verification_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['native_driver_runs','failure_injections']},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('output');a=ap.parse_args();verify(a.build,a.output)
