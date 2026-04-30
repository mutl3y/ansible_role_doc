"""T4-03: CLI streaming progress output tests."""

from __future__ import annotations

import io

from prism.progress import ProgressReporter, progress_reporter_enabled
from prism.scanner_core.di import DIContainer
from prism.scanner_core.events import (
    ScanPhaseEvent,
    clear_default_listeners,
    get_default_listeners,
    register_default_listener,
    unregister_default_listener,
)


def test_progress_reporter_writes_pre_post_to_stream() -> None:
    buf = io.StringIO()
    reporter = ProgressReporter(stream=buf)
    reporter(ScanPhaseEvent(phase_name="feature_detection", kind="pre"))
    reporter(ScanPhaseEvent(phase_name="feature_detection", kind="post"))
    out = buf.getvalue()
    assert "feature_detection: start" in out
    assert "feature_detection: done" in out
    assert "ms)" in out


def test_default_listener_registry_roundtrip() -> None:
    clear_default_listeners()
    try:
        assert get_default_listeners() == ()

        def listener(event: ScanPhaseEvent) -> None:
            return None

        register_default_listener(listener)
        assert listener in get_default_listeners()
        unregister_default_listener(listener)
        assert listener not in get_default_listeners()
        unregister_default_listener(listener)
    finally:
        clear_default_listeners()


def test_di_container_picks_up_default_listeners() -> None:
    clear_default_listeners()
    seen: list[ScanPhaseEvent] = []

    def listener(event: ScanPhaseEvent) -> None:
        seen.append(event)

    register_default_listener(listener)
    try:
        container = DIContainer(role_path="/tmp/role", scan_options={})
        bus = container.factory_event_bus()
        assert bus.listener_count == 1
        with bus.phase("variable_discovery"):
            pass
        assert [e.kind for e in seen] == ["pre", "post"]
    finally:
        clear_default_listeners()


def test_explicit_empty_listeners_overrides_defaults() -> None:
    clear_default_listeners()

    def listener(event: ScanPhaseEvent) -> None:
        return None

    register_default_listener(listener)
    try:
        container = DIContainer(
            role_path="/tmp/role", scan_options={}, event_listeners=[]
        )
        assert container.factory_event_bus().listener_count == 0
    finally:
        clear_default_listeners()


def test_progress_reporter_enabled_context_manager() -> None:
    clear_default_listeners()
    buf = io.StringIO()
    with progress_reporter_enabled(stream=buf) as reporter:
        assert reporter in get_default_listeners()
    assert reporter not in get_default_listeners()


def test_progress_reporter_non_callable_rejected() -> None:
    import pytest

    with pytest.raises(TypeError):
        register_default_listener("not-callable")  # type: ignore[arg-type]
