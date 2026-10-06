"""Bounded line receive; exact legacy readline limit/EOF/ACK semantics."""
import io
class PacketStream:
 def __init__(self,sock,packet_limit,legacy=False):
  self.raw=sock.makefile('rwb',buffering=0);self.reader=self.raw if legacy else io.BufferedReader(self.raw,buffer_size=64*1024);self.limit=packet_limit+1
 def readline(self,size=None):return self.reader.readline(self.limit if size is None else min(size,self.limit))
 def write(self,raw):return self.raw.write(raw)
 def close(self):self.reader.close()
