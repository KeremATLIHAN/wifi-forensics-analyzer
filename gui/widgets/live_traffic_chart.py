from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class LiveTrafficChart(QWidget):
    """Son N trafik örneğini gösteren hafif canlı çizgi grafik."""

    def __init__(
        self,
        max_points: int = 60,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.max_points = max_points
        self.values: deque[float] = deque(
            maxlen=max_points
        )
        self.elapsed_values: deque[int] = deque(
            maxlen=max_points
        )
        self.current_elapsed = 0

        self.setMinimumHeight(220)

    def add_value(
        self,
        value: float,
        elapsed_seconds: int,
    ) -> None:
        """Yeni trafik örneğini oturum zamanı ile birlikte ekler."""
        self.values.append(
            max(0.0, float(value))
        )
        self.elapsed_values.append(
            max(0, int(elapsed_seconds))
        )
        self.current_elapsed = max(
            0,
            int(elapsed_seconds),
        )
        self.update()

    def clear(self) -> None:
        self.values.clear()
        self.elapsed_values.clear()
        self.current_elapsed = 0
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        rect = self.rect()

        background = QColor("#0F172A")
        grid_color = QColor("#243247")
        text_color = QColor("#94A3B8")
        line_color = QColor("#2DD4BF")

        painter.fillRect(
            rect,
            background,
        )

        margin_left = 64
        margin_right = 20
        margin_top = 26
        margin_bottom = 38

        chart_rect = QRectF(
            margin_left,
            margin_top,
            max(
                1,
                rect.width()
                - margin_left
                - margin_right,
            ),
            max(
                1,
                rect.height()
                - margin_top
                - margin_bottom,
            ),
        )

        # Grid
        grid_pen = QPen(grid_color)
        grid_pen.setWidth(1)

        painter.setPen(grid_pen)

        horizontal_lines = 4

        for index in range(
            horizontal_lines + 1
        ):
            y = (
                chart_rect.top()
                + chart_rect.height()
                * index
                / horizontal_lines
            )

            painter.drawLine(
                QPointF(
                    chart_rect.left(),
                    y,
                ),
                QPointF(
                    chart_rect.right(),
                    y,
                ),
            )

        if not self.values:
            painter.setPen(text_color)
            painter.drawText(
                chart_rect,
                Qt.AlignmentFlag.AlignCenter,
                "Canlı trafik verisi bekleniyor...",
            )
            return

        values = list(self.values)

        max_value = max(values)

        # Grafik tamamen düz görünmesin.
        scale_max = max(
            1.0,
            max_value * 1.15,
        )

        painter.setPen(text_color)

        for index in range(
            horizontal_lines + 1
        ):
            value = (
                scale_max
                * (
                    horizontal_lines - index
                )
                / horizontal_lines
            )

            y = (
                chart_rect.top()
                + chart_rect.height()
                * index
                / horizontal_lines
            )

            painter.drawText(
                QRectF(
                    6,
                    y - 9,
                    margin_left - 18,
                    18,
                ),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                f"{value:.1f}",
            )

        painter.drawText(
            QRectF(
                6,
                4,
                margin_left - 14,
                18,
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            "Mbps",
        )

        times = list(self.elapsed_values)
        window_end = max(
            self.current_elapsed,
            1,
        )
        window_start = max(
            0,
            window_end - self.max_points,
        )
        window_duration = max(
            1,
            window_end - window_start,
        )

        x_positions = []

        for sample_time in times:
            relative_position = (
                sample_time - window_start
            ) / window_duration
            relative_position = max(
                0.0,
                min(
                    1.0,
                    relative_position,
                ),
            )
            x = (
                chart_rect.left()
                + chart_rect.width()
                * relative_position
            )
            x_positions.append(x)

        path = QPainterPath()

        for index, value in enumerate(values):
            x = x_positions[index]

            normalized = (
                value / scale_max
            )

            y = (
                chart_rect.bottom()
                - normalized
                * chart_rect.height()
            )

            point = QPointF(x, y)

            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)

        traffic_pen = QPen(line_color)
        traffic_pen.setWidth(2)

        painter.setPen(traffic_pen)
        painter.drawPath(path)

        def format_elapsed(seconds: int) -> str:
            seconds = max(0, seconds)
            minutes, remaining_seconds = divmod(
                seconds,
                60,
            )
            return (
                f"{minutes:02d}:"
                f"{remaining_seconds:02d}"
            )

        painter.setPen(text_color)
        tick_count = 4

        for index in range(tick_count + 1):
            ratio = index / tick_count
            tick_time = int(
                window_start
                + (
                    window_end - window_start
                )
                * ratio
            )
            x = (
                chart_rect.left()
                + chart_rect.width() * ratio
            )

            painter.drawText(
                QRectF(
                    x - 22,
                    chart_rect.bottom() + 8,
                    44,
                    18,
                ),
                Qt.AlignmentFlag.AlignCenter,
                format_elapsed(tick_time),
            )