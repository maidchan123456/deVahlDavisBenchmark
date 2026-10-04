# Route A diagnostic transient contract v1.1

**INCOMPLETE: U01/U02/U03 CLOSED; U04 UNRESOLVED. No execution authority.**

Ownership: `DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION`.
This is an independent diagnostic contract fix, not formal Amendment008 or v1.8.
Parent v1.0 JSON SHA256: `3ea8c134b1c0468a455c8d090eb3b47dae510b06a9886eedbaa5f79aed8e152f`.
Formal v1.7 JSON SHA256: `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`.
Version1.1 JSON SHA256: `574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675`. Companion `.sha256` is authoritative.
Parent files and formal/historical artifacts remain immutable.

The JSON retains the complete parent contract. Parent physical problem, governing
equations, mesh, cold initialization, spatial/backward scheme, Co series/conditional
third rule, dimensional time, QoIs, mass/energy operators and normalization,
thermo-synchronization definitions, cadence, restart, evidence namespace,
comparison0.5% target and claim boundaries remain unchanged. Its
`revision_invariants.unchanged_parent_sections` lists19 byte-structure-equal sections.
This document registers only U01–U04 decisions. Source facts are distinguished from
engineering choices. No new transient observations informed any parameter.

## U01 — CLOSED numerical policy; native observer binding depends on U04

Use native foamRun/fluid PIMPLE: **24 fixed outer corrections,2 pressure corrections
per outer,0 nonorthogonal corrections**. `momentumPredictor yes; simpleRho no;
transonic no; consistent no; hydrostaticInitialisation no; correctPhi no`.
Inherited transport prediction first/correction final remains. Native
`outerCorrectorResidualControl` and end-run residual controls are omitted.
`runTimeModifiable no`. Native early residual exits are not a nonlinear certificate.

Source RUN/PIMPLE/OUTERRES/RHOMODE/ENERGY/PRESSURE/RHOSTAGES/EOS shows that one outer
is PISO-like pressure correction with lagged energy/momentum coefficients.
Pressure corrections do not re-solve the coupled thermal state. Boussinesq psi=0
cannot fix EOS mass using a pressure offset; thermo/EOS assignments and continuity
stages must be observed independently. Multiple outer corrections therefore allow
coupled convergence to be tested.24 is a **finite engineering work budget**, not a
prediction that24 iterations always converge. Two pressure solves refresh phi/U/K
within each outer; orthogonal inherited mesh requires no nonorthogonal correction.
Worst case per physical step:24 momentum/energy solves,48 pressure solves,49 density
solves. Greater cost buys measurable iterative isolation; exhaustion stops the series.

| Field (and identical explicit Final entry) | Solver | Preconditioner | tolerance | relTol | maxIter |
|---|---|---|---:|---:|---:|
| U/UFinal | PBiCGStab | DILU |1e-12|0|2000|
| e/eFinal | PBiCGStab | DILU |1e-12|0|2000|
| p_rgh/p_rghFinal | PCG | DIC |1e-12|0|4000|
| rho/rhoFinal | diagonal | none |1e-14|0|1|

PCG is suitable for the registered symmetric pressure diffusion matrix;
asymmetric advective momentum/energy use PBiCGStab. Native residuals are normalized
linear residuals, not physical conservation errors. Log every component solve
(Ux,Uy,e,p_rgh,rho), initial/final residual, iteration and full stage indexes;
final residual must meet the registered absolute normalized tolerance and iteration
cap. `relTol0` prevents accepting a merely relative reduction. No relaxed Final policy.

**No under-relaxation:** empty `relaxationFactors { fields {} equations {} }`;
omit all field/equation/Final entries. Native matrix relaxationFactor then returns0,
so matrix relax is a no-op. Native field/density/pressure factors default1.
**Do not specify equation relaxation1:** native `fvMatrix::relax(1)` still enforces
diagonal dominance and changes coefficients/source. No relaxation allows matrix
observations to retain governing action and avoids damping disguising outer changes.
It can make contraction harder; failure triggers STOP, never a relaxation retry.

Observe matched outer completion epochs at all24 corrections. Hard observables:
U,T,p_rgh,rho_s,rho_T,Nu_bar_cavity,Umax,Wmax. Save global/local C/end mass and
assembly/end energy defects and their changes as diagnostics, not invented hard
conservation tolerances. The metric normalization is:

- U: infinity change/max(current U infinity,alpha0/L).
- T: infinity change/DeltaT (or e change/(Cv*DeltaT)); never divide by300K.
- p_rgh: infinity change/max(current infinity,rho0*Uchar²), Uchar=0.031132117082250315m/s.
- rho_s/rho_T: infinity change/(rho0*beta*DeltaT)=change/0.001kg/m³.
- Primary QoI: absolute change/max(abs(current QoI),1).

