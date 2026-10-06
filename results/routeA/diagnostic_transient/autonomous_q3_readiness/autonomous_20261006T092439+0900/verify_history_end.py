from pathlib import Path
import hashlib,json,subprocess,time,os
root=Path.cwd();master=Path(Path('/tmp/route_a_master_path').read_text());guard=json.loads((master/'start_guard.json').read_text());bad=[];begin=time.monotonic()
for row in guard['files']:
 p=root/row['path'];s=p.stat()
 if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:bad.append(row['path'])
assert not bad,bad
source_bad=[]
for name in ['Scout_harness_manifest_cycle_1.json','Scout_harness_manifest_cycle_2.json','Isolated_U03_scout_harness_manifest.json']:
 m=json.loads((master/name).read_text())
 for group in ['source_SHA256','artifact_SHA256','validation_SHA256']:
  for path,digest in m[group].items():
   if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:source_bad.append(path)
assert not source_bad,source_bad
for key in ['Scout_dispatch_cycle_1.json','Scout_dispatch_cycle_2.json','Isolated_U03_scout_dispatch.json']:
 out=Path(json.loads((master/key).read_text())['output']);trial=json.loads((out/'trial_result.json').read_text());assert not trial.get('remaining_live_pids'),trial
statuses=subprocess.check_output(['git','status','--short'],text=True);diff=subprocess.check_output(['git','diff','--stat'],text=True);(master/'git_status_end.txt').write_text(statuses);(master/'git_diff_stat_end.txt').write_text(diff)
report={'status':'PASS','historical_files_checked':len(guard['files']),'historical_bytes_SHA256_mtime_unchanged':True,'all_three_scout_source_artifact_validation_manifests_unchanged':True,'HEAD_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==guard['HEAD'],'all_scout_supervisor_remaining_live_pids_empty':True,'canonical_SHA256':hashlib.sha256((root/'docs/routeA_diagnostic_transient_contract_v1.5.json').read_bytes()).hexdigest(),'formal_SHA256':hashlib.sha256((root/'docs/routeA_execution_contract_v1.7.json').read_bytes()).hexdigest(),'git_diff_stat':diff,'wall_seconds':time.monotonic()-begin}
(master/'end_guard.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
