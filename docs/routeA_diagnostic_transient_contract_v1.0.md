# Route A diagnostic transient study contract v1.0

Task: `PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT`  
Date: 2026-10-05, Asia/Tokyo  
Ownership: `DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION`  
Diagnostic guard: `DIAGNOSTIC_TRANSIENT_CONTRACT_v1.0`  
Preparation: **INCOMPLETE**; technical readiness: **NO**; execution authorization: **NO**.

This is a separate, preparation-only diagnostic contract. Resolved definitions below are preregistered; unresolved settings are blocking fields, not defaults or permission to improvise. SHA-256 of the companion JSON is recorded in its `.sha256` sidecar and in the preparation report. A later diagnostic revision must close the blockers before a separately instructed RUN task. This document is not formal Amendment 008, formal v1.8, or a replacement for formal v1.7.

## 1. Purpose and ownership

Primary question: at Ra=1e6 on the fixed 160×160×1 Route A grid, how do different Courant controls affect the trajectory from rest and uniform internal T0, final steady QoIs, mass behavior, and implemented energy balance?

The study will characterize startup, time-step sensitivity, steady arrival, closed-cavity mass, energy storage/work, and thermo/solver-density synchronization. It supplies fluid-only evidence relevant to later moving particles or objects. No study data exist from this preparation task.

## 2. Formal-status separation and authority

Observed HEAD equals the requested HEAD: `fd129af05d43e3551cf0d4a037b5dd8f54ccbe4a`. The current formal JSON is [routeA_execution_contract_v1.7.json](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_execution_contract_v1.7.json), SHA-256 `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`. Its `current_execution_guard` remains `v1.7`, and `authority.Gate_J_authorized` remains false.

Normative inputs: `docs/acceptance_criteria.md` §12/§14, `docs/benchmark_spec.md` §6, and current formal v1.7. Current research separation: `results/routeA/attempts/attempt_008/GateJ_prerequisite_review.md` and `.json`. Implementation evidence: local `/opt/openfoam13` source, `docs/openfoam_design.md`, `docs/routeA_implementation.md`, `docs/routeA_execution_plan.json`, accepted `A-Ra1e6-fine` end_9000 provenance/metrics, its original inputs, and existing extraction code. Historical implementation status summaries do not override the later reviews.

Preserved statuses: H formal PASS / review SUPPORTED_WITH_LIMITATIONS; `BENCHMARK_CORE_PASS=NO`, `ROUTE_A_CHARACTERIZED=NO`, `FORMAL_GATE_J_PREREQUISITES_SATISFIED=NO`, `FORMAL_GATE_J_CURRENTLY_ALLOWED=NO`, `FORMAL_GATE_J_EXECUTED=NO`, `FORMAL_GATE_J_PASS=NOT_EVALUATED`, `DOWNSTREAM_TRANSIENT_READY=NO`, `PARTICLE_COUPLING_READY=NO`, `ALL_ROUTE_A_GATE_F=FAIL`, `ALL_RA_NEEDS_320=YES`. Historical saved NOT_EVALUATED values are not rewritten to NO; NO here is the current readiness predicate.

Local source hashes in the JSON/report identify the exact inspected files. The Foundation [energy source](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/applications/modules/fluid/thermophysicalPredictor.C) and [density synchronization source](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/applications/modules/isothermalFluid/isothermalFluid.C) were also consulted as primary-source cross-checks. Public master is supplementary and cannot replace the pinned local runtime evidence.

## 3. Physical problem

Use the original accepted `A-Ra1e6-fine` physical formulation, not the Gate H beta1e-4 perturbation. This characterizes the intended research condition.

| Quantity | Fixed value |
| --- | --- |
| Ra / Pr / beta ΔT | 1,000,000 / 0.71 / 1e-3 |
| Grid / domain | 160×160×1 uniform orthogonal hex; L×L×W = 0.1×0.1×0.001 m |
| T0 / Th / Tc / ΔT | 300 / 300.5 / 299.5 / 1 K |
| rho0 / beta / mu / Cv | 1 kg/m³ / 1e-3 K⁻¹ / 1e-5 Pa s / 1000 J/(kg K) |
| nu0 / alpha0 | 1e-5 / 1.4084507042253522e-5 m²/s |
| k | Cv mu / Pr = 0.014084507042253521 W/(m K) |
| g | (0, −140.8450704225352, 0) m/s², computed from Ra nu0 alpha0/(beta ΔT L³) |
| Model | foamRun + fluid; heRhoThermo/pureMixture/const/eConst/Boussinesq/specie/sensibleInternalEnergy |
| Transport | laminar Stokes; laminar Fourier; no radiation, MRF, fvModels sources, fvConstraints, mesh motion, or particles |
| Energy reference | Inherit original eConst Tref/esRef defaults; Tref is not T0. Do not replace e by Cv(T−T0) in the equation. |
| Pressure reference | hRef=0 m; constant pRef=0 Pa; PIMPLE pRefValue=0 Pa; pRefCell=12719 |

Reference cell centre is (0.0496875, 0.0496875, 0.0005) m, selected by nearest-domain-centre distance and then minimum cell ID. `pRefValue` is passed to the p_rgh equation reference; it does not prescribe absolute p(refCell)=0. No atmospheric pressure offset is added. x is horizontal; OpenFOAM y is vertical, denoted Z=y/L in the paper. OpenFOAM U.y supplies paper W. z is the empty thickness direction.

All Co series hold the physical model and spatial grid fixed. `GRID_320_EXECUTED=NO`, `GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED=NO`.

## 4. Governing equations and density roles

Let rho_s denote the solver density and rho_T the thermo/EOS density. For the inspected Boussinesq/eConst branch:

\[
\rho_T=\rho_0[1-\beta(T-T_0)],\qquad \psi=\partial\rho_T/\partial p=0,
\quad e=C_v(T-T_{ref})+e_{s,ref},\quad K=|U|^2/2.
\]

The intended continuum form of the implemented conservative equations, with all registered sources absent, is:

\[
\partial_t\rho_s+\nabla\cdot(\rho_s U)=0,
\]
\[
\partial_t(\rho_s U)+\nabla\cdot(\rho_s UU)-\nabla\cdot\tau
=-\nabla p+\rho_s g,
\]
\[
\partial_t(\rho_s e)+\nabla\cdot(\rho_s Ue)
+\partial_t(\rho_s K)+\nabla\cdot(\rho_s UK)
+\nabla\cdot(pU)-\nabla\cdot(k\nabla T)=\rho_s U\cdot g.
\]

