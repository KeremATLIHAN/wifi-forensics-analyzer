from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.live_traffic_monitor import LiveTrafficMonitor


class AnomalyPage(QWidget):
    """CyberLab canlı ağ anomali izleme sayfası."""

    monitoring_requested = Signal(int, int)
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.monitor = LiveTrafficMonitor()

        self.interface_combo = QComboBox()

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 120)
        self.duration_spin.setValue(5)
        self.duration_spin.setSuffix(" dk")

        self.start_button = QPushButton("İzlemeyi Başlat")

        self.stop_button = QPushButton("Durdur")
        self.stop_button.setEnabled(False)

        self.status_label = QLabel(
            "Canlı izleme için ağ arayüzü seçin."
        )

        self.elapsed_value = QLabel("00:00")
        self.packet_value = QLabel("0")
        self.pps_value = QLabel("0")
        self.traffic_value = QLabel("0.00 Mbps")
        self.total_data_value = QLabel("0 MB")
        self.peak_value = QLabel("0.00 Mbps")

        self._build_ui()
        self._connect_signals()
        self.load_interfaces()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Anomaly Monitor")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Seçili ağ arayüzündeki canlı trafiği "
            "belirli bir süre boyunca izleyin."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self._create_control_panel())
        layout.addWidget(self._create_live_summary())

        self.status_label.setObjectName("moduleStatus")
        layout.addWidget(self.status_label)

        layout.addStretch(1)

    def _create_control_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("İzleme Ayarları")
        heading.setObjectName("sectionTitle")

        controls = QHBoxLayout()
        controls.setSpacing(10)

        interface_label = QLabel("Ağ Arayüzü:")
        duration_label = QLabel("İzleme Süresi:")

        self.start_button.setObjectName("primaryButton")
        self.stop_button.setObjectName("secondaryButton")

        controls.addWidget(interface_label)
        controls.addWidget(self.interface_combo, 1)
        controls.addWidget(duration_label)
        controls.addWidget(self.duration_spin)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)

        layout.addWidget(heading)
        layout.addLayout(controls)

        return panel

    def _create_live_summary(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentCard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Canlı Trafik")
        heading.setObjectName("sectionTitle")

        layout.addWidget(heading)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        cards = (
            ("Geçen Süre", self.elapsed_value),
            ("Toplam Paket", self.packet_value),
            ("Paket / sn", self.pps_value),
            ("Anlık Trafik", self.traffic_value),
            ("Toplam Veri", self.total_data_value),
            ("Peak", self.peak_value),
        )

        for title, value_label in cards:
            card = QFrame()
            card.setObjectName("summaryCard")

            card_layout = QVBoxLayout(card)

            title_label = QLabel(title)
            title_label.setObjectName("summaryTitle")

            value_label.setObjectName("summaryValue")

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)

            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        return panel

    def _connect_signals(self) -> None:
        self.start_button.clicked.connect(
            self._start_monitoring
        )

        self.stop_button.clicked.connect(
            self._stop_monitoring
        )

    def load_interfaces(self) -> None:
        self.interface_combo.clear()

        try:
            interfaces = self.monitor.list_interfaces()
        except Exception as exc:
            self.status_label.setText(
                f"Arayüzler alınamadı: {exc}"
            )
            return

        for interface in interfaces:
            self.interface_combo.addItem(
                interface.display_name,
                interface.index,
            )

        if interfaces:
            self.status_label.setText(
                f"{len(interfaces)} ağ arayüzü bulundu."
            )
        else:
            self.status_label.setText(
                "Capture edilebilir ağ arayüzü bulunamadı."
            )

    def _start_monitoring(self) -> None:
        interface_index = self.interface_combo.currentData()

        if interface_index is None:
            self.status_label.setText(
                "Lütfen bir ağ arayüzü seçin."
            )
            return

        duration_seconds = (
            self.duration_spin.value()
            * 60
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.status_label.setText(
            "Canlı trafik izleme başlatılıyor..."
        )

        self.monitoring_requested.emit(
            int(interface_index),
            duration_seconds,
        )

    def _stop_monitoring(self) -> None:
        self.stop_button.setEnabled(False)

        self.status_label.setText(
            "İzleme durduruluyor..."
        )

        self.stop_requested.emit()
