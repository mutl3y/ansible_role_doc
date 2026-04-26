"""Unit tests for prism.scanner_plugins.ansible.kernel (FIND-13 closure)."""

from __future__ import annotations

from typing import Any

from prism.scanner_plugins.ansible.kernel import (
    ANSIBLE_KERNEL_PLUGIN_MANIFEST,
    AnsibleBaselineKernelPlugin,
    PLUGIN_CONTRACT_VERSION,
    load_ansible_kernel_plugin,
)


def test_plugin_contract_version_is_v1() -> None:
    assert PLUGIN_CONTRACT_VERSION["major"] == 1
    assert PLUGIN_CONTRACT_VERSION["minor"] == 0


def test_load_returns_baseline_plugin_instance() -> None:
    plugin = load_ansible_kernel_plugin()
    assert isinstance(plugin, AnsibleBaselineKernelPlugin)


def test_manifest_exposes_plugin_id_and_capabilities() -> None:
    assert ANSIBLE_KERNEL_PLUGIN_MANIFEST["plugin_id"] == "prism.ansible.baseline.v1"
    capabilities = ANSIBLE_KERNEL_PLUGIN_MANIFEST["capabilities"]
    assert capabilities["platform"] == "ansible"
    assert capabilities["supports_provenance"] is True
    assert capabilities["supports_incremental"] is False


def test_prepare_includes_metadata() -> None:
    plugin = load_ansible_kernel_plugin()
    result = plugin.prepare({"platform": "ansible"})
    assert result["metadata"]["plugin_id"] == "prism.ansible.baseline.v1"
    assert result["metadata"]["platform"] == "ansible"


def test_prepare_defaults_platform_to_ansible_when_missing() -> None:
    plugin = load_ansible_kernel_plugin()
    result = plugin.prepare({})
    assert result["metadata"]["platform"] == "ansible"


def test_scan_without_orchestrator_returns_empty_payload_skeleton() -> None:
    plugin = load_ansible_kernel_plugin()
    response = plugin.scan({"scan_id": "S1", "target_path": "/r"})
    payload = response["payload"]
    assert payload["role_name"] == ""
    assert payload["display_variables"] == {}
    assert payload["requirements_display"] == []
    assert response["metadata"]["scan_id"] == "S1"


def test_scan_with_orchestrator_invokes_callable_with_role_path_and_options() -> None:
    captured: dict[str, Any] = {}

    def fake_orchestrator(*, role_path: str, scan_options: dict[str, Any]):
        captured["role_path"] = role_path
        captured["scan_options"] = scan_options
        return {"role_name": "r", "display_variables": {"a": {}}}

    plugin = load_ansible_kernel_plugin(orchestrate_scan_payload_fn=fake_orchestrator)
    response = plugin.scan(
        {"scan_id": "S2", "target_path": "/role", "options": {"detailed_catalog": True}}
    )
    assert captured == {
        "role_path": "/role",
        "scan_options": {"detailed_catalog": True},
    }
    assert response["payload"]["role_name"] == "r"


def test_analyze_reports_phase_results_keys() -> None:
    plugin = load_ansible_kernel_plugin()
    response = plugin.analyze(
        {"scan_id": "S3"},
        {"phase_results": {"prepare": {}, "scan": {}}},
    )
    assert response["metadata"]["plugin_analyze"] == "completed"
    assert sorted(response["metadata"]["phase_results"]) == ["prepare", "scan"]


def test_finalize_reports_payload_presence() -> None:
    plugin = load_ansible_kernel_plugin()
    with_payload = plugin.finalize({"scan_id": "S"}, {"payload": {"k": 1}})
    without_payload = plugin.finalize({"scan_id": "S"}, {})
    assert with_payload["metadata"]["has_payload"] is True
    assert without_payload["metadata"]["has_payload"] is False
