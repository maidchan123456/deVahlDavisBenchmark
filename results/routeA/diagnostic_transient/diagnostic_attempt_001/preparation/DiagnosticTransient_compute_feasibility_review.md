# Route A diagnostic transient compute feasibility review

## 1. Executive summary

Review COMPLETE; compute/memory/I/O and practical executable status remain UNRESOLVED. Current frozen serial/fixed24 design is not qualified for a run. Existing CFD timing is partial; synthetic tests reveal substantial serialization/evaluator overhead and quadratic arrival-window work. No arbitrary wall-clock deadline or formal pass/fail criterion was introduced. No numerical, persistence or authority changes.

## 2. Authority verification

HEAD 708881e95dc83456ae43b574984a29c37d303ef0 equals requested708881e95dc83456ae43b574984a29c37d303ef0. v1.5 and formalv1.7 supplied hashes verified before/after. Protected v1.4 implementation hashes verified scoped to this task. v1.5 JSON/MD/sidecar read-only; no v1.6. Reports are review findings, not updates to canonical readiness. launcher.prepare remains pinned to version1.4; compatibility is a separate authority/runtime blocker, not compute performance.

## 3. Host hardware

Intel(R) Xeon(R) w5-2545;12 physical cores/24 logical CPUs,1 socket/1 NUMA,800–4700MHz reported range;L1d576KiB/L1i384KiB aggregate,L2 24MiB,L3 30MiB. MemTotal 66619408384 B;MemAvailable 63353577472 B at recorded inspection. >=24GiB host preflight satisfied. NVMe-backed local filesystem;raw lsblk/findmnt/df/free/meminfo/nproc/uname/uptime saved. Swap exists but no fit/speed assumption uses swap. Initial uptime ~7days is past observation, not future guarantee;logical CPU count supplies no serial speedup.

## 4. Frozen transient workload

Exact numerical dictionary follows below:24 outer/2pressure/0nonorthogonal, momentumPredictor=true,simpleRho=false,transonic=false,consistent=false; no early residual termination, empty relaxationFactors. U01 requires four terminal transitions ending21–24. Source native density predictor runs once when transient/simpleRho=false; each of48 pressure correctors solves density again. Source is inspected, not executed as CFD.

```json
{
  "U": {
    "solver": "PBiCGStab",
    "preconditioner": "DILU",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 2000
  },
  "e": {
    "solver": "PBiCGStab",
    "preconditioner": "DILU",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 2000
  },
  "p_rgh": {
    "solver": "PCG",
    "preconditioner": "DIC",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 4000
  },
  "rho": {
    "solver": "diagonal",
    "tolerance": 1e-14,
    "relTol": 0,
    "maxIter": 1
  },
  "UFinal": {
    "solver": "PBiCGStab",
    "preconditioner": "DILU",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 2000
  },
  "eFinal": {
    "solver": "PBiCGStab",
    "preconditioner": "DILU",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 2000
  },
  "p_rghFinal": {
    "solver": "PCG",
    "preconditioner": "DIC",
    "tolerance": 1e-12,
    "relTol": 0,
    "maxIter": 4000
  },
  "rhoFinal": {
    "solver": "diagonal",
    "tolerance": 1e-14,
    "relTol": 0,
    "maxIter": 1
  }
}
```

## 5. Step-count scenarios

PLANNING_ONLY: maximum200061/400122/800244 steps at t*=2 from accepted steady prospective speed, not actual adaptive controller trajectory. For t*=0.5/1/2 use ceil(maximum*endpoint/2);startup ramp/arrival can change these counts. Earliest scenario is best-case planning, not prediction. Each series is independent cold start;Co0.125 comparison only, conditional/review/authorization and worst-case disk policy unchanged.

## 6. Solve-count model

Perstep U24 vector fv calls, e24, pressure48, rho49 =145fv calls. U contributes48 Ux/Uy records;total169 scalar records. Native source loop/density hooks plus all three synthetic primary rows confirm counts. Call count differs from Krylov iteration count;rho diagonal solve may have0 reported iterations. Full graph1141 in-step callbacks+3controller callbacks=1144 recurring;one constructor once. Four-cell test1152 records also contains7 auxiliary fixtures;those are not production work.701 physical-step matrix packets lead to >=1475 replay_matrix calls from two evaluator passes plus73 solved-stage identities;additional matrix_action/end evaluations not included in that count.

