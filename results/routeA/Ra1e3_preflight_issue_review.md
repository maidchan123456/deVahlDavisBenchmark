# Route A Ra1e3 preflight issue review

2026-10-04（Asia/Tokyo）、HEAD `20cdaf034c83e64bd8d87f901eb63aa663556e87`。**REVIEW COMPLETE / EVALUATOR_FALSE_POSITIVE / technically ready YES**。

旧 `analyze_case.py:541` のcase-insensitive regex `Floating point exception` は正常起動行 `sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).` に一致する。A-COND/A-SMOKE先頭30行で実際に再現した。Ra1e3のsolverは未実行で、このSTOPをsolver/model/divergence/Gate D numerical failureや実FPEの証拠とはしない。必要範囲内に実FPE例はなく、`REAL_FPE_REPOSITORY_EXAMPLE = NOT_AVAILABLE`。

`classify_health_lines` を追加し、strip後のfullmatchで既知正常bannerのみFPEから除外した。fatal/NaN/Inf regexとaggregate ORは維持。他のhealth/divergence/field/provenance検査は既存Gate Dのまま。変更を正規化したASTは旧版と一致し、数値helper/parserには変更がない。

synthetic fixtureはparser検証用であり、CFD evidenceではない。入力・期待値・実測flagは [review JSON](Ra1e3_preflight_issue_review.json) の `validation.fixtures` に保存した。

| Fixture | Result |
|---|---|
| normal_banner_fragment | PASS |
| normal_openfoam_banner | PASS |
| normal_banner_whitespace_case | PASS |
| true_fpe_standalone | PASS |
| true_fpe_shell | PASS |
| true_fpe_openfoam | PASS |
| banner_then_true_fpe | PASS |
| banner_with_event_suffix | PASS |
| unknown_trapping_context | PASS |
| fatal_error | PASS |
| fatal_io_error | PASS |
| nan | PASS |
| inf | PASS |
| normal_log | PASS |
| banner_then_nan | PASS |

| Dry case | Banner | FPE | Health＋numerical | v1.0 numerical result |
|---|---|---|---|---|
| A-COND | YES | NO | PASS | 完全一致 |
| A-SMOKE | YES | NO | PASS | 完全一致 |

各logは `head -n 30` と `tail -n 4000` だけ読んだ。中間は未検査で、全log無障害の新証明ではない。末尾Endを確認したが新process exit codeは存在しない。wall monitorと20 velocity samplesで[2801,3000]を再評価し、Rwin・Initial residual・hot Nu・exact heat slopeはv1.0 dry出力と完全一致。main writerは実行していない。formal result/statusは書き換えていない。

保護対象90ファイルは前後hash一致（v1.0三ファイル、accepted fields/results、A-COND/A-SMOKE inputs/monitors/results、template/数値辞書、Route B既存証拠、STOP四成果物を含む）。リストはJSONの `protected_before_and_after_sha256`。scope外のsource/log再監査はしていない。

[Amendment 001](../../docs/routeA_execution_contract_amendment_001.md) と [effective v1.1](../../docs/routeA_execution_contract_v1.1.md) を別ファイルとして凍結した。v1.0は不変。現行hash guardのanalyzer値は新digest。旧値は明示的なhistorical recordにのみ残す。

attempt 001の元STOP四成果物は不変で、履歴の意味は `STOPPED_PRE_SOLVER_EVALUATOR_FALSE_POSITIVE`。次回はattempt 002、batch output `results/routeA/attempts/attempt_002/`。solver/case/meshなしで終了し、新しいユーザー実行指示を待つ。Git add/commit/pushはしていない。

```text
ROUTE_A_RA1E3_ISSUE_REVIEW = COMPLETE
ISSUE_CLASS = EVALUATOR_FALSE_POSITIVE
DIRECT_CAUSE = Case-insensitive regex Floating point exception matches the normal sigFpe trapping banner.
NORMAL_BANNER_FALSE_POSITIVE_CONFIRMED = YES
ANALYZER_FIX_APPLIED = YES
ANALYZER_FIX_SCOPE = FPE_CLASSIFIER_ONLY
OLD_ANALYZER_SHA256 = f63d2d958bdc48ed21519dbb0a87daf0f5f4fc99ba8c84b18290809d0dcd9783
NEW_ANALYZER_SHA256 = 327761f2b20d86ef8a3a924c64e46bd63da7b11e7a88ba7d74ccfaf232ddbac9
NORMAL_BANNER_TEST = PASS
TRUE_FPE_FIXTURE_TEST = PASS
FATAL_FIXTURE_TEST = PASS
NONFINITE_FIXTURE_TEST = PASS
A_COND_DRY_VALIDATION = PASS
A_SMOKE_DRY_VALIDATION = PASS
ORIGINAL_CONTRACT_V1_0_UNCHANGED = YES
ORIGINAL_CONTRACT_SHA256 = 33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936
CONTRACT_AMENDMENT_CREATED = YES
CONTRACT_AMENDMENT_ID = Route A Execution Contract Amendment 001
EFFECTIVE_CONTRACT_VERSION = 1.1
EFFECTIVE_CONTRACT_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
FORMAL_CRITERIA_CHANGED = NO
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
EXISTING_RESULTS_RECLASSIFIED = NO
ROUTE_B_MODIFIED = NO
SOLVER_EXECUTED = NO
CASE_CREATED = NO
MESH_GENERATED = NO
RA1E3_TRIO_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RERUN_ROUTE_A_RA1E3_TRIO
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
REAL_FPE_REPOSITORY_EXAMPLE = NOT_AVAILABLE
```
