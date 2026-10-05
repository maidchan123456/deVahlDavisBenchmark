# DiagnosticTransient resource revision

## 1. Overall result

**INCOMPLETE**。v1.3 resource candidateとP1 native synthetic prototypeを作成しましたが、production primary/control/certificate/arrivalのlive bindingが未完了です。production classificationは明示STOP。synthetic mass/energy PASSだけで完了/readyとはしません。CFD/ケース/mesh/初期化は実行ゼロ。

## 2. Parent v1.2 verification

指定HEAD `ed2371e88c2d728bfbf8fffd21cd99497c1b9afc` 一致。parent SHA `7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd`、formalSHA `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60` は一致。parentU01–U04 CLOSED/formal/historical evidenceは未変更。直接authority4レビュー成果物と保護対象のhashをauthority.jsonに保存。native parent source 810ファイルのhashを既存build authorityと照合。repo全体の再監査なし。

## 3. Scope/invariants

| Section | v1.2→v1.3 |
|---|---|
| Physical model/mesh/initial condition | unchanged |
| U01 numerics/24outer/2pressure/tolerance/relaxation | unchanged |
| U02 dt/controller/Co | unchanged |
| U03 duration/arrival/final values | unchanged |
| U04 math/native stages/hooks | unchanged |
| U04 persistence/online retention | revised prototype |
| Fullfield/raw cadence/chunk/hash/fsync | revised candidate |
| Resource guards | added; production binding blocked |

契約内23 semantic sectionsをparentとJSON値比較。native transition/stage/operator hook bodiesはparentコピー。保存経路のconstructor start/emit/finishだけ差替え。

## 4. P1 scientific rationale

全required native stageは実際に評価し、scalar/norm/epoch/validityを保存する方針。永久raw保存と評価頻度を分離。全step raw independent再assembleと任意posthoc field QoIは失われる。信頼根拠はfrozen source/U04事前検証、online fail-closed、complete compact stage graph、selected実raw replay。未実装primary collectorがあるためproductionでの削減は未許可。

## 5. Every-step evidence

毎native stageのtime/index/outer/pressure/energy/rho counters、exact metadata(epoch含む)commitment、payload identity、matrix scalar sums/L1/Linf/defect/bound/max cell、term metrics、C/end/sync metricsをbinary receiptへ保存。75 required primary/stage columns全体のlive collector、Co control/achieved/cap reason、native linear residual/certificate、arrival historiesは未bound。primary_evidence.pyはvolume Nuと4097点centreline extrema等のarray helperのみ。既存9000配列比較はNu差約3.55e-15、velocity/positions一致。これは新CFD結果/全live scalar bitwise qualificationではありません。

## 6. Raw audit schedule

Cold t*=0はinitial state+stage receipt（t0で存在しないmatrixを作らない）。最初3 physical stepsでEuler/BDF transition；first valid BDF2がここに含まれない場合qualification STOP。full t*=.5/1/1.5/1.99各first completed crossing。59bundleはΔ*=.05、初回density7+terminal outer52；max7 full/56 bundle per series。U03 candidateはm*.1なので3確認windowsのstart/mid/endは.05 gridで事前登録済み。actual native crossing timesを記録しdt変更/過去raw復元はしない。Final/anomaly reserve16にactual endpoint/current/recent contextを割当。science-trigger feedは未bound。

## 7. Field snapshot schedule

t*=0 initial、[0,.05] Δ*=.001（51点）、以降Δ*=.005（max390点）、final/anomaly64枠で505/series。initial target0をconstructorで消費しfirst stepへ二重計上しない。必須final_fields.bin保存。T/U/e/rho/p/phi等typed current stateとBC/history/source/input geometryで図示可能；restart許可ではない。field write失敗はSTOP。rawflow every-step/粒子forcing historyは保持せずparticle-ready NO。

## 8. Online reduction design

generate_online.pyはv1.2 replay loopをfilesystem読み込みからgenerator入力へ機械移行。各callbackで同じfield/oldTime/BC/unit/native matrix action/term sum/reference/rho sync/storage checksを保存前に実行し、成功ACKだけ返す。評価failureは即series invalid。every-stage compact graphはfrozen StageLedgerで再検証、selected59はそのreceipt witnessに対応させて同じ数学を再評価。partial auditをcomplete raw replayと呼ばない。

## 9. Packed/chunk storage

