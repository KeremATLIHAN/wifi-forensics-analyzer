from ml.runtime.flow_state import FlowState
from ml.runtime.packet_record import PacketRecord


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
        tcp_syn=1,
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
        tcp_syn=1,
        tcp_ack=1,
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
        tcp_ack=1,
        tcp_psh=1,
    ),
]

flow = FlowState(packets[0])

for packet in packets[1:]:
    flow.add_packet(packet)

features = flow.to_feature_dict()

assert flow.fwd.packets == 2
assert flow.bwd.packets == 1
assert flow.total_packets == 3
assert flow.total_bytes == 420

assert abs(
    flow.flow_duration_seconds - 0.3
) < 1e-9

assert abs(
    flow.flow_duration_microseconds
    - 300_000.0
) < 1e-6

assert abs(
    features["Flow Duration"]
    - 300_000.0
) < 1e-6

assert abs(
    features["Flow IAT Mean"]
    - 150_000.0
) < 1e-6

assert abs(
    features["Flow IAT Min"]
    - 100_000.0
) < 1e-6

assert abs(
    features["Flow IAT Max"]
    - 200_000.0
) < 1e-6

assert features["SYN Flag Count"] == 2
assert features["ACK Flag Count"] == 2
assert features["PSH Flag Count"] == 1

print("FlowState packet direction: OK")
print("Flow counters:              OK")
print("Flow duration:              OK")
print("TCP flag counters:          OK")
print("Feature count:", len(features))
