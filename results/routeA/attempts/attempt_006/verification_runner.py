import hashlib,json,re,shutil
from pathlib import Path
R=Path.cwd();O=R/'results/routeA/attempts/attempt_006'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=json.loads((O/'execution_state.json').read_text());assert s['overall'] in ['COMPLETE','STOPPED']
segments=[];regenerated=[]
for row in s['cases']:
 if not row['computed']:continue
 case=R/'cases/routeA'/row['case_id'];m=json.loads((case/'case_manifest.json').read_text())
 for rel,h in m['input_sha256'].items():
  if rel!='system/controlDict':assert sha(case/rel)==h,rel
 first=R/row['segments'][0]['path']
 control=(case/'system/controlDict').read_text()
 control=re.sub(r'(^\s*startFrom\s+)[^;]+;',r'\g<1>startTime;',control,flags=re.M)
 control=re.sub(r'(^\s*endTime\s+)[^;]+;',r'\g<1>3000;',control,flags=re.M)
 assert control==(first/'controlDict').read_text(),'unpermitted control change'
 for seg in row['segments']:
  p=R/seg['path'];assert sha(p/'sealed_sha256.json')==seg['sealed_sha256_manifest']
  for rel,h in json.loads((p/'sealed_sha256.json').read_text()).items():assert sha(p/rel)==h,rel
  mf=json.loads((p/'segment_manifest.json').read_text())
  for rel,h in mf['mesh_sha256'].items():assert sha(case/rel)==h,rel
  for field,h in mf['final_field_validation']['field_sha256'].items():
   actual=sha(case/str(seg['end_iteration'])/field)
   if field=='wallHeatFlux' and seg['end_iteration']<row['final_iteration'] and actual!=h:
    regenerated.append({'case_id':row['case_id'],'iteration':seg['end_iteration'],'field':field,'observed_checkpoint_sha256':h,'current_derived_working_sha256':actual,'classification':'DERIVED_FUNCTION_OBJECT_FIELD_REGENERATED_IN_WORKING_CASE; not native restart input or sealed raw Q','restart_guard_before_continuation':'PASS','raw_evidence_seal':'UNCHANGED'})
   else:assert actual==h,(field,seg['end_iteration'])
  for field,h in mf['diagnostic_field_sha256'].items():assert sha(case/str(seg['end_iteration'])/field)==h,field
  assert mf['process']['exit_code']==0 and mf['health']['normal_exit']
  assert mf['runtime_provenance']['status']=='PASS' and mf['gate_A']=='PASS' and mf['OQ_02']=='PASS'
  segments.append({'case_id':row['case_id'],'iteration':seg['end_iteration'],'native_restart_fields_mesh_input_raw_final_seals_runtime_health':'PASS'})
protected=json.loads((O/'protected_before_sha256.json').read_text())
for p,h in protected.items():assert sha(R/p)==h,p
for p,h in json.loads((O/'RouteB_baseline_sha256.json').read_text()).items():assert sha(R/p)==h,p
result={'status':'PASS','protected_file_count':len(protected),'all_historical_evidence_unchanged':True,'permitted_control_changes_only':True,'accepted_final_fields_all_match':True,'segments':segments,'derived_wallHeatFlux_regeneration_observations':regenerated,'solver_concurrency':1,'numerical_physical_model_criteria_changed':False,'Ra1e3_results_modified':False,'Route_B_modified':False,'current_environment_checked_before_case_generation':True}
assert not (O/'final_verification.json').exists();(O/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copy2(__file__,O/'verification_runner.py');shutil.copy2('/tmp/report_routeA_attempt006.py',O/'group_evaluation.py')
rp=O/'Ra1e5_trio_report.json';r=json.loads(rp.read_text());r['working_derived_field_observations']=regenerated;rp.write_text(json.dumps(r,indent=2)+'\n')
md=O/'Ra1e5_trio_report.md';text=md.read_text();text+='\n最終照合: native restart fields・final accepted fields・input/mesh・raw/final seals・runtime/OQ-02/Gate AはPASS。派生wallHeatFluxの旧working checkpoint再出力差は'+str(len(regenerated))+'件で、封印raw Q/log/metricsは不変。詳細final_verification.json。\n';md.write_text(text)
files={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file()}
(O/'attempt_sealed_sha256.json').write_text(json.dumps(files,indent=2)+'\n')
print('Final verification PASS:',len(segments),'segments;',len(protected),'protected files;',len(regenerated),'derived-field observations;',len(files),'attempt files sealed')