These expressions explain terms; the diagnostics below use the actual finite-volume operators and their evaluation stages. In the momentum implementation the stress coefficient is rho_s nuEff, with nuEff=mu/rho_T. It reduces to mu when densities coincide. The pressure force is reconstructed from the pressure-corrected face flux and buoyancy force. The energy implementation contains explicit K storage/transport and pressure/gravity work; do not add a separate viscous heat source or substitute the classical incompressible temperature equation.

## 5. Transient solver algorithm: confirmed sequence and blockers

The exact source sequence in `foamRun.C` is preSolve → adjustDeltaT → increment time → outer PIMPLE loop → postSolve → write. Within each outer loop: first-outer density predictor (when simpleRho=false) → transport prediction → momentum predictor → internal-energy solve → thermo.correct → pressure correctors → transport correction. No LTS or steady pseudo-time mode is permitted.

In `correctBuoyantPressure.C`: copy thermo density into rho_s and relax if configured; assemble pressure coefficients/phiHbyA including backward ddtCorr; constrain wall pressure gradients; solve p_rgh through non-orthogonal corrections; update native phi; update U and K; reconstruct p; apply thermo.correctRho(psi Δp), which is zero for this EOS; solve density continuity; report native continuity; reconstruct p again. With `simpleRho=false`, the continuity density remains until `postSolve()`, which assigns rho_s=thermo.rho(). No transient closed-mass pressure-level adjustment is provided by the steady-only adjustMass branch.

| Control | Confirmed implementation / preparation decision |
| --- | --- |
| Coupling | transient PISO when outer=1; PIMPLE when outer>1. Future exact count/mode UNRESOLVED. |
| nOuterCorrectors / nCorrectors | Existing steady reference 1 / 2 is not a transient convergence prescription. Both future counts UNRESOLVED. |
| nNonOrthogonalCorrectors | 0 fixed, because the target is the same exactly orthogonal mesh; still one pressure solve per pressure correction. |
| momentumPredictor / simpleRho | true / false fixed; preserve native transient density path. |
| transonic / consistent | false / false fixed; audited non-transonic conventional branch. |
| hydrostaticInitialisation / correctPhi | false / false fixed; static canonical mesh. |
| Transport controls | Explicit transportPredictionFirst=true, transportCorrectionFinal=true, matching inspected defaults. |
| Linear solvers | Source supports inherited rho diagonal, p_rgh PCG/DIC, U/e PBiCGStab/DILU. Final tolerance, relTol, maxIter and Final entries UNRESOLVED. Reference steady tolerance=1e-10, relTol=0 is evidence only. |
| Relaxation | Source calls EEqn/UEqn relaxation and pressure-force/density relaxation. Future explicit field/equation factors UNRESOLVED; steady p_rgh/U/e=0.3/0.5/0.7 is not silently imported. |
| Runtime changes | runTimeModifiable=false; no result-driven controller or numerical changes. |

`TRANSIENT_ALGORITHM=UNRESOLVED` means the native sequence is known but its complete numerical configuration is not frozen. It does not mean that a generic algorithm may be invented.

## 6. Canonical independent cold initial condition

Every series starts from the same analytic time-0 state, never an accepted steady field or another Co solution. Internal U=(0,0,0), T=T0, rho_s=rho_T=rho0, K=0, phi=0. Use noSlip on the four physical walls; hot/cold T fixedValue at Th/Tc; top/bottom T zeroGradient; front/back empty on mesh and all fields. Energy patch values come from thermo's temperature BC conversion.

For cells and physical patches define gh=g·x (hRef=0), p=rho_T gh+pRef, p_rgh=0. At hot/cold patches use EOS rho_T=0.9995/1.0005 kg/m³, not internal rho0. At adiabatic patches initially use T0. Input p is calculated on physical walls, p_rgh fixedFluxPressure; front/back empty. Omit a stale rho/phi file or write its exactly equivalent canonical value; do not read either from a steady checkpoint. e is initialized by thermo from T using the unchanged reference convention.

Future initialization verification must inspect constructor-complete state before the first solve in the same registered process. Check all cells and four physical patches: p_rgh=p−rho_s gh−pRef and p_rgh≈0 with inherited OQ-02 1e-12 Pa tolerance. Include U/T/rho/phi/e checks. No constructor or initialization run occurs in preparation. The startup observation mechanism must be resolved with the stage evaluator (U04).

## 7. Spatial discretization

Reuse original uniform mesh geometry and topology. Keep gradSchemes default Gauss linear; divSchemes default none with explicit Gauss linear for div(phi,U), div(phi,e), div(phi,K), div(phi,(p|rho)), and diagnostic div(U); laplacianSchemes default Gauss linear orthogonal; interpolationSchemes default linear; snGradSchemes default orthogonal. The actual Stokes stress correction is face-flux divergence, not controlled by the legacy unused stress-divergence dictionary key. Fourier's laplacianCorrection uses its coded uncorrected orthogonal matrix; preserve that operator.

Input/model/geometry verification must use real dictionary contents and future mesh evidence, including 25,600 cells, zero non-orthogonality, two-dimensional solution directions, wall/empty types, and reference-cell coordinates. Existing mesh evidence is a reference, not a new mesh result. No blockMesh/checkMesh invocation or case generation occurs now.

## 8. Temporal discretization and startup

Dictionary syntax is confirmed: `ddtSchemes { default backward; }`. All active ddt(rho), ddt(rho,U), ddt(rho,e), ddt(rho,K), ddt(p_rgh), ddt(p), and ddtCorr must resolve to backward. No per-field Euler override or localEuler.

For current h=Δt_n and previous k=Δt_(n−1), define

\[
a=1+\frac{h}{h+k},\quad c=\frac{h^2}{k(h+k)},\quad b=a+c,
\quad D_B F^n=\frac{aF^n-bF^{n-1}+cF^{n-2}}{h}.
\]

This is the inspected static-mesh backward operator. At equal steps the coefficients are (3/2,2,1/2). With fewer than two old times, the implementation substitutes great for k, giving a first-order startup limit. Record nOldTimes and effective coefficients separately for rho, e, K and U; do not assume their startup bookkeeping or restored history is identical. No synthetic warm history is fabricated.

