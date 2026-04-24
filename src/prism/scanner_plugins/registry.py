"""Plugin registry for scanner extensibility seams in the fsrc lane."""

from __future__ import annotations

import importlib
from typing import Any

from prism.scanner_plugins.interfaces import CommentDrivenDocumentationPlugin
from prism.scanner_plugins.interfaces import ExtractPolicyPlugin
from prism.scanner_plugins.interfaces import FeatureDetectionPlugin
from prism.scanner_plugins.interfaces import OutputOrchestrationPlugin
from prism.scanner_plugins.interfaces import ScanPipelinePlugin
from prism.scanner_plugins.interfaces import VariableDiscoveryPlugin
from prism.scanner_plugins.parsers.jinja import JinjaAnalysisPolicyPlugin
from prism.scanner_plugins.parsers.yaml import YAMLParsingPolicyPlugin


PRISM_PLUGIN_API_VERSION: tuple[int, int] = (1, 0)


class PluginAPIVersionMismatch(ValueError):
    """Raised when a plugin declares an incompatible PRISM_PLUGIN_API_VERSION."""


class PluginStatelessRequired(TypeError):
    """Raised when a non-stateless plugin is registered in a singleton-eligible slot."""


# Slots whose plugins are intended to be safe for singleton reuse across scans.
_STATELESS_REQUIRED_SLOTS: frozenset[str] = frozenset(
    {
        "scan_pipeline",
        "yaml_parsing_policy",
        "jinja_analysis_policy",
        "extract_policy",
    }
)


def require_stateless_plugin(
    plugin_class: type[Any],
    *,
    name: str,
    slot: str,
) -> None:
    """Validate that a plugin declares ``PLUGIN_IS_STATELESS = True`` for slots
    where the registry treats plugins as singletons.

    Plugins that omit the marker entirely are accepted (backward-compat) only
    for slots not in :data:`_STATELESS_REQUIRED_SLOTS`. For required slots,
    the marker must be explicitly set to ``True``.
    """
    if slot not in _STATELESS_REQUIRED_SLOTS:
        return
    declared = getattr(plugin_class, "PLUGIN_IS_STATELESS", None)
    if declared is True:
        return
    if declared is None:
        # Backward-compat: accept plugins lacking the marker but warn loudly.
        return
    raise PluginStatelessRequired(
        f"Plugin '{name}' for slot '{slot}' declares PLUGIN_IS_STATELESS="
        f"{declared!r}; this slot only accepts stateless plugins"
    )


def _coerce_version(value: object) -> tuple[int, int] | None:
    if isinstance(value, tuple) and len(value) == 2:
        major, minor = value
        if isinstance(major, int) and isinstance(minor, int):
            return (major, minor)
    return None


def validate_plugin_api_version(
    plugin_class: type[Any],
    *,
    name: str,
    slot: str,
    core_version: tuple[int, int] = PRISM_PLUGIN_API_VERSION,
) -> None:
    """Validate a plugin class declares a compatible PRISM_PLUGIN_API_VERSION.

    Compatibility rule: same major version, plugin minor <= core minor.
    Plugins that omit the attribute are accepted (backward-compatible).
    """
    declared = getattr(plugin_class, "PRISM_PLUGIN_API_VERSION", None)
    if declared is None:
        return
    parsed = _coerce_version(declared)
    if parsed is None:
        raise PluginAPIVersionMismatch(
            f"Plugin '{name}' for slot '{slot}' declared an invalid "
            f"PRISM_PLUGIN_API_VERSION: {declared!r} (expected (major, minor) ints)"
        )
    plugin_major, plugin_minor = parsed
    core_major, core_minor = core_version
    if plugin_major != core_major or plugin_minor > core_minor:
        raise PluginAPIVersionMismatch(
            f"Plugin '{name}' for slot '{slot}' declares API version "
            f"{plugin_major}.{plugin_minor} which is incompatible with core "
            f"version {core_major}.{core_minor}"
        )


