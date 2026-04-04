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
        # TODO: Implement proper feature detection
        return {}

    def analyze_task_catalog(
        self, role_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        # TODO: Implement proper task catalog analysis
        return {}


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
        # For now, return the payload as-is; TODO: implement proper orchestration
        return scan_payload


class DefaultCommentDrivenDocumentationPlugin(CommentDrivenDocumentationPlugin):
    """Default comment-driven documentation plugin using existing extraction logic."""

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