| Co | t_star_end | Steps_PLANNING_ONLY | fv_solves_per_step | total_fv_solves | total_scalar_records | U_fv_calls | e_calls | pressure_calls | rho_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.5 | 50016 | 145 | 7252320 | 8452704 | 1200384 | 1200384 | 2400768 | 2450784 |
| 0.5 | 1.0 | 100031 | 145 | 14504495 | 16905239 | 2400744 | 2400744 | 4801488 | 4901519 |
| 0.5 | 2.0 | 200061 | 145 | 29008845 | 33810309 | 4801464 | 4801464 | 9602928 | 9802989 |
| 0.25 | 0.5 | 100031 | 145 | 14504495 | 16905239 | 2400744 | 2400744 | 4801488 | 4901519 |
| 0.25 | 1.0 | 200061 | 145 | 29008845 | 33810309 | 4801464 | 4801464 | 9602928 | 9802989 |
| 0.25 | 2.0 | 400122 | 145 | 58017690 | 67620618 | 9602928 | 9602928 | 19205856 | 19605978 |
| 0.125 | 0.5 | 200061 | 145 | 29008845 | 33810309 | 4801464 | 4801464 | 9602928 | 9802989 |
| 0.125 | 1.0 | 400122 | 145 | 58017690 | 67620618 | 9602928 | 9602928 | 19205856 | 19605978 |
| 0.125 | 2.0 | 800244 | 145 | 116035380 | 135241236 | 19205856 | 19205856 | 38411712 | 39211956 |

## 7. Existing real CFD timing evidence

Read-only7 segment logs: baseline end3000/6000/9000 and GateH end3000/6000/9000/12000;each3000steady iterations,nProcs1. Same host/build. Baseline wall/iteration~0.128/0.102/0.071s;GateH late~0.033s. Pressure mean iterations/call baseline~227/178/114 while U/e are~1–3. Full distributions, calls,total iterations,CPU/ClockTime and hashes saved. ClockTime has1second resolution;CPU deltas useful for proxy. Logs include assembly/thermo/function objects/output and different relaxation/tolerance. They do not isolate solve cost or measure transient adaptive coupling.

| Case | Segment | Iterations | CPU seconds | Clock seconds | Wall s/iteration | Mean pressure iterations |
| --- | --- | --- | --- | --- | --- | --- |
| A-Ra1e6-fine | 3000.0 | 3000 | 383.435 | 384.0 | 0.128 | 226.9 |
| A-Ra1e6-fine | 6000.0 | 3000 | 307.575 | 307.0 | 0.1023 | 177.8 |
| A-Ra1e6-fine | 9000.0 | 3000 | 211.407 | 212.0 | 0.0707 | 113.7 |
| A-H-Ra1e6-fine-beta1e-4 | 12000.0 | 3000 | 97.882 | 98.0 | 0.0327 | 37.3 |
| A-H-Ra1e6-fine-beta1e-4 | 3000.0 | 3000 | 384.426 | 385.0 | 0.1283 | 226.7 |
| A-H-Ra1e6-fine-beta1e-4 | 6000.0 | 3000 | 307.998 | 308.0 | 0.1027 | 177.6 |
| A-H-Ra1e6-fine-beta1e-4 | 9000.0 | 3000 | 209.367 | 209.0 | 0.0697 | 112.3 |

## 8. Synthetic diagnostic timing

Three balanced-order OFF/ON repeats of saved four-cell manufactured native driver, one24-outer synthetic step plus auxiliary fixtures. OFF median 0.365s;ON 22.3s, range 21.5–22.3s. fdiag=98.360% is SYNTHETIC_ONLY, not production percentage. GNU time max-single-process RSS~86MiB ON is not native+backend simultaneous RSS and is not scaled to160². Actual load/host busy fractions saved;low host utilization but no frequency/isolation guarantee. Historical U04 P0 ON20.92s/OFF0.289s and v1.3/v1.4 synthetic RSS records are auxiliary evidence, not current production timing. No fresh P0/v1.3 suite or physical run.

| Mode | min_wall_s | median_wall_s | max_wall_s | median_max_single_process_RSS_KiB |
| --- | --- | --- | --- | --- |
| ON | 21.523232138948515 | 22.26968833594583 | 22.328719564015046 | 88028.0 |
| OFF | 0.3647940179798752 | 0.3651115819811821 | 0.3663363369414583 | 87540.0 |

## 9. CFD core compute model

Historical workload group = U+e+2pressure.24groups form a core-only reference~0.85–9.2s/step,central~2.5s. Factors0.5/1/3 are explicit sensitivity assumptions for transient diagonal/coupling/1e-12/unrelaxed changes, not measured bounds. Multiplying raw steady iteration time directly by transient steps is not used. Core-only central Co0.5 maximum~5.7days,Co0.25~11days;diagnostics and actual transient changes absent. Pressure is likely core leader by iteration workload but isolated cost ranking remains unmeasured.

