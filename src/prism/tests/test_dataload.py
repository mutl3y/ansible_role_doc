"""Unit tests for prism.scanner_extract.dataload (FIND-13 closure)."""

from __future__ import annotations

from pathlib import Path

from prism.scanner_extract.dataload import (
    RoleVariableMaps,
    iter_role_argument_spec_entries,
    load_role_variable_maps,
)


def test_role_variable_maps_is_namedtuple() -> None:
    rvm = RoleVariableMaps({"a": 1}, {"b": 2}, {"a": Path("/x")}, {"b": Path("/y")})
    assert rvm.defaults_data == {"a": 1}
    assert rvm.vars_data == {"b": 2}
    assert rvm.defaults_sources == {"a": Path("/x")}


def test_load_role_variable_maps_collects_defaults_and_vars() -> None:
    candidates = {
        "defaults": [Path("/r/defaults/main.yml"), Path("/r/defaults/extra.yml")],
        "vars": [Path("/r/vars/main.yml")],
    }

    def iter_candidates(_root: Path, kind: str) -> list[Path]:
        return candidates[kind]

    yaml_files: dict[Path, dict] = {
        Path("/r/defaults/main.yml"): {"a": 1, "b": 2},
        Path("/r/defaults/extra.yml"): {"c": 3},
        Path("/r/vars/main.yml"): {"v": 9},
    }

    def loader(p: Path) -> object:
        return yaml_files.get(p, None)

    rvm = load_role_variable_maps("/r", True, iter_candidates, loader)
    assert rvm.defaults_data == {"a": 1, "b": 2, "c": 3}
    assert rvm.vars_data == {"v": 9}
    assert rvm.defaults_sources["a"] == Path("/r/defaults/main.yml")
    assert rvm.defaults_sources["c"] == Path("/r/defaults/extra.yml")
    assert rvm.vars_sources["v"] == Path("/r/vars/main.yml")


def test_load_role_variable_maps_skips_vars_when_include_vars_main_false() -> None:
    def iter_candidates(_root: Path, kind: str) -> list[Path]:
        return [Path(f"/r/{kind}/main.yml")]

    def loader(p: Path) -> object:
        return {"k": 1} if "defaults" in str(p) else {"v": 2}

    rvm = load_role_variable_maps("/r", False, iter_candidates, loader)
    assert rvm.defaults_data == {"k": 1}
    assert rvm.vars_data == {}


def test_load_role_variable_maps_skips_non_dict_payloads() -> None:
    def iter_candidates(_root: Path, kind: str) -> list[Path]:
        return [Path(f"/r/{kind}/main.yml")]

    rvm = load_role_variable_maps("/r", True, iter_candidates, lambda _p: "string")
    assert rvm.defaults_data == {} and rvm.vars_data == {}


def test_iter_role_argument_spec_entries_yields_flat_options(tmp_path: Path) -> None:
    arg_specs_file = tmp_path / "meta" / "argument_specs.yml"
    arg_specs_file.parent.mkdir()
    arg_specs_file.write_text("ignored")

    yaml_payload = {
        "argument_specs": {
            "main": {
                "options": {
                    "name": {"type": "str"},
                    "tags": {"type": "list"},
                    "{{ skip }}": {"type": "str"},
                    123: {"type": "ignored"},
                }
            },
            "broken": "not a dict",
        }
    }

    def loader(_p: Path) -> object:
        return yaml_payload

    def meta_loader(_role_path: str) -> dict:
        return {"argument_specs": {"meta_main": {"options": {"role_var": {}}}}}

    entries = list(iter_role_argument_spec_entries(str(tmp_path), loader, meta_loader))
    sources = {(src, name) for src, name, _spec in entries}
    assert ("meta/argument_specs.yml", "name") in sources
    assert ("meta/argument_specs.yml", "tags") in sources
    assert ("meta/main.yml", "role_var") in sources
    assert not any("skip" in name for _, name, _ in entries)


def test_iter_role_argument_spec_entries_skips_non_dict_meta(tmp_path: Path) -> None:
    def meta_loader(_role_path: str) -> dict:
        return {}

    out = list(
        iter_role_argument_spec_entries(str(tmp_path), lambda _p: None, meta_loader)
    )
    assert out == []
