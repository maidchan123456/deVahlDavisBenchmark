"""Manufactured binding policy tests, distinct from the native integration test."""
import copy,json,math
from pathlib import Path
import online_evaluator,persistence,packed
from live_collector import Live,Arrival
from primary_evidence import policy
H=Path(__file__).resolve().parent;R=H.parents[3];OUT=R/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/resource_revision_fix';ROOT=OUT/'live_native_sealed_input/on'
class FakeWriter:
    def __init__(self):self.alerts=[];self.anomalies=0;self.fields=[];self.published={}
    def publish(self,name,raw,kind):self.published[name]=raw
    def anomaly(self,reason):self.alerts.append(reason);self.anomalies+=1
    def snapshot(self,state,name):self.fields.append(name)
class SubsetLedger:
    def __init__(self):self.epochs={}
    def accept(self,r):self.last=r['metadata']['stage']
    def finish(self):assert self.last=='time_end'
def main():
    contract=json.loads((R/'docs/routeA_diagnostic_transient_contract_v1.2.json').read_text());contract['live_provenance']={'input_hash':'0'*64,'evaluator_hash':'1'*64}
    geometry=packed.decode((ROOT/'live_geometry.bin').read_bytes());initial=persistence.restore(packed.decode((ROOT/'initial_state.bin').read_bytes()),ROOT)
    records=list(persistence.iter_bundle_file(ROOT,next(ROOT.glob('full_*.bin')).name));m=records[0]['metadata'];gen=online_evaluator.evaluate(iter(records),m['study_guard_sha256'],m['source_set_sha256'],m['instrumentation_sha256'],SubsetLedger)
    receipts=[]
    while True:
        try:receipts.append(next(gen))
        except StopIteration:break
    w=FakeWriter();live=Live(w,contract,False)
    for stage,h in [('constructor_complete',m['previous_deltaT']),('preSolve_after',m['previous_deltaT']),('controller_complete',m['deltaT'])]:
        meta=dict(m,stage=stage,physical_time=m['physical_time']-m['deltaT'],deltaT=h)
        live.accept({'metadata':meta,'payload':{'native_state_epoch':initial},'live_binding':geometry if stage=='constructor_complete' else {'linear':[]}}, {'synchronization':[],'valid':True})
    for r,q in zip(records,receipts):live.accept(r,q)
    assert live.outer_certificate()['status']=='PASS';assert live.outer_certificate()['linear_status']=='PASS'
    terminal=records[-1];receipt=receipts[-1]
    # Build a passing near-limit geometric contraction with explicit synthetic T arrays.
    base=copy.deepcopy(live.outer[-1][0]);states=[];temperature=base['T']['cells'][0]
    steps=[9e-8,4.41e-8,2.1609e-8,1.058841e-8];offset=0.
    for j in range(5):
        if j:offset+=steps[j-1]
        s=copy.deepcopy(base);s['T']['cells']=[temperature+offset]*len(s['T']['cells']);states.append((s,copy.deepcopy(live.outer[-1][1])))
    live.outer.clear();live.outer.extend(states)
    near=live.outer_certificate();assert near['status']=='PASS' and max(near['changes']['T'])>.8*policy.OUTER_CHANGE_LIMIT
    # Calling actual collector end-step executes the registered anomaly branch.
    live.arrival=Arrival(contract['physical_problem'],contract);live.previous_diagnostics={'mass_balance_residual':0.,'energy_balance_residual_end':0.,'rho_sync_Linf':0.}
    live.accept(terminal,receipt);assert 'U01_NEAR_FAILURE' in w.alerts
    live.outer[-1][0]['T']['cells'][0]+=1e-3;live.linear[0]['final']=1e-2
    live.arrival=Arrival(contract['physical_problem'],contract);live.accept(terminal,receipt)
    assert {'U01_FAILURE','LINEAR_FAILURE'}<=set(w.alerts)
    # Controller failure uses the same native-state observation function.
    controller=dict(m,stage='controller_complete',deltaT=.1)
    live.accept({'metadata':controller,'payload':{'native_state_epoch':initial},'live_binding':{'linear':[]}}, {'synchronization':[],'valid':True});assert 'CONTROLLER_ANOMALY' in w.alerts
    row=json.loads(w.published['primary_000001.jsonl'].splitlines()[-1]) if 'primary_000001.jsonl' in w.published else json.loads(live.rows[-1])
    live.outer.clear();live.outer.extend(states);live.linear[0]['final']=0.;live.arrival=Arrival(contract['physical_problem'],contract)
    for i in range(50):live.arrival.add(dict(row,dimensionless_time=i/100,validity=True))
    endpoint=copy.deepcopy(terminal);endpoint['metadata']['physical_time']=355.;endpoint['metadata']['time_index']+=1
    live.accept(endpoint,receipt);assert {'ARRIVAL_CANDIDATE_TRANSITION','ARRIVAL_CONFIRMED'}<=set(w.alerts) and len(w.fields)>=2
    # Raw-capture anomaly thresholds are health/relative-change triggers, not conservation acceptance.
    assert any(x.startswith('DIAGNOSTIC_RELATIVE_CHANGE_energy') for x in w.alerts)
    # Frozen U02/03 direct comparisons, including nonuniform integration.
    for target in (.5,.25,.125):
        for co in (0.,.1,1.,10.):assert policy.controller_step(.001,co,target)==min(.0012,min(policy.MAX_DT,target/co*.001) if co else policy.MAX_DT)
    a=Arrival(contract['physical_problem'],contract);history=dict(row)
    for t in (0.,.01,.031,.073,.12,.155,.203,.277,.319,.379,.419,.477,.50001):a.add(dict(history,dimensionless_time=t,validity=True))
    assert a.confirmed and all(abs(a.confirmed['final_mean'][k]-row[k])<=64*math.ulp(max(1.,abs(row[k]))) for k in ('Nu_bar_cavity','Umax','Wmax'))
    report={'status':'PASS','classification':'MANUFACTURED_POLICY_AND_BINDING_UNIT_TEST_NOT_CFD','anomaly_branches_observed':sorted(set(w.alerts)),'arrival_selected_fields':len(w.fields),'native_sample_reduction_reused':True,'near_failure_certificate':'PASS_CONTRACTING_BELOW_FROZEN_LIMIT','nonuniform_U03_policy':'PASS','frozen_U02_controller':'PASS','no_physical_threshold_added':True}
    (OUT/'live_policy_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
