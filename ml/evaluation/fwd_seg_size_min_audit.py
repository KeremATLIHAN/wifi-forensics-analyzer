from __future__ import annotations

import pandas as pd

from ml.preprocessing.dataset_loader import (
    DATASET_ROOT,
)


SAMPLE_ROWS = 100_000
FEATURE = "Fwd Seg Size Min"


def main() -> None:
    files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    frames = []
    remaining = SAMPLE_ROWS
    used_files = []

    for path in files:
        if remaining <= 0:
            break

        # Önce gerçek kolon isimlerini oku.
        header = pd.read_csv(
            path,
            nrows=0,
        )

        columns = {
            str(column).strip(): column
            for column in header.columns
        }

        if FEATURE not in columns:
            continue

        actual_column = columns[FEATURE]

        df = pd.read_csv(
            path,
            usecols=[actual_column],
            nrows=remaining,
        )

        df.columns = [FEATURE]

        frames.append(df)

        used_files.append(
            (
                path,
                len(df),
            )
        )

        remaining -= len(df)

    if not frames:
        raise RuntimeError(
            f"{FEATURE!r} içeren CSV bulunamadı."
        )

    sample = pd.concat(
        frames,
        ignore_index=True,
    )

    feature = pd.to_numeric(
        sample[FEATURE],
        errors="coerce",
    ).dropna()

    print("=" * 78)
    print("CYBERLAB FWD SEG SIZE MIN AUDIT")
    print("=" * 78)

    print()
    print(
        f"Dataset root: {DATASET_ROOT}"
    )

    print(
        f"Rows loaded: {len(sample):,}"
    )

    print(
        f"Valid values: {len(feature):,}"
    )

    print()
    print("-" * 78)
    print("SOURCE FILES")
    print("-" * 78)

    for path, count in used_files:
        relative = path.relative_to(
            DATASET_ROOT
        )

        print(
            f"{count:>10,}  {relative}"
        )

    print()
    print("-" * 78)
    print("DISTRIBUTION")
    print("-" * 78)

    print(
        feature.describe().to_string()
    )

    print()
    print("-" * 78)
    print("MOST COMMON VALUES")
    print("-" * 78)

    print(
        feature
        .value_counts()
        .head(25)
        .to_string()
    )

    zero_count = int(
        (feature == 0).sum()
    )

    positive_count = int(
        (feature > 0).sum()
    )

    negative_count = int(
        (feature < 0).sum()
    )

    print()
    print("-" * 78)
    print("ZERO / POSITIVE / NEGATIVE")
    print("-" * 78)

    total = len(feature)

    print(
        f"Zero:     {zero_count:>10,} "
        f"({zero_count / total:>8.2%})"
    )

    print(
        f"Positive: {positive_count:>10,} "
        f"({positive_count / total:>8.2%})"
    )

    print(
        f"Negative: {negative_count:>10,} "
        f"({negative_count / total:>8.2%})"
    )

    print()
    print("=" * 78)
    print("FWD SEG SIZE MIN AUDIT: OK")
    print("=" * 78)


if __name__ == "__main__":
    main()