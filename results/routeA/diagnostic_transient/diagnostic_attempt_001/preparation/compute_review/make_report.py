"""Read-only evidence synthesis; writes only this review's output artifacts."""
import collections,csv,hashlib,json,math,re,statistics,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[5];P=O.parent
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def csvout(name,rows):
    with (P/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def table(rows,keys):
    text='| '+' | '.join(keys)+' |\n| '+' | '.join('---' for _ in keys)+' |\n'
    for row in rows:text+='| '+' | '.join(str(row.get(k,'')) for k in keys)+' |\n'
    return text+'\n'
def duration(seconds):
    if seconds<3600:return f'~{seconds/60:.1g} min'
    if seconds<86400:return f'~{seconds/3600:.2g} h'
    if seconds<86400*365:return f'~{seconds/86400:.2g} days'
    return f'~{seconds/(86400*365.25):.2g} years'

def main():
    start=load(O/'start_guard.json');c=load(R/'docs/routeA_diagnostic_transient_contract_v1.5.json')
    assert sha(R/'docs/routeA_diagnostic_transient_contract_v1.5.json')=='06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d'
    assert sha(R/'docs/routeA_execution_contract_v1.7.json')=='fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60'
    for path,digest in start['protected_sha256'].items():assert sha(R/path)==digest,path
    host=load(O/'host_hardware.json');ls={x['field'].rstrip(':'):x['data'] for x in json.loads(host['lscpu'])['lscpu']}
    mem={line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in host['meminfo'].splitlines() if 'kB' in line}
    primitive=load(O/'primitive_timings.json');supp=load(O/'supplemental_timings.json');native=load(O/'native_timings.json');steady=load(O/'steady_timing_evidence.json');callbacks=load(O/'callback_workload.json')
    timings={x['component']:x for x in primitive['timings']+supp['timings']}
    t=lambda name:timings[name]['median']
    on=[x for x in native['trials'] if x['mode']=='on'];off=[x for x in native['trials'] if x['mode']=='off']
    summary={mode:{'median_wall_s':statistics.median(x['wall_seconds'] for x in trials),'min_wall_s':min(x['wall_seconds'] for x in trials),'max_wall_s':max(x['wall_seconds'] for x in trials),
             'median_max_single_process_RSS_KiB':statistics.median(x['max_process_rss_KiB'] for x in trials)} for mode,trials in [('ON',on),('OFF',off)]}
    summary['synthetic_overhead_fraction']=(summary['ON']['median_wall_s']-summary['OFF']['median_wall_s'])/summary['ON']['median_wall_s']
    assert len(on)==len(off)==3
    assert all(x['linear_records_by_field']=={'Ux':24,'Uy':24,'e':24,'p_rgh':48,'rho':49} for x in on)
    counts={'U_fv':24,'U_scalar':48,'e_fv':24,'p_rgh_fv':48,'rho_fv':49,'fv_total':145,'scalar_total':169}
    assert 24+24+48+49==145 and 48+24+48+49==169
    capacity=c['resource_revision_fix']['capacity'];series=capacity['series']
    baseline=[x for x in steady if x['case']=='A-Ra1e6-fine']
    costs=[x['wall_s_per_iteration_including_startup'] for x in baseline]
    # Comparable workload units: one historical SIMPLE iteration has one U/e
    # and two pressure solves. 24 such component groups, plus 49 transient rho
    # solves/old-time terms, form a proxy, never a measured PIMPLE step.
    core={'optimistic':24*min(costs)*.5,'central':24*statistics.median(costs),'conservative':24*max(costs)*3}
    ncallback=callbacks['callbacks_per_full_physical_step']
    replay_calls=2*callbacks['matrix_packets_per_physical_step']+49+24
    required_callback=t('canonical_state_string')+t('canonical_payload_string')+t('JSON_decode_payload')+t('binary_pack_payload')
    representative_diag=ncallback*required_callback+replay_calls*t('matrix_replay_including_epoch_hash')+25*t('primary_QoI_4097_points')+t('U01_terminal_certificate_25600')
    # Source-shaped sensitivity, NOT confidence bounds. Some callbacks have
    # fewer/more matrices; this is one deliberately explicit data-shape model.
    diag={name:representative_diag*factor for name,factor in [('optimistic',.5),('central',1),('conservative',2)]}
    step={name:core[name]+diag[name] for name in core}
    computations=[
        {'Component':'CFD momentum/energy/pressure group','Evidence source':'7 historical SIMPLE segments; 3 baseline segments for numerical proxy','Cost estimate':f'{core["optimistic"]:.2g}–{core["conservative"]:.2g} s/physical-step proxy','Confidence':'LOW; relaxed 1e-10 SIMPLE differs from unrelaxed 1e-12 PIMPLE'},
        {'Component':'rho49/thermo/assembly/field update','Evidence source':'native OpenFOAM source graph; historical aggregate timing','Cost estimate':'UNRESOLVED separately; included only as uncertainty in core proxy','Confidence':'LOW'},
        {'Component':'native observer/object/string construction','Evidence source':'NativeStageObserver meshState/emit; tiny OFF/ON','Cost estimate':'UNRESOLVED at target size; not included in Python subtotal','Confidence':'LOW'},
        {'Component':'mass/energy matrix replay','Evidence source':'actual replay_matrix on manufactured 25600-cell/50880-face matrix','Cost estimate':f'{t("matrix_replay_including_epoch_hash"):.3g} s/call; >= {replay_calls} graph calls/step plus matrix_action/end work','Confidence':'MEDIUM primitive; LOW total-step extrapolation'},
        {'Component':'canonical payload/state identities','Evidence source':'actual online_evaluator.canonical, representative target-size state/payload','Cost estimate':f'{t("canonical_state_string"):.3g} / {t("canonical_payload_string"):.3g} s/state / payload; {ncallback} callbacks/step','Confidence':'MEDIUM shape-only; LOW production'},
        {'Component':'primary QoI and 4097 extrema','Evidence source':'actual primary_evidence.primary on 160x160 synthetic arrays','Cost estimate':f'{t("primary_QoI_4097_points"):.3g} s/call; 24 outer_end + time_end and startup calls','Confidence':'MEDIUM primitive'},
        {'Component':'U01 terminal certificate','Evidence source':'actual Live.outer_certificate; stationary shared manufactured arrays','Cost estimate':f'{t("U01_terminal_certificate_25600"):.3g} s/certificate','Confidence':'MEDIUM primitive, no production RSS claim'},
        {'Component':'U03 arrival windows','Evidence source':'frozen arrival_candidate, 101/201/401 nodes; 15001-node attempt aborted','Cost estimate':'quadratic history scan; target-node latency UNRESOLVED; supplemental scenario table','Confidence':'HIGH source complexity; LOW projected timing'},
        {'Component':'JSON decode / Python encode','Evidence source':'representative target-shape 7.4MB JSON','Cost estimate':f'{t("JSON_decode_payload"):.3g} / {t("JSON_encode_payload"):.3g} s/callback','Confidence':'MEDIUM primitive; native encoder UNRESOLVED'},
        {'Component':'AF_UNIX IPC ACK','Evidence source':'16MiB socketpair transfer with reader thread; no backend work','Cost estimate':f'{t("AF_UNIX_16MiB_ACK_no_backend_work"):.3g} s/16MiB','Confidence':'MEDIUM primitive; production ACK includes all synchronous processing'},
        {'Component':'binary packing','Evidence source':'actual packed.encode on target-shape payload','Cost estimate':f'{t("binary_pack_payload"):.3g} s/{timings["binary_pack_payload"]["output_bytes"]} B packet','Confidence':'MEDIUM primitive; static sharing changes real packet size'},
        {'Component':'SHA256','Evidence source':'16MiB allocation + hashlib; canonical generation timed separately','Cost estimate':f'{t("SHA256_16MiB"):.3g} s/16MiB incl allocation','Confidence':'MEDIUM primitive; native SHA code not isolated'},
        {'Component':'logging / selected audit / fields / fsync','Evidence source':'retention caps, actual publish/rotation code, 3x16MiB fsynced writes','Cost estimate':'average/burst models below; sustained multi-GiB latency UNRESOLVED','Confidence':'LOW sustained workload'},
    ]
    runtime=[];solve_rows=[];io_rates=[];arrival_rows=[]
    for co in ('0.5','0.25','0.125'):
        for end in (.5,1.,2.):
            steps=math.ceil(series[co]['steps_planning_only']*end/2)
            row={'Co':co,'t_star_end':end,'Steps_PLANNING_ONLY':steps,'fv_solves_per_step':145,'total_fv_solves':steps*145,
                 'total_scalar_records':steps*169,'U_fv_calls':steps*24,'Ux_Uy_records':steps*48,'e_calls':steps*24,'pressure_calls':steps*48,'rho_calls':steps*49}
            solve_rows.append(row)
            projected={name:steps*step[name] for name in step}
            runtime.append({'Co':co,'t_star_end':end,'Steps_PLANNING_ONLY':steps,
                'Optimistic_SHAPE_ONLY':duration(projected['optimistic']), 'Central_SHAPE_ONLY':duration(projected['central']),
                'Conservative_SHAPE_ONLY':duration(projected['conservative']),
                'optimistic_seconds_conditional':projected['optimistic'],'central_seconds_conditional':projected['central'],
                'conservative_seconds_conditional':projected['conservative'],
                'core_only_proxy_days':steps*core['central']/86400,
                'wall_seconds_per_t_star_central_shape_only':projected['central']/end,
                'wall_seconds_per_simulated_second_central_shape_only':projected['central']/(end*710),
                'qualified_runtime_estimate':'UNRESOLVED','classification':'CONDITIONAL_DATA_SHAPE_STRESS_MODEL_NOT_PRODUCTION_BOUNDS',
                'omissions':'native observer, additional field/BC identities, static-sharing hashes, full end evaluator, U03 candidate spikes, startup costs, sustained selected I/O'})
            parts=series[co]['parts'];perstep=(parts['receipts_and_primary']+parts['complete_solver_logs'])/series[co]['steps_planning_only']
            fixed=parts['full_raw_audits']+parts['selected_bundles']+parts['field_snapshots']+parts['fixed_provenance_and_static']
            capbytes=steps*perstep+fixed # intentionally use full t*=2 fixed caps for all scenarios
            chunks=math.ceil(steps/64);logfiles=math.ceil(steps*65536/(4*2**20));files=chunks*2+logfiles+7+56+505
            fsyncs=3*files+7 # full audit spool adds at least 7 file fsyncs
            for name,wall in projected.items():
                io_rates.append({'Co':co,'t_star_end':end,'scenario':name,'classification':'CAP_BASED_CONDITIONAL_RATE_NOT_MEASURED_PRODUCTION',
                    'permanent_planning_cap_bytes':capbytes,'GB_per_hour':capbytes/wall*3600/1e9,'MB_per_second':capbytes/wall/1e6,
                    'files_estimate':files,'files_per_hour':files/wall*3600,'fsync_estimate_lower_bound':fsyncs,
                    'fsync_per_hour_lower_bound':fsyncs/wall*3600,'peak_full_audit_bytes':9*2**30,
                    'excluded':'extra immutable/provenance/trigger/lifecycle/validation calls; uses full fixed ceilings even for early arrival'})
        nodes=math.ceil(series[co]['steps_planning_only']*.3/2)+2
        one401=t('U03_three_windows_401_nodes')
        # 401 fixture covers 0.5; production .3 retained nodes plus baseline.
        # O(N^2) demonstration only; conservative extra nodes/values may differ.
        projected=one401*(nodes/401)**2
        arrival_rows.append({'Co':co,'last_0p3_window_nodes_PLANNING_ONLY':nodes,
            'candidate_cost_quadratic_shape_proxy_seconds':projected,
            'candidate_cost_shape_proxy':duration(projected),'classification':'LOW_CONFIDENCE_COMPLEXITY_EXTRAPOLATION_NOT_MEASURED_TARGET',
            'arrival_memory_numeric_lower_bytes':nodes*9*8,'arrival_memory_Python_scalar_estimate_bytes':nodes*9*32,
            'maximum_candidate_endpoints':16})
    # Retained-size ceilings and native numerical bases, not RSS estimates.
    memory=[
        {'Component':'current registered scalar/vector fields','Scaling':'O(Ncells)','Estimated bytes':25600*11*8,'Evidence':'8 scalar + U3 components in meshState; lower numerical storage only; excludes other OpenFOAM objects'},
        {'Component':'surface phi and address arrays','Scaling':'O(Nfaces)','Estimated bytes':102720*8+50880*2*4,'Evidence':'actual boundary mesh; excludes patch metadata and C++ allocation'},
        {'Component':'rho/e/K oldTime numeric histories','Scaling':'O(Ncells x 2 levels)','Estimated bytes':25600*6*8,'Evidence':'meshState exports existing histories; actual histories can differ by field'},
        {'Component':'one sparse scalar matrix basic arrays','Scaling':'O(Ncells+NinternalFaces)','Estimated bytes':(2*25600+2*50880)*8+2*50880*4,'Evidence':'diag/source/upper/lower + int32 addresses; excludes psi/BC/action/replay copies'},
        {'Component':'last5 outer primitive states','Scaling':'O(5 x Ncells)','Estimated bytes':5*25600*(160+4*32),'Evidence':'Live retains U3+T+p_rgh+rho+rhoThermo; Python float/list planning estimate, no tiny-RSS scaling'},
        {'Component':'recent16 stage packed ring','Scaling':'bounded 16 x stage cap','Estimated bytes':512*2**20,'Evidence':'Writer default ring1GiB but max16 x 32MiB stage enforces effective512MiB'},
        {'Component':'selected bundle retained','Scaling':'bounded','Estimated bytes':512*2**20,'Evidence':'BUNDLE_CAP; publication joins/prefix can temporarily allocate additional512MiB–1GiB'},
        {'Component':'receipt chunk retained','Scaling':'bounded','Estimated bytes':64*2**20,'Evidence':'chunk quota; join/prefix can add128MiB transient allocations'},
        {'Component':'primary scalar chunk retained','Scaling':'bounded','Estimated bytes':16*2**20,'Evidence':'Live rows_bytes quota; joining duplicates current chunk'},
        {'Component':'transient stage encoder buffer','Scaling':'bounded packed bytes only','Estimated bytes':32*2**20,'Evidence':'STAGE_CAP is after encoding; constructing Python/C++ JSON objects is additional'},
        {'Component':'field snapshot/final packet buffer','Scaling':'bounded packed bytes only','Estimated bytes':16*2**20,'Evidence':'FIELD_CAP; pre-encoded field copies and final/current simultaneous copies additional'},
        {'Component':'JSON IPC and Python evaluator state','Scaling':'O(fields/matrices x Ncells/Nfaces)','Estimated bytes':'UNRESOLVED','Evidence':'Python lists/floats, C++ Json maps, term packets, canonical strings and deep snapshots coexist; not bounded by packed-byte cap alone'},
        {'Component':'arrival history Co0.25 planning','Scaling':'O(Nsteps in last0.3 window)','Estimated bytes':arrival_rows[1]['arrival_memory_Python_scalar_estimate_bytes'],'Evidence':'9 deques; source trims old nodes, scalar history remains on disk; adaptive dt can increase count'},
        {'Component':'native/runtime baseline + temporary assembly/thermo','Scaling':'O(Ncells/Nfaces) + O(1)','Estimated bytes':'UNRESOLVED','Evidence':'native process peak AS/RSS on target grid not measured'},
        {'Component':'target-shape primitive process high-water RSS','Scaling':'measured synthetic process only','Estimated bytes':int(primitive['baseline_RSS_KiB']*1024),'Evidence':'617128KiB includes imports, synthetic lists/matrix and sequential serialization allocations; not production peak'},
        {'Component':'native/backend AS limits','Scaling':'per process virtual ceiling','Estimated bytes':8*2**30,'Evidence':'8GiB each; limits are failure guard, not fit proof; combined16GiB without swap assumption'},
        {'Component':'minimum host available memory','Scaling':'host preflight','Estimated bytes':24*2**30,'Evidence':f'Current MemAvailable {mem["MemAvailable"]} B; passes host check but not process AS qualification'},
    ]
    io_model=[]
    b05=series['0.5'];steps05=b05['steps_planning_only']
    for name,freq,per,total,burden in [
        ('compact receipts','64 physical steps',64*(b05['parts']['receipts_and_primary']/steps05-65536),b05['parts']['receipts_and_primary']-steps05*65536,'3 fsync/publication + metadata hash;64MiB chunk cap'),
        ('primary rows','64 steps',64*65536,steps05*65536,'max64KiB/row;actual rows smaller;3 fsync/publication'),
        ('complete solver log','4MiB rotation',4*2**20,b05['parts']['complete_solver_logs'],'ordered full logs;3 fsync/publication;source-derived budget64KiB/step'),
        ('selected full raw audit','<=7/series',9*2**30,b05['parts']['full_raw_audits'],'spool plus streaming hash; additional spool fsync;9GiB storage burst, not9GiB resident allocation'),
        ('selected bundle','<=56/series',512*2**20,b05['parts']['selected_bundles'],'join retained records and atomic publish;temporary memory spike distinct from spool'),
        ('R2 field snapshots','<=505/series',16*2**20,b05['parts']['field_snapshots'],'inherited initial/startup/development/arrival/final schedule;per-write field buffer cap'),
        ('fixed provenance/static','once/series',2**30,b05['parts']['fixed_provenance_and_static'],'static blobs and retained inputs/source/manifests;not bulk throughput proof'),
    ]:io_model.append({'Evidence class':name,'Frequency':freq,'Bytes/write planning cap':int(per),'Total bytes Co0p5 maximum cap':total,'Estimated I/O burden':burden})
    io_trials=primitive['io_trials'];io_median=statistics.median(x['total_with_directory_fsync_seconds'] for x in io_trials)
    speed=16*2**20/io_median
    io_observation={'bytes_per_trial':16*2**20,'repeats':3,'median_write_file_directory_fsync_s':io_median,
        'min_total_s':min(x['total_with_directory_fsync_seconds'] for x in io_trials),'max_total_s':max(x['total_with_directory_fsync_seconds'] for x in io_trials),
        'effective_MB_s':speed/1e6,'9GiB_same_speed_illustration_s':9*2**30/speed,
        'classification':'CACHED_SMALL_WRITE_ONLY_NOT_SUSTAINED_THROUGHPUT_OR_MAX_AUDIT_MEASUREMENT'}
    bottlenecks=[
        {'Bottleneck':'diagnostic canonical/packet/object work','Severity':'HIGH','Evidence':f'full state every {ncallback} callbacks/step; target shape Python subtotal {representative_diag:.2g}s/step','Mitigation requiring contract change?':'Separate implementation qualification/revision; no changes made','Production ranking':'leading candidate, not proven full-pipeline dominance'},
        {'Bottleneck':'U03 arrival-window repeated history validation','Severity':'HIGH','Evidence':'101/201/401 nodes ~quadratic timings;15001 aborted;planning30k/60k/120k history nodes','Mitigation requiring contract change?':'Any optimization needs separate semantic-preservation qualification','Production ranking':'candidate spike bottleneck'},
        {'Bottleneck':'pressure solves','Severity':'HIGH','Evidence':'48calls/step;baseline pressure mean114–227iterations/call, U/e means~1–3','Mitigation requiring contract change?':'No fixed24/linear changes here; future MPI/U01 studies only','Production ranking':'likely core-solver leader; per-component timing absent'},
        {'Bottleneck':'momentum/energy/density/thermo/assembly','Severity':'UNKNOWN','Evidence':'24U+24e+49rho;no isolated real cost measurements','Mitigation requiring contract change?':'Bounded timing qualification first','Production ranking':'UNRESOLVED'},
        {'Bottleneck':'JSON IPC','Severity':'HIGH','Evidence':'synchronous ACK after evaluator/retention;~7.4MB shape packet;socket-only transfer much smaller than canonical/packing','Mitigation requiring contract change?':'Transport revision would need separate review','Production ranking':'serialization/backend work exceeds bare socket in shape test'},
        {'Bottleneck':'memory','Severity':'UNKNOWN','Evidence':'bounded packed rings/bundles but pre-encoding objects and selected spikes unmeasured','Mitigation requiring contract change?':'Target-size resource qualification first','Production ranking':'UNRESOLVED'},
        {'Bottleneck':'I/O throughput','Severity':'UNKNOWN','Evidence':'9GiB audit /512MiB bundle /16MiB field caps;only3x16MiB measured','Mitigation requiring contract change?':'No persistence/cadence changes;bounded burst qualification','Production ranking':'UNRESOLVED sustained throughput'},
        {'Bottleneck':'fsync latency','Severity':'MEDIUM','Evidence':'3file/directory/manifest fsync per publication;small fixture ~milliseconds','Mitigation requiring contract change?':'No durability changes here','Production ranking':'small-file sample available;long-tail unresolved'},
        {'Bottleneck':'continuous-run operational risk','Severity':'HIGH','Evidence':'even core-only proxy primary runs days;shape stress runs years;single continuous process/no resume','Mitigation requiring contract change?':'Uptime/process-supervision plan;checkpoint restart would require a revision','Production ranking':'feasibility qualification blocker'},
    ]
    sensitivity=[{'Step factor':a,'Cost factor':b,'Total runtime factor':a*b,'scope':'PLANNING_ONLY_NOT_PHYSICAL_PREDICTION'} for a in (.5,.75,1.,1.25,1.5) for b in (.5,.75,1.,1.25,1.5)]
    options=[{'option':'A current serial/fixed24','information_value':'MEDIUM','assessment':'Preserves science; insufficient target-stage/whole-step evidence; no run now'},
             {'option':'B future MPI diagnostic qualification','information_value':'HIGH','assessment':'Could accelerate core/partitioned diagnostics; no24-thread factor assumed. Serial Python backend and global identities need design/qualification'},
             {'option':'C U01 outer-policy review','information_value':'MEDIUM','assessment':'24 exists for k21–24 certificate. Reducing outer count alone does not resolve callback serialization or quadratic arrival; separate scientific task only'},
             {'option':'D bounded production-like timing qualification preparation','information_value':'HIGH','assessment':'Next task defines hard CPU/time/disk/RSS bounds and authorization; no pilot/short CFD authorized by this review'}]
    statuses=dict(c['final_status'])
    statuses.update(ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY_REVIEW='COMPLETE',
        DIAGNOSTIC_CONTRACT_VERSION='1.5',DIAGNOSTIC_CONTRACT_HASH_VERIFIED='YES',DIAGNOSTIC_CONTRACT_SHA256=sha(R/'docs/routeA_diagnostic_transient_contract_v1.5.json'),
        HOST_CPU_MODEL=ls['Model name'],HOST_PHYSICAL_CORES=int(ls['Core(s) per socket'])*int(ls['Socket(s)']),HOST_LOGICAL_CPUS=int(ls['CPU(s)']),
        HOST_MEM_TOTAL_BYTES=mem['MemTotal'],HOST_MEM_AVAILABLE_BYTES=mem['MemAvailable'],PARALLEL_DIAGNOSTIC_SUPPORT='NOT_VALIDATED',CURRENT_EXECUTION_MODE='SERIAL',
        FV_SOLVES_PER_PHYSICAL_STEP=145,SCALAR_COMPONENT_RECORDS_PER_PHYSICAL_STEP=169,CO05_STEPS_PLANNING=series['0.5']['steps_planning_only'],
        CO025_STEPS_PLANNING=series['0.25']['steps_planning_only'],CO0125_STEPS_PLANNING=series['0.125']['steps_planning_only'],
        EXISTING_REAL_CFD_TIMING_EVIDENCE='PARTIAL',SYNTHETIC_TIMING_EXECUTED='YES',SYNTHETIC_TIMING_SCOPE='SYNTHETIC_ONLY',
        CORE_SOLVER_COST_ESTIMATE=f'~{core["optimistic"]:.1g}–{core["conservative"]:.1g} s/step ROUGH_COMPONENT_COST_PROXY; production cost UNRESOLVED',
        DIAGNOSTIC_OVERHEAD_ESTIMATE=f'UNRESOLVED; four-cell ON {summary["ON"]["median_wall_s"]:.2g}s/OFF {summary["OFF"]["median_wall_s"]:.2g}s; target-shape Python subtotal ~{representative_diag:.1g}s/step, not production',
        COMPUTE_FEASIBILITY='UNRESOLVED',COMPUTE_CONFIDENCE='LOW',MEMORY_PEAK_ESTIMATE_BYTES='UNRESOLVED',MEMORY_FEASIBILITY='UNRESOLVED',MEMORY_CONFIDENCE='LOW',
        AVERAGE_IO_RATE_ESTIMATE='UNRESOLVED production; cap-based conditional GB/hour and MB/s tables provided',
        PEAK_IO_BURST_ESTIMATE='9 GiB full-audit cap; 512 MiB bundle cap; 16 MiB field cap; durations UNRESOLVED',IO_FEASIBILITY='UNRESOLVED',IO_CONFIDENCE='LOW',
        CORE_SOLVER_COMPUTE_RISK='HIGH',DIAGNOSTIC_COMPUTE_RISK='HIGH',IPC_RISK='HIGH',MEMORY_RISK='UNKNOWN',IO_THROUGHPUT_RISK='UNKNOWN',FSYNC_LATENCY_RISK='MEDIUM',
        LONG_RUN_OPERATIONAL_RISK='HIGH',SERIAL_ONLY_RESOURCE_RISK='HIGH',CURRENT_FROZEN_DESIGN_PRACTICALLY_EXECUTABLE='UNRESOLVED',
        BOUNDED_TIMING_QUALIFICATION_REQUIRED='YES',COMPUTE_POLICY_REVISION_REQUIRED='UNRESOLVED',MPI_QUALIFICATION_INFORMATION_VALUE='HIGH',U01_OUTER_POLICY_REVIEW_INFORMATION_VALUE='MEDIUM',
        EXECUTION_AUTHORIZED='NO',COMPLETE_EXECUTION_CONFIGURATION_FROZEN='NO',PILOT_CFD_EXECUTED='NO',
        N_OUTER_CORRECTORS_CHANGED='NO',LINEAR_SOLVER_POLICY_CHANGED='NO',TEMPORAL_POLICY_CHANGED='NO',PERSISTENCE_POLICY_CHANGED='NO',SEAL_PURGE_POLICY_CHANGED='NO',RETENTION_POLICY_CHANGED='NO',
        NEXT_SINGLE_TASK='PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_BOUNDED_TIMING_QUALIFICATION')
    for key in ('CO05_TSTAR05_RUNTIME_ESTIMATE','CO05_TSTAR1_RUNTIME_ESTIMATE','CO05_TSTAR2_RUNTIME_ESTIMATE','CO025_TSTAR05_RUNTIME_ESTIMATE','CO025_TSTAR1_RUNTIME_ESTIMATE','CO025_TSTAR2_RUNTIME_ESTIMATE','CO0125_TSTAR2_RUNTIME_ESTIMATE'):statuses[key]='UNRESOLVED'
    request=Path('/home/mirai/.codex/attachments/9bf8516f-b8f1-4f1f-a86f-f519c796200c/貼り付けたテキスト.txt').read_text();block=request.split('# 101. REQUIRED FINAL STATUS')[1].split('# 102.')[0]
    required=re.findall(r'^([A-Z][A-Z0-9_]+)\s*=\s*\n',block,re.M);assert all(k in statuses for k in required),[k for k in required if k not in statuses]
    final={k:statuses[k] for k in required}
    sections=[
        ('Executive summary','Review COMPLETE; compute/memory/I/O and practical executable status remain UNRESOLVED. Current frozen serial/fixed24 design is not qualified for a run. Existing CFD timing is partial; synthetic tests reveal substantial serialization/evaluator overhead and quadratic arrival-window work. No arbitrary wall-clock deadline or formal pass/fail criterion was introduced. No numerical, persistence or authority changes.'),
        ('Authority verification',f'HEAD {start["HEAD"]} equals requested708881e95dc83456ae43b574984a29c37d303ef0. v1.5 and formalv1.7 supplied hashes verified before/after. Protected v1.4 implementation hashes verified scoped to this task. v1.5 JSON/MD/sidecar read-only; no v1.6. Reports are review findings, not updates to canonical readiness. launcher.prepare remains pinned to version1.4; compatibility is a separate authority/runtime blocker, not compute performance.'),
        ('Host hardware',f'{ls["Model name"]};12 physical cores/24 logical CPUs,1 socket/1 NUMA,800–4700MHz reported range;L1d576KiB/L1i384KiB aggregate,L2 24MiB,L3 30MiB. MemTotal {mem["MemTotal"]} B;MemAvailable {mem["MemAvailable"]} B at recorded inspection. >=24GiB host preflight satisfied. NVMe-backed local filesystem;raw lsblk/findmnt/df/free/meminfo/nproc/uname/uptime saved. Swap exists but no fit/speed assumption uses swap. Initial uptime ~7days is past observation, not future guarantee;logical CPU count supplies no serial speedup.'),
        ('Frozen transient workload','Exact numerical dictionary follows below:24 outer/2pressure/0nonorthogonal, momentumPredictor=true,simpleRho=false,transonic=false,consistent=false; no early residual termination, empty relaxationFactors. U01 requires four terminal transitions ending21–24. Source native density predictor runs once when transient/simpleRho=false; each of48 pressure correctors solves density again. Source is inspected, not executed as CFD.'),
        ('Step-count scenarios','PLANNING_ONLY: maximum200061/400122/800244 steps at t*=2 from accepted steady prospective speed, not actual adaptive controller trajectory. For t*=0.5/1/2 use ceil(maximum*endpoint/2);startup ramp/arrival can change these counts. Earliest scenario is best-case planning, not prediction. Each series is independent cold start;Co0.125 comparison only, conditional/review/authorization and worst-case disk policy unchanged.'),
        ('Solve-count model','Perstep U24 vector fv calls, e24, pressure48, rho49 =145fv calls. U contributes48 Ux/Uy records;total169 scalar records. Native source loop/density hooks plus all three synthetic primary rows confirm counts. Call count differs from Krylov iteration count;rho diagonal solve may have0 reported iterations. Full graph1141 in-step callbacks+3controller callbacks=1144 recurring;one constructor once. Four-cell test1152 records also contains7 auxiliary fixtures;those are not production work.701 physical-step matrix packets lead to >=1475 replay_matrix calls from two evaluator passes plus73 solved-stage identities;additional matrix_action/end evaluations not included in that count.'),
        ('Existing real CFD timing evidence','Read-only7 segment logs: baseline end3000/6000/9000 and GateH end3000/6000/9000/12000;each3000steady iterations,nProcs1. Same host/build. Baseline wall/iteration~0.128/0.102/0.071s;GateH late~0.033s. Pressure mean iterations/call baseline~227/178/114 while U/e are~1–3. Full distributions, calls,total iterations,CPU/ClockTime and hashes saved. ClockTime has1second resolution;CPU deltas useful for proxy. Logs include assembly/thermo/function objects/output and different relaxation/tolerance. They do not isolate solve cost or measure transient adaptive coupling.'),
        ('Synthetic diagnostic timing',f'Three balanced-order OFF/ON repeats of saved four-cell manufactured native driver, one24-outer synthetic step plus auxiliary fixtures. OFF median {summary["OFF"]["median_wall_s"]:.3g}s;ON {summary["ON"]["median_wall_s"]:.3g}s, range {summary["ON"]["min_wall_s"]:.3g}–{summary["ON"]["max_wall_s"]:.3g}s. fdiag={summary["synthetic_overhead_fraction"]:.3%} is SYNTHETIC_ONLY, not production percentage. GNU time max-single-process RSS~86MiB ON is not native+backend simultaneous RSS and is not scaled to160². Actual load/host busy fractions saved;low host utilization but no frequency/isolation guarantee. Historical U04 P0 ON20.92s/OFF0.289s and v1.3/v1.4 synthetic RSS records are auxiliary evidence, not current production timing. No fresh P0/v1.3 suite or physical run.'),
        ('CFD core compute model',f'Historical workload group = U+e+2pressure.24groups form a core-only reference~{core["optimistic"]:.2g}–{core["conservative"]:.2g}s/step,central~{core["central"]:.2g}s. Factors0.5/1/3 are explicit sensitivity assumptions for transient diagonal/coupling/1e-12/unrelaxed changes, not measured bounds. Multiplying raw steady iteration time directly by transient steps is not used. Core-only central Co0.5 maximum~{series["0.5"]["steps_planning_only"]*core["central"]/86400:.2g}days,Co0.25~{series["0.25"]["steps_planning_only"]*core["central"]/86400:.2g}days;diagnostics and actual transient changes absent. Pressure is likely core leader by iteration workload but isolated cost ranking remains unmeasured.'),
        ('Diagnostic overhead model',f'Tstep=TCFD+Tevaluator+Tprimary+TIPC+Tpacking+Thashing+Tlogging+TselectedIO. Target-size non-CFD arrays have25600cells/50880internal faces;actual canonical/replay/pack/QoI functions timed3times. Representative payload JSON~{primitive["payload_JSON_bytes"]/1e6:.2g}MB. Python subtotal model1144*(state canonical+payload canonical+JSON decode+packed encode)+1475*sparse replay+25*QoI+U01 =~{representative_diag:.2g}s/step. It is a CONDITIONAL SHAPE stress model, not target-pipeline measurement or confidence range. It omits native C++ Json construction, more field/BC/hash passes,static-sharing encode, end matrix work,real selected writes and U03spikes. Different stage sizes/matrix diagonal-vs-sparse/value formatting may reduce or enlarge it. P1 saves disk bytes by reducing after evaluation;every raw state still serializes/evaluates. Bare socket/16MiB SHA costs are small relative to canonical/packing in this shape test. True production diagnostic fraction UNRESOLVED.'),
        ('Runtime projections','Tables show nine conditional optimistic/central/conservative shape scenarios,using0.5/1/2*Python subtotal plus core proxy. They can imply months/years, which flags high information value of further timing;they are neither predictions nor strict lower/upper bounds. Qualified runtime estimates remain UNRESOLVED rather than presenting a misleading precise range. Raw seconds retained for reproducibility;human durations rounded. Separate core-only rows and walltime/t*/physical-second metrics expose assumptions. Conditional Co0.125 remains unauthorized regardless of estimate.'),
        ('Step-count/cost sensitivity','Steps vary0.5–1.5 and per-step cost0.5–1.5 independently;total scales by product (0.75x0.75=0.5625,1.25x1.25=1.5625,1.5x1.5=2.25). These are planning sensitivities, not physical uncertainty distributions. Startup/developed linear iterations and adaptive deltaT can differ. Arrival evaluations are nonlinear in retained node count;linear whole-step model omits their spikes.'),
        ('Memory model',f'Numeric lower storage, retained-byte ceilings, Python estimates and actual high-water RSS are distinguished below. Host memory headroom exists but process8GiB AS fit remains unproven. Explicit retained buffers ring512MiB+bundle512MiB+receipt64MiB+primary16MiB+stage32MiB+field16MiB exceed old1.19GB accounting once added copies/outer history are included. Bundle joining can transiently add512MiB–1GiB;receipt concatenation adds128MiB;C++/Python objects,old histories/term packets,matrix replay rows and canonical strings are extra. Full9GiB audit is streamed disk spool, not full-RSS allocation. Synchronization list resets after each yield;last5 and ring are bounded,arrival only retains bracketing0.3history. Primitive process high-water~{primitive["baseline_RSS_KiB"]*1024/2**20:.2g}MiB is synthetic data-shape observation,not production peak. Overall peak UNRESOLVED;no tiny-cell RSS scaling.'),
        ('I/O model',f'Unchanged64-step receipt/primary chunks,4MiB log rotation,max7 full9GiB audits,56x512MiB bundles,505x16MiB fields and provenance caps. Full Co0.5 permanent178636906968B/Co0.25 250017072048B unchanged. Raw data transmitted and reduced each stage is not total retained I/O;historical9.70GB numerical payload/step was a rough schema projection,not disk usage or measured socket traffic. Three16MiB write+file/directory-fsync samples median{io_median:.3g}s,~{speed/1e6:.2g}MB/s effective cached small-write rate. Sustained9GiB audit/background contention and hash-read latency UNRESOLVED. Tables include cap-based average GB/hour,MB/s,files/hour,fsync/hour for each shape scenario. Three durable actions/publication and extra audit spool fsync counted as lower bound;immutable/trigger/seal/validation tail work extra. Early-arrival tables keep full fixed caps intentionally conservative. No throughput/storage policy change.'),
        ('Long-run operational risk','Single continuous process perCo;process termination invalidates primary/no resume. Core-only reference already days;shape stress scenarios can be much longer. Reboot/power/maintenance/native/backend failures and resource quotas matter;no permitted wall-clock maximum or reliability guarantee supplied. SSH disconnect itself is not identical to process termination if future supervision detaches the process;supervision is not modified here. Prior uptime is not evidence of future uninterrupted reliability.'),
        ('Serial-only assessment','Current qualified evidence is serial,nProcs1. Observer has per-process sequence/state graph and synchronous single Python backend;no MPI diagnostic aggregation/hash/arrival/native proof inspected or found. PARALLEL_DIAGNOSTIC_SUPPORT=NOT_VALIDATED. Available24 logical CPUs does not multiply serial throughput. Future MPI could have high value but bottlenecks in canonical/arrival/backend may not scale;no MPI/OpenMP implementation or execution.'),
        ('Bottleneck ranking','Evidence-backed candidate ranking in table. Diagnostic object/canonical/packing/replay work and U03quadratic validation are highest measurement priorities;pressure likely leads core by iteration workload. U03interpolate scans all times/values and monotonicity per sampled point;window_stats/integral calls it repeatedly,thereforeO(Nnodes²).101/201/401node medians show near4x cost per doubling.15001-node attempt was manually aborted after at least37s to keep this review bounded;not a completed timing or production bound. Planning last0.3window nodes~30k/60k/120k;quadratic projections below are LOW_CONFIDENCE stress estimates,not a timed arrival. Dominant actual full production bottleneck remains UNRESOLVED.'),
        ('Compute feasibility','UNRESOLVED/LOW confidence. Existing real CFD component evidence plus shape-level measurements do not qualify coupled target-step cost,adaptive future counts,spikes and continuous-run practicality. Feasible would mean demonstrated unchanged full target workload,acceptable user-defined run budget and reliability;infeasible would require a hard resource contradiction or unacceptable agreed budget. Neither can be concluded from fast CPU,operation count,or arbitrary7day rule. Evidence signals HIGH risk and justifies bounded qualification preparation.'),
        ('Memory feasibility','UNRESOLVED/LOW confidence. Read-only available RAM passes host preflight and target-shape primitivefits;native/backend actual concurrent AS/RSS and selected-audit/canonical peaks not measured.8GiB cap and24GiB available are guards,not proof. Marginal/feasible/infeasible labels are withheld until target workload peak is bounded.'),
        ('I/O feasibility','UNRESOLVED/LOW confidence. Storage capacity remains FEASIBLE/storage-readyYES under inherited planning guard;cached16MiB local writes supply small-latency evidence only. Sustainedselected audit and durable manifest workload not qualified. Disk capacity and throughput are separate questions.'),
        ('Overall resource readiness','Resource-readyNO,configuration-frozenNO,execution-authorizedNO. Scientific/technical/storage readinessYES preserved from v1.5. launcher version1.4 compatibility and future provenance/cold-start recipe binding remain separate pre-run blockers. Contract and all formal/historical status read-only;review findings do not overwrite canonical authority.'),
        ('Evidence limitations','No production/pilot/short CFD,case/mesh/init,physical arrival or native160² timing. Shape fixtures omitpatch values,static geometry/actual history epoch identities and multiple per-stage payload distributions;they exercise existing primitive functions without changing algorithms. CPU frequency/cache/load not pinned;smallI/O may be cached. AS/RSS roles and caps differ. Current OFF/ON one-step driver includes setup/fingerprints andauxiliary fixtures;production percentages not inferred. One U03fixture preparation failed for missing test harness attributes and another for insufficient bracketing;corrected fixtures only are timing evidence. The large-node microbenchmark was stopped;no physicalsolver process terminated. All illustrative scenarios retain uncertainty and qualified estimates remainUNRESOLVED.'),
        ('Exact next task','PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_BOUNDED_TIMING_QUALIFICATION. Define minimal production-like stage/whole-step resource measurement scope,bounds,mandatory failure criteria,source/authority compatibility and explicit authorization in that separate task. No CFD is automatically authorized. Compare serial preservation,MPI qualification,U01policy review andboundedqualification options below;do not reduce24outer or modify tolerance/cadence in this review.'),
    ]
    sources=[R/'docs/routeA_diagnostic_transient_contract_v1.5.json',R/'docs/routeA_execution_contract_v1.7.json',
             R/'Scripts/routeA/diagnostic_transient/v1_4/launcher.py',R/'Scripts/routeA/diagnostic_transient/v1_4/NativeStageObserver.C',
             R/'Scripts/routeA/diagnostic_transient/v1_4/online_evaluator.py',R/'Scripts/routeA/diagnostic_transient/v1_4/synthetic_native_binding_driver.C',
             R/'Scripts/routeA/diagnostic_transient/v1_4/persistence.py',R/'Scripts/routeA/diagnostic_transient/v1_4/live_collector.py',
             R/'Scripts/routeA/diagnostic_transient/v1_1/contract_policy.py',R/'cases/routeA/A-Ra1e6-fine/constant/polyMesh/boundary',
             Path('/opt/openfoam13/applications/modules/isothermalFluid/isothermalFluid.C'),
             Path('/opt/openfoam13/applications/modules/isothermalFluid/momentumPredictor.C'),
             Path('/opt/openfoam13/applications/modules/isothermalFluid/correctBuoyantPressure.C'),
             Path('/opt/openfoam13/applications/modules/isothermalFluid/correctDensity.C'),
             Path('/opt/openfoam13/applications/modules/fluid/thermophysicalPredictor.C')]
    sources+=[R/x['path'] for x in steady]
    sources+=[O/name for name in ('host_hardware.json','native_timings.json','primitive_timings.json','supplemental_timings.json','callback_workload.json','steady_timing_evidence.json','measure.py','extra_measure.py','make_report.py')]
    report={'task':'REVIEW_ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY','status':final,'additional_invariance_status':{k:statuses[k] for k in ('U01_CHANGED','U02_CHANGED','U03_CHANGED','U04_EQUATION_SEMANTICS_CHANGED','N_OUTER_CORRECTORS_CHANGED','LINEAR_SOLVER_POLICY_CHANGED','TEMPORAL_POLICY_CHANGED','PERSISTENCE_POLICY_CHANGED','SEAL_PURGE_POLICY_CHANGED','RETENTION_POLICY_CHANGED','CASE_GENERATED','MESH_GENERATED','INITIALIZATION_EXECUTED','BENCHMARK_CORE_PASS','ROUTE_A_CHARACTERIZED','ALL_ROUTE_A_GATE_F','ALL_RA_NEEDS_320','GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED')},
        'sections':[{'number':i,'title':title,'text':text} for i,(title,text) in enumerate(sections,1)],'start_guard':start,
        'host_memory_snapshot_bytes':mem,'hardware':ls,'exact_frozen_linear_dictionary':c['transient_algorithm']['linear_solver_dictionary'],
        'frozen_switches':c['transient_algorithm']['frozen_switches'],'relaxationFactors':c['transient_algorithm']['relaxationFactors'],
        'solve_counts_per_step':counts,'solve_count_scenarios':solve_rows,'callback_workload':callbacks,'steady_timing_evidence':steady,
        'native_summary_SYNTHETIC_ONLY':summary,'primitive_measurements_SYNTHETIC_ONLY':primitive,'supplemental_measurements_SYNTHETIC_ONLY':supp,
        'compute_model':computations,'model_parameters':{'core_proxy_seconds_per_step':core,'Python_shape_subtotal_seconds_per_step':representative_diag,
            'diagnostic_shape_sensitivity_seconds_per_step':diag,'combined_shape_seconds_per_step':step,'qualification':'NOT_PRODUCTION_QUALIFIED','mandatory_callback_primitive_subtotal':required_callback},
        'runtime_scenarios':runtime,'sensitivity':sensitivity,'memory_model':memory,'io_model':io_model,'io_rates':io_rates,'io_observation':io_observation,
        'arrival_quadratic_sensitivity':arrival_rows,'bottlenecks':bottlenecks,'options':options,
        'input_sha256':{str(path):sha(path) for path in sources},'invariance_verification':{'all_scoped_protected_hashes_equal':True,'canonical_v1_5_unchanged':True,'formal_v1_7_unchanged':True},
        'end_guard':{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'git_status_short':subprocess.check_output(['git','status','--short'],text=True),'git_diff_stat':subprocess.check_output(['git','diff','--stat'],text=True)}}
    csvout('DiagnosticTransient_compute_model.csv',computations);csvout('DiagnosticTransient_runtime_scenarios.csv',runtime)
    csvout('DiagnosticTransient_memory_model.csv',memory);csvout('DiagnosticTransient_io_model.csv',io_model);csvout('DiagnosticTransient_bottleneck_ranking.csv',bottlenecks)
    csvout('DiagnosticTransient_solve_counts.csv',solve_rows);csvout('DiagnosticTransient_io_rates.csv',io_rates);csvout('DiagnosticTransient_runtime_sensitivity.csv',sensitivity)
    write(P/'DiagnosticTransient_compute_feasibility_review.json',report)
    md='# Route A diagnostic transient compute feasibility review\n\n'
    for i,(title,text) in enumerate(sections,1):
        md+=f'## {i}. {title}\n\n{text}\n\n'
        if i==4:md+='```json\n'+json.dumps(c['transient_algorithm']['linear_solver_dictionary'],indent=2)+'\n```\n\n'
        if i==6:md+=table(solve_rows,['Co','t_star_end','Steps_PLANNING_ONLY','fv_solves_per_step','total_fv_solves','total_scalar_records','U_fv_calls','e_calls','pressure_calls','rho_calls'])
        if i==7:
            logs=[{'Case':x['case'],'Segment':x['steady_iteration_last'],'Iterations':x['steps'],'CPU seconds':round(x['cpu_seconds_last'],3),'Clock seconds':x['clock_seconds_last'],'Wall s/iteration':round(x['wall_s_per_iteration_including_startup'],4),'Mean pressure iterations':round(x['field_iterations']['p_rgh']['mean'],1)} for x in steady]
            md+=table(logs,list(logs[0]))
        if i==8:md+=table([{'Mode':mode,**values} for mode,values in summary.items() if isinstance(values,dict)],['Mode','min_wall_s','median_wall_s','max_wall_s','median_max_single_process_RSS_KiB'])
        if i in (9,10):
            if i==9:md+=table(computations,list(computations[0]))
            else:md+=table([{'Primitive':x['component'],'Median seconds':round(x['median'],5),'Min':round(x['min'],5),'Max':round(x['max'],5)} for x in primitive['timings']+supp['timings']],['Primitive','Median seconds','Min','Max'])
        if i==11:md+='**Conditional data-shape stress scenarios, not qualified runtime ranges:**\n\n'+table(runtime,['Co','t_star_end','Steps_PLANNING_ONLY','Optimistic_SHAPE_ONLY','Central_SHAPE_ONLY','Conservative_SHAPE_ONLY','qualified_runtime_estimate'])
        if i==12:md+=table(sensitivity,['Step factor','Cost factor','Total runtime factor'])
        if i==13:md+=table(memory,list(memory[0]))
        if i==14:md+=table(io_model,list(io_model[0]));md+=table(io_rates,['Co','t_star_end','scenario','GB_per_hour','MB_per_second','files_per_hour','fsync_per_hour_lower_bound'])
        if i==17:md+=table(bottlenecks,list(bottlenecks[0]));md+=table(arrival_rows,['Co','last_0p3_window_nodes_PLANNING_ONLY','candidate_cost_shape_proxy','arrival_memory_Python_scalar_estimate_bytes','classification'])
        if i==23:md+=table(options,list(options[0]))
    md+='## Required final status\n\n```text\n'+'\n'.join(k+' = '+str(v) for k,v in final.items())+'\n```\n\n'
    md+='No git add/commit/push. New review artifacts remain untracked; tracked git diff --stat is empty. Referenced source/evidence hashes, raw hardware/timing data and all scenario parameters are retained in the JSON report and compute_review directory.\n'
    (P/'DiagnosticTransient_compute_feasibility_review.md').write_text(md)
    print(json.dumps({'result':'COMPLETE','compute':'UNRESOLVED','memory':'UNRESOLVED','IO':'UNRESOLVED',
                      'Python_shape_subtotal_s_per_step':representative_diag,'conditional_Co05_tstar2':runtime[2]['Central_SHAPE_ONLY'],
                      'next_task':final['NEXT_SINGLE_TASK']},indent=2))

if __name__=='__main__':main()
