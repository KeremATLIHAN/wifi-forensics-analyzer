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

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from src.config import PROJECT_ROOT
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
    """Okunabilir ve markalı bir HTML analiz raporu oluşturur."""

    ensure_directory(output_file.parent)

    network_rows: list[str] = []

    for network in report.get("networks", []):
        ssid_text = (
            ", ".join(network.get("ssids", []))
            if network.get("ssids")
            else "SSID belirlenemedi"
        )

        channel = (
            network.get("channel")
            if network.get("channel") is not None
            else "Bilinmiyor"
        )

        signal_value = network.get("average_signal_dbm")
        signal = (
            f"{signal_value} dBm"
            if signal_value is not None
            else "Bilinmiyor"
        )

        client_rows: list[str] = []

        for client in network.get("clients", [])[:25]:
            client_rows.append(
                "<tr>"
                f"<td>{html.escape(str(client.get('mac', '—')))}</td>"
                f"<td>{html.escape(str(client.get('vendor', 'Bilinmiyor')))}</td>"
                f"<td>{html.escape(str(client.get('packet_count', 0)))}</td>"
                f"<td>{html.escape(str(client.get('sent_packets', 0)))}</td>"
                f"<td>{html.escape(str(client.get('received_packets', 0)))}</td>"
                f"<td>{html.escape(str(client.get('first_seen', '—')))}</td>"
                f"<td>{html.escape(str(client.get('last_seen', '—')))}</td>"
                f"<td>{html.escape(str(client.get('activity_level', '—')))}</td>"
                "</tr>"
            )

        clients_table = (
            "<table>"
            "<thead><tr>"
            "<th>İstemci MAC</th>"
            "<th>Vendor</th>"
            "<th>Toplam Paket</th>"
            "<th>Gönderilen</th>"
            "<th>Alınan</th>"
            "<th>İlk Görülme</th>"
            "<th>Son Görülme</th>"
            "<th>Aktivite</th>"
            "</tr></thead>"
            "<tbody>"
            + (
                "".join(client_rows)
                if client_rows
                else (
                    "<tr><td colspan='8'>"
                    "Bu ağ için istemci gözlemlenmedi."
                    "</td></tr>"
                )
            )
            + "</tbody>"
            "</table>"
        )

        network_rows.append(
            "<section class='network-card'>"
            f"<h3>{html.escape(ssid_text)}</h3>"
            "<dl>"
            f"<dt>BSSID</dt><dd>{html.escape(str(network.get('bssid', '—')))}</dd>"
            f"<dt>Kanal</dt><dd>{html.escape(str(channel))}</dd>"
            f"<dt>Ortalama sinyal</dt><dd>{html.escape(signal)}</dd>"
            f"<dt>İstemci sayısı</dt><dd>{len(network.get('clients', []))}</dd>"
            "</dl>"
            f"{clients_table}"
            "</section>"
        )

    subtype_rows: list[str] = []

    for subtype, count in report.get("frame_subtypes", {}).items():
        subtype_rows.append(
            "<tr>"
            f"<td>{html.escape(str(subtype))}</td>"
            f"<td>{html.escape(str(count))}</td>"
            "</tr>"
        )

    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    findings = report.get("security_findings", [])
    finding_rows: list[str] = []

    severity_map = {
        "critical": ("KRİTİK", "#ef4444"),
        "warning": ("UYARI", "#f59e0b"),
        "success": ("BAŞARILI", "#10b981"),
        "info": ("BİLGİ", "#3b82f6"),
    }

    for finding in findings:
        severity = str(finding.get("severity", "info"))

        label, color = severity_map.get(
            severity,
            ("BİLGİ", "#3b82f6"),
        )

        title = html.escape(
            str(finding.get("title", "Bulgu"))
        )

        description = html.escape(
            str(finding.get("description", ""))
        )

        finding_rows.append(
            f"""
            <div class="finding">
                <div
                    class="finding-indicator"
                    style="background:{color};"
                ></div>

                <div class="finding-content">
                    <div class="finding-header">
                        <span
                            class="finding-badge"
                            style="
                                color:{color};
                                border-color:{color};
                            "
                        >
                            {label}
                        </span>

                        <strong>{title}</strong>
                    </div>

                    <p>{description}</p>
                </div>
            </div>
            """
        )

    findings_html = (
        "".join(finding_rows)
        if finding_rows
        else """
        <div class="finding">
            <div
                class="finding-indicator"
                style="background:#10b981;"
            ></div>

            <div class="finding-content">
                <div class="finding-header">
                    <span
                        class="finding-badge"
                        style="
                            color:#10b981;
                            border-color:#10b981;
                        "
                    >
                        BİLGİ
                    </span>

                    <strong>
                        Ek güvenlik bulgusu bulunamadı
                    </strong>
                </div>

                <p>
                    Analiz motoru bu yakalama için
                    ek bir güvenlik bulgusu üretmedi.
                </p>
            </div>
        </div>
        """
    )

    document = f"""<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>CyberLab Wi-Fi Forensics Report</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 0;
            background: #f1f5f9;
            color: #1e293b;
            font-family: "Segoe UI", Arial, sans-serif;
        }}

        main {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 36px 24px 60px;
        }}

        .report-header {{
            background: #0f172a;
            color: #ffffff;
            padding: 32px;
            border: 1px solid #1e293b;
            border-radius: 14px;
            margin-bottom: 24px;
        }}

        .brand {{
            color: #2dd4bf;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 4px;
            margin-bottom: 8px;
        }}

        .report-header h1 {{
            margin: 0 0 8px;
            font-size: 30px;
            font-weight: 800;
        }}

        .report-header > p {{
            margin: 0;
            color: #cbd5e1;
            font-size: 14px;
        }}

        .metadata {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-top: 24px;
        }}

        .metadata-item {{
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 12px;
            color: #f8fafc;
        }}

        .metadata-label {{
            display: block;
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: #ffffff;
            border: 1px solid #dbe3ec;
            border-radius: 12px;
            padding: 18px;
        }}

        .summary-label {{
            color: #64748b;
            font-size: 13px;
            font-weight: 600;
        }}

        .summary-value {{
            display: block;
            color: #0f172a;
            font-size: 28px;
            font-weight: 800;
            margin-top: 8px;
        }}

        .report-section {{
            margin-top: 30px;
        }}

        .section-title {{
            color: #0f172a;
            font-size: 19px;
            font-weight: 800;
            margin: 0 0 14px;
            padding-bottom: 8px;
            border-bottom: 2px solid #2dd4bf;
        }}

        .finding {{
            display: grid;
            grid-template-columns: 5px 1fr;
            gap: 14px;
            background: #ffffff;
            border: 1px solid #dbe3ec;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
        }}

        .finding-indicator {{
            border-radius: 5px;
        }}

        .finding-content {{
            min-width: 0;
        }}

        .finding-header {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .finding-header strong {{
            color: #0f172a;
        }}

        .finding-badge {{
            display: inline-block;
            border: 1px solid;
            border-radius: 5px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: 800;
        }}

        .finding p {{
            margin: 6px 0 0;
            color: #64748b;
            font-size: 13px;
            line-height: 1.5;
        }}

        .network-card {{
            background: #ffffff;
            border: 1px solid #dbe3ec;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
        }}

        .network-card h3 {{
            color: #0f172a;
            margin: 0 0 14px;
            font-size: 17px;
        }}

        dl {{
            display: grid;
            grid-template-columns: 180px 1fr;
            gap: 8px 16px;
            margin: 0;
        }}

        dt {{
            color: #64748b;
            font-weight: 600;
        }}

        dd {{
            margin: 0;
            color: #0f172a;
            font-weight: 600;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 14px;
            background: #ffffff;
        }}

        th {{
            background: #f8fafc;
            color: #475569;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        th,
        td {{
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            padding: 9px 10px;
        }}

        td {{
            color: #334155;
        }}

        .empty-state {{
            background: #ffffff;
            border: 1px solid #dbe3ec;
            border-radius: 10px;
            padding: 16px;
            color: #64748b;
        }}

        .disclaimer {{
            margin-top: 36px;
            padding: 16px;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            color: #64748b;
            font-size: 12px;
            line-height: 1.6;
        }}

        .disclaimer strong {{
            color: #334155;
        }}

        footer {{
            margin-top: 28px;
            text-align: center;
            color: #94a3b8;
            font-size: 11px;
        }}

        @media (max-width: 700px) {{
            .summary {{
                grid-template-columns: 1fr;
            }}

            .metadata {{
                grid-template-columns: 1fr;
            }}

            dl {{
                grid-template-columns: 1fr;
            }}

            main {{
                padding: 18px 12px 40px;
            }}

            .report-header {{
                padding: 22px;
            }}

            .report-header h1 {{
                font-size: 24px;
            }}
        }}
    </style>
</head>

<body>
<main>

    <header class="report-header">
        <div class="brand">
            CYBERLAB
        </div>

        <h1>
            Wi-Fi Forensics Analysis Report
        </h1>

        <p>
            Kablosuz ağ yakalama dosyası analiz raporu
        </p>

        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">
                    Yakalama Dosyası
                </span>
                {html.escape(capture_name)}
            </div>

            <div class="metadata-item">
                <span class="metadata-label">
                    Rapor Tarihi
                </span>
                {generated_at}
            </div>

            <div class="metadata-item">
                <span class="metadata-label">
                    Analiz Modülü
                </span>
                Wi-Fi Forensics
            </div>
        </div>
    </header>

    <div class="summary">
        <div class="summary-card">
            <span class="summary-label">
                Toplam Paket
            </span>
            <strong class="summary-value">
                {report.get("total_packets", 0)}
            </strong>
        </div>

        <div class="summary-card">
            <span class="summary-label">
                Tespit Edilen Ağ
            </span>
            <strong class="summary-value">
                {report.get("network_count", 0)}
            </strong>
        </div>

        <div class="summary-card">
            <span class="summary-label">
                EAPOL Paketleri
            </span>
            <strong class="summary-value">
                {report.get("eapol_packet_count", 0)}
            </strong>
        </div>
    </div>

    <section class="report-section">
        <h2 class="section-title">
            Security Findings
        </h2>
        {findings_html}
    </section>

    <section class="report-section">
        <h2 class="section-title">
            Tespit Edilen Ağlar
        </h2>

        {
            "".join(network_rows)
            if network_rows
            else (
                '<div class="empty-state">'
                'Analiz sonucunda kablosuz ağ '
                'tespit edilmedi.'
                '</div>'
            )
        }
    </section>

    <section class="report-section">
        <h2 class="section-title">
            802.11 Frame Analysis
        </h2>

        <table>
            <thead>
                <tr>
                    <th>Frame Alt Tipi</th>
                    <th>Paket Sayısı</th>
                </tr>
            </thead>

            <tbody>
                {
                    "".join(subtype_rows)
                    if subtype_rows
                    else (
                        "<tr>"
                        "<td colspan='2'>"
                        "Frame alt tipi verisi bulunamadı."
                        "</td>"
                        "</tr>"
                    )
                }
            </tbody>
        </table>
    </section>

    <div class="disclaimer">
        <strong>
            Analiz Notu:
        </strong>

        Bu rapor, yakalama dosyasında gözlemlenen
        veriler üzerinden otomatik olarak oluşturulmuştur.
        Bir bulgunun raporda bulunmaması,
        ilgili güvenlik olayının gerçekleşmediğini
        tek başına kanıtlamaz.
    </div>

    <footer>
        Generated by CyberLab Desktop Security Suite
    </footer>

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
    """HTML rapor yapısını baskıya uygun stillerle PDF'e dönüştürür."""

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

    pdf_css = """
    <style>
        body {
            background: #ffffff !important;
            color: #1e293b !important;
        }

        main {
            max-width: none !important;
            padding: 18px !important;
        }

        .report-header {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 2px solid #2dd4bf !important;
            border-radius: 8px !important;
            padding: 22px !important;
        }

        .report-header h1 {
            color: #0f172a !important;
        }

        .report-header > p {
            color: #475569 !important;
        }

        .metadata-item {
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }

        .metadata-label {
            color: #64748b !important;
        }

        .summary-card,
        .finding,
        .network-card {
            break-inside: avoid;
            page-break-inside: avoid;
            box-shadow: none !important;
        }

        table {
            page-break-inside: auto;
        }

        tr {
            break-inside: avoid;
            page-break-inside: avoid;
        }

        th {
            background: #f1f5f9 !important;
            color: #334155 !important;
        }
    </style>
    """

    html_content = html_content.replace(
        "</head>",
        pdf_css + "</head>",
    )

    document = QTextDocument()

    # Gerçek CyberLab logosunu PDF kaynağı olarak ekle.
    logo_path = (
        PROJECT_ROOT
        / "resources"
        / "logo"
        / "cyberlab_logo.png"
    )

    if logo_path.exists():
        logo_image = QImage(
            str(logo_path)
        )

        document.addResource(
            QTextDocument.ResourceType.ImageResource,
            QUrl("cyberlab-logo"),
            logo_image,
        )

        logo_html = """
        <div style="
            margin-bottom: 14px;
        ">
            <img
                src="cyberlab-logo"
                width="150"
            >
        </div>
        """

        html_content = html_content.replace(
            '<div class="brand">\n            CYBERLAB\n        </div>',
            logo_html,
        )

    document.setHtml(
        html_content
    )

    printer = QPrinter(
        QPrinter.PrinterMode.HighResolution
    )

    printer.setOutputFormat(
        QPrinter.OutputFormat.PdfFormat
    )

    printer.setOutputFileName(
        str(output_file)
    )

    document.print_(
        printer
    )

    temp_html.unlink(
        missing_ok=True
    )

    return output_file
