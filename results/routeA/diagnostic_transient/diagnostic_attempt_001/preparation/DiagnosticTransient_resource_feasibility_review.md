# DiagnosticTransient resource feasibility review

## 1. Executive summary

Review COMPLETE。契約v1.2/U01–U04/formal v1.7は変更せず、solver・synthetic solver driver・case/mesh生成・初期化は一切実行していません。

登録primary questionは固定160²でCo変更がQoI trajectory/final valuesとmass/energy behaviorに及ぼす差です。必要なのは全stepの正確なonline評価・scalar/norm/validity evidenceと選択されたraw auditであり、全matrix・全field・全stageの永久保存ではありません。この削減は新たなonline/replay/retention実装の再検証を条件とします。

P0の元projection **5,825,629,244,755,728 bytes = 5.825629 PB** をliteral再現。現free **796,351,639,552 bytes = 0.796352 TB** の約7,315倍です。補正numeric projectionは6.392273 PBで、JSON実容量ではありません。推奨は未採用のP1候補：永久retain 395.183 GB、scratch込みpeak 412.362 GB（freeの51.78%）。Storage planningは条件付きで現実化できますが、compute/I/O/memory実測は未解決、resource-readyはNOです。

## 2. Authority/provenance

Known HEAD4986b1a4…の後続HEAD `98b65be92d6f5109b13ff18584eeaedb2d45ec0b` を確認。後続は既存結果のvisualization commitであり、診断SHA `7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd` とformalSHA `fbc744e012f66b37b5d9409be961cb5a9410c3d75ac7e2f026b2acf118d3bb60` は指定値に一致。git tracked開始差分なし。全instrumentation/codeと契約群45ファイルの開始/終了hash一致を確認しました。既存input 1,234ファイル（healthy U04 streamの1,152 payloadを含む）のhashも照合済み。日付はAsia/Tokyo、記録時刻 `2026-10-05T18:53:06+09:00`。

`resource_review/authority_and_host.json` にdf-h/df-B1/df-i/lscpu/MemAvailable/cgroup/CPU affinityを保存。既存steady logのHostはmirai-Precision-5860-Tower、nProcs=1。最終照合の詳細は`resource_review/verification.json`、入力hashは`verified_input_sha256.json`、新規成果物hashは`artifact_sha256.json`に記録。終了時git tracked/index差分なし、HEAD不変。終了時freeは`verification.json`/`end_df.txt`に別記し、本文のfreeは上記時刻のaccounting snapshotを使用。現在ホストはXeon w5-2545、12cores/24logical CPUs、affinity24。これを将来jobの専用割当・MPI速度保証とは扱いません。

## 3. Current resource envelope

FS available inodes=59,458,653、total=62,447,616。現在inode空きは多いものの、P0のphysical record filesだけで684,808,803個が必要となり、容量以前にinode envelopeも不足。記録ごと3fsyncで約2,054,426,409回。

元baseline field numeric componentのみでも1.228 TB。実existing complete directory scaleでevery-stepをwhat-if計算すると約3.427TBです。既存ASCIIと将来binary/nonuniform/historyを同一視せず、actual future sizeの測定とは扱いません。

## 4. Step-count planning scenarios

Constant prospective hを使うceil(710*t*/h)。startup ramp/adaptive variation/actual arrivalを予測しません。max-durationは登録maximum2を計画用に使用し、native endTimeの微小shortfallやovershoot制御を変更しません。minimum0.5は3window確認を既に包含し、さらに0.3を加算しません。

| Scenario | t* / seconds | Co0.5 steps | Co0.25 steps | primary sum | conditionalCo0.125 |
|---|---|---|---|---|---|
| B_EARLIEST_ALLOWED_ARRIVAL | 0.5 / 355.0 | 50016 | 100031 | 150047 | 200061 |
| C_INTERMEDIATE_SCENARIO | 1.0 / 710.0 | 100031 | 200061 | 300092 | 400122 |
| A_MAX_DURATION_SCENARIO | 2.0 / 1420.0 | 200061 | 400122 | 600183 | 800244 |

## 5. Storage accounting model

S_total=N_step*(S_scalar+S_field+24*S_outer+48*S_pressure+S_mass_matrices+S_energy_matrices+S_terms+S_ledger+S_integrity+S_log)+S_selected_audits+S_fixed+S_scratch。

