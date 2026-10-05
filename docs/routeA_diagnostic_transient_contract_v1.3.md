# Route A diagnostic transient contract v1.3

RESOURCE / EVIDENCE RETENTION REVISION ONLY.

**RESOURCE_REVISION_CANDIDATE_INCOMPLETE_PRODUCTION_BINDING_BLOCKED**

This contract is a diagnostic-only candidate with execution_authorized=false. It does not authorize CFD or supersede parent v1.2 technical readiness/history. Complete P1 production primary/control/certificate/arrival binding remains unqualified; server.py rejects DIAGNOSTIC_OBSERVATION.

Parent v1.2 SHA: `7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd`. Formal v1.7 SHA: `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60` (read-only).

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

全required native stageは実際に評価し、scalar/norm/epoch/validityを保存する方針。永久raw保存と評価頻度を分離。全step raw independent再assembleと任意posthoc field QoIは失われる。信頼根拠はfrozen source/U04事前検証、online fail-closed、complete compact stage graph、selected実raw replay。未実装primary collectorがあるためproductionでの削減は未許可。

毎native stageのtime/index/outer/pressure/energy/rho counters、exact metadata(epoch含む)commitment、payload identity、matrix scalar sums/L1/Linf/defect/bound/max cell、term metrics、C/end/sync metricsをbinary receiptへ保存。75 required primary/stage columns全体のlive collector、Co control/achieved/cap reason、native linear residual/certificate、arrival historiesは未bound。primary_evidence.pyはvolume Nuと4097点centreline extrema等のarray helperのみ。既存9000配列比較はNu差約3.55e-15、velocity/positions一致。これは新CFD結果/全live scalar bitwise qualificationではありません。

Cold t*=0はinitial state+stage receipt（t0で存在しないmatrixを作らない）。最初3 physical stepsでEuler/BDF transition；first valid BDF2がここに含まれない場合qualification STOP。full t*=.5/1/1.5/1.99各first completed crossing。59bundleはΔ*=.05、初回density7+terminal outer52；max7 full/56 bundle per series。U03 candidateはm*.1なので3確認windowsのstart/mid/endは.05 gridで事前登録済み。actual native crossing timesを記録しdt変更/過去raw復元はしない。Final/anomaly reserve16にactual endpoint/current/recent contextを割当。science-trigger feedは未bound。

t*=0 initial、[0,.05] Δ*=.001（51点）、以降Δ*=.005（max390点）、final/anomaly64枠で505/series。initial target0をconstructorで消費しfirst stepへ二重計上しない。必須final_fields.bin保存。T/U/e/rho/p/phi等typed current stateとBC/history/source/input geometryで図示可能；restart許可ではない。field write失敗はSTOP。rawflow every-step/粒子forcing historyは保持せずparticle-ready NO。

generate_online.pyはv1.2 replay loopをfilesystem読み込みからgenerator入力へ機械移行。各callbackで同じfield/oldTime/BC/unit/native matrix action/term sum/reference/rho sync/storage checksを保存前に実行し、成功ACKだけ返す。評価failureは即series invalid。every-stage compact graphはfrozen StageLedgerで再検証、selected59はそのreceipt witnessに対応させて同じ数学を再評価。partial auditをcomplete raw replayと呼ばない。

little endian IEEE754 Float64、native addresses Int64、explicit shape/types/byte length/SHA、signed zero。metadata JSON+typed binary。Float32/quantization/decimal truncationなし。exact type/shape/hash byte equalityのみdedup。geometry/volumes/Cv/g/owner/neighbourをshared blobsで一回保存し、各callbackでexact一致検査。動く係数/異なるepochsの推測dedupなし。Native transportはJSON17 IPCのままで、production serialization costを解決済みとはしない。

64step chunksを登録。buffer上限64MiB、8stepならfsync/file約8倍、256stepならcrash-loss/memory約4倍なので64を中間候補としてunit test65stepsで64+1に分割。64以外のproduction性能最適性は未測定。data fsync→no-overwrite atomic hardlink→dir fsync→hash-chain manifest append/fsync、3fsync/file+completion2。完整rootはcomplete.jsonでseal。途中chunk/orphan/manifest欠損はINVALID、last completed hashed chunkはaudit prefixのみ；U03 primary interruption invalid/no resume不変。raw log4MiB rotationはlossless unit PASS、production launcherへの接続は未完了。

Last16 stage packed payloads、各32MiB cap、rolling最大536,870,912 bytes。current59bundle最大512MiB、chunk64MiB、encoder32MiB、finalfields16MiB。全step9GiB rawはselected stepのみscratchへstreamし、RAMへ全stepを保持しない。normal時nonselectedは検査後discard、anomalyはavailable16 stages/current contextのみ。Failure pathと手動trigger APIはtested、near/fail/Co/arrival等全science triggerは未接続なのでANOMALY_TRIGGERED_RAW_CAPTURE=NO。

C3を登録：Co0.125 science trigger >0.5% 不変。発動時は実行前STOP、別capacity review/recheck、明示authorization。三系列最大peak 758.305GB/free 95.30% は55%予算外。既存primary raw削除/archive自動化なし。外部容量未確認/not assumed。

Packed buffer deterministic caps合計1,191,182,336 B。native/backend AS8GiBずつ、合計16GiB、host MemAvailable>=24GiBのguardで少なくとも8GiB余地を要求；swapなし。合成RSS最大265,844KiBはdriver/children測定scopeであり160²RSSではない。JSON transport+retained evaluator objects+未boundprimary collectorがcaps内に収まる160²proofなし、MEMORY_FEASIBILITY=UNRESOLVED。selected offline audit decoderも1stageずつstreamし全stepをJSON objectsに保持しない。

容量/inodesのprimary planningは成立。ただしfully implemented P1、every-step全primary/control/U01/U03/science-trigger/launcher bindingが未完成なのでSTORAGE_READY=NO、RESOURCE_READY=NO。科学的許可/technical readiness YESはparent v1.2状態の継承であって、v1.3が実行可能になったことを意味しない。

- Complete native-to-P1 live binding of every required primary/stage column, Co/controller receipts and native per-solve residuals is not implemented. Existing QoI array helper is not attached to native callbacks.
- U01 certificate/registered U03 arrival and final-window collector and related anomaly/arrival triggers are not bound to the new live compact path. Frozen definitions are unchanged; do not infer them from thinned disk fields.
- Production preflight, frozen runtime source/library checks and full raw-log rotation need integration into the future authorized run launcher. Production classification is currently rejected before evidence reduction.
- Only synthetic pipeline and buffer limits are qualified. Production target memory/I/O/compute remain unresolved; no production or pilot timing was performed.

**FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION**。Native→complete primary/control/per-solve/certificate/arrival収集を接続し、全registered trigger/log/preflight/source pinをqualify、every-value比対/selected replay/failure/non-invasiveness/repeatabilityを再検証してactual schema再計上。definitions U01–U03/mathは不変。Closure後もcompute unresolvedなら次にcompute feasibility review；今はRUN/compute-onlyへ進めない。推奨gpt-6.1-sol / medium、user decision required。

Machine authority: routeA_diagnostic_transient_contract_v1.3.json.
JSON SHA256: `212c1dc5056775e1825e13f29336ce51483679862e5e41c1e164f8c724db21b3`.
