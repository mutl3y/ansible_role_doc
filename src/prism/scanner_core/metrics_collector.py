"""Metrics collector for performance and error tracking."""

from __future__ import annotations

import time
from typing import Any, Dict


class MetricsCollector:
    """Collects metrics for scans, performance, and errors."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.alert_thresholds = self.config.get("alert_thresholds", {})
        self._scan_count = 0
        self._scan_duration_total = 0.0
        self._error_count = 0
        self._errors: Dict[str, int] = {}
        self._alerts: list[str] = []
        self._scan_start_time: float | None = None

    def start_scan(self) -> None:
        """Start timing a scan."""
        if self.enabled:
            self._scan_start_time = time.time()

    def end_scan(self) -> None:
        """End timing a scan and record metrics."""
        if self.enabled and self._scan_start_time is not None:
            duration = time.time() - self._scan_start_time
            self._scan_count += 1
            self._scan_duration_total += duration
            max_duration = self.alert_thresholds.get("max_scan_duration")
            if max_duration and duration > max_duration:
                self._alerts.append(
                    f"Scan duration {duration:.3f}s exceeded threshold {max_duration}s"
                )
            self._scan_start_time = None

    def record_error(self, error_type: str) -> None:
        """Record an error."""
        if self.enabled:
            self._error_count += 1
            self._errors[error_type] = self._errors.get(error_type, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "scan_count": self._scan_count,
            "scan_duration_total": self._scan_duration_total,
            "error_count": self._error_count,
            "errors": self._errors.copy(),
            "alerts": self._alerts.copy(),
        }
