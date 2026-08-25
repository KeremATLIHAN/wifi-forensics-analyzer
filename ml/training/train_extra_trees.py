from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
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
MODEL_PATH = MODEL_DIR / "cyberlab_binary_et_v2.joblib"


def prepare_xy(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:

    X = frame.loc[
        :,
        list(FEATURE_COLUMNS),
    ].copy()

    y = frame["Label"].astype(np.int8)

    return X, y


def evaluate_binary(
    name: str,
    model: ExtraTreesClassifier,
    frame: pd.DataFrame,
) -> None:

    X, y = prepare_xy(frame)

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    print()
    print("=" * 70)
    print(f"{name} EVALUATION")
    print("=" * 70)

    print(
        f"Accuracy:  "
        f"{accuracy_score(y, predictions):.6f}"
    )
    print(
        f"Precision: "
        f"{precision_score(y, predictions):.6f}"
    )
    print(
        f"Recall:    "
        f"{recall_score(y, predictions):.6f}"
    )
    print(
        f"F1:        "
        f"{f1_score(y, predictions):.6f}"
    )
    print(
        f"ROC-AUC:   "
        f"{roc_auc_score(y, probabilities):.6f}"
    )
    print(
        f"PR-AUC:    "
        f"{average_precision_score(y, probabilities):.6f}"
    )

    print()
    print("Confusion matrix:")
    print(confusion_matrix(y, predictions))

    print()
    print("Classification report:")
    print(
        classification_report(
            y,
            predictions,
            digits=6,
        )
    )

    print()
    print("-" * 70)
    print("FAMILY DETECTION RATE")
    print("-" * 70)

    evaluation = frame[
        ["_family", "Label"]
    ].copy()

    evaluation["prediction"] = predictions

    for family in sorted(
        evaluation["_family"].unique()
    ):
        family_rows = evaluation[
            evaluation["_family"] == family
        ]

        total = len(family_rows)

        expected = (
            0 if family == "BENIGN" else 1
        )

        correct = int(
            (
                family_rows["prediction"]
                == expected
            ).sum()
        )

        rate = (
            correct / total
            if total
            else 0.0
        )

        print(
            f"{family:<15} "
            f"{correct:>6,}/{total:<6,} "
            f"{rate * 100:>7.3f}%"
        )


def main() -> None:
    splits = load_splits()

    X_train, y_train = prepare_xy(
        splits.train
    )

    print("=" * 70)
    print("CYBERLAB BINARY IDS - EXTRA TREES V2")
    print("=" * 70)

    print(
        f"Training rows:     "
        f"{len(X_train):,}"
    )
    print(
        f"Training features: "
        f"{len(FEATURE_COLUMNS)}"
    )
    print(
        f"Benign:            "
        f"{int((y_train == 0).sum()):,}"
    )
    print(
        f"Attack:            "
        f"{int((y_train == 1).sum()):,}"
    )

    model = ExtraTreesClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )

    print()
    print("Training ExtraTreesClassifier...")

    model.fit(
        X_train,
        y_train,
    )

    print("Training complete.")

    evaluate_binary(
        "VALIDATION",
        model,
        splits.validation,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": model,
        "feature_columns": list(
            FEATURE_COLUMNS
        ),
        "model_name": (
            "CyberLab Binary IDS Extra Trees v2"
        ),
        "random_state": RANDOM_STATE,
        "decision_threshold": 0.50,
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
        compress=3,
    )

    print()
    print(
        f"Model saved: {MODEL_PATH}"
    )


if __name__ == "__main__":
    main()