"""Property-based tests for Jinja scanning and task-module detection robustness."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from prism.scanner_plugins.ansible.task_line_parsing import detect_task_module
from prism.scanner_plugins.parsers.jinja.analysis_policy import (
    collect_undeclared_jinja_variables,
)


@settings(max_examples=100)
@given(st.text())
def test_jinja_scanner_never_crashes_on_arbitrary_text(text: str) -> None:
    """collect_undeclared_jinja_variables must not propagate uncaught exceptions.

    TemplateSyntaxError and TemplateAssertionError are caught internally.
    Any other exception escaping is a regression.
    """
    result = collect_undeclared_jinja_variables(text)
    assert isinstance(result, set)


@settings(max_examples=100)
@given(st.text())
def test_jinja_scanner_returns_only_string_variable_names(text: str) -> None:
    """All variable names returned must be non-empty strings."""
    result = collect_undeclared_jinja_variables(text)
    for name in result:
        assert isinstance(name, str)
        assert name  # Jinja variable names are never empty identifiers


@settings(max_examples=100)
@given(st.text())
def test_jinja_scanner_returns_empty_set_when_no_jinja_markers(text: str) -> None:
    """Strings with no '{{' or '{%' markers must immediately return an empty set."""
    if "{{" in text or "{%" in text:
        return  # skip strings that contain Jinja markers
    result = collect_undeclared_jinja_variables(text)
    assert result == set()


@settings(max_examples=100)
@given(st.dictionaries(st.text(max_size=40), st.one_of(st.text(), st.none())))
def test_detect_task_module_never_crashes_on_arbitrary_dict(task: dict) -> None:
    """detect_task_module must return str | None for any dict input without raising."""
    result = detect_task_module(task)
    assert result is None or isinstance(result, str)


@settings(max_examples=100)
@given(st.text(max_size=80))
def test_detect_task_module_on_single_key_dict(key: str) -> None:
    """detect_task_module with a single-key dict must return str | None without raising."""
    result = detect_task_module({key: "value"})
    assert result is None or isinstance(result, str)
