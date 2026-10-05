# v1.5 authority compatibility with frozen v1.4 runtime

Canonical authority: exact v1.5 contract SHA. Executable implementation:
unchanged v1.4 resource implementation. This layer has no numerical implementation.

From repository root:

```bash
python3 -B Scripts/routeA/diagnostic_transient/v1_5_runtime/verify_runtime_authority.py
python3 -B -m unittest discover -s Scripts/routeA/diagnostic_transient/v1_5_runtime -p test_runtime_authority.py -v
```

`authority.verify_authority()` verifies the manifest digest, canonical/formal
contracts, consistency report and semantic diff, full v1.4 file set, 810 native
source identities, historical linked-library identities, parent/resource
instrumentation digests, replacement observer, timing plan and compute review.
Repository pins reject symlinks. External libraries permit a symlink only when
both its exact registered target realpath and target SHA match.

The original semantic report differs from the canonical contract at `/prepared_at`
only. Both exact timestamp values are registered as a provenance-only erratum;
all other diff rows must match exactly. Original evidence stays unchanged.

`production.prepare()` transparently bridges canonical provenance to the frozen
v1.4 **read-only** preflight: the two authorities and their provenance sets remain
explicit in its returned receipt. It uses the original prepare body for series,
capacity, namespace, conditional Co and lifecycle guards. It does not falsify a
version or mutate a contract. Actual production preflight was not performed here.

`production.run()` checks compatibility, canonical resource readiness and explicit
authorization before preflight or writes. The current exact authority always
rejects execution because readiness is NO. There is no production executor in
this layer; future execution binding requires a separate reviewed task.

`qualification.validate_permission()` validates mode-specific permission
**declarations** and prior-stage declarations. It never launches or writes, never
imports production code, and cannot establish actual user permission by trusting
a supplied task-reference string. Q1/Q2 forbid execution inputs, production
namespace and Q3 permissions; Q3 requires separate scope plus the frozen plan's
prerequisites. Even accepted declarations return `execution_authorized=false`.

The original timing plan/protocol remain immutable historical preparation
artifacts. Its old REQUIRES_FIX gate is not silently set to PASS. Next task must
integrate this verified mapping into target native adapter, independent watchdog,
actual stage receipts and a measurement-ready preparation layer while retaining
all Q1/Q2/Q3 definitions. No target harness or watchdog is implemented here.
