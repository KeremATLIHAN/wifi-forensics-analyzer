"""Wi-Fi analizini arka planda çalıştıran worker."""

from __future__ import annotations

import os
import shutil
import traceback
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from src.analyzer import analyze_packets
from src.tshark_parser import (
    get_available_fields,
    parse_capture,
    resolve_fields,
)


class WorkerSignals(QObject):
    """Worker ile GUI arasındaki sinyaller."""

    progress = Signal(int, str)
    completed = Signal(dict)
    failed = Signal(str)
    finished = Signal()


class AnalysisWorker(QRunnable):
    """CAP, PCAP veya PCAPNG dosyasını arka planda analiz eder."""

    def __init__(self, capture_file: Path) -> None:
        super().__init__()
        self.capture_file = capture_file
        self.signals = WorkerSignals()

    @staticmethod
    def _ensure_tshark_path() -> None:
        """Windows'taki Wireshark klasörünü geçici olarak PATH'e ekler."""

        if shutil.which("tshark"):
            return

        tshark_path = Path(
            r"C:\Program Files\Wireshark\tshark.exe"
        )

        if not tshark_path.exists():
            raise FileNotFoundError(
                "TShark bulunamadı. "
                r"Beklenen konum: C:\Program Files\Wireshark\tshark.exe"
            )

        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = (
            f"{tshark_path.parent}{os.pathsep}{current_path}"
        )

    @Slot()
    def run(self) -> None:
        """Analiz işlemini gerçekleştirir."""

        try:
            self._ensure_tshark_path()

            self.signals.progress.emit(
                10,
                "TShark kontrol ediliyor...",
            )

            available_fields = get_available_fields()

            self.signals.progress.emit(
                25,
                "Paket alanları eşleştiriliyor...",
            )

            resolved_fields = resolve_fields(
                available_fields
            )

            self.signals.progress.emit(
                40,
                "Yakalama dosyası okunuyor...",
            )

            packets = parse_capture(
                self.capture_file,
                resolved_fields,
            )

            self.signals.progress.emit(
                65,
                "Paketler analiz ediliyor...",
            )

            report: dict[str, Any] = analyze_packets(
                packets
            )

            report["capture_file"] = str(
                self.capture_file
            )
            report["capture_name"] = (
                self.capture_file.name
            )

            self.signals.progress.emit(
                100,
                "Analiz tamamlandı.",
            )

            self.signals.completed.emit(report)

        except Exception as error:
            self.signals.failed.emit(
                f"{type(error).__name__}: {error}\n\n"
                f"{traceback.format_exc()}"
            )

        finally:
            self.signals.finished.emit()