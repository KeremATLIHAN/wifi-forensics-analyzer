from ml.runtime.flow_tracker import FlowTracker
from ml.runtime.packet_record import PacketRecord


def packet(
    timestamp: float,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
) -> PacketRecord:

    return PacketRecord(
        timestamp=timestamp,
        frame_length=100,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=6,
        transport="TCP",
        tcp_ack=1,
    )


tracker = FlowTracker(
    inactivity_timeout=10.0
)

# Flow 1
tracker.process_packet(
    packet(
        1000.0,
        "192.168.1.10",
        "8.8.8.8",
        50000,
        443,
    )
)

tracker.process_packet(
    packet(
        1001.0,
        "8.8.8.8",
        "192.168.1.10",
        443,
        50000,
    )
)

# Flow 2
tracker.process_packet(
    packet(
        1005.0,
        "192.168.1.20",
        "1.1.1.1",
        51000,
        53,
    )
)

assert tracker.active_flow_count == 2

# t=1012:
# Flow 1 son paket 1001 -> 11 saniye idle -> expire
# Flow 2 son paket 1005 -> 7 saniye idle -> aktif
completed = tracker.expire_flows(1012.0)

assert len(completed) == 1
assert tracker.active_flow_count == 1

assert (
    completed[0].reason
    == "INACTIVITY_TIMEOUT"
)

remaining = tracker.close_all()

assert len(remaining) == 1
assert tracker.active_flow_count == 0

print("Multiple flow tracking:    OK")
print("Bidirectional routing:     OK")
print("Inactivity expiration:     OK")
print("Graceful flow shutdown:    OK")
print("FlowTracker validation:    OK")