little endian IEEE754 Float64、native addresses Int64、explicit shape/types/byte length/SHA、signed zero。metadata JSON+typed binary。Float32/quantization/decimal truncationなし。exact type/shape/hash byte equalityのみdedup。geometry/volumes/Cv/g/owner/neighbourをshared blobsで一回保存し、各callbackでexact一致検査。動く係数/異なるepochsの推測dedupなし。Native transportはJSON17 IPCのままで、production serialization costを解決済みとはしない。

## 10. Hash/manifest/fsync design

64step chunksを登録。buffer上限64MiB、8stepならfsync/file約8倍、256stepならcrash-loss/memory約4倍なので64を中間候補としてunit test65stepsで64+1に分割。64以外のproduction性能最適性は未測定。data fsync→no-overwrite atomic hardlink→dir fsync→hash-chain manifest append/fsync、3fsync/file+completion2。完整rootはcomplete.jsonでseal。途中chunk/orphan/manifest欠損はINVALID、last completed hashed chunkはaudit prefixのみ；U03 primary interruption invalid/no resume不変。raw log4MiB rotationはlossless unit PASS、production launcherへの接続は未完了。

## 11. Rolling buffer/anomaly capture

Last16 stage packed payloads、各32MiB cap、rolling最大536,870,912 bytes。current59bundle最大512MiB、chunk64MiB、encoder32MiB、finalfields16MiB。全step9GiB rawはselected stepのみscratchへstreamし、RAMへ全stepを保持しない。normal時nonselectedは検査後discard、anomalyはavailable16 stages/current contextのみ。Failure pathと手動trigger APIはtested、near/fail/Co/arrival等全science triggerは未接続なのでANOMALY_TRIGGERED_RAW_CAPTURE=NO。

## 12. Co0.125 policy

C3を登録：Co0.125 science trigger >0.5% 不変。発動時は実行前STOP、別capacity review/recheck、明示authorization。三系列最大peak 758.305GB/free 95.30% は55%予算外。既存primary raw削除/archive自動化なし。外部容量未確認/not assumed。

## 13. Synthetic pipeline validation

| Metric | P0 same native fixture | P1 same native fixture |
|---|---|---|
| bytes | 19023111 | 27509617 |
| files | 1154 | 14 |
| fsync_calls | 3458 | 38 |
| wall seconds | 22.776525092078373 | 19.59497989504598 |

1152 records/1141 physical stage observations；frozen mass/energy/end/sync/reference values BITWISE、selected full replayと59partial replay PASS。1step fixtureはstartup full+final auditを両方保存するためP1 bytesはP0より大きい（ratio旧/新=0.692）。容量削減率/production speedupへ外挿しない。tests/native .logは全文保持。

## 14. Non-invasiveness

同じnative in-memory fixtureをOFF、P0 ON、P1 ONで実行し、matrix/source/BC/oldTime/physical fields/native residual physical fingerprintがBITWISE一致。P1二回のpayload/chunk/sharedblob/manifest/summary全bytesが一致。Synthetic only、production model160²のnon-invasivenessを実行証明したとは主張しない。

## 15. Failure injection

| Injected fault | Result |
|---|---|
| wrong_epoch | FAIL_CLOSED |
| duplicate_step | FAIL_CLOSED |
| missing_step | FAIL_CLOSED |
| NaN | FAIL_CLOSED |
| wrong_native_schema | FAIL_CLOSED |
| truncated_binary | FAIL_CLOSED |
| wrong_hash | FAIL_CLOSED |
| wrong_schema | FAIL_CLOSED |
| wrong_endian | FAIL_CLOSED |
| wrong_shape | FAIL_CLOSED |
| missing_chunk | FAIL_CLOSED |
| bad_manifest | FAIL_CLOSED |
| partial_commit | FAIL_CLOSED |
| scratch_stage_quota | FAIL_CLOSED |
| mandatory_field_failure | FAIL_CLOSED |
| native_ack_failure_propagation | FAIL_CLOSED |

追加unit：Co0.125 guard、space/inodes quota、64+1chunk、recent16 flush、log byte rotation、unqualified production STOP。必須field encoding failure/scratch-stage quotaもSTOP。Full production primary/control collector未接続は別のqualification failureで、synthetic PASSに埋めない。

## 16. Storage scenarios

| t* | primary retained GB | primary peak GB | 3series peak GB | primary/free | 3series/free |
|---|---|---|---|---|---|
| 0.5 | 159.184 | 176.364 | 293.398 | 22.16% | 36.87% |
| 1.0 | 237.535 | 254.715 | 448.367 | 32.01% | 56.35% |
| 2.0 | 394.237 | 411.417 | 758.305 | 51.70% | 95.30% |

