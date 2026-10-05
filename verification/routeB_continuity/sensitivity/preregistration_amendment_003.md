# Preregistration Amendment 003 — Pressure-Tolerance Single-Factor Diagnostic

All rules and exact values below are fixed before the first solver call. Existing v1/001/002 are immutable. This is a diagnostic, not a quota, Gate threshold or steady-criterion change.

## research questions

```json
[
  "Does tightening p_rgh absolute tolerance reduce epsilon_phi_mean/max?",
  "Do QoI/U/T/heat variation bands systematically decrease?",
  "Is pressure precision a meaningful, negligible or unresolved contributor to current band?",
  "Does preserved tight-branch band weaken the primary-cause hypothesis?"
]
```

## single factor

```json
"p_rgh_absolute_tolerance"
```

## common parent

```json
{
  "Ra_test": 30000,
  "grid": [
    20,
    20,
    1
  ],
  "source": "zero",
  "iteration": 12000,
  "tree_hashes": {
    "U": "1e319f4661afed3992a6be31f954effd3b7a49582e5552380063da01995349fe",
    "alphat": "e29fe1c6dddb9eb38423349801b4d71a8ae5f21aa25d800bc26798fbd46f12db",
    "phi": "b221f60d0bcd87a4f684f530cd619ed0c31ae1d21c02341e695ee14f5c7f6801",
    "T": "ba8484010268a9dae6c869a4cc20fe28f16a47855a1b763fbee0d402201c28f3",
    "p": "9a08968b558df1d5d259c2642c6e722d8bfbefc5b18f7dac3fa22baeb20d3725",
    "p_rgh": "f22af178a878ad88fca991483f8aac68f9af46171ee69332f80cfc41628a3dc3",
    "uniform/time": "906fbe54ab7952035b4fca38bf552537e5329585befa9faaa3e8834b5a930d5d"
  }
}
```

## levels

```json
{
  "P10": 1e-10,
  "P8": 1e-08,
  "P12": 1e-12
}
```

## execution order

```json
[
  "P10",
  "P8",
  "P12"
]
```

## run interval

```json
[
  12000,
  18000
]
```

## unchanged

```json
[
  "U/T tolerances1e-12 and relTol0",
  "p relTol0",
  "PCG/DIC and maxIter10000",
  "relaxation",
  "SIMPLE structure",
  "discretization/fvSchemes",
  "mesh",
  "physics/properties",
  "BC",
  "initial complete12000 state",
  "zero source",
  "solver source/binary",
  "native monitor definitions",
  "QoI definitions",
  "original steady criteria",
  "ASCII precision16/writeInterval20/purgeWrite14",
  "controlDict auditPressureTolerance1e-10"
]
```

## monitor capacity parameter

```json
"Keep auditPressureTolerance1e-10 fixed; it supplies original native epsilon stability criteria, not actual PCG tolerance. Actual PCG tolerance is fvSolution.p_rgh.tolerance. Do not retune native criteria per branch."
```

## branch input difference

```json
"Only fvSolution.solvers.p_rgh.tolerance token; parent case_manifest retained byte-identical for provenance, actual branch settings recorded separately."
```

## late statistics

```json
{
  "interval_inclusive": [
    15000,
    18000
  ],
  "sample_interval": 20,
  "sample_count": 151,
  "window_iterations": 200,
  "window_samples": 11,
  "warmup": "Only first restart at12000; first U/T sentinel12020 and incomplete windows until12240 excluded; late15000 onward has complete history.",
  "metrics": [
    "QoI_max_range",
    "U_change_20",
    "T_change_20",
    "U_window_max",
    "T_window_max",
    "heat_window_range",
    "epsilon_phi_mean",
    "epsilon_phi_max",
    "R_recursive",
    "R_true",
    "Np",
    "Kp",
    "P95_normalized",
    "P99_normalized",
    "heat_imbalance"
  ],
  "statistics": [
    "min",
    "median",
    "max",
    "P95"
  ],
  "empirical_uncertainty": "15 disjoint200-iteration blocks (15000,15200],...,(17800,18000],10 samples/block. Min/max of block medians = empirical variability envelope, not a confidence interval; the inclusive15000 sample belongs to overall151 statistics only."
}
```

## primary

```json
"P12 vsP10; P8 directional diagnostic"
```

## resolved change rule

```json
"Effective block-median envelopes must not overlap, and absolute overall median change must exceed the fixed matching historical_resolution_proxy from prior C/R median shift. Where no historical proxy exists, use zero and explicitly no certified uncertainty bound. No arbitrary factor2 or percentage cutoff."
```

