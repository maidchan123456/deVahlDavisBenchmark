#!/usr/bin/env python3
"""Build an immutable v2 launch envelope; no CFD or Git mutation."""
import ast,difflib,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
V2=Path(__file__).resolve().parent;PREP=V2.parent;ROOT=PREP.parents[3]
sys.path.insert(0,str(V2));from head_integrity_v2 import sha,save,git,changes,OLD,AUTHORITY
current=git('rev-parse','HEAD').decode().strip()
assert subprocess.run(['git','merge-base','--is-ancestor',OLD,current],cwd=ROOT).returncode==0
records=changes(OLD,current)
assert all(r['change']=='A' and r['path'].startswith('results/routeA/plain_transient_co05_production/co05_20261006_0602/') for r in records),'Unreviewed sensitive/unknown change'
oldplan=json.loads((PREP/'production_execution_plan.json').read_text());m=json.loads((PREP/'production_input_manifest.json').read_text());case=Path(m['case'])
files={str(case/rel):digest for rel,digest in m['case_files_sha256'].items()}
files.update({str(ROOT/rel):digest for rel,digest in json.loads((PREP/'source_reference_guard.json').read_text()).items()})
files.update({v['path']:v['sha256'] for v in m['binary_provenance'].values()});files.update(m['installed_source_sha256'])
# Every old preparation and blocked-attempt file remains immutable. V2 is excluded.
original={str(f.relative_to(PREP)):sha(f) for f in PREP.rglob('*') if f.is_file() and V2 not in f.parents}
files.update({str(PREP/rel):digest for rel,digest in original.items()})
for rel,digest in AUTHORITY.items():assert sha(ROOT/rel)==digest
assert all(sha(path)==expected for path,expected in files.items())
assert {str(f.relative_to(case)) for f in case.rglob('*') if f.is_file()}==set(m['case_files_sha256'])
assert not (PREP/'execution').exists() and not (PREP/'execution_v2').exists()
mpi_version=subprocess.check_output(['mpirun','--version'],text=True).strip();assert mpi_version==m['MPI_version']
assert os.environ.get('WM_PROJECT_VERSION')=='13'
# Source-adapt old launcher: native execution loop and case semantics are unchanged.
source=(PREP/'production_launcher.py').read_text();new=source
new=new.replace('P = Path(__file__).resolve().parent','V2 = Path(__file__).resolve().parent\nP = V2.parent\nfrom head_integrity_v2 import reviewed_head_guard, verify_package_and_authorization')
new=new.replace("return json.loads((P / name).read_text())","return json.loads(((V2 / 'production_execution_plan_v2.json') if name == 'production_execution_plan.json' else (P / name)).read_text())")
old_head="require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==plan['expected_HEAD'],'HEAD changed; reviewed preparation refresh required')"
assert new.count(old_head)==1
new=new.replace(old_head,"reviewed_head_guard(plan)\n    verify_package_and_authorization(plan)")
new=new.replace("a=json.loads(Path(path).read_text())","require(Path(path).resolve()==(V2/'production_authorization_v2.json').resolve(),'use pinned v2 authorization receipt')\n    a=verify_package_and_authorization(plan)")
new=new.replace("sha(P/'production_execution_plan.json')","sha(V2/'production_execution_plan_v2.json')")
new=new.replace("'AUTHORIZED':'NO','case':plan['case']","'AUTHORIZED':'YES','case':plan['case']")
assert new!=source
(V2/'production_launcher_v2.py').write_text(new)
old_ast=ast.parse(source);new_ast=ast.parse(new)
protected=['semantics','descendants','kill_tree','verified_master','fatal_line','final_state','execute']
functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
a,b=functions(old_ast),functions(new_ast)
assert all(a[name]==b[name] for name in protected),'Production-sensitive loop behavior changed'
save(V2/'launcher_behavior_equivalence_v2.json',{'protected_function_AST_identity':{name:a[name]==b[name] for name in protected},'execution_loop_unchanged':True,'changes':['historical P kept at original prep; v2 envelope read separately','HEAD identity guard replaced by reviewed provenance plus sensitive byte identity','v2 plan/authorization/package seal verification added','execution namespace comes from v2 plan','dry print reflects current authorization YES']})
(V2/'launcher_v1_to_v2.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),new.splitlines(True),fromfile='historical/production_launcher.py',tofile='head_review_v2/production_launcher_v2.py')))
(V2/'run_production_v2.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
launcher_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/python3 -B "$launcher_dir/production_launcher_v2.py" "$@"
''');(V2/'run_production_v2.sh').chmod(0o755)
for name in ['production_launcher_v2.py','run_production_v2.sh','head_integrity_v2.py','build_review_v2.py']:
 files[str(V2/name)]=sha(V2/name)
comparisons=[{'path':path,'prepared_or_reviewed_sha256':expected,'current_sha256':sha(path),'match':sha(path)==expected} for path,expected in files.items()]
review={'ROUTE_A_CO05_HEAD_CHANGE_REVIEW':'PASS','old_preparation_head':OLD,'current_reviewed_head':current,'commit_range_reviewed':OLD+'..'+current,
'commits':git('log','--format=%H','--reverse',OLD+'..'+current).decode().splitlines(),'changed_paths':records,'changed_path_count':len(records),'all_tracked_changes_are_additions_to_original_prep_results':True,'production_sensitive_state_equivalent':True,'HEAD_CHANGE_PRODUCTION_SENSITIVE':'NO','production_sensitive_hashes_before_and_current':comparisons,'original_artifacts_sha256':original,'MPI_version_unchanged':mpi_version,'OpenFOAM_build_prepared':m['OpenFOAM_build'],'WM_PROJECT_VERSION':'13','launcher_execution_loop_AST_identical':True,'reason_repin_is_safe':'Only preparation and blocked-attempt artifacts were added in Git. All actual cold case/mesh/decomposition dictionaries, authorities, prepared binary/installed-source hashes and frozen references match independently. v2 only changes reviewed HEAD/authorization envelope and runtime namespace; native execution loop and solver semantics remain identical.'}
save(V2/'head_change_review.json',review)
(V2/'head_change_review.md').write_text(f'''# Route A Co0.5 HEAD review v2

PASS. Old preparation HEAD:{OLD}. Reviewed current HEAD:{current}.

Local range {OLD}..{current} contains two known commits and {len(records)} changed paths, all additions under the original production preparation results namespace. No physical/numerical case, authority or solver source path changed in Git. Every changed path is classified in head_change_review.json.

Git diff is supporting evidence. Primary proof is exact SHA256 identity of all164 case files (cold0, constants, system, mesh and12 processor meshes/initial fields), authorities, frozen references, prepared binaries/native solver library/installed OpenFOAM source hashes, MPI version and all historical preparation/blocked artifacts. Prepared and current hashes are both recorded for every sensitive input. The complete old package remains unchanged, including expected_HEAD=f57d... and AUTHORIZED=NO draft.

V2 pins reviewed provenance plus production-sensitive byte hashes. The HEAD provenance guard is distinct from production input integrity. A later results-only descendant commit is reviewed and recorded, not automatically rejected for a different HEAD; sensitive or unknown drift fails closed. The v2 package seal covers authorization/plan/manifest/scripts. Native execution loop, final-state verification, fatal detection, tree cleanup and scientific dictionary checks have identical AST to the original launcher. The only execution envelope changes are reviewed provenance, v2 authorization and execution_v2 namespace. Review receipt and source diff document them.

There is no pre-existing trajectory:all13 case roots contain cold0 only, and execution/ and execution_v2/ are absent. Previous BLOCKED_HEAD_CHANGED record remains0 steps. New non-CFD binding and pRefPoint evidence are retained separately in v2. No scientific/numerical/controller/output policy is changed by repin. Production remains one cold continuous Co0.5 series; no automatic restart/rerun, no Q3/GateJ or other series.
''')
sensitive={'preparation_id':PREP.name,'old_preparation_HEAD':OLD,'reviewed_current_HEAD':current,'files_sha256':files,'case_files_sha256':m['case_files_sha256'],'source_provenance_manifest_sha256':sha(PREP/'production_input_manifest.json'),'execution_loop_AST_identical':True}
save(V2/'production_sensitive_manifest_v2.json',sensitive)
plan=dict(oldplan);plan.update(expected_HEAD=current,old_preparation_HEAD=OLD,reviewed_current_HEAD=current,runtime_output=str(PREP/'execution_v2'),production_sensitive_manifest_file=str(V2/'production_sensitive_manifest_v2.json'),production_sensitive_manifest_sha256=sha(V2/'production_sensitive_manifest_v2.json'),PRODUCTION_EXECUTION_AUTHORIZED='YES',updated_HEAD_policy='Reviewed provenance + exact sensitive input/runtime/script identity; non-sensitive descendant HEAD changes get an additional review receipt; sensitive/unknown drift fails closed.',historical_execution_plan_sha256=sha(PREP/'production_execution_plan.json'))
save(V2/'production_execution_plan_v2.json',plan)
request=Path('/home/mirai/.codex/attachments/94cfeb87-d235-4e33-9cea-66bcbdee26fd/貼り付けたテキスト.txt')
auth={'TASK':'REVIEW_REPIN_AND_RUN_ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION','AUTHORIZED':'YES','AUTHORIZATION_SOURCE':'EXPLICIT_CURRENT_USER_INSTRUCTION','authorization_class':'ROUTE_A_PLAIN_TRANSIENT_CO05_PRODUCTION','preparation_id':PREP.name,'reviewed_HEAD':current,'expected_HEAD':current,'production_sensitive_manifest_sha256':plan['production_sensitive_manifest_sha256'],'input_manifest_sha256':plan['input_manifest_sha256'],'execution_plan_sha256':sha(V2/'production_execution_plan_v2.json'),'source_user_authorization_reference':str(request),'source_user_authorization_sha256':sha(request),'MPI_RANKS':12,'maxCo':.5,'endTime_s':1420,'CO05_ALLOWED':'YES','CO025_ALLOWED':'NO','AUTOMATIC_RESTART':'NO','AUTOMATIC_RERUN':'NO','Q3_ALLOWED':'NO','FORMAL_GATE_J_ALLOWED':'NO'}
save(V2/'production_authorization_v2.json',auth)
seal_names=['production_sensitive_manifest_v2.json','production_execution_plan_v2.json','production_authorization_v2.json','production_launcher_v2.py','run_production_v2.sh','head_integrity_v2.py','head_change_review.md','head_change_review.json','launcher_behavior_equivalence_v2.json','launcher_v1_to_v2.diff','build_review_v2.py']
save(V2/'execution_package_seal_v2.json',{name:sha(V2/name) for name in seal_names})
# Read-only native geometry mapping, no decompose or CFD.
sys.path.insert(0,str(PREP));from mesh_geometry import geometry,labels
import numpy as np
point=np.array([.0496875,.0496875,.0005]);globalgeo=geometry(case/'constant/polyMesh');mapping=[];covered=[]
for rank in range(12):
 mesh=case/f'processor{rank}/constant/polyMesh';ids=labels(mesh/'cellProcAddressing');g=geometry(mesh);covered.extend(ids.tolist())
 assert np.max(np.abs(g['centres']-globalgeo['centres'][ids]))<1e-13
 cells=np.where(np.all((g['lo']<point)&(point<g['hi']),axis=1))[0]
 for cellid in cells:mapping.append({'rank':rank,'local_cell':int(cellid),'global_cell':int(ids[cellid]),'centre':g['centres'][cellid].tolist()})
assert sorted(covered)==list(range(25600)) and mapping==[{'rank':3,'local_cell':2107,'global_cell':12719,'centre':[.0496875,.04968750000000001,.0005]}]
save(V2/'pRefPoint_mapping_reverification_v2.json',{'result':'PASS','native_global_local_geometry_identical':True,'all_cells_once':True,'mapping':mapping})
save(V2/'git_status_at_review_start.json',{'HEAD':current,'status':git('status','--short').decode()})
print(json.dumps({'head_review':'PASS','reviewed_HEAD':current,'changed_paths':len(records),'all_old_sensitive_inputs_match':True,'protected_execution_functions_AST_identical':True,'v2_authorization':'YES','v2_runtime_output':plan['runtime_output']},indent=2))
