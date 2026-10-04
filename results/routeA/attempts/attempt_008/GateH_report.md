# Route A Gate H attempt 008

## 1. Executive result

Execution **COMPLETE**, perturbed computed=True, accepted=True, final iteration=12000, Gate D=PASS. Formal Gate H **PASS**; sensitivity characterization completed=True. No baseline rerun, tuning, cap extension, other grid or downstream execution.

## 2. Contract/provenance

HEAD `8be31bbf38eaec5f38fb3a544288e0a574b80c11`. Sole current guard v1.7 SHA `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`; Amendment007 SHA `9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592`; all start guards PASS. Actual runtime Foundation13 build13-441953dfbb42, fluid/heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy, laminar Stokes/Fourier/SIMPLE verified from actual initialization and primary logs. Canonical analyzer/runtime checker scripts unchanged. Protection: 223995 pre-existing files unchanged; contract/threshold/numerics immutable.

## 3. Baseline evidence

Historical accepted A-Ra1e6-fine, grid160x160x1, Ra1e6/Pr.71, betaDeltaT1e-3 at9000. Baseline owner HISTORICAL_ACCEPTED_STEADY_BASELINE; read-only reuse, no rerun/restart/continuation/analyzer output. Final segment/seal/native field/mesh hashes verified against v1.7. Source: `results/routeA/cases/A-Ra1e6-fine/segments/end_9000`.

## 4. Perturbed case generation

One NEW A-H-Ra1e6-fine-beta1e-4, attempt008. Hash-guarded unchanged generator loaded using importlib, BETA set to Decimal1e-4 in memory; canonical main called with A-SMOKE generation role and formal distinct name/grid160/Ra1e6/end3000. Original manifest sealed. Exactly one NEW physicalProperties beta1e-3 literal changed to beta1e-4; raw versus final input hashes separately recorded. Canonical cold U0/T0, EOS/hydrostatic p with pRef=hRef0, p_rgh0; no historical field/mesh copy. blockMesh/checkMesh and isolated one-iteration constructor workflow, runtime provenance and OQ-02 checked before primary. Detailed phase evidence in `cases/A-H-Ra1e6-fine-beta1e-4/`.

## 5. beta/g/Ra/Pr verification

| Parameter | Actual / relation |
| --- | --- |
| baseline beta | 0.001 |
| perturbed beta | 0.0001 |
| beta ratio | 0.1 |
| g ratio | 10 |
| perturbed g vector | [0.0, -1408.4507042253522, 0.0] |
| Ra from actual g/beta/nu/alpha | 1000000 |
| Pr actual | 0.71 |
| DeltaT | 1 |
| grid | 160x160x1 |

Canonical gravity formula used, not rounded manual value. PhysicalProperties beta and all other held properties checked against frozen inputs. Common-grid mesh hashes match baseline; fixed schemes/relaxation/tolerances match template/baseline. Initial p changes dependently with g/EOS as registered; only beta/g are independent physical changes.

## 6. Execution history

| Start | End | Gate D | Failure components | Seal SHA-256 |
| --- | --- | --- | --- | --- |
| 0 | 3000 | FAIL | ['QOI_RWIN_PASS', 'RESIDUAL_PASS'] | 79c81d1b8ac77712e0b9acebdd7b797b02aca7fe45f6704651d25405c44489b2 |
| 3000 | 6000 | FAIL | ['QOI_RWIN_PASS', 'RESIDUAL_PASS'] | 56d5ea80f1ceb6459304a0e5dbed1ce5b0762acca3caef1232379b49d7da8b3f |
| 6000 | 9000 | FAIL | ['HEAT_TREND_PASS'] | 6e9e985fc106deec06a8b59036267a02bf878a58800a7634d23d59e934aa712d |
| 9000 | 12000 | PASS | NONE | 458e4c6279f390ee9fabe3efd548022513d68df9d2d40846821f307298a49ef7 |

initial3000,+3000,cap30000; one primary branch/concurrency1. Every segment health→raw seal→canonical analyzer→six-boolean D→final seal before continuation. No tuning/retry/extension; only startFrom/endTime changes. Intermediate FAILs retained. Stop reason: None.

## 7. Gate D

