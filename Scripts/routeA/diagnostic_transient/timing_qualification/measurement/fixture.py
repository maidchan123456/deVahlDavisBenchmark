"""Read-only actual topology and resource-only packet/matrix fixtures. No CFD imports."""
import collections,copy,json,math,re
from pathlib import Path
from common import ROOT,PREP,PLAN,load,sha,need
from persistence import iter_bundle_file
from online_evaluator import StageLedger

MESH=ROOT/'cases/routeA/A-Ra1e6-fine/constant/polyMesh'

def body(path):
 text=path.read_text();need('format      ascii;' in text,'STOP_MESH_FORMAT')
 text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
 text=re.sub(r'FoamFile\s*\{.*?\}','',text,flags=re.S)
 return text.strip()

def labels(path):
 text=body(path);m=re.fullmatch(r'(\d+)\s*\(\s*([\s\d-]*)\s*\)',text)
 need(m is not None,'STOP_LABEL_LIST');v=[int(x) for x in m[2].split()];need(len(v)==int(m[1]),'STOP_LABEL_COUNT');return v

def topology(path=MESH,target=True):
 path=Path(path);need(not path.is_symlink(),'STOP_MESH_SYMLINK')
 own=labels(path/'owner');nei=labels(path/'neighbour');n=max(own)+1
 text=body(path/'boundary');patches=[]
 for name,block in re.findall(r'(\w+)\s*\{([^{}]*)\}',text):
  def val(k):return re.search(r'\b'+k+r'\s+(\w+)\s*;',block)[1]
  p={'name':name,'type':val('type'),'nFaces':int(val('nFaces')),'startFace':int(val('startFace'))};p['face_cells']=own[p['startFace']:p['startFace']+p['nFaces']] if p['type']!='empty' else [];patches.append(p)
 need(all(0<=v<n for v in own+nei) and len(nei)<len(own),'STOP_TOPOLOGY_ADDRESSING')
 need(len(set((o,q) for o,q in zip(own,nei)))==len(nei),'STOP_DUPLICATE_INTERNAL_FACE')
 counts={'nCells':n,'nInternalFaces':len(nei),'nFaces':len(own),'active':sum(p['nFaces'] for p in patches if p['type']!='empty'),'empty':sum(p['nFaces'] for p in patches if p['type']=='empty')}
 if target:
  t=load(PLAN)['Q1_design']['topology'];expected={k:t[v] for k,v in [('nCells','cells'),('nInternalFaces','internal_faces'),('nFaces','total_faces'),('active','active_boundary_faces'),('empty','empty_faces')]}
  need(counts==expected,'STOP_TARGET_TOPOLOGY')
  need([(p['name'],p['type'],p['nFaces']) for p in patches]==[('hotWall','wall',160),('coldWall','wall',160),('bottomWall','wall',160),('topWall','wall',160),('front','empty',25600),('back','empty',25600)],'STOP_PATCH_TOPOLOGY')
 need([p['startFace'] for p in patches]==[len(nei)+sum(q['nFaces'] for q in patches[:i]) for i in range(len(patches))] and sum(p['nFaces'] for p in patches)+len(nei)==len(own),'STOP_PATCH_COVERAGE')
 return dict(counts=counts,owner=own[:len(nei)],neighbour=nei,patches=patches,mesh_SHA256={str(f):sha(f) for f in sorted(path.iterdir()) if f.is_file()},classification='RESOURCE_QUALIFICATION_FIXTURE_ONLY')

