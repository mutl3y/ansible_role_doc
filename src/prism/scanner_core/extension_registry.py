"""Extension registry for pluggable custom processors in orchestrators.

This module provides a registry for registering custom processors that can hook
into various points in the scanner orchestrators, allowing for pluggable extensions.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List
from enum import Enum


class HookPoint(Enum):
    """Enumeration of hook points where custom processors can be registered."""

    VARIABLE_DISCOVERY_PRE = "variable_discovery_pre"
    VARIABLE_DISCOVERY_POST = "variable_discovery_post"
    FEATURE_DETECTION_PRE = "feature_detection_pre"
    FEATURE_DETECTION_POST = "feature_detection_post"


Processor = Callable[..., Any]


class ExtensionRegistry:
    """Registry for managing custom processors at various hook points.

    Allows registration of processors that can modify or extend behavior
    at specific points in the orchestrator pipelines.
    """

    def __init__(self) -> None:
        self._processors: Dict[HookPoint, List[Processor]] = {
            point: [] for point in HookPoint
        }

    def register(self, hook_point: HookPoint, processor: Processor) -> None:
        """Register a processor for a specific hook point."""
        self._processors[hook_point].append(processor)

    def get_processors(self, hook_point: HookPoint) -> List[Processor]:
        """Get all registered processors for a hook point."""
        return self._processors[hook_point].copy()

    def call_processors(
        self, hook_point: HookPoint, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Call all processors for a hook point with given arguments."""
        results = []
        for processor in self._processors[hook_point]:
            results.append(processor(*args, **kwargs))
        return results
