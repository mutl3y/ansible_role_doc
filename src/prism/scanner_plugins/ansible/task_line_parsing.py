"""Ansible-owned task-line parsing constants and helpers for fsrc."""

from __future__ import annotations

from prism.scanner_plugins.ansible.task_traversal_bare import (
    INCLUDE_VARS_KEYS,
    ROLE_INCLUDE_KEYS,
    SET_FACT_KEYS,
    TASK_BLOCK_KEYS,
    TASK_INCLUDE_KEYS,
    TASK_META_KEYS,
    TEMPLATED_INCLUDE_RE,
    WHEN_IN_LIST_RE,
    extract_constrained_when_values,
)

__all__ = [
    "INCLUDE_VARS_KEYS",
    "ROLE_INCLUDE_KEYS",
    "SET_FACT_KEYS",
    "TASK_BLOCK_KEYS",
    "TASK_INCLUDE_KEYS",
    "TASK_META_KEYS",
    "TEMPLATED_INCLUDE_RE",
    "WHEN_IN_LIST_RE",
    "extract_constrained_when_values",
]


def detect_task_module(task: dict) -> str | None:
    for include_key in TASK_INCLUDE_KEYS:
        if include_key in task:
            if "import_tasks" in include_key:
                return "import_tasks"
            return "include_tasks"

    for include_key in ROLE_INCLUDE_KEYS:
        if include_key in task:
            if "import_role" in include_key:
                return "import_role"
            return "include_role"

    for key in task:
        if key in TASK_META_KEYS or key in TASK_BLOCK_KEYS:
            continue
        if key.startswith("with_"):
            continue
        return key
    return None


__all__ = [
    "INCLUDE_VARS_KEYS",
    "ROLE_INCLUDE_KEYS",
    "SET_FACT_KEYS",
    "TASK_BLOCK_KEYS",
    "TASK_INCLUDE_KEYS",
    "WHEN_IN_LIST_RE",
    "TASK_META_KEYS",
    "TEMPLATED_INCLUDE_RE",
    "detect_task_module",
    "extract_constrained_when_values",
]
