"""Monotonic span trees; overlapping process spans are never summed as wall."""
import contextlib,time

class Span:
 def __init__(self,compact=False):self.compact=compact;self.aggregates={};self.counter=0;self.values={};self.nodes=[];self.stack=[];self.payload_class='startup';self.max_nodes=150000
 @contextlib.contextmanager
 def scope(self,name):
  start=time.perf_counter();node={'id':self.counter,'parent_id':self.stack[-1]['id'] if self.stack else None,'name':name,'payload_class':self.payload_class,'start':start,'child_seconds':0.}
  if len(self.nodes)>=self.max_nodes:raise ValueError('STOP_SPAN_RECORD_CAP')
  self.counter+=1;self.nodes.append(node);self.stack.append(node)
  try:yield node
  finally:
   node['inclusive_seconds']=time.perf_counter()-start;node['exclusive_seconds']=max(0.,node['inclusive_seconds']-node.pop('child_seconds'));self.stack.pop()
   if self.stack:self.stack[-1]['child_seconds']+=node['inclusive_seconds']
   self.values[name]=self.values.get(name,0.)+node['inclusive_seconds']
 def wrap(self,name,f):
  def wrapped(*args,**kwargs):
   with self.scope(name):return f(*args,**kwargs)
  return wrapped
 def flush(self):
  if not self.compact:return
  if self.stack:raise ValueError('STOP_SPAN_FLUSH_INSIDE_PARENT')
  lookup={n['id']:n for n in self.nodes};paths={}
  for n in self.nodes:
   parent=paths.get(n['parent_id'],());path=parent+(n['name'],);paths[n['id']]=path
   key=(n['payload_class'],path);row=self.aggregates.setdefault(key,{'id':n['payload_class']+':'+ '/'.join(path),'parent_id':n['payload_class']+':'+ '/'.join(parent) if parent else None,'name':n['name'],'payload_class':n['payload_class'],'count':0,'inclusive_seconds':0.,'exclusive_seconds':0.,'start':n['start'],'end':n['start']})
   row['count']+=1;row['inclusive_seconds']+=n['inclusive_seconds'];row['exclusive_seconds']+=n['exclusive_seconds'];row['end']=n['start']+n['inclusive_seconds']
  self.nodes=[]
 def report(self):
  self.flush();nodes=list(self.aggregates.values()) if self.compact else self.nodes;classes={}
  for n in nodes:
   row=classes.setdefault(n['payload_class'],{}).setdefault(n['name'],{'count':0,'inclusive_seconds':0.,'exclusive_seconds':0.})
   row['count']+=n.get('count',1)
   for key in ('inclusive_seconds','exclusive_seconds'):row[key]+=n[key]
  return {'clock':'perf_counter/CLOCK_MONOTONIC','nodes':nodes,'per_class':classes,'representation':'exact summed span tree per class/path' if self.compact else 'individual span tree','cross_process_rule':'native send-to-ACK includes backend processing; never add backend spans to ACK wall','exclusive_rule':'subtract direct same-process children only'}
