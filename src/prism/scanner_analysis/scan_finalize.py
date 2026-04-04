"""Scan context finalization and enrichment functions."""

from __future__ import annotations

from typing import Any, Callable

from prism.scanner_data.contracts_request import (
    PolicyContext,
    ScanContextPayload,
    ScanMetadata,
)


def finalize_scan_context_payload(
    *,
    rp: str,
    role_name: str,
    description: str,
    requirements_display: list,
    undocumented_default_filters: list[dict],
    display_variables: dict,
    metadata: ScanMetadata,
) -> ScanContextPayload:
    """Return normalized context payload used by run_scan output emission."""
    return ScanContextPayload(
        rp=rp,
        role_name=role_name,
        description=description,
        requirements_display=requirements_display,
        undocumented_default_filters=undocumented_default_filters,
        display_variables=display_variables,
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
    """Resolve scan identity and collect core role artifacts."""
    from prism.scanner_extract.discovery import resolve_scan_identity, load_meta
    from prism.scanner_config.marker import load_readme_marker_prefix
    from prism.scanner_core.scan_facade_helpers import collect_scan_artifacts

    effective_resolve_scan_identity = resolve_scan_identity_fn or resolve_scan_identity
    effective_load_readme_marker_prefix = (
        load_readme_marker_prefix_fn or load_readme_marker_prefix
    )
    effective_collect_scan_artifacts = (
        collect_scan_artifacts_fn or collect_scan_artifacts
    )

    rp, meta, role_name, description = effective_resolve_scan_identity(
        role_path,
        role_name_override,
        load_meta_fn=load_meta,
    )
    marker_config_warnings: list[str] = []
    marker_prefix = effective_load_readme_marker_prefix(
        role_path,
        readme_config_path,
        warning_collector=marker_config_warnings,
    )
    variables, requirements, found, metadata = effective_collect_scan_artifacts(
        role_path=role_path,
        include_vars_main=include_vars_main,
        exclude_path_patterns=exclude_path_patterns,
        detailed_catalog=detailed_catalog,
        marker_prefix=marker_prefix,
    )
    if marker_config_warnings:
        metadata = {**metadata, "readme_marker_config_warnings": marker_config_warnings}
    return (
        rp,
        meta,
        role_name,
        description,
        marker_prefix,
        variables,
        requirements,
        found,
        metadata,
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
    load_readme_section_config: Callable[..., dict | None] | None = None,
    apply_readme_section_config: (
        Callable[[ScanMetadata, dict | None], None] | None
    ) = None,
) -> tuple[list, dict]:
    """Apply scan options that shape metadata and requirements rendering."""
    if build_requirements_display is None:
        from prism.scanner_extract.requirements_wrapper import (
            build_requirements_display as _build_requirements_display,
        )

        build_requirements_display = _build_requirements_display

    if load_readme_section_config is None:
        from prism.scanner_config.readme import (
            load_readme_section_config as _load_readme_section_config,
        )

        load_readme_section_config = _load_readme_section_config

    if apply_readme_section_config is None:
        from prism.scanner_config.readme import (
            apply_readme_section_config as _apply_readme_section_config,
        )

        apply_readme_section_config = _apply_readme_section_config

    updates = {}
    updates["include_task_parameters"] = bool(include_task_parameters)
    updates["include_task_runbooks"] = bool(include_task_runbooks)
    updates["inline_task_runbooks"] = bool(inline_task_runbooks)

    requirements_display, collection_compliance_notes = build_requirements_display(
        requirements=requirements,
        meta=meta,
        features=metadata.get("features") or {},
        include_collection_checks=include_collection_checks,
    )
    updates["collection_compliance_notes"] = collection_compliance_notes  # type: ignore[assignment]
    updates["keep_unknown_style_sections"] = keep_unknown_style_sections

    readme_section_config_warnings: list[str] = []
    readme_section_config = load_readme_section_config(
        role_path,
        config_path=readme_config_path,
        adopt_heading_mode=adopt_heading_mode,
        strict=False,
        warning_collector=readme_section_config_warnings,
    )
    if readme_section_config_warnings:
        updates["readme_section_config_warnings"] = readme_section_config_warnings  # type: ignore[assignment]
    effective_metadata = {**metadata, **updates}
    apply_readme_section_config(effective_metadata, readme_section_config)
    return requirements_display, effective_metadata


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
    """Add variable/doc/style insights to scan metadata and display payloads."""
    undocumented_default_filters: list[dict] = []
    display_variables: dict = {}
    if collect_variable_insights_and_default_filter_findings is not None:
        _variable_insights, undocumented_default_filters, display_variables = (
            collect_variable_insights_and_default_filter_findings(
                di_container=di_container,
                role_path=role_path,
                vars_seed_paths=vars_seed_paths,
                include_vars_main=include_vars_main,
                exclude_path_patterns=exclude_path_patterns,
                marker_prefix=marker_prefix,
                found_default_filters=found,
                variables=variables,
                metadata=metadata,
                style_readme_path=style_readme_path,
                policy_context=policy_context,
                ignore_unresolved_internal_underscore_references=ignore_unresolved_internal_underscore_references,
                non_authoritative_test_evidence_max_file_bytes=non_authoritative_test_evidence_max_file_bytes,
                non_authoritative_test_evidence_max_files_scanned=non_authoritative_test_evidence_max_files_scanned,
                non_authoritative_test_evidence_max_total_bytes=non_authoritative_test_evidence_max_total_bytes,
            )
        )

    if build_doc_insights is not None:
        doc_insights = build_doc_insights(
            role_name=role_name,
            description=description,
            metadata=metadata,
            variables=variables,
            variable_insights=metadata.get("variable_insights") or [],
        )
    else:
        doc_insights = {}
    metadata["doc_insights"] = doc_insights

    if apply_style_and_comparison_metadata is not None:
        apply_style_and_comparison_metadata(
            metadata=metadata,
            style_readme_path=style_readme_path,
            style_source_path=style_source_path,
            style_guide_skeleton=style_guide_skeleton,
            compare_role_path=compare_role_path,
            role_path=role_path,
            exclude_path_patterns=exclude_path_patterns,
            policy_context=policy_context,
        )

    return undocumented_default_filters, display_variables, metadata
