"""Branch-focused tests for scanner_kernel.plugin_name_resolver."""

from __future__ import annotations

import pytest

from prism.scanner_kernel.plugin_name_resolver import resolve_scan_pipeline_plugin_name


class _Registry:
    def __init__(self, plugin_names: list[str]) -> None:
        self._plugin_names = plugin_names

    def list_scan_pipeline_plugins(self) -> list[str]:
        return list(self._plugin_names)

    def get_scan_pipeline_plugin(self, plugin_name: str) -> object | None:
        if plugin_name in self._plugin_names:
            return object
        return None


def test_resolve_plugin_name_prefers_explicit_scan_pipeline_plugin() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={"scan_pipeline_plugin": "  custom  ", "platform": "ansible"},
        registry=_Registry(["default"]),
    )

    assert result == "custom"


def test_resolve_plugin_name_uses_policy_context_selection_plugin() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={
            "policy_context": {"selection": {"plugin": "  policy_plugin  "}},
            "platform": "ansible",
        },
        registry=_Registry(["default"]),
    )

    assert result == "policy_plugin"


def test_resolve_plugin_name_falls_back_to_platform() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={"platform": "  kubernetes  "},
        registry=_Registry(["default"]),
    )

    assert result == "kubernetes"


def test_resolve_plugin_name_uses_default_plugin_when_present() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={},
        registry=_Registry(["other", "default", "zeta"]),
    )

    assert result == "default"


def test_resolve_plugin_name_uses_single_registered_plugin_when_no_default() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={},
        registry=_Registry(["only_plugin"]),
    )

    assert result == "only_plugin"


def test_resolve_plugin_name_uses_lexical_fallback_when_multiple_plugins() -> None:
    result = resolve_scan_pipeline_plugin_name(
        scan_options={},
        registry=_Registry(["zeta", "beta", "gamma"]),
    )

    assert result == "beta"


def test_resolve_plugin_name_errors_when_registry_missing_for_unresolved_selection() -> (
    None
):
    with pytest.raises(ValueError, match="registry must be provided"):
        resolve_scan_pipeline_plugin_name(scan_options={})
