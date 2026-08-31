from __future__ import annotations

from ml.runtime.cicflowmeter_compat import (
    CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    PRODUCTION_PROFILE,
    apply_cicflowmeter_compatibility,
)
from ml.runtime.packet_record import PacketRecord


def tcp_packet() -> PacketRecord:
    return PacketRecord(
        timestamp=1.25,
        frame_length=1500,
        src_ip="192.0.2.1",
        dst_ip="198.51.100.2",
        src_port=12345,
        dst_port=443,
        protocol=6,
        transport="TCP",
        tcp_syn=1,
        tcp_ack=1,
        tcp_fin=1,
        tcp_rst=1,
        tcp_psh=1,
        tcp_urg=1,
        tcp_cwr=1,
        tcp_ece=1,
        tcp_header_length=20,
        tcp_window_size=8192,
        tcp_payload_length=1460,
    )


packet = tcp_packet()

legacy_zero_length = apply_cicflowmeter_compatibility(
    packet,
    profile=CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    is_ipv4=True,
    raw_ipv4_total_length=0,
)

assert legacy_zero_length.timestamp == packet.timestamp
assert legacy_zero_length.frame_length == packet.frame_length
assert legacy_zero_length.src_ip == packet.src_ip
assert legacy_zero_length.dst_ip == packet.dst_ip
assert legacy_zero_length.src_port == 0
assert legacy_zero_length.dst_port == 0
assert legacy_zero_length.protocol == 0
assert legacy_zero_length.transport == "OTHER"
assert legacy_zero_length.payload_length == 0
assert legacy_zero_length.tcp_header_length == 0
assert legacy_zero_length.tcp_window_size == 0
assert legacy_zero_length.tcp_payload_length == 0
assert legacy_zero_length.udp_length == 0
assert not any(
    (
        legacy_zero_length.tcp_syn,
        legacy_zero_length.tcp_ack,
        legacy_zero_length.tcp_fin,
        legacy_zero_length.tcp_rst,
        legacy_zero_length.tcp_psh,
        legacy_zero_length.tcp_urg,
        legacy_zero_length.tcp_cwr,
        legacy_zero_length.tcp_ece,
    )
)

legacy_normal_length = apply_cicflowmeter_compatibility(
    packet,
    profile=CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    is_ipv4=True,
    raw_ipv4_total_length=1500,
)
assert legacy_normal_length is packet

production_zero_length = apply_cicflowmeter_compatibility(
    packet,
    profile=PRODUCTION_PROFILE,
    is_ipv4=True,
    raw_ipv4_total_length=0,
)
assert production_zero_length is packet

ipv6_zero_length = apply_cicflowmeter_compatibility(
    packet,
    profile=CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    is_ipv4=False,
    raw_ipv4_total_length=0,
)
assert ipv6_zero_length is packet

udp_packet = PacketRecord(
    timestamp=2.0,
    frame_length=128,
    src_ip="192.0.2.10",
    dst_ip="198.51.100.20",
    src_port=5353,
    dst_port=5353,
    protocol=17,
    transport="UDP",
    udp_length=94,
)

legacy_udp = apply_cicflowmeter_compatibility(
    udp_packet,
    profile=CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    is_ipv4=True,
    raw_ipv4_total_length=0,
)
assert legacy_udp is udp_packet

print("CICFlowMeter compatibility unit tests: OK")
