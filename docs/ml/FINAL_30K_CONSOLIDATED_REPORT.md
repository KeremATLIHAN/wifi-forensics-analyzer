# CyberLab ? Final 30K Consolidated Evaluation

## 1. Executive Summary

The read-only Final 30K evaluation used 30,000 rows: 29,893 normal-duration rows, 107 zero-duration rows, 68 zero-byte degenerate rows, and 39 positive-byte degenerate rows. Baseline model evaluation completed with Accuracy 0.9667666667, Precision 0.9843652715, Recall 0.9486000000, and F1 0.9661517569. Zero-duration rows were retained, no normalization was applied, and diagnostic metadata was kept separate from the model contract. Semantic clearance remains CONDITIONAL.

## 2. Model Performance

| Population | Accuracy | F1 |
|---|---:|---:|
| Overall | 0.9667666667 | 0.9661517569 |
| Normal duration | 0.9668149734 | 0.9661479661 |
| Zero duration | 0.9532710280 | 0.9668874172 |
| Zero-byte zero-duration | 0.9852941176 | 0.9913043478 |
| Positive-byte zero-duration | 0.8974358974 | 0.8888888889 |

Overall Precision is 0.9843652715 and Recall is 0.9486000000. Confusion matrix: `[[14774, 226], [771, 14229]]`.

## 3. Zero-Duration Forensics

The population invariant is **107 = 68 + 39**. The observed fingerprint is duration = 0, two packets, positive finite global rates, and zero directional rates. The 68-row anomaly has total bytes = 0 while both global rates are positive. This pattern is not explained by the runtime zero-duration guard.

## 4. Source Provenance

The prior source audit scanned 32/32 source CSVs. All 68 Final anomaly rows had semantic source matches (68/68; 0 unmatched; 0 partial) across duration, rates, packet counts, lengths, headers, windows, segment size, and packet-length fields. No CSV-to-Parquet transformation, sampling/split transformation, or preprocessing rate modification was found. The anomaly therefore exists in the source CSV population. Original extractor/source-generation provenance remains UNKNOWN.

## 5. Train/Serve Skew

Runtime behavior is `duration <= 0 ? global rates = 0.0`, while source/Parquet rows contain positive global rates at duration = 0. TRAIN/SERVE SKEW is CONFIRMED. The upstream extractor root cause is UNKNOWN.

## 6. Counterfactual Evaluation

A temporary in-memory transformation set Flow Bytes/s, Flow Packets/s, Fwd Packets/s, and Bwd Packets/s to zero. Baseline F1 0.9661517569 changed to 0.9655781112 (delta -0.0005736457). Zero-duration F1 changed from 0.9668874172 to 0.8571428571; positive-byte/P5 F1 changed from 0.8888888889 to 0.6000000000. The three Dictionary Brute Force false negatives did not change. Runtime-consistent rate normalization is therefore NOT ADOPTED as a production solution.

## 7. Feature Separability

`degenerate_flow` is defined as `Flow Duration <= 0`; Flow Duration is already one of the 57 features. Separability analysis therefore classifies its model information content as **REDUNDANT**. It remains useful diagnostic metadata, but is not a new independent model feature. Feature importance and correlation are descriptive, not causal.

## 8. P5 Forensics

P5 contains 39 rows: 35 correct and 4 errors. Errors are three Dictionary Brute Force false negatives and one benign false positive. False-negative row IDs are 14556, 15065, and 19981. They share positive global rates, zero directional rates, a two-packet pattern, and SPECIALIST_BENIGN routing. Specialist probabilities were 0.346965, 0.538107, and 0.548495 against a 0.60 attack threshold. This is a candidate fingerprint, not a causal conclusion.

## 9. Model Probability and Routing

Existing specialist usage was 4,234 / 29,893 = 14.2% for normal-duration rows and 22 / 39 = 56.4% for the positive-byte degenerate/P5 population. The three Dictionary Brute Force false negatives followed SPECIALIST_BENIGN at specialist probabilities 0.346965, 0.538107, and 0.548495 against the 0.60 threshold. These observations are diagnostic evidence; model bias and causal mechanism are not established.

## 10. Diagnostic Architecture

```text
FlowState
  ??? 57-feature vector ? IDS model
  ??? diagnostic metadata ? diagnostic report
```

Diagnostic fields are `degenerate_flow`, `zero_duration_rate_mismatch`, and `zero_duration_zero_bytes`. They are not model inputs, features, or prediction signals; they do not modify predictions, thresholds, routing, rate values, or dataset values. Their diagnostic value is useful even though their model information content is redundant. The governing principle is **DETECT, DON'T DISTORT**.

## 11. Final 30K Diagnostic Results

The diagnostic-only run reported: Total 30,000; `degenerate_flow` 107; `zero_duration_rate_mismatch` 107; `zero_duration_zero_bytes` 68; positive-byte degenerate 39. Invariant: **107 = 68 + 39**. Model inference was NOT RUN. Dataset and 57-feature contract were unchanged.

## 12. Final Architectural Decision

1. Zero-duration rows: RETAIN.
2. Rate normalization: NOT ADOPTED.
3. 57-feature contract: UNCHANGED.
4. `degenerate_flow` model feature: NOT ADOPTED.
5. Diagnostic metadata: ADOPTED.
6. Zero-byte / positive-byte cohorts: SEPARATELY REPORTED.
7. Source provenance is established at CSV level, but upstream root cause: UNKNOWN.
8. Train/serve skew: CONFIRMED.
9. Diagnostic reporting: ADOPTED.
10. Semantic clearance: CONDITIONAL.

## 13. Risk

The anomaly population is small and finite-valued, but has a confirmed semantic mismatch and unknown upstream generation cause. P5 performance is lower than the aggregate population. Counterfactual normalization produced a negative aggregate and subgroup effect. Diagnostic metadata and model data remain deliberately separate.

## 14. Limitations

Original packet timestamp history is unavailable; exact runtime reconstruction is not possible. The original extractor command/version and upstream generation provenance were not found. P4/P5 populations are small. Feature importance, correlation, and counterfactuals do not establish causality or semantic authority.

## 15. Final Conclusion

- Model evaluation: COMPLETED
- Zero-duration anomaly: OBSERVED AND SOURCE-MATCHED
- Upstream root cause: UNKNOWN
- Train/serve skew: CONFIRMED
- Runtime normalization: NOT ADOPTED
- `degenerate_flow` model feature: NOT ADOPTED
- `degenerate_flow` diagnostic: ADOPTED
- 57-feature contract: UNCHANGED
- Diagnostic reporting: ADOPTED
- Semantic clearance: CONDITIONAL

## 16. Source Reports

This draft consolidates the following existing reports without modifying them:

- `docs/ml/FINAL_30K_EVALUATION.md`
- `docs/ml/DEGENERATE_FLOW_SENSITIVITY_ANALYSIS.md`
- `docs/ml/P5_ZERO_DURATION_FORENSICS.md`
- `docs/ml/P5_SPECIALIST_MODEL_FORENSICS.md`
- `docs/ml/ZERO_DURATION_COUNTERFACTUAL_EVALUATION.md`
- `docs/ml/DEGENERATE_FLOW_FEATURE_SEPARABILITY.md`
- `docs/ml/FINAL_30K_DIAGNOSTIC_REPORT.md`

## 17. File Safety

Only this new draft is created. Existing reports, production code, tests, dataset, source CSVs, and model artifacts remain unchanged. No commit or push was performed.
