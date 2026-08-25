from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS


RANDOM_STATE = 42
N_SPLITS = 5

OUTPUT_DIR = Path(
    "ml/datasets/processed/hard_case_v1"
)

OUTPUT_PATH = (
    OUTPUT_DIR / "hard_case_train.parquet"
)


def main() -> None:
    splits = load_splits()

    train = splits.train.reset_index(
        drop=True
    )

    X = train.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y = (
        train["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    oof_probability = np.zeros(
        len(train),
        dtype=float,
    )

    splitter = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    print("=" * 78)
    print("CYBERLAB HARD-CASE DATASET BUILDER")
    print("=" * 78)

    print(f"Rows:       {len(train):,}")
    print(f"Features:   {len(FEATURE_COLUMNS)}")
    print(f"OOF folds:  {N_SPLITS}")

    for fold, (
        train_idx,
        holdout_idx,
    ) in enumerate(
        splitter.split(X, y),
        start=1,
    ):
        print(
            f"\nTraining OOF fold "
            f"{fold}/{N_SPLITS}..."
        )

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            n_jobs=-1,
            random_state=(
                RANDOM_STATE + fold
            ),
        )

        model.fit(
            X.iloc[train_idx],
            y[train_idx],
        )

        oof_probability[
            holdout_idx
        ] = model.predict_proba(
            X.iloc[holdout_idx]
        )[:, 1]

    train["_oof_probability"] = (
        oof_probability
    )

    train["_oof_prediction"] = (
        oof_probability >= 0.50
    ).astype(np.int8)

    # Hard attacks:
    # gerçek saldırı fakat RF güveni düşük.
    hard_attack = (
        (train["Label"] == 1)
        & (train["_oof_probability"] < 0.70)
    )

    # Hard benign:
    # benign fakat saldırıya benzemeye başlamış.
    hard_benign = (
        (train["Label"] == 0)
        & (train["_oof_probability"] >= 0.10)
    )

    hard_mask = (
        hard_attack
        | hard_benign
    )

    hard = train.loc[
        hard_mask
    ].copy()

    print()
    print("-" * 78)
    print("HARD-CASE CORPUS")
    print("-" * 78)

    print(
        f"Total hard cases: "
        f"{len(hard):,}"
    )

    print(
        f"Hard benign:      "
        f"{int(hard_benign.sum()):,}"
    )

    print(
        f"Hard attacks:     "
        f"{int(hard_attack.sum()):,}"
    )

    print()
    print("Family distribution:")

    counts = (
        hard["_family"]
        .value_counts()
        .sort_values(
            ascending=False
        )
    )

    for family, count in counts.items():
        print(
            f"  {family:<15} "
            f"{int(count):>7,}"
        )

    print()
    print("Probability summary:")

    print(
        hard["_oof_probability"]
        .describe(
            percentiles=[
                0.10,
                0.25,
                0.50,
                0.75,
                0.90,
            ]
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    hard.to_parquet(
        OUTPUT_PATH,
        index=False,
        engine="pyarrow",
    )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )

    print()
    print("=" * 78)
    print("HARD-CASE DATASET BUILD: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()