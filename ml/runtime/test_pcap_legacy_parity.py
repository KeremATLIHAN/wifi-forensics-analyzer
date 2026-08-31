from __future__ import annotations

from collections import Counter

from ml.runtime.cicflowmeter_compat import (
    CICFLOWMETER_JNETPCAP_1_4_PROFILE,
)
from ml.runtime.flow_tracker import FlowTracker
from ml.runtime.tshark_packet_parser import TSharkPacketParser


CAPTURE = (
    "captures/lab/"
    "cyberlab_ip_parity_test.pcapng"
)


def completed_flows(profile: str):
    parser = TSharkPacketParser(profile=profile)
    tracker = FlowTracker(inactivity_timeout=60.0)
    completed = []
    packet_count = 0

    for packet in parser.parse_file(CAPTURE):
        packet_count += 1
        tracker.process_packet(packet)
        completed.extend(
            tracker.expire_flows(packet.timestamp)
        )

    completed.extend(
        tracker.close_all(reason="END_OF_CAPTURE")
    )
    return packet_count, completed


production_count, production_flows = completed_flows(
    "production"
)
legacy_count, legacy_flows = completed_flows(
    CICFLOWMETER_JNETPCAP_1_4_PROFILE
)

assert production_count == legacy_count == 618

production_reason_counts = Counter(
    flow.reason
    for flow in production_flows
)
assert production_reason_counts == {
    "TCP_FIN": 5,
    "TCP_RST": 1,
    "END_OF_CAPTURE": 17,
}


def matching_flow(flows, protocol, ports):
    matches = [
        flow
        for flow in flows
        if flow.key.protocol == protocol
        and {
            flow.key.endpoint_a.port,
            flow.key.endpoint_b.port,
        }
        == ports
        and {
            flow.key.endpoint_a.ip,
            flow.key.endpoint_b.ip,
        }
        == {"172.20.10.9", "172.64.155.209"}
    ]
    assert len(matches) == 1
    return matches[0]


production_tcp = matching_flow(
    production_flows,
    6,
    {443, 52658},
)
legacy_tcp = matching_flow(
    legacy_flows,
    6,
    {443, 52658},
)
legacy_other = matching_flow(
    legacy_flows,
    0,
    {0},
)

assert production_tcp.features["Total Fwd Packet"] == 18
assert production_tcp.features["Total Bwd packets"] == 33
assert legacy_tcp.features["Total Fwd Packet"] == 14
assert legacy_tcp.features["Total Bwd packets"] == 33
assert legacy_other.features["Total Fwd Packet"] == 4
assert legacy_other.features["Total Bwd packets"] == 0
assert round(legacy_other.features["Flow Duration"]) == 9463610

reason_counts = Counter(
    flow.reason
    for flow in legacy_flows
)
print("Legacy completion reasons:", dict(reason_counts))
assert reason_counts["TCP_FIN"] == 5
assert reason_counts["TCP_RST"] == 1
assert reason_counts["END_OF_CAPTURE"] == 19

print("Production 52658: 18 FWD / 33 BWD")
print("Legacy 52658:     14 FWD / 33 BWD")
print("Legacy proto=0:   4 FWD / 0 BWD")
print(
    "Legacy proto=0 duration: ",
    f"{legacy_other.features['Flow Duration']:.0f} us",
    sep="",
)
print("Packets: production=618 legacy=618")
print(
    "Production completion reasons:",
    dict(production_reason_counts),
)
