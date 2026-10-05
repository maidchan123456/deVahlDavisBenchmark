#!/usr/bin/env python3
"""Analyze only verification/work microcases and synthetic outputs."""
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from common import HERE, ROOT, RESULTS, WORK, L, WIDTH, read_case, parser, production_continuity_metrics, write_csv


def load_csv(path):
    with path.open() as f:return list(csv.DictReader(f))


def numeric_rows(path):
    return [{k:float(v) for k,v in r.items()} for r in load_csv(path)]


def extent(rows,key):
    values=[float(r[key]) for r in rows]
    return {'min':min(values),'max':max(values)}


def quantum(values, precision=16):
    absolute=np.abs(values)
    result=np.zeros_like(values)
    mask=absolute>0
    result[mask]=.51*10.0**(np.floor(np.log10(absolute[mask]))-precision+1)
    return result


def analyze():
    manifest=json.loads((RESULTS/'run_manifest.json').read_text())
    assert all(d['file_sha256_equal'] for d in manifest['audit_equivalence'].values())
    operator=json.loads((RESULTS/'operator_stage_summary.json').read_text())
    assert operator['status']=='PASS'
    serialization=load_csv(RESULTS/'serialization_test.csv')
    serialization=[r for r in serialization if r['stage']=='synthetic']
    local=load_csv(RESULTS/'local_metrics.csv')
    local=[r for r in local if r['source']=='synthetic']
    mapping=[];by_case={};artifacts=[]
    for case in manifest['cases']:
        folder=Path(case['path'])
        assert folder.is_relative_to(WORK/'microcases'), 'Never read benchmark case'
        n=case['n']
        rows=numeric_rows(folder/'continuityAudit.csv')
        if case['role']=='restart':rows=numeric_rows(folder/'continuityAudit_first5.csv')+rows
        assert len(rows)==10
        for a in rows:
            assert all(math.isfinite(v) for v in a.values()), 'STOP: nonfinite audit metric'
            assert a['converged']==1 and a['R_recursive']<case['tolerance'], 'STOP: failed pressure solve'
            assert a['Up']>0
            iteration=int(a['iteration'])
            m,U,phi,q,boundary=read_case(folder,iteration,n)
            volume=(L/n)*(L/n)*WIDTH
            # Actual unmodified function uses the same nominal uniform volume.
            production_mean,_=production_continuity_metrics(folder,folder/str(iteration),U.reshape(n,n,3),n,n,L,WIDTH)
            assert np.isclose(production_mean,m['mean_abs_div_phi'],rtol=2e-15,atol=0), 'STOP: production parser/incidence disagreement'
            # Conservative significant-digit IO bound plus arithmetic/geometry terms.
            internal_budget=quantum(phi)
            boundary_budget=sum(float(np.sum(quantum(b))) for b in boundary)
            l1_budget=2*float(np.sum(internal_budget))+boundary_budget
            total_volume=L*L*WIDTH
            max_budget=(2*float(np.sum(internal_budget))+boundary_budget)/volume
            mean_budget=l1_budget/total_volume
            mean_error=m['mean_abs_div_phi']-a['mean_abs_div_phi']
            max_error=m['max_abs_div_phi']-a['max_abs_div_phi']
            assert abs(mean_error)<=mean_budget+1e-12*a['mean_abs_div_phi'], 'STOP: unexpected write/read mean error'
            assert abs(max_error)<=max_budget+1e-12*a['max_abs_div_phi'], 'STOP: unexpected write/read max error'
            serialization.append({'stage':'microcase','case_id':case['id'],'n':n,'tolerance':case['tolerance'],
                'iteration':iteration,'write_precision':16,**m,
                'mean_metric_error':mean_error,'max_metric_error':max_error,
                'P99_metric_error':m['P99_abs_div_phi']-a['P99_abs_div_phi'],
                'global_signed_error':m['signed_volume_mean_div_phi']-a['signed_volume_mean_div_phi'],
                'epsilon_mean_write_read_error':m['epsilon_phi_mean']-a['epsilon_phi_mean'],
                'mean_IO_budget':mean_budget,'max_IO_budget_conservative':max_budget,
                'production_mean_match':True})
            cell=int(m['max_cell_id'])
            local.append({'source':'microcase','case_id':case['id'],'role':case['role'],'n':n,
                'tolerance':case['tolerance'],'iteration':iteration,**m,
                'max_cell_x':(cell%n+.5)*L/n,'max_cell_y':(cell//n+.5)*L/n,'max_cell_z':WIDTH/2,
                'P95_dimensionless':L/m['Up']*m['P95_abs_div_phi'],
                'P99_dimensionless':L/m['Up']*m['P99_abs_div_phi']})
            prediction=(a['true_nonreference_L1']+abs(a['q_reference']))*L/(a['Up']*total_volume)
            closure=abs(a['signed_volume_mean_div_phi']*total_volume-a['net_boundary_flux'])
            conservative=2*a['true_nonreference_L1']+abs(a['net_boundary_flux'])+2*a['mapping_defect_L1']+closure
            assert a['sum_abs_q']<=conservative*(1+1e-12), 'STOP: reference-aware bound failed'
            mapping.append({'case_id':case['id'],'role':case['role'],'n':n,'tolerance':case['tolerance'],**a,
                'epsilon_reference_corrected_prediction':prediction,
                'reference_corrected_epsilon_error':a['epsilon_phi_mean']-prediction,
                'relative_L1_norm_drift':a['abs_L1_norm_drift']/a['true_residual_L1'],
                'physical_mapping_epsilon_rounding_proxy':a['mapping_defect_L1']*L/(a['Up']*total_volume),
                'closed_reference_bound_q_L1':conservative,'reference_bound_verified':True,
                'boundary_telescoping_error_m3_s':closure})
        by_case[case['id']]=mapping[-10:]
        for iteration in (5,10):
            for name in ('U','T','p_rgh','phi'):
                p=folder/str(iteration)/name
                artifacts.append({'case_id':case['id'],'iteration':iteration,'field':name,'bytes':p.stat().st_size,
                                  'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        for p in (folder/'continuityAudit.csv',folder/'log.audit'):
            if p.exists():artifacts.append({'case_id':case['id'],'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    sweep=[r for r in mapping if r['role']=='sweep']
    final=[r for r in sweep if r['iteration']==10]
    continuous=next(c for c in manifest['cases'] if c['id']=='audit_n20_tol1e-8')
    restarted=next(c for c in manifest['cases'] if c['role']=='restart')
    cpath=Path(continuous['path']);rpath=Path(restarted['path'])
    restart_rows=[]
    for field in ('U','T','p_rgh','phi'):
        size=2*20*19 if field=='phi' else 400
        reader=parser.read_vector if field=='U' else parser.read_scalar
        x=reader(cpath/'10'/field,size);y=reader(rpath/'10'/field,size)
        delta=float(np.max(abs(y-x)));scale=float(np.max(abs(x)))
        restart_rows.append({'quantity':field,'max_absolute_difference':delta,'relative_max_difference':delta/scale if scale else None,
                             'continuous_file_sha256':hashlib.sha256((cpath/'10'/field).read_bytes()).hexdigest(),
                             'restart_file_sha256':hashlib.sha256((rpath/'10'/field).read_bytes()).hexdigest()})
    cr=by_case[continuous['id']][-1];rr=by_case[restarted['id']][-1]
    for key in ('epsilon_phi_mean','epsilon_phi_max','P99_abs_div_phi','R_recursive','R_true','Np','Up'):
        restart_rows.append({'quantity':key,'continuous_value':cr[key],'restart_value':rr[key],
            'max_absolute_difference':abs(rr[key]-cr[key]),'relative_max_difference':abs(rr[key]-cr[key])/abs(cr[key])})
    assert all(np.isfinite(float(r['max_absolute_difference'])) for r in restart_rows)
    precision16=[r for r in serialization if r['stage']=='synthetic' and int(r['write_precision'])==16 and r['test']=='A1_exact_flux']
    precision6=[r for r in serialization if r['stage']=='synthetic' and int(r['write_precision'])==6 and r['test']=='A1_exact_flux']
    micro=[r for r in serialization if r['stage']=='microcase' and any(r['case_id']==c['id'] and c['role']=='sweep' for c in manifest['cases'])]
    grid={str(n):{'final_sweep':[{k:r[k] for k in ('tolerance','epsilon_phi_mean','epsilon_phi_max','P99_abs_div_phi','Kp','ratio_recursive','ratio_true')} for r in final if r['n']==n],
        'all_tolerances_all_iterations_Kp_range':extent([r for r in sweep if r['n']==n],'Kp'),
        'max_mean_write_read_difference':max(abs(float(r['mean_metric_error'])) for r in micro if r['n']==n)} for n in (20,40,80)}
    tolerance={str(t):{'mean_range':extent([r for r in sweep if r['tolerance']==t],'epsilon_phi_mean'),
        'relative_norm_drift_range':extent([r for r in sweep if r['tolerance']==t],'relative_L1_norm_drift'),
        'plateau_established':False} for t in (1e-6,1e-8,1e-10)}
    summary={
        'schema':'routeB-caseC-continuity-verification-v1', 'review_date':'2026-10-04',
        'benchmark_results_used_for_threshold_derivation':False,'benchmark_post_hoc_comparison_performed':False,
        'operator_verification':operator,
        'serialization':{'write_precision_16_effect':'Measured actual ASCII write/read perturbation; bounded by significant-digit IO budget in this suite.',
            'parser_effect':'Exactly matches Python conversion of serialized significant digits; actual production parser/function used.',
            'restart_effect':'10 continuous vs 5+restart+5, ASCII16; finite differences quantified, includes restart initialization/history/BC effects, not isolated pure IO floor.',
            'synthetic_ASCII16_exact_flux_mean_range':extent(precision16,'mean_abs_div_phi'),
            'synthetic_ASCII16_exact_flux_max_range':extent(precision16,'max_abs_div_phi'),
            'synthetic_ASCII6_exact_flux_mean_range':extent(precision6,'mean_abs_div_phi'),
            'microcase_mean_metric_error_absolute_max':max(abs(float(r['mean_metric_error'])) for r in micro),
            'microcase_max_metric_error_absolute_max':max(abs(float(r['max_metric_error'])) for r in micro),
            'microcase_epsilon_mean_error_absolute_max':max(abs(float(r['epsilon_mean_write_read_error'])) for r in micro),
            'restart_comparison':restart_rows},
        'solver_mapping':{'audit_solver_used':True,'audit_solver_equivalent_to_stock':True,
            'stock_equivalence_basis':'Full final ASCII16 field-file SHA256 equality for U,T,p_rgh,phi, including all patches; 20^2 tolerance=1e-8 serial 10 iterations.',
            'true_residual_available':True,'norm_factor_available':True,'Kp_available':True,
            'recursive_residual_vector_available':False,
            'recursive_norm_available':True,
            'norm_factor_method':'Installed v6 PCG::normFactor on copied boundary/reference-assembled fvMatrix, no diagnostic solve.',
            'direct_mapping_validated':False,
            'reference_aware_physical_mapping_validated':True,
            'overall_validation':'PARTIAL',
            'mapping_scope':'v6, serial double, closed orthogonal uniform 20/40/80^2, Ra_test=30000, pressure relTol=0, first 10 SIMPLE iterations. q=b0-A0*p_star validated to observed arithmetic discrepancy; reported R alone is insufficient.',
            'pressure_solve_rows':len(mapping),'sweep_pressure_solve_rows':len(sweep),
            'Kp_range':extent(sweep,'Kp'),
            'ratio_recursive_range':extent(sweep,'ratio_recursive'),
            'ratio_true_range':extent(sweep,'ratio_true'),
            'mapping_defect_L1_m3_s_range':extent(sweep,'mapping_defect_L1'),
            'abs_L1_norm_drift_m3_s_range':extent(sweep,'abs_L1_norm_drift'),
            'maximum_relative_L1_norm_drift':max(r['relative_L1_norm_drift'] for r in sweep),
            'reference_corrected_epsilon_error_absolute_max':max(abs(r['reference_corrected_epsilon_error']) for r in sweep),
            'reference_bound_verified_all_rows':True,
            'drift_caveat':'Only difference of L1 norms is measured, not ||r_true-r_recursive||_1. Recomputed true residual also has cancellation/rounding; no vector drift upper bound claimed.'},
        'grid_dependence':grid,'tolerance_dependence':tolerance,
        'numerical_floor':{'mean':None,'max':None,'quantification_status':'PARTIAL',
            'basis':'Synthetic rounding levels and real write/read/evaluation discrepancies measured; tightest solver tolerance 1e-10 does not establish a plateau or universal floor.',
            'scope':'serial DP ASCII16, stated geometry/scales and grids; no binary/parallel, no full steady solution',
            'synthetic_ASCII16_scoped_mean_range':extent(precision16,'mean_abs_div_phi'),
            'synthetic_ASCII16_scoped_max_range':extent(precision16,'max_abs_div_phi'),
            'physical_mapping_epsilon_rounding_proxy_range':extent(sweep,'physical_mapping_epsilon_rounding_proxy')},
        'local_metrics':{'mean':'Primary Candidate B Hard candidate, threshold unresolved.',
            'max':'Necessary diagnostic for isolated defects; potential guard research, no Hard adoption.',
            'p95':'Uniform-volume linear percentile diagnostic.',
            'p99':'Can equal zero with two defective cells out of 400 or more; not a maximum guard.',
            'global_signed':'Internal perturbations cancel globally; boundary leakage is detected; does not prove local conservation.',
            'A4_max_to_mean_ratios':{str(n):n*n/2 for n in (20,40,80,160)},
            'local_guard_hard_adopted':False},
        'tau_phi':None,'tau_phi_status':'UNRESOLVED','explicit_acceptance_budget_available':False,
        'recommended_threshold_strategy':'SCHEME_3_ERROR_BUDGET_WITH_VERIFIED_REFERENCE_AWARE_MAPPING_AND_OPERATOR_IO_AUDIT',
        'recommended_local_guard':'UNRESOLVED','local_guard_research_preference':'MEAN_PLUS_MAX',
        'candidate_B_status':'PROVISIONAL','current_formal_gate_G':'FAIL','new_spec_Ra1e3_gate_G':'NOT_EVALUATED',
        'solver_rerun_for_existing_benchmark_required':False,'spec_change_executed':False,'criteria_modified':False,
        'user_decision_required':True,
        'required_user_decision':['Define independent mean/local physical acceptance budget and applicability scope.','Decide whether to research a maximum local guard; no threshold or guard adoption in this task.','If a certified solver floor is required, separately scope tighter tolerance/frozen-state/parallel/binary tests.'],
        'limitations':['10 SIMPLE iterations only; no claim of steady convergence.','Different pressure tolerance changes later nonlinear states; across-run trends are not a frozen-matrix experiment.','No recursive residual vector; norm differences are not vector drift bounds.','Roundoff/evaluation discrepancies measured, not rigorous universal floor.','Restart test combines serialization and reinitialization effects.','Equivalence tested for one representative serial condition.','Uniform Cartesian single-block patch family only.','No peer-reference comparison, parallel run, binary parser or existing benchmark field access.','Physical research acceptance budget still absent.'],
        'stock_equivalence_field_hashes':manifest['audit_equivalence'],
        'microcase':{k:manifest[k] for k in ('Ra_test','Pr','L_m','width_m','serial','iterations','write_precision','write_format','relTol')},
        'git_policy':'Large microcase fields, binaries, objects and raw logs retained only in ignored verification/work and auditSolver build directories; compact hashes and summaries tracked.'}
    write_csv('solver_mapping.csv',mapping);write_csv('serialization_test.csv',serialization)
    write_csv('restart_test.csv',restart_rows);write_csv('local_metrics.csv',local)
    (RESULTS/'verification_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (RESULTS/'artifact_hashes.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    write_report(summary,final,precision16,precision6,restart_rows,mapping)
    print(json.dumps({'operator':'PASS','audit_equivalent':True,'mapping':'PARTIAL','floor':'PARTIAL','tau_phi':None,
                     'mapping_rows':len(mapping),'microcase_mean_io_error':summary['serialization']['microcase_mean_metric_error_absolute_max'],
                     'max_norm_drift_relative':summary['solver_mapping']['maximum_relative_L1_norm_drift']},indent=2))


def write_report(s,final,p16,p6,restart,mapping):
    def fmt(value):return f'{float(value):.6g}'
    def table(keys,rows):
        return '| '+' | '.join(keys)+' |\n| '+' | '.join('---' for k in keys)+' |\n'+''.join('| '+' | '.join(fmt(r[k]) if isinstance(r[k],(float,int)) else str(r[k]) for k in keys)+' |\n' for r in rows)
    synthetic=[]
    for a,b in zip(p16,p6):synthetic.append({'grid':a['n']+'²','ASCII16 mean':fmt(a['mean_abs_div_phi']),'ASCII16 max':fmt(a['max_abs_div_phi']),'ASCII6 mean':fmt(b['mean_abs_div_phi'])})
    final_table=table(['n','tolerance','Kp','R_recursive','R_true','epsilon_phi_mean','epsilon_phi_max','P99_abs_div_phi','ratio_recursive'],final)
    restart_table=table(['quantity','max_absolute_difference','relative_max_difference'],restart)
    sm=s['solver_mapping'];io=s['serialization']
    report=fr'''# Route B Case C Continuity Verification

## 1. Purpose

2026-10-04。Route B Candidate Bのepsilon_phiについて、operator、v6 pressure残差との対応、serialization/restart、local conservationを独立検証した。**operator PASS、stock/audit同値、referenceを考慮したmappingは検証できたが、tolerance単独の直接変換は不可。numerical floorはPARTIAL、tau_phiはUNRESOLVED、Candidate BはPROVISIONAL。**

## 2. Independence from benchmark results

正式matrixのcase/field/metricsを読み込まず、正式Ra=1e3/1e4/1e5/1e6、320²、Route Aのsolverを実行していない。指定された既存reviewの背景値は導出に使用せず、post-hoc比較も実施しない。reference CSV・paper比較なし。現行Gate G FAILと新案NOT_EVALUATEDを保持する。

コード・microcase・binaryはverification/routeB_continuity内、summaryはresults/routeB/caseC_continuity_verification内に限定。raw field/log/build objectはlocal .gitignoreで除外し、再現用設定・sourceとcompact CSV/hashを保存する。

## 3. epsilon_phi operator verification

q_i=sum_f s_if phi_f、d_i=q_i/Vi、M=sum_i|q_i|/Vtotal、epsilon_phi=(L/Up)M。phi/qはm³/s、divergenceはs⁻¹。actual production foam_fields parserとanalyze_case.pyの**continuity_metrics関数そのもの**を使った。ASTでその関数だけ読み込み、production mainやpaper reference処理を実行しない。owner/neighbour、4物理壁、empty front/back、uniform volumeを検証した。

解析qとの差はcellごとの32-operation unit-roundoff modelと実測ASCII roundingのincidence伝播で評価し、20条件がPASS。これはimplementation testの誤差budgetであって物理acceptance thresholdではない。最初の完全一致assertでは検証側の1/n²とproductionの(1/n)(1/n)の体積計算順が異なり、20²でV差4.34e-19が出た。検証側を修正して完全一致を確認し、production bugの証拠はなかった。

## 4. Synthetic exact-flux tests

20²/40²/80²/160²。L=depth=1m、Up=1m/sをprescribed cell U=(1,0,0)から与え、phiとは独立のnormalization入力とした。合成場はhydrodynamic solutionではない。psi=sin²(pi x)sin²(2pi y)、境界vertex psi=0。vertical face fluxはy方向psi差、horizontal fluxは負のx方向psi差で、正確算術ではtelescopingする。

{table(['grid','ASCII16 mean','ASCII16 max','ASCII6 mean'],synthetic)}

表のdivergence単位はs⁻¹。L/Up=1sなのでepsilon値も同じ数値。in-memory値・P95/P99・globalはserialization CSVのmemory_*列へ保存。ASCII16でmean {fmt(io['synthetic_ASCII16_exact_flux_mean_range']['min'])}–{fmt(io['synthetic_ASCII16_exact_flux_mean_range']['max'])}、max {fmt(io['synthetic_ASCII16_exact_flux_max_range']['min'])}–{fmt(io['synthetic_ASCII16_exact_flux_max_range']['max'])}という、この構成の丸め水準を測定した。

single internal faceにdelta_phi=1e-6/1e-8/1e-9を注入した試験はzero baselineを用い、隣接cellの±delta、sum|q|=2|delta|、mean=2|delta|/Vtotal、max=|delta|/Vi、global=0に一致。絶対・相対誤差をoperator CSVへ記録した。1つのhotWall faceへの1e-8漏れはsum q=net boundary flux=1e-8m³/sとして検出された。empty patchは0-length scalar listで読み飛ばすことも確認した。

## 5. Serialization and parser effects

同一合成phiのin-memory float64、ASCII相当precision16/6、actual parser read-backを比較。parser値はPythonのserialized significant-digit conversionと完全一致し、parser独自の追加誤差を認めなかった。precision6のexact-flux meanは{fmt(io['synthetic_ASCII6_exact_flux_mean_range']['min'])}–{fmt(io['synthetic_ASCII6_exact_flux_mean_range']['max'])}s⁻¹へ増大した。precision6は感度診断だけでありproduction設定を変更しない。

実microcaseでも各iterationのaudit in-memory metricと実OpenFOAM ASCII16 field read-backを比較した。sweep 90 solvesの最大absolute mean差は{fmt(io['microcase_mean_metric_error_absolute_max'])}s⁻¹、max差は{fmt(io['microcase_max_metric_error_absolute_max'])}s⁻¹、epsilon mean差は{fmt(io['microcase_epsilon_mean_error_absolute_max'])}。CSVへP99/globalの差も収録。faceのsignificant-digit quantumを両隣cellへ伝播した保守的IO budget内であることを確認した。微小なuniform mesh volume計算差・加算順も差の一部であり、全差をserializationだけと断定しない。

## 6. OpenFOAM microcase

Foundation v6、buoyantBoussinesqSimpleFoam、laminar、closed cavity、Pr=0.71、**Ra_test=30000**。L=0.01m、depth=0.001m、1 depth cell、front/back empty。hot/cold=301/300K、TRef=300.5K、g=(0,-9.81,0)m/s²、nu=1e-6m²/s、alpha=nu/Pr、beta=Ra_test nu²/(Pr g L³)。beta deltaTは約0.00431。開始U=0、T=300.5K。gravityによるnonzero convectionを得た。

20²/40²/80²、p_rgh PCG/DICのtolerance=1e-6/1e-8/1e-10、relTol=0、maxIter=10000。他の設定・初期条件・relaxationは同一。10 SIMPLE iterationsだけを実行し、**steady convergenceを主張しない**。初期各pressure solveを調べる目的に限定する。stock/audit代表、restart、reference cornerの補助条件も20²で実施した。

## 7. Audit solver verification

通常のstock logにはNp、true residual、local percentile、physical reference residualがないため、v6 solver sourceを専用auditSolverへコピーし、別名buoyantBoussinesqSimpleFoamContinuityAuditとしてwmakeした。installation source/binaryは変更しない。

追加はコピーしたmatrixのboundary/reference assembly、installed PCG::normFactor呼び出し、solve後のb−Ap再評価、phiのincidenceとmetric出力だけ。PCG内部や支配方程式・discretization・relaxationは変更していない。solve return valueを保存し、p relaxation前のtrue residualを取得する。診断用PCG objectはnormFactorを呼ぶだけでsolveしない。

20²、tolerance=1e-8、10 iterationsでstockとauditをserial実行し、**U/T/p_rgh/phiの最終fieldファイル全体がSHA-256一致**。patch値もhash対象である。internal差も全て0。証拠hashはsummaryとartifact_hashesに保存。代表条件以外の同値性を実証したとはしない。

## 8. Pressure residual to flux-imbalance mapping

physical pressure matrix（reference追加前）A0/b0、referenceとBC込みAs/bsをコピーし、同じunrelaxed p*についてr0=b0−A0p*とrtrue=bs−As p*を再計算した。actual corrected phiからqを別に集計する。

$$q\simeq r_0,\quad R_{{true}}=\|r_{{true}}\|_1/N_p,\quad K_p=LN_p/(U_pV_\Omega).$$

Npはinstalled PCGのactual normFactorで取得。全sweepのKpは{fmt(sm['Kp_range']['min'])}–{fmt(sm['Kp_range']['max'])}。q−r0のL1評価差は{fmt(sm['mapping_defect_L1_m3_s_range']['min'])}–{fmt(sm['mapping_defect_L1_m3_s_range']['max'])}m³/sであり、matrix/face評価のcancellation・丸めが残る。したがってepsilon_phi=toleranceという直接関係は成立しない。

epsilon/(Kp R_recursive)は{fmt(sm['ratio_recursive_range']['min'])}–{fmt(sm['ratio_recursive_range']['max'])}、true residualでのratioは{fmt(sm['ratio_true_range']['min'])}–{fmt(sm['ratio_true_range']['max'])}。ratioが1に近いことだけで無条件同一視しない。

reference-aware予測は

$$\epsilon_{{pred}}=\frac L{{U_pV_\Omega}}\left(\sum_{{i\ne j}}|r_{{true,i}}|+|q_j|\right).$$

そのepsilonとの最大absolute差は{fmt(sm['reference_corrected_epsilon_error_absolute_max'])}。reference行のalgebraic residualとq_jを別々に記録し、非reference行・net boundary Bを使ったsum|q|≤2 sum_(i≠j)|rtrue_i|+|B|という前回の条件付き上界を、実測operator discrepancyとtelescoping roundoffを加えて全rowで確認した。これは今回の有限suiteでの量的検証であり、全matrixへの認証上界ではない。別のreference corner runでも関係を確認し、Np・reference寄与が変わることを記録した。

## 9. True vs recursive residual

reported finalはrecursive residual norm、trueはsolve直後にassembled matrixのAmulで再評価した値。L1 norm差の最大は{fmt(sm['abs_L1_norm_drift_m3_s_range']['max'])}m³/s、true L1に対する差の最大比は{fmt(sm['maximum_relative_L1_norm_drift'])}。80²、1e-10、iteration10ではR_recursive=7.98321e-11に対しR_true=8.87236e-11。

取得したのは**L1 normの差**であり、recursive residual vectorそのものは取得していない。abs(||rtrue||₁−||rrec||₁)と||rtrue−rrec||₁は同じではなく、前者は後者の下界にしかならない。再計算true residual自体にもcancellation/roundingがあり、全差をPCG再帰driftだけに帰属できない。前reviewのE_recの認証上界を今回取得したとはしない。

## 10. Grid dependence

以下は**iteration10のin-memory audit値**。P99はs⁻¹、epsilonは無次元。全iteration1–10はsolver_mapping.csvにある。

{final_table}

同じ1e-8でKpは20²/40²/80²で約3.924/6.471/11.890、epsilon meanは約2.854e-8/6.056e-8/1.104e-7。格子細分化で同じnormalized pressure toleranceが同じepsilonを与えるわけではない。pressure operatorとstate、Upのgrid依存を含む。field write/read差もgrid別にsummaryへ保存した。

## 11. Solver-tolerance dependence

全pressure solveはrelTol=0でabsolute toleranceを満たした。各gridでtoleranceを1e-6→1e-8→1e-10にするとepsilonは大きく低下するが、ちょうど100倍則ではない。最終Rのovershoot、linear iteration数、Kp、reference、true残差評価差が影響する。toleranceの違いが後続SIMPLE stateにも影響するので、全run間の比較は完全なfrozen-matrix sweepではない。

1e-10までではplateauを確立していない。tight caseでのtrue/recursive差やoutput/evaluation差は検出できたが、それから下限floorを外挿しない。pressure tolerance自体をtau_phi候補として使用しない。

## 12. Restart/write precision dependence

production templateで確認したASCII writePrecision16を独立caseにも使った。20²、1e-8について10 continuousと5→write/read restart→5を比較。

{restart_table}

restartはbitwise同一ではないが、差は表の範囲で定量化された。final U/phiに加えT/p_rgh、epsilon mean/max、P99、R_recursive/R_true/Np/Upを記録した。restartはserializationだけでなく、rhok・pressureゲージ・BC・iteration historyの再初期化を含むため、この差を純粋なIO floorと同一視しない。restart結果はacceptance budgetではない。

## 13. Mean vs local conservation

固定delta_phi=1e-8のinternal defectではmean=2e-8s⁻¹が格子によらず同じだが、maxはVi⁻¹で増大する。20²/40²/80²/160²のmax/meanは200/800/3200/12800。2cellだけの異常なのでP99は全て0。signed globalも0。一方boundary漏れはsigned globalで検出される。

meanは全領域L1 budget、maxは孤立欠陥、percentileは分布、signed globalはboundary整合を測る。各microcase/iterationのmean/max/P95/P99、無次元値、boundary net、max cell ID/coordinateをlocal_metrics.csvに保存。P99をmax guardの代用にはできない。

## 14. Numerical floor

**PARTIAL。普遍的floorのmean/max値はnull。** 合成fieldのscoped roundoffレベル、ASCII16/6の感度、実phi出力のmetric差、matrix/face算術評価差、restart差を量的に得た。ただし、合成fieldのscale・telescoping構造はpressure-corrected phiとは異なる。microcaseも10 iterations、最小tolerance1e-10だけでfloor plateauを示していない。

machine epsilon=2.220446049250313e-16をphi floorへ直結しない。serial DP ASCII16という範囲に限定し、conditioning、parallel、binary、他mesh family、別Ra/Up scaleへの普遍化をしない。

## 15. Acceptance-budget implications

A numerical measurement floor、B linear solver convergence capability、C research acceptance budgetを区別する。今回Aの一部とBを調べ、qとpressure residualのreference-aware関係を具体化した。しかしCの許容保存誤差を支配方程式だけから唯一の数値として決められず、目的量への許容影響も事前指定されていない。

追加すべき根拠は、mean/local保存欠陥が許容目的量精度に与える影響と、その研究上の許容量の事前定義。数値floorの安全係数だけでHard閾値を選ばない。正式結果の値に合わせてbudgetを逆算しない。

## 16. tau_phi assessment

**tau_phi=null、UNRESOLVED。Candidate BはPROVISIONAL。** Operator実装と条件付きmappingの根拠は強化されたが、共通fixed tauやsolver-linked数値を正式採用できる状態ではない。推奨は独立error budgetに今回のreference-aware mappingとoperator/IO監査を組み合わせる方式。benchmark再計算は不要であり、既存結果の再判定も行っていない。

## 17. Local-guard assessment

孤立cellの品質まで保証したいならmax guardの研究が必要そうであり、L2（mean+max）を優先検討する根拠は得た。L3（percentile）だけでは今回の2cell欠陥を検出できない。ただし**local guardをHardへ採用する判断は今回行わない**。その数値budgetは未定のためrecommended_local_guard=UNRESOLVED、research_preference=MEAN_PLUS_MAX。L1もmean threshold未定なので正式採用しない。

## 18. Limitations

10 iterationsはsteady solutionではない。tolerance間でstateが変わる。recursive vectorは未取得。true residual計算にも丸めがある。restartはIOと再初期化が混在。stock同値性は代表1条件だけ。uniform Cartesian、serial DP、ASCII16、指定scaleの検証であり、binary/parallelや全Raを認証していない。machine epsilonや合成floorはacceptance値ではない。

sourceの主根拠はlocal v6 PCG.C:93–110/172–180、lduMatrixSolver.C:174–196、fvScalarMatrix.C:154–169、fvMatrix.C:507–518/1458–1466、pEqn.H:29–46、continuityErrs.H:33–40、fvcSurfaceIntegrate.C:51–75。absolute source path/lineとコピー元hashはsource_audit.jsonに収録する。公式sourceは[PCG](https://cpp.openfoam.org/v6/PCG_8C_source.html)、[normalization](https://cpp.openfoam.org/v6/lduMatrixSolver_8C_source.html)（前reviewで確認、今回の根拠は実installed source）。長いsource引用は行わない。

## 19. Required user decision

次は結果非依存のmean/local acceptance budgetと適用範囲を定めること。孤立欠陥をHardで抑える目的があるかを確認し、max guardのbudget研究を進めるか判断する。認証されたsolver floorが必要なら、frozen-stateでのよりtightなsolve、残差vector取得、parallel/binary等を別途scopeにする。現行Gate G・production code・reference・正式CSV/status/fieldは変更していない。開始時のRoute A untracked 2directoryは未変更。

```text
CASE_C_OPERATOR_VERIFICATION = PASS
AUDIT_SOLVER_USED = YES
AUDIT_SOLVER_EQUIVALENT_TO_STOCK = YES
RESIDUAL_TO_FLUX_MAPPING_VALIDATED = PARTIAL
NUMERICAL_FLOOR_QUANTIFIED = PARTIAL
TAU_PHI = UNRESOLVED
TAU_PHI_STATUS = UNRESOLVED
RECOMMENDED_LOCAL_GUARD = UNRESOLVED
CANDIDATE_B_STATUS = PROVISIONAL
BENCHMARK_RESULTS_USED_FOR_THRESHOLD_DERIVATION = NO
BENCHMARK_SOLVER_RERUN_REQUIRED = NO
GATE_G_CRITERIA_MODIFIED = NO
SPEC_CHANGE_EXECUTED = NO
USER_DECISION_REQUIRED = YES
```
'''
    (RESULTS/'verification_report.md').write_text(report)


if __name__=='__main__':
    try:analyze()
    except Exception as exc:
        (RESULTS/'STOP.json').write_text(json.dumps({'status':'STOP','reason':str(exc)},indent=2)+'\n')
        raise
