"""Scanner I/O package - output rendering and YAML loading utilities.

Current capability ownership:
- primary output rendering and output-path resolution
- scanner-report and runbook sidecar emission
- collection markdown rendering and runbook artifact persistence
- YAML candidate iteration and parse-failure collection
"""

from __future__ import annotations

from prism.scanner_io.loader import (
    collect_yaml_parse_failures,
    iter_role_yaml_candidates,
    load_yaml_file,
    map_argument_spec_type,
    parse_yaml_candidate,
)
from prism.scanner_io.collection_renderer import render_collection_markdown
from prism.scanner_io.output import (
    FinalOutputPayload,
    build_final_output_payload,
    render_final_output,
    resolve_output_path,
    write_output,
)
from prism.scanner_io.scan_output import (
    build_emit_scan_outputs_args,
    build_scan_output_payload,
    build_scan_report_sidecar_args,
    build_runbook_sidecar_args,
)

__all__ = [
    "collect_yaml_parse_failures",
    "iter_role_yaml_candidates",
    "load_yaml_file",
    "map_argument_spec_type",
    "parse_yaml_candidate",
    "render_collection_markdown",
    "FinalOutputPayload",
    "build_final_output_payload",
    "render_final_output",
    "resolve_output_path",
    "write_output",
    "build_emit_scan_outputs_args",
    "build_scan_output_payload",
    "build_scan_report_sidecar_args",
    "build_runbook_sidecar_args",
]


def __getattr__(name: str) -> object:
    """Enforce module public API at runtime."""
    if name.startswith("_"):
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}' "
            f"(private member; only __all__ symbols are public)"
        )
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose only public API in dir() and introspection."""
    return sorted(__all__)
