"""
Default plugin implementations for Prism scanner.

These wrap the existing scanner logic into pluggable components.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from prism.scanner_data.contracts import VariableRow
from prism.scanner_plugins.interfaces import (
    CommentDrivenDocumentationPlugin,
    FeatureDetectionPlugin,
    OutputOrchestrationPlugin,
    VariableDiscoveryPlugin,
)


class DefaultVariableDiscoveryPlugin(VariableDiscoveryPlugin):
    """Default variable discovery plugin using existing VariableDiscovery."""

    def __init__(self, di: Any) -> None:
        self._di = di

    def discover_static_variables(
        self, role_path: str, options: Dict[str, Any]
    ) -> Tuple[VariableRow, ...]:
        from prism.scanner_core.variable_discovery import VariableDiscovery

        discovery = VariableDiscovery(self._di, role_path, options)
        return discovery.discover_static()

    def discover_referenced_variables(
        self,
        role_path: str,
        options: Dict[str, Any],
        readme_content: Optional[str] = None,
    ) -> FrozenSet[str]:
        from prism.scanner_core.variable_discovery import VariableDiscovery

        discovery = VariableDiscovery(self._di, role_path, options)
        return discovery.discover_referenced(readme_content)

    def resolve_unresolved_variables(
        self,
        static_names: FrozenSet[str],
        referenced: FrozenSet[str],
        options: Dict[str, Any],
    ) -> Dict[str, str]:
        from prism.scanner_core.variable_discovery import VariableDiscovery

        discovery = VariableDiscovery(
            self._di, "", options
        )  # role_path not needed for resolve
        return discovery.resolve_unresolved(
            static_names=static_names, referenced=referenced
        )


class DefaultFeatureDetectionPlugin(FeatureDetectionPlugin):
    """Default feature detection plugin using existing FeatureDetector."""

    def __init__(self, di: Any) -> None:
        self._di = di

    def detect_features(
        self, role_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        from prism.scanner_core.feature_detector import FeatureDetector

        detector = FeatureDetector(self._di, role_path, options)
        return detector.detect()

    def analyze_task_catalog(
        self, role_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        from prism.scanner_core.feature_detector import FeatureDetector

        detector = FeatureDetector(self._di, role_path, options)
        return detector.analyze_task_catalog()


class DefaultOutputOrchestrationPlugin(OutputOrchestrationPlugin):
    """Default output orchestration plugin using existing OutputOrchestrator."""

    def __init__(self, di: Any) -> None:
        self._di = di

    def orchestrate_output(
        self,
        scan_payload: Any,  # RunScanOutputPayload
        metadata: Dict[str, Any],
        discovered_variables: list[VariableRow],
    ) -> Any:  # RunScanOutputPayload
        from prism.scanner_io import build_scan_output_payload

        merged_metadata = dict(scan_payload.get("metadata") or {})
        merged_metadata.update(metadata)
        merged_metadata["discovered_variables_count"] = len(discovered_variables)

        return build_scan_output_payload(
            role_name=scan_payload["role_name"],
            description=scan_payload["description"],
            display_variables=scan_payload["display_variables"],
            requirements_display=scan_payload["requirements_display"],
            undocumented_default_filters=scan_payload["undocumented_default_filters"],
            metadata=merged_metadata,
        )


class DefaultCommentDrivenDocumentationPlugin(CommentDrivenDocumentationPlugin):
    """Default comment-driven documentation plugin using existing extraction logic."""

    def __init__(self, di: Any | None = None) -> None:
        self._di = di

    def extract_role_notes_from_comments(
        self,
        role_path: str,
        exclude_paths: Optional[List[str]] = None,
        marker_prefix: str = "prism",
    ) -> Dict[str, List[str]]:
        from prism.scanner_extract.task_catalog_assembly import (
            _extract_role_notes_from_comments,
        )

        return _extract_role_notes_from_comments(
            role_path=role_path,
            exclude_paths=exclude_paths,
            marker_prefix=marker_prefix,
        )


def resolve_comment_driven_documentation_plugin(
    di: Any | None,
) -> CommentDrivenDocumentationPlugin:
    """Resolve comment-driven documentation plugin from DI with safe fallback."""
    factory = getattr(di, "factory_comment_driven_doc_plugin", None)
    if callable(factory):
        plugin = factory()
        if plugin is not None:
            return plugin
    return DefaultCommentDrivenDocumentationPlugin(di=di)
