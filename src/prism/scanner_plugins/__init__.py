"""Scanner plugin package ownership for the fsrc lane.

Importing this module bootstraps required defaults onto the canonical plugin
registry singleton and exposes that same singleton via DEFAULT_PLUGIN_REGISTRY.
"""

from __future__ import annotations

from typing import cast

from prism.scanner_plugins.default_scan_pipeline import DefaultScanPipelinePlugin
from prism.scanner_plugins.ansible import AnsibleScanPipelinePlugin
from prism.scanner_plugins.ansible import AnsibleReadmeRendererPlugin
from prism.scanner_plugins.ansible.default_policies import (
    AnsibleDefaultTaskAnnotationPolicyPlugin,
    AnsibleDefaultTaskLineParsingPolicyPlugin,
    AnsibleDefaultTaskTraversalPolicyPlugin,
    AnsibleDefaultVariableExtractorPolicyPlugin,
)
from prism.scanner_plugins.parsers.jinja import DefaultJinjaAnalysisPolicyPlugin
from prism.scanner_plugins.parsers.yaml import DefaultYAMLParsingPolicyPlugin
from prism.scanner_plugins.parsers.comment_doc.role_notes_parser import (
    CommentDrivenDocumentationParser,
)
from prism.scanner_plugins.registry import PluginRegistry
from prism.scanner_plugins.registry import plugin_registry as canonical_plugin_registry
from prism.scanner_plugins.registry import (
    PRISM_PLUGIN_API_VERSION,
    PluginAPIVersionMismatch,
    validate_plugin_api_version,
)
from prism.scanner_plugins.discovery import (
    PRISM_PLUGIN_ENTRY_POINT_GROUP,
    EntryPointPluginLoadError,
    discover_entry_point_plugins,
)
from prism.scanner_plugins.interfaces import ScanPipelinePlugin


# ---------------------------------------------------------------------------
# Built-in plugin registration tables.
#
# Source of truth for which plugins are baseline-registered. Iterated by
# bootstrap_default_plugins() so the bootstrap step is data-driven instead of
# 100+ lines of repetitive `if name not in list_X(): register_X(...)` blocks.
#
# Adding a new built-in is now a single tuple addition rather than a new
# imperative branch.
# ---------------------------------------------------------------------------

# (slot_name, plugin_class) entries grouped by the registry method that
# accepts a directly-imported class.
_DIRECT_REGISTRATIONS: tuple[tuple[str, str, type], ...] = (
    ("comment_driven_doc", "default", CommentDrivenDocumentationParser),
    ("readme_renderer", "ansible", AnsibleReadmeRendererPlugin),
    ("scan_pipeline", "default", cast(type, DefaultScanPipelinePlugin)),
    ("scan_pipeline", "ansible", cast(type, AnsibleScanPipelinePlugin)),
    ("extract_policy", "task_line_parsing", AnsibleDefaultTaskLineParsingPolicyPlugin),
    ("extract_policy", "task_traversal", AnsibleDefaultTaskTraversalPolicyPlugin),
    (
        "extract_policy",
        "variable_extractor",
        AnsibleDefaultVariableExtractorPolicyPlugin,
    ),
    (
        "extract_policy",
        "task_annotation_parsing",
        AnsibleDefaultTaskAnnotationPolicyPlugin,
    ),
    ("yaml_parsing_policy", "yaml_parsing", DefaultYAMLParsingPolicyPlugin),
    ("jinja_analysis_policy", "jinja_analysis", DefaultJinjaAnalysisPolicyPlugin),
)

# (slot, name, module_path, class_name) entries for slots that must defer the
# class import until first use (avoids load-time cycles via the
# scanner_plugins eager-import chain — see LESSON-08).
_DEFERRED_REGISTRATIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "variable_discovery",
        "ansible",
        "prism.scanner_plugins.ansible.variable_discovery",
        "AnsibleVariableDiscoveryPlugin",
    ),
    (
        "variable_discovery",
        "default",
        "prism.scanner_plugins.ansible.variable_discovery",
        "AnsibleVariableDiscoveryPlugin",
    ),
    (
        "feature_detection",
        "ansible",
        "prism.scanner_plugins.ansible.feature_detection",
        "AnsibleFeatureDetectionPlugin",
    ),
    (
        "feature_detection",
        "default",
        "prism.scanner_plugins.ansible.feature_detection",
        "AnsibleFeatureDetectionPlugin",
    ),
)

