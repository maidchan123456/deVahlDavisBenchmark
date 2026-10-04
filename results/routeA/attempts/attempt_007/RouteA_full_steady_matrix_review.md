# Route A full steady matrix review

Task: REVIEW_ROUTE_A_FULL_STEADY_MATRIX. Review only; no solver, case/mesh generation, continuation, contract amendment, or historical status change.

## 1. Executive summary

**INFERENCE:** VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION. **OBSERVED:** 12/12 computed, 12/12 accepted, D PASS all 12, fine E and G PASS all four Ra; F FAIL all four groups, needs_320 YES unchanged. Execution completion and acceptance do not mean full Verification.

**Research recommendation:** NO_320_NOW; targeted Ra1e6 refinement has highest deferred information value. TARGETED_320_REQUIRED_BEFORE_GATE_H=NO for a bounded common-160-grid sensitivity question; GATE_H_SCIENTIFICALLY_ALLOWED=YES conditionally, technically ready=NO. Next single task: PREPARE_ROUTE_A_GATE_H_EXECUTION_CONTRACT. USER_DECISION_REQUIRED=YES records the research decision for the next task, without initiating it.

## 2. Evidence provenance

Current authority v1.6 SHA-256 `c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59`; analyzer/runtime-checker and current start guards PASS. HEAD `a40bb187be64c2a65f24e8254a87ae6b71ab6604`. Historical Ra1e3/4/5/6 execution snapshots are v1.3/1.4/1.5/1.6 respectively; current v1.6 does not retroactively relabel them. Ra1e3 coarse is accepted reuse after the evaluator repair, not a new solver run. Ra1e3 position errors use historical group E absolute-coordinate values, cross-checked against separately saved v1.4 position-semantics reanalysis; original v1.3 Wmax_X relative-error payload is not used.

**OBSERVED:** attempt 004–007 original seals, 12 final segment raw/derived seals, native final fields and mesh hashes, runtime provenance, Gate A/OQ-02 and normal exit evidence verified. Full protected-before manifest includes existing contracts/amendments, scripts/templates, reference, results, case fields and existing external Route B protected paths. Before/after comparison is saved separately; original seals remain untouched. Historical rewritten working wallHeatFlux at earlier checkpoints is distinct from sealed raw evidence; only current final accepted fields are checked against final manifests. No historical Gate is recalculated.

Primary authority and exact hashes:

| Source | SHA-256 |
| --- | --- |
| results/routeA/attempts/attempt_004/Ra1e3_trio_report.json | 10bab3a03554b413259ba35837c9a9ce62f3c5fd3d6d4531acef090d4d7858ac |
| results/routeA/attempts/attempt_004/Ra1e3_group_evaluation.json | 55625f9bf8627ee46e0be87f942dc8560a28cd39d29db7999bd3cc8eabf7ede5 |
| results/routeA/attempts/attempt_004/Ra1e3_routeA_vs_routeB.csv | a4f35ee1922bcc5f1120480d1a598213e2b57a0ddfbe62b333bcb057ae34f65b |
| results/routeA/attempts/attempt_004/Ra1e3_trio_matrix.csv | fb625374ce9946028fc650ffb0d424ae24e09cd33d958a8abe036e1bfc1608a4 |
| results/routeA/attempts/attempt_004/attempt_sealed_sha256.json | 838357d91dfaa431af0dadbc70c9899e45734dd37553363b2ade4a4226904e33 |
| results/routeA/attempts/attempt_005/Ra1e4_trio_report.json | 36283fa158aa54ac11c83357c61cbc2ca6e476b2a74dc55282c6ed99d5a99afa |
| results/routeA/attempts/attempt_005/Ra1e4_group_evaluation.json | 30d6469e89e53b0aecbf113118f6fc7b5afa3f072bec1e6603d707f799ab192b |
| results/routeA/attempts/attempt_005/Ra1e4_routeA_vs_routeB.csv | 1ea0bdf06417f34e74fd9b0011f95ee9ddbe8ea1dc292e89c9ce0923f66d17f8 |
| results/routeA/attempts/attempt_005/Ra1e4_trio_matrix.csv | 3c740c1efd59e70e0d174df179a8675f9c019561089b52602fb259fcadb1928d |
| results/routeA/attempts/attempt_005/attempt_sealed_sha256.json | 03ef65ed45c73bef82d6fe840b53796b5ecd34dd465612d868ee82e6ca476c36 |
| results/routeA/attempts/attempt_006/Ra1e5_trio_report.json | bda0b3558b935ed07db1d2fab9d79466c3c48e922807157c7f087197af00d88c |
| results/routeA/attempts/attempt_006/Ra1e5_group_evaluation.json | 6af46450936c86a3efac3976456272a1d3a47d322c096cf5c520dd81fa12824e |
| results/routeA/attempts/attempt_006/Ra1e5_routeA_vs_routeB.csv | f9788b1353f12dd1f0548a9259e51b24ab40b693d648e9576843807ed72b9093 |
| results/routeA/attempts/attempt_006/Ra1e5_trio_matrix.csv | b53b3768e70edb4dfa411947f75c759d0294ea281de95c7cac1fd85d8da4f221 |
| results/routeA/attempts/attempt_006/attempt_sealed_sha256.json | 845976e6f63ec4cf630a6821cf54846753855e2e4201e4781be163a4bca16a21 |
| results/routeA/attempts/attempt_007/Ra1e6_trio_report.json | ab47624ae64723ed8d677544d7a72dfd73f51904ba173384dc8e13b1446cb0ef |
| results/routeA/attempts/attempt_007/Ra1e6_group_evaluation.json | 82f3bf630c4e40bb0148886a93e126a755a5714d027346c8a885d3f0f87a6a64 |
| results/routeA/attempts/attempt_007/Ra1e6_routeA_vs_routeB.csv | 716a47ed60c05202ab83a03a6a99d4832cfcd5ba58f6b6e97af33bb77ac9cc2a |
| results/routeA/attempts/attempt_007/Ra1e6_trio_matrix.csv | 11a818373e9dfa1ca15697059c3a0cb1bd99b26f1df84f1ec30d8731441ff515 |
| results/routeA/attempts/attempt_007/attempt_sealed_sha256.json | e17457fc8bbe7bd0ab26ea7a8e6ee6f0da3faf92dc75ebc78c84f59a73f33373 |
| results/routeA/attempts/attempt_005/Ra1e4_result_review.json | 94a0c25ca9080d31938dd1e4637806e952bc2ccc5768bf3f17397b6d5b641c14 |
| results/routeA/attempts/attempt_004/paper_position_semantics_review.json | b04c4eea132ba364d108b5b8318bfd833597a63be639725d64b886f2f626d1f3 |
| results/routeA/attempts/attempt_004/position_semantics_reanalysis/fine/metrics.json | 2c9f7fa87dde96e6f9ea12302a22a6662e00d2f963d848f0c89be04d997b2779 |
| results/routeB/Ra1e6_post_matrix_gateD_review.json | 1c8e8ea2c3f8dc58b42a4954c80642f8cd00f8cdc549b80c592851e04d86daac |
| docs/routeA_pre_full_matrix_review.md | 0ceac629a9fd98d85b0d882eb523410237be84ae005acfb34033a8c71ade557e |
| docs/acceptance_criteria.md | 2fe82dba1644621a7e57ddc11c4ea5ba5007db50122fbd0c0179f5af5ac38db4 |
| docs/routeB_design.md | d87ab88109c1080e3b32867719f217df7118c43b4d3caa0da30bc814938eabf6 |
| docs/routeA_execution_contract_v1.6.json | c0cdf8d6a08c6190ceff49535c1d44b4050a92373a3faa06cc1e49b9b3b7fe59 |
| results/routeA/attempts/attempt_007/RouteA_full_steady_matrix_summary.json | d554f077bd847cd358f71f04bb53d2e5dc627261c157ca7126d624a57af16aab |

