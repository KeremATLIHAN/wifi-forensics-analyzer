from __future__ import annotations

import joblib
import numpy as np

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS
from ml.training.train_binary import MODEL_PATH as PRIMARY_MODEL_PATH
from ml.training.train_hard_case_specialist import (
    MODEL_PATH as SPECIALIST_MODEL_PATH,
)


PRIMARY_THRESHOLD = 0.50

ROUTING_FLOORS = (
    0.10,
    0.20,
    0.30,
)

SPECIALIST_THRESHOLDS = (
    0.40,
    0.50,
    0.60,
    0.70,
)


def family_rate(
    predictions: np.ndarray,
    families: np.ndarray,
    family: str,
) -> float:

    mask = families == family

    if not mask.any():
        return 0.0

    expected = (
        0 if family == "BENIGN" else 1
    )

    return float(
        (
            predictions[mask] == expected
        ).mean()
        * 100
    )


def main() -> None:
    primary_artifact = joblib.load(
        PRIMARY_MODEL_PATH
    )

    specialist_artifact = joblib.load(
        SPECIALIST_MODEL_PATH
    )

    primary = primary_artifact["model"]
    specialist = specialist_artifact["model"]

    validation = load_splits().validation

    X = validation.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y = (
        validation["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    families = (
        validation["_family"]
        .to_numpy()
    )

    primary_probability = (
        primary.predict_proba(X)[:, 1]
    )

    specialist_probability = (
        specialist.predict_proba(X)[:, 1]
    )

    baseline = (
        primary_probability >= PRIMARY_THRESHOLD
    ).astype(np.int8)

    baseline_fp = int(
        (
            (y == 0)
            & (baseline == 1)
        ).sum()
    )

    baseline_fn = int(
        (
            (y == 1)
            & (baseline == 0)
        ).sum()
    )

    print("=" * 118)
    print("CYBERLAB HIERARCHICAL IDS EVALUATION")
    print("=" * 118)

    print()
    print("PRIMARY RF BASELINE")
    print(
        f"FP={baseline_fp:,} "
        f"FN={baseline_fn:,} "
        f"BRUTE={family_rate(baseline, families, 'BRUTE_FORCE'):.2f}% "
        f"MITM={family_rate(baseline, families, 'MITM'):.2f}% "
        f"MIRAI={family_rate(baseline, families, 'MIRAI'):.2f}%"
    )

    print()
    print(
        f"{'Floor':>6} "
        f"{'SpecThr':>7} "
        f"{'Routed':>7} "
        f"{'FP':>6} "
        f"{'FN':>6} "
        f"{'Benign':>9} "
        f"{'Attack':>9} "
        f"{'Brute':>9} "
        f"{'MITM':>9} "
        f"{'Mirai':>9}"
    )

    print("-" * 118)

    for floor in ROUTING_FLOORS:
        routing_mask = (
            (primary_probability >= floor)
            & (
                primary_probability
                < PRIMARY_THRESHOLD
            )
        )

        routed = int(
            routing_mask.sum()
        )

        for specialist_threshold in (
            SPECIALIST_THRESHOLDS
        ):
            predictions = baseline.copy()

            specialist_attack = (
                specialist_probability
                >= specialist_threshold
            )

            promote = (
                routing_mask
                & specialist_attack
            )

            predictions[promote] = 1

            fp = int(
                (
                    (y == 0)
                    & (predictions == 1)
                ).sum()
            )

            fn = int(
                (
                    (y == 1)
                    & (predictions == 0)
                ).sum()
            )

            benign = family_rate(
                predictions,
                families,
                "BENIGN",
            )

            attack = float(
                (
                    predictions[y == 1] == 1
                ).mean()
                * 100
            )

            brute = family_rate(
                predictions,
                families,
                "BRUTE_FORCE",
            )

            mitm = family_rate(
                predictions,
                families,
                "MITM",
            )

            mirai = family_rate(
                predictions,
                families,
                "MIRAI",
            )

            print(
                f"{floor:>6.2f} "
                f"{specialist_threshold:>7.2f} "
                f"{routed:>7,} "
                f"{fp:>6,} "
                f"{fn:>6,} "
                f"{benign:>8.2f}% "
                f"{attack:>8.2f}% "
                f"{brute:>8.2f}% "
                f"{mitm:>8.2f}% "
                f"{mirai:>8.2f}%"
            )


if __name__ == "__main__":
    main()