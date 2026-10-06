"""Frozen evaluator/Live/Writer bindings, with resource-only context and span trees."""
import collections,copy,json,os,resource,socket,statistics,struct,time
from transport import PacketStream
from durable import SpanLedger
from common import load,plan,CONTRACT,before_write,atomic,ROOT,sha,need
import online_evaluator as oe
import persistence as persist
import live_collector as lc
from spans import Span
from schedule import context


def structural_receipt(r):
 """Isolated codec/memory event receipt; never a scientific/full-step verdict."""
 metrics={}
 for key in ('matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix'):
  if key in r['payload']:
   _,defect,bound=oe.replay_matrix(r['payload'][key]);metrics[key]={'defect':defect,'arithmetic_bound':bound}
 return {'sequence':r['sequence'],'metadata':r['metadata'],'payload_sha256':r['payload_sha256'],'matrix_metrics':metrics,'term_metrics':{},'synchronization':[],'valid':True,'term_name':r['payload'].get('term')}

def pack_compact(p,schema_id=0):
 need(set(p)=={'stage','values','columns','identity','payload','valid','term_name'},'STOP_COMPACT_SCHEMA')
 need(p['valid'] is True and all(type(x) in (int,float) for x in p['values']),'STOP_COMPACT_VALUES')
 oe.finite_tree(p);ids=[bytes.fromhex(p[k]) for k in ('identity','payload')];need(all(len(x)==32 for x in ids),'STOP_COMPACT_IDENTITY')
 return struct.pack('<II',schema_id,len(p['values']))+b''.join(ids)+struct.pack('<'+'d'*len(p['values']),*p['values'])

def logical_bytes(value):
 """Pre-serialization content: 8-byte numbers, UTF-8 strings/keys, bool1/null0."""
 if value is None:return 0
 if isinstance(value,bool):return 1
 if isinstance(value,(int,float)):return 8
 if isinstance(value,str):return len(value.encode())
 if isinstance(value,list):return sum(map(logical_bytes,value))
 return sum(len(k.encode())+logical_bytes(v) for k,v in value.items())

