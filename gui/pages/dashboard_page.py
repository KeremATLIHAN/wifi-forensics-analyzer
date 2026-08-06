"""CyberLab Desktop Suite dashboard sayfası."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class DashboardPage(QWidget):
    """CyberLab ana karşılama ve genel durum sayfası."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        """Dashboard bileşenlerini oluşturur."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Siber güvenlik laboratuvar çalışmalarını, analiz "
            "modüllerini ve raporları tek merkezden yönetin."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        welcome_card = QFrame()
        welcome_card.setObjectName("contentCard")

        card_layout = QVBoxLayout(welcome_card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(10)

        card_title = QLabel("CyberLab Desktop Suite")
        card_title.setObjectName("sectionTitle")

        card_text = QLabel(
            "CyberLab, siber güvenlik eğitimi boyunca öğrenilen "
            "konuların bağımsız analiz modüllerine dönüştürüldüğü "
            "modüler bir masaüstü çalışma platformudur.\n\n"
            "İlk aktif modül: Wi-Fi Forensics."
        )
        card_text.setWordWrap(True)

        card_layout.addWidget(card_title)
        card_layout.addWidget(card_text)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(welcome_card)
        layout.addStretch(1)