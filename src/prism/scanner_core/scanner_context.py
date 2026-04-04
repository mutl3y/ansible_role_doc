"""Scanner orchestrator: main entry point coordinating all scan phases.

This module provides ScannerContext, the primary orchestrator that coordinates
the complete scanner workflow: variable discovery → feature detection → output
orchestration.

ScannerContext replaces the procedural body of scanner.py:run_scan() with a
clean, testable class that owns orchestration logic while delegating to
specialized orchestrators (VariableDiscovery, OutputOrchestrator, FeatureDetector).
"""

from __future__ import annotations

import inspect
import traceback
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from opentelemetry import trace
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from prism.errors import PrismRuntimeError
from prism.scanner_data.contracts_request import ScanContextPayload, ScanOptionsDict
from prism.scanner_core import scan_request
from prism.scanner_core.di import DIContainer
from prism.scanner_core.logging_config import set_scan_context
from prism.scanner_io.loader import load_readme_content


_REQUIRED_SCAN_OPTION_KEYS: set[str] = {
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

_RECOVERABLE_PHASE_ERRORS: tuple[type[Exception], ...] = (PrismRuntimeError,)


def _prepare_scan_context_compat(
    prepare_scan_context_fn: Callable[..., ScanContextPayload],
    normalized_scan_options: ScanOptionsDict,
    di: DIContainer,
) -> ScanContextPayload:
    """Invoke prepare_scan_context callback with legacy/modern compatibility.

    Supports both callback signatures:
    1) callback(scan_options)
    2) callback(scan_options, di_container=...)
    """
    try:
        signature = inspect.signature(prepare_scan_context_fn)
    except (TypeError, ValueError):
        signature = None

    if signature is not None:
        parameters = signature.parameters
        if "di_container" in parameters or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        ):
            return prepare_scan_context_fn(
                normalized_scan_options,
                di_container=di,
            )
        return prepare_scan_context_fn(normalized_scan_options)

    # Fallback for callables without introspectable signatures.
    try:
        return prepare_scan_context_fn(normalized_scan_options, di_container=di)
    except TypeError as error:
        if "di_container" not in str(error):
            raise
        return prepare_scan_context_fn(normalized_scan_options)


