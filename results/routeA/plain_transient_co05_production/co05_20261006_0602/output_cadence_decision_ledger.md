# Output cadence decision

Selected `writeControl runTime; writeInterval 5; purgeWrite 0; writeFormat ascii; writeCompression off; writePrecision 17; timePrecision 12;`. Numeric time-directory precision can increase natively if needed; field values stay at17 digits.

| interval | regular snapshots | with10 startup requests, upper bound | allocated field bytes | field files |
|---|---:|---:|---:|---:|
| 2s | 710 | 720 | 7207649280 | 103680 |
| 5s | 284 | 294 | 2943123456 | 42336 |
| 10s | 142 | 152 | 1521614848 | 21888 |

The 5s default preserves284 later samples and permits approach-to-steady/profile comparisons. It gives t* spacing0.00704225352. Ten native SIGUSR1 write requests target steps2,5,10,20,30,39,60,100,250,500. Requests go to the verified master during the preceding step after native handler activation. Actual write indices/times are read from uniform/time after the run; signals and asynchronous observation can shift the requested step. These are extra native full fields, with no online field analysis, no function objects, no end-time signal, no deltaT adjustment. Duplicate requests/regular writes coalesce, so294 is an upper bound. Cold0 is retained separately.

Startup sampling matters: the pilot speed maximum changed from0.0225 to0.0397m/s between1.49 and2.93s. Five-second-only output would miss that startup. Five-second later output is adequate for planned evolution analysis; resolving every possible oscillation is not claimed. The 2s alternative costs2.45 times as many fields;10s halves later temporal resolution. No format conversion, purge, or every-step output is needed.

Actual pilot measurements:12 rank filesets form one snapshot; each contains144 files and at most10010624 allocated bytes.294 snapshots use2943123456 allocated bytes; at200000 completed steps the measured native log rate gives5394465552 bytes. Combined expectation is8337589008 bytes (~7.77GiB), plus cold case and offline tables. Expected output files:42336 native field/state files + one combined stdout/stderr log + a small metadata set. Profiles may add294 CSVs. This is a planning estimate based on real early/late ASCII fields, not a hard capacity bound; field string lengths and step count can vary.

Disk reserve:32GiB before launch,8GiB low-watermark during run; preparation free capacity792038248448 bytes. The reserve exceeds3 times the estimate and covers inputs, decomposition, postprocessing and margin.200000 is used only for capacity estimation, never as a timestep stopping rule.

Installed Time::setDeltaT invokes write-time adjustment only for adjustableRunTime. Plain runTime output and native writeOnce flags only select writes. Output does not modify the frozen Co/controller/BDF trajectory.
