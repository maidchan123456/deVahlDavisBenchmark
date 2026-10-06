#!/usr/bin/env python3
"""Non-CFD guard tests; synthetic Git drift remains in memory only."""
import contextlib,io,json,subprocess
from pathlib import Path
from unittest.mock import patch
import head_integrity_v2 as guard
import production_launcher_v2 as launch
V2=Path(__file__).resolve().parent;plan=launch.check();tests=[]
assert launch.authorization(V2/'production_authorization_v2.json',plan)['AUTHORIZED']=='YES'
tests.append('authorized_reviewed_package_full_preflight_PASS')
# Reversible v2 receipt tamper must be rejected by the sealed package.
f=V2/'production_authorization_v2.json';original=f.read_bytes()
try:
 f.write_bytes(original+b'\n')
 try:launch.check()
 except RuntimeError as e:assert 'v2 package changed' in str(e)
 else:raise AssertionError('tampered receipt accepted')
finally:f.write_bytes(original)
tests.append('actual_v2_authorization_tamper_rejected_and_restored')
# Simulate a sensitive file hash change without touching historical/case files.
real_sha=guard.sha;target=str(Path(plan['case'])/'0/U')
with patch.object(guard,'sha',lambda path:'modified_hash' if str(path)==target else real_sha(path)):
 try:launch.check()
 except RuntimeError as e:assert 'PRODUCTION_SENSITIVE_CHANGE' in str(e)
 else:raise AssertionError('changed input accepted')
tests.append('sensitive_input_mismatch_rejected')
# Non-sensitive future HEAD drift is accepted with a new receipt; test sink captures
# the receipt in memory and emits no fictitious Git review artifact.
with patch.object(guard,'git',return_value=b'SYNTHETIC_RESULTS_ONLY_TEST_HEAD\n'),patch.object(guard,'changes',return_value=[{'change':'A','path':'results/unexecuted_report.md','classification':'RESULTS_ONLY'}]),patch.object(guard.subprocess,'run',return_value=subprocess.CompletedProcess([],0)),patch.object(guard,'save') as sink:
 assert guard.reviewed_head_guard(plan)=='SYNTHETIC_RESULTS_ONLY_TEST_HEAD';assert sink.called
 tests.append('synthetic_results_only_HEAD_drift_accepted_no_disk_receipt')
with patch.object(guard,'git',return_value=b'SYNTHETIC_SENSITIVE_TEST_HEAD\n'),patch.object(guard,'changes',return_value=[{'change':'M','path':'docs/routeA_execution_contract_v1.7.json','classification':'PRODUCTION_SENSITIVE'}]),patch.object(guard.subprocess,'run',return_value=subprocess.CompletedProcess([],0)):
 try:guard.reviewed_head_guard(plan)
 except RuntimeError as e:assert 'PRODUCTION_SENSITIVE_CHANGE' in str(e)
 else:raise AssertionError('sensitive HEAD drift accepted')
 tests.append('synthetic_sensitive_HEAD_drift_rejected')
assert not Path(plan['runtime_output']).exists()
assert launch.check()==plan
(V2/'dry_guard_validation_v2.json').write_text(json.dumps({'result':'PASS','CFD_EXECUTED':'NO','tests':tests,'synthetic_git_tests':'memory only; no real reviewed HEAD is fabricated'},indent=2)+'\n')
print(json.dumps(tests,indent=2))
