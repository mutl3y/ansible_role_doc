"""Identifier normalization utilities.

Functions for normalizing and validating variable identifiers.
"""

import re
from typing import Any, Iterable

_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _coerce_identifier(value: object) -> str | None:
    """Return a lower-cased identifier token when ``value`` looks like one."""
    if not isinstance(value, str):
        return None
    token = value.strip()
    if not token:
        return None
    if "." in token:
        token = token.rsplit(".", 1)[-1]
    lowered = token.lower()
    if _VALID_IDENTIFIER_RE.match(lowered):
        return lowered
    return None


def _iter_strings(value: Any) -> Iterable[str]:
    """Yield string items recursively from nested containers."""
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings(nested)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _iter_strings(item)


def _load_ansible_core_builtin_variables() -> set[str]:
    """Best-effort import of ansible-core builtin/reserved variable names."""
    names: set[str] = set()

    try:
        from ansible.vars.reserved import get_reserved_names  # type: ignore

        for raw in get_reserved_names() or []:
            token = _coerce_identifier(raw)
            if token:
                names.add(token)
    except ImportError:
        # Ansible not installed, skip
        pass

    try:
        from ansible import constants as ansible_constants  # type: ignore

        for attr_name in (
            "MAGIC_VARIABLE_MAPPING",
            "COMMON_CONNECTION_VARS",
            "INTERNAL_RESULT_KEYS",
            "RESTRICTED_RESULT_KEYS",
        ):
            raw_value = getattr(ansible_constants, attr_name, None)
            for raw in _iter_strings(raw_value):
                token = _coerce_identifier(raw)
                if token:
                    names.add(token)
    except ImportError:
        # Ansible not installed, skip
        pass

    return names


def _build_task_keyword_ignored_identifiers() -> set[str]:
    """Return keyword-like task parser tokens that must never be treated as vars."""
    from .task_parser import (
        TASK_BLOCK_KEYS,
        TASK_INCLUDE_KEYS,
        TASK_META_KEYS,
        ROLE_INCLUDE_KEYS,
        INCLUDE_VARS_KEYS,
        SET_FACT_KEYS,
    )

    names: set[str] = set()
    for raw in (
        *TASK_META_KEYS,
        *TASK_BLOCK_KEYS,
        *TASK_INCLUDE_KEYS,
        *ROLE_INCLUDE_KEYS,
        *INCLUDE_VARS_KEYS,
        *SET_FACT_KEYS,
    ):
        token = _coerce_identifier(raw)
        if token:
            names.add(token)
    return names
