#!/usr/bin/env bash
# Diagnostic module build + synthetic native fixtures ONLY. No CFD/case utilities.
set -eo pipefail
u04_source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
u04_repo_root=$(cd -- "$u04_source_dir/../../../.." && pwd)
u04_output=${1:?Specify a new isolated evidence directory}
if [[ -e "$u04_output" ]]; then
    echo 'Evidence directory must be new; prior evidence is immutable.' >&2
    exit 1
fi
if source /opt/openfoam13/etc/bashrc; then :; else exit 1; fi
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
python3 - "$u04_repo_root" <<'PY'
import hashlib,sys
from pathlib import Path
r=Path(sys.argv[1])
for name,expected in {
 'docs/routeA_diagnostic_transient_contract_v1.1.json':'574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675',
 'docs/routeA_execution_contract_v1.7.json':'fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60',
}.items():
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==expected,'STOP_U04_PARENT_OR_SOURCE_MISMATCH'
PY
mkdir -p -- "$u04_output"
u04_output=$(cd -- "$u04_output" && pwd)
python3 "$u04_source_dir/build_u04.py" "$u04_output/build" > "$u04_output/build.log" 2>&1
python3 "$u04_source_dir/verify_u04.py" "$u04_output/build" "$u04_output/tests" > "$u04_output/verification.log" 2>&1
python3 "$u04_source_dir/resource_estimator.py" "$u04_output/tests/observed_1" "$u04_output/resource_estimate.json" > "$u04_output/resource_estimate.log" 2>&1
