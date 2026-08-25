from __future__ import annotations

from ml.preprocessing.dataset_persistence import (
    load_splits,
)
from ml.preprocessing.training_dataset import (
    FEATURE_COLUMNS,
)


def main() -> None:
    splits = load_splits()

    print("=" * 70)
    print("CYBERLAB PERSISTED DATASET INTEGRITY")
    print("=" * 70)

    expected_rows = {
        "TRAIN": 140_000,
        "VALIDATION": 30_000,
        "TEST": 30_000,
    }

    for name, frame in (
        ("TRAIN", splits.train),
        ("VALIDATION", splits.validation),
        ("TEST", splits.test),
    ):
        print()
        print("-" * 70)
        print(name)
        print("-" * 70)

        print(f"Rows:     {len(frame):,}")
        print(f"Columns:  {len(frame.columns)}")
        print(f"Features: {len(FEATURE_COLUMNS)}")

        if len(frame) != expected_rows[name]:
            raise ValueError(
                f"{name} row count mismatch."
            )

        missing_features = (
            set(FEATURE_COLUMNS)
            - set(frame.columns)
        )

        if missing_features:
            raise ValueError(
                f"{name} missing features: "
                + ", ".join(
                    sorted(missing_features)
                )
            )

        benign = int(
            (frame["Label"] == 0).sum()
        )

        attack = int(
            (frame["Label"] == 1).sum()
        )

        print(
            f"Benign:   {benign:,}"
        )

        print(
            f"Attack:   {attack:,}"
        )

        print("\nFamilies:")

        family_counts = (
            frame["_family"]
            .value_counts()
            .sort_index()
        )

        for family, count in (
            family_counts.items()
        ):
            print(
                f"  {family:<15} "
                f"{int(count):>8,}"
            )

    print()
    print("=" * 70)
    print("PERSISTED DATASET INTEGRITY: OK")
    print("=" * 70)


if __name__ == "__main__":
    main()