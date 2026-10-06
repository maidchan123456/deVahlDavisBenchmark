import json,shutil,re,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
C=P/'common_input'; mesh=C/'constant/polyMesh'
def listbody(p):
 s=p.read_text();m=re.search(r'\n(\d+)\s*\n\(\s*\n',s);assert m,p
 return int(m[1]),s[m.end():s.rfind(')')]
def labels(p):n,s=listbody(p);a=[int(v) for v in s.split()];assert len(a)==n;return a
n,s=listbody(mesh/'points');pts=[[float(x) for x in row.split()] for row in re.findall(r'\(([^()]*)\)',s)];assert len(pts)==n
n,s=listbody(mesh/'faces');faces=[[int(x) for x in row.split()] for row in re.findall(r'\d+\(([^()]*)\)',s)];assert len(faces)==n
owner=labels(mesh/'owner');neigh=labels(mesh/'neighbour');indices=[i for i,x in enumerate(owner) if x==12719]+[i for i,x in enumerate(neigh) if x==12719];vertices={v for i in indices for v in faces[i]};centre=[sum(pts[v][k] for v in vertices)/len(vertices) for k in range(3)]
assert all(abs(a-b)<1e-14 for a,b in zip(centre,[.0496875,.0496875,.0005]))
(P/'reference_cell_proof.json').write_text(json.dumps({'original_global_cell':12719,'vertex_average_m':centre,'faces':indices,'unique_vertices':sorted(vertices),'new_pRefPoint_m':[.0496875,.0496875,.0005],'pRefValue':0,'native_source':'/opt/openfoam13/src/finiteVolume/cfdTools/general/findRefCell/findRefCell.C','reason':'native pRefCell is rank0 local ID; pRefPoint locates the same global physical cell on any decomposition','physics_and_numerical_policy_changed':False},indent=2)+'\n')
archive=P/'superseded_cell_reference_attempts';archive.mkdir();shutil.copy2(P/'pilot.py',archive/'pilot_before_reference_repair.py');shutil.copy2(P/'common_input_manifest.json',archive/'common_input_manifest.json')
for r in [1,2,4]:shutil.move(P/f'rank_{r:02d}',archive/f'rank_{r:02d}')
for r in [6,8,12]:
 d=P/f'rank_{r:02d}';assert not (d/'timing.json').exists()
 # these are unused preparations only, keep their original manifest
 shutil.copy2(d/'input_manifest.json',archive/f'unused_rank_{r:02d}_input_manifest.json')
 shutil.rmtree(d)
f=C/'system/fvSolution';s=f.read_text();assert s.count('pRefCell 12719;')==1;f.write_text(s.replace('pRefCell 12719;','pRefPoint (0.0496875 0.0496875 0.0005);'))
def manifest(p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file()}
(P/'common_input_manifest.json').write_text(json.dumps(manifest(C),indent=2)+'\n')
for r in [1,2,4,6,8,12]:
 d=P/f'rank_{r:02d}';d.mkdir();shutil.copytree(C,d/'case');(d/'case/system/decomposeParDict').write_text('FoamFile { format ascii; class dictionary; object decomposeParDict; }\nnumberOfSubdomains '+str(r)+';\nmethod scotch;\n');(d/'input_manifest.json').write_text(json.dumps(manifest(d/'case'),indent=2)+'\n');shutil.copy2(P/'environment.txt',d/'environment.txt')
d=json.loads((P/'design.json').read_text());d['primary_timing_source']='external monotonic completion timestamps because native ClockTime is integer seconds';d['reference_cell_representation']='pRefPoint (0.0496875 0.0496875 0.0005), proven identical to original global cell12719';d['repair_history']='Preserved initial serial and2rank runs plus4rank initialization failure; same physical reference point required for fair decomposition.';(P/'design.json').write_text(json.dumps(d,indent=2)+'\n')
# preparation recipe now reproduces corrected common dictionary
f=P/'pilot.py';s=f.read_text().replace('switches.update(pRefCell=12719,pRefValue=0)',"switches.update(pRefPoint='(0.0496875 0.0496875 0.0005)',pRefValue=0)");f.write_text(s)
print('Same reference cell proved; repaired all common inputs; original attempts preserved.')