```json
{
  "status": "PASS",
  "booleans": {
    "NORMAL_EXIT": true,
    "NO_FATAL_OR_NAN": true,
    "INPUT_PROVENANCE_PASS": true,
    "QOI_RWIN_PASS": true,
    "RESIDUAL_PASS": true,
    "HEAT_TREND_PASS": true
  },
  "failure_components": [],
  "computed": true,
  "accepted": true,
  "numerical_evaluation": {
    "contract_version": "1.0",
    "window_start_iteration": 11801,
    "window_end_iteration": 12000,
    "window_inclusive": true,
    "Nu_samples": 200,
    "velocity_samples": 20,
    "velocity_sample_iterations": [
      11810,
      11820,
      11830,
      11840,
      11850,
      11860,
      11870,
      11880,
      11890,
      11900,
      11910,
      11920,
      11930,
      11940,
      11950,
      11960,
      11970,
      11980,
      11990,
      12000
    ],
    "Rwin": {
      "Nu_bar_0": 8.162005169060867e-08,
      "Umax": 3.4810201431040285e-07,
      "Wmax": 3.0173872504066437e-08
    },
    "Nu_monitor": "hot-wall Q/(k*DeltaT*W), not the hot/cold pair average",
    "Nu_bar_0_last": 8.863347542476841,
    "Nu_bar_1_last": 8.863347541280728,
    "heat_imbalance_start": 1.8080556395475032e-10,
    "heat_imbalance_end": 1.3495046361980488e-10,
    "heat_trend_method": "OLS exact rational arithmetic on original decimal Q tokens",
    "heat_slope_per_iteration_display": -2.5811490915445843e-13,
    "heat_slope_sign_exact": -1,
    "heat_trend_pass": true,
    "residual_fields": [
      "Ux",
      "Uy",
      "e",
      "p_rgh"
    ],
    "final_initial_residuals": {
      "Ux": 1.831488030218606e-09,
      "Uy": 1.904231750991522e-09,
      "e": 1.180909889294752e-10,
      "p_rgh": 9.582390410729954e-10
    },
    "residual_pass": true,
    "qoi_rwin_pass": true,
    "numerical_checks_pass": true,
    "formal_Gate_D_requires_external_execution_and_provenance_flags": true
  },
  "formal_criteria_unchanged": true
}
```

## 8. Primary Gate H metrics

| QoI | Baseline | Perturbed | Signed Δ | D_H fraction | Threshold fraction | Check |
| --- | --- | --- | --- | --- | --- | --- |
| Nu_bar_cavity | 8.86898945579 | 8.86551246466 | -0.00347699112434 | 0.000392039154142 | 0.002 | PASS |
| Umax | 64.9147345964 | 64.8992091435 | -0.0155254528812 | 0.000239166854455 | 0.002 | PASS |
| Wmax | 219.900261662 | 219.87596235 | -0.0242993115569 | 0.000110501512701 | 0.002 | PASS |

D_H=abs(perturbed−baseline)/abs(baseline). Each criterion is independent, no averaging compensation. Existing threshold .002=.2%, unchanged.

## 9. epsilon_v

| Baseline | Perturbed | Signed Δ | Non-worsening |
| --- | --- | --- | --- |
| 0.000949693061761 | 0.000902645766533 | -4.70472952284e-05 | PASS |

Same frozen reconstructed Gauss-linear div(U) and normalization; require perturbed≤baseline, no slack. Native mass closure is separately recorded and cannot replace this H requirement.

## 10. Density-range diagnostics

| Diagnostic | Baseline | Perturbed | Signed Δ |
| --- | --- | --- | --- |
| rho_min | 0.999503052952 | 0.999950305054 | 0.000447252101595 |
| rho_max | 1.00049694763 | 1.00004969495 | -0.000447252678805 |
| max_relative_density_deviation | 0.000496947629901 | 4.9694951096e-05 | -0.000447252678805 |

Measured amplitude ratio perturbed/baseline: 0.100000378523. Density range comes from final native rho; maximum relative deviation measured as max|rho/rho0−1|. Approximate tenfold reduction at similar T was expected scaling, not assumed or a new acceptance criterion.

## 11. Secondary diagnostics

