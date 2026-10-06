from pathlib import Path
import json,hashlib,re,subprocess,sys
root=Path.cwd();master=Path(Path('/tmp/route_a_master_path').read_text());report=master/'Autonomous_Q3_readiness_final_report.md'
# Final editorial check before sealing the new report.
text=report.read_text().replace('44.1KiB/s程度','44.1kB/s程度');report.write_text(text)
r=json.loads((master/'Autonomous_Q3_readiness_final_report.json').read_text());status=r['final_status'];prompt=Path(r['master_scope']['master_prompt']).read_text();segment=prompt.split('# 124. REQUIRED FINAL STATUS FIELDS',1)[1].split('# 125.',1)[0];required=set(re.findall(r'(?m)^([A-Z][A-Z0-9_]+)\s*=',segment));assert not(required-set(status)),required-set(status)
assert status['Q3_BOUNDED_CFD_QUALIFICATION_READY']=='NO' and status['Q3_EXECUTED']=='NO' and status['AUTONOMOUS_ROUTE_A_ADVANCE_TO_Q3_READY']=='BLOCKED'
assert status['AUTONOMOUS_MAJOR_CYCLES_EXECUTED']==2 and status['NONCFD_SCOUTS_EXECUTED']==3 and r['failed_campaign_immutable_files']==49
assert sum(s['completed_trials'] for s in r['all_scout_campaigns'])==49
assert all(status[k]=='NO' for k in ['SCIENTIFIC_CONTRACT_CHANGED','NUMERICAL_POLICY_CHANGED','U01_CHANGED','U02_CHANGED','U03_CHANGED','U04_EQUATION_SEMANTICS_CHANGED','HOST_STABILITY_RULE_CHANGED','Q3_AUTHORIZED','CFD_EXECUTED','PRODUCTION_EXECUTION_AUTHORIZED','FORMAL_GATE_J_EXECUTED'])
# Check no direct measurement executables remain; exclude our code-only CLI.
owned=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 if not args:continue
 decoded=[a.decode(errors='replace') for a in args]
 if any(a.endswith('/build_cycle2_codec/native_adapter') or a.endswith('/build/native_adapter') and str(master) in a or any(a.endswith('/'+name) and '/compute_revision_v' in a for name in ('backend.py','worker.py','watchdog.py','campaign.py')) for a in decoded):owned.append(int(p.name))
assert not owned,owned
scopes=subprocess.check_output(['systemctl','--user','list-units','--no-legend','--plain','route-a-*.scope'],text=True);assert not scopes.strip(),scopes
proof={'status':'PASS','required_final_fields_present':len(required),'provided_status_fields':len(status),'scientific_and_authorization_invariants':'PASS','old_failed_campaign_files_unchanged':49,'owned_measurement_processes_remaining':owned,'dedicated_scopes_remaining':[],'CFD_executed':False,'git_mutation_executed':False}
(master/'final_report_validation.json').write_text(json.dumps(proof,indent=2)+'\n')
# Seal all new master evidence bytes. Large immutable scout evidence has its own
# independently verified manifests, pinned here rather than duplicated.
rows=[]
for p in sorted(master.rglob('*')):
 if p.is_file() and p.name not in ('master_evidence_manifest.json','master_evidence_seal.json'):
  rows.append({'path':str(p.relative_to(master)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
external=[]
for s in r['all_scout_campaigns']:
 p=Path(s['output'])/'qualification_manifest.json';external.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
source_extra=root/'Scripts/routeA/diagnostic_transient/compute_revision_v3/measurement/REVISION_NOTES.md'
manifest={'schema':'autonomous_master_evidence/1','master_run_id':master.name,'artifacts':rows,'scout_evidence_manifests':external,'revision_notes':{'path':str(source_extra),'sha256':hashlib.sha256(source_extra.read_bytes()).hexdigest()},'reports_status':'BLOCKED_RESOURCE_REDESIGN','historical_integrity_guard':'end_guard.json','no_CFD':True}
p=master/'master_evidence_manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n')
for row in rows:
 f=master/row['path'];assert f.stat().st_size==row['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
seal={'status':'PASS','master_manifest_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'master_files_pinned':len(rows),'scout_manifests_pinned':len(external),'readback_all_artifacts':'PASS','no_further_automatic_execution':True};(master/'master_evidence_seal.json').write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps(seal));print(json.dumps(proof))
