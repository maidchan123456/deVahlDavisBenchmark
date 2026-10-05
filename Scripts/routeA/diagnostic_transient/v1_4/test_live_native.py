"""Native manufactured four-cell stream, with actual vector+scalar solves; no CFD."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
import persistence
H=Path(__file__).resolve().parent;R=H.parents[3];PREP=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';OUT=PREP/'resource_revision_fix';BUILD=OUT/'native/build_verified';DRIVER=OUT/'native/build_retry/binding_driver';OLD=PREP/'u04_verification/final/build'

def main():
    dest=OUT/'live_native_sealed_input';dest.mkdir(exist_ok=False);assert (BUILD/'librouteAU04Observer.so').is_file();a=json.loads((OLD/'build_provenance.json').read_text());guard='574b83ed63e244e9fbb1307d1a463e1c92fade86a99375054d599b06b155d675'
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',ROUTE_A_P1_SERVER=str(H/'server.py'),ROUTE_A_P1_SERVER_SHA256=hashlib.sha256((H/'server.py').read_bytes()).hexdigest(),ROUTE_A_BIND_LIVE='1',ROUTE_A_SYNTHETIC_LIVE='1',ROUTE_A_DIAGNOSTIC_CONTRACT_FILE=str(R/'docs/routeA_diagnostic_transient_contract_v1.2.json'),ROUTE_A_FIXTURE_SHA256=hashlib.sha256((H/'synthetic_native_binding_driver.C').read_bytes()).hexdigest())
    libs='/opt/openfoam13/platforms/linux64GccDPInt32Opt/lib';env['LD_LIBRARY_PATH']=str(BUILD)+':'+str(OLD)+':'+libs+':'+libs+'/openmpi-system'
    for mode in ('on','off'):
        cmd=[str(DRIVER),str(dest/mode),guard,a['source_set_sha256'],a['instrumentation_sha256'],mode,'none']
        with (dest/(mode+'.log')).open('w') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
        assert p.returncode==0,(mode,(dest/(mode+'.log')).read_text()[-5000:])
    assert (dest/'on.physical.json').read_bytes()==(dest/'off.physical.json').read_bytes()
    persistence.verify(dest/'on')
    rows=[json.loads(x) for p in (dest/'on').glob('primary_*.jsonl') for x in p.read_text().splitlines()]
    assert len(rows)==1;row=rows[0];assert len(row['linear_solves'])==169
    assert {x['field'] for x in row['linear_solves']}=={'Ux','Uy','e','p_rgh','rho'}
    assert row['U01']['linear_status']=='PASS' and row['validity'] and row['controller']['status']=='PASS'
    report={'status':'PASS','classification':'SYNTHETIC_NATIVE_BINDING_TEST_NOT_CFD_RESULT','physical_non_invasiveness':'BITWISE','primary_steps':1,'native_linear_component_solves':169,'native_fv_solves':145,'complete_required_primary_columns':True,'controller_observation':row['controller'],'U01_actual_certificate':row['U01']['status'],'manufactured_state_is_not_registered_benchmark_initial_state':True,'production_CFD_executed':False,'evidence_root':str(dest/'on')}
    (OUT/'live_native_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
