# DiagnosticTransient contract fix v1.1

1. **Overall: INCOMPLETE.** U01–U03 CLOSED; U04 actual native observation/export binding remains UNRESOLVED. No CFD case or production solver build/run.
2. **Parent verified:** v1.0 SHA `3ea8c134b1c0468a455c8d090eb3b47dae510b06a9886eedbaa5f79aed8e152f`; formal v1.7 SHA `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60`. HEAD matches74b1f7b2c0e844ac559997277ce30dde2450b3f8. Both immutable.
3. **U01:** fixed PIMPLE24outer/2pressure/0nonorthogonal; explicit normal/Final solver entries; no under-relaxation; fixed cap/failure policy.
4. **Numerical rationale:** terminal4 state/QoI changes<=1e-7 with contraction<=0.5 or arithmetic-floor plateau; conditional local tail proxy<=5e-5,100times below0.5% target. Linear residual is separate. This does not prove global accumulated trajectory error.
5. **U02:** inputdeltaT=2.3111979166666666e-05s; firstphysicalh=2.7734374999999998e-05s; maxh=.027734375s; native1.2growth; finite achieved-Co overshoot recorded; timestamp floor64ulp;2M-step resource cap.
6. **Scales:** existing mesh verifiesdx=.000625m; cellthermal=.027734375s/globalthermal710s; accepted speedchar=.03113211708m/s implies prospective Co h=.00710/.00355/.00177s. Fo0.001 balances illustrative Euler startup accuracy/cost. No new transient data.
7. **U03:** t*=t/710s; minimum.5/max2;71s windows,3disjoint; range<=5e-5,halfdrift<=2.5e-5,OLSspan<=5e-5; primary final last-window physical-time mean. Conservative native endTime1419.972265625s prevents overshooting1420s; no extension.
8. **U04 implementation:** native matrix-copy/sign/volume adapter, native synthetic operator tests,offline evidence checker and14-site exact-source observation plan. Adapter verified; actual hooks/term exporter not connected.
9. **Tests:**75native checksPASS,12policy testsPASS,14source anchorsPASS,repeat summaries identical. Stationary synthetic mass/energy observed0; storedmatrix bounds5.86198e-13kg/s/1.08447e-9W;4manufactured linear matrix solves max8.88178e-16W. These are synthetic numerical floors, not CFD accuracy. The diagonal native residual test initially aborted; private zero-offdiagonal scratch repair passed. No production attempt.
10. **Threshold:** OptionB DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION. Mandatory mass/energy evidence,validity,stationarity and explicit conservation-concern review; no hard numerical conservationPASS invented.
11. **New contract:** [`routeA_diagnostic_transient_contract_v1.1.md`](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.1.md), [`JSON`](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.1.json), [`SHA sidecar`](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.1.sha256). JSON SHA `574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675`. Full source line/function/hash mapping is in JSON;19parent sections unchanged.
12. **Readiness:** scientificallyCONDITIONAL/technicallyNO; formalJ remainsNO/NOT_EVALUATED; core/downstream/particleNO, allF FAIL/allneeds320YES. 86protected files and24native sources unchanged bySHA.
13. **Remaining:** actual source-stage/oldTime/BC epoch binding; safe single-assembly terms and coefficient exporter; isolatedoverlay; complete synthetic driver/export/replay and failure-propagation verification. Default final outputs cannot substitute these.
14. **Exact next:** FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT, U04 only; preserve registered U01–U03. No execution authorization follows from this incomplete revision.

Source facts/engineering choices and mathematical detail: [v1.1 contract](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/docs/routeA_diagnostic_transient_contract_v1.1.md).
Implementation: [observer](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/v1_1/NativeMatrixObserver.H), [stage plan](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/v1_1/instrumentation_stage_plan.json).
Evidence: [unit summary](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/v1_1_unit_verification/unit_verification.json), [native log](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/v1_1_unit_verification/test.log), [policy log](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/v1_1_unit_verification/policy_tests.log).
Reproduce stand-alone tests: run `/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/diagnostic_transient/v1_1/run_unit_verification.sh` with a fresh output directory under /tmp. No production solver or case utility is invoked. The binary is ephemeral; source/compiler/runtime and binary SHA are pinned in logs/report.

Formal source mirrors used as supplemental interpretation checks:
[pressure stages](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/applications/modules/isothermalFluid/correctBuoyantPressure.C),
[native matrix residual](https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-13/master/src/finiteVolume/fvMatrices/fvMatrix/fvMatrixSolve.C).
Local SHA-pinned sources are the authority.

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_CONTRACT_FIX = INCOMPLETE
STUDY_OWNERSHIP = DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION
PARENT_DIAGNOSTIC_CONTRACT_VERSION = 1.0
PARENT_DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
PARENT_DIAGNOSTIC_CONTRACT_SHA256 = 3ea8c134b1c0468a455c8d090eb3b47dae510b06a9886eedbaa5f79aed8e152f
FORMAL_ROUTE_A_CONTRACT_VERSION = 1.7
FORMAL_ROUTE_A_CONTRACT_CHANGED = NO
U01_STATUS = CLOSED
TRANSIENT_ALGORITHM = PIMPLE fixed24 outer;2 pressure;0 nonOrthogonal; momentumPredictor=yes;simpleRho=no;transonic=no;consistent=no; no native early residual termination
N_OUTER_CORRECTORS = 24
N_CORRECTORS = 2
N_NON_ORTHOGONAL_CORRECTORS = 0
LINEAR_SOLVER_POLICY = U/e:PBiCGStab/DILU tol1e-12 maxIter2000;p_rgh:PCG/DIC tol1e-12 maxIter4000;rho:diagonal tol1e-14 maxIter1;all relTol0 and explicit identical Final entries
RELAXATION_POLICY = Empty relaxationFactors fields/equations; omit all field/equation/Final entries: equation factor0/no-op, field/density/pressure factor1/no under-relaxation; do not specify equation factor1
INNER_CONVERGENCE_RULE = Every solve final normalized native residual <=1e-12 (rho<=1e-14),relTol=0 and fixed maxIter; all8 terminal outer changes(k21..24)<=1e-7, each contracts q<=0.5 or all lie at registered floating floor; conditional tail<=5e-5; otherwise STOP_NO_RETRY
ITERATIVE_ERROR_BUDGET_JUSTIFIED = YES
U02_STATUS = CLOSED
INITIAL_DELTA_T = 2.3111979166666666e-05
MAX_DELTA_T = 0.027734375
MIN_DELTA_T = 64*ulp(max(abs(t_seconds),710 seconds)); t+h>t required
DELTA_T_GROWTH_FACTOR = 1.2
CO_OVERSHOOT_POLICY = Record-only for finite achieved Co under exact native controller law; control/end Co separate; all excursions flagged; law/hash/nonfinite failure STOP; no achieved-Co upper bound
U03_STATUS = CLOSED
DIMENSIONLESS_TIME_DEFINITION = t*=alpha0*t/L^2=t/(710 s)
MINIMUM_T_STAR = 0.5
MAXIMUM_T_STAR = 2.0
ARRIVAL_WINDOW_T_STAR = 0.1
CONFIRMATION_WINDOW_COUNT = 3
QOI_RANGE_CRITERION = (max-min)/max(abs(time-weighted mean),1)<=5e-5 for Nu_bar_cavity,Umax,Wmax
QOI_TREND_CRITERION = abs(secondHalfMean-firstHalfMean)/denom<=2.5e-5 AND abs(continuous OLS slope)*W/denom<=5e-5
FINAL_VALUE_DEFINITION = Time-weighted piecewise-linear mean in last confirmed71s window; same duration per Co; also save endpoint/range/OLS/half drift
MASS_ENERGY_HARD_THRESHOLD = DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION
U04_STATUS = UNRESOLVED
EVALUATOR_IMPLEMENTATION = Native C++ deep fvScalarMatrix observation adapter + native operator synthetic tests + offline policy/StageLedger; stage/export overlay DESIGN_ONLY_NOT_CONNECTED
ASSEMBLY_STAGE_CAPTURE = NO
MASS_EVALUATOR_UNIT_TEST = PASS
ENERGY_EVALUATOR_UNIT_TEST = PASS
STAGE_IDENTITY_TEST = PASS
UNITS_SIGN_TEST = PASS
EVALUATOR_FLOOR_CHARACTERIZED = YES
SYNTHETIC_EVALUATOR_TESTS_EXECUTED = YES
DIAGNOSTIC_CONTRACT_CREATED = YES
DIAGNOSTIC_CONTRACT_VERSION = 1.1
DIAGNOSTIC_CONTRACT_SHA256 = 574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = CONDITIONAL
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
SOLVER_EXECUTED = NO
PRODUCTION_SOLVER_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
DIAGNOSTIC_TRANSIENT_EXECUTED = NO
GRID_320_EXECUTED = NO
ROUTE_B_RERUN = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_STUDY_CONTRACT
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
FIRST_PHYSICAL_DELTA_T = 2.7734374999999998e-05
EVALUATOR_FLOOR_SCOPE = SYNTHETIC_STORED_MATRIX_SUMMATION_AND_LINEAR_SOLVE_ONLY;CFD_floor_not_measured
SYNTHETIC_LINEAR_MATRIX_SOLVES = 4
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
PARTICLE_COUPLING_STARTED = NO
```

Unit compiler/library provenance: [build_runtime_provenance.json](/home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/v1_1_unit_verification/build_runtime_provenance.json).20linked libraries SHA-pinned; synthetic nominal case directory does not exist.

Final git status: only newly created diagnostic files plus existing untracked cases/verification; tracked diff and staged diff empty. No git add/commit/push.