互いにexclusiveなA–J分類で元numeric baselineを厳密に分解。records/stepはcategoryが寄与するrecord数で、同じstage recordが複数categoryを含むため列のcountは加算しません。mean bytes/recordは該当numeric subtotal/count。StageLedger/string SHA/keys/manifests/logsのASCIIを元baselineは計上しないため、A/I/Jが0でも科学的不要という意味ではありません。

| Component | numeric mean bytes/record | records/step | bytes/step | primary total | fraction | necessity/reduction |
|---|---|---|---|---|---|---|
| A Primary scalar histories | 0 | 0 | 0 | 0.000 GB | 0.0000% | every-step scalars essential |
| B Full CFD field snapshots | 2045440 | 1 | 2045440 | 1.228 TB | 0.0211% | selected snapshots essential; every-step disk full fields optional |
| C Outer-iteration field/state copies | 2799944 | 1141 | 3194736480 | 1.9174 PB | 32.9136% | every-outer derived norms/certificate essential; every field array optional |
| D Pressure-corrector fields/matrices | 8031349 | 672 | 5397066240 | 3.2392 PB | 55.6030% | every-pressure rho/reference validity and norms essential; raw arrays selected |
| E Mass total matrix payload | 2803680 | 98 | 274760640 | 164.907 TB | 2.8307% | native action every invocation essential; raw coefficients selected audit |
| F Energy total matrix payload | 3577600 | 72 | 257587200 | 154.599 TB | 2.6538% | native unrelaxed assembly evaluation every solve essential; raw selected |
| G Term-separated payload | 1260804 | 460 | 579970032 | 348.088 TB | 5.9751% | term sums/signs/dimensions every solve essential; raw term arrays selected |
| H StageLedger metadata | 224 | 1141 | 255584 | 153.397 GB | 0.0026% | all-stage online fail-closed essential; compact persisted receipts |
| I Hash/manifest/provenance | 0 | 1141 | 0 | 0.000 GB | 0.0000% | integrity/provenance essential; file/chunk roots plus shared immutable references |
| J Raw solver logs | 0 | 0 | 0 | 0.000 GB | 0.0000% | complete raw solver log essential audit |

2cell→25600cellはcells/diag/source/psi/oldTime/current actionsにO(Ncells)、upper/lower/owner/neighbour/phi/weightsにO(Nfaces)、active boundaryに640faces、scalar metadataはO(1)。旧estimatorでCv cell arrayとlinear_weights arrayが未scaleでした。review側のshape補正はnumeric step 10.650541GB、primary 6.392273PB。旧コード/記録は不変です。物理patch数・metadata/strings・ASCII digits・compression・uniform/nonuniformは別の不確かさです。

Matrix payloadはpsi/history/addressing/volumesも含み、pure coefficient-only量ではありません。Pressure category Dはpressure-phase field copiesとreference matricesを含み、mass total matricesはE、energy totalはF、term submatricesはGへexclusive分類。原projectionはFloat64-equivalentで、現在の17-digit JSON測定値ではありません。

## 6. Dominant storage contributors

| rank | category | total | fraction |
|---|---|---|---|
| 1 | D Pressure-corrector fields/matrices | 3.2392 PB | 55.603% |
| 2 | C Outer-iteration field/state copies | 1.9174 PB | 32.914% |
| 3 | G Term-separated payload | 348.088 TB | 5.975% |
| 4 | E Mass total matrix payload | 164.907 TB | 2.831% |
| 5 | F Energy total matrix payload | 154.599 TB | 2.654% |

Pareto top1=55.603%、top3=94.492%、top5=99.976%。state copies C+Dで88.517%。610recordsでpayload.state/rootとnative_state_epochが完全一致し、その二重copyのnumeric scaleだけで2.804GB/step。geometry/Cv/g等のimmutable blobと厳密同一payloadのreference化はlossless。異なるstage/epochの同一性を推測してdedupしません。

## 7. Compute solve-count estimate