Evidence checks: `full_steady_review_checks/evidence_checks.json`; protection: `full_steady_review_checks/protected_after_check.json`. Final status copy is in JSON. Numerics are formatted here; CSV/JSON preserve full source precision.

## 3. 12-case matrix

**OBSERVED:** Counts and final iterations match the reports and sealed summary sources. E/G attach only to accepted fine cases; F attaches to an accepted trio, not separately to every coarse/medium row.

| Case | N² | Final iteration | Computed | Accepted | D | Nu cavity | Nu hot | Nu half | Nu cold | Umax | Wmax |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-Ra1e3-coarse | 40 | 3000 | True | True | PASS | 1.118855173 | 1.11861213 | 1.11873791 | 1.118612176 | 3.648078448 | 3.689537161 |
| A-Ra1e3-medium | 80 | 6000 | True | True | PASS | 1.118103298 | 1.118001216 | 1.118123125 | 1.118001676 | 3.647297616 | 3.696866257 |
| A-Ra1e3-fine | 160 | 18000 | True | True | PASS | 1.117942492 | 1.117847969 | 1.11802097 | 1.117850356 | 3.650095122 | 3.69868728 |
| A-Ra1e4-coarse | 40 | 3000 | True | True | PASS | 2.259954629 | 2.257421422 | 2.258514697 | 2.257421472 | 16.1213351 | 19.59733346 |
| A-Ra1e4-medium | 80 | 6000 | True | True | PASS | 2.249077279 | 2.247985148 | 2.249053666 | 2.247985276 | 16.17307049 | 19.62683953 |
| A-Ra1e4-fine | 160 | 15000 | True | True | PASS | 2.246385203 | 2.245572701 | 2.246773468 | 2.245575186 | 16.18458293 | 19.62196141 |
| A-Ra1e5-coarse | 40 | 3000 | True | True | PASS | 4.62617047 | 4.616285032 | 4.618667493 | 4.616285034 | 34.82796059 | 68.87369295 |
| A-Ra1e5-medium | 80 | 3000 | True | True | PASS | 4.549200801 | 4.545605757 | 4.547772166 | 4.545606594 | 34.78485459 | 68.57077664 |
| A-Ra1e5-fine | 160 | 12000 | True | True | PASS | 4.529825749 | 4.527649791 | 4.529826259 | 4.527650671 | 34.75498427 | 68.6552097 |
| A-Ra1e6-coarse | 40 | 3000 | True | True | PASS | 9.438988398 | 9.402284677 | 9.406410667 | 9.402284628 | 65.62783804 | 222.7092048 |
| A-Ra1e6-medium | 80 | 3000 | True | True | PASS | 8.987854982 | 8.976492304 | 8.981001234 | 8.976492302 | 65.11855314 | 218.3334115 |
| A-Ra1e6-fine | 160 | 9000 | True | True | PASS | 8.868989456 | 8.863383392 | 8.867669176 | 8.863383756 | 64.9147346 | 219.9002617 |


## 4. Gate D synthesis

**OBSERVED:** All final cases PASS, including normal finite execution/provenance, QoI stationarity, Initial residuals and non-increasing heat imbalance over the frozen final window. Rwin threshold remains 5e-4; final Initial residual threshold 1e-7. Final maxima used in paper/grid comparisons are not interchangeable with monitor sampling.

