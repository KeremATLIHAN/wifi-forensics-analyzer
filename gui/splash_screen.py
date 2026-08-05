"""CyberLab Desktop Suite açılış ekranı."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    """Uygulama başlatılırken gösterilen özel açılış penceresi."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFixedSize(620, 360)

        self.status_label: QLabel
        self.progress_bar: QProgressBar

        self._build_ui()

    def _build_ui(self) -> None:
        """Splash ekranının görsel bileşenlerini oluşturur."""

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("splashContainer")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(48, 42, 48, 36)
        layout.setSpacing(14)

        brand_label = QLabel("CYBERLAB")
        brand_label.setObjectName("splashBrand")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_font = QFont()
        brand_font.setPointSize(30)
        brand_font.setBold(True)
        brand_label.setFont(brand_font)

        product_label = QLabel("Desktop Security Suite")
        product_label.setObjectName("splashProduct")
        product_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        slogan_label = QLabel("Learn. Analyze. Improve.")
        slogan_label.setObjectName("splashSlogan")
        slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel("v0.2.0-dev")
        version_label.setObjectName("splashVersion")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Uygulama hazırlanıyor...")
        self.status_label.setObjectName("splashStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("splashProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        layout.addStretch()
        layout.addWidget(brand_label)
        layout.addWidget(product_label)
        layout.addWidget(slogan_label)
        layout.addSpacing(18)
        layout.addWidget(version_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        outer_layout.addWidget(container)

    def update_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        """İlerleme çubuğunu ve durum mesajını günceller."""

        normalized_value = max(0, min(value, 100))

        self.progress_bar.setValue(normalized_value)
        self.status_label.setText(message)
