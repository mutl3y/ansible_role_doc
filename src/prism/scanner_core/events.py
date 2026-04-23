"""Scan phase event system (T3-01).

Provides a lightweight pub/sub bus for emitting :class:`ScanPhaseEvent`
instances at the boundaries of each scanner pipeline phase. The bus is
opt-in: when no listeners are registered, ``emit`` is effectively free
and no behaviour changes.

Subscribers are plain callables ``(ScanPhaseEvent) -> None``. Listener
exceptions are caught and logged so that observability never breaks the
scan; this matches the constitutional rule that telemetry must not change
production semantics.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Mapping

logger = logging.getLogger(__name__)


EventListener = Callable[["ScanPhaseEvent"], None]


# Canonical phase names emitted by the built-in pipeline. External
# consumers may emit additional phases without registering them here.
PHASE_FEATURE_DETECTION = "feature_detection"
PHASE_VARIABLE_DISCOVERY = "variable_discovery"
PHASE_OUTPUT_RENDER = "output_render"


@dataclass(frozen=True)
class ScanPhaseEvent:
    """A single pre/post boundary event for a named pipeline phase."""

    phase_name: str
    kind: str  # "pre" or "post"
    context: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in ("pre", "post"):
            raise ValueError(
                f"ScanPhaseEvent.kind must be 'pre' or 'post', got {self.kind!r}"
            )
        if not self.phase_name:
            raise ValueError("ScanPhaseEvent.phase_name must not be empty")


class EventBus:
    """In-process event bus.

    Listeners registered via :meth:`subscribe` receive every event
    dispatched through :meth:`emit`. Use :meth:`phase` as a context
    manager to emit a matched ``pre``/``post`` pair around a block of
    work.
    """

    def __init__(self, listeners: list[EventListener] | None = None) -> None:
        self._listeners: list[EventListener] = list(listeners or [])

    def subscribe(self, listener: EventListener) -> None:
        if not callable(listener):
            raise TypeError("EventBus listener must be callable")
        self._listeners.append(listener)

    def unsubscribe(self, listener: EventListener) -> None:
        try:
            self._listeners.remove(listener)
        except ValueError:
            pass

    @property
    def listener_count(self) -> int:
        return len(self._listeners)

    def emit(self, event: ScanPhaseEvent) -> None:
        if not self._listeners:
            return
        for listener in tuple(self._listeners):
            try:
                listener(event)
            except Exception:  # pragma: no cover - defensive
                logger.exception(
                    "EventBus listener raised for phase=%s kind=%s",
                    event.phase_name,
                    event.kind,
                )

    @contextmanager
    def phase(
        self,
        phase_name: str,
        *,
        context: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Iterator[None]:
        """Emit ``pre``/``post`` events around the wrapped block."""
        ctx = dict(context or {})
        meta = dict(metadata or {})
        self.emit(
            ScanPhaseEvent(
                phase_name=phase_name, kind="pre", context=ctx, metadata=meta
            )
        )
        try:
            yield
        finally:
            self.emit(
                ScanPhaseEvent(
                    phase_name=phase_name, kind="post", context=ctx, metadata=meta
                )
            )


__all__ = [
    "EventBus",
    "EventListener",
    "PHASE_FEATURE_DETECTION",
    "PHASE_OUTPUT_RENDER",
    "PHASE_VARIABLE_DISCOVERY",
    "ScanPhaseEvent",
]
