"""Policy warning list merge helpers for scanner_core metadata assembly."""

from __future__ import annotations

from prism.scanner_data.contracts_request import ScanPolicyWarning


def _copy_policy_warning_entries(raw_warnings: object) -> list[ScanPolicyWarning]:
    if not isinstance(raw_warnings, list):
        return []
    # Each warning should already be a dict; dict(warning) is a shallow copy.
    return [dict(warning) for warning in raw_warnings if isinstance(warning, dict)]


def merge_policy_warning_entries(
    ingress_warnings: object,
    metadata_warnings: object,
) -> list[ScanPolicyWarning]:
    merged: list[ScanPolicyWarning] = []
    for warning in _copy_policy_warning_entries(ingress_warnings):
        if warning not in merged:
            merged.append(warning)
    for warning in _copy_policy_warning_entries(metadata_warnings):
        if warning not in merged:
            merged.append(warning)
    return merged
