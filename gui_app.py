#!/usr/bin/env python3

"""CyberLab Desktop Suite masaüstü uygulaması."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.splash_screen import SplashScreen
from gui.styles import DARK_STYLESHEET
from pathlib import Path
from PySide6.QtGui import QIcon

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


class ApplicationLauncher:
    """Splash ekranından ana pencereye geçişi yönetir."""

    if sys.platform == "win32":
        app_id = "CyberLab.DesktopSuite.v0.2"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_id
        )

    def __init__(self, app: QApplication) -> None:
        self.app = app

        base_dir = Path(__file__).resolve().parent

        icon_path = (
            base_dir
            / "resources"
            / "icons"
            / "cyberlab.ico"
        )

        if icon_path.exists():
            icon = QIcon(str(icon_path))

            self.app.setWindowIcon(icon)

        base_dir = Path(__file__).resolve().parent

        icon_path = (
            base_dir
            / "resources"
            / "icons"
            / "cyberlab.ico"
        )

        if icon_path.exists():
            self.app.setWindowIcon(
                QIcon(str(icon_path))
            )

        self.splash = SplashScreen()
        self.main_window: MainWindow | None = None

        self.current_step = 0

        self.loading_steps: list[tuple[int, str]] = [
            (10, "Tema sistemi yükleniyor..."),
            (30, "Uygulama ayarları hazırlanıyor..."),
            (55, "Modül kayıt sistemi başlatılıyor..."),
            (75, "Wi-Fi Forensics modülü yükleniyor..."),
            (90, "Ana pencere hazırlanıyor..."),
            (100, "CyberLab hazır."),
        ]

        self.timer = QTimer()
        self.timer.setInterval(350)
        self.timer.timeout.connect(self._advance_loading)

   

    def start(self) -> None:
        """Splash ekranını gösterip yükleme akışını başlatır."""

        self.splash.show()
        self._center_splash()
        self.timer.start()

    def _center_splash(self) -> None:
        """Splash ekranını aktif ekranın merkezine taşır."""

        screen = self.app.primaryScreen()

        if screen is None:
            return

        screen_geometry = screen.availableGeometry()
        splash_geometry = self.splash.frameGeometry()

        splash_geometry.moveCenter(screen_geometry.center())
        self.splash.move(splash_geometry.topLeft())

    def _advance_loading(self) -> None:
        """Yükleme adımlarını sırayla uygular."""

        if self.current_step >= len(self.loading_steps):
            self.timer.stop()
            self._open_main_window()
            return

        progress, message = self.loading_steps[self.current_step]

        self.splash.update_progress(
            progress,
            message,
        )

        self.current_step += 1

    def _open_main_window(self) -> None:
        """Splash ekranını kapatıp ana pencereyi açar."""

        self.main_window = MainWindow()
        self.main_window.setWindowIcon(QIcon("resources/icons/cyberlab.ico"))
        self.main_window.show()

        self.splash.close()


def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName("CyberLab Desktop Suite")
    app.setOrganizationName("KeremATLIHAN")
    app.setStyleSheet(DARK_STYLESHEET)

    launcher = ApplicationLauncher(app)
    launcher.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
