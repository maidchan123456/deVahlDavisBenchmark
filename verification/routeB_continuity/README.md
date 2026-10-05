# Route B continuity Case C verification

This suite verifies the existing uniform FV continuity operator and pressure residual mapping using independent manufactured fluxes and a new OpenFOAM Foundation v6 microcase. It never runs a production benchmark case or compares with paper reference values. No acceptance threshold or production specification is changed.

The result is operator PASS, stock/audit field equivalence, a quantitatively verified reference-aware mapping in this suite, and **tau_phi UNRESOLVED**. Measurement precision and linear solver capability do not supply a research acceptance budget.

Run from the repository root with Python 3 and NumPy:

```bash
python3 -B verification/routeB_continuity/run_verification.py
python3 -B verification/routeB_continuity/analyze_verification.py
```

`run_verification.py` first requires the synthetic tests to pass, generates the independent template, selects the v6 environment explicitly, compiles the separately named audit binary, and runs the serial suite. It refuses to overwrite an existing microcase directory. For a fresh rerun, move the isolated `verification/routeB_continuity/work/microcases/` directory aside first; retain the existing CSV/report if comparing runs. Re-analysis alone reads the retained independent cases and does not execute a solver.

For operator verification alone:

```bash
python3 -B verification/routeB_continuity/synthetic_operator_tests.py
```

This rewrites synthetic result CSVs. Run `analyze_verification.py` afterward to restore the combined synthetic/microcase CSVs.

Inputs and scope:

- Synthetic grids: 20², 40², 80², 160². Exact streamfunction edge flux; zero-baseline internal perturbations 1e-6, 1e-8, 1e-9 m³/s; physical-wall leakage 1e-8 m³/s. Actual production parser and the unmodified `continuity_metrics` function are used. Only that function is compiled from its AST; analyzer main/reference code is never executed. Uniform cell U=(1,0,0) supplies Up=1 m/s for normalization and is independent of synthetic phi.
- Serialization: in-memory float64, significant-digit ASCII precision16 and diagnostic precision6. Empty patches are represented by zero-length scalar lists. P95/P99 use NumPy's linear empirical percentile and equal cell volumes.
- Microcases: Ra_test=30000, Pr=0.71, closed laminar cavity 0.01×0.01×0.001 m, one depth cell and front/back empty. 20², 40², 80²; p_rgh PCG/DIC tolerances 1e-6/1e-8/1e-10, relTol=0. The three tolerances are controlled test variables, not proposed tau_phi values.
- Each microcase runs 10 SIMPLE iterations. This is an early-pressure-solve verification, not a steady benchmark. A representative 20²/1e-8 stock run establishes final U/T/p_rgh/phi full-file hash equivalence. Separate 20² cases test 5+restart+5 and a corner reference cell.
- ASCII writePrecision16 matches the read-only production template setting. No binary or parallel claim is made.

The copied audit solver retains the stock main, UEqn, TEqn, createFields and transport logic. Only diagnostic additions to main/pEqn and `continuityAudit.H` are present; the diff is saved in `auditSolver/diagnostic_diff.patch`. Installed PCG and other production source/binaries are unchanged. A copied matrix is boundary assembled; the installed PCG's `normFactor` is called without solving. True residual is recomputed at the unrelaxed pressure solve state. Reported recursive residual is recorded as its L1 norm; its vector is not available. The difference of norms must not be interpreted as a vector drift upper bound.

Safety gates stop before further solver work on failed synthetic verification, microcase fatal/nonfinite data, or stock/audit field inequality. A STOP record and partial review are retained on a run failure. Existing benchmark solvers are outside the executable case-path allowlist by construction.

Compact outputs and hashes are in [the results directory](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/caseC_continuity_verification). Raw fields/logs/synthetic files are retained under ignored `work/`; audit binaries and build objects are also ignored. Do not add those large artifacts to Git. No commit is performed by this suite.

See [verification_report.md](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/caseC_continuity_verification/verification_report.md) and [verification_summary.json](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeB/caseC_continuity_verification/verification_summary.json) for measured values, limitations and the remaining independent error-budget decision.
