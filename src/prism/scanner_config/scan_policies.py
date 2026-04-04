"""Scan policy application functions."""

from __future__ import annotations

from typing import Callable


def apply_unconstrained_dynamic_include_policy(
    *,
    role_path: str,
    readme_config_path: str | None,
    fail_on_unconstrained_dynamic_includes: bool | None,
    metadata: dict,
    load_fail_on_unconstrained_dynamic_includes: Callable[
        [str, str | None, bool], bool
    ],
) -> dict:
    """Apply and enforce unconstrained dynamic include scan policy."""
    # Intentionally allow malformed policy parsing RuntimeError to propagate.
    config_default = load_fail_on_unconstrained_dynamic_includes(
        role_path,
        readme_config_path,
        False,
    )
    effective_fail = (
        config_default
        if fail_on_unconstrained_dynamic_includes is None
        else bool(fail_on_unconstrained_dynamic_includes)
    )
    effective_metadata = {
        **metadata,
        "fail_on_unconstrained_dynamic_includes": effective_fail,
    }

    hazards = [
        *(effective_metadata.get("unconstrained_dynamic_task_includes") or []),
        *(effective_metadata.get("unconstrained_dynamic_role_includes") or []),
    ]
    if effective_fail and hazards:
        first = hazards[0] if isinstance(hazards[0], dict) else {}
        first_file = str(first.get("file") or "<unknown>")
        first_task = str(first.get("task") or "(unnamed task)")
        first_module = str(first.get("module") or "include")
        first_target = str(first.get("target") or "")
        raise RuntimeError(
            "Unconstrained dynamic includes detected "
            f"({len(hazards)} findings). "
            f"First finding: {first_file} / {first_task} / {first_module} -> {first_target}. "
            "Constrain with a simple when allow-list, disable via "
            "scan.fail_on_unconstrained_dynamic_includes in .prism.yml, "
            "or override at call time."
        )
    return effective_metadata


def apply_yaml_like_task_annotation_policy(
    *,
    role_path: str,
    readme_config_path: str | None,
    fail_on_yaml_like_task_annotations: bool | None,
    metadata: dict,
    load_fail_on_yaml_like_task_annotations: Callable[[str, str | None, bool], bool],
) -> dict:
    """Apply and enforce YAML-like task annotation strict-fail policy."""
    # Intentionally allow malformed policy parsing RuntimeError to propagate.
    config_default = load_fail_on_yaml_like_task_annotations(
        role_path,
        readme_config_path,
        False,
    )
    effective_fail = (
        config_default
        if fail_on_yaml_like_task_annotations is None
        else bool(fail_on_yaml_like_task_annotations)
    )
    effective_metadata = {
        **metadata,
        "fail_on_yaml_like_task_annotations": effective_fail,
    }

    features = effective_metadata.get("features") or {}
    yaml_like_count = int(features.get("yaml_like_task_annotations") or 0)
    if effective_fail and yaml_like_count > 0:
        raise RuntimeError(
            "YAML-like task annotations detected "
            f"({yaml_like_count} findings). "
            "Use plain text or key=value payloads in marker comments, disable via "
            "scan.fail_on_yaml_like_task_annotations in .prism.yml, "
            "or override at call time."
        )
    return effective_metadata