| Quantity | Baseline | Perturbed | Signed Δ | Absolute Δ | Relative fraction |
| --- | --- | --- | --- | --- | --- |
| Nu_bar_0 | 8.86338339241 | 8.86334754248 | -3.58499314643e-05 | 3.58499314643e-05 | 4.04472309017e-06 |
| Nu_bar_half | 8.86766917628 | 8.86384513983 | -0.00382403645038 | 0.00382403645038 | 0.000431233549015 |
| Nu_bar_1 | 8.86338375634 | 8.86334754128 | -3.62150581168e-05 | 3.62150581168e-05 | 4.0859178743e-06 |
| Umax_Z | 0.85302734375 | 0.85302734375 | 0 | 0 | NOT_EVALUATED |
| Wmax_X | 0.04052734375 | 0.04052734375 | 0 | 0 | NOT_EVALUATED |
| Nu_hot_local_max | 17.8241361702 | 17.8237433376 | -0.000392832577006 | 0.000392832577006 | 2.20393613051e-05 |
| Nu_hot_local_max_Z | 0.0371436599327 | 0.0371562545067 | 1.2594573965e-05 | 1.2594573965e-05 | NOT_EVALUATED |
| Nu_hot_local_min | 0.975666154602 | 0.974896282518 | -0.000769872083765 | 0.000769872083765 | 0.000789073270743 |
| Nu_hot_local_min_Z | 1 | 1 | 0 | 0 | NOT_EVALUATED |
| physical_heat_imbalance | 4.10599116837e-08 | 1.34950327573e-10 | -4.09249613562e-08 | 4.09249613562e-08 | 0.996713331275 |
| section_Nu_deviation | 0.000539266406373 | 0.000260610978779 | -0.000278655427595 | 0.000278655427595 | 0.516730551544 |
| native_mass_epsilon_m | 9.2012824914e-11 | 8.80533211037e-11 | -3.95950381023e-12 | 3.95950381023e-12 | 0.0430320861677 |
| temperature_symmetry | 0.00011037035422 | 1.153148257e-05 | -9.88388716503e-05 | 9.88388716503e-05 | 0.895520109078 |
| velocity_symmetry | 0.000401098248353 | 4.11558290899e-05 | -0.000359942419263 | 0.000359942419263 | 0.897392149532 |
| T_min | 299.50305237 | 299.503050489 | -1.88106196219e-06 | 1.88106196219e-06 | 6.28061032203e-09 |
| T_max | 300.496947048 | 300.496949461 | 2.41316587335e-06 | 2.41316587335e-06 | 8.03058366169e-09 |

All position differences are signed/absolute normalized-coordinate diagnostics; relative field null for positions. No new H thresholds on secondary values. Native mass kg/s flux and reconstructed div(U) remain distinct diagnostics; no Route B operator/causal comparison is performed.

## 12. Formal Gate H result

**PASS**. Accepted-pair eligibility=True. Checks: {"Nu_bar_cavity": "PASS", "Umax": "PASS", "Wmax": "PASS", "reconstructed_velocity_epsilon_v": "PASS"}. Failed components: NONE. Quantified characterization completed=True. D-unaccepted or missing pair cannot be promoted to formal H.

## 13. Scientific interpretation

OBSERVED: Nu_bar_cavity changed by 0.0392039154%, Umax changed by 0.0239166854%, Wmax changed by 0.0110501513%. These are measured common160-grid responses to jointly prescribed beta/10 and g×10 at fixed Ra/Pr. All primary responses satisfy the existing .2% criterion. epsilon_v does not worsen. H evaluates within-Route-A formulation sensitivity, not A/B causal decomposition or a mathematical classical Boussinesq limit.

## 14. Limitations

GATE_H_GRID_INDEPENDENT_CLAIM_ALLOWED=NO. Same-grid cancellation may occur but is not guaranteed; grid/model interaction unknown. Two points cannot establish continuum sensitivity, exact formulation error, A=B, all energy-work terms vanishing, validation or full Verification.

## 15. Gate F reminder

All four historical Gate F groups remain FAIL and needs_320 YES. Ra1e6 Nu fine-medium1.3402375461%>1%; Wmax NON_MONOTONIC_OR_UNDEFINED, p/GCI null. Gate H does not resolve these failures. No320 executed or automatically required before this bounded fixed-grid H.

## 16. Downstream implication

DOWNSTREAM_TRANSIENT_READY=NO. Gate J unexecuted; no transient/particle work authorized or performed. Even H PASS would not alone certify downstream readiness. Preserve partial Verification status and separately review H before any future Gate J preparation.

## 17. Next task

`REVIEW_ROUTE_A_GATE_H_RESULT` / gpt-6.1-sol / medium. USER_DECISION_REQUIRED=YES. Execution stops here; no automatic extra beta points/320/Gate J.