All four terminal transitions k21..24 must be finite and<=1e-7 individually.
For each observable, either all3 terminal ratios contract by<=0.5, or all4 changes
are at/below the fixed stored-arithmetic floor. Conservative local tail proxy
2*lastChange (contracting branch) or4*floor (plateau branch) must be<=5e-5.
The exact field/QoI roundoff floor formulas, including Nu reduction and temperature
subtraction, are in JSON `inner_convergence.roundoff_floor`; floor>1e-7 stops the
certificate as unresolvable. Never replace a large nonlinear change by a small
linear residual. No native convergence-control OR criterion is reused here.

The primary0.5% target is0.005; iterative budget5e-5 is100times smaller, and change
threshold1e-7 is budget/500. Required observed contraction gives a geometric-tail
proxy well below this budget. This is a **conditional local fixed-point certificate**,
not a theorem about accumulated trajectory error, nonnormal amplification or
unobserved modes. Report this limitation when interpreting Co differences.24 outer
is accepted only when the certificate actually passes. Any linear/nonlinear failure
=>`NONLINEAR_CONVERGENCE_FAILURE`/linear failure, retain invalid data and STOP;
no corrector increase, dt recovery, relaxation/tolerance tuning or continuation.

## U02 — CLOSED cold-start/native controller

Existing accepted ASCII `constant/polyMesh/points` has51842points and161×161×2
coordinate planes; owner header has25600cells. Read-only spacing checks give
dx=dy=0.000625m, width0.001m, bounds[0,0.1]×[0,0.1]×[0,0.001]. This agrees with
blockMeshDict160×160×1; no blockMesh/checkMesh ran. Mesh evidence paths/hashes
are in JSON `courant_control.mesh_evidence`.

alpha0=1.4084507042253522e-5m²/s; t_cell=dx²/alpha0=0.027734375s;
t_global=710s. Existing accepted steady maximum dimensionless speed221.0380313
only supplies a **prospective scale**, Uchar=0.03113211708m/s, global advective
3.212116919s and cell advective0.02007573074s. Steady iteration9000 is never seconds.

| First-step Fo candidate | First physical h (s) | Illustrative first Euler heat-mode relative defect |
|---:|---:|---:|
|0.01|0.00027734375|0.00304358118|
|**0.001 chosen**|**0.000027734375**|**0.0000318308574**|
|0.0001|0.0000027734375|0.000000319829487|

For a uniform2D reference heat stencil lambda_max<=8alpha/dx², first-step Euler
mode defect exp(z)/(1+z)-1, z=8Fo. Middle choice lies below illustrative5e-5 local
budget without10times more tiny initial steps. This is a startup resolution rationale,
not a full coupled boundary-jump error guarantee. First order startup is retained
from native backward when history is missing. Acceleration scale beta*DeltaT*|g|
=0.1408450704m/s² gives first-step speed scale3.90625e-6m/s; coldCo=0 cannot choose h.
No explicit Fourier stability bound is imposed on the implicit method.

**Preregister controlDict deltaT=2.3111979166666666e-05s**.
Source RUN/DT shows preSolve then adjustDeltaT before the first time increment:
coldCo=0 still gives1.2growth. Thus **first physical h=2.7734374999999998e-05s**.
Use both values identically for Co0.5/0.25/conditional0.125.
Finite **maxDeltaT=0.027734375s (Fo1)** prevents uncontrolled near-zero-Co growth;
it is a temporal-resolution cap, not permission for arbitrarily large implicit steps.
If Co stays inactive the cap is reached after38 growth steps.

Native law: h_new=min(1.2h_old,maxDeltaT,maxCo*h_old/Co_control whenCo_control>small).
Pinned Foundationv13 DP `small` is DBL_EPSILON=2.220446049250313e-16, **not a presumed
legacy1e-15**. No model/functionObject/write-alignment/other cap allowed. Verify h
against this law within64eps*max(abs(observedh),abs(expectedh)); unexpected caps stop.
Record prior-state controlCo and achieved end-stateCo independently. **Finite
achieved-Co overshoot is record-only** when native law/fields are valid; no numerical
achievedCo ceiling. Record every excursion, maximum, count and physical duration;
never claim targetCo is an achieved bound. Nonfinite/negative Co or controller
identity failure STOP. No post-hoc tolerance or recovery controller.

Prospective uniform-grid flux bound h≈Co*dx/(sqrt(2)*Uchar) gives0.007097843,
0.003548921,0.001774461s, below maxDeltaT; this suggests different later timesteps
but is not transient evidence. Save cap-active counts AND duration fractions,
actual h distributions and Co histories. If controls produce nearly identical h,
report uninformative control sensitivity; do not alter the registered cap.

