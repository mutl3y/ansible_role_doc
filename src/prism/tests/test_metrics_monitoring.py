"""Tests for metrics and monitoring implementation."""

import time

from prism.scanner_core.metrics_collector import MetricsCollector


def test_metrics_collector_records_scan_duration():
    collector = MetricsCollector()
    collector.start_scan()
    time.sleep(0.01)  # Simulate some time
    collector.end_scan()

    metrics = collector.get_metrics()
    assert "scan_count" in metrics
    assert metrics["scan_count"] == 1
    assert "scan_duration_total" in metrics
    assert metrics["scan_duration_total"] > 0


def test_metrics_collector_records_errors():
    collector = MetricsCollector()
    collector.record_error("test_error")

    metrics = collector.get_metrics()
    assert "error_count" in metrics
    assert metrics["error_count"] == 1
    assert "errors" in metrics
    assert "test_error" in metrics["errors"]


def test_metrics_collector_configurable():
    config = {"enabled": True}
    collector = MetricsCollector(config)
    assert collector.enabled is True

    config_disabled = {"enabled": False}
    collector_disabled = MetricsCollector(config_disabled)
    assert collector_disabled.enabled is False


def test_metrics_collector_alert_thresholds():
    config = {"alert_thresholds": {"max_scan_duration": 0.001}}  # Very low threshold
    collector = MetricsCollector(config)

    collector.start_scan()
    time.sleep(0.01)  # Exceed threshold
    collector.end_scan()

    # Check that alert was logged or something, but for now, just check metrics
    metrics = collector.get_metrics()
    assert "alerts" in metrics
    assert len(metrics["alerts"]) > 0
