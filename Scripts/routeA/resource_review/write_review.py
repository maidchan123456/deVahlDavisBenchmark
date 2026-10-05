"""Render the resource review only; no contract/evaluator changes or CFD calls."""
from pathlib import Path
import csv,json,math,hashlib
ROOT=Path(__file__).resolve().parents[3];PREP=ROOT/'results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation';DIR=PREP/'resource_review'
load=lambda p:json.loads(Path(p).read_text());write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
A=load(DIR/'resource_accounting.json');C=load(ROOT/'docs/routeA_diagnostic_transient_contract_v1.2.json');free=A['authority']['filesystem']['free_user_bytes'];orig=A['original_projection_reconstructed_bytes'];MAX='A_MAX_DURATION_SCENARIO'
P={p['policy']:p for p in A['policy_scenarios'] if p['scenario']==MAX};scratch=16*2**30
recommended=P['P1_CONSERVATIVE_REDUCED']['primary_bytes']+scratch
conditional_steps=next(s for s in A['step_solve_scenarios'] if s['scenario']==MAX)['series'][2]['planning_steps']
conditional_extra=conditional_steps*sum(P['P1_CONSERVATIVE_REDUCED']['step_byte_budget'].values())+7*A['packed_caps']['full_audit_step_bytes']+56*A['packed_caps']['selected_outer_bundle_bytes']+505*A['packed_caps']['field_snapshot_bytes']
status={'ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_FEASIBILITY_REVIEW':'COMPLETE','CURRENT_DIAGNOSTIC_CONTRACT_VERSION':'1.2','CURRENT_DIAGNOSTIC_CONTRACT_HASH_VERIFIED':'YES','CURRENT_DIAGNOSTIC_CONTRACT_SHA256':'7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd','CURRENT_FREE_STORAGE_BYTES':free,'CURRENT_FREE_STORAGE_TB':free/1e12,'CURRENT_PRIMARY_STORAGE_ESTIMATE_BYTES':int(orig),'CURRENT_PRIMARY_STORAGE_ESTIMATE_PB':orig/1e15,'CURRENT_PRIMARY_STORAGE_FEASIBLE':'NO','CURRENT_POLICY_DOMINANT_STORAGE_SOURCE':'PRESSURE_CORRECTOR_FIELD_STATE_AND_MATRIX_COPIES','FULL_FIELDS_EVERY_STEP_SCIENTIFICALLY_REQUIRED':'NO','FULL_MATRIX_EVERY_STEP_SCIENTIFICALLY_REQUIRED':'NO','EVERY_STEP_PRIMARY_SCALARS_REQUIRED':'YES','EVERY_STEP_GLOBAL_MASS_ENERGY_REQUIRED':'YES','SELECTED_RAW_MATRIX_AUDIT_SCIENTIFICALLY_SUFFICIENT':'CONDITIONAL','ONLINE_REDUCTION_WITH_SELECTED_RAW_AUDIT_DEFENSIBLE':'CONDITIONAL','RECOMMENDED_EVIDENCE_POLICY':'P1_CONSERVATIVE_REDUCED','RECOMMENDED_STORAGE_ESTIMATE_BYTES':recommended,'RECOMMENDED_STORAGE_ESTIMATE_TB':recommended/1e12,'RECOMMENDED_STORAGE_FRACTION_OF_FREE':recommended/free,'STORAGE_FEASIBILITY':'FEASIBLE','COMPUTE_FEASIBILITY':'UNRESOLVED','IO_FEASIBILITY':'UNRESOLVED','MEMORY_FEASIBILITY':'UNRESOLVED','SERIAL_ONLY_RESOURCE_RISK':'HIGH','RESOURCE_POLICY_REVISION_REQUIRED':'YES','U01_REVISION_REQUIRED':'UNRESOLVED','U02_REVISION_REQUIRED':'NO','U03_REVISION_REQUIRED':'NO','U04_REVISION_REQUIRED':'YES','EVIDENCE_CADENCE_REVISION_REQUIRED':'YES','DIAGNOSTIC_CONTRACT_V1_3_REQUIRED':'YES','DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED':'YES','DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY':'YES','DIAGNOSTIC_TRANSIENT_RESOURCE_READY':'NO','FORMAL_GATE_J_CURRENTLY_ALLOWED':'NO','FORMAL_GATE_J_EXECUTED':'NO','GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED':'NO','DOWNSTREAM_TRANSIENT_READY':'NO','PARTICLE_COUPLING_READY':'NO','SOLVER_EXECUTED':'NO','PRODUCTION_SOLVER_EXECUTED':'NO','CFD_TRANSIENT_EXECUTED':'NO','CASE_GENERATED':'NO','MESH_GENERATED':'NO','INITIALIZATION_EXECUTED':'NO','DIAGNOSTIC_CONTRACT_VERSION':'1.2','DIAGNOSTIC_CONTRACT_CHANGED':'NO','U01_CHANGED':'NO','U02_CHANGED':'NO','U03_CHANGED':'NO','U04_CHANGED':'NO','FORMAL_CRITERIA_CHANGED':'NO','HISTORICAL_STATUS_CHANGED':'NO','FORMAL_GATE_J_PASS':'NOT_EVALUATED','BENCHMARK_CORE_PASS':'NO','ROUTE_A_CHARACTERIZED':'NO','ALL_ROUTE_A_GATE_F':'FAIL','ALL_RA_NEEDS_320':'YES','PARALLEL_DIAGNOSTIC_SUPPORT':'NOT_VALIDATED','NEXT_SINGLE_TASK':'PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION','RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK':'gpt-6.1-sol / medium','USER_DECISION_REQUIRED':'YES'}
items=[]
for name in C['sampling']['required_primary_and_stage_columns']:
 if name in {'input_hash','evaluator_hash'}:tier='TIER_2_AUDIT_REQUIRED';retain='sealed configuration once plus reference/chain commitment every step';evaluate='start/loaded-code authority checks, every-step reference identity'
 else:tier='TIER_1_PRIMARY_REQUIRED';retain='every relevant native stage scalar/norm, plus every-step primary summary';evaluate='every relevant native stage/step; no evaluation thinning'
 items.append({'item':name,'tier':tier,'necessity':'SCIENTIFICALLY_REQUIRED_EVIDENCE','evaluation':evaluate,'retention':retain,'claim_supported':'Co comparison/arrival/mass-energy/synchronization/inner validity/reproducible final scalars'})
