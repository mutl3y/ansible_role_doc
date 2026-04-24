"""Task-file line parsing constants and marker helpers for fsrc."""

from __future__ import annotations

import re
from collections.abc import Collection
from typing import Any, Iterator

from prism.scanner_core.di_helpers import require_prepared_policy


class _PolicyBackedCollectionProxy:
    def __init__(self, policy_attr_name: str) -> None:
        self._policy_attr_name = policy_attr_name

    def _current_value(self) -> object:
        try:
            return getattr(
                require_prepared_policy(None, "task_line_parsing", "task_line_parsing"),
                self._policy_attr_name,
            )
        except ValueError:
            from prism.scanner_plugins.ansible import task_traversal_bare as _ttb

            return getattr(_ttb, self._policy_attr_name)

    def __iter__(self) -> Iterator[Any]:
        value = self._current_value()
        if isinstance(value, (set, tuple, list, frozenset)):
            return iter(value)
        return iter(())

    def __contains__(self, item: object) -> bool:
        value = self._current_value()
        if isinstance(value, (set, tuple, list, frozenset)):
            return item in value
        return False

    def __len__(self) -> int:
        value = self._current_value()
        if isinstance(value, (set, tuple, list, frozenset)):
            return len(value)
        return 0

    def __repr__(self) -> str:
        return repr(self._current_value())


class _PolicyBackedRegexProxy:
    def __init__(self, policy_attr_name: str) -> None:
        self._policy_attr_name = policy_attr_name

    def _current_regex(self) -> re.Pattern[str]:
        try:
            current = getattr(
                require_prepared_policy(None, "task_line_parsing", "task_line_parsing"),
                self._policy_attr_name,
            )
        except ValueError:
            from prism.scanner_plugins.ansible import task_traversal_bare as _ttb

            current = getattr(_ttb, self._policy_attr_name)
        if isinstance(current, re.Pattern):
            return current
        raise ValueError(
            f"prepared_policy_bundle.task_line_parsing.{self._policy_attr_name} "
            f"must be a compiled re.Pattern, got {type(current).__name__}"
        )

    def match(self, *args: Any, **kwargs: Any):
        return self._current_regex().match(*args, **kwargs)

    def search(self, *args: Any, **kwargs: Any):
        return self._current_regex().search(*args, **kwargs)

    def fullmatch(self, *args: Any, **kwargs: Any):
        return self._current_regex().fullmatch(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        return getattr(self._current_regex(), name)


TASK_INCLUDE_KEYS: Collection[str] = _PolicyBackedCollectionProxy("TASK_INCLUDE_KEYS")  # type: ignore[assignment]
ROLE_INCLUDE_KEYS: Collection[str] = _PolicyBackedCollectionProxy("ROLE_INCLUDE_KEYS")  # type: ignore[assignment]
INCLUDE_VARS_KEYS: Collection[str] = _PolicyBackedCollectionProxy("INCLUDE_VARS_KEYS")  # type: ignore[assignment]
SET_FACT_KEYS: Collection[str] = _PolicyBackedCollectionProxy("SET_FACT_KEYS")  # type: ignore[assignment]
TASK_BLOCK_KEYS: Collection[str] = _PolicyBackedCollectionProxy("TASK_BLOCK_KEYS")  # type: ignore[assignment]
TASK_META_KEYS: Collection[str] = _PolicyBackedCollectionProxy("TASK_META_KEYS")  # type: ignore[assignment]


def get_task_include_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).TASK_INCLUDE_KEYS


def get_role_include_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).ROLE_INCLUDE_KEYS


def get_include_vars_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).INCLUDE_VARS_KEYS


def get_set_fact_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).SET_FACT_KEYS


def get_task_block_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).TASK_BLOCK_KEYS


def get_task_meta_keys(di: object | None = None) -> object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).TASK_META_KEYS


def get_templated_include_re(di: object | None = None) -> re.Pattern[str] | object:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).TEMPLATED_INCLUDE_RE


def _extract_constrained_when_values(
    task: dict,
    variable: str,
    *,
    di: object | None = None,
) -> list[str]:
    return require_prepared_policy(
        di, "task_line_parsing", "task_line_parsing"
    ).extract_constrained_when_values(task, variable)


