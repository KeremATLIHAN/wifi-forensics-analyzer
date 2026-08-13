"""CyberLab Wi-Fi Forensics kullanıcı arayüzü."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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


class WifiPage(QWidget):
    """Wi-Fi yakalama dosyalarının yönetildiği modül sayfası."""

    capture_selected = Signal(Path)
    analysis_requested = Signal(Path)

    def __init__(self) -> None:
        super().__init__()

        self.selected_capture: Path | None = None
        self.summary_values: dict[str, QLabel] = {}

        self.capture_path_input = QLineEdit()
        self.browse_button = QPushButton("Dosya Seç")
        self.analyze_button = QPushButton("Analiz Et")
        self.progress_bar = QProgressBar()
        self.status_label = QLabel(
            "Analiz için bir yakalama dosyası seçin."
        )
        self.network_table = QTableWidget()
        self.client_table = QTableWidget()
        self.current_clients: list[dict] = []
        self.device_detail_values: dict[str, QLabel] = {}
        self.analysis_log = QPlainTextEdit()
        self.detail_values: dict[str, QLabel] = {}

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """Wi-Fi Forensics sayfasını oluşturur."""

        layout = QVBoxLayout(self)
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

        results_splitter.setObjectName(
            "resultsSplitter"
        )

        results_splitter.setChildrenCollapsible(False)

        results_splitter.addWidget(
            self._create_networks_panel()
        )

        results_splitter.addWidget(
            self._create_network_details_panel()
        )

        results_splitter.setStretchFactor(0, 3)
        results_splitter.setStretchFactor(1, 2)

        results_splitter.setSizes(
            [700, 420]
        )

        layout.addWidget(results_splitter, 2)

        layout.addWidget(
        self._create_clients_section(),
        1,
        )
       
        layout.addWidget(self._create_log_panel())
        self.status_label.setObjectName("moduleStatus")
        layout.addWidget(self.status_label)

    def _connect_signals(self) -> None:
        """Sayfadaki düğmelerin olaylarını bağlar."""

        self.browse_button.clicked.connect(
            self._select_capture_file
        )
        self.analyze_button.clicked.connect(
            self._request_analysis
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

            layout.addStretch(1)

        return panel


    def show_network_details(
        self,
        network: dict,
        eapol_count: int,
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
        handshake_found = eapol_count >= 4

        self.detail_values["handshake"].setText(
            "● Bulundu" if handshake_found else "● Bulunamadı"
        )

        self.detail_values["handshake"].setStyleSheet(
            (
                "color: #34D399; font-weight: 700;"
                if handshake_found
                else "color: #F87171; font-weight: 700;"
            )
        )

        self.client_table.setRowCount(len(clients))

        for row_index, client in enumerate(clients):
            mac_address = str(
                client.get("mac", "—")
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
                QTableWidgetItem(packet_count),
            )


    def clear_network_details(self) -> None:
        """Detay panelini temizler."""

        for key, label in self.detail_values.items():
            label.setText("—")

            if key == "handshake":
                label.setStyleSheet("")

        self.client_table.setRowCount(0)

        self.current_clients = []
        self.client_table.setRowCount(0)
        self.clear_device_details()

    def _create_log_panel(self) -> QFrame:
        """Canlı analiz günlüğü panelini oluşturur."""

        panel = QFrame()
        panel.setObjectName("contentCard")
        panel.setMaximumHeight(170)

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

        self.client_table.setColumnCount(2)

        self.client_table.setHorizontalHeaderLabels(
            [
                "MAC Adresi",
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
            ("packets", "Paket Sayısı"),
            ("status", "Durum"),
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

        mac_address = str(
            client.get("mac", "—")
        )

        packet_count = int(
            client.get("packet_count", 0)
        )

        self.device_detail_values["mac"].setText(
            mac_address
        )

        self.device_detail_values["packets"].setText(
            str(packet_count)
        )

        self.device_detail_values["status"].setText(
            "● Aktif"
        )

        self.device_detail_values[
            "status"
        ].setStyleSheet(
            "color: #34D399; font-weight: 700;"
        )

    def clear_device_details(self) -> None:
        """Cihaz detay panelini temizler."""

        for label in self.device_detail_values.values():
            label.setText("—")
            label.setStyleSheet("")