Minimum h=64*ulp(max(abs(t_seconds),710seconds)); h>0, finite and t+h>t required.
This is timestamp representability, not physics stability. Stagnation/underflow STOP.
Resource watchdog2,000,000steps=>RESOURCE_LIMIT_REACHED, separate from scientific
arrival cap; no automatic extension. Future disk preflight must use the inherited
full-fields-every-step and internal-stage evidence volume; no cadence change here.

## U03 — CLOSED arrival/duration/final statistic

Keep t*=alpha0*t/L²=t/710s. Minimum t*=0.5 (355s); maximum t*=2 (1420s).
Source TIME_END tests t<endTime-0.5storedh before the next native adjustment.
**controlDict endTime=1419.972265625s=1420-maxDeltaT**, so any next native step stays
below1420. Last raw endpoint can be slightly short of2; no output alignment or dt
modification. No qualifying arrival by native cap =>STEADY_NOT_REACHED; no extension.

Window W*=0.1 (71s),3 consecutive **nonoverlapping** windows. Candidate endpoints
m*0.1, integer m>=5. At endpoint E, confirmation covers[E-0.3,E-0.2],
[E-0.2,E-0.1],[E-0.1,E] in t*. Native raw histories must bracket all endpoints;
no extrapolation. Earliest valid candidate is arrival. First possible E=0.5.

For Nu_bar_cavity/Umax/Wmax, denom=max(abs(time-weighted window mean),1):
range/denom<=5e-5 AND abs(second-half mean-first-half mean)/denom<=2.5e-5
AND abs(continuous OLS slope)*W*/denom<=5e-5, in each of all3 windows.
Exact piecewise-linear integrals and centered continuous-time OLS preserve
nonuniform-step physical weighting. No smoothing or step-average replacement.

Supporting rho_min/max/mean,total_mass,energy_storage must also be stationary
with these range/trend fractions, using deviation-from-initial-state denominators
and perturbation floors0.001kg/m³,1e-8kg,0.01J respectively. Raw conserved
functionals retain the original reference; centering is for stationarity only.
All raw diagnostic fields finite; evaluator/inner/stage identities valid; no
unexplained jump or sync failure. Known EOS assignment jumps must reconcile with
captured native C/end histories and exact source-defined identities.
Mass drift,C/end residual; energy assembly/end residual,hot/cold heat,work,
kinetic/storage terms remain mandatory signed/local diagnostics and review inputs.

Pure reference conduction tau=710/pi²=71.938s; minimum/cap are4.93/19.74 reference
e-folds. W≈tau and≈22accepted-reference bulk transits;3windows require213s persistence.
These are engineering horizons, not a promise that convection/EOS actually settles.
Range5e-5 is1/100 of primary temporal target, limiting final-averaging ambiguity;
trend and repeated disjoint windows reject isolated flat intervals.

Primary final value =time-weighted mean in **last confirmed71s window**, equal
physical duration in each series. Save endpoint,range,OLS slope,half-mean drift and
candidate/history interval. Whole-run averages are prohibited.

**Option B: MASS_ENERGY_HARD_THRESHOLD=
DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION.** No invented hard conservation
accuracy tolerance. Validity and state stationarity are hard requirements, not an
R_M/R_E accuracy PASS. Persistent signed/global and local defects, cancellation,
EOS mass jumps, referenced pressure compatibility and evaluator floors must be
plotted and interpreted. A stationary state with a large constant defect can be
`arrival_with_conservation_concerns`; never mass/energy conservation PASS. QoI
agreement or assigned postSolve rho does not waive these concerns.

## U04 — UNRESOLVED runtime wiring; tested native adapter

Implementation: `Scripts/routeA/diagnostic_transient/v1_1/NativeMatrixObserver.H`
plus native matrix/operator unit tests, offline policy and StageLedger, and an
exact-source `instrumentation_stage_plan.json`.14 anchor checks pass on the pinned
native source. The plan records constructor, density predictor, pre-relax EEqn,
post-energy/pre-thermo, post-thermo, pressure EOS copy,pre/post pressure reference,
correctDensity,continuity C,pre/post postSolve and final driver stages.
**These are planned observation sites; hooks/exporter are not connected.**

