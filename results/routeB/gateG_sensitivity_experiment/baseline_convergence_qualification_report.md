# 20x20 Zero-Source Baseline Convergence Qualification

## 1. Purpose

20²/zero-source/Ra30000だけを、元1e-8 criteriaのまま追加反復し、decay/plateau/oscillationを分類。研究quota/tauは決めない。

## 2. Previous STOP

12000でQoI/U/T/heatの登録条件が未達。原STOPと前回report/summaryは変更していない。

## 3. Amendment and hashes

Original JSON: `567af0e99595d20cb6aeecc99788c4d4b7d36e2f5f33bec05dc4093bde07d0e3`。Amendment JSON: `6d90e0bba92d62b0563f8582487783521ddc78a6251f071aa4af86eac47fe7d7`。Markdown: `58e8b8995b95a761f630716d6ae68d5ec75710936e5d2d3fedadbc79395f3e93`。再開前に固定し、各call前にhash検証。

## 4. Unchanged numerical conditions

p1e-10、U/T1e-12、relTol0、relaxation、scheme、mesh、physics、BC、source、binary、monitor/QoI definition不変。新しいworking copyのcontrolDictはstartFrom latestTimeとendTimeだけ変更。

## 5. Continuation provenance

U/T/p_rgh/phiの12000保存hash一致。全restart tree/mesh/inputs/sourceを記録。binaryは再buildせずpath/source/build時刻で前回との整合を確認し、本task中はSHA256で固定。前回binary digestは未保存なので過去のcryptographic equalityを捏造しない。各checkpointでfieldsをignored archiveへ保存。

## 6. Original steady criteria

sample20、window200、value/U/T/heat1e-8、position1/4096、元epsilon capacity条件、momentum/T initial<=1e-8、pressure final<=1.1e-10、finite/normal exit、200追加confirmationを維持。各restartのmonitor初期化による欠測windowは保存して判定から除外。

## 7. Checkpoint results

| Iteration | QoI max range | U change | T change | Heat range | epsilon_mean | Criteria |
|---|---|---|---|---|---|---|
| 12000 | 8.7279e-08 | 2.2789e-07 | 1.6271e-07 | 2.4398e-08 | 2.2745e-10 | False |
| 15000 | 6.4134e-08 | 1.2737e-07 | 3.2393e-08 | 3.2407e-08 | 3.3987e-10 | False |
| 18000 | 1.5275e-07 | 6.8619e-07 | 4.2320e-07 | 5.6225e-08 | 4.2879e-10 | False |
| 24000 | 1.3889e-07 | 3.0098e-07 | 2.9874e-07 | 3.0875e-08 | 1.8962e-10 | False |
| 30000 | 1.1217e-07 | 3.1527e-07 | 1.3686e-07 | 3.1948e-08 | 2.1061e-10 | False |


## 8. QoI convergence

{"Nu_bar_cavity": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [3.059987402403681e-08, 2.665156823246098e-08, 2.14327517391043e-08], "magnitude_key": "Nu_bar_cavity_range", "fitted_last_first_ratio": 0.7004196070306871, "class": "INCONCLUSIVE", "reason": "Neither registered decay nor stable-band rule met"}, "Nu_bar_0": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [3.52731749265561e-08, 3.566615041841798e-08, 3.325493447481927e-08], "magnitude_key": "Nu_bar_0_range", "fitted_last_first_ratio": 0.9427825690219469, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}, "Nu_bar_half": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [6.518709409177097e-08, 9.192204732842883e-08, 6.291721257396516e-08], "magnitude_key": "Nu_bar_half_range", "fitted_last_first_ratio": 0.965178973699767, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}, "Umax": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [8.077048077765928e-08, 8.048155766066953e-08, 9.706727197573604e-08], "magnitude_key": "Umax_range", "fitted_last_first_ratio": 1.201766673185189, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}, "Wmax": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [3.4012766864068844e-08, 3.539065415926998e-08, 2.9714331666495187e-08], "magnitude_key": "Wmax_range", "fitted_last_first_ratio": 0.8736228894652339, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}, "Umax_Z": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [0.0, 0.0, 0.0], "magnitude_key": "Umax_Z_range", "class": "INCONCLUSIVE", "reason": "Zero magnitude; no log floor; observed constant/quantized range"}, "Wmax_X": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [0.0, 0.0, 0.0], "magnitude_key": "Wmax_X_range", "class": "INCONCLUSIVE", "reason": "Zero magnitude; no log floor; observed constant/quantized range"}}。全7QoIのcurrent/min/max/mean/normalized range/slope/前checkpoint差はCSV/JSON参照。

