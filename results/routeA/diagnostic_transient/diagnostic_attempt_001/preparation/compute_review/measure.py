"""Bounded SYNTHETIC_ONLY measurements. No physical case, solver or purge."""
import gc, hashlib, json, os, resource, statistics, subprocess, sys, time
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[5]
PREP=OUT.parent
H=ROOT/'Scripts/routeA/diagnostic_transient/v1_4'
sys.path.insert(0,str(H))

def write(name,x): (OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cpu():
    values=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    return {'total':sum(values),'idle':values[3]+values[4]}

def native():
    driver=PREP/'resource_revision_fix/native/build_retry/binding_driver'
    build=PREP/'resource_revision_fix/native/build_verified'
    old=PREP/'u04_verification/final/build'
    a=json.loads((old/'build_provenance.json').read_text())
    guard='574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675'
    libs='/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib'
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',ROUTE_A_P1_SERVER=str(H/'server.py'),
        ROUTE_A_P1_SERVER_SHA256=digest(H/'server.py'),ROUTE_A_BIND_LIVE='1',ROUTE_A_SYNTHETIC_LIVE='1',
        ROUTE_A_DIAGNOSTIC_CONTRACT_FILE=str(ROOT/'docs/routeA_diagnostic_transient_contract_v1.2.json'),
        ROUTE_A_FIXTURE_SHA256=digest(H/'synthetic_native_binding_driver.C'),
        LD_LIBRARY_PATH=str(build)+':'+str(old)+':'+libs+':'+libs+'/openmpi-system')
    trials=[];start=time.monotonic()
    for trial in range(3):
        for mode in ('off','on') if trial%2==0 else ('on','off'):
            if time.monotonic()-start>100:break
            target=OUT/f'native_{trial}_{mode}';assert not target.exists()
            cmd=['/usr/bin/time','-f','%e %U %S %M','-o',str(OUT/f'time_{trial}_{mode}.txt'),
                 str(driver),str(target),guard,a['source_set_sha256'],a['instrumentation_sha256'],mode,'none']
            load=os.getloadavg();before=cpu();t=time.perf_counter()
            with (OUT/f'native_{trial}_{mode}.log').open('x') as log:
                p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=35)
            dt=time.perf_counter()-t;after=cpu();assert p.returncode==0,(trial,mode)
            tm=list(map(float,(OUT/f'time_{trial}_{mode}.txt').read_text().split()))
            row={'trial':trial,'mode':mode,'wall_seconds':dt,'cpu_user_seconds':tm[1],'cpu_system_seconds':tm[2],
                 'max_process_rss_KiB':tm[3], 'load_average_before':load,
                 'host_busy_fraction':1-(after['idle']-before['idle'])/max(1,after['total']-before['total'])}
            if mode=='on':
                manifest=[json.loads(x) for x in (target/'manifest.jsonl').read_text().splitlines()]
                complete=json.loads((target/'complete.json').read_text());row.update(events=complete['events'],steps=complete['steps'],
                    persisted_bytes=sum(x['bytes'] for x in manifest),artifacts=len(manifest))
                primary=json.loads(next(target.glob('primary_*.jsonl')).read_text().splitlines()[0])
                row['linear_record_count']=len(primary['linear_solves'])
                row['linear_records_by_field']={key:sum(x['field']==key for x in primary['linear_solves']) for key in {x['field'] for x in primary['linear_solves']}}
            trials.append(row);write('native_timings.json',{'classification':'SYNTHETIC_ONLY_FOUR_CELL_ONE_STEP_WITH_AUXILIARY_FIXTURES',
                'driver_sha256':digest(driver),'observer_sha256':digest(build/'librouteAU04Observer.so'),
                'historical_fixture_authority':'v1.1 guard/v1.2 definitions; not canonical production v1.5 run',
                'RSS_scope':'GNU time maximum single-process RSS in process tree; not simultaneous native+backend sum',
                'trials':trials})
            print('native',trial,mode,round(dt,3),flush=True)

