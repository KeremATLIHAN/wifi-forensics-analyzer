from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS
from ml.training.train_binary import MODEL_PATH


BANDS = (
    (0.00, 0.10),
    (0.10, 0.20),
    (0.20, 0.30),
    (0.30, 0.40),
    (0.40, 0.50),
    (0.50, 0.70),
    (0.70, 0.90),
    (0.90, 1.01),
)


def main() -> None:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]

    validation = load_splits().validation.copy()

    X = validation.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    probabilities = model.predict_proba(X)[:, 1]

    validation["_probability"] = probabilities

    print("=" * 90)
    print("CYBERLAB PROBABILITY BAND ANALYSIS")
    print("=" * 90)

    for low, high in BANDS:
        mask = (
            (validation["_probability"] >= low)
            & (validation["_probability"] < high)
        )

        band = validation.loc[mask]

        print()
        print("-" * 90)
        print(
            f"BAND {low:.2f} <= p < {high:.2f}"
        )
        print("-" * 90)

        print(f"Flows: {len(band):,}")

        if band.empty:
            continue

        counts = (
            band["_family"]
            .value_counts()
            .sort_values(ascending=False)
        )

        for family, count in counts.items():
            percentage = (
                count / len(band) * 100
            )

            print(
                f"{family:<15} "
                f"{int(count):>6,} "
                f"{percentage:>7.2f}%"
            )

    print()
    print("=" * 90)
    print("MISSED ATTACK DISTRIBUTION (p < 0.50)")
    print("=" * 90)

    missed = validation[
        (validation["Label"] == 1)
        & (validation["_probability"] < 0.50)
    ]

    print(f"Total missed attacks: {len(missed):,}")
    print()

    counts = (
        missed["_family"]
        .value_counts()
        .sort_values(ascending=False)
    )

    for family, count in counts.items():
        percentage = (
            count / len(missed) * 100
        )

        median_probability = (
            missed.loc[
                missed["_family"] == family,
                "_probability",
            ].median()
        )

        print(
            f"{family:<15} "
            f"{int(count):>6,} "
            f"{percentage:>7.2f}% "
            f"median_p={median_probability:.4f}"
        )


if __name__ == "__main__":
    main()