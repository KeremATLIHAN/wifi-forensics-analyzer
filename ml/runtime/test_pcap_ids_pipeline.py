from __future__ import annotations

from collections import Counter

import numpy as np

from ml.runtime.flow_tracker import FlowTracker
from ml.runtime.hierarchical_ids_engine import (
    HierarchicalIDSEngine,
)
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


def main() -> None:
    parser = TSharkPacketParser()

    tracker = FlowTracker(
        inactivity_timeout=60.0
    )

    engine = HierarchicalIDSEngine()

    packet_count = 0
    transport_counts = Counter()

    first_timestamp: float | None = None
    last_timestamp: float | None = None

    expired_flows = []

    # --------------------------------------------------------------
    # PCAP -> PACKETS -> FLOWS
    # --------------------------------------------------------------

    for packet in parser.parse_file(CAPTURE):
        packet_count += 1

        transport_counts[
            packet.transport
        ] += 1

        if first_timestamp is None:
            first_timestamp = packet.timestamp

        last_timestamp = packet.timestamp

        tracker.process_packet(packet)

        expired_flows.extend(
            tracker.expire_flows(
                packet.timestamp
            )
        )

    completed_flows = (
        expired_flows
        + tracker.close_all(
            reason="END_OF_CAPTURE"
        )
    )

    # --------------------------------------------------------------
    # Known capture integrity
    # --------------------------------------------------------------

    assert packet_count == 618
    assert transport_counts["TCP"] == 235
    assert transport_counts["UDP"] == 383
    assert len(completed_flows) == 17

    # --------------------------------------------------------------
    # FLOW -> FEATURES -> IDS
    # --------------------------------------------------------------

    decisions = []

    decision_path_counts = Counter()
    prediction_counts = Counter()

    for flow in completed_flows:
        features = flow.features

        if len(features) != len(
            INFERENCE_FEATURES
        ):
            raise AssertionError(
                "Flow feature count mismatch: "
                f"{len(features)} != "
                f"{len(INFERENCE_FEATURES)}"
            )

        if set(features) != set(
            INFERENCE_FEATURES
        ):
            missing = (
                set(INFERENCE_FEATURES)
                - set(features)
            )

            unexpected = (
                set(features)
                - set(INFERENCE_FEATURES)
            )

            raise AssertionError(
                "Flow feature schema mismatch. "
                f"Missing={sorted(missing)}, "
                f"Unexpected={sorted(unexpected)}"
            )

        for feature in INFERENCE_FEATURES:
            value = float(
                features[feature]
            )

            if not np.isfinite(value):
                raise AssertionError(
                    "Non-finite runtime feature: "
                    f"{feature}={value}"
                )

        decision = engine.predict(
            features
        )

        decisions.append(
            (flow, decision)
        )

        decision_path_counts[
            decision.decision_path
        ] += 1

        prediction_counts[
            decision.label
        ] += 1

    assert len(decisions) == len(
        completed_flows
    )

    # --------------------------------------------------------------
    # REPORT
    # --------------------------------------------------------------

    print("=" * 82)
    print(
        "CYBERLAB PCAP -> HIERARCHICAL IDS PIPELINE"
    )
    print("=" * 82)

    print()
    print(
        f"Capture:               {CAPTURE}"
    )

    print(
        f"Packets processed:     {packet_count:,}"
    )

    print(
        f"TCP packets:           "
        f"{transport_counts['TCP']:,}"
    )

    print(
        f"UDP packets:           "
        f"{transport_counts['UDP']:,}"
    )

    print(
        f"Completed flows:       "
        f"{len(completed_flows):,}"
    )

    print(
        f"Valid feature vectors: "
        f"{len(decisions):,}"
    )

    print(
        f"IDS decisions:         "
        f"{len(decisions):,}"
    )

    if (
        first_timestamp is not None
        and last_timestamp is not None
    ):
        duration = (
            last_timestamp
            - first_timestamp
        )

        print(
            f"Capture duration:      "
            f"{duration:.3f} s"
        )

    print()
    print("-" * 82)
    print("DECISION PATHS")
    print("-" * 82)

    known_paths = (
        "PRIMARY_BENIGN",
        "PRIMARY_ATTACK",
        "SPECIALIST_BENIGN",
        "SPECIALIST_ATTACK",
    )

    for path in known_paths:
        print(
            f"{path:<24} "
            f"{decision_path_counts[path]:>6}"
        )

    print()
    print("-" * 82)
    print("PREDICTIONS")
    print("-" * 82)

    print(
        f"{'BENIGN':<24} "
        f"{prediction_counts['BENIGN']:>6}"
    )

    print(
        f"{'ATTACK':<24} "
        f"{prediction_counts['ATTACK']:>6}"
    )

    print()
    print("-" * 82)
    print("FLOW DECISIONS")
    print("-" * 82)

    for index, (
        flow,
        decision,
    ) in enumerate(
        decisions,
        start=1,
    ):
        specialist_text = "-"

        if (
            decision.specialist_probability
            is not None
        ):
            specialist_text = (
                f"{decision.specialist_probability:.4f}"
            )

        print()
        print(
            f"Flow #{index:02d} | "
            f"{decision.label:<6} | "
            f"{decision.decision_path}"
        )

        print(
            f"  {flow.key.endpoint_a}"
            f" <-> "
            f"{flow.key.endpoint_b}"
        )

        print(
            f"  Protocol: "
            f"{flow.key.protocol}"
        )

        print(
            f"  Primary p:    "
            f"{decision.primary_probability:.4f}"
        )

        print(
            f"  Specialist p: "
            f"{specialist_text}"
        )

    print()
    print("-" * 82)
    print("PIPELINE INTEGRITY")
    print("-" * 82)

    print("Packet parsing:       OK")
    print("Flow extraction:      OK")
    print("57-feature contract:  OK")
    print("IDS inference:        OK")

    print()
    print("=" * 82)
    print(
        "PCAP -> HIERARCHICAL IDS PIPELINE: OK"
    )
    print("=" * 82)


if __name__ == "__main__":
    main()