def tiny_topology():
 return {'counts':{'nCells':4,'nInternalFaces':4,'nFaces':20,'active':16,'empty':0},'owner':[0,0,1,2],'neighbour':[1,2,3,3],'patches':[{'name':'walls','type':'wall','nFaces':16,'startFace':4,'face_cells':[i//4 for i in range(16)]}],'mesh_SHA256':{},'classification':'TINY_SELF_TEST_ONLY'}

def validate_graph(nodes):
 need(len(nodes)==1145,'STOP_CALLBACK_GRAPH')
 ledger=StageLedger()
 for r in nodes:ledger.accept(r)
 ledger.finish()
 need(sum(sum(k in r['payload'] for k in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix')) for r in nodes)==701,'STOP_MATRIX_GRAPH')
 classes=collections.Counter((r['metadata']['stage'],r['payload'].get('term','')) for r in nodes[1:]);expected=collections.Counter()
 for row in load(PLAN)['callback_classes']:expected[(row['callback_type'],row['term'])]+=row['frequency_per_step']
 need(classes==expected,'STOP_CALLBACK_TAXONOMY')
 return True

def graph():
 source=PREP/'compute_review/native_0_on/full_2.bin';need(sha(source)==load(PLAN)['authority_sha256'][str(source.relative_to(ROOT))],'STOP_CALLBACK_SOURCE_SHA256')
 records=list(iter_bundle_file(source.parent,source.name))
 physical=[r for r in records if r['metadata']['time_index']==2]
 need(len(physical)==1141,'STOP_CALLBACK_GRAPH')
 first=copy.deepcopy(physical[0]);nodes=[]
 for stage in ('constructor_complete','preSolve_before','preSolve_after','controller_complete'):
  r=copy.deepcopy(first);r['metadata']['stage']=stage;r['metadata']['time_index']=0 if stage=='constructor_complete' else 2;r['live_binding']={'linear':[]};nodes.append(r)
 nodes+=physical
 for i,r in enumerate(nodes,1):r['sequence']=i
 ledger=StageLedger()
 for r in nodes:ledger.accept(r)
 ledger.finish()
 mat=sum(sum(k in r['payload'] for k in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix')) for r in physical)
 need(mat==701,'STOP_MATRIX_GRAPH')
 validate_graph(nodes);return nodes

DIMS={'rho':[1,-3,0,0,0,0,0],'rhoFluidThermo:rho':[1,-3,0,0,0,0,0],'T':[0,0,0,1,0,0,0],'e':[0,2,-2,0,0,0,0],'K':[0,2,-2,0,0,0,0],'p':[1,-1,-2,0,0,0,0],'p_rgh':[1,-1,-2,0,0,0,0],'gh':[0,2,-2,0,0,0,0]}

def state(topo,index=2):
 n=topo['counts']['nCells'];v=[1e-9]*n;out={}
 for name,dims in DIMS.items():
  value={'rho':1.,'rhoFluidThermo:rho':1.,'T':3.,'e':6.}.get(name,0.)
  patches=[{'name':p['name'],'type':'empty' if p['type']=='empty' else ('fixedValue' if name in ('T','e') else 'zeroGradient'),'values':[value]*len(p['face_cells']),'updated':False,'manipulated_matrix':False} for p in topo['patches']]
  olds=[]
  if name in ('rho','e','K'):
   for level in range(1,min(index,2)+1):olds.append({'name':name+('_0'*level),'dimensions':dims,'cells':[value]*n,'patches':[{k:p[k] for k in ('name','type','values')} for p in patches],'history_level':level,'represented_time_index':index-level,'represented_physical_time':.3-.1*level,'time_index':index-level,'value_sha256':'','object_epoch_sha256':''})
  out[name]={'name':name,'dimensions':dims,'cells':[value]*n,'patches':patches,'time_index':index,'has_stored_old_times':bool(olds),'n_old_times':len(olds),'n_materialized_old_times':len(olds),'old_times':olds,'value_sha256':''}
 out['U']={'dimensions':[0,1,-1,0,0,0,0],'cells':[[0.,0.,0.] for _ in range(n)],'time_index':index,'patches':[{'name':p['name'],'values':[[0.,0.,0.] for _ in p['face_cells']],'updated':False,'manipulated_matrix':False} for p in topo['patches']],'value_sha256':''}
 out['phi']={'dimensions':[1,0,-1,0,0,0,0],'internal':[0.]*len(topo['owner']),'patches':[{'name':p['name'],'values':[0.]*len(p['face_cells']),'face_cells':p['face_cells']} for p in topo['patches']],'value_sha256':''}
 out.update(geometry={'owner':topo['owner'],'neighbour':topo['neighbour'],'linear_weights':[.5]*len(topo['owner'])},volumes=v,state_epoch='')
 return out

def packets(topo,nodes=None):
 nodes=nodes or graph();n=topo['counts']['nCells'];s=state(topo);zero=[0.]*n;h=710./25600;k=.1;a=1+h/(h+k)
 for i,template in enumerate(nodes,1):
  m=copy.deepcopy(template['metadata']);stage=m['stage'];is_start=stage=='constructor_complete';current=state(topo,0) if is_start else s
  m.update(time_index=0 if is_start else 2,physical_time=0. if is_start else .3,deltaT=h,previous_deltaT=k,classification='SYNTHETIC_EVALUATOR_TEST',case_identity='RESOURCE_QUALIFICATION_FIXTURE_ONLY',study_guard_sha256=sha(ROOT/'docs/routeA_diagnostic_transient_contract_v1.5.json'))
  p={'native_state_epoch':current,'thermal_context':{'Cv':[2.]*n,'g':[0.,0.,0.]}}
  original=template['payload'];term=original.get('term','')
  if 'term' in original:p['term']=term
  def matrix(matkey,old):
   name=old['psi_name'];density=name=='rho';pressure=name=='p_rgh';diag=[a*1e-9/h if density or name=='e' else 0.]*n
   if pressure:diag=[1.]*n
   if term and term not in ('D_B_rho','S_e'):diag=[0.]*n
   referenced=pressure and (stage=='pressure_post_reference' or (stage=='pressure_solved' and matkey!='physical_matrix'))
   if referenced:diag[0]*=2
   value={'rho':1.,'e':6.}.get(name,0.)
   mat={'psi_name':name,'psi':current[name],'dimensions':old['dimensions'],'volumes':current['volumes'],'diag':diag,'source':[d*value for d in diag],'has_diag':True,'has_upper':old['has_upper'],'has_lower':old['has_lower'],'upper':[0.]*len(topo['owner']) if old['has_upper'] or old['has_lower'] else [],'lower':[0.]*len(topo['owner']) if old['has_upper'] or old['has_lower'] else [],'owner':topo['owner'],'neighbour':topo['neighbour'],'patches':[{'name':fp['name'],'type':fp['type'],'face_cells':t['face_cells'],'internal_coeffs':[0.]*len(t['face_cells']),'boundary_coeffs':[0.]*len(t['face_cells']),'updated':False,'manipulated_matrix':False} for t,fp in zip(topo['patches'],current[name]['patches'])],'native_lhs_minus_rhs':zero,'arithmetic_bound':0.,'matrix_epoch':''}
   return mat
  for key in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix'):
   if key in original and not is_start:p[key]=matrix(key,original[key])
  if 'state' in original:p['state']=current
  if 'integrated_cells' in original:p.update(integrated_cells=zero,dimensions=original['dimensions'],operator_dimensions=original['operator_dimensions'])
  if 'pre_operator_n_old_times' in original:p.update(pre_operator_n_old_times=2,effective_previous_deltaT=k)
  if 'term_actions' in original:p['term_actions']={key:zero for key in original['term_actions']}
  if 'ref_cell' in original:p.update(ref_cell=0,ref_value=0.)
  if stage in ('constructor_complete','preSolve_before','preSolve_after','controller_complete') or stage not in ('term_capture','energy_unrelaxed_assembly','energy_after_relax','energy_after_solve','mass_unrelaxed_assembly','mass_after_solve','pressure_pre_reference','pressure_post_reference','pressure_solved'):
   p.update(current)
  binding=copy.deepcopy(template.get('live_binding',{'linear':[]}))
  for row in binding.get('linear',[]):row.update(initial=0.,final=0.,iterations=0)
  if is_start:
   binding={'linear':[],'target_Co':.5,'adjustTimeStep':True,'maxDeltaT':710./25600,'centres':[[.025+.05*(j%2),.025+.05*(j//2),.0005] for j in range(n)] if n==4 else [[.1*(j%160+.5)/160,.1*(j//160+.5)/160,.0005] for j in range(n)],'Sf':[[0.,0.,0.] for _ in topo['owner']],'patch_geometry':[{'name':t['name'],'face_cells':t['face_cells'],'delta':[1.]*len(t['face_cells']),'Sf':[[0.,0.,0.] for _ in t['face_cells']]} for t in topo['patches']]}
  yield {'metadata':m,'payload':p,'sequence':i,'live_binding':binding,'payload_sha256':''}
