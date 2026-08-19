
from __future__ import annotations


# CyberLab dahili OUI tablosu.
#
# Bu tablo başlangıç için küçük tutulmuştur.
# Daha sonra IEEE OUI veritabanından oluşturulan
# kapsamlı bir offline database ile değiştirilebilir.

OUI_DATABASE: dict[str, str] = {
    "00:1A:79": "Cisco",
    "00:1B:63": "Apple",
    "00:1C:B3": "Apple",
    "00:1D:4F": "Apple",
    "00:1E:C2": "Apple",
    "00:1F:5B": "Apple",
    "00:21:E9": "Apple",
    "00:22:41": "Apple",
    "00:23:12": "Apple",
    "00:23:32": "Apple",
    "00:23:6C": "Apple",
    "00:25:00": "Apple",
    "00:25:4B": "Apple",
    "00:26:08": "Apple",
    "00:26:BB": "Apple",
    "3C:A7:AE": "Technicolor",
}


def normalize_oui(mac_address: str) -> str:
    """MAC adresinden XX:XX:XX biçiminde OUI üretir."""

    if not mac_address:
        return ""

    normalized = (
        mac_address
        .strip()
        .upper()
        .replace("-", ":")
    )

    parts = normalized.split(":")

    if len(parts) < 3:
        return ""

    return ":".join(parts[:3])


def is_locally_administered(
    mac_address: str,
) -> bool:
    """MAC adresinin locally administered olup olmadığını kontrol eder."""

    if not mac_address:
        return False

    try:
        first_octet = int(
            mac_address
            .replace("-", ":")
            .split(":")[0],
            16,
        )
    except (ValueError, IndexError):
        return False

    return bool(first_octet & 0x02)


def lookup_vendor(
    mac_address: str,
) -> str:
    """MAC adresinden cihaz üreticisini döndürür."""

    if not mac_address:
        return "Bilinmiyor"

    if is_locally_administered(mac_address):
        return "Private / Randomized MAC"

    oui = normalize_oui(mac_address)

    if not oui:
        return "Bilinmiyor"

    return OUI_DATABASE.get(
        oui,
        "Bilinmiyor",
    )