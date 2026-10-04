# Route A analyzer issue review

**COMPLETE / CANONICAL_ANALYZER_EVALUATION_ORDER_BUG**。HEAD `f96aa2f7945ed84c8517baf084c18f0a22fd18f7` は指定値と一致。修正前v1.2/analyzer/runtime checker hash guardとsealed end_3000はPASS。

直接原因はpaper comparisonがvelocity extremaより先に構築され、referenceのUmax等をNu-only calculated辞書から参照したこと。比較blockを4097-point extremaの後へ移し、4 velocity keyを追加。subset guardで欠落をcontrolled evaluator ValueErrorにした。数値定義とpaper_difference、Nu_bar_1 referenceなしの扱いは維持。

5 unit tests（reference coverage、velocity先行、controlled missing Umax、Nu_bar_1、paper_difference semantics）はPASS。6 required numerical helpersとpaper_differenceの旧／新出力は同一。AST正規化比較も順序/key/guard以外同一。

同一bytesの修正版canonical source/helper/reference copiesを `post_fix_reanalysis/canonical_workspace/` に配置して、元case、sealed solver.log、segment-start 0を使用。source __file__ ROOTにより全出力は新workspaceに隔離した。exit code 0、metricsとlocal/section/centreline/convergence CSVが完成。主要成果物は [post_fix_reanalysis](post_fix_reanalysis/metrics.json) にも同一bytesで保存。既存solver/native dataはread-only。

| Canonical QoI | Value |
|---|---:|
| Nu_bar_cavity | 1.11885517318 |
| Nu_bar_0 | 1.11861212999 |
| Nu_bar_half | 1.11873791039 |
| Nu_bar_1 | 1.1186121761 |
| Umax | 3.6480784481 |
| Umax_Z | 0.8125 |
| Wmax | 3.68953716131 |
| Wmax_X | 0.1875 |
| Nu_hot_local_max | 1.51056348013 |
| Nu_hot_local_max_Z | 0.088578410338 |
| Nu_hot_local_min | 0.6898370869 |
| Nu_hot_local_min_Z | 1 |

主要8値はdiagnosticと完全一致。local quartic値の最大差4.21884749e-15はroundoff範囲。paper比較はreferenceの全non-empty keyで完成、Nu_bar_1はreference/error nullの既存special扱い。出力は実測結果で期待値へ強制していない。

**formal Gate D PASS**。actual exit 0＋End、全区間health、finite/positive fields、runtime/Gate A/OQ-02、input/mesh/field hashesを旧sealから再検証。新canonical monitorのRwin/residual/heat trendを合わせ、6 boolean全PASS。窓2801–3000、Nu Rwin=0、U/W Rwin≈3.8e-10、最大Initial residual≈1.18e-10、exact heat slope sign=0。詳細は [gate_D_status.json](post_fix_reanalysis/gate_D_status.json)。

所有はPOST_FIX_REEVALUATION_OF_ATTEMPT_003_CHECKPOINT。今回のpost-fix computed YES、next execution stateでacceptable YES。attempt 003のSTOP/computed NO/accepted NO/Gate D NOT_EVALUATEDとend_3000内の旧gate_D_status.jsonは不変。保護対象7060hash entriesは前後一致。baselineリストはpost_fix_reanalysis/protected_before_sha256.json。

[Amendment 003](../../../../docs/routeA_execution_contract_amendment_003.md) と [effective v1.3](../../../../docs/routeA_execution_contract_v1.3.md) を新規凍結。旧contract/A1/A2、reference、runtime checker、physics/numerics/criteria、solver結果は変更なし。

attempt 004はSKIP_SOLVER_AND_ACCEPT_3000。旧seal／native 3000／post-fix metrics/Gate Dのhashを確認し、新attempt rootへaccepted reuseを記録してmedium→fineへ進む。coarse再solver・3000→6000は不要。今回solver/case生成なし、attempt_004 rootも作成なし。

```text
ROUTE_A_ANALYZER_ISSUE_REVIEW = COMPLETE
ISSUE_CLASS = CANONICAL_ANALYZER_EVALUATION_ORDER_BUG
DIRECT_CAUSE = paper comparisonが4097点centreline extremaの計算前にreferenceのUmax等を参照した。
ANALYZER_FIX_APPLIED = YES
ANALYZER_FIX_SCOPE = PAPER_COMPARISON_ORDER_ONLY
OLD_ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
NEW_ANALYZER_SHA256 = e1f5da10349b997d858cc04802a04366a668e6af4cf51367569e198993e8e0ac
REFERENCE_KEY_COVERAGE_TEST = PASS
VELOCITY_KEY_ORDER_TEST = PASS
CONTROLLED_MISSING_KEY_TEST = PASS
PAPER_DIFFERENCE_REGRESSION_TEST = PASS
NUMERICAL_HELPER_REGRESSION = PASS
ATTEMPT_003_END_3000_SEAL_INTACT = YES
POST_FIX_CANONICAL_REANALYSIS = PASS
CANONICAL_QOI_MATCHES_DIAGNOSTIC = YES
PAPER_COMPARISON_COMPLETE = YES
COARSE_FORMAL_GATE_D = PASS
COARSE_GATE_D_FAILURE_COMPONENTS = NONE
COARSE_COMPUTED_AFTER_POST_FIX_REEVALUATION = YES
COARSE_ACCEPTABLE_FOR_NEXT_EXECUTION_STATE = YES
CONTRACT_AMENDMENT_003_CREATED = YES
PARENT_EFFECTIVE_CONTRACT_VERSION = 1.2
PARENT_EFFECTIVE_CONTRACT_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
EFFECTIVE_CONTRACT_VERSION = 1.3
EFFECTIVE_CONTRACT_SHA256 = 227414aaff22a0f37bed234f6b26c0a296d18f592da641aa55f1c4a4538ff3f1
FORMAL_CRITERIA_CHANGED = NO
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
REFERENCE_DATA_CHANGED = NO
SOLVER_RESULT_CHANGED = NO
ATTEMPT_003_HISTORY_PRESERVED = YES
PRIMARY_SOLVER_EXECUTED = NO
CONTINUATION_EXECUTED = NO
MEDIUM_CASE_CREATED = NO
FINE_CASE_CREATED = NO
COARSE_ATTEMPT_004_ACTION = SKIP_SOLVER_AND_ACCEPT_3000
ATTEMPT_004_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RERUN_ROUTE_A_RA1E3_TRIO_ATTEMPT_004
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
