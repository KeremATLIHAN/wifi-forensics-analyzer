from __future__ import annotations

from dataclasses import dataclass

from ml.runtime.packet_record import PacketRecord


@dataclass(
    slots=True,
    frozen=True,
    order=True,
)
class Endpoint:
    ip: str
    port: int


@dataclass(
    slots=True,
    frozen=True,
)
class FlowKey:
    """
    Bidirectional network flow kimliği.

    A -> B ile B -> A aynı FlowKey'i üretir.
    """

    endpoint_a: Endpoint
    endpoint_b: Endpoint
    protocol: int

    @classmethod
    def from_packet(
        cls,
        packet: PacketRecord,
    ) -> "FlowKey":

        source = Endpoint(
            ip=packet.src_ip,
            port=packet.src_port,
        )

        destination = Endpoint(
            ip=packet.dst_ip,
            port=packet.dst_port,
        )

        endpoint_a, endpoint_b = sorted(
            (source, destination)
        )

        return cls(
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
            protocol=packet.protocol,
        )

    def direction(
        self,
        packet: PacketRecord,
    ) -> str:
        """
        Canonical FlowKey'e göre paketin yönünü döndürür.
        """

        source = Endpoint(
            packet.src_ip,
            packet.src_port,
        )

        if source == self.endpoint_a:
            return "A_TO_B"

        return "B_TO_A"