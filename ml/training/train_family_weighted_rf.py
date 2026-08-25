from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS


RANDOM_STATE = 42

MODEL_DIR = Path("ml/models")
MODEL_PATH = (
    MODEL_DIR
    / "cyberlab_binary_family_weighted_rf_v3.joblib"
)

# Conservative first experiment.
FAMILY_WEIGHTS = {
    "BENIGN": 1.0,
    "DDOS": 1.0,
    "DOS": 1.0,
    "RECON": 1.0,
    "MQTT": 1.0,
    "BRUTE_FORCE": 2.0,
    "MITM": 2.0,
    "MIRAI": 2.0,
}


def main() -> None:
    splits = load_splits()

    train = splits.train
    validation = splits.validation

    X_train = train.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y_train = (
        train["Label"]
        .astype(np.int8)
    )

    sample_weight = (
        train["_family"]
        .map(FAMILY_WEIGHTS)
        .astype(float)
        .to_numpy()
    )

    if np.isnan(sample_weight).any():
        raise ValueError(
            "Missing family weight."
        )

    print("=" * 70)
    print("CYBERLAB FAMILY-WEIGHTED RF V3")
    print("=" * 70)

    print(f"Training rows:     {len(X_train):,}")
    print(f"Training features: {len(FEATURE_COLUMNS)}")

    print("\nFamily weights:")

    for family, weight in FAMILY_WEIGHTS.items():
        print(
            f"  {family:<15} {weight:.2f}"
        )

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )

    print("\nTraining family-weighted Random Forest...")

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weight,
    )

    print("Training complete.")

    X_val = validation.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y_val = (
        validation["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    probabilities = (
        model.predict_proba(X_val)[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(np.int8)

    print()
    print("=" * 70)
    print("VALIDATION EVALUATION")
    print("=" * 70)

    print(
        f"Accuracy:  "
        f"{accuracy_score(y_val, predictions):.6f}"
    )
    print(
        f"Precision: "
        f"{precision_score(y_val, predictions):.6f}"
    )
    print(
        f"Recall:    "
        f"{recall_score(y_val, predictions):.6f}"
    )
    print(
        f"F1:        "
        f"{f1_score(y_val, predictions):.6f}"
    )
    print(
        f"ROC-AUC:   "
        f"{roc_auc_score(y_val, probabilities):.6f}"
    )
    print(
        f"PR-AUC:    "
        f"{average_precision_score(y_val, probabilities):.6f}"
    )

    print("\nConfusion matrix:")
    print(
        confusion_matrix(
            y_val,
            predictions,
        )
    )

    print()
    print("-" * 70)
    print("FAMILY DETECTION RATE")
    print("-" * 70)

    families = (
        validation["_family"]
        .to_numpy()
    )

    for family in sorted(
        validation["_family"].unique()
    ):
        mask = families == family

        expected = (
            0
            if family == "BENIGN"
            else 1
        )

        correct = int(
            (
                predictions[mask]
                == expected
            ).sum()
        )

        total = int(mask.sum())

        rate = (
            correct / total * 100
        )

        print(
            f"{family:<15} "
            f"{correct:>6,}/{total:<6,} "
            f"{rate:>7.3f}%"
        )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": model,
        "feature_columns": list(FEATURE_COLUMNS),
        "model_name": (
            "CyberLab Family Weighted RF v3"
        ),
        "random_state": RANDOM_STATE,
        "decision_threshold": 0.50,
        "family_weights": FAMILY_WEIGHTS,
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
        compress=3,
    )

    print()
    print(f"Model saved: {MODEL_PATH}")


if __name__ == "__main__":
    main()