from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ml.preprocessing.dataset_loader import DATASET_ROOT
from ml.preprocessing.runtime_feature_schema import (
    RUNTIME_MODEL_FEATURES,
)


FEATURE_COLUMNS = tuple(sorted(RUNTIME_MODEL_FEATURES))

TARGET_COLUMN = "Label"
METADATA_COLUMNS = (
    "Attack Name",
)


def discover_csv_files() -> list[Path]:
    files = sorted(DATASET_ROOT.rglob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    return files


def validate_training_contract() -> None:
    files = discover_csv_files()

    required = set(FEATURE_COLUMNS) | {
        TARGET_COLUMN,
        *METADATA_COLUMNS,
    }

    print("=" * 70)
    print("CYBERLAB TRAINING DATA CONTRACT")
    print("=" * 70)

    print(f"CSV files:        {len(files)}")
    print(f"Runtime features: {len(FEATURE_COLUMNS)}")
    print(f"Target:           {TARGET_COLUMN}")

    errors: list[str] = []

    for path in files:
        columns = {
            str(column).strip()
            for column in pd.read_csv(
                path,
                nrows=0,
            ).columns
        }

        missing = required - columns

        if missing:
            errors.append(
                f"{path}: "
                + ", ".join(sorted(missing))
            )

    if errors:
        print("\nCONTRACT ERRORS:")

        for error in errors:
            print(f"  - {error}")

        raise ValueError(
            "Training dataset contract validation failed."
        )

    print("\nSchema contract: OK")


def validate_numeric_sample(
    rows_per_file: int = 10_000,
) -> None:
    files = discover_csv_files()

    bad_columns: set[str] = set()
    checked_rows = 0

    for path in files:
        df = pd.read_csv(
            path,
            usecols=list(FEATURE_COLUMNS),
            nrows=rows_per_file,
            low_memory=False,
        )

        checked_rows += len(df)

        numeric = df.apply(
            pd.to_numeric,
            errors="coerce",
        )

        for column in FEATURE_COLUMNS:
            original_missing = df[column].isna()
            converted_missing = numeric[column].isna()

            invalid = (
                converted_missing
                & ~original_missing
            )

            if invalid.any():
                bad_columns.add(column)

        values = numeric.to_numpy(
            dtype=np.float64,
            copy=False,
        )

        if np.isinf(values).any():
            raise ValueError(
                f"Infinity bulundu: {path}"
            )

    print(
        f"Numeric sample rows: {checked_rows:,}"
    )

    if bad_columns:
        raise ValueError(
            "Non-numeric feature bulundu: "
            + ", ".join(sorted(bad_columns))
        )

    print("Numeric contract: OK")


if __name__ == "__main__":
    validate_training_contract()
    validate_numeric_sample()

    print()
    print("=" * 70)
    print("TRAINING DATA CONTRACT: OK")
    print("=" * 70)