_RESERVED_UNSUPPORTED_PLATFORMS: tuple[str, ...] = ("kubernetes", "terraform")

# Maps slot -> (list_method_name, register_method_name) on PluginRegistry.
_DIRECT_SLOT_DISPATCH: dict[str, tuple[str, str]] = {
    "comment_driven_doc": (
        "list_comment_driven_doc_plugins",
        "register_comment_driven_doc_plugin",
    ),
    "scan_pipeline": (
        "list_scan_pipeline_plugins",
        "register_scan_pipeline_plugin",
    ),
    "extract_policy": (
        "list_extract_policy_plugins",
        "register_extract_policy_plugin",
    ),
    "yaml_parsing_policy": (
        "list_yaml_parsing_policy_plugins",
        "register_yaml_parsing_policy_plugin",
    ),
    "jinja_analysis_policy": (
        "list_jinja_analysis_policy_plugins",
        "register_jinja_analysis_policy_plugin",
    ),
    "readme_renderer": (
        "list_readme_renderer_plugins",
        "register_readme_renderer_plugin",
    ),
}

_DEFERRED_SLOT_DISPATCH: dict[str, tuple[str, str]] = {
    "variable_discovery": (
        "list_variable_discovery_plugins",
        "register_deferred_variable_discovery_plugin",
    ),
    "feature_detection": (
        "list_feature_detection_plugins",
        "register_deferred_feature_detection_plugin",
    ),
}


def bootstrap_default_plugins(registry: PluginRegistry | None = None) -> PluginRegistry:
    """Register baseline fsrc plugin ownership seams into the plugin registry.

    Data-driven: iterates :data:`_DIRECT_REGISTRATIONS`,
    :data:`_DEFERRED_REGISTRATIONS`, and
    :data:`_RESERVED_UNSUPPORTED_PLATFORMS`. First-registrant-wins
    semantics preserved via the per-slot list-membership guard.
    """

    active_registry = registry or canonical_plugin_registry

    for slot, name, plugin_cls in _DIRECT_REGISTRATIONS:
        list_method, register_method = _DIRECT_SLOT_DISPATCH[slot]
        if name not in getattr(active_registry, list_method)():
            getattr(active_registry, register_method)(name, plugin_cls)

    for slot, name, module_path, class_name in _DEFERRED_REGISTRATIONS:
        list_method, register_method = _DEFERRED_SLOT_DISPATCH[slot]
        if name not in getattr(active_registry, list_method)():
            getattr(active_registry, register_method)(name, module_path, class_name)

    for platform_name in _RESERVED_UNSUPPORTED_PLATFORMS:
        if not active_registry.is_reserved_unsupported_platform(platform_name):
            active_registry.register_reserved_unsupported_platform(platform_name)

    # Auto-discover externally distributed plugins via entry points. Failures
    # are logged (not raised) so a broken third-party plugin cannot block
    # built-in scanner usage. PluginAPIVersionMismatch still propagates.
    discover_entry_point_plugins(registry=active_registry)

    return active_registry


DEFAULT_PLUGIN_REGISTRY = bootstrap_default_plugins()

__all__ = [
    "DEFAULT_PLUGIN_REGISTRY",
    "EntryPointPluginLoadError",
    "PRISM_PLUGIN_API_VERSION",
    "PRISM_PLUGIN_ENTRY_POINT_GROUP",
    "PluginAPIVersionMismatch",
    "ScanPipelinePlugin",
    "bootstrap_default_plugins",
    "discover_entry_point_plugins",
    "interfaces",
    "registry",
    "validate_plugin_api_version",
]
