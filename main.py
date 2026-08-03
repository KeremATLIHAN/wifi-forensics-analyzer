
#!/usr/bin/env python3

"""
Wi-Fi Forensics Analyzer

Bu sürüm:
- TShark alanlarını otomatik algılar.
- CAP/PCAP/PCAPNG dosyasını satır satır okur.
- Ağları, istemci adaylarını ve EAPOL paketlerini analiz eder.
- Sonuçları terminalde özetler.

Parola denemesi veya parola kırma işlemi yapmaz.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any
from src.config import REPORTS_DIR
from src.reporters import generate_all_reports
from src.analyzer import analyze_packets
from src.tshark_parser import (
    TsharkError,
    get_available_fields,
    parse_capture,
    print_field_status,
    resolve_fields,
)


def parse_arguments() -> argparse.Namespace:
    """Terminal parametrelerini okur."""

    parser = argparse.ArgumentParser(
        description=(
            "Wi-Fi CAP, PCAP ve PCAPNG dosyalarını "
            "TShark ile analiz eder."
        )
    )

    parser.add_argument(
        "capture_file",
        type=Path,
        help="Analiz edilecek yakalama dosyası",
    )

    parser.add_argument(
        "--show-clients",
        type=int,
        default=10,
        help=(
            "Her ağ için gösterilecek en fazla "
            "istemci adayı sayısı"
        ),
    )

    parser.add_argument(
        "--hide-fields",
        action="store_true",
        help="TShark alan eşleştirmelerini gizler",
    )

    parser.add_argument(
        "--output-name",
        default=None,
        help="Rapor dosyalarının temel adı",
    )

    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="JSON, CSV ve HTML raporlarını oluşturmaz",
    )

    return parser.parse_args()


def format_ssids(ssids: list[str]) -> str:
    """SSID listesini terminal için biçimlendirir."""

    if not ssids:
        return "<SSID belirlenemedi veya gizli>"

    return ", ".join(ssids)


def print_summary(
    report: dict[str, Any],
    client_limit: int,
) -> None:
    """Analiz raporunu terminalde gösterir."""

    print()
    print("=" * 72)
    print("WI-FI FORENSICS ANALYZER")
    print("=" * 72)

    print(
        f"Toplam paket       : "
        f"{report['total_packets']}"
    )

    print(
        f"Görülen BSSID      : "
        f"{report['network_count']}"
    )

    print(
        f"EAPOL paket sayısı : "
        f"{report['eapol_packet_count']}"
    )

    if report["eapol_packet_count"] == 0:
        print()
        print(
            "[!] Yakalama dosyasında EAPOL paketi "
            "tespit edilmedi."
        )
        print(
            "    WPA/WPA2 kimlik doğrulama trafiği "
            "yakalanmamış olabilir."
        )
    else:
        print()
        print("[+] EAPOL paketleri bulundu.")
        print(
            "    Not: EAPOL paketi bulunması tek başına "
            "eksiksiz 4-way handshake bulunduğunu göstermez."
        )

    print()
    print("TESPİT EDİLEN AĞLAR")
    print("-" * 72)

    if not report["networks"]:
        print(
            "Yakalama dosyasında kullanılabilir "
            "BSSID bilgisi bulunamadı."
        )

    for index, network in enumerate(
        report["networks"],
        start=1,
    ):
        ssid_text = format_ssids(
            network["ssids"]
        )

        channel = (
            network["channel"]
            if network["channel"] is not None
            else "bilinmiyor"
        )

        signal = network["average_signal_dbm"]

        signal_text = (
            f"{signal} dBm"
            if signal is not None
            else "bilinmiyor"
        )

        clients = network["clients"]

        print()
        print(f"[{index}] SSID           : {ssid_text}")
        print(f"    BSSID          : {network['bssid']}")
        print(f"    Kanal          : {channel}")
        print(f"    Ortalama sinyal: {signal_text}")
        print(f"    İstemci adayı  : {len(clients)}")

        for client in clients[:client_limit]:
            print(
                f"      - {client['mac']} "
                f"({client['packet_count']} paket)"
            )

        remaining_clients = len(clients) - client_limit

        if remaining_clients > 0:
            print(
                f"      ... {remaining_clients} "
                "istemci adayı daha var"
            )

    print()
    print("802.11 ÇERÇEVE ALT TİPLERİ")
    print("-" * 72)

    if not report["frame_subtypes"]:
        print("Çerçeve alt tipi bilgisi bulunamadı.")
    else:
        for subtype, count in report["frame_subtypes"].items():
            print(f"{subtype:<30} {count:>10}")

    print()
    print("EN ÇOK GÖRÜLEN KAYNAK MAC ADRESLERİ")
    print("-" * 72)

    for item in report["top_sources"][:10]:
        print(
            f"{item['mac']:<20} "
            f"{item['packet_count']:>10} paket"
        )

    if report["eapol_packets"]:
        print()
        print("EAPOL PAKETLERİ")
        print("-" * 72)

        for packet in report["eapol_packets"][:50]:
            print(
                f"Frame {packet['frame_number']}: "
                f"{packet['source'] or '?'} -> "
                f"{packet['destination'] or '?'} "
                f"BSSID={packet['bssid'] or '?'} "
                f"type={packet['eapol_type']}"
            )

        remaining_eapol = (
            len(report["eapol_packets"]) - 50
        )

        if remaining_eapol > 0:
            print(
                f"... {remaining_eapol} "
                "EAPOL paketi daha var"
            )
        if not args.no_reports:
            base_name = (
                args.output_name
                if args.output_name
                else capture_file.stem
            )

            created_files = generate_all_reports(
                report=report,
                reports_dir=REPORTS_DIR,
                base_name=base_name,
                capture_name=capture_file.name,
            )

            print()
            print("OLUŞTURULAN RAPORLAR")
            print("-" * 72)

            for created_file in created_files:
                print(created_file.resolve())


def main() -> int:
    """Programın başlangıç noktası."""

    args = parse_arguments()

    capture_file = (
        args.capture_file
        .expanduser()
        .resolve()
    )

    try:
        available_fields = get_available_fields()

        resolved_fields = resolve_fields(
            available_fields
        )

        if not args.hide_fields:
            print_field_status(
                resolved_fields
            )

        print()
        print(f"Dosya analiz ediliyor: {capture_file}")

        packets = parse_capture(
            capture_file,
            resolved_fields,
        )

        report = analyze_packets(
            packets
        )

        print_summary(
            report,
            max(args.show_clients, 0),
        )

        return 0

    except TsharkError as error:
        print(
            f"\nHata:\n{error}",
            file=sys.stderr,
        )
        return 1

    except KeyboardInterrupt:
        print(
            "\nİşlem kullanıcı tarafından durduruldu."
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