| Case | D | Final Rwin | Final Initial residuals | Heat OLS slope / iteration |
| --- | --- | --- | --- | --- |
| A-Ra1e3-coarse | PASS (accepted reuse) | {'Nu_bar_0': 0.0, 'Umax': 3.7963777915442344e-10, 'Wmax': 3.8057085179798307e-10} | {'Ux': 5.794631978111069e-13, 'Uy': 1.741000695055185e-12, 'e': 5.728142082739951e-11, 'p_rgh': 1.177069303012431e-10} | 0 |
| A-Ra1e3-medium | PASS | {'Nu_bar_0': 2.0752675581805465e-06, 'Umax': 3.5062460778834005e-06, 'Wmax': 3.6902150700975385e-06} | {'Ux': 7.344288988870381e-09, 'Uy': 6.789191564025066e-09, 'e': 4.440921937867483e-09, 'p_rgh': 1.129147743632867e-08} | -4.637801323e-10 |
| A-Ra1e3-fine | PASS | {'Nu_bar_0': 4.67935139160673e-06, 'Umax': 2.561537227987182e-05, 'Wmax': 2.4054442370890662e-05} | {'Ux': 6.022214974574855e-08, 'Uy': 6.302767005504157e-08, 'e': 9.075025527702204e-09, 'p_rgh': 4.180571114994891e-08} | -4.919849563e-10 |
| A-Ra1e4-coarse | PASS | {'Nu_bar_0': 0.0, 'Umax': 2.7851601453678632e-11, 'Wmax': 1.9417961051279377e-11} | {'Ux': 4.732429668539095e-12, 'Uy': 4.29159538576274e-12, 'e': 9.655208094965825e-11, 'p_rgh': 1.171047483620124e-10} | 0 |
| A-Ra1e4-medium | PASS | {'Nu_bar_0': 2.120172402643553e-08, 'Umax': 2.5612206804561346e-08, 'Wmax': 2.1222069936285234e-08} | {'Ux': 6.004509222380837e-11, 'Uy': 5.804071427854237e-11, 'e': 9.992890253575361e-11, 'p_rgh': 1.160386741081262e-10} | -3.967582846e-11 |
| A-Ra1e4-fine | PASS | {'Nu_bar_0': 7.548360750640182e-06, 'Umax': 1.8797939899177281e-06, 'Wmax': 5.930528981148159e-07} | {'Ux': 6.584500199275401e-09, 'Uy': 7.791588524034357e-09, 'e': 1.433956737784489e-08, 'p_rgh': 2.403298087462e-08} | -3.544481783e-10 |
| A-Ra1e5-coarse | PASS | {'Nu_bar_0': 0.0, 'Umax': 2.28637626992438e-10, 'Wmax': 9.162337213683937e-11} | {'Ux': 3.295793953809839e-11, 'Uy': 6.687858119034998e-11, 'e': 8.707955390251524e-11, 'p_rgh': 9.989087721845041e-11} | 0 |
| A-Ra1e5-medium | PASS | {'Nu_bar_0': 1.1055850333900684e-05, 'Umax': 6.653352260240967e-05, 'Wmax': 1.7178324694405755e-05} | {'Ux': 5.826402622429625e-08, 'Uy': 6.507514050264846e-08, 'e': 5.151133315596054e-08, 'p_rgh': 5.356351270587836e-08} | -4.94271872e-10 |
| A-Ra1e5-fine | PASS | {'Nu_bar_0': 2.179447241630733e-06, 'Umax': 1.0446733977539926e-05, 'Wmax': 3.40539247084051e-06} | {'Ux': 1.159111332677023e-08, 'Uy': 1.319574113778433e-08, 'e': 1.088493158414897e-08, 'p_rgh': 1.089845962092787e-08} | -1.325096374e-10 |
| A-Ra1e6-coarse | PASS | {'Nu_bar_0': 1.2905519076742738e-09, 'Umax': 5.384434158737456e-09, 'Wmax': 2.7222496244627674e-09} | {'Ux': 1.972585551268684e-10, 'Uy': 1.797303883550135e-10, 'e': 2.468311227793433e-10, 'p_rgh': 4.602992902868331e-09} | -7.102047017e-13 |
| A-Ra1e6-medium | PASS | {'Nu_bar_0': 8.104134967967558e-07, 'Umax': 5.533256315076269e-06, 'Wmax': 8.361054944963635e-07} | {'Ux': 8.519055821960452e-09, 'Uy': 8.665610800875329e-09, 'e': 8.6259150409898e-09, 'p_rgh': 8.117761138870714e-09} | -1.763995624e-11 |
| A-Ra1e6-fine | PASS | {'Nu_bar_0': 1.1481782858137638e-06, 'Umax': 2.8469248404361728e-05, 'Wmax': 3.814859633796983e-06} | {'Ux': 3.729257822450917e-08, 'Uy': 3.727611817203866e-08, 'e': 1.950819622643953e-08, 'p_rgh': 1.57430685322117e-08} | -2.906704593e-12 |

Recorded continuations demonstrate intermediate FAILs resolved under frozen caps/settings; they remain historical FAIL checkpoints. Ra1e3 coarse accepted-reuse owner supersedes its original execution-issue classification for reuse only. **INFERENCE:** final iteration counts alone do not show that higher Ra is inherently easier to converge. All fine cases passed only after continuation; pressure/energy/velocity convergence and stationarity remain distinct checks.

## 5. Gate E synthesis

**OBSERVED:** Four fine practical comparisons PASS. Frozen scalar errors for Nu_cavity/Umax/Wmax are ≤1%, position absolute-coordinate errors ≤0.01. **INFERENCE:** this supports agreement of selected benchmark QoIs within practical tolerances. It establishes neither exact reproduction, a pure numerical-error bound, nor full physical validation. Route B Hard benchmark verification is a separate authority.

| Ra | D scope | Fine E | Trio F | Fine G | Group needs_320 |
| --- | --- | --- | --- | --- | --- |
| 1000 | PASS_ALL_3 | PASS | FAIL | PASS | YES |
| 10000 | PASS_ALL_3 | PASS | FAIL | PASS | YES |
| 100000 | PASS_ALL_3 | PASS | FAIL | PASS | YES |
| 1000000 | PASS_ALL_3 | PASS | FAIL | PASS | YES |


## 6. Gate F detailed review

