# B-Ra1e6-coarse residual checkpoint review

HEAD: `afd628193d4d649032784e98c02ae21a1e7a783f`. 24000 field/input provenance: PASS.

| Iteration | Ux | Uy | T | p_rgh |
|---:|---:|---:|---:|---:|
| 3000 | 1.6514081e-07 | 9.3189127e-08 | 4.7071178e-08 | 1.0265487e-06 |
| 6000 | 1.4472617e-07 | 8.4689486e-08 | 4.2748705e-08 | 8.8919409e-07 |
| 9000 | 1.4224696e-07 | 7.9874401e-08 | 3.7697723e-08 | 7.5798844e-07 |
| 12000 | 1.3829312e-07 | 7.4565105e-08 | 4.0746182e-08 | 8.0761082e-07 |
| 15000 | 1.5191256e-07 | 8.4534614e-08 | 4.1542629e-08 | 8.9307353e-07 |
| 18000 | 1.5431567e-07 | 8.1045322e-08 | 4.5067570e-08 | 9.3676828e-07 |
| 21000 | 1.3882472e-07 | 8.0731664e-08 | 3.7134667e-08 | 7.2709684e-07 |
| 24000 | 1.1922791e-07 | 6.6632281e-08 | 4.1628624e-08 | 8.7838269e-07 |
| 27000 | 1.3543774e-07 | 7.5061683e-08 | 3.2481496e-08 | 6.0792782e-07 |
| 30000 | 1.5408301e-07 | 7.9684232e-08 | 4.0387350e-08 | 7.3751209e-07 |

Recent window: checkpoints 15000–30000.

| Field | Recent min | Recent max | 27000/24000 | 30000/27000 | Monotonic decay |
|---|---:|---:|---:|---:|---|
| Ux | 1.1922791e-07 | 1.5431567e-07 | 1.135957 | 1.137667 | NO |
| Uy | 6.6632281e-08 | 8.4534614e-08 | 1.126506 | 1.061583 | NO |
| T | 3.2481496e-08 | 4.5067570e-08 | 0.780268 | 1.243396 | NO |
| p_rgh | 6.0792782e-07 | 9.3676828e-07 | 0.692099 | 1.213157 | NO |

**RESIDUAL_BEHAVIOR = PLATEAU_OR_OSCILLATORY**. No sustained monotonic decrease or decade reduction appears in the full checkpoint history. This classification does not identify the numerical mechanism or modify formal acceptance.

27000 Gate D FAIL: residuals only. 30000 Gate D FAIL: residuals and positive heat-imbalance slope. Both exited normally, with no NaN/Inf/fatal.

| Iteration | Rwin Nu | Rwin U | Rwin W | Heat imbalance | Heat slope/iteration |
|---:|---:|---:|---:|---:|---:|
| 27000 | 1.5161537e-07 | 1.0949003e-06 | 1.1733605e-07 | 2.6591435e-08 | -8.3610027e-11 |
| 30000 | 1.0697915e-07 | 1.5075762e-06 | 1.1582907e-07 | 4.5920804e-08 | 7.4181246e-11 |

Stopped at 30000. Gate D residual limit remains <=1e-7; no numerical settings were changed. Target remains CONVERGENCE_NOT_REACHED and unaccepted. Matrix accepted count remains 9/12.

Next action: DECIDE_RA1E6_GATE_D_POLICY. User decision required. No Ra1e6 medium/fine, 320 or microcase solver executed. Prior accepted cases and pre-24000 history preserved.
