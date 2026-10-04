# Route A execution checker issue review

**COMPLETE / EXECUTION_CHECKER_EVIDENCE_COLLECTION_FALSE_NEGATIVE**。HEAD `64ee7b17537c679fc2514022d0ffcafbb9941b78` は指定値と一致。

実行実体 `/tmp/routeA_attempt002_runner.py` とattempt 002保存コピーのhashは一致。Selecting/Build/SIMPLE行限定の収集がthermo辞書を落とし、false MISSINGを起こした。旧runnerとSTOP reportは変更していない。

canonical checker [runtime_provenance.py](../../../../Scripts/routeA/runtime_provenance.py) はthermo 7keyをcomplete blockから収集し、frozen runtime modelと項目別に比較する。MISSINGとMISMATCHを区別、順序/空白変更を許容。analyzerや数値evaluatorは変更しない。

required fixture 7件、unit test 12 method（15 field missing/wrong subtest含む）は全PASS。fixture入力と結果は [review JSON](execution_checker_issue_review.json)。A-COND、A-SMOKE、attempt 002 coarse initは各先頭120行のread-only runtime dry checkがPASS。既存logを正規化／変更せず、新solverは実行しなかった。

旧checker SHA `57425049622655ddc904c3ae1e70d5d8966b8b206a3b0650972fc4aeaa92b86d`、新checker SHA `5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a`。旧digestはrunner全体、新digestは抽出したruntime checker。新checkerはv1.2のimplementation_sha256に登録した。[Amendment 002](../../../../docs/routeA_execution_contract_amendment_002.md) と [v1.2](../../../../docs/routeA_execution_contract_v1.2.md) を新規作成、元v1.0/v1.1/A1は不変。

coarse reuse YES。generated raw/formal/seal input hashes、template substitutions、Ra/Pr、mesh/checkMesh、clone time-0 dump/log、pre-primary sealが一致。primary caseのtime directoryは0だけで、primary log/segment/evolved fieldsはない。保護対象186ファイルは前後hash一致。

OQ-02はNOT_EVALUATEDのまま。attempt 003開始時にverify_initialization.pyで既存cloneを検証し、PASSを確認する必要がある。cloneの再solver実行は不要：成功したconstructor dump/logがそのまま残るため。新verification/progress outputはattempt_003へ保存し、旧manifest/status/sealは上書きしない。

attempt 003は技術的準備完了。次はRERUN_ROUTE_A_RA1E3_TRIO_ATTEMPT_003。今回はprimary/initialization solver実行、case/mesh生成なし。medium/fine、attempt_003 rootも作っていない。ユーザーの新しい実行指示を待つ。

```text
ROUTE_A_EXECUTION_ISSUE_REVIEW = COMPLETE
ISSUE_CLASS = EXECUTION_CHECKER_EVIDENCE_COLLECTION_FALSE_NEGATIVE
DIRECT_CAUSE = Selecting/Build/SIMPLE行だけのcollectorが複数行thermo辞書を落とし、heRhoThermoをfalse MISSINGと判定した。
EXECUTION_CHECKER_PATH = /home/mirai/OpenFOAM/mirai-13/run/deVahlDavisBenchmark/Scripts/routeA/runtime_provenance.py
ORIGINAL_EXECUTION_CHECKER_PATH = /tmp/routeA_attempt002_runner.py
EXECUTION_CHECKER_CANONICALIZED = YES
CHECKER_FIX_APPLIED = YES
CHECKER_FIX_SCOPE = RUNTIME_THERMO_EVIDENCE_COLLECTION_ONLY
OLD_CHECKER_SHA256 = 57425049622655ddc904c3ae1e70d5d8966b8b206a3b0650972fc4aeaa92b86d
NEW_CHECKER_SHA256 = 5055345c7e64758a4f902c81219e2dda2e5b9cdec22c3f22fc8297bbc1bb9e5a
MULTILINE_THERMO_FIXTURE = PASS
THERMO_MISSING_FIXTURE = PASS
THERMO_MISMATCH_FIXTURE = PASS
WHITESPACE_ORDER_VARIATION_FIXTURE = PASS
WRONG_STRESS_MODEL_FIXTURE = PASS
A_COND_RUNTIME_DRY_CHECK = PASS
A_SMOKE_RUNTIME_DRY_CHECK = PASS
ATTEMPT_002_COARSE_RUNTIME_DRY_CHECK = PASS
ANALYZER_CHANGED = NO
FORMAL_CRITERIA_CHANGED = NO
NUMERICAL_SETTINGS_CHANGED = NO
PHYSICAL_MODEL_CHANGED = NO
EXISTING_RESULTS_RECLASSIFIED = NO
CONTRACT_AMENDMENT_002_CREATED = YES
PARENT_EFFECTIVE_CONTRACT_VERSION = 1.1
PARENT_EFFECTIVE_CONTRACT_SHA256 = dbd70320ceb3f20e4455c5d67d24b3dae40d2616a832438b23faa99c6b0b892b
EFFECTIVE_CONTRACT_VERSION = 1.2
EFFECTIVE_CONTRACT_SHA256 = 7db8d5b8217f009243cb884e291f3d7a09a699b4fe35073792cbaedb5bf7b7fe
ATTEMPT_002_HISTORY_PRESERVED = YES
ATTEMPT_002_COARSE_PRE_PRIMARY_SEAL_INTACT = YES
ATTEMPT_002_COARSE_CASE_REUSABLE = YES
ATTEMPT_002_COARSE_CASE_REUSE_REASON = Input/template/Ra/Pr/mesh/clone/log/seal一致、primary未開始・time 0のみ、physics/numerics不変。
OQ02_STILL_REQUIRED_BEFORE_PRIMARY = YES
PRIMARY_SOLVER_EXECUTED = NO
MEDIUM_CASE_CREATED = NO
FINE_CASE_CREATED = NO
ATTEMPT_003_TECHNICALLY_READY = YES
NEXT_SINGLE_TASK = RERUN_ROUTE_A_RA1E3_TRIO_ATTEMPT_003
RECOMMENDED_REASONING_MODEL_FOR_NEXT_TASK = gpt-6.1-sol / medium
USER_DECISION_REQUIRED = YES
```