**OBSERVED:** Rows below copy historical F quantities and component checks. Relative differences/GCI are shown in percent; p/GCI null for non-monotonic quantities. No status is recomputed.

| Ra | QoI | 40² | 80² | 160² | Type | Fine–medium % | p_obs | GCI fine % | Status | Recorded checks | QoI needs_320 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | Nu_bar_cavity | 1.118855173 | 1.118103298 | 1.117942492 | MONOTONIC_CONVERGENCE | 0.01438412583 | 2.225169804 | 0.01174003741 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 1000 | Umax | 3.648078448 | 3.647297616 | 3.650095122 | NON_MONOTONIC_OR_UNDEFINED | 0.07664198983 | null | null | FAIL | null | True |
| 1000 | Wmax | 3.689537161 | 3.696866257 | 3.69868728 | MONOTONIC_CONVERGENCE | 0.04923430943 | 2.008885929 | 0.0488320464 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 10000 | Nu_bar_cavity | 2.259954629 | 2.249077279 | 2.246385203 | MONOTONIC_CONVERGENCE | 0.1198403581 | 2.014536125 | 0.1182438137 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 10000 | Umax | 16.1213351 | 16.17307049 | 16.18458293 | MONOTONIC_CONVERGENCE | 0.07113213773 | 2.167958109 | 0.06107739175 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 10000 | Wmax | 19.59733346 | 19.62683953 | 19.62196141 | NON_MONOTONIC_OR_UNDEFINED | 0.02486051188 | null | null | FAIL | null | True |
| 100000 | Nu_bar_cavity | 4.62617047 | 4.549200801 | 4.529825749 | MONOTONIC_CONVERGENCE | 0.4277217938 | 1.990089863 | 0.4316617981 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 100000 | Umax | 34.82796059 | 34.78485459 | 34.75498427 | MONOTONIC_CONVERGENCE | 0.08594544 | 0.5291756216 | 0.5818862337 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 100000 | Wmax | 68.87369295 | 68.57077664 | 68.6552097 | NON_MONOTONIC_OR_UNDEFINED | 0.1229812953 | null | null | FAIL | null | True |
| 1000000 | Nu_bar_cavity | 9.438988398 | 8.987854982 | 8.868989456 | MONOTONIC_CONVERGENCE | 1.340237546 | 1.924223786 | 1.438369884 | FAIL | {'fine_medium_le_1pct': False, 'GCI_within_existing_limit': True} | False |
| 1000000 | Umax | 65.62783804 | 65.11855314 | 64.9147346 | MONOTONIC_CONVERGENCE | 0.3139788639 | 1.321187614 | 0.6284952282 | PASS | {'fine_medium_le_1pct': True, 'GCI_within_existing_limit': True} | False |
| 1000000 | Wmax | 222.7092048 | 218.3334115 | 219.9002617 | NON_MONOTONIC_OR_UNDEFINED | 0.7125276324 | null | null | FAIL | null | True |

Ra1e3: U reversal, 0.07664199% fine–medium, p/GCI undefined. Ra1e4: W reversal, 0.02486051%. Ra1e5: W reversal, 0.12298130%; Nu/U PASS, but U order 0.52918 is low and warrants caution about assuming second-order asymptotic behavior. Ra1e6: **two distinct failures**: monotonic Nu has 1.3402375461% difference >1%; GCI 1.4383698843% satisfies its 1.5% criterion, but that does not override the independent difference failure. W reversal has 0.71252763% difference and undefined p/GCI; U PASS. The historical per-QoI Nu needs_320=false is preserved even though Nu FAIL; the group needs_320=YES is independently retained.

**INFERENCE:** Three-grid formal convergence is not established for all monitored quantities in any group. A tiny reversal and Ra1e6 1.34% Nu change have different magnitudes and information value. FAIL alone does not prove unusable fine solutions, wrong numerics, large mesh error for every QoI, or an invalid physical model. Conversely a small observed difference with undefined GCI does not provide a rigorous error bound. Extrema/interpolation or cancellation contributions are **HYPOTHESES**, not established causes.

## 7. Gate G synthesis

**OBSERVED:** All fine components PASS. Values below are dimensionless fractions/indicators, not percentages. Limits: heat .002; section .005; native mass 1e-6; reconstructed volume .002; both symmetry .002.

| Ra | physical_heat_imbalance | section_Nu_deviation | native_mass_epsilon_m | reconstructed_velocity_epsilon_v | temperature_symmetry | velocity_symmetry |
| --- | --- | --- | --- | --- | --- | --- |
| 1000 | 2.136130817e-06 | 0.0001547391941 | 4.946257734e-13 | 0.0005648447889 | 1.828459729e-05 | 0.0003879064693 |
| 10000 | 1.106898303e-06 | 0.0005386738988 | 2.594755005e-12 | 0.0005292183447 | 8.189118663e-05 | 0.0003489933218 |
| 100000 | 1.943294773e-07 | 0.0004913179337 | 1.692703674e-11 | 0.0006380717163 | 0.0001000284313 | 0.0003873910478 |
| 1000000 | 4.105991168e-08 | 0.0005392664064 | 9.201282491e-11 | 0.0009496930618 | 0.0001103703542 | 0.0004010982484 |

Heat imbalance decreases across these four fine results. Section deviation is not monotonic with Ra. Native mass epsilon increases across Ra; reconstructed epsilon decreases slightly from Ra1e3 to Ra1e4 then increases, highest at Ra1e6. Temperature symmetry defect increases; velocity defect is similar across cases with a small minimum at Ra1e4. All remain below their limits. **INFERENCE:** conservation/symmetry are supported within these steady operators and thresholds. Native mass phi [kg/s] and reconstructed Gauss-linear div(U) are distinct; neither is a proof of complete transient mass/energy conservation or an error bound for all QoIs.

## 8. Paper benchmark trend

