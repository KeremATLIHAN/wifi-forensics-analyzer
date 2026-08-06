"""CyberLab Wi-Fi Forensics kullanıcı arayüzü."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
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
        layout.addWidget(self._create_networks_panel(), 1)

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

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

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
            ("packets", "Paketler"),
            ("networks", "Ağlar"),
            ("clients", "İstemciler"),
            ("eapol", "EAPOL"),
        )

        for key, title in cards:
            card, value_label = self._create_summary_card(title)
            self.summary_values[key] = value_label
            layout.addWidget(card)

        return container

    @staticmethod
    def _create_summary_card(
        title: str,
    ) -> tuple[QFrame, QLabel]:
        """Tek bir özet kartı oluşturur."""

        card = QFrame()
        card.setObjectName("summaryCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)

        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")

        value_label = QLabel("—")
        value_label.setObjectName("summaryValue")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

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

        for column in range(1, 5):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

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