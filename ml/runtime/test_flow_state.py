import math
import unittest

from ml.runtime.flow_state import FlowState
from ml.runtime.flow_tracker import FlowTracker
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


class FeatureContractRegressionTests(unittest.TestCase):
    @staticmethod
    def packet(timestamp, payload=0, backward=False, udp=False):
        source = ("192.168.1.10", 50000)
        destination = ("8.8.8.8", 443)
        if backward:
            source, destination = destination, source
        return PacketRecord(
            timestamp=timestamp,
            frame_length=100 + payload,
            src_ip=source[0], dst_ip=destination[0],
            src_port=source[1], dst_port=destination[1],
            protocol=17 if udp else 6,
            transport="UDP" if udp else "TCP",
            tcp_payload_length=0 if udp else payload,
            udp_length=payload + 8 if udp else 0,
            tcp_ack=0 if udp else 1,
            tcp_header_length=0 if udp else 20,
            tcp_window_size=0 if udp else 4096,
        )

    def test_active_data_excludes_only_first_flow_packet(self):
        flow = FlowState(self.packet(1.0, 10))
        self.assertEqual(flow.to_feature_dict()["Fwd Act Data Pkts"], 0)
        self.assertEqual(flow.fwd.packets, 1)
        self.assertEqual(flow.fwd.bytes, 10)
        self.assertEqual(flow.fwd.ack_count, 1)
        self.assertEqual(flow.fwd.header_length_total, 20)
        self.assertEqual(flow.fwd_initial_window, 4096)
        self.assertEqual(flow.all_packet_lengths.count, 2)
        self.assertEqual(flow.all_packet_lengths.total, 20)
        for timestamp, payload, backward, expected in (
            (1.1, 20, False, 1),
            (1.2, 30, True, 1),
            (1.3, 0, False, 1),
            (1.4, 40, False, 2),
        ):
            flow.add_packet(self.packet(timestamp, payload, backward))
            self.assertEqual(flow.to_feature_dict()["Fwd Act Data Pkts"], expected)
        empty_first = FlowState(self.packet(1.0))
        empty_first.add_packet(self.packet(1.1, 20))
        self.assertEqual(empty_first.fwd_active_data_packets, 1)

    def test_udp_active_data_scope_unchanged(self):
        flow = FlowState(self.packet(1.0, 10, udp=True))
        flow.add_packet(self.packet(1.1, 20, udp=True))
        self.assertEqual(flow.fwd_active_data_packets, 0)
        self.assertEqual(flow.fwd.bytes, 30)

    def assert_iat(self, stats, samples):
        self.assertEqual(stats.count, len(samples))
        self.assertAlmostEqual(stats.total, sum(samples), places=5)
        self.assertAlmostEqual(stats.min_value, min(samples), places=5)
        self.assertAlmostEqual(stats.max_value, max(samples), places=5)
        mean = sum(samples) / len(samples)
        self.assertAlmostEqual(stats.mean, mean, places=5)
        variance = (
            sum((value - mean) ** 2 for value in samples) / (len(samples) - 1)
            if len(samples) > 1 else 0.0
        )
        self.assertAlmostEqual(stats.std, math.sqrt(variance), places=5)

    def test_signed_global_and_forward_iat(self):
        flow = FlowState(self.packet(1.0))
        self.assertEqual(flow.flow_iat.count, 0)
        self.assertEqual(flow.fwd.iat.count, 0)
        for timestamp in (1.1, 1.05):
            flow.add_packet(self.packet(timestamp))
        self.assertEqual(flow.last_flow_packet_timestamp, 1.05)
        self.assertEqual(flow.fwd.last_timestamp, 1.05)
        flow.add_packet(self.packet(1.2))
        samples = [100000, -50000, 150000]
        self.assert_iat(flow.flow_iat, samples)
        self.assert_iat(flow.fwd.iat, samples)
        features = flow.to_feature_dict()
        for prefix in ("Flow", "Fwd"):
            for suffix, expected in (
                ("Min", -50000), ("Max", 150000),
                ("Mean", 200000 / 3), ("Std", math.sqrt(32500000000 / 3)),
            ):
                self.assertAlmostEqual(features[f"{prefix} IAT {suffix}"], expected, places=5)
        self.assertAlmostEqual(features["Fwd IAT Total"], 200000, places=5)

    def test_signed_backward_iat(self):
        flow = FlowState(self.packet(1.0))
        for timestamp in (1.1, 1.05, 1.2):
            flow.add_packet(self.packet(timestamp, backward=True))
        self.assert_iat(flow.bwd.iat, [-50000, 150000])
        features = flow.to_feature_dict()
        for suffix, expected in (
            ("Min", -50000), ("Max", 150000), ("Mean", 50000),
            ("Total", 100000), ("Std", math.sqrt(20000000000)),
        ):
            self.assertAlmostEqual(features[f"Bwd IAT {suffix}"], expected, places=5)
        self.assertEqual(flow.fwd.iat.count, 0)

    def test_duration_uses_last_accepted_timestamp(self):
        flow = FlowState(self.packet(1.0))
        flow.add_packet(self.packet(1.1))
        flow.add_packet(self.packet(1.05))
        self.assertAlmostEqual(flow.to_feature_dict()["Flow Duration"], 50000, places=5)
        self.assertEqual(flow.last_timestamp, 1.1)
        flow.add_packet(self.packet(1.2))
        self.assertAlmostEqual(flow.to_feature_dict()["Flow Duration"], 200000, places=5)

    def test_inactivity_keeps_maximum_timestamp(self):
        tracker = FlowTracker(inactivity_timeout=1.0)
        for timestamp in (1.0, 1.1, 1.05):
            flow = tracker.process_packet(self.packet(timestamp))
        self.assertEqual(flow.last_timestamp, 1.1)
        self.assertAlmostEqual(flow.flow_duration_microseconds, 50000, places=5)
        self.assertEqual(tracker.expire_flows(2.075), [])
        completed = tracker.expire_flows(2.1)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].reason, "INACTIVITY_TIMEOUT")
        self.assertAlmostEqual(completed[0].features["Flow Duration"], 50000, places=5)

    def test_negative_duration_and_single_signed_observation(self):
        flow = FlowState(self.packet(1.1))
        flow.add_packet(self.packet(1.05))
        self.assertAlmostEqual(flow.flow_duration_microseconds, -50000, places=5)
        self.assertEqual(flow.last_timestamp, 1.1)
        self.assert_iat(flow.flow_iat, [-50000])
        self.assert_iat(flow.fwd.iat, [-50000])

    def test_nonpositive_duration_rates_unchanged(self):
        for timestamps in ((1.0,), (1.0, 1.0), (1.1, 1.05)):
            with self.subTest(timestamps=timestamps):
                flow = FlowState(self.packet(timestamps[0], 10))
                for timestamp in timestamps[1:]:
                    flow.add_packet(self.packet(timestamp, 20, backward=True))
                features = flow.to_feature_dict()
                for name in ("Flow Bytes/s", "Flow Packets/s", "Fwd Packets/s", "Bwd Packets/s"):
                    self.assertEqual(features[name], 0.0)
                if len(timestamps) == 2 and timestamps[0] == timestamps[1]:
                    self.assert_iat(flow.flow_iat, [0])


if __name__ == "__main__":
    unittest.main()
