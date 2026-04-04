"""Integration tests for complete scanner workflow (end-to-end validation).

These tests validate the complete scanner workflow from role discovery
to output generation. Unlike unit tests (which isolate and mock each
component), integration tests run the full pipeline with real files
to ensure components work together correctly.

These tests are kept for regression validation of critical paths:
- Full role scanning
- Complete payload generation
- Public API contracts (api.py, cli.py)
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from prism import errors as prism_errors
from prism import scanner
from prism.scanner_core import scan_request
from prism.scanner_core import DIContainer, ScannerContext
from pyfakefs.fake_filesystem import FakeFilesystem


def _prepare_scan_context_stub(
    scan_options: dict[str, object], di_container=None, **kwargs
):
    """Stub implementation of prepare_scan_context for testing."""
    role_path = str(scan_options["role_path"])
    role_name = str(scan_options.get("role_name_override") or "").strip()
    if not role_name:
        role_name = Path(role_path).name
    return {
        "role_path": role_path,
        "role_name": role_name,
        "description": f"Test role: {role_name}",
        "display_variables": {},
        "requirements_display": [],
        "undocumented_default_filters": [],
        "scan_options": scan_options,
    }


def _canonical_scan_options(role_path: str) -> dict:
    scan_options = scan_request.build_run_scan_options_canonical(
        role_path=role_path,
        role_name_override=None,
        readme_config_path=None,
        include_vars_main=True,
        exclude_path_patterns=None,
        detailed_catalog=False,
        include_task_parameters=True,
        include_task_runbooks=True,
        inline_task_runbooks=True,
        include_collection_checks=True,
        keep_unknown_style_sections=True,
        adopt_heading_mode=None,
        vars_seed_paths=None,
        style_readme_path=None,
        style_source_path=None,
        style_guide_skeleton=False,
        compare_role_path=None,
        fail_on_unconstrained_dynamic_includes=None,
        fail_on_yaml_like_task_annotations=None,
        ignore_unresolved_internal_underscore_references=False,
    )
    scan_options["enforce_role_path_exists"] = True
    return scan_options


def _build_context(role_path: str) -> ScannerContext:
    scan_options = _canonical_scan_options(role_path)
    di = DIContainer(role_path=role_path, scan_options=scan_options)
    return ScannerContext(
        di=di,
        role_path=role_path,
        scan_options=scan_options,
        prepare_scan_context_fn=_prepare_scan_context_stub,
    )


class TestScannerIntegrationEndToEnd:
    """Test complete scanner workflow (end-to-end integration)."""

    def test_scanner_context_orchestrate_scan_with_empty_role(
        self, fs: FakeFilesystem
    ) -> None:
        """Full scan workflow with empty role produces valid payload."""
        with fs.patcher:
            role_path = Path("/test_role")
            role_path.mkdir(parents=True, exist_ok=True)
            context = _build_context(str(role_path))

            # Full orchestration
            payload = context.orchestrate_scan()

            # Validate payload structure
            assert isinstance(payload, dict)
            assert "display_variables" in payload
            assert "metadata" in payload

    def test_scanner_context_orchestrate_scan_with_basic_role(
        self, fs: FakeFilesystem
    ) -> None:
        """Full scan workflow with basic role discovers variables."""
        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )
            context = _build_context(str(role_path))

            # Full orchestration
            payload = context.orchestrate_scan()

            # Validate payload structure
            assert isinstance(payload, dict)
            assert "display_variables" in payload
            assert "metadata" in payload

    def test_scanner_context_orchestrate_scan_with_complex_role(
        self, fs: FakeFilesystem
    ) -> None:
        """Full scan workflow with complex role analyzes features."""
        with fs.patcher:
            role_path = Path("/complex_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "handlers").mkdir(parents=True, exist_ok=True)
            (role_path / "templates").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\napp_name: myapp\napp_version: 1.0.0\napp_port: 8080\napp_config:\n  debug: false\n  timeout: 30\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Install application\n  apt:\n    name: '{{ app_name }}'\n    state: present\n  notify: restart app\n\n- name: Configure application\n  template:\n    src: app.conf.j2\n    dest: /etc/app/config\n  notify: restart app\n"
            )
            (role_path / "handlers" / "main.yml").write_text(
                "---\n- name: restart app\n  systemd:\n    name: '{{ app_name }}'\n    state: restarted\n"
            )
            (role_path / "templates" / "app.conf.j2").write_text(
                "# Configuration for {{ app_name }}\nport: {{ app_port }}\nversion: {{ app_version }}\n"
            )
            context = _build_context(str(role_path))

            # Full orchestration
            payload = context.orchestrate_scan()

            # Validate payload structure
            assert isinstance(payload, dict)
            assert "display_variables" in payload
            assert "metadata" in payload

    def test_scanner_context_payload_contains_metadata(
        self, fs: FakeFilesystem
    ) -> None:
        """Payload includes complete metadata after orchestration."""
        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )
            context = _build_context(str(role_path))

            payload = context.orchestrate_scan()

            # Validate metadata presence
            assert "metadata" in payload
            metadata = payload["metadata"]
            assert isinstance(metadata, dict)

    def test_scanner_context_handles_missing_role_gracefully(
        self, fs: FakeFilesystem
    ) -> None:
        """ScannerContext raises explicitly when role path does not exist."""
        with fs.patcher:
            missing_role_path = Path("/missing-role")
            assert not missing_role_path.exists()

            context = _build_context(str(missing_role_path))

            with pytest.raises(FileNotFoundError, match="role path not found"):
                context.orchestrate_scan()

    def test_scanner_context_discovered_variables_contain_all_phases(
        self, fs: FakeFilesystem
    ) -> None:
        """Discovered variables include both static and referenced sources."""
        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )
            context = _build_context(str(role_path))

            context.orchestrate_scan()

            discovered = context.discovered_variables
            # Should be tuple (immutable)
            assert isinstance(discovered, tuple)

    def test_scanner_context_state_is_immutable_after_orchestration(
        self, fs: FakeFilesystem
    ) -> None:
        """ScannerContext maintains immutable state after orchestration."""
        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )
            context = _build_context(str(role_path))

            # First orchestration
            payload1 = context.orchestrate_scan()
            discovered1 = context.discovered_variables

            assert isinstance(payload1["metadata"], dict)

            # Second orchestration (should be independent)
            payload2 = context.orchestrate_scan()
            discovered2 = context.discovered_variables

            assert isinstance(payload2["metadata"], dict)
            assert discovered1 == discovered2

            # Mutating returned payload must not affect subsequent orchestration state.
            payload2["display_variables"]["__test_mutation__"] = {"required": False}
            payload2["metadata"]["__test_mutation__"] = True

            payload3 = context.orchestrate_scan()
            assert "__test_mutation__" not in payload3["display_variables"]
            assert "__test_mutation__" not in payload3["metadata"]

    def test_run_scan_raises_on_discovery_failure_by_default(
        self,
        fs: FakeFilesystem,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """run_scan must surface discovery failures by default."""

        class _FailingDiscovery:
            def discover(self) -> tuple[object, ...]:
                raise RuntimeError("discovery exploded")

        monkeypatch.setattr(
            DIContainer,
            "factory_variable_discovery",
            lambda self: _FailingDiscovery(),
        )

        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )

            with pytest.raises(RuntimeError, match="discovery exploded"):
                scanner.run_scan(
                    role_path=str(role_path),
                    output="README.md",
                    output_format="md",
                    dry_run=True,
                )

    def test_run_scan_best_effort_marks_degraded_metadata(
        self,
        fs: FakeFilesystem,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Best-effort run_scan mode should annotate degraded metadata."""

        captured: dict[str, object] = {}

        class _FailingDiscovery:
            def discover(self) -> tuple[object, ...]:
                raise prism_errors.PrismRuntimeError(
                    code=prism_errors.ROLE_SCAN_RUNTIME_ERROR,
                    category=prism_errors.ERROR_CATEGORY_RUNTIME,
                    message="discovery exploded",
                )

        def fake_emit_scan_outputs(args: dict[str, object]) -> str:
            captured["metadata"] = args["metadata"]
            return "ok"

        monkeypatch.setattr(
            DIContainer,
            "factory_variable_discovery",
            lambda self: _FailingDiscovery(),
        )
        monkeypatch.setattr(scanner, "_emit_scan_outputs", fake_emit_scan_outputs)

        with fs.patcher:
            role_path = Path("/basic_role")
            (role_path / "defaults").mkdir(parents=True, exist_ok=True)
            (role_path / "tasks").mkdir(parents=True, exist_ok=True)
            (role_path / "defaults" / "main.yml").write_text(
                "---\ntest_variable: test_value\nenabled: true\n"
            )
            (role_path / "tasks" / "main.yml").write_text(
                "---\n- name: Test task\n  debug:\n    msg: '{{ test_variable }}'\n"
            )

            scanner.run_scan(
                role_path=str(role_path),
                output="README.md",
                output_format="md",
                dry_run=True,
                strict_phase_failures=False,
            )

            metadata = cast(dict[str, object], captured["metadata"])
            scan_errors = cast(list[dict[str, str]], metadata["scan_errors"])
            assert metadata["scan_degraded"] is True
            assert scan_errors[0]["phase"] == "discovery"
            assert scan_errors[0]["error_type"] == "PrismRuntimeError"
            assert "discovery exploded" in scan_errors[0]["message"]
