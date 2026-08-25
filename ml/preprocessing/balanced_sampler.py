from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from ml.preprocessing.attack_mapping import (
    ATTACK_FAMILY_MAP,
    get_attack_family,
)
from ml.preprocessing.dataset_loader import DATASET_ROOT
from ml.preprocessing.training_dataset import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)


RANDOM_STATE = 42
CHUNK_SIZE = 100_000

FAMILY_QUOTAS = {
    "BENIGN": 100_000,

    "DDOS": 32_000,
    "DOS": 21_500,
    "RECON": 16_000,
    "MQTT": 13_000,
    "BRUTE_FORCE": 9_000,
    "MITM": 6_870,
    "MIRAI": 1_630,
}

EXPECTED_TOTAL = sum(FAMILY_QUOTAS.values())
EXPECTED_BENIGN = FAMILY_QUOTAS["BENIGN"]

EXPECTED_ATTACK = (
    EXPECTED_TOTAL - EXPECTED_BENIGN
)


def discover_csv_files() -> list[Path]:
    files = sorted(DATASET_ROOT.rglob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    return files


def build_balanced_corpus() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_STATE)

    reservoirs: dict[str, pd.DataFrame] = {}
    seen_counts: dict[str, int] = defaultdict(int)

    usecols = [
        *FEATURE_COLUMNS,
        "Attack Name",
        TARGET_COLUMN,
    ]

    files = discover_csv_files()

    print("=" * 70)
    print("CYBERLAB FAMILY-AWARE BALANCED SAMPLER")
    print("=" * 70)
    print(f"CSV files:    {len(files)}")
    print(f"Chunk size:   {CHUNK_SIZE:,}")
    print(f"Random state: {RANDOM_STATE}")
    print(f"Target rows:  {EXPECTED_TOTAL:,}")
    print()

    for file_index, path in enumerate(
        files,
        start=1,
    ):
        print(
            f"[{file_index:02}/{len(files)}] "
            f"{path.name}"
        )

        for chunk in pd.read_csv(
            path,
            usecols=usecols,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        ):
            chunk["Attack Name"] = (
                chunk["Attack Name"]
                .astype(str)
                .str.strip()
            )

            unknown = (
                set(chunk["Attack Name"].unique())
                - set(ATTACK_FAMILY_MAP)
            )

            if unknown:
                raise ValueError(
                    "Unknown attack names: "
                    + ", ".join(sorted(unknown))
                )

            chunk["_family"] = (
                chunk["Attack Name"]
                .map(get_attack_family)
            )

            for family, quota in FAMILY_QUOTAS.items():
                family_rows = chunk[
                    chunk["_family"] == family
                ]

                if family_rows.empty:
                    continue

                seen_counts[family] += len(
                    family_rows
                )

                existing = reservoirs.get(family)

                if existing is None:
                    combined = family_rows
                else:
                    combined = pd.concat(
                        [
                            existing,
                            family_rows,
                        ],
                        ignore_index=True,
                    )

                if len(combined) > quota:
                    indices = rng.choice(
                        len(combined),
                        size=quota,
                        replace=False,
                    )

                    combined = (
                        combined
                        .iloc[indices]
                        .reset_index(drop=True)
                    )

                reservoirs[family] = combined

    print()
    print("-" * 70)
    print("SAMPLING SUMMARY")
    print("-" * 70)

    problems: list[str] = []

    selected_frames: list[pd.DataFrame] = []

    for family, quota in FAMILY_QUOTAS.items():
        frame = reservoirs.get(family)

        selected = (
            0 if frame is None else len(frame)
        )

        seen = seen_counts[family]

        print(
            f"{family:<15} "
            f"seen={seen:>10,} "
            f"selected={selected:>8,} "
            f"target={quota:>8,}"
        )

        if selected < quota:
            problems.append(
                f"{family}: "
                f"{selected:,}/{quota:,}"
            )

        if frame is not None:
            selected_frames.append(frame)

    if problems:
        raise ValueError(
            "Family quotas could not be satisfied: "
            + "; ".join(problems)
        )

    corpus = pd.concat(
        selected_frames,
        ignore_index=True,
    )

    corpus = corpus.sample(
        frac=1.0,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    corpus[TARGET_COLUMN] = (
        corpus["_family"]
        .ne("BENIGN")
        .astype(np.int8)
    )

    if len(corpus) != EXPECTED_TOTAL:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL:,} rows, "
            f"got {len(corpus):,}."
        )

    benign_count = int(
        (corpus[TARGET_COLUMN] == 0).sum()
    )

    attack_count = int(
        (corpus[TARGET_COLUMN] == 1).sum()
    )

    if benign_count != EXPECTED_BENIGN:
        raise ValueError(
            f"Expected {EXPECTED_BENIGN:,} benign rows, "
            f"got {benign_count:,}."
        )

    if attack_count != EXPECTED_ATTACK:
        raise ValueError(
            f"Expected {EXPECTED_ATTACK:,} attack rows, "
            f"got {attack_count:,}."
        )

    print()
    print(f"Total selected: {len(corpus):,}")
    print(f"Benign:         {benign_count:,}")
    print(f"Attack:         {attack_count:,}")
    print()
    print("Balanced corpus validation: OK")

    return corpus


if __name__ == "__main__":
    from ml.preprocessing.dataset_persistence import (
        save_splits,
    )
    from ml.preprocessing.dataset_split import (
        split_corpus,
    )

    corpus = build_balanced_corpus()
    splits = split_corpus(corpus)

    save_splits(splits)