For rho-weighted storage, old products are rho.oldTime()*e.oldTime() and rho.oldTime()*K.oldTime(), not rho_current multiplied by a derivative of e/K. A simple (F^n−F^(n−1))/h is saved as a physical secant diagnostic, never substituted for D_B in the discrete conservation residual.

## 9. Courant controller

Fixed controller architecture: Foundation v13 native adjustTimeStep=true, per-series maxCo=target, deltaTFactor=1.2 (explicitly fixing inspected native default), finite maxDeltaT, no function object or fvModel time-step cap, no adjustableRunTime write alignment. No additional userTime transformation. Initial deltaT and numeric maxDeltaT are **UNRESOLVED** (U02).

Source definition, with native mass phi in kg/s:

\[
C_i=\frac{h}{2V_i\rho_{s,i}}\sum_{f\in i}|\phi_f|,
\quad Co_{max}=\max_i C_i,\quad
Co_{mean}=\frac{h\sum_i[\sum_f|\phi_f|/\rho_{s,i}]}{2\sum_i V_i}.
\]

Do not replace this by face interpolation of phi/rhof for the controller. The solver cap is min(maxDeltaT, fvModels.maxDeltaT, maxCo/Co_previous * deltaT_previous) when Co_previous>small; the Courant restriction is omitted otherwise. foamRun then sets the new step to min(1.2 deltaT_previous, solver cap, functionObjects.maxDeltaT). Initial setDeltaT only reduces the specified initial step using the caps. Freeze the concrete initial/max steps and prove that all other caps are inactive before RUN.

At U=0 initial Co=0, so maxCo does not constrain startup: a grounded initial step and finite diffusion/startup cap are essential. Ra/Pr, steady iteration counts and the source defaults do not specify a transient accuracy cap. No cap number is fabricated here. Record prior-state reported Co, control decision/new h, and recomputed end-step Co separately; the log's preSolve Co uses the previous solution and previous h. Do not mislabel it as the achieved Co of the newly solved step. Native adaptation can overshoot the target during growth; record it, and resolve any overshoot STOP policy in U02 before RUN.

## 10. Independent Co series and case concepts

Primary Co targets: 0.5 and 0.25. Conditional target: 0.125. Case concepts: `A-DT-Ra1e6-fine-Co0p5`, `A-DT-Ra1e6-fine-Co0p25`, `A-DT-Ra1e6-fine-Co0p125`. All have the same canonical cold state and identical final frozen algorithm/physics/spatial settings; maxCo is the only primary series control changed. No Co0.5→Co0.25 restart.

Shared initial/maxDeltaT caps must be registered and cap activity reported. If caps dominate both trajectories, two different target labels do not demonstrate a factor-two actual temporal refinement. Mark this limitation using measured h histories rather than changing caps after seeing results.

## 11. Inner convergence

`TRANSIENT_INNER_CONVERGENCE_RULE=UNRESOLVED` (U01). Required before RUN: per-step linear residual requirements/maxIter, complete outer nonlinear criteria, maximum outer/inner counts, explicit relaxation factors, criteria evaluation after pressure/thermo synchronization, and non-converged-step handling. The steady Gate D final initial residual≤1e-7 over steady iterations does not bound transient nonlinear iteration error. Its 200-iteration window is not a physical-time window.

Inspect `PIMPLE/outerCorrectorResidualControl`, whose per-field subdictionaries contain tolerance and relTol. Native pimpleLoop checks initial residuals from its solve index; it may schedule an additional final iteration when convergence is detected. Hitting nOuterCorrectors prints a non-convergence message but does not inherently abort the time loop. Native absolute OR relative checks and its field aggregation are not a substitute for explicitly requiring Ux and Uy evidence. End-process residualControl must not stop the physical study early.

Future evidence must retain every Ux/Uy/e/p_rgh/rho solve's initial/final residual and iterations, time index, outer index, pressure index, non-orthogonal index and field/component. Also retain unrelaxed equation defects and between-outer state changes; a small linear final residual alone does not prove nonlinear convergence. U01 must justify an iterative error budget sufficiently below the 0.5% diagnostic comparison and distinguish it from temporal truncation; do not copy thresholds solely because the syntax accepts them.

Non-converged-step handling is fixed in principle: STOP the entire affected series, mark partial evidence invalid for final temporal conclusions, keep all data; do not continue, reduce dt, tune relaxation/correctors/tolerance, or drop the step. Concrete convergence numbers/counts must be preregistered before this handling can be operational.

## 12. Dimensionless time

Fix `DIMENSIONLESS_TIME_DEFINITION=t*=alpha0*t/L²=t/710 s`, using repository heat-diffusion reference scales in `docs/benchmark_spec.md` and `docs/openfoam_design.md` §8. This is a dimensional consequence of the already fixed alpha0/L velocity scale, not a new literature threshold. Use reference alpha0, not local temperature-dependent diffusivity. t*=0 is the common cold start. Save dimensional seconds and dimensionless values for every accepted or failed step.

## 13. Duration and termination

Minimum t*, maximum t* (and hence endTime), physical-time steady-window length, and the minimum number of confirmation windows are **UNRESOLVED** (U03). 710 s defines units, not the time needed to reach steady state. The design docs explicitly leave non-dimensional termination time open; accepted steady iteration label 9000 is not 9000 s.

A future complete revision must stop at the first registered confirmation endpoint that satisfies the full arrival rule after minimum t*, or at the registered maximum duration. At the cap without arrival report `STEADY_NOT_REACHED`; no automatic extension and no final steady Co comparison. Also preregister a compute/step watchdog if necessary, distinguishing resource interruption from scientific duration. Maximum duration must be fixed before generation/execution.

## 14. Steady-arrival definition and final window

`STEADY_ARRIVAL_RULE=UNRESOLVED`. Required architecture is fixed: common physical-time windows for all Co series, not a count of steps; Nu_bar_cavity/Umax/Wmax histories; normalized range and drift; mass drift and stage continuity residuals; energy storage/residual/work; rho_min/rho_max/rho_mean and synchronization defects; inner convergence/evidence health across the entire window. The ranges may use (max−min)/max(|time-weighted mean|,1) for the dimensionless primary QoIs, consistent with existing scales; thresholds and physical window lengths remain U03.

