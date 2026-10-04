"""Read-only independent checks of end algebra against exported native fixtures."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
SOURCE=ROOT/'Scripts/routeA/diagnostic_transient/v1_2'
sys.path.insert(0,str(SOURCE));import replay_evaluator as evaluator
BASE=Path(__file__).resolve().parent/'final'
prov=json.loads((BASE/'build/build_provenance.json').read_text())
assert hashlib.sha256((SOURCE/'replay_evaluator.py').read_bytes()).hexdigest()==prov['implementation_sha256']['replay_evaluator.py']
records=[json.loads(p.read_text()) for p in sorted((BASE/'tests/observed_1').glob('[0-9]*.json'))]
replayed=json.loads((BASE/'tests/observed_1.replay.json').read_text());end=replayed['synchronization'][0]['energy_end_terms']
checks=[]
assert evaluator.norms([2.,-4.],[1.,2.])=={'signed_global':-2.,'absolute_global':6.,'local_volume_L1':2.,'local_Linf':2.},'INHERITED_VOLUME_WEIGHTED_MEAN_L1'
def compare(name,actual,expected,bound):
    defect=max(abs(x-y) for x,y in zip(actual,expected));assert len(actual)==len(expected) and defect<=bound,(name,defect,bound)
    checks.append({'name':name,'maximum_absolute_defect':defect,'stored_arithmetic_allowance':bound})
fixtures={r['payload']['fixture_kind']:r['payload'] for r in records if 'fixture_kind' in r['payload']}
for fixture,term,sign in [('D_energy_storage_only','S_e',1),('E_wall_conduction','H_out',1),('F_gravity_work','W_g',-1),('G_pressure_work','W_p',1)]:
    m=fixtures[fixture]['matrix'];_,_,floor=evaluator.replay_matrix(m)
    compare('end_'+term+'_versus_isolated_native',end[term],[sign*x for x in m['native_lhs_minus_rhs']],floor+64*math.ulp(1.)*sum(abs(x) for x in end[term]))
last=next(r for r in reversed(records) if r['metadata']['stage']=='energy_after_solve')
for term in ['F_e','F_K']:
    compare('end_'+term+'_versus_native_last_assembly',end[term],last['payload']['term_actions'][term],last['payload']['unrelaxed_matrix']['arithmetic_bound']+64*math.ulp(1.)*sum(abs(x) for x in end[term]))
for r in records:
    p=r['payload'];meta=r['metadata']
    if meta['stage']!='term_capture' or p['term']!='S_K':continue
    state=p['native_state_epoch'];h=meta['deltaT'];k=p['effective_previous_deltaT'];a=1+h/(h+k);c=h*h/(k*(h+k));b=a+c
    assert k==(1/math.ulp(1.) if p['pre_operator_n_old_times']<2 else meta['previous_deltaT'])
    expected=[];products=[]
    for i,v in enumerate(state['volumes']):
        rr=state['rho'];kk=state['K'];row=[a*rr['cells'][i]*kk['cells'][i],-b*rr['old_times'][0]['cells'][i]*kk['old_times'][0]['cells'][i],c*rr['old_times'][1]['cells'][i]*kk['old_times'][1]['cells'][i]]
        expected.append(v*math.fsum(row)/h);products.extend(abs(v*x/h) for x in row)
    compare('native_S_K_old_product_'+str(meta['outer']),p['integrated_cells'],expected,64*math.ulp(1.)*math.fsum(products))
result={'status':'PASS','classification':'SYNTHETIC_EVALUATOR_TEST','checks':len(checks),'identities':checks,'end_energy_terms_verified_against_actual_native_export':['S_e','S_K(old-product path)','F_e','F_K','W_p','H_out','W_g'],'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'no_native_reassembly':True,'no_CFD':True,'inherited_local_L1_normalization':'PASS'}
(BASE.parent/'end_state_native_identity_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='identities'},indent=2))
