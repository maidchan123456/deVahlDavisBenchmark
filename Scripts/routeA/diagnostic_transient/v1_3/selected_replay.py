"""Selected raw replay, witnessed by complete compact native-stage receipts."""
import json,struct
from pathlib import Path
from packed import need,sha
from persistence import verify,iter_bundle_file
from online_evaluator import evaluate,StageLedger,canonical

def witnesses(root,selected_sequences):
    verify(root);ledger=StageLedger();result={}
    for path in sorted(Path(root).glob('chunk_*.bin')):
        raw=path.read_bytes();n=struct.unpack('<Q',raw[6:14])[0];h=json.loads(raw[14:14+n]);pos=14+n
        schemas={sid:json.loads(key) for key,sid in h['schema_table'].items()}
        for _ in range(h['events']):
            sid,count=struct.unpack('<II',raw[pos:pos+8]);identity=raw[pos+8:pos+40];payload=raw[pos+40:pos+72];pos+=72
            v=struct.unpack('<'+'d'*count,raw[pos:pos+count*8]);pos+=8*count;stage,columns,term=schemas[sid]
            need(all(float(x).is_integer() for x in v[:7]),'COUNTER_TYPE')
            m={'time_index':int(v[1]),'outer':int(v[2]),'pressure':int(v[3]),'nonOrthogonal':int(v[4]),'energy_solve':int(v[5]),'rho_solve':int(v[6]),'physical_time':v[7],'deltaT':v[8],'previous_deltaT':v[9],'stage':stage}
            r={'sequence':int(v[0]),'metadata':m,'payload':{'term':term}}
            ledger.accept(r)
            if r['sequence'] in selected_sequences:result[r['sequence']]={'identity':identity,'payload':payload,'metadata':m,'metrics':dict(zip(columns,v[10:]))}
    ledger.finish();return result

def replay(root,filename,guard,source,instrument):
    selected_sequences={r['sequence'] for r in iter_bundle_file(root,filename)};proof=witnesses(root,selected_sequences);records=iter_bundle_file(root,filename)
    class SelectedLedger:
        def __init__(self):self.epochs={};self.previous=0;self.last=None
        def accept(self,r):
            i=r['sequence'];need(i in proof and i>self.previous,'SELECTED_SEQUENCE')
            need(sha(canonical(r['metadata']).encode())==proof[i]['identity'].hex(),'SELECTED_METADATA_EPOCH')
            need(r['payload_sha256']==proof[i]['payload'].hex(),'SELECTED_PAYLOAD_EPOCH');self.previous=i;self.last=r['metadata']['stage']
        def finish(self):need(self.last=='time_end','SELECTED_BUNDLE_TERMINAL_MISSING')
    gen=evaluate(iter(records),guard,source,instrument,SelectedLedger);receipts=[]
    while True:
        try:receipts.append(next(gen))
        except StopIteration as done:summary=done.value;break
    return {'status':'PASS','coverage':'SELECTED59_WITH_COMPLETE_COMPACT_STAGE_GRAPH; not all-step raw replay','selected_records':len(selected_sequences),'summary':summary,'receipts':receipts}
