"""Variable extraction traversal helpers.

Functions for traversing role files to extract variable references and definitions.
"""

import re
import yaml
from pathlib import Path

from .._jinja_analyzer import (
    _collect_jinja_local_bindings_from_text,
    _collect_undeclared_jinja_variables,
)
from .task_parser import (
    _iter_task_mappings,
    INCLUDE_VARS_KEYS,
    _iter_task_include_targets,
    _load_yaml_file,
    _collect_task_files,
    _is_path_excluded,
)
from .variable_policy import _active_ignored_identifiers

# Regex patterns
DEFAULT_TARGET_RE = re.compile(r"\b(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*\|\s*default\b")
JINJA_VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)")
JINJA_IDENTIFIER_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
VAULT_KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*!vault\b", re.MULTILINE)

# Strip quoted string literals before identifier scanning of when: expressions
_QUOTED_STRING_RE = re.compile(r"\"[^\"]*\"|'[^']*'")
_WHEN_FILTER_OR_TEST_CONTEXT_RE = re.compile(r"(?:\|\s*|is\s+|is\s+not\s+)$")
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_WHEN_OPERATOR_KEYWORDS: frozenset[str] = frozenset(
    {
        # Logical operators
        "and",
        "or",
        "not",
        # Comparison/membership operators and textual aliases
        "is",
        "in",
        "eq",
        "ne",
        "lt",
        "gt",
        "le",
        "ge",
    }
)

_REGISTERED_RESULT_ATTRS: frozenset[str] = frozenset(
    {
        "stdout",
        "stderr",
        "rc",
        "stdout_lines",
        "stderr_lines",
        "results",
        "changed",
        "failed",
        "skipped",
        "msg",
    }
)


def _extract_default_target_var(occurrence: dict) -> str | None:
    """Extract the variable name used with ``| default(...)`` when available."""
    line = str(occurrence.get("line") or occurrence.get("match") or "")
    match = DEFAULT_TARGET_RE.search(line)
    if not match:
        return None
    return match.group("var")


def _collect_include_vars_files(
    role_path: str,
    exclude_paths: list[str] | None = None,
) -> list[Path]:
    """Return var files referenced by static ``include_vars`` tasks within the role.

    Only files whose paths can be resolved to a concrete file inside the role
    directory are returned.  Dynamic paths containing Jinja2 expressions are
    silently ignored.
    """
    role_root = Path(role_path).resolve()
    task_files = _collect_task_files(role_root, exclude_paths=exclude_paths)
    result: list[Path] = []
    seen: set[Path] = set()
    for task_file in task_files:
        data = _load_yaml_file(task_file)
        for task in _iter_task_mappings(data):
            for key in INCLUDE_VARS_KEYS:
                if key not in task:
                    continue
                value = task[key]
                ref: str | None = None
                if isinstance(value, str):
                    ref = value
                elif isinstance(value, dict):
                    ref = value.get("file") or value.get("name")
                if not ref or "{{" in ref or "{%" in ref:
                    continue
                for candidate in (
                    (task_file.parent / ref).resolve(),
                    (role_root / "vars" / ref).resolve(),
                    (role_root / ref).resolve(),
                ):
                    if candidate.is_file() and candidate not in seen:
                        try:
                            candidate.relative_to(role_root)
                        except ValueError:
                            continue
                        seen.add(candidate)
                        result.append(candidate)
                        break
    return result


def _collect_set_fact_names(
    role_path: str,
    exclude_paths: list[str] | None = None,
) -> set[str]:
    """Return variable names assigned by ``set_fact`` tasks within the role.

    Only names with static (non-templated) keys are returned.
    """
    from .task_parser import _iter_task_mappings, SET_FACT_KEYS

    role_root = Path(role_path).resolve()
    task_files = _collect_task_files(role_root, exclude_paths=exclude_paths)
    names: set[str] = set()
    for task_file in task_files:
        data = _load_yaml_file(task_file)
        for task in _iter_task_mappings(data):
            for key in SET_FACT_KEYS:
                if key not in task:
                    continue
                value = task[key]
                if isinstance(value, dict):
                    for vname in value:
                        if isinstance(vname, str) and "{{" not in vname:
                            names.add(vname)
    return names