**OBSERVED:** Fine scalar absolute relative errors shown as percent; positions are absolute [0,1] coordinate errors (not percentages).

| Ra | Nu error % | U error % | W error % | |ΔZ_U| | |ΔX_W| |
| --- | --- | --- | --- | --- | --- |
| 1000 | 0.00514385828 | 0.03001156306 | 0.04563916833 | 0.0024296875 | 0.00022265625 |
| 10000 | 0.150922991 | 0.0406906536 | 0.02529137497 | 0.000978515625 | 0.002826171875 |
| 100000 | 0.2395607315 | 0.07193857593 | 0.09507173533 | 0.001728515625 | 0.000326171875 |
| 1000000 | 0.7839710885 | 0.4405610342 | 0.2462899625 | 0.00302734375 | 0.00262734375 |

Nu and U errors increase across these Ra. W error first decreases at Ra1e4 then rises, largest at Ra1e6; position errors show no monotonic Ra trend. Largest fine errors are still below preregistered practical criteria. **HYPOTHESIS:** finite-grid/discretization, equation formulation, extraction/operator and implementation differences can all contribute. **UNKNOWN:** their separate contributions; paper error increase cannot be identified as mesh error from these data alone.

## 9. Route A–B trend

**OBSERVED:** Fine A–B gaps copied from historical CSV. Scalars are |A−B|/|B| in percent; positions are absolute coordinate differences. Full precision, signed gaps, A/B values and operator/ownership metadata are in `RouteA_AB_Ra_trend.csv` and JSON. Ra1e3–Ra1e5 compare accepted baselines; Ra1e6 has strictly weaker **DIAGNOSTIC_ONLY_UNACCEPTED_B_BASELINE** ownership (B computed YES, accepted NO, D FAIL).

| Ra | Evidence | Nu_bar_cavity % | Nu_bar_0 % | Umax % | Wmax % | Umax_Z |Δposition| | Wmax_X |Δposition| | Nu_hot_local_max % | Nu_hot_local_min % | Nu_hot_local_max_Z |Δposition| | Nu_hot_local_min_Z |Δposition| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | accepted A/B | 0.007011511942 | 0.0009333070552 | 0.02782890672 | 0.03384365659 | 0 | 0 | 0.005459455213 | 0.008132156868 | 2.289053047e-05 | 0 |
| 10000 | accepted A/B | 0.02961018604 | 0.001708220854 | 0.02199895984 | 0.01340843904 | 0 | 0 | 0.001944690006 | 0.008841883827 | 6.517103606e-06 | 0 |
| 100000 | accepted A/B | 0.03893463836 | 2.966209667e-05 | 0.02504998897 | 0.0120608603 | 0 | 0 | 0.0003891755668 | 0.009178107081 | 4.974289176e-06 | 0 |
| 1000000 | unaccepted B diagnostic | 0.043634244 | 0.0001587888877 | 0.0234547965 | 0.01218458283 | 0 | 0 | 0.0002242392306 | 0.002036144566 | 1.417709861e-06 | 0 |

Nu cavity gap increases across Ra (0.0070115%, 0.0296102%, 0.0389346%, diagnostic 0.0436342%). U/W gaps remain small without a monotonic Ra trend. U/W positions agree exactly at the frozen extraction resolution; this does not show equality of continuous extremum positions. Hot Nu mean gaps are tiny and non-monotonic; local maximum scalar and location gaps decrease, local minimum scalar gaps do not follow a monotonic pattern. These observations do not isolate a model-only difference.

**Scope:** no hard A–B threshold is defined. Nu_half, section consistency and native mass-versus-volume continuity are NOT_LIKE_FOR_LIKE; comparison coverage COMPLETE does not mean numerical equivalence. Original Ra1e4 coverage PARTIAL (two absent B coarse symmetry metrics) remains untouched; separately owned accepted-field diagnostic derivation supports reviewed coverage COMPLETE, as recorded in Ra1e4_result_review.json. This does not affect the already populated fine trend.

## 10. Ra1e6 A/B convergence contrast

**OBSERVED:** Route A D PASS 3/3, accepted 3/3 at 3000/3000/9000. Route B D PASS 0/3, accepted 0/3, computed 3/3 at 30000 each. Fine gaps: Nu cavity **0.04363424400041102%**, Umax **0.023454796496258343%**, Wmax **0.012184582832095954%**. B fails the residual criterion on all three grids and heat-trend criterion on coarse/medium; fine heat trend PASS does not override residual FAIL; detailed final windows are retained from the B post-matrix review in JSON. Close final principal values do not satisfy or nullify B acceptance criteria.

**INFERENCE (allowed wording):** “A and B produce very similar principal QoIs, while their frozen iterative-convergence classifications differ.” **UNKNOWN:** causal mechanism, error bounds and harmlessness of B residual floor.

Candidate classification: SUPPORTED means an observed implementation/history difference, **not supported causation**. PLAUSIBLE means a proposed mechanism without direct measurement. UNTESTED means no discriminating evidence in this matrix.

