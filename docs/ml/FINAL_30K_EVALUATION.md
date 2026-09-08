# CyberLab — Final 30K IDS Evaluation

## 1. Evaluation Scope

This evaluation was performed read-only against `ml/datasets/processed/binary_v1/test.parquet`.

- Total rows: **30,000**
- Existing model artifacts were loaded; no retraining was performed.
- The dataset was not modified.
- No feature normalization or imputation was applied.
- Zero-duration rows were neither removed nor changed.

The purpose was to measure the current IDS Engine v2 performance on the Final 30K and report the effect of the zero-duration population separately.

## 2. Model Artifacts

| Artifact | Model | Features | Estimators |
|---|---|---:|---:|
| `cyberlab_binary_rf_v1.joblib` | RandomForestClassifier | 57 | 300 |
| `cyberlab_hard_case_specialist_v1.joblib` | RandomForestClassifier | 57 | 400 |

The artifacts were used as-is and were not changed.

## 3. Dataset Validation

- Rows: **30,000**
- Required features: **57**
- Valid feature vectors: **30,000**
- Missing features: **0**
- Duplicate feature vectors: **0**
- Non-numeric features: **0**
- Non-finite features: **0**
- Invalid packet count: **0**

Metadata columns were `Attack Name`, `Label`, and `_family`.

## 4. Population Breakdown

| Population | Count |
|---|---:|
| Positive duration | 29,893 |
| Zero duration | 107 |
| Negative duration | 0 |
| Zero duration + total bytes = 0 | 68 |
| Zero duration + total bytes > 0 | 39 |
| Single packet | 0 |
| Packet count >= 2 | 30,000 |

The single-packet policy therefore produced **0 skipped** flows and **30,000 IDS decisions**.

## 5. Overall Performance

Ground truth:

- Benign: **15,000**
- Attack: **15,000**

Predictions:

- Benign: **15,545**
- Attack: **14,455**

Confusion matrix (`[[TN, FP], [FN, TP]]`):

```text
[[14774, 226],
 [  771, 14229]]
```

| Metric | Value |
|---|---:|
| Accuracy | 0.9667666667 |
| Precision | 0.9843652715 |
| Recall | 0.9486000000 |
| F1 | 0.9661517569 |

## 6. Normal-Duration Performance

The 29,893 positive-duration rows produced:

```text
[[14745, 225],
 [  767, 14156]]
```

| Metric | Value |
|---|---:|
| Accuracy | 0.9668149734 |
| Precision | 0.9843543564 |
| Recall | 0.9486028278 |
| F1 | 0.9661479661 |

## 7. Zero-Duration Performance

The 107 zero-duration rows produced:

```text
[[29, 1],
 [ 4, 73]]
```

| Metric | Value |
|---|---:|
| Accuracy | 0.9532710280 |
| Precision | 0.9864864865 |
| Recall | 0.9480519481 |
| F1 | 0.9668874172 |

The zero-duration subset contained 30 benign and 77 attack rows. Its aggregate effect was small: overall accuracy was approximately 0.0000483 lower than the normal-duration subset, while overall F1 was approximately 0.0000038 higher.

## 8. Zero-Byte Zero-Duration Performance

The 68 zero-duration rows with total bytes equal to zero produced:

```text
[[10, 0],
 [ 1, 57]]
```

| Metric | Value |
|---|---:|
| Accuracy | 0.9852941176 |
| Precision | 1.0000000000 |
| Recall | 0.9827586207 |
| F1 | 0.9913043478 |

The remaining 39 zero-duration rows with total bytes greater than zero produced:

```text
[[19, 1],
 [ 3, 16]]
```

| Metric | Value |
|---|---:|
| Accuracy | 0.8974358974 |
| Precision | 0.9411764706 |
| Recall | 0.8421052632 |
| F1 | 0.8888888889 |

## 9. Routing and Model Output Sanity

All 30,000 rows met the minimum two-packet inference requirement. No decision was skipped. The primary model returned finite probabilities for every row, with minimum 0.0, maximum 1.0, and mean approximately 0.4992740932.

The specialist was used for 4,267 rows. Routing paths were:

| Path | Count |
|---|---:|
| PRIMARY_ATTACK | 14,073 |
| PRIMARY_BENIGN | 11,660 |
| SPECIALIST_BENIGN | 3,885 |
| SPECIALIST_ATTACK | 382 |

## 10. Interpretation and Decision

The Final 30K performance evaluation completed successfully. Zero-duration rows were included in the reported metrics and did not materially change aggregate accuracy or F1. The 39 zero-duration rows with positive total bytes had a materially lower subset performance and should remain visible in future provenance and semantic reviews.

Performance does not establish the provenance of the zero-duration values. Runtime/reference zero-duration parity remains **FAIL**, and the cause of the 68-row zero-byte anomaly remains **unknown**. Therefore semantic clearance is **CONDITIONAL**, even though model inference and performance measurement completed.

## 11. Reproducibility and File Safety

- Final 30K was evaluated read-only in this phase.
- Code, tests, dataset contents, and model artifacts were not changed.
- Retraining, normalization, imputation, and row filtering were not performed.
- No commit or push was performed for the evaluation.

At the start of documentation, the pre-existing working-tree status contained the untracked user directory `CICFlowMeter-reference/`; it was preserved unchanged. This report is the only new file created by this documentation step.

**Final 30K:** evaluated read-only
**Model inference:** completed
**Final performance metrics:** calculated
**Semantic clearance:** conditional