実receipt 225,464 B/physical step、primary8KiB+complete log64KiB/step reserve、chunk schema16KiB、full9GiB/bundle512MiB/field16MiB/fixed1GiB per seriesのcapを計上。Conservative typed model full6.527GB、59bundle0.331GB。型mask/metadata余地込み、synthetic偶然一致/圧縮のcredit0。旧P1約395GB→実schema候補約394GBで整合。ただし未boundprimary8KiBは予約で実production measureではない。

## 17. Inode/file-count scenarios

| t* | primary files bound | 3series files bound |
|---|---|---|
| 0.5 | 5288 | 11839 |
| 1.0 | 10198 | 23112 |
| 2.0 | 20020 | 45660 |

各series：ceil(Nsteps/64) receipt chunks+same ceiling4MiB logs、full audits、bundles、field snapshots、固定64files（shared blobs/source/provenance/root manifest/completion等）。max primary約2万/三系列約4.6万、現free inodesのごく一部。old約6.85億files不要。Per-chunk manifest別fileは作らず各series root manifest1。

## 18. Memory assessment

Packed buffer deterministic caps合計1,191,182,336 B。native/backend AS8GiBずつ、合計16GiB、host MemAvailable>=24GiBのguardで少なくとも8GiB余地を要求；swapなし。合成RSS最大265,844KiBはdriver/children測定scopeであり160²RSSではない。JSON transport+retained evaluator objects+未boundprimary collectorがcaps内に収まる160²proofなし、MEMORY_FEASIBILITY=UNRESOLVED。selected offline audit decoderも1stageずつstreamし全stepをJSON objectsに保持しない。

## 19. I/O assessment

FSYNC/inodesは大幅削減。Chunk/uncompressed binary/atomic failure pathsのsynthetic correctness PASS。ただし全required native callbackは継続しnative transient JSON serialize/hash/IPC/full evaluatorを毎stage実行する。ON約20s対OFF約0.3sのfixture overheadをproduction時間へ転用しない。IO_FEASIBILITY=UNRESOLVED、source-static arraysの検査も残る。

## 20. Compute status

24outer/2pressure/linear設定/early-exit禁止を保持。最大主系列約8700万fv calls、約1.014億scalar componentsの元planning不変。Serial only；MPI NOT_VALIDATED、CPU24logicalを24倍速度とみなさない。今回CFD/pilot/short-runなし。COMPUTE_FEASIBILITY=UNRESOLVED。

## 21. v1.3 contract

JSON/Markdown/SHAを新規作成：`docs/routeA_diagnostic_transient_contract_v1.3.*`。SHA `212c1dc5056775e1825e13f29336ce51483679862e5e41c1e164f8c724db21b3`。scope RESOURCE_EVIDENCE_RETENTION_ONLY、parent v1.2 SHA固定。**candidate INCOMPLETE / execution_authorized=false**。v1.2/formalを上書きせず、old native semantic hashesとnew persistence/runtime source hash `8ee521d7ba5e12d143ff1690ce9c1f3d660f36f0b0e6a286999266c630d0d0df` を別にpin。

## 22. Readiness

容量/inodesのprimary planningは成立。ただしfully implemented P1、every-step全primary/control/U01/U03/science-trigger/launcher bindingが未完成なのでSTORAGE_READY=NO、RESOURCE_READY=NO。科学的許可/technical readiness YESはparent v1.2状態の継承であって、v1.3が実行可能になったことを意味しない。

- Complete native-to-P1 live binding of every required primary/stage column, Co/controller receipts and native per-solve residuals is not implemented. Existing QoI array helper is not attached to native callbacks.
- U01 certificate/registered U03 arrival and final-window collector and related anomaly/arrival triggers are not bound to the new live compact path. Frozen definitions are unchanged; do not infer them from thinned disk fields.
- Production preflight, frozen runtime source/library checks and full raw-log rotation need integration into the future authorized run launcher. Production classification is currently rejected before evidence reduction.
- Only synthetic pipeline and buffer limits are qualified. Production target memory/I/O/compute remain unresolved; no production or pilot timing was performed.

## 23. Exact next task

**FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION**。Native→complete primary/control/per-solve/certificate/arrival収集を接続し、全registered trigger/log/preflight/source pinをqualify、every-value比対/selected replay/failure/non-invasiveness/repeatabilityを再検証してactual schema再計上。definitions U01–U03/mathは不変。Closure後もcompute unresolvedなら次にcompute feasibility review；今はRUN/compute-onlyへ進めない。推奨gpt-6.1-sol / medium、user decision required。

## Required final status

