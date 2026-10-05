"""Lossless fixed-byte log rotation. Hash/order are committed through Writer."""
from packed import need
class RawLog:
    def __init__(self,writer,chunk_bytes=4*2**20):
        self.writer=writer;self.chunk_bytes=chunk_bytes;self.pending=bytearray();self.parts=0;self.total=0
    def write(self,raw):
        need(isinstance(raw,bytes),'RAW_LOG_TYPE');self.total+=len(raw)
        pos=0
        while pos<len(raw):
            n=min(self.chunk_bytes-len(self.pending),len(raw)-pos);self.pending.extend(raw[pos:pos+n]);pos+=n
            if len(self.pending)==self.chunk_bytes:self.flush()
    def flush(self):
        if self.pending:
            self.parts+=1;self.writer.publish(f'raw_log_{self.parts:08d}.bin',bytes(self.pending),'raw_log');self.pending.clear()
