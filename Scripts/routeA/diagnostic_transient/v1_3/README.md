# Route A diagnostic v1.3 resource prototype

RESOURCE / EVIDENCE RETENTION REVISION ONLY. This namespace inherits the frozen
v1.2 operator taps, equations and stage graph. U01–U03 are unchanged.

This implementation is **INCOMPLETE for production diagnostic use**. `server.py`
rejects `DIAGNOSTIC_OBSERVATION`. The complete live primary/control/inner/arrival
collector is not bound. Passing synthetic mass/energy replay tests does not close
that gap. Do not remove this guard just to enable a run.

`generate_online.py` mechanically moves the v1.2 replay loop before persistence.
`generate_native.py` changes only persistence start/send/finish calls. JSON is
currently transient IPC transport; retained arrays use typed binary storage.
`persistence.py` commits64-step compact chunks and selected raw/field audits,
shares exact static blobs, and uses16 bounded recent stages. Full-step raw audits
stream only selected steps into scratch, never a whole step in memory.
`selected_replay.py` witnesses59 selected packets against the complete compact
native stage graph; it never labels partial replay as complete raw coverage.

`build_synthetic.py OUTPUT` builds only a replacement observer shared library,
using the frozen existing native fixture/build. `test_pipeline.py` executes only
that in-memory synthetic fixture, P0/P1/OFF, and mutations. `test_storage.py OUTPUT`
checks chunk/memory/quota/rotation semantics without a solver or mesh.
`account_capacity.py` uses existing U04 data and writes resource-only scenarios.

No script here executes foamRun, creates a CFD case, meshes, initializes fields,
modifies v1.2/formal criteria, or commits to Git. New SHA/provenance and diagnostic
v1.3 candidate authority are in the resource revision report and contract.
