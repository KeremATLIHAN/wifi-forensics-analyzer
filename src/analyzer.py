"""
Yakalama paketlerini analiz eden modül.

Bu modül parola denemesi yapmaz.
Yalnızca yakalama dosyasındaki 802.11 paketlerini sınıflandırır.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from src.utils import decode_ssid, first_value, is_valid_mac, normalize_mac
from src.oui_lookup import lookup_vendor
from datetime import datetime


FRAME_SUBTYPE_NAMES = {
    "0": "Association Request",
    "1": "Association Response",
    "2": "Reassociation Request",
    "3": "Reassociation Response",
    "4": "Probe Request",
    "5": "Probe Response",
    "8": "Beacon",
    "10": "Disassociation",
    "11": "Authentication",
    "12": "Deauthentication",
}


def is_ignored_mac(mac_address: str) -> bool:
    """Broadcast ve multicast adreslerini filtreler."""

    if not mac_address:
        return True

    if mac_address == "ff:ff:ff:ff:ff:ff":
        return True

    if mac_address.startswith("01:00:5e"):
        return True

    if mac_address.startswith("33:33"):
        return True

    return False


def safe_signal(value: str) -> int | None:
    """Sinyal değerini mümkünse tam sayıya dönüştürür."""

    value = first_value(value)

    if not value:
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def analyze_packets(
    packets: Iterable[dict[str, str]],
) -> dict[str, Any]:
    """Paket akışını okuyup özet rapor oluşturur."""

    total_packets = 0
    eapol_packets = 0

    ssids_by_bssid: dict[str, set[str]] = defaultdict(set)
    channels_by_bssid: dict[str, Counter[str]] = defaultdict(Counter)
    signals_by_bssid: dict[str, list[int]] = defaultdict(list)
    clients_by_bssid: dict[str, Counter[str]] = defaultdict(Counter)

    source_counts: Counter[str] = Counter()
    destination_counts: Counter[str] = Counter()
    subtype_counts: Counter[str] = Counter()

    eapol_details: list[dict[str, str]] = []

    client_first_seen: dict[str, dict[str, float]] = defaultdict(dict)
    client_last_seen: dict[str, dict[str, float]] = defaultdict(dict)

    client_sent_counts: dict[str, Counter[str]] = defaultdict(Counter)
    client_received_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for packet in packets:
        total_packets += 1

        frame_number = first_value(packet.get("frame_number", ""))
        timestamp = first_value(packet.get("timestamp", ""))
        try:
            timestamp_value = float(timestamp)
        except (TypeError, ValueError):
            timestamp_value = None
        frame_subtype = first_value(packet.get("frame_subtype", ""))

        source = normalize_mac(
            first_value(packet.get("source", ""))
        )
        destination = normalize_mac(
            first_value(packet.get("destination", ""))
        )
        bssid = normalize_mac(
            first_value(packet.get("bssid", ""))
        )

        ssid_raw = first_value(packet.get("ssid", ""))
        channel = first_value(packet.get("channel", ""))
        signal = safe_signal(packet.get("signal", ""))
        eapol_type = first_value(packet.get("eapol_type", ""))

        if source and is_valid_mac(source):
            source_counts[source] += 1

        if destination and is_valid_mac(destination):
            destination_counts[destination] += 1

        if frame_subtype:
            subtype_name = FRAME_SUBTYPE_NAMES.get(
                frame_subtype,
                f"Subtype {frame_subtype}",
            )
            subtype_counts[subtype_name] += 1

        if bssid and is_valid_mac(bssid):
            if ssid_raw:
                ssids_by_bssid[bssid].add(
                    decode_ssid(ssid_raw)
                )

            if channel:
                channels_by_bssid[bssid][channel] += 1

            if signal is not None:
                signals_by_bssid[bssid].append(signal)

            for mac_address in (source, destination):
                if not is_valid_mac(mac_address):
                    continue

                if mac_address == bssid:
                    continue

                if is_ignored_mac(mac_address):
                    continue

                clients_by_bssid[bssid][mac_address] += 1

                if timestamp_value is not None:
                    if mac_address not in client_first_seen[bssid]:
                        client_first_seen[bssid][mac_address] = timestamp_value

                    client_last_seen[bssid][mac_address] = timestamp_value

                if mac_address == source:
                    client_sent_counts[bssid][mac_address] += 1

                if mac_address == destination:
                    client_received_counts[bssid][mac_address] += 1

        if eapol_type:
            eapol_packets += 1

            eapol_details.append(
                {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "source": source,
                    "destination": destination,
                    "bssid": bssid,
                    "eapol_type": eapol_type,
                }
            )

    bssids = (
        set(ssids_by_bssid)
        | set(channels_by_bssid)
        | set(signals_by_bssid)
        | set(clients_by_bssid)
    )

    networks: list[dict[str, Any]] = []

    for bssid in sorted(bssids):
        channels = channels_by_bssid.get(
            bssid,
            Counter(),
        )
        signals = signals_by_bssid.get(
            bssid,
            [],
        )
        clients = clients_by_bssid.get(
            bssid,
            Counter(),
        )

        primary_channel = (
            channels.most_common(1)[0][0]
            if channels
            else None
        )

        average_signal = (
            round(sum(signals) / len(signals), 2)
            if signals
            else None
        )

        networks.append(
            {
                "bssid": bssid,
                "ssids": sorted(
                    ssids_by_bssid.get(bssid, [])
                ),
                "channel": primary_channel,
                "average_signal_dbm": average_signal,
                "clients": [
                        {
                            "mac": mac,
                            "vendor": lookup_vendor(mac),
                            "packet_count": packet_count,
                            "sent_packets": client_sent_counts[bssid][mac],
                            "received_packets": client_received_counts[bssid][mac],
                            "first_seen": (
                                datetime.fromtimestamp(
                                    client_first_seen[bssid][mac]
                                ).strftime("%H:%M:%S")
                                if mac in client_first_seen[bssid]
                                else "—"
                            ),
                            "last_seen": (
                                datetime.fromtimestamp(
                                    client_last_seen[bssid][mac]
                                ).strftime("%H:%M:%S")
                                if mac in client_last_seen[bssid]
                                else "—"
                            ),
                            "activity_level": (
                                "Yüksek"
                                if packet_count >= 1000
                                else "Orta"
                                if packet_count >= 250
                                else "Düşük"
                            ),
                        }
                        for mac, packet_count
                        in clients.most_common()
                    ],
                
            }
        )

    handshake_candidates: list[dict[str, Any]] = []

    eapol_groups: dict[
        tuple[str, str],
        list[dict[str, str]],
    ] = defaultdict(list)

    for packet in eapol_details:
        bssid = packet.get("bssid", "")
        source = packet.get("source", "")
        destination = packet.get("destination", "")

        if not bssid:
            continue

        client = ""

        if source and source != bssid:
            client = source
        elif destination and destination != bssid:
            client = destination

        if not client:
            continue

        eapol_groups[(bssid, client)].append(packet)

    for (bssid, client), packets_for_pair in eapol_groups.items():
        packet_count = len(packets_for_pair)

        first_seen = (
            packets_for_pair[0].get("timestamp", "")
            if packets_for_pair
            else ""
        )

        last_seen = (
            packets_for_pair[-1].get("timestamp", "")
            if packets_for_pair
            else ""
        )

        handshake_candidates.append(
            {
                "bssid": bssid,
                "client": client,
                "eapol_packet_count": packet_count,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "status": (
                    "strong_candidate"
                    if packet_count >= 4
                    else "partial"
                ),
            }
        )

    findings: list[dict[str, str]] = []

    strong_handshakes = [
        candidate
        for candidate in handshake_candidates
        if candidate.get("status") == "strong_candidate"
    ]

    partial_handshakes = [
        candidate
        for candidate in handshake_candidates
        if candidate.get("status") == "partial"
    ]

    if strong_handshakes:
        findings.append(
            {
                "severity": "success",
                "title": "Handshake adayı tespit edildi",
                "description": (
                    f"{len(strong_handshakes)} istemci/ağ eşleşmesinde "
                    "en az 4 EAPOL paketi gözlemlendi."
                ),
            }
        )
    elif partial_handshakes:
        findings.append(
            {
                "severity": "warning",
                "title": "Eksik EAPOL alışverişi",
                "description": (
                    f"{len(partial_handshakes)} istemci/ağ eşleşmesinde "
                    "kısmi EAPOL trafiği gözlemlendi."
                ),
            }
        )
    else:
        findings.append(
            {
                "severity": "warning",
                "title": "Handshake bulunamadı",
                "description": (
                    "Yakalama dosyasında istemci/ağ bazında "
                    "yeterli EAPOL trafiği tespit edilmedi."
                ),
            }
        )

    if not networks:
        findings.append(
            {
                "severity": "warning",
                "title": "Kablosuz ağ bulunamadı",
                "description": (
                    "Yakalama içerisinde analiz edilebilir bir BSSID bulunamadı."
                ),
            }
        )
    else:
        findings.append(
            {
                "severity": "info",
                "title": "Kablosuz ağlar tespit edildi",
                "description": (
                    f"Toplam {len(networks)} farklı ağ gözlemlendi."
                ),
            }
        )

    all_clients = [
        client
        for network in networks
        for client in network.get("clients", [])
    ]

    high_activity_clients = [
        client
        for client in all_clients
        if client.get("activity_level") == "Yüksek"
    ]

    if high_activity_clients:
        findings.append(
            {
                "severity": "info",
                "title": "Yoğun istemci aktivitesi",
                "description": (
                    f"{len(high_activity_clients)} istemci yüksek "
                    "paket aktivitesi gösteriyor."
                ),
            }
        )

    missing_channel_networks = [
        network
        for network in networks
        if network.get("channel") is None
    ]

    if missing_channel_networks:
        findings.append(
            {
                "severity": "warning",
                "title": "Kanal bilgisi eksik",
                "description": (
                    f"{len(missing_channel_networks)} ağ için kanal bilgisi "
                    "yakalama dosyasından alınamadı."
                ),
            }
        )

    missing_signal_networks = [
        network
        for network in networks
        if network.get("average_signal_dbm") is None
    ]

    if missing_signal_networks:
        findings.append(
            {
                "severity": "warning",
                "title": "Sinyal bilgisi eksik",
                "description": (
                    f"{len(missing_signal_networks)} ağ için sinyal seviyesi "
                    "bulunamadı."
                ),
            }
        )

    return {
        "total_packets": total_packets,
        "network_count": len(networks),
        "eapol_packet_count": eapol_packets,
        "networks": networks,
        "security_findings": findings,
        "frame_subtypes": dict(
            subtype_counts.most_common()
        ),
        "top_sources": [
            {
                "mac": mac,
                "packet_count": count,
            }
            for mac, count in source_counts.most_common(20)
        ],
        "top_destinations": [
            {
                "mac": mac,
                "packet_count": count,
            }
            for mac, count
            in destination_counts.most_common(20)
        ],
        "eapol_packets": eapol_details,
        "handshake_candidates": handshake_candidates,
    }