Synthetic PASS/feature YESは上記prototype scope。全P1 production qualificationはINCOMPLETE。

```text
ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION = INCOMPLETE
STUDY_OWNERSHIP = DIAGNOSTIC_FIXED_GRID_TRANSIENT_CHARACTERIZATION
PARENT_DIAGNOSTIC_CONTRACT_VERSION = 1.2
PARENT_DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
PARENT_DIAGNOSTIC_CONTRACT_SHA256 = 7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd
DIAGNOSTIC_CONTRACT_CREATED = YES
DIAGNOSTIC_CONTRACT_VERSION = 1.3
DIAGNOSTIC_CONTRACT_SHA256 = 212c1dc5056775e1825e13f29336ce51483679862e5e41c1e164f8c724db21b3
REVISION_SCOPE = RESOURCE_EVIDENCE_RETENTION_ONLY
U01_CHANGED = NO
U02_CHANGED = NO
U03_CHANGED = NO
U04_EQUATION_SEMANTICS_CHANGED = NO
U04_PERSISTENCE_POLICY_CHANGED = YES
RECOMMENDED_POLICY_IMPLEMENTED = NO
EVERY_STEP_PRIMARY_SCALARS = NO
EVERY_STEP_GLOBAL_MASS_ENERGY = YES
EVERY_STAGE_COMPACT_RECEIPTS = YES
FULL_FIELDS_EVERY_STEP = NO
FULL_MATRIX_EVERY_STEP = NO
SELECTED_RAW_MATRIX_AUDIT = YES
SELECTED_FULL_FIELD_SNAPSHOTS = YES
ANOMALY_TRIGGERED_RAW_CAPTURE = NO
ROLLING_BUFFER_IMPLEMENTED = YES
ROLLING_BUFFER_PEAK_BYTES = 536870912
PACKED_BINARY_PAYLOAD = YES
LOSSLESS_STORAGE = YES
CHUNKED_RECEIPTS = YES
CHUNK_SIZE_STEPS = 64
ATOMIC_CHUNK_COMMIT = YES
HASH_MANIFEST_POLICY = SHA256_TYPED_BLOBS_AND_CHUNKS_WITH_ORDERED_MANIFEST_CHAIN
FIELD_SNAPSHOT_POLICY = TSTAR_0_TO_0P05_DENSE_0P001_THEN_0P005_FINAL_ANOMALY_RESERVE64
RAW_AUDIT_POLICY = FIRST3_FULL_PLUS_0P5_1_1P5_1P99_AND_59RECORD_BUNDLES_EVERY_0P05_RESERVE16
CO0125_RESOURCE_POLICY = C3_STOP_SEPARATE_RESOURCE_REVIEW_RECHECK_AND_EXPLICIT_AUTHORIZATION
CO0125_AUTOMATIC_EXECUTION_ALLOWED = NO
RESOURCE_PREFLIGHT_REQUIRED = YES
SYNTHETIC_RESOURCE_PIPELINE_TESTS = PASS
ONLINE_REDUCTION_EQUIVALENCE = BITWISE
SELECTED_RAW_REPLAY = PASS
FAILURE_PROPAGATION = PASS
NON_INVASIVENESS = BITWISE
REPEATABILITY = PASS
CURRENT_FREE_STORAGE_BYTES = 795736838144
PRIMARY_2_SERIES_RETAINED_ESTIMATE_BYTES = 394237085064
PRIMARY_2_SERIES_PEAK_ESTIMATE_BYTES = 411416954248
PRIMARY_2_SERIES_PEAK_FRACTION_OF_FREE = 0.5170264018536593
CONDITIONAL_3_SERIES_PEAK_ESTIMATE_BYTES = 758305164520
CONDITIONAL_3_SERIES_PEAK_FRACTION_OF_FREE = 0.9529597326280549
ESTIMATED_FILE_COUNT_PRIMARY = 20020
ESTIMATED_FILE_COUNT_THREE_SERIES = 45660
STORAGE_FEASIBILITY = FEASIBLE
INODE_FEASIBILITY = FEASIBLE
MEMORY_FEASIBILITY = UNRESOLVED
IO_FEASIBILITY = UNRESOLVED
COMPUTE_FEASIBILITY = UNRESOLVED
DIAGNOSTIC_TRANSIENT_STORAGE_READY = NO
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = YES
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = YES
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
SOLVER_EXECUTED = NO
SYNTHETIC_NATIVE_DRIVER_EXECUTED = YES
PRODUCTION_SOLVER_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
NEXT_SINGLE_TASK = FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
