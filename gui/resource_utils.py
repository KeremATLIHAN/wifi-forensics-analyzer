"""CyberLab resource dosyalarının yollarını yönetir."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    """Development ve PyInstaller ortamında resource yolunu döndürür."""

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent.parent

    return base_dir.joinpath(*parts)