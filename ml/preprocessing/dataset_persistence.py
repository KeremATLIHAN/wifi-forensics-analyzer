from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ml.preprocessing.dataset_split import DatasetSplits


OUTPUT_ROOT = Path("ml/datasets/processed/binary_v1")

TRAIN_PATH = OUTPUT_ROOT / "train.parquet"
VALIDATION_PATH = OUTPUT_ROOT / "validation.parquet"
TEST_PATH = OUTPUT_ROOT / "test.parquet"


@dataclass(frozen=True)
class PersistedDataset:
    train_path: Path
    validation_path: Path
    test_path: Path


def save_splits(
    splits: DatasetSplits,
) -> PersistedDataset:

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    splits.train.to_parquet(
        TRAIN_PATH,
        index=False,
        engine="pyarrow",
    )

    splits.validation.to_parquet(
        VALIDATION_PATH,
        index=False,
        engine="pyarrow",
    )

    splits.test.to_parquet(
        TEST_PATH,
        index=False,
        engine="pyarrow",
    )

    print("=" * 70)
    print("CYBERLAB DATASET PERSISTENCE")
    print("=" * 70)

    print(
        f"Train:      {TRAIN_PATH} "
        f"({len(splits.train):,} rows)"
    )

    print(
        f"Validation: {VALIDATION_PATH} "
        f"({len(splits.validation):,} rows)"
    )

    print(
        f"Test:       {TEST_PATH} "
        f"({len(splits.test):,} rows)"
    )

    print()
    print("Dataset persistence: OK")

    return PersistedDataset(
        train_path=TRAIN_PATH,
        validation_path=VALIDATION_PATH,
        test_path=TEST_PATH,
    )


def load_splits() -> DatasetSplits:

    required = (
        TRAIN_PATH,
        VALIDATION_PATH,
        TEST_PATH,
    )

    missing = [
        path
        for path in required
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing persisted datasets: "
            + ", ".join(
                str(path)
                for path in missing
            )
        )

    return DatasetSplits(
        train=pd.read_parquet(TRAIN_PATH),
        validation=pd.read_parquet(
            VALIDATION_PATH
        ),
        test=pd.read_parquet(TEST_PATH),
    )