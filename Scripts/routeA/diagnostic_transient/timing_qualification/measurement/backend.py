"""Qualification receiver calling frozen v1.4 evaluator/Live/Writer, without CFD."""
import copy,json,os,resource,socket,sys,time,collections,statistics
from common import load,plan,CONTRACT,before_write,atomic,ROOT,sha
import online_evaluator as oe
import persistence as persist
import live_collector as lc

class Span:
 def __init__(self):self.values={};self.depth={}
 def wrap(self,name,f):
  def run(*args,**kwargs):
   depth=self.depth.get(name,0);self.depth[name]=depth+1;t=time.perf_counter()
   try:return f(*args,**kwargs)
   finally:
    self.depth[name]=depth
    if not depth:self.values[name]=self.values.get(name,0.)+time.perf_counter()-t
  return run

def serve(fd,out,budget,purpose="full",event=None,tiny=False):
 if os.environ.get('ROUTE_A_TIMING_SELF_TEST')!='TINY_SELF_TEST_ONLY':
  from runner import verify_stage_execution
  verify_stage_execution(os.environ['ROUTE_A_TIMING_STAGE_RECEIPT'],os.environ['ROUTE_A_TIMING_AUTHORIZATION_FILE'])
 cfg=plan();caps=cfg['stages']['Q1']['budgets'] # cap identity is equal across Q1/Q2
 resource.setrlimit(resource.RLIMIT_AS,(caps['backend_AS_max_bytes'],)*2)
 spans=Span()
 for name in ('canonical','replay_matrix','sha'):
  original=getattr(oe,name)
  def install(name,original):
   timed=spans.wrap(name,original)
   def wrapper(*args,**kwargs):
    setattr(oe,name,original) # recursion uses frozen function; serial backend only
    try:return timed(*args,**kwargs)
    finally:setattr(oe,name,wrapper)
   setattr(oe,name,wrapper)
  install(name,original)
 persist.encode=spans.wrap('packing',persist.encode)
 class Writer(persist.Writer):
  def publish(self,name,raw,kind):
   before_write(out,budget,len(raw)+4096,3)
   return spans.wrap('publish_fsync_manifest',super().publish)(name,raw,kind)
  def accept(self,r,receipt):
   before_write(out,budget,self.stage_cap+4096,3)
   return spans.wrap('persistence_accept',super().accept)(r,receipt)
 writer_root=out/'runtime';before_write(out,budget,4096,1);writer_root.mkdir()
 writer=Writer(writer_root);c=copy.deepcopy(load(CONTRACT));c['live_provenance']={'input_hash':'RESOURCE_QUALIFICATION_FIXTURE_ONLY','evaluator_hash':sha(ROOT/'Scripts/routeA/diagnostic_transient/v1_4/online_evaluator.py')}
 live=lc.Live(writer,c,strict=False)
 live.qoi=spans.wrap('primary_QoI',live.qoi);live.outer_certificate=spans.wrap('U01_certificate',live.outer_certificate)
 sock=socket.socket(fileno=fd);stream=sock.makefile('rwb',buffering=0);current=[None];bytes_in=0;count=0;matrices=0;classes=collections.defaultdict(lambda:{"JSON_bytes":[],"packed_bytes":[]})
 def records():
  nonlocal bytes_in
  while True:
   raw=stream.readline(cfg['Q1_design']['packet_limit_bytes']+1)
   if raw==b'FINISH\n':return
   if not raw or not raw.endswith(b'\n'):raise ValueError('STOP_TRANSPORT_TRUNCATED')
   bytes_in+=len(raw);r=spans.wrap('JSON_decode',json.loads)(raw)
   if r['metadata']['classification']!='SYNTHETIC_EVALUATOR_TEST' or r['metadata']['case_identity']!='RESOURCE_QUALIFICATION_FIXTURE_ONLY':raise ValueError('STOP_FIXTURE_CLASSIFICATION')
   current[0]=r
   key=r['metadata']['stage']+'|'+r['payload'].get('term','');classes[key]['JSON_bytes'].append(len(raw));yield r
 if purpose!='full':
  result_rows=[];memory_packets=[];last_record=None
  from packed import encode
  for r in records():
   p=r['payload'];oe.finite_tree(r);spans.wrap('canonicalization',oe.canonical)(p)
   for key in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix'):
    if key in p:spans.wrap('matrix_replay',oe.replay_matrix)(p[key])
   raw=spans.wrap('packing',encode)(r);spans.wrap('SHA',oe.sha)(raw)
   if r['metadata']['stage']=='constructor_complete':live.geometry=r['live_binding']
   if event and r['metadata']['stage']!='constructor_complete':
    memory_packets.append(raw);last_record=r
    if event=='U01 last5 states':
     state=p['native_state_epoch'];live.outer.append(({k:{'cells':state[k]['cells'],'value_sha256':state[k]['value_sha256']} for k in ('U','T','p_rgh','rho','rhoFluidThermo:rho')},live.qoi(state)))
   else:before_write(out,budget,len(raw)+8192,3);writer.publish('primitive_'+str(len(result_rows))+'.bin',raw,'qualification_primitive')
   result_rows.append({'stage':r['metadata']['stage'],'packed_bytes':len(raw),'serialized_bytes':len(oe.canonical(r).encode())});stream.write(b'OK\n')
  if event:
   from io_memory import memory_event
   spans.wrap('memory_event',memory_event)(out,budget,event,last_record,tiny,memory_packets,live)
  atomic(out,'backend_result.json',{'status':'COMPLETE_ISOLATED_PRIMITIVE_NOT_STEP','rows':result_rows,'spans_seconds_inclusive':spans.values,'event':event},budget);stream.write(b'OK\n');sock.close();return
 gen=oe.evaluate(records(),sha(CONTRACT),c['resource_revision']['native_semantic_source_set_sha256'],c['resource_revision']['native_semantic_parent_instrumentation_sha256'])
 try:
  while True:
   try:receipt=next(gen)
   except StopIteration as end:
    live.finish();writer.finish(end.value)
    atomic(out,'backend_result.json',{'status':'COMPLETE_FIXTURE_NOT_SCIENCE','callbacks_including_constructor':count,'matrix_packets':matrices,'bytes_IPC_received':bytes_in,'spans_seconds_inclusive':spans.values,'span_nesting':'ACK includes backend; do not add ACK to backend spans','evaluator_summary':end.value,'callback_class_bytes':{key:{metric:{'count':len(values),'min':min(values),'median':statistics.median(values),'max':max(values)} for metric,values in row.items() if values} for key,row in classes.items()},'writer_bytes':writer.written_bytes,'writer_fsyncs':writer.fsyncs,'U01_primary_steps':live.steps,'scientific_claim':False},budget)
    stream.write(b'OK\n');break
   count+=1;matrices+=len(receipt['matrix_metrics']);writer.accept(current[0],receipt);classes[current[0]['metadata']['stage']+'|'+current[0]['payload'].get('term','')]['packed_bytes'].append(len(writer.ring[-1]));live.accept(current[0],receipt);stream.write(b'OK\n')
 except BaseException as error:
  atomic(out,'backend_failure.json',{'status':'STOPPED','error':str(error),'callbacks_completed':count,'matrix_packets_completed':matrices,'spans_seconds_inclusive':spans.values},budget)
  try:stream.write(b'FAIL\n')
  except OSError:pass
  raise
 finally:sock.close()
if __name__=='__main__':
 from pathlib import Path
 serve(int(sys.argv[1]),Path(sys.argv[2]),load(sys.argv[3]),*sys.argv[4:5],event=sys.argv[5] if len(sys.argv)>5 and sys.argv[5]!='NONE' else None,tiny=len(sys.argv)>6 and sys.argv[6]=='TINY')