| Candidate | Difference/mechanism evidence | Interpretive label | Assessment |
| --- | --- | --- | --- |
| Equation formulation | SUPPORTED | HYPOTHESIS | A and B implement different equations (frozen A model; docs/routeB_design.md). That difference exists; a causal contribution to Gate D contrast is untested. |
| Pressure variable/scaling | SUPPORTED | HYPOTHESIS | A uses physical pressure, B kinematic pressure; different scaling can affect matrix/residual behavior, but no controlled matched-formulation test identifies causality. |
| Density treatment | SUPPORTED | HYPOTHESIS | A thermodynamic Boussinesq rho and mass flux versus B constant-density continuity with buoyancy rhok; neither physical superiority nor convergence causation follows. |
| Energy formulation | SUPPORTED | HYPOTHESIS | A sensible internal energy e versus B temperature T equation; residual fields and work terms differ. Causal effect untested. |
| Linear system conditioning | PLAUSIBLE | HYPOTHESIS | No condition numbers or matched linear systems measured; scaling/formulation may contribute. |
| Solver implementation | SUPPORTED | HYPOTHESIS | Foundation13 fluid vs Foundation6 buoyantBoussinesqSimpleFoam are distinct implementations. Accuracy or causal convergence advantage is not established. |
| Pressure-velocity coupling details | UNTESTED | UNKNOWN | Both employ steady SIMPLE paths; effects of detailed correction sequence are not isolated by this matrix. |
| Residual normalization/scaling | PLAUSIBLE | HYPOTHESIS | e/T and physical/kinematic pressure are different solved quantities; same threshold does not prove identical residual meaning. Matched normalization study absent. |
| Numerical operators | SUPPORTED | HYPOTHESIS | Section and native continuity operators explicitly differ; they are NOT_LIKE_FOR_LIKE. Their causal contribution to iterative classifications remains untested. |
| Convergence history | SUPPORTED | OBSERVED | A passes at 3000/3000/9000; B remains unaccepted at 30000 each, with recorded residual/heat-trend failures. Different histories are observed, not an explanation of their origin. |

**INFERENCE / research decision:** choose option B: record as important and defer causal investigation until after H or a dedicated thesis question. Option A (mandatory pre-H causal study) adds substantial controlled comparisons without being necessary to evaluate within-A fixed-grid sensitivity. Option C (no investigation relevance) understates the thesis observation. Particle-coupling relevance is indirect: Gate J transient mass/energy evidence matters more directly; close steady A/B QoIs cannot certify it. H itself changes two linked inputs within A and cannot identify the A/B contrast mechanism.

## 11. 320² information-value assessment

**INFERENCE:** Priority is conditional on the immediate fixed-grid H/model-development objective, not a relaxation of formal needs_320 or proof of harmless error.

| Ra | Information value | Basis | Required before fixed-grid H |
| --- | --- | --- | --- |
| 1000 | LOW_INFORMATION_VALUE | Umax non-monotonic with fine-medium 0.07664199%; Nu/W GCI only 0.01174004%/0.04883205%; fine paper/G checks PASS. Additional grid can investigate a small extremum reversal, but low immediate value for the Ra1e6 fixed-grid H question. | NO |
| 10000 | LOW_INFORMATION_VALUE | Wmax non-monotonic but fine-medium only 0.02486051%; Nu/U GCI 0.11824381%/0.06107739%; fine paper/G PASS. Small reversal is formally unresolved; low immediate relevance to H. | NO |
| 100000 | MEDIUM_INFORMATION_VALUE | Wmax reversal fine-medium 0.12298130%; Nu difference 0.42772179%, GCI 0.43166180%; U observed order 0.52918 and GCI 0.58188623% despite PASS. Additional grid would test whether low order/extremum behavior persists; useful cross-Ra context but not an H prerequisite. | NO |
| 1000000 | HIGH_INFORMATION_VALUE | Nu difference 1.34023755% exceeds 1%, GCI 1.43836988% below 1.5% but close; Wmax reversal 0.71252763%; paper Nu error 0.78397109%. Most direct uncertainty for the Ra1e6 baseline used in H; can clarify refinement trend, not guarantee formal resolution. | NO |

All fine paper/G diagnostics PASS contributes practical support, not a grid-error guarantee. Any all-Ra grid-convergence thesis claim raises the relevance of every deferred group.

| strategy | scientific benefit | thesis benefit | computation cost | implementation cost | Gate F resolution | new nonmonotonicity risk | effect on H | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NO_320_NOW | Preserves useful fixed-grid H question while documenting unresolved F. | Enables bounded model-sensitivity discussion; no grid independence claim. | Zero new refinement runs. | Review documentation now; separate H snapshot later. | None; all historical FAIL unchanged. | No new sampling now; existing ambiguity remains. | H preparation can proceed; interaction uncertainty explicitly retained. | Recommended immediate strategy. |
| RA1E6_ONLY | Tests highest-impact Nu trend and W reversal on H baseline. | Strongest targeted reduction of Ra1e6 refinement ambiguity. | One 102400-cell case; walltime unknown. | Separate study snapshot, case/postprocess/seal work and preregistered 4-grid or 80/160/320 interpretation. | May clarify new triplet; no guaranteed PASS and historical 40/80/160 FAIL remains. | Additional reversal or non-asymptotic trend possible. | Delays H if first; useful follow-up if H interpretation requires grid assurance. | Highest-priority deferred refinement option. |
| SELECTED_RA | Ra1e5+Ra1e6 would contrast lower U order/W reversal and high-Ra Nu trend. | Cross-Ra mechanism context, partial grid assurance only. | Two 102400-cell runs for suggested pair; runtime unknown. | Multiple cases and preregistered comparison/interpretation. | Only selected groups may resolve; none guaranteed. | Both may reveal new reversals. | Greater delay; optional after H motivates specific cross-Ra question. | Conditional later option. |
| ALL_RA | Broadest refinement evidence across all 4 Ra. | Most relevant if all-Ra formal grid verification becomes thesis objective. | Four 102400-cell runs; runtime not simply 4x or predicted from iteration counts. | Largest execution, analysis, storage and evidence burden. | Can investigate every failure; does not guarantee monotonicity, defined GCI or small 160-grid error. | Any/all groups can remain unresolved. | Largest pre-H delay, little necessary benefit for strictly fixed-grid H question. | Not justified now by needs_320 alone. |

320² contains 102400 cells versus 25600 at 160² (4× cell count). Storage/per-iteration work may increase, but runtime, conditioning and required iterations are UNKNOWN; neither 4× walltime nor a specific completion budget follows. New study would need frozen refinement/sampling/acceptance interpretation; evaluating 80/160/320 or four-grid evidence cannot retroactively make original 40/80/160 FAIL disappear.

