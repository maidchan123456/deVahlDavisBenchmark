"""Check review accounting and frozen inputs; does not invoke any solver."""
import csv, datetime, hashlib, json, math, os, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
PREP = ROOT / 'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation'
OUT = PREP / 'resource_review'
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    return json.loads(p.read_text())
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)
def main():
    a = read(OUT / 'resource_accounting.json')
    r = read(PREP / 'DiagnosticTransient_resource_feasibility_review.json')
    authority = a['authority']
    assert git('rev-parse', 'HEAD').strip() == authority['actual_HEAD']
    assert git('diff', '--stat') == ''
    assert git('diff', '--cached', '--stat') == ''
    protected = authority['protected_code_and_contract_sha256']
    for name, expected in protected.items():
        assert digest(ROOT / name) == expected, name
    assert not list((ROOT / 'docs').glob('routeA_diagnostic_transient_contract_v1.3.*'))
    b = a['breakdown']
    assert {x['category'] for x in b} == set('ABCDEFGHIJ')
    assert sum(x['legacy_numeric_bytes_per_step'] for x in b) == a['legacy_per_step_bytes']
    assert sum(x['legacy_primary_bytes'] for x in b) == 5825629244755728
    assert sum(x['corrected_primary_bytes'] for x in b) == 6392273389723944
    assert math.isclose(sum(x['legacy_fraction'] for x in b), 1)
    assert a['legacy_per_step_bytes'] * 600183 == a['original_projection_reconstructed_bytes']
    for scenario in a['step_solve_scenarios']:
        primary = 0
        for series in scenario['series']:
            n = math.ceil(scenario['physical_time_s'] / series['h_s'])
            assert n == series['planning_steps']
            assert series['solve_counts']['all_native_fv_solve_calls'] == n * 145
            assert series['solve_counts']['scalar_component_total_2D'] == n * 169
            if not series['conditional_series']:
                primary += n
        assert primary == scenario['primary_planning_steps']
    free = authority['filesystem']['free_user_bytes']
    for policy in a['policy_scenarios']:
        assert math.isclose(policy['fraction_of_free'], policy['primary_bytes'] / free)
        if 'parts' in policy:
            assert sum(policy['parts'].values()) == policy['primary_bytes']
            assert policy['retained_raw_record_slots'] == policy['full_raw_audit_steps'] * 1141 + policy['selected_raw_bundles'] * 59
    assert r['recommended_retained_bytes'] == 395182571008
    assert r['recommended_peak_bytes'] == r['recommended_retained_bytes'] + 16 * 2**30 == 412362440192
    assert r['conditional_all_three_peak_bytes'] == r['recommended_peak_bytes'] + r['conditional_Co0125_additional_bytes'] == 673180296704
    assert r['recommended_retained_bytes'] <= .5 * free
    assert r['recommended_peak_bytes'] <= .55 * free
    assert r['conditional_all_three_peak_bytes'] > .7 * free
    assert not r['recommended_policy_applied'] and not r['diagnostic_v1_3_created']
    status = r['status']
    assert status['DIAGNOSTIC_TRANSIENT_RESOURCE_READY'] == 'NO'
    assert status['RECOMMENDED_STORAGE_ESTIMATE_BYTES'] == r['recommended_peak_bytes']
    for key in ['SOLVER_EXECUTED', 'PRODUCTION_SOLVER_EXECUTED', 'CFD_TRANSIENT_EXECUTED', 'CASE_GENERATED', 'MESH_GENERATED', 'INITIALIZATION_EXECUTED', 'DIAGNOSTIC_CONTRACT_CHANGED', 'U01_CHANGED', 'U02_CHANGED', 'U03_CHANGED', 'U04_CHANGED', 'FORMAL_CRITERIA_CHANGED', 'HISTORICAL_STATUS_CHANGED']:
        assert status[key] == 'NO'
    contract = read(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.2.json')
    required = set(contract['sampling']['required_primary_and_stage_columns'])
    classified = {x['item'] for x in r['evidence_classification']}
    assert required <= classified
    markdown = (PREP / 'DiagnosticTransient_resource_feasibility_review.md').read_text()
    assert sum(line.startswith('## ') and line[3:4].isdigit() for line in markdown.splitlines()) == 21
    text_status = (OUT / 'final_status.txt').read_text()
    for key, value in status.items():
        assert f'{key} = {value}' in text_status
        assert f'{key} = {value}' in markdown
    # Verify original input manifests/hashes rather than executing U04 again.
    inputs = {}
    stream = PREP / 'u04_verification/final/tests/observed_1'
    entries = [json.loads(line) for line in (stream / 'manifest.jsonl').read_text().splitlines()]
    assert len(entries) == 1152
    for entry in entries:
        path = stream / entry['file']
        assert digest(path) == entry['sha256'], entry['file']
        inputs[str(path.relative_to(ROOT))] = entry['sha256']
    for name in ['manifest.jsonl', 'complete.json']:
        path = stream / name
        inputs[str(path.relative_to(ROOT))] = digest(path)
    for data in a['actual_fields']:
        assert sum(item['bytes'] for item in data['files']) == data['file_content_bytes']
        for item in data['files']:
            path = ROOT / item['path']
            assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256']
            inputs[item['path']] = item['sha256']
    for item in a['steady_log_evidence']:
        assert digest(ROOT / item['path']) == item['sha256']
        inputs[item['path']] = item['sha256']
    for name in ['resource_estimate.json', 'tests/verification_summary.json']:
        path = PREP / 'u04_verification/final' / name
        inputs[str(path.relative_to(ROOT))] = digest(path)
    inputs.update(protected)
    (OUT / 'verified_input_sha256.json').write_text(json.dumps(inputs, indent=2) + '\n')
    sv = os.statvfs(ROOT)
    result = {'result': 'PASS', 'verification_time': datetime.datetime.now().astimezone().isoformat(), 'checks': ['exclusive category accounting', 'scenario step and native solve counts', 'policy component totals and budget limits', 'status and 21-section report consistency', 'all required evidence columns classified', 'frozen source/contract SHA unchanged', 'all 1152 existing healthy-stream manifest hashes valid', 'existing field/log hashes unchanged', 'HEAD unchanged; tracked/index diffs empty; no v1.3 created'], 'protected_files_checked': len(protected), 'existing_input_files_hashed': len(inputs), 'free_user_bytes_at_end': sv.f_bavail * sv.f_frsize, 'free_inodes_at_end': sv.f_favail, 'no_solver_executed': True, 'notes': 'Read-only verification of saved artifacts; no native U04 driver or replay solver invocation. Report free storage remains the timestamped accounting capture.'}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    (OUT / 'end_git_status.txt').write_text(git('status', '--short'))
    (OUT / 'end_git_diff_stat.txt').write_text(git('diff', '--stat'))
    (OUT / 'end_df.txt').write_text(subprocess.check_output(['df', '-B1', str(ROOT)], text=True) + subprocess.check_output(['df', '-i', str(ROOT)], text=True))
    artifacts = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'artifact_sha256.json']
    artifacts += list(PREP.glob('DiagnosticTransient_resource*')) + [PREP / 'DiagnosticTransient_evidence_policy_comparison.csv']
    artifacts += list((ROOT / 'Scripts/routeA/resource_review').glob('*.py'))
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(artifacts))}
    (OUT / 'artifact_sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    main()
