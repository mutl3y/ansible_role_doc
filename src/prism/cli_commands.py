"""Command and parser orchestration for prism CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError

from .errors import (
    PrismRuntimeError,
    REPO_SCAN_PAYLOAD_JSON_INVALID,
    REPO_SCAN_PAYLOAD_SHAPE_INVALID,
    REPO_SCAN_PAYLOAD_TYPE_INVALID,
)
from .scanner import SECTION_CONFIG_FILENAMES

_EXIT_CODE_GENERIC_ERROR = 2
_EXIT_CODE_NOT_FOUND = 3
_EXIT_CODE_PERMISSION_DENIED = 4
_EXIT_CODE_JSON_PAYLOAD_ERROR = 5
_EXIT_CODE_NETWORK_ERROR = 6
_EXIT_CODE_OS_ERROR = 7
_EXIT_CODE_INTERRUPTED = 130


def _add_shared_scan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--compare-role-path",
        default=None,
        help="Optional local role path used as a baseline comparison in the generated review.",
    )
    parser.add_argument(
        "--style-readme",
        default=None,
        help="Optional local README path used as a style guide for section order and headings.",
    )
    parser.add_argument(
        "--style-source",
        default=None,
        help=(
            "Explicit style source markdown path used when resolving style-guide skeletons "
            "or as fallback style input when --style-readme is not provided."
        ),
    )
    parser.add_argument(
        "--create-style-guide",
        action="store_true",
        help=(
            "Generate a style-guide skeleton README that keeps only section headings/order. "
            "When used without --style-readme, style source is resolved from env/cwd/XDG/system/bundled defaults."
        ),
    )
    parser.add_argument(
        "--vars-context-path",
        action="append",
        default=None,
        help=(
            "Optional external variable context file or directory (can be passed multiple times), "
            "for example group_vars/ to improve required/undocumented variable detection. "
            "Context paths are treated as non-authoritative hints."
        ),
    )
    parser.add_argument(
        "--vars-seed",
        action="append",
        default=None,
        help=(
            "Deprecated alias for --vars-context-path. Optional vars seed file or directory "
            "(can be passed multiple times), for example group_vars/ to prime "
            "required/undocumented variable detection."
        ),
    )
    parser.add_argument(
        "--concise-readme",
        action="store_true",
        help="Keep README concise and write scanner-heavy sections to a sidecar report.",
    )
    parser.add_argument(
        "--scanner-report-output",
        default=None,
        help="Optional output path for scanner sidecar report in concise mode.",
    )
    parser.add_argument(
        "--include-scanner-report-link",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Include a scanner report section/link in concise README output "
            "(use --no-include-scanner-report-link to hide it)."
        ),
    )
    parser.add_argument(
        "--variable-sources",
        choices=("defaults+vars", "defaults-only"),
        default="defaults-only",
        help=(
            "Select which role variable files are documented: "
            "'defaults-only' (default) or 'defaults+vars'."
        ),
    )
    parser.add_argument(
        "--readme-config",
        default=None,
        help=(
            "Optional YAML config controlling README section visibility "
            "(defaults to <role>/.prism.yml when present)."
        ),
    )
    parser.add_argument(
        "--policy-config",
        default=None,
        help=(
            "Optional pattern-policy override YAML path used during scanning "
            "(highest precedence over env/cwd/XDG/system policy sources)."
        ),
    )
    parser.add_argument(
        "--fail-on-unconstrained-dynamic-includes",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Fail scan when unconstrained dynamic includes are detected "
            "(include_tasks/import_tasks/include_role/import_role). "
            "Overrides scan.fail_on_unconstrained_dynamic_includes from .prism.yml "
            "when explicitly set."
        ),
    )
    parser.add_argument(
        "--fail-on-yaml-like-task-annotations",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Fail scan when YAML-like marker comment payloads are detected "
            "(for example key: value). Overrides "
            "scan.fail_on_yaml_like_task_annotations from .prism.yml "
            "when explicitly set."
        ),
    )
    parser.add_argument(
        "--ignore-unresolved-internal-underscore-references",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Suppress unresolved variable findings for underscore-prefixed "
            "internal names (for example _tmp, __state). Overrides "
            "scan.ignore_unresolved_internal_underscore_references from .prism.yml "
            "when explicitly set."
        ),
    )
    parser.add_argument(
        "--adopt-heading-mode",
        choices=("canonical", "style", "popular"),
        default=None,
        help=(
            "Section heading mode when using README config include_sections: "
            "canonical (default), style (use include_sections labels), or popular "
            "(use bundled display titles). Can also be set via "
            "readme.adopt_heading_mode in .prism.yml."
        ),
    )
    parser.add_argument(
        "--keep-unknown-style-sections",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Keep unmapped headings from style README sources as placeholder sections "
            "(enabled by default; use --no-keep-unknown-style-sections to suppress)."
        ),
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=None,
        help=(
            "Exclude role-relative paths or glob patterns from analysis "
            "(can be passed multiple times; examples: templates/*, tests/**, vars/main.yml)."
        ),
    )
    parser.add_argument(
        "--detailed-catalog",
        action="store_true",
        help="Include detailed task and handler tables in generated README sections.",
    )
    parser.add_argument(
        "--task-parameters",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include compact task parameter values in detailed task summary tables.",
    )
    parser.add_argument(
        "--task-runbooks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Render task runbook/comment details when task annotations are present.",
    )
    parser.add_argument(
        "--inline-task-runbooks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Inline short runbook snippets in the task summary table.",
    )
    parser.add_argument(
        "--runbook-output",
        default=None,
        help=(
            "Generate a standalone runbook markdown file. For the 'role' command, "
            "provide a file path (e.g. RUNBOOK.md). For 'collection' and 'repo' commands, "
            "provide a directory path; per-role runbook files will be written there."
        ),
    )
    parser.add_argument(
        "--runbook-csv-output",
        default=None,
        help=(
            "Generate runbook CSV output (columns: file, task_name, step). "
            "For the 'role' command, provide a file path (e.g. RUNBOOK.csv). "
            "For 'collection' and 'repo' commands, provide a directory path; "
            "per-role CSV files will be written there."
        ),
    )
    parser.add_argument(
        "--include-collection-checks",
        action="store_true",
        help="Include collection compliance audit notes in requirements sections (off by default).",
    )
    parser.add_argument(
        "--feedback-from-learn",
        default=None,
        help=(
            "Optional feedback source for guided audit recommendations from prism-learn. "
            "Can be a local file path (feedback.json) or HTTPS API endpoint URL. "
            "Feedback can override CLI flags based on aggregate role analysis."
        ),
    )


def _add_common_output_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_template: bool,
    format_choices: tuple[str, ...],
) -> None:
    parser.add_argument(
        "-o", "--output", default="README.md", help="Output README file path"
    )
    if include_template:
        parser.add_argument(
            "-t",
            "--template",
            default=None,
            help="Template path (optional). If omitted, uses bundled template.",
        )
    parser.add_argument(
        "-f",
        "--format",
        default=format_choices[0],
        choices=format_choices,
        help=f"Output format ({', '.join(format_choices)}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render output without writing files; prints the rendered result to stdout.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )


def _add_repo_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-url",
        required=True,
        help="GitHub/Git repository URL to clone and scan.",
    )
    parser.add_argument(
        "--repo-ref",
        default=None,
        help="Optional branch, tag, or ref to clone from the repository.",
    )
    parser.add_argument(
        "--repo-role-path",
        default=".",
        help="Role path inside the cloned repository (default: repository root).",
    )
    parser.add_argument(
        "--repo-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for repository clone operations (default: 60).",
    )
    parser.add_argument(
        "--repo-style-readme-path",
        default=None,
        help="Optional README path inside a cloned repository to use as a style guide.",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prism",
        description="Generate documentation for Ansible roles and collections.",
    )
    subparsers = p.add_subparsers(dest="command")
    subparsers.required = True

    role_parser = subparsers.add_parser("role", help="Document a local role")
    role_parser.add_argument(
        "role_path", help="Path to the Ansible role directory to scan"
    )
    _add_shared_scan_arguments(role_parser)
    _add_common_output_arguments(
        role_parser,
        include_template=True,
        format_choices=("md", "html", "json", "pdf"),
    )

    collection_parser = subparsers.add_parser(
        "collection", help="Document a local Ansible collection root"
    )
    collection_parser.add_argument(
        "collection_path",
        help="Path to the Ansible collection root (requires galaxy.yml and roles/)",
    )
    _add_shared_scan_arguments(collection_parser)
    _add_common_output_arguments(
        collection_parser,
        include_template=False,
        format_choices=("md", "json"),
    )

    repo_parser = subparsers.add_parser(
        "repo", help="Document a role from a repository source"
    )
    _add_repo_arguments(repo_parser)
    _add_shared_scan_arguments(repo_parser)
    _add_common_output_arguments(
        repo_parser,
        include_template=True,
        format_choices=("md", "html", "json", "pdf"),
    )

    completion_parser = subparsers.add_parser(
        "completion", help="Generate shell completion output"
    )
    completion_parser.add_argument(
        "shell", choices=("bash",), help="Shell to generate completion for"
    )
    return p


def _collect_option_strings(parser: argparse.ArgumentParser) -> list[str]:
    options: set[str] = set()
    for action in parser._actions:
        for option in getattr(action, "option_strings", []):
            if option in {"-h", "--help"}:
                continue
            options.add(option)
    return sorted(options)


def _build_bash_completion_script(
    *,
    parser_factory=build_parser,
) -> str:
    parser = parser_factory()
    subparsers_action = next(
        (
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ),
        None,
    )
    if subparsers_action is None:
        raise RuntimeError("subcommand parser is not configured")

    commands = sorted(subparsers_action.choices)
    command_words = " ".join(commands)

    command_options: dict[str, str] = {}
    for command in commands:
        subparser = subparsers_action.choices[command]
        words: list[str] = []
        words.extend(_collect_option_strings(subparser))
        for action in subparser._actions:
            if action.option_strings:
                continue
            if action.dest == "help":
                continue
            if isinstance(action.choices, (list, tuple)):
                words.extend(str(choice) for choice in action.choices)
        command_options[command] = " ".join(sorted(set(words)))

    case_lines: list[str] = []
    for command in commands:
        options = command_options.get(command, "")
        case_lines.extend(
            [
                f"        {command})",
                f'            opts="{options}"',
                "            ;;",
            ]
        )

    script = [
        "# prism bash completion (generated)",
        "_prism_completion() {",
        "    local cur prev cmd opts",
        "    COMPREPLY=()",
        '    cur="${COMP_WORDS[COMP_CWORD]}"',
        '    prev="${COMP_WORDS[COMP_CWORD-1]}"',
        '    cmd="${COMP_WORDS[1]}"',
        "",
        "    if [[ ${COMP_CWORD} -eq 1 ]]; then",
        f'        COMPREPLY=( $(compgen -W "{command_words}" -- "$cur") )',
        "        return 0",
        "    fi",
        "",
        '    case "$cmd" in',
        *case_lines,
        "        *)",
        '            opts=""',
        "            ;;",
        "    esac",
        "",
        '    if [[ "$cur" == -* ]]; then',
        '        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )',
        "        return 0",
        "    fi",
        "",
        '    if [[ "$cmd" == "completion" && ${COMP_CWORD} -eq 2 ]]; then',
        '        COMPREPLY=( $(compgen -W "bash" -- "$cur") )',
        "        return 0",
        "    fi",
        "",
        '    COMPREPLY=( $(compgen -f -- "$cur") )',
        "}",
        "complete -F _prism_completion prism",
        "",
    ]
    return "\n".join(script)


def _resolve_effective_readme_config(
    role_path: Path,
    explicit_config_path: str | None,
) -> str | None:
    if explicit_config_path:
        return explicit_config_path
    for cfg_name in SECTION_CONFIG_FILENAMES:
        default_cfg = role_path / cfg_name
        if default_cfg.is_file():
            return str(default_cfg)
    return None


def _resolve_vars_context_paths(args: argparse.Namespace) -> list[str] | None:
    context_paths = list(args.vars_context_path or [])
    legacy_paths = list(args.vars_seed or [])
    if legacy_paths:
        print(
            "Warning: --vars-seed is deprecated and will be removed in a future release; "
            "use --vars-context-path instead.",
            file=sys.stderr,
        )
        context_paths.extend(legacy_paths)
    return context_paths or None


def _resolve_include_collection_checks(
    feedback_source: str | None,
    include_collection_checks: bool,
    *,
    load_feedback,
    apply_feedback_recommendations,
) -> bool | None:
    try:
        feedback = load_feedback(feedback_source)
    except (
        FileNotFoundError,
        HTTPError,
        URLError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print(f"Error loading feedback: {exc}", file=sys.stderr)
        return None

    applied = apply_feedback_recommendations(feedback, include_collection_checks)
    return bool(applied["include_collection_checks"])


def _normalize_repo_json_payload(
    rendered_payload: str,
    *,
    repo_style_readme_path: str | None,
    scanner_report_relpath: str | None,
    normalize_repo_scan_result_payload,
) -> str:
    try:
        normalized_payload = normalize_repo_scan_result_payload(
            rendered_payload,
            repo_style_readme_path=repo_style_readme_path,
            scanner_report_relpath=scanner_report_relpath,
        )
    except PrismRuntimeError as exc:
        if exc.code in {
            REPO_SCAN_PAYLOAD_JSON_INVALID,
            REPO_SCAN_PAYLOAD_TYPE_INVALID,
            REPO_SCAN_PAYLOAD_SHAPE_INVALID,
        }:
            return rendered_payload
        raise
    if isinstance(normalized_payload, str):
        return normalized_payload
    return rendered_payload


def _map_top_level_exception_to_exit_code(exc: Exception) -> int:
    if isinstance(exc, PrismRuntimeError):
        if exc.category == "network":
            return _EXIT_CODE_NETWORK_ERROR
        if exc.category == "io":
            return _EXIT_CODE_OS_ERROR
        return _EXIT_CODE_GENERIC_ERROR
    if isinstance(exc, FileNotFoundError):
        return _EXIT_CODE_NOT_FOUND
    if isinstance(exc, PermissionError):
        return _EXIT_CODE_PERMISSION_DENIED
    if isinstance(exc, json.JSONDecodeError):
        return _EXIT_CODE_JSON_PAYLOAD_ERROR
    if isinstance(exc, (HTTPError, URLError)):
        return _EXIT_CODE_NETWORK_ERROR
    if isinstance(exc, OSError):
        return _EXIT_CODE_OS_ERROR
    return _EXIT_CODE_GENERIC_ERROR


def _format_top_level_exception(exc: Exception) -> str:
    if isinstance(exc, PrismRuntimeError):
        return f"Error: code={exc.code} category={exc.category} message={exc.message}"
    return f"Error: message={exc}"


def _handle_repo_command(args: argparse.Namespace) -> int:
    from .cli_repo import handle_repo_command

    return handle_repo_command(args)


def _handle_collection_command(args: argparse.Namespace) -> int:
    from .cli_collection import handle_collection_command

    return handle_collection_command(args)


def _handle_role_command(args: argparse.Namespace) -> int:
    from .cli_role import handle_role_command

    return handle_role_command(args)


def _handle_completion_command(args: argparse.Namespace) -> int:
    from .cli_completion import handle_completion_command

    return handle_completion_command(args)
