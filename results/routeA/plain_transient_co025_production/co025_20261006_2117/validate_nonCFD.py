#!/usr/bin/env python3
"""Mesh/affinity/cold-input checks only. Never invokes foamRun."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
import numpy as np
from mesh_geometry import geometry,labels
P=Path(__file__).resolve().parent
context=json.loads((P/'preparation_context.json').read_text());case=Path(context['case']);source=Path(context['source']);root=Path(context['root'])
def save(name,data):(P/name).write_text(json.dumps(data,indent=2)+'\n')
def run(argv,name):
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 r=subprocess.run(argv,env=env,capture_output=True,text=True)
 (P/(name+'.stdout.txt')).write_text(r.stdout);(P/(name+'.stderr.txt')).write_text(r.stderr)
 save(name+'.json',{'argv':argv,'returncode':r.returncode,'CFD_EXECUTED':'NO','environment_overrides':{k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}})
 assert r.returncode==0,(name,r.stderr[-2000:],r.stdout[-2000:]);return r
mpi=['mpirun','--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings','-np','12']
for argv,name in [(['checkMesh','-case',str(case),'-noFunctionObjects'],'checkMesh_serial'),(mpi+['checkMesh','-case',str(case),'-parallel','-noFunctionObjects'],'checkMesh_parallel')]:
 r=run(argv,name);assert 'Mesh OK' in r.stdout,name
probe=P/'affinity_probe.py'
probe.write_text("import os,json\nfrom pathlib import Path\ncpus=sorted(os.sched_getaffinity(0));cores=sorted(set((int((Path('/sys/devices/system/cpu')/('cpu'+str(c))/'topology/physical_package_id').read_text()),int((Path('/sys/devices/system/cpu')/('cpu'+str(c))/'topology/core_id').read_text())) for c in cpus));print(json.dumps({'rank':int(os.environ['OMPI_COMM_WORLD_RANK']),'cpus':cpus,'physical_cores':cores,'threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}}),flush=True)\n")
r=run(mpi+['/usr/bin/python3','-B',str(probe)],'MPI_affinity_probe')
rows=[json.loads(line) for line in r.stdout.splitlines() if line.startswith('{')]
assert sorted(x['rank'] for x in rows)==list(range(12))
assert all(len(x['physical_cores'])==1 and set(x['threads'].values())=={'1'} for x in rows)
assert len({tuple(x['physical_cores'][0]) for x in rows})==12
save('MPI_binding_verification.json',{'result':'PASS','ranks':rows,'distinct_physical_cores':12,'probe_not_CFD':True})
g=geometry(case/'constant/polyMesh');point=np.array([.0496875,.0496875,.0005]);matches=np.flatnonzero(np.all((point>g['lo'])&(point<g['hi']),axis=1));assert len(matches)==1
global_id=int(matches[0]);owner=[];allids=[]
for rank in range(12):
 base=case/f'processor{rank}';ids=labels(base/'constant/polyMesh/cellProcAddressing');allids.extend(ids.tolist());found=np.flatnonzero(ids==global_id)
 if len(found):
  local=int(found[0]);localg=geometry(base/'constant/polyMesh');assert np.all(point>localg['lo'][local]) and np.all(point<localg['hi'][local]);owner.append({'rank':rank,'local_cell':local,'global_cell':global_id,'centre':localg['centres'][local].tolist()})
assert len(owner)==1 and np.array_equal(np.sort(allids),np.arange(25600))
save('pRefPoint_mapping.json',{'result':'PASS','pRefPoint':point.tolist(),'strictly_inside_one_cell':True,'owner':owner,'global_cell_addressing_bijection':True,'cells':25600})
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
old=json.loads((source/'production_input_manifest.json').read_text());records=[]
assert {str(f.relative_to(case)) for f in case.rglob('*') if f.is_file()}==set(old['case_files_sha256'])
for rel,h in old['case_files_sha256'].items():
 actual=sha(case/rel);kind='INTENDED_CO_CHANGE' if rel=='system/controlDict' else 'IDENTICAL'
 if kind=='INTENDED_CO_CHANGE':
  before=(Path(old['case'])/rel).read_text();after=(case/rel).read_text();normalized=re.sub(r'(\bmaxCo\s+)0\.25(\s*;)',r'\g<1>0.5\2',after);assert before==normalized
 else:assert actual==h,rel
 records.append({'path':rel,'Co05_sha256':h,'Co025_sha256':actual,'classification':kind})
save('co05_vs_co025_input_diff.json',{'result':'PASS','all_files':records,'only_changed_case_file':'system/controlDict','only_changed_dictionary_entry':'maxCo:0.5 ->0.25','unintended_differences':[],'decomposition_preparation':'Frozen Co05 scotch12 cold mesh and addressing copied byte-identically; no new partition required; parallel checkMesh and bijection verified.','runtime_trajectory_copied':False})
(P/'co05_vs_co025_input_diff.md').write_text('# Co0.5 → Co0.25 input audit\n\nPASS. All164 cold input files compared. Only system/controlDict differs, solely maxCo0.5→0.25. Physical inputs, mesh, fvSchemes, fvSolution, time scheme, PIMPLE, linear solvers, initial dt, maxdt, endTime and native output dictionaries are byte-identical. New namespace and future output metadata are provenance changes. Frozen12-rank scotch decomposition reused byte-identically and verified by parallel checkMesh, cell-addressing bijection and interior pRefPoint mapping. No runtime trajectory copied.\n')
save('nonCFD_validation_summary.json',{'result':'PASS','checkMesh_serial':'PASS','checkMesh_parallel':'PASS','MPI_binding':'PASS','pRefPoint':'PASS','decomposition':'PASS','input_diff':'PASS','cold_only':True,'CFD_EXECUTED':'NO'})
print(json.dumps({'result':'PASS','case':str(case),'files':len(records),'pRef':owner},indent=2))
