"""Collection command execution for prism CLI."""

from __future__ import annotations

import argparse
import json

from .api import scan_collection
from .cli_commands import (
    _resolve_vars_context_paths,
    _resolve_include_collection_checks,
)
from .feedback import load_feedback, apply_feedback_recommendations
from .cli_presenters import (
    _render_collection_markdown,
    _emit_success,
    _persist_collection_role_markdown_documents,
    _resolve_cli_output_path,
)


def handle_collection_command(args: argparse.Namespace) -> int:
    """Execute the collection command."""
    vars_context_paths = _resolve_vars_context_paths(args)

    include_collection_checks = _resolve_include_collection_checks(
        args.feedback_from_learn,
        args.include_collection_checks,
        load_feedback=load_feedback,
        apply_feedback_recommendations=apply_feedback_recommendations,
    )
    if include_collection_checks is None:
        return 1

    payload = scan_collection(
        args.collection_path,
        compare_role_path=args.compare_role_path,
        style_readme_path=args.style_readme,
        vars_seed_paths=vars_context_paths,
        concise_readme=args.concise_readme,
        scanner_report_output=args.scanner_report_output,
        include_vars_main=args.variable_sources == "defaults+vars",
        include_scanner_report_link=args.include_scanner_report_link,
        readme_config_path=args.readme_config,
        adopt_heading_mode=args.adopt_heading_mode,
        style_guide_skeleton=args.create_style_guide,
        keep_unknown_style_sections=args.keep_unknown_style_sections,
        exclude_path_patterns=args.exclude_path,
        style_source_path=args.style_source,
        policy_config_path=args.policy_config,
        fail_on_unconstrained_dynamic_includes=args.fail_on_unconstrained_dynamic_includes,
        fail_on_yaml_like_task_annotations=args.fail_on_yaml_like_task_annotations,
        ignore_unresolved_internal_underscore_references=args.ignore_unresolved_internal_underscore_references,
        detailed_catalog=args.detailed_catalog,
        include_collection_checks=include_collection_checks,
        include_task_parameters=args.task_parameters,
        include_task_runbooks=args.task_runbooks,
        inline_task_runbooks=args.inline_task_runbooks,
        include_rendered_readme=args.format == "md",
        runbook_output_dir=args.runbook_output,
        runbook_csv_output_dir=args.runbook_csv_output,
        include_traceback=args.verbose,
    )
    rendered = (
        json.dumps(payload, indent=2)
        if args.format == "json"
        else _render_collection_markdown(payload)
    )
    if args.dry_run:
        print(rendered, end="")
        return _emit_success(args, rendered)

    output_path = _resolve_cli_output_path(args.output, args.format)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    if args.format == "md":
        _persist_collection_role_markdown_documents(
            output_path=output_path,
            payload=payload,
        )
    return _emit_success(args, str(output_path.resolve()))
