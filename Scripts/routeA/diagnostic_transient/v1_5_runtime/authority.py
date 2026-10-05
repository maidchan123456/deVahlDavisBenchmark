"""Exact authority lineage verification. Read-only; no numerical or execution code."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

from pins import MANIFEST_SHA256

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PREP = 'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/'


def need(condition, code):
    if not condition:
        raise ValueError(code)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'STOP_DUPLICATE_AUTHORITY_KEY')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def repository_path(root, relative):
    rel = Path(relative)
    need(not rel.is_absolute() and '..' not in rel.parts, 'STOP_PATH_ESCAPE')
    current = root
    need(not root.is_symlink(), 'STOP_REPOSITORY_SYMLINK')
    for part in rel.parts:
        current = current / part
        need(not current.is_symlink(), 'STOP_REPOSITORY_SYMLINK')
    return current


def verify_file(path, digest, realpath=None):
    path = Path(path)
    need(path.is_file(), 'STOP_MISSING_PINNED_FILE:' + str(path))
    if realpath is not None:
        need(str(path.resolve()) == realpath, 'STOP_REALPATH_IDENTITY:' + str(path))
    need(sha(path) == digest, 'STOP_PINNED_SHA256:' + str(path))


def manifest():
    path = HERE / 'runtime_authority_manifest.json'
    need(not path.is_symlink(), 'STOP_MANIFEST_SYMLINK')
    verify_file(path, MANIFEST_SHA256)
    m = load(path)
    need(m['schema'] == 'routeA_runtime_authority_mapping/1.0', 'STOP_MAPPING_SCHEMA')
    return m


def checker(root):
    path = root / 'Scripts/routeA/diagnostic_transient/v1_5/check_contract_consistency.py'
    spec = importlib.util.spec_from_file_location('frozen_v15_consistency', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_lineage(old, canonical, report, audit):
    need(canonical.get('version') == '1.5' and old.get('version') == '1.4', 'STOP_UNKNOWN_AUTHORITY_VERSION')
    need(canonical['revision_scope'] == 'MACHINE_AUTHORITY_CONSISTENCY_ONLY', 'STOP_REVISION_SCOPE')
    diff = audit.semantic_diff(old, canonical)
    recorded = [dict(row) for row in report['semantic_diff']]
    for erratum in manifest()['semantic_report_errata']:
        rows = [row for row in recorded if row['path'] == erratum['path']]
        actual = [row for row in diff if row['path'] == erratum['path']]
        need(len(rows) == len(actual) == 1
             and rows[0]['after'] == erratum['report_after']
             and actual[0]['after'] == erratum['canonical_after'], 'STOP_UNREGISTERED_REPORT_ERRATUM')
        rows[0]['after'] = erratum['canonical_after']
    need(diff == recorded, 'STOP_SEMANTIC_DIFF_EVIDENCE')
    need(all(x['category'] != 'OUT_OF_SCOPE' for x in diff), 'STOP_OUT_OF_SCOPE_REVISION')
    for section in audit.SCIENTIFIC:
        need(old[section] == canonical[section], 'STOP_SCIENTIFIC_SECTION:' + section)
    for section in ('capacity', 'retention', 'lifecycle', 'immutable_seal',
                    'purge_allowlist_only', 'purge_requires_valid_seal_and_dry_run_and_explicit_authorization',
                    'no_auto_purge_on_preflight_failure', 'source_SHA256'):
        need(old['resource_revision_fix'][section] == canonical['resource_revision_fix'][section],
             'STOP_PERSISTENCE_CAPACITY_SEAL:' + section)
    # Full exact diff evidence also binds sampling/field/audit and all other leaves.
    return diff


def verify_authority(contract_path=None, root=ROOT):
    m = manifest()
    expected = root / m['canonical_path']
    if contract_path is not None:
        need(Path(contract_path).absolute() == expected.absolute(), 'STOP_CANONICAL_PATH_SPOOF')
    for rel, digest in m['pinned_repository_files'].items():
        verify_file(repository_path(root, rel), digest)
    for path, identity in m['critical_identities'].items():
        verify_file(path, identity['sha256'], identity['realpath'])
    c = load(expected)
    old = load(root / m['implementation_contract_path'])
    report = load(root / PREP / 'DiagnosticTransient_v1_4_authority_consistency_fix.json')
    audit = checker(root)
    diff = verify_lineage(old, c, report, audit)
    check_result = audit.check(c, root)
    need(not check_result['errors'], 'STOP_CANONICAL_CONSISTENCY_CHECK')
    sources = c['resource_revision_fix']['source_SHA256']
    need(sources == old['resource_revision_fix']['source_SHA256']
         == c['resource_revision']['implementation_sha256'], 'STOP_IMPLEMENTATION_HASH_MAPPING')
    for rel, digest in sources.items():
        need(m['pinned_repository_files'].get(rel) == digest, 'STOP_IMPLEMENTATION_SET_INCOMPLETE')
    native = c['u04_build_authority']['native_source_sha256']
    native_digest = hashlib.sha256(json.dumps(native, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    need(native_digest == m['native_semantic_source_set_sha256'], 'STOP_NATIVE_SOURCE_SET')
    for path, digest in native.items():
        need(m['critical_identities'][path]['sha256'] == digest, 'STOP_NATIVE_SET_INCOMPLETE')
    instrument_digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    need(instrument_digest == m['resource_instrumentation_sha256'], 'STOP_RESOURCE_INSTRUMENTATION')
    parent = load(root / PREP / 'u04_verification/final/build/build_provenance.json')
    need(hashlib.sha256(json.dumps(parent['implementation_sha256'], sort_keys=True,
                                  separators=(',', ':')).encode()).hexdigest()
         == m['parent_instrumentation_sha256'], 'STOP_PARENT_INSTRUMENTATION')
    verify_file(root / m['replacement_observer_path'], c['resource_revision']['replacement_library_sha256'])
    need(c['formal_authority']['version'] == '1.7', 'STOP_FORMAL_VERSION')
    ready = c['final_status']['DIAGNOSTIC_TRANSIENT_RESOURCE_READY'] == 'YES'
    return {'schema': 'routeA_runtime_authority_receipt/1.0',
            'canonical_authority': {'path': str(expected), 'version': c['version'], 'sha256': sha(expected)},
            'formal_authority': {'path': str(root / m['formal_path']), 'version': '1.7',
                                 'sha256': sha(root / m['formal_path'])},
            'implementation_generation': 'v1.4', 'rule_id': m['rule_id'],
            'manifest_sha256': MANIFEST_SHA256, 'RUNTIME_AUTHORITY_COMPATIBILITY': 'PASS',
            'mapping_input_HEAD': m['mapping_input_HEAD'],
            'semantic_report_errata': m['semantic_report_errata'],
            'RESOURCE_READINESS': 'YES' if ready else 'NO', 'resource_ready': ready,
            'EXECUTION_AUTHORIZED': 'NO', 'production_run_authorized': False,
            'COMPLETE_EXECUTION_CONFIGURATION_FROZEN': 'NO',
            'current_execution_guard': c['diagnostic_execution_guard'],
            'repository_files_verified': len(m['pinned_repository_files']),
            'native_and_library_identities_verified': len(m['critical_identities']),
            'semantic_diff_leaves_verified': len(diff),
            'qualification_permissions': m['permission_matrix'],
            'qualification_execution_authorized': False,
            'timestamp_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat()}
