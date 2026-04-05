"""Tests for scanner plugin defaults and runtime boundary contracts."""

from __future__ import annotations

import importlib
from typing import Any

import prism.scanner as scanner_module
import prism.scanner_core.di as di_module
import prism.scanner_core.scanner_context as scanner_context_module
from prism.scanner_plugins.defaults import (
    DefaultFeatureDetectionPlugin,
    DefaultOutputOrchestrationPlugin,
    resolve_comment_driven_documentation_plugin,
)


def test_default_feature_detection_plugin_delegates_to_feature_detector(
    monkeypatch,
) -> None:
    """Default feature plugin should delegate to canonical feature detector."""

    class _FakeFeatureDetector:
        def __init__(self, di: Any, role_path: str, options: dict[str, Any]) -> None:
            self._role_path = role_path
            self._options = options

        def detect(self) -> dict[str, Any]:
            return {
                "role_path": self._role_path,
                "role_name_override": self._options.get("role_name_override"),
            }

        def analyze_task_catalog(self) -> dict[str, Any]:
            return {"main.yml": {"task_count": 1}}

    monkeypatch.setattr(
        "prism.scanner_core.feature_detector.FeatureDetector",
        _FakeFeatureDetector,
    )

    plugin = DefaultFeatureDetectionPlugin(di=object())
    detected = plugin.detect_features(
        role_path="/tmp/role",
        options={"role_name_override": "demo"},
    )
    catalog = plugin.analyze_task_catalog(
        role_path="/tmp/role",
        options={"role_name_override": "demo"},
    )

    assert detected == {
        "role_path": "/tmp/role",
        "role_name_override": "demo",
    }
    assert catalog == {"main.yml": {"task_count": 1}}


def test_default_output_orchestration_plugin_returns_merged_payload_copy() -> None:
    """Default output plugin should delegate payload construction to canonical builder."""
    from prism.scanner_io import build_scan_output_payload

    payload = {
        "role_name": "demo",
        "description": "desc",
        "display_variables": {"x": {"required": False}},
        "requirements_display": [],
        "undocumented_default_filters": [],
        "metadata": {"existing": True},
    }

    plugin = DefaultOutputOrchestrationPlugin(di=object())
    result = plugin.orchestrate_output(
        scan_payload=payload,
        metadata={"features": {"tasks_scanned": 2}},
        discovered_variables=[{"name": "x"}, {"name": "y"}],
    )

    expected = build_scan_output_payload(
        role_name=payload["role_name"],
        description=payload["description"],
        display_variables=payload["display_variables"],
        requirements_display=payload["requirements_display"],
        undocumented_default_filters=payload["undocumented_default_filters"],
        metadata={
            "existing": True,
            "features": {"tasks_scanned": 2},
            "discovered_variables_count": 2,
        },
    )

    assert result is not payload
    assert result == expected
    assert result["display_variables"] is payload["display_variables"]
    assert result["requirements_display"] is payload["requirements_display"]
    assert (
        result["undocumented_default_filters"]
        is payload["undocumented_default_filters"]
    )
    assert result["metadata"]["existing"] is True
    assert result["metadata"]["features"] == {"tasks_scanned": 2}
    assert result["metadata"]["discovered_variables_count"] == 2


def test_plugin_registry_stays_utility_only_not_runtime_wired() -> None:
    """Runtime scanner seams should not directly depend on global plugin registry."""
    scanner_source = importlib.import_module("prism.scanner").__dict__.get(
        "__doc__", ""
    )
    del scanner_source

    scanner_module_source = scanner_module.__loader__.get_source(
        scanner_module.__name__
    )
    context_module_source = scanner_context_module.__loader__.get_source(
        scanner_context_module.__name__
    )
    di_module_source = di_module.__loader__.get_source(di_module.__name__)

    assert scanner_module_source is not None
    assert context_module_source is not None
    assert di_module_source is not None

    assert (
        "from prism.scanner_plugins.registry import plugin_registry"
        not in scanner_module_source
    )
    assert "plugin_registry" not in context_module_source
    assert "plugin_registry" not in di_module_source


def test_plugin_registry_remains_utility_module() -> None:
    """Utility registry should still support explicit registration and lookup."""
    from prism.scanner_plugins.registry import PluginRegistry

    class _Plugin:
        pass

    registry = PluginRegistry()
    registry.register_feature_detection_plugin("demo", _Plugin)

    assert registry.get_feature_detection_plugin("demo") is _Plugin


def test_resolve_comment_driven_documentation_plugin_uses_di_factory() -> None:
    marker = object()

    class _FakeContainer:
        def factory_comment_driven_doc_plugin(self):
            return marker

    plugin = resolve_comment_driven_documentation_plugin(_FakeContainer())

    assert plugin is marker


def test_resolve_comment_driven_documentation_plugin_falls_back_without_di() -> None:
    plugin = resolve_comment_driven_documentation_plugin(None)

    assert hasattr(plugin, "extract_role_notes_from_comments")
