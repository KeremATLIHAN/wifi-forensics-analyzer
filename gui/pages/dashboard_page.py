"""CyberLab Desktop Suite dashboard sayfası."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class DashboardPage(QWidget):
    """CyberLab ana karşılama ve durum ekranı."""

    def __init__(self) -> None:
        super().__init__()

        self.metric_values: dict[str, QLabel] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Dashboard arayüzünü oluşturur."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        description = QLabel(
            "CyberLab sistem durumunu ve son analiz özetini "
            "tek ekrandan görüntüleyin."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self._create_metrics_panel())
        layout.addWidget(self._create_system_card())
        layout.addStretch(1)

    def _create_metrics_panel(self) -> QWidget:
        """Dashboard özet kartlarını oluşturur."""

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        metrics = (
            ("status", "●", "Sistem Durumu", "Hazır"),
            ("capture", "◫", "Son Dosya", "Henüz analiz yok"),
            ("packets", "◆", "Son Paket Sayısı", "—"),
            ("networks", "◉", "Son Ağ Sayısı", "—"),
        )

        for index, (key, icon, title, value) in enumerate(metrics):
            card, value_label = self._create_metric_card(
                icon,
                title,
                value,
            )

            self.metric_values[key] = value_label

            row = index // 2
            column = index % 2

            grid.addWidget(card, row, column)

        return container

    @staticmethod
    def _create_metric_card(
        icon: str,
        title: str,
        value: str,
    ) -> tuple[QFrame, QLabel]:
        """Tek bir dashboard kartı oluşturur."""

        card = QFrame()
        card.setObjectName("summaryCard")
        card.setMinimumHeight(120)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        heading = QLabel(f"{icon}  {title}")
        heading.setObjectName("summaryTitle")

        value_label = QLabel(value)
        value_label.setObjectName("summaryValue")
        value_label.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(value_label)
        layout.addStretch(1)

        return card, value_label

    def _create_system_card(self) -> QFrame:
        """CyberLab çalışma durumu kartını oluşturur."""

        card = QFrame()
        card.setObjectName("contentCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        title = QLabel("CyberLab Desktop Suite")
        title.setObjectName("sectionTitle")

        text = QLabel(
            "Wi-Fi Forensics modülü aktif.\n"
            "TShark tabanlı yakalama analizi kullanılabilir.\n"
            "Yeni güvenlik modülleri için mimari genişletilebilir yapıdadır."
        )
        text.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(text)

        return card

    def update_analysis_summary(
        self,
        capture_name: str,
        packet_count: int,
        network_count: int,
    ) -> None:
        """Son başarılı analiz bilgisini dashboard'a aktarır."""

        self.metric_values["status"].setText("Hazır")
        self.metric_values["capture"].setText(capture_name)
        self.metric_values["packets"].setText(str(packet_count))
        self.metric_values["networks"].setText(str(network_count))

    def set_analysis_running(self) -> None:
        """Analiz sırasında dashboard durumunu günceller."""

        self.metric_values["status"].setText("Analiz çalışıyor...")

    def set_analysis_failed(self) -> None:
        """Analiz başarısız olduğunda durum bilgisini günceller."""

        self.metric_values["status"].setText("Analiz hatası")