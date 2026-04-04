"""Curated public compatibility surface for scanner data contracts.

Domain-owned contracts live in dedicated modules so unrelated contract changes
do not converge in a single god-file. This module preserves the stable
import surface for existing consumers by re-exporting the curated public set.
"""

from pathlib import Path
from typing import Any, Protocol

from prism.scanner_data.contracts_errors import (
    CollectionScanResult as CollectionScanResult,
    FailureDetail as FailureDetail,
    FailurePolicyContract as FailurePolicyContract,
    RepoScanResult as RepoScanResult,
    RoleScanResult as RoleScanResult,
    ScanPhaseStatus as ScanPhaseStatus,
)
from prism.scanner_data.contracts_collection import (
    PluginCatalog as PluginCatalog,
    PluginCatalogSummary as PluginCatalogSummary,
    PluginExtraction as PluginExtraction,
    PluginRecord as PluginRecord,
    PluginScanFailure as PluginScanFailure,
)
from prism.scanner_data.contracts_extraction import (
    VariableAnalysisResults as VariableAnalysisResults,
)
from prism.scanner_data.contracts_output import (
    AnnotationQualityCounters as AnnotationQualityCounters,
    EmitScanOutputsArgs as EmitScanOutputsArgs,
    FinalOutputPayload as FinalOutputPayload,
    NormalizedScannerReportMetadata as NormalizedScannerReportMetadata,
    OutputConfiguration as OutputConfiguration,
    ReadmeSectionRenderInput as ReadmeSectionRenderInput,
    RunbookSidecarArgs as RunbookSidecarArgs,
    RunbookSidecarPayload as RunbookSidecarPayload,
    RunScanOutputPayload as RunScanOutputPayload,
    ScanPayloadBuilder as ScanPayloadBuilder,
    ScanRenderPayload as ScanRenderPayload,
    ScanReportSidecarArgs as ScanReportSidecarArgs,
    ScannerCounters as ScannerCounters,
    ScannerReportIssueListRow as ScannerReportIssueListRow,
    ScannerReportMetadata as ScannerReportMetadata,
    ScannerReportSectionRenderInput as ScannerReportSectionRenderInput,
    ScannerReportYamlParseFailureRow as ScannerReportYamlParseFailureRow,
    SectionBodyRenderResult as SectionBodyRenderResult,
)
from prism.scanner_data.contracts_report import (
    ReportRenderingMetadata as ReportRenderingMetadata,
)
from prism.scanner_data.contracts_request import (
    FeaturesContext as FeaturesContext,
    PolicyContext as PolicyContext,
    ScanBaseContext as ScanBaseContext,
    ScanContext as ScanContext,
    ScanContextPayload as ScanContextPayload,
    ScanMetadata as ScanMetadata,
    ScanOptionsDict as ScanOptionsDict,
    ScanPhaseError as ScanPhaseError,
    StyleGuideConfig as StyleGuideConfig,
    _SectionTitleBucket as _SectionTitleBucket,
    _StyleSection as _StyleSection,
)
from prism.scanner_data.contracts_variables import (
    ReferenceContext as ReferenceContext,
    Variable as Variable,
    VariableProvenance as VariableProvenance,
    VariableRow as VariableRow,
    VariableRowBuilder as VariableRowBuilder,
    VariableRowWithMeta as VariableRowWithMeta,
)


# Protocols for DI pluggability
class DataLoaderProtocol(Protocol):
    """Protocol for data loading operations."""

    def iter_role_argument_spec_entries(
        self,
        role_path: str,
        load_yaml_file_fn: Callable[[Path], object],
        load_meta_fn: Callable[[str], dict],
    ) -> Any: ...

    def load_role_variable_maps(
        self,
        role_path: str,
        include_vars_main: bool,
        iter_variable_map_candidates_fn: Callable[[Path, str], list[Path]],
        load_yaml_file_fn: Callable[[Path], object],
    ) -> tuple[dict, dict, dict[str, Path], dict[str, Path]]: ...

    def map_argument_spec_type(self, spec_entry: dict[str, Any]) -> str: ...


class DiscoveryProtocol(Protocol):
    """Protocol for discovery operations."""

    def iter_role_variable_map_candidates(
        self, role_root: Path, subdir: str
    ) -> list[Path]: ...


class TaskParserProtocol(Protocol):
    """Protocol for task parsing operations."""

    def _format_inline_yaml(self, value: object) -> str: ...

    def _load_yaml_file(self, file_path: Path) -> object | None: ...

    def _collect_task_files(
        self, role_path: str, exclude_patterns: list[str] | None = None
    ) -> list[Path]: ...

    def _iter_task_include_targets(self, data: object) -> list[str]: ...

    def _iter_task_mappings(self, data: object) -> Any: ...

    def _iter_role_include_targets(
        self, role_path: str, load_yaml_file_fn: Callable[[Path], object]
    ) -> Any: ...

    def _iter_dynamic_role_include_targets(
        self, role_path: str, load_yaml_file_fn: Callable[[Path], object]
    ) -> Any: ...

    def _detect_task_module(self, task: dict[str, Any]) -> str | None: ...

    def _extract_collection_from_module_name(self, module_name: str) -> str | None: ...

    def _extract_task_annotations_for_file(
        self, file_path: Path, load_yaml_file_fn: Callable[[Path], object]
    ) -> dict[str, Any]: ...


class VariableExtractorProtocol(Protocol):
    """Protocol for variable extraction operations."""

    def _collect_referenced_variable_names(self, content: str) -> set[str]: ...

    def _collect_set_fact_names(self, content: str) -> set[str]: ...

    def _find_variable_line_in_yaml(
        self, file_path: Path, var_name: str
    ) -> int | None: ...

    def _infer_variable_type(self, value: object) -> str: ...

    def _is_sensitive_variable(self, variable_name: str) -> bool: ...


__all__ = [
    "AnnotationQualityCounters",
    "CollectionScanResult",
    "DataLoaderProtocol",
    "DiscoveryProtocol",
    "EmitScanOutputsArgs",
    "FailureDetail",
    "FailurePolicyContract",
    "FeaturesContext",
    "FinalOutputPayload",
    "NormalizedScannerReportMetadata",
    "OutputConfiguration",
    "PluginCatalog",
    "PluginCatalogSummary",
    "PluginExtraction",
    "PluginRecord",
    "PluginScanFailure",
    "ReadmeSectionRenderInput",
    "ReferenceContext",
    "RepoScanResult",
    "ReportRenderingMetadata",
    "RoleScanResult",
    "RunbookSidecarPayload",
    "RunbookSidecarArgs",
    "RunScanOutputPayload",
    "ScanRenderPayload",
    "ScanBaseContext",
    "ScanContext",
    "ScanContextPayload",
    "ScanMetadata",
    "ScanOptionsDict",
    "ScanPhaseError",
    "ScanPhaseStatus",
    "ScanReportSidecarArgs",
    "ScannerCounters",
    "ScannerReportIssueListRow",
    "ScannerReportMetadata",
    "ScannerReportSectionRenderInput",
    "ScannerReportYamlParseFailureRow",
    "ScanPayloadBuilder",
    "SectionBodyRenderResult",
    "StyleGuideConfig",
    "TaskParserProtocol",
    "Variable",
    "VariableAnalysisResults",
    "VariableExtractorProtocol",
    "VariableProvenance",
    "VariableRow",
    "VariableRowBuilder",
    "VariableRowWithMeta",
    "_SectionTitleBucket",
    "_StyleSection",
]