Native sourceはmomentumPredictor=yesで各outerにvector U solve、各outer e solve、2pressure solves、first-outer density predictor1+各pressure後density48=49。したがって24U+24e+48p+49rho=145fv solve calls/step。2D Ux/Uy componentとしては48U+24e+48p+49rho=169scalar calls。rho diagonal direct solveはPCGの反復1回と同コストではありません。CFDでは初回history fallback/conditioning/iterationsが異なります。

| series atmax | U vector | Ux/Uy components | e | p | rho diagonal | fv total | scalar2D total |
|---|---|---|---|---|---|---|---|
| 0.5 | 4801464 | 9602928 | 4801464 | 9602928 | 9802989 | 29008845 | 33810309 |
| 0.25 | 9602928 | 19205856 | 9602928 | 19205856 | 19605978 | 58017690 | 67620618 |
| 0.125 | 19205856 | 38411712 | 19205856 | 38411712 | 39211956 | 116035380 | 135241236 |

既存3000iteration segmentsのClockTimeは384/307/212s（0.128/0.1023/0.0707s perSIMPLE iteration）。writeInterval100・ASCII16・tolerance/steady conditioningの異なる実行です。24倍what-ifは最大primary約11.78–21.34days、earliest約2.95–5.34daysで、すべてROUGH_PLANNING_SCALE_ONLY。transient実測runtimeではありません。完全stepを仮に0.1/1/10sとすると最大primary0.695/6.947/69.466days。CPU時間の保証や24outer変更根拠には使用しません。computeのmaterial riskはHIGH、feasibilityはUNRESOLVEDです。

## 8. I/O assessment

保存済みsynthetic OFF=0.288577861s、ON=20.915767975s、ratio=72.48。1152records=19,023,111bytes、mean=16513.1bytes/record。1152にはstartup4/auxiliary7が含まれ、physical1141。bytes/stage/outerはstage_record_accounting.csv/resource_accounting.jsonに保存。実CFD overheadへ外挿しません。

現在sourceではpayload serialize/hash→exclusive temp/fsync→hardlink atomic publish/unlink→directoryfsync→manifest append/fsync。FSYNC3/recordに加え、deep copies、旧history copying、17digitostringstream、JSON value tree、payload/file hashes、repeated fields/matrix arrays、native full fields writeが候補cost。既存profilingがないため寄与率は不明です。

候補はmetadata JSON+Float64/Int32 packed blobs、geometry/coeff/source/psi epochsをshared immutable reference化し、every-step結果/outer-pressure receiptsをappend-only chunks（例64steps）へまとめる。per-array hashをなくす場合でもdecoded matrix/field identitiesとchunk file SHA/Merkle/root manifestが対応し、logical integrity checksは維持。packed byte order/type/shape/dimensions/signed-zero/versionを明示します。lossy/precision truncationは禁止。

Fsync alternatives: perrecordは最強durabilityだがprimary約20.5億回。perphysical-stepは少なくとも約120万data+commit sync。64step chunksは概算約1.9万data+commit sync（audit追加を除く）。後者crash時は最後のcomplete hashed chunkまでがaudit evidence、未commit tailはinvalid。U03のsingle continuous primaryは中断で全attempt invalid、prefixからresume/受入れはしません。v1.2 current formatのfsyncだけ勝手に省くことは不可。

Compression sample（in-memory read-only、compressed filesは生成しない）：

| existing sample | input | gzip6 fraction | zstd3 fraction | interpretation |
|---|---|---|---|---|
| actual_complete_9000_directory | 0.006 GB | 39.9955% | 42.1211% | sample-only; no production guarantee |
| existing_U04_complete_synthetic_stream | 0.019 GB | 2.1959% | 0.5824% | sample-only; no production guarantee |

元P0をfree内に納めるcompression fractionは0.00013670以下、50%budgetなら0.00006835以下が必要。syntheticの極端な反復/zero/history/metadata圧縮率を25600cellへ保証できません。Native binary/gzip/zstd/chunkingは有用ですが、容量設計はcompression benefit0で計算。JSON ASCIIはnumeric8byteに対し多くの値で20–25charsになり得るため元Float64 projectionを実JSON容量と扱いません。

## 9. Memory assessment

Measured host RAM=62.04GiB、available=58.96GiB、synthetic peakRSS=82612KiB（libraries/meshbaselineを含みwhole-processをcell比でscaleしない）。largest corrected record=17.627MB、fullstep=10.648GB、selected59records=0.555GB。

