from __future__ import annotations

from collections import Counter

from ml.runtime.flow_tracker import FlowTracker
from ml.runtime.tshark_packet_parser import (
    TSharkPacketParser,
)


CAPTURE = (
    "captures/lab/"
    "cyberlab_ip_parity_test.pcapng"
)


parser = TSharkPacketParser()

tracker = FlowTracker(
    inactivity_timeout=60.0
)

packet_count = 0
transport_counts = Counter()

first_timestamp: float | None = None
last_timestamp: float | None = None

expired_flows = []


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


assert packet_count == 618

assert (
    transport_counts["TCP"]
    == 235
)

assert (
    transport_counts["UDP"]
    == 383
)

assert completed_flows


print("=" * 70)
print("CYBERLAB PCAP → FLOW PIPELINE TEST")
print("=" * 70)

print()
print(
    f"Packets processed: "
    f"{packet_count:,}"
)

print(
    f"TCP packets:       "
    f"{transport_counts['TCP']:,}"
)

print(
    f"UDP packets:       "
    f"{transport_counts['UDP']:,}"
)

print(
    f"Completed flows:   "
    f"{len(completed_flows):,}"
)

if (
    first_timestamp is not None
    and last_timestamp is not None
):
    capture_duration = (
        last_timestamp
        - first_timestamp
    )

    print(
        f"Capture duration:  "
        f"{capture_duration:.3f} s"
    )


reason_counts = Counter(
    flow.reason
    for flow in completed_flows
)

print()
print("Flow completion reasons:")

for reason, count in sorted(
    reason_counts.items()
):
    print(
        f"  {reason:<25} "
        f"{count:>6}"
    )


feature_counts = Counter(
    len(flow.features)
    for flow in completed_flows
)

print()
print(
    "Feature-vector sizes:"
)

for size, count in sorted(
    feature_counts.items()
):
    print(
        f"  {size:>3} features -> "
        f"{count:>6} flows"
    )


assert set(feature_counts) == {57}


print()
print("-" * 70)
print("FIRST FIVE FLOWS")
print("-" * 70)

for index, flow in enumerate(
    completed_flows[:5],
    start=1,
):
    features = flow.features

    print()
    print(
        f"Flow #{index}"
    )

    print(
        "  Endpoint A:",
        flow.key.endpoint_a,
    )

    print(
        "  Endpoint B:",
        flow.key.endpoint_b,
    )

    print(
        "  Protocol:  ",
        flow.key.protocol,
    )

    print(
        "  Duration:  ",
        f"{features['Flow Duration']:.0f} µs",
    )

    print(
        "  Fwd Pkts:  ",
        int(
            features[
                "Total Fwd Packet"
            ]
        ),
    )

    print(
        "  Bwd Pkts:  ",
        int(
            features[
                "Total Bwd packets"
            ]
        ),
    )

    print(
        "  Bytes/s:   ",
        f"{features['Flow Bytes/s']:.2f}",
    )

    print(
        "  Packets/s: ",
        f"{features['Flow Packets/s']:.2f}",
    )


print()
print("=" * 70)
print("END-TO-END FLOW PIPELINE: OK")
print("=" * 70)
