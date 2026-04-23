"""G-03: Integration tests for InMemoryLRUScanCache wired into the scan dispatch path."""

from __future__ import annotations

from pathlib import Path


from prism.api_layer.non_collection import run_scan
from prism.scanner_core.scan_cache import InMemoryLRUScanCache


def _build_tiny_role(role_path: Path) -> None:
    (role_path / "defaults").mkdir(parents=True)
    (role_path / "tasks").mkdir(parents=True)
    (role_path / "defaults" / "main.yml").write_text(
        "---\ncache_test_var: hello\n", encoding="utf-8"
    )
    (role_path / "tasks" / "main.yml").write_text(
        '---\n- name: Cache test task\n  debug:\n    msg: "{{ cache_test_var }}"\n',
        encoding="utf-8",
    )
    (role_path / "README.md").write_text(
        "Role for scan cache integration tests.\n",
        encoding="utf-8",
    )


def test_cache_hit_on_second_identical_scan(tmp_path: Path) -> None:
    """Two consecutive scans of the same role with the cache enabled: second is a hit."""
    role_path = tmp_path / "cache_role"
    _build_tiny_role(role_path)

    backend = InMemoryLRUScanCache()

    result1 = run_scan(str(role_path), include_vars_main=True, cache_backend=backend)
    assert backend.hits == 0
    assert backend.misses == 1

    result2 = run_scan(str(role_path), include_vars_main=True, cache_backend=backend)
    assert backend.hits == 1
    assert backend.misses == 1

    assert result1 == result2


def test_cache_miss_on_content_change(tmp_path: Path) -> None:
    """Two scans with different role content produce two misses (zero hits)."""
    role_path_a = tmp_path / "role_a"
    _build_tiny_role(role_path_a)

    role_path_b = tmp_path / "role_b"
    _build_tiny_role(role_path_b)
    (role_path_b / "defaults" / "main.yml").write_text(
        "---\ncache_test_var: different_content\n", encoding="utf-8"
    )

    backend = InMemoryLRUScanCache()

    run_scan(str(role_path_a), include_vars_main=True, cache_backend=backend)
    run_scan(str(role_path_b), include_vars_main=True, cache_backend=backend)

    assert backend.hits == 0
    assert backend.misses == 2


def test_cache_backend_none_is_zero_overhead(tmp_path: Path) -> None:
    """cache_backend=None (default) path has no overhead — no cache_backend attribute checked."""
    role_path = tmp_path / "nocache_role"
    _build_tiny_role(role_path)

    result = run_scan(str(role_path), include_vars_main=True)
    assert isinstance(result, dict)
    assert result["role_name"] == "nocache_role"
