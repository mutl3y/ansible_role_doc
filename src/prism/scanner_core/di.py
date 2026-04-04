"""Hand-crafted Dependency Injection container for scanner orchestrators."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from prism.scanner_core.extension_registry import ExtensionRegistry
    from prism.scanner_core.feature_detector import FeatureDetector
    from prism.scanner_core.output_orchestrator import OutputOrchestrator
    from prism.scanner_core.scanner_context import ScannerContext
    from prism.scanner_core.variable_discovery import VariableDiscovery
    from prism.scanner_data.builders import VariableRowBuilder


@dataclass
class WiringSpec:
    """Specification for wiring a service in the DI container."""

    factory: Callable[..., Any]
    lifecycle: str  # singleton | transient
    dependencies: list[str]


class DIContainer:
    """Lightweight DI container for scanner orchestrators."""

    def __init__(
        self,
        role_path: str,
        scan_options: dict[str, Any],
        *,
        scanner_context_wiring: dict[str, Any] | None = None,
        factory_overrides: dict[str, Callable[..., Any]] | None = None,
        wiring_registry: dict[str, WiringSpec | dict[str, Any]] | None = None,
    ) -> None:
        if not role_path:
            raise ValueError("role_path must not be empty")
        if scan_options is None:
            raise ValueError("scan_options must not be None")

        self._role_path = role_path
        self._scan_options = scan_options
        self._cache: dict[str, Any] = {}
        self._mocks: dict[str, Any] = {}
        self._building: set[str] = set()
        self._scanner_context_wiring = scanner_context_wiring or {}
        self._factory_overrides = factory_overrides or {}

        base_registry = wiring_registry or self._build_default_wiring_registry()
        self._wiring_registry = self._normalize_wiring_registry(base_registry)

    def _normalize_wiring_registry(
        self,
        registry: dict[str, WiringSpec | dict[str, Any]],
    ) -> dict[str, WiringSpec]:
        normalized: dict[str, WiringSpec] = {}
        for name, spec in registry.items():
            if isinstance(spec, WiringSpec):
                normalized[name] = spec
                continue
            normalized[name] = WiringSpec(
                factory=spec["factory"],
                lifecycle=str(spec.get("lifecycle", "singleton")),
                dependencies=list(spec.get("dependencies", [])),
            )
        return normalized

    def _build_default_wiring_registry(self) -> dict[str, WiringSpec]:
        return {
            "variable_discovery": WiringSpec(
                factory=self._create_variable_discovery,
                lifecycle="singleton",
                dependencies=[],
            ),
            "feature_detector": WiringSpec(
                factory=self._create_feature_detector,
                lifecycle="singleton",
                dependencies=[],
            ),
            "variable_row_builder": WiringSpec(
                factory=self._create_variable_row_builder,
                lifecycle="singleton",
                dependencies=[],
            ),
            "logger_factory": WiringSpec(
                factory=self._create_logger_factory,
                lifecycle="singleton",
                dependencies=[],
            ),
            "metrics_collector": WiringSpec(
                factory=self._create_metrics_collector,
                lifecycle="singleton",
                dependencies=[],
            ),
            "extension_registry": WiringSpec(
                factory=self._create_extension_registry,
                lifecycle="singleton",
                dependencies=[],
            ),
        }

    def _invoke_factory(self, factory: Callable[..., Any], deps: list[Any]) -> Any:
        """Invoke a wiring factory with deps and optional DI self binding."""
        try:
            signature = inspect.signature(factory)
            positional_params = [
                p
                for p in signature.parameters.values()
                if p.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
            if len(positional_params) == len(deps) + 1:
                return factory(self, *deps)
            return factory(*deps)
        except (TypeError, ValueError):
            return factory(*deps)

    def _resolve(self, service_name: str) -> Any:
        """Resolve a service from the wiring registry with cycle detection."""
        if service_name in self._building:
            raise RuntimeError(f"Cycle detected in DI container: {service_name}")

        self._building.add(service_name)
        try:
            if service_name in self._mocks:
                return self._mocks[service_name]

            spec = self._wiring_registry.get(service_name)
            if spec is None:
                raise ValueError(
                    f"Service '{service_name}' not found in wiring registry"
                )

            if spec.lifecycle == "singleton" and service_name in self._cache:
                return self._cache[service_name]

            deps = [self._resolve(dep) for dep in spec.dependencies]
            instance = self._invoke_factory(spec.factory, deps)

            if spec.lifecycle == "singleton":
                self._cache[service_name] = instance

            return instance
        finally:
            self._building.discard(service_name)

    def _create_variable_discovery(self) -> VariableDiscovery:
        override = self._factory_overrides.get("variable_discovery_factory")
        if override is not None:
            return override(self, self._role_path, self._scan_options)

        from prism.scanner_core.variable_discovery import VariableDiscovery

        return VariableDiscovery(self, self._role_path, self._scan_options)

    def _create_feature_detector(self) -> FeatureDetector:
        override = self._factory_overrides.get("feature_detector_factory")
        if override is not None:
            return override(self, self._role_path, self._scan_options)

        from prism.scanner_core.feature_detector import FeatureDetector

        return FeatureDetector(self, self._role_path, self._scan_options)

    def _create_variable_row_builder(self) -> VariableRowBuilder:
        from prism.scanner_data.builders import VariableRowBuilder

        return VariableRowBuilder()

    def _create_logger_factory(self) -> Any:
        from prism.scanner_core.logging_config import LoggerFactory

        return LoggerFactory()

    def _create_metrics_collector(self) -> Any:
        from prism.scanner_core.metrics_collector import MetricsCollector

        return MetricsCollector()

    def _create_extension_registry(self) -> ExtensionRegistry:
        from prism.scanner_core.extension_registry import ExtensionRegistry

        return ExtensionRegistry()

    def factory_scanner_context(self) -> ScannerContext:
        scanner_context_cls = self._scanner_context_wiring.get("scanner_context_cls")
        prepare_scan_context_fn = self._scanner_context_wiring.get(
            "prepare_scan_context_fn"
        )
        if scanner_context_cls is None or prepare_scan_context_fn is None:
            raise RuntimeError(
                "factory_scanner_context is disabled: scanner_context_wiring is "
                "not configured. ScannerContext requires prepare_scan_context_fn "
                "runtime seam injection."
            )

        return scanner_context_cls(
            di=self,
            role_path=self._role_path,
            scan_options=self._scan_options,
            prepare_scan_context_fn=prepare_scan_context_fn,
        )

    def factory_variable_discovery(self) -> VariableDiscovery:
        return self._resolve("variable_discovery")

    def factory_feature_detector(self) -> FeatureDetector:
        return self._resolve("feature_detector")

    def factory_variable_row_builder(self) -> VariableRowBuilder:
        return self._resolve("variable_row_builder")

    def factory_logger_factory(self) -> Any:
        return self._resolve("logger_factory")

    def factory_metrics_collector(self) -> Any:
        return self._resolve("metrics_collector")

    def factory_extension_registry(self) -> ExtensionRegistry:
        return self._resolve("extension_registry")

    def factory_output_orchestrator(self, output_path: str) -> OutputOrchestrator:
        cache_key = f"output_orchestrator:{output_path}"
        if cache_key not in self._cache:
            from prism.scanner_core.output_orchestrator import OutputOrchestrator

            self._cache[cache_key] = OutputOrchestrator(
                di=self,
                output_path=output_path,
                options=self._scan_options,
            )
        return self._cache[cache_key]

    def inject_mock_variable_discovery(self, mock: Any) -> None:
        self._mocks["variable_discovery"] = mock

    def inject_mock_feature_detector(self, mock: Any) -> None:
        self._mocks["feature_detector"] = mock

    def clear_mocks(self) -> None:
        self._mocks.clear()

    def clear_cache(self) -> None:
        self._cache.clear()
