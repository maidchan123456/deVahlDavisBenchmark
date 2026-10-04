# Route A execution contract v1.4

2026-10-04（Asia/Tokyo）。**FROZEN / Ra1e4 trio technically ready YES**。v1.0 + Amendments 001/002/003/004のfull effective snapshot。sole current guardは[JSON](routeA_execution_contract_v1.4.json)。旧versionはhistoricalとして不変。

```text
EFFECTIVE_CONTRACT_VERSION = 1.4
EFFECTIVE_CONTRACT_SHA256 = 2665b8a62211618ae531e7b8d42242e3d8f9ae469b95b634beab672c89b345d7
ANALYZER_SHA256 = e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed
RUNTIME_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
PARENT_V1_3_SHA256 = 227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1
AMENDMENT_004_JSON_SHA256 = 803befbe8a0fd9a6f396b4f33dee70bbaa692036b9238ac259b8277b48340c64
```

自己参照を避けJSON digestは本書に保存。実行前に全implementation/template/caps/reference、immutable parent/amendment chainと保存済みRa1e3/reanalysis証拠を照合。不一致ならSTOP。

唯一のanalyzer behavior変更はpaper position/scalar classification。POSITION_KEYSはUmax_Z/Wmax_X/Nu_hot_local_max_Z/Nu_hot_local_min_Z。他のscalarはrelative semantics。paper_difference自体、4097点速度、quartic local Nu、全QoI、Gate D/E/F/G基準は不変。

initial/continuation/cap=3000/3000/30000、Rwin≤5e-4、Ux/Uy/e/p_rgh最終Initial residual≤1e-7、inclusive 200 window、元decimal Qのexact rational OLS slope≤0を維持。physics・scheme・relaxation・correctorsはparentと一致。F/G FAILはNON_BLOCKING_WITH_DOCUMENTED_LIMITATION、automatic tuning/retry/320/post-cap extensionは禁止。

Ra1e3 attempt 004はCOMPLETE/accepted3、D各PASS/E診断PASS/F FAIL・needs_320 YES/G PASSをhistoricalとして保存。別所有POSITION_SEMANTICS_REEVALUATION_OF_ACCEPTED_RA1E3_TRIOにcorrected paper payloadを保存。既存report/json/csv/solver sealは不変。

次回task RUN_ROUTE_A_RA1E4_TRIO。新規formal A-Ra1e4-coarse→medium→fine、40²/80²/160²、Ra=10000、Pr=.71、concurrency=1。各caseでinput/hash→blockMesh→checkMesh→initialization/runtime/OQ-02/Gate A→primary。Ra1e3 coarse reuseはRa1e4には適用しない。予定batch root attempt_005はNOT_STARTED。今回はsolverなしで終了し、次のユーザー実行指示を待つ。

詳細は[Amendment 004](routeA_execution_contract_amendment_004.md)。
