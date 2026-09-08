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

## ML / IDS Development Milestone

CyberLab now includes a validated machine-learning and runtime flow-processing foundation for hierarchical intrusion detection.

### Dataset and Feature Pipeline

- CIC-BCCC-NRC-ACI-IoT-2023 dataset integrated into the project
- 57 dataset features aligned with runtime PCAP / flow features
- Runtime feature parity validated
- Eight normalized traffic and attack families:
  - BENIGN
  - BRUTE_FORCE
  - DDOS
  - DOS
  - MIRAI
  - MITM
  - MQTT
  - RECON
- Balanced corpus containing 200,000 flows:
  - 100,000 benign
  - 100,000 attack
- Dataset split:
  - 140,000 training flows
  - 30,000 validation flows
  - 30,000 final-test flows

### Final 30K IDS Evaluation

The read-only final evaluation used `ml/datasets/processed/binary_v1/test.parquet` with 30,000 rows. Existing model artifacts were used without retraining, normalization, imputation, or dataset modification.

- Valid feature vectors: 30,000
- IDS decisions: 30,000
- Skipped: 0

Overall performance:

- Accuracy: 96.6767%
- Precision: 98.4365%
- Recall: 94.8600%
- F1: 96.6152%

Population results:

- Normal duration: 29,893 rows; accuracy 96.6815%; F1 96.6148%
- Zero duration: 107 rows; accuracy 95.3271%; F1 96.6887%
- Zero-byte zero-duration: 68 rows; accuracy 98.5294%; F1 99.1304%
- Zero-duration with total bytes greater than zero: 39 rows; accuracy 89.7436%; F1 88.8889%

The detailed evaluation is documented in [`docs/ml/FINAL_30K_EVALUATION.md`](docs/ml/FINAL_30K_EVALUATION.md).

Zero-duration population remains a known semantic/provenance limitation. The observed dataset contains `Flow Duration = 0`, `Flow Bytes/s > 0`, `Flow Packets/s > 0`, `Fwd Packets/s = 0`, and `Bwd Packets/s = 0`, while runtime behavior for `duration <= 0` sets global rates to `0.0`. Therefore:

- REFERENCE/RUNTIME ZERO-DURATION PARITY: **FAIL**
- ZERO-DURATION PROVENANCE: **UNKNOWN**
- 68-ROW ANOMALY CAUSE: **UNKNOWN**
- SEMANTIC CLEARANCE: **CONDITIONAL**

This limitation is a semantic/provenance issue, not a model performance failure. The final performance evaluation is **COMPLETED**; semantic clearance remains **CONDITIONAL**. The 107 zero-duration rows have a numerically small aggregate effect on overall accuracy and F1, while the 39-row zero-duration population with positive total bytes has lower subset performance.

### Binary IDS Validation

The binary Random Forest IDS currently has the following **validation** results:

- Accuracy: approximately 96.08%
- Precision: approximately 99.17%
- Attack recall: approximately 92.94%
- ROC-AUC: approximately 0.990

BRUTE_FORCE and MITM were identified as the more difficult attack families.

### Hierarchical IDS Validation

A hierarchical architecture combining a Primary Random Forest with a Hard-Case Specialist has been developed.

- Specialist corpus: 24,709 hard-case samples selected through five-fold out-of-fold prediction
- False negatives: 1,059 to 806
- BRUTE_FORCE detection: 61.41% to 67.63%
- MITM detection: 69.16% to 76.14%
- False positives: 117 to 228

These are **validation results**, not final-test results.

### CICFlowMeter Lifecycle Parity

Controlled PCAP tests against the CICFlowMeter reference implementation validate:

- Normal TCP lifecycle
- TCP FIN lifecycle
- TCP RST lifecycle
- Flow lifetimes below 120 seconds
- Flow lifetimes above 120 seconds
- Exact 120-second boundary behavior
- 120 seconds plus 1 microsecond boundary behavior
- Lifecycle-aware regression behavior

Maximum flow lifetime is 120 seconds and uses strict `>` semantics. A packet at exactly 120 seconds remains in the current flow; a packet beyond the boundary starts a new flow after the previous flow is completed.

Verified regression status:

- TEST-01 through TEST-08: PASS
- 55222 lifecycle parity: PASS
- 52658 legacy parser parity: PASS
- Full Python test suite: 10 / 10 PASS

The production parser preserves TShark's normal TCP decoding. The separately selected legacy profile reproduces the relevant JNetPcap compatibility behavior: the 52658 flow changes from 18 FWD / 33 BWD in production to 14 FWD / 33 BWD in legacy mode, with the remaining four packets represented as a protocol-0 flow. Internal lifecycle flow counts and CICFlowMeter CSV-equivalent counts are treated as separate concepts.

### Current IDS Architecture

The validated runtime path is:

```text
PCAP
  -> TShark packet parsing
  -> bidirectional flow tracking
  -> 57-feature runtime vector
  -> Primary IDS
  -> Hard-Case Specialist
```

Packet parsing compatibility, FIN/RST lifecycle handling, maximum flow lifetime behavior, flow feature generation, model artifact validation, and hierarchical inference have dedicated regression coverage.

### Next Steps

1. Freeze hierarchical inference configuration
2. Freeze the feature / model contract
3. Complete the runtime integration: PCAP -> flow -> 57 features -> Primary IDS -> Specialist
4. Open the 30,000-flow final-test set once for final evaluation
5. Build the IDS alerting and reporting system
6. Integrate IDS results with the GUI and anomaly-monitoring workflow
7. Add live-traffic integration

The final test set must remain unopened until configuration and contracts are frozen.

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
├── ml/
│   ├── preprocessing/
│   ├── runtime/
│   └── models/
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
- pandas
- scikit-learn
- joblib

---

## Status

**CyberLab v1.0.0 — Stable Wi-Fi Forensics Suite / ML-IDS Validation Milestone**

The Wi-Fi forensics application is stable. The ML/IDS runtime, lifecycle parity, feature contract, hierarchical inference foundation, and read-only Final 30K performance evaluation are documented. Semantic clearance for the zero-duration population remains conditional.
