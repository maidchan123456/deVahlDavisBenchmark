#!/usr/bin/env python3
"""Clone a generated case and add an execute-at-start constructor field dump."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    args = parser.parse_args()
    source = Path(args.case).resolve()
    target = ROOT / "results/routeA/initialization_check" / source.name
    if target.exists():
        raise SystemExit(f"Refusing to overwrite initialization evidence: {target}")
    shutil.copytree(source, target)
    control = target / "system/controlDict"
    text = control.read_text()
    start = text.index("functions\n{")
    text = text[:start] + """endTime 1;

functions
{
    constructorState
    {
        type writeObjects;
        libs (\"libutilityFunctionObjects.so\");
        objects (p p_rgh rho gh);
        writeOption anyWrite;
        executeAtStart true;
    }
}
"""
    # Remove the earlier endTime entry so the last-write behavior is explicit.
    lines = text.splitlines()
    seen_new = False
    output = []
    for line in reversed(lines):
        if line.strip().startswith("endTime"):
            if not seen_new:
                seen_new = True
                output.append(line)
        else:
            output.append(line)
    control.write_text("\n".join(reversed(output)) + "\n")
    print(target)


if __name__ == "__main__":
    main()
