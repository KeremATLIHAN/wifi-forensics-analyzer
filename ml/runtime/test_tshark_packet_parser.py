from collections import Counter

from ml.runtime.tshark_packet_parser import (
    TSharkPacketParser,
)


CAPTURE = (
    "captures/lab/"
    "cyberlab_ip_parity_test.pcapng"
)


parser = TSharkPacketParser()

packets = list(
    parser.parse_file(CAPTURE)
)

assert packets

counts = Counter(
    packet.transport
    for packet in packets
)

assert len(packets) == 618
assert counts["TCP"] == 235
assert counts["UDP"] == 383

for packet in packets:
    packet.validate()

print("TShark parsing:           OK")
print("PacketRecord conversion: OK")
print("Packet validation:       OK")
print()
print("Total packets:", len(packets))
print("TCP packets:  ", counts["TCP"])
print("UDP packets:  ", counts["UDP"])

print()
print("First packet:")
print(packets[0])