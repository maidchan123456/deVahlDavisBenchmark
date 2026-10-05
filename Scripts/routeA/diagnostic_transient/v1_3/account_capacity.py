"""Actual compact schema + conservative typed 25600-cell planning, no CFD."""
import csv,json,math,os,sys,struct
from pathlib import Path
import online_evaluator as online,packed,persistence as persistence
H=Path(__file__).resolve().parent;R=H.parents[3];PREP=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';OUT=PREP/'resource_revision'
CELL={'cells','diag','source','volumes','native_lhs_minus_rhs','integrated_cells','Cv'}
FACE={'upper','lower','owner','neighbour','internal','linear_weights'}
BOUNDARY={'values','face_cells','internal_coeffs','boundary_coeffs'}
STATIC={'geometry','volumes','Cv','g','owner','neighbour'}
def numeric(x):
    if type(x) in (int,float):return 1
    if isinstance(x,list):return sum(numeric(v) for v in x)
    if isinstance(x,dict):return sum(numeric(v) for v in x.values())
    return 0

def typed(x,path=()):
    if isinstance(x,list):
        if x and (path[-1] in CELL or 'term_actions' in path):return numeric(x)*25600/len(x)*8
        if x and path[-1] in FACE:return numeric(x)*50880/len(x)*8
        if x and path[-1] in BOUNDARY:return numeric(x)*640/len(x)*8
        return sum(typed(v,path) for v in x)
    if isinstance(x,dict):return sum(typed(v,path+(k,)) for k,v in x.items())
    return 8 if type(x) in (int,float) else 0

def remove_known(x):
    if isinstance(x,dict):return {k:remove_known(v) for k,v in x.items() if k not in STATIC}
    if isinstance(x,list):return [remove_known(v) for v in x]
    return x

