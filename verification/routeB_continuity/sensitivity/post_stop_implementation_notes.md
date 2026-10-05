# Post-STOP implementation notes

The first20-grid zero-source baseline candidate reached the registered maximum12000 iterations without satisfying the immutable steady rule. All solver work stopped. No preregistration or source/monitor code was changed, and no new solver or mesh execution occurred after STOP.

Read-only diagnosis records individual stopping failures, seven-QoI Rwin histories, compact pressure/audit tails and source hashes. Report generation was clarified to distinguish a NOT_CONVERGED candidate from an accepted baseline and to mark all unexecuted phases explicitly. Empty figures carry a no-observation label.

Two orchestration maintenance edits were made after STOP for future safety: refuse execution when STOP.json already exists, and clear the inherited WM_BASH_FUNCTIONS loading flag before requesting a fresh OpenFOAM shell environment. The original environment request emitted missing-function warnings, while each actual solver log identifies Foundation v6 and serial execution. These maintenance edits were not solver-tested after STOP.

Future execution requires a separately authorized task and a new/amended registration. Do not delete STOP, overwrite existing runs, relax the old stopping criteria, or reuse this incomplete baseline as a numerical reference.
