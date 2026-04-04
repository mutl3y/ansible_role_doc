"""
Plugin interfaces for Prism scanner extensibility.

This module defines the abstract interfaces that plugins must implement
to extend Prism's scan logic. All plugins are loaded dynamically via the
extension registry and must maintain immutability and isolation.
"""

from abc import abstractmethod
from typing import Any, Dict, FrozenSet, List, Optional, Protocol, Tuple

from prism.scanner_data.contracts import (
    RunScanOutputPayload,
    VariableRow,
)


class VariableDiscoveryPlugin(Protocol):
    """Interface for variable discovery plugins."""

    @abstractmethod
    def discover_static_variables(
        self, role_path: str, options: Dict[str, Any]
    ) -> Tuple[VariableRow, ...]:
        """Discover variables defined statically in the role."""
        ...

    @abstractmethod
    def discover_referenced_variables(
        self,
        role_path: str,
        options: Dict[str, Any],
        readme_content: Optional[str] = None,
    ) -> FrozenSet[str]:
        """Discover variables referenced in the role."""
        ...

    @abstractmethod
    def resolve_unresolved_variables(
        self,
        static_names: FrozenSet[str],
        referenced: FrozenSet[str],
        options: Dict[str, Any],
    ) -> Dict[str, str]:
        """Resolve uncertainty reasons for unresolved variables."""
        ...


class FeatureDetectionPlugin(Protocol):
    """Interface for feature detection plugins."""

    @abstractmethod
    def detect_features(
        self, role_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect features in the role and return metadata."""
        ...

    @abstractmethod
    def analyze_task_catalog(
        self, role_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the task catalog for detailed per-file insights."""
        ...


class OutputOrchestrationPlugin(Protocol):
    """Interface for output orchestration plugins."""

    @abstractmethod
    def orchestrate_output(
        self,
        scan_payload: RunScanOutputPayload,
        metadata: Dict[str, Any],
        discovered_variables: list[VariableRow],
    ) -> RunScanOutputPayload:
        """Orchestrate the final output payload."""
        ...


class ScanPipelinePlugin(Protocol):
    """Protocol for scan pipeline plugins that can modify the entire scan process."""

    def process_scan_pipeline(
        self,
        scan_options: dict[str, Any],
        scan_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Process the scan pipeline, potentially modifying scan options or context.

        Args:
            scan_options: The scan options dict
            scan_context: The scan context dict

        Returns:
            Modified scan context dict
        """
        ...


class CommentDrivenDocumentationPlugin(Protocol):
    """Interface for comment-driven documentation extraction plugins."""

    @abstractmethod
    def extract_role_notes_from_comments(
        self,
        role_path: str,
        exclude_paths: Optional[List[str]] = None,
        marker_prefix: str = "prism",
    ) -> Dict[str, List[str]]:
        """Extract comment-driven role notes from YAML files."""
        ...
