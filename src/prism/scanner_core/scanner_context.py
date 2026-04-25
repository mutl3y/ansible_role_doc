"""Minimal scanner-context orchestrator for the fsrc package lane."""

from __future__ import annotations

from copy import deepcopy
import logging
from typing import Any, Callable, cast

from prism.errors import PrismRuntimeError
from prism.scanner_core.metadata_merger import merge_policy_warning_entries
from prism.scanner_data.contracts_request import ScanContextPayload, ScanOptionsDict
from prism.scanner_data.contracts_request import ScanPolicyBlockerFacts
from prism.scanner_core.execution_request_builder import (
    NonCollectionRunScanExecutionRequest,
    build_non_collection_run_scan_execution_request,
)
from prism.scanner_core.filters.underscore_policy import (
    apply_underscore_reference_filter,
)

_REQUIRED_SCAN_OPTION_KEYS: frozenset[str] = frozenset(
    {
        "role_path",
        "role_name_override",
        "readme_config_path",
        "include_vars_main",
        "exclude_path_patterns",
        "detailed_catalog",
        "include_task_parameters",
        "include_task_runbooks",
        "inline_task_runbooks",
        "include_collection_checks",
        "keep_unknown_style_sections",
        "adopt_heading_mode",
        "vars_seed_paths",
        "style_readme_path",
        "style_source_path",
        "style_guide_skeleton",
        "compare_role_path",
        "fail_on_unconstrained_dynamic_includes",
        "fail_on_yaml_like_task_annotations",
        "ignore_unresolved_internal_underscore_references",
    }
)

_RECOVERABLE_PHASE_ERRORS: tuple[type[Exception], ...] = (PrismRuntimeError,)


def _require_prepared_policy_bundle(
    scan_options: ScanOptionsDict,
) -> dict[str, Any]:
    prepared_policy_bundle = scan_options.get("prepared_policy_bundle")
    if not isinstance(prepared_policy_bundle, dict):
        raise ValueError(
            "scan_options must include a prepared_policy_bundle before "
            "ScannerContext orchestration"
        )

    task_line_policy = prepared_policy_bundle.get("task_line_parsing")
    if task_line_policy is None:
        raise ValueError(
            "prepared_policy_bundle.task_line_parsing must be provided before "
            "ScannerContext orchestration"
        )

    jinja_analysis_policy = prepared_policy_bundle.get("jinja_analysis")
    if jinja_analysis_policy is None:
        raise ValueError(
            "prepared_policy_bundle.jinja_analysis must be provided before "
            "ScannerContext orchestration"
        )

    return cast(dict[str, Any], prepared_policy_bundle)


__all__ = [
    "NonCollectionRunScanExecutionRequest",
    "ScannerContext",
    "build_non_collection_run_scan_execution_request",
]


