"""Bounded new R3 validation copies; shares16GiB with R4 scratch."""
import os
from pathlib import Path
from lifecycle import Series,required_retention,name
from packed import need
CAP=16*2**30

def copy(root,source,destination):
    name(destination);need(required_retention(destination)=='R3','TEMPORARY_DESTINATION_CLASS')
    series=Series(root)
    with series.lock() as fd:
        need(series.state(fd) in ('RUNNING','VALIDATING'),'TEMP_COPY_AFTER_SEAL_FORBIDDEN')
        total=sum((series.root/p).stat().st_size for p in os.listdir(fd) if required_retention(p) in ('R3','R4'))
        temp='atomic_temporary_'+destination;out=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        try:
            with Path(source).open('rb') as src:
                for block in iter(lambda:src.read(2**20),b''):
                    need(total+len(block)<=CAP,'SHARED_TEMPORARY_SCRATCH_CAP');offset=0
                    while offset<len(block):offset+=os.write(out,block[offset:])
                    total+=len(block)
            os.fsync(out)
        finally:os.close(out)
        os.link(temp,destination,src_dir_fd=fd,dst_dir_fd=fd,follow_symlinks=False);os.unlink(temp,dir_fd=fd);os.fsync(fd)