**Central decision:** TARGETED_320_REQUIRED_BEFORE_GATE_H=NO, RECOMMENDED_320_STRATEGY=NO_320_NOW. Ra1e6-only is the highest-priority deferred refinement, especially if H conclusions require continuum accuracy. 320 does not guarantee monotonic convergence, defined GCI, or a small 160² error; another reversal may add ambiguity. This decision is based on the bounded common-grid question, not on declaring F irrelevant.

## 12. Gate H readiness

Purpose confirmed in `docs/routeA_pre_full_matrix_review.md` §10 and `docs/acceptance_criteria.md` §10: Ra1e6 accepted fine baseline betaDeltaT=1e-3 versus 1e-4, **beta/10, g×10**, fixed Ra/Pr and other conditions. Frozen criteria: Nu_cavity/Umax/Wmax relative change each ≤0.2%; reconstructed epsilon_v decreases or does not worsen.

**INFERENCE:** GATE_H_SCIENTIFICALLY_ALLOWED=YES for fixed-grid sensitivity. Accepted Ra1e6 baseline D and G PASS and practical E agreement support using the baseline for this bounded question. Nu fine-medium 1.34% exceeds the H comparison threshold 0.2%, and W reversal 0.71% is unresolved: therefore a small H change cannot be called a grid-independent effect or an exact formulation-error bound. **HYPOTHESIS:** shared discretization errors may partially cancel in the common-grid difference. **UNKNOWN:** cancellation and discretization/model interaction. H can measure the actual fixed-grid response without resolving F; if its interpretation needs a continuum response or a null-effect assertion, targeted refinement becomes required evidence for that claim.

GATE_H_TECHNICALLY_READY=NO; v1.6 is a steady matrix execution contract and no H snapshot exists. GATE_H_CONTRACT_UPDATE_REQUIRED=YES for the future task; this review creates no amendment. Conditions:

- Preregister Gate H in a separate execution snapshot; current v1.6 does not authorize H.
- Use accepted A-Ra1e6-fine baseline, identical 160-grid, schemes, solver settings, DeltaT and other properties; only beta/10 and g*10, with Ra/Pr rechecked.
- Both H cases must independently satisfy frozen iterative/provenance checks; preserve mass/heat/section/epsilon_v diagnostics and original 0.2%/non-worsening rules.
- Describe the outcome as fixed-grid two-point sensitivity; do not infer a continuum limit, A=B, or disappearance of all energy differences.
- If a small H difference is central to a grid-independent thesis claim, or discretization/model interaction affects the interpretation, preregister targeted Ra1e6 refinement before making that claim.
- No automatic escalation to extra beta points, gauge/energy studies, 320 runs or solver tuning.

No formal `ROUTE_A_CHARACTERIZED` status is granted; F and other upper-level prerequisites remain unresolved. Preserve Gate H then Gate J roadmap. Gate J is unexecuted and needs separate transient algorithm/time-step, total mass/EOS consistency and energy-storage/work diagnostics; steady heat closure or small div(phi) is insufficient. H PASS is a downstream requirement, but H alone cannot complete readiness.

## 13. Verification status for thesis

| Layer | Assessment | Scope |
| --- | --- | --- |
| Execution/provenance | PASS / strong complete for this steady matrix | Frozen input/runtime, normal finite run, sealing and final fields. |
| Iterative convergence | PASS | All 12 final cases; preserved D rules. |
| Benchmark agreement | SUPPORTED | All 4 fine practical E diagnostics; selected QoIs only. |
| Conservation/symmetry | PASS / SUPPORTED | All 4 fine G checks with specified steady operators. |
| Grid convergence | PARTIAL / UNRESOLVED | Some components PASS; group F FAIL all 4; no universal error bound. |
| Overall | VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION | No full Verification, characterization, transient or coupling-ready award. |

**INFERENCE:** STEADY_BASELINE_USABLE_FOR_MODEL_SENSITIVITY=CONDITIONAL under §12. Future particle-work baseline=CONDITIONAL for the next fluid-only model development steps. Do not grant transient/coupled readiness; separately frozen Gate H and then Gate J mass-energy/time-step evidence and formal prerequisites are required before particle coupling. Formal upper-level A/B prerequisites have not been waived by the nonblocking workflow or this research recommendation.

## 14. Allowed claims

These are evidence-bounded English statements usable in a thesis (first five OBSERVED/interpretive synthesis; last is conditional INFERENCE):

> All 12 Route A steady cases were computed and accepted under their frozen execution contracts and satisfied the preregistered steady iterative convergence criterion.

> The 160 × 160 solutions at Ra = 10^3, 10^4, 10^5 and 10^6 satisfied the practical paper benchmark criterion for cavity-averaged Nusselt number, the two centreline velocity maxima, and their positions.

> The preregistered steady conservation and symmetry checks passed for all four fine-grid solutions.

> Formal three-grid convergence was not established for all monitored quantities at any of the four Rayleigh numbers.

> At Ra = 10^6, A and B produce very similar principal quantities of interest on the same fine grid, while their frozen iterative-convergence classifications differ; the B comparison is diagnostic because B is unaccepted.

> The accepted Ra = 10^6 fine-grid solution can support a separately preregistered fixed-grid model-sensitivity study, with unresolved grid-convergence limitations explicitly retained.

## 15. Prohibited/unsupported claims

The present evidence does not authorize:

- fully verified / complete Verification / all gates passed
- grid independent / grid-independent model sensitivity
- exactly validated / exact paper reproduction / pure discretization-error bound from paper differences
- all numerical error is negligible / Gate F failure is harmless
- Route A is physically superior / Route B is incorrect / OpenFOAM13 is more accurate
- variable-density formulation causes better convergence / B residual floor is harmless
- 320 guarantees Gate F PASS or bounds the 160-grid error
- Gate H PASS proves A=B or all energy differences vanish
- steady Gate G proves transient mass-energy conservation or particle-coupling readiness
- ROUTE_A_CHARACTERIZED / DOWNSTREAM_TRANSIENT_READY awarded by this review