Adapter deep copies native scalar matrix diagonal/offdiagonal/source/boundary
coefficients and validates dimensions/StageId. Native `residual=b-Apsi` is negated.
Matrix actions are already cell-integrated kg/s orW; explicit field rates multiply
V once; local norms divide byV and global signed/absolute sums use extended-precision
Neumaier accumulation. On a purely diagonal matrix native residual requests missing
lower/upper arrays: allocate zeros in a private scratch only. Actual governing
matrix remains unchanged. Stage metadata includes time/index,outer,pressure,
energy_solve,stage,oldTime IDs,h/h_previous. StageLedger detects malformed IDs,
duplicate/missing/reordered records. It does not bind fake IDs to native field epochs.
The snapshot intentionally retains LIVE psi for evaluation after solve: evaluate
before later BC/field epochs change. It is not a persistent full-state snapshot.
Serial uncoupled-only scope matches the inherited one-process plan.

Standalone build links native finiteVolume/OpenFOAM libraries; creates1/2-cell
polyhedra and Time in memory, no case/mesh write, no thermo or CFD module. It advances
synthetic Time solely to install h/k for manufactured BDF tests, not a CFD evolution.
Four manufactured1/2-cell linear matrix solves characterize evaluator arithmetic
floors:1-cell native diagonal shortcut;2-cell PCG/DIC andPBiCGStab/DILU; **no production solver build/run**.

Final results: **75 native checks PASS,12 policy tests PASS,14 source anchors PASS**.
Repeated native summaries identical (17 significant digits). Native checks cover
actual BC/source residual sign,nonuniform volume/no doubleV,deep frozen coefficients,
updated psi,dimensions/nonfinite/stage failures,internal flux cancellation/outward
sign,variable-step BDF rho/rho-e old products,all named energy signs/units,
Fourier explicit lag+native implicit correction and full termwise-vs-matrix identity.
Original matrix diagonal/source unchanged under observation. Native unit identity
maximum absolute defect7.105427357601002e-15 (mixed-unit checks, not one physical
conservation threshold). Policy tests cover first growth,caps,underflow,linear/outer
failure,physical-time weighting/OLS,arrival confirmation,runaway,mismatched stages.

| Synthetic floor measurement | Observed | Stored-matrix arithmetic bound |
|---|---:|---:|
| stationary rho storage (kg/s)|0|5.861977570020869e-13|
| stationary e storage (W)|0|1.084465850453861e-9|
| manufactured linear solve residual maximum (W)|8.881784197001252e-16|recorded separately from normalized solver residual|

Cancellation fixture[1e16,1,-1e16] returns1 under compensated sum; conservative
DBL-epsilon aggregation bound22.20446049 illustrates loss of precision in cancellation.
Do not subtract a measured floor from a residual. Per-stage future bounds use
gamma_m times sums of absolute stored matrix products,including boundaries, plus
aggregation allowance. These bound stored arithmetic only, not assembly,
conditioning or actual CFD error. Belowfloor=>unresolved_by_evaluator, abovefloor=>
detected algebraic defect; neither is a conservation scientific PASS/FAIL.

Remaining **material U04 blocker**: native stage/field/oldTime/BC epoch binding and
coefficient/term exporter, isolated source overlay, safe single-assembly term capture
without extra BC/history updates,complete synthetic native driver export/replay and
STOP propagation have not been implemented/verified. An end-field reader cannot
recover lagged assembly data. Actual ASSEMBLY_STAGE_CAPTURE=NO. Operator tests alone
cannot close this gap or prove CFD mass/energy conservation. Source/library overlay
and exporter hashes must be frozen after this verification before any future RUN.

## Source traceability and immutable authority

JSON `fix_source_traceability` provides local file, function/line anchors,SHA256,
source-to-equation fact and affected U-items. The14-site plan adds exact lexical
anchors and stage/payload choices. Counts,tolerances,Fo,horizons,contraction and
arrival fractions are explicitly **engineering decisions**; local source supplies
operator/control/order semantics,not those numbers. Accepted existing steady metrics
supply only scale evidence. Online primary source mirrors are supplemental:
[Foundationv13 pressure correction](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/applications/modules/isothermalFluid/correctBuoyantPressure.C),
[Foundationv13 matrix residual](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/src/finiteVolume/fvMatrices/fvMatrix/fvMatrixSolve.C).
Local pinned hashes, not a mutable online branch, govern this contract.

Formal GateJ currently allowedNO/executedNO/passNOT_EVALUATED; benchmark coreNO,
RouteA characterizedNO; downstream/particle readinessNO; allF FAIL/allneeds320YES.
Solver,case generation,mesh generation,initialization,diagnostic transient,320²,
RouteB andparticles **not executed**. No criteria,formal source,status or historical
artifact changes; no git add/commit/push. See contract-fix report for hashes and checks.

Next single task: **FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT — U04 only**.
Keep preregistered U01–U03 fixed. Scientific allowanceCONDITIONAL; technical readinessNO.
