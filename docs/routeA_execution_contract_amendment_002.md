# Route A Execution Contract Amendment 002

2026-10-04（Asia/Tokyo）。Parent v1.1 → effective v1.2。HEAD `64ee7b17537c679fc2514022d0ffcafbb9941b78`。

分類は `EXECUTION_CHECKER_EVIDENCE_COLLECTION_FALSE_NEGATIVE`。直接原因：Selecting/Build/SIMPLE行だけのcollectorが複数行thermo辞書を落とし、heRhoThermoをfalse MISSINGと判定した。

実行実体は `/tmp/routeA_attempt002_runner.py`、保存コピーは `results/routeA/attempts/attempt_002/execution_runner.py`。両者のhashは同じで、いずれも変更しない。runtime collection/comparisonだけを `Scripts/routeA/runtime_provenance.py` に切り出してcanonical化した。旧hashはrunner全体、新hashは抽出したcheckerのdigestである。

```text
PARENT_V1_1_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
OLD_CHECKER_SHA256 = 57425049622655ddc904c3ae1e70d5d8966b8b206a3b0650972fc4aeaa92b86d
NEW_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
AMENDMENT_002_JSON_SHA256 = a8b2d80647f491d0ee06e434604b5d9a49d2d8e7ce7b622cfa19548e5f1a56eb
```

actual selected thermo blockの7keyを構造化し、各項目とversion/build/fluid/laminar/Stokes/laminar/Fourier/SIMPLEをfrozen modelへexact照合する。key順序・空白・tabを許容する。不足はRUNTIME_EVIDENCE_MISSING、不一致／重複／複数blockはRUNTIME_MODEL_MISMATCHとしてFAIL。input/manifestをruntime evidenceの代用にしない。health・input provenance・OQ-02は別に必要。

required synthetic fixture 7件PASS、unit test 12 method（全15required fieldのmissing/wrong subtest含む）PASS。A-COND/A-SMOKE/attempt 002 coarse initの先頭120行でdry PASS。CFD result/statusは変更しない。

今回ユーザーのFIX_ROUTE_A_EXECUTION_ISSUE依頼sections 7–22に基づく変更。analyzer、generator、numerical criteria、physics、solver設定、既存結果分類は不変。primary/initialization solver、case/mesh生成は今回なし。保護対象186ファイルの前後hashは一致。

coarse reuse YES。input/template/Ra/Pr/mesh/checkMesh/clone/log/pre-primary seal一致、primary未実行でtime 0のみ。clone再実行は不要だが、attempt 003でcanonical verify_initialization.pyを実行しOQ-02 PASSを得てからprimaryへ進む。現在のOQ-02はNOT_EVALUATEDのまま。

詳細は [Amendment JSON](routeA_execution_contract_amendment_002.json)、現行guardは [v1.2](routeA_execution_contract_v1.2.md)。過去contractとattempt 002のSTOPは不変。
