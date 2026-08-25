from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS
from ml.training.train_binary import MODEL_PATH


THRESHOLDS = [
    0.50,
    0.45,
    0.40,
    0.35,
    0.30,
    0.25,
    0.20,
]


def main() -> None:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]

    validation = load_splits().validation

    X = validation.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    probabilities = model.predict_proba(X)[:, 1]

    print("=" * 78)
    print("CYBERLAB BINARY IDS THRESHOLD ANALYSIS")
    print("=" * 78)

    print(
        f"{'Threshold':>9} "
        f"{'FP':>7} "
        f"{'FN':>7} "
        f"{'Benign':>9} "
        f"{'Attack':>9} "
        f"{'Brute':>9} "
        f"{'MITM':>9} "
        f"{'Mirai':>9}"
    )

    print("-" * 78)

    y = validation["Label"].to_numpy()

    families = validation["_family"].to_numpy()

    for threshold in THRESHOLDS:
        predictions = (
            probabilities >= threshold
        ).astype(np.int8)

        fp = int(
            ((y == 0) & (predictions == 1)).sum()
        )

        fn = int(
            ((y == 1) & (predictions == 0)).sum()
        )

        def family_rate(
            family: str,
            expected: int,
        ) -> float:
            mask = families == family

            if not mask.any():
                return 0.0

            return float(
                (predictions[mask] == expected).mean()
                * 100
            )

        benign_rate = family_rate(
            "BENIGN", 0
        )

        attack_rate = float(
            (
                predictions[y == 1] == 1
            ).mean()
            * 100
        )

        brute_rate = family_rate(
            "BRUTE_FORCE", 1
        )

        mitm_rate = family_rate(
            "MITM", 1
        )

        mirai_rate = family_rate(
            "MIRAI", 1
        )

        print(
            f"{threshold:>9.2f} "
            f"{fp:>7,} "
            f"{fn:>7,} "
            f"{benign_rate:>8.2f}% "
            f"{attack_rate:>8.2f}% "
            f"{brute_rate:>8.2f}% "
            f"{mitm_rate:>8.2f}% "
            f"{mirai_rate:>8.2f}%"
        )


if __name__ == "__main__":
    main()