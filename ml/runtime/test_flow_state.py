import math
import unittest

from ml.runtime.flow_state import FlowState
from ml.runtime.packet_record import PacketRecord


class FlowStateParityTests(unittest.TestCase):

    def test_tcp_payload_length_semantics(self):
        packet = PacketRecord(
            timestamp=1000.0,
            frame_length=100,
            src_ip="192.168.1.10",
            dst_ip="8.8.8.8",
            src_port=50000,
            dst_port=443,
            protocol=6,
            transport="TCP",
            tcp_payload_length=25,
        )

        self.assertEqual(packet.payload_length, 25)

    def test_udp_payload_length_semantics(self):
        packet = PacketRecord(
            timestamp=1000.0,
            frame_length=100,
            src_ip="192.168.1.10",
            dst_ip="8.8.8.8",
            src_port=50000,
            dst_port=53,
            protocol=17,
            transport="UDP",
            udp_length=28,
        )

        # TShark udp.length includes the 8-byte UDP header.
        self.assertEqual(packet.payload_length, 20)

    def test_global_packet_length_first_packet_duplication(self):
        packets = [
            PacketRecord(
                timestamp=1000.0,
                frame_length=100,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=10,
            ),
            PacketRecord(
                timestamp=1000.1,
                frame_length=120,
                src_ip="8.8.8.8",
                dst_ip="192.168.1.10",
                src_port=443,
                dst_port=50000,
                protocol=6,
                transport="TCP",
                tcp_payload_length=20,
            ),
            PacketRecord(
                timestamp=1000.3,
                frame_length=200,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=30,
            ),
        ]

        flow = FlowState(packets[0])

        for packet in packets[1:]:
            flow.add_packet(packet)

        features = flow.to_feature_dict()

        # CICFlowMeter global packet-length observations:
        #
        # first packet is added twice:
        # [10, 10, 20, 30]
        expected = [10.0, 10.0, 20.0, 30.0]

        expected_mean = sum(expected) / len(expected)

        expected_variance = sum(
            (value - expected_mean) ** 2
            for value in expected
        ) / (len(expected) - 1)

        expected_std = math.sqrt(expected_variance)

        self.assertEqual(
            flow.all_packet_lengths.count,
            4,
        )

        self.assertAlmostEqual(
            features["Packet Length Mean"],
            expected_mean,
        )

        self.assertAlmostEqual(
            features["Packet Length Variance"],
            expected_variance,
        )

        self.assertAlmostEqual(
            features["Packet Length Std"],
            expected_std,
        )

        self.assertEqual(
            features["Packet Length Min"],
            10.0,
        )

        self.assertEqual(
            features["Packet Length Max"],
            30.0,
        )

    def test_direction_and_payload_byte_totals(self):
        packets = [
            PacketRecord(
                timestamp=1000.0,
                frame_length=100,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=10,
            ),
            PacketRecord(
                timestamp=1000.1,
                frame_length=120,
                src_ip="8.8.8.8",
                dst_ip="192.168.1.10",
                src_port=443,
                dst_port=50000,
                protocol=6,
                transport="TCP",
                tcp_payload_length=20,
            ),
            PacketRecord(
                timestamp=1000.3,
                frame_length=200,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=30,
            ),
        ]

        flow = FlowState(packets[0])

        for packet in packets[1:]:
            flow.add_packet(packet)

        self.assertEqual(flow.fwd.packets, 2)
        self.assertEqual(flow.bwd.packets, 1)

        self.assertEqual(flow.fwd.bytes, 40)
        self.assertEqual(flow.bwd.bytes, 20)

        self.assertEqual(flow.total_packets, 3)
        self.assertEqual(flow.total_bytes, 60)

    def test_flow_and_directional_iat_microseconds(self):
        packets = [
            PacketRecord(
                timestamp=1000.0,
                frame_length=100,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=10,
            ),
            PacketRecord(
                timestamp=1000.1,
                frame_length=120,
                src_ip="8.8.8.8",
                dst_ip="192.168.1.10",
                src_port=443,
                dst_port=50000,
                protocol=6,
                transport="TCP",
                tcp_payload_length=20,
            ),
            PacketRecord(
                timestamp=1000.3,
                frame_length=200,
                src_ip="192.168.1.10",
                dst_ip="8.8.8.8",
                src_port=50000,
                dst_port=443,
                protocol=6,
                transport="TCP",
                tcp_payload_length=30,
            ),
        ]

        flow = FlowState(packets[0])

        for packet in packets[1:]:
            flow.add_packet(packet)

        features = flow.to_feature_dict()

        self.assertAlmostEqual(
            features["Flow Duration"],
            300_000.0,
            places=5,
        )

        self.assertAlmostEqual(
            features["Flow IAT Mean"],
            150_000.0,
            places=5,
        )

        self.assertAlmostEqual(
            features["Flow IAT Min"],
            100_000.0,
            places=5,
        )

        self.assertAlmostEqual(
            features["Flow IAT Max"],
            200_000.0,
            places=5,
        )

        # Forward packets occur at 1000.0 and 1000.3.
        self.assertAlmostEqual(
            features["Fwd IAT Mean"],
            300_000.0,
            places=5,
        )

        # Only one backward packet -> no backward IAT sample.
        self.assertEqual(
            features["Bwd IAT Mean"],
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
