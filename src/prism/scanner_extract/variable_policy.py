"""Policy handling for variable extraction.

Request-scoped policy management and derived state.
"""

import re
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Iterable

from ..scanner_config.patterns import load_pattern_config

# ---------------------------------------------------------------------------
# Policy management (request-scoped)
# ---------------------------------------------------------------------------

_POLICY_OVERRIDE: ContextVar[dict[str, Any] | None] = ContextVar(
    "prism_variable_extractor_policy_override",
    default=None,
)


def _active_policy() -> dict[str, Any]:
    policy_override = _POLICY_OVERRIDE.get()
    if isinstance(policy_override, dict):
        return policy_override
    # Load default policy when no override is active
    return load_pattern_config()


def _active_ignored_identifiers() -> set[str]:
    return _build_effective_ignored_identifiers(_active_policy())


def _active_sensitivity_tokens() -> (
    tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]
):
    sensitivity = _active_policy().get("sensitivity") or {}
    return (
        tuple(sensitivity.get("name_tokens") or ()),
        tuple(sensitivity.get("vault_markers") or ()),
        tuple(sensitivity.get("credential_prefixes") or ()),
        tuple(sensitivity.get("url_prefixes") or ()),
    )


@contextmanager
def policy_override_scope(policy: dict[str, Any] | None):
    """Apply a request-scoped policy override for variable extraction."""

    token: Token[dict[str, Any] | None] = _POLICY_OVERRIDE.set(policy)
    try:
        yield
    finally:
        _POLICY_OVERRIDE.reset(token)


def _build_effective_ignored_identifiers(policy: dict[str, Any]) -> set[str]:
    """Merge policy ignores with task keywords and ansible builtin variables."""
    ignored: set[str] = {
        token.lower()
        for token in policy.get("ignored_identifiers", set())
        if isinstance(token, str)
    }
    ignored.update(_build_task_keyword_ignored_identifiers())
    ignored.update(
        {
            token.lower()
            for token in policy.get("ansible_builtin_variables", set())
            if isinstance(token, str)
        }
    )
    ignored.update(_load_ansible_core_builtin_variables())
    return ignored


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


_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Public export
IGNORED_IDENTIFIERS = _active_ignored_identifiers
