# Route B Gate G sensitivity experiment preregistration v1

This immutable registration precedes all solver execution. The companion JSON is authoritative for exact numerical controls, source anchors, uncertainties and selection rules. No scientific quota or tau_mean is selected.

Ra_test=30000, Pr=.71, L=.01 m, depth=.001 m; temperatures 301/300/300.5 K, nu=1e-6 m2/s. Scripts compute alpha and beta from Ra and save them. Four walls are no-slip/impermeable, hot left/cold right, adiabatic top/bottom, empty front/back; laminar serial DP ASCII16. Formal cases/results and 160/320 grids are forbidden.

Exploration uses 20/40; 80 is holdout. Every Arm 1/2 condition cold-starts. Arm 1 uses pressure tolerances 1e-6/8/10, relTol=0. The tightest sufficiently steady same-grid zero-source run is a numerical baseline, not truth. All seven QoIs and field, residual, continuity, boundary and heat monitors apply.

Steady rule: sample every20 iterations; minimum400, 200-iteration window, a further200 of sustained qualification, maximum12000. Value range and U/T field change criteria are1e-8; position resolution1/4096; heat imbalance range1e-8. Continuity range is monitored against solver capacity, not an acceptance threshold. U/T initial residual <=1e-8 and final pressure residual <=1.1 times its own tolerance are independently checked. Normal exit and finite data are mandatory.

Source solver changes only the integrated pressure RHS by -g; sources are internal-face incidence pairs with zero net, no source on the reference cell. Original U/T operators, flux correction order and relaxation remain. Zero-source full field SHA256 equivalence must precede nonzero sources. Tiny positive source tests the sign q≈+g and source dimensions. Realization is checked using measured q-g (<=5% source L1), physical residual mapping, reference handling, wall flux and closure; these are experimental purity rules, not research acceptance quotas.

Pilot20: P1 positive at1e-8..1e-4. Selection begins at the lowest resolved value-response level with two larger valid levels; otherwise use highest three valid levels and explicitly report incomplete resolution. Fewer than three valid levels or a STOP condition prevents further execution. Exploration20/40 then uses P1/P2/P4 at three levels plus negative mid P1/P2. Same actual epsilon is checked; nominal equality alone is insufficient. At most two adjustment trials per condition, all retained.

Uncertainty is conservative baseline+test tail/continuation variation plus extraction and available restart/serialization contributions; no unproven RSS independence. Nu has a defined discrete sum; centreline peaks compare4097/8193 and tied-peak intervals. Differences below uncertainty are EFFECT_NOT_RESOLVED. Near-zero scale branch is fixed by baseline uncertainty, independent characteristic scale=1 in dimensionless units. Absolute-position differences use X/L or Z/L.

Temperature offset diagnostic shifts20-grid temperatures and TRef by+50 K, preserving DeltaT/Ra/Pr; compare zero-source invariance and one source response. Do not modify TEqn or compensate heat sources. Nonzero continuity with absolute-T convection is a perturbed numerical system.

After exploration only, freeze confirmation_manifest_v1.json with amplitudes, patterns/signs, response envelope, uncertainty and comparison criteria, record SHA256, then run80 holdout (P1/P3, >=two amplitudes and both signs plus Arm1). No retroactive v1 refit. Confirmation concerns sensitivity trend, not quota PASS. Quota and tau remain UNRESOLVED.

STOP on solver non-equivalence, unknown sign/dimensions, nonzero source net, uncontrolled source realization, fatal/NaN, failed maximum-iteration steady criterion, required confirmation rewrite, need for formal data or production edits. Preserve all partial evidence. Amend registration by a new amendment file, never overwriting v1 after first solver execution.