Do not transplant Gate D's hot-wall monitor or its non-increasing two-wall imbalance rule. During a transient net wall heat input supplies storage and work. A flat sampled QoI or rho range does not by itself prove arrival. Mass/energy hard thresholds remain unresolved unless grounded; define how their finite diagnostic histories enter the arrival decision before RUN.

On arrival use the registered final steady window, report endpoint values and time-weighted window summaries separately. Primary final comparator will use the time-weighted mean of each QoI in its equal-duration confirmed final window. Position means, ranges and endpoint positions are all retained. Without a frozen/achieved window there is no final value for the 0.5% criterion. No whole-run average or steady-baseline agreement is an arrival test.

## 15. Primary QoIs and diagnostic baseline comparison

Use the accepted extractor definitions, porting the definitions to non-integer physical times without invoking the steady analyzer. It currently rounds times to iteration labels and writes formal result roots; that execution path is unsuitable here.

| Quantity | Definition / units / evaluation |
| --- | --- |
| Nu_bar_cavity | theta=(T−Tc)/ΔT; U*=U.x L/alpha0; 1+Σ(V U* theta)/Vdomain. The conductive integral 1 follows exactly from fixed hot/cold temperatures. Paper-definition diagnostic, not conserved energy. |
| Nu_bar_0 | Hot wall paper-definition mean from T/geometry normal gradient; store physical heat-flux route separately. |
| Umax, Umax_Z | Positive U.x L/alpha0 on exact X=0.5; linear interpolation of two bracketing cell-centre columns to centreline, then 4097 fixed points with noSlip endpoints; Z=y/L. |
| Wmax, Wmax_X | Positive U.y L/alpha0 on exact Z=0.5; same method from bracketing rows, 4097 points; X=x/L. |
| Q_hot/Q_cold | Official Fourier/wallHeatFlux convention, positive into cavity, units W; see §17. |
| epsilon_v | L ⟨|fvc::div(U)|⟩V / maxcell|U|, same reconstructed-velocity operator as baseline. At zero velocity report null with ZERO_SPEED reason and dimensional divergence=0; never invent a denominator. |

Also save Nu_bar_1/Nu_bar_half, section profile, raw/position extrema, full T/U fields at registered writes, and raw T/rho ranges. Compare future final values with accepted end_9000 and canonical Table V (`reference/de_vahl_davis_table_v.csv`) as diagnostics, using unchanged signed/absolute scalar differences and absolute normalized-position errors. Do not relabel these as a new formal E/G/J result.

## 16. Mass diagnostic: actual discrete equation

`correctDensity.C` solves fvm::ddt(rho_s)+fvc::div(phi)=0. Static finite-volume cell residual at density-solve completion is

\[
r_{M,i}=D_B\rho_{s,i}+\frac1{V_i}\sum_{f\in i}s_{if}\phi_f,
\quad R_{M,C}=\sum_iV_i r_{M,i}=D_B M_C+B_M,
\quad M_C=\sum_iV_i\rho_{s,i}^{C},\quad B_M=\sum_{f\in\partial V}\phi_f.
\]

Here C is the continuity-solve stage; oldTime states are those actually used by that solve, normally prior end-step states. Do not build a fictitious multi-step history consisting only of prior C snapshots. Internal face fluxes cancel exactly in the global sum; boundary faces are outward oriented; empty patches have zero active contribution. Native phi is a pressure-corrected **mass** flux [kg/s], not U·Sf [m³/s]. Save actual boundary values, not an imposed zero in the evaluator.

| Saved term | Meaning / units / operator / evaluation |
| --- | --- |
| total_mass_C, total_mass_end, total_mass_EOS | kg; Σrho V at continuity, after postSolve, and thermo; fluid contained in domain |
| mass_storage_rate | kg/s; D_B M using actual density-stage histories; discrete temporal storage |
| mass_storage_rate_secant | kg/s; (M_end^n−M_end^(n−1))/h; physical interval change, separate from BDF2 |
| boundary_mass_flux | kg/s; native Σwall phi; positive outward loss |
| mass_balance_residual_C | kg/s; D_B M_C+B_M; density-equation defect |
| mass_balance_residual_end | kg/s; D_B M_end+B_M_end using end-state histories; synchronized-state conservation diagnostic, not solved density matrix residual |
| mass_local_L1 / Linf | kg/(m³ s); ⟨|r_M|⟩V / max|r_M|; expose cancellation hidden by a global sum |
| mass_drift | (M_end−M0)/M0; dimensionless total change, not a conservation residual |
| eos_mass_jump / sync_mass_rate | M_end−M_C [kg] and a(M_end−M_C)/h [kg/s] for matched old states and unchanged phi |

For the last pressure correction, with no constraints and simpleRho=false, U/K/phi are unchanged by postSolve, so `R_M,end − R_M,C = a(M_end−M_C)/h` when both evaluators use the same old states/coefficient. Record it as a decomposition, and verify prerequisites; do not assume old fields are C-stage histories. If coefficients or old states differ, compute the full difference and flag the mismatch.

Pressure compatibility is separately important. With psi=0 and closed Neumann walls, integrating the pre-reference pressure equation requires D_B M_EOS+B_M=0. Temperature can change EOS mass, while changing p cannot change rho_T. `fvMatrix::setReference` adds a diagonal/source contribution at cell12719; a small residual of the referenced pressure system can hide a physical-equation defect there. Record pre-reference pressure continuity residual, post-reference solved residual, reference contribution and reference-cell residual. This is a source-derived research hypothesis/diagnostic requirement, not an observed failure.

Expected ideal closed behavior: boundary physical mass flux=0 and invariant mass if both continuity and EOS synchronization are compatible and converged. A small C-stage residual alongside an EOS synchronization jump must be reported, not called overall conservation PASS.

Normalization is fixed before results: Vdomain=L²W=1e-5 m³, Mref=rho0 Vdomain=1e-5 kg, tchar=710 s, mRateRef=Mref/tchar=1.4084507042253522e-8 kg/s. Signed global normalized residual is R_M/mRateRef; magnitude is stored separately. Local dimensionless defect is tchar r_M/rho0. Also save M/Mref and drift/M0. Do not normalize by a nearly zero wall flux or solution velocity.