def _collect_register_names(
    role_path: str,
    exclude_paths: list[str] | None = None,
) -> set[str]:
    """Return variable names assigned by task-level ``register`` statements."""
    role_root = Path(role_path).resolve()
    task_files = _collect_task_files(role_root, exclude_paths=exclude_paths)
    names: set[str] = set()
    for task_file in task_files:
        data = _load_yaml_file(task_file)
        for task in _iter_task_mappings(data):
            register_name = task.get("register")
            if not isinstance(register_name, str):
                continue
            # Skip dynamic register names and invalid identifiers.
            if "{{" in register_name or "{%" in register_name:
                continue
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", register_name):
                continue
            names.add(register_name)
    return names


def _find_variable_line_in_yaml(file_path: Path, var_name: str) -> int | None:
    """Return 1-indexed line where ``var_name`` is defined in a YAML file."""
    pattern = re.compile(rf"^\s*{re.escape(var_name)}\s*:")
    try:
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines()):
            if pattern.match(line):
                return idx + 1
    except OSError:
        return None
    return None


def _collect_dynamic_include_vars_refs(
    role_path: str,
    exclude_paths: list[str] | None = None,
) -> list[str]:
    """Return dynamic include_vars references that cannot be statically resolved."""
    from .task_parser import _iter_task_mappings, INCLUDE_VARS_KEYS

    role_root = Path(role_path).resolve()
    refs: list[str] = []
    for task_file in _collect_task_files(role_root, exclude_paths=exclude_paths):
        data = _load_yaml_file(task_file)
        for task in _iter_task_mappings(data):
            for key in INCLUDE_VARS_KEYS:
                if key not in task:
                    continue
                value = task[key]
                ref: str | None = None
                if isinstance(value, str):
                    ref = value
                elif isinstance(value, dict):
                    ref = value.get("file") or value.get("name")
                if ref and ("{{" in ref or "{%" in ref):
                    refs.append(ref)
    return refs


def _collect_dynamic_task_include_refs(
    role_path: str,
    exclude_paths: list[str] | None = None,
) -> list[str]:
    """Return templated include/import task references from task files."""
    role_root = Path(role_path).resolve()
    refs: list[str] = []
    for task_file in _collect_task_files(role_root, exclude_paths=exclude_paths):
        data = _load_yaml_file(task_file)
        for ref in _iter_task_include_targets(data):
            if "{{" in ref or "{%" in ref:
                refs.append(ref)
    return refs


def _collect_referenced_variable_names(
    role_path: str,
    exclude_paths: list[str] | None = None,
    ignored_identifiers: set[str] | frozenset[str] | None = None,
) -> set[str]:
    """Collect likely variable references from role tasks/templates/handlers files."""
    role_root = Path(role_path).resolve()
    candidates: set[str] = set()
    effective_ignored_identifiers = _active_ignored_identifiers()
    if ignored_identifiers:
        effective_ignored_identifiers.update(
            token.lower() for token in ignored_identifiers if isinstance(token, str)
        )
    scan_dirs = ["tasks", "templates", "handlers", "vars"]
    for dirname in scan_dirs:
        root = role_root / dirname
        if not root.is_dir():
            continue
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if _is_path_excluded(file_path, role_root, exclude_paths):
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            local_bindings = _collect_jinja_local_bindings_from_text(text)
            for name in _collect_undeclared_jinja_variables(text):
                lowered = name.lower()
                if lowered in effective_ignored_identifiers:
                    continue
                candidates.add(name)
            for match in JINJA_VAR_RE.findall(text):
                lowered = match.lower()
                if (
                    lowered not in effective_ignored_identifiers
                    and match not in local_bindings
                ):
                    candidates.add(match)
            if file_path.suffix in {".yml", ".yaml"}:
                for line in text.splitlines():
                    if "when:" not in line:
                        continue
                    expression = _QUOTED_STRING_RE.sub("", line.split("when:", 1)[1])
                    for token_match in JINJA_IDENTIFIER_RE.finditer(expression):
                        token = token_match.group(1)
                        if not _is_when_expression_token_candidate(
                            expression, token_match
                        ):
                            continue
                        lowered = token.lower()
                        if lowered in effective_ignored_identifiers:
                            continue
                        candidates.add(token)
    candidates -= _REGISTERED_RESULT_ATTRS
    return candidates


