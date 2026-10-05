"""Create new v1.5 metadata authority and reports; never overwrite old revisions."""
import copy
import csv
import datetime
import json
import subprocess
from pathlib import Path

from check_contract_consistency import COMPONENTS, GUARD, HASHES, NEXT, PREP, ROOT, SCOPE, TASK, check, load, sha
from test_contract_consistency import negative_tests


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main(reports_only=False):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == '8707aa00785f83b0620fdc6b8847c200f59b3522'
    initial_status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
    verified = {}
    for version, digest in HASHES.items():
        path = ('docs/routeA_execution_contract_v1.7.json' if version == 'formal'
                else f'docs/routeA_diagnostic_transient_contract_v{version}.json')
        assert sha(ROOT / path) == digest, path
        verified[path] = digest
    old = load(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.4.json')
    c = copy.deepcopy(old)
    target = ROOT / 'docs/routeA_diagnostic_transient_contract_v1.5.json'
    if reports_only:
        existing = load(target)
        assert target.with_suffix('.sha256').read_text().split() == [sha(target), target.name]
        prior_report = load(ROOT / (PREP + 'DiagnosticTransient_v1_4_authority_consistency_fix.json'))
        initial_status = prior_report['start_guard']['git_status_short']
    else:
        assert not target.exists(), 'Existing v1.5 authority must not be overwritten'
    c.update(version='1.5', task=TASK, revision_scope=SCOPE,
             prepared_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
             diagnostic_execution_guard=GUARD,
             document_state='MACHINE_AUTHORITY_CONSISTENCY_FINALIZED_RESOURCE_QUALIFICATION_PENDING',
             decision_type='METADATA_CONSISTENCY_V1_5_FROM_IMMUTABLE_V1_4')
    p = c['authority_provenance']
    p['original_contract_fix_input_HEAD'] = p.pop('HEAD')
    p['original_contract_fix_HEAD_equals_requested'] = p.pop('HEAD_equals_requested')
    p['original_preparation_HEAD'] = load(ROOT / 'docs/routeA_diagnostic_transient_contract_v1.0.json')['authority_provenance']['HEAD']
    p['resource_revision_parent_HEAD'] = load(ROOT / (PREP + 'resource_revision/authority.json'))['HEAD']
    p['v1_4_fix_input_HEAD'] = load(ROOT / (PREP + 'resource_revision_fix/start_guard.json'))['HEAD']
    p['current_consistency_fix_input_HEAD'] = head
    p['HEAD_semantics'] = {
        'original_preparation_HEAD': 'v1.0 preparation input HEAD (fd129...); not its resulting commit',
        'original_contract_fix_input_HEAD': 'v1.1 U01-U04 contract-fix input HEAD, inherited by v1.2-v1.4; 74b1... is the commit containing v1.0',
        'original_contract_fix_HEAD_equals_requested': 'Historical v1.1 input verification only',
        'resource_revision_parent_HEAD': 'v1.3 resource-candidate preparation input HEAD from resource_revision/authority.json',
        'v1_4_fix_input_HEAD': 'v1.4 binding/lifecycle fix input HEAD from resource_revision_fix/start_guard.json',
        'current_consistency_fix_input_HEAD': 'v1.5 creation input HEAD; no git commit was made for this task',
        'references_sha256_and_source_inventory': 'Inherited preparation/fix inventories; not a new repository-wide audit or v1.5 creation inventory',
    }
    c['resource_readiness_components'] = COMPONENTS
    c['current_execution_blockers'] = ['COMPUTE_FEASIBILITY_UNRESOLVED', 'MEMORY_FEASIBILITY_UNRESOLVED',
                                       'IO_FEASIBILITY_UNRESOLVED', 'EXPLICIT_FUTURE_RUN_AUTHORIZATION_REQUIRED']
    fix = c['resource_revision_fix']
    evidence_paths = list(fix['test_evidence'].values()) + [
        PREP + 'DiagnosticTransient_resource_revision_fix.json',
        PREP + 'resource_revision_fix/start_guard.json',
        PREP + 'resource_revision/authority.json',
        'Scripts/routeA/diagnostic_transient/v1_4/resource_guard.py',
        'Scripts/routeA/diagnostic_transient/v1_4/launcher.py',
        'Scripts/routeA/diagnostic_transient/v1_4/finalize.py',
    ]
    for path in fix['test_evidence'].values():
        assert load(ROOT / path)['status'] == 'PASS', path
    native = load(ROOT / fix['test_evidence']['native'])
    assert native['complete_required_primary_columns'] is True
    assert native['native_linear_component_solves'] == 169 and native['U01_actual_certificate'] == 'PASS'
    policy = load(ROOT / fix['test_evidence']['policy'])
    assert policy['nonuniform_U03_policy'] == 'PASS' and policy['frozen_U02_controller'] == 'PASS'
    previous_report = load(ROOT / (PREP + 'DiagnosticTransient_resource_revision_fix.json'))
    assert previous_report['final_contract_sha256'] == HASHES['1.4']
    assert previous_report['status']['ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION_FIX'] == 'COMPLETE'
    c['consistency_revision'] = {
        'scope': SCOPE, 'source_version': '1.4',
        'source_path': 'docs/routeA_diagnostic_transient_contract_v1.4.json',
        'source_sha256': HASHES['1.4'], 'source_preserved_byte_for_byte': True,
        'lineage': [
            {'version': v, 'path': f'docs/routeA_diagnostic_transient_contract_v{v}.json',
             'sha256': HASHES[v], 'historical_state': state}
            for v, state in [('1.2', 'U01_U04_CLOSED'), ('1.3', 'RESOURCE_REVISION_CANDIDATE_INCOMPLETE'),
                             ('1.4', 'RESOURCE_BINDING_LIFECYCLE_FIX_FINALIZED')]
        ] + [{'version': '1.5', 'path': 'docs/routeA_diagnostic_transient_contract_v1.5.json',
              'current_state': 'MACHINE_AUTHORITY_CONSISTENCY_ONLY'}],
        'evidence_sha256': {path: sha(ROOT / path) for path in evidence_paths},
        'historical_sections': [key for key in c if key.startswith('inherited_')],
        'frozen_historical_annotations': {
            'inner_convergence.instrumentation_binding_pending': 'Inherited v1.2 annotation; current live qualification is resource_revision.qualification',
            'steady_arrival.validity_dependency': 'Inherited v1.2 dependency text; current binding evidence is evaluator_verification/resource_revision_fix',
            'u04_build_authority': 'Historical v1.2 build/protected-artifact inventory, preserved unchanged',
            'resource_candidate_lineage': 'Historical incomplete v1.3 to finalized v1.4 decision, preserved unchanged',
        },
        'production_supported_semantics': 'Binding implementation supports production observation; not resource qualification or run authorization',
        'schema_semantics': 'Inherited routeA_diagnostic_transient_contract/1.3 format identifier; document revision is version=1.5',
        'runtime_compatibility': 'Unchanged v1.4 launcher.prepare is pinned to version 1.4. This metadata-only v1.5 is not an executable launcher migration; a future authorized revision must bind its chosen authority explicitly.',
        'reviewed_evidence_scope': 'Stored v1.4 synthetic/read-only PASS evidence inspected and hashed; no native tests or solver were re-executed',
    }
    for i, label in [(23, 'v1.4 live primary/control/certificate/arrival collector'),
                     (24, 'v1.4 production resource/runtime/log guard binding')]:
        c['readiness_checklist'][i].update(item=label, status='FIXED', blocker=None,
            evidence=[fix['test_evidence'][key] for key in (('native', 'policy') if i == 23 else ('preflight', 'lifecycle'))])
    c['readiness_checklist'][25]['item'] = 'production compute/I/O/memory resource qualification'
    c['pre_run_resource_review'].update(revision_complete=True, resource_revision_complete=True,
        storage_revision_complete=True, overall_resource_ready=False, compute_review_required=True,
        next_single_task=NEXT, planning_model='resource_revision_fix.capacity',
        review_scope='Completed storage/evidence revision review; production compute/memory/I/O qualification remains unresolved')
    rr = c['resource_revision']
    rr['U04_scope'] = 'Equations/native graph/math unchanged; inherited v1.4 online validation, packing, persistence, cadence and guards unchanged. U04 CLOSED evidence immutable; live binding synthetically qualified, production resource qualification unresolved.'
    rr['commit']['normal_discard'] = 'nonselected raw arrays only after successful live evaluation; v1.4 binding synthetically qualified, production resource qualification and run authorization remain pending'
    rr['trust_basis'][6] = 'production blocked pending compute/memory/I/O resource qualification and explicit future run authorization; v1.4 primary/control/certificate/arrival binding PASS'
    guards = rr['resource_guards']
    guards['native_primary_binding_complete'] = True
    guards['storage_guard_authority'] = {
        'legacy_0p55_guard_status': 'PER_SERIES_ONLY',
        'fraction_rule': '0 < current_series_working_peak_bytes <= 0.55 * current_verified_free_bytes',
        'sequential_reserve_rule': 'current_verified_free_bytes > current_series_working_peak_bytes + measured_existing_permanent_bytes + max(32 * 2**30, int(0.10 * current_verified_free_bytes))',
        'combination': 'BOTH_REQUIRED', 'cumulative_peak_fraction_is_a_run_gate': False,
        'free_space_semantics': 'statvfs f_bavail*f_frsize immediately before each series; already excludes retained footprint. Existing permanent in reserve rule is an additional conservative reserve, not actual usage counted twice.',
        'existing_permanent_semantics': 'Measured retained bytes and lifecycle manifests from verified prior production seals in PURGED state; not guaranteed planning reclaim',
        'other_preflight_requirements': ['registered series working/permanent/file caps', 'pinned provenance/source/library hashes',
            'new registered export root', 'required prior production seals and measured retained footprint',
            '0 < planned_files <= 0.05 * current_free_inodes', 'MemAvailable >= 24 * 2**30',
            'Co0.125 separate resource review and explicit conditional authorization'],
        'execution_requirements': ['overall resource ready YES', 'explicit future run authorization', 'immediate preflight recheck'],
        'evidence': ['Scripts/routeA/diagnostic_transient/v1_4/resource_guard.py:preflight',
                     'Scripts/routeA/diagnostic_transient/v1_4/launcher.py:prepare',
                     fix['test_evidence']['preflight']],
        'hierarchy': 'v1.4 resource_guard.preflight retains per-series 0.55; launcher.prepare additionally requires sequential reserve. Neither supersedes the other. Initial-free cumulative 0.560285624635319 is descriptive capacity accounting.',
    }
    c['sampling']['full_fields']['production_binding_qualified'] = True
    c['final_status'].update(DIAGNOSTIC_CONTRACT_VERSION='1.5', FINAL_DIAGNOSTIC_CONTRACT_VERSION='1.5',
        PARENT_DIAGNOSTIC_CONTRACT_SHA256=HASHES['1.2'],
        PARENT_DIAGNOSTIC_CONTRACT_PATH=c['parent_diagnostic_authority']['path'],
        FORMAL_ROUTE_A_CONTRACT_SHA256=HASHES['formal'], CURRENT_EXECUTION_GUARD=GUARD,
        EXECUTION_AUTHORIZED='NO', COMPLETE_EXECUTION_CONFIGURATION_FROZEN='NO',
        ROUTE_A_DIAGNOSTIC_TRANSIENT_AUTHORITY_CONSISTENCY_FIX='COMPLETE', REVISION_SCOPE=SCOPE,
        LEGACY_0P55_GUARD_STATUS='PER_SERIES_ONLY',
        SAMPLING_RULE='every native stage evaluated/compact receipts; inherited v1.4 selected binary field/raw audit policy and live binding synthetically qualified; production resource qualification unresolved')
    result = check(c)
    assert not result['errors'], result['errors']
    if reports_only:
        c['prepared_at'] = existing['prepared_at']
        assert c == existing, 'Report refresh must preserve the existing v1.5 authority'
    negatives = negative_tests(c)
    assert all(x['status'] == 'PASS' for x in negatives), negatives
    if not reports_only:
        write(target, c)
    digest = sha(target)
    if not reports_only:
        target.with_suffix('.sha256').write_text(digest + '  ' + target.name + '\n')
    result.update(contract_path=str(target.relative_to(ROOT)), contract_sha256=digest,
                  negative_tests=negatives, negative_tests_status='PASS')
    out = ROOT / PREP
    checks_path = out / 'DiagnosticTransient_contract_consistency_checks.json'
    write(checks_path, result)
    diff_path = out / 'DiagnosticTransient_v1_4_v1_5_semantic_diff.csv'
    with diff_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'category', 'operation', 'before', 'after'])
        writer.writeheader()
        for row in result['semantic_diff']:
            writer.writerow(dict(row, before=json.dumps(row['before'], ensure_ascii=False), after=json.dumps(row['after'], ensure_ascii=False)))
    status = dict(c['final_status'])
    status.update(SOURCE_CONTRACT_VERSION='1.4', SOURCE_CONTRACT_SHA256=HASHES['1.4'],
        SOURCE_CONTRACT_HASH_VERIFIED='YES', NEW_DIAGNOSTIC_CONTRACT_CREATED='YES',
        NEW_DIAGNOSTIC_CONTRACT_VERSION='1.5', NEW_DIAGNOSTIC_CONTRACT_SHA256=digest,
        PARENT_VERSION_SHA_CONSISTENT='YES', FORMAL_ROUTE_A_VERSION='1.7', FORMAL_ROUTE_A_SHA256=HASHES['formal'],
        FORMAL_AUTHORITY_CONSISTENT='YES', STALE_V1_3_EXECUTION_GUARD_REMOVED='YES',
        LIVE_PRIMARY_BINDING_STATUS_CONSISTENT='YES', PRODUCTION_PREFLIGHT_STATUS_CONSISTENT='YES',
        READINESS_CHECKLIST_STALE_ITEMS_FIXED='YES', RESOURCE_REVISION_COMPLETE_STATUS_CONSISTENT='YES',
        NEXT_SINGLE_TASK_CONSISTENT='YES', AUTHORITY_HEAD_SEMANTICS_RESOLVED='YES', LEGACY_0P55_GUARD_SEMANTICS_RESOLVED='YES',
        SEQUENTIAL_PRIMARY_PEAK_FRACTION=0.560285624635319, CONSISTENCY_CHECKER_IMPLEMENTED='YES',
        CONSISTENCY_CHECKER_PASS='YES', ACTIVE_CURRENT_STATE_CONTRADICTIONS=0, NEGATIVE_TESTS='PASS',
        SCIENTIFIC_SECTIONS_CHANGED='NO', PERSISTENCE_POLICY_CHANGED='NO', SEAL_PURGE_POLICY_CHANGED='NO',
        CAPACITY_ESTIMATES_CHANGED='NO')
    # Required report fields from the task; no dependency on a temporary attachment.
    keys = (
        'ROUTE_A_DIAGNOSTIC_TRANSIENT_AUTHORITY_CONSISTENCY_FIX SOURCE_CONTRACT_VERSION SOURCE_CONTRACT_SHA256 '
        'SOURCE_CONTRACT_HASH_VERIFIED NEW_DIAGNOSTIC_CONTRACT_CREATED NEW_DIAGNOSTIC_CONTRACT_VERSION '
        'NEW_DIAGNOSTIC_CONTRACT_SHA256 REVISION_SCOPE PARENT_DIAGNOSTIC_CONTRACT_VERSION '
        'PARENT_DIAGNOSTIC_CONTRACT_SHA256 PARENT_VERSION_SHA_CONSISTENT FORMAL_ROUTE_A_VERSION '
        'FORMAL_ROUTE_A_SHA256 FORMAL_AUTHORITY_CONSISTENT STALE_V1_3_EXECUTION_GUARD_REMOVED '
        'CURRENT_EXECUTION_GUARD LIVE_PRIMARY_BINDING_STATUS_CONSISTENT PRODUCTION_PREFLIGHT_STATUS_CONSISTENT '
        'READINESS_CHECKLIST_STALE_ITEMS_FIXED RESOURCE_REVISION_COMPLETE_STATUS_CONSISTENT NEXT_SINGLE_TASK_CONSISTENT '
        'AUTHORITY_HEAD_SEMANTICS_RESOLVED LEGACY_0P55_GUARD_SEMANTICS_RESOLVED LEGACY_0P55_GUARD_STATUS '
        'SEQUENTIAL_PRIMARY_PEAK_FRACTION STORAGE_FEASIBILITY DIAGNOSTIC_TRANSIENT_STORAGE_READY '
        'MEMORY_FEASIBILITY IO_FEASIBILITY COMPUTE_FEASIBILITY '
        'DIAGNOSTIC_TRANSIENT_RESOURCE_READY DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY '
        'COMPLETE_EXECUTION_CONFIGURATION_FROZEN EXECUTION_AUTHORIZED CONSISTENCY_CHECKER_IMPLEMENTED '
        'CONSISTENCY_CHECKER_PASS ACTIVE_CURRENT_STATE_CONTRADICTIONS NEGATIVE_TESTS '
        'SCIENTIFIC_SECTIONS_CHANGED U01_CHANGED U02_CHANGED '
        'U03_CHANGED U04_EQUATION_SEMANTICS_CHANGED PERSISTENCE_POLICY_CHANGED '
        'SEAL_PURGE_POLICY_CHANGED CAPACITY_ESTIMATES_CHANGED PRODUCTION_SOLVER_EXECUTED '
        'CFD_TRANSIENT_EXECUTED PRODUCTION_DATA_PURGED HISTORICAL_DATA_PURGED '
        'FORMAL_CRITERIA_CHANGED HISTORICAL_STATUS_CHANGED FORMAL_GATE_J_CURRENTLY_ALLOWED '
        'FORMAL_GATE_J_EXECUTED FORMAL_GATE_J_PASS BENCHMARK_CORE_PASS '
        'ROUTE_A_CHARACTERIZED ALL_ROUTE_A_GATE_F ALL_RA_NEEDS_320 '
        'DOWNSTREAM_TRANSIENT_READY PARTICLE_COUPLING_READY NEXT_SINGLE_TASK '
        'RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK USER_DECISION_REQUIRED '
    ).split()
    assert all(key in status for key in keys), [key for key in keys if key not in status]
    final_status = {key: status[key] for key in keys}
    final_text = '\n'.join(f'{key} = {value}' for key, value in final_status.items())
    sections = [
        ('Overall result', 'COMPLETE. New v1.5 changes machine authority metadata only. Source v1.4 and all historical authorities remain byte-for-byte unchanged. No run authorization.'),
        ('v1.4 parent verification', f'Input HEAD {head}; v1.4/v1.3/v1.2/formal v1.7 hashes match all supplied authorities. Existing untracked Route A cases were left untouched. Verification remained scoped to the contract lineage and referenced v1.4 evidence/source.'),
        ('Detected inconsistencies', 'Corrected A–G: duplicate v1.2 SHA inherited from v1.1; stale v1.3 guard; two OPEN binding checklist entries; incomplete revision/obsolete next task; native binding false; inherited current-state text; ambiguous HEAD. Also corrected sampling.full_fields.production_binding_qualified=false and trust_basis[6] stale qualification blocker. Qualified binding means synthetic implementation verification, not production CFD qualification.'),
        ('Parent SHA correction', f'All current parent version/path/SHA fields point to v1.2 ({HASHES["1.2"]}). Formal v1.7 SHA remains unchanged.'),
        ('Execution guard correction', f'{GUARD}. Remaining blockers: compute, memory, I/O qualification and explicit future run authorization. execution_authorized=false.'),
        ('Readiness checklist correction', 'Entries 23/24 FIXED with native/policy and preflight/lifecycle evidence; null blockers. Production compute/I/O/memory qualification stays OPEN. Source v1.4 OPEN entries remain in the immutable source.'),
        ('Resource-review status correction', 'revision_complete/resource_revision_complete/storage_revision_complete=true. resource_ready/overall_resource_ready=false; compute_review_required=true. Completed review scope is storage/evidence revision, not overall resource qualification.'),
        ('Live-binding flag correction', 'Stored live_native_validation PASS: complete required columns, 145 fv solves/169 component records, U01 PASS, controller PASS, bitwise non-invasiveness. live_policy_validation PASS verifies U03/controller/anomaly bindings; lifecycle validation retains selected fields. Native-primary and field-binding status flags now agree. Evidence was inspected, not re-executed.'),
        ('Authority HEAD semantics', 'v1.0 actual preparation input fd129af05d43e3551cf0d4a037b5dd8f54ccbe4a. Inherited 74b1f7b2c0e844ac559997277ce30dde2450b3f8 is v1.1 fix input HEAD, as confirmed by v1.0/v1.1 contracts and git show of the v1.0 commit. v1.3 input ed2371e88c2d728bfbf8fffd21cd99497c1b9afc comes from resource_revision/authority.json; v1.4 fix input 7369926b5517ce1da49829759653224489614575 from start_guard.json. Current v1.5 input HEAD is recorded separately. Historical inventories and U04 build authority remain unchanged.'),
        ('Storage guard 0.55 vs sequential 0.5603 resolution', 'PER_SERIES_ONLY, retained at 0.55. resource_guard.preflight receives each series working peak, current statvfs free and file budget. launcher.prepare additionally checks current free > working peak + measured existing permanent + max(32 GiB, int(10% current free)). BOTH_REQUIRED. Current free already excludes retained bytes; existing permanent is an additional conservative reserve. Cumulative 0.560285624635319 uses initial free and is descriptive, not the per-series gate numerator. Primary planning guard checks below pass; no threshold, capacity, safety reserve, lifecycle or code changes. Fresh measurements and checks are still required before each future series. Co0.125 remains conditional, infeasible at the current worst-case planning caps, and requires separate review/authorization.'),
        ('Historical/current-state separation', 'Preserved every inherited_* section, resource_candidate_lineage, original v1.3 INCOMPLETE fact, U04 build authority, and frozen scientific annotation strings. Explicit scope descriptions identify their historical meaning. v1.5 readiness is current. Unchanged v1.4 launcher is version-pinned to 1.4; this metadata-only revision does not migrate it or claim executable v1.5 support.'),
        ('v1.4→v1.5 changed JSON paths', f'{len(result["semantic_diff"])} leaf changes, individually listed and classified in DiagnosticTransient_v1_4_v1_5_semantic_diff.csv and the JSON report. Only STATUS_METADATA/PROVENANCE_METADATA/GUARD_METADATA/READINESS_METADATA/RESOURCE_GUARD_CLARIFICATION allowed; 0 out-of-scope changes.'),
        ('Scientific-section invariance', 'All 17 required scientific sections semantically equal; remaining non-allowlisted contract leaves are also equal. resource_revision_fix is wholly equal, including capacity, P1 evidence/cadence, R0–R4, seal/purge lifecycle and source hashes. Formal authority/status and all historical sections equal. U01/U02/U03/U04 equation semantics unchanged.'),
        ('Consistency checker', 'check_contract_consistency.py checks real lineage and evidence hashes, duplicate statuses/next tasks, readiness/guard hierarchy, frozen scientific/historical/source/library equality, strict metadata diff allowlist and storage guard semantics. CLI validates sidecar; JSON loader rejects duplicate keys. Result: 0 contradictions, 0 stale active blockers, 0 mismatched parent hashes, 0 conflicting current next tasks.'),
        ('Negative tests', f'{len(negatives)} synthetic mutated contracts fail the intended invariant, including all six requested mutations. Additional tests cover formal SHA, revision status, extra next-task field, unresolved readiness, sampling binding, frozen configuration, threshold relaxation, cumulative gate, HEAD ambiguity, scientific/capacity and historical changes. No CFD, mesh, case or purge tests.'),
        ('Final readiness', 'Scientific/technical/storage/live binding/evidence lifecycle READY. Memory/I/O/compute UNRESOLVED. Overall resource NOT_READY; complete execution configuration remains unfrozen; execution unauthorized. Formal Gate J, Gate F, 320 need and downstream/particle status unchanged.'),
        ('Exact next task', NEXT + '. Recommended gpt-6.1-sol / medium. USER_DECISION_REQUIRED=YES refers to selecting/authorizing a future task; this completed fix grants no run authorization.'),
    ]
    report_path = out / 'DiagnosticTransient_v1_4_authority_consistency_fix.json'
    report = {'task': TASK, 'status': final_status, 'start_guard': {'HEAD': head, 'git_status_short': initial_status,
        'authority_sha256': verified, 'git_status_capture_scope': 'Contract-generation snapshot after new checker scripts were written'}, 'sections': [{'number': i, 'title': title, 'text': text} for i, (title, text) in enumerate(sections, 1)],
        'detected_inconsistency_count': 10, 'semantic_diff': result['semantic_diff'],
        'scientific_invariants': result['scientific_invariants'], 'consistency_checks_path': str(checks_path.relative_to(ROOT)),
        'negative_tests': negatives, 'storage_guard_planning_checks': result['storage_guard_planning_checks'],
        'final_contract_path': str(target.relative_to(ROOT)), 'final_contract_sha256': digest,
        'evidence_sha256': c['consistency_revision']['evidence_sha256']}
    write(report_path, report)
    md = '# Route A diagnostic transient v1.4 authority consistency fix → v1.5\n\n'
    for i, (title, text) in enumerate(sections, 1):
        md += f'## {i}. {title}\n\n{text}\n\n'
        if i == 10:
            md += '| Co | Planning current free B | Working peak B | Existing permanent B | Peak/current free | 55% | Reserve |\n|---|---:|---:|---:|---:|---|---|\n'
            for row in result['storage_guard_planning_checks']:
                md += f'| {row["Co"]} | {row["planning_current_free"]} | {row["working_peak"]} | {row["existing_permanent"]} | {row["working_peak_fraction"]:.9f} | PASS | PASS |\n'
            md += '\nPlanning arithmetic uses initial free minus prior planned permanent after hypothetical valid purge; it is not a current disk measurement or purge authorization.\n\n'
        if i == 12:
            md += '| JSON pointer | Classification | Operation |\n|---|---|---|\n'
            for row in result['semantic_diff']:
                md += f'| `{row["path"]}` | {row["category"]} | {row["operation"]} |\n'
            md += '\n'
    md += '## Required final status\n\n```text\n' + final_text + '\n```\n'
    (out / 'DiagnosticTransient_v1_4_authority_consistency_fix.md').write_text(md)
    doc = '# Route A diagnostic transient contract v1.5\n\n'
    doc += 'Revision scope: `MACHINE_AUTHORITY_CONSISTENCY_ONLY`. Canonical machine authority is [v1.5 JSON](routeA_diagnostic_transient_contract_v1.5.json); its SHA is in the companion sidecar.\n\n'
    doc += 'Lineage: v1.2 U01–U04 closed → incomplete v1.3 resource candidate → finalized v1.4 resource/binding/lifecycle fix → v1.5 authority consistency fix. All previous versions remain immutable.\n\n'
    for index in (4, 6, 7, 8, 9, 10, 12, 15, 16):
        title, text = sections[index]
        doc += f'## {title}\n\n{text}\n\n'
    doc += 'Detailed report, changed paths, invariants and synthetic mutation results are in `results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_v1_4_authority_consistency_fix.{md,json}`.\n\n'
    doc += '## Required final status\n\n```text\n' + final_text + '\n```\n'
    target.with_suffix('.md').write_text(doc)
    print(json.dumps({'status': 'COMPLETE', 'new_sha256': digest, 'changed_paths': len(result['semantic_diff']),
                      'contradictions': result['contradictions'], 'negative_tests': len(negatives)}, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports-only', action='store_true', help='Refresh checks/reports while preserving published v1.5 JSON and sidecar')
    main(parser.parse_args().reports_only)
