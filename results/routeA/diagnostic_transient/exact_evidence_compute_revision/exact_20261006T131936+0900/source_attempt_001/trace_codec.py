"""Lossless independently complete gzip members, one per original raw JSON line.

Every retained member includes all original sample fields. A malformed/truncated
member fails closed, never silently drops samples. Bytes physically written are
quota-accounted before publication. No original trace is deleted or subsampled.
"""
import gzip,hashlib,json,os
from common import before_write
class Trace:
 def __init__(self,path,out,budget):
  self.file=path.open('xb');self.out=out;self.budget=budget;self.raw_bytes=0;self.compressed_bytes=0;self.samples=0;self.raw_hash=hashlib.sha256()
 def write(self,raw):
  b=raw.encode();packed=gzip.compress(b,compresslevel=1,mtime=0);before_write(self.out,self.budget,len(packed),0);self.file.write(packed);self.file.flush();self.raw_hash.update(b);self.raw_bytes+=len(b);self.compressed_bytes+=len(packed);self.samples+=1
 def accounting(self):return {'representation':'concatenated complete gzip members; one raw JSON line per member','samples':self.samples,'uncompressed_bytes':self.raw_bytes,'stored_bytes':self.compressed_bytes,'raw_SHA256':self.raw_hash.hexdigest(),'lossless':True,'sample_fields_unchanged':True}
 def close(self):self.file.flush();os.fsync(self.file.fileno());self.file.close()
def iter_trace(path):
 opener=gzip.open if str(path).endswith('.gz') else open
 with opener(path,'rt') as f:
  for line in f:yield json.loads(line)