## 17. Energy diagnostic: source-derived implemented balance

For static mesh, sensibleInternalEnergy=e and no sources, the exact registered operator target is

\[
\mathcal E = fvm::ddt(\rho_s,e)+fvm::div(\phi,e)
+fvc::ddt(\rho_s,K)+fvc::div(\phi,K)
+fvc::div(\phi,p/\rho_s)+divq(e)
-\rho_s(U\cdot g)=0.
\]

`Fourier::divq(e)` is **−fvc::laplacian(k,T) − fvm::laplacianCorrection(k/Cv,e)**. The single-phase transport `alpha()` in that implementation equals phase fraction 1, not thermal diffusivity alpha0. The correction matrix is a coded uncorrected orthogonal Laplacian with an explicit correction source. Preserve this term, its assembly snapshot and thermal BC conversion; do not replace it blindly with a newly evaluated final −laplacian(k,T).

Two residuals are required, with distinct names:

* **R_E,assembly:** unrelaxed EEqn assembled at the actual energy-solve stage and applied to the post-energy-solve e. Retain lagged rho_s/phi/U/K/p/T/Cv, oldTime fields and boundary coefficients/source. Pressure correction later changes U/K/phi/rho, so recomputing from end fields is not this residual. Report the relaxed solved-matrix residual separately.
* **R_E,end:** re-evaluation of the same unrelaxed governing operators on synchronized end fields and native end phi, with the actual old histories, reference conventions, and converged-state Fourier law. It measures full coupled state defect; it is not asserted to have been solved during the last energy predictor.

Define the stage-specific global balance with positive outward transport and positive source/work into the fluid:

\[
R_E=S_e+S_K+F_e+F_K+W_p+H_{out}-W_g-S_{models}.
\]

For assembly stage Hout includes the exact correction-matrix action. For end-state evaluation reassemble that operator and retain its explicit/implicit parts; at a self-consistent refreshed e/T reference it reduces to the Fourier divergence. Report the correction contribution and verify this reduction rather than deleting it.

| Term | Mathematical / physical meaning | Units; sign | OpenFOAM operator; numerical evaluation |
| --- | --- | --- | --- |
| E_int | ΣV rho_s e; stored sensible internal energy in original reference | J | thermo.he(), solver rho; sum cell products at named stage |
| E_kin | ΣV rho_s K; bulk kinetic energy | J | K=0.5 magSqr(U), using assembly K for assembly diagnostic |
| S_e | D_B ΣV rho_s e; internal storage rate | W; increasing storage positive | action of fvm::ddt(rho,e), with native old products/coefficient |
| S_K | D_B ΣV rho_s K; kinetic storage rate | W; increasing storage positive | fvc::ddt(rho,K) volume integral |
| F_e | Σboundary phi e_face; advected internal energy | W; outward positive | fvm::div(phi,e) matrix/face-flux evaluation, Gauss linear and actual boundary coefficients |
| F_K | Σboundary phi K_face; kinetic transport | W; outward positive | fvc::div(phi,K), Gauss linear; native phi |
| W_p | Σboundary phi (p/rho_s)_face; pressure-work transport | W; outward positive | fvc::div(phi,p/rho), exact composite-field interpolation; do not independently interpolate p and divide by rhof |
| H_out | integrated divq(e); net conducted heat leaving fluid | W; outward positive | exact Fourier explicit Laplacian and implicit correction action; cell sum with boundary terms |
| Q_hot / Q_cold | −Σpatch q_out | W; inward positive | q=−k snGrad(T); wallHeatFlux=−q. Hot normally positive; cold normally negative |
| W_g | ΣV rho_s U·g; gravitational work on fluid | W; positive input | cell-centred multiplication from energy RHS, never replaced by an assumed zero or boundary identity |
| S_models | integrated source applied to energy | W; positive input | fvModels.source(rho,e); absent=0 under guard, any nonzero source is wrong-model STOP |
| R_E | LHS−RHS global equation defect | W; signed plus magnitude | unrelaxed matrix action with boundary diagonals/sources plus explicit terms; also local L1/Linf |

At any stage with native zero boundary phi, Fe/FK/Wp vanish as global boundary transports. Pressure work may still be large locally; store volume weighted L1/Linf and signed integral separately for Wp and Wg, plus their cancellation defect. Large opposing terms must not be canceled analytically before numerical evaluation. No `−dpdt` branch is used for e, and no moving-mesh pressure work is present. No separate viscous-work flux is inserted into this energy equation.

The pressure `p/rho` composite uses the unchanged hydrostatic/gauge convention. The potential energy E_pot=−ΣV rho_s gh [J] may be saved as an auxiliary only; it is not added to the primary equation residual. On a conservative compatible continuum solution gravity work relates to potential storage, but cell rho_s U·g and native phi transport need not obey that identity discretely. Quantify their defect if used. The primary functional is E_int+E_kin with an explicit Wg term.

Numerical evaluation requirements: retain unrelaxed matrix coefficients/implicit correction sources or equivalent term actions at assembly; account for non-coupled boundary diagonal/source terms; apply LHS−RHS convention. `fvMatrix::residual()` is b−Aψ, so negate it to obtain our convention; its dimensions already include cell volume. Do not multiply an integrated matrix residual by V again. Explicit field terms in W/m³ must be multiplied by V exactly once. Record assembly/solve/end stages, coefficient hashes and old-time identifiers to prevent mixed-epoch residuals. Evaluator implementation/verification is unresolved U04; a final-field Python sum alone is insufficient to prove the assembly balance.

End-state closed-cavity equation, when actual boundary phi is zero, is

\[
S_e+S_K-(Q_{hot}+Q_{cold})-W_g=R_{E,end}.
\]

Thus net wall input, storage and residual are three distinct quantities. Q_hot+Q_cold≠0 during startup is not a failure. In a compatible steady closed continuum limit storage→0 and integrated gravity work→0, giving two-wall equality. Preserve measured discrete Wg and operator defects in that comparison; do not use steady heat balance as the entire transient criterion.

