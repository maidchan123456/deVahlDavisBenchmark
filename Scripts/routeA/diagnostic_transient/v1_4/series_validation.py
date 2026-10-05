"""Actual artifact validation for seals and final analysis from retained scalars."""
import hashlib,json,math
from pathlib import Path
import persistence,selected_replay,lifecycle
from packed import need

def primary_rows(root):
    rows=[]
    for p in sorted(Path(root).glob('primary_*.jsonl')):
        rows.extend(json.loads(x) for x in p.read_text().splitlines())
    need(rows and all(r['validity'] for r in rows),'PRIMARY_MISSING_OR_INVALID')
    need(all(b['time_index']==a['time_index']+1 and b['time']>a['time'] for a,b in zip(rows,rows[1:])),'PRIMARY_TIME_GAP')
    return rows

def final_analysis(root,synthetic=False):
    rows=primary_rows(root);arrival=json.loads((Path(root)/('synthetic_arrival_fixture.json' if synthetic else 'arrival_result.json')).read_text())
    return {'classification':'SYNTHETIC_ONLY' if synthetic else 'DIAGNOSTIC_OBSERVATION','endpoint_primary':{k:rows[-1][k] for k in ('Nu_bar_cavity','Umax','Wmax','Umax_Z','Wmax_X')},'registered_final_mean':arrival['confirmed']['final_mean'] if arrival['confirmed'] else None,'arrival_confirmed':arrival['confirmed'] is not None,'mass_energy_interpretation':'DIAGNOSTIC_ONLY_WITH_REGISTERED_INTERPRETATION'}

def compare(rootA,rootB,synthetic=False):
    A=final_analysis(rootA,synthetic);B=final_analysis(rootB,synthetic)
    need(A['registered_final_mean'] is not None and B['registered_final_mean'] is not None,'CO_COMPARISON_REQUIRES_CONFIRMED_FINAL_MEANS')
    differences={k:abs(B['registered_final_mean'][k]-A['registered_final_mean'][k])/max(abs(B['registered_final_mean'][k]),1.) for k in ('Nu_bar_cavity','Umax','Wmax')}
    return {'relative_differences':differences,'C3_trigger':any(v>.005 for v in differences.values()),'C3_policy':'STOP_SEPARATE_RESOURCE_REVIEW_RECHECK_AND_EXPLICIT_AUTHORIZATION','only_R0_used':True}

def log_verify(root):
    root=Path(root);done=json.loads((root/'raw_log_completion.json').read_text());chain='0'*64;total=0
    rows=[json.loads(x) for x in (root/'raw_log_manifest.jsonl').read_text().splitlines()]
    for i,row in enumerate(rows,1):
        claimed=row.pop('chain');need(row['path']==f'raw_log_{i:08d}.bin' and row['previous']==chain,'LOG_ORDER');chain=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest();need(chain==claimed,'LOG_CHAIN')
        digest,size=persistence.file_digest(root/row['path']);need(digest==row['sha256'] and size==row['bytes'],'LOG_HASH');total+=size
    need(done['complete'] and done['exit_code']==0 and done['bytes']==total and done['chain']==chain,'LOG_COMPLETION');return total

def validate(root,classification,guard,source,instrument,synthetic=False):
    root=Path(root);extra=set(classification)|lifecycle.CONTROL
    persistence.verify(root,extra);done=json.loads((root/'complete.json').read_text());rows=primary_rows(root);need(len(rows)==done['steps'],'PRIMARY_STEP_COVERAGE')
    need(all(r['U01']['status']=='PASS' and r['U01']['linear_status']=='PASS' and r['controller']['status']=='PASS' and len(r['linear_solves'])==169 for r in rows),'U01_CONTROLLER_INVALID')
    arrival=json.loads((root/('synthetic_arrival_fixture.json' if synthetic else 'arrival_result.json')).read_text());need(arrival['confirmed'] is not None,'U03_NOT_CONFIRMED')
    log_verify(root);raw=selected_replay.replay(root,'final_bundle.bin',guard,source,instrument,extra);need(raw['status']=='PASS','SELECTED_REPLAY_FAILED')
    stats=json.loads((root/'final_statistics.json').read_text());need(stats==final_analysis(root,synthetic),'FINAL_STATISTICS_MISMATCH')
    provenance=json.loads((root/'provenance.json').read_text());need(set(provenance)==set(lifecycle.PROVENANCE),'PROVENANCE_MISSING')
    if not synthetic:
        import provenance as archive
        archive.verify(root)
    need((root/'final_fields.bin').is_file() and (root/'initial_state.bin').is_file(),'MANDATORY_FIELDS_MISSING')
    return {'checks':{k:'PASS' for k in lifecycle.CHECKS},'selected_records':raw['selected_records'],'limitations':['SYNTHETIC LIFECYCLE TEST ONLY: manufactured native one-step plus separately labelled constant scalar arrival fixture; never a CFD trajectory or scientific arrival claim'] if synthetic else ['Fixed160 grid diagnostic only; no grid independence; mass/energy accuracy is diagnostic-only; deleted hashes do not recreate payload; future analyses of purged nonselected fields require a new computation; no bitwise rerun guarantee'],'synthetic':synthetic}

def reproduce_primary_from_R2(root,physical):
    from packed import decode
    from primary_evidence import primary
    root=Path(root);state=persistence.restore(decode((root/'final_fields.bin').read_bytes()),root);geometry=decode((root/'live_geometry.bin').read_bytes())
    values=primary(state,geometry['centres'],physical);recorded=primary_rows(root)[-1]
    keys=('Nu_bar_cavity','Nu_bar_0','Umax','Umax_Z','Wmax','Wmax_X')
    need(all(values[k]==recorded[k] for k in keys),'POST_PURGE_R2_PRIMARY_REPRODUCTION_MISMATCH')
    return {'status':'PASS','scope':'Independent retained R2 state + R0 native geometry reload; no purged data','values':{k:values[k] for k in keys}}
