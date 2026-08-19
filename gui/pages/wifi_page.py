"""CyberLab Wi-Fi Forensics kullanıcı arayüzü."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from PySide6.QtWidgets import QScrollArea

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QAbstractItemView,
    QTableWidgetItem,
    QSplitter,

)

from src.config import REPORTS_DIR
from src.reporters import (
    save_html_report,
    save_json_report,
    save_pdf_report,
)


class WifiPage(QWidget):
    """Wi-Fi yakalama dosyalarının yönetildiği modül sayfası."""

    capture_selected = Signal(Path)
    analysis_requested = Signal(Path)

    def __init__(self) -> None:
        super().__init__()

        self.selected_capture: Path | None = None
        self.summary_values: dict[str, QLabel] = {}
        self.current_report: dict | None = None

        self.capture_path_input = QLineEdit()
        self.browse_button = QPushButton("Dosya Seç")
        self.analyze_button = QPushButton("Analiz Et")

        self.export_button = QPushButton("Raporu Kaydet")
        self.export_button.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.status_label = QLabel(
            "Analiz için bir yakalama dosyası seçin."
        )

        self.network_table = QTableWidget()
        self.client_table = QTableWidget()
        self.analysis_log = QPlainTextEdit()

        self.detail_values: dict[str, QLabel] = {}
        self.device_detail_values: dict[str, QLabel] = {}
        self.current_clients: list[dict] = []
        self.current_handshake_candidates: list[dict] = []

        self.handshake_details_button = QPushButton(
            "Handshake Detayları"
        )
        self.handshake_details_button.setEnabled(False)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """Wi-Fi Forensics sayfasını oluşturur."""

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)

        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Wi-Fi Forensics")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Yetkili laboratuvar ortamlarında oluşturulan CAP, "
            "PCAP ve PCAPNG dosyalarını inceleyin."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self._create_capture_panel())
        layout.addWidget(self._create_summary_panel())

        results_splitter = QSplitter(
            Qt.Orientation.Horizontal
        )
        results_splitter.setObjectName("resultsSplitter")
        results_splitter.setChildrenCollapsible(False)

        networks_panel = self._create_networks_panel()
        details_panel = self._create_network_details_panel()

        networks_panel.setMinimumHeight(280)
        details_panel.setMinimumHeight(280)

        results_splitter.addWidget(networks_panel)
        results_splitter.addWidget(details_panel)

        results_splitter.setStretchFactor(0, 3)
        results_splitter.setStretchFactor(1, 2)
        results_splitter.setSizes([700, 420])

        layout.addWidget(results_splitter)

        clients_section = self._create_clients_section()
        clients_section.setMinimumHeight(260)

        layout.addWidget(clients_section)

        layout.addWidget(self._create_findings_panel())

        log_panel = self._create_log_panel()
        log_panel.setMinimumHeight(160)

        layout.addWidget(log_panel)

        self.status_label.setObjectName("moduleStatus")
        layout.addWidget(self.status_label)

        scroll_area.setWidget(content)

        outer_layout.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        """Sayfadaki düğmelerin olaylarını bağlar."""

        self.browse_button.clicked.connect(
            self._select_capture_file
        )
        self.analyze_button.clicked.connect(
            self._request_analysis
        )
        self.export_button.clicked.connect(
            self._export_report
        )
        self.handshake_details_button.clicked.connect(
            self._show_handshake_details
        )

    def _create_capture_panel(self) -> QFrame:
        """Dosya seçme ve analiz başlatma panelini oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.capture_path_input.setReadOnly(True)
        self.capture_path_input.setPlaceholderText(
            "Bir .cap, .pcap veya .pcapng dosyası seçin"
        )

        self.analyze_button.setObjectName("primaryButton")
        self.analyze_button.setEnabled(False)

        controls.addWidget(self.capture_path_input, 1)
        controls.addWidget(self.browse_button)
        controls.addWidget(self.analyze_button)
        controls.addWidget(self.export_button)

        self.progress_bar.setObjectName("analysisProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(18)

        layout.addLayout(controls)
        layout.addWidget(self.progress_bar)

        return panel

    def _create_summary_panel(self) -> QWidget:
        """Paket ve ağ özet kartlarını oluşturur."""

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        cards = (
            ("packets", "◫", "Paketler"),
            ("networks", "◉", "Ağlar"),
            ("clients", "♟", "İstemciler"),
            ("eapol", "◆", "EAPOL"),
        )

        for key, icon, title in cards:
            card, value_label = self._create_summary_card(
                icon,
                title,
            )
            self.summary_values[key] = value_label
            layout.addWidget(card)

        return container

    @staticmethod
    def _create_summary_card(
        icon: str,
        title: str,
    ) -> tuple[QFrame, QLabel]:
        """Tek bir modern özet kartı oluşturur."""

        card = QFrame()
        card.setObjectName("summaryCard")
        card.setMinimumHeight(118)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setObjectName("summaryIcon")

        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        value_label = QLabel("—")
        value_label.setObjectName("summaryValue")

        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.addStretch(1)

        return card, value_label

    def _create_networks_panel(self) -> QFrame:
        """Tespit edilen ağların gösterileceği tabloyu oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Tespit Edilen Ağlar")
        heading.setObjectName("sectionTitle")

        self.network_table.setColumnCount(5)
        self.network_table.setHorizontalHeaderLabels(
            [
                "SSID",
                "BSSID",
                "Kanal",
                "Sinyal",
                "İstemci",
            ]
        )
        self.network_table.setAlternatingRowColors(True)
        self.network_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.network_table.verticalHeader().setVisible(False)

        header = self.network_table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.network_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.network_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.network_table.setShowGrid(False)

        layout.addWidget(heading)
        layout.addWidget(self.network_table)

        return panel

    def _select_capture_file(self) -> None:
        """Kullanıcıdan bir yakalama dosyası seçmesini ister."""

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Yakalama Dosyası Seç",
            "",
            (
                "Wi-Fi Capture Files "
                "(*.cap *.pcap *.pcapng);;"
                "All Files (*)"
            ),
        )

        if not file_path:
            return

        self.selected_capture = Path(file_path)
        self.capture_path_input.setText(file_path)
        self.analyze_button.setEnabled(True)
        self.progress_bar.setValue(0)

        self.status_label.setStyleSheet(
            "color: #94A3B8; font-weight: 600;"
        )
        self.status_label.setText(
            "Dosya seçildi. Analizi başlatabilirsiniz."
        )

        self.capture_selected.emit(self.selected_capture)

    def _request_analysis(self) -> None:
        """Seçili dosya için analiz isteği yayınlar."""

        if self.selected_capture is None:
            return

        self.status_label.setText(
            "Analiz motoru bağlantısı hazırlanıyor..."
        )

        self.analysis_requested.emit(self.selected_capture)


    def _create_network_details_panel(self) -> QFrame:
        """Seçilen ağın ayrıntı panelini oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")
        panel.setMinimumWidth(240)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        heading = QLabel("Ağ Detayları")
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        fields = (
            ("ssid", "SSID"),
            ("bssid", "BSSID"),
            ("channel", "Kanal"),
            ("signal", "Sinyal"),
            ("clients", "İstemciler"),
            ("eapol", "EAPOL"),
            ("handshake", "Handshake"),
        )

        for key, title in fields:
            row = QHBoxLayout()

            title_label = QLabel(f"{title}:")
            title_label.setStyleSheet(
                "color: #94A3B8; font-weight: 600;"
            )

            value_label = QLabel("—")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                value_label.textInteractionFlags()
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )

            title_label.setMinimumWidth(90)
            row.addWidget(title_label)
            row.addWidget(value_label, 1)

            self.detail_values[key] = value_label
            layout.addLayout(row)

        self.handshake_details_button.setObjectName(
            "secondaryButton"
        )

        layout.addWidget(
            self.handshake_details_button
        )

        layout.addStretch(1)

        return panel


    def show_network_details(
        self,
        network: dict,
        eapol_count: int,
        handshake_candidates: list[dict] | None = None,
    ) -> None:
        """Seçilen ağın bilgilerini detay panelinde gösterir."""

        ssids = network.get("ssids", [])
        clients = network.get("clients", [])
        self.current_clients = clients

        if clients:
            self.client_table.selectRow(0)
        else:
            self.clear_device_details()

        signal = network.get("average_signal_dbm")
        channel = network.get("channel")

        self.detail_values["ssid"].setText(
            ", ".join(ssids) if ssids else "<Gizli SSID>"
        )
        self.detail_values["bssid"].setText(
            str(network.get("bssid", "—"))
        )
        self.detail_values["channel"].setText(
            str(channel if channel is not None else "—")
        )
        self.detail_values["signal"].setText(
            f"{signal} dBm" if signal is not None else "—"
        )
        self.detail_values["clients"].setText(
            str(len(clients))
        )
        self.detail_values["eapol"].setText(
            str(eapol_count)
        )

        handshake_candidates = handshake_candidates or []

        network_bssid = str(
            network.get("bssid", "")
        ).lower()

        network_candidates = [
            candidate
            for candidate in handshake_candidates
            if str(
                candidate.get("bssid", "")
            ).lower() == network_bssid
        ]

        self.current_handshake_candidates = (
            network_candidates
        )

        self.handshake_details_button.setEnabled(
            bool(network_candidates)
        )

        strong_candidates = [
            candidate
            for candidate in network_candidates
            if candidate.get("status") == "strong_candidate"
        ]

        partial_candidates = [
            candidate
            for candidate in network_candidates
            if candidate.get("status") == "partial"
        ]

        if strong_candidates:
            handshake_text = (
                f"● Güçlü Aday ({len(strong_candidates)})"
            )
            handshake_style = (
                "color: #34D399; font-weight: 700;"
            )
        elif partial_candidates:
            handshake_text = (
                f"● Kısmi ({len(partial_candidates)})"
            )
            handshake_style = (
                "color: #FBBF24; font-weight: 700;"
            )
        else:
            handshake_text = "● Bulunamadı"
            handshake_style = (
                "color: #F87171; font-weight: 700;"
            )

        self.detail_values["handshake"].setText(
            handshake_text
        )

        self.detail_values["handshake"].setStyleSheet(
            handshake_style
        )

        self.client_table.setRowCount(len(clients))

        for row_index, client in enumerate(clients):
            mac_address = str(
                client.get("mac", "—")
            )

            vendor = str(
                client.get("vendor", "Bilinmiyor")
            )

            packet_count = str(
                client.get("packet_count", 0)
            )

            self.client_table.setItem(
                row_index,
                0,
                QTableWidgetItem(mac_address),
            )

            self.client_table.setItem(
                row_index,  
                1,
                QTableWidgetItem(vendor),
            )

            self.client_table.setItem(
                row_index,
                2,
                QTableWidgetItem(packet_count),
            )

    def _show_handshake_details(self) -> None:
        """Seçili ağın handshake adaylarını bir tabloda gösterir."""

        if not self.current_handshake_candidates:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Handshake Detayları")
        dialog.resize(900, 360)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Handshake Adayları")
        heading.setObjectName("sectionTitle")

        description = QLabel(
            "Seçili ağ için istemci bazında tespit edilen "
            "EAPOL alışverişleri."
        )
        description.setWordWrap(True)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            [
                "BSSID",
                "İstemci",
                "EAPOL",
                "Durum",
                "İlk Görülme",
                "Son Görülme",
            ]
        )
        table.setRowCount(
            len(self.current_handshake_candidates)
        )

        for row, candidate in enumerate(
            self.current_handshake_candidates
        ):
            status = candidate.get(
                "status",
                "partial",
            )

            status_text = (
                "Güçlü Aday"
                if status == "strong_candidate"
                else "Kısmi"
            )

            values = [
                candidate.get("bssid", "—"),
                candidate.get("client", "—"),
                candidate.get(
                    "eapol_packet_count",
                    0,
                ),
                status_text,
                candidate.get(
                    "first_seen",
                    "—",
                ),
                candidate.get(
                    "last_seen",
                    "—",
                ),
            ]

            for column, value in enumerate(values):
                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        table.verticalHeader().setVisible(False)

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        close_button = QPushButton(
            "Kapat"
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(table)
        layout.addWidget(close_button)

        dialog.exec()


    def clear_network_details(self) -> None:
        """Detay panelini temizler."""

        for key, label in self.detail_values.items():
            label.setText("—")

            if key == "handshake":
                label.setStyleSheet("")

        self.client_table.setRowCount(0)

        self.current_clients = []
        self.current_handshake_candidates = []
        self.handshake_details_button.setEnabled(
            False
        )
        self.client_table.setRowCount(0)
        self.clear_device_details()

    def _create_log_panel(self) -> QFrame:
        """Canlı analiz günlüğü panelini oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")
        panel.setMinimumHeight(160)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        heading = QLabel("Analiz Günlüğü")
        heading.setObjectName("sectionTitle")

        self.analysis_log.setReadOnly(True)
        self.analysis_log.setObjectName("analysisLog")
        self.analysis_log.setPlaceholderText(
            "Analiz işlemleri burada görüntülenecek..."
        )
        self.analysis_log.setMaximumBlockCount(200)

        layout.addWidget(heading)
        layout.addWidget(self.analysis_log)

        return panel

    def add_log(self, message: str) -> None:
        """Analiz günlüğüne bir mesaj ekler."""

        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")

        self.analysis_log.appendPlainText(f"[{timestamp}] {message}")

        scroll_bar = self.analysis_log.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def clear_log(self) -> None:
        """Analiz günlüğünü temizler."""

        self.analysis_log.clear()


    def _create_clients_section(self) -> QSplitter:
        """İstemci listesi ve cihaz detaylarını responsive olarak gösterir."""

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        splitter.setObjectName(
            "clientsSplitter"
        )

        splitter.setChildrenCollapsible(False)

        splitter.addWidget(
            self._create_clients_panel()
        )

        splitter.addWidget(
            self._create_device_details_panel()
        )

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        splitter.setSizes(
            [720, 400]
        )

        return splitter 

    def _create_clients_panel(self) -> QFrame:
        """Seçilen ağa bağlı istemcileri gösterir."""

        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )
        layout.setSpacing(10)

        heading = QLabel("İstemci Cihazları")
        heading.setObjectName("sectionTitle")

        self.client_table.setColumnCount(3)

        self.client_table.setHorizontalHeaderLabels(
            [
                "MAC Adresi",
                "Vendor",
                "Paket Sayısı",
            ]
        )

        self.client_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.client_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.client_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.client_table.setAlternatingRowColors(True)
        self.client_table.setShowGrid(False)

        self.client_table.verticalHeader().setVisible(
            False
        )

        header = self.client_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.client_table.itemSelectionChanged.connect(
            self._on_client_selected
        )

        layout.addWidget(heading)
        layout.addWidget(self.client_table)

        return panel

    def _create_device_details_panel(self) -> QFrame:
        """Seçilen istemci cihazının ayrıntılarını gösterir."""

        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )
        layout.setSpacing(12)

        heading = QLabel("Cihaz Detayları")
        heading.setObjectName("sectionTitle")

        layout.addWidget(heading)

        fields = (
            ("mac", "MAC Adresi"),
            ("vendor", "Üretici"),
            ("packets", "Toplam Paket"),
            ("sent", "Gönderilen"),
            ("received", "Alınan"),
            ("first_seen", "İlk Görülme"),
            ("last_seen", "Son Görülme"),
            ("activity", "Aktivite"),
        )

        for key, title in fields:

            row = QHBoxLayout()
            row.setSpacing(12)

            title_label = QLabel(title)
            title_label.setObjectName(
                "detailTitle"
            )
            title_label.setMinimumWidth(100)

            value_label = QLabel("—")
            value_label.setObjectName(
                "detailValue"
            )

            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            row.addWidget(title_label)
            row.addWidget(value_label, 1)

            self.device_detail_values[key] = (
                value_label
            )

            layout.addLayout(row)

        layout.addStretch(1)

        return panel

    def _on_client_selected(self) -> None:
            """Seçilen istemcinin detaylarını gösterir."""

            row = self.client_table.currentRow()

            if not 0 <= row < len(self.current_clients):
                self.clear_device_details()
                return

            client = self.current_clients[row]

            self.device_detail_values["mac"].setText(
                str(client.get("mac", "—"))
            )
            self.device_detail_values["vendor"].setText(
                str(client.get("vendor", "Bilinmiyor"))
            )

            self.device_detail_values["packets"].setText(
                str(client.get("packet_count", 0))
            )

            self.device_detail_values["sent"].setText(
                str(client.get("sent_packets", 0))
            )

            self.device_detail_values["received"].setText(
                str(client.get("received_packets", 0))
            )

            self.device_detail_values["first_seen"].setText(
                str(client.get("first_seen", "—"))
            )

            self.device_detail_values["last_seen"].setText(
                str(client.get("last_seen", "—"))
            )

            activity = str(
                client.get("activity_level", "Düşük")
            )

            self.device_detail_values["activity"].setText(
                f"● {activity}"
            )

            activity_colors = {
                "Düşük": "#94A3B8",
                "Orta": "#FBBF24",
                "Yüksek": "#34D399",
            }

            self.device_detail_values[
                "activity"
            ].setStyleSheet(
                f"color: {activity_colors.get(activity, '#94A3B8')}; "
                "font-weight: 700;"
            )

    def clear_device_details(self) -> None:
        """Cihaz detay panelini temizler."""

        for label in self.device_detail_values.values():
            label.setText("—")
            label.setStyleSheet("")

    def _create_findings_panel(self) -> QFrame:
        """Security Findings panelini oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        heading = QLabel("Security Findings")
        heading.setObjectName("sectionTitle")

        layout.addWidget(heading)

        self.findings_layout = QVBoxLayout()
        self.findings_layout.setSpacing(8)

        placeholder = QLabel(
            "Analiz tamamlandığında güvenlik bulguları burada gösterilecek."
        )
        placeholder.setObjectName("findingDescription")
        placeholder.setWordWrap(True)

        self.findings_layout.addWidget(placeholder)

        layout.addLayout(self.findings_layout)

        return panel


    def show_security_findings(
        self,
        findings: list[dict[str, str]],
    ) -> None:
        """Analiz bulgularını kullanıcıya gösterir."""

        if self.findings_layout is None:
            return

        while self.findings_layout.count():
            item = self.findings_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        if not findings:
            label = QLabel(
                "Analiz sonucunda ek bir güvenlik bulgusu üretilmedi."
            )
            label.setWordWrap(True)
            self.findings_layout.addWidget(label)
            return

        severity_styles = {
            "success": ("#34D399", "✓"),
            "warning": ("#FBBF24", "⚠"),
            "info": ("#60A5FA", "●"),
            "critical": ("#F87171", "✕"),
        }

        for finding in findings:
            severity = finding.get("severity", "info")
            color, symbol = severity_styles.get(
                severity,
                ("#94A3B8", "●"),
            )

            card = QFrame()
            card.setObjectName("findingCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)

            title = QLabel(
                f"{symbol} {finding.get('title', 'Bulgu')}"
            )
            title.setStyleSheet(
                f"color: {color}; font-weight: 700;"
            )

            description = QLabel(
                finding.get("description", "")
            )
            description.setObjectName("findingDescription")
            description.setWordWrap(True)

            card_layout.addWidget(title)
            card_layout.addWidget(description)

            self.findings_layout.addWidget(card)


    def set_analysis_report(
        self,
        report: dict,
    ) -> None:
        """Son analiz raporunu saklar."""

        self.current_report = report
        self.export_button.setEnabled(True)
        self.export_button.setText(
            "Raporu Kaydet"
        )

    def clear_analysis_report(self) -> None:
        """Önceki analiz raporunu temizler."""

        self.current_report = None
        self.export_button.setEnabled(False)

    def _open_report_file(self, output_path: Path) -> None:
        """Kaydedilen raporu uygun uygulamayla açar."""

        resolved_path = output_path.resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Dosya bulunamadı: {resolved_path}"
            )

        if sys.platform == "win32":
            if resolved_path.suffix.lower() == ".html":
                edge_paths = [
                    Path(
                        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                    ),
                    Path(
                        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                    ),
                ]

                for edge_path in edge_paths:
                    if edge_path.exists():
                        subprocess.Popen(
                            [
                                str(edge_path),
                                str(resolved_path),
                            ]
                        )
                        return

            os.startfile(str(resolved_path))
            return

        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(resolved_path)]
            )
            return

        subprocess.Popen(
            ["xdg-open", str(resolved_path)]
        )

    def _export_report(self) -> None:
        """Mevcut analiz sonucunu seçilen formatta dışa aktarır."""

        if not self.current_report:
            self.add_log(
                "Kaydedilecek analiz raporu bulunamadı."
            )
            return

        capture_name = str(
            self.current_report.get(
                "capture_name",
                self.selected_capture.name
                if self.selected_capture
                else "Bilinmeyen dosya",
            )
        )
        default_name = (
            self.selected_capture.stem
            if self.selected_capture
            else "cyberlab_report"
        )

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Raporu Kaydet",
            str(REPORTS_DIR / default_name),
            (
                "PDF Raporu (*.pdf);;"
                "HTML Raporu (*.html);;"
                "JSON Raporu (*.json)"
            ),
        )

        if not file_path:
            return

        output_path = Path(file_path)

        try:
            if "PDF" in selected_filter:
                output_path = output_path.with_suffix(
                    ".pdf"
                )

                save_pdf_report(
                    self.current_report,
                    output_path,
                    capture_name,
                )

            elif "HTML" in selected_filter:
                output_path = output_path.with_suffix(
                    ".html"
                )

                save_html_report(
                    self.current_report,
                    output_path,
                    capture_name,
                )

            else:
                output_path = output_path.with_suffix(
                    ".json"
                )

                save_json_report(
                    self.current_report,
                    output_path,
                )

            self.add_log(
                f"✓ Rapor kaydedildi: {output_path}"
            )

            self.status_label.setText(
                "Rapor başarıyla kaydedildi."
            )

            answer = QMessageBox.question(
                self,
                "Rapor Kaydedildi",
                (
                    "Rapor başarıyla oluşturuldu.\n\n"
                    f"{output_path.name}\n\n"
                    "Dosyayı şimdi görüntülemek "
                    "ister misiniz?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if answer == QMessageBox.StandardButton.Yes:
                try:
                    self._open_report_file(
                        output_path
                    )

                except Exception as exc:
                    self.add_log(
                        f"✕ Dosya açılamadı: {exc}"
                    )

                    QMessageBox.warning(
                        self,
                        "Dosya Açılamadı",
                        (
                            "Rapor başarıyla kaydedildi ancak "
                            "otomatik olarak açılamadı.\n\n"
                            f"{output_path}"
                        ),
                    )

        except Exception as exc:
            self.add_log(
                f"✕ Rapor oluşturulamadı: {exc}"
            )

            self.status_label.setText(
                "Rapor oluşturulamadı."
            )

            QMessageBox.critical(
                self,
                "Rapor Hatası",
                (
                    "Rapor oluşturulurken "
                    "bir hata meydana geldi.\n\n"
                    f"{exc}"
                ),
            )