def primitives():
    import numpy as np
    import online_evaluator as evaluator
    import packed,primary_evidence
    contract=json.loads((ROOT/'docs/routeA_diagnostic_transient_contract_v1.5.json').read_text())
    n=25600;nx=160;L=.1;dx=L/nx
    points=np.array([[(x+.5)*dx,(y+.5)*dx,.0005] for y in range(nx) for x in range(nx)])
    U=np.zeros((n,3));U[:,0]=np.sin(2*np.pi*points[:,0]/L);U[:,1]=np.cos(2*np.pi*points[:,1]/L)
    # Data-shape fixtures only: these arrays are never OpenFOAM initial fields.
    state={'U':{'cells':U.tolist()},'T':{'cells':(300+.2*np.sin(points[:,0])).tolist()},
           'volumes':[dx*dx*.001]*n}
    for key in ('rho','e','K','p','p_rgh','gh','rhoFluidThermo:rho'):
        state[key]={'cells':[1.+i*1e-7 for i in range(n)],'old_times':
                    [{'cells':[1.+i*1e-7 for i in range(n)]} for _ in range(2 if key in ('rho','e','K') else 0)],'patches':[]}
    owners=[];neighbours=[]
    for y in range(nx):
        for x in range(nx):
            i=y*nx+x
            if x+1<nx:owners.append(i);neighbours.append(i+1)
            if y+1<nx:owners.append(i);neighbours.append(i+nx)
    nf=len(owners);state['phi']={'internal':[.001]*nf,'patches':[]}
    matrix={'has_diag':True,'dimensions':evaluator.MASS,'psi_name':'rho','diag':[4.]*n,
            'source':[0.]*n,'has_upper':True,'has_lower':True,'upper':[-1.]*nf,'lower':[-1.]*nf,
            'owner':owners,'neighbour':neighbours,'patches':[],'psi':{'cells':[1.]*n,'patches':[]},
            'volumes':[1.]*n,'arithmetic_bound':0.}
    action=[4.]*n
    for o,nb in zip(owners,neighbours):action[o]-=1.;action[nb]-=1.
    matrix['native_lhs_minus_rhs']=action
    matrix['matrix_epoch']=evaluator.sha(evaluator.canonical(evaluator.coefficient_key(matrix)).encode())
    payload={'native_state_epoch':state,'unrelaxed_matrix':matrix}
    rows=[]
    def bench(name,fn,repeat=3):
        trials=[];bytes_out=None;loads=[]
        for _ in range(repeat):
            gc.collect();loads.append(os.getloadavg());start=time.perf_counter();value=fn();trials.append(time.perf_counter()-start)
            if isinstance(value,(str,bytes)):bytes_out=len(value)
            del value
        rows.append({'component':name,'seconds':trials,'min':min(trials),'median':statistics.median(trials),'max':max(trials),
                     'output_bytes':bytes_out,'load_average':loads,'scope':'SYNTHETIC_TARGET_SIZE_DATA_SHAPE_ONLY'})
        print('primitive',name,round(rows[-1]['median'],4),flush=True)
    bench('primary_QoI_4097_points',lambda:primary_evidence.primary(state,points.tolist(),contract['physical_problem']))
    bench('canonical_state_string',lambda:evaluator.canonical(state))
    bench('canonical_payload_string',lambda:evaluator.canonical(payload))
    bench('JSON_encode_payload',lambda:json.dumps(payload,separators=(',',':'),allow_nan=False))
    raw=json.dumps(payload,separators=(',',':'),allow_nan=False).encode()
    bench('JSON_decode_payload',lambda:json.loads(raw))
    bench('binary_pack_payload',lambda:packed.encode(payload))
    bench('matrix_replay_including_epoch_hash',lambda:evaluator.replay_matrix(matrix))
    bench('SHA256_16MiB',lambda:hashlib.sha256(b'x'*(16*2**20)).hexdigest())
    # Three bounded 16MiB writes + fsync: cached local-filesystem observation,
    # never a claim of sustained NVMe throughput or selected 9GiB audit speed.
    data=b'x'*(16*2**20);io=[]
    for i in range(3):
        path=OUT/f'io_fixture_{i}.bin';t=time.perf_counter()
        with path.open('xb') as f:
            f.write(data);write_end=time.perf_counter();f.flush();os.fsync(f.fileno());sync_end=time.perf_counter()
        directory=os.open(OUT,os.O_DIRECTORY);os.fsync(directory);os.close(directory)
        io.append({'bytes':len(data),'write_seconds':write_end-t,'file_fsync_seconds':sync_end-write_end,
                   'total_with_directory_fsync_seconds':time.perf_counter()-t,'load_average':os.getloadavg()})
    write('primitive_timings.json',{'classification':'SYNTHETIC_ONLY_NON_CFD_TARGET_SIZE_ARRAY_MICROBENCHMARK',
        'Ncells':n,'Ninternal_faces':nf,'patch_values_omitted':True,
        'limitations':'Not valid production state epochs/BCs/whole callback graph. Field counts/history vary by stage. No native C++ packet-building timing; no Krylov solve. No direct tiny RSS scaling.',
        'baseline_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'payload_JSON_bytes':len(raw),'timings':rows,'io_trials':io})

if __name__=='__main__':
    native() if sys.argv[1]=='native' else primitives()
