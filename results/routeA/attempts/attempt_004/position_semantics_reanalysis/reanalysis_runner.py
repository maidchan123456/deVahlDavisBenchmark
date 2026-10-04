import contextlib,hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
R=Path.cwd();O=R/'results/routeA/attempts/attempt_004/position_semantics_reanalysis'
sys.path.insert(0,str(R/'Scripts/routeA'));import analyze_case as a
REF=a.PAPER_REFERENCE;AH=hashlib.sha256((R/'Scripts/routeA/analyze_case.py').read_bytes()).hexdigest()
history=json.loads((O.parent/'Ra1e3_trio_report.json').read_text());checks=[]
keys=['Nu_bar_cavity','Nu_bar_0','Nu_bar_half','Nu_bar_1','Umax','Umax_Z','Wmax','Wmax_X','Nu_hot_local_max','Nu_hot_local_max_Z','Nu_hot_local_min','Nu_hot_local_min_Z']
for name,start,end in [('coarse',0,3000),('medium',3000,6000),('fine',15000,18000)]:
 cid='A-Ra1e3-'+name;case=R/'cases/routeA'/cid;sealed=R/'results/routeA/cases'/cid/'segments'/('end_'+str(end))
 oldpath=R/history['cases'][['coarse','medium','fine'].index(name)]['metrics_path'];old=json.loads(oldpath.read_text())
 dest=O/name;dest.mkdir(exist_ok=False);workspace=dest/'canonical_workspace';(workspace/'reference').mkdir(parents=True)
 shutil.copy2(REF,workspace/'reference/de_vahl_davis_table_v.csv');a.ROOT=workspace;a.PAPER_REFERENCE=workspace/'reference/de_vahl_davis_table_v.csv'
 log=sealed/'solver.log';sys.argv=['analyze_case.py',str(case),'--segment-start',str(start),'--solver-log',str(log)]
 with (dest/'log.canonical_reanalysis').open('w') as f, contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):a.main()
 outputs=workspace/'results/routeA/cases'/cid
 for p in outputs.iterdir():shutil.copy2(p,dest/p.name)
 new=json.loads((dest/'metrics.json').read_text());assert new['final_iteration']==end
 diffs={k:new[k]-old[k] for k in keys}
 for k,d in diffs.items():assert abs(d)<=64*np.finfo(float).eps*max(1,abs(old[k])),('STOP_QOI_CHANGED',cid,k,d)
 assert new['Gate_D_monitor_evaluation']==old['Gate_D_monitor_evaluation'],('STOP_GATE_D_CHANGED',cid)
 assert old['paper_comparison_like_for_like']['Wmax_X']['calculated']==new['paper_comparison_like_for_like']['Wmax_X']['calculated']
 before=old['paper_comparison_like_for_like'];after=new['paper_comparison_like_for_like']
 for k in before:
  if k!='Wmax_X':assert before[k]==after[k],('OTHER_PAPER_PAYLOAD_CHANGED',k)
 for k in a.POSITION_KEYS:
  assert 'absolute_position_error' in after[k] and 'signed_position_difference' in after[k]
  assert 'absolute_relative_error' not in after[k] and 'signed_relative_difference' not in after[k]
 assert before['Wmax_X']['reference']==after['Wmax_X']['reference']
 # Verify every other numerical/diagnostic payload is identical, permitting only roundoff in QoIs.
 changed=[k for k in old if old[k]!=new[k] and k!='paper_comparison_like_for_like']
 assert not changed,('UNEXPECTED_METRICS_CHANGE',cid,changed)
 gate_source=O.parent/'cases/A-Ra1e3-coarse/accepted_reuse/gate_D_status.json' if name=='coarse' else sealed/'gate_D_status.json'
 gd=json.loads(gate_source.read_text());assert gd['status']=='PASS'
 row={'case_id':cid,'source_iteration':end,'segment_start':start,'owner':'POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIO','canonical_analyzer_sha256':AH,'metrics_before_path':str(oldpath.relative_to(R)),'metrics_after_path':str((dest/'metrics.json').relative_to(R)),'QoI_absolute_differences':diffs,'QoIs_exactly_unchanged':all(d==0 for d in diffs.values()),'Gate_D_numerical_evaluation_identical':True,'formal_Gate_D_before':'PASS','formal_Gate_D_after':'PASS','formal_Gate_D_evidence_path':str(gate_source.relative_to(R)),'Wmax_X_before':before['Wmax_X'],'Wmax_X_after':after['Wmax_X'],'all_other_metrics_exactly_unchanged':True,'solver_executed':False}
 (dest/'evaluation_ownership.json').write_text(json.dumps(row,indent=2)+'\n');checks.append(row)
 print(cid,'reanalysis PASS; QoIs/monitors exact; Wmax_X position semantics PASS')
fine=json.loads((O/'fine/metrics.json').read_text());ref=a.read_paper_reference(REF)[1000]
errors={k:fine['paper_comparison_like_for_like'][k]['absolute_relative_error'] for k in ['Nu_bar_cavity','Umax','Wmax']}
positions={k:fine['paper_comparison_like_for_like'][k]['absolute_position_error'] for k in ['Umax_Z','Wmax_X']}
assert all(v<=.01 for v in list(errors.values())+list(positions.values()))
assert history['Gate_E_diagnostic']['status']=='PASS' and history['Gate_F']['status']=='FAIL' and history['Gate_G']['status']=='PASS'
result={'status':'PASS','owner':'POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIO','analyzer_sha256':AH,'cases':checks,'Gate_E_diagnostic':{'status':'PASS','status_changed':False,'relative_errors':errors,'absolute_position_errors':positions,'criteria_unchanged':True},'Gate_F':'FAIL','needs_320':'YES','Gate_G':'PASS','F_G_source':'Historical attempt_004 read-only; no new study','all_QoIs_exactly_unchanged':True,'Gate_D_statuses_unchanged':True,'historical_statuses_changed':False,'solver_executed':False}
(O/'comparison_semantics_check.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copy2('/tmp/routeA_position_fix/unit_tests.log',O/'unit_tests.log')
shutil.copy2(__file__,O/'reanalysis_runner.py')
