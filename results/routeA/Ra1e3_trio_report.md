# Route A Ra1e3 trio execution report

2026-10-04（Asia/Tokyo）。開始HEAD: `0031c2c072b8f204a0de95fd06cb98ef7f39c8c6`（指定HEADと一致）。

**Overall: STOPPED — STOP_EVALUATOR_AMBIGUITY。** case生成・mesh生成・initialization/primary solver開始前に停止。契約を変更して3ケースを進める操作は行わなかった。

## Contract guard / execution state

authoritative JSON SHA-256は期待値 `33eb082f77f00b2330003ba8bafcb0438a24d7ec6b0bf456625741bfae63c936` と一致。generator/analyzer/template/initialization scripts/reference/capsの21件のhash guardはPASS。3 destinationは不存在を確認した。

shell環境はFoundation OpenFOAM-13、WM_PROJECT_VERSION=13、WM_PROJECT_DIR=/opt/openfoam13、WM_OPTIONS=linux64GccDPInt32Opt、foamRunの期待pathと一致。新規caseのruntime model/mesh/OQ-02は**NOT_RUN**。

| case | planned grid | created | computed | accepted | final iteration | Gate D |
|---|---|---|---|---|---|---|
| A-Ra1e3-coarse | 40×40×1 | NO | NO | NO | NONE | NOT_EVALUATED |
| A-Ra1e3-medium | 80×80×1 | NO | NO | NO | NONE | NOT_EVALUATED |
| A-Ra1e3-fine | 160×160×1 | NO | NO | NO | NONE | NOT_EVALUATED |

NOは今回未実行を意味する。既存A-COND/A-SMOKEのPASSやaccepted結果を取り消した意味ではない。

## Reproducible stop evidence

凍結済み `Scripts/routeA/analyze_case.py:541` のmain writerは次のregexでfatal_or_nanを保存する。

```python
FOAM FATAL (?:ERROR|IO ERROR)|Floating point exception|\bnan\b|\binf\b
```

既存canonical A-SMOKE logの最初30行だけを読み、同じregexを適用すると正常bannerに一致する。

```text
sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).
regex_match = floating point exception
canonical_fatal_or_nan_on_normal_banner = True
```

これはFPE trapping有効化の表示であり、FPE発生の証拠ではない。凍結main writerが通常起動を異常扱いするため、canonical health evidenceと実process healthが矛盾する。今回はユーザーの**evaluator failure / ambiguityではbatch STOP**を適用し、除外規則や別のhealth解釈を追加しなかった。

analyzer SHA-256は `f63d2d958bdc48ed21519dbb0a87daf0f5f4fc99ba8c84b18290809d0dcd9783` で、凍結contract内の値と一致。未追跡の変更やhash mismatchが原因ではなく、凍結した解析式自身の問題である。

前回dry validationはnumerical monitor / residual helperを確認したが、main writerのhealth expressionをstartup bannerへ適用する検査は含まなかった。このため前回READY宣言ではこのfalse positiveを見落としていた。

## QoIs / comparisons / group Gates

- 主QoI: 新しいRoute A値なし。matrix CSVの数値欄は空欄で保持し、ゼロを代入しない。
- paper comparison: NOT_EVALUATED。A–paperは今後もPRACTICAL_BENCHMARK_COMPARISON。
- A–B comparison: NOT_EVALUATED。対応するB baselineをread-onlyで必要部分だけ参照したが、Aが未実行なので差を計算しない。
- Gate F / needs_320 / Gate G: NOT_EVALUATED。新しいgrid値やfine fieldがないので判定しない。
- continuation、post-cap extension、retry、tuning、320、Gate H/J、粒子couplingは実施なし。

## Protection / next task

contract記録の保護78ファイルのhash不変を確認。contract Markdown/JSON/caps、analyzer、generator、template、既存minimal cases/results、B baseline metrics/full manifestも不変。今回の追加は次の4つの報告ファイルのみ。

- `results/routeA/Ra1e3_trio_report.md`
- `results/routeA/Ra1e3_trio_report.json`
- `results/routeA/Ra1e3_trio_matrix.csv`
- `results/routeA/Ra1e3_routeA_vs_routeB.csv`

**Ra1e4は開始不可。NEXT_SINGLE_TASK = REVIEW_ROUTE_A_RA1E3_ISSUE。** startup bannerのfalse positiveをreviewし、必要ならユーザー承認を記録したversioned amendmentで解析式と新contract hashを定義する。main health pathのdry検証・hash guardを終えるまではRa1e3を再開始しない。今回は修正／amendment／solver自動開始を行っていない。新しいGate閾値や研究課題は不要。

```text
ROUTE_A_RA1E3_TRIO = STOPPED
CONTRACT_HASH_VERIFIED = YES
A_RA1E3_COARSE_COMPUTED = NO
A_RA1E3_COARSE_ACCEPTED = NO
A_RA1E3_COARSE_FINAL_ITERATION = NONE
A_RA1E3_COARSE_GATE_D = NOT_EVALUATED
A_RA1E3_MEDIUM_COMPUTED = NO
A_RA1E3_MEDIUM_ACCEPTED = NO
A_RA1E3_MEDIUM_FINAL_ITERATION = NONE
A_RA1E3_MEDIUM_GATE_D = NOT_EVALUATED
A_RA1E3_FINE_COMPUTED = NO
A_RA1E3_FINE_ACCEPTED = NO
A_RA1E3_FINE_FINAL_ITERATION = NONE
A_RA1E3_FINE_GATE_D = NOT_EVALUATED
RA1E3_GATE_E_DIAGNOSTIC = NOT_EVALUATED
RA1E3_GATE_F = NOT_EVALUATED
RA1E3_NEEDS_320 = NOT_EVALUATED
RA1E3_GATE_G = NOT_EVALUATED
ROUTE_A_VS_ROUTE_B_COMPARISON = NOT_EVALUATED
FORMAL_CRITERIA_CHANGED = NO
SOLVER_TUNING_PERFORMED = NO
POST_CAP_EXTENSION_PERFORMED = NO
AUTOMATIC_320_PERFORMED = NO
ROUTE_B_MODIFIED = NO
NEXT_RA_READY = NO
NEXT_SINGLE_TASK = REVIEW_ROUTE_A_RA1E3_ISSUE
USER_DECISION_REQUIRED = YES
SOLVER_EXECUTED = NO
CASE_CREATED = NO
MESH_GENERATED = NO
STOP_REASON = STOP_EVALUATOR_AMBIGUITY
```

Git add/commit/pushなし。