```text
ROUTE_A_GATE_H_ATTEMPT=008
ROUTE_A_GATE_H_EXECUTION=COMPLETE
EFFECTIVE_CONTRACT_VERSION=1.7
EFFECTIVE_CONTRACT_HASH_VERIFIED=YES
EFFECTIVE_CONTRACT_SHA256=fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60
AMENDMENT_007_HASH_VERIFIED=YES
AMENDMENT_007_SHA256=9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592
ANALYZER_HASH_VERIFIED=YES
ANALYZER_SHA256=e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
RUNTIME_CHECKER_HASH_VERIFIED=YES
RUNTIME_CHECKER_SHA256=5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
GATE_H_CLASSIFICATION=FIXED_GRID_MODEL_FORMULATION_SENSITIVITY
GATE_H_BASELINE_CASE=A-Ra1e6-fine
GATE_H_BASELINE_ACCEPTED=YES
GATE_H_BASELINE_FINAL_ITERATION=9000
GATE_H_BASELINE_RERUN=NO
GATE_H_PERTURBED_CASE=A-H-Ra1e6-fine-beta1e-4
GATE_H_PERTURBED_COMPUTED=YES
GATE_H_PERTURBED_ACCEPTED=YES
GATE_H_PERTURBED_FINAL_ITERATION=12000
GATE_H_PERTURBED_GATE_D=PASS
GATE_H_PERTURBED_GATE_D_FAILURE_COMPONENTS=NONE
GATE_H_BASELINE_BETA=1e-3
GATE_H_PERTURBED_BETA=1e-4
GATE_H_BETA_RATIO=0.1
GATE_H_G_RATIO=10
GATE_H_RA_ACTUAL=1000000.0
GATE_H_PR_ACTUAL=0.7100000000000001
GATE_H_RA_HELD_FIXED=YES
GATE_H_PR_HELD_FIXED=YES
GATE_H_DELTA_T_HELD_FIXED=YES
GATE_H_GRID_HELD_FIXED=YES
GATE_H_NUMERICS_HELD_FIXED=YES
GATE_H_NU_CAVITY_RELATIVE_DIFFERENCE=0.0003920391541424215
GATE_H_NU_CAVITY_THRESHOLD=0.002
GATE_H_NU_CAVITY_CHECK=PASS
GATE_H_UMAX_RELATIVE_DIFFERENCE=0.00023916685445488672
GATE_H_UMAX_THRESHOLD=0.002
GATE_H_UMAX_CHECK=PASS
GATE_H_WMAX_RELATIVE_DIFFERENCE=0.00011050151270079289
GATE_H_WMAX_THRESHOLD=0.002
GATE_H_WMAX_CHECK=PASS
GATE_H_BASELINE_EPSILON_V=0.000949693061760976
GATE_H_PERTURBED_EPSILON_V=0.0009026457665325413
GATE_H_EPSILON_V_NON_WORSENING=PASS
GATE_H_BASELINE_MAX_RELATIVE_DENSITY_DEVIATION=0.0004969476299010456
GATE_H_PERTURBED_MAX_RELATIVE_DENSITY_DEVIATION=4.9694951095968776e-05
GATE_H_FORMAL_RESULT=PASS
GATE_H_CHARACTERIZATION_COMPLETED=YES
GATE_H_GRID_INDEPENDENT_CLAIM_ALLOWED=NO
ALL_ROUTE_A_GATE_F=FAIL
ALL_RA_NEEDS_320=YES
GRID_320_EXECUTED=NO
GATE_J_EXECUTED=NO
DOWNSTREAM_TRANSIENT_READY=NO
FORMAL_CRITERIA_CHANGED=NO
NUMERICAL_SETTINGS_CHANGED=NO
PHYSICAL_CHANGES_BEYOND_BETA_G=NO
SOLVER_TUNING_PERFORMED=NO
POST_CAP_EXTENSION_PERFORMED=NO
BASELINE_MODIFIED=NO
HISTORICAL_RESULTS_MODIFIED=NO
ROUTE_B_MODIFIED=NO
NEXT_SINGLE_TASK=REVIEW_ROUTE_A_GATE_H_RESULT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK=gpt-6.1-sol / medium
USER_DECISION_REQUIRED=YES
OVERALL_VERIFICATION_STATUS=VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION
TARGETED_320_REQUIRED_BEFORE_GATE_H=NO
ROUTE_A_SOLVER_EXECUTED=YES
ROUTE_B_SOLVER_EXECUTED=NO
GATE_H_BASELINE_OWNERSHIP=HISTORICAL_ACCEPTED_STEADY_BASELINE
```