## classification

```json
{
  "STRONG_EFFECT": "Resolved P12 reductions in recursive pressure residual, epsilon mean and max, plus all four QoI_max_range/U_change_20/T_change_20/heat_window_range; all corresponding medians non-increasing P8\u2192P10\u2192P12.",
  "LIMITED_EFFECT": "Resolved pressure-residual decrease and at least one epsilon mean/max decrease, but not all four major bands resolve decreases; remaining bands are nonzero and no major-band resolved increase. Non-monotone medians within overlapping scatter may coexist with LIMITED_EFFECT; disclose this rather than treat them as resolved causal reversals.",
  "NO_RESOLVED_EFFECT": "Pressure residual resolves a decrease, but neither epsilon nor any major band resolves a decrease/increase; finite experiment has insufficient resolution, not proof of zero effect.",
  "INCONCLUSIVE": "Incomplete/nonfeasible branches, unresolved pressure change, resolved contrary responses, or any case not meeting the above rules. Preserve all nonmonotone/worsened data.",
  "monotonicity": "Per metric descriptive median order: FLAT if exactly equal, MONOTONIC if P8>=P10>=P12, otherwise NON_MONOTONIC (including tightening-induced increase). Overall seven primary metrics: any NON_MONOTONIC ->NON_MONOTONIC; all FLAT ->FLAT; otherwise MONOTONIC; missing ->INCONCLUSIVE. Separate empirical resolved-change assessment.",
  "primary_cause": "NOT_SUPPORTED only if epsilon improves with resolved pressure response, none of QoI/U20/T20 decreases resolves, and all three retain median above unchanged1e-8 with overlapping block envelopes and median shifts within prior scatter proxy. STRONG_EFFECT supports pressure precision as a contributor but primary cause remains INCONCLUSIVE without replicated/longer evidence. All other cases INCONCLUSIVE.",
  "contributor": "Do not call coupled-solver response pure continuity. A resolved pressure/epsilon effect alone does not establish meaningful or negligible contribution to QoI/U/T band."
}
```

## ratios

```json
"Report P12/P10 and P8/P10 median ratios for every metric; zero denominator ->null, no floor"
```

## normalization scales

```json
{
  "U_Up_reference_m_s": 0.0051293067249479985,
  "T_DeltaT_K": 1.0,
  "p_rgh_parent_centered_internal_RMS_m2_s2": 5.64631031820992e-05,
  "phi_characteristic_face_flux_m3_s": 2.564653362473999e-09,
  "rule": "All scales frozen from common12000: Up=max internal |U|, pscale=centered internal RMS. Same gauge/reference in both branches. Flux=Up*(L/20)*depth."
}
```

## field canonicalization

```json
"Reuse immutable amendment002 Float64/internal+physical patch values/pressure gradients/empty patch canonicalization; U max/RMS vector norm, scalars max/RMS, gradients separate. Frozen common12000 Up/T/p/phi scales."
```

## mapping

```json
"Audit true and recursive pressure residuals, Np,Kp, epsilon/(Kp*R), reference/mapping defects and physical-flux evidence. Report deviations; solver tolerance is never epsilon threshold."
```

## steady evaluation

```json
"Native criteria unchanged with capacity parameter1e-10; postprocess original U/T initial<=1e-8 and pressure final<=1.1*branch tolerance (unchanged preregistered functional rule). Record qualification, never resume Arm1/Arm2. If original native monitor auto-terminates before18000, preserve/STOP without disabling it or restarting."
```

## STOP

```json
[
  "parent/input/binary/source mismatch",
  "any unexpected factor difference",
  "NaN/Inf/fatal/unstable/abnormal exit",
  "P10 cannot reproduce previous continuous C18000 raw/payload hashes",
  "P12 linear stall/breakdown ->NOT_FEASIBLE, no alternate",
  "need formal data, existing preregistration edit, U/T/relaxation/other factor change",
  "failure to reach18000 in one original-settings process; no retry/restart"
]
```

P12 preflight permits only an attempt, not a guarantee: no prior1e-12 feasibility evidence or universal floor. A stalled/broken P12 is preserved as NOT_FEASIBLE, never replaced by1e-11. Each branch has one fresh process at12000, no intermediate restart. P10 must reproduce previous continuous C18000 before P8/P12 start. Run and environment/source/input digests are retained. No other grid, formal data, Arm1/Arm2, git add/commit/push. Stop here; later factors require a separate task.
