from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.preprocessing.training_dataset import FEATURE_COLUMNS


RANDOM_STATE = 42

DATASET_PATH = Path(
    "ml/datasets/processed/hard_case_v1/"
    "hard_case_train.parquet"
)

MODEL_DIR = Path("ml/models")

MODEL_PATH = (
    MODEL_DIR
    / "cyberlab_hard_case_specialist_v1.joblib"
)


def main() -> None:
    frame = pd.read_parquet(DATASET_PATH)

    X = frame.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y = (
        frame["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    print("=" * 78)
    print("CYBERLAB HARD-CASE SPECIALIST V1")
    print("=" * 78)

    print(f"Rows:       {len(frame):,}")
    print(f"Features:   {len(FEATURE_COLUMNS)}")
    print(f"Benign:     {int((y == 0).sum()):,}")
    print(f"Attack:     {int((y == 1).sum()):,}")

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )

    print()
    print("Training specialist...")

    model.fit(X, y)

    print("Training complete.")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": model,
        "feature_columns": list(FEATURE_COLUMNS),
        "model_name": (
            "CyberLab Hard-Case Specialist v1"
        ),
        "random_state": RANDOM_STATE,
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