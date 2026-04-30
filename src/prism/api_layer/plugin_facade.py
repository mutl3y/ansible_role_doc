"""Thin facade for API-layer access to scanner_plugins functionality.

This module provides a controlled boundary between the API layer and the plugin
layer, preventing direct scanner_plugins imports from spreading across top-level
API/CLI modules.

All functions in this module are simple pass-through wrappers with no additional
logic. They exist solely to establish an import boundary for architectural hygiene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from prism.scanner_config.audit_rules import AuditReport, AuditRule
    from prism.scanner_data.contracts_request import (
        PreparedPolicyBundle,
        PreparedYAMLParsingPolicy,
    )
    from prism.scanner_plugins.interfaces import CommentDrivenDocumentationPlugin
    from prism.scanner_plugins.registry import PluginRegistry


@runtime_checkable
class _HasScanOptions(Protocol):
    """Minimal DI interface for scan_options access."""

    scan_options: dict[str, object]


def get_default_plugin_registry() -> PluginRegistry:
    """Return the default plugin registry instance.

    This is a pass-through to scanner_plugins.DEFAULT_PLUGIN_REGISTRY.
    """
    from prism.scanner_plugins import DEFAULT_PLUGIN_REGISTRY

    return DEFAULT_PLUGIN_REGISTRY


def ensure_prepared_policy_bundle(
    *,
    scan_options: dict[str, object],
    di: _HasScanOptions | object,
) -> PreparedPolicyBundle:
    """Ensure prepared policy bundle is available from scan_options.

    This is a pass-through to scanner_plugins.bundle_resolver.ensure_prepared_policy_bundle.
    """
    from prism.scanner_plugins.bundle_resolver import (
        ensure_prepared_policy_bundle as _ensure_prepared_policy_bundle,
    )

    return _ensure_prepared_policy_bundle(scan_options=scan_options, di=di)


def resolve_comment_driven_documentation_plugin(
    di: object,
) -> CommentDrivenDocumentationPlugin:
    """Resolve the comment-driven documentation plugin from DI.

    This is a pass-through to scanner_plugins.defaults.resolve_comment_driven_documentation_plugin.
    """
    from prism.scanner_plugins.defaults import (
        resolve_comment_driven_documentation_plugin as _resolve_plugin,
    )

    return _resolve_plugin(di)


def load_audit_rules_from_file(rules_path: str) -> list[AuditRule]:
    """Load audit rules from a file path.

    This is a pass-through to scanner_plugins.audit.load_audit_rules_from_file.
    """
    from prism.scanner_plugins.audit.loader import load_audit_rules_from_file as _load

    return _load(rules_path)


def run_audit(payload: dict[str, object], rules: list[AuditRule]) -> AuditReport:
    """Run audit rules against a scan payload.

    This is a pass-through to scanner_plugins.audit.run_audit.
    """
    from prism.scanner_plugins.audit.runner import run_audit as _run_audit

    return _run_audit(payload, rules)


def resolve_yaml_parsing_policy_plugin(
    di: object | None = None,
    *,
    strict_mode: bool = True,
    registry: PluginRegistry | None = None,
) -> PreparedYAMLParsingPolicy:
    """Resolve the YAML parsing policy plugin from DI or registry.

    This is a pass-through to scanner_plugins.defaults.resolve_yaml_parsing_policy_plugin.
    """
    from prism.scanner_plugins.defaults import (
        resolve_yaml_parsing_policy_plugin as _resolve_plugin,
    )

    return _resolve_plugin(di, strict_mode=strict_mode, registry=registry)
