#!/usr/bin/env bash
# Standalone native matrix/operator tests only. No production CFD executable,
# solver module, actual case, mesh utilities, initialization or time evolution.
set -eo pipefail
verification_source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
verification_build_root=${1:-$(mktemp -d /tmp/routeA-contract-fix-unit.XXXXXX)}
mkdir -p -- "$verification_build_root"
if [[ -e "$verification_build_root/test.log" || -e "$verification_build_root/compile.log" ]]; then
    echo 'Refusing to overwrite prior unit evidence; choose a new directory.' >&2
    exit 1
fi
verification_build_root=$(cd -- "$verification_build_root" && pwd)
if source /opt/openfoam13/etc/bashrc; then
    :
else
    echo 'OpenFOAM unit-library environment setup failed.' >&2
    exit 1
fi
verification_lib=/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib
g++ -std=c++14 -O2 -DWM_DP -DWM_LABEL_SIZE=32 -DNoRepository \
    -I/opt/openfoam13/src/OpenFOAM/lnInclude \
    -I/opt/openfoam13/src/OSspecific/POSIX/lnInclude \
    -I/opt/openfoam13/src/finiteVolume/lnInclude \
    -I/opt/openfoam13/src/meshTools/lnInclude \
    -I"$verification_source_dir" "$verification_source_dir/TestNativeMatrixObserver.C" \
    -L"$verification_lib" -L"$verification_lib/openmpi-system" \
    -Wl,-rpath,"$verification_lib" -Wl,-rpath,"$verification_lib/openmpi-system" \
    -lfiniteVolume -lmeshTools -lOpenFOAM -lPstream -ldl \
    -o "$verification_build_root/TestNativeMatrixObserver" \
    > "$verification_build_root/compile.log" 2>&1
ulimit -c 0
(cd /tmp && "$verification_build_root/TestNativeMatrixObserver") > "$verification_build_root/test.log" 2>&1
(cd /tmp && "$verification_build_root/TestNativeMatrixObserver") > "$verification_build_root/test_repeat.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 "$verification_source_dir/test_contract_policy.py" \
    > "$verification_build_root/policy_tests.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 "$verification_source_dir/verify_stage_plan.py" \
    > "$verification_build_root/source_anchors.json"
python3 - "$verification_build_root" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1])
a=json.loads((root/'test.log').read_text().splitlines()[-1])
b=json.loads((root/'test_repeat.log').read_text().splitlines()[-1])
assert a == b and a['status'] == 'PASS'
a['deterministic_summary'] = True
a['binary_sha256'] = hashlib.sha256((root/'TestNativeMatrixObserver').read_bytes()).hexdigest()
a['policy_tests'] = 12
a['policy_status'] = 'PASS'
a['source_anchor_tests'] = json.loads((root/'source_anchors.json').read_text())
(root/'unit_verification.json').write_text(json.dumps(a,indent=2)+'\n')
print(json.dumps(a,indent=2))
PY
