"""Feature detector orchestration for foundational fsrc scanner-core parity."""

from __future__ import annotations

import threading
from typing import Any

from prism.scanner_core.di import DIContainer
from prism.scanner_core.di_helpers import get_event_bus_or_none
from prism.scanner_core.events import PHASE_FEATURE_DETECTION
from prism.scanner_data.contracts_request import (
    FeaturesContext,
    validate_feature_detector_inputs,
)
from prism.scanner_core.task_extract_adapters import collect_task_handler_catalog
from prism.scanner_plugins.interfaces import FeatureDetectionPlugin


class FeatureDetector:
    """Detect aggregate role features and produce task-catalog summaries."""

    def __init__(
        self,
        di: DIContainer,
        role_path: str,
        options: dict[str, Any],
    ) -> None:
        validate_feature_detector_inputs(
            di=di,
            role_path=role_path,
            options=options,
        )
        self._di = di
        self._role_path = role_path
        self._options = options
        self._plugin: FeatureDetectionPlugin | None = None
        self._plugin_resolved = False
        self._plugin_lock = threading.Lock()

    def _resolve_plugin(self) -> FeatureDetectionPlugin | None:
        if self._plugin_resolved:
            return self._plugin
        with self._plugin_lock:
            if not self._plugin_resolved:
                factory = getattr(self._di, "factory_feature_detection_plugin", None)
                if callable(factory):
                    self._plugin = factory()
                self._plugin_resolved = True
        return self._plugin

    def detect(self) -> FeaturesContext:
        plugin = self._resolve_plugin()
        if plugin is not None:
            event_bus = get_event_bus_or_none(self._di)
            ctx = {"role_path": self._role_path}
            if event_bus is not None:
                with event_bus.phase(PHASE_FEATURE_DETECTION, context=ctx):
                    return plugin.detect_features(self._role_path, self._options)
            return plugin.detect_features(self._role_path, self._options)

        raise ValueError(
            "FeatureDetector requires a plugin via DI factory_feature_detection_plugin"
        )

    def analyze_task_catalog(self) -> dict[str, dict[str, Any]]:
        plugin = self._resolve_plugin()
        if plugin is not None:
            return plugin.analyze_task_catalog(self._role_path, self._options)

        raise ValueError(
            "FeatureDetector requires a plugin via DI factory_feature_detection_plugin"
        )

    def collect_task_handler_catalog(
        self,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        return collect_task_handler_catalog(
            self._role_path,
            exclude_paths=self._options.get("exclude_path_patterns"),
            di=self._di,
        )
