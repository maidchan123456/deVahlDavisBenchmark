"""Synchronous native callback receiver; ACK only after evaluation and retention."""
import json,os,resource,socket,sys,traceback
from pathlib import Path
from online_evaluator import evaluate
from persistence import Writer
from live_collector import Live
import hashlib

def classification_guard(classification):
    if classification!='SYNTHETIC_EVALUATOR_TEST':
        if classification!='DIAGNOSTIC_OBSERVATION':raise ValueError('WRONG_CLASSIFICATION')
        if not os.environ.get('ROUTE_A_PREFLIGHT_RECEIPT'):raise ValueError('PRODUCTION_PREFLIGHT_REQUIRED')

def serve(fd,root,guard,source,instrument):
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    sock=socket.socket(fileno=fd);stream=sock.makefile('rwb',buffering=0)
    if os.environ.get('ROUTE_A_SYNTHETIC_LIVE')!='1' and os.environ.get('ROUTE_A_BIND_LIVE')=='1':
        from launcher import verify_preflight_receipt
        preflight_receipt=verify_preflight_receipt(root,guard)
    if os.environ.get('ROUTE_A_BIND_LIVE')=='1' and os.environ.get('ROUTE_A_SYNTHETIC_LIVE')!='1':os.environ['ROUTE_A_SERIES_RETAINED_CAP_BYTES']=str(preflight_receipt['post_seal_bytes'])
    writer=Writer(root);current=[None];live=None
    if os.environ.get('ROUTE_A_BIND_LIVE')=='1':
        contract_path=Path(os.environ['ROUTE_A_DIAGNOSTIC_CONTRACT_FILE']);contract=json.loads(contract_path.read_text())
        # Synthetic fixtures have no CFD input dictionaries; pin the native driver instead.
        if os.environ.get('ROUTE_A_SYNTHETIC_LIVE')=='1':
            contract['live_provenance']={'input_hash':os.environ['ROUTE_A_FIXTURE_SHA256'],'evaluator_hash':hashlib.sha256((Path(__file__).parent/'online_evaluator.py').read_bytes()).hexdigest()}
        if os.environ.get('ROUTE_A_SYNTHETIC_LIVE')!='1':
            contract['live_provenance']={'input_hash':hashlib.sha256(json.dumps(preflight_receipt['provenance']['input'],sort_keys=True).encode()).hexdigest(),'evaluator_hash':hashlib.sha256((Path(__file__).parent/'online_evaluator.py').read_bytes()).hexdigest()}
        live=Live(writer,contract,strict=os.environ.get('ROUTE_A_SYNTHETIC_LIVE')!='1')
        if live.strict:live.expected_Co=preflight_receipt['Co']
    def records():
        while True:
            raw=stream.readline(512*2**20)
            if raw==b'FINISH\n':return
            if not raw or not raw.endswith(b'\n'):raise ValueError('EVALUATOR_FAILURE: TRANSPORT_TRUNCATED')
            r=json.loads(raw)
            classification_guard(r['metadata']['classification'])
            if r['metadata']['classification']=='DIAGNOSTIC_OBSERVATION' and live is None:raise ValueError('PRODUCTION_LIVE_BINDING_REQUIRED')
            if r['metadata']['classification']=='DIAGNOSTIC_OBSERVATION':
                if os.environ.get('ROUTE_A_SYNTHETIC_LIVE')=='1':raise ValueError('SYNTHETIC_BYPASS_FORBIDDEN_FOR_PRODUCTION')
                if r['metadata']['case_identity']!=preflight_receipt['case_id']:raise ValueError('PREFLIGHT_CASE_IDENTITY_MISMATCH')
            current[0]=r;yield r
    gen=evaluate(records(),guard,source,instrument)
    try:
        while True:
            try:receipt=next(gen)
            except StopIteration as done:
                if live:live.finish()
                writer.finish(done.value);stream.write(b'OK\n');break
            writer.accept(current[0],receipt)
            if live:live.accept(current[0],receipt)
            stream.write(b'ARRIVED\n' if live and live.strict and current[0]['metadata']['stage']=='time_end' and live.arrival.confirmed else b'OK\n')
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:
            if live:live.flush()
            writer.chunk();writer.anomaly('EVALUATOR_OR_EVIDENCE_FAILURE')
        except Exception:pass
        stream.write(b'FAIL\n');raise
    finally:sock.close()
if __name__=='__main__':serve(int(sys.argv[1]),*sys.argv[2:])
