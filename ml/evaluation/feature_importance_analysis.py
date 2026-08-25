from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS
from ml.training.train_binary import MODEL_PATH


RANDOM_STATE = 42
TOP_N = 20

# Permutation importance pahalıdır.
# Validation setinden sabit ve dengeli bir örnek kullanıyoruz.
SAMPLE_SIZE = 10_000


def main() -> None:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]

    validation = load_splits().validation

    sample = validation.sample(
        n=min(SAMPLE_SIZE, len(validation)),
        random_state=RANDOM_STATE,
    )

    X = sample.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y = (
        sample["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    print("=" * 78)
    print("CYBERLAB FEATURE IMPORTANCE ANALYSIS")
    print("=" * 78)

    print(f"Model:             {artifact['model_name']}")
    print(f"Features:          {len(FEATURE_COLUMNS)}")
    print(f"Validation sample: {len(X):,}")

    baseline_prediction = model.predict(X)

    baseline_f1 = f1_score(
        y,
        baseline_prediction,
    )

    print(f"Baseline F1:       {baseline_f1:.6f}")

    # ------------------------------------------------------------
    # Random Forest built-in importance
    # ------------------------------------------------------------

    builtin = pd.DataFrame(
        {
            "feature": list(FEATURE_COLUMNS),
            "importance": model.feature_importances_,
        }
    ).sort_values(
        "importance",
        ascending=False,
    )

    print()
    print("-" * 78)
    print(f"TOP {TOP_N} BUILT-IN FEATURE IMPORTANCE")
    print("-" * 78)

    for rank, row in enumerate(
        builtin.head(TOP_N).itertuples(),
        start=1,
    ):
        print(
            f"{rank:>2}. "
            f"{row.feature:<32} "
            f"{row.importance:.8f}"
        )

    # ------------------------------------------------------------
    # Permutation importance
    # ------------------------------------------------------------

    print()
    print("Calculating permutation importance...")
    print("This may take a little while.")

    result = permutation_importance(
        model,
        X,
        y,
        scoring="f1",
        n_repeats=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    permutation = pd.DataFrame(
        {
            "feature": list(FEATURE_COLUMNS),
            "importance_mean": (
                result.importances_mean
            ),
            "importance_std": (
                result.importances_std
            ),
        }
    ).sort_values(
        "importance_mean",
        ascending=False,
    )

    print()
    print("-" * 78)
    print(f"TOP {TOP_N} PERMUTATION IMPORTANCE")
    print("-" * 78)

    for rank, row in enumerate(
        permutation.head(TOP_N).itertuples(),
        start=1,
    ):
        print(
            f"{rank:>2}. "
            f"{row.feature:<32} "
            f"mean={row.importance_mean:>10.6f} "
            f"std={row.importance_std:>10.6f}"
        )

    # ------------------------------------------------------------
    # Features appearing in both top lists
    # ------------------------------------------------------------

    builtin_top = set(
        builtin.head(TOP_N)["feature"]
    )

    permutation_top = set(
        permutation.head(TOP_N)["feature"]
    )

    overlap = builtin_top & permutation_top

    print()
    print("-" * 78)
    print("TOP-LIST OVERLAP")
    print("-" * 78)

    print(
        f"Features appearing in both top-{TOP_N} lists: "
        f"{len(overlap)}"
    )

    for feature in sorted(overlap):
        print(f"  - {feature}")

    print()
    print("=" * 78)
    print("FEATURE IMPORTANCE ANALYSIS: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()