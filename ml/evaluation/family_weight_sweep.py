from __future__ import annotations

import numpy as np

from sklearn.ensemble import RandomForestClassifier

from ml.preprocessing.dataset_persistence import load_splits
from ml.preprocessing.training_dataset import FEATURE_COLUMNS


RANDOM_STATE = 42

WEIGHTS = (
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
)

TARGET_FAMILIES = {
    "BRUTE_FORCE",
    "MITM",
    "MIRAI",
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
        .to_numpy()
    )

    X_val = validation.loc[
        :,
        list(FEATURE_COLUMNS),
    ]

    y_val = (
        validation["Label"]
        .astype(np.int8)
        .to_numpy()
    )

    train_families = (
        train["_family"].to_numpy()
    )

    val_families = (
        validation["_family"].to_numpy()
    )

    print("=" * 100)
    print("CYBERLAB FAMILY WEIGHT SWEEP")
    print("=" * 100)

    print(
        f"{'Weight':>7} "
        f"{'FP':>6} "
        f"{'FN':>6} "
        f"{'Benign':>9} "
        f"{'Attack':>9} "
        f"{'Brute':>9} "
        f"{'MITM':>9} "
        f"{'Mirai':>9}"
    )

    print("-" * 100)

    for weight in WEIGHTS:

        sample_weight = np.ones(
            len(train),
            dtype=float,
        )

        target_mask = np.isin(
            train_families,
            list(TARGET_FAMILIES),
        )

        sample_weight[target_mask] = weight

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )

        model.fit(
            X_train,
            y_train,
            sample_weight=sample_weight,
        )

        probabilities = (
            model.predict_proba(X_val)[:, 1]
        )

        predictions = (
            probabilities >= 0.50
        ).astype(np.int8)

        fp = int(
            (
                (y_val == 0)
                & (predictions == 1)
            ).sum()
        )

        fn = int(
            (
                (y_val == 1)
                & (predictions == 0)
            ).sum()
        )

        def rate(
            family: str,
            expected: int,
        ) -> float:
            mask = (
                val_families == family
            )

            return float(
                (
                    predictions[mask]
                    == expected
                ).mean()
                * 100
            )

        benign_rate = rate(
            "BENIGN",
            0,
        )

        attack_rate = float(
            (
                predictions[y_val == 1]
                == 1
            ).mean()
            * 100
        )

        brute_rate = rate(
            "BRUTE_FORCE",
            1,
        )

        mitm_rate = rate(
            "MITM",
            1,
        )

        mirai_rate = rate(
            "MIRAI",
            1,
        )

        print(
            f"{weight:>7.2f} "
            f"{fp:>6,} "
            f"{fn:>6,} "
            f"{benign_rate:>8.2f}% "
            f"{attack_rate:>8.2f}% "
            f"{brute_rate:>8.2f}% "
            f"{mitm_rate:>8.2f}% "
            f"{mirai_rate:>8.2f}%"
        )


if __name__ == "__main__":
    main()