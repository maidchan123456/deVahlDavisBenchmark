"""Print a read-only compatibility receipt; never executes qualification or CFD."""
import json
import subprocess
from authority import ROOT, verify_authority

if __name__ == '__main__':
    receipt = verify_authority()
    receipt['HEAD'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    print(json.dumps(receipt, indent=2))