| Component | Evidence source | Cost estimate | Confidence |
| --- | --- | --- | --- |
| CFD momentum/energy/pressure group | 7 historical SIMPLE segments; 3 baseline segments for numerical proxy | 0.85–9.2 s/physical-step proxy | LOW; relaxed 1e-10 SIMPLE differs from unrelaxed 1e-12 PIMPLE |
| rho49/thermo/assembly/field update | native OpenFOAM source graph; historical aggregate timing | UNRESOLVED separately; included only as uncertainty in core proxy | LOW |
| native observer/object/string construction | NativeStageObserver meshState/emit; tiny OFF/ON | UNRESOLVED at target size; not included in Python subtotal | LOW |
| mass/energy matrix replay | actual replay_matrix on manufactured 25600-cell/50880-face matrix | 0.0834 s/call; >= 1475 graph calls/step plus matrix_action/end work | MEDIUM primitive; LOW total-step extrapolation |
| canonical payload/state identities | actual online_evaluator.canonical, representative target-size state/payload | 0.215 / 0.309 s/state / payload; 1144 callbacks/step | MEDIUM shape-only; LOW production |
| primary QoI and 4097 extrema | actual primary_evidence.primary on 160x160 synthetic arrays | 0.0459 s/call; 24 outer_end + time_end and startup calls | MEDIUM primitive |
| U01 terminal certificate | actual Live.outer_certificate; stationary shared manufactured arrays | 0.0972 s/certificate | MEDIUM primitive, no production RSS claim |
| U03 arrival windows | frozen arrival_candidate, 101/201/401 nodes; 15001-node attempt aborted | quadratic history scan; target-node latency UNRESOLVED; supplemental scenario table | HIGH source complexity; LOW projected timing |
| JSON decode / Python encode | representative target-shape 7.4MB JSON | 0.0554 / 0.0941 s/callback | MEDIUM primitive; native encoder UNRESOLVED |
| AF_UNIX IPC ACK | 16MiB socketpair transfer with reader thread; no backend work | 0.00504 s/16MiB | MEDIUM primitive; production ACK includes all synchronous processing |
| binary packing | actual packed.encode on target-shape payload | 0.353 s/3679649 B packet | MEDIUM primitive; static sharing changes real packet size |
| SHA256 | 16MiB allocation + hashlib; canonical generation timed separately | 0.00895 s/16MiB incl allocation | MEDIUM primitive; native SHA code not isolated |
| logging / selected audit / fields / fsync | retention caps, actual publish/rotation code, 3x16MiB fsynced writes | average/burst models below; sustained multi-GiB latency UNRESOLVED | LOW sustained workload |

## 10. Diagnostic overhead model

Tstep=TCFD+Tevaluator+Tprimary+TIPC+Tpacking+Thashing+Tlogging+TselectedIO. Target-size non-CFD arrays have25600cells/50880internal faces;actual canonical/replay/pack/QoI functions timed3times. Representative payload JSON~7.4MB. Python subtotal model1144*(state canonical+payload canonical+JSON decode+packed encode)+1475*sparse replay+25*QoI+U01 =~1.2e+03s/step. It is a CONDITIONAL SHAPE stress model, not target-pipeline measurement or confidence range. It omits native C++ Json construction, more field/BC/hash passes,static-sharing encode, end matrix work,real selected writes and U03spikes. Different stage sizes/matrix diagonal-vs-sparse/value formatting may reduce or enlarge it. P1 saves disk bytes by reducing after evaluation;every raw state still serializes/evaluates. Bare socket/16MiB SHA costs are small relative to canonical/packing in this shape test. True production diagnostic fraction UNRESOLVED.

| Primitive | Median seconds | Min | Max |
| --- | --- | --- | --- |
| primary_QoI_4097_points | 0.04589 | 0.03829 | 0.05141 |
| canonical_state_string | 0.21454 | 0.21405 | 0.22128 |
| canonical_payload_string | 0.30878 | 0.30624 | 0.30886 |
| JSON_encode_payload | 0.09408 | 0.09397 | 0.09837 |
| JSON_decode_payload | 0.05538 | 0.0546 | 0.05545 |
| binary_pack_payload | 0.35297 | 0.35127 | 0.35584 |
| matrix_replay_including_epoch_hash | 0.08339 | 0.08184 | 0.0841 |
| SHA256_16MiB | 0.00895 | 0.00881 | 0.00902 |
| U01_terminal_certificate_25600 | 0.09722 | 0.09295 | 0.10064 |
| AF_UNIX_16MiB_ACK_no_backend_work | 0.00504 | 0.00459 | 0.00589 |
| U03_three_windows_101_nodes | 0.01158 | 0.01154 | 0.01218 |
| U03_three_windows_201_nodes | 0.04033 | 0.04007 | 0.04095 |
| U03_three_windows_401_nodes | 0.15504 | 0.15196 | 0.1556 |

## 11. Runtime projections

Tables show nine conditional optimistic/central/conservative shape scenarios,using0.5/1/2*Python subtotal plus core proxy. They can imply months/years, which flags high information value of further timing;they are neither predictions nor strict lower/upper bounds. Qualified runtime estimates remain UNRESOLVED rather than presenting a misleading precise range. Raw seconds retained for reproducibility;human durations rounded. Separate core-only rows and walltime/t*/physical-second metrics expose assumptions. Conditional Co0.125 remains unauthorized regardless of estimate.

**Conditional data-shape stress scenarios, not qualified runtime ranges:**

