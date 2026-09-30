# v1.2 改訂記録

更新日: 2026-09-30  
対象: `docs/benchmark_spec.md` および `docs/acceptance_criteria.md`

## 目的と範囲

本改訂は、v1.1 の実装前・候補表現を、完了済みの Route A/B 監査と最小 implementation checks の記録に整合させる文書改訂である。full matrix、Gate H、transient は実行しておらず、本改訂のための CFD run も行っていない。

## v1.1 からの主な変更と根拠

- Route B を監査済み Foundation v6 `buoyantBoussinesqSimpleFoam` として採用した。provenance は build `6-af7d7f427be7`、Git HEAD `af7d7f427be78e9b9beb6aceca8fe7d5d4636876`、binary `/home/mirai/OpenFOAM/OpenFOAM-6/platforms/linux64GccDPInt32Opt/bin/buoyantBoussinesqSimpleFoam` である。
- Route A OQ-02 を解決済みとした。内部は `p=rho0*gh+pRef`、fixed-T壁は `p=rho(Twall)*gh+pRef`、constructor relation `p_rgh=p-rho*gh-pRef` は cell と4 physical walls で確認済みである。`pRefValue` と一様な `pRef` は別である。
- Route B は volume-flux continuity、constant `nu`、`alpha=nu/Pr`、laminar/Stokes、`alphat=0`、steady SIMPLE、中心差分相当を用いる。入力は kinematic `p_rgh`、`0/p` は置かずsolverが `p` を生成する。radiation/MRF/fvOptions/particle coupling は使わない。
- Route B Nu B1 は actual field/mesh の fixedValue patch `snGrad(T)=(Twall-Towner)*deltaCoeffs`、B2 は壁内向き座標の `Tw,T1,T2` の二次多項式補間から得る壁面一次導関数 `(-8*Tw/3 + 3*T1 - T2/3)/h` を使う。v6標準 `wallHeatFlux` は使用しない。

根拠は `docs/openfoam_design.md`、`docs/routeB_design.md`、`docs/routeA_implementation.md`、`docs/routeB_implementation.md`、`results/routeA/`、`results/routeB/` にある。

## Gate G の演算子修正

v1.1 は mass/volume divergence を一般式で記載していた。v1.2 は実際に保存された internal/boundary face flux を使い、empty face寄与をゼロとして

$$D_h(\phi)_i=V_i^{-1}\sum_{f\in i}\phi_f^{out},\qquad
\langle|D_h|\rangle_V=\sum_iV_i|D_h(\phi)_i|/\sum_iV_i$$

を固定した。Route A native mass flux は `epsilon_native,m <= 1e-6`、Route B native volume flux は `epsilon_native,v <= 1e-6` である。Route A solver-consistent volume flux は、native stored mass fluxから、v13 `correctBuoyantPressure` が用いる同じ face-density definition `rhof=fvc::interpolate(rho)` で派生する diagnostic `phi_v=phi_m/rhof` に対して `epsilon_sc,v <= 2e-3` とする。Route B native `phi_v` は同じ solver-consistent check でもあり、より厳しい `1e-6` を適用する。reconstructed cell-U divergence `epsilon_Urec` は Diagnostic のみである。

これは閾値緩和ではなく、solverが保存するfluxと離散演算子を一致させる演算子定義の補正である。連続体の `rho0 div(u)` の等価性は異なる離散演算子間の数値一致を意味しない。旧 Route B manifest の `epsilon_m` は reconstructed `epsilon_v` を複写した legacy compatibility label であり、native mass conservationではない。既存 manifest と implementation/design report は不変である。

## Gate H への影響

QoI（mean Nu、Umax、Vmax）の0.2%閾値は変更していない。Route A の両感度点では native mass conservation のGate G適合を保ち、`epsilon_sc,v` のdecrease/non-worseningを評価し、`epsilon_Urec`はDiagnosticとして別記する。Gate Hは `BENCHMARK_CORE_PASS` 外、`ROUTE_A_CHARACTERIZED` の実施・報告要件、`DOWNSTREAM_TRANSIENT_READY` のHard PASS要件である。

## 現在の状態

- Phase 0--4: 完了。Route A/B audit、A-COND/B-COND Gate C、A/B coarse smoke、minimal A/B diagnostic。
- Phase 5: 次・未実行。Route B 4 Ra x 3 grids、Gate D/E/F/G/K。
- Phase 6--8: 未実行。Route A full matrix、Gate H、transient/下流拡張。
- `BENCHMARK_CORE_PASS`、`ROUTE_A_CHARACTERIZED`、`DOWNSTREAM_TRANSIENT_READY`: NOT EVALUATED。

解決済み事項は Route B採用/provenance、OQ-01 work-root分離、OQ-02、Route B pressure/transport/postprocessing、Gate G演算子である。未解決または未実行事項は OQ-03、full grid convergence、local Nu endpoint/extrema、normalized L2 symmetry実計算、Gate H、closed-volume nonsteady mass、transient、historical v5/custom implementationである。

## Hashes とアーカイブ

v1.1原本は byte-identical archive として保存する。

| ファイル | SHA256 |
|---|---|
| `docs/archive/v1.1/benchmark_spec.md` | `2be4e290ac56da6f1ba112d8defe908024757bdaf2df7e40d5504ee9da4ca159` |
| `docs/archive/v1.1/acceptance_criteria.md` | `ab1f7938e8a9d42e8fe0395c0fef8b4b2f46786e9ddbe3e74db555b9aebe1fa2` |
| `docs/benchmark_spec.md` (v1.2) | `6a99a16f00201442211393bf226a60c8083be534cea378ebfa85c3e7f30d6997` |
| `docs/acceptance_criteria.md` (v1.2) | `69a6ae6bd550659ffacf27b805fc94bb0e1ccd0261e924753ebf8db8ea3a5f11` |

`docs/revision_v1.2.md` のSHA256は、本文を書き込んだ後に外部の最終検証値として報告する。
