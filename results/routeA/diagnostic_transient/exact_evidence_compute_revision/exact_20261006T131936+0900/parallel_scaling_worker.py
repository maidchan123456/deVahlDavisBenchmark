from pathlib import Path
import sys,os,json,random,struct,time,hashlib,resource,concurrent.futures,subprocess
m=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/exact_evidence_compute_revision/exact_20261006T131936+0900');out=m/'parallel_scaling';sys.path.insert(0,str(m/'parallel_build'))
if len(sys.argv)>1:
 workers=int(sys.argv[1]);case=sys.argv[2];repeat=int(sys.argv[3]);resource.setrlimit(resource.RLIMIT_AS,(2*2**30,)*2)
 import numeric_parallel
 rng=random.Random(43006);arrays=[([float(i%7)]*25600 if case=='constant' else [rng.uniform(-1e3,1e3) for _ in range(25600)]) for i in range(32)];prepared=[(struct.pack('<'+'d'*len(x),*x),[len(x)]) for x in arrays];pool=concurrent.futures.ThreadPoolExecutor(max_workers=workers) if workers>1 else None
 t=time.monotonic();c=time.process_time();hashes=[]
 for iteration in range(16):
  values=list(pool.map(lambda p:numeric_parallel.canonical(*p),prepared)) if pool else [numeric_parallel.canonical(*p) for p in prepared]
  digest=hashlib.sha256()
  for raw in values:digest.update(raw.encode())
  hashes.append(digest.hexdigest())
 wall=time.monotonic()-t;cpu=time.process_time()-c
 if pool:pool.shutdown(wait=True)
 assert len(set(hashes))==1
 print(json.dumps({'workers':workers,'case':case,'repeat':repeat,'wall_seconds':wall,'CPU_seconds':cpu,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'ordered_output_SHA256':hashes[0],'arrays':32,'cells':25600,'iterations':16}));sys.exit(0)
for case in ('constant','random'):
 for workers in (1,2,4,8,12):
  for repeat in range(3):
   p=subprocess.run([sys.executable,'-B',__file__,str(workers),case,str(repeat)],capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
   with (out/'rows.jsonl').open('a') as f:f.write(p.stdout);f.flush();os.fsync(f.fileno())
rows=[json.loads(x) for x in (out/'rows.jsonl').read_text().splitlines()]
for case in ('constant','random'):assert len({r['ordered_output_SHA256'] for r in rows if r['case']==case})==1
(out/'worker_result.json').write_text(json.dumps({'status':'PASS','rows':rows,'workers':[1,2,4,8,12],'deterministic_commit_order':'registered array index','no_CFD':True},indent=2)+'\n')
