"""Repo command execution for prism CLI."""

from __future__ import annotations

import argparse

from .repo_services import (
    build_sparse_clone_paths,
    checkout_repo_scan_role,
    clone_repo,
    fetch_repo_directory_names,
    fetch_repo_file,
    normalize_repo_scan_result_payload,
    prepare_repo_scan_inputs,
    repo_name_from_url,
    repo_path_looks_like_role,
    repo_scan_workspace,
    resolve_repo_scan_scanner_report_relpath,
    resolve_repo_scan_target,
    resolve_style_readme_candidate,
)
from .scanner import resolve_default_style_guide_source
from .cli import run_scan
from .feedback import load_feedback, apply_feedback_recommendations
from .cli_commands import (
    _resolve_vars_context_paths,
    _resolve_include_collection_checks,
    _resolve_effective_readme_config,
)
from .cli_presenters import _emit_success, _finalize_repo_json_output
from .cli import _save_style_comparison_artifacts


def handle_repo_command(args: argparse.Namespace) -> int:
    """Execute the repo command."""
    vars_context_paths = _resolve_vars_context_paths(args)

    with repo_scan_workspace() as workspace:
        if args.verbose:
            print(f"Cloning: {args.repo_url}")
        checkout = resolve_repo_scan_target(
            repo_url=args.repo_url,
            workspace=workspace,
            repo_role_path=args.repo_role_path,
            repo_style_readme_path=args.repo_style_readme_path,
            style_readme_path=args.style_readme,
            repo_ref=args.repo_ref,
            repo_timeout=args.repo_timeout,
            lightweight_readme_only=False,
            checkout_repo_scan_role_fn=checkout_repo_scan_role,
            prepare_repo_scan_inputs_fn=prepare_repo_scan_inputs,
            fetch_repo_directory_names_fn=fetch_repo_directory_names,
            repo_path_looks_like_role_fn=repo_path_looks_like_role,
            fetch_repo_file_fn=fetch_repo_file,
            clone_repo_fn=clone_repo,
            build_sparse_clone_paths_fn=build_sparse_clone_paths,
            resolve_style_readme_candidate_fn=resolve_style_readme_candidate,
        )
        style_readme_path = checkout.effective_style_readme_path
        if args.create_style_guide and not style_readme_path:
            style_readme_path = (
                args.style_source or resolve_default_style_guide_source()
            )

        include_collection_checks = _resolve_include_collection_checks(
            args.feedback_from_learn,
            args.include_collection_checks,
            load_feedback=load_feedback,
            apply_feedback_recommendations=apply_feedback_recommendations,
        )
        if include_collection_checks is None:
            return 1

        outpath = run_scan(
            str(checkout.role_path),
            output=args.output,
            template=args.template,
            output_format=args.format,
            compare_role_path=args.compare_role_path,
            style_readme_path=style_readme_path,
            role_name_override=repo_name_from_url(args.repo_url),
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
        if args.format == "json":
            scanner_report_relpath = resolve_repo_scan_scanner_report_relpath(
                concise_readme=args.concise_readme,
                scanner_report_output=args.scanner_report_output,
                primary_output_path=args.output,
            )
            outpath = _finalize_repo_json_output(
                outpath,
                dry_run=args.dry_run,
                repo_style_readme_path=checkout.resolved_repo_style_readme_path,
                scanner_report_relpath=scanner_report_relpath,
                normalize_repo_json_payload=normalize_repo_scan_result_payload,
            )

        if args.dry_run:
            print(outpath, end="")
            return _emit_success(args, outpath)

        effective_readme_config_path = _resolve_effective_readme_config(
            checkout.role_path,
            args.readme_config,
        )
        style_source_path, style_demo_path = _save_style_comparison_artifacts(
            style_readme_path,
            outpath,
            repo_name_from_url(args.repo_url),
            effective_readme_config_path,
            args.keep_unknown_style_sections,
        )
        return _emit_success(args, outpath, style_source_path, style_demo_path)
