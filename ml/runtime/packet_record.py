from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PacketRecord:
    """
    TShark'tan alınan tek bir ağ paketinin
    CyberLab IDS tarafından kullanılan normalize edilmiş hali.

    Bu sınıf ML feature içermez.
    Yalnızca ham packet-level bilgiyi temsil eder.
    """

    timestamp: float
    frame_length: int

    src_ip: str
    dst_ip: str

    src_port: int
    dst_port: int

    protocol: int

    transport: str

    tcp_syn: int = 0
    tcp_ack: int = 0
    tcp_fin: int = 0
    tcp_rst: int = 0
    tcp_psh: int = 0
    tcp_urg: int = 0
    tcp_cwr: int = 0
    tcp_ece: int = 0

    tcp_header_length: int = 0
    tcp_window_size: int = 0
    tcp_payload_length: int = 0

    udp_length: int = 0

    @property
    def is_tcp(self) -> bool:
        return self.transport == "TCP"

    @property
    def is_udp(self) -> bool:
        return self.transport == "UDP"

    def validate(self) -> None:
        if self.timestamp < 0:
            raise ValueError(
                "Packet timestamp negatif olamaz."
            )

        if self.frame_length < 0:
            raise ValueError(
                "Frame length negatif olamaz."
            )

        if not 0 <= self.src_port <= 65535:
            raise ValueError(
                f"Geçersiz source port: {self.src_port}"
            )

        if not 0 <= self.dst_port <= 65535:
            raise ValueError(
                f"Geçersiz destination port: {self.dst_port}"
            )

        if self.transport not in {
            "TCP",
            "UDP",
            "OTHER",
        }:
            raise ValueError(
                f"Desteklenmeyen transport: {self.transport}"
            )