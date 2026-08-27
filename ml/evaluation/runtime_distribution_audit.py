from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from ml.preprocessing.dataset_persistence import load_splits
from ml.runtime.flow_tracker import FlowTracker
from ml.runtime.ids_inference_contract import (
    INFERENCE_FEATURES,
)
from ml.runtime.tshark_packet_parser import (
    TSharkPacketParser,
)


CAPTURE = (
    "captures/lab/"
    "cyberlab_ip_parity_test.pcapng"
)


def extract_runtime_flows() -> pd.DataFrame:
    parser = TSharkPacketParser()

    tracker = FlowTracker(
        inactivity_timeout=60.0
    )

    expired = []

    for packet in parser.parse_file(CAPTURE):
        tracker.process_packet(packet)

        expired.extend(
            tracker.expire_flows(
                packet.timestamp
            )
        )

    completed = (
        expired
        + tracker.close_all(
            reason="END_OF_CAPTURE"
        )
    )

    rows = []

    for flow in completed:
        rows.append(
            {
                feature: float(
                    flow.features[feature]
                )
                for feature
                in INFERENCE_FEATURES
            }
        )

    return pd.DataFrame(
        rows,
        columns=INFERENCE_FEATURES,
    )


def robust_position(
    value: float,
    median: float,
    q1: float,
    q3: float,
) -> float:

    iqr = q3 - q1

    if iqr == 0:
        if value == median:
            return 0.0

        return np.inf

    return abs(
        value - median
    ) / iqr


def main() -> None:
    validation = (
        load_splits()
        .validation
        .loc[
            :,
            list(INFERENCE_FEATURES),
        ]
    )

    runtime = extract_runtime_flows()

    print("=" * 100)
    print("CYBERLAB RUNTIME DISTRIBUTION AUDIT")
    print("=" * 100)

    print()
    print(
        f"Validation rows:       "
        f"{len(validation):,}"
    )

    print(
        f"Runtime flows:         "
        f"{len(runtime):,}"
    )

    print(
        f"Features:              "
        f"{len(INFERENCE_FEATURES)}"
    )

    results = []

    for feature in INFERENCE_FEATURES:
        reference = (
            validation[feature]
            .astype(float)
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .dropna()
        )

        observed = (
            runtime[feature]
            .astype(float)
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .dropna()
        )

        if reference.empty or observed.empty:
            continue

        q1 = float(
            reference.quantile(0.25)
        )

        median = float(
            reference.median()
        )

        q3 = float(
            reference.quantile(0.75)
        )

        runtime_median = float(
            observed.median()
        )

        position = robust_position(
            runtime_median,
            median,
            q1,
            q3,
        )

        reference_min = float(
            reference.min()
        )

        reference_max = float(
            reference.max()
        )

        outside = int(
            (
                (observed < reference_min)
                | (observed > reference_max)
            ).sum()
        )

        outside_pct = (
            outside
            / len(observed)
            * 100.0
        )

        results.append(
            {
                "feature": feature,
                "validation_median": median,
                "runtime_median": runtime_median,
                "iqr_position": position,
                "outside_pct": outside_pct,
            }
        )

    results.sort(
        key=lambda item: (
            item["iqr_position"],
            item["outside_pct"],
        ),
        reverse=True,
    )

    print()
    print("-" * 100)
    print("TOP DISTRIBUTION SHIFTS")
    print("-" * 100)

    print(
        f"{'Feature':<32}"
        f"{'Val Median':>15}"
        f"{'Run Median':>15}"
        f"{'IQR Dist':>12}"
        f"{'Outside':>12}"
    )

    print("-" * 100)

    for item in results[:25]:
        position = item[
            "iqr_position"
        ]

        if np.isinf(position):
            position_text = "INF"
        else:
            position_text = (
                f"{position:.3f}"
            )

        print(
            f"{item['feature']:<32}"
            f"{item['validation_median']:>15.3f}"
            f"{item['runtime_median']:>15.3f}"
            f"{position_text:>12}"
            f"{item['outside_pct']:>11.2f}%"
        )

    severe = [
        item
        for item in results
        if (
            item["iqr_position"] >= 3.0
            or item["outside_pct"] >= 25.0
        )
    ]

    print()
    print("-" * 100)
    print("SUMMARY")
    print("-" * 100)

    print(
        f"Audited features:      "
        f"{len(results)}"
    )

    print(
        f"Severe-shift features: "
        f"{len(severe)}"
    )

    print()
    print("=" * 100)
    print("RUNTIME DISTRIBUTION AUDIT: OK")
    print("=" * 100)


if __name__ == "__main__":
    main()