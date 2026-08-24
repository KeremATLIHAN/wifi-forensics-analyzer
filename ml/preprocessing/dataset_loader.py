from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd
import numpy as np


DATASET_ROOT = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "tabular_iot_attack_2024"
)

CONSTANT_FEATURES = {
    "Bwd PSH Flags",
    "Bwd URG Flags",
    "Fwd Bulk Rate Avg",
    "Fwd Bytes/Bulk Avg",
    "Fwd Packet/Bulk Avg",
    "Protocol",
}


def normalize_columns(columns) -> tuple[str, ...]:
    return tuple(
        str(column).strip()
        for column in columns
    )


def inspect_csv_schemas() -> None:
    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    print("=" * 70)
    print("CYBERLAB ML DATASET SCHEMA ANALYSIS")
    print("=" * 70)

    print(
        f"\nToplam CSV dosyası: "
        f"{len(csv_files)}"
    )

    schemas: dict[
        tuple[str, ...],
        list[Path],
    ] = defaultdict(list)

    dataset_columns: dict[
        str,
        set[str],
    ] = {}

    for csv_file in csv_files:

        try:
            df = pd.read_csv(
                csv_file,
                nrows=0,
            )

        except Exception as exc:
            print(
                f"\n[ERROR] {csv_file}"
            )
            print(exc)
            continue

        columns = normalize_columns(
            df.columns
        )

        schemas[columns].append(
            csv_file
        )

        relative = csv_file.relative_to(
            DATASET_ROOT
        )

        source = relative.parts[0]

        if source not in dataset_columns:
            dataset_columns[source] = set(
                columns
            )

        else:
            dataset_columns[source] &= set(
                columns
            )

    print(
        f"\nFarklı CSV şema sayısı: "
        f"{len(schemas)}"
    )

    for index, (
        columns,
        files,
    ) in enumerate(
        schemas.items(),
        start=1,
    ):
        print("\n" + "-" * 70)

        print(
            f"SCHEMA {index}"
        )

        print(
            f"Dosya sayısı: {len(files)}"
        )

        print(
            f"Kolon sayısı: {len(columns)}"
        )

        print("\nÖrnek dosyalar:")

        for file in files[:5]:
            print(
                "  -",
                file.relative_to(
                    DATASET_ROOT
                ),
            )

        print("\nKolonlar:")

        for number, column in enumerate(
            columns,
            start=1,
        ):
            print(
                f"{number:>3}. {column}"
            )

    print("\n" + "=" * 70)
    print("SOURCE DATASET COMPARISON")
    print("=" * 70)

    for source, columns in (
        dataset_columns.items()
    ):
        print(
            f"\n{source}"
        )

        print(
            f"Ortak kolon sayısı: "
            f"{len(columns)}"
        )

    if dataset_columns:

        global_common = set.intersection(
            *dataset_columns.values()
        )

        print("\n" + "=" * 70)

        print(
            "TÜM DATASETLERDE ORTAK FEATURE'LAR"
        )

        print("=" * 70)

        print(
            f"\nToplam: "
            f"{len(global_common)}"
        )

        for column in sorted(
            global_common
        ):
            print(
                f"  - {column}"
            )


