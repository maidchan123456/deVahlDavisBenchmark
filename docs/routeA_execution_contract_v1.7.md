# Route A execution contract v1.7 — Gate H

Effective JSON SHA-256: `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`. Parent v1.6 SHA-256: `c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59`. Amendment007 JSON SHA-256: `9bb55b9c266aeb935c3dd49f77a2e023a2e55b33bc2fc9b2e9159b9b9fb9b592`.

Full effective snapshot: v1.0 + Amendments001–007. Current execution guard `v1.7`; all earlier snapshots immutable.

## Scope and authority

Preparation only; no solver/generation/constructor clone. Future `RUN_ROUTE_A_GATE_H` needs a separate user instruction. Gate H is fixed-grid model/formulation sensitivity, not grid convergence/validation/transient/particle work. Existing authority: pre-full-matrix review §10 says matrix baseline A-Ra1e6-fine and one additional sensitivity case; acceptance criteria §10 retains 0.2% and epsilon_v non-worsening.

## Historical evidence and baseline

Full steady review COMPLETE, computed/accepted12, D all PASS, fine E/G all PASS, F all FAIL, needs_320 YES. Verification partial. Review JSON SHA `5faa9b10a240c25848e61e5fdc6dc327b5e1deb60694168e610baff24744a62c`; review seal SHA `7efafd03c32dde5daa675fc54d02bfcc143432fa543aa14d38b968afde5f3114`.

Baseline `A-Ra1e6-fine`, 160x160x1, accepted D PASS at9000, HISTORICAL_ACCEPTED_STEADY_BASELINE; execution policy HISTORICAL_ACCEPTED_BASELINE_REUSE, no baseline rerun/restart/continuation/field/status edits. Final segment SHA `2efd0136ab36176bd22c373f5dd1d7b12619d5b9d8b4c5f9d96d490bfce6154d`; all baseline field/mesh hashes are frozen in JSON.

## Controlled perturbation

Only NEW `A-H-Ra1e6-fine-beta1e-4` in attempt008. Ra=1000000, Pr=.71, beta1e-3→1e-4, DeltaT=1K, betaDeltaT1e-3→1e-4, beta ratio.1, g ratio10. Compute g from canonical formula, not rounded manual value. Planned g magnitude `1408.450704225352112676056338028169014085` m/s²; direction (0,-1,0).

Reference nu0=mu/rho0=1e-5; alpha0=nu0/Pr; k=rho0*Cv*alpha0 unchanged. eConst Cv/Cp handling unchanged: no independent new Cp value. Hold geometry, temperatures, BC types, rho0/mu/Cv/framework, schemes, relaxation, tolerances, Gate D and extraction fixed. Dependent initial p must change consistently with g/EOS; this is canonical initialization, not a warm start or third independent physical change.

## Registered canonical generation and execution procedure

1. Only during separately authorized RUN_ROUTE_A_GATE_H: verify v1.7 external SHA, Amendment007 SHA and every start guard; refuse any existing new-case/result/initialization/attempt008 destination.

2. Use importlib.util.spec_from_file_location/module_from_spec/exec_module to load the hash-guarded unchanged Scripts/routeA/generate_case.py without calling main automatically. Assign module.BETA=module.Decimal("1e-4") in memory only. No source edit; all other constants/functions remain unchanged.

3. Set sys.argv to [generator, --case-id, A-SMOKE, --name, A-H-Ra1e6-fine-beta1e-4, --nx, 160, --ny, 160, --ra, 1000000, --end-time, 3000] and call module.main(). This canonical main computes gravity from perturbed BETA and builds 0/p using canonical make_p with that same BETA. No baseline fields or mesh are copied.

4. Before any mesh or constructor/solver run, preserve the raw generated manifest as generated_manifest_original.json. The canonical template has literal beta 1e-3: require exactly one beta 1e-3; entry in NEW constant/physicalProperties, replace only its value with beta 1e-4;. Reject count!=1. This is the registered Gate H physical overlay on the newly generated case; canonical template is never edited.

5. Finalize NEW case_manifest.json: formal case_id, generator_role=A-SMOKE, attempt008, contract/version/hash, generator SHA, in-memory BETA override and exact overlay record; beta/g/Ra/Pr from actual dictionaries and formula. Recompute input_sha256 for all initial OpenFOAM inputs after overlay, excluding manifests/evidence files; preserve raw generator hashes separately. Freeze final input manifest before mesh. Raw generator physicalProperties hash is intermediate, not final authority.

