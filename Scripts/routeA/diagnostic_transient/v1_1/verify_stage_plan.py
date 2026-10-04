"""Read-only exact-source anchor check; no solver hooks are inserted."""
import hashlib
import json
from pathlib import Path

plan = json.loads(Path(__file__).with_name('instrumentation_stage_plan.json').read_text())
for entry in plan['entries']:
    source = Path(entry['source']).read_bytes()
    if hashlib.sha256(source).hexdigest() != entry['sha256']:
        raise ValueError('SOURCE_HASH_MISMATCH: ' + entry['source'])
    lines = source.decode().splitlines()
    actual = [i + 1 for i, line in enumerate(lines) if entry['anchor'] in line]
    if actual != entry['lines']:
        raise ValueError('SOURCE_ANCHOR_MISMATCH: ' + entry['source'])
print(json.dumps({'status': 'PASS', 'anchors': len(plan['entries']),
                  'actual_runtime_hooks_connected': False}, sort_keys=True))