## 9. U/T field convergence

{"U": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [2.1884069730154016e-07, 3.0584633496181496e-07, 2.8479140975427466e-07], "magnitude_key": "U_window_max", "fitted_last_first_ratio": 1.3013640207966513, "class": "INCONCLUSIVE", "reason": "Neither registered decay nor stable-band rule met"}, "T": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [8.035738119360758e-08, 2.230698896710237e-07, 9.389415822624869e-08], "magnitude_key": "T_window_max", "fitted_last_first_ratio": 1.168457170101482, "class": "INCONCLUSIVE", "reason": "Neither registered decay nor stable-band rule met"}}。20/40/100/200 separationのmax/RMSを各checkpointに保存。Hard判定は元の20-step max/window条件。

## 10. Residual behaviour

各checkpointのUx/Uy/T/p initial/finalとpressure true residual/Npを保存。linear_solver_precision_as_primary_cause=INCONCLUSIVE。固定条件でのouter変動とlinear residualの同時存在は因果同定ではない。

## 11. Conservation behaviour

epsilon mean/max/max-to-mean、heat imbalanceを保存。boundaryとzero sourceも不変。これらをGate G thresholdに転換しない。

## 12. Decay / plateau / oscillation classification

QoIは後半3checkpointのband中央値が約1.05e-7 / 9.57e-8 / 1.04e-7、heatは約3.53e-8 / 3.13e-8 / 2.91e-8で、登録済みPLATEAU規則に適合した。Uはlog-fit比率1.301が登録帯[0.8,1.25]を外れ、Tは中央値の最大/最小比2.776がfactor2条件を外れたため、U/TおよびoverallはINCONCLUSIVEとした。これらの分類cutoffは実行後に変更していない。明確な周期性は登録規則で確認されていない。

{"qoi": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [1.0465592014510689e-07, 9.572432746324953e-08, 1.0387909182722118e-07], "magnitude_key": "QoI_max_range", "fitted_last_first_ratio": 0.992577311280541, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}, "U": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [2.1884069730154016e-07, 3.0584633496181496e-07, 2.8479140975427466e-07], "magnitude_key": "U_window_max", "fitted_last_first_ratio": 1.3013640207966513, "class": "INCONCLUSIVE", "reason": "Neither registered decay nor stable-band rule met"}, "T": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [8.035738119360758e-08, 2.230698896710237e-07, 9.389415822624869e-08], "magnitude_key": "T_window_max", "fitted_last_first_ratio": 1.168457170101482, "class": "INCONCLUSIVE", "reason": "Neither registered decay nor stable-band rule met"}, "heat": {"late_checkpoints": [18000, 24000, 30000], "amplitude_medians": [3.531853956914555e-08, 3.131879825141723e-08, 2.908433834269947e-08], "magnitude_key": "heat_window_range", "fitted_last_first_ratio": 0.8234864379303971, "periodicity_lags_samples": [null, null, null], "class": "PLATEAU", "reason": "Stable amplitude band; registered coherent-periodicity test not established"}}。Overall=INCONCLUSIVE。全classification cutoffはamendmentに事前固定。

## 13. Whether 1e-8 is reached

criterion_reached=False、baseline_convergence_qualified=False、final iteration=30000。基準を緩めない。

## 14. Confirmation window

confirmation_completed=False。compiled markerはfirst qualificationから200継続を意味し、residual等の元条件も確認。今回の確認区間: None。

## 15. Interpretation

分類は登録された有限観測範囲に限定し、decay/plateauの未確定要素を残す。 原因がmachine/parser/sampling/SIMPLE/relaxationのどれかは断定しない。

## 16. What is NOT concluded

truth/exact solution、scientific acceptance quota、tau_mean、new steady criterion、Candidate B正式採用、formal結果再評価、全Ra/gridへの外挿は結論しない。Arm1他tolerance/40/80/Arm2/offset/holdoutを実行していない。

## 17. Next decision

同じnumerical problemのresolution bandの原因を、別taskで対照実験により切り分けるか。plateau値をquota/criterionへ自動採用しない。 Baselineはacceptedにできない。