## 16. Remaining uncertainties

**UNKNOWN:** continuum numerical errors for non-monotonic extrema; validity of asymptotic regime (including Ra1e5 U low observed order); individual paper-difference contributions; A/B convergence causal origin; grid/model interaction in H; full energy/work and transient mass conservation; 320 runtime or eventual formal PASS. **HYPOTHESIS:** discretization, interpolation/extremum resolution and equation differences could contribute, but no candidate has been isolated. Local Nu diagnostics do not supply a whole-field validation or a particle-force accuracy guarantee.

No inference of higher-Ra convergence ease from iteration counts, no promotion of unaccepted B, and no new thresholds or post-hoc Gate definitions. The original attempt seals remain the execution authority; this review has its own artifact seal.

## 17. Recommended next step

**One next task:** `PREPARE_ROUTE_A_GATE_H_EXECUTION_CONTRACT` using `gpt-6.1-sol / medium`. Prepare a reviewable snapshot for the fixed-grid two-point study and its evidence ownership; solver execution is a separate authorization. This review does not prepare or execute that snapshot. USER_DECISION_REQUIRED=YES: user chooses the proposed research progression; no further decision is needed to complete this authorized read-only review.

Deferred priority: targeted Ra1e6 refinement when continuum/grid assurance is needed; Ra1e5 secondary, Ra1e3/4 low immediate information value. Maintain all historical F FAIL/needs_320 YES.

Required statuses:

```text
ROUTE_A_FULL_STEADY_MATRIX_REVIEW=COMPLETE
EFFECTIVE_CONTRACT_VERSION=1.6
EFFECTIVE_CONTRACT_HASH_VERIFIED=YES
ROUTE_A_MATRIX_CASE_COUNT=12
ROUTE_A_MATRIX_COMPUTED_COUNT=12
ROUTE_A_MATRIX_ACCEPTED_COUNT=12
ROUTE_A_STEADY_MATRIX_COMPUTATION_COMPLETE=YES
ALL_ROUTE_A_CASES_ACCEPTED=YES
ALL_ROUTE_A_GATE_D=PASS
ALL_ROUTE_A_GATE_E_DIAGNOSTIC=PASS
ALL_ROUTE_A_GATE_G=PASS
ALL_ROUTE_A_GATE_F=FAIL
RA1E3_GATE_F=FAIL
RA1E3_GATE_F_PRIMARY_REASON=Umax NON_MONOTONIC_OR_UNDEFINED; p_obs/GCI=null
RA1E4_GATE_F=FAIL
RA1E4_GATE_F_PRIMARY_REASON=Wmax NON_MONOTONIC_OR_UNDEFINED; p_obs/GCI=null
RA1E5_GATE_F=FAIL
RA1E5_GATE_F_PRIMARY_REASON=Wmax NON_MONOTONIC_OR_UNDEFINED; p_obs/GCI=null
RA1E6_GATE_F=FAIL
RA1E6_GATE_F_PRIMARY_REASON=Nu_bar_cavity fine-medium 1.3402375460880519% > 1%; Wmax NON_MONOTONIC_OR_UNDEFINED, p_obs/GCI=null
ALL_RA_NEEDS_320=YES
OVERALL_VERIFICATION_STATUS=VERIFICATION_PARTIAL_WITH_DOCUMENTED_GRID_CONVERGENCE_LIMITATION
GRID_CONVERGENCE_FORMALLY_ESTABLISHED_FOR_ALL_MONITORED_QOIS=NO
FINE_GRID_PRACTICAL_BENCHMARK_AGREEMENT_SUPPORTED=YES
CONSERVATION_AND_SYMMETRY_SUPPORTED=YES
RA1E6_A_B_CONVERGENCE_CLASSIFICATION_DIFFERS=YES
RA1E6_A_ACCEPTED=YES
RA1E6_B_ACCEPTED=NO
RA1E6_A_B_PRIMARY_QOIS_CLOSE=YES
RA1E6_A_B_CAUSAL_MECHANISM_ESTABLISHED=NO
TARGETED_320_INFORMATION_VALUE_RA1E3=LOW
TARGETED_320_INFORMATION_VALUE_RA1E4=LOW
TARGETED_320_INFORMATION_VALUE_RA1E5=MEDIUM
TARGETED_320_INFORMATION_VALUE_RA1E6=HIGH
RECOMMENDED_320_STRATEGY=NO_320_NOW
TARGETED_320_REQUIRED_BEFORE_GATE_H=NO
STEADY_BASELINE_USABLE_FOR_MODEL_SENSITIVITY=CONDITIONAL
GATE_H_SCIENTIFICALLY_ALLOWED=YES
GATE_H_TECHNICALLY_READY=NO
GATE_H_CONTRACT_UPDATE_REQUIRED=YES
GATE_J_EXECUTED=NO
GRID_320_EXECUTED=NO
SOLVER_EXECUTED=NO
FORMAL_CRITERIA_CHANGED=NO
HISTORICAL_STATUS_CHANGED=NO
CONTRACT_AMENDMENT_CREATED=NO
FULL_VERIFICATION_CLAIM_ALLOWED=NO
NEXT_SINGLE_TASK=PREPARE_ROUTE_A_GATE_H_EXECUTION_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK=gpt-6.1-sol / medium
USER_DECISION_REQUIRED=YES
ROUTE_A_SOLVER_EXECUTED=NO
ROUTE_B_SOLVER_EXECUTED=NO
CASE_GENERATED=NO
MESH_GENERATED=NO
CONTINUATION_EXECUTED=NO
GATE_H_EXECUTED=NO
EFFECTIVE_CONTRACT_CHANGED=NO
STEADY_BASELINE_USABLE_FOR_FUTURE_PARTICLE_WORK=CONDITIONAL
```
