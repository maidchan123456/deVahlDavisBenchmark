# Route B remaining matrix batch

Initial HEAD: `382b1f1bc55256aa1a74bf2dd0d51095798dc1f8`.

| Case | Grid | Final iteration | Gate D | Gate E | Gate F | needs_320 |
|---|---|---:|---|---|---|---|
| B-Ra1e5-medium | 80² | 9000 | PASS | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| B-Ra1e5-fine | 160² | 12000 | PASS | PASS | FAIL | True |
| B-Ra1e6-coarse | 40² | 24000 | FAIL | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| B-Ra1e6-medium | 80² | None | NOT_RUN | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| B-Ra1e6-fine | 160² | None | NOT_RUN | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |

Accepted: 9/12. Full matrix complete: NO.
Batch stop reason: B-Ra1e6-coarse: CONVERGENCE_NOT_REACHED at existing cap 24000.
Next action: FIX_STOPPED_CASE.
Gate G review remains frozen; numerical criteria unchanged. No 320 or microcase solver executed.
