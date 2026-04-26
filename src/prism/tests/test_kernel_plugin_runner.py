"""Branch-focused tests for scanner_kernel.kernel_plugin_runner."""

from __future__ import annotations

from typing import Any

from prism.scanner_kernel.kernel_plugin_runner import run_kernel_plugin_orchestrator


class _PluginMissingAnalyzeFinalize:
    def prepare(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        return {}

    def scan(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        return {"payload": {"items": [1]}}


class _PluginFailingPrepare:
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def prepare(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        self._events.append("prepare")
        raise RuntimeError("prepare failed")

    def scan(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        self._events.append("scan")
        return {}

    def analyze(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any]:
        del request
        del response
        self._events.append("analyze")
        return {}

    def finalize(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any]:
        del request
        del response
        self._events.append("finalize")
        return {}


class _PluginMergeOutputs:
    def prepare(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        return {
            "metadata": {"prepare": "ok"},
            "warnings": ["warn-prepare"],
            "provenance": ["prov-prepare"],
        }

    def scan(self, request: dict[str, Any]) -> dict[str, Any]:
        del request
        return {
            "payload": {"resource_count": 3},
            "metadata": {"scan": "ok"},
            "warnings": ["warn-scan"],
            "errors": ["soft-scan-error"],
            "provenance": ["prov-scan"],
        }

    def analyze(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any]:
        del request
        del response
        return {
            "metadata": {"analyze": "ok"},
            "warnings": ["warn-analyze"],
        }

    def finalize(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> dict[str, Any]:
        del request
        del response
        return {
            "metadata": {"finalize": "ok"},
            "provenance": ["prov-finalize"],
        }


def test_run_kernel_plugin_orchestrator_marks_missing_phase_handlers_as_skipped() -> (
    None
):
    response = run_kernel_plugin_orchestrator(
        platform="ansible",
        target_path="/tmp/role",
        scan_options={},
        load_plugin_fn=lambda _platform: _PluginMissingAnalyzeFinalize(),
    )

    assert response["phase_results"]["prepare"]["status"] == "completed"
    assert response["phase_results"]["scan"]["status"] == "completed"
    assert response["phase_results"]["analyze"]["status"] == "skipped"
    assert response["phase_results"]["finalize"]["status"] == "skipped"


def test_run_kernel_plugin_orchestrator_stops_on_failed_phase_when_fail_fast_true() -> (
    None
):
    events: list[str] = []

    response = run_kernel_plugin_orchestrator(
        platform="ansible",
        target_path="/tmp/role",
        scan_options={},
        load_plugin_fn=lambda _platform: _PluginFailingPrepare(events),
        fail_fast=True,
    )

    assert events == ["prepare"]
    assert response["phase_results"]["prepare"]["status"] == "failed"
    assert "scan" not in response["phase_results"]
    assert response["errors"][0]["recoverable"] is False


def test_run_kernel_plugin_orchestrator_continues_after_failure_when_fail_fast_false() -> (
    None
):
    events: list[str] = []

    response = run_kernel_plugin_orchestrator(
        platform="ansible",
        target_path="/tmp/role",
        scan_options={},
        load_plugin_fn=lambda _platform: _PluginFailingPrepare(events),
        fail_fast=False,
    )

    assert events == ["prepare", "scan", "analyze", "finalize"]
    assert response["phase_results"]["prepare"]["status"] == "failed"
    assert response["phase_results"]["scan"]["status"] == "completed"
    assert response["phase_results"]["analyze"]["status"] == "completed"
    assert response["phase_results"]["finalize"]["status"] == "completed"
    assert response["errors"][0]["recoverable"] is True


def test_run_kernel_plugin_orchestrator_merges_phase_payload_metadata_and_lists() -> (
    None
):
    response = run_kernel_plugin_orchestrator(
        platform="ansible",
        target_path="/tmp/role",
        scan_options={},
        load_plugin_fn=lambda _platform: _PluginMergeOutputs(),
    )

    assert response["payload"] == {"resource_count": 3}
    assert response["metadata"] == {
        "kernel_orchestrator": "fsrc-v1",
        "prepare": "ok",
        "scan": "ok",
        "analyze": "ok",
        "finalize": "ok",
    }
    assert response["warnings"] == ["warn-prepare", "warn-scan", "warn-analyze"]
    assert response["errors"] == ["soft-scan-error"]
    assert response["provenance"] == ["prov-prepare", "prov-scan", "prov-finalize"]