Fullstep packed ring1/2/4stepsは10.65/21.30/42.59GB。現在Json objectはscalarごとstring/vector/mapも持つため、ABI estimate16–32xでは1step170–341GBとなり、このホストのfullstep JSON ringは非現実的。正確なtarget RSS実測ではありません。

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

| existing accepted160² directory | du -sb | core U/T/p/p_rgh/rho/phi | format |
|---|---|---|---|
| cases/routeA/A-Ra1e6-fine/3000 | 5,708,277 | 4,523,506 | actual existing steady ASCII writePrecision16, not future binary transient measurement |
| cases/routeA/A-Ra1e6-fine/6000 | 5,708,483 | 4,523,638 | actual existing steady ASCII writePrecision16, not future binary transient measurement |
| cases/routeA/A-Ra1e6-fine/9000 | 5,709,592 | 4,523,930 | actual existing steady ASCII writePrecision16, not future binary transient measurement |

未来binary sizeは未実測。snapshot budget16MiBはlargest existingcompleteASCII5.71MBの約2.94倍にe/rho_T/K/history/metadataを含めたplanning cap。超過時はresource STOP/reviewでありfieldやoldTimeを黙って切り捨てません。

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

| policy/scenario | retained storage | fraction free | full raw audits | selected bundles | fullfields | risk/feasibility |
|---|---|---|---|---|---|---|
| P0_CURRENT_MAXIMAL/B_EARLIEST_ALLOWED_ARRIVAL | 1.4564 PB | 182886.48% | 150047 | 0 | 150047 | NO as-is |
| P1_CONSERVATIVE_REDUCED/B_EARLIEST_ALLOWED_ARRIVAL | 185.995 GB | 23.36% | 8 | 52 | 410 | capacity fits; unimplemented/conditional |
| P2_AGGRESSIVE_DEFENSIBLE/B_EARLIEST_ALLOWED_ARRIVAL | 97.596 GB | 12.26% | 4 | 26 | 154 | capacity fits; unimplemented/conditional |
| P0_CURRENT_MAXIMAL/C_INTERMEDIATE_SCENARIO | 2.9128 PB | 365770.51% | 300092 | 0 | 300092 | NO as-is |
| P1_CONSERVATIVE_REDUCED/C_INTERMEDIATE_SCENARIO | 255.724 GB | 32.11% | 10 | 72 | 610 | capacity fits; unimplemented/conditional |
| P2_AGGRESSIVE_DEFENSIBLE/C_INTERMEDIATE_SCENARIO | 123.653 GB | 15.53% | 4 | 36 | 204 | capacity fits; unimplemented/conditional |
| P0_CURRENT_MAXIMAL/A_MAX_DURATION_SCENARIO | 5.8256 PB | 731539.81% | 600183 | 0 | 600183 | NO as-is |
| P1_CONSERVATIVE_REDUCED/A_MAX_DURATION_SCENARIO | 395.183 GB | 49.62% | 14 | 112 | 1010 | capacity fits; unimplemented/conditional |
| P2_AGGRESSIVE_DEFENSIBLE/A_MAX_DURATION_SCENARIO | 201.538 GB | 25.31% | 6 | 56 | 304 | capacity fits; unimplemented/conditional |

At maximum P1 retained allocation:

| component | primary bytes |
|---|---|
| every_step_scalar_norm_ledger_log_bytes | 76.516 GB |
| full_step_audit_bytes | 180.389 GB |
| selected_outer_bundle_bytes | 120.259 GB |
| field_snapshot_bytes | 16.945 GB |
| fixed_provenance_bytes | 1.074 GB |

P1 max全raw step coverage=14/600183=0.002333%、selected bundle112、raw record slots=22,582。すべての684,808,803stage eventsをonlineでcheckしながら、raw retained coverageは限定されることを明示。P2 fullstep6、bundle56、field304。

Current free 796.352 GBの50% retention ceiling候補=398.176 GB、70%比較=557.446 GB。P1 retain約395GBは50%内ですがheadroomは約3GBだけ。scratch16GiBを別計上したpeak 412.362 GBに対してoverall55%候補=437.993 GBを提案し、45%をOS/otherstudies/uncertaintyへ残します。予算は採用せずdecision supportのみ。ConditionalCo0.125最大は追加260.818 GB、3series peak673.180 GBで50/55/70%候補を超えるため、trigger後の容量を別途解決せずRUN-readyにしません。

## 16. Scientific information retained/lost

| claim | P0 | P1 | P2 | condition/loss |
|---|---|---|---|---|
| primary Co sensitivity | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| registered arrival decisions | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| global mass behavior | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| global energy behavior | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| rho synchronization | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| selected evaluator audit | YES | CONDITIONAL | CONDITIONAL | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| thesis transient figures | YES | PARTIAL | PARTIAL | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| all final scalar conclusions from retained histories | YES | YES | YES | After proposed online/encoder/sparse-replay validation; every relevant scalar/norm/decision saved. Figures only at retained actual times; no independent all-step raw reassembly. |
| independent offline replay of every native assembly | YES | NO | NO | Not a primary claim of this study; particle readiness remains NO even for P0. |
| arbitrary post-hoc field-based QoIs at every step | YES | NO | NO | Not a primary claim of this study; particle readiness remains NO even for P0. |
| dense flow history suitable for particle forcing | PARTIAL | NO | NO | Not a primary claim of this study; particle readiness remains NO even for P0. |

Safe to sample: fullfields/profiles/local defect maps/selected fullraw audit。Safe selected-only: native coeff/source/BC/current-old arrays、full24outer playback at registered epochs。Safe discard after validated online reduction: nonselected raw fullstage arrays、exact duplicate states/immutable blobs。MUST_KEEP_EVERY_STEP: allregistered primary/state/arrival/scalar histories、every-relevant-stage mass/energy terms/norms/sync/reference/global changes、inner solve/certificate outcomes、stage health/epoch commitments、failure events。Raw logはcomplete。復元不能な証拠を残したと主張しません。

## 17. Thesis implications

P1はstartup t*=0,.001,.002,.005,.01,.02,.05、evolution .1,.2,.3,.5,1,1.5とactual arrival/final3windowsでTcontours、Uvectors/streamlines、Nu profilesを作る時刻候補。時刻は実際のafter-crossing native timeとcaptionに書く。Flow plume onsetが候補時刻の間に起きた場合、scalarからfieldsを生成しない；retained .005 snapshotsの分解能限界を明記。P2の.02ではcirculation/plumeの細部を見逃すリスクが高まる。futureparticle studiesの初期flow参考にはselectedfields/selectedprofilesが有用ですが、dynamic coupling forcing historyとして十分とは言わずPARTICLE_COUPLING_READY=NO。

## 18. Resource feasibility

| resource | current/recommended assessment | grade | remaining condition |
|---|---|---|---|
| STORAGE | P0 infeasible; P1 primary planning peak≈412GB fits796GB free | CRITICAL current | v1.3 packed caps+quota; conditionalthird≈0.68TB needs separate budget |
| COMPUTE | ~87million fv calls primary / ~101million scalar component calls | HIGH/UNRESOLVED | serial runtime unknown; steady-cost what-if not guarantee |
| I/O | P0≈2.05billion fsync calls; chunk candidates drastically reduce | HIGH/UNRESOLVED | online native reduction,packed encoding and crash semantics validated |
| MEMORY | fullstep JSON ring170–341GB impossible; packed bounded≈1.36GB buffer proposed | MEDIUM/UNRESOLVED | target live matrix/encoder/RSS estimate not measured;8GiB total budget proposed |

Serial support is explicit: current observer global sink/serial manifests and matrix coupled-patch STOP are notMPI-ready。24logical CPUsを24倍速度として使わない。Parallel support NOT_VALIDATED、別task/qualification無しにparallel launchしない。Compute materialでも24outer/linear tolerance/certificateを本reviewで変更せず、U01 revision necessityはUNRESOLVED。

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
ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_FEASIBILITY_REVIEW = COMPLETE
CURRENT_DIAGNOSTIC_CONTRACT_VERSION = 1.2
CURRENT_DIAGNOSTIC_CONTRACT_HASH_VERIFIED = YES
CURRENT_DIAGNOSTIC_CONTRACT_SHA256 = 7e95d4078433ff9e96527dd37430c2519cd1479ccc581e84f64bc94762af08dd
CURRENT_FREE_STORAGE_BYTES = 796351639552
CURRENT_FREE_STORAGE_TB = 0.796351639552
CURRENT_PRIMARY_STORAGE_ESTIMATE_BYTES = 5825629244755728
CURRENT_PRIMARY_STORAGE_ESTIMATE_PB = 5.825629244755728
CURRENT_PRIMARY_STORAGE_FEASIBLE = NO
CURRENT_POLICY_DOMINANT_STORAGE_SOURCE = PRESSURE_CORRECTOR_FIELD_STATE_AND_MATRIX_COPIES
FULL_FIELDS_EVERY_STEP_SCIENTIFICALLY_REQUIRED = NO
FULL_MATRIX_EVERY_STEP_SCIENTIFICALLY_REQUIRED = NO
EVERY_STEP_PRIMARY_SCALARS_REQUIRED = YES
EVERY_STEP_GLOBAL_MASS_ENERGY_REQUIRED = YES
SELECTED_RAW_MATRIX_AUDIT_SCIENTIFICALLY_SUFFICIENT = CONDITIONAL
ONLINE_REDUCTION_WITH_SELECTED_RAW_AUDIT_DEFENSIBLE = CONDITIONAL
RECOMMENDED_EVIDENCE_POLICY = P1_CONSERVATIVE_REDUCED
RECOMMENDED_STORAGE_ESTIMATE_BYTES = 412362440192
RECOMMENDED_STORAGE_ESTIMATE_TB = 0.412362440192
RECOMMENDED_STORAGE_FRACTION_OF_FREE = 0.5178145177474375
STORAGE_FEASIBILITY = FEASIBLE
COMPUTE_FEASIBILITY = UNRESOLVED
IO_FEASIBILITY = UNRESOLVED
MEMORY_FEASIBILITY = UNRESOLVED
SERIAL_ONLY_RESOURCE_RISK = HIGH
RESOURCE_POLICY_REVISION_REQUIRED = YES
U01_REVISION_REQUIRED = UNRESOLVED
U02_REVISION_REQUIRED = NO
U03_REVISION_REQUIRED = NO
U04_REVISION_REQUIRED = YES
EVIDENCE_CADENCE_REVISION_REQUIRED = YES
DIAGNOSTIC_CONTRACT_V1_3_REQUIRED = YES
DIAGNOSTIC_TRANSIENT_SCIENTIFICALLY_ALLOWED = YES
DIAGNOSTIC_TRANSIENT_TECHNICALLY_READY = YES
DIAGNOSTIC_TRANSIENT_RESOURCE_READY = NO
FORMAL_GATE_J_CURRENTLY_ALLOWED = NO
FORMAL_GATE_J_EXECUTED = NO
GRID_INDEPENDENT_TRANSIENT_CLAIM_ALLOWED = NO
DOWNSTREAM_TRANSIENT_READY = NO
PARTICLE_COUPLING_READY = NO
SOLVER_EXECUTED = NO
PRODUCTION_SOLVER_EXECUTED = NO
CFD_TRANSIENT_EXECUTED = NO
CASE_GENERATED = NO
MESH_GENERATED = NO
INITIALIZATION_EXECUTED = NO
DIAGNOSTIC_CONTRACT_VERSION = 1.2
DIAGNOSTIC_CONTRACT_CHANGED = NO
U01_CHANGED = NO
U02_CHANGED = NO
U03_CHANGED = NO
U04_CHANGED = NO
FORMAL_CRITERIA_CHANGED = NO
HISTORICAL_STATUS_CHANGED = NO
FORMAL_GATE_J_PASS = NOT_EVALUATED
BENCHMARK_CORE_PASS = NO
ROUTE_A_CHARACTERIZED = NO
ALL_ROUTE_A_GATE_F = FAIL
ALL_RA_NEEDS_320 = YES
PARALLEL_DIAGNOSTIC_SUPPORT = NOT_VALIDATED
NEXT_SINGLE_TASK = PREPARE_ROUTE_A_DIAGNOSTIC_TRANSIENT_RESOURCE_REVISION
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