| Co | t_star_end | Steps_PLANNING_ONLY | Optimistic_SHAPE_ONLY | Central_SHAPE_ONLY | Conservative_SHAPE_ONLY | qualified_runtime_estimate |
| --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.5 | 50016 | ~3.4e+02 days | ~1.9 years | ~3.8 years | UNRESOLVED |
| 0.5 | 1.0 | 100031 | ~1.9 years | ~3.8 years | ~7.6 years | UNRESOLVED |
| 0.5 | 2.0 | 200061 | ~3.8 years | ~7.6 years | ~15 years | UNRESOLVED |
| 0.25 | 0.5 | 100031 | ~1.9 years | ~3.8 years | ~7.6 years | UNRESOLVED |
| 0.25 | 1.0 | 200061 | ~3.8 years | ~7.6 years | ~15 years | UNRESOLVED |
| 0.25 | 2.0 | 400122 | ~7.6 years | ~15 years | ~30 years | UNRESOLVED |
| 0.125 | 0.5 | 200061 | ~3.8 years | ~7.6 years | ~15 years | UNRESOLVED |
| 0.125 | 1.0 | 400122 | ~7.6 years | ~15 years | ~30 years | UNRESOLVED |
| 0.125 | 2.0 | 800244 | ~15 years | ~30 years | ~61 years | UNRESOLVED |

## 12. Step-count/cost sensitivity

Steps vary0.5–1.5 and per-step cost0.5–1.5 independently;total scales by product (0.75x0.75=0.5625,1.25x1.25=1.5625,1.5x1.5=2.25). These are planning sensitivities, not physical uncertainty distributions. Startup/developed linear iterations and adaptive deltaT can differ. Arrival evaluations are nonlinear in retained node count;linear whole-step model omits their spikes.

| Step factor | Cost factor | Total runtime factor |
| --- | --- | --- |
| 0.5 | 0.5 | 0.25 |
| 0.5 | 0.75 | 0.375 |
| 0.5 | 1.0 | 0.5 |
| 0.5 | 1.25 | 0.625 |
| 0.5 | 1.5 | 0.75 |
| 0.75 | 0.5 | 0.375 |
| 0.75 | 0.75 | 0.5625 |
| 0.75 | 1.0 | 0.75 |
| 0.75 | 1.25 | 0.9375 |
| 0.75 | 1.5 | 1.125 |
| 1.0 | 0.5 | 0.5 |
| 1.0 | 0.75 | 0.75 |
| 1.0 | 1.0 | 1.0 |
| 1.0 | 1.25 | 1.25 |
| 1.0 | 1.5 | 1.5 |
| 1.25 | 0.5 | 0.625 |
| 1.25 | 0.75 | 0.9375 |
| 1.25 | 1.0 | 1.25 |
| 1.25 | 1.25 | 1.5625 |
| 1.25 | 1.5 | 1.875 |
| 1.5 | 0.5 | 0.75 |
| 1.5 | 0.75 | 1.125 |
| 1.5 | 1.0 | 1.5 |
| 1.5 | 1.25 | 1.875 |
| 1.5 | 1.5 | 2.25 |

## 13. Memory model

Numeric lower storage, retained-byte ceilings, Python estimates and actual high-water RSS are distinguished below. Host memory headroom exists but process8GiB AS fit remains unproven. Explicit retained buffers ring512MiB+bundle512MiB+receipt64MiB+primary16MiB+stage32MiB+field16MiB exceed old1.19GB accounting once added copies/outer history are included. Bundle joining can transiently add512MiB–1GiB;receipt concatenation adds128MiB;C++/Python objects,old histories/term packets,matrix replay rows and canonical strings are extra. Full9GiB audit is streamed disk spool, not full-RSS allocation. Synchronization list resets after each yield;last5 and ring are bounded,arrival only retains bracketing0.3history. Primitive process high-water~6e+02MiB is synthetic data-shape observation,not production peak. Overall peak UNRESOLVED;no tiny-cell RSS scaling.

