# CyberLab

### Desktop Wi-Fi Forensics & Security Analysis Suite

CyberLab is a desktop Wi-Fi forensic analysis application designed for educational, laboratory, and authorized security analysis environments.

It analyzes `.cap`, `.pcap`, and `.pcapng` capture files through TShark and presents network, client, handshake, security, and traffic information through a PySide6 desktop interface.

> **Version:** 1.0.0

---

## Features

### Wi-Fi Forensics

- CAP / PCAP / PCAPNG capture support
- TShark-based packet analysis
- SSID and BSSID discovery
- Wi-Fi channel detection
- Client device discovery
- Signal level analysis
- 802.11 frame subtype analysis
- EAPOL packet detection

### Device Intelligence

- Offline OUI / Vendor detection
- Client MAC address analysis
- Private / Randomized MAC detection
- Sent / received packet statistics
- Client activity analysis
- First / last seen information

### Handshake Analysis

CyberLab includes an EAPOL analysis engine for identifying Wi-Fi handshake candidates.

- EAPOL candidate detection
- Client / BSSID association
- Partial handshake identification
- Strong handshake candidate identification
- Detailed handshake inspection

Handshake findings indicate evidence observed in the capture and should not be interpreted as proof of unauthorized activity.

### Security Findings v2

The analysis engine automatically generates structured forensic observations.

Finding categories include:

- Handshake
- Privacy
- Wireless
- Signal
- Activity
- Device

Severity levels:

- Critical
- Warning
- Info
- Success

CyberLab intentionally distinguishes forensic observations from security conclusions. For example, high packet activity or weak signal strength alone is not classified as an attack.

### Search & Filtering

Network and client tables support real-time filtering.

Networks can be searched by:

- SSID
- BSSID

Clients can be searched by:

- MAC address
- Vendor

### Analytics Dashboard

CyberLab provides lightweight Qt-based analytics without external plotting frameworks.

Current analytics include:

- Top active client devices
- Wi-Fi network signal levels
- 802.11 frame subtype distribution

### Reporting

Analysis results can be exported as:

- PDF
- HTML
- JSON

PDF reports are generated using ReportLab and include:

- Analysis summary
- Security findings
- Detected networks
- Client activity
- Vendor information
- Signal information
- 802.11 frame analysis
- Repeated table headers
- Automatic pagination
- Page numbers

---

## Desktop Interface

CyberLab uses PySide6 / Qt for its desktop interface.

The application includes:

- Splash screen
- Dashboard
- Wi-Fi Forensics workspace
- Responsive scrollable layout
- Network details
- Client device tables
- Handshake details
- Security Findings dashboard
- Analytics
- Report export

---

## Requirements

### Windows

- Windows 10 / 11
- Python 3
- TShark / Wireshark
- PySide6
- ReportLab

### Linux / Kali Linux

The analysis engine can also be executed in compatible Linux environments with TShark installed.

---

## Installation From Source

Clone the repository:

```bash
git clone https://github.com/KeremATLIHAN/wifi-forensics-analyzer.git
cd wifi-forensics-analyzer
```

Create a virtual environment.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## TShark

CyberLab uses TShark as its packet-analysis backend.

### Windows

Install Wireshark and make sure TShark is available on the system.

Verify:

```powershell
tshark --version
```

### Kali / Debian-based Linux

```bash
sudo apt update
sudo apt install tshark
```

Verify:

```bash
tshark --version
```

---

## Running CyberLab

### Desktop GUI

```bash
python gui_app.py
```

### Command-Line Analysis

```bash
python main.py captures/example.pcapng
```

---

## Windows Build

CyberLab can be packaged as a Windows desktop application using PyInstaller.

Example:

```powershell
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name CyberLab `
  --icon "resources\icons\cyberlab.ico" `
  --add-data "resources;resources" `
  gui_app.py
```

The application will be generated under:

```text
dist/CyberLab/
```

---

## Project Structure

```text
wifi-forensics-analyzer/
│
├── gui/
│   ├── pages/
│   └── resources/
│
├── src/
│   ├── analyzer.py
│   ├── reporters.py
│   ├── tshark_parser.py
│   └── config.py
│
├── resources/
│   ├── icons/
│   └── logo/
│
├── captures/
├── reports/
│
├── gui_app.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Release History

### v1.0.0 — Stable Release

- PySide6 desktop application
- Wi-Fi forensic analysis engine
- Vendor / OUI detection
- Randomized MAC detection
- Handshake Analysis v2
- Security Findings v2
- Network and client filtering
- Analytics dashboard
- PDF / HTML / JSON reporting
- Responsive desktop interface
- Windows executable packaging

### Earlier Development

The project evolved from an initial command-line Wi-Fi capture analyzer into the CyberLab desktop forensic analysis suite.

---

## Security & Authorized Use

CyberLab is intended for:

- Cybersecurity education
- Authorized laboratory exercises
- Analysis of capture files you own or are authorized to inspect
- Defensive security research
- Wi-Fi forensic learning

CyberLab is **not intended for unauthorized access, interception, or analysis of third-party wireless networks**.

Users are responsible for ensuring that capture files and network analysis activities comply with applicable laws, policies, and authorization requirements.

---

## Technology

- Python
- PySide6 / Qt
- TShark
- ReportLab
- PyInstaller

---

## Status

**CyberLab v1.0.0 — Stable**