Energy scale is fixed: Eref=Mref Cv ΔT=0.01 J; Qref=Eref/tchar=k ΔT W=1.4084507042253522e-5 W. Save E_int/Eref, E_kin/Eref and signed/magnitude R_E/Qref and every term/Qref. Store local defects normalized by rho0 Cv ΔT/tchar. Retain raw e-reference energies; subtracting a constant times M changes storage if mass drifts, so an anomaly energy cannot replace the primary functional. An auxiliary E_int−e(T0)M may be saved with its mass-related correction explicitly shown.

No new mass/energy hard accuracy tolerance is assigned: `MASS_ENERGY_HARD_THRESHOLD=UNRESOLVED`. Report double-precision reduction conditioning and linear/outer iterative floors separately; a solver's normalized residual is not a W or kg/s tolerance. Before RUN U04 must establish evaluator identity/units/sign tests on synthetic data or matrix algebra without solver execution, and a defensible roundoff/iteration-floor interpretation. Finite/positive-state and evaluator-health STOP rules are fixed in §22.

## 18. Thermo/rho synchronization and OQ-07

Observe named stages: constructor-before-first-solve; first-outer density predictor completion; energy assembly; energy solve before thermo correction; after thermo.correct; pressure-EOS reset; before/after each correctDensity; immediately before/after postSolve. Link observations to time/outer/pressure indices. Save rho_s and independently exposed rho_T, rho_s−rho_T (signed, volume mean, L1, Linf), EOS prediction from T, M_s/M_T, rho min/max/mean and pressure relation defect.

Native transient continuity output is **density discrepancy**, not D_B rho+div(phi): local=∫|rho_s−rho_T|/M_s, global=∫(rho_s−rho_T)/M_s. The inspected transient routine adds global to cumulative on every invocation; keep pressure/outer count and the raw cumulative values, do not treat cumulative as physical mass drift or a deltaT-weighted integral. This differs from its steady branch.

After postSolve rho_s−rho_T can be identically zero by assignment while M has changed. End-only consistency is not evidence that the previous continuity solve and EOS evolution conserve mass simultaneously. With psi=0, pressure cannot correct EOS mass by compressibility. The inspected postSolve does not rebuild p or p_rgh after its density assignment: if the prior relation holds, the end-state defect p−p_rgh−rho_end gh−pRef equals (rho_C−rho_end)gh. Save this defect instead of repairing p in the evaluator. Record jumps at the pressure EOS copy and postSolve, restart reconstruction of thermo/rho/p, and old-time history fidelity. Do not force an offset onto rho_T, redistribute mass, or change the EOS to make the diagnostic look conserved.

## 19. Sampling and write policy

Fixed diagnostic cadence: initial state at t=0 and every solved step; every outer/pressure solve for residuals and stage mass/energy/rho records. Primary Nu/4097-point extrema and end Co are evaluated after postSolve each step. No ten-iteration centreline subsampling, integer rounding, skipped initial transient or interpolated values replacing raw data.

For design clarity fix full field writes every physical step (`writeControl timeStep; writeInterval 1; purgeWrite 0`), plus time-0 canonical evidence; scalar and operator diagnostics remain separate append-only streams. Use binary full-field output to preserve DP values and ASCII diagnostic precision17/time directory precision17; preserve original log numeric tokens too. No output-alignment function object alters dt. Disk capacity must be checked after U02/U03 determine duration/step sizes; insufficient capacity is STOP before RUN. Any lower-storage cadence needs a diagnostic revision rather than a mid-run adjustment. Full fields alone still lack pre-postSolve stage evidence.

Every record needs case/study/guard/input hashes, time index, physical and dimensionless time, Δt/previous Δt/BDF coefficients, stage and corrector identifiers, evaluator version and validity flags. Primary CSV includes at least time, dimensionless_time, deltaT, Co_mean, Co_max, Nu_bar_cavity, Nu_bar_0, Umax, Umax_Z, Wmax, Wmax_X, Q_hot, Q_cold, total_mass, mass_storage_rate, boundary_mass_flux, mass_balance_residual, energy_storage, wall_heat_terms, work/source terms, energy_balance_residual, rho_min, rho_max, rho_mean, epsilon_v, native continuity; assembly/C/end-stage data are named separately. Save startup energy/mass values rather than inferring them from later samples.

## 20. Restart and serialization

Single continuous process per Co series is the primary policy. A forced interruption retains immutable partial data and marks the primary series interrupted. Do not silently resume it. The primary rerun, if separately authorized, begins from the original cold state under a new diagnostic attempt with identical frozen settings.

A necessary restart requires a diagnostic revision before resume, preserving complete backward oldTime fields, previous h, current rho_s/rho_T and p/p_rgh, EOS/pressure constructor changes, Co/controller state and output identity. Mark restarted trajectories separately; compare pre/post mass/energy/QoIs and histories. A writePrecision change or binary format alone does not prove restart equivalence. No claim of zero restart error and no warm start between Co series. Restart testing is secondary and no restart is run here.

## 21. Evidence, directories and sealing

Preparation report lives at `results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_contract_preparation.{md,json}`. This separate namespace prevents new material from entering the already sealed formal attempt_008. The attempt_008 Gate J review remains read-only provenance.

Future case root: `cases/routeA/diagnostic_transient/diagnostic_attempt_001/<case_id>/`. Future result root: `results/routeA/diagnostic_transient/diagnostic_attempt_001/series/<case_id>/`. These are concepts only; no case or series directories are generated now. Never write into formal Gate J results, formal attempt_009, existing steady-case results or original seals. No existing generator/steady analyzer is executed or patched during preparation.

Future evidence: complete numeric frozen dictionaries/model/BC/init recipe and canonical initial hashes; prospective mesh/input hashes; local source and executable/loaded-library hashes/build banner; raw solver/stage/evaluator logs; per-step histories; field writes; actual Co/cap activity; all convergence decisions/STOP events; independent initial-state equivalence; final-window endpoints and means; temporal summary; trajectory overlays; mass storage/flux/residual/sync plot; energy term/residual/cancellation plot; T/U snapshots/centrelines and positions; reference comparisons; provenance index and status/limitations.

Seal inputs before run and raw data before analysis. Preserve raw original decimal tokens. Save JSON/CSV schema versions and algorithm/evaluator hashes; verify monotonic times, duplicates, missing steps/correctors, finite numbers, units/stages and field/CSV consistency. SHA-256 manifest excludes its own file and records members exactly; never append retrospectively to formal seals. Report documents any baseline-vs-runtime-source identity limitation. Current read-only verification hashes 79 relevant pre-existing authorities/design/baseline files; it is a bounded preparation check, not a re-audit of unrelated repository history.

## 22. STOP conditions and no auto-tuning

Execution is blocked while U01–U04 or any required readiness field remains unresolved. Future mandatory STOP conditions: wrong Foundation version/model/runtime/library identity; formal/diagnostic hash mismatch; future input/hash/recipe mismatch; mesh/reference-cell/dimensionality mismatch; Ra/Pr mismatch (inherited Gate A recomputation tolerance 1e-10 relative); incorrect cold cell/patch initialization; incorrect backward scheme/history; wrong native Co controller or any unregistered cap; FPE, FatalError, non-finite field/term/residual/time/Co; non-positive rho or Δt; linear/nonlinear convergence failure; evaluator/term identity/units/sign/stage failure; incomplete/corrupt/non-monotonic evidence; unexpected source/constraint/moving mesh; inadequate storage; unregistered numerical or physical setting changes. At maximum physical duration without arrival stop with STEADY_NOT_REACHED, not an invented convergence PASS.

No hard mass/energy accuracy PASS threshold exists yet. Finite residuals or positive density alone do not establish scientific adequacy. Resolve evaluator identity/floor policy and arrival role before RUN; inability to evaluate a required term is an immediate STOP, never a reason to omit it. Native maxCo is a control target: a specific overshoot/underflow policy remains U02 rather than being invented during execution.

No relaxation/tolerance/corrector/maxCo/maxDeltaT/time-scheme/mesh/physics tuning after observing a result. Changes require a separately preregistered **diagnostic** revision, retaining failures and original data; no formal amendment or criteria relaxation.

## 23. Temporal comparison and conditional third series

Primary nonzero final scalar difference is fixed here because AC §12 and the prerequisite review leave its denominator unspecified:

\[
D_t(Q)=\frac{|Q_{fineCo}-Q_{coarseCo}|}{|Q_{fineCo}|}.
\]

Lower maxCo supplies the comparison reference because it is the intended finer temporal control; this is a directional diagnostic convention, not proof of greater accuracy. Compare time-weighted confirmed final-window means of Nu_bar_cavity/Umax/Wmax. A zero fine value gives an undefined relative difference (store null and absolute difference); absent steady arrival or invalid inner/evaluator evidence blocks this comparison and demands review, not a forced third series.

For valid 0.5 vs 0.25 final windows, **any D_t>0.005 triggers the future independent Co0.125 cold-start series** under the same frozen diagnostic settings and a future authorized task. Equality 0.005 meets the diagnostic target. Report all quantities and compare the two finest valid series if the third is added. If 0.25/0.125 still exceeds it, label diagnostic target unmet; no automatic fourth series or tuning. This never produces Gate J PASS.

Save absolute/dimensionless steady-arrival time differences, relative arrival difference only when the fine time is nonzero, signed/absolute drift and mass/energy residual-scale differences. Across matched intervals save duration-weighted RMS, L1, Linf and signed-integral statistics of already normalized mass/energy residuals; evaluate C/assembly/end quantities separately, not a single combined score. Do not select the normalization after seeing results.

Trajectories are aligned by t* over the shared valid interval. Fix comparison nodes as the sorted union of raw sample t* values in that interval, using piecewise linear interpolation with no extrapolation. Save both native grids and interpolated values and mark them; this is comparison only and never used to fabricate discrete conservation residuals. Report differences for Nu/U/W, mass, E_int/E_kin, normalized residuals and stage jumps; retain extrema in native histories. No numerical interpolation spacing is chosen after results.

Two Co targets cannot identify order2. Even with a third, adaptive dt ratios, cap-dominated startup, first-order start and nonlinear/inner effects preclude automatic Richardson/observed-order claims. Actual h distributions and refinements must support any later temporal-order analysis in a separate review.

## 24. Interpretation limits

Permitted result language after a valid future study: evaluated time-step sensitivity between the specified native Courant controls on the fixed 160² Route A grid. Do not claim grid-independent transient solution, fully verified transient solver, classical-Boussinesq transient validation, full Verification, Route A characterization completion, formal Gate J PASS, FSI validation or particle readiness. Table V is a steady reference, not a transient trajectory reference. Both Co controls may share spatial/model/evaluator errors.

## 25. Future formal Gate J relationship

Formal J stays not executed/not evaluated/not allowed. This study neither executes, bypasses nor relaxes its prerequisites. No automatic promotion is allowed. If prerequisites later become satisfied, reuse of diagnostic evidence requires a new explicit formal authority/provenance/scientific review; no promised rerun waiver. Formal v1.7 and AC remain read-only.

## 26. Future particle/FSI relationship and preparation decision

Potential later evidence: fluid time-step/controller behavior, startup, steady arrival, density synchronization, mass and energy trajectory. Particle forces, particle heat transfer, moving-interface resolution and coupling stability remain untested. Particle and downstream readiness stay NO even if the future diagnostic succeeds.

Blocking work, limited to this contract:

| ID | Missing item and why it cannot be inferred | Required closure without running a solver |
| --- | --- | --- |
| U01 | Complete transient corrector counts, linear/maxIter/relaxation settings, nonlinear error budget and fail rule. Source defines algorithm/syntax but no study-specific adequacy; steady Gate D is a different error test. | Source-grounded numerical design, component-wise criterion, maximum correction budget, unrelaxed defects and justified separation from temporal sensitivity; freeze all dictionary values and failure handling. |
| U02 | Initial Δt, finite maxDeltaT and actual-Co overshoot/underflow policy. Cold Co=0 imposes no startup accuracy bound. | Grounded startup/diffusion-resolution cap and paired controller plan with actual cap accounting; explicit numeric physical-time settings, resource estimate and failure rules. |
| U03 | Minimum/maximum t*, physical arrival windows, drift/range/confirmation policy and mass/energy role. Source/time scale does not predict nonlinear steady-arrival duration. | Fix a defensible physical-duration/arrival protocol and equal-duration final windows, cap outcome and criteria before examining any transient result; no steady-iteration-to-seconds conversion. |
| U04 | Mechanism and evidence verification for constructor and in-loop rho/energy/matrix/reference observations; native end-step function objects do not expose these stages. | Specify a supported read-only observation/evaluation method with no change to equations/order/relaxation; exact matrix actions and snapshots; synthetic algebra tests and floor policy. If runtime instrumentation is required, preregister implementation authority and pin its source/binary separately before RUN. No /opt edits/builds in preparation. |