class ScannerContext:
    """Coordinate variable discovery, feature detection, and payload shaping."""

    def __init__(
        self,
        *,
        di: Any,
        role_path: str,
        scan_options: ScanOptionsDict,
        build_run_scan_options_fn: Callable[..., ScanOptionsDict] | None = None,
        prepare_scan_context_fn: (
            Callable[[ScanOptionsDict], ScanContextPayload] | None
        ) = None,
    ) -> None:
        if di is None:
            raise ValueError("di (DIContainer) must not be None")
        if not role_path:
            raise ValueError("role_path must not be empty")
        if scan_options is None:
            raise ValueError("scan_options must not be None")

        self._di = di
        self._role_path = role_path
        self._scan_options = scan_options
        self._prepare_scan_context_fn = prepare_scan_context_fn
        self._strict_phase_failures = bool(
            self._scan_options.get("strict_phase_failures", True)
        )

        self._discovered_variables: tuple[Any, ...] = ()
        self._detected_features: dict[str, Any] = {}
        self._scan_metadata: dict[str, Any] = {}
        self._scan_errors: list[dict[str, str]] = []

    def orchestrate_scan(self) -> dict[str, Any]:
        self._discovered_variables = ()
        self._detected_features = {}
        self._scan_metadata = {}
        self._scan_errors = []

        _require_prepared_policy_bundle(self._scan_options)

        self._discovered_variables = self._discover_variables()
        self._detected_features = self._detect_features()

        return self._build_output_payload()

    def _record_phase_error(self, phase: str, error: Exception) -> dict[str, str]:
        entry = {
            "phase": phase,
            "error_type": error.__class__.__name__,
            "message": str(error),
        }
        self._scan_errors.append(entry)
        self._scan_metadata = {
            "scan_errors": list(self._scan_errors),
            "scan_degraded": True,
        }
        return entry

    def _discover_variables(self) -> tuple[Any, ...]:
        try:
            discovery = self._di.factory_variable_discovery()
            return discovery.discover()
        except Exception as error:
            logger = logging.getLogger(__name__)
            if self._strict_phase_failures or not isinstance(
                error,
                _RECOVERABLE_PHASE_ERRORS,
            ):
                logger.error("Variable discovery failed")
                raise
            entry = self._record_phase_error("discovery", error)
            logger.error(
                "Variable discovery failed; continuing in best-effort mode",
                extra={"scan_error": entry},
            )
            return ()

    def _detect_features(self) -> dict[str, Any]:
        try:
            detector = self._di.factory_feature_detector()
            return detector.detect()
        except Exception as error:
            logger = logging.getLogger(__name__)
            if self._strict_phase_failures or not isinstance(
                error,
                _RECOVERABLE_PHASE_ERRORS,
            ):
                logger.error("Feature detection failed")
                raise
            entry = self._record_phase_error("feature_detection", error)
            logger.error(
                "Feature detection failed; continuing in best-effort mode",
                extra={"scan_error": entry},
            )
            return {"task_files_scanned": 0, "tasks_scanned": 0}

    def _build_output_payload(self) -> dict[str, Any]:
        self._validate_required_scan_option_keys()
        context_payload = self._build_context_payload()
        metadata = dict(context_payload.get("metadata") or {})
        self._merge_features_into_metadata(metadata)
        self._merge_policy_warnings_into_metadata(metadata)
        display_variables = self._apply_underscore_reference_policy(
            scan_options=self._scan_options,
            metadata=metadata,
            display_variables=dict(context_payload.get("display_variables") or {}),
        )
        metadata["scan_policy_blocker_facts"] = self._build_scan_policy_blocker_facts(
            scan_options=self._scan_options,
            metadata=metadata,
        )
        self._record_scan_errors_into_metadata(metadata)
        self._scan_metadata = metadata

        return {
            "role_name": context_payload["role_name"],
            "description": context_payload["description"],
            "display_variables": display_variables,
            "requirements_display": list(context_payload["requirements_display"]),
            "undocumented_default_filters": list(
                context_payload["undocumented_default_filters"]
            ),
            "metadata": metadata,
        }

    def _validate_required_scan_option_keys(self) -> None:
        missing_keys = sorted(
            key for key in _REQUIRED_SCAN_OPTION_KEYS if key not in self._scan_options
        )
        if missing_keys:
            raise ValueError(
                "scan_options missing required canonical keys: "
                + ", ".join(missing_keys)
            )

    def _build_context_payload(self) -> ScanContextPayload:
        if self._prepare_scan_context_fn is None:
            raise ValueError(
                "prepare_scan_context_fn must be provided for canonical "
                "ScannerContext orchestration"
            )
        return self._prepare_scan_context_fn(self._scan_options)

    def _merge_features_into_metadata(self, metadata: dict[str, Any]) -> None:
        if "features" not in metadata and self._detected_features:
            metadata["features"] = dict(self._detected_features)

    def _merge_policy_warnings_into_metadata(self, metadata: dict[str, Any]) -> None:
        policy_warning_list = merge_policy_warning_entries(
            self._scan_options.get("scan_policy_warnings"),
            metadata.get("scan_policy_warnings"),
        )
        if policy_warning_list:
            metadata["scan_policy_warnings"] = policy_warning_list

    def _record_scan_errors_into_metadata(self, metadata: dict[str, Any]) -> None:
        if self._scan_errors:
            metadata["scan_errors"] = list(self._scan_errors)
            metadata["scan_degraded"] = True

    def _build_scan_policy_blocker_facts(
        self,
        *,
        scan_options: ScanOptionsDict,
        metadata: dict[str, Any],
    ) -> ScanPolicyBlockerFacts:
        builder_fn = self._di.factory_blocker_fact_builder()
        return builder_fn(
            scan_options=scan_options,
            metadata=metadata,
            di=self._di,
        )

    def _apply_underscore_reference_policy(
        self,
        *,
        scan_options: ScanOptionsDict,
        metadata: dict[str, Any],
        display_variables: dict[str, Any],
    ) -> dict[str, Any]:
        return apply_underscore_reference_filter(
            display_variables=display_variables,
            metadata=metadata,
            ignore_flag=bool(
                scan_options.get("ignore_unresolved_internal_underscore_references")
            ),
        )

    @property
    def discovered_variables(self) -> tuple[Any, ...]:
        return self._discovered_variables

    @property
    def detected_features(self) -> dict[str, Any]:
        return deepcopy(self._detected_features)

    @property
    def scan_metadata(self) -> dict[str, Any]:
        return deepcopy(self._scan_metadata)
