"""
TShark ile CAP/PCAP/PCAPNG dosyalarını okuyan modül.

Bu modül:
- Sistemdeki geçerli TShark alanlarını bulur.
- Alan adı farklılıklarını otomatik yönetir.
- Bozuk son paketi bulunan dosyalarda okunabilen paketleri korur.
- Paketleri satır satır işler.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path
from typing import Iterator

from src.config import FIELD_CANDIDATES, OUTPUT_COLUMNS


class TsharkError(RuntimeError):
    """TShark ile ilgili hatalar için özel hata sınıfı."""


def check_tshark() -> None:
    """TShark sistemde bulunuyor mu kontrol eder."""

    if shutil.which("tshark") is None:
        raise TsharkError(
            "TShark bulunamadı.\n"
            "Kurulum için:\n"
            "sudo apt install tshark"
        )


def get_available_fields() -> set[str]:
    """
    Sistemdeki TShark alanlarını listeler.

    `tshark -G fields` çıktısından geçerli alan adlarını toplar.
    """

    check_tshark()

    process = subprocess.run(
        ["tshark", "-G", "fields"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if process.returncode != 0:
        raise TsharkError(
            "TShark alan listesi alınamadı.\n"
            f"{process.stderr.strip()}"
        )

    fields: set[str] = set()

    for line in process.stdout.splitlines():
        parts = line.split("\t")

        # TShark field satırları çoğunlukla F ile başlar.
        if len(parts) >= 3 and parts[0] == "F":
            fields.add(parts[2])

    return fields


def resolve_fields(
    available_fields: set[str],
) -> dict[str, str | None]:
    """
    Her mantıksal alan için kullanılabilir ilk TShark alanını seçer.
    """

    resolved: dict[str, str | None] = {}

    for logical_name, candidates in FIELD_CANDIDATES.items():
        selected = None

        for candidate in candidates:
            if candidate in available_fields:
                selected = candidate
                break

        resolved[logical_name] = selected

    return resolved


def print_field_status(
    resolved_fields: dict[str, str | None],
) -> None:
    """Algılanan alanları terminalde gösterir."""

    print("\nTShark alan eşleştirmeleri")
    print("-" * 60)

    for logical_name in OUTPUT_COLUMNS:
        field_name = resolved_fields.get(logical_name)

        if field_name:
            print(f"[+] {logical_name:<16} -> {field_name}")
        else:
            print(f"[-] {logical_name:<16} -> kullanılamıyor")


def build_tshark_command(
    capture_file: Path,
    resolved_fields: dict[str, str | None],
) -> tuple[list[str], list[str]]:
    """
    TShark komutunu oluşturur.

    Geriye:
    - komut listesi
    - gerçekten seçilmiş mantıksal alanlar

    döndürür.
    """

    command = [
        "tshark",
        "-n",
        "-r",
        str(capture_file),
        "-T",
        "fields",
        "-E",
        "separator=\t",
        "-E",
        "quote=d",
        "-E",
        "occurrence=f",
    ]

    selected_columns: list[str] = []

    for logical_name in OUTPUT_COLUMNS:
        tshark_field = resolved_fields.get(logical_name)

        if tshark_field:
            command.extend(["-e", tshark_field])
            selected_columns.append(logical_name)

    if not selected_columns:
        raise TsharkError(
            "Kullanılabilir hiçbir TShark alanı bulunamadı."
        )

    return command, selected_columns


def parse_capture(
    capture_file: Path,
    resolved_fields: dict[str, str | None],
) -> Iterator[dict[str, str]]:
    """
    Yakalama dosyasını satır satır okur.

    Her paket için sözlük döndürür.
    """

    if not capture_file.exists():
        raise TsharkError(
            f"Dosya bulunamadı: {capture_file}"
        )

    if not capture_file.is_file():
        raise TsharkError(
            f"Belirtilen yol dosya değil: {capture_file}"
        )

    command, selected_columns = build_tshark_command(
        capture_file,
        resolved_fields,
    )

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if process.stdout is None:
        raise TsharkError(
            "TShark standart çıktısı alınamadı."
        )

    reader = csv.reader(
        process.stdout,
        delimiter="\t",
        quotechar='"',
    )

    packet_count = 0

    for row in reader:
        packet_count += 1

        row += [""] * (
            len(selected_columns) - len(row)
        )

        packet = {
            column: value
            for column, value in zip(
                selected_columns,
                row,
            )
        }

        # Kullanılamayan alanlar da boş olarak eklenir.
        for column in OUTPUT_COLUMNS:
            packet.setdefault(column, "")

        yield packet

    stderr_text = ""

    if process.stderr is not None:
        stderr_text = process.stderr.read()

    return_code = process.wait()

    if return_code != 0:
        lowered_error = stderr_text.lower()

        if packet_count > 0 and (
            "cut short" in lowered_error
            or "truncated" in lowered_error
        ):
            print(
                "\n[UYARI] Yakalama dosyasının son bölümü eksik."
            )
            print(
                f"[UYARI] Okunabilen {packet_count} paket kullanıldı."
            )
        else:
            raise TsharkError(
                "TShark yakalama dosyasını okuyamadı.\n"
                f"{stderr_text.strip()}"
            )
