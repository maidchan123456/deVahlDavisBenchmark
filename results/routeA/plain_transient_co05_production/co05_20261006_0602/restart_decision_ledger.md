# Continuous cold-start decision

Strict restart = NOT RELIED UPON. Primary production = CONTINUOUS_COLD_START, one uninterrupted native run from validated cold0 to endTime1420. No pilot state, synthetic oldTime, injected pressure/energy history, or restart research is used.

Native e/K histories are incomplete on disk. Stored U_0/rho_0/phi_0 and uniform/time do not establish identical variable-step backward continuation. All native state outputs are retained, but no strict-BDF restart claim is made.

Interruption, timeout, fatal/nonfinite log, disk low-watermark, observer failure or partial final output => INTERRUPTED_REQUIRES_RESTART_REVIEW_OR_COLD_RERUN and STOP_AND_REVIEW. Preserve logs, return code, metadata and whatever states were actually written. No automatic restart/retry/cold rerun. A later explicit task must review restart limitations or authorize a new cold rerun in a fresh namespace. Do not overwrite this execution directory. A24h wall guard is operational protection, not the6.1h projection; there is no step-count or online steady stopping rule.
