"""Small bounded U01/U03/socket microbenchmarks; SYNTHETIC_ONLY."""
import collections,json,os,signal,socket,statistics,sys,threading,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5]
sys.path.insert(0,str(ROOT/'Scripts/routeA/diagnostic_transient/v1_4'))
import live_collector,primary_evidence
c=json.loads((ROOT/'docs/routeA_diagnostic_transient_contract_v1.5.json').read_text());n=25600
fields={'U':{'cells':[[0.,0.,0.] for _ in range(n)],'value_sha256':'synthetic'},'T':{'cells':[300.]*n,'value_sha256':'synthetic'}}
for k in ['p_rgh','rho','rhoFluidThermo:rho']:fields[k]={'cells':[1.]*n,'value_sha256':'synthetic'}
obj=live_collector.Live.__new__(live_collector.Live);obj.outer_count=24;obj.physical=c['physical_problem'];obj.contract=c;obj.strict=False
obj.linear=json.loads(next((OUT/'native_0_on').glob('primary_*.jsonl')).read_text().splitlines()[0])['linear_solves']
obj.outer=collections.deque([(fields,{'Nu_bar_cavity':1.,'Umax':0.,'Wmax':0.}) for _ in range(5)],maxlen=5)
rows=[]
def measure(name,fn):
    times=[]
    for _ in range(3):
        signal.alarm(5);t=time.perf_counter();fn();times.append(time.perf_counter()-t);signal.alarm(0)
    rows.append({'component':name,'seconds':times,'median':statistics.median(times),'min':min(times),'max':max(times),'load_average':os.getloadavg()})
    print(name,rows[-1]['median'],flush=True)
measure('U01_terminal_certificate_25600',obj.outer_certificate)
raw=b'x'*(16*2**20)
def ipc():
    a,b=socket.socketpair()
    def read():
        total=0
        while total<len(raw):total+=len(b.recv(65536))
        b.sendall(b'OK\n')
    t=threading.Thread(target=read);t.start();a.sendall(raw);assert a.recv(3)==b'OK\n';t.join();a.close();b.close()
measure('AF_UNIX_16MiB_ACK_no_backend_work',ipc)
arrival=live_collector.Arrival(c['physical_problem'],c)
for count in (101,201,401):
    times=[i*.5/(count-1) for i in range(count)];histories={k:[1.]*count for k in arrival.names}
    measure('U03_three_windows_'+str(count)+'_nodes',lambda:primary_evidence.policy.arrival_candidate(times,histories,.5,arrival.scales,True))
(OUT/'supplemental_timings.json').write_text(json.dumps({'classification':'SYNTHETIC_ONLY',
    'limitations':'Shared stationary U01 objects; manufactured constant U03 histories. Socket transfer excludes encoding/evaluator/persistence. Not production memory, epochs or arrival.',
    'large_history_attempt':{'nodes':15001,'status':'ABORTED_NOT_COMPLETED','elapsed_lower_bound_seconds':37,
                             'reason':'Stopped this review-owned Python-only primitive benchmark to keep work bounded; no CFD process was interrupted'},
    'timings':rows},indent=2)+'\n')
