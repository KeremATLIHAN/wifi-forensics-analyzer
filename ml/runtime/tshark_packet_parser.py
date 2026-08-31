from __future__ import annotations

import csv
import io
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

from ml.runtime.cicflowmeter_compat import (
    CICFLOWMETER_JNETPCAP_1_4_PROFILE,
    PRODUCTION_PROFILE,
    SUPPORTED_PROFILES,
    ParserProfile,
    apply_cicflowmeter_compatibility,
)
from ml.runtime.packet_record import PacketRecord


class TSharkPacketParser:
    """
    PCAP/PCAPNG içindeki IPv4 TCP/UDP paketlerini
    CyberLab PacketRecord nesnelerine dönüştürür.
    """

    FIELDS = [
        "frame.time_epoch",
        "frame.len",
        "ip.src",
        "ip.dst",
        "ip.proto",
        "tcp.srcport",
        "tcp.dstport",
        "udp.srcport",
        "udp.dstport",
        "tcp.flags.syn",
        "tcp.flags.ack",
        "tcp.flags.fin",
        "tcp.flags.reset",
        "tcp.flags.push",
        "tcp.flags.urg",
        "tcp.flags.cwr",
        "tcp.flags.ece",
        "tcp.hdr_len",
        "tcp.window_size_value",
        "tcp.len",
        "udp.length",
    ]

    def __init__(
        self,
        tshark_path: str = "tshark",
        profile: ParserProfile = PRODUCTION_PROFILE,
    ) -> None:
        if profile not in SUPPORTED_PROFILES:
            raise ValueError(
                f"Desteklenmeyen parser profile: {profile}"
            )

        self.tshark_path = tshark_path
        self.profile = profile

    @staticmethod
    def _int(
        value: str,
        default: int = 0,
    ) -> int:
        value = value.strip()

        if not value:
            return default

        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def _float(
        value: str,
        default: float = 0.0,
    ) -> float:
        value = value.strip()

        if not value:
            return default

        try:
            return float(value)
        except ValueError:
            return default

    def parse_file(
        self,
        capture_path: str | Path,
    ) -> Iterator[PacketRecord]:

        path = Path(capture_path)

        if not path.exists():
            raise FileNotFoundError(path)

        raw_ipv4_lengths: Iterator[int | None] | None = None

        if self.profile == CICFLOWMETER_JNETPCAP_1_4_PROFILE:
            raw_ipv4_lengths = self._raw_ipv4_total_lengths(
                path
            )

        command = [
            self.tshark_path,
            "-r",
            str(path),
            "-Y",
            "ip && (tcp || udp)",
            "-T",
            "fields",
            "-E",
            "separator=\t",
            "-E",
            "quote=n",
            "-E",
            "occurrence=f",
        ]

        for field in self.FIELDS:
            command.extend(
                ["-e", field]
            )

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert process.stdout is not None

        reader = csv.reader(
            process.stdout,
            delimiter="\t",
        )

        try:
            for row in reader:
                if len(row) != len(self.FIELDS):
                    continue

                (
                    timestamp,
                    frame_length,
                    src_ip,
                    dst_ip,
                    protocol,
                    tcp_src_port,
                    tcp_dst_port,
                    udp_src_port,
                    udp_dst_port,
                    tcp_syn,
                    tcp_ack,
                    tcp_fin,
                    tcp_rst,
                    tcp_psh,
                    tcp_urg,
                    tcp_cwr,
                    tcp_ece,
                    tcp_header_length,
                    tcp_window_size,
                    tcp_payload_length,
                    udp_length,
                ) = row

                protocol_number = self._int(
                    protocol
                )

                if protocol_number == 6:
                    transport = "TCP"

                    src_port = self._int(
                        tcp_src_port
                    )
                    dst_port = self._int(
                        tcp_dst_port
                    )

                elif protocol_number == 17:
                    transport = "UDP"

                    src_port = self._int(
                        udp_src_port
                    )
                    dst_port = self._int(
                        udp_dst_port
                    )

                else:
                    continue

                packet = PacketRecord(
                    timestamp=self._float(
                        timestamp
                    ),
                    frame_length=self._int(
                        frame_length
                    ),
                    src_ip=src_ip.strip(),
                    dst_ip=dst_ip.strip(),
                    src_port=src_port,
                    dst_port=dst_port,
                    protocol=protocol_number,
                    transport=transport,
                    tcp_syn=self._int(tcp_syn),
                    tcp_ack=self._int(tcp_ack),
                    tcp_fin=self._int(tcp_fin),
                    tcp_rst=self._int(tcp_rst),
                    tcp_psh=self._int(tcp_psh),
                    tcp_urg=self._int(tcp_urg),
                    tcp_cwr=self._int(tcp_cwr),
                    tcp_ece=self._int(tcp_ece),
                    tcp_header_length=self._int(
                        tcp_header_length
                    ),
                    tcp_window_size=self._int(
                        tcp_window_size
                    ),
                    tcp_payload_length=self._int(
                        tcp_payload_length
                    ),
                    udp_length=self._int(
                        udp_length
                    ),
                )

                packet.validate()

                if raw_ipv4_lengths is not None:
                    try:
                        raw_ipv4_total_length = next(
                            raw_ipv4_lengths
                        )
                    except StopIteration as error:
                        raise RuntimeError(
                            "TShark raw IPv4 metadata packet "
                            "akışından önce sona erdi."
                        ) from error

                    packet = apply_cicflowmeter_compatibility(
                        packet,
                        profile=self.profile,
                        is_ipv4=True,
                        raw_ipv4_total_length=(
                            raw_ipv4_total_length
                        ),
                    )

                yield packet

            if raw_ipv4_lengths is not None:
                try:
                    next(raw_ipv4_lengths)
                except StopIteration:
                    pass
                else:
                    raise RuntimeError(
                        "TShark raw IPv4 metadata akışında "
                        "fazladan paket bulundu."
                    )

        finally:
            if process.stdout:
                process.stdout.close()

            stderr = ""

            if process.stderr:
                stderr = process.stderr.read()
                process.stderr.close()

            return_code = process.wait()

            if return_code != 0:
                raise RuntimeError(
                    "TShark packet parsing failed:\n"
                    + stderr
                )

    def _raw_ipv4_total_lengths(
        self,
        path: Path,
    ) -> Iterator[int | None]:
        """Stream raw IPv4 Total Length values from TShark PDML."""

        command = [
            self.tshark_path,
            "-r",
            str(path),
            "-Y",
            "ip && (tcp || udp)",
            "-T",
            "pdml",
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert process.stdout is not None

        try:
            for _, element in ET.iterparse(
                process.stdout,
                events=("end",),
            ):
                if element.tag != "packet":
                    continue

                raw_total_length: int | None = None

                for field in element.iter("field"):
                    if field.get("name") != "ip.len":
                        continue

                    raw_value = field.get("value")

                    if raw_value:
                        try:
                            raw_total_length = int(
                                raw_value,
                                16,
                            )
                        except ValueError as error:
                            raise RuntimeError(
                                "Geçersiz ham IPv4 Total "
                                f"Length değeri: {raw_value}"
                            ) from error

                    break

                if raw_total_length is None:
                    raise RuntimeError(
                        "TShark PDML çıktısında ham IPv4 "
                        "Total Length bulunamadı."
                    )

                element.clear()
                yield raw_total_length

        finally:
            process.stdout.close()

            stderr = b""

            if process.stderr:
                stderr = process.stderr.read()
                process.stderr.close()

            return_code = process.wait()

            if return_code != 0:
                raise RuntimeError(
                    "TShark raw IPv4 metadata parsing failed:\n"
                    + stderr.decode(
                        "utf-8",
                        errors="replace",
                    )
                )
