"""
Genel yardımcı fonksiyonlar.
"""

from __future__ import annotations

import re
from pathlib import Path


MAC_PATTERN = re.compile(
    r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$"
)


def normalize_mac(value: str) -> str:
    """MAC adresini küçük harfe çevirip temizler."""

    return value.strip().lower()


def is_valid_mac(value: str) -> bool:
    """Değerin standart MAC adresi biçiminde olup olmadığını kontrol eder."""

    return bool(MAC_PATTERN.fullmatch(value.strip()))


def first_value(value: str) -> str:
    """
    TShark bir alanda birden fazla değer döndürürse
    ilk kullanılabilir değeri seçer.
    """

    if not value:
        return ""

    return value.split(",")[0].strip()


def decode_ssid(value: str) -> str:
    """
    SSID bilgisini okunabilir metne dönüştürmeye çalışır.

    Bazı TShark sürümleri SSID değerini hexadecimal olarak döndürebilir.
    """

    value = value.strip()

    if not value:
        return "<gizli veya belirtilmemiş SSID>"

    # Hexadecimal olabilecek değerleri çözmeyi dene.
    if len(value) % 2 == 0:
        try:
            decoded = bytes.fromhex(value).decode(
                "utf-8",
                errors="strict",
            )

            if decoded and decoded.isprintable():
                return decoded

        except (ValueError, UnicodeDecodeError):
            pass

    return value


def ensure_directory(path: Path) -> None:
    """Dizin yoksa oluşturur."""

    path.mkdir(
        parents=True,
        exist_ok=True,
    )