| Component | Scaling | Estimated bytes | Evidence |
| --- | --- | --- | --- |
| current registered scalar/vector fields | O(Ncells) | 2252800 | 8 scalar + U3 components in meshState; lower numerical storage only; excludes other OpenFOAM objects |
| surface phi and address arrays | O(Nfaces) | 1228800 | actual boundary mesh; excludes patch metadata and C++ allocation |
| rho/e/K oldTime numeric histories | O(Ncells x 2 levels) | 1228800 | meshState exports existing histories; actual histories can differ by field |
| one sparse scalar matrix basic arrays | O(Ncells+NinternalFaces) | 1630720 | diag/source/upper/lower + int32 addresses; excludes psi/BC/action/replay copies |
| last5 outer primitive states | O(5 x Ncells) | 36864000 | Live retains U3+T+p_rgh+rho+rhoThermo; Python float/list planning estimate, no tiny-RSS scaling |
| recent16 stage packed ring | bounded 16 x stage cap | 536870912 | Writer default ring1GiB but max16 x 32MiB stage enforces effective512MiB |
| selected bundle retained | bounded | 536870912 | BUNDLE_CAP; publication joins/prefix can temporarily allocate additional512MiB–1GiB |
| receipt chunk retained | bounded | 67108864 | chunk quota; join/prefix can add128MiB transient allocations |
| primary scalar chunk retained | bounded | 16777216 | Live rows_bytes quota; joining duplicates current chunk |
| transient stage encoder buffer | bounded packed bytes only | 33554432 | STAGE_CAP is after encoding; constructing Python/C++ JSON objects is additional |
| field snapshot/final packet buffer | bounded packed bytes only | 16777216 | FIELD_CAP; pre-encoded field copies and final/current simultaneous copies additional |
| JSON IPC and Python evaluator state | O(fields/matrices x Ncells/Nfaces) | UNRESOLVED | Python lists/floats, C++ Json maps, term packets, canonical strings and deep snapshots coexist; not bounded by packed-byte cap alone |
| arrival history Co0.25 planning | O(Nsteps in last0.3 window) | 17286048 | 9 deques; source trims old nodes, scalar history remains on disk; adaptive dt can increase count |
| native/runtime baseline + temporary assembly/thermo | O(Ncells/Nfaces) + O(1) | UNRESOLVED | native process peak AS/RSS on target grid not measured |
| target-shape primitive process high-water RSS | measured synthetic process only | 631939072 | 617128KiB includes imports, synthetic lists/matrix and sequential serialization allocations; not production peak |
| native/backend AS limits | per process virtual ceiling | 8589934592 | 8GiB each; limits are failure guard, not fit proof; combined16GiB without swap assumption |
| minimum host available memory | host preflight | 25769803776 | Current MemAvailable 63353577472 B; passes host check but not process AS qualification |

## 14. I/O model

Unchanged64-step receipt/primary chunks,4MiB log rotation,max7 full9GiB audits,56x512MiB bundles,505x16MiB fields and provenance caps. Full Co0.5 permanent178636906968B/Co0.25 250017072048B unchanged. Raw data transmitted and reduced each stage is not total retained I/O;historical9.70GB numerical payload/step was a rough schema projection,not disk usage or measured socket traffic. Three16MiB write+file/directory-fsync samples median0.0142s,~1.2e+03MB/s effective cached small-write rate. Sustained9GiB audit/background contention and hash-read latency UNRESOLVED. Tables include cap-based average GB/hour,MB/s,files/hour,fsync/hour for each shape scenario. Three durable actions/publication and extra audit spool fsync counted as lower bound;immutable/trigger/seal/validation tail work extra. Early-arrival tables keep full fixed caps intentionally conservative. No throughput/storage policy change.

| Evidence class | Frequency | Bytes/write planning cap | Total bytes Co0p5 maximum cap | Estimated I/O burden |
| --- | --- | --- | --- | --- |
| compact receipts | 64 physical steps | 14446080 | 45157769688 | 3 fsync/publication + metadata hash;64MiB chunk cap |
| primary rows | 64 steps | 4194304 | 13111197696 | max64KiB/row;actual rows smaller;3 fsync/publication |
| complete solver log | 4MiB rotation | 4194304 | 13111197696 | ordered full logs;3 fsync/publication;source-derived budget64KiB/step |
| selected full raw audit | <=7/series | 9663676416 | 67645734912 | spool plus streaming hash; additional spool fsync;9GiB storage burst, not9GiB resident allocation |
| selected bundle | <=56/series | 536870912 | 30064771072 | join retained records and atomic publish;temporary memory spike distinct from spool |
| R2 field snapshots | <=505/series | 16777216 | 8472494080 | inherited initial/startup/development/arrival/final schedule;per-write field buffer cap |
| fixed provenance/static | once/series | 1073741824 | 1073741824 | static blobs and retained inputs/source/manifests;not bulk throughput proof |

