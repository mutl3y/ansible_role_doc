"""Role command execution for prism CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from .scanner import resolve_default_style_guide_source
from .cli import run_scan
from .feedback import load_feedback, apply_feedback_recommendations
from .cli_commands import (
    _resolve_vars_context_paths,
    _resolve_include_collection_checks,
    _resolve_effective_readme_config,
)
from .cli_presenters import _emit_success
from .cli import _save_style_comparison_artifacts


def handle_role_command(args: argparse.Namespace) -> int:
    """Execute the role command."""
    vars_context_paths = _resolve_vars_context_paths(args)

    include_collection_checks = _resolve_include_collection_checks(
        args.feedback_from_learn,
        args.include_collection_checks,
        load_feedback=load_feedback,
        apply_feedback_recommendations=apply_feedback_recommendations,
    )
    if include_collection_checks is None:
        return 1

    style_readme_path = args.style_readme
    if args.create_style_guide and not style_readme_path:
        style_readme_path = args.style_source or resolve_default_style_guide_source()
    outpath = run_scan(
        args.role_path,
        output=args.output,
        template=args.template,
        output_format=args.format,
        compare_role_path=args.compare_role_path,
        style_readme_path=style_readme_path,
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
        runbook_output=args.runbook_output,
        runbook_csv_output=args.runbook_csv_output,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(outpath, end="")
        return _emit_success(args, outpath)

    effective_readme_config_path = _resolve_effective_readme_config(
        Path(args.role_path),
        args.readme_config,
    )
    style_source_path, style_demo_path = _save_style_comparison_artifacts(
        args.style_readme,
        outpath,
        role_config_path=effective_readme_config_path,
        keep_unknown_style_sections=args.keep_unknown_style_sections,
    )
    return _emit_success(args, outpath, style_source_path, style_demo_path)
