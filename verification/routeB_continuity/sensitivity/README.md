# Independent Route B Gate G QoI sensitivity experiment

This directory is completely separate from formal cases. Execute only `experiment.py` after preparation, immutable preregistration and successful isolated `wmake`. The script refuses existing run directories and validates case paths, Ra/grid and preregistration/confirmation hashes before each mesh/solver call. Results go to `results/routeB/gateG_sensitivity_experiment`.

`prepare.py` copies stock Foundation v6 source and adds only the controlled integrated pressure RHS and read-only diagnostics/steady monitoring. Original UEqn/TEqn/operators/relaxation remain. The source solver is a separate local binary. Zero-source full-file stock equivalence and a tiny source sign/units/realization gate precede nonzero steady experiments. Any registered STOP preserves partial data and generates a report; do not automatically restart after STOP.

Exploration uses20/40 and pilot20;80 is held out until the confirmation manifest is hashed and frozen. Sources are zero-net internal-face incidence patterns, held fixed using same-grid baseline Up. Numeric stopping, realization and sampling rules are measurement controls, not research quotas. `b_Q` and `tau_mean` stay unresolved.

Large fields, build artifacts and full solver logs are locally ignored under `runs/` and `auditSolver/`. Compact per-run JSON, CSV, manifest hashes, source residual evidence and figures are retained in the result directory. No production or past Case C files are changed. No git add/commit/push is performed.
