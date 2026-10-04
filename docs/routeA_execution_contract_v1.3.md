# Route A execution contract v1.3

2026-10-04（Asia/Tokyo）。**FROZEN / attempt 004 technically ready YES**。v1.0 + Amendment 001 + Amendment 002 + [Amendment 003](routeA_execution_contract_amendment_003.md) の [full effective JSON](routeA_execution_contract_v1.3.json)。数値条件は不変。

```text
EFFECTIVE_CONTRACT_VERSION = 1.3
EFFECTIVE_CONTRACT_SHA256 = 227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1
ANALYZER_SHA256 = e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
PARENT_V1_2_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
AMENDMENT_003_JSON_SHA256 = c34d29178c7d6193f44efbfeb255855a8b82c62a7874201411a7de37fdbb92f7
```

digestは保存済みJSON bytesのSHA-256。自己参照を避け本書に保存。**sole current execution-contract guardはv1.3**。実行前にdigest、全implementation/template/caps/reference、parent/amendment chain、checkpoint/reanalysis hashesを検証し、不一致ならSTOP。旧contractとamendmentsはhistoricalとして不変に保持する。

| 不変の条件 | 値 |
|---|---|
| initial / continuation / cap | 3000 / 3000 / 30000 |
| residual | Ux/Uy/e/p_rgh 最終Initial residual ≤1e-7 |
| Rwin | hot Nu_bar_0/Umax/Wmax 各≤5e-4、scale=1 |
| window / cadence | inclusive 200反復、wall/residual 1、velocity 10 |
| heat trend | 元Q tokensでexact rational OLS slope≤0 |
| Gate D | NORMAL_EXIT AND NO_FATAL_OR_NAN AND INPUT_PROVENANCE_PASS AND QOI_RWIN_PASS AND RESIDUAL_PASS AND HEAT_TREND_PASS |
| F/G | 正式基準・NON_BLOCKING_WITH_DOCUMENTED_LIMITATION維持 |

model/physics/BC、linear solver tolerance/relTol/relaxation/correctors/schemes、Nu/velocity/local Nu/operator定義、runtime checker、Amendment 001 health、封印とCOMPUTED/ACCEPTED論理は同じ。analyzerはpaper比較の順序・完全key・controlled key guardのみ更新。

sealed coarse end_3000のpost-fix canonical再解析は正常終了し、formal Gate D PASS。これはPOST_FIX_REEVALUATION_OF_ATTEMPT_003_CHECKPOINTという別所有の結果で、attempt 003 reportとraw sealのSTOP/NOT_EVALUATEDを書き換えない。

**COARSE_ATTEMPT_004_ACTION = SKIP_SOLVER_AND_ACCEPT_3000**。次回root `results/routeA/attempts/attempt_004/` でnative 3000 fields、旧seal、新gate/metrics hashesを再検証し、accepted checkpoint reuseを新execution stateへ記録する。coarse再solver・continuationは不要。既存case/generated manifest/status/segment sealは不変に保持。medium→fineを新規生成して順次実行し、concurrency 1とする。medium/fineのmesh/initialization/runtime/OQ-02/Gate Aは通常どおり必要。

新canonical成果物は `results/routeA/attempts/attempt_003/post_fix_reanalysis/`。検証詳細は [analyzer review](../results/routeA/attempts/attempt_003/analyzer_issue_review.md)。今回はsolver/continuation/new case生成なし。次のユーザー実行指示を待つ。
