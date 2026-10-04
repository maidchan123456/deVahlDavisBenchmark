# Route A execution contract v1.1

2026-10-04（Asia/Tokyo）。**FROZEN / Ra1e3 trio technically ready YES**。実行は次のユーザー指示を待つ。今回はsolver/case/meshなし。

[effective JSON](routeA_execution_contract_v1.1.json) はv1.0の全契約snapshotに [Amendment 001](routeA_execution_contract_amendment_001.md) を適用したもの。数値条件・モデル・Gate定義は同じで、FPE classifierの実装hashと必要なversion/artifact/attempt metadataだけを更新した。

```text
EFFECTIVE_CONTRACT_VERSION = 1.1
EFFECTIVE_CONTRACT_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
NEW_ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
PARENT_V1_0_CONTRACT_SHA256 = 33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936
AMENDMENT_JSON_SHA256 = 63769f59ab7e5ed49115120e4c34326795fc40a8413d07e6086446af3be2b352
```

digestは保存済みJSON bytesに対するSHA-256。自己参照を避け本書に保存する。次回case生成前にeffective JSONを上記digestと照合し、JSONのimplementation/template/caps hashを照合する。別途parent/amendmentのdigestも確認する。違えばSTOP。**現行execution-contract digestはこのv1.1のみ**。v1.0の旧analyzer hashは歴史記録で、現行実行のguardに使わない。

Gate Dの論理は以下のまま。

```text
NORMAL_EXIT AND NO_FATAL_OR_NAN AND INPUT_PROVENANCE_PASS
AND QOI_RWIN_PASS AND RESIDUAL_PASS AND HEAT_TREND_PASS
```

| 固定項目 | 値 |
|---|---|
| residual | Ux/Uy/e/p_rgh 最終Initial residual ≤ 1e-7 |
| Rwin | hot-only Nu_bar_0/Umax/Wmax 各≤5e-4、scale=1 |
| window | [N-199,N] inclusive、200反復 |
| cadence | wall/residual 1、velocity 10、各200/20 samples |
| heat trend | 元Q decimal tokenによるexact rational OLS slope≤0 |
| initial / continuation / cap | 3000 / 3000 / 30000 |
| numerical evaluator version | 1.0、数値helperのversionラベルも維持 |
| F/G | NON_BLOCKING_WITH_DOCUMENTED_LIMITATION、正式閾値維持 |
| retry/tuning/320/post-cap | 自動実施不可 |

OpenFOAM Foundation v13、foamRun/fluid、steady SIMPLE、既存Boussinesq/laminar Stokes/Fourier、BC/物性/scheme/tolerance/relaxationはJSONの `frozen_model` とtemplate hashで固定する。全区間health/actual exit code/field/provenance/mesh/OQ-02検査、COMPUTEDとACCEPTEDの区別、segment封印、診断定義はv1.0と同一。

既知の正常trapping bannerのみFPE判定から除外する。fatal/FPE/NaN/Infのevent検出と外部divergence検査は保持する。15 fixture PASS、A-COND/A-SMOKE bounded healthと数値dry PASS。数値結果はv1.0 dryと同一。これで既存結果を昇格しない。

attempt 001は `STOPPED_PRE_SOLVER_EVALUATOR_FALSE_POSITIVE` として元STOP artifactを保持。次回 `RERUN_ROUTE_A_RA1E3_TRIO` はattempt 002、順序coarse→medium→fine、batch出力は `results/routeA/attempts/attempt_002/`。case artifact rootと物理case IDは既存契約どおり。過去トップレベルbatch reportは上書きしない。

旧 [v1.0](routeA_execution_contract.md) は不変のhistorical artifact。新JSONの `historical_v1_0_*` は歴史記録で、現行guardは `implementation_sha256`。検証証拠は [issue review](../results/routeA/Ra1e3_preflight_issue_review.md)。
