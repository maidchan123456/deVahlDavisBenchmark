"""Synthetic-only resource integration and mutation tests. Never executes foamRun."""
import copy,hashlib,json,os,shutil,struct,subprocess,sys,time,resource
from pathlib import Path
import packed,persistence,online_evaluator as online
H=Path(__file__).resolve().parent;R=H.parents[3];PREP=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';OLD=PREP/'u04_verification/final';OUT=PREP/'resource_revision'
sys.path.insert(0,str(H.parent/'v1_2'));import replay_evaluator as parent

def stop(gen):
    receipts=[]
    while True:
        try:receipts.append(next(gen))
        except StopIteration as s:return receipts,s.value

def main():
    tests=OUT/'tests';tests.mkdir(exist_ok=False)
    a=json.loads((OLD/'build/build_provenance.json').read_text());src=a['source_set_sha256'];inst=a['instrumentation_sha256'];guard='574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675'
    # Same already-verified native fixture, replacement library selected by loader.
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['ROUTE_A_P1_SERVER']=str(H/'server.py');env['ROUTE_A_P1_SERVER_SHA256']=packed.sha((H/'server.py').read_bytes())
    libs='/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib';runs={}
    for name,on,new in [('old_P0','on',False),('new_P1','on',True),('new_P1_repeat','on',True),('observer_off','off',True)]:
        env['LD_LIBRARY_PATH']=(str(OUT/'build')+':' if new else '')+str(OLD/'build')+':'+libs+':'+libs+'/openmpi-system'
        cmd=[str(OLD/'build/synthetic_native_driver'),str(tests/name),guard,src,inst,on,'none'];t=time.perf_counter()
        with (tests/(name+'.log')).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        runs[name]={'seconds':time.perf_counter()-t,'exit_code':r.returncode,'classification':'SYNTHETIC_RESOURCE_PIPELINE_TEST_NOT_CFD_RESULT'}
        assert r.returncode==0,(name,(tests/(name+'.log')).read_text()[-3500:])
    assert (tests/'new_P1.physical.json').read_bytes()==(tests/'observer_off.physical.json').read_bytes()==(tests/'old_P0.physical.json').read_bytes()
    for p in (tests/'new_P1').iterdir():assert p.read_bytes()==(tests/'new_P1_repeat'/p.name).read_bytes(),p.name
    assert persistence.verify(tests/'new_P1')['status']=='PASS'
    original=[json.loads(p.read_text()) for p in sorted((tests/'old_P0').glob('[0-9]*.json'))]
    old_summary=parent.replay(tests/'old_P0',guard,src,inst)
    receipts,summary=stop(online.evaluate(iter(original),guard,src,inst))
    sync=[s for r in receipts for s in r['synchronization']]
    assert parent.canonical(sync)==parent.canonical(old_summary['synchronization'])
    for k,v in old_summary.items():
        if k!='synchronization':assert parent.canonical(v)==parent.canonical(summary[k]),k
    for rec in original:
        assert parent.canonical(packed.decode(packed.encode(rec)))==parent.canonical(rec)
    z={'values':[0.,-0.,1.2345678901234567],'labels':[0,2**31-1,-1]}
    assert struct.pack('<d',packed.decode(packed.encode(z))['values'][1])==struct.pack('<d',-0.)
    # Selected complete step reload followed by the same online equations/ledger.
    selected=persistence.load_bundle((tests/'new_P1/full_2.bin').read_bytes(),tests/'new_P1')
    startup=original[:4];aux=[x for x in original if x['metadata']['stage']=='auxiliary_fixture']
    rr,ss=stop(online.evaluate(iter(startup+selected+aux),guard,src,inst))
    assert parent.canonical(ss)==parent.canonical(summary)
    assert parent.canonical([s for r in rr for s in r['synchronization']])==parent.canonical(sync)
    import selected_replay
    partial=selected_replay.replay(tests/'new_P1','final_bundle.bin',guard,src,inst)
    assert partial['selected_records']==59
    expected={r['sequence']:r for r in receipts}
    for rr in partial['receipts']:
        assert parent.canonical(rr)==parent.canonical(expected[rr['sequence']])
    failures=[]
    def reject(name,action):
        try:action()
        except (ValueError,OSError,KeyError,struct.error,AssertionError) as e:failures.append({'test':name,'status':'FAIL_CLOSED','reason':str(e)[:220]})
        else:raise AssertionError('SILENT_RECOVERY '+name)
    for name,mutate in {
        'wrong_epoch':lambda r:r[3]['metadata']['oldTime_ids']['rho'][0].update(time_index=999),
        'duplicate_step':lambda r:r.insert(6,copy.deepcopy(r[6])),
        'missing_step':lambda r:r.pop(6),
        'NaN':lambda r:r[5]['payload']['native_state_epoch']['rho']['cells'].__setitem__(0,float('nan')),
        'wrong_native_schema':lambda r:r[0]['metadata'].update(schema='wrong')
    }.items():
        rs=copy.deepcopy(original);mutate(rs);reject(name,lambda:stop(online.evaluate(iter(rs),guard,src,inst)))
    raw=packed.encode(z)
    reject('truncated_binary',lambda:packed.decode(raw[:-1]))
    reject('wrong_hash',lambda:packed.decode(raw[:-1]+bytes([raw[-1]^1])))
    for key,value in [('schema','wrong'),('endian','big'),('shape',[99])]:
        n=struct.unpack('<Q',raw[6:14])[0];head=json.loads(raw[14:14+n]);data=raw[14+n:]
        if key=='shape':head['arrays'][0]['shape']=value
        else:head[key]=value
        h=json.dumps(head,separators=(',',':')).encode();bad=b'RAP13\0'+struct.pack('<Q',len(h))+h+data
        reject('wrong_'+key,lambda:packed.decode(bad))
    for name in ['missing_chunk','bad_manifest','partial_commit']:
        dest=tests/name;shutil.copytree(tests/'new_P1',dest)
        if name=='missing_chunk':next(dest.glob('chunk_*.bin')).unlink()
        elif name=='bad_manifest':(dest/'manifest.jsonl').write_bytes((dest/'manifest.jsonl').read_bytes()+b'{}\n')
        else:(dest/'interrupted.partial').write_bytes(b'partial')
        reject(name,lambda:persistence.verify(dest))
    # Test data-write, scratch/memory quota and mandatory snapshot failure propagation.
    w=persistence.Writer(tests/'small_ring',ring_cap=64,stage_cap=1)
    reject('scratch_stage_quota',lambda:w.accept(original[0],receipts[0]))
    w2=persistence.Writer(tests/'failed_field');reject('mandatory_field_failure',lambda:w2.snapshot({'cells':[float('nan')]},'field.bin'))
    # Native evaluator failure must cross ACK boundary and invalidate the fixture.
    env['LD_LIBRARY_PATH']=str(OUT/'build')+':'+str(OLD/'build')+':'+libs+':'+libs+'/openmpi-system'
    cmd=[str(OLD/'build/synthetic_native_driver'),str(tests/'native_failure'),guard,src,inst,'on','wrongdimensions']
    with (tests/'native_failure.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
    assert r.returncode!=0 and not (tests/'native_failure/complete.json').exists()
    failures.append({'test':'native_ack_failure_propagation','status':'FAIL_CLOSED'})
    def stats(root):
        files=[p for p in root.iterdir() if p.is_file()];return {'bytes':sum(p.stat().st_size for p in files),'files':len(files)}
    old=stats(tests/'old_P0');new=stats(tests/'new_P1')
    # One-step native fixture has one final compact chunk, fields2,audits2,summary.
    entries=[json.loads(x) for x in (tests/'new_P1/manifest.jsonl').read_text().splitlines()]
    report={'status':'PASS','classification':'SYNTHETIC_RESOURCE_PIPELINE_TEST_NOT_CFD_RESULT','runs':runs,'old':dict(old,fsync_calls=3*len(original)+2),'new':dict(new,fsync_calls=3*len(entries)+2),'reduction_factor':old['bytes']/new['bytes'],'online_reduction_equivalence':'BITWISE','selected_raw_replay':'PASS','selected59_partial_replay':'PASS','non_invasiveness':'BITWISE','repeatability':'PASS','all_stage_count':len(receipts),'parent_summary_equivalence':'BITWISE','failure_injections':failures,'source_set_sha256':src,'native_semantic_instrumentation_sha256':inst,'peak_child_RSS_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'not_production_speedup':True,'production_solver_executed':False,'case_generated':False}
    (OUT/'synthetic_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
