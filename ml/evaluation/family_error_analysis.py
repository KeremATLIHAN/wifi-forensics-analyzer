from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from ml.preprocessing.dataset_persistence import (
    load_splits,
)
from ml.preprocessing.training_dataset import (
    FEATURE_COLUMNS,
)
from ml.training.train_binary import MODEL_PATH


TARGET_FAMILIES = (
    "BRUTE_FORCE",
    "MITM",
    "MIRAI",
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

    predictions = (
        probabilities >= 0.50
    ).astype(np.int8)

    validation["_probability"] = probabilities
    validation["_prediction"] = predictions

    print("=" * 78)
    print("CYBERLAB FAMILY ERROR ANALYSIS")
    print("=" * 78)

    for family in TARGET_FAMILIES:
        frame = validation[
            validation["_family"] == family
        ].copy()

        detected = frame[
            frame["_prediction"] == 1
        ]

        missed = frame[
            frame["_prediction"] == 0
        ]

        print()
        print("=" * 78)
        print(family)
        print("=" * 78)

        print(f"Total:     {len(frame):,}")
        print(f"Detected:  {len(detected):,}")
        print(f"Missed:    {len(missed):,}")

        print(
            "Probability median "
            f"(detected): "
            f"{detected['_probability'].median():.6f}"
        )

        print(
            "Probability median "
            f"(missed):   "
            f"{missed['_probability'].median():.6f}"
        )

        rows = []

        for feature in FEATURE_COLUMNS:
            detected_median = float(
                detected[feature].median()
            )

            missed_median = float(
                missed[feature].median()
            )

            all_values = frame[feature].to_numpy(
                dtype=float
            )

            scale = float(
                np.nanpercentile(
                    np.abs(all_values),
                    75,
                )
            )

            if (
                not np.isfinite(scale)
                or scale == 0
            ):
                scale = 1.0

            separation = (
                abs(
                    detected_median
                    - missed_median
                )
                / scale
            )

            rows.append(
                {
                    "feature": feature,
                    "detected_median": detected_median,
                    "missed_median": missed_median,
                    "separation": separation,
                }
            )

        result = (
            pd.DataFrame(rows)
            .sort_values(
                "separation",
                ascending=False,
            )
            .head(15)
        )

        print()
        print("TOP MEDIAN-SEPARATING FEATURES")
        print("-" * 78)

        for row in result.itertuples():
            print(
                f"{row.feature:<30} "
                f"det={row.detected_median:>12.3f} "
                f"miss={row.missed_median:>12.3f} "
                f"sep={row.separation:>10.4f}"
            )


if __name__ == "__main__":
    main()