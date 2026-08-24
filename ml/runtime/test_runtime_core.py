from ml.runtime.flow_key import FlowKey
from ml.runtime.packet_record import PacketRecord


packet_1 = PacketRecord(
    timestamp=1000.0,
    frame_length=100,
    src_ip="192.168.1.10",
    dst_ip="8.8.8.8",
    src_port=50000,
    dst_port=443,
    protocol=6,
    transport="TCP",
    tcp_syn=1,
)

packet_2 = PacketRecord(
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
)

packet_1.validate()
packet_2.validate()

key_1 = FlowKey.from_packet(packet_1)
key_2 = FlowKey.from_packet(packet_2)

assert key_1 == key_2

assert key_1.direction(packet_1) != (
    key_1.direction(packet_2)
)

print("PacketRecord validation: OK")
print("Bidirectional FlowKey:    OK")

print(
    "Packet 1 direction:      ",
    key_1.direction(packet_1),
)

print(
    "Packet 2 direction:      ",
    key_1.direction(packet_2),
)