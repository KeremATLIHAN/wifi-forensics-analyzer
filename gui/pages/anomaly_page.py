from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.live_traffic_monitor import LiveTrafficMonitor
from gui.widgets.live_traffic_chart import LiveTrafficChart


class AnomalyPage(QWidget):
    """CyberLab canlı ağ anomali izleme sayfası."""

    monitoring_requested = Signal(int, int)
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.monitor = LiveTrafficMonitor()
        self.traffic_chart = LiveTrafficChart(max_points=60)
        self.traffic_chart.setMinimumHeight(220)
        self.traffic_chart.setMaximumHeight(260)

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
        self.session_status_label = QLabel(
            "Canlı trafik izleme bekleniyor..."
        )
        self.session_interface_label = QLabel(
            "Arayüz: —"
        )
        self.session_duration_label = QLabel(
            "Süre: 00:00 / 00:00"
        )

        self.elapsed_value = QLabel("00:00")
        self.packet_value = QLabel("0")
        self.pps_value = QLabel("0")
        self.traffic_value = QLabel("0.00 Mbps")
        self.total_data_value = QLabel("0 MB")
        self.peak_value = QLabel("0.00 Mbps")

        self.findings_container = QWidget()
        self.findings_layout = QVBoxLayout(
            self.findings_container
        )
        self.findings_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.findings_layout.setSpacing(10)
        self.findings_layout.addStretch(1)
        self.finding_count = 0

        self._build_ui()
        self._connect_signals()
        self.load_interfaces()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
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
        layout.addWidget(self._create_timeline_panel())
        layout.addWidget(
            self._create_findings_panel()
        )
        layout.addWidget(
            self._create_session_status_bar()
        )

        self.status_label.setObjectName("moduleStatus")
        layout.addWidget(self.status_label)

        layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

    def _create_session_status_bar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("statusBarCard")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.session_status_label.setObjectName(
            "sessionStatusText"
        )
        self.session_interface_label.setObjectName(
            "sessionMetaText"
        )
        self.session_duration_label.setObjectName(
            "sessionMetaText"
        )

        layout.addWidget(self.session_status_label)
        layout.addStretch(1)
        layout.addWidget(self.session_interface_label)

        separator = QLabel("|")
        separator.setObjectName("sessionMetaText")
        layout.addWidget(separator)
        layout.addWidget(self.session_duration_label)

        return panel

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

    def _create_timeline_panel(
            self,
        ) -> QFrame:
            panel = QFrame()
            panel.setObjectName(
                "contentCard"
            )
            panel.setMinimumHeight(310)

            layout = QVBoxLayout(panel)
            layout.setContentsMargins(
                18,
                18,
                18,
                18,
            )
            layout.setSpacing(12)

            heading = QLabel(
                "Live Traffic Timeline"
            )
            heading.setObjectName(
                "sectionTitle"
            )

            description = QLabel(
                "Son 60 saniyelik anlık trafik "
                "seviyesi (Mbps)."
            )
            description.setObjectName(
                "pageDescription"
            )

            layout.addWidget(heading)
            layout.addWidget(description)
            layout.addWidget(
                self.traffic_chart
            )

            return panel

    def _create_findings_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentCard")
        panel.setMinimumHeight(300)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel("Anomaly Findings")
        heading.setObjectName("sectionTitle")

        self.findings_info = QLabel(
            "Henüz anomali tespit edilmedi."
        )
        self.findings_info.setObjectName("pageDescription")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(180)
        scroll.setMaximumHeight(300)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.findings_container)

        layout.addWidget(heading)
        layout.addWidget(self.findings_info)
        layout.addWidget(scroll)

        return panel

    def clear_findings(self) -> None:
        while self.findings_layout.count() > 1:
            item = self.findings_layout.takeAt(0)

            if item is None:
                continue

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.finding_count = 0
        self.findings_info.setText(
            "Henüz anomali tespit edilmedi."
        )

    def add_point_finding(
        self,
        *,
        elapsed_seconds: int,
        value: float,
        baseline: float,
        z_score: float,
        severity: str,
        detected_at: str,
    ) -> None:
        self.finding_count += 1
        self.findings_info.setText(
            f"{self.finding_count} anomali tespit edildi."
        )

        card = QFrame()
        card.setObjectName("anomalyFindingCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        minutes, seconds = divmod(
            elapsed_seconds,
            60,
        )

        title = QLabel(
            f"POINT ANOMALY  ·  {severity.upper()}"
        )
        title.setObjectName("sectionTitle")

        reason = QLabel(
            "Ani trafik sapması tespit edildi."
        )
        reason.setObjectName("findingDescription")

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(8)

        def add_metric(label: str, metric_value: str) -> None:
            metric = QFrame()
            metric.setStyleSheet(
                """
                QFrame {
                    background-color: #14243A;
                    border: 1px solid #29405E;
                    border-radius: 7px;
                }
                """
            )

            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(10, 8, 10, 8)
            metric_layout.setSpacing(2)

            metric_title = QLabel(label)
            metric_title.setStyleSheet(
                "color: #94A3B8; font-size: 11px;"
            )

            metric_value_label = QLabel(metric_value)
            metric_value_label.setStyleSheet(
                "color: #F8FAFC; font-size: 13px; "
                "font-weight: 700;"
            )

            metric_layout.addWidget(metric_title)
            metric_layout.addWidget(metric_value_label)
            metrics_layout.addWidget(metric, 1)

        add_metric(
            "Zaman",
            f"{minutes:02d}:{seconds:02d}",
        )
        add_metric(
            "Gözlenen",
            f"{value:.2f} Mbps",
        )
        add_metric(
            "Baseline",
            f"{baseline:.2f} Mbps",
        )
        add_metric(
            "Z-Score",
            f"{z_score:.2f}",
        )

        layout.addWidget(title)
        layout.addWidget(reason)
        layout.addLayout(metrics_layout)

        time_label = QLabel(detected_at)
        time_label.setStyleSheet(
            "color: #94A3B8; font-size: 11px;"
        )
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(time_label)

        self.findings_layout.insertWidget(
            self.findings_layout.count() - 1,
            card,
        )

    def add_contextual_finding(
        self,
        *,
        elapsed_seconds: int,
        value: float,
        baseline: float,
        z_score: float,
        severity: str,
        detected_at: str,
    ) -> None:
        self.finding_count += 1
        self.findings_info.setText(
            f"{self.finding_count} anomali tespit edildi."
        )

        minutes, seconds = divmod(elapsed_seconds, 60)

        card = QFrame()
        card.setObjectName("anomalyFindingCard")
        card.setMinimumHeight(88)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(5)

        title = QLabel(
            f"CONTEXTUAL ANOMALY · {severity.upper()}"
        )
        title.setStyleSheet(
            "font-size: 14px; font-weight: 800; "
            "color: #F8FAFC;"
        )
        reason = QLabel(
            "Trafik seviyesi mevcut oturum bağlamına "
            "göre beklenmeyen sapma gösterdi."
        )
        details = QLabel(
            f"Zaman: {minutes:02d}:{seconds:02d}   |   "
            f"Gözlenen: {value:.2f} Mbps   |   "
            f"Yerel Baseline: {baseline:.2f} Mbps   |   "
            f"Z-Score: {z_score:.2f}   |   "
            f"Saat: {detected_at}"
        )
        details.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(reason)
        layout.addWidget(details)

        self.findings_layout.insertWidget(
            self.findings_layout.count() - 1,
            card,
        )
