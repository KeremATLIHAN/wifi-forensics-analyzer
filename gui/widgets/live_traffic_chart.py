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

        self.setMinimumHeight(220)

    def add_value(self, value: float) -> None:
        self.values.append(
            max(0.0, float(value))
        )
        self.update()

    def clear(self) -> None:
        self.values.clear()
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

        margin_left = 52
        margin_right = 18
        margin_top = 18
        margin_bottom = 34

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
                    4,
                    y - 8,
                    margin_left - 10,
                    16,
                ),
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                f"{value:.1f}",
            )

        painter.drawText(
            QRectF(
                4,
                2,
                margin_left - 8,
                16,
            ),
            Qt.AlignmentFlag.AlignRight,
            "Mbps",
        )

        if len(values) == 1:
            x_positions = [
                chart_rect.right()
            ]
        else:
            step_x = (
                chart_rect.width()
                / (
                    self.max_points - 1
                )
            )

            missing_points = (
                self.max_points
                - len(values)
            )

            x_positions = [
                chart_rect.left()
                + step_x
                * (
                    missing_points + index
                )
                for index
                in range(len(values))
            ]

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