| Co | t_star_end | scenario | GB_per_hour | MB_per_second | files_per_hour | fsync_per_hour_lower_bound |
| --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.5 | optimistic | 0.015111063308057223 | 0.00419751758557145 | 0.3519817478209786 | 1.0567907727130206 |
| 0.5 | 0.5 | central | 0.007550716515193715 | 0.002097421254220476 | 0.17587871496121116 | 0.5280586400808636 |
| 0.5 | 0.5 | conservative | 0.003768557651468676 | 0.00104682156985241 | 0.08778095107448833 | 0.26355372029879837 |
| 0.5 | 1.0 | optimistic | 0.008633362884556316 | 0.002398156356821199 | 0.31749940738521004 | 0.9529209910070084 |
| 0.5 | 1.0 | central | 0.0043139304220452535 | 0.0011983140061236817 | 0.15864853253771075 | 0.47615684732356856 |
| 0.5 | 1.0 | conservative | 0.0021530798391369683 | 0.0005980777330936023 | 0.07918137834816175 | 0.23764956963616057 |
| 0.5 | 2.0 | optimistic | 0.005394464104865909 | 0.0014984622513516414 | 0.30034857240675067 | 0.9012571027025411 |
| 0.5 | 2.0 | central | 0.0026955131069772145 | 0.000748753640827004 | 0.15007858016035783 | 0.45034136586425494 |
| 0.5 | 2.0 | conservative | 0.0013453288205818009 | 0.00037370245016161134 | 0.0749041207475873 | 0.2247650798021057 |
| 0.25 | 0.5 | optimistic | 0.008633362884556316 | 0.002398156356821199 | 0.31749940738521004 | 0.9529209910070084 |
| 0.25 | 0.5 | central | 0.0043139304220452535 | 0.0011983140061236817 | 0.15864853253771075 | 0.47615684732356856 |
| 0.25 | 0.5 | conservative | 0.0021530798391369683 | 0.0005980777330936023 | 0.07918137834816175 | 0.23764956963616057 |
| 0.25 | 1.0 | optimistic | 0.005394464104865909 | 0.0014984622513516414 | 0.30034857240675067 | 0.9012571027025411 |
| 0.25 | 1.0 | central | 0.0026955131069772145 | 0.000748753640827004 | 0.15007858016035783 | 0.45034136586425494 |
| 0.25 | 1.0 | conservative | 0.0013453288205818009 | 0.00037370245016161134 | 0.0749041207475873 | 0.2247650798021057 |
| 0.25 | 2.0 | optimistic | 0.0037749985253836987 | 0.001048610701495472 | 0.29177236141102203 | 0.8754227769742107 |
| 0.25 | 2.0 | central | 0.0018862963597835176 | 0.0005239712110509771 | 0.14579320747128266 | 0.4374324351054387 |
| 0.25 | 2.0 | conservative | 0.0009414492737603873 | 0.00026151368715566316 | 0.07276529405421159 | 0.21832224094230665 |
| 0.125 | 0.5 | optimistic | 0.005394464104865909 | 0.0014984622513516414 | 0.30034857240675067 | 0.9012571027025411 |
| 0.125 | 0.5 | central | 0.0026955131069772145 | 0.000748753640827004 | 0.15007858016035783 | 0.45034136586425494 |
| 0.125 | 0.5 | conservative | 0.0013453288205818009 | 0.00037370245016161134 | 0.0749041207475873 | 0.2247650798021057 |
| 0.125 | 1.0 | optimistic | 0.0037749985253836987 | 0.001048610701495472 | 0.29177236141102203 | 0.8754227769742107 |
| 0.125 | 1.0 | central | 0.0018862963597835176 | 0.0005239712110509771 | 0.14579320747128266 | 0.4374324351054387 |
| 0.125 | 1.0 | conservative | 0.0009414492737603873 | 0.00026151368715566316 | 0.07276529405421159 | 0.21832224094230665 |
| 0.125 | 2.0 | optimistic | 0.002965265735642593 | 0.000823684926567387 | 0.28748425591315774 | 0.8625056141100453 |
| 0.125 | 2.0 | central | 0.001481687986186669 | 0.0004115799961629636 | 0.1436505211267451 | 0.43097796972603064 |
| 0.125 | 2.0 | conservative | 0.0007395095003496806 | 0.00020541930565268904 | 0.07169588070752372 | 0.21510082151240717 |

## 15. Long-run operational risk

Single continuous process perCo;process termination invalidates primary/no resume. Core-only reference already days;shape stress scenarios can be much longer. Reboot/power/maintenance/native/backend failures and resource quotas matter;no permitted wall-clock maximum or reliability guarantee supplied. SSH disconnect itself is not identical to process termination if future supervision detaches the process;supervision is not modified here. Prior uptime is not evidence of future uninterrupted reliability.

## 16. Serial-only assessment

Current qualified evidence is serial,nProcs1. Observer has per-process sequence/state graph and synchronous single Python backend;no MPI diagnostic aggregation/hash/arrival/native proof inspected or found. PARALLEL_DIAGNOSTIC_SUPPORT=NOT_VALIDATED. Available24 logical CPUs does not multiply serial throughput. Future MPI could have high value but bottlenecks in canonical/arrival/backend may not scale;no MPI/OpenMP implementation or execution.

## 17. Bottleneck ranking

Evidence-backed candidate ranking in table. Diagnostic object/canonical/packing/replay work and U03quadratic validation are highest measurement priorities;pressure likely leads core by iteration workload. U03interpolate scans all times/values and monotonicity per sampled point;window_stats/integral calls it repeatedly,thereforeO(Nnodes²).101/201/401node medians show near4x cost per doubling.15001-node attempt was manually aborted after at least37s to keep this review bounded;not a completed timing or production bound. Planning last0.3window nodes~30k/60k/120k;quadratic projections below are LOW_CONFIDENCE stress estimates,not a timed arrival. Dominant actual full production bottleneck remains UNRESOLVED.

