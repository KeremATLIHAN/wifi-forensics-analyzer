from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from ml.runtime.flow_key import FlowKey
from ml.runtime.packet_record import PacketRecord


@dataclass
class RunningStats:
    count: int = 0
    total: float = 0.0
    total_sq: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.total_sq += value * value

        if self.minimum is None or value < self.minimum:
            self.minimum = value

        if self.maximum is None or value > self.maximum:
            self.maximum = value

    @property
    def mean(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total / self.count

    @property
    def variance(self) -> float:
        if self.count == 0:
            return 0.0

        value = (
            self.total_sq / self.count
            - self.mean * self.mean
        )

        return max(0.0, value)

    @property
    def std(self) -> float:
        return sqrt(self.variance)

    @property
    def min_value(self) -> float:
        return 0.0 if self.minimum is None else self.minimum

    @property
    def max_value(self) -> float:
        return 0.0 if self.maximum is None else self.maximum


@dataclass
class DirectionStats:
    packets: int = 0
    bytes: int = 0

    packet_lengths: RunningStats = field(
        default_factory=RunningStats
    )

    iat: RunningStats = field(
        default_factory=RunningStats
    )

    last_timestamp: float | None = None

    syn_count: int = 0
    ack_count: int = 0
    fin_count: int = 0
    rst_count: int = 0
    psh_count: int = 0
    urg_count: int = 0
    cwr_count: int = 0
    ece_count: int = 0

    header_length_total: int = 0

    def add_packet(
        self,
        packet: PacketRecord,
    ) -> None:
        self.packets += 1
        self.bytes += packet.payload_length

        self.packet_lengths.add(
            float(packet.payload_length)
        )

        if self.last_timestamp is not None:
            delta = (
                packet.timestamp
                - self.last_timestamp
            ) * 1_000_000.0

            if delta >= 0:
                self.iat.add(delta)

        self.last_timestamp = packet.timestamp

        self.syn_count += packet.tcp_syn
        self.ack_count += packet.tcp_ack
        self.fin_count += packet.tcp_fin
        self.rst_count += packet.tcp_rst
        self.psh_count += packet.tcp_psh
        self.urg_count += packet.tcp_urg
        self.cwr_count += packet.tcp_cwr
        self.ece_count += packet.tcp_ece

        self.header_length_total += (
            packet.tcp_header_length
        )


class FlowState:
    """
    Tek bir bidirectional flow'un canlı durumunu tutar.

    Fwd/Bwd yönü ilk görülen pakete göre belirlenir.
    """

    def __init__(
        self,
        first_packet: PacketRecord,
    ) -> None:
        first_packet.validate()

        self.key = FlowKey.from_packet(
            first_packet
        )

        self.first_timestamp = (
            first_packet.timestamp
        )

        self.last_timestamp = (
            first_packet.timestamp
        )

        self.forward_source_ip = (
            first_packet.src_ip
        )
        self.forward_source_port = (
            first_packet.src_port
        )
        self.forward_destination_ip = (
            first_packet.dst_ip
        )
        self.forward_destination_port = (
            first_packet.dst_port
        )

        self.fwd_initial_window: int | None = None
        self.bwd_initial_window: int | None = None

        self.fwd_active_data_packets = 0

        self.fwd_segment_size_min: int | None = None

        self.fwd = DirectionStats()
        self.bwd = DirectionStats()

        self.all_packet_lengths = RunningStats()

        # CICFlowMeter parity:
        # The first forward packet contributes an additional
        # observation to global packet-length statistics.
        self.all_packet_lengths.add(
            float(first_packet.payload_length)
        )

        self.flow_iat = RunningStats()

        self.last_flow_packet_timestamp: (
            float | None
        ) = None

        self.add_packet(first_packet)

    def _is_forward(
        self,
        packet: PacketRecord,
    ) -> bool:
        return (
            packet.src_ip
            == self.forward_source_ip
            and packet.src_port
            == self.forward_source_port
        )

    def add_packet(
        self,
        packet: PacketRecord,
    ) -> None:
        packet.validate()

        packet_key = FlowKey.from_packet(
            packet
        )

        if packet_key != self.key:
            raise ValueError(
                "Packet bu FlowState'e ait değil."
            )

        if self.last_flow_packet_timestamp is not None:
            delta = (
                packet.timestamp
                - self.last_flow_packet_timestamp
            ) * 1_000_000.0

            if delta >= 0:
                self.flow_iat.add(delta)

        self.last_flow_packet_timestamp = (
            packet.timestamp
        )

        self.last_timestamp = max(
            self.last_timestamp,
            packet.timestamp,
        )

        self.all_packet_lengths.add(
            float(packet.payload_length)
        )

        if self._is_forward(packet):
            self.fwd.add_packet(packet)

            if (
                packet.is_tcp
                and self.fwd_initial_window is None
            ):
                self.fwd_initial_window = (
                    packet.tcp_window_size
                )

            if (
                packet.is_tcp
                and packet.tcp_payload_length > 0
            ):
                self.fwd_active_data_packets += 1

            if packet.is_tcp:
                segment_size = (
                    packet.tcp_header_length
                )

                if (
                    self.fwd_segment_size_min is None
                    or segment_size
                    < self.fwd_segment_size_min
                ):
                    self.fwd_segment_size_min = (
                        segment_size
                    )

        else:
            self.bwd.add_packet(packet)

            if (
                packet.is_tcp
                and self.bwd_initial_window is None
            ):
                self.bwd_initial_window = (
                    packet.tcp_window_size
                )

    @property
    def flow_duration_seconds(self) -> float:
        return max(
            0.0,
            self.last_timestamp
            - self.first_timestamp,
        )

    @property
    def flow_duration_microseconds(self) -> float:
        return self.flow_duration_seconds * 1_000_000.0

    @property
    def total_packets(self) -> int:
        return (
            self.fwd.packets
            + self.bwd.packets
        )

    @property
    def total_bytes(self) -> int:
        return (
            self.fwd.bytes
            + self.bwd.bytes
        )

    def to_feature_dict(self) -> dict[str, float]:
        duration_seconds = self.flow_duration_seconds

        flow_bytes_per_sec = (
            self.total_bytes / duration_seconds
            if duration_seconds > 0
            else 0.0
        )

        flow_packets_per_sec = (
            self.total_packets / duration_seconds
            if duration_seconds > 0
            else 0.0
        )

        fwd_packets_per_sec = (
            self.fwd.packets / duration_seconds
            if duration_seconds > 0
            else 0.0
        )

        bwd_packets_per_sec = (
            self.bwd.packets / duration_seconds
            if duration_seconds > 0
            else 0.0
        )

        return {
            "Src Port":
                self.forward_source_port,

            "Dst Port":
                self.forward_destination_port,

            "Flow Duration":
                self.flow_duration_microseconds,

            "Total Fwd Packet":
                self.fwd.packets,

            "Total Bwd packets":
                self.bwd.packets,

            "Total Length of Fwd Packet":
                self.fwd.bytes,

            "Total Length of Bwd Packet":
                self.bwd.bytes,

            "Fwd Packet Length Max":
                self.fwd.packet_lengths.max_value,

            "Fwd Packet Length Min":
                self.fwd.packet_lengths.min_value,

            "Fwd Packet Length Mean":
                self.fwd.packet_lengths.mean,

            "Fwd Packet Length Std":
                self.fwd.packet_lengths.std,

            "Bwd Packet Length Max":
                self.bwd.packet_lengths.max_value,

            "Bwd Packet Length Min":
                self.bwd.packet_lengths.min_value,

            "Bwd Packet Length Mean":
                self.bwd.packet_lengths.mean,

            "Bwd Packet Length Std":
                self.bwd.packet_lengths.std,

            "Fwd Segment Size Avg":
                self.fwd.packet_lengths.mean,

            "Bwd Segment Size Avg":
                self.bwd.packet_lengths.mean,

            "Down/Up Ratio":
                (
                    self.bwd.packets
                    // self.fwd.packets
                    if self.fwd.packets > 0
                    else 0
                ),

            "Flow Bytes/s":
                flow_bytes_per_sec,

            "Flow Packets/s":
                flow_packets_per_sec,

            "Fwd Packets/s":
                fwd_packets_per_sec,

            "Bwd Packets/s":
                bwd_packets_per_sec,

            "Fwd Header Length":
                self.fwd.header_length_total,

            "Bwd Header Length":
                self.bwd.header_length_total,

            "Fwd PSH Flags":
                self.fwd.psh_count,

            "Fwd URG Flags":
                self.fwd.urg_count,

            "FWD Init Win Bytes":
                (
                    self.fwd_initial_window
                    if self.fwd_initial_window is not None
                    else 0
                ),

            "Bwd Init Win Bytes":
                (
                    self.bwd_initial_window
                    if self.bwd_initial_window is not None
                    else 0
                ),

            "Fwd Act Data Pkts":
                self.fwd_active_data_packets,

            "Fwd Seg Size Min":
                (
                    self.fwd_segment_size_min
                    if self.fwd_segment_size_min is not None
                    else 0
                ),

            "Packet Length Min":
                self.all_packet_lengths.min_value,

            "Packet Length Max":
                self.all_packet_lengths.max_value,

            "Packet Length Mean":
                self.all_packet_lengths.mean,

            "Packet Length Std":
                self.all_packet_lengths.std,

            "Packet Length Variance":
                self.all_packet_lengths.variance,

            "FIN Flag Count":
                self.fwd.fin_count
                + self.bwd.fin_count,

            "SYN Flag Count":
                self.fwd.syn_count
                + self.bwd.syn_count,

            "RST Flag Count":
                self.fwd.rst_count
                + self.bwd.rst_count,

            "PSH Flag Count":
                self.fwd.psh_count
                + self.bwd.psh_count,

            "ACK Flag Count":
                self.fwd.ack_count
                + self.bwd.ack_count,

            "URG Flag Count":
                self.fwd.urg_count
                + self.bwd.urg_count,

            "CWR Flag Count":
                self.fwd.cwr_count
                + self.bwd.cwr_count,

            "ECE Flag Count":
                self.fwd.ece_count
                + self.bwd.ece_count,

            "Flow IAT Mean":
                self.flow_iat.mean,

            "Flow IAT Std":
                self.flow_iat.std,

            "Flow IAT Max":
                self.flow_iat.max_value,

            "Flow IAT Min":
                self.flow_iat.min_value,

            "Fwd IAT Total":
                self.fwd.iat.total,

            "Fwd IAT Mean":
                self.fwd.iat.mean,

            "Fwd IAT Std":
                self.fwd.iat.std,

            "Fwd IAT Max":
                self.fwd.iat.max_value,

            "Fwd IAT Min":
                self.fwd.iat.min_value,

            "Bwd IAT Total":
                self.bwd.iat.total,

            "Bwd IAT Mean":
                self.bwd.iat.mean,

            "Bwd IAT Std":
                self.bwd.iat.std,

            "Bwd IAT Max":
                self.bwd.iat.max_value,

            "Bwd IAT Min":
                self.bwd.iat.min_value,
        }
