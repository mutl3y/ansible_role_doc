"""Scan state building and preparation functions."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable

from prism.scanner_data.contracts_request import (
    PolicyContext,
    ScanBaseContext,
    ScanContextPayload,
    ScanMetadata,
    ScanOptionsDict,
)


def build_runtime_scan_state(
    *,
    role_path: str,
    role_name_override: str | None,
    readme_config_path: str | None,
    include_vars_main: bool,
    exclude_path_patterns: list[str] | None,
    detailed_catalog: bool,
    include_task_parameters: bool,
    include_task_runbooks: bool,
    inline_task_runbooks: bool,
    include_collection_checks: bool,
    keep_unknown_style_sections: bool,
    adopt_heading_mode: str | None,
    vars_seed_paths: list[str] | None,
    style_readme_path: str | None,
    style_source_path: str | None,
    style_guide_skeleton: bool,
    compare_role_path: str | None,
    policy_config_path: str | None,
    fail_on_unconstrained_dynamic_includes: bool | None,
    fail_on_yaml_like_task_annotations: bool | None,
    ignore_unresolved_internal_underscore_references: bool | None,
    strict_phase_failures: bool,
    failure_policy: Any,
    runbook_output: str | None,
    runbook_csv_output: str | None,
    load_pattern_policy_with_context: Any,
    build_run_scan_options_fn: Callable[..., ScanOptionsDict],
    resolve_scan_request_for_runtime_fn: Callable[..., bool],
    logger_factory: Any = None,
) -> tuple[dict[str, Any], PolicyContext, ScanOptionsDict]:
    """Resolve request-scoped policy and canonical scan options for one run."""
    if logger_factory is None:
        from prism.scanner_core.logging_config import LoggerFactory

        logger_factory = LoggerFactory()
    logger = logger_factory.get_logger(__name__)
    logger.info(
        "Starting runtime scan state build",
        extra={"operation": "build_runtime_scan_state", "role_path": role_path},
    )

    loaded_policy, policy_context = load_pattern_policy_with_context(
        override_path=policy_config_path,
        search_root=role_path,
    )
    if failure_policy is not None and hasattr(failure_policy, "strict"):
        strict_phase_failures = bool(getattr(failure_policy, "strict"))

    scan_options = build_run_scan_options_fn(
        role_path=role_path,
        role_name_override=role_name_override,
        readme_config_path=readme_config_path,
        include_vars_main=include_vars_main,
        exclude_path_patterns=exclude_path_patterns,
        detailed_catalog=resolve_scan_request_for_runtime_fn(
            detailed_catalog=detailed_catalog,
            runbook_output=runbook_output,
            runbook_csv_output=runbook_csv_output,
        ),
        include_task_parameters=include_task_parameters,
        include_task_runbooks=include_task_runbooks,
        inline_task_runbooks=inline_task_runbooks,
        include_collection_checks=include_collection_checks,
        keep_unknown_style_sections=keep_unknown_style_sections,
        adopt_heading_mode=adopt_heading_mode,
        vars_seed_paths=vars_seed_paths,
        style_readme_path=style_readme_path,
        style_source_path=style_source_path,
        style_guide_skeleton=style_guide_skeleton,
        compare_role_path=compare_role_path,
        fail_on_unconstrained_dynamic_includes=fail_on_unconstrained_dynamic_includes,
        fail_on_yaml_like_task_annotations=fail_on_yaml_like_task_annotations,
        ignore_unresolved_internal_underscore_references=(
            ignore_unresolved_internal_underscore_references
        ),
        policy_context=policy_context,
    )
    scan_options = {
        **scan_options,
        "strict_phase_failures": bool(strict_phase_failures),
    }

    # Set scan context for logging
    role_name = scan_options.get("role_name") or role_name_override or "unknown"
    scan_id = f"scan_{id(scan_options)}"  # Simple scan_id
    from prism.scanner_core.logging_config import set_scan_context

    with set_scan_context(role_name=role_name, scan_id=scan_id):
        logger.info(
            "Completed runtime scan state build",
            extra={"operation": "build_runtime_scan_state", "role_path": role_path},
        )
        return loaded_policy, policy_context, scan_options


@contextmanager
def scan_policy_scope(
    *,
    loaded_policy: dict[str, Any],
    policy_context: PolicyContext,
    variable_policy_scope: Callable[..., Any],
    style_section_aliases_scope: Callable[..., Any],
    variable_guidance_keywords_scope: Callable[..., Any],
):
    """Apply request-scoped policy overrides used by one scanner execution."""
    with variable_policy_scope(loaded_policy), style_section_aliases_scope(
        dict(policy_context["section_aliases"])
    ), variable_guidance_keywords_scope(
        tuple(policy_context["variable_guidance_keywords"])
    ):
        yield


def prepare_scan_context(
    scan_options: ScanOptionsDict,
    *,
    scan_context_builder_cls: type,
    collect_scan_base_context: Callable[..., ScanBaseContext],
    load_ignore_unresolved_internal_underscore_references: Callable[
        [str, str | None, bool], bool
    ],
    apply_unconstrained_dynamic_include_policy: Callable[..., None],
    apply_yaml_like_task_annotation_policy: Callable[..., None],
    finalize_scan_context_payload: Callable[..., ScanContextPayload],
    logger_factory: Any = None,
    di_container=None,
    load_non_authoritative_test_evidence_max_file_bytes: (
        Callable[..., int] | None
    ) = None,
    load_non_authoritative_test_evidence_max_files_scanned: (
        Callable[..., int] | None
    ) = None,
    load_non_authoritative_test_evidence_max_total_bytes: (
        Callable[..., int] | None
    ) = None,
    enrich_scan_context_with_insights: (
        Callable[..., tuple[list[dict], dict, ScanMetadata]] | None
    ) = None,
    non_authoritative_test_evidence_max_file_bytes: int | None = None,
    non_authoritative_test_evidence_max_files_scanned: int | None = None,
    non_authoritative_test_evidence_max_total_bytes: int | None = None,
    collect_scan_identity_and_artifacts: Callable[..., tuple[Any, ...]] | None = None,
    apply_scan_metadata_configuration: Callable[..., tuple[list, dict]] | None = None,
    apply_unconstrained_dynamic_include_policy_arg: Callable[..., dict] | None = None,
    apply_yaml_like_task_annotation_policy_arg: Callable[..., dict] | None = None,
    resolve_scan_identity: (
        Callable[[str, str | None], tuple[Any, Any, str, str]] | None
    ) = None,
    load_readme_marker_prefix: Callable[..., str] | None = None,
    collect_scan_artifacts: (
        Callable[..., tuple[dict, list, list, ScanMetadata]] | None
    ) = None,
) -> ScanContextPayload:
    """Prepare the scan context payload from scan options."""
    if logger_factory is None:
        from prism.scanner_core.logging_config import LoggerFactory

        logger_factory = LoggerFactory()
    logger = logger_factory.get_logger(__name__)
    logger.info(
        "Starting scan context preparation",
        extra={"operation": "prepare_scan_context"},
    )

    effective_collect_scan_identity_and_artifacts = (
        collect_scan_identity_and_artifacts or collect_scan_identity_and_artifacts
    )
    effective_apply_scan_metadata_configuration = (
        apply_scan_metadata_configuration or apply_scan_metadata_configuration
    )
    effective_apply_unconstrained_dynamic_include_policy = (
        apply_unconstrained_dynamic_include_policy_arg
        or apply_unconstrained_dynamic_include_policy
    )
    effective_apply_yaml_like_task_annotation_policy = (
        apply_yaml_like_task_annotation_policy_arg
        or apply_yaml_like_task_annotation_policy
    )

    if load_non_authoritative_test_evidence_max_file_bytes is None:
        raise ValueError(
            "load_non_authoritative_test_evidence_max_file_bytes must be provided"
        )
    if load_non_authoritative_test_evidence_max_files_scanned is None:
        raise ValueError(
            "load_non_authoritative_test_evidence_max_files_scanned must be provided"
        )
    if load_non_authoritative_test_evidence_max_total_bytes is None:
        raise ValueError(
            "load_non_authoritative_test_evidence_max_total_bytes must be provided"
        )
    if enrich_scan_context_with_insights is None:
        raise ValueError("enrich_scan_context_with_insights must be provided")
    if non_authoritative_test_evidence_max_file_bytes is None:
        raise ValueError(
            "non_authoritative_test_evidence_max_file_bytes must be provided"
        )
    if non_authoritative_test_evidence_max_files_scanned is None:
        raise ValueError(
            "non_authoritative_test_evidence_max_files_scanned must be provided"
        )
    if non_authoritative_test_evidence_max_total_bytes is None:
        raise ValueError(
            "non_authoritative_test_evidence_max_total_bytes must be provided"
        )
    if effective_collect_scan_identity_and_artifacts is None:
        raise ValueError("collect_scan_identity_and_artifacts must be provided")
    if effective_apply_scan_metadata_configuration is None:
        raise ValueError("apply_scan_metadata_configuration must be provided")
    if effective_apply_unconstrained_dynamic_include_policy is None:
        raise ValueError("apply_unconstrained_dynamic_include_policy must be provided")
    if effective_apply_yaml_like_task_annotation_policy is None:
        raise ValueError("apply_yaml_like_task_annotation_policy must be provided")

    builder = scan_context_builder_cls(
        collect_scan_base_context=collect_scan_base_context,
        load_ignore_unresolved_internal_underscore_references=load_ignore_unresolved_internal_underscore_references,
        load_fail_on_unconstrained_dynamic_includes=(
            lambda role_path, role_name=None, default=False, **kwargs: default
        ),
        load_fail_on_yaml_like_task_annotations=(
            lambda role_path, role_name=None, default=False, **kwargs: default
        ),
        load_non_authoritative_test_evidence_max_file_bytes=load_non_authoritative_test_evidence_max_file_bytes,
        load_non_authoritative_test_evidence_max_files_scanned=load_non_authoritative_test_evidence_max_files_scanned,
        load_non_authoritative_test_evidence_max_total_bytes=load_non_authoritative_test_evidence_max_total_bytes,
        enrich_scan_context_with_insights=enrich_scan_context_with_insights,
        finalize_scan_context_payload=finalize_scan_context_payload,
        non_authoritative_test_evidence_max_file_bytes=non_authoritative_test_evidence_max_file_bytes,
        non_authoritative_test_evidence_max_files_scanned=non_authoritative_test_evidence_max_files_scanned,
        non_authoritative_test_evidence_max_total_bytes=non_authoritative_test_evidence_max_total_bytes,
        collect_scan_identity_and_artifacts=effective_collect_scan_identity_and_artifacts,
        apply_scan_metadata_configuration=effective_apply_scan_metadata_configuration,
        apply_unconstrained_dynamic_include_policy=effective_apply_unconstrained_dynamic_include_policy,
        apply_yaml_like_task_annotation_policy=effective_apply_yaml_like_task_annotation_policy,
        resolve_scan_identity=resolve_scan_identity,
        load_readme_marker_prefix=load_readme_marker_prefix,
        collect_scan_artifacts=collect_scan_artifacts,
        di_container=di_container,
    )
    scan_context_payload = builder.build_scan_context(scan_options)

    logger.info(
        "Completed scan context preparation",
        extra={"operation": "prepare_scan_context"},
    )
    return scan_context_payload


def collect_scan_base_context(
    scan_options,
    load_fail_on_unconstrained_dynamic_includes,
    load_fail_on_yaml_like_task_annotations,
    load_non_authoritative_test_evidence_max_file_bytes,
    load_non_authoritative_test_evidence_max_files_scanned,
    load_non_authoritative_test_evidence_max_total_bytes,
    *,
    collect_scan_identity_and_artifacts,
    apply_scan_metadata_configuration,
    apply_unconstrained_dynamic_include_policy,
    apply_yaml_like_task_annotation_policy,
    resolve_scan_identity,
    load_readme_marker_prefix,
    collect_scan_artifacts,
):
    """Collect base context for scan from options."""
    role_path = scan_options["role_path"]
    readme_config_path = scan_options.get("readme_config_path")

    (
        rp,
        meta,
        role_name,
        description,
        marker_prefix,
        variables,
        requirements,
        found,
        metadata,
    ) = collect_scan_identity_and_artifacts(
        role_path=role_path,
        role_name_override=scan_options.get("role_name_override"),
        readme_config_path=readme_config_path,
        include_vars_main=bool(scan_options.get("include_vars_main", True)),
        exclude_path_patterns=scan_options.get("exclude_path_patterns"),
        detailed_catalog=bool(scan_options.get("detailed_catalog", False)),
        resolve_scan_identity_fn=resolve_scan_identity,
        load_readme_marker_prefix_fn=load_readme_marker_prefix,
        collect_scan_artifacts_fn=collect_scan_artifacts,
    )

    requirements_display, metadata = apply_scan_metadata_configuration(
        role_path=role_path,
        readme_config_path=readme_config_path,
        adopt_heading_mode=scan_options.get("adopt_heading_mode"),
        include_task_parameters=bool(scan_options.get("include_task_parameters", True)),
        include_task_runbooks=bool(scan_options.get("include_task_runbooks", True)),
        inline_task_runbooks=bool(scan_options.get("inline_task_runbooks", True)),
        include_collection_checks=bool(
            scan_options.get("include_collection_checks", True)
        ),
        keep_unknown_style_sections=bool(
            scan_options.get("keep_unknown_style_sections", True)
        ),
        meta=meta,
        requirements=requirements,
        metadata=metadata,
    )

    metadata = apply_unconstrained_dynamic_include_policy(
        role_path=role_path,
        readme_config_path=readme_config_path,
        fail_on_unconstrained_dynamic_includes=scan_options.get(
            "fail_on_unconstrained_dynamic_includes"
        ),
        metadata=metadata,
    )
    metadata = apply_yaml_like_task_annotation_policy(
        role_path=role_path,
        readme_config_path=readme_config_path,
        fail_on_yaml_like_task_annotations=scan_options.get(
            "fail_on_yaml_like_task_annotations"
        ),
        metadata=metadata,
    )

    return {
        "rp": rp,
        "role_name": role_name,
        "description": description,
        "marker_prefix": marker_prefix,
        "variables": variables,
        "found": found,
        "metadata": metadata,
        "requirements_display": requirements_display,
    }
