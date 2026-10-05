# Bounded timing qualification preparation

The governing plan is
`results/routeA/diagnostic_transient/diagnostic_attempt_001/preparation/DiagnosticTransient_bounded_timing_qualification_plan.json`.

Safe preparation checks from repository root:

```bash
python3 -B Scripts/routeA/diagnostic_transient/timing_qualification/protocol.py
python3 -B Scripts/routeA/diagnostic_transient/timing_qualification/u03_scaling.py
python3 -B -m unittest discover -s Scripts/routeA/diagnostic_transient/timing_qualification -p test_protocol.py -v
```

Default U03 invocation is dry-run. The current plan explicitly blocks Q1/Q2/Q3,
even when a receipt falsely declares Q0 PASS: launcher authority compatibility
is REQUIRES_FIX. A reviewed compatibility fix must reissue this protocol and
its source pins before measurement. Receipts declare prior authorization;
creating a receipt does not grant user authorization.

The U03 runner is a bounded scaffold using unchanged `arrival_candidate`.
Its subprocess wall cap, worker CPU/AS caps and larger-N STOP bookkeeping are
prepared. External host-memory/disk/process-group supervision, complete metric
capture and scaling-fit qualification must be integrated before future use.
The target-size native adapter is specified but not implemented here.

Tests perform pure validation/gate checks, a four-node estimator sanity check,
and a mocked timeout. They execute no target-size benchmark or CFD and create
no case, mesh, initial field, seal or purge operation.