def serve(fd,out,budget,purpose='full',event=None,tiny=False):
 if os.environ.get('ROUTE_A_TIMING_SELF_TEST')!='TINY_SELF_TEST_ONLY':
  from runner import verify_stage_execution
  verify_stage_execution(os.environ['ROUTE_A_TIMING_STAGE_RECEIPT'],os.environ['ROUTE_A_TIMING_AUTHORIZATION_FILE'])
 cfg=plan();caps=cfg['stages']['Q1']['budgets'];resource.setrlimit(resource.RLIMIT_AS,(caps['backend_AS_max_bytes'],)*2)
 from reuse import install
 reuse=install(oe,persist) if os.environ.get('ROUTE_A_REUSE','ON')=='ON' else None
 spans=Span(compact=True);classes=collections.defaultdict(lambda:{'JSON_bytes':[],'packed_bytes':[]});events=[]
 for name in ('canonical','replay_matrix','sha'):
  original=getattr(oe,name)
  def install(name,original):
   timed=spans.wrap(name,original)
   def wrapper(*args,**kwargs):
    setattr(oe,name,original)
    try:return timed(*args,**kwargs)
    finally:setattr(oe,name,wrapper)
   setattr(oe,name,wrapper)
  install(name,original)
 persist.canonical=oe.canonical # imported alias must enter the same recursion guard
 import packed
 packed.sha=spans.wrap('packed_SHA',packed.sha);persist.sha=packed.sha
 original_encode=persist.encode;persist.encode=spans.wrap('packing',original_encode)
 class Writer(persist.Writer):
  def publish(self,name,raw,kind):
   before_write(out,budget,len(raw)+8192,3)
   if tiny and os.environ.get('ROUTE_A_TINY_INJECT')=='writer_race' and name=='initial_state.bin':
    import signal
    with (self.root/(name+'.partial')).open('xb') as f:f.write(raw[:max(1,len(raw)//2)]);f.flush();os.fsync(f.fileno())
    signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(5)
   with spans.scope('persistence_write_fsync_manifest'):
    return super().publish(name,raw,kind)
  def publish_spool(self,name,kind):
   before_write(out,budget,8192,3)
   with spans.scope('stream_hash_commit_fsync'):
    return super().publish_spool(name,kind)
  def accept(self,r,receipt):
   before_write(out,budget,self.stage_cap+8192,3)
   with spans.scope('writer_accept'):
    return super().accept(r,receipt)
 root=out/'runtime';before_write(out,budget,4096,1);root.mkdir();writer=Writer(root)
 kind=os.environ.get('ROUTE_A_TIMING_CONTEXT','STARTUP_ONE_TIME');writer.schedule=context(kind)
 c=copy.deepcopy(load(CONTRACT));c['live_provenance']={'input_hash':'RESOURCE_QUALIFICATION_FIXTURE_ONLY','evaluator_hash':sha(ROOT/'Scripts/routeA/diagnostic_transient/v1_4/online_evaluator.py')}
 live=lc.Live(writer,c,strict=False);live.qoi=spans.wrap('primary_QoI',live.qoi);live.outer_certificate=spans.wrap('U01_certificate',live.outer_certificate)
 sock=socket.socket(fileno=fd);stream=PacketStream(sock,cfg['Q1_design']['packet_limit_bytes'],legacy=os.environ.get('ROUTE_A_RECEIVER')=='LEGACY');from bulk import Bulk
 bulk=Bulk(cfg['Q1_design']['packet_limit_bytes']) if os.environ.get('ROUTE_A_BULK','ON')=='ON' else None
 ledger=SpanLedger(out,budget,enabled=os.environ.get('ROUTE_A_OBSERVER','ON')=='ON');current=[None];bytes_in=0;count=0;matrices=0;rows=[]
 def records():
  nonlocal bytes_in
  while True:
   begin=len(spans.nodes)
   with spans.scope('backend_receive'):
    if bulk:
     with spans.scope('bulk_decode_identity'):r,raw_size=bulk.receive(stream)
     if r is None:return
    else:
     raw=stream.readline(cfg['Q1_design']['packet_limit_bytes']+1);raw_size=len(raw)
     if raw==b'FINISH\n':return
     need(raw and raw.endswith(b'\n'),'STOP_TRANSPORT_TRUNCATED');r=spans.wrap('JSON_decode',json.loads)(raw)
   bytes_in+=raw_size
   if reuse:reuse.begin(r['metadata'],r['sequence'])
   need(r['metadata']['classification']=='SYNTHETIC_EVALUATOR_TEST' and r['metadata']['case_identity']=='RESOURCE_QUALIFICATION_FIXTURE_ONLY','STOP_FIXTURE_CLASSIFICATION')
   label=r.get('resource_payload_class',r['metadata']['stage']+'|'+r['payload'].get('term',''));spans.payload_class=label
   for node in spans.nodes[begin:]:node['payload_class']=label
   for node in spans.stack:node['payload_class']=label
   classes[label]['JSON_bytes'].append(raw_size);current[0]=r;yield r
 def ack():
  with spans.scope('ACK_preparation'):pass
  ledger.commit(spans,current[0],count,matrices,bytes_in)
  spans.wrap('ACK_send',stream.write)(b'OK\n');spans.flush()
 def save(summary,status):
  metrics={'bulk':bulk.report() if bulk else None,'reuse':reuse.report() if reuse else None,'status':status,'callbacks_including_constructor':count,'matrix_packets':matrices,'bytes_IPC_received':bytes_in,'spans_seconds_inclusive':spans.values,'span_tree':spans.report(),'evaluator_summary':summary,'callback_class_bytes':{key:{metric:{'count':len(v),'min':min(v),'median':statistics.median(v),'max':max(v),'p50':statistics.median(v),'p95':sorted(v)[max(0,__import__('math').ceil(.95*len(v))-1)]} for metric,v in row.items() if v} for key,row in classes.items()},'rows':rows,'memory_events':events,'writer_bytes':writer.written_bytes,'writer_fsyncs':writer.fsyncs,'U01_primary_steps':live.steps,'context_kind':kind,'schedule':{'step':writer.schedule.step,'full_count':writer.schedule.full_count,'bundle_count':writer.schedule.bundle_count,'full':writer.schedule.full,'selected':writer.schedule.selected},'scientific_claim':False}
  atomic(out,'backend_result.json',metrics,budget)
 try:
  if purpose!='full':
   if event=='full raw audit preparation as streaming path':writer.schedule=context('STARTUP_ONE_TIME');writer.schedule.begin(.3)
   last=None;before=None
   for r in records():
    last=r;count+=1;label=spans.payload_class
    if event:events.append({'event':event,'phase':'before','monotonic':time.monotonic(),'record':count,'role':'backend'})
    with spans.scope('isolated_callback'):
     retained_before=writer.written_bytes;oe.finite_tree(r);p=r['payload'];canonical=spans.wrap('canonicalization',oe.canonical)(p);need(oe.sha(canonical.encode())==r['payload_sha256'],'STOP_PRIMITIVE_PAYLOAD_HASH')
     if r.get('resource_payload_class')=='compact_scalar_receipt':
      raw=spans.wrap('compact_receipt_packing',pack_compact)(p);oe.sha(raw);writer.rows.append(raw);writer.events+=1;writer.rows_bytes+=len(raw);writer.schema[json.dumps([p['stage'],p['columns'],p['term_name']],separators=(',',':'))]=0
      if event=='chunk publication':writer.chunk()
      else:writer.chunk()
     else:
      receipt=spans.wrap('replay',structural_receipt)(r);matrices+=len(receipt['matrix_metrics']);writer.accept(r,receipt);raw=writer.ring[-1]
      if r['metadata']['stage']=='constructor_complete':live.geometry=r['live_binding']
      if event=='U01 last5 states' and r['metadata']['stage']=='outer_end':
       state=p['native_state_epoch'];live.outer.append(({k:{'cells':state[k]['cells'],'value_sha256':state[k]['value_sha256']} for k in ('U','T','p_rgh','rho','rhoFluidThermo:rho')},live.qoi(state)))
     classes[label]['packed_bytes'].append(len(raw));content_bytes=len(raw) if r.get('resource_payload_class')=='compact_scalar_receipt' else spans.wrap('telemetry_logical_byte_count',logical_bytes)(p);rows.append({'class':label,'stage':r['metadata']['stage'],'logical_bytes':content_bytes,'logical_definition':'RAC13 row bytes for compact; numeric8/UTF8/bool1/null0 before share for other classes','JSON_bytes':classes[label]['JSON_bytes'][-1],'IPC_bytes':classes[label]['JSON_bytes'][-1],'packed_bytes':len(raw),'retained_bytes':writer.written_bytes-retained_before,'retained_bytes_cumulative':writer.written_bytes,'native_state_present':'native_state_epoch' in p})
    ack()
   if last:
    if event:
     from io_memory import memory_event
     with spans.scope('memory_event'):
      result=memory_event(out,budget,event,last,tiny,live=live,writer=writer)
     events.append({'event':event,'phase':'after','monotonic':time.monotonic(),'role':'backend','model':result})
    elif any(r['class']=='selected_bundle_payload' for r in rows):writer.audit(writer.bundle,'selected_primitive.bin','selected_audit')
   save(None,'COMPLETE_ISOLATED_PRIMITIVE_NOT_STEP');ack();return
  gen=oe.evaluate(records(),sha(CONTRACT),c['resource_revision']['native_semantic_source_set_sha256'],c['resource_revision']['native_semantic_parent_instrumentation_sha256'])
  while True:
   try:
    with spans.scope('evaluator_callback'):receipt=next(gen)
   except StopIteration as end:
    spans.payload_class='finalization'
    with spans.scope('finalization'):live.finish();writer.finish(end.value)
    save(end.value,'COMPLETE_FIXTURE_NOT_SCIENCE');ack();break
   count+=1;matrices+=len(receipt['matrix_metrics']);r=current[0];label=r['metadata']['stage']+'|'+r['payload'].get('term','');spans.payload_class=label
   # next(gen) enters records() and establishes the actual class before replay.
   with spans.scope('callback_persistence_live'):
    writer.accept(r,receipt);classes[label]['packed_bytes'].append(len(writer.ring[-1]));live.accept(r,receipt)
   ack()
 except BaseException as error:
  atomic(out,'backend_failure.json',{'status':'STOPPED','error':str(error),'callbacks_completed':count,'matrix_packets_completed':matrices,'spans_seconds_inclusive':spans.values},budget,emergency=True)
  try:stream.write(b'FAIL\n')
  except OSError:pass
  raise
 finally:
  if writer.full_spool and not writer.full_spool.closed:writer.full_spool.close()
  ledger.close();stream.close();sock.close()

if __name__=='__main__':
 import sys
 from pathlib import Path
 if sys.argv[6]=='TINY' and os.environ.get('ROUTE_A_TIMING_SELF_TEST')=='TINY_SELF_TEST_ONLY' and os.environ.get('ROUTE_A_TINY_INJECT')=='backend_crash':os._exit(71)
 if sys.argv[6]=='TINY' and os.environ.get('ROUTE_A_TIMING_SELF_TEST')=='TINY_SELF_TEST_ONLY' and os.environ.get('ROUTE_A_TINY_INJECT')=='nested_ignore':
  import signal,subprocess
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  subprocess.Popen([sys.executable,'-B',str(__import__('common').HERE/'tiny_child.py'),'tree',sys.argv[2]])
  time.sleep(5)
 serve(int(sys.argv[1]),Path(sys.argv[2]),load(sys.argv[3]),sys.argv[4],event=sys.argv[5] if sys.argv[5]!='NONE' else None,tiny=sys.argv[6]=='TINY')
