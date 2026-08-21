from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class NetworkInterface:
    """TShark tarafından görülen bir ağ arayüzü."""

    index: int
    name: str
    description: str = ""

    @property
    def display_name(self) -> str:
        if self.description:
            return f"{self.description} ({self.name})"
        return self.name


class LiveTrafficMonitor:
    """
    CyberLab canlı ağ trafiği izleme motoru.

    Sprint 1'in ilk aşamasında:
    - TShark erişimini kontrol eder.
    - Capture edilebilir interface'leri listeler.

    Canlı packet capture sonraki adımda eklenecek.
    """

    def __init__(self, tshark_path: str = "tshark") -> None:
        self.tshark_path = tshark_path
        self.process: Optional[subprocess.Popen] = None

    def check_tshark(self) -> tuple[bool, str]:
        """TShark'ın sistemde erişilebilir olup olmadığını kontrol eder."""

        try:
            result = subprocess.run(
                [self.tshark_path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )

            if result.returncode != 0:
                message = (
                    result.stderr.strip()
                    or "TShark çalıştırılamadı."
                )
                return False, message

            first_line = result.stdout.splitlines()[0]
            return True, first_line

        except FileNotFoundError:
            return (
                False,
                "TShark bulunamadı. Wireshark/TShark kurulumunu kontrol edin.",
            )

        except subprocess.TimeoutExpired:
            return False, "TShark kontrolü zaman aşımına uğradı."

        except Exception as exc:
            return False, f"TShark kontrol hatası: {exc}"

    def list_interfaces(self) -> list[NetworkInterface]:
        """TShark'ın capture edebildiği ağ arayüzlerini döndürür."""

        result = subprocess.run(
            [self.tshark_path, "-D"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "Ağ arayüzleri alınamadı."
            )

        interfaces: list[NetworkInterface] = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            try:
                index_text, remainder = line.split(".", 1)
                index = int(index_text.strip())
                remainder = remainder.strip()
            except (ValueError, TypeError):
                continue

            name = remainder
            description = ""

            # Windows TShark çıktısı genellikle:
            # 1. \Device\NPF_{GUID} (Wi-Fi)
            if remainder.endswith(")") and " (" in remainder:
                name_part, description_part = remainder.rsplit(" (", 1)
                name = name_part.strip()
                description = description_part[:-1].strip()

            interfaces.append(
                NetworkInterface(
                    index=index,
                    name=name,
                    description=description,
                )
            )

        return interfaces