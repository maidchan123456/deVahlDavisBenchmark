# Gate H execution contract preparation

Ownership: PRE_GATE_H_EXECUTION_CONTRACT_PREPARATION. **COMPLETE; technical readiness YES.** No solver/case/mesh/clone/continuation executed.

HEAD `8b3cf320508a9f70b7cc5be533a7346581ad8b7d`; parent v1.6 hash `c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59` verified; 9952 start guards PASS, review seal PASS, accepted baseline final fields/mesh/seals PASS.

Full steady review linkage preserved: 12 computed/accepted, D PASS all, fine E/G PASS all, F FAIL all; partial Verification, needs_320 YES.

Scientific question: fixed Ra1e6/Pr.71, common160², fixed numerics; reduce EOS betaDeltaT1e-3→1e-4 with beta/10 and g×10. Baseline accepted A-Ra1e6-fine at9000 is historical read-only reuse; existing §10 roadmap specifies only one additional case. No fresh pair or baseline warm start.

Existing 0.2% primary threshold and epsilon_v non-worsening remain. D accepted-pair eligibility; cap unaccepted gives H NOT_EVALUATED. Quantified characterization must be reported even if H FAIL. Positions and other diagnostics have no new thresholds. Density-amplitude reduction is an expectation, not an assumed observation.

Generator review found hard-coded BETA and literal template beta. v1.7 specifies unchanged module loaded with in-memory Decimal BETA1e-4, canonical main/make_p, exact beta overlay on NEW case only, raw-manifest preservation and corrected initial input hashes before mesh. No source/template edits. Dependent p follows the existing EOS/hydrostatic initialization relation.

No320; not prerequisite for this fixed-grid experiment. Historical F failures and all existing criteria retained. No continuum-limit, grid-independent, A/B-causal or full Verification claim; no Gate J authorization.

Amendment007 JSON SHA `9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592`; effective v1.7 JSON SHA `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`. Full snapshot contains v1.0+Amendments001–007 with superseded active v1.6 metadata explicitly historical. Immutable scientific/numerical subtrees and schedule checks PASS.

Protected 223989 existing files: changed0. No tracked diff, only six authorized new artifacts. Proof and artifact digests are embedded in preparation JSON, avoiding new evidence-directory scope.

Attempt008 NOT_STARTED; no execution result directory created. Planned one new sensitivity case and GateH_report.md/json, GateH_comparison.csv, GateH_diagnostics.json. Next single task RUN_ROUTE_A_GATE_H; separate user instruction required. Post-run REVIEW_ROUTE_A_GATE_H_RESULT.

```text
ROUTE_A_GATE_H_EXECUTION_CONTRACT_PREPARATION=COMPLETE
PARENT_EFFECTIVE_CONTRACT_VERSION=1.6
PARENT_EFFECTIVE_CONTRACT_HASH_VERIFIED=YES
PARENT_EFFECTIVE_CONTRACT_SHA256=c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59
FULL_STEADY_MATRIX_REVIEW_VERIFIED=YES
OVERALL_VERIFICATION_STATUS=VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION
ALL_ROUTE_A_GATE_F=FAIL
ALL_RA_NEEDS_320=YES
GRID_320_EXECUTED=NO
TARGETED_320_REQUIRED_BEFORE_GATE_H=NO
GATE_H_SCIENTIFICALLY_ALLOWED=YES
GATE_H_CLASSIFICATION=FIXED_GRID_MODEL_FORMULATION_SENSITIVITY
GATE_H_TARGET_RA=1000000
GATE_H_TARGET_PR=0.71
GATE_H_GRID=160x160x1
GATE_H_BASELINE_CASE=A-Ra1e6-fine
GATE_H_BASELINE_ACCEPTED=YES
GATE_H_BASELINE_FINAL_ITERATION=9000
GATE_H_BASELINE_EXECUTION_POLICY=HISTORICAL_ACCEPTED_BASELINE_REUSE
GATE_H_BASELINE_SOLVER_RERUN_REQUIRED=NO
GATE_H_BASELINE_BETA=1e-3
GATE_H_BASELINE_BETA_DELTA_T=1e-3
GATE_H_PERTURBED_BETA=1e-4
GATE_H_PERTURBED_BETA_DELTA_T=1e-4
GATE_H_BETA_RATIO=0.1
GATE_H_G_RATIO=10
GATE_H_RA_HELD_FIXED=YES
GATE_H_PR_HELD_FIXED=YES
GATE_H_DELTA_T_HELD_FIXED=YES
GATE_H_GRID_HELD_FIXED=YES
GATE_H_NUMERICS_HELD_FIXED=YES
GATE_H_GRID_INDEPENDENT_CLAIM_ALLOWED=NO
GATE_H_HARD_THRESHOLD=0.002 relative fraction (0.2%) for Nu_bar_cavity/Umax/Wmax; reconstructed epsilon_v non-worsening
GATE_H_RESULT_TYPE=PASS_FAIL
CONTRACT_AMENDMENT_007_CREATED=YES
AMENDMENT_007_SCOPE=GATE_H_FIXED_GRID_MODEL_SENSITIVITY
EFFECTIVE_CONTRACT_VERSION=1.7
NEXT_ATTEMPT_ID=008
ROUTE_A_SOLVER_EXECUTED=NO
ROUTE_B_SOLVER_EXECUTED=NO
GATE_H_SOLVER_EXECUTED=NO
CASE_GENERATED=NO
MESH_GENERATED=NO
INITIALIZATION_CLONE_EXECUTED=NO
CONTINUATION_EXECUTED=NO
GATE_J_EXECUTED=NO
FORMAL_STEADY_MATRIX_STATUS_CHANGED=NO
FORMAL_CRITERIA_CHANGED=NO
NUMERICAL_SETTINGS_CHANGED=NO
HISTORICAL_RESULTS_CHANGED=NO
GATE_H_TECHNICALLY_READY=YES
NEXT_SINGLE_TASK=RUN_ROUTE_A_GATE_H
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK=gpt-6.1-sol / medium
USER_DECISION_REQUIRED=YES
EFFECTIVE_CONTRACT_SHA256=fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60
```
