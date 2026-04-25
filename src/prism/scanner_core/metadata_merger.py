"""Policy warning list merge helpers for scanner_core metadata assembly."""

from __future__ import annotations

from typing import Any


def _copy_policy_warning_entries(raw_warnings: object) -> list[dict[str, Any]]:
    if not isinstance(raw_warnings, list):
        return []
    return [dict(warning) for warning in raw_warnings if isinstance(warning, dict)]


def merge_policy_warning_entries(
    ingress_warnings: object,
    metadata_warnings: object,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for warning in _copy_policy_warning_entries(ingress_warnings):
        if warning not in merged:
            merged.append(warning)
    for warning in _copy_policy_warning_entries(metadata_warnings):
        if warning not in merged:
            merged.append(warning)
    return merged