def _is_when_expression_token_candidate(
    expression: str,
    token_match: re.Match[str],
) -> bool:
    """Return whether a token from a ``when:`` expression should count as input."""
    token = token_match.group(1).lower()
    if token in _WHEN_OPERATOR_KEYWORDS:
        return False

    start = token_match.start(1)
    end = token_match.end(1)

    # Ignore dotted attributes like result.stdout or result.rc.
    if start > 0 and expression[start - 1] == ".":
        return False

    before = expression[:start].rstrip()
    if _WHEN_FILTER_OR_TEST_CONTEXT_RE.search(before):
        return False

    # Ignore callable/filter-like names such as version(...), search(...), etc.
    after = expression[end:].lstrip()
    if after.startswith("("):
        return False

    return True


def _read_seed_yaml(path: Path) -> tuple[dict, set[str]]:
    """Read a seed vars YAML file and return mapping plus detected secret keys."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}, set()

    secret_keys = set(VAULT_KEY_RE.findall(text))
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        # Try to sanitize vault content
        sanitized = re.sub(
            r":\s*!vault\b[^\n]*\n(?:[ \t]+.*\n?)*",
            ': "<vault>"\n',
            text,
            flags=re.MULTILINE,
        )
        try:
            data = yaml.safe_load(sanitized)
        except yaml.YAMLError:
            data = None
    if not isinstance(data, dict):
        return {}, secret_keys
    parsed = {key: value for key, value in data.items() if isinstance(key, str)}
    from .variable_sensitivity import _is_sensitive_variable

    for key, value in parsed.items():
        if _is_sensitive_variable(key, value):
            secret_keys.add(key)
    return parsed, secret_keys


def _resolve_seed_var_files(seed_paths: list[str] | None) -> list[Path]:
    """Resolve seed var file/dir inputs into concrete YAML files."""
    files: list[Path] = []
    if not seed_paths:
        return files
    for raw_path in seed_paths:
        seed_path = Path(raw_path).expanduser().resolve()
        if seed_path.is_file() and seed_path.suffix in {".yml", ".yaml"}:
            files.append(seed_path)
            continue
        if seed_path.is_dir():
            files.extend(
                sorted(
                    candidate
                    for candidate in seed_path.rglob("*")
                    if candidate.is_file() and candidate.suffix in {".yml", ".yaml"}
                )
            )
    return files


def load_seed_variables(seed_paths: list[str] | None) -> tuple[dict, set[str], dict]:
    """Load external seed variables from files/directories.

    Returns ``(values, secret_names, source_map)``.
    """
    values: dict = {}
    secret_names: set[str] = set()
    source_map: dict[str, str] = {}
    for path in _resolve_seed_var_files(seed_paths):
        file_values, file_secrets = _read_seed_yaml(path)
        values.update(file_values)
        secret_names.update(file_secrets)
        for key in file_values:
            source_map[key] = str(path)
    return values, secret_names, source_map


def _infer_variable_type(value: object) -> str:
    """Infer a lightweight type label for rendered variable summaries."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if value is None:
        return "null"
    return "str"


# Public exports
extract_default_target_var = _extract_default_target_var
collect_include_vars_files = _collect_include_vars_files
