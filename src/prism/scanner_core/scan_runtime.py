"""Runtime scan-context orchestration seam for scanner facade delegation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from prism.scanner_data.contracts_request import ScanMetadata, PolicyContext
from prism.scanner_data.contracts_output import (
    RunScanOutputPayload,
    ScanReportSidecarArgs,
    EmitScanOutputsArgs,
    RunbookSidecarArgs,
)


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
    """Apply unconstrained dynamic include policy via delegation."""
    from prism.scanner_config import (
        apply_unconstrained_dynamic_include_policy as canonical_apply_unconstrained_dynamic_include_policy,
    )

    return canonical_apply_unconstrained_dynamic_include_policy(
        role_path=role_path,
        readme_config_path=readme_config_path,
        fail_on_unconstrained_dynamic_includes=fail_on_unconstrained_dynamic_includes,
        metadata=metadata,
        load_fail_on_unconstrained_dynamic_includes=load_fail_on_unconstrained_dynamic_includes,
    )


def apply_yaml_like_task_annotation_policy(
    *,
    role_path: str,
    readme_config_path: str | None,
    fail_on_yaml_like_task_annotations: bool | None,
    metadata: dict,
    load_fail_on_yaml_like_task_annotations: Callable[[str, str | None, bool], bool],
) -> dict:
    """Apply YAML-like task annotation policy via delegation."""
    from prism.scanner_config import (
        apply_yaml_like_task_annotation_policy as canonical_apply_yaml_like_task_annotation_policy,
    )

    return canonical_apply_yaml_like_task_annotation_policy(
        role_path=role_path,
        readme_config_path=readme_config_path,
        fail_on_yaml_like_task_annotations=fail_on_yaml_like_task_annotations,
        metadata=metadata,
        load_fail_on_yaml_like_task_annotations=load_fail_on_yaml_like_task_annotations,
    )


def _build_emit_scan_outputs_args_wrapper(
    *,
    output: str,
    output_format: str,
    concise_readme: bool,
    scanner_report_output: str | None,
    include_scanner_report_link: bool,
    payload: RunScanOutputPayload,
    template: str | None,
    dry_run: bool,
    runbook_output: str | None,
    runbook_csv_output: str | None,
) -> EmitScanOutputsArgs:
    """Wrapper to preserve type hints for partial binding."""
    from prism.scanner_io import (
        build_emit_scan_outputs_args as canonical_build_emit_scan_outputs_args,
    )

    return canonical_build_emit_scan_outputs_args(
        output=output,
        output_format=output_format,
        concise_readme=concise_readme,
        scanner_report_output=scanner_report_output,
        include_scanner_report_link=include_scanner_report_link,
        payload=payload,
        template=template,
        dry_run=dry_run,
        runbook_output=runbook_output,
        runbook_csv_output=runbook_csv_output,
    )


def build_emit_scan_outputs_args(
    build_emit_scan_outputs_args_fn: Callable[..., EmitScanOutputsArgs] | None = None,
    *,
    output: str | None = None,
    output_format: str | None = None,
    concise_readme: bool | None = None,
    scanner_report_output: str | None = None,
    include_scanner_report_link: bool | None = None,
    payload: RunScanOutputPayload | None = None,
    template: str | None = None,
    dry_run: bool | None = None,
    runbook_output: str | None = None,
    runbook_csv_output: str | None = None,
) -> EmitScanOutputsArgs:
    """Build emit scan outputs args via delegation."""
    resolved_output = output if output is not None else "README.md"
    resolved_output_format = output_format if output_format is not None else "markdown"
    resolved_concise_readme = concise_readme if concise_readme is not None else False
    resolved_include_scanner_report_link = (
        include_scanner_report_link if include_scanner_report_link is not None else True
    )
    resolved_payload = payload if payload is not None else {}
    resolved_dry_run = dry_run if dry_run is not None else False

    if callable(build_emit_scan_outputs_args_fn):
        # Called via partial binding
        return build_emit_scan_outputs_args_fn(
            output=resolved_output,
            output_format=resolved_output_format,
            concise_readme=resolved_concise_readme,
            scanner_report_output=scanner_report_output,
            include_scanner_report_link=resolved_include_scanner_report_link,
            payload=resolved_payload,
            template=template,
            dry_run=resolved_dry_run,
            runbook_output=runbook_output,
            runbook_csv_output=runbook_csv_output,
        )
    else:
        # Called directly
        return _build_emit_scan_outputs_args_wrapper(
            output=resolved_output,
            output_format=resolved_output_format,
            concise_readme=resolved_concise_readme,
            scanner_report_output=scanner_report_output,
            include_scanner_report_link=resolved_include_scanner_report_link,
            payload=resolved_payload,
            template=template,
            dry_run=resolved_dry_run,
            runbook_output=runbook_output,
            runbook_csv_output=runbook_csv_output,
        )


def emit_scan_outputs(
    args: dict[str, Any],
    emit_scan_outputs_fn: Callable,
    **kwargs: Any,
) -> Any:
    """Emit scan outputs via delegation."""
    # Map parameter names to match what emit_scan_outputs_fn expects
    mapped_kwargs = {}
    for k, v in kwargs.items():
        if k == "render_runbook":
            mapped_kwargs["render_runbook_fn"] = v
        elif k == "render_runbook_csv":
            mapped_kwargs["render_runbook_csv_fn"] = v
        else:
            mapped_kwargs[k] = v
    return emit_scan_outputs_fn(args, **mapped_kwargs)


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
    """Collect scan base context via delegation."""
    from prism.scanner_core.scan_state import (
        collect_scan_base_context as canonical_collect_scan_base_context,
    )

    return canonical_collect_scan_base_context(
        scan_options,
        load_fail_on_unconstrained_dynamic_includes,
        load_fail_on_yaml_like_task_annotations,
        load_non_authoritative_test_evidence_max_file_bytes,
        load_non_authoritative_test_evidence_max_files_scanned,
        load_non_authoritative_test_evidence_max_total_bytes,
        collect_scan_identity_and_artifacts=collect_scan_identity_and_artifacts,
        apply_scan_metadata_configuration=apply_scan_metadata_configuration,
        apply_unconstrained_dynamic_include_policy=apply_unconstrained_dynamic_include_policy,
        apply_yaml_like_task_annotation_policy=apply_yaml_like_task_annotation_policy,
        resolve_scan_identity=resolve_scan_identity,
        load_readme_marker_prefix=load_readme_marker_prefix,
        collect_scan_artifacts=collect_scan_artifacts,
    )


def build_scan_report_sidecar_args(
    *,
    concise_readme: bool,
    scanner_report_output: str | None,
    out_path: Path,
    include_scanner_report_link: bool,
    payload: RunScanOutputPayload,
    dry_run: bool,
) -> ScanReportSidecarArgs:
    """Build scan report sidecar args via delegation."""
    from prism.scanner_io import (
        build_scan_report_sidecar_args as canonical_build_scan_report_sidecar_args,
    )

    return canonical_build_scan_report_sidecar_args(
        concise_readme=concise_readme,
        scanner_report_output=scanner_report_output,
        out_path=out_path,
        include_scanner_report_link=include_scanner_report_link,
        payload=payload,
        dry_run=dry_run,
    )


def build_runbook_sidecar_args(
    *,
    runbook_output: str | None,
    runbook_csv_output: str | None,
    payload: RunScanOutputPayload,
) -> RunbookSidecarArgs:
    """Build runbook sidecar args via delegation."""
    from prism.scanner_io import (
        build_runbook_sidecar_args as canonical_build_runbook_sidecar_args,
    )

    return canonical_build_runbook_sidecar_args(
        runbook_output=runbook_output,
        runbook_csv_output=runbook_csv_output,
        payload=payload,
    )


def apply_scan_metadata_configuration(
    *,
    role_path: str,
    readme_config_path: str | None,
    adopt_heading_mode: str | None,
    include_task_parameters: bool,
    include_task_runbooks: bool,
    inline_task_runbooks: bool,
    include_collection_checks: bool,
    keep_unknown_style_sections: bool,
    meta: dict,
    requirements: list,
    metadata: ScanMetadata,
    build_requirements_display: (
        Callable[..., tuple[list[str], list[str]]] | None
    ) = None,
    enrich_scan_context_with_insights: (
        Callable[..., tuple[list[dict], dict, ScanMetadata]] | None
    ) = None,
    **kwargs: Any,
) -> tuple[list[str], ScanMetadata]:
    """Apply scan metadata configuration via delegation."""
    from prism.scanner_analysis import (
        apply_scan_metadata_configuration as canonical_apply_scan_metadata_configuration,
    )

    return canonical_apply_scan_metadata_configuration(
        role_path=role_path,
        readme_config_path=readme_config_path,
        adopt_heading_mode=adopt_heading_mode,
        include_task_parameters=include_task_parameters,
        include_task_runbooks=include_task_runbooks,
        inline_task_runbooks=inline_task_runbooks,
        include_collection_checks=include_collection_checks,
        keep_unknown_style_sections=keep_unknown_style_sections,
        meta=meta,
        requirements=requirements,
        metadata=metadata,
        build_requirements_display=build_requirements_display,
        **kwargs,
    )


def build_scan_output_payload(
    *,
    role_name: str,
    description: str,
    display_variables: dict,
    requirements_display: list,
    undocumented_default_filters: list,
    metadata: dict,
) -> RunScanOutputPayload:
    """Build scan output payload via delegation."""
    from prism.scanner_io import (
        build_scan_output_payload as canonical_build_scan_output_payload,
    )

    return canonical_build_scan_output_payload(
        role_name=role_name,
        description=description,
        display_variables=display_variables,
        requirements_display=requirements_display,
        undocumented_default_filters=undocumented_default_filters,
        metadata=metadata,
    )


def collect_scan_identity_and_artifacts(
    *,
    role_path: str,
    role_name_override: str | None,
    readme_config_path: str | None,
    include_vars_main: bool,
    exclude_path_patterns: list[str] | None,
    detailed_catalog: bool,
    resolve_scan_identity_fn: Callable[..., tuple[Any, Any, str, str]] | None = None,
    load_readme_marker_prefix_fn: Callable[..., str] | None = None,
    collect_scan_artifacts_fn: (
        Callable[..., tuple[dict, list, list, ScanMetadata]] | None
    ) = None,
) -> tuple[Any, Any, str, str, str, dict, list, list, ScanMetadata]:
    """Collect scan identity and artifacts via delegation."""
    from prism.scanner_analysis import (
        collect_scan_identity_and_artifacts as canonical_collect_scan_identity_and_artifacts,
    )

    return canonical_collect_scan_identity_and_artifacts(
        role_path=role_path,
        role_name_override=role_name_override,
        readme_config_path=readme_config_path,
        include_vars_main=include_vars_main,
        exclude_path_patterns=exclude_path_patterns,
        detailed_catalog=detailed_catalog,
        resolve_scan_identity_fn=resolve_scan_identity_fn,
        load_readme_marker_prefix_fn=load_readme_marker_prefix_fn,
        collect_scan_artifacts_fn=collect_scan_artifacts_fn,
    )


def build_runtime_scan_state(
    build_runtime_scan_state_fn: Callable,
    **kwargs: Any,
) -> Any:
    """Build runtime scan state via delegation."""
    return build_runtime_scan_state_fn(**kwargs)


def scan_policy_scope(
    scan_policy_scope_fn: Callable,
    **kwargs: Any,
) -> Any:
    """Apply scan policy scope via delegation."""
    return scan_policy_scope_fn(**kwargs)


def render_primary_scan_output(
    *,
    out_path: Path,
    output_format: str,
    template: str | None,
    dry_run: bool,
    output_payload: dict[str, Any],
    render_primary_scan_output_fn: Callable,
    render_and_write_scan_output: Callable,
    **kwargs: Any,
) -> Any:
    """Render primary scan output via delegation."""
    return render_primary_scan_output_fn(
        out_path=out_path,
        output_format=output_format,
        template=template,
        dry_run=dry_run,
        output_payload=output_payload,
        render_and_write_scan_output=render_and_write_scan_output,
        **kwargs,
    )


def prepare_scan_context(scan_options: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Prepare scan context via delegation."""
    from prism.scanner_core.scan_state import (
        prepare_scan_context as canonical_prepare_scan_context,
    )

    return canonical_prepare_scan_context(scan_options=scan_options, **kwargs)


