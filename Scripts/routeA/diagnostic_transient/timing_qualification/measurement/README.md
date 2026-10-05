# Non-CFD qualification campaign preparation

The active decision is machine-derived in
`TimingQualification_measurement_readiness_v2.json` and the active implementation
is pinned by `TimingQualification_harness_manifest_v2.json`. Earlier reports
and the first harness manifest are immutable history; their source pins refer
to the preceding git revision. No authorization is issued by preparation.

Read-only inspection:

```sh
python3 -B Scripts/routeA/diagnostic_transient/timing_qualification/measurement/runner.py
```

A future Q1/Q2 campaign needs a separately supplied exact-schema non-CFD
measurement authorization, prior-stage evidence, and a fresh qualification
output. The external authorization pins canonical, plan, and active harness
hashes. The runner, worker, backend and fixed native permission helper verify
their boundaries. Stage receipts also bind quota context, watchdog, runtime,
mesh, topology and registered graph. The four-cell test substitute never grants
actual measurement permission and cannot select target-size data. No CFD
launcher, Time API or solver call exists in this namespace.

Q1 performs one separately indexed full startup audit sample, then the original
OFF/ON/ON/OFF/OFF/ON order at the same resource-only checkpoint. Reconstructing
that checkpoint invokes the unmodified Schedule for its three startup slots;
recurring samples exercise its first selected target. All three production
startup audit slots remain explicit: the one measured startup-audit sample has
projection multiplicity three, **not** a claim to have measured three different
production startup states. Constructor, per-trial setup, native recurring
callbacks, selected publication, full startup audit and finalization have
separate metrics. Full trial/stage wall still includes setup and publication.
The projection is resource-fixture planning only, never CFD execution evidence.

The original DiagnosticJson.H representation, serializer and SHA execute on
native objects. OFF retains common fixture preparation/parsing/graph traversal.
Backend evaluation, Live and Writer methods remain frozen. Compact scalar
receipts use receipt_bytes and the exact original RAC13 scalar-row layout;
controller states are a separate class. Six primitive classes are measured
individually. Selected primitives transport and collect the registered selected
records and call Writer.audit. Memory events call original share/accept/ring,
bundle, snapshot, spool, U01 and chunk methods. Sharing retains the original
object ownership: static objects by reference, fresh packed bytes per record,
Live references to last-five field arrays. A chunk-publication event supplements
the seven existing memory events without altering the plan's numerical rules.

Native callback spans separate construction/hash/serialization/send/ACK; backend
spans are a class/path tree with exact accumulated inclusive and exclusive times.
The backend compacts completed span records between callbacks, retaining counts,
parents and totals. ACK includes receiver work and is never added to backend
wall. Host and repeatability rules are read from the frozen plan. Missing CPU,
frequency or trace evidence, sampling gaps, high CV/ratio or other CPU activity
produce UNRESOLVED; no extra repeats are added. Profiling overhead and synthetic
numeric patterns remain qualifications on future production cost projections.
No unit-test timing is target-size performance evidence.

Each trial first executes real publication, write, hash and fsync. Afterwards its
workspace representation migrates to an append-only bounded archive with exact
trial offsets/lengths/SHA and chained metadata. Small artifacts occupy <=64MiB
chunks. The bounded full startup audit is atomically adopted without a second
9GiB copy; selected bytes already present inside that audit can be referenced
by exact record offsets. Identical completed artifacts share SHA references.
No write being measured is replaced by a link. Workspace duplicates are retired
only after durable archive commit and verified readback: all logical evidence,
including partial artifacts, remains readable. Committed archive bytes/records
are never rewritten or purged. Uncommitted tails are explicitly invalid and
cannot resume a stage; committed corruption fails verification.

`archive.layout` accounts for archive chunks/blobs, current workspace, control
files, partial publications and eight reserved STOP files. `schedule.accounting`
proves the simultaneous Q1 retained/temporary bound, conditional on enforced
exact fixture identity and full-audit bundle views. Normal writes protect a
16MiB/eight-file STOP reserve plus bounded log/roles/time-v side-channel credit.
The outer supervisor observes whole-stage quota while trial supervisors observe
the same root. Emergency result/manifest writes can use the reserved space.
Every trial's outputs remain individually addressable; packing is a lossless
representation change, not a retention/purge policy change.

Watchdogs run outside the measured process, with nested registered groups,
20ms memory/process observations and 100ms disk/file observations, hard AS
limits and parent-death cleanup. TERM grace is <=1s then KILL. Heartbeats pulse
during cleanup; coordinator failure kills registered nested groups. Concurrent
native+backend peak is distinct from the sum of individual peaks. Sampling can
miss short-lived maxima, so event coverage remains explicitly reviewable.

The I/O path and U03 mathematics are unchanged. Prefix streaming never allocates
9GiB in RAM. Cache state and logical/proc physical I/O remain distinct. No case,
mesh, initialization, target timing campaign, Q3 or production CFD is executed by
this preparation task. Resource feasibility and execution permission remain
UNRESOLVED/NO even when the implementation readiness is YES.