6. Verify immutable properties, schemes, BC types, geometry and numerical values against the baseline/template; only beta and g are independent physical changes. Dependent initial 0/p is regenerated using p=rho*gh+pRef (internal rho0 at T0; wall EOS rho at Th/Tc), not warm-started. p_rgh remains canonical zero; pRef=hRef=0. Gate A recomputes Ra/Pr from actual inputs with existing 1e-10 relative criterion; mesh geometry must match baseline.

7. Then canonical blockMesh/checkMesh and existing isolated prepare_initialization_check.py + verify_initialization.py workflow, including its one-iteration constructor check, followed by runtime_provenance.py with v1.7. These are future execution operations, all prohibited during preparation.

8. One primary solution path: initial 3000, seal; D PASS -> accepted stop; normal finite D FAIL -> +3000 from same sealed latestTime, cap30000. Only startFrom/endTime continuation edits. STOP on evaluator, provenance, nonfinite, fatal, divergence or evidence corruption; no tuning, retry, cap extension, baseline rerun or extra grid.

9. Use unchanged canonical analyzer on the NEW sensitivity case only; snapshot metrics/raw monitors/logs/fields after every segment before continuation. Extract baseline comparisons from sealed historical metrics (read-only); do not route analyzer/postprocessing output into baseline directories.

## Schedule and comparison eligibility

Initial3000, increments3000, cap30000, one primary path/concurrency1. D unchanged: final200-iteration stationarity Rwin≤5e-4 for Nu_bar_0/Umax/Wmax, Initial residual Ux/Uy/e/p_rgh≤1e-7, exact heat OLS slope≤0 plus health/provenance. Continuation only from sealed same-case latestTime. Cap D FAIL: computed YES, accepted NO, formal H NOT_EVALUATED. No post-cap extension/tuning/retry.

## Metrics and existing classification

D_H=|Qpert−Qbase|/|Qbase|, baseline denominator; signed scalar/relative differences stored. Primary H threshold ONLY Nu_bar_cavity/Umax/Wmax each≤.002 (0.2%). Same reconstructed epsilon_v must decrease or not worsen (≤baseline); no new slack. Accepted complete pair: PASS iff all these conditions, otherwise FAIL. Missing/unaccepted pair: NOT_EVALUATED. Characterization is quantified/reportable regardless of numerical H PASS/FAIL; downstream roadmap still needs H PASS.

Positions use signed/absolute normalized-coordinate differences, no new Hard thresholds. Secondary diagnostics: Nu_bar_0, Nu_bar_half, Nu_bar_1, Umax_Z, Wmax_X, Nu_hot_local_max, Nu_hot_local_max_Z, Nu_hot_local_min, Nu_hot_local_min_Z, physical_heat_imbalance, section_Nu_deviation, native_mass_epsilon_m, reconstructed_velocity_epsilon_v, temperature_symmetry, velocity_symmetry, T range, rho_min, rho_max, max(abs(rho/rho0-1)). Density diagnostics include actual min/max and max|rho/rho0−1|; approximate tenfold reduction at comparable T is expected scaling, not a result fixed in advance.

## Scientific limits

All four historical F FAIL/needs_320 YES remain. Ra1e6 Nu fine-medium1.3402375461%>1%; W non-monotonic p/GCI undefined. No320 now; not required before bounded fixed-grid H. H change cannot provide exact continuum/model-error bound. Common-grid cancellation is possible, model/grid interaction unknown. Two points do not prove the classical Boussinesq limit, A=B, all work terms vanishing, A/B causal decomposition, or full Verification.

## Start guards and output ownership

Verify external v1.7 digest and Amendment007/parent chain, implementation/template/reference/caps and required_existing_artifacts; verify all full review seal members and baseline final fields/mesh/accepted status; F limitations/no320 unchanged. Require new case/results/initialization destinations absent and attempt008 NOT_STARTED; reject unexpected artifacts. Obsolete v1.6 next-Ra destination guards are historical, not guards for new H execution.

Baseline read-only; perturbation GATE_H_FORMAL_SENSITIVITY_CASE; comparison FIXED_GRID_MODEL_FORMULATION_SENSITIVITY. New result root `results/routeA/cases/A-H-Ra1e6-fine-beta1e-4/`; new batch root `results/routeA/attempts/attempt_008/` (not created now). Planned outputs: GateH_report.md, GateH_report.json, GateH_comparison.csv, GateH_diagnostics.json. All segments sealed with contract/input/mesh/field/log/runtime/health/Initial-residual/QoI hashes and ownership before continuation.

## Next task

`RUN_ROUTE_A_GATE_H` / gpt-6.1-sol / medium, separately user-authorized. Afterwards `REVIEW_ROUTE_A_GATE_H_RESULT`. No Gate J contract/authorization and no automatic downstream work. Technical readiness YES means the execution procedure and authority are frozen, not that any run has started or a result has been obtained.
