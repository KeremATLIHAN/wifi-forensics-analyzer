"""
Proje genelinde kullanılan sabitler.

TShark sürümleri arasında bazı alan adları değişebildiği için
her bilgi için birden fazla aday alan tanımlıyoruz.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CAPTURES_DIR = PROJECT_ROOT / "captures"
REPORTS_DIR = PROJECT_ROOT / "reports"


# Her mantıksal alan için TShark üzerinde denenebilecek alan adları.
FIELD_CANDIDATES = {
    "frame_number": [
        "frame.number",
    ],
    "timestamp": [
        "frame.time_epoch",
    ],
    "frame_type": [
        "wlan.fc.type",
    ],
    "frame_subtype": [
        "wlan.fc.type_subtype",
    ],
    "source": [
        "wlan.sa",
        "wlan.ta",
    ],
    "destination": [
        "wlan.da",
        "wlan.ra",
    ],
    "bssid": [
        "wlan.bssid",
    ],
    "ssid": [
        "wlan.ssid",
        "wlan_mgt.ssid",
    ],
    "channel": [
        "wlan_radio.channel",
        "radiotap.channel.freq",
    ],
    "signal": [
        "radiotap.dbm_antsignal",
        "wlan_radio.signal_dbm",
    ],
    "eapol_type": [
        "eapol.type",
    ],
}


OUTPUT_COLUMNS = [
    "frame_number",
    "timestamp",
    "frame_type",
    "frame_subtype",
    "source",
    "destination",
    "bssid",
    "ssid",
    "channel",
    "signal",
    "eapol_type",
]
