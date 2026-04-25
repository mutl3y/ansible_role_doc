"""Ansible task-keyword vocabulary.

Canonical home for the bare (non-FQCN) Ansible task keyword sets used by
the Ansible default policy plugins. The FQCN-inclusive supersets live in
`scanner_plugins.ansible.task_traversal_bare` and the canonical Ansible
plugin (`scanner_plugins.ansible.extract_policies`).
"""

from __future__ import annotations

TASK_INCLUDE_KEYS: frozenset[str] = frozenset(
    {
        "include_tasks",
        "import_tasks",
    }
)
ROLE_INCLUDE_KEYS: frozenset[str] = frozenset(
    {
        "include_role",
        "import_role",
    }
)
INCLUDE_VARS_KEYS: frozenset[str] = frozenset({"include_vars"})
SET_FACT_KEYS: frozenset[str] = frozenset({"set_fact"})
TASK_BLOCK_KEYS: tuple[str, ...] = ("block", "rescue", "always")
TASK_META_KEYS: frozenset[str] = frozenset(
    {
        "name",
        "when",
        "tags",
        "register",
        "notify",
        "vars",
        "become",
        "become_user",
        "become_method",
        "check_mode",
        "changed_when",
        "failed_when",
        "ignore_errors",
        "ignore_unreachable",
        "delegate_to",
        "run_once",
        "loop",
        "loop_control",
        "with_items",
        "with_dict",
        "with_fileglob",
        "with_first_found",
        "with_nested",
        "with_sequence",
        "environment",
        "args",
        "retries",
        "delay",
        "until",
        "throttle",
        "no_log",
    }
)

__all__ = [
    "INCLUDE_VARS_KEYS",
    "ROLE_INCLUDE_KEYS",
    "SET_FACT_KEYS",
    "TASK_BLOCK_KEYS",
    "TASK_INCLUDE_KEYS",
    "TASK_META_KEYS",
]