def finalize_scan_context_payload(
    *,
    rp: str,
    role_name: str,
    description: str,
    requirements_display: list,
    undocumented_default_filters: list[dict],
    display_variables: dict,
    metadata: ScanMetadata,
) -> dict[str, Any]:
    """Finalize scan context payload via delegation."""
    from prism.scanner_analysis import (
        finalize_scan_context_payload as canonical_finalize_scan_context_payload,
    )

    return canonical_finalize_scan_context_payload(
        rp=rp,
        role_name=role_name,
        description=description,
        requirements_display=requirements_display,
        undocumented_default_filters=undocumented_default_filters,
        display_variables=display_variables,
        metadata=metadata,
    )


def enrich_scan_context_with_insights(
    *,
    role_path: str,
    role_name: str,
    description: str,
    vars_seed_paths: list[str] | None,
    include_vars_main: bool,
    exclude_path_patterns: list[str] | None,
    marker_prefix: str,
    found: list,
    variables: dict,
    metadata: ScanMetadata,
    style_readme_path: str | None,
    style_source_path: str | None,
    style_guide_skeleton: bool,
    compare_role_path: str | None,
    ignore_unresolved_internal_underscore_references: bool,
    non_authoritative_test_evidence_max_file_bytes: int,
    non_authoritative_test_evidence_max_files_scanned: int,
    non_authoritative_test_evidence_max_total_bytes: int,
    collect_variable_insights_and_default_filter_findings: (
        Callable[..., tuple[list[dict], list[dict], dict]] | None
    ) = None,
    build_doc_insights: Callable[..., dict] | None = None,
    apply_style_and_comparison_metadata: Callable[..., None] | None = None,
    di_container=None,  # DI container for plugins
    policy_context: PolicyContext | None = None,
) -> tuple[list[dict], dict, ScanMetadata]:
    """Enrich scan context with insights via delegation."""
    from prism.scanner_analysis import (
        enrich_scan_context_with_insights as canonical_enrich_scan_context_with_insights,
    )

    return canonical_enrich_scan_context_with_insights(
        role_path=role_path,
        role_name=role_name,
        description=description,
        vars_seed_paths=vars_seed_paths,
        include_vars_main=include_vars_main,
        exclude_path_patterns=exclude_path_patterns,
        marker_prefix=marker_prefix,
        found=found,
        variables=variables,
        metadata=metadata,
        style_readme_path=style_readme_path,
        style_source_path=style_source_path,
        style_guide_skeleton=style_guide_skeleton,
        compare_role_path=compare_role_path,
        ignore_unresolved_internal_underscore_references=ignore_unresolved_internal_underscore_references,
        non_authoritative_test_evidence_max_file_bytes=non_authoritative_test_evidence_max_file_bytes,
        non_authoritative_test_evidence_max_files_scanned=non_authoritative_test_evidence_max_files_scanned,
        non_authoritative_test_evidence_max_total_bytes=non_authoritative_test_evidence_max_total_bytes,
        collect_variable_insights_and_default_filter_findings=collect_variable_insights_and_default_filter_findings,
        build_doc_insights=build_doc_insights,
        apply_style_and_comparison_metadata=apply_style_and_comparison_metadata,
        di_container=di_container,
        policy_context=policy_context,
    )
