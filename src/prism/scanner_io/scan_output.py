"""Scan output building and emission functions."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from prism.scanner_data.contracts_output import (
    EmitScanOutputsArgs,
    RunScanOutputPayload,
    RunbookSidecarArgs,
    ScanReportSidecarArgs,
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
    """Build the shared payload used for scanner report and primary output rendering."""
    return {
        "role_name": role_name,
        "description": description,
        "display_variables": display_variables,
        "requirements_display": requirements_display,
        "undocumented_default_filters": undocumented_default_filters,
        "metadata": metadata,
    }


def build_emit_scan_outputs_args(
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
    """Build the typed argument bundle for emit_scan_outputs."""
    return {
        "output": output,
        "output_format": output_format,
        "concise_readme": concise_readme,
        "scanner_report_output": scanner_report_output,
        "include_scanner_report_link": include_scanner_report_link,
        "role_name": payload["role_name"],
        "description": payload["description"],
        "display_variables": payload["display_variables"],
        "requirements_display": payload["requirements_display"],
        "undocumented_default_filters": payload["undocumented_default_filters"],
        "metadata": payload["metadata"],
        "template": template,
        "dry_run": dry_run,
        "runbook_output": runbook_output,
        "runbook_csv_output": runbook_csv_output,
    }


def build_scan_report_sidecar_args(
    *,
    concise_readme: bool,
    scanner_report_output: str | None,
    out_path: Path,
    include_scanner_report_link: bool,
    payload: RunScanOutputPayload,
    dry_run: bool,
) -> ScanReportSidecarArgs:
    """Build the typed argument bundle for scanner report sidecar emission."""
    return {
        "concise_readme": concise_readme,
        "scanner_report_output": scanner_report_output,
        "out_path": out_path,
        "include_scanner_report_link": include_scanner_report_link,
        "role_name": payload["role_name"],
        "description": payload["description"],
        "display_variables": payload["display_variables"],
        "requirements_display": payload["requirements_display"],
        "undocumented_default_filters": payload["undocumented_default_filters"],
        "metadata": payload["metadata"],
        "dry_run": dry_run,
    }


def build_runbook_sidecar_args(
    *,
    runbook_output: str | None,
    runbook_csv_output: str | None,
    payload: RunScanOutputPayload,
) -> RunbookSidecarArgs:
    """Build the typed argument bundle for optional runbook sidecar emission."""
    return {
        "runbook_output": runbook_output,
        "runbook_csv_output": runbook_csv_output,
        "role_name": payload["role_name"],
        "metadata": payload["metadata"],
    }


def render_primary_scan_output(
    *,
    out_path: Path,
    output_format: str,
    template: str | None,
    dry_run: bool,
    output_payload: RunScanOutputPayload,
    render_primary_scan_output_fn: Callable[..., str | bytes],
    render_and_write_scan_output: Callable[..., str | bytes],
) -> str | bytes:
    """Render and optionally write the primary scan output."""
    return render_primary_scan_output_fn(
        out_path=out_path,
        output_format=output_format,
        template=template,
        dry_run=dry_run,
        output_payload=output_payload,
        render_and_write_scan_output=render_and_write_scan_output,
    )


def emit_scan_outputs(
    args: EmitScanOutputsArgs,
    *,
    emit_scan_outputs_fn: Callable[..., str | bytes],
    build_scanner_report_markdown: Callable[..., str],
    render_and_write_scan_output: Callable[..., str | bytes],
    render_runbook: Callable[..., str],
    render_runbook_csv: Callable[..., str],
) -> str | bytes:
    """Render primary outputs and optional sidecars for a scanner run."""
    return emit_scan_outputs_fn(
        args,
        build_scanner_report_markdown=build_scanner_report_markdown,
        render_and_write_output=render_and_write_scan_output,
        render_runbook_fn=render_runbook,
        render_runbook_csv_fn=render_runbook_csv,
    )
