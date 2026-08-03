#!/usr/bin/env python3

"""
Wi-Fi Forensics Analyzer başlangıç dosyası.

Bu ilk sürüm:
- TShark alanlarını algılar.
- Yakalama dosyasını okur.
- Paket sayısını gösterir.
- İlk birkaç paketi örnek olarak yazdırır.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.tshark_parser import (
    TsharkError,
    get_available_fields,
    parse_capture,
    print_field_status,
    resolve_fields,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "CAP, PCAP ve PCAPNG dosyalarını "
            "TShark ile analiz eder."
        )
    )

    parser.add_argument(
        "capture_file",
        type=Path,
        help="Analiz edilecek yakalama dosyası",
    )

    parser.add_argument(
        "--show-packets",
        type=int,
        default=5,
        help="Terminalde gösterilecek örnek paket sayısı",
    )

    return parser.parse_args()


def main() -> int:
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

        print_field_status(
            resolved_fields
        )

        print(f"\nDosya okunuyor: {capture_file}")

        total_packets = 0

        for packet in parse_capture(
            capture_file,
            resolved_fields,
        ):
            total_packets += 1

            if total_packets <= args.show_packets:
                print(
                    f"\nPaket #{total_packets}"
                )

                for key, value in packet.items():
                    if value:
                        print(
                            f"  {key:<16}: {value}"
                        )

        print("\n" + "=" * 60)
        print(f"Toplam okunabilen paket: {total_packets}")
        print("=" * 60)

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
