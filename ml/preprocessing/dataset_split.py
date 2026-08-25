from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


@dataclass(frozen=True)
class DatasetSplits:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def split_corpus(
    corpus: pd.DataFrame,
) -> DatasetSplits:

    if "_family" not in corpus.columns:
        raise ValueError(
            "Corpus '_family' column is required "
            "for stratified splitting."
        )

    # First split:
    # 70% train / 30% temporary
    train, temporary = train_test_split(
        corpus,
        test_size=(
            VALIDATION_RATIO + TEST_RATIO
        ),
        random_state=RANDOM_STATE,
        stratify=corpus["_family"],
    )

    # Temporary dataset is 30% of total.
    # Split it equally:
    # 15% validation / 15% test.
    validation, test = train_test_split(
        temporary,
        test_size=0.5,
        random_state=RANDOM_STATE,
        stratify=temporary["_family"],
    )

    splits = DatasetSplits(
        train=train.reset_index(drop=True),
        validation=validation.reset_index(drop=True),
        test=test.reset_index(drop=True),
    )

    validate_splits(
        corpus,
        splits,
    )

    return splits


def validate_splits(
    corpus: pd.DataFrame,
    splits: DatasetSplits,
) -> None:

    total = (
        len(splits.train)
        + len(splits.validation)
        + len(splits.test)
    )

    if total != len(corpus):
        raise ValueError(
            "Split row count does not match corpus."
        )

    expected_families = set(
        corpus["_family"].unique()
    )

    for name, frame in (
        ("TRAIN", splits.train),
        ("VALIDATION", splits.validation),
        ("TEST", splits.test),
    ):
        families = set(
            frame["_family"].unique()
        )

        missing = (
            expected_families - families
        )

        if missing:
            raise ValueError(
                f"{name} missing families: "
                + ", ".join(sorted(missing))
            )

    print("=" * 70)
    print("CYBERLAB DATASET SPLIT")
    print("=" * 70)

    print(
        f"Corpus:     {len(corpus):>8,}"
    )
    print(
        f"Train:      {len(splits.train):>8,}"
    )
    print(
        f"Validation: {len(splits.validation):>8,}"
    )
    print(
        f"Test:       {len(splits.test):>8,}"
    )

    print()

    for name, frame in (
        ("TRAIN", splits.train),
        ("VALIDATION", splits.validation),
        ("TEST", splits.test),
    ):
        print("-" * 70)
        print(name)
        print("-" * 70)

        counts = (
            frame["_family"]
            .value_counts()
        )

        for family in sorted(
            expected_families
        ):
            count = int(
                counts.get(family, 0)
            )

            print(
                f"{family:<15} "
                f"{count:>8,}"
            )

        benign = int(
            (frame["Label"] == 0).sum()
        )

        attack = int(
            (frame["Label"] == 1).sum()
        )

        print(
            f"\nBinary: "
            f"benign={benign:,}, "
            f"attack={attack:,}"
        )

    print()
    print("Dataset split validation: OK")