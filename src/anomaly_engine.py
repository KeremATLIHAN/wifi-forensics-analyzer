from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass
class PointAnomalyResult:
    is_anomaly: bool
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    severity: str
    reason: str


@dataclass
class ContextualAnomalyResult:
    is_anomaly: bool
    value: float
    local_mean: float
    local_std: float
    z_score: float
    severity: str
    reason: str


@dataclass
class CollectiveAnomalyResult:
    is_anomaly: bool
    value: float
    short_mean: float
    long_mean: float
    difference: float
    consecutive_count: int
    severity: str
    reason: str


class PointAnomalyDetector:
    """
    Canlı trafik için basit Z-score tabanlı nokta anomali dedektörü.

    Mantık:
    - Son N örnek baseline olarak tutulur.
    - İlk warmup_samples boyunca alarm üretilmez.
    - Yeni örnek baseline ortalama/std değerine göre değerlendirilir.
    """

    def __init__(
        self,
        window_size: int = 60,
        warmup_samples: int = 15,
        z_threshold: float = 3.0,
        min_std: float = 0.05,
    ) -> None:
        self.window_size = window_size
        self.warmup_samples = warmup_samples
        self.z_threshold = z_threshold
        self.min_std = min_std

        self.values: deque[float] = deque(
            maxlen=window_size
        )

    def reset(self) -> None:
        self.values.clear()

    def add_sample(
        self,
        value: float,
    ) -> PointAnomalyResult:
        value = max(0.0, float(value))

        # Warm-up aşaması
        if len(self.values) < self.warmup_samples:
            self.values.append(value)

            return PointAnomalyResult(
                is_anomaly=False,
                value=value,
                baseline_mean=mean(self.values),
                baseline_std=0.0,
                z_score=0.0,
                severity="info",
                reason="Baseline hazırlanıyor.",
            )

        baseline_values = list(self.values)

        baseline_mean = mean(
            baseline_values
        )

        baseline_std = pstdev(
            baseline_values
        )

        safe_std = max(
            baseline_std,
            self.min_std,
        )

        z_score = (
            value - baseline_mean
        ) / safe_std

        is_anomaly = (
            abs(z_score)
            >= self.z_threshold
        )

        severity = "warning"

        if abs(z_score) >= 5.0:
            severity = "critical"
        elif abs(z_score) >= 4.0:
            severity = "warning"
        else:
            severity = "info"

        reason = (
            "Ani trafik sapması tespit edildi."
            if is_anomaly
            else "Trafik baseline aralığında."
        )

        # Yeni örneği baseline'a ekle.
        # Şimdilik anomaly örneklerini de dahil ediyoruz.
        self.values.append(value)

        return PointAnomalyResult(
            is_anomaly=is_anomaly,
            value=value,
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            z_score=z_score,
            severity=severity,
            reason=reason,
        )


class ContextualAnomalyDetector:
    """Yakın geçmiş bağlamına göre trafik sapmalarını tespit eder."""

    def __init__(
        self,
        window_size: int = 90,
        warmup_samples: int = 30,
        z_threshold: float = 2.5,
        min_std: float = 0.05,
    ) -> None:
        self.window_size = window_size
        self.warmup_samples = warmup_samples
        self.z_threshold = z_threshold
        self.min_std = min_std
        self.values: deque[float] = deque(maxlen=window_size)

    def reset(self) -> None:
        self.values.clear()

    def add_sample(
        self,
        value: float,
    ) -> ContextualAnomalyResult:
        value = max(0.0, float(value))

        if len(self.values) < self.warmup_samples:
            self.values.append(value)
            return ContextualAnomalyResult(
                is_anomaly=False,
                value=value,
                local_mean=mean(self.values),
                local_std=0.0,
                z_score=0.0,
                severity="info",
                reason="Bağlamsal baseline hazırlanıyor.",
            )

        baseline_values = list(self.values)
        local_mean = mean(baseline_values)
        local_std = pstdev(baseline_values)
        safe_std = max(local_std, self.min_std)
        z_score = (value - local_mean) / safe_std
        is_anomaly = abs(z_score) >= self.z_threshold
        severity = "warning" if abs(z_score) >= 4.0 else "info"
        reason = (
            "Mevcut trafik seviyesi yakın geçmiş bağlamına "
            "göre beklenmeyen sapma gösterdi."
            if is_anomaly
            else "Trafik yerel bağlam içinde."
        )

        self.values.append(value)

        return ContextualAnomalyResult(
            is_anomaly=is_anomaly,
            value=value,
            local_mean=local_mean,
            local_std=local_std,
            z_score=z_score,
            severity=severity,
            reason=reason,
        )


class CollectiveAnomalyDetector:
    """Uzun süreli trafik sapmalarını kısa ve uzun pencerelerle izler."""

    def __init__(
        self,
        short_window: int = 15,
        long_window: int = 60,
        min_difference_mbps: float = 1.0,
        min_ratio: float = 1.25,
        min_consecutive: int = 5,
    ) -> None:
        self.short_window = short_window
        self.long_window = long_window
        self.min_difference_mbps = min_difference_mbps
        self.min_ratio = min_ratio
        self.min_consecutive = min_consecutive
        self.consecutive_count = 0
        self.values: deque[float] = deque(maxlen=long_window)

    def reset(self) -> None:
        self.values.clear()
        self.consecutive_count = 0

    def add_sample(
        self,
        value: float,
    ) -> CollectiveAnomalyResult:
        value = max(0.0, float(value))
        self.values.append(value)

        if len(self.values) < self.long_window:
            return CollectiveAnomalyResult(
                is_anomaly=False,
                value=value,
                short_mean=0.0,
                long_mean=0.0,
                difference=0.0,
                consecutive_count=0,
                severity="info",
                reason="Collective baseline hazırlanıyor.",
            )

        values = list(self.values)
        short_values = values[-self.short_window:]
        short_mean = mean(short_values)
        long_mean = mean(values)
        difference = short_mean - long_mean
        ratio = (
            short_mean / long_mean
            if long_mean > 0
            else 0.0
        )

        sustained_deviation = (
            difference >= self.min_difference_mbps
            and ratio >= self.min_ratio
        )

        if sustained_deviation:
            self.consecutive_count += 1
        else:
            self.consecutive_count = 0

        is_anomaly = (
            self.consecutive_count >= self.min_consecutive
        )

        if is_anomaly:
            severity = (
                "warning"
                if ratio < 2.5
                else "critical"
            )
            reason = (
                "Trafik seviyesi uzun süre baseline "
                "üzerinde seyrediyor."
            )
        else:
            severity = "info"
            reason = (
                "Sürekli anormal trafik paterni "
                "henüz oluşmadı."
            )

        return CollectiveAnomalyResult(
            is_anomaly=is_anomaly,
            value=value,
            short_mean=short_mean,
            long_mean=long_mean,
            difference=difference,
            consecutive_count=self.consecutive_count,
            severity=severity,
            reason=reason,
        )