"""Role discovery and path-handling helpers for scanner orchestration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable

import yaml

from prism.scanner_data.contracts import DiscoveryProtocol


@lru_cache(maxsize=128)
def _load_yaml_with_mtime(file_path_str: str, mtime: float):
    file_path = Path(file_path_str)
    try:
        text = file_path.read_text(encoding="utf-8")
        return yaml.safe_load(text)
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None


def load_yaml_file_cached(file_path: Path):
    if not file_path.is_file():
        return None
    mtime = file_path.stat().st_mtime
    return _load_yaml_with_mtime(str(file_path), mtime)


ROLE_METADATA_YAML_INVALID = "ROLE_METADATA_YAML_INVALID"
ROLE_METADATA_IO_ERROR = "ROLE_METADATA_IO_ERROR"
ROLE_METADATA_SHAPE_INVALID = "ROLE_METADATA_SHAPE_INVALID"


def _record_metadata_warning(
    warning_collector: list[str] | None,
    *,
    code: str,
    meta_file: Path,
    error: Exception | str,
) -> None:
    if warning_collector is None:
        return
    warning_collector.append(f"{code}: {meta_file}: {error}")


def iter_role_variable_map_candidates(role_root: Path, subdir: str) -> list[Path]:
    """Return role variable map files in deterministic merge order.

    Order is:
    1) ``<subdir>/main.yml`` then ``<subdir>/main.yaml`` fallback
    2) sorted fragments under ``<subdir>/main/*.yml`` then ``*.yaml``
    """
    candidates: list[Path] = []

    main_yml = role_root / subdir / "main.yml"
    main_yaml = role_root / subdir / "main.yaml"
    if main_yml.exists():
        candidates.append(main_yml)
    elif main_yaml.exists():
        candidates.append(main_yaml)

    fragment_dir = role_root / subdir / "main"
    if fragment_dir.is_dir():
        candidates.extend(sorted(fragment_dir.glob("*.yml")))
        candidates.extend(sorted(fragment_dir.glob("*.yaml")))

    return candidates


def load_meta(
    role_path: str,
    *,
    strict: bool = False,
    warning_collector: list[str] | None = None,
) -> dict:
    """Load the role metadata file ``meta/main.yml`` if present.

    Returns a mapping (empty if missing or unparsable).
    """
    meta_file = Path(role_path) / "meta" / "main.yml"
    if meta_file.exists():
        loaded = load_yaml_file_cached(meta_file)
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            _record_metadata_warning(
                warning_collector,
                code=ROLE_METADATA_SHAPE_INVALID,
                meta_file=meta_file,
                error="metadata root must be a mapping",
            )
            return {}
        return loaded
    return {}


def load_requirements(role_path: str) -> list:
    """Load ``meta/requirements.yml`` as a list, or return an empty list."""
    path = Path(role_path) / "meta" / "requirements.yml"
    if path.exists():
        payload = load_yaml_file_cached(path)
        return payload if isinstance(payload, list) else []
    return []


def load_variables(
    role_path: str,
    *,
    include_vars_main: bool = True,
    exclude_paths: list[str] | None = None,
    collect_include_vars_files: Callable[[str, list[str] | None], list[Path]],
) -> dict:
    """Load role variables from defaults/vars and static include_vars targets."""
    vars_out: dict = {}
    role_root = Path(role_path)
    subdirs = ["defaults"]
    if include_vars_main:
        subdirs.append("vars")

    for sub in subdirs:
        for path in iter_role_variable_map_candidates(role_root, sub):
            data = load_yaml_file_cached(path)
            if data is None or not isinstance(data, dict):
                continue
            vars_out.update(data)

    for extra_path in collect_include_vars_files(role_path, exclude_paths):
        data = load_yaml_file_cached(extra_path)
        if data is None or not isinstance(data, dict):
            continue
        vars_out.update(data)

    return vars_out


def resolve_scan_identity(
    role_path: str,
    role_name_override: str | None,
    *,
    load_meta_fn: Callable[[str], dict],
) -> tuple[Path, dict, str, str]:
    """Resolve role path, metadata, role name, and description."""
    role_root = Path(role_path)
    if not role_root.is_dir():
        raise FileNotFoundError(f"role path not found: {role_path}")

    meta = load_meta_fn(role_path)
    galaxy = meta.get("galaxy_info", {}) if isinstance(meta, dict) else {}
    role_name = galaxy.get("role_name", role_root.name)
    if role_name_override and (not galaxy.get("role_name") or role_name == "repo"):
        role_name = role_name_override
    description = galaxy.get("description", "")

    return role_root, meta, role_name, description


class ConcreteDiscovery(DiscoveryProtocol):
    """Concrete implementation of DiscoveryProtocol using scanner_extract functions."""

    def iter_role_variable_map_candidates(self, role_root, subdir):
        return iter_role_variable_map_candidates(role_root, subdir)
