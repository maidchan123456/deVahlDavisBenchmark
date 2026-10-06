import os,json
from pathlib import Path
cpus=sorted(os.sched_getaffinity(0));cores=sorted(set((int((Path('/sys/devices/system/cpu')/('cpu'+str(c))/'topology/physical_package_id').read_text()),int((Path('/sys/devices/system/cpu')/('cpu'+str(c))/'topology/core_id').read_text())) for c in cpus));print(json.dumps({'rank':int(os.environ['OMPI_COMM_WORLD_RANK']),'cpus':cpus,'physical_cores':cores,'threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}}),flush=True)
