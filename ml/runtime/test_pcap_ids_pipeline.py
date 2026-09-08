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
    assert len(completed_flows) == 23

    completion_reason_counts = Counter(
        flow.reason
        for flow in completed_flows
    )

    assert completion_reason_counts == {
        "TCP_FIN": 5,
        "TCP_RST": 1,
        "END_OF_CAPTURE": 17,
    }
    assert completion_reason_counts["FLOW_TIMEOUT"] == 0

    flow_55222 = [
        flow
        for flow in completed_flows
        if flow.key.protocol == 6
        and {
            flow.key.endpoint_a.ip,
            flow.key.endpoint_b.ip,
        }
        == {
            "140.82.121.5",
            "172.20.10.9",
        }
        and {
            flow.key.endpoint_a.port,
            flow.key.endpoint_b.port,
        }
        == {443, 55222}
    ]

    assert len(flow_55222) == 3

    flow_55222_by_reason = {
        flow.reason: flow
        for flow in flow_55222
    }

    assert set(flow_55222_by_reason) == {
        "TCP_FIN",
        "TCP_RST",
        "END_OF_CAPTURE",
    }

    expected_55222 = {
        "TCP_FIN": (1, 1, 495),
        "TCP_RST": (1, 1, 208),
        "END_OF_CAPTURE": (2, 0, 424854),
    }

    for reason, expected in expected_55222.items():
        features = flow_55222_by_reason[reason].features
        actual = (
            int(features["Total Fwd Packet"]),
            int(features["Total Bwd packets"]),
            round(features["Flow Duration"]),
        )
        assert actual == expected

    continuation_endpoints = {
        55224: {
            "104.18.32.47",
            "172.20.10.9",
        },
        53019: {
            "172.20.10.9",
            "52.123.244.40",
        },
        54099: {
            "172.20.10.9",
            "4.207.44.71",
        },
        54102: {
            "172.20.10.9",
            "20.184.175.16",
        },
    }

    for client_port, endpoint_ips in (
        continuation_endpoints.items()
    ):
        matches = [
            flow
            for flow in completed_flows
            if flow.key.protocol == 6
            and flow.reason == "END_OF_CAPTURE"
            and {
                flow.key.endpoint_a.ip,
                flow.key.endpoint_b.ip,
            }
            == endpoint_ips
            and {
                flow.key.endpoint_a.port,
                flow.key.endpoint_b.port,
            }
            == {443, client_port}
        ]

        assert len(matches) == 1

        features = matches[0].features
        fwd_packets = int(
            features["Total Fwd Packet"]
        )
        bwd_packets = int(
            features["Total Bwd packets"]
        )

        assert fwd_packets == 1
        assert bwd_packets == 0
        assert fwd_packets + bwd_packets == 1

    # --------------------------------------------------------------
    # FLOW -> FEATURES -> IDS
    # --------------------------------------------------------------

    decisions = []
    skipped = []
    valid_feature_vectors = 0

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

        valid_feature_vectors += 1

        decision = engine.predict(
            features
        )

        if decision is None:
            skipped.append(flow)
            continue

        decisions.append(
            (flow, decision)
        )

        decision_path_counts[
            decision.decision_path
        ] += 1

        prediction_counts[
            decision.label
        ] += 1

    assert len(decisions) == 19
    assert len(skipped) == 4
    assert valid_feature_vectors == 23
    assert len(decisions) + len(skipped) == len(
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
        f"{valid_feature_vectors:,}"
    )

    print(
        f"IDS decisions:         "
        f"{len(decisions):,}"
    )

    print(
        f"Inference skipped:      "
        f"{len(skipped):,}"
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