def inspect_dataset_distribution() -> None:
    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    print("\n" + "=" * 70)
    print("CYBERLAB DATASET DISTRIBUTION ANALYSIS")
    print("=" * 70)

    total_rows = 0
    source_rows: defaultdict[str, int] = defaultdict(int)
    label_counts: defaultdict[str, int] = defaultdict(int)
    attack_counts: defaultdict[str, int] = defaultdict(int)

    for index, csv_file in enumerate(
        csv_files,
        start=1,
    ):
        relative = csv_file.relative_to(
            DATASET_ROOT
        )

        source = relative.parts[0]

        print(
            f"[{index:02}/{len(csv_files)}] "
            f"{relative}"
        )

        try:
            df = pd.read_csv(
                csv_file,
                usecols=[
                    "Attack Name",
                    "Label",
                ],
                low_memory=False,
            )

        except Exception as exc:
            print(
                f"  ERROR: {exc}"
            )
            continue

        row_count = len(df)

        total_rows += row_count
        source_rows[source] += row_count

        for label, count in (
            df["Label"]
            .value_counts(dropna=False)
            .items()
        ):
            label_counts[str(label)] += int(
                count
            )

        for attack, count in (
            df["Attack Name"]
            .value_counts(dropna=False)
            .items()
        ):
            attack_counts[str(attack)] += int(
                count
            )

        print(
            f"     Rows: {row_count:,}"
        )

    print("\n" + "=" * 70)
    print("SOURCE DISTRIBUTION")
    print("=" * 70)

    for source, count in sorted(
        source_rows.items()
    ):
        percentage = (
            count / total_rows * 100
            if total_rows
            else 0
        )

        print(
            f"{source:<55}"
            f"{count:>12,} "
            f"({percentage:6.2f}%)"
        )

    print("\n" + "=" * 70)
    print("LABEL DISTRIBUTION")
    print("=" * 70)

    for label, count in sorted(
        label_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        percentage = (
            count / total_rows * 100
            if total_rows
            else 0
        )

        print(
            f"{label:<30}"
            f"{count:>12,} "
            f"({percentage:6.2f}%)"
        )

    print("\n" + "=" * 70)
    print("ATTACK DISTRIBUTION")
    print("=" * 70)

    for attack, count in sorted(
        attack_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        percentage = (
            count / total_rows * 100
            if total_rows
            else 0
        )

        print(
            f"{attack:<40}"
            f"{count:>12,} "
            f"({percentage:6.2f}%)"
        )

    print("\n" + "=" * 70)
    print(
        f"TOTAL ROWS: {total_rows:,}"
    )
    print("=" * 70)


def inspect_data_quality(
    chunk_size: int = 100_000,
) -> None:

    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    print("\n" + "=" * 70)
    print("CYBERLAB DATA QUALITY ANALYSIS")
    print("=" * 70)

    total_rows = 0
    total_missing = 0
    total_inf = 0

    missing_by_column = defaultdict(int)
    inf_by_column = defaultdict(int)

    excluded = CONSTANT_FEATURES | {
        "Flow ID",
        "Src IP",
        "Dst IP",
        "Timestamp",
        "Attack Name",
        "Label",
    }

    for file_index, csv_file in enumerate(
        csv_files,
        start=1,
    ):
        relative = csv_file.relative_to(
            DATASET_ROOT
        )

        print(
            f"\n[{file_index:02}/{len(csv_files)}] "
            f"{relative}"
        )

        file_rows = 0

        for chunk in pd.read_csv(
            csv_file,
            chunksize=chunk_size,
            low_memory=False,
        ):
            chunk.columns = [
                str(column).strip()
                for column in chunk.columns
            ]

            row_count = len(chunk)

            total_rows += row_count
            file_rows += row_count

            missing = chunk.isna().sum()

            for column, count in missing.items():
                if count:
                    missing_by_column[column] += int(
                        count
                    )
                    total_missing += int(count)

            candidate_columns = [
                column
                for column in chunk.columns
                if column not in excluded
            ]

            numeric = (
                chunk[candidate_columns]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
            )

            inf_mask = np.isinf(
                numeric.to_numpy(
                    dtype="float64",
                    copy=False,
                )
            )

            counts = inf_mask.sum(axis=0)

            for column, count in zip(
                numeric.columns,
                counts,
            ):
                if count:
                    inf_by_column[column] += int(
                        count
                    )
                    total_inf += int(count)

        print(
            f"     Rows checked: "
            f"{file_rows:,}"
        )

    print("\n" + "=" * 70)
    print("MISSING VALUES")
    print("=" * 70)

    if not missing_by_column:
        print("Missing value bulunamadı.")
    else:
        for column, count in sorted(
            missing_by_column.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(
                f"{column:<40} {count:>12,}"
            )

    print("\n" + "=" * 70)
    print("INFINITY VALUES")
    print("=" * 70)

    if not inf_by_column:
        print("Infinity değeri bulunamadı.")
    else:
        for column, count in sorted(
            inf_by_column.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(
                f"{column:<40} {count:>12,}"
            )

    print("\n" + "=" * 70)
    print("QUALITY SUMMARY")
    print("=" * 70)

    print(
        f"Rows checked:   {total_rows:,}"
    )

    print(
        f"Missing values: {total_missing:,}"
    )

    print(
        f"Infinity:       {total_inf:,}"
    )

def inspect_feature_variability(
    chunk_size: int = 100_000,
) -> None:

    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    excluded = CONSTANT_FEATURES | {
        "Flow ID",
        "Src IP",
        "Dst IP",
        "Timestamp",
        "Attack Name",
        "Label",
    }

    unique_values = defaultdict(set)
    total_rows = 0

    print("\n" + "=" * 70)
    print("CYBERLAB FEATURE VARIABILITY ANALYSIS")
    print("=" * 70)

    for file_index, csv_file in enumerate(
        csv_files,
        start=1,
    ):
        relative = csv_file.relative_to(
            DATASET_ROOT
        )

        print(
            f"[{file_index:02}/{len(csv_files)}] "
            f"{relative}"
        )

        for chunk in pd.read_csv(
            csv_file,
            chunksize=chunk_size,
            low_memory=False,
        ):
            chunk.columns = [
                str(column).strip()
                for column in chunk.columns
            ]

            total_rows += len(chunk)

            candidate_columns = [
                column
                for column in chunk.columns
                if column not in excluded
            ]

            for column in candidate_columns:

                # Burada bütün benzersiz değerleri RAM'de
                # tutmak istemiyoruz. İlk 100 değer yeterli.
                if len(unique_values[column]) <= 100:
                    values = (
                        chunk[column]
                        .dropna()
                        .unique()
                    )

                    remaining = (
                        101 -
                        len(unique_values[column])
                    )

                    unique_values[column].update(
                        values[:remaining]
                    )

    print("\n" + "=" * 70)
    print("FEATURE VARIABILITY")
    print("=" * 70)

    constant_features = []
    low_variability_features = []

    for column in sorted(unique_values):

        count = len(
            unique_values[column]
        )

        if count == 1:
            constant_features.append(column)

        elif count <= 10:
            low_variability_features.append(
                (column, count)
            )

    print("\nCONSTANT FEATURES:")

    if constant_features:
        for column in constant_features:
            print(f"  - {column}")
    else:
        print("  None")

    print("\nLOW VARIABILITY FEATURES (<=10 unique):")

    if low_variability_features:
        for column, count in low_variability_features:
            print(
                f"  - {column:<35} "
                f"{count:>3} unique"
            )
    else:
        print("  None")

    print("\n" + "=" * 70)
    print(f"ROWS CHECKED: {total_rows:,}")
    print("=" * 70)

from ml.preprocessing.feature_schema import (
    schema_summary,
    validate_schema,
)


if __name__ == "__main__":
    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    sample = pd.read_csv(
        csv_files[0],
        nrows=0,
    )

    validate_schema(
        list(sample.columns)
    )

    schema_summary()

    print("\nSchema validation: OK")


