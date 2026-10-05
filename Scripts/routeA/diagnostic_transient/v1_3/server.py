"""Synchronous native callback receiver; ACK only after evaluation and retention."""
import json,os,resource,socket,sys,traceback
from pathlib import Path
from online_evaluator import evaluate
from persistence import Writer

def classification_guard(classification):
    if classification!='SYNTHETIC_EVALUATOR_TEST':
        raise ValueError('STOP_RESOURCE_REVISION_UNQUALIFIED_PRODUCTION_PRIMARY_BINDING')

def serve(fd,root,guard,source,instrument):
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    sock=socket.socket(fileno=fd);stream=sock.makefile('rwb',buffering=0)
    writer=Writer(root);current=[None]
    def records():
        while True:
            raw=stream.readline(512*2**20)
            if raw==b'FINISH\n':return
            if not raw or not raw.endswith(b'\n'):raise ValueError('EVALUATOR_FAILURE: TRANSPORT_TRUNCATED')
            r=json.loads(raw)
            classification_guard(r['metadata']['classification'])
            current[0]=r;yield r
    gen=evaluate(records(),guard,source,instrument)
    try:
        while True:
            try:receipt=next(gen)
            except StopIteration as done:
                writer.finish(done.value);stream.write(b'OK\n');break
            writer.accept(current[0],receipt);stream.write(b'OK\n')
    except Exception:
        traceback.print_exc(file=sys.stderr)
        try:writer.anomaly('EVALUATOR_OR_EVIDENCE_FAILURE')
        except Exception:pass
        stream.write(b'FAIL\n');raise
    finally:sock.close()
if __name__=='__main__':serve(int(sys.argv[1]),*sys.argv[2:])
