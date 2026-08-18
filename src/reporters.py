"""
Analiz sonuçlarını JSON, CSV ve HTML formatlarında kaydeder.
"""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter

from src.utils import ensure_directory


def save_json_report(
    report: dict[str, Any],
    output_file: Path,
) -> Path:
    """Tam analiz raporunu JSON formatında kaydeder."""

    ensure_directory(output_file.parent)

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_file


def save_network_csv(
    report: dict[str, Any],
    output_file: Path,
) -> Path:
    """Tespit edilen ağları CSV formatında kaydeder."""

    ensure_directory(output_file.parent)

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "SSID",
                "BSSID",
                "Kanal",
                "Ortalama_Sinyal_dBm",
                "Istemci_Sayisi",
            ]
        )

        for network in report["networks"]:
            writer.writerow(
                [
                    " | ".join(network["ssids"]),
                    network["bssid"],
                    network["channel"],
                    network["average_signal_dbm"],
                    len(network["clients"]),
                ]
            )

    return output_file


def save_clients_csv(
    report: dict[str, Any],
    output_file: Path,
) -> Path:
    """Ağ ve istemci ilişkilerini CSV formatında kaydeder."""

    ensure_directory(output_file.parent)

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "BSSID",
                "SSID",
                "Istemci_MAC",
                "Paket_Sayisi",
            ]
        )

        for network in report["networks"]:
            ssid_text = " | ".join(network["ssids"])

            for client in network["clients"]:
                writer.writerow(
                    [
                        network["bssid"],
                        ssid_text,
                        client["mac"],
                        client["packet_count"],
                    ]
                )

    return output_file


def save_html_report(
    report: dict[str, Any],
    output_file: Path,
    capture_name: str,
) -> Path:
    """Okunabilir bir HTML analiz raporu oluşturur."""

    ensure_directory(output_file.parent)

    network_rows = []

    for network in report["networks"]:
        ssid_text = (
            ", ".join(network["ssids"])
            if network["ssids"]
            else "SSID belirlenemedi"
        )

        channel = (
            network["channel"]
            if network["channel"] is not None
            else "Bilinmiyor"
        )

        signal = (
            f"{network['average_signal_dbm']} dBm"
            if network["average_signal_dbm"] is not None
            else "Bilinmiyor"
        )

        client_rows = []

        for client in network["clients"][:25]:
            client_rows.append(
                "<tr>"
                f"<td>{html.escape(client['mac'])}</td>"
                f"<td>{client['packet_count']}</td>"
                "</tr>"
            )

        clients_table = (
            "<table>"
            "<thead><tr>"
            "<th>İstemci MAC</th>"
            "<th>Paket sayısı</th>"
            "</tr></thead>"
            "<tbody>"
            + "".join(client_rows)
            + "</tbody>"
            "</table>"
        )

        network_rows.append(
            "<section class='network-card'>"
            f"<h3>{html.escape(ssid_text)}</h3>"
            "<dl>"
            f"<dt>BSSID</dt><dd>{html.escape(network['bssid'])}</dd>"
            f"<dt>Kanal</dt><dd>{html.escape(str(channel))}</dd>"
            f"<dt>Ortalama sinyal</dt><dd>{html.escape(signal)}</dd>"
            f"<dt>İstemci adayı</dt><dd>{len(network['clients'])}</dd>"
            "</dl>"
            f"{clients_table}"
            "</section>"
        )

    subtype_rows = []

    for subtype, count in report["frame_subtypes"].items():
        subtype_rows.append(
            "<tr>"
            f"<td>{html.escape(subtype)}</td>"
            f"<td>{count}</td>"
            "</tr>"
        )

    document = f"""<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Wi-Fi Forensics Raporu</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f6f8;
            color: #1f2933;
        }}

        main {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px;
        }}

        h1, h2, h3 {{
            margin-top: 0;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}

        .summary-card,
        .network-card {{
            background: white;
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        .summary-card strong {{
            display: block;
            font-size: 28px;
            margin-top: 8px;
        }}

        .network-card {{
            margin-bottom: 20px;
        }}

        dl {{
            display: grid;
            grid-template-columns: 180px 1fr;
            gap: 8px 16px;
        }}

        dt {{
            font-weight: bold;
        }}

        dd {{
            margin: 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        th, td {{
            text-align: left;
            border-bottom: 1px solid #d9e2ec;
            padding: 9px;
        }}

        th {{
            background: #e9eef3;
        }}

        .warning {{
            background: #fff4d6;
            border-left: 5px solid #d9a400;
            padding: 14px;
            margin-bottom: 24px;
        }}
    </style>
</head>
<body>
<main>
    <h1>Wi-Fi Forensics Analyzer</h1>
    <p><strong>Yakalama dosyası:</strong> {html.escape(capture_name)}</p>

    <div class="summary">
        <div class="summary-card">
            Toplam paket
            <strong>{report['total_packets']}</strong>
        </div>

        <div class="summary-card">
            Görülen BSSID
            <strong>{report['network_count']}</strong>
        </div>

        <div class="summary-card">
            EAPOL paketi
            <strong>{report['eapol_packet_count']}</strong>
        </div>
    </div>

    {
        "<div class='warning'>EAPOL paketi tespit edilmedi.</div>"
        if report["eapol_packet_count"] == 0
        else ""
    }

    <h2>Tespit edilen ağlar</h2>
    {''.join(network_rows) if network_rows else '<p>Ağ bulunamadı.</p>'}

    <h2>802.11 çerçeve alt tipleri</h2>
    <table>
        <thead>
            <tr>
                <th>Alt tip</th>
                <th>Sayı</th>
            </tr>
        </thead>
        <tbody>
            {''.join(subtype_rows)}
        </tbody>
    </table>
</main>
</body>
</html>
"""

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(document)

    return output_file


def generate_all_reports(
    report: dict[str, Any],
    reports_dir: Path,
    base_name: str,
    capture_name: str,
) -> list[Path]:
    """Tüm rapor formatlarını tek seferde üretir."""

    ensure_directory(reports_dir)

    created_files = [
        save_json_report(
            report,
            reports_dir / f"{base_name}.json",
        ),
        save_network_csv(
            report,
            reports_dir / f"{base_name}_networks.csv",
        ),
        save_clients_csv(
            report,
            reports_dir / f"{base_name}_clients.csv",
        ),
        save_html_report(
            report,
            reports_dir / f"{base_name}.html",
            capture_name,
        ),
    ]

    return created_files

def export_json_report(
    report: dict,
    output_dir: Path,
) -> Path:
    """CyberLab analiz sonucunu JSON raporu olarak kaydeder."""

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        output_dir
        / f"cyberlab_report_{timestamp}.json"
    )

    payload = {
        "product": "CyberLab",
        "module": "Wi-Fi Forensics",
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "report": report,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    return output_path


def save_pdf_report(
    report: dict[str, Any],
    output_file: Path,
    capture_name: str,
) -> Path:
    """HTML rapor yapısını kullanarak PDF çıktısı oluşturur."""

    ensure_directory(output_file.parent)

    temp_html = output_file.with_suffix(".temp.html")

    save_html_report(
        report,
        temp_html,
        capture_name,
    )

    html_content = temp_html.read_text(
        encoding="utf-8"
    )

    document = QTextDocument()
    document.setHtml(html_content)

    printer = QPrinter(
        QPrinter.PrinterMode.HighResolution
    )
    printer.setOutputFormat(
        QPrinter.OutputFormat.PdfFormat
    )
    printer.setOutputFileName(
        str(output_file)
    )

    document.print_(printer)

    temp_html.unlink(
        missing_ok=True
    )

    return output_file
