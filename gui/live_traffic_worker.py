from __future__ import annotations

import subprocess
import time

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class LiveTrafficSignals(QObject):
    """LiveTrafficWorker sinyalleri."""

    sample = Signal(dict)
    status = Signal(str)
    error = Signal(str)
    finished = Signal()


class LiveTrafficWorker(QRunnable):
    """
    Seçilen TShark arayüzünden canlı trafik metrikleri üretir.

    Her yaklaşık 1 saniyede GUI'ye:
    - elapsed_seconds
    - total_packets
    - packets_per_second
    - current_mbps
    - total_bytes
    - peak_mbps

    değerlerini gönderir.
    """

    def __init__(
        self,
        interface_index: int,
        duration_seconds: int,
        tshark_path: str = "tshark",
    ) -> None:
        super().__init__()

        self.interface_index = interface_index
        self.duration_seconds = duration_seconds
        self.tshark_path = tshark_path

        self.signals = LiveTrafficSignals()

        self._stop_requested = False
        self.process: subprocess.Popen | None = None

    def stop(self) -> None:
        """Worker'a kontrollü durdurma isteği gönderir."""

        self._stop_requested = True

        if self.process is not None:
            try:
                self.process.terminate()
            except Exception:
                pass

    @Slot()
    def run(self) -> None:
        """Canlı TShark capture işlemini çalıştırır."""

        command = [
            self.tshark_path,
            "-l",
            "-n",
            "-i",
            str(self.interface_index),
            "-T",
            "fields",
            "-e",
            "frame.time_epoch",
            "-e",
            "frame.len",
            "-E",
            "separator=\t",
        ]

        try:
            self.signals.status.emit(
                "TShark canlı izleme başlatılıyor..."
            )

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            if self.process.stdout is None:
                raise RuntimeError(
                    "TShark stdout akışı oluşturulamadı."
                )

            start_time = time.monotonic()
            last_sample_time = start_time

            total_packets = 0
            total_bytes = 0

            interval_packets = 0
            interval_bytes = 0

            peak_mbps = 0.0

            self.signals.status.emit(
                "Canlı trafik izleniyor."
            )

            for line in self.process.stdout:

                if self._stop_requested:
                    break

                now = time.monotonic()
                elapsed = now - start_time

                if elapsed >= self.duration_seconds:
                    break

                line = line.strip()

                if not line:
                    continue

                parts = line.split("\t")

                if len(parts) < 2:
                    continue

                try:
                    frame_length = int(parts[1])
                except (ValueError, TypeError):
                    continue

                total_packets += 1
                total_bytes += frame_length

                interval_packets += 1
                interval_bytes += frame_length

                interval_elapsed = (
                    now - last_sample_time
                )

                if interval_elapsed >= 1.0:

                    packets_per_second = (
                        interval_packets
                        / interval_elapsed
                    )

                    current_mbps = (
                        interval_bytes
                        * 8
                        / interval_elapsed
                        / 1_000_000
                    )

                    peak_mbps = max(
                        peak_mbps,
                        current_mbps,
                    )

                    self.signals.sample.emit(
                        {
                            "elapsed_seconds": int(
                                elapsed
                            ),
                            "duration_seconds": (
                                self.duration_seconds
                            ),
                            "total_packets": (
                                total_packets
                            ),
                            "packets_per_second": (
                                packets_per_second
                            ),
                            "current_mbps": (
                                current_mbps
                            ),
                            "total_bytes": (
                                total_bytes
                            ),
                            "peak_mbps": (
                                peak_mbps
                            ),
                        }
                    )

                    interval_packets = 0
                    interval_bytes = 0
                    last_sample_time = now

            self.signals.status.emit(
                "Canlı trafik izleme tamamlandı."
            )

        except Exception as exc:
            self.signals.error.emit(
                f"Canlı trafik izleme hatası: {exc}"
            )

        finally:
            if self.process is not None:
                try:
                    if self.process.poll() is None:
                        self.process.terminate()

                        try:
                            self.process.wait(
                                timeout=2
                            )
                        except subprocess.TimeoutExpired:
                            self.process.kill()

                except Exception:
                    pass

                self.process = None

            self.signals.finished.emit()

