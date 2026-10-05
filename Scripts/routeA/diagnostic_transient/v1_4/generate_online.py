"""Mechanically move the frozen v1.2 replay loop before persistence; no math edits."""
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
parent=(HERE.parent/'v1_2/replay_evaluator.py').read_text()
assert hashlib.sha256(parent.encode()).hexdigest()=='ccc9ab23b48c4192235444ce179fe91e347841169354c2b9fbf81027f9a96cab'
start=parent.index('    ledger=StageLedger();')
loop=parent.index('    for line in lines:',start)
body=parent.index('        r=json.loads(data);',loop)
end=parent.index('    ledger.finish()',body)
init=parent[start:loop].replace('events=[]','event_hash=hashlib.sha256(b"[");event_count=0')
code=parent[body:end].replace('r=json.loads(data);finite_tree(r);','finite_tree(r);')
code=code.replace('ledger.accept(r);events.append((m[\'time_index\'],m[\'outer\'],m[\'pressure\'],stage))', '''ledger.accept(r)
        if event_count:event_hash.update(b',')
        event_hash.update(canonical((m['time_index'],m['outer'],m['pressure'],stage)).encode());event_count+=1''')
receipt='''        receipt={'sequence':r['sequence'],'metadata':m,'payload_sha256':r['payload_sha256'],'term_name':p.get('term'),
            'matrix_metrics':{},'term_metrics':{},'synchronization':synchronization,'valid':True}
        for key in ['matrix','current_matrix','unrelaxed_matrix','physical_matrix','referenced_matrix']:
            if key in p:
                packet=p[key];action,defect,bound=replay_matrix(packet)
                receipt['matrix_metrics'][key]=dict(norms(action,packet['volumes']),matrix_epoch=packet['matrix_epoch'],defect=defect,bound=bound,max_cell=max(range(len(action)),key=lambda i:abs(action[i])/packet['volumes'][i]))
        if 'term_actions' in p:
            volumes=p['native_state_epoch']['volumes']
            receipt['term_metrics']={key:norms(values,volumes) for key,values in p['term_actions'].items()}
        yield receipt
        synchronization=[]
'''
summary=parent[end:parent.index('\n\ndef norms',end)]
summary=summary.replace("'records':len(lines)","'records':event_count").replace("sha(canonical(events).encode())","event_hash.copy().hexdigest()")
summary=summary.replace('    ledger.finish()','    ledger.finish();event_hash.update(b"]")')
# Per-step synchronization is yielded immediately, never accumulated for a run.
new=parent[:parent.index('def replay(')]+'''def evaluate(records,guard,source,instrument,ledger_factory=StageLedger):
    """Generator: validates each actual packet before yielding any compact receipt."""
'''+init.replace('ledger=StageLedger()','ledger=ledger_factory()')+'    for r in records:\n'+code+receipt+summary+parent[parent.index('\n\ndef norms'):parent.index("if __name__=='__main__':")]
(HERE/'online_evaluator.py').write_text(new)
