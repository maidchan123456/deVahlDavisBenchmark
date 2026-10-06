"""Publish preparation-only reports; never authorize or launch measurements."""
import csv,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from common import ROOT,HERE,PREP,PLAN,CONTRACT,load,sha,authority,atomic
from fixture import topology,graph,state

def main(request_text):
 receipt=authority.verify_authority();cfg=load(PLAN);t=topology();g=graph()
 old=load(PREP/'runtime_authority_compatibility/artifact_sha256.json')
 assert all(sha(ROOT/p)==h for p,h in old.items())
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 assert head=='8135eec17dab5c66082bb25b9e3509ee2cc39ac9'
 assert not subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).strip()
 log=PREP/'timing_preparation_tests_verified.log';history_log=PREP/'timing_preparation_fixture_history_test.log'
 assert 'Ran 26 tests' in log.read_text() and log.read_text().endswith('OK\n')
 assert history_log.read_text().endswith('OK\n')
 tests=[m[1] for m in re.finditer(r'^(test_\w+) .*? \.\.\. ok$',log.read_text(),re.M)]
 assert len(tests)==26
 text=Path(request_text).read_text();block=text.split('# 121. REQUIRED FINAL STATUS')[1].split('# 122.')[0]
 pairs=re.findall(r'([A-Z][A-Z0-9_]+)\s*=\s*\n([^\n]+)',block)
 statuses={k:v.strip().split(' / ')[0] for k,v in pairs}
 for k,v in list(statuses.items()):
  if v=='YES':statuses[k]='NO'
  if v=='PASS':statuses[k]='FAIL'
 statuses.update(ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION_FIX='INCOMPLETE',CANONICAL_AUTHORITY_HASH_VERIFIED='YES',FORMAL_AUTHORITY_HASH_VERIFIED='YES',RUNTIME_AUTHORITY_COMPATIBILITY='PASS',TARGET_SIZE_DIAGNOSTIC_HARNESS_PREPARED='NO',TARGET_SIZE_NATIVE_ADAPTER_IMPLEMENTED='YES',TARGET_TOPOLOGY_VALIDATED='YES',TARGET_CELL_COUNT='25600',TARGET_INTERNAL_FACE_COUNT='50880',CALLBACK_GRAPH_SUPPORTED='YES',CALLBACKS_PER_STEP_EQUIVALENT='1144',MATRIX_PACKET_GRAPH_SUPPORTED='YES',MATRIX_PACKETS_PER_STEP_EQUIVALENT='701',NEXT_SINGLE_TASK='FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION',RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK='gpt-6.1-sol / medium',USER_DECISION_REQUIRED='YES',DIAGNOSTIC_TRANSIENT_STORAGE_READY='YES',ALL_RA_NEEDS_320='YES')
 yes=['INDEPENDENT_RESOURCE_WATCHDOG_PREPARED','WATCHDOG_OUT_OF_PROCESS','PROCESS_GROUP_SUPERVISION','WALL_TIME_GUARD_IMPLEMENTED','NATIVE_RSS_MONITOR_IMPLEMENTED','BACKEND_RSS_MONITOR_IMPLEMENTED','COMBINED_RSS_MONITOR_IMPLEMENTED','VMSIZE_AS_MONITOR_IMPLEMENTED','HOST_MEMORY_MONITOR_IMPLEMENTED','DISK_FREE_MONITOR_IMPLEMENTED','FILE_COUNT_MONITOR_IMPLEMENTED','PROCESS_IO_MONITOR_IMPLEMENTED','LOADAVG_MONITOR_IMPLEMENTED','WATCHDOG_FAILURE_FAILS_CLOSED','PARTIAL_EVIDENCE_PRESERVED','CENSORED_TRIAL_POLICY_IMPLEMENTED','QUALIFICATION_STAGE_RECEIPT_IMPLEMENTED','QUALIFICATION_MANIFEST_IMPLEMENTED','U03_SCALING_RUNNER_PREPARED','IO_RUNNER_PREPARED','QUALIFICATION_NAMESPACE_ISOLATED']
 for k in yes:statuses[k]='YES'
 for k in ['PROCESS_GROUP_KILL_TEST','WALL_TIMEOUT_TEST','MEMORY_GUARD_TEST','DISK_GUARD_TEST','FILE_COUNT_GUARD_TEST','PATH_TRAVERSAL_TEST','SYMLINK_ESCAPE_TEST','PRIVILEGE_ESCALATION_TEST']:statuses[k]='PASS'
 statuses.update(LINEAR_SOLVER_POLICY_CHANGED='NO',TEMPORAL_POLICY_CHANGED='NO',RETENTION_POLICY_CHANGED='NO',Q1_Q2_ACTUAL_MEASUREMENT_AUTHORIZED='NO')
 blockers=[
 {'id':'B1','stage':'Q1','issue':'Recurring measurement resets the frozen Writer to startup full-audit schedule. Startup cost separation and selected-audit binding are incomplete; retaining all three ON full audits has not been reconciled with 12GiB stage scratch. No target measurement exists to resolve size uncertainty.','resolution':'Bind resource-only schedule context and constructor timing explicitly; preserve production policy; validate selected/full retention and all repeats inside the fixed budget using tiny fixtures.'},
 {'id':'B2','stage':'Q2','issue':'Per-trial file layout cannot finish registered U03, primitive and memory repeats under 256 files without prohibited cleanup.','static_evidence':{'U03_trials':21,'primitive_trials':15,'memory_trials':21,'IO_trials':3,'files_per_U03_trial_lower_bound':11,'U03_files_lower_bound':231,'primitive_files_lower_bound_each':17,'U03_plus_primitives_lower_bound':486,'stage_files_limit':256},'resolution':'Use a stage append ledger/trace with immutable trial indexes and bounded publication overhead. Do not raise the budget or purge evidence.'},
 {'id':'B3','stage':'Q2','issue':'Scalar primitive currently uses full controller-state payload rather than a separate compact receipt; spans are primarily aggregate. Isolated memory packing does not yet reproduce all Writer.share/ring accounting. Registered repeat and host stability decisions are not integrated into stage output.','resolution':'Complete small receipt/primitive classes, per-class exclusive/inclusive span accounting and actual Writer memory-event binding; consume frozen repeatability/host rules.'},
 {'id':'B4','stage':'Q1/Q2','issue':'Whole-stage positive receipt, nested supervision and quota-reserved STOP publication have not been tested end to end. Current tests establish per-trial behavior, immutable publication and negative permission checks.','resolution':'Add tiny whole-stage tests using a test-only validator substitute, with no real authorization receipt and no target campaign.'}]
 sections=[
 ('Executive summary','INCOMPLETE. Native adapter and independent per-trial watchdog are implemented and tiny tests pass. Both stage readiness flags remain NO; future execution is explicitly denied.'),
 ('Authority verification',f'Canonical v1.5 and formal v1.7 SHA verified. Runtime compatibility PASS, 91 repository pins and 851 native/library identities verified. Previous runtime artifact hashes also match; HEAD remains {head}.'),
 ('Existing preparation blockers','Original target adapter was absent and watchdog interface-only. This new namespace supplies code and tests; the old frozen plan and runtime mapping are unchanged.'),
 ('New harness architecture','Read-only mesh and stored graph -> manufactured Python fixture -> original C++ Json representation/serializer -> AF_UNIX -> frozen evaluator/Live/Writer. OFF retains preparation/parsing/graph traversal. No CFD command or time API is used.'),
 ('Target-size topology adapter','Read-only existing A-Ra1e6-fine mesh: 25600 cells, 50880 internal faces, 102720 total faces, 640 active boundary faces and 51200 empty faces. Four 160-face wall patches and two 25600-face empty patches. Empty field-patch arrays contain zero values, as the native schema requires.'),
 ('Target-size fixture generation','rho/rhoFluidThermo:rho,U,T,e,p,p_rgh,phi,K,gh have target shapes. Constant resource-only values, synthetic volumes/centres/thermal context and zero explicit terms have no physical interpretation. Old histories for rho/e/K have 0/1/2 levels at synthetic indices 0/1/2. b=Apsi and native original hashes/epochs are regenerated; no time is advanced.'),
 ('Callback/matrix graph mapping','Registered 42 stage/term classes map to 1144 recurring callbacks (1141 physical +3 controller), with 701 scalar matrix packets; one constructor is excluded. Matrix slots and explicit terms remain class-specific. Vector U field and 169 manufactured scalar solve records are represented; the registered graph has no U vector-matrix callback.'),
 ('Qualification authority integration','Every public target worker requires an external future authorization, sealed stage receipt, frozen authority verifier and permission validator. The direct native executable calls a fixed permission helper. Harness manifest readiness=false blocks both stages before execution. No actual authorization receipt was issued.'),
 ('Independent watchdog','Separate process samples /proc RSS, VmSize, HWM, CPU ticks, IO and host state around 20ms. Disk/files/statvfs sampling around100ms. Trace overhead and uncertainty are disclosed; missed peaks or invalid samples cannot establish feasibility.'),
 ('Process-group supervision','Dedicated groups, registered nested groups, PPid tracking, subreaper and parent-death SIGKILL. TERM grace <=1s then KILL; cleanup pulses keep watchdog heartbeat alive. Escape and supervisor-crash tests pass. Whole-stage nested integration remains B4.'),
 ('Memory/AS monitoring','Plan-based native/backend AS and RSS 8GiB, combined RSS16GiB, host MemAvailable24GiB. RLIMIT_AS plus sampled VmSize; aggregate process limits conservative. Simultaneous max(native+backend) is separate from sum of individual peaks. Tests use small limits, never8GiB allocation.'),
 ('Disk/file monitoring','Frozen per-stage scratch/file/inode/free-space guards; before-write checks plus independent monitoring, logical/allocated bytes, symlink rejection. No purge. Overall file layout and STOP-publication reserves are not qualified; B2/B4 prevent READY.'),
 ('Wall-time enforcement','Plan supplies stage/trial budgets. Q1 order OFF/ON/ON/OFF/OFF/ON. Q2 U03 trial15s/suite120s; whole Q2 420s. External supervisor enforces deadlines; no in-process-only timeout or retry.'),
 ('Partial/censored evidence','STOP retains immutable receipt and trace/log/result/manifest where generated, exit/signal and stop reason; watchdog failure invalidates the sample. Timeout is CENSORED, excluded from fit, and stops larger U03 N. Small tests inspect retained partial artifacts before temporary-test cleanup; no real qualification evidence was created.'),
 ('Q1 runner readiness','Implemented fixed native/backend runner, graph assertions, original full processing, native/time-v CPU/RSS and class byte summaries. Startup/full-audit schedule and bounded repeat retention remain B1; Q1_MEASUREMENT_READY=NO.'),
 ('Q2/U03 runner readiness','Frozen arrival_candidate algorithm for N100..6400 and three repeats, eight histories/all three windows. Completed-only fit requires three sizes/three repeats, records local slopes/residuals and LOW_CONFIDENCE projection. Tiny N4 only was executed. Whole Q2 remains NO because B2-B4.'),
 ('IPC/memory/I/O runner readiness','Native parse/hash/serialization/ACK and backend decode/canonical/replay/pack/SHA/publish/QoI/U01 spans implemented. ACK is inclusive. Seven memory-event tiny paths and bounded nonsparse IO with real file/directory fsync and readback tested. Memory-event sizes are actual packets, not theoretical maxima. Full9GiB is streamed, never allocated or claimed qualified. Small scalar/per-class and memory sharing remain B3.'),
 ('Namespace/permission safety','Production series and external/traversal/symlink paths rejected, unknown mode and Q1-to-Q3 escalation rejected. Source case is read-only. Authorization schema accepts no external execution command. Fresh output and immutable publication prevent historical overwrite.'),
 ('Positive tests','26 unittest checks passed, including full four-cell native/backend graph. After startup-history correction, focused full native/backend test passed again. These are correctness/process tests only; no timing values are reported as target performance.'),
 ('Negative tests','Wrong authority/topology/callback/matrix counts, missing/tampered permission/receipt, direct native missing permission, prohibited execution inputs/namespace/path/escalation, wall/memory/disk/file limits, group escape and watchdog crash all reject/stop as expected.'),
 ('Measurement-readiness decision','Both Q1/Q2 readiness flags are NO. New harness manifest enforces this independently of future external permission. No automatic Q3 or production decision; resource feasibility remains UNRESOLVED.'),
 ('Remaining blockers','B1 schedule/startup/scratch reconciliation; B2 bounded file layout; B3 complete scalar/class/memory/stability accounting; B4 tiny whole-stage positive/partial/quota-reserve integration.'),
 ('Exact next task','FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION. Do not start RUN_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION until these blockers are closed. Q3 and production remain unauthorized.')]
 validation={'status':'PASS_SHAPE_AND_GRAPH_ONLY','counts':t['counts'],'patches':[{k:p[k] for k in ('name','type','nFaces','startFace')} for p in t['patches']],'mesh_SHA256':t['mesh_SHA256'],'callbacks_recurring':len(g)-1,'constructor_excluded':1,'matrix_packets':701,'callback_classes':len(cfg['callback_classes']),'old_history_counts':{str(i):{k:len(state(t,i)[k]['old_times']) for k in ('rho','e','K')} for i in (0,1,2)},'fields':list(state(t)),'Q1_timing_result':None,'CFD_executed':False}
 atomic(PREP,'TimingQualification_fixture_validation.json',validation)
 atomic(PREP,'TimingQualification_measurement_readiness.json',{'fix':'INCOMPLETE','Q1_measurement_ready':False,'Q2_measurement_ready':False,'actual_measurements_authorized':False,'blockers':blockers,'required_final_status':statuses})
 watchdog_tests=[name for name in tests if any(key in name for key in ('child','wall','memory_guard','disk_guard','file_count','supervisor','escape'))]
 atomic(PREP,'TimingQualification_watchdog_tests.json',{'status':'PASS_PER_TRIAL_TINY_ONLY','tests':watchdog_tests,'whole_stage_end_to_end':'NOT_VERIFIED','test_log_SHA256':sha(log),'small_override_only':True,'no_large_allocation':True})
 with (PREP/'TimingQualification_negative_tests.csv').open('x',newline='') as f:
  w=csv.writer(f);w.writerow(['test','expected','result','scope','evidence'])
  for name in tests:w.writerow([name,'REJECT_OR_STOP' if any(x in name for x in ('wrong','guard','timeout','crash','escalation','permission','tampering','traversal','escape','missing')) else 'SUCCESS','PASS','TINY_CORRECTNESS_ONLY',str(log.relative_to(ROOT))])
 source={str(p.relative_to(ROOT)):sha(p) for p in sorted(HERE.iterdir()) if p.is_file()}
 artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted((PREP/'timing_harness_build_v4').iterdir()) if p.is_file()}
 artifacts.update(t['mesh_SHA256'])
 source_bundle=PREP/'compute_review/native_0_on/full_2.bin';assert sha(source_bundle)==cfg['authority_sha256'][str(source_bundle.relative_to(ROOT))];artifacts[str(source_bundle.relative_to(ROOT))]=sha(source_bundle)
 # Read-only dependencies of the fixed executable; no solver linkage.
 for path in ['/usr/bin/python3','/usr/bin/time','/usr/lib/x86_64-linux-gnu/libcrypto.so.3','/usr/lib/x86_64-linux-gnu/libstdc++.so.6','/usr/lib/x86_64-linux-gnu/libgcc_s.so.1','/usr/lib/x86_64-linux-gnu/libc.so.6','/usr/lib/x86_64-linux-gnu/libm.so.6','/lib64/ld-linux-x86-64.so.2']:artifacts[path]=sha(Path(path))
 atomic(PREP,'TimingQualification_harness_manifest.json',{'schema':'nonCFD_timing_harness/1','source_SHA256':source,'artifact_SHA256':artifacts,'canonical_SHA256':sha(CONTRACT),'plan_SHA256':sha(PLAN),'measurement_ready':{'Q1':False,'Q2':False},'blockers':blockers,'CFD_linkage':False,'actual_execution_authorized':False})
 report={'task':'FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION','generated_UTC':datetime.now(timezone.utc).isoformat(),'HEAD':head,'required_final_status':statuses,'authority_receipt':receipt,'sections':[{'number':i,'title':title,'content':body} for i,(title,body) in enumerate(sections,1)],'blockers':blockers,'tests':{'passed':26,'log_SHA256':sha(log),'startup_history_focused_test_SHA256':sha(history_log),'campaign_values':None},'original_files_changed':False,'actual_authorization_receipt_created':False}
 atomic(PREP,'DiagnosticTransient_timing_qualification_preparation_fix.json',report)
 md='# Diagnostic transient timing qualification preparation fix\n\n'
 md+='Status: **INCOMPLETE**. Q1/Q2 measurement readiness: **NO**.\n\n'
 for i,(title,body) in enumerate(sections,1):md+=f'## {i}. {title}\n\n{body}\n\n'
 md+='## Required final status\n\n```text\n'+''.join(f'{k} = {v}\n' for k,v in statuses.items())+'```\n'
 (PREP/'DiagnosticTransient_timing_qualification_preparation_fix.md').write_text(md)
 atomic(PREP,'TimingQualification_invariance_verification.json',{'HEAD':head,'initial_known_HEAD':head,'tracked_diff_empty':True,'runtime_artifact_SHA256':old,'authority_receipt':receipt,'mesh_SHA256':t['mesh_SHA256'],'new_case_created':False,'git_add_commit_push_executed':False})
 print(json.dumps({'fix':'INCOMPLETE','tests':len(tests),'required_status_keys':len(statuses),'Q1_ready':False,'Q2_ready':False}))

if __name__=='__main__':main(sys.argv[1])
