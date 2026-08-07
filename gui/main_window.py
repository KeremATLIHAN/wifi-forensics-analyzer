"""CyberLab Desktop Suite ana pencere yapısı."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from time import perf_counter

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from gui.worker import AnalysisWorker
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.pages.dashboard_page import DashboardPage
from gui.pages.wifi_page import WifiPage


class MainWindow(QMainWindow):
    """CyberLab Desktop Suite ana uygulama penceresi."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CyberLab Desktop Suite")
        self.resize(1280, 780)
        self.setMinimumSize(1000, 650)

        self.navigation_buttons: list[QPushButton] = []
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.wifi_page = WifiPage()

        self.thread_pool = QThreadPool.globalInstance()
        self.active_worker: AnalysisWorker | None = None
        self.last_networks: list[dict[str, Any]] = []
        self.last_eapol_count = 0
        self.analysis_started_at: float | None = None

        self._build_ui()
        self._connect_page_signals()
        self._select_page(0)

    def _build_ui(self) -> None:
        """Ana pencere yerleşimini oluşturur."""

        central_widget = QWidget()
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._create_sidebar())

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.wifi_page)

        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(central_widget)
        self.statusBar().showMessage(
            "CyberLab Desktop Suite hazır."
        )

    def _connect_page_signals(self) -> None:
        """Sayfalardan gelen olayları ana pencereye bağlar."""

        self.wifi_page.capture_selected.connect(
            self._on_capture_selected
        )
        self.wifi_page.analysis_requested.connect(
            self._on_analysis_requested
        )
        self.wifi_page.network_table.itemSelectionChanged.connect(
             self._on_network_selected
        )

    def _create_sidebar(self) -> QFrame:
        """Sol navigasyon panelini oluşturur."""

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 18)
        layout.setSpacing(8)

        brand_title = QLabel("CYBERLAB")
        brand_title.setObjectName("brandTitle")

        brand_subtitle = QLabel("Learn. Analyze. Improve.")
        brand_subtitle.setObjectName("brandSubtitle")

        layout.addWidget(brand_title)
        layout.addWidget(brand_subtitle)
        layout.addSpacing(25)

        layout.addWidget(
            self._create_navigation_button(
                "Dashboard",
                0,
            )
        )
        layout.addWidget(
            self._create_navigation_button(
                "Wi-Fi Forensics",
                1,
            )
        )

        layout.addStretch(1)

        version_label = QLabel("Desktop Suite · v0.2-dev")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(
            "color: #64748B; font-size: 11px;"
        )

        layout.addWidget(version_label)

        return sidebar

    def _create_navigation_button(
        self,
        text: str,
        page_index: int,
    ) -> QPushButton:
        """Sol menü için bir navigasyon düğmesi oluşturur."""

        button = QPushButton(text)
        button.setObjectName("navigationButton")
        button.setCheckable(True)

        button.clicked.connect(
            lambda checked=False, index=page_index: (
                self._select_page(index)
            )
        )

        self.navigation_buttons.append(button)

        return button

    def _select_page(self, page_index: int) -> None:
        """Seçilen sayfayı görüntüler."""

        if not 0 <= page_index < self.stack.count():
            return

        self.stack.setCurrentIndex(page_index)

        for index, button in enumerate(
            self.navigation_buttons
        ):
            button.setChecked(index == page_index)

        page_names = {
            0: "Dashboard",
            1: "Wi-Fi Forensics",
        }

        selected_name = page_names.get(
            page_index,
            "CyberLab",
        )

        self.statusBar().showMessage(
            f"{selected_name} sayfası açıldı."
        )

    def _on_capture_selected(
        self,
        capture_file: Path,
    ) -> None:
        """Yakalama dosyası seçildiğinde durum çubuğunu günceller."""

        self.statusBar().showMessage(
           f"● Dosya seçildi: {capture_file.name}"
        )

        self.wifi_page.add_log(f"Yakalama dosyası seçildi: {capture_file.name}")

    def _on_analysis_requested(
        self,
        capture_file: Path,
    ) -> None:
        """Seçilen yakalama dosyasının analizini başlatır."""

        self.wifi_page.clear_log()

        self.analysis_started_at = perf_counter()

        self.dashboard_page.set_analysis_running()

        self.wifi_page.add_log(f"● Analiz başlatıldı: {capture_file.name}")

        if self.active_worker is not None:
            QMessageBox.information(
                self,
                "Analiz devam ediyor",
                "Mevcut analiz tamamlanmadan yeni analiz başlatılamaz.",
            )
            return

        worker = AnalysisWorker(capture_file)
        self.active_worker = worker

        worker.signals.progress.connect(
            self._on_analysis_progress
        )
        worker.signals.completed.connect(
            self._on_analysis_completed
        )
        worker.signals.failed.connect(
            self._on_analysis_failed
        )
        worker.signals.finished.connect(
            self._on_analysis_finished
        )

        self.wifi_page.browse_button.setEnabled(False)
        self.wifi_page.analyze_button.setEnabled(False)
        self.wifi_page.progress_bar.setValue(0)
        self.wifi_page.network_table.setRowCount(0)
        self.last_networks = []
        self.last_eapol_count = 0
        self.wifi_page.clear_network_details()

        self.statusBar().showMessage(
            f"Analiz başlatıldı: {capture_file.name}"
        )

        self.thread_pool.start(worker)


    def _on_analysis_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        """Analiz ilerlemesini Wi-Fi sayfasında gösterir."""
        self.wifi_page.add_log( f"● {message}")
        self.wifi_page.progress_bar.setValue(value)
        self.wifi_page.status_label.setText(message)
        self.statusBar().showMessage(message)

        self.wifi_page.status_label.setStyleSheet(
                "color: #FBBF24; font-weight: 600;"
            )


    def _on_analysis_completed(
        self,
        report: dict[str, Any],
    ) -> None:
        """Analiz sonuçlarını kartlara ve tabloya aktarır."""

        networks = report.get("networks", [])
        self.last_networks = networks
        self.last_eapol_count = int(
            report.get("eapol_packet_count", 0)
        )

        client_macs = {
            client.get("mac")
            for network in networks
            for client in network.get("clients", [])
            if client.get("mac")
        }

        self.wifi_page.summary_values["packets"].setText(
            str(report.get("total_packets", 0))
        )
        self.wifi_page.summary_values["networks"].setText(
            str(report.get("network_count", len(networks)))
        )
        self.wifi_page.summary_values["clients"].setText(
            str(len(client_macs))
        )
        self.wifi_page.summary_values["eapol"].setText(
            str(report.get("eapol_packet_count", 0))
        )

        self.wifi_page.network_table.setRowCount(len(networks))

        for row_index, network in enumerate(networks):
            ssids = network.get("ssids", [])
            signal = network.get("average_signal_dbm")
            channel = network.get("channel")
            clients = network.get("clients", [])

            values = [
                ", ".join(ssids) if ssids else "<Gizli SSID>",
                str(network.get("bssid", "")),
                str(channel if channel is not None else "—"),
                f"{signal} dBm" if signal is not None else "—",
                str(len(clients)),
            ]

            for column_index, value in enumerate(values):
                self.wifi_page.network_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

        self.wifi_page.status_label.setStyleSheet(
            "color: #34D399; font-weight: 600;"
        )
        self.wifi_page.status_label.setText(
            "Analiz başarıyla tamamlandı."
        )
        self.statusBar().showMessage("Analiz tamamlandı.")

        self.wifi_page.add_log(
            "✓ Analiz başarıyla tamamlandı."
        )

        self.wifi_page.add_log(
            f"✓ {report.get('total_packets', 0)} paket işlendi."
        )

        self.wifi_page.add_log(
            f"✓ {len(networks)} ağ tespit edildi."
        )

        if self.analysis_started_at is not None:
                elapsed = perf_counter() - self.analysis_started_at

                self.wifi_page.add_log(
                    f"✓ Analiz süresi: {elapsed:.2f} saniye"
                )

                self.dashboard_page.update_analysis_summary(
            report.get("capture_name", "Bilinmeyen dosya"),
            report.get("total_packets", 0),
            len(networks),
        )


    def _on_analysis_failed(
        self,
        error_message: str,
    ) -> None:
        """Analiz sırasında oluşan hatayı gösterir."""

        self.wifi_page.status_label.setStyleSheet(
            "color: #F87171; font-weight: 600;"
        )
        self.wifi_page.status_label.setText(
            "Analiz sırasında hata oluştu."
        )
        self.wifi_page.add_log(
            "✕ Analiz sırasında hata oluştu."
        )
        QMessageBox.critical(
            self,
            "Analiz hatası",
            error_message,
        )

        if self.analysis_started_at is not None:
            elapsed = perf_counter() - self.analysis_started_at

            self.wifi_page.add_log(
                f"✕ Analiz {elapsed:.2f} saniye sonra başarısız oldu."
            )
        self.dashboard_page.set_analysis_failed()

    def _on_analysis_finished(self) -> None:
        """Analiz kontrollerini yeniden etkinleştirir."""

        self.active_worker = None
        self.wifi_page.browse_button.setEnabled(True)
        self.wifi_page.analyze_button.setEnabled(
            self.wifi_page.selected_capture is not None
        )
        self.analysis_started_at = None

    def _on_network_selected(self) -> None:
        """Tabloda seçilen ağın ayrıntılarını gösterir."""

        selected_row = (
            self.wifi_page.network_table.currentRow()
        )

        if not 0 <= selected_row < len(self.last_networks):
            self.wifi_page.clear_network_details()
            return

        network = self.last_networks[selected_row]

        self.wifi_page.show_network_details(
            network,
            self.last_eapol_count,
        )