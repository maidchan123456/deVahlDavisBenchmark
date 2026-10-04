# Route A execution contract v1.2

2026-10-04（Asia/Tokyo）。**FROZEN / attempt 003 technically ready YES**。今回は実行せず、新しいユーザー実行指示を待つ。

[effective JSON](routeA_execution_contract_v1.2.json) はv1.0 + Amendment 001 + [Amendment 002](routeA_execution_contract_amendment_002.md) のfull snapshot。数値契約は不変で、runtime checkerとそのhash、必要なversion/artifact/reuse metadataを追加した。

```text
EFFECTIVE_CONTRACT_VERSION = 1.2
EFFECTIVE_CONTRACT_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
EXECUTION_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
PARENT_V1_1_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
AMENDMENT_002_JSON_SHA256 = a8b2d80647f491d0ee06e434604b5d9a49d2d8e7ce7b622cfa19548e5f1a56eb
```

digestは保存済みJSON bytesのSHA-256で、自己参照を避け本書に保存。**sole current execution-contract guardはv1.2**。実行前にこのdigestとimplementation_sha256（runtime checkerを含む）、template、capsを照合し、parent/amendment chainも検証。不一致ならsolver開始前STOP。旧v1.0/v1.1とAmendment 001はhistorical artifactとして保持する。

runtime判定にはcanonical `Scripts/routeA/runtime_provenance.py` を使用する。例：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 Scripts/routeA/runtime_provenance.py --log LOG --contract docs/routeA_execution_contract_v1.2.json --max-lines 120
```

stdout JSON、exit 0 PASS／1 FAIL。actual runtime dictionaryとmodel linesを収集し、MISSING/MISMATCHを区別する。input provenance、health、actual process exit、field検査、OQ-02を代替しない。historical attempt 002 runnerのcollectorを再利用しない。120行内に証拠がなければSTOPしてreviewする。

| 数値条件 | 不変の値 |
|---|---|
| initial / continuation / cap | 3000 / 3000 / 30000 |
| residual | 最終Initial residual Ux/Uy/e/p_rgh ≤1e-7 |
| Rwin | hot Nu_bar_0/Umax/Wmax 各≤5e-4、scale=1 |
| window / cadence | inclusive 200反復、wall/residual 1、velocity 10 |
| heat trend | 元Q decimal tokens、exact rational OLS slope≤0 |
| Gate D | NORMAL_EXIT AND NO_FATAL_OR_NAN AND INPUT_PROVENANCE_PASS AND QOI_RWIN_PASS AND RESIDUAL_PASS AND HEAT_TREND_PASS |
| Gate F/G | 正式基準・NON_BLOCKING_WITH_DOCUMENTED_LIMITATION維持 |

physics/BC/solver/scheme/tolerance/relaxation/correctors、Nu・continuity/symmetry定義、COMPUTED/ACCEPTED論理、segment封印規則はeffective JSONにそのまま保持する。analyzerとAmendment 001 classifierは変更しない。

attempt 003 rootは `results/routeA/attempts/attempt_003/`、順序coarse→medium→fine、concurrency 1。coarseだけ登録済みreuse例外：既存case/mesh/cloneのprovenance再照合→canonical runtime check→既存cloneに対するverify_initialization.py→OQ-02 PASS→Gate A完了→primary 0→3000。clone再実行は不要（正常終了とtime-0 dumpのhash一致）。OQ-02は現在NOT_EVALUATEDで、今回昇格しない。

旧case/generated manifest、case_status.json、pre_primary_stop、clone、attempt 001/002 reportsを保持する。v1.2/attempt_003のreuse linkage、OQ-02 outputとprogress/statusは新attempt rootへ記録する。今後primary caseが進化しても旧sealは不変に保つ。medium/fineは次回新規生成し、今回作らない。

準備の証拠は [checker issue review](../results/routeA/attempts/attempt_002/execution_checker_issue_review.md)。
