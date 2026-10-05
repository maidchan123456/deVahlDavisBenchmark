"""One frozen Q1 campaign. No retry, optimization, CFD or Q2 dispatch."""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
HERE = ROOT / 'Scripts/routeA/diagnostic_transient/timing_qualification/measurement'
sys.path.insert(0, str(HERE))
from common import atomic, authority, host, load, need, plan, sha, PLAN, CONTRACT, PREP
import runner
from campaign import launch_campaign

reg = load(OUT / 'premeasurement_regression.json')
need(reg['status'] == 'PASS' and reg['tests_run'] == 46 and reg['source_unchanged_during_tests'], 'STOP_PREMEASUREMENT_REGRESSION_FAILURE')
guard = load(OUT / 'start_guard.json')
for path, digest in guard['source_and_authority_SHA256'].items():
    need(sha(ROOT / path) == digest, 'STOP_PREMEASUREMENT_SHA_CHANGED:' + path)
need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == guard['HEAD'], 'STOP_HEAD_CHANGED')
runtime = authority.verify_authority()
need(runtime['RUNTIME_AUTHORITY_COMPATIBILITY'] == 'PASS', 'STOP_Q0_NOT_PASS')
runner.verify_harness()
now = datetime.now(timezone.utc).isoformat()
scope = {
    'schema': 'user_nonCFD_qualification_scope/1',
    'task': 'RUN_ROUTE_A_DIAGNOSTIC_TRANSIENT_NONCFD_TIMING_QUALIFICATION',
    'qualification_id': OUT.name, 'HEAD': guard['HEAD'], 'timestamp': now,
    'user_authorization_scope': 'Q1_Q2_NONCFD_ONLY',
    'authorization_class': 'NONCFD_TIMING_QUALIFICATION',
    'allowed_stages': ['Q1', 'Q2'], 'campaigns_per_stage': 1,
    'forbidden_stages': ['Q3', 'PILOT_CFD', 'PRODUCTION_CFD'],
    'production_execution_authorized': False, 'Q3_authorized': False,
    'CFD_allowed': False, 'physical_time_advance_allowed': False,
    'production_namespace_allowed': False,
    'case_generation_allowed': False, 'mesh_generation_allowed': False,
    'initialization_allowed': False,
    'task_attachment_SHA256': guard['task_attachment_SHA256'],
    'canonical_authority_SHA256': sha(CONTRACT),
    'formal_authority_SHA256': sha(ROOT / 'docs/routeA_execution_contract_v1.7.json'),
    'measurement_readiness_SHA256': sha(PREP / 'TimingQualification_measurement_readiness_v2.json'),
    'blocker_closure_SHA256': sha(PREP / 'TimingQualification_blocker_closure.json'),
    'preparation_fix_002_SHA256': sha(PREP / 'DiagnosticTransient_timing_qualification_preparation_fix_002.md'),
    'runtime_mapping_SHA256': sha(ROOT / 'Scripts/routeA/diagnostic_transient/v1_5_runtime/runtime_authority_manifest.json'),
    'plan_SHA256': sha(PLAN), 'harness_manifest_SHA256': sha(runner.HARNESS_MANIFEST),
    'premeasurement_regression_SHA256': sha(OUT / 'premeasurement_regression.json'),
}
atomic(OUT, 'authorization_scope.json', scope)
auth = {
    'schema': 'nonCFD_timing_authorization/1',
    'authorized_task': scope['task'],
    'task_reference': 'User attachment ef2044e4-7525-40f4-93e5-f56a9a8262ab; scope receipt SHA256=' + sha(OUT / 'authorization_scope.json'),
    'scope': 'NONCFD_TIMING_QUALIFICATION', 'allowed_stages': ['Q1', 'Q2'],
    'execution_authorized': True, 'canonical_SHA256': sha(CONTRACT),
    'plan_SHA256': sha(PLAN), 'harness_manifest_SHA256': sha(runner.HARNESS_MANIFEST),
}
atomic(OUT, 'authorization.json', auth)
atomic(OUT, 'Q0_prerequisite_evidence.json', {
    'Q0_status': 'PASS', 'authority': runtime,
    'harness_SHA256': sha(runner.HARNESS_MANIFEST),
    'regression_SHA256': sha(OUT / 'premeasurement_regression.json'),
    'new_Q0_campaign_executed': False,
    'basis': 'Existing runtime/authority/mesh/build compatibility plus full frozen harness regression; no CFD launcher',
})
commands = {
    'lscpu': ['lscpu'], 'free_bytes': ['free', '-b'],
    'meminfo': ['cat', '/proc/meminfo'], 'disk_bytes': ['df', '-B1'],
    'inodes': ['df', '-i'], 'uptime': ['uptime'],
}
snapshot = {'timestamp': datetime.now(timezone.utc).isoformat(), 'host': host(), 'commands': {}, 'CPU_governors_and_frequencies': {}, 'settings_changed': False, 'serial_execution': True}
for name, argv in commands.items():
    r = subprocess.run(argv, capture_output=True, text=True, check=False)
    snapshot['commands'][name] = {'argv': argv, 'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
for cpu in sorted(Path('/sys/devices/system/cpu').glob('cpu[0-9]*')):
    snapshot['CPU_governors_and_frequencies'][cpu.name] = {
        name: (cpu / 'cpufreq' / name).read_text().strip() if (cpu / 'cpufreq' / name).exists() else 'UNKNOWN'
        for name in ('scaling_governor', 'scaling_cur_freq', 'scaling_min_freq', 'scaling_max_freq')
    }
atomic(OUT, 'host_snapshot_before_Q1.json', snapshot)
atomic(OUT, 'measurement_start_SHA_snapshot.json', {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'pins': {path: sha(ROOT / path) for path in guard['source_and_authority_SHA256']},
    'authorization_SHA256': sha(OUT / 'authorization.json'),
    'authorization_scope_SHA256': sha(OUT / 'authorization_scope.json'),
    'host_snapshot_SHA256': sha(OUT / 'host_snapshot_before_Q1.json'),
})
result = launch_campaign(OUT / 'Q1', 'Q1', OUT / 'authorization.json', {'Q0_status': 'PASS'})
print(json.dumps({'stage': 'Q1', 'status': result['status'], 'STOP_reason': result['STOP_reason'], 'trials': len(result['trials']), 'completed': result['completed_repeats']}, indent=2))
