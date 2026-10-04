"""Read-only planning envelope from frozen v1.1 and synthetic payload layout."""
import argparse,json,math,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CELL={'cells','diag','source','volumes','native_lhs_minus_rhs','integrated_cells'}
FACE={'upper','lower','owner','neighbour','internal'}
BOUNDARY={'values','face_cells','internal_coeffs','boundary_coeffs'}
LABEL={'owner','neighbour','face_cells'}
def nums(x):
    if isinstance(x,bool):return 0
    if isinstance(x,(int,float)):return 1
    if isinstance(x,list):return sum(map(nums,x))
    if isinstance(x,dict):return sum(nums(v) for v in x.values())
    return 0
def projected_numeric_bytes(x,path=()):
    if isinstance(x,list):
        key=path[-1] if path else ''
        if x and (key in CELL or 'term_actions' in path):return nums(x)*25600/len(x)*8
        if x and key in FACE:return nums(x)*50880/len(x)*(4 if key in LABEL else 8)
        if x and key in BOUNDARY:return nums(x)*640/len(x)*(4 if key in LABEL else 8)
        return sum(projected_numeric_bytes(v,path) for v in x)
    if isinstance(x,dict):return sum(projected_numeric_bytes(v,path+(k,)) for k,v in x.items())
    return 8 if isinstance(x,(int,float)) and not isinstance(x,bool) else 0

def estimate(stream):
    parent=json.loads((ROOT/'docs/routeA_diagnostic_transient_contract_v1.1.json').read_text())
    records=[json.loads(p.read_text()) for p in sorted(Path(stream).glob('[0-9]*.json'))]
    physical=[r for r in records if r['metadata']['stage'] not in {'auxiliary_fixture','constructor_complete','preSolve_before','preSolve_after','controller_complete'}]
    per_step=sum(projected_numeric_bytes(r) for r in physical)
    field_step=8*(25600*(5+3)+50880) # five scalar +Uvector+internalphi; boundary/headers excluded
    duration=parent['duration']['maximum_t_star']*parent['dimensionless_time']['t_char_s']
    prospective=parent['courant_control']['scales']['prospective_h_by_Co_s'];max_steps=parent['courant_control']['maximum_steps']
    series={co:{'prospective_constant_h_s':h,'planning_steps':math.ceil(duration/h),'numeric_payload_equivalent_bytes':math.ceil(duration/h)*(per_step+field_step)} for co,h in prospective.items()}
    free=shutil.disk_usage(ROOT).free
    primary=sum(series[co]['numeric_payload_equivalent_bytes'] for co in ['0.5','0.25'])
    worst=2*max_steps*(per_step+field_step)
    return {'classification':'PLANNING_ESTIMATE_ONLY','frozen_contract_version':'1.1','U01_U03_changed':False,'cell_count':25600,'internal_faces':50880,'active_boundary_faces':640,'records_per_physical_step':len(physical),'diagnostic_numeric_payload_Float64_equivalent_bytes_per_step':per_step,'full_field_numeric_bytes_per_step':field_step,'series_planning_envelope':series,'primary_numeric_payload_equivalent_bytes':primary,'two_series_step_watchdog_numeric_equivalent_bytes':worst,'available_filesystem_bytes':free,'resource_feasibility_concern':primary>free,'resource_feasibility_review_required':primary>free,'limitations':['No CFD stepcount/runtime inferred. Prospective h scales are inherited acceptedsteady estimates, not actual adaptiveh.','Byte figure is uncompressed numerical-payload equivalent with actual native cells/faces projected from synthetic schema, not measured actualJSON size or a disk lowerbound. Field count conservative; strings/headers/precision/compression maychange bytes.','No changes to24outer,cadence,duration or diagnostic tolerance. Resource review must decide feasibility before RUN.','Synthetic timing/memory figures do not predict production runtime.']}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stream');ap.add_argument('output');a=ap.parse_args();result=estimate(a.stream);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
