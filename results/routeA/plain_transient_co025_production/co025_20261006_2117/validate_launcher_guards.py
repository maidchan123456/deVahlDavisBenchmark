"""Non-CFD fail-closed tests, using mocks for byte drift and future HEAD."""
import ast,hashlib,json,subprocess
from pathlib import Path
from unittest import mock
import production_launcher as launch
import head_integrity as guard
P=Path(__file__).resolve().parent;plan=json.loads((P/'production_execution_plan.json').read_text());case=Path(plan['case']);out=Path(plan['runtime_output'])
before={str(f.relative_to(case)):hashlib.sha256(f.read_bytes()).hexdigest() for f in case.rglob('*') if f.is_file()};checks={}
def rejects(fn,label):
 try:fn()
 except RuntimeError as e:checks[label]={'result':'PASS','rejected':str(e)}
 else:raise AssertionError('Guard unexpectedly accepted '+label)
rejects(lambda:launch.authorization(P/'production_authorization_draft.json',plan),'NO_draft_cannot_authorize')
actual_sha=guard.sha;target=str(case/'0/U')
with mock.patch.object(guard,'sha',side_effect=lambda p:'0'*64 if str(p)==target else actual_sha(p)):
 rejects(lambda:guard.verify_package(plan),'physical_input_hash_mismatch')
realread=Path.read_text
def text_changed(path,*a,**kw):
 text=realread(path,*a,**kw)
 return text.replace('maxCo           0.25','maxCo           0.5') if path==case/'system/controlDict' else text
control=(case/'system/controlDict').read_text();import re
wrong=re.sub(r'(\bmaxCo\s+)0\.25',r'\g<1>0.5',control)
with mock.patch.object(Path,'read_text',lambda p,*a,**kw:wrong if p==case/'system/controlDict' else realread(p,*a,**kw)):
 rejects(lambda:launch.semantics(case,plan),'wrong_maxCo_semantics')
wrongplan=plan.copy();wrongplan['ranks']=11
rejects(lambda:launch.semantics(case,wrongplan),'wrong_MPI_ranks')
# Future HEAD classification without editing Git or writing a fictitious receipt.
fake='f'*40
def fake_output(args,**kw):
 if args[1:3]==['rev-parse','HEAD']:return fake+'\n'
 return b'A\0results/example/future_report.json\0'
with mock.patch.object(guard,'verify_package'),mock.patch.object(guard.subprocess,'check_output',side_effect=fake_output),mock.patch.object(guard.subprocess,'run',return_value=mock.Mock(returncode=0)),mock.patch.object(Path,'exists',return_value=True):
 assert guard.reviewed_head_guard(plan)==fake;checks['results_only_future_HEAD']={'result':'PASS','synthetic_test_only':True}
 def sensitive_output(args,**kw):return fake+'\n' if args[1:3]==['rev-parse','HEAD'] else b'M\0docs/routeA_execution_contract_v1.7.json\0'
 with mock.patch.object(guard.subprocess,'check_output',side_effect=sensitive_output):rejects(lambda:guard.reviewed_head_guard(plan),'sensitive_future_HEAD')
after={str(f.relative_to(case)):hashlib.sha256(f.read_bytes()).hexdigest() for f in case.rglob('*') if f.is_file()};assert after==before and not out.exists()
assert json.loads((P/'production_authorization_draft.json').read_text())['AUTHORIZED']=='NO'
record={'result':'PASS','checks':checks,'case_byte_identity_before_after':True,'cold_only':True,'execution_namespace_created':False,'CFD_EXECUTED':'NO','physical_steps_advanced':0,'mocked_checks_do_not_write_fictitious_HEAD_receipts':True}
(P/'launcher_guard_validation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
