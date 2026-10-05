"""Persistence boundaries and registered guards, using no solver or mesh."""
import json,math,struct,tempfile
from pathlib import Path
import persistence as p,packed
from resource_guard import preflight

def run(output):
    root=Path(output);root.mkdir(exist_ok=False);checks=[]
    w=p.Writer(root/'chunks')
    seq=0
    for i in range(65):
        for stage in ['time_start','time_end']:
            seq+=1;m={'stage':stage,'time_index':i+1,'outer':24 if stage=='time_end' else 0,'pressure':0,'nonOrthogonal':0,'energy_solve':0,'rho_solve':0,'physical_time':(i+1)*1e-5,'deltaT':1e-5,'previous_deltaT':1e-5}
            r={'sequence':seq,'metadata':m,'payload':{'native_state_epoch':{}},'payload_sha256':packed.sha(b'{}')}
            receipt={'sequence':seq,'metadata':m,'payload_sha256':r['payload_sha256'],'matrix_metrics':{},'term_metrics':{},'synchronization':[],'valid':True}
            w.accept(r,receipt)
    w.anomaly('UNIT_BUFFER_FLUSH');w.finish({'status':'PERSISTENCE_UNIT_ONLY_NOT_PHYSICS_VALIDATION'})
    assert p.verify(root/'chunks')['events']==130
    assert len(list((root/'chunks').glob('chunk_*.bin')))==2
    assert w.peak_ring_bytes<=min(16*p.STAGE_CAP,p.RING_CAP)
    checks.append('64-step chunk then1-step terminal chunk, recent16 anomaly flush and full scratch streaming PASS')
    for co,authorized,free,files,inodes in [(.125,False,10**12,100,10000),(.5,False,1,100,10000),(.5,False,10**12,100,1)]:
        try:preflight(root,1000,files,co,authorized,free,inodes)
        except ValueError:checks.append(f'resource guard Co={co} free={free} inodes={inodes} FAIL_CLOSED')
        else:raise AssertionError('GUARD_BYPASS')
    from log_rotation import RawLog
    log=p.Writer(root/'logs');rotation=RawLog(log,chunk_bytes=7)
    raw=b'0\x00line1\nline2\xffEND';rotation.write(raw[:3]);rotation.write(raw[3:]);rotation.flush()
    restored=b''.join(path.read_bytes() for path in sorted((root/'logs').glob('raw_log_*.bin')))
    assert restored==raw;checks.append('lossless byte log rotation/order/hash manifest PASS')
    from server import classification_guard
    try:classification_guard('DIAGNOSTIC_OBSERVATION')
    except ValueError:checks.append('unqualified production primary binding STOP PASS')
    else:raise AssertionError('PRODUCTION_GUARD_BYPASS')
    s=p.Schedule()
    for i in range(1,200001):s.begin(710*(2*i/200000))
    assert s.full_count==7 and s.bundle_count==40 and s.field_count==441
    checks.append('max t*2 schedule7full/40periodic bundles/441base fields per series PASS')
    (root/'unit_results.json').write_text(json.dumps({'status':'PASS','classification':'PERSISTENCE_UNIT_TEST_NOT_CFD_RESULT','checks':checks,'peak_ring_bytes':w.peak_ring_bytes,'chunk_steps':p.CHUNK_STEPS},indent=2)+'\n')
if __name__=='__main__':
    import sys
    run(sys.argv[1])
