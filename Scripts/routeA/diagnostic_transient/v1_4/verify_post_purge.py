"""Additional independent retained-field reproduction and class-override attack checks."""
import hashlib,json
from pathlib import Path
import lifecycle,series_validation
H=Path(__file__).resolve().parent;R=H.parents[3];OUT=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/resource_revision_fix'
def main():
    report=json.loads((OUT/'lifecycle_validation.json').read_text());root=OUT/'lifecycle_test_verified/seriesA';lifecycle.Series(root).verify(report['seal_id'])
    physical=json.loads((R/'docs/routeA_diagnostic_transient_contract_v1.2.json').read_text())['physical_problem'];reproduced=series_validation.reproduce_primary_from_R2(root,physical)
    target=OUT/'lifecycle_test_core_override';target.mkdir(exist_ok=False);failures=[]
    for cls,name in [('R0','primary_000001.jsonl'),('R1','final_bundle.bin'),('R2','final_fields.bin')]:
        p=target/cls;p.mkdir();(p/name).write_bytes(b'SYNTHETIC_RETENTION_ATTACK_FIXTURE');s=lifecycle.Series(p);s.begin();prov={k:'0'*64 for k in lifecycle.PROVENANCE}
        try:s.seal({name:'R3'},{'case_id':cls,'Co':.5,'start_time':0.,'end_time':1.,'classification':'SYNTHETIC_RETENTION_ATTACK_TEST'},prov,lambda p:{'checks':{k:'PASS' for k in lifecycle.CHECKS},'limitations':[]})
        except ValueError as e:assert 'RETENTION_CLASS_VIOLATION' in str(e);failures.append({'test':cls+'_incorrectly_classified_R3_at_seal','status':'FAIL_CLOSED','reason':str(e)})
        else:raise AssertionError('CORE_CLASS_OVERRIDE_ALLOWED')
    report['independent_final_primary_from_retained_R2']=reproduced;report['failure_injections'].extend(failures)
    (OUT/'lifecycle_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'post_purge_R2_validation.json').write_text(json.dumps(reproduced,indent=2)+'\n');print(json.dumps(reproduced,indent=2))
if __name__=='__main__':main()
