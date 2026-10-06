# Co0.5 → Co0.25 input audit

PASS. All164 cold input files compared. Only system/controlDict differs, solely maxCo0.5→0.25. Physical inputs, mesh, fvSchemes, fvSolution, time scheme, PIMPLE, linear solvers, initial dt, maxdt, endTime and native output dictionaries are byte-identical. New namespace and future output metadata are provenance changes. Frozen12-rank scotch decomposition reused byte-identically and verified by parallel checkMesh, cell-addressing bijection and interior pRefPoint mapping. No runtime trajectory copied.