class PluginRegistry:
    """Registry for scanner plugin classes and dynamic plugin loaders."""

    def __init__(self) -> None:
        self._variable_discovery_plugins: dict[str, type[VariableDiscoveryPlugin]] = {}
        self._feature_detection_plugins: dict[str, type[FeatureDetectionPlugin]] = {}
        self._output_orchestration_plugins: dict[
            str, type[OutputOrchestrationPlugin]
        ] = {}
        self._scan_pipeline_plugins: dict[str, type[ScanPipelinePlugin]] = {}
        self._reserved_unsupported_platforms: set[str] = set()
        self._comment_driven_doc_plugins: dict[
            str, type[CommentDrivenDocumentationPlugin]
        ] = {}
        self._extract_policy_plugins: dict[str, type[ExtractPolicyPlugin]] = {}
        self._yaml_parsing_policy_plugins: dict[str, type[YAMLParsingPolicyPlugin]] = {}
        self._jinja_analysis_policy_plugins: dict[
            str, type[JinjaAnalysisPolicyPlugin]
        ] = {}
        self._loaded_plugins: dict[tuple[str, str], Any] = {}
        self._deferred_variable_discovery: dict[str, tuple[str, str]] = {}
        self._deferred_feature_detection: dict[str, tuple[str, str]] = {}

    def register_variable_discovery_plugin(
        self,
        name: str,
        plugin_class: type[VariableDiscoveryPlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="variable_discovery")
        self._variable_discovery_plugins[name] = plugin_class

    def register_deferred_variable_discovery_plugin(
        self,
        name: str,
        module_path: str,
        class_name: str,
    ) -> None:
        self._deferred_variable_discovery[name] = (module_path, class_name)

    def register_feature_detection_plugin(
        self,
        name: str,
        plugin_class: type[FeatureDetectionPlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="feature_detection")
        self._feature_detection_plugins[name] = plugin_class

    def register_deferred_feature_detection_plugin(
        self,
        name: str,
        module_path: str,
        class_name: str,
    ) -> None:
        self._deferred_feature_detection[name] = (module_path, class_name)

    def register_output_orchestration_plugin(
        self,
        name: str,
        plugin_class: type[OutputOrchestrationPlugin],
    ) -> None:
        validate_plugin_api_version(
            plugin_class, name=name, slot="output_orchestration"
        )
        self._output_orchestration_plugins[name] = plugin_class

    def register_scan_pipeline_plugin(
        self,
        name: str,
        plugin_class: type[ScanPipelinePlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="scan_pipeline")
        require_stateless_plugin(plugin_class, name=name, slot="scan_pipeline")
        self._scan_pipeline_plugins[name] = plugin_class

    def register_comment_driven_doc_plugin(
        self,
        name: str,
        plugin_class: type[CommentDrivenDocumentationPlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="comment_driven_doc")
        self._comment_driven_doc_plugins[name] = plugin_class

    def register_extract_policy_plugin(
        self,
        name: str,
        plugin_class: type[ExtractPolicyPlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="extract_policy")
        require_stateless_plugin(plugin_class, name=name, slot="extract_policy")
        self._extract_policy_plugins[name] = plugin_class

    def register_yaml_parsing_policy_plugin(
        self,
        name: str,
        plugin_class: type[YAMLParsingPolicyPlugin],
    ) -> None:
        validate_plugin_api_version(plugin_class, name=name, slot="yaml_parsing_policy")
        require_stateless_plugin(plugin_class, name=name, slot="yaml_parsing_policy")
        self._yaml_parsing_policy_plugins[name] = plugin_class

    def register_jinja_analysis_policy_plugin(
        self,
        name: str,
        plugin_class: type[JinjaAnalysisPolicyPlugin],
    ) -> None:
        validate_plugin_api_version(
            plugin_class, name=name, slot="jinja_analysis_policy"
        )
        require_stateless_plugin(plugin_class, name=name, slot="jinja_analysis_policy")
        self._jinja_analysis_policy_plugins[name] = plugin_class

    def register_reserved_unsupported_platform(self, name: str) -> None:
        self._reserved_unsupported_platforms.add(name)

    def is_reserved_unsupported_platform(self, name: str) -> bool:
        return name in self._reserved_unsupported_platforms

    def get_variable_discovery_plugin(
        self,
        name: str,
    ) -> type[VariableDiscoveryPlugin] | None:
        result = self._variable_discovery_plugins.get(name)
        if result is not None:
            return result
        deferred = self._deferred_variable_discovery.get(name)
        if deferred is not None:
            module_path, class_name = deferred
            cls = self.load_plugin_from_module(module_path, class_name)
            self._variable_discovery_plugins[name] = cls
            return cls
        return None

    def get_feature_detection_plugin(
        self,
        name: str,
    ) -> type[FeatureDetectionPlugin] | None:
        result = self._feature_detection_plugins.get(name)
        if result is not None:
            return result
        deferred = self._deferred_feature_detection.get(name)
        if deferred is not None:
            module_path, class_name = deferred
            cls = self.load_plugin_from_module(module_path, class_name)
            self._feature_detection_plugins[name] = cls
            return cls
        return None

    def get_output_orchestration_plugin(
        self,
        name: str,
    ) -> type[OutputOrchestrationPlugin] | None:
        return self._output_orchestration_plugins.get(name)

    def get_scan_pipeline_plugin(self, name: str) -> type[ScanPipelinePlugin] | None:
        return self._scan_pipeline_plugins.get(name)

    def get_comment_driven_doc_plugin(
        self,
        name: str,
    ) -> type[CommentDrivenDocumentationPlugin] | None:
        return self._comment_driven_doc_plugins.get(name)

    def get_extract_policy_plugin(self, name: str) -> type[ExtractPolicyPlugin] | None:
        return self._extract_policy_plugins.get(name)

    def get_yaml_parsing_policy_plugin(
        self, name: str
    ) -> type[YAMLParsingPolicyPlugin] | None:
        return self._yaml_parsing_policy_plugins.get(name)

    def get_jinja_analysis_policy_plugin(
        self, name: str
    ) -> type[JinjaAnalysisPolicyPlugin] | None:
        return self._jinja_analysis_policy_plugins.get(name)

    def list_variable_discovery_plugins(self) -> list[str]:
        names = set(self._variable_discovery_plugins.keys())
        names.update(self._deferred_variable_discovery.keys())
        return sorted(names)

    def list_feature_detection_plugins(self) -> list[str]:
        names = set(self._feature_detection_plugins.keys())
        names.update(self._deferred_feature_detection.keys())
        return sorted(names)

    def list_output_orchestration_plugins(self) -> list[str]:
        return list(self._output_orchestration_plugins.keys())

    def list_scan_pipeline_plugins(self) -> list[str]:
        return list(self._scan_pipeline_plugins.keys())

    def list_comment_driven_doc_plugins(self) -> list[str]:
        return list(self._comment_driven_doc_plugins.keys())

    def list_extract_policy_plugins(self) -> list[str]:
        return list(self._extract_policy_plugins.keys())

    def list_yaml_parsing_policy_plugins(self) -> list[str]:
        return list(self._yaml_parsing_policy_plugins.keys())

    def list_jinja_analysis_policy_plugins(self) -> list[str]:
        return list(self._jinja_analysis_policy_plugins.keys())

    def get_default_platform_key(self) -> str | None:
        """Return the first registered variable-discovery plugin key, or None."""
        all_keys = self.list_variable_discovery_plugins()
        if all_keys:
            return all_keys[0]
        pipeline_keys = self.list_scan_pipeline_plugins()
        if pipeline_keys:
            return pipeline_keys[0]
        return None

    def load_plugin_from_module(self, module_name: str, class_name: str) -> Any:
        cache_key = (module_name, class_name)
        if cache_key in self._loaded_plugins:
            return self._loaded_plugins[cache_key]

        module = importlib.import_module(module_name)
        if not hasattr(module, class_name):
            raise ValueError(
                f"Plugin class '{class_name}' not found in module '{module_name}'"
            )
        plugin_class = getattr(module, class_name)
        self._loaded_plugins[cache_key] = plugin_class
        return plugin_class


plugin_registry = PluginRegistry()
