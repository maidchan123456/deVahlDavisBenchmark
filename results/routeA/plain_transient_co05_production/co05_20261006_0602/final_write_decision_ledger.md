# Native final-write decision

Use ordinary `runTime` writes at5s with beginTime0 and endTime1420. Do not add an assumed writeAtEnd option: the installed Time/TimeIO/foamRun sources have no such control. Do not force a final timestep, change maxCo, use adjustableRunTime, or signal early termination during normal completion.

The native running predicate is `t < E - 0.5*dt`. The native write bin is `int(((t-beginTime)+0.5*dt)/interval)`. With E=1420 and interval5, the first non-running completed step crosses bin284. maxDeltaT0.027734375 is far smaller than5, so it cannot skip a write bin. foamRun writes after postSolve, before the next running test. Thus the final computed state is saved by the regular output policy.

This saves the final native state near1420; it does not force an exact1420 timestamp. Native variable dt endTime semantics permit a final physical time in [1419.9861328125,1420.0161783854167) under the frozen maxDeltaT and growth1.2. Actual t,t*,time index,dt are read from each rank's uniform/time.value; directory names and ordinary printed Time headers are not treated as exact physical time. Atconstant dt the half-step interval is tighter. No state at exactly t=1420 is interpolated or invented.

Three million non-CFD floating-point boundary evaluations passed, including representable values at/above the native termination boundary. This is source/arithmetic verification, not execution of a physical timestep. Final postflight requires all12 rank states match, have all native fields/histories and satisfy the termination/bin predicates. A missing/partial final write becomes STOP_AND_REVIEW, not silent success.

Sources (installed source hashes pinned in production_input_manifest.json):
- /opt/openfoam13/src/OpenFOAM/db/Time/Time.C:70-119;884-886;1052-1060;1196-1214 — adjustableRunTime adjusts dt; runTime does not; native running and write bin predicates
- /opt/openfoam13/src/OpenFOAM/db/Time/TimeIO.C:210-249;254-282 — uniform/time has actual value,index,deltaT,deltaT0; writeTime gates native AUTO_WRITE objects
- /opt/openfoam13/applications/solvers/foamRun/foamRun.C:188-200 — postSolve then runTime.write before loop termination; End alone does not force write
- /opt/openfoam13/applications/solvers/foamRun/setDeltaT.C:55-80 — native bounded growth and solver CFL policy
- /opt/openfoam13/src/OSspecific/POSIX/signals/sigWriteNow.C:58-65;102-120 — native writeOnce flag, no dt change