def main():
    root=PREP/'u04_verification/final/tests/observed_1';rs=[json.loads(p.read_text()) for p in sorted(root.glob('[0-9]*.json'))];m=rs[0]['metadata']
    gen=online.evaluate(iter(rs),m['study_guard_sha256'],m['source_set_sha256'],m['instrumentation_sha256']);receipts=[]
    while True:
        try:receipts.append(next(gen))
        except StopIteration:break
    skipped={'constructor_complete','preSolve_before','preSolve_after','controller_complete','auxiliary_fixture'}
    selected=[];project=0;bundle_project=0;rows=[];receipt_size=0
    for r,receipt in zip(rs,receipts):
        c=persistence.receipt_bytes(receipt);size=72+8*len(c['values'])
        if r['metadata']['stage'] in skipped:continue
        receipt_size+=size
        pl=r['payload'];ns=pl['native_state_epoch'];fresh=dict(pl)
        if fresh.get('state')==ns:fresh.pop('state')
        elif fresh.get('state_epoch') and {k:v for k,v in pl.items() if k not in {'native_state_epoch','thermal_context'}}==ns:
            for k in ns:fresh.pop(k)
        pr=remove_known(dict(r,payload=fresh))
        arrays=typed(pr);metadata=len(packed.encode(pr))
        # No credit for coincident equal arrays in the tiny manufactured fixture.
        # 1 extra type byte per typed value is a worst-case mixed JSON-number mask.
        estimate=arrays*9/8+metadata+4096
        project+=estimate
        mm=r['metadata'];s=mm['stage'];is_bundle=mm['outer']==24 or mm['outer']==1 and mm['pressure']==0 and (s in {'before_correctDensity','mass_unrelaxed_assembly','mass_after_solve','after_correctDensity'} or s=='term_capture' and pl['term'] in {'D_B_rho','div_phi','mass_models'})
        if is_bundle:bundle_project+=estimate
        rows.append({'stage':s,'receipt_bytes':size,'typed_array_projection':arrays,'conservative_packed_projection':estimate,'selected_bundle':is_bundle})
    need=persistence.need
    need(project<=persistence.AUDIT_CAP,'PLANNED_AUDIT_CAP_INSUFFICIENT')
    need(bundle_project<=persistence.BUNDLE_CAP,'PLANNED_BUNDLE_CAP_INSUFFICIENT')
    contract=json.loads((R/'docs/routeA_diagnostic_transient_contract_v1.2.json').read_text());sv=os.statvfs(R);free=sv.f_bavail*sv.f_frsize
    # Chunk schema table occurs once per chunk. 16KiB upper allowance must be
    # measured/checked separately, rather than pretending every stage costs O(N).
    chunk_schema_budget=16*2**10
    compact_per_step=receipt_size+8192+65536
    scenarios=[]
    for star in [.5,1.,2.]:
        series=[]
        for co in ['0.5','0.25','0.125']:
            h=contract['courant_control']['scales']['prospective_h_by_Co_s'][co];steps=math.ceil(710*star/h);chunks=math.ceil(steps/64)
            full=3+sum(t<=star for t in [.5,1,1.5,1.99]);bundles=math.floor(star/.05+1e-9)+16;fields=51+math.floor((star-.05)/.005+1e-9)+64
            parts={'receipts_and_primary':steps*(receipt_size+8192)+chunks*chunk_schema_budget,'full_raw_audits':full*persistence.AUDIT_CAP,'selected_bundles':bundles*persistence.BUNDLE_CAP,'field_snapshots':fields*persistence.FIELD_CAP,'complete_solver_logs':steps*65536,'fixed_provenance_and_static':2**30}
            retained=sum(parts.values());files=chunks+chunks+full+bundles+fields+64 # receipt/log chunks, audits, fields, fixed/source/blobs/root
            series.append({'Co':co,'steps':steps,'receipt_chunks':chunks,'log_chunks_4MiB':chunks,'manifest_files':1,'full_raw_audits':full,'selected_bundles':bundles,'field_snapshots':fields,'retained_bytes':retained,'file_count_bound':files,'parts':parts})
        primary=sum(s['retained_bytes'] for s in series[:2]);third=sum(s['retained_bytes'] for s in series)
        scenarios.append({'t_star':star,'series':series,'primary_retained_bytes':primary,'primary_peak_bytes':primary+persistence.SCRATCH_CAP,'primary_peak_fraction_of_free':(primary+persistence.SCRATCH_CAP)/free,'three_retained_bytes':third,'three_peak_bytes':third+persistence.SCRATCH_CAP,'three_peak_fraction_of_free':(third+persistence.SCRATCH_CAP)/free,'primary_file_count':sum(s['file_count_bound'] for s in series[:2]),'three_file_count':sum(s['file_count_bound'] for s in series)})
    memory={'packed_recent16_stage_cap_bytes':min(persistence.RING_CAP,16*persistence.STAGE_CAP),'selected_bundle_cap_bytes':persistence.BUNDLE_CAP,'compact_chunk_cap_bytes':64*2**20,'transient_stage_encode_cap_bytes':persistence.STAGE_CAP,'final_field_buffer_cap_bytes':persistence.FIELD_CAP,'buffer_bytes_bound':min(persistence.RING_CAP,16*persistence.STAGE_CAP)+persistence.BUNDLE_CAP+64*2**20+persistence.STAGE_CAP+persistence.FIELD_CAP,'audit_scratch_cap_bytes':persistence.AUDIT_CAP,'scratch_total_cap_bytes':persistence.SCRATCH_CAP,'full_raw_step_in_memory':False,'native_address_space_limit_bytes':8*2**30,'backend_address_space_limit_bytes':8*2**30,'total_process_virtual_memory_cap_bytes':16*2**30,'production_target_RSS':'UNMEASURED','temporary_JSON_transport_and_retained_evaluator_objects':'within process AS caps only; allocation failure stops; no proof target data fit under caps'}
    result={'classification':'PLANNING_ESTIMATE_ONLY','current_free_bytes':free,'free_inodes':sv.f_favail,'receipt_binary_bytes_per_physical_step':receipt_size,'primary_reserve_bytes_per_step':8192,'complete_log_reserve_bytes_per_step':65536,'chunk_schema_table_budget_bytes':chunk_schema_budget,'full_raw_packed_projection_per_step':project,'selected_bundle_packed_projection_bytes':bundle_project,'projection_scope':'Static mesh/Cv/g/address data stored once; only byte-identical known state/native_state duplication credited. No speculative synthetic cross-array equality/compression credit. Includes worst-case type masks and metadata allowance. Caps are fail-closed budgets, not production measurements.','scenarios':scenarios,'memory':memory,'no_production_CFD':True}
    (OUT/'capacity_accounting.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,data in [('DiagnosticTransient_v1_3_storage_model.csv',rows),('DiagnosticTransient_v1_3_resource_scenarios.csv',[{k:v for k,v in s.items() if k!='series'} for s in scenarios]),('DiagnosticTransient_v1_3_evidence_schedule.csv',[dict(t_star=sc['t_star'],**{k:v for k,v in se.items() if k!='parts'}) for sc in scenarios for se in sc['series']])]:
        with (PREP/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    print(json.dumps({'raw_project_GB':project/1e9,'bundle_project_GB':bundle_project/1e9,'receipt_step_bytes':receipt_size,'scenarios':[{k:v for k,v in s.items() if k!='series'} for s in scenarios]},indent=2))
if __name__=='__main__':main()
