"""Production guards and read-only preflight bridge. No production executor enabled."""
import copy
import importlib.util
import sys
from pathlib import Path
from authority import ROOT, load, manifest, need, repository_path, sha, verify_authority


def production_guards(receipt, explicit_run_authorization_id):
    need(receipt['RUNTIME_AUTHORITY_COMPATIBILITY'] == 'PASS', 'STOP_AUTHORITY_NOT_PASS')
    need(receipt['resource_ready'] is True, 'RESOURCE_READY_NO_NO_EXECUTION')
    need(isinstance(explicit_run_authorization_id, str) and explicit_run_authorization_id.strip(),
         'EXPLICIT_RUN_AUTHORIZATION_REQUIRED')


def legacy_prepare(mapped):
    # Load only the pinned modules, with temporary import names. The immutable
    # launcher.prepare body performs the existing disk/series/C3/lifecycle guards.
    directory = ROOT / 'Scripts/routeA/diagnostic_transient/v1_4'
    names = ('packed', 'log_rotation', 'resource_guard', 'lifecycle')
    saved = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, directory / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        spec = importlib.util.spec_from_file_location('frozen_v14_launcher', directory / 'launcher.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.prepare(mapped)
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def prepare(spec):
    authority = verify_authority()
    m = manifest()
    need(not any(k in spec for k in ('qualification', 'mode', 'resource_ready',
                                     'ignore_resource_ready', 'production_run_authorized')), 'STOP_PRODUCTION_OVERRIDE')
    contract_entries = spec['provenance']['contract']
    need(len(contract_entries) == 1, 'STOP_SINGLE_CANONICAL_AUTHORITY_REQUIRED')
    entry = contract_entries[0]
    expected = ROOT / m['canonical_path']
    need(Path(entry['path']).absolute() == expected and entry['sha256'] == sha(expected), 'STOP_CANONICAL_PROVENANCE')
    for entries in spec['provenance'].values():
        for e in entries:
            path = Path(e['path'])
            need(set(e) == {'path', 'realpath', 'sha256'} and path.is_absolute(), 'STOP_PROVENANCE_IDENTITY_SCHEMA')
            need(str(path.resolve()) == e['realpath'] and sha(path) == e['sha256'], 'STOP_PROVENANCE_IDENTITY')
    case_id = spec['case_id']
    need(isinstance(case_id, str) and Path(case_id).name == case_id and case_id not in ('.', '..'), 'STOP_CASE_ID')
    registered = ROOT / 'results/routeA/diagnostic_transient/diagnostic_attempt_001/series' / case_id
    need(Path(spec['export_root']).absolute() == registered, 'UNREGISTERED_EXPORT_NAMESPACE')
    repository_path(ROOT, str(registered.relative_to(ROOT)))
    mapped = copy.deepcopy(spec)
    v14 = ROOT / m['implementation_contract_path']
    mapped['provenance']['contract'] = [{'path': str(v14), 'realpath': str(v14.resolve()), 'sha256': sha(v14)}]
    result = legacy_prepare(mapped)
    # The compatibility mapping remains explicit; never mutate canonical JSON or
    # falsify its version. Direct-v1.4 prepare is only a read-only implementation check.
    result.update(contract_path=str(expected), contract_sha256=sha(expected),
                  resource_ready=authority['resource_ready'],
                  canonical_provenance=spec['provenance'],
                  mapped_implementation_provenance=mapped['provenance'],
                  runtime_authority_receipt=authority, production_run_authorized=False)
    return result


def run(spec, explicit_run_authorization_id):
    # Reject the current canonical NO before case preflight, output writes or
    # process construction. No supplied spec/qualification flag can override it.
    receipt = verify_authority()
    production_guards(receipt, explicit_run_authorization_id)
    prepare(spec)
    # A future production executor requires its own reviewed authorization/binding;
    # this compatibility task introduces no reachable launch path.
    raise ValueError('STOP_PRODUCTION_EXECUTOR_NOT_AUTHORIZED_OR_IMPLEMENTED')