`MASS_ENERGY_HARD_THRESHOLD=UNRESOLVED` is acceptable as a diagnostic design state, but neither substitutes for U04 evaluator/failure closure nor establishes technical readiness. Do not invent 1e-6/1e-4/1% conservation limits.

Preparation creates this v1.0 and seals its resolved definitions and blockers. `DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED=CONDITIONAL`, `DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY=NO`, `NEXT_SINGLE_TASK=FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT`. No RUN next task is authorized by this document. Future exact-task recommendation follows the user request: gpt-6.1-sol / medium; USER_DECISION_REQUIRED=YES.

## Appendix A. Source → equation → evaluator → saved evidence

All paths below are relative to the pinned `/opt/openfoam13` unless stated otherwise. JSON stores the full paths, line anchors and SHA-256. Anchors identify inspected blocks, not a claim that one line contains every formula.

| Source and anchor | Discrete equation / behavior | Diagnostic operator | Saved evidence |
| --- | --- | --- | --- |
| applications/solvers/foamRun/foamRun.C:125 | preSolve/adjust/time/outer/post/write sequence | stage/time labels and observation boundaries | stage event log, time index |
| applications/solvers/foamRun/setDeltaT.C:34 | initial cap and native growth cap | registered min/cap decision | previous h, new h, cap reason |
| applications/modules/fluidSolver/fluidSolver.C:106,229 | cell-density Courant formula and maxDeltaT | exact native formula before and after step | Co_mean/max_control/end, actual h |
| src/finiteVolume/solver/solver.C:38,83 | deltaTFactor default/read | explicit 1.2 guard | input/decision provenance |
| applications/modules/isothermalFluid/isothermalFluid.C:330,387 | first density predictor and postSolve EOS assignment | stage masses and oldTime identity | M_C, M_end, rho jumps |
| applications/modules/isothermalFluid/correctDensity.C:35 | fvm ddt(rho)+fvc div(phi)=0 | BDF2+native face sum, local/global defect | mass storage/flux/R_C/R_end |
| applications/modules/isothermalFluid/correctBuoyantPressure.C:180,226 | pressure projection, psi correction, continuity solve | pre-reference pressure compatibility and corrected phi | reference-cell contribution, phi, rho stages |
| src/finiteVolume/fvMatrices/fvMatrix/fvMatrix.C:562 | pressure-reference diagonal/source addition | pre/post-reference equation actions | raw physical and referenced defects |
| applications/modules/fluid/thermophysicalPredictor.C:34 | rho e/rho K transport, pressure/gravity, divq | unrelaxed EEqn action at its assembly state | E storage, all term actions, R_E,assembly |
| applications/modules/isothermalFluid/momentumPredictor.C:36 | rho-weighted momentum and K update | stage K/U and source identity | U/K epoch hashes and ranges |
| src/ThermophysicalTransportModels/fluid/laminar/Fourier/Fourier.C:99,130 | q and explicit/implicit divq | exact term matrix/face flux | wall Q, correction term, H_out |
| src/finiteVolume/finiteVolume/fvm/fvmLaplacian.C:370 | uncorrected laplacianCorrection | retain correction source/coefficient reference | conduction assembly action |
| src/finiteVolume/fvMatrices/fvMatrix/fvMatrixSolve.C:348 | residual includes boundary terms, b−Aψ | negate and distinguish volume-integrated units | signed unrelaxed/relaxed residual |
| src/functionObjects/field/wallHeatFlux/wallHeatFlux.C:62,256 | reports −q, integrated area Q | inward-positive heat convention | Q_hot, Q_cold and physical Nu |
| src/finiteVolume/finiteVolume/ddtSchemes/backwardDdtScheme/backwardDdtScheme.C:59,149,279,518 | startup and variable-step rho-weighted BDF2 | exact native coefficients/old products | startup order, h/k, storage |
| src/thermophysicalModels/specie/equationOfState/Boussinesq/BoussinesqI.H:75,137 | rho(T), psi=0 | independent algebraic EOS check | rho_T, psi, EOS defect |
| src/thermophysicalModels/specie/thermo/eConst/eConstThermo.C:39 | Cv/Tref/esRef defaults | retain energy-reference provenance | e/E_int and anomaly correction |
| src/thermophysicalModels/basic/rhoFluidThermo/rhoFluidThermo.C:57,64 | separate thermo density and correctRho | expose both density identities | rho_s/rho_T stage records |
| applications/modules/fluidSolver/fluidSolver.C:174 | transient density-discrepancy continuity log | reproduce signed/local discrepancy | native global/local/cumulative with indices |
| src/finiteVolume/cfdTools/general/solutionControl/pimpleControl/pimpleLoop/pimpleLoop.C:69 | final extra iteration / cap behavior | convergence event vs actual iterations | convergence/STOP evidence |
| src/finiteVolume/cfdTools/general/solutionControl/convergenceControl/singleRegionCorrectorConvergenceControl/singleRegionCorrectorConvergenceControl.C:40,182 | outerCorrectorResidualControl and initial residual checks | retain component/solve-index semantics | complete initial/final/iteration stream |
| Repository Scripts/routeA/analyze_case.py:256,347,449 | paper Nu,4097 extrema,reconstructed div(U) | reuse mathematical definitions only | same-definition primary QoIs/epsilon_v |

## Appendix B. Preparation scope attestation

SOLVER_EXECUTED=NO; CASE_GENERATED=NO; MESH_GENERATED=NO; INITIALIZATION_EXECUTED=NO; DIAGNOSTIC_TRANSIENT_EXECUTED=NO; FORMAL_GATE_J_EXECUTED=NO; GRID_320_EXECUTED=NO; ROUTE_B_RERUN=NO; PARTICLE_COUPLING_STARTED=NO. FORMAL_ROUTE_A_CONTRACT_CHANGED=NO; ACCEPTANCE_CRITERIA_CHANGED=NO; FORMAL_STATUS_CHANGED=NO; FORMAL_GATE_J_AUTHORIZED=NO. No git add/commit/push; no modification of existing cases, formal seals, /opt source or binaries.
