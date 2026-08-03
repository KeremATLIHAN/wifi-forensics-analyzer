# WiFi Forensics Analyzer

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Platform](https://img.shields.io/badge/Linux-Kali-success)
![License](https://img.shields.io/badge/License-Educational-lightgrey)

A modular Python application for analyzing Wi-Fi capture files
(.cap, .pcap, .pcapng) in educational and authorized laboratory environments.

---

# Features

✔ CAP / PCAP / PCAPNG support

✔ Automatic TShark field detection

✔ SSID decoding

✔ BSSID discovery

✔ Client discovery

✔ Channel analysis

✔ 802.11 Management Frame Analysis

✔ EAPOL detection

✔ JSON reports

✔ CSV reports

✔ HTML reports

---

# Planned Features

- OUI Vendor Detection
- RSSI Graphs
- Channel Utilization
- Hidden SSID Detection
- Beacon Statistics
- Probe Analysis
- Device Timeline
- SQLite Database
- Flask Dashboard
- PDF Reports

---

# Project Structure

wifi_forensics_analyzer/

captures/

reports/

src/

README.md

requirements.txt

main.py

---

# Installation

```bash
git clone <repository>

cd wifi_forensics_analyzer

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

Install TShark

```bash
sudo apt install tshark
```

---

# Usage

```bash
python main.py captures/example.pcapng
```

---

# Project Roadmap

v0.1

- Core Parser

- TShark Integration

- JSON/CSV/HTML Reports

v0.2

- Wi-Fi Forensics Engine

v0.3

- OUI Detection

v0.4

- Timeline Analysis

v0.5

- HTML Dashboard

v1.0

- Professional Release

---

# License

This project is intended for educational purposes and analysis of
capture files obtained in authorized laboratory environments.

It is not intended to be used for unauthorized access to third-party
wireless networks.
