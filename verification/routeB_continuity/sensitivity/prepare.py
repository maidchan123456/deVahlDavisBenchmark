#!/usr/bin/env python3
"""Prepare an isolated preregistered experiment, without running any solver."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = ROOT / 'results/routeB/gateG_sensitivity_experiment'
FOAM = Path('/home/mirai/OpenFOAM/OpenFOAM-6')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prepare():
    if (HERE/'experiment_preregistration_v1.json').exists():
        raise RuntimeError('Preregistration already exists; refusing to overwrite')
    RESULTS.mkdir(parents=True, exist_ok=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    assert head=='415376a5dca99638059b497e5ca46c44f1e36220',head
    protected=[ROOT/p for p in ['docs/acceptance_criteria.md','docs/benchmark_spec.md','Scripts/routeB/foam_fields.py','Scripts/routeB/analyze_case.py','results/routeB/gateG_conservation_error_budget_review.md','results/routeB/gateG_qoi_impact_quota_review.md','results/routeB/caseC_continuity_verification/verification_report.md']]
    provenance={'HEAD':head,'initial_git_status_before_new_work':'?? cases/routeA/Ra0_medium/\n?? cases/routeA/Ra1e4_coarse/\n?? verification/\n','preparation_git_status':status,'protected_hashes':{str(p.relative_to(ROOT)):sha(p) for p in protected}}
    (RESULTS/'startup_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    source=FOAM/'applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam'
    audit=HERE/'auditSolver';audit.mkdir()
    for p in source.iterdir():
        if p.is_file() and p.suffix in ('.H','.C'): shutil.copy2(p,audit/p.name)
    (audit/'Make').mkdir()
    shutil.copy2(source/'Make/options',audit/'Make/options')
    (audit/'Make/files').write_text('buoyantBoussinesqSimpleFoam.C\n\nEXE = $(PWD)/bin/buoyantBoussinesqSimpleFoamContinuitySourceAudit\n')
    old=HERE.parent/'auditSolver'
    shutil.copy2(old/'continuityAudit.H',audit/'continuityAudit.H')
    shutil.copy2(HERE/'steadyMonitor.H',audit/'steadyMonitor.H')
    p=audit/'pEqn.H';s=p.read_text()
    s=s.replace('        p_rghEqn.setReference', '''        const ContinuityAuditMatrix auditPhysical(p_rghEqn);
        // operator==(matrix, field) adds V*field to source (v6 fvMatrix.C:1458).
        // Target q=b0-A0*p=g, so solve with b0-g. No other matrix term changes.
        p_rghEqn.source() -= mesh.V()*continuitySource.primitiveField();
        const ContinuityAuditMatrix auditForced(p_rghEqn);
        p_rghEqn.setReference''')
    s=s.replace('        p_rghEqn.solve();','''        const ContinuityAuditMatrix auditAlgebraic(p_rghEqn);
        const scalar auditNp=auditAlgebraic.normalization();
        const solverPerformance auditPerformance=p_rghEqn.solve();
        const scalarField auditTrue=auditAlgebraic.trueResidual();
        const scalarField auditPhysicalTrue=auditPhysical.trueResidual();
        lastForcedResidual=auditForced.trueResidual();
        lastPhysicalResidual=auditPhysicalTrue;''')
    s=s.replace('            fvOptions.correct(U);','''            fvOptions.correct(U);
            writeContinuityAudit(auditOut,runTime,mesh,phi,U,pRefCell,
                auditNp,auditPerformance,auditTrue,auditPhysicalTrue);''')
    p.write_text(s)
    p=audit/'buoyantBoussinesqSimpleFoam.C';s=p.read_text()
    s=s.replace('#include "simpleControl.H"','#include "simpleControl.H"\n#include "continuityAudit.H"\n#include "steadyMonitor.H"')
    s=s.replace('    turbulence->validate();','''    turbulence->validate();
    volScalarField continuitySource(IOobject("continuitySource",runTime.constant(),mesh,
        IOobject::MUST_READ,IOobject::NO_WRITE),mesh);
    if(continuitySource.dimensions()!=dimless/dimTime)
        FatalErrorInFunction<<"continuitySource must have units 1/s"<<exit(FatalError);
    const bool monitorEnabled=runTime.controlDict().lookupOrDefault<bool>("steadyMonitorEnabled",true);
    const scalar pressureTolerance=runTime.controlDict().lookupOrDefault<scalar>("auditPressureTolerance",1e-10);
    SensitivityMonitor sensitivityMonitor(runTime);
    scalarField lastForcedResidual(mesh.nCells(),0.),lastPhysicalResidual(mesh.nCells(),0.);
    std::ofstream auditOut((runTime.path()/"continuityAudit.csv").c_str());
    auditOut<<"iteration,cell_count,Np,R_initial,R_recursive,linear_iterations,converged,true_residual_L1,R_true,recursive_residual_L1,abs_L1_norm_drift,true_nonreference_L1,true_reference_residual,physical_reference_residual,q_reference,mapping_defect_L1,mapping_defect_max,sum_abs_q,max_abs_q,mean_abs_div_phi,max_abs_div_phi,P95_abs_div_phi,P99_abs_div_phi,signed_volume_mean_div_phi,net_boundary_flux,Up,Kp,epsilon_phi_mean,epsilon_phi_max,ratio_recursive,ratio_true,native_sum_local,native_global,reference_cell,max_cell_id,max_cell_x,max_cell_y,max_cell_z\\n";''')
    s=s.replace('        runTime.write();','''        if(monitorEnabled && sensitivityMonitor.check(runTime,mesh,U,T,phi,pressureTolerance))
        {
            Info<<"SENSITIVITY_STEADY_CONFIRMED"<<nl;
            runTime.writeAndEnd();
        }
        runTime.write();''')
    s=s.replace('    Info<< "End\\n" << endl;','''    std::ofstream cells((runTime.path()/"sourceCells.csv").c_str());
    cells<<"cell,g,V,physical_residual,forced_residual,X,Z\\n";
    forAll(mesh.V(),i) cells<<std::setprecision(17)<<i<<','
        <<mesh.V()[i]*continuitySource[i]<<','<<mesh.V()[i]<<','
        <<lastPhysicalResidual[i]<<','<<lastForcedResidual[i]<<','
        <<mesh.C()[i].x()/.01<<','<<mesh.C()[i].y()/.01<<'\\n';
    Info<<"SENSITIVITY_STATUS "<<(sensitivityMonitor.steady ? "STEADY" : "NOT_CONVERGED")<<nl;
    Info<< "End\\n" << endl;''')
    p.write_text(s)
    reg={
      'schema':'routeB-gateG-independent-qoi-sensitivity-preregistration-v1',
      'physics':{'Ra_test':30000,'Pr':.71,'L_m':.01,'depth_m':.001,'Th_K':301,'Tc_K':300,'TRef_K':300.5,'DeltaT_K':1,'nu_m2_s':1e-6,'alpha_definition':'nu/Pr','beta_definition':'Ra*nu*alpha/(g*DeltaT*L**3)','gravity_m_s2':9.81,'laminar':True,'impermeable_walls':True,'front_back':'empty'},
      'grid_split':{'exploration':[20,40],'holdout':[80],'forbidden':[160,320]},
      'profile':'serial/DP/ASCII16, Foundation v6',
      'qois':['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Umax','Wmax','Umax_Z','Wmax_X'],
      'arm_1':{'tolerances':[1e-6,1e-8,1e-10],'relTol':0,'initial_state':'Cold start U=0, T=TRef, p_rgh=0 for every condition','other_settings':'Fixed Case C template schemes and relaxation; U/T linear tolerance 1e-12 relTol 0','pure_continuity_claim':False},
      'baseline':{'pressure_tolerance':1e-10,'same_grid_only':True,'name':'highest-fidelity tested numerical baseline'},
      'stopping':{'minimum_iteration':400,'sample_interval':20,'window_iterations':200,'window_samples':11,'continuation_block':200,'maximum_iteration':12000,'value_QoI_window_range_normalized_by_max_abs_or_one':1e-8,'position_window_absolute':1/4096,'U_change_over_20_iterations_over_Up':1e-8,'T_change_over_20_iterations_over_DeltaT':1e-8,'heat_imbalance_window_absolute_range':1e-8,'epsilon_mean_window_absolute_range':'<=2*100*p_tolerance','epsilon_max_window_absolute_range':'<=2*100*p_tolerance*n_cells','continuity_capacity_scale_rationale':'Case C Kp reached about 25; 100 is a conservative numerical monitor capacity allowance, not research quota. Tight field/QoI conditions independently apply.','momentum_temperature_initial_residual_max':1e-8,'pressure_final_residual_max':'1.1*run-specific tolerance, never 1e-10 for 1e-6 run','normal_exit_and_finite_required':True,'repeat_qualified_checks_for_full_continuation_block':True},
      'arm_2':{'binary':'buoyantBoussinesqSimpleFoamContinuitySourceAudit','source_units':'g m3/s; s=g/V 1/s','source_equation':'Build unchanged stock pressure matrix then subtract g from its source before reference; q target +g, verified tiny test','sum_g':'Zero by internal-face incidence','nominal':'eta=L/(Up_base*Vtotal)*sum(abs(g)); amplitude fixed within run','patterns':{'P1':[[.5,.5]],'P2':[[.075,.5]],'P3':[[.925,.5]],'P4':[[.25,.25],[.75,.25],[.25,.75],[.75,.75]],'P5':[[.5,.575]]},'face_selection':'Internal X-oriented face nearest Euclidean nondimensional anchor, smallest face ID ties, excludes faces incident on pRefCell; P4 sites require disjoint source cells','reference_cell':'central cell (n//2)*n+n//2; no source directly there','equivalence':'20x20 stock/source zero-source cold-start 10 iterations; U/T/p_rgh/phi complete SHA256 match or investigate then STOP','tiny_sign_test':'20x20, eta=1e-7 positive P1, 20 iterations; compare q versus +/-g, dimensional checks and zero net; below-capability runs STOP','realization_rule':{'relative_L1_q_minus_g_max':.05,'reason':'Controlled-source purity criterion (not research quota). Compare measured vector error, not recursive-vs-true norm drift. Case C supplies mapping units/reference awareness; no certified universal bound transferred.','mapping_scaled_error_max':1e-6,'roundoff_zero_net_rule':'abs(sum_g)<=64*machine_epsilon*sum_abs_g; exact cancellation expected','boundary_rule':'impermeable flux exact zero or <=64*machine_epsilon*Up*L*depth; closure within 128*machine_epsilon*sum_abs_face_flux'},'exploration_patterns':['P1','P2','P4'],'signs':'Positive at all selected levels; additional negative P1/P2 at mid level'},
      'pilot':{'grid':20,'pattern':'P1','sign':1,'levels':[1e-8,1e-7,1e-6,1e-5,1e-4],'selection':'Among valid steady realized levels, start at lowest level where at least one value QoI difference exceeds its conservative uncertainty AND two larger valid levels exist; select that level and next two valid levels. If none qualifies with two successors, use the three highest valid levels, mark response resolution incomplete. Fewer than three valid levels => STOP, preserve pilot. No quota PASS involved.'},
      'uncertainty':{'combination':'Conservative sum/envelope, no unsupported RSS; baseline/test contributions retained','iterative':'Per QoI max of tail window range and final-minus-200-iterations-earlier magnitude, each side separately','extraction':'Nu exact defined discrete sums with 64*eps absolute term-sum allowance; U/W and positions compare 4097/8193 sampling plus 1/4096 coordinate resolution and tied-peak interval; no physical interpolation error guarantee','restart_serialization':'20 baseline matched restart last 200 iterations versus uninterrupted continuation from common checkpoint; all grids report own memory/file diagnostic where available; use corresponding per-QoI measured restart differences conservatively, untested-grid transfer explicitly limited','near_zero_rule':'If abs(baseline)<=10*baseline uncertainty, use Nu characteristic=1 or nondimensional velocity characteristic=1; record the branch, no arbitrary floor','source_matching':'Tolerance from q-g plus repeatability epsilon changes only, before QoI pattern comparison; maximum two additional amplitude trials per matched condition; preserve all trials','effect_not_resolved':'abs(Delta Q)<=combined uncertainty; never ZERO_EFFECT'},
      'holdout_policy':'No 80 nonzero-source results before exploration analysis and immutable confirmation_manifest_v1 with SHA256. Then P1 seen and P3 held-out, at least two amplitudes and both signs. Never alter v1 model after seeing holdout; new versions separate.',
      'temperature_offset':'20 grid, shift all temperatures and TRef +50 K; zero-source and representative mid-positive P1 comparisons; interpretation only, no calibration',
      'STOP':['Zero-source solver changes solution','Cannot establish sign/dimensions','Nonzero net source','Source realization not controlled relative to numerical residual/reference','Arm2 NaN/fatal','Any steady run fails at max iteration','Need to rewrite confirmation after holdout','Need formal results','Need production changes'],
      'quota':None,'quota_status':'UNRESOLVED','tau_mean':None,'tau_mean_status':'UNRESOLVED',
      'formal_results_used':False,'formal_solver_allowed':False,
      'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in audit.iterdir() if p.is_file()}
    }
    (HERE/'experiment_preregistration_v1.json').write_text(json.dumps(reg,indent=2)+'\n')
    md='''# Route B Gate G sensitivity experiment preregistration v1

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
'''
    (HERE/'experiment_preregistration_v1.md').write_text(md)
    hashes={p.name:sha(p) for p in [HERE/'experiment_preregistration_v1.json',HERE/'experiment_preregistration_v1.md']}
    (RESULTS/'preregistration_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps({'HEAD':head,'preregistration_hashes':hashes},indent=2))

if __name__=='__main__': prepare()