class ScannerContext:
    """Main orchestrator for role scanning.

    Orchestrates the complete scan process:
    1. VariableDiscovery: discover all variables (static + referenced)
    2. FeatureDetector: analyze role features (tasks, handlers, collections)
    3. OutputOrchestrator: render and emit outputs (README, JSON, sidecar reports)

    Maintains immutable data contracts throughout. Uses immutable tuples
    and frozensets for discovered data; transforms to lists only at boundaries (JSON, etc).

    **Design Rationale:**
    - Encapsulates procedural orchestration logic into a cohesive class
    - Enables testable dependency injection for phase orchestrators
    - Maintains immutable data flow: discover → detect → output
    - Operates at higher abstraction than scanner.py internals
    - Delegates to specialized orchestrators (wave 2+)
    """

    def __init__(
        self,
        di: DIContainer,
        role_path: str,
        scan_options: ScanOptionsDict,
        build_run_scan_options_fn: Callable[..., ScanOptionsDict] | None = None,
        prepare_scan_context_fn: Callable[..., ScanContextPayload] | None = None,
    ) -> None:
        """Initialize context with DI container and scan options.

        Args:
            di: DIContainer instance providing orchestrator factories.
            role_path: Absolute or relative path to Ansible role directory.
            scan_options: Normalized scan configuration dict from build_run_scan_options_canonical().
                         Must include keys like role_name_override, include_vars_main, etc.

        Raises:
            ValueError: If di is None, role_path is empty, or scan_options is None.
        """
        if di is None:
            raise ValueError("di (DIContainer) must not be None")
        if not role_path:
            raise ValueError("role_path must not be empty")
        if scan_options is None:
            raise ValueError("scan_options must not be None")

        self._di = di
        self._role_path = role_path
        self._scan_options = scan_options
        self._build_run_scan_options_fn = (
            build_run_scan_options_fn or scan_request.build_run_scan_options_canonical
        )
        self._prepare_scan_context_fn = (
            prepare_scan_context_fn or scan_request.prepare_scan_context_canonical
        )
        self._strict_phase_failures = bool(
            self._scan_options.get("strict_phase_failures", True)
        )

        # Metrics collector for performance and error tracking
        self._metrics = self._di.factory_metrics_collector()
        self._logger_factory = self._di.factory_logger_factory()
        self._logger = self._logger_factory.get_logger(__name__)

        # Internal state: discovered variables and features stored as immutable tuples/dicts
        self._discovered_variables: tuple[Any, ...] = ()
        self._detected_features: dict[str, Any] = {}
        self._scan_metadata: dict[str, Any] = {}
        self._scan_errors: list[dict[str, str]] = []

    def orchestrate_scan(self) -> dict[str, Any]:
        """Execute complete scan orchestration: discover → detect → emit.

        Orchestration phases:
        1. **Discovery Phase**: Use VariableDiscovery to find all variables
           (static from defaults/vars + referenced from tasks/handlers/templates).
           Result: discovered_variables: tuple[VariableRow, ...] (immutable)
        2. **Detection Phase**: Use FeatureDetector to analyze role features
           (task count, modules used, handlers, collections, etc.).
           Result: detected_features: dict[str, Any] (FeaturesContext)
        3. **Output Phase**: Use OutputOrchestrator to render outputs
           (README, JSON report, sidecar reports). Result: final payload.

        **Immutability Contract:**
        - discovered_variables stored as immutable tuple[VariableRow, ...]
        - detected_features stored as immutable dict[str, Any]
        - payload built via ScanPayloadBuilder (immutable typed dict)
        - No mutations to discovered data after discovery phase completes

                **Error Handling:**
                - Core phase failures raise by default (strict behavior).
                - Optional best-effort mode (strict_phase_failures=False) records
                    structured scan_errors metadata and continues with degraded output.

        Returns:
            dict[str, Any]: RunScanOutputPayload-compatible dict with:
                - role_name: str
                - description: str
                - display_variables: dict[str, Any]
                - requirements_display: list[Any]
                - undocumented_default_filters: list[Any]
                - metadata: ScanMetadata

        Raises:
            ValueError: If orchestration encounters unrecoverable errors
                        (e.g., invalid role structure).
        """
        enforce_role_path_exists = bool(
            self._scan_options.get("enforce_role_path_exists", False)
        ) or (
            self._prepare_scan_context_fn is scan_request.prepare_scan_context_canonical
        )

        role_path = Path(self._role_path)
        if enforce_role_path_exists and (
            not role_path.exists() or not role_path.is_dir()
        ):
            raise FileNotFoundError(f"role path not found: {self._role_path}")

        self._discovered_variables = ()
        self._detected_features = {}
        self._scan_metadata = {}
        self._scan_errors = []

        # Set scan context for logging
        role_name = self._scan_options.get("role_name", "unknown")
        scan_id = f"scan_{id(self)}"
        with set_scan_context(role_name=role_name, scan_id=scan_id):
            # Start metrics collection
            self._metrics.start_scan()

            phase_tracer = trace.get_tracer(__name__)

            # Phase 1: Variable Discovery (returns immutable tuple)
            with self._start_phase_span(phase_tracer, "variable_discovery") as span:
                span.set_attribute("phase", "discovery")
                span.set_attribute("role_name", role_name)
                self._discovered_variables = self._discover_variables()

            # Phase 2: Feature Detection (returns immutable dict)
            with self._start_phase_span(phase_tracer, "feature_detection") as span:
                span.set_attribute("phase", "detection")
                span.set_attribute("role_name", role_name)
                self._detected_features = self._detect_features()

            # Phase 3: Output Orchestration & Payload Building
            with self._start_phase_span(phase_tracer, "output_orchestration") as span:
                span.set_attribute("phase", "output")
                span.set_attribute("role_name", role_name)
                payload = self._build_output_payload()

        # End metrics collection
        self._metrics.end_scan()

        return payload

    @contextmanager
    def _start_phase_span(self, phase_tracer: Any, span_name: str):
        """Start a span across tracer API variants.

        Prefer start_as_span when available; otherwise emulate it via start_span.
        """
        start_as_span = getattr(phase_tracer, "start_as_span", None)
        if callable(start_as_span):
            with start_as_span(span_name) as span:
                yield span
            return

        span = phase_tracer.start_span(span_name)
        try:
            yield span
        finally:
            end = getattr(span, "end", None)
            if callable(end):
                end()

    def _record_phase_error(self, phase: str, error: Exception) -> dict[str, str]:
        """Record a structured phase failure entry for metadata propagation."""
        entry = {
            "phase": phase,
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        self._scan_errors.append(entry)
        self._scan_metadata = {
            "scan_errors": list(self._scan_errors),
            "scan_degraded": True,
        }
        # Record error in metrics
        self._metrics.record_error(f"{phase}_error")
        return entry

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_RECOVERABLE_PHASE_ERRORS),
        reraise=False,
    )
    def _discover_variables(self) -> tuple[Any, ...]:
        """Execute variable discovery phase.

        Delegates to VariableDiscovery to find all variables.
        Returns immutable tuple of VariableRow.

        **Phase Contract:**
        - Input: role_path, scan_options
        - Output: tuple[VariableRow, ...] (immutable - no mutations after return)
        - Error: catch, log, return empty tuple

        Returns:
            tuple[Any, ...]: Discovered variables (immutable collection).
        """
        try:
            factory = getattr(self._di, "factory_variable_discovery", None)
            if callable(factory):
                discovery = factory()
                discover = getattr(discovery, "discover", None)
                if callable(discover):
                    return tuple(discover())

            plugin_factory = getattr(
                self._di, "factory_variable_discovery_plugin", None
            )
            if callable(plugin_factory):
                plugin = plugin_factory()
                static_vars = plugin.discover_static_variables(
                    self._role_path, self._scan_options
                )
                readme_content = load_readme_content(self._role_path)
                referenced_vars = plugin.discover_referenced_variables(
                    self._role_path,
                    self._scan_options,
                    readme_content,
                )
                plugin.resolve_unresolved_variables(
                    frozenset(v["name"] for v in static_vars),
                    referenced_vars,
                    self._scan_options,
                )
                return tuple(static_vars)

            raise AttributeError(
                "DIContainer does not provide variable discovery factory"
            )
        except Exception as e:
            if self._strict_phase_failures or not isinstance(
                e,
                _RECOVERABLE_PHASE_ERRORS,
            ):
                self._logger.error(
                    "Variable discovery failed",
                    extra={"operation": "variable_discovery", "phase": "discovery"},
                )
                raise
            entry = self._record_phase_error("discovery", e)
            self._logger.error(
                "Variable discovery failed; continuing in best-effort mode",
                extra={
                    "scan_error": entry,
                    "operation": "variable_discovery",
                    "phase": "discovery",
                },
            )
            return ()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_RECOVERABLE_PHASE_ERRORS),
        reraise=False,
    )
    def _detect_features(self) -> dict[str, Any]:
        """Execute feature detection phase.

        Delegates to FeatureDetector to analyze role structure and features.
        Returns immutable dict of features.

        **Phase Contract:**
        - Input: role_path, scan_options, discovered_variables
        - Output: dict[str, Any] (FeaturesContext - treat as immutable)
        - Error: catch, log, return minimal features dict

        Returns:
            dict[str, Any]: Detected features (immutable dict).
        """
        try:
            factory = getattr(self._di, "factory_feature_detector", None)
            if callable(factory):
                detector = factory()
                detect = getattr(detector, "detect", None)
                if callable(detect):
                    return dict(detect())

            plugin_factory = getattr(self._di, "factory_feature_detection_plugin", None)
            if callable(plugin_factory):
                plugin = plugin_factory()
                return dict(plugin.detect_features(self._role_path, self._scan_options))

            raise AttributeError(
                "DIContainer does not provide feature detection factory"
            )
        except Exception as e:
            if self._strict_phase_failures or not isinstance(
                e,
                _RECOVERABLE_PHASE_ERRORS,
            ):
                self._logger.error(
                    "Feature detection failed",
                    extra={"operation": "feature_detection", "phase": "detection"},
                )
                raise
            entry = self._record_phase_error("feature_detection", e)
            self._logger.error(
                "Feature detection failed; continuing in best-effort mode",
                extra={
                    "scan_error": entry,
                    "operation": "feature_detection",
                    "phase": "detection",
                },
            )
            return {
                "task_files_scanned": 0,
                "tasks_scanned": 0,
                "recursive_task_includes": 0,
                "unique_modules": "none",
                "external_collections": "none",
                "handlers_notified": "none",
                "privileged_tasks": 0,
                "conditional_tasks": 0,
                "tagged_tasks": 0,
                "included_role_calls": 0,
                "included_roles": "none",
                "dynamic_included_role_calls": 0,
                "dynamic_included_roles": "none",
                "disabled_task_annotations": 0,
                "yaml_like_task_annotations": 0,
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_RECOVERABLE_PHASE_ERRORS),
        reraise=False,
    )
    def _build_output_payload(self) -> dict[str, Any]:
        """Build final RunScanOutputPayload from orchestration results.

        Assembles the output payload from phases 1 & 2, delegating rendering
        to OutputOrchestrator. This payload is used by scanner.py:run_scan()
        to emit final outputs.

        **Immutability Note:**
        - Discovered variables are converted from tuple to list for JSON serialization
        - Payload is built via ScanPayloadBuilder for immutability
        - All transformations create new structures (no mutations)

        **Payload Contract (RunScanOutputPayload):**
        - role_name: str
        - description: str
        - display_variables: dict[str, Any]
        - requirements_display: list[Any]
        - undocumented_default_filters: list[Any]
        - metadata: ScanMetadata

        Returns:
            dict[str, Any]: Payload ready for output emission (immutable from perspective of caller).
        """
        missing_keys = sorted(
            key for key in _REQUIRED_SCAN_OPTION_KEYS if key not in self._scan_options
        )
        if missing_keys:
            raise ValueError(
                "scan_options missing required canonical keys: "
                + ", ".join(missing_keys)
            )

        normalized_scan_options = self._build_run_scan_options_fn(
            role_path=str(self._scan_options.get("role_path") or self._role_path),
            role_name_override=self._scan_options.get("role_name_override"),
            readme_config_path=self._scan_options.get("readme_config_path"),
            include_vars_main=bool(self._scan_options.get("include_vars_main", True)),
            exclude_path_patterns=self._scan_options.get("exclude_path_patterns"),
            detailed_catalog=bool(self._scan_options.get("detailed_catalog", False)),
            include_task_parameters=bool(
                self._scan_options.get("include_task_parameters", True)
            ),
            include_task_runbooks=bool(
                self._scan_options.get("include_task_runbooks", True)
            ),
            inline_task_runbooks=bool(
                self._scan_options.get("inline_task_runbooks", True)
            ),
            include_collection_checks=bool(
                self._scan_options.get("include_collection_checks", True)
            ),
            keep_unknown_style_sections=bool(
                self._scan_options.get("keep_unknown_style_sections", True)
            ),
            adopt_heading_mode=self._scan_options.get("adopt_heading_mode"),
            vars_seed_paths=self._scan_options.get("vars_seed_paths"),
            style_readme_path=self._scan_options.get("style_readme_path"),
            style_source_path=self._scan_options.get("style_source_path"),
            style_guide_skeleton=bool(
                self._scan_options.get("style_guide_skeleton", False)
            ),
            compare_role_path=self._scan_options.get("compare_role_path"),
            fail_on_unconstrained_dynamic_includes=self._scan_options.get(
                "fail_on_unconstrained_dynamic_includes"
            ),
            fail_on_yaml_like_task_annotations=self._scan_options.get(
                "fail_on_yaml_like_task_annotations"
            ),
            ignore_unresolved_internal_underscore_references=self._scan_options.get(
                "ignore_unresolved_internal_underscore_references"
            ),
            policy_context=self._scan_options.get("policy_context"),
        )

        if self._prepare_scan_context_fn is None:
            raise ValueError(
                "prepare_scan_context_fn must be provided for canonical ScannerContext orchestration"
            )

        try:
            context_payload = _prepare_scan_context_compat(
                self._prepare_scan_context_fn,
                normalized_scan_options,
                self._di,
            )
        except Exception as e:
            if self._strict_phase_failures or not isinstance(
                e,
                _RECOVERABLE_PHASE_ERRORS,
            ):
                self._logger.error(
                    "Output payload building failed",
                    extra={"operation": "output_payload_building", "phase": "output"},
                )
                raise
            entry = self._record_phase_error("output", e)
            self._logger.error(
                "Output payload building failed; returning degraded payload",
                extra={
                    "scan_error": entry,
                    "operation": "output_payload_building",
                    "phase": "output",
                },
            )
            # Return degraded payload with minimal valid structure
            degraded_metadata = dict(self._scan_metadata)
            if self._scan_errors:
                degraded_metadata["scan_errors"] = list(self._scan_errors)
                degraded_metadata["scan_degraded"] = True
            degraded_metadata["metrics"] = self._metrics.get_metrics()
            return {
                "role_name": "unknown",
                "description": "",
                "display_variables": {},
                "requirements_display": [],
                "undocumented_default_filters": [],
                "metadata": degraded_metadata,
            }

        metadata = dict(context_payload.get("metadata") or {})
        if "features" not in metadata and self._detected_features:
            metadata["features"] = dict(self._detected_features)
        if self._scan_errors:
            metadata["scan_errors"] = list(self._scan_errors)
            metadata["scan_degraded"] = True
        # Add metrics to metadata
        metadata["metrics"] = self._metrics.get_metrics()
        self._scan_metadata = metadata

        return {
            "role_name": context_payload["role_name"],
            "description": context_payload["description"],
            "display_variables": dict(context_payload.get("display_variables") or {}),
            "requirements_display": list(context_payload["requirements_display"]),
            "undocumented_default_filters": list(
                context_payload["undocumented_default_filters"]
            ),
            "metadata": metadata,
        }

    @property
    def discovered_variables(self) -> tuple[Any, ...]:
        """Variables discovered during scan (static + referenced).

        Immutable tuple. Updated only by orchestrate_scan().

        Returns:
            tuple[Any, ...]: Variables discovered in phase 1 (variable discovery).
                             Immutable after discovery phase completes.
        """
        return self._discovered_variables

    @property
    def detected_features(self) -> dict[str, Any]:
        """Features detected during scan (tasks, handlers, collections, etc.).

        Immutable dict from caller perspective. Updated only by orchestrate_scan().

        Returns:
            dict[str, Any]: Features detected in phase 2 (feature detection).
                            Type: FeaturesContext when fully populated.
        """
        return deepcopy(self._detected_features)

    @property
    def scan_metadata(self) -> dict[str, Any]:
        """Scan metadata (role name, repository, scanning timestamp, etc.).

        Immutable from caller perspective. Updated throughout orchestration.

        Returns:
            dict[str, Any]: Metadata dict flowing through all phases.
                            Type: ScanMetadata when fully populated.
        """
        return deepcopy(self._scan_metadata)
