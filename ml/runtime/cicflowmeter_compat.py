from __future__ import annotations

from dataclasses import replace
from typing import Literal

from ml.runtime.packet_record import PacketRecord


ParserProfile = Literal[
    "production",
    "cicflowmeter_jnetpcap_1_4",
]

PRODUCTION_PROFILE: ParserProfile = "production"
CICFLOWMETER_JNETPCAP_1_4_PROFILE: ParserProfile = (
    "cicflowmeter_jnetpcap_1_4"
)

SUPPORTED_PROFILES = {
    PRODUCTION_PROFILE,
    CICFLOWMETER_JNETPCAP_1_4_PROFILE,
}


def apply_cicflowmeter_compatibility(
    packet: PacketRecord,
    *,
    profile: ParserProfile,
    is_ipv4: bool,
    raw_ipv4_total_length: int | None,
) -> PacketRecord:
    """Apply explicitly selected legacy packet-decoder semantics."""

    if profile not in SUPPORTED_PROFILES:
        raise ValueError(
            f"Desteklenmeyen parser profile: {profile}"
        )

    if (
        profile == PRODUCTION_PROFILE
        or not is_ipv4
        or not packet.is_tcp
        or raw_ipv4_total_length != 0
    ):
        return packet

    legacy_packet = replace(
        packet,
        src_port=0,
        dst_port=0,
        protocol=0,
        transport="OTHER",
        tcp_syn=0,
        tcp_ack=0,
        tcp_fin=0,
        tcp_rst=0,
        tcp_psh=0,
        tcp_urg=0,
        tcp_cwr=0,
        tcp_ece=0,
        tcp_header_length=0,
        tcp_window_size=0,
        tcp_payload_length=0,
        udp_length=0,
    )

    legacy_packet.validate()
    return legacy_packet
