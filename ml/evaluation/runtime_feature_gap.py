from __future__ import annotations

from ml.preprocessing.runtime_feature_schema import (
    RUNTIME_MODEL_FEATURES,
)
from ml.runtime.flow_state import FlowState
from ml.runtime.packet_record import PacketRecord


def build_test_flow() -> FlowState:
    packet = PacketRecord(
        timestamp=1000.0,
        frame_length=100,
        src_ip="192.168.1.10",
        dst_ip="8.8.8.8",
        src_port=50000,
        dst_port=443,
        protocol=6,
        transport="TCP",
        tcp_syn=1,
    )

    return FlowState(packet)


def main() -> None:
    flow = build_test_flow()

    implemented = set(
        flow.to_feature_dict().keys()
    )

    expected = set(
        RUNTIME_MODEL_FEATURES
    )

    missing = sorted(
        expected - implemented
    )

    unexpected = sorted(
        implemented - expected
    )

    matched = sorted(
        expected & implemented
    )

    coverage = (
        len(matched) / len(expected) * 100
        if expected
        else 0.0
    )

    print("=" * 70)
    print("CYBERLAB RUNTIME FEATURE GAP AUDIT")
    print("=" * 70)

    print()
    print(f"Runtime target: {len(expected)}")
    print(f"Implemented:    {len(implemented)}")
    print(f"Matched:        {len(matched)}")
    print(f"Missing:        {len(missing)}")
    print(f"Unexpected:     {len(unexpected)}")
    print(f"Coverage:       {coverage:.2f}%")

    print()
    print("-" * 70)
    print("MISSING FEATURES")
    print("-" * 70)

    if missing:
        for index, feature in enumerate(
            missing,
            start=1,
        ):
            print(
                f"{index:>2}. {feature}"
            )
    else:
        print("None")

    print()
    print("-" * 70)
    print("UNEXPECTED FEATURES")
    print("-" * 70)

    if unexpected:
        for index, feature in enumerate(
            unexpected,
            start=1,
        ):
            print(
                f"{index:>2}. {feature}"
            )
    else:
        print("None")


if __name__ == "__main__":
    main()