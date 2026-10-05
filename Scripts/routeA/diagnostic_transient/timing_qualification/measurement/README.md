# Non-CFD timing implementation preparation

This namespace is a new adapter around frozen v1.4 resource processing and the
v1.5 runtime authority mapping. It never imports a CFD launcher, constructs a
case, changes a mesh, solves an fv equation, or advances OpenFOAM Time.

**Current decision: INCOMPLETE. Q1/Q2 measurement readiness is NO.**
`TimingQualification_harness_manifest.json` records this decision. The future
runner rejects both stages even if supplied with an otherwise valid future
non-CFD authorization. No execution authorization is created by this task.

Read-only inspection:

```sh
python3 -B Scripts/routeA/diagnostic_transient/timing_qualification/measurement/runner.py
```

The standalone adapter uses the original `DiagnosticJson.H` Json container,
serializer, and SHA implementation. Python manufactures resource-only values
and feeds the original-shaped objects through a C++ parser; parsing and common
fixture work remain in OFF. ON additionally hashes, serializes, sends over
AF_UNIX, receives ACK, and runs the original evaluator, packed codec, Live
collector, and persistence Writer. Native parse/construction and serialization
are separate spans. ACK spans include backend work and must not be added to
backend spans. These extra preparation/parsing costs must be disclosed in any
future comparison with production instrumentation.

The four-cell self-test may traverse the whole registered graph. The native
adapter enforces four cells for the self-test bypass. Target runs require the
sealed receipt and an independent fixed Python authority/permission verifier;
the worker and backend also revalidate. Authorization inputs have an exact
schema and cannot contain command/binary/solver/case execution inputs. Output
must be a fresh private qualification namespace, with no symlink or traversal.
Receipts and final JSON publication use fsync and an immutable atomic publish.
Mutable heartbeat/roles files are supervision state, not sealed evidence.

The outer supervisor enforces stage budgets; inner supervisors enforce trials.
All budgets come from the frozen plan. `/proc` sampling targets 20 ms, disk/file
sampling 100 ms. Trace collection overhead counts toward the wall/scratch/file
bounds. Sample gaps can miss transient peaks. The simultaneous RSS maximum is
recorded separately from the sum of separate process high-water marks.
Hard AS limits and parent-death SIGKILL supplement TERM (at most one second)
then KILL. Registered nested trial groups are allowed; escaping groups stop.
Supervisor crashes invalidate trials and trigger coordinator cleanup. Censored
trials never become completed fit points. No output purge is performed.

Remaining fixes before measurement:

1. Q1 must explicitly bind and separate constructor/startup costs, and reconcile
   recurring selected-audit timing with the frozen Writer's initial three
   full-audit steps. Resetting Writer per repeat currently selects full audit.
   Retained output across all ON repeats has not been shown to fit 12 GiB.
2. Q2 uses separate files per trial. Even the U03 suite plus required memory and
   primitive repetitions cannot complete within the stage's 256-file limit.
   Preserve evidence in a stage-level append format with sealed per-trial
   indexes; do not increase quotas or delete previous output.
3. Complete separate small-receipt/scalar primitives and per-class spans,
   reconcile memory events with Writer sharing/ring behavior, and integrate
   registered repeat/host stability decisions. Current aggregate spans and
   byte-class summaries are useful but insufficient for full Q2 qualification.
4. Verify the whole-stage receipt/supervision/partial-failure path using tiny
   fixtures and test-only validator substitution without issuing actual
   measurement authorization.

The large I/O runner is implemented but only sub-kilobyte I/O is tested here.
Its uncompressed repeated-byte files are nonsparse; readback is cache
uncontrolled/warm. Logical bytes and `/proc` physical bytes are distinct.
The memory streaming event does not allocate or qualify a 9 GiB raw audit.
Event payloads represent actual generated packet sizes, not every theoretical
maximum cap. Manufactured linear records and outer context exercise unchanged
U01 arithmetic; they are not real solver records or scientific evidence.

The requested next task remains
`FIX_ROUTE_A_DIAGNOSTIC_TRANSIENT_TIMING_QUALIFICATION_PREPARATION`.
Resource feasibility stays UNRESOLVED; production resource-ready and execution
permission stay NO. Existing contracts, plan, U01–U04, numerical settings,
persistence policies, formal gates, and historical results remain frozen.
