from pathlib import Path
import os,sys,json,math,random,struct,hashlib,resource,time,concurrent.futures
m=Path('/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/exact_evidence_compute_revision/exact_20261006T131936+0900');sys.path.insert(0,str(m/'parallel_build'));sys.path.insert(0,str(Path.cwd()/'Scripts/routeA/diagnostic_transient/v1_4'));import numeric_parallel;from online_evaluator import canonical
rng=random.Random(4006);values=[-0.,0,1.,1e16,1e17,1e-9,float.fromhex('0x0.0000000000001p-1022')]
for _ in range(20000):
 v=struct.unpack('<d',rng.randbytes(8))[0]
 if math.isfinite(v):values.append(v)
for x in [values,[[v,-v,0.] for v in values[:257]],[1.,0.,-0.]*256]:
 flat=x if type(x[0]) in (int,float) else [v for row in x for v in row];shape=[len(x)] if type(x[0]) in (int,float) else [len(x),len(x[0])];raw=struct.pack('<'+'d'*len(flat),*flat);assert numeric_parallel.canonical(raw,shape)==canonical(x)
for args in [(b'x',[1]),(struct.pack('<d',math.inf),[1]),(struct.pack('<d',1),[2]),(struct.pack('<d',1),[0])]:
 try:numeric_parallel.canonical(*args)
 except ValueError:pass
 else:raise AssertionError('negative')
(m/'parallel_numeric_equivalence.json').write_text(json.dumps({'status':'PASS','random_IEEE64_values':len(values),'canonical_17digit_exact':True,'signedzero_exact':True,'vectors_exact':True,'invalid_shape_length_nonfinite_fail_closed':True},indent=2)+'\n');print('PASS',len(values))