extra=[
 ('native linear solver initial/final residual,iteration count,component ID,tolerance outcome','TIER_1_PRIMARY_REQUIRED','every native solve; packed receipt+raw log','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('all24outer state/QoI transitions, floating floors, contraction/tail certificate','TIER_1_PRIMARY_REQUIRED','every outer; computed from live previous/current fields','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('local defect L1,Linf,max cell/location,cancellation signed/absolute ratios','TIER_1_PRIMARY_REQUIRED','every relevant mass/energy stage and final step','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('arrival raw primary/state scalars,three windows,range/OLS/half drift,bracketing decisions','TIER_1_PRIMARY_REQUIRED','every physical step; no interpolation/output-driven dt changes','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('stage validity,old-time value/storage epoch,BC coefficient epoch,matrix identity','TIER_1_PRIMARY_REQUIRED','validate every callback; persist bounded receipts/chain roots and all failures','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('inputs,source/instrumentation/library/binary/schema/analysis hashes and decision history','TIER_2_AUDIT_REQUIRED','once sealed + every-step references + selected audit manifests','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('raw solver log and nonfinite/evaluator/counter/quota failure event','TIER_2_AUDIT_REQUIRED','complete append log; failures never sampled or discarded','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('selected full native matrix coefficients/source/BC/psi/native action/history','TIER_2_AUDIT_REQUIRED','first3steps/full audit epochs and periodic/final/anomaly bundles','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('selected T/U/e/p/p_rgh/rho_s/rho_T/phi/K/full-field and local defect snapshots','TIER_2_AUDIT_REQUIRED','dense startup + physical-time periodic + final/anomaly','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('selected exact4097point profiles,hot/cold/local Nu profiles','TIER_2_AUDIT_REQUIRED','field snapshot times and confirmation/final windows','SCIENTIFICALLY_REQUIRED_EVIDENCE'),
 ('all matrices/allstage field arrays at every non-audit physical step','TIER_3_DEBUG_OPTIONAL','discard only after validated online reduction and committed receipts','AUDIT_CONVENIENCE_EVIDENCE'),
 ('full local defect distributions at all non-audit stages','TIER_3_DEBUG_OPTIONAL','retain norms/max location every stage, full arrays selected only','AUDIT_CONVENIENCE_EVIDENCE'),
 ('byte-identical duplicate native_state_epoch/state/root arrays','TIER_4_REDUNDANT_AFTER_VALIDATION','intern exact payload once with references; never assume different epochs equal','AUDIT_CONVENIENCE_EVIDENCE'),
 ('repeated static geometry,addressing,V,constant Cv/g/dimensions/source labels','TIER_4_REDUNDANT_AFTER_VALIDATION','seal once and validate/reference at runtime; nonconstant/mismatch stops','AUDIT_CONVENIENCE_EVIDENCE'),
 ('registered no-op after-relax coefficient duplicate and absent zero model raw arrays','TIER_4_REDUNDANT_AFTER_VALIDATION','retain equality/zero-source check every invocation; selected raw samples','AUDIT_CONVENIENCE_EVIDENCE')]
for item,tier,retention,need in extra:items.append({'item':item,'tier':tier,'necessity':need,'evaluation':'every required native operation where applicable; source hooks/equations/counts unchanged','retention':retention,'claim_supported':'audit/figures/health; complete all-step field/operator reanalysis intentionally not promised'})
with (DIR/'evidence_item_classification.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
component=[]
necessity={'A':'every-step scalars essential','B':'selected snapshots essential; every-step disk full fields optional','C':'every-outer derived norms/certificate essential; every field array optional','D':'every-pressure rho/reference validity and norms essential; raw arrays selected','E':'native action every invocation essential; raw coefficients selected audit','F':'native unrelaxed assembly evaluation every solve essential; raw selected','G':'term sums/signs/dimensions every solve essential; raw term arrays selected','H':'all-stage online fail-closed essential; compact persisted receipts','I':'integrity/provenance essential; file/chunk roots plus shared immutable references','J':'complete raw solver log essential audit'}
for b in A['breakdown']:component.append(dict(b,current_cadence='every physical step / every indicated native stage',scientific_necessity=necessity[b['category']],reduction_candidate='packed every-step receipts, exact shared-state references, selected lossless raw payload; no change applied'))
with (PREP/'DiagnosticTransient_resource_breakdown.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(component[0]));w.writeheader();w.writerows(component)
comparison=[]
for p in A['policy_scenarios']:
 row={'policy':p['policy'],'scenario':p['scenario'],'t_star':p['t_star'],'retained_bytes':p['primary_bytes'],'retained_fraction_of_free':p['fraction_of_free'],'peak_bytes_including_16GiB_scratch':p['primary_bytes']+(0 if p['policy']=='P0_CURRENT_MAXIMAL' else scratch),'field_snapshots':p['field_snapshots'],'full_raw_audit_steps':p.get('full_raw_audit_steps',p.get('raw_audit_steps')),'selected_raw_bundles':p.get('selected_raw_bundles',0),'raw_record_slots':p.get('retained_raw_record_slots',p.get('physical_stage_records')),'coverage':'all-step raw replay' if p['policy']=='P0_CURRENT_MAXIMAL' else 'every-step online checks/receipts; selected full-step and matrix replay','risk':'capacity+inode failure' if p['policy']=='P0_CURRENT_MAXIMAL' else 'conditional new online/packed/sparse-ledger qualification; no arbitrary new field-QoI reanalysis','current_implementation_usable':'YES' if p['policy']=='P0_CURRENT_MAXIMAL' else 'NO','estimated_capacity_fit':'NO' if p['policy']=='P0_CURRENT_MAXIMAL' else 'YES_PRIMARY_ONLY_CONDITIONAL'};comparison.append(row)
with (PREP/'DiagnosticTransient_evidence_policy_comparison.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(comparison[0]));w.writeheader();w.writerows(comparison)
claims=[]
for question in ['primary Co sensitivity','registered arrival decisions','global mass behavior','global energy behavior','rho synchronization','selected evaluator audit','thesis transient figures','all final scalar conclusions from retained histories']:
 claims.append({'claim':question,'P0':'YES','P1':'CONDITIONAL' if question=='selected evaluator audit' else 'PARTIAL' if question=='thesis transient figures' else 'YES','P2':'CONDITIONAL' if question=='selected evaluator audit' else 'PARTIAL' if question=='thesis transient figures' else 'YES','condition':'After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly.'})
for question in ['independent offline replay of every native assembly','arbitrary post-hoc field-based QoIs at every step','dense flow history suitable for particle forcing']:
 claims.append({'claim':question,'P0':'YES' if question!='dense flow history suitable for particle forcing' else 'PARTIAL','P1':'NO','P2':'NO','condition':'Not a primary claim of this study; particle readiness remains NO even for P0.'})
with (DIR/'claim_preservation.csv').open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=list(claims[0]));w.writeheader();w.writerows(claims)
result={'status':status,'classification':'PLANNING_ESTIMATE_ONLY','recommended_policy_applied':False,'diagnostic_v1_3_created':False,'recommended_capacity_meaning':'Planning primary2series peak includes16GiB scratch; does not establish implementation/runtime/conditional-third-series readiness.','recommended_retained_bytes':P['P1_CONSERVATIVE_REDUCED']['primary_bytes'],'recommended_scratch_bytes':scratch,'recommended_peak_bytes':recommended,'conditional_Co0125_additional_bytes':conditional_extra,'conditional_all_three_peak_bytes':recommended+conditional_extra,'budget_proposals':{'retained_ceiling_50_percent_bytes':.5*free,'total_peak_candidate_55_percent_bytes':.55*free,'70_percent_comparison_bytes':.7*free,'policy_adopted':False},'risk_grades':{'STORAGE_CURRENT':'CRITICAL','COMPUTE':'HIGH_UNRESOLVED','IO':'HIGH_UNRESOLVED','MEMORY':'MEDIUM_UNRESOLVED; full-step JSON rolling buffer infeasible'},'evidence_classification':items,'claim_preservation':claims,'resource_accounting':A,'scientific_necessity_decision':'All-step online evaluation/validity/scalars indispensable; all-step permanent raw matrix/full-field retention unnecessary for registered primary claims, conditional on qualified online reduction plus selected raw audit.','requalification_required':['Online all-stage dimensions/epoch/nonfinite/matrix/term/replay-health/floor checks that currently occur in offline replay must run before discard.','Lossless typed encoder/decoder, partial selected-matrix replay honestly distinct from complete-step replay, receipt-chain/manifest integrity and crash/quota semantics.','Exact registered4097point extrema and volume Nu after postSolve, every-outer certificate/state statistics, all-step scalar histories and arrival/statistical reanalysis.','Non-invasiveness,repeatability,failure propagation and selected raw replay for new retention implementation.'],'no_physics_or_numerical_revision_proposed':True,'U04_revision_scope':'Resource implementation/exporter/online-validation/sparse-audit protocol needs new qualification; frozen equations,hooks,signs,epochs and existing U04 evidence remain unchanged.','U01_revision_scope':'UNRESOLVED necessity due unknown compute cost; no evidence justifies changing24outer or solver settings now.','additional_work_before_RUN':['Prepare diagnostic resource v1.3 policy and validate resource-only implementation without changingU01-U03 definitions.','Resolve serial compute/I/O/target-memory feasibility with an explicit bounded planning/validation design, not an unregistered pilot.','Plan conditionalCo0.125 capacity; primary-only395GB estimate does not cover it.'],'forbidden_actions_executed':[]}
write(PREP/'DiagnosticTransient_resource_feasibility_review.json',result)
fmt=lambda x:f'{x/1e9:,.3f} GB' if abs(x)<1e12 else f'{x/1e12:,.3f} TB' if abs(x)<1e15 else f'{x/1e15:,.4f} PB'
table=lambda header,rows:'| '+' | '.join(header)+' |\n|'+ '|'.join(['---']*len(header))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
md='''# DiagnosticTransient resource feasibility review

## 1. Executive summary

Review COMPLETE。契約v1.2/U01–U04/formal v1.7は変更せず、solver・synthetic solver driver・case/mesh生成・初期化は一切実行していません。

登録primary questionは固定160²でCo変更がQoI trajectory/final valuesとmass/energy behaviorに及ぼす差です。必要なのは全stepの正確なonline評価・scalar/norm/validity evidenceと選択されたraw auditであり、全matrix・全field・全stageの永久保存ではありません。この削減は新たなonline/replay/retention実装の再検証を条件とします。

'''
md+=f"P0の元projection **{int(orig):,} bytes = {orig/1e15:.6f} PB** をliteral再現。現free **{free:,} bytes = {free/1e12:.6f} TB** の約{orig/free:,.0f}倍です。補正numeric projectionは{A['corrected_primary_numeric_equivalent_bytes']/1e15:.6f} PBで、JSON実容量ではありません。推奨は未採用のP1候補：永久retain {fmt(P['P1_CONSERVATIVE_REDUCED']['primary_bytes'])}、scratch込みpeak {fmt(recommended)}（freeの{recommended/free:.2%}）。Storage planningは条件付きで現実化できますが、compute/I/O/memory実測は未解決、resource-readyはNOです。\n\n"
md+='''## 2. Authority/provenance

'''+f"Known HEAD4986b1a4…の後続HEAD `{A['authority']['actual_HEAD']}` を確認。後続は既存結果のvisualization commitであり、診断SHA `{status['CURRENT_DIAGNOSTIC_CONTRACT_SHA256']}` とformalSHA `{A['authority']['contract_hashes']['docs/routeA_execution_contract_v1.7.json']}` は指定値に一致。git tracked開始差分なし。全instrumentation/codeと契約群45ファイルの開始/終了hash一致を確認しました。既存input 1,234ファイル（healthy U04 streamの1,152 payloadを含む）のhashも照合済み。日付はAsia/Tokyo、記録時刻 `{A['authority']['client_timestamp']}`。\n\n"
md+='''`resource_review/authority_and_host.json` にdf-h/df-B1/df-i/lscpu/MemAvailable/cgroup/CPU affinityを保存。既存steady logのHostはmirai-Precision-5860-Tower、nProcs=1。最終照合の詳細は`resource_review/verification.json`、入力hashは`verified_input_sha256.json`、新規成果物hashは`artifact_sha256.json`に記録。終了時git tracked/index差分なし、HEAD不変。終了時freeは`verification.json`/`end_df.txt`に別記し、本文のfreeは上記時刻のaccounting snapshotを使用。現在ホストはXeon w5-2545、12cores/24logical CPUs、affinity24。これを将来jobの専用割当・MPI速度保証とは扱いません。

## 3. Current resource envelope

'''+f"FS available inodes={A['authority']['filesystem']['free_inodes']:,}、total={A['authority']['filesystem']['total_inodes']:,}。現在inode空きは多いものの、P0のphysical record filesだけで{A['synthetic_IO']['physical_record_publications_primary_max_duration']:,}個が必要となり、容量以前にinode envelopeも不足。記録ごと3fsyncで約{A['synthetic_IO']['record_fsync_calls_primary_max_duration']:,}回。\n\n"
md+=f"元baseline field numeric componentのみでも{fmt(next(b['legacy_primary_bytes'] for b in A['breakdown'] if b['category']=='B'))}。実existing complete directory scaleでevery-stepをwhat-if計算すると約{max(v['du_sb_bytes'] for v in A['actual_fields'])*600183/1e12:.3f}TBです。既存ASCIIと将来binary/nonuniform/historyを同一視せず、actual future sizeの測定とは扱いません。\n\n"
md+='''## 4. Step-count planning scenarios

Constant prospective hを使うceil(710*t*/h)。startup ramp/adaptive variation/actual arrivalを予測しません。max-durationは登録maximum2を計画用に使用し、native endTimeの微小shortfallやovershoot制御を変更しません。minimum0.5は3window確認を既に包含し、さらに0.3を加算しません。

'''+table(['Scenario','t* / seconds','Co0.5 steps','Co0.25 steps','primary sum','conditionalCo0.125'],[[s['scenario'],f"{s['t_star']} / {s['physical_time_s']}",s['series'][0]['planning_steps'],s['series'][1]['planning_steps'],s['primary_planning_steps'],s['series'][2]['planning_steps']] for s in A['step_solve_scenarios']])+'\n'
md+='''## 5. Storage accounting model

S_total=N_step*(S_scalar+S_field+24*S_outer+48*S_pressure+S_mass_matrices+S_energy_matrices+S_terms+S_ledger+S_integrity+S_log)+S_selected_audits+S_fixed+S_scratch。

互いにexclusiveなA–J分類で元numeric baselineを厳密に分解。records/stepはcategoryが寄与するrecord数で、同じstage recordが複数categoryを含むため列のcountは加算しません。mean bytes/recordは該当numeric subtotal/count。StageLedger/string SHA/keys/manifests/logsのASCIIを元baselineは計上しないため、A/I/Jが0でも科学的不要という意味ではありません。

'''+table(['Component','numeric mean bytes/record','records/step','bytes/step','primary total','fraction','necessity/reduction'],[[b['category']+' '+b['name'],f"{b['legacy_numeric_bytes_per_record_mean']:.0f}",b['records_per_step'],f"{b['legacy_numeric_bytes_per_step']:.0f}",fmt(b['legacy_primary_bytes']),f"{b['legacy_fraction']:.4%}",necessity[b['category']]] for b in A['breakdown']])+'\n'
md+=f"2cell→25600cellはcells/diag/source/psi/oldTime/current actionsにO(Ncells)、upper/lower/owner/neighbour/phi/weightsにO(Nfaces)、active boundaryに640faces、scalar metadataはO(1)。旧estimatorでCv cell arrayとlinear_weights arrayが未scaleでした。review側のshape補正はnumeric step {A['corrected_per_step_numeric_bytes']/1e9:.6f}GB、primary {A['corrected_primary_numeric_equivalent_bytes']/1e15:.6f}PB。旧コード/記録は不変です。物理patch数・metadata/strings・ASCII digits・compression・uniform/nonuniformは別の不確かさです。\n\n"
md+='''Matrix payloadはpsi/history/addressing/volumesも含み、pure coefficient-only量ではありません。Pressure category Dはpressure-phase field copiesとreference matricesを含み、mass total matricesはE、energy totalはF、term submatricesはGへexclusive分類。原projectionはFloat64-equivalentで、現在の17-digit JSON測定値ではありません。

## 6. Dominant storage contributors

'''+table(['rank','category','total','fraction'],[[i+1,b['category']+' '+b['name'],fmt(b['legacy_primary_bytes']),f"{b['legacy_fraction']:.3%}"] for i,b in enumerate(A['ranked_contributors'][:5])])+'\n'+f"Pareto top1={A['pareto']['1']:.3%}、top3={A['pareto']['3']:.3%}、top5={A['pareto']['5']:.3%}。state copies C+Dで{sum(b['legacy_fraction'] for b in A['breakdown'] if b['category'] in ['C','D']):.3%}。610recordsでpayload.state/rootとnative_state_epochが完全一致し、その二重copyのnumeric scaleだけで{A['exact_duplicate_state_blocks']['legacy_bytes_per_step']/1e9:.3f}GB/step。geometry/Cv/g等のimmutable blobと厳密同一payloadのreference化はlossless。異なるstage/epochの同一性を推測してdedupしません。\n\n"
md+='''## 7. Compute solve-count estimate

Native sourceはmomentumPredictor=yesで各outerにvector U solve、各outer e solve、2pressure solves、first-outer density predictor1+各pressure後density48=49。したがって24U+24e+48p+49rho=145fv solve calls/step。2D Ux/Uy componentとしては48U+24e+48p+49rho=169scalar calls。rho diagonal direct solveはPCGの反復1回と同コストではありません。CFDでは初回history fallback/conditioning/iterationsが異なります。

'''+table(['series atmax','U vector','Ux/Uy components','e','p','rho diagonal','fv total','scalar2D total'],[[v['Co']]+[v['solve_counts'][k] for k in ['U_vector_calls','U_scalar_component_calls_2D','e_calls','p_calls','rho_diagonal_calls','all_native_fv_solve_calls','scalar_component_total_2D']] for v in next(s for s in A['step_solve_scenarios'] if s['scenario']==MAX)['series']])+'\n'
md+='''既存3000iteration segmentsのClockTimeは384/307/212s（0.128/0.1023/0.0707s perSIMPLE iteration）。writeInterval100・ASCII16・tolerance/steady conditioningの異なる実行です。24倍what-ifは最大primary約11.78–21.34days、earliest約2.95–5.34daysで、すべてROUGH_PLANNING_SCALE_ONLY。transient実測runtimeではありません。完全stepを仮に0.1/1/10sとすると最大primary0.695/6.947/69.466days。CPU時間の保証や24outer変更根拠には使用しません。computeのmaterial riskはHIGH、feasibilityはUNRESOLVEDです。

## 8. I/O assessment

'''+f"保存済みsynthetic OFF={A['synthetic_IO']['off_s']:.9f}s、ON={A['synthetic_IO']['on_s']:.9f}s、ratio={A['synthetic_IO']['ratio']:.2f}。1152records={A['synthetic_IO']['raw_bytes']:,}bytes、mean={A['synthetic_IO']['mean_bytes_per_record']:.1f}bytes/record。1152にはstartup4/auxiliary7が含まれ、physical1141。bytes/stage/outerはstage_record_accounting.csv/resource_accounting.jsonに保存。実CFD overheadへ外挿しません。\n\n"
md+='''現在sourceではpayload serialize/hash→exclusive temp/fsync→hardlink atomic publish/unlink→directoryfsync→manifest append/fsync。FSYNC3/recordに加え、deep copies、旧history copying、17digitostringstream、JSON value tree、payload/file hashes、repeated fields/matrix arrays、native full fields writeが候補cost。既存profilingがないため寄与率は不明です。

候補はmetadata JSON+Float64/Int32 packed blobs、geometry/coeff/source/psi epochsをshared immutable reference化し、every-step結果/outer-pressure receiptsをappend-only chunks（例64steps）へまとめる。per-array hashをなくす場合でもdecoded matrix/field identitiesとchunk file SHA/Merkle/root manifestが対応し、logical integrity checksは維持。packed byte order/type/shape/dimensions/signed-zero/versionを明示します。lossy/precision truncationは禁止。

Fsync alternatives: perrecordは最強durabilityだがprimary約20.5億回。perphysical-stepは少なくとも約120万data+commit sync。64step chunksは概算約1.9万data+commit sync（audit追加を除く）。後者crash時は最後のcomplete hashed chunkまでがaudit evidence、未commit tailはinvalid。U03のsingle continuous primaryは中断で全attempt invalid、prefixからresume/受入れはしません。v1.2 current formatのfsyncだけ勝手に省くことは不可。

Compression sample（in-memory read-only、compressed filesは生成しない）：

'''+table(['existing sample','input','gzip6 fraction','zstd3 fraction','interpretation'],[[v['sample'],fmt(v['input_bytes']),f"{v['gzip_fraction']:.4%}",f"{v.get('zstd_fraction',0):.4%}",'sample-only; no production guarantee'] for v in A['compression_samples']])+'\n'
md+=f"元P0をfree内に納めるcompression fractionは{free/orig:.8f}以下、50%budgetなら{.5*free/orig:.8f}以下が必要。syntheticの極端な反復/zero/history/metadata圧縮率を25600cellへ保証できません。Native binary/gzip/zstd/chunkingは有用ですが、容量設計はcompression benefit0で計算。JSON ASCIIはnumeric8byteに対し多くの値で20–25charsになり得るため元Float64 projectionを実JSON容量と扱いません。\n\n"
md+='''## 9. Memory assessment

'''+f"Measured host RAM={A['memory']['measured_host_total_bytes']/2**30:.2f}GiB、available={A['memory']['measured_host_available_bytes']/2**30:.2f}GiB、synthetic peakRSS={A['memory']['synthetic_peak_RSS_KiB']}KiB（libraries/meshbaselineを含みwhole-processをcell比でscaleしない）。largest corrected record={A['memory']['largest_corrected_record_numeric_bytes']/1e6:.3f}MB、fullstep={A['memory']['full_step_numeric_bytes']/1e9:.3f}GB、selected59records={A['memory']['selected_bundle_numeric_bytes']/1e9:.3f}GB。\n\n"
md+='''Fullstep packed ring1/2/4stepsは10.65/21.30/42.59GB。現在Json objectはscalarごとstring/vector/mapも持つため、ABI estimate16–32xでは1step170–341GBとなり、このホストのfullstep JSON ringは非現実的。正確なtarget RSS実測ではありません。

候補はpacked current final-outer+initial-density bundle1GiB capと直近16stages（shape estimate約282MB）、合計約1.36GBのbounded buffer。全resident RSS8GiBを提案上限とし、payload/live matrices/decoder/hash queuesを含む実装計測が必要。過去全outer/fullstep matrixの取得は保証しません。Ringは過去stageを後から再assembleしない方式です。Scratch16GiB capはselected audit/chunk/partialのみ；毎stepのfullraw10.65GBをscratchへ書いてから消す案は累積PB I/Oを残すため推奨しません。

## 10. Evidence classification

`evidence_item_classification.csv` は登録required columns全項目と追加solver/certificate/raw/field/integrity itemsをTier分類。

- TIER_1_PRIMARY_REQUIRED: every-step primary time/t*/dt/control+achievedCo/QoI/positions/arrival history、各native stageのmass/energy signed terms/norms/cancellation/floors/rho sync/reference defect、各solve performance、各outer certificate、全runtime validity/failures。
- TIER_2_AUDIT_REQUIRED: sealed inputs/code/libs/analysis hashes、complete solver log、selected full native matrices/fields/profiles/local defect arrays、manifests/decisions。
- TIER_3_DEBUG_OPTIONAL: non-audit stepでの全raw matrices、全stage arrays、全local distributions永久保存。
- TIER_4_REDUNDANT_AFTER_VALIDATION: exact duplicate states、repeated static geometry/Cv/g、verified no-op coefficient duplicates、absent-model zero raw vectors。checksとidentitiesは毎回残す。

SCIENCE REQUIREDとAUDIT CONVENIENCEを分離。Scalar localL1/Linfは安価でU01/U03/diagnosticに有用なので評価も保存も間引きません。

## 11. Full-field necessity

登録primaryだけにはfullfield every-step diskは不要。Nu_bar_cavityは1+volumeMean((UxL/alpha0)*theta)、既存analyze_case.paper_nusseltのcavity式。壁Nu平均へ定義変更しない。Umax/Wmaxは2本のbracketing cell-centre lineをexactcentrelineへ線形補間し4097points/no-slip endpoints/positive maxima/positionsを抽出する既存式で、必要fieldsはmemory内に存在します。既存257-point cellPointFace monitorは登録4097 methodの代用にしません。Online portの同値性とtiming/field orderは将来qualification要件。

F1 every-step:原field numericだけ1.23TB、existingcompleteASCII scale約3.43TB。F2 fixed Δt*=.01/.005なら最大201/401snapshots per series（actual crossing timeを保存、dtを変更しない）。F3 dense startup .001→以降.005/.02はflow立上りを保つ。F4 startup+periodic+confirmation/final+anomalyは推奨。F5 checkpoint+analysisはpossibleだがU03resume許可ではなく、圧倒的に疎いfieldsはfield-history後解析/粒子forcing用途を失う。

'''+table(['existing accepted160² directory','du -sb','core U/T/p/p_rgh/rho/phi','format'],[[v['time_directory'],f"{v['du_sb_bytes']:,}",f"{v['base_U_T_p_p_rgh_rho_phi_bytes']:,}",v['format']] for v in A['actual_fields']])+'\n'
md+='''未来binary sizeは未実測。snapshot budget16MiBはlargest existingcompleteASCII5.71MBの約2.94倍にe/rho_T/K/history/metadataを含めたplanning cap。超過時はresource STOP/reviewでありfieldやoldTimeを黙って切り捨てません。

## 12. Matrix-payload necessity

M1 every-step全coeff永久保存はcomplete independent replayを可能にするが、primary claimsには過剰。M2 fixed physical-time auditは一定drift検出/一部offline replay。M3 startup+periodic+arrival/anomalyは重要局面を保つ。M4 every-step hash/norm/validity+selected fullpayloadは推奨組合せ。

全matrixを保存しなくても全invocationのnative mass/energy evaluationとstage/epochチェックは必要です。U04のsynthetic PASSは個別production数値誤差/field運動の証明ではなく、selected production auditsが必要。Current replayはfullstreamを前提とするためfileを削るだけではEVALUATOR_FAILUREです。新しいselected-matrix replay modeはfull-step replayと明示的に区別し、raw欠落を補完したと主張しません。

## 13. Online reduction validity

Trust chainはverified U04 source/hook/math + sealed input/loadedbinary/library/encoder hashes + runTimeModifiable=false + every-stage online dimensions/oldTime/BC/matrix/finite/term/native-action checks + every-step/outer/pressure durable receipts + selected actual raw replay + allfailure eventsです。現在offline-onlyのsemantic checksをdiscard前にonlineで行う移行が必要。単にrawを捨てて後からscalarを最終fieldで推測する案ではありません。

全stepのindependent raw再assemble/replayは失われますが、saved complete scalar historiesからCo trajectories、arrival windows、final time-weighted mean、mass/energy behavior、rho jumps、inner certificate/validityは再解析可能。Input/source/analysis/decisions/selectedfields/matrices/logsで検証します。任意の新しいpost-hoc field QoIやdense particle historyは保証しません。

## 14. Candidate evidence policies

P0=current v1.2、P1/P2=提案のみ。Numerical settings/step law/arrival/equations/hooksを変更しません。Evaluation cadenceとretention cadenceを分離します。

**P1 conservative**: primary scalar8KiB/step、outer receipts24×1KiB、pressure receipts48×512B、ledger4KiB、manifest512B、full raw solverlog64KiB/stepをplanning caps。Fullstep raw first3stepsとscheduled t*=.5,1,1.5,1.99（max7/series、12GiB/audit）。Finalouter+initial-density bundle59records at Δt*=.05（max40/series）+final/anomaly reserve16/series（1GiB/bundle）。Fields t*∈[0,.05]はΔ*=.001、その後Δ*=.005、final/anomaly64reserve（max505/series、16MiB/snapshot）。Dense current .005 fieldsで幅.1windowに約20snapshots；判定自体はevery-step scalarsで行います。

**P2 aggressive**: scalar4KiB、outer512B、pressure256B、ledger2KiB、manifest256B、same complete log64KiB。Fullstep first1step + scheduled .5,1.99（max3/series）；bundles Δ*=.1 +8reserve（max28/series）；fields startup[0,.02] Δ*=.001、以降.02 +32reserve（max152/series）。重要なplume細部/非定常local distributionの図示/audit密度が減るためP1を優先。

頻度の根拠: startup history/BC/最初のcopyをfirst3full stepsで追う；Δ*=.05はarrival幅.1ごと2audit、immutable source/codeのdrift-riskとbudgetを両立；Δ*=.005はphysical evolutionを可視化しconfirmation3windowに十分な図示点；periodic fullstep .5/1/1.5はminimum/intermediate/max-horizonに沿ったall24outer検査、1.99はnative終端shortfallを踏まえた終盤coverage。保証されたoptimal samplingではなくv1.3で審査・登録すべき工学候補。

Future scheduleはcontroller後のactual new timeで事前判定し、native dtを出力時刻に合わせて変更しません。Final/arrival/anomalyはring内のcurrent lastouter/recentstagesをflushできる範囲に限定。過去全step matrixを復元できるとは主張しない。Arrival3windowの過去fieldsは全期間.005periodicで既に確保し、判定後に過去をdenseだったことにしません。Quota超過はSTOP_RESOURCE、silent pruneは禁止。Finite achievedCo overshootはU02どおりrecord-only、追加numerical fail thresholdにしません。

P3 pilot+productionはno recommendation now。pilot costsを減算しない；将来CFD pilotを必要とするなら明示authorization/新taskが必要。今回は実行ゼロ。

## 15. Storage estimates by policy

Lossless packed uncompressed、compression利得0。12GiB fullaudit capはcorrectednumeric10.65GBに約21%margin、1GiB bundlecapは0.555GBに約94%margin。O(1)headers/metadata/patch differencesの余地はcap内、actual target-case sizeを保証しません。Future quota/preflightが必要です。

'''+table(['policy/scenario','retained storage','fraction free','full raw audits','selected bundles','fullfields','risk/feasibility'],[[v['policy']+'/'+v['scenario'],fmt(v['primary_bytes']),f"{v['fraction_of_free']:.2%}",v.get('full_raw_audit_steps',v.get('raw_audit_steps')),v.get('selected_raw_bundles',0),v['field_snapshots'],'NO as-is' if v['policy']=='P0_CURRENT_MAXIMAL' else 'capacity fits; unimplemented/conditional'] for v in A['policy_scenarios']])+'\n'
md+='''At maximum P1 retained allocation:

'''+table(['component','primary bytes'],[[k,fmt(v)] for k,v in P['P1_CONSERVATIVE_REDUCED']['parts'].items()])+'\n'
md+=f"P1 max全raw step coverage=14/600183={14/600183:.6%}、selected bundle112、raw record slots={P['P1_CONSERVATIVE_REDUCED']['retained_raw_record_slots']:,}。すべての684,808,803stage eventsをonlineでcheckしながら、raw retained coverageは限定されることを明示。P2 fullstep6、bundle56、field304。\n\n"
md+=f"Current free {fmt(free)}の50% retention ceiling候補={fmt(.5*free)}、70%比較={fmt(.7*free)}。P1 retain約395GBは50%内ですがheadroomは約3GBだけ。scratch16GiBを別計上したpeak {fmt(recommended)}に対してoverall55%候補={fmt(.55*free)}を提案し、45%をOS/otherstudies/uncertaintyへ残します。予算は採用せずdecision supportのみ。ConditionalCo0.125最大は追加{fmt(conditional_extra)}、3series peak{fmt(recommended+conditional_extra)}で50/55/70%候補を超えるため、trigger後の容量を別途解決せずRUN-readyにしません。\n\n"
md+='''## 16. Scientific information retained/lost

'''+table(['claim','P0','P1','P2','condition/loss'],[[v['claim'],v['P0'],v['P1'],v['P2'],v['condition']] for v in claims])+'\n'
md+='''Safe to sample: fullfields/profiles/local defect maps/selected fullraw audit。Safe selected-only: native coeff/source/BC/current-old arrays、full24outer playback at registered epochs。Safe discard after validated online reduction: nonselected raw fullstage arrays、exact duplicate states/immutable blobs。MUST_KEEP_EVERY_STEP: allregistered primary/state/arrival/scalar histories、every-relevant-stage mass/energy terms/norms/sync/reference/global changes、inner solve/certificate outcomes、stage health/epoch commitments、failure events。Raw logはcomplete。復元不能な証拠を残したと主張しません。

## 17. Thesis implications

P1はstartup t*=0,.001,.002,.005,.01,.02,.05、evolution .1,.2,.3,.5,1,1.5とactual arrival/final3windowsでTcontours、Uvectors/streamlines、Nu profilesを作る時刻候補。時刻は実際のafter-crossing native timeとcaptionに書く。Flow plume onsetが候補時刻の間に起きた場合、scalarからfieldsを生成しない；retained .005 snapshotsの分解能限界を明記。P2の.02ではcirculation/plumeの細部を見逃すリスクが高まる。futureparticle studiesの初期flow参考にはselectedfields/selectedprofilesが有用ですが、dynamic coupling forcing historyとして十分とは言わずPARTICLE_COUPLING_READY=NO。

## 18. Resource feasibility

'''+table(['resource','current/recommended assessment','grade','remaining condition'],[['STORAGE','P0 infeasible; P1 primary planning peak≈412GB fits796GB free','CRITICAL current','v1.3 packed caps+quota; conditionalthird≈0.68TB needs separate budget'],['COMPUTE','~87million fv calls primary / ~101million scalar component calls','HIGH/UNRESOLVED','serial runtime unknown; steady-cost what-if not guarantee'],['I/O','P0≈2.05billion fsync calls; chunk candidates drastically reduce','HIGH/UNRESOLVED','online native reduction,packed encoding and crash semantics validated'],['MEMORY','fullstep JSON ring170–341GB impossible; packed bounded≈1.36GB buffer proposed','MEDIUM/UNRESOLVED','target live matrix/encoder/RSS estimate not measured;8GiB total budget proposed']])+'\n'
md+='''Serial support is explicit: current observer global sink/serial manifests and matrix coupled-patch STOP are notMPI-ready。24logical CPUsを24倍速度として使わない。Parallel support NOT_VALIDATED、別task/qualification無しにparallel launchしない。Compute materialでも24outer/linear tolerance/certificateを本reviewで変更せず、U01 revision necessityはUNRESOLVED。

## 19. Recommended resource policy

P1_CONSERVATIVE_REDUCEDをcandidateとして推奨。Every-step online scienceを維持し、retentionをphysical-time/frame/case-purposeへ合わせ、fullstep proofはstartup+scheduled、中間auditはlastouter+initialdensity、anomalyはbounded buffersでpossibleなcontextを追加。Binary/chunk/dedupのbaselinecapacityで計算し、compressionを必要条件にしない。現在のJSON全stageを作ってscratchへ書いた後にdiscardするだけではCPU/I/Oを解決しません。Runtime transient計測無しでRUNが実用的とは結論しません。

## 20. Contract-revision requirement

Diagnostic v1.3が必要ですが作成しません。U01/U02/U03の数字・physics・equations・arrival・hard thresholdは変更提案なし。U04 theoretical capture/hooks/oldTime/BC/sign/floorは不変、resource exporter/online discard validation/sparse-audit mode/typedformat/crash/quotaのimplementation adaptationと再qualificationが必要なのでU04_REVISION_REQUIRED=YES（数値evaluator再設計を意味しない）。既存U04 CLOSED証跡を上書きしません。

必要future validation: packed decoded actionとnative stored action/selected原format replayの一致、全stage online guard移行、receipt fullgraphとselected rawの正直なcoverage、lost/duplicate/wrongepoch/NaN/wrongtype/hash/partialchunk/quota/fault failure tests、OFF/ON bitwise or explicit justified equivalence、every-step exact primary extractor/window/statistical再解析、binary/library/schema/input hash pins。No silent evidence-loss/result-driven tuning。

## 21. Exact next task

**PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION**。
Diagnostic-only v1.3 candidate、resource retention/requalification設計とcompute/conditionalthird capacity gateをまとめる。Computeが未解決ならRUNを許可しない。推奨gpt-6.1-sol / medium。User decision required。実solver/pilot/case/mesh/initializationは一切実行せず終了。

## Required final status

```text
'''+''.join(f'{k} = {v}\n' for k,v in status.items())+'```\n'
(PREP/'DiagnosticTransient_resource_feasibility_review.md').write_text(md)
(DIR/'final_status.txt').write_text(''.join(f'{k} = {v}\n' for k,v in status.items()))
print(json.dumps({'review':'COMPLETE','retained_GB':P['P1_CONSERVATIVE_REDUCED']['primary_bytes']/1e9,'peak_GB':recommended/1e9,'peak_fraction':recommended/free,'conditional_all_three_peak_GB':(recommended+conditional_extra)/1e9,'next':status['NEXT_SINGLE_TASK']},indent=2))
