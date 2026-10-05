"""Diagnostic execution prerequisite, independent of formal Gate J."""
import os
from pathlib import Path
from packed import need

def preflight(root,planned_peak,planned_files,co=.5,authorized_conditional=False,free_override=None,inodes_override=None):
    stat=os.statvfs(root);free=stat.f_bavail*stat.f_frsize if free_override is None else free_override
    inodes=stat.f_favail if inodes_override is None else inodes_override
    need(co in (.5,.25,.125),'UNKNOWN_CO')
    need(co!=.125 or authorized_conditional,'STOP_CO0125_RESOURCE_REVIEW_AND_EXPLICIT_AUTHORIZATION_REQUIRED')
    need(planned_peak>0 and planned_peak<=.55*free,'RESOURCE_PREFLIGHT_STORAGE')
    need(planned_files>0 and planned_files<=.05*inodes,'RESOURCE_PREFLIGHT_INODES')
    mem={line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if 'kB' in line}
    need(mem['MemAvailable']>=24*2**30,'RESOURCE_PREFLIGHT_MEMORY')
    return {'RESOURCE_PREFLIGHT_PASS':True,'free_bytes':free,'free_inodes':inodes,'planned_peak':planned_peak,'planned_files':planned_files,'memory_available_bytes':mem['MemAvailable'],'memory_process_limits':'8GiB native +8GiB backend address space; >=8GiB reserve','external_capacity_assumed':False,'Co0125_guard':'C3; trigger preserved, stop before execution pending separate review and explicit authorization'}
