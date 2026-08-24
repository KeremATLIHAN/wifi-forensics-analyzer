from __future__ import annotations

from pathlib import Path

import pandas as pd


DATASET_ROOT = Path(
    "ml/datasets/tabular_iot_attack_2024"
)

COLUMNS = [
    "Flow Duration",
    "Total Fwd Packet",
    "Total Bwd packets",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
]


def find_csv() -> Path:
    # Önce benign örnek tercih ediyoruz.
    benign = sorted(
        DATASET_ROOT.rglob("Benign Traffic.csv")
    )

    if benign:
        return benign[0]

    csv_files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    if not csv_files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    return csv_files[0]


def main() -> None:
    csv_path = find_csv()

    print("=" * 70)
    print("CYBERLAB FEATURE PARITY AUDIT")
    print("=" * 70)
    print(f"Dataset: {csv_path}")
    print()

    df = pd.read_csv(
        csv_path,
        usecols=COLUMNS,
        nrows=50_000,
    )

    print("ROWS:", len(df))
    print()

    print("-" * 70)
    print("FLOW DURATION")
    print("-" * 70)
    print(
        df["Flow Duration"]
        .describe(
            percentiles=[
                0.50,
                0.90,
                0.95,
                0.99,
            ]
        )
    )

    print()
    print("-" * 70)
    print("FLOW IAT")
    print("-" * 70)

    for column in [
        "Flow IAT Mean",
        "Flow IAT Std",
        "Flow IAT Max",
        "Flow IAT Min",
    ]:
        values = df[column]

        print(
            f"{column:20} "
            f"median={values.median():.6f} "
            f"mean={values.mean():.6f} "
            f"max={values.max():.6f}"
        )

    print()
    print("-" * 70)
    print("PACKET LENGTH STD")
    print("-" * 70)

    for column in [
        "Fwd Packet Length Std",
        "Bwd Packet Length Std",
    ]:
        non_zero = df.loc[
            df[column] > 0,
            column,
        ]

        print(
            f"{column:25} "
            f"nonzero={len(non_zero):,} "
            f"median="
            f"{non_zero.median() if len(non_zero) else 0:.6f}"
        )

    print()
    print("-" * 70)
    print("RATE CONSISTENCY CHECK")
    print("-" * 70)

    valid = df[
        df["Flow Duration"] > 0
    ].copy()

    # Hipotez 1:
    # Flow Duration mikro-saniye ise:
    valid["Expected Packets/s"] = (
        (
            valid["Total Fwd Packet"]
            + valid["Total Bwd packets"]
        )
        / valid["Flow Duration"]
        * 1_000_000
    )

    valid["Packets/s Error"] = (
        valid["Expected Packets/s"]
        - valid["Flow Packets/s"]
    ).abs()

    print(
        "Median packets/s error "
        "(duration assumed microseconds):",
        valid["Packets/s Error"].median(),
    )

    valid["Expected Bytes/s"] = (
        (
            valid["Total Length of Fwd Packet"]
            + valid["Total Length of Bwd Packet"]
        )
        / valid["Flow Duration"]
        * 1_000_000
    )

    valid["Bytes/s Error"] = (
        valid["Expected Bytes/s"]
        - valid["Flow Bytes/s"]
    ).abs()

    print(
        "Median bytes/s error "
        "(duration assumed microseconds):",
        valid["Bytes/s Error"].median(),
    )

    print()
    print("-" * 70)
    print("PACKET LENGTH CONSISTENCY")
    print("-" * 70)

    # Mean * packet count ile total length arasındaki
    # matematiksel uyumu kontrol ediyoruz.

    fwd_valid = df[
        df["Total Fwd Packet"] > 0
    ].copy()

    fwd_valid["Expected Fwd Total"] = (
        fwd_valid["Fwd Packet Length Mean"]
        * fwd_valid["Total Fwd Packet"]
    )

    fwd_valid["Fwd Length Error"] = (
        fwd_valid["Expected Fwd Total"]
        - fwd_valid["Total Length of Fwd Packet"]
    ).abs()

    print(
        "Median Fwd length error:",
        fwd_valid["Fwd Length Error"].median(),
    )

    bwd_valid = df[
        df["Total Bwd packets"] > 0
    ].copy()

    bwd_valid["Expected Bwd Total"] = (
        bwd_valid["Bwd Packet Length Mean"]
        * bwd_valid["Total Bwd packets"]
    )

    bwd_valid["Bwd Length Error"] = (
        bwd_valid["Expected Bwd Total"]
        - bwd_valid["Total Length of Bwd Packet"]
    ).abs()

    print(
        "Median Bwd length error:",
        bwd_valid["Bwd Length Error"].median(),
    )


if __name__ == "__main__":
    main()