| Bottleneck | Severity | Evidence | Mitigation requiring contract change? | Production ranking |
| --- | --- | --- | --- | --- |
| diagnostic canonical/packet/object work | HIGH | full state every 1144 callbacks/step; target shape Python subtotal 1.2e+03s/step | Separate implementation qualification/revision; no changes made | leading candidate, not proven full-pipeline dominance |
| U03 arrival-window repeated history validation | HIGH | 101/201/401 nodes ~quadratic timings;15001 aborted;planning30k/60k/120k history nodes | Any optimization needs separate semantic-preservation qualification | candidate spike bottleneck |
| pressure solves | HIGH | 48calls/step;baseline pressure mean114–227iterations/call, U/e means~1–3 | No fixed24/linear changes here; future MPI/U01 studies only | likely core-solver leader; per-component timing absent |
| momentum/energy/density/thermo/assembly | UNKNOWN | 24U+24e+49rho;no isolated real cost measurements | Bounded timing qualification first | UNRESOLVED |
| JSON IPC | HIGH | synchronous ACK after evaluator/retention;~7.4MB shape packet;socket-only transfer much smaller than canonical/packing | Transport revision would need separate review | serialization/backend work exceeds bare socket in shape test |
| memory | UNKNOWN | bounded packed rings/bundles but pre-encoding objects and selected spikes unmeasured | Target-size resource qualification first | UNRESOLVED |
| I/O throughput | UNKNOWN | 9GiB audit /512MiB bundle /16MiB field caps;only3x16MiB measured | No persistence/cadence changes;bounded burst qualification | UNRESOLVED sustained throughput |
| fsync latency | MEDIUM | 3file/directory/manifest fsync per publication;small fixture ~milliseconds | No durability changes here | small-file sample available;long-tail unresolved |
| continuous-run operational risk | HIGH | even core-only proxy primary runs days;shape stress runs years;single continuous process/no resume | Uptime/process-supervision plan;checkpoint restart would require a revision | feasibility qualification blocker |

| Co | last_0p3_window_nodes_PLANNING_ONLY | candidate_cost_shape_proxy | arrival_memory_Python_scalar_estimate_bytes | classification |
| --- | --- | --- | --- | --- |
| 0.5 | 30012 | ~1e+01 min | 8643456 | LOW_CONFIDENCE_COMPLEXITY_EXTRAPOLATION_NOT_MEASURED_TARGET |
| 0.25 | 60021 | ~6e+01 min | 17286048 | LOW_CONFIDENCE_COMPLEXITY_EXTRAPOLATION_NOT_MEASURED_TARGET |
| 0.125 | 120039 | ~3.9 h | 34571232 | LOW_CONFIDENCE_COMPLEXITY_EXTRAPOLATION_NOT_MEASURED_TARGET |

## 18. Compute feasibility

UNRESOLVED/LOW confidence. Existing real CFD component evidence plus shape-level measurements do not qualify coupled target-step cost,adaptive future counts,spikes and continuous-run practicality. Feasible would mean demonstrated unchanged full target workload,acceptable user-defined run budget and reliability;infeasible would require a hard resource contradiction or unacceptable agreed budget. Neither can be concluded from fast CPU,operation count,or arbitrary7day rule. Evidence signals HIGH risk and justifies bounded qualification preparation.

## 19. Memory feasibility

UNRESOLVED/LOW confidence. Read-only available RAM passes host preflight and target-shape primitivefits;native/backend actual concurrent AS/RSS and selected-audit/canonical peaks not measured.8GiB cap and24GiB available are guards,not proof. Marginal/feasible/infeasible labels are withheld until target workload peak is bounded.

## 20. I/O feasibility

UNRESOLVED/LOW confidence. Storage capacity remains FEASIBLE/storage-readyYES under inherited planning guard;cached16MiB local writes supply small-latency evidence only. Sustainedselected audit and durable manifest workload not qualified. Disk capacity and throughput are separate questions.

## 21. Overall resource readiness

Resource-readyNO,configuration-frozenNO,execution-authorizedNO. Scientific/technical/storage readinessYES preserved from v1.5. launcher version1.4 compatibility and future provenance/cold-start recipe binding remain separate pre-run blockers. Contract and all formal/historical status read-only;review findings do not overwrite canonical authority.

## 22. Evidence limitations

No production/pilot/short CFD,case/mesh/init,physical arrival or native160² timing. Shape fixtures omitpatch values,static geometry/actual history epoch identities and multiple per-stage payload distributions;they exercise existing primitive functions without changing algorithms. CPU frequency/cache/load not pinned;smallI/O may be cached. AS/RSS roles and caps differ. Current OFF/ON one-step driver includes setup/fingerprints andauxiliary fixtures;production percentages not inferred. One U03fixture preparation failed for missing test harness attributes and another for insufficient bracketing;corrected fixtures only are timing evidence. The large-node microbenchmark was stopped;no physicalsolver process terminated. All illustrative scenarios retain uncertainty and qualified estimates remainUNRESOLVED.

## 23. Exact next task

PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_BOUNDED_TIMING_QUALIFICATION. Define minimal production-like stage/whole-step resource measurement scope,bounds,mandatory failure criteria,source/authority compatibility and explicit authorization in that separate task. No CFD is automatically authorized. Compare serial preservation,MPI qualification,U01policy review andboundedqualification options below;do not reduce24outer or modify tolerance/cadence in this review.

