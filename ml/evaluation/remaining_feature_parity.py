from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATASET_ROOT = Path(
    "ml/datasets/tabular_iot_attack_2024"
)

COLUMNS = [
    "Total Fwd Packet",
    "Total Bwd packets",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Packet Length Mean",
    "Average Packet Size",
    "Fwd Segment Size Avg",
    "Bwd Segment Size Avg",
    "Down/Up Ratio",
]


def find_csv() -> Path:
    benign = sorted(
        DATASET_ROOT.rglob("Benign Traffic.csv")
    )

    if benign:
        return benign[0]

    files = sorted(
        DATASET_ROOT.rglob("*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"CSV bulunamadı: {DATASET_ROOT}"
        )

    return files[0]


def error_summary(
    name: str,
    actual: pd.Series,
    expected: pd.Series,
) -> None:

    error = (
        actual.astype(float)
        - expected.astype(float)
    ).abs()

    print()
    print(name)
    print(
        f"  Median error: {error.median():.12f}"
    )
    print(
        f"  Mean error:   {error.mean():.12f}"
    )
    print(
        f"  Max error:    {error.max():.12f}"
    )
    print(
        "  Exact/close:  "
        f"{np.isclose(actual, expected).mean() * 100:.4f}%"
    )


def main() -> None:
    path = find_csv()

    print("=" * 70)
    print("CYBERLAB REMAINING FEATURE PARITY AUDIT")
    print("=" * 70)
    print(f"Dataset: {path}")

    df = pd.read_csv(
        path,
        usecols=COLUMNS,
        nrows=50_000,
    )

    print(f"Rows: {len(df):,}")

    print()
    print("-" * 70)
    print("SEGMENT SIZE")
    print("-" * 70)

    error_summary(
        "Fwd Segment Size Avg "
        "vs Fwd Packet Length Mean",
        df["Fwd Segment Size Avg"],
        df["Fwd Packet Length Mean"],
    )

    error_summary(
        "Bwd Segment Size Avg "
        "vs Bwd Packet Length Mean",
        df["Bwd Segment Size Avg"],
        df["Bwd Packet Length Mean"],
    )

    print()
    print("-" * 70)
    print("AVERAGE PACKET SIZE")
    print("-" * 70)

    total_packets = (
        df["Total Fwd Packet"]
        + df["Total Bwd packets"]
    )

    total_bytes = (
        df["Total Length of Fwd Packet"]
        + df["Total Length of Bwd Packet"]
    )

    valid_packets = total_packets > 0

    avg_packet_candidate = (
        total_bytes[valid_packets]
        / total_packets[valid_packets]
    )

    error_summary(
        "Average Packet Size "
        "vs Total Bytes / Total Packets",
        df.loc[
            valid_packets,
            "Average Packet Size",
        ],
        avg_packet_candidate,
    )

    print()
    print("-" * 70)
    print("AVERAGE PACKET SIZE - EXTENDED")
    print("-" * 70)

    fwd = df["Total Fwd Packet"].astype(float)
    bwd = df["Total Bwd packets"].astype(float)

    fwd_bytes = (
        df["Total Length of Fwd Packet"]
        .astype(float)
    )

    bwd_bytes = (
        df["Total Length of Bwd Packet"]
        .astype(float)
    )

    total_bytes_extended = (
        fwd_bytes + bwd_bytes
    )

    actual_avg_packet_size = (
        df["Average Packet Size"]
        .astype(float)
    )

    candidates = {
        "bytes / (fwd+bwd)":
            total_bytes_extended
            / (fwd + bwd).replace(0, np.nan),

        "bytes / (fwd+bwd+1)":
            total_bytes_extended
            / (fwd + bwd + 1),

        "bytes / fwd":
            total_bytes_extended
            / fwd.replace(0, np.nan),

        "bytes / (fwd+1)":
            total_bytes_extended
            / (fwd + 1),

        "Fwd Mean":
            df[
                "Fwd Packet Length Mean"
            ].astype(float),

        "Bwd Mean":
            df[
                "Bwd Packet Length Mean"
            ].astype(float),

        "Packet Length Mean":
            df["Packet Length Mean"].astype(float),
    }

    for name, candidate in candidates.items():

        valid = (
            actual_avg_packet_size.notna()
            & candidate.notna()
            & np.isfinite(candidate)
        )

        error_summary(
            f"Average Packet Size vs {name}",
            actual_avg_packet_size[valid],
            candidate[valid],
        )

    print()
    print("-" * 70)
    print("AVERAGE PACKET SIZE - DIAGNOSTIC")
    print("-" * 70)

    diagnostic = df[
        [
            "Total Fwd Packet",
            "Total Bwd packets",
            "Total Length of Fwd Packet",
            "Total Length of Bwd Packet",
            "Fwd Packet Length Mean",
            "Bwd Packet Length Mean",
            "Packet Length Mean",
            "Average Packet Size",
        ]
    ].copy()

    diagnostic["Total Packets"] = (
        diagnostic["Total Fwd Packet"]
        + diagnostic["Total Bwd packets"]
    )

    diagnostic["Total Bytes"] = (
        diagnostic["Total Length of Fwd Packet"]
        + diagnostic["Total Length of Bwd Packet"]
    )

    diagnostic["Bytes / Packets"] = (
        diagnostic["Total Bytes"]
        / diagnostic["Total Packets"].replace(
            0,
            np.nan,
        )
    )

    diagnostic["Avg - PacketMean"] = (
        diagnostic["Average Packet Size"]
        - diagnostic["Packet Length Mean"]
    )

    diagnostic["Avg * Packets"] = (
        diagnostic["Average Packet Size"]
        * diagnostic["Total Packets"]
    )

    diagnostic["Avg * (Packets+1)"] = (
        diagnostic["Average Packet Size"]
        * (
            diagnostic["Total Packets"]
            + 1
        )
    )

    # Sadece Average Packet Size'in basit
    # total_bytes / total_packets formülünden
    # farklı olduğu satırları incele.
    mismatch = diagnostic[
        ~np.isclose(
            diagnostic["Average Packet Size"],
            diagnostic["Bytes / Packets"],
        )
    ]

    print(
        mismatch.head(20).to_string(
            index=False
        )
    )

    print()
    print("-" * 70)
    print("DOWN / UP RATIO")
    print("-" * 70)

    valid_fwd = (
        df["Total Fwd Packet"] > 0
    )

    ratio_float = (
        df.loc[
            valid_fwd,
            "Total Bwd packets",
        ]
        / df.loc[
            valid_fwd,
            "Total Fwd Packet",
        ]
    )

    error_summary(
        "Down/Up Ratio vs Bwd/Fwd",
        df.loc[
            valid_fwd,
            "Down/Up Ratio",
        ],
        ratio_float,
    )

    ratio_floor = np.floor(
        ratio_float
    )

    error_summary(
        "Down/Up Ratio vs floor(Bwd/Fwd)",
        df.loc[
            valid_fwd,
            "Down/Up Ratio",
        ],
        ratio_floor,
    )


if __name__ == "__main__":
    main()