def _normalize_marker_prefix(
    marker_prefix: str | None,
    *,
    di: object | None = None,
) -> str:
    return require_prepared_policy(
        di, "task_annotation_parsing", "task_annotation_parsing"
    ).normalize_marker_prefix(marker_prefix)


def _build_marker_line_re(
    marker_prefix: str | None,
    *,
    di: object | None = None,
):
    normalized_prefix = _normalize_marker_prefix(marker_prefix, di=di)
    return require_prepared_policy(
        di, "task_annotation_parsing", "task_annotation_parsing"
    ).get_marker_line_re(normalized_prefix)


def get_marker_line_re(marker_prefix, *, di: object | None = None):
    return _build_marker_line_re(marker_prefix, di=di)


class _PolicyBackedMarkerLineRegexProxy:
    """Proxy that resolves marker-line regex from annotation policy at call time."""

    def _current_regex(self) -> re.Pattern[str]:
        try:
            policy = require_prepared_policy(
                None, "task_annotation_parsing", "task_annotation_parsing"
            )
            regex = policy.get_marker_line_re(policy.normalize_marker_prefix(None))
        except ValueError:
            from prism.scanner_plugins.parsers.comment_doc.marker_utils import (
                DEFAULT_DOC_MARKER_PREFIX,
                get_marker_line_re,
            )

            regex = get_marker_line_re(DEFAULT_DOC_MARKER_PREFIX)
        if isinstance(regex, re.Pattern):
            return regex
        raise ValueError(
            "prepared_policy_bundle.task_annotation_parsing.get_marker_line_re "
            "must return a compiled re.Pattern"
        )

    def match(self, *args: Any, **kwargs: Any):
        return self._current_regex().match(*args, **kwargs)

    def search(self, *args: Any, **kwargs: Any):
        return self._current_regex().search(*args, **kwargs)

    def fullmatch(self, *args: Any, **kwargs: Any):
        return self._current_regex().fullmatch(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        return getattr(self._current_regex(), name)


ROLE_NOTES_RE = _PolicyBackedMarkerLineRegexProxy()
TASK_NOTES_LONG_RE = _PolicyBackedMarkerLineRegexProxy()


class _PolicyBackedAnnotationRegexProxy:
    def __init__(self, policy_attr_name: str) -> None:
        self._policy_attr_name = policy_attr_name

    def _current_regex(self) -> re.Pattern[str]:
        try:
            current = getattr(
                require_prepared_policy(
                    None, "task_annotation_parsing", "task_annotation_parsing"
                ),
                self._policy_attr_name,
                None,
            )
        except ValueError:
            from prism.scanner_plugins.policies import constants as _c

            current = getattr(_c, self._policy_attr_name, None)
        if isinstance(current, re.Pattern):
            return current
        raise ValueError(
            f"prepared_policy_bundle.task_annotation_parsing.{self._policy_attr_name} "
            f"must be a compiled regex pattern"
        )

    def match(self, *args: Any, **kwargs: Any):
        return self._current_regex().match(*args, **kwargs)

    def search(self, *args: Any, **kwargs: Any):
        return self._current_regex().search(*args, **kwargs)

    def fullmatch(self, *args: Any, **kwargs: Any):
        return self._current_regex().fullmatch(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        return getattr(self._current_regex(), name)


COMMENT_CONTINUATION_RE = _PolicyBackedAnnotationRegexProxy(
    "COMMENT_CONTINUATION_RE",
)
COMMENTED_TASK_ENTRY_RE = _PolicyBackedAnnotationRegexProxy(
    "COMMENTED_TASK_ENTRY_RE",
)
TASK_ENTRY_RE = _PolicyBackedAnnotationRegexProxy(
    "TASK_ENTRY_RE",
)
YAML_LIKE_KEY_VALUE_RE = _PolicyBackedAnnotationRegexProxy(
    "YAML_LIKE_KEY_VALUE_RE",
)
YAML_LIKE_LIST_ITEM_RE = _PolicyBackedAnnotationRegexProxy(
    "YAML_LIKE_LIST_ITEM_RE",
)
TEMPLATED_INCLUDE_RE = _PolicyBackedRegexProxy("TEMPLATED_INCLUDE_RE")
