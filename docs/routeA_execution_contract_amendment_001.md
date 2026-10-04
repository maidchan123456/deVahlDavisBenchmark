# Route A Execution Contract Amendment 001

2026-10-04（Asia/Tokyo）。Parent v1.0 → effective v1.1。HEAD `20cdaf034c83e64bd8d87f901eb63aa663556e87`。

正常起動bannerの `floating point exception` が旧regexに一致するため、preflightはcase/mesh/solver前にSTOPした。分類は **EVALUATOR_FALSE_POSITIVE**。今回の依頼文がclassifier修正・amendment作成を明示的に許可している。

変更ファイルは `Scripts/routeA/analyze_case.py` のみ。`classify_health_lines` で既知bannerをstrip後のfullmatchに限定してFPE判定から除外する。standalone `floating point exception trapping` も既知文言として除外する。他の行の `Floating point exception` 検出、fatal regex、NaN/Inf regex、health flagのORは保持する。bannerと実FPEが別行／同じ行に共存すれば検出する。Gate Dの外部divergence/field/provenance検査は引き続き必要。

```text
PARENT_CONTRACT_SHA256 = 33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936
OLD_ANALYZER_SHA256 = f63d2d958bdc48ed21519dbb0a87daf0f5f4fc99ba8c84b18290809d0dcd9783
NEW_ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
AMENDMENT_JSON_SHA256 = 63769f59ab7e5ed49115120e4c34326795fc40a8413d07e6086446af3be2b352
```

15件のsynthetic parser fixtureは全PASS。実FPEのrepository例は必要範囲内で得られていないため `REAL_FPE_REPOSITORY_EXAMPLE = NOT_AVAILABLE`。fixtureはCFD結果ではない。

A-COND/A-SMOKEは各logの先頭30行＋末尾4000行で正常bannerあり、FPE/fatal/NaN/Infなし。窓2801–3000の数値helper評価は両方PASS、v1.0のdry評価と完全一致。log中間は今回検査していない。analyzer main writerは実行していない。

修正箇所以外のASTは同一。保護対象90ファイルのhashは前後一致。formal numerical criteria、物理モデル、solver設定、caps/continuation、Gate F/G policy、既存結果分類はすべて変更なし。solver/case/meshは今回なし。v1.0三ファイルとattempt 001のSTOP証拠はそのまま保持する。

次回はattempt 002として、batch reportを `results/routeA/attempts/attempt_002/` に保存する。既存のトップレベルSTOP report/matrix/comparisonは上書きしない。ユーザーの新しい実行指示が必要。

機械可読の詳細・fixture入力・dry結果・許可元・保護hashは [amendment JSON](routeA_execution_contract_amendment_001.json)。現行execution guardは [v1.1](routeA_execution_contract_v1.1.md) のdigestを使用する。
