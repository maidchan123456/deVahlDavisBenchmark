"""Archive exact registered inputs/source/instrumentation/analysis before sealing.
Mesh/binary/library/compiler identities are retained as manifests; do not promise
future bitwise restoration from identities alone. Native geometry and R2 remain.
"""
import hashlib,json,os
from pathlib import Path
from launcher import hash_file
from lifecycle import PROVENANCE,required_retention
from packed import need

def stage(root,spec):
    root=Path(root);result={};classes={}
    for category in PROVENANCE:
        entries=[]
        for i,item in enumerate(spec['provenance'][category]):
            need(hash_file(item['path'])==item['sha256'],'PROVENANCE_CHANGED_BEFORE_SEAL')
            entry=dict(item)
            if category in ('contract','input','source','instrumentation','analysis'):
                dest=f'{category}_source_{i:05d}{Path(item["path"]).suffix}'
                with Path(item['path']).open('rb') as src,(root/dest).open('xb') as out:
                    for block in iter(lambda:src.read(2**20),b''):out.write(block)
                    out.flush();os.fsync(out.fileno())
                need(hash_file(root/dest)==item['sha256'],'ARCHIVE_COPY_HASH');entry['archive_path']=dest;classes[dest]='R0'
            entries.append(entry)
        doc={'category':category,'files':entries,'platform':spec['platform'],'identities_only':category in ('mesh','binary','libraries','compiler'),'bitwise_rerun_guaranteed':False}
        dest=f'provenance_{category}.json'
        with (root/dest).open('x') as f:json.dump(doc,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
        result[category]=hash_file(root/dest);classes[dest]='R0'
    with (root/'provenance.json').open('x') as f:json.dump(result,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(root,os.O_DIRECTORY);os.fsync(fd);os.close(fd);classes['provenance.json']='R0';return result,classes

def verify(root):
    root=Path(root);p=json.loads((root/'provenance.json').read_text());need(set(p)==set(PROVENANCE),'PROVENANCE_MISSING')
    for category,digest in p.items():
        path=root/f'provenance_{category}.json';need(hash_file(path)==digest,'PROVENANCE_DOCUMENT_HASH');doc=json.loads(path.read_text());need(doc['files'] and doc['platform'],'PROVENANCE_EMPTY')
        for e in doc['files']:
            if category in ('contract','input','source','instrumentation','analysis'):
                need('/' not in e['archive_path'] and hash_file(root/e['archive_path'])==e['sha256'],'PROVENANCE_ARCHIVE_HASH')
    return p