| option | information_value | assessment |
| --- | --- | --- |
| A current serial/fixed24 | MEDIUM | Preserves science; insufficient target-stage/whole-step evidence; no run now |
| B future MPI diagnostic qualification | HIGH | Could accelerate core/partitioned diagnostics; no24-thread factor assumed. Serial Python backend and global identities need design/qualification |
| C U01 outer-policy review | MEDIUM | 24 exists for k21–24 certificate. Reducing outer count alone does not resolve callback serialization or quadratic arrival; separate scientific task only |
| D bounded production-like timing qualification preparation | HIGH | Next task defines hard CPU/time/disk/RSS bounds and authorization; no pilot/short CFD authorized by this review |

## Required final status

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_COMPUTE_FEASIBILITY_REVIEW = COMPLETE
DIAGNOSTIC_CONTRACT_VERSION = 1.5
DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
DIAGNOSTIC_CONTRACT_SHA256 = 06c71945289ffe419b784843f7aab2fea66c44d28c9dba46d828bbd24837e27d
HOST_CPU_MODEL = Intel(R) Xeon(R) w5-2545
HOST_PHYSICAL_CORES = 12
HOST_LOGICAL_CPUS = 24
HOST_MEM_TOTAL_BYTES = 66619408384
HOST_MEM_AVAILABLE_BYTES = 63353577472
PARALLEL_DIAGNOSTIC_SUPPORT = NOT_VALIDATED
CURRENT_EXECUTION_MODE = SERIAL
FV_SOLVES_PER_PHYSICAL_STEP = 145
SCALAR_COMPONENT_RECORDS_PER_PHYSICAL_STEP = 169
CO05_STEPS_PLANNING = 200061
CO025_STEPS_PLANNING = 400122
CO0125_STEPS_PLANNING = 800244
EXISTING_REAL_CFD_TIMING_EVIDENCE = PARTIAL
SYNTHETIC_TIMING_EXECUTED = YES
SYNTHETIC_TIMING_SCOPE = SYNTHETIC_ONLY
CORE_SOLVER_COST_ESTIMATE = ~0.8–9 s/step ROUGH_COMPONENT_COST_PROXY; production cost UNRESOLVED
DIAGNOSTIC_OVERHEAD_ESTIMATE = UNRESOLVED; four-cell ON 22s/OFF 0.37s; target-shape Python subtotal ~1e+03s/step, not production
CO05_TSTAR05_RUNTIME_ESTIMATE = UNRESOLVED
CO05_TSTAR1_RUNTIME_ESTIMATE = UNRESOLVED
CO05_TSTAR2_RUNTIME_ESTIMATE = UNRESOLVED
CO025_TSTAR05_RUNTIME_ESTIMATE = UNRESOLVED
CO025_TSTAR1_RUNTIME_ESTIMATE = UNRESOLVED
CO025_TSTAR2_RUNTIME_ESTIMATE = UNRESOLVED
CO0125_TSTAR2_RUNTIME_ESTIMATE = UNRESOLVED
COMPUTE_FEASIBILITY = UNRESOLVED
COMPUTE_CONFIDENCE = LOW
MEMORY_PEAK_ESTIMATE_BYTES = UNRESOLVED
MEMORY_FEASIBILITY = UNRESOLVED
MEMORY_CONFIDENCE = LOW
AVERAGE_IO_RATE_ESTIMATE = UNRESOLVED production; cap-based conditional GB/hour and MB/s tables provided
PEAK_IO_BURST_ESTIMATE = 9 GiB full-audit cap; 512 MiB bundle cap; 16 MiB field cap; durations UNRESOLVED
IO_FEASIBILITY = UNRESOLVED
IO_CONFIDENCE = LOW
CORE_SOLVER_COMPUTE_RISK = HIGH
DIAGNOSTIC_COMPUTE_RISK = HIGH
IPC_RISK = HIGH
MEMORY_RISK = UNKNOWN
IO_THROUGHPUT_RISK = UNKNOWN
FSYNC_LATENCY_RISK = MEDIUM
LONG_RUN_OPERATIONAL_RISK = HIGH
SERIAL_ONLY_RESOURCE_RISK = HIGH
CURRENT_FROZEN_DESIGN_PRACTICALLY_EXECUTABLE = UNRESOLVED
BOUNDED_TIMING_QUALIFICATION_REQUIRED = YES
COMPUTE_POLICY_REVISION_REQUIRED = UNRESOLVED
MPI_QUALIFICATION_INFORMATION_VALUE = HIGH
U01_OUTER_POLICY_REVIEW_INFORMATION_VALUE = MEDIUM
DIAGNOSTIC_TRANSIENT_STORAGE_READY = YES
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
COMPLETE_EXECUTION_CONFIGURATION_FROZEN = NO
EXECUTION_AUTHORIZED = NO
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = YES
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = YES
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
PRODUCTION_SOLVER_EXECUTED = NO
PILOT_CFD_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_BOUNDED_TIMING_QUALIFICATION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```

No git add/commit/push. New review artifacts remain untracked; tracked git diff --stat is empty. Referenced source/evidence hashes, raw hardware/timing data and all scenario parameters are retained in the JSON report and compute_review directory.
