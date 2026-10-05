"""Frozen authority integration and immutable qualification artifacts."""
import hashlib,json,math,os,sys,time,functools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
PREP=ROOT/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation'
sys.path.insert(0,str(ROOT/'Scripts/routeA/diagnostic_transient/v1_5_runtime'))
import authority
import qualification
sys.path.insert(0,str(ROOT/'Scripts/routeA/diagnostic_transient/v1_4'))
PLAN=PREP/'DiagnosticTransient_bounded_timing_qualification_plan.json'
CONTRACT=ROOT/'docs/routeA_diagnostic_transient_contract_v1.5.json'
need=authority.need;sha=authority.sha;load=authority.load

@functools.lru_cache(maxsize=1)
def plan():
 authority.verify_authority()
 return load(PLAN)

def safe_output(path):
 qualification.validate_output(ROOT,str(Path(path).absolute()))
 return Path(path).absolute()

def footprint(root):
 total=allocated=count=0
 for p in root.rglob('*'):
  need(not p.is_symlink(),'STOP_OUTPUT_SYMLINK')
  if p.is_file():
   try:s=p.stat()
   except FileNotFoundError:continue # atomic publication race, not a missing guard
   total+=s.st_size;allocated+=s.st_blocks*512;count+=1
 return max(total,allocated),count

def quota_context(root):
 root=Path(root).absolute()
 for parent in (root,*root.parents):
  p=parent/'quota_context.json'
  if p.exists():
   need(not p.is_symlink(),'STOP_QUOTA_SYMLINK');q=load(p)
   need(Path(q['root']).absolute()==parent,'STOP_QUOTA_ROOT')
   return q
 return None

def before_write(root,budget,size=0,files=1,reserve=True,emergency=False):
 q=quota_context(root)
 if q:
  root=Path(q['root']);budget=q['budget']
  keep_bytes=0 if emergency else q['stop_reserve_bytes']+q.get('sidechannel_reserve_bytes',0);keep_files=0 if emergency else q['stop_reserve_files']+q.get('sidechannel_reserve_files',0)
 else:keep_bytes=keep_files=0
 total,count=footprint(root);v=os.statvfs(root);free=v.f_bavail*v.f_frsize
 need(total+size+keep_bytes<=budget['scratch_bytes'] and count+files+keep_files<=budget['files_max'],'STOP_STORAGE_GUARD')
 need(files+keep_files<=v.f_favail,'STOP_INODES')
 if reserve:need(free>max(size,budget['scratch_bytes']-total)+max(32*2**30,int(.1*free)),'STOP_DISK_FREE_GUARD')

def atomic(root,name,value,budget=None,emergency=False):
 need(Path(name).name==name and name not in ('.','..'),'STOP_ARTIFACT_PATH')
 raw=(json.dumps(value,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
 if budget or quota_context(root):before_write(root,budget,len(raw),2,emergency=emergency)
 target=root/name
 if target.exists():raise FileExistsError(str(target))
 tmp=root/(name+'.partial')
 with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.link(tmp,target);tmp.unlink();fd=os.open(root,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
 return sha(target)

def host():
 available=0
 for line in Path('/proc/meminfo').read_text().splitlines():
  if line.startswith('MemAvailable:'):available=int(line.split()[1])*1024
 return {'MemAvailable':available,'loadavg':os.getloadavg(),'CPU_stat':Path('/proc/stat').read_text().splitlines()[0],
         'time_monotonic':time.monotonic(),'CPU_count':os.cpu_count(),'CPU_frequency':{k:(Path('/sys/devices/system/cpu/cpu0/cpufreq')/k).read_text().strip() if (Path('/sys/devices/system/cpu/cpu0/cpufreq')/k).exists() else 'UNKNOWN' for k in ('scaling_cur_freq','scaling_min_freq','scaling_max_freq')},'CPU_governor':Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor').read_text().strip() if Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor').exists() else 'UNKNOWN'}

def manifest(root,budget=None):
 rows=[]
 for f in sorted(root.rglob('*')):
  if f.is_file() and f.name!='qualification_manifest.json':rows.append({'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':sha(f)})
 return atomic(root,'qualification_manifest.json',{'schema':'qualification_evidence/1','artifacts':rows,'production_result':False},budget,emergency=True)
