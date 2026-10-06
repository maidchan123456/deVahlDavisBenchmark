"""Exact Writer.share and complete scientific graph across worker counts."""
import copy,hashlib,json,os,subprocess,sys,time
from common import HERE,REVISION_ROOT,plan,atomic,load,sha
import persistence as persist,packed
from sharing import share
from pathlib import Path
base=REVISION_ROOT/'parallel_revision_equivalence';base.mkdir(exist_ok=False)
value={'volumes':[1e-9]*4,'owner':[0,1,2],'payload':{'scalar':[0.,-0.,1,2.], 'vectors':[[1.,0.,-0.],[2,3,4]],'mixed':[None,'x',False,{'labels':[1,2]}]}}
a=persist.Writer(base/'share_old');b=persist.Writer(base/'share_new')
for i in range(2):
 old=a.share(copy.deepcopy(value));new=share(b,copy.deepcopy(value),persist.encode,persist.sha,packed.need);assert old==new
files=lambda p:{str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
assert files(a.root)==files(b.root)
value['volumes'][0]=2e-9;errors=[]
for w,fn in [(a,lambda x:a.share(x)),(b,lambda x:share(b,x,persist.encode,persist.sha,packed.need))]:
 try:fn(value)
 except Exception as e:errors.append((type(e).__name__,str(e)))
assert len(errors)==2 and errors[0]==errors[1]
keys=('status','callbacks_including_constructor','matrix_packets','evaluator_summary','writer_bytes','writer_fsyncs','U01_primary_steps','schedule')
reference=REVISION_ROOT/'tiny_equivalence_parallel/new_on';rows=[];ref=load(reference/'backend_result.json');ref_files=files(reference/'runtime')
for workers in (1,2,8,12):
 out=base/f'workers_{workers}';out.mkdir();request={'kind':'pipeline','mode':'ON','purpose':'full','tiny':True,'classification':'TINY_SELF_TEST_ONLY','budget':plan()['stages']['Q1']['budgets']};atomic(out,'worker_request.json',request)
 env=dict(os.environ,ROUTE_A_PARALLEL_WORKERS=str(workers));begin=time.monotonic();p=subprocess.run([sys.executable,'-B',str(HERE/'worker.py'),str(out/'worker_request.json')],env=env,capture_output=True,timeout=35);(out/'execution.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode()+(out/'backend.log').read_text()
 actual=load(out/'backend_result.json');assert all(actual[k]==ref[k] for k in keys);assert files(out/'runtime')==ref_files
 progress=[json.loads(x) for x in (out/'native_progress.jsonl').read_text().splitlines() if x.startswith('{')];assert [x['callbacks_including_constructor'] for x in progress if 'callbacks_including_constructor' in x]==list(range(1,1146));assert actual['parallel']['workers']==workers
 rows.append({'workers':workers,'wall_seconds':time.monotonic()-begin,'scientific_result_equal':True,'Writer_SHA256_equal':True,'record_order_equal':True,'parallel':actual['parallel']})
 print('PASS fullgraph workers',workers,flush=True)
atomic(REVISION_ROOT,'parallel_revision_equivalence.json',{'status':'PASS','workers':[1,2,4,8,12],'share_Writer_exact':True,'share_mutation_error_exact':errors,'fullgraph_results':rows,'callbacks':1145,'matrices':701,'no_CFD':True})
