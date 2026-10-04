# Route A Execution Contract Amendment 004

2026-10-04（Asia/Tokyo）。parent v1.3 SHA-256 `227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1`。ユーザーtask FIX_ROUTE_A_PAPER_POSITION_SEMANTICSに基づく位置分類だけの修正。

原因はcanonical paper comparisonの`key.endswith("_Z")`。Wmax_Xがscalar-relative payloadになっていた。4つの明示POSITION_KEYS（Umax_Z、Wmax_X、Nu_hot_local_max_Z、Nu_hot_local_min_Z）へのmembershipへ変更し、paper_differenceの数式・scalar semantics・Nu_bar_1 handlingは維持。

analyzer old `e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac` → new `e6207e33ae2279e84786115ebfd912b170dcb23f220f1b1155314c723c54cfed`。15 tests PASS。7 helperの出力が完全一致し、分類変更を正規化した全ASTも一致。従来order testのobsolete suffix assertionだけを更新、旧source/testを別所有artifactへ保存。

3ケースをnative fields/log/monitor read-onlyでcanonical再解析。12 QoIと全非paper metrics、Gate D monitor、Wmax_X以外のpaper payloadが完全一致。Wmax_X calculated/referenceは不変、signed_position_difference/absolute_position_errorへ変更しrelative fieldsなし。Gate D各PASS、Gate E診断PASS、Gate F FAIL・needs_320 YES、Gate G PASSを保持。attempt 004の既存報告・CSV・sealは上書きなし。

Gate Eは元からabsolute coordinate differenceでPASS。基準・numerics・physics・reference・solver results・historical status変更なし。solver/continuation/case/mesh生成なし。全83200既存保護ファイルのhash不変。Route Bはread-only、既存A–B位置差CSVの整合PASS。

詳細とuser authorizationは[amendment JSON](routeA_execution_contract_amendment_004.json)。別所有再解析は[comparison check](../results/routeA/attempts/attempt_004/position_semantics_reanalysis/comparison_semantics_check.json)。effective v1.4は[JSON](routeA_execution_contract_v1.4.json)と[MD](routeA_execution_contract_v1.4.md)。Ra1e4実行には新しいユーザー指示が必要。
