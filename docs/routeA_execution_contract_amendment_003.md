# Route A Execution Contract Amendment 003

2026-10-04（Asia/Tokyo）。Parent v1.2 → effective v1.3。HEAD `f96aa2f7945ed84c8517baf084c18f0a22fd18f7`。

分類 `CANONICAL_ANALYZER_EVALUATION_ORDER_BUG`。paper comparisonが4097点centreline extremaの計算前にreferenceのUmax等を参照した。 velocity dataは存在し、solver/physics/Gate D failureではない。

paper comparisonを既存4097点centreline extrema計算の後へ移し、calculatedにUmax/Umax_Z/Wmax/Wmax_Xを追加。required reference keysのsubset guardを比較前に実施し、欠落はPAPER_COMPARISON_CALCULATED_KEY_MISSINGというValueErrorにする。Nu_bar_1 special handling、paper_differenceと既存key.endswith(_Z) dispatch、全数値定義は保持。

```text
PARENT_V1_2_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
OLD_ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
NEW_ANALYZER_SHA256 = e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac
AMENDMENT_003_JSON_SHA256 = c34d29178c7d6193f44efbfeb255855a8b82c62a7874201411a7de37fdbb92f7
```

5 unit test PASS。6 required numerical helpersとpaper_differenceの旧／新出力は同一。変更を正規化したASTも同一。sealed end_3000のchecksum、native inputs/fields/log/monitorは不変。

solverなしでbyte-identical patched analyzer/helper/reference copiesを別canonical workspaceで実行しexit 0。canonical metricsと4 CSV、paper comparisonが完成。主要8 QoIは旧diagnosticと完全一致、local quartic値の最大差は4.21884749e-15で浮動小数点roundoff範囲。

POST_FIX_REEVALUATION_OF_ATTEMPT_003_CHECKPOINTとしてformal Gate D PASS。旧actual exit/health/runtime/Gate A/OQ-02と不変のfield/input hashesを再照合し、新canonical metricsの数値成分と合わせた結果。attempt 003自身のSTOP/computed NO/accepted NO/Gate D NOT_EVALUATEDとraw sealは変更しない。

formal criteria、numerics、physics、reference、solver結果は不変。今回solver/continuation/medium/fine生成なし。今回ユーザー依頼がorder/guard修正・再解析・別所有のformal評価・Amendment 003/v1.3を明示的に許可する。詳細は [JSON](routeA_execution_contract_amendment_003.json)。

次回attempt 004のcoarseはSKIP_SOLVER_AND_ACCEPT_3000。hash/reanalysis/native checkpoint検証後、新execution stateへaccepted reuseを記録してmedium→fineへ進む。今回は実行せず、ユーザーの新しい実行指示を待つ。
