from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATASET_ROOT = Path(
    "ml/datasets/tabular_iot_attack_2024"
)

COLUMNS = [
    "Fwd Packet Length Min",
    "Fwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Max",
    "Packet Length Min",
    "Packet Length Max",
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
    print("GLOBAL PACKET POPULATION PARITY")
    print("-" * 70)

    total_packets = (
        df["Total Fwd Packet"].astype(float)
        + df["Total Bwd packets"].astype(float)
    )

    valid = total_packets > 0

    actual_packet_mean = (
        df.loc[
            valid,
            "Packet Length Mean",
        ].astype(float)
    )

    average_packet_size = (
        df.loc[
            valid,
            "Average Packet Size",
        ].astype(float)
    )

    packet_count = total_packets[valid]

    # Hypothesis:
    # CIC global packet-length statistics use N+1 observations,
    # while Average Packet Size divides the same accumulated
    # packet-length sum by N.
    expected_packet_mean = (
        average_packet_size
        * packet_count
        / (packet_count + 1.0)
    )

    error_summary(
        "Packet Length Mean vs "
        "Average Packet Size * N / (N+1)",
        actual_packet_mean,
        expected_packet_mean,
    )

    implied_packet_sum = (
        average_packet_size
        * packet_count
    )

    directional_total = (
        df.loc[
            valid,
            "Total Length of Fwd Packet",
        ].astype(float)
        + df.loc[
            valid,
            "Total Length of Bwd Packet",
        ].astype(float)
    )

    implied_extra = (
        implied_packet_sum
        - directional_total
    )

    print()
    print("IMPLIED EXTRA PACKET-LENGTH OBSERVATION")
    print("-" * 70)

    print(
        implied_extra.describe(
            percentiles=[
                0.10,
                0.25,
                0.50,
                0.75,
                0.90,
                0.99,
            ]
        ).to_string()
    )

    print()
    print("Most common implied extra values:")

    print(
        implied_extra
        .round(6)
        .value_counts()
        .head(20)
        .to_string()
    )

    print()
    print("-" * 70)
    print("IMPLIED EXTRA VALUE MATCH AUDIT")
    print("-" * 70)

    candidates = {
        "Packet Length Min":
            df.loc[valid, "Packet Length Min"].astype(float),

        "Packet Length Max":
            df.loc[valid, "Packet Length Max"].astype(float),

        "Fwd Packet Length Min":
            df.loc[valid, "Fwd Packet Length Min"].astype(float),

        "Fwd Packet Length Max":
            df.loc[valid, "Fwd Packet Length Max"].astype(float),

        "Bwd Packet Length Min":
            df.loc[valid, "Bwd Packet Length Min"].astype(float),

        "Bwd Packet Length Max":
            df.loc[valid, "Bwd Packet Length Max"].astype(float),
    }

    for name, candidate in candidates.items():

        matches = np.isclose(
            implied_extra,
            candidate,
        )

        print(
            f"{name:<28} "
            f"{matches.mean() * 100:>8.4f}%"
        )

    print()
    print("-" * 70)
    print("DIRECTIONAL VS GLOBAL LENGTH SUM AUDIT")
    print("-" * 70)

    fwd_count = (
        df.loc[
            valid,
            "Total Fwd Packet",
        ].astype(float)
    )

    bwd_count = (
        df.loc[
            valid,
            "Total Bwd packets",
        ].astype(float)
    )

    fwd_mean = (
        df.loc[
            valid,
            "Fwd Packet Length Mean",
        ].astype(float)
    )

    bwd_mean = (
        df.loc[
            valid,
            "Bwd Packet Length Mean",
        ].astype(float)
    )

    directional_implied_sum = (
        fwd_mean * fwd_count
        + bwd_mean * bwd_count
    )

    global_implied_sum = (
        df.loc[
            valid,
            "Average Packet Size",
        ].astype(float)
        * (
            fwd_count
            + bwd_count
        )
    )

    sum_delta = (
        global_implied_sum
        - directional_implied_sum
    )

    print()
    print(
        "Global implied sum vs "
        "directional implied sum"
    )

    print(
        sum_delta.describe(
            percentiles=[
                0.10,
                0.25,
                0.50,
                0.75,
                0.90,
                0.99,
            ]
        ).to_string()
    )

    print()
    print("Most common deltas:")

    print(
        sum_delta
        .round(6)
        .value_counts()
        .head(20)
        .to_string()
    )

    print()
    print(
        "Exact zero delta: "
        f"{np.isclose(sum_delta, 0).mean() * 100:.4f}%"
    )

    print()
    print(
        "Delta equals implied_extra: "
        f"{np.isclose(sum_delta, implied_extra).mean() * 100:.4f}%"
    )

    print()
    print("-" * 70)
    print("FIRST-PACKET HYPOTHESIS AUDIT")
    print("-" * 70)

    first_packet_candidates = {
        "Fwd Packet Length Min":
            df.loc[
                valid,
                "Fwd Packet Length Min",
            ].astype(float),

        "Fwd Packet Length Max":
            df.loc[
                valid,
                "Fwd Packet Length Max",
            ].astype(float),

        "Fwd Packet Length Mean":
            df.loc[
                valid,
                "Fwd Packet Length Mean",
            ].astype(float),
    }

    fwd_single_packet = (
        df.loc[
            valid,
            "Total Fwd Packet",
        ].astype(float)
        == 1
    )

    print(
        f"Rows with exactly one FWD packet: "
        f"{int(fwd_single_packet.sum()):,}"
    )

    if fwd_single_packet.any():

        single_extra = (
            implied_extra[
                fwd_single_packet
            ]
        )

        single_fwd_mean = (
            df.loc[
                valid,
                "Fwd Packet Length Mean",
            ]
            .astype(float)[
                fwd_single_packet
            ]
        )

        matches = np.isclose(
            single_extra,
            single_fwd_mean,
        )

        print(
            "Implied extra == only FWD packet length: "
            f"{matches.mean() * 100:.4f}%"
        )

        error_summary(
            "Implied extra vs only FWD packet length",
            single_extra,
            single_fwd_mean,
        )

        print()
        print(
            "Most common implied first-packet lengths "
            "(single-FWD flows):"
        )

        first_length_counts = (
            single_extra
            .round(6)
            .value_counts()
            .head(30)
        )

        for value, count in first_length_counts.items():
            print(
                f"  {value:>10.3f} : "
                f"{count:>6,}"
            )

        print()
        print(
            "Single-FWD first-packet length summary:"
        )
        print(
            single_extra.describe(
                percentiles=[
                    0.10,
                    0.25,
                    0.50,
                    0.75,
                    0.90,
                    0.95,
                    0.99,
                ]
            )
        )

    print()
    print("All-row candidate matching:")

    for name, candidate in (
        first_packet_candidates.items()
    ):

        matches = np.isclose(
            implied_extra,
            candidate,
        )

        print(
            f"{name:<28} "
            f"{matches.mean() * 100:>8.4f}%"
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
