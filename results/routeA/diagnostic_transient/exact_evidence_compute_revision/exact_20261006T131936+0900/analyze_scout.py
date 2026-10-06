import sys,json,gzip,hashlib,statistics
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'Scripts/routeA/diagnostic_transient/compute_revision_v4/measurement'))
from common import atomic,REVISION_ROOT,load,sha
from archive import recover,artifact_blocks
from analysis import host_stability
cycle=int(sys.argv[1]);attempt=int(sys.argv[2]);out=Path(load(REVISION_ROOT/f'Scout_dispatch_cycle_{cycle}_a{attempt}.json')['output']);records,tail=recover(out/'archive');assert not tail
summary=[]
for rec in records:
 artifacts={x['path']:x for x in rec['artifacts']}
 def raw(name):return b''.join(artifact_blocks(out/'archive',artifacts[name]))
 meta=rec['metadata'];worker=json.loads(raw('worker_result.json'));native=[json.loads(x) for x in raw('native_progress.jsonl').splitlines() if x.startswith(b'{')];trace=[json.loads(x) for x in gzip.decompress(raw('resource_trace.jsonl.gz')).splitlines()];backend=json.loads(raw('backend_result.json')) if 'backend_result.json' in artifacts else None
 ledger=[json.loads(x) for x in raw('backend_span_ledger.jsonl').splitlines()] if 'backend_span_ledger.jsonl' in artifacts else [];callbacks=[x for x in native if 'callbacks_including_constructor' in x]
 r={'trial':rec['trial_id'],'request':meta['request'],'wall_seconds':meta['wall_seconds'],'constructor_seconds':callbacks[0]['callback_inclusive_seconds'],'representative_seconds':callbacks[1]['callback_inclusive_seconds'],'representative_native_spans':callbacks[1],'reuse':backend.get('reuse') if backend else None,'bulk':backend.get('bulk') if backend else None,'parallel':backend.get('parallel') if backend else None,'callback_JSON_bytes':[x['bytes_IPC'] for x in callbacks],'native_time_v':worker['native_time_v'],'backend_time_v':worker['backend_time_v'],'backend_span_values':backend['spans_seconds_inclusive'] if backend else None,'backend_span_per_class':backend['span_tree']['per_class'] if backend else None,'durable_receipts':len(ledger),'ledger_bytes':artifacts.get('backend_span_ledger.jsonl',{}).get('bytes',0),'host_stability':meta['host_stability'],'trace_accounting':meta['trace_accounting'],'peak_RSS_bytes':meta['peak_RSS_bytes'],'MemAvailable_min':min(x['host']['MemAvailable'] for x in trace),'files_peak':max(x['file_count'] for x in trace),'scratch_peak':max(x['scratch_bytes'] for x in trace),'host_busy_upper_max':None}
 hostfr=[]
 for a,b in zip(trace,trace[1:]):
  v=[int(x) for x in a['host']['CPU_stat'].split()[1:9]];w=[int(x) for x in b['host']['CPU_stat'].split()[1:9]];dt=sum(w)-sum(v);db=(sum(w)-w[3]-w[4])-(sum(v)-v[3]-v[4])
  if dt:hostfr.append(db/dt)
 r['host_busy_upper_max']=max(hostfr) if hostfr else None;summary.append(r)
atomic(REVISION_ROOT,f'Scout_analysis_cycle_{cycle}_a{attempt}.json',{'status':'COMPLETE_RESOURCE_SCOUT_NOT_QUALIFIED_Q1_Q2','campaign':str(out),'source_manifest_SHA256':sha(REVISION_ROOT/f'Scout_manifest_cycle_{cycle}_a{attempt}.json'),'trials':summary,'CFD_executed':False})
for r in summary:
 print(r['trial'],round(r['wall_seconds'],3),round(r['representative_seconds'],3),r['callback_JSON_bytes'],r['host_stability'])
 if r['backend_span_values']:print('backend', {k:round(v,4) for k,v in r['backend_span_values'].items() if k in ('backend_receive','JSON_decode','canonical','replay','writer_accept','packing','packed_SHA','ACK_send')})
