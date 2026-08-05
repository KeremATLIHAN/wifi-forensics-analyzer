"""CyberLab Desktop Suite ana pencere yapısı."""

from __future__ import annotations

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


class MainWindow(QMainWindow):
    """CyberLab Desktop Suite ana uygulama penceresi."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CyberLab Desktop Suite")
        self.resize(1280, 780)
        self.setMinimumSize(1000, 650)

        self.navigation_buttons: list[QPushButton] = []
        self.stack = QStackedWidget()

        central_widget = QWidget()
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._create_sidebar()
        dashboard_page = self._create_dashboard_page()
        wifi_page = self._create_wifi_page()

        self.stack.addWidget(dashboard_page)
        self.stack.addWidget(wifi_page)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(central_widget)
        self.statusBar().showMessage("CyberLab Desktop Suite hazır.")

        self._select_page(0)

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

        dashboard_button = self._create_navigation_button(
            "Dashboard",
            0,
        )
        wifi_button = self._create_navigation_button(
            "Wi-Fi Forensics",
            1,
        )

        layout.addWidget(dashboard_button)
        layout.addWidget(wifi_button)
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
        """Sol menü için navigasyon düğmesi oluşturur."""

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

    def _create_dashboard_page(self) -> QWidget:
        """İlk dashboard sayfasını oluşturur."""

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        description = QLabel(
            "CyberLab modüllerini, laboratuvar çalışmalarını "
            "ve analiz sonuçlarını tek merkezden yönetin."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        welcome_card = QFrame()
        welcome_card.setObjectName("contentCard")

        card_layout = QVBoxLayout(welcome_card)
        card_layout.setContentsMargins(22, 22, 22, 22)

        card_title = QLabel("CyberLab Desktop Suite")
        card_title.setObjectName("sectionTitle")

        card_text = QLabel(
            "İlk masaüstü uygulama kabuğu başarıyla çalışıyor.\n\n"
            "Sonraki aşamada Wi-Fi analiz motoru arka plan worker "
            "üzerinden arayüze bağlanacaktır."
        )
        card_text.setWordWrap(True)

        card_layout.addWidget(card_title)
        card_layout.addWidget(card_text)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(welcome_card)
        layout.addStretch(1)

        return page

    def _create_wifi_page(self) -> QWidget:
        """Wi-Fi Forensics modülünün geçici sayfasını oluşturur."""

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Wi-Fi Forensics")
        title.setObjectName("pageTitle")

        description = QLabel(
            "CAP, PCAP ve PCAPNG dosyalarını analiz eden "
            "CyberLab modülü."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        module_card = QFrame()
        module_card.setObjectName("contentCard")

        card_layout = QVBoxLayout(module_card)
        card_layout.setContentsMargins(22, 22, 22, 22)

        status_title = QLabel("Modül Durumu")
        status_title.setObjectName("sectionTitle")

        status_text = QLabel(
            "Arayüz iskeleti hazır.\n"
            "Analiz motoru sonraki görevde bağlanacak."
        )
        status_text.setWordWrap(True)

        card_layout.addWidget(status_title)
        card_layout.addWidget(status_text)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(module_card)
        layout.addStretch(1)

        return page

    def _select_page(self, page_index: int) -> None:
        """Seçilen sayfayı görüntüler."""

        if page_index < 0 or page_index >= self.stack.count():
            return

        self.stack.setCurrentIndex(page_index)

        for index, button in enumerate(self.navigation_buttons):
            button.setChecked(index == page_index)

        page_names = {
            0: "Dashboard",
            1: "Wi-Fi Forensics",
        }

        selected_name = page_names.get(page_index, "CyberLab")
        self.statusBar().showMessage(
            f"{selected_name} sayfası açıldı."
        )
