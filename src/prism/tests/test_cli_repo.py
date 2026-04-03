from pathlib import Path
import base64
import json
import subprocess
from types import SimpleNamespace

import pytest

from prism import cli
from prism import repo_services
from prism.tests import _cli_repo_error_and_feedback as cli_repo_error_and_feedback

_REAL_FETCH_REPO_FILE = cli._fetch_repo_file
_REAL_FETCH_REPO_DIRECTORY_NAMES = cli._fetch_repo_directory_names


def _export_shard_symbols(module):
    for name, value in module.__dict__.items():
        if name.startswith("__"):
            continue
        globals().setdefault(name, value)


_export_shard_symbols(cli_repo_error_and_feedback)


def _write_generated_output(output: str) -> str:
    """Persist a fake generated artifact and return its resolved path."""
    Path(output).write_text("generated", encoding="utf-8")
    return str(Path(output).resolve())


@pytest.fixture(autouse=True)
def _disable_remote_github_api(monkeypatch):
    monkeypatch.setattr(
        cli, "_fetch_repo_directory_names", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(cli, "_fetch_repo_file", lambda *args, **kwargs: None)


def test_cli_scans_from_repo_url(monkeypatch, tmp_path):

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        (destination / "tasks").mkdir(parents=True, exist_ok=True)
        (destination / "tasks" / "main.yml").write_text(
            "---\n- name: Task\n  debug:\n    msg: \"{{ demo | default('x') }}\"\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-out.md"
    rc = cli.main(
        ["repo", "--repo-url", "https://github.com/example/role.git", "-o", str(out)]
    )

    assert rc == 0
    assert out.exists()


def test_cli_repo_ref_is_used_for_clone(monkeypatch, tmp_path):

    def fake_clone_repo(repo_url, destination, **kwargs):
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "tasks").mkdir(parents=True, exist_ok=True)
        (destination / "tasks" / "main.yml").write_text(
            "---\n- name: Task\n  debug:\n    msg: \"{{ demo | default('x') }}\"\n",
            encoding="utf-8",
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "_clone_repo", fake_clone_repo)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-ref.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-ref",
            "main",
            "--repo-role-path",
            ".",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()


def test_cli_repo_timeout_is_forwarded(monkeypatch, tmp_path):

    def fake_clone_repo(repo_url, destination, **kwargs):
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "tasks").mkdir(parents=True, exist_ok=True)
        (destination / "tasks" / "main.yml").write_text(
            "---\n- name: Task\n  debug:\n    msg: \"{{ demo | default('x') }}\"\n",
            encoding="utf-8",
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "_clone_repo", fake_clone_repo)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-timeout.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-timeout",
            "5",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()


def test_cli_repo_uses_shared_preflight_orchestration(monkeypatch, tmp_path):
    calls: dict = {}

    def fake_prepare_repo_scan_inputs(
        repo_url,
        *,
        workspace,
        repo_role_path,
        repo_style_readme_path,
        repo_ref,
        repo_timeout,
        fetch_repo_directory_names,
        repo_path_looks_like_role,
        fetch_repo_file,
    ):
        calls["prepare_repo_url"] = repo_url
        calls["prepare_role_path"] = repo_role_path
        calls["prepare_style_readme_path"] = repo_style_readme_path
        calls["prepare_ref"] = repo_ref
        calls["prepare_timeout"] = repo_timeout
        calls["prepare_workspace"] = workspace
        return repo_services._RepoScanPreparation(
            repo_dir_names={"tasks", "defaults", "meta"},
            style_candidates=["README.md", "Readme.md"],
            fetched_repo_style_readme_path=None,
            resolved_repo_style_readme_path=repo_style_readme_path,
        )

    def fake_clone_repo(
        repo_url,
        destination,
        ref=None,
        timeout=60,
        sparse_paths=None,
        allow_sparse_fallback_to_full=True,
    ):
        calls["clone_sparse_paths"] = sparse_paths
        role_dir = destination / "roles" / "demo"
        role_dir.mkdir(parents=True)

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["run_scan_style_readme_path"] = kwargs.get("style_readme_path")
        return _write_generated_output(output)

    monkeypatch.setattr(
        cli,
        "_prepare_repo_scan_inputs",
        fake_prepare_repo_scan_inputs,
    )
    monkeypatch.setattr(cli, "_clone_repo", fake_clone_repo)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-orchestrated.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--repo-ref",
            "main",
            "--repo-timeout",
            "11",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_repo_uses_shared_checkout_orchestration(monkeypatch, tmp_path):
    calls: dict = {}
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)

    def fake_checkout_repo_scan_role(
        repo_url,
        *,
        workspace,
        repo_role_path,
        repo_style_readme_path,
        style_readme_path,
        repo_ref,
        repo_timeout,
        prepare_repo_scan_inputs,
        fetch_repo_directory_names,
        repo_path_looks_like_role,
        fetch_repo_file,
        clone_repo,
        build_sparse_clone_paths,
        resolve_style_readme_candidate,
    ):
        calls["repo_url"] = repo_url
        calls["repo_role_path"] = repo_role_path
        calls["repo_style_readme_path"] = repo_style_readme_path
        calls["style_readme_path"] = style_readme_path
        calls["repo_ref"] = repo_ref
        calls["repo_timeout"] = repo_timeout
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=None,
            resolved_repo_style_readme_path=repo_style_readme_path,
            style_candidates=["README.md"],
            fetched_repo_style_readme_path=None,
        )

    def fake_run_scan(scanned_role_path, output, template, output_format, **kwargs):
        calls["scanned_role_path"] = scanned_role_path
        calls["role_name_override"] = kwargs.get("role_name_override")
        calls["run_scan_style_readme_path"] = kwargs.get("style_readme_path")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-checkout-orchestrated.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--repo-ref",
            "main",
            "--repo-timeout",
            "9",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_repo_json_dry_run_reports_logical_repo_paths(
    monkeypatch, tmp_path, capsys
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")
    report_path = tmp_path / "reports" / "repo.scan.md"

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        return json.dumps(payload)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    output_path = tmp_path / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "--scanner-report-output",
            str(report_path),
            "--dry-run",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["metadata"]["style_guide"]["path"] == "readme.md"
    assert payload["metadata"]["scanner_report_relpath"] == "reports/repo.scan.md"


def test_cli_repo_json_non_dry_run_persists_logical_repo_paths(monkeypatch, tmp_path):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")
    report_path = tmp_path / "reports" / "repo.scan.md"

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        output_path = Path(output)
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        output_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(output_path)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    output_path = tmp_path / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "--scanner-report-output",
            str(report_path),
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["style_guide"]["path"] == "readme.md"
    assert payload["metadata"]["scanner_report_relpath"] == "reports/repo.scan.md"


def test_cli_repo_json_non_dry_run_sets_default_scanner_report_relpath(
    monkeypatch, tmp_path
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        output_path = Path(output)
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        output_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(output_path)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    output_path = tmp_path / "nested" / "repo-scan.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["style_guide"]["path"] == "readme.md"
    assert payload["metadata"]["scanner_report_relpath"] == "repo-scan.scan-report.md"


def test_cli_repo_json_dry_run_normalizes_windows_scanner_report_relpath(
    monkeypatch, tmp_path, capsys
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        return json.dumps(payload)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)
    monkeypatch.setattr(
        repo_services.os.path,
        "relpath",
        lambda *args, **kwargs: r"..\reports\nested\repo.scan.md",
    )

    output_path = tmp_path / "artifacts" / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "--scanner-report-output",
            r"reports\nested\repo.scan.md",
            "--dry-run",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    payload = json.loads(captured.out)
    assert (
        payload["metadata"]["scanner_report_relpath"]
        == "../reports/nested/repo.scan.md"
    )


def test_cli_repo_json_non_dry_run_normalizes_windows_scanner_report_relpath(
    monkeypatch, tmp_path
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        output_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(output_path)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)
    monkeypatch.setattr(
        repo_services.os.path,
        "relpath",
        lambda *args, **kwargs: r"..\reports\nested\repo.scan.md",
    )

    output_path = tmp_path / "artifacts" / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "--scanner-report-output",
            r"reports\nested\repo.scan.md",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert (
        payload["metadata"]["scanner_report_relpath"]
        == "../reports/nested/repo.scan.md"
    )


def test_cli_repo_json_non_dry_run_malformed_payload_skips_normalization_gracefully(
    monkeypatch, tmp_path
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    malformed_payload = '{"role_name": "demo-role", "metadata":'

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        output_path = Path(output)
        output_path.write_text(malformed_payload, encoding="utf-8")
        return str(output_path)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    output_path = tmp_path / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )

    assert rc == 0
    assert output_path.read_text(encoding="utf-8") == malformed_payload


def test_cli_repo_json_dry_run_malformed_payload_skips_normalization_gracefully(
    monkeypatch, tmp_path, capsys
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    malformed_payload = '{"role_name": "demo-role", "metadata":'

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return malformed_payload

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    output_path = tmp_path / "repo-scan.json"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--dry-run",
            "-f",
            "json",
            "-o",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.out == malformed_payload


def test_cli_repo_json_non_dry_run_relative_output_path_sets_nested_scanner_report_relpath(
    monkeypatch, tmp_path
):
    role_path = tmp_path / "repo" / "roles" / "demo"
    role_path.mkdir(parents=True)
    fetched_style = tmp_path / "fetched-style.md"
    fetched_style.write_text("# Style\n", encoding="utf-8")

    def fake_checkout_repo_scan_role(*args, **kwargs):
        return repo_services._RepoCheckoutResult(
            checkout_dir=tmp_path / "repo",
            role_path=role_path,
            effective_style_readme_path=str(fetched_style.resolve()),
            resolved_repo_style_readme_path="readme.md",
            style_candidates=["README.md", "Readme.md", "readme.md"],
            fetched_repo_style_readme_path=fetched_style,
        )

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "role_name": "demo-role",
            "metadata": {
                "style_guide": {"path": kwargs.get("style_readme_path")},
            },
        }
        output_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(output_path)

    monkeypatch.setattr(cli, "_checkout_repo_scan_role", fake_checkout_repo_scan_role)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)
    monkeypatch.chdir(tmp_path)

    output_relpath = Path("artifacts") / "json" / "repo-scan.json"
    scanner_report_rel_output = (
        Path("artifacts") / "reports" / "nested" / "repo.scan.md"
    )
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "--concise-readme",
            "--scanner-report-output",
            str(scanner_report_rel_output),
            "-f",
            "json",
            "-o",
            str(output_relpath),
        ]
    )

    assert rc == 0
    payload = json.loads((tmp_path / output_relpath).read_text(encoding="utf-8"))
    assert payload["metadata"]["style_guide"]["path"] == "readme.md"
    assert (
        payload["metadata"]["scanner_report_relpath"]
        == "../reports/nested/repo.scan.md"
    )


def test_cli_repo_scan_uses_shared_temp_root(monkeypatch, tmp_path):
    clone_calls: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        clone_calls["destination"] = destination
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-shared-tmp.md"
    rc = cli.main(
        ["repo", "--repo-url", "https://github.com/example/role.git", "-o", str(out)]
    )

    assert rc == 0
    assert clone_calls["destination"].parent.parent == tmp_path / "prism"
    assert not (tmp_path / "prism").exists()


def test_cli_github_https_url_is_preserved_by_default(monkeypatch, tmp_path):
    clone_cmd: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        clone_cmd["cmd"] = cmd
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-ssh-url.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert clone_cmd["cmd"][-2] == "https://github.com/example/role"


def test_cli_repo_transport_policy_can_force_ssh(monkeypatch, tmp_path):
    clone_cmd: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        clone_cmd["cmd"] = cmd
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)
    monkeypatch.setenv("PRISM_REPO_TRANSPORT_POLICY", "ssh")

    out = tmp_path / "repo-ssh-url.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert clone_cmd["cmd"][-2] == "git@github.com:example/role.git"


def test_cli_ssh_repo_url_is_preserved(monkeypatch, tmp_path):
    clone_cmd: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        clone_cmd["cmd"] = cmd
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-ssh-preserved.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "git@github.com:example/role.git",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert clone_cmd["cmd"][-2] == "git@github.com:example/role.git"


def test_fetch_repo_file_uses_github_contents_api(monkeypatch, tmp_path):
    seen: dict = {}
    destination = tmp_path / "fetched" / "README.md"
    encoded = base64.b64encode(b"# Guide\n").decode("ascii")

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {"type": "file", "encoding": "base64", "content": encoded}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(cli, "urlopen", fake_urlopen)

    result = _REAL_FETCH_REPO_FILE(
        "https://github.com/example/demo-role.git",
        "docs/README.md",
        destination,
        ref="main",
        timeout=5,
    )

    assert result == destination
    assert destination.read_text(encoding="utf-8") == "# Guide\n"
    assert seen["timeout"] == 5
    assert seen["url"].endswith("/contents/docs/README.md?ref=main")


def test_fetch_repo_directory_names_uses_github_contents_api(monkeypatch):
    seen: dict = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                [
                    {"type": "dir", "name": "tasks"},
                    {"type": "dir", "name": "defaults"},
                    {"type": "file", "name": "README.md"},
                ]
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(cli, "urlopen", fake_urlopen)

    result = _REAL_FETCH_REPO_DIRECTORY_NAMES(
        "https://github.com/example/demo-role.git",
        repo_path=".",
        ref="main",
        timeout=7,
    )

    assert result == {"defaults", "tasks"}
    assert seen["timeout"] == 7
    assert seen["url"].endswith("/contents?ref=main")


def test_repo_path_looks_like_role_uses_standard_role_dirs():
    assert cli._repo_path_looks_like_role({"tasks", "defaults", "meta"}) is True
    assert cli._repo_path_looks_like_role({"tasks", "meta", "handlers"}) is False
    assert cli._repo_path_looks_like_role({"tasks", "defaults"}) is False
    assert cli._repo_path_looks_like_role({"docs", "github"}) is False


def test_build_repo_style_readme_candidates_handles_case_variants():
    assert cli._build_repo_style_readme_candidates("README.md") == [
        "README.md",
        "Readme.md",
        "readme.md",
    ]
    assert cli._build_repo_style_readme_candidates("docs/readme.md") == [
        "docs/readme.md",
        "docs/README.md",
        "docs/Readme.md",
    ]
    assert cli._build_repo_style_readme_candidates("docs/STYLE.md") == ["docs/STYLE.md"]


def test_fetch_repo_file_returns_none_for_non_github_repo(tmp_path):
    destination = tmp_path / "README.md"

    result = cli._fetch_repo_file(
        "https://gitlab.com/example/demo-role.git",
        "README.md",
        destination,
    )

    assert result is None
    assert not destination.exists()


def test_cli_requires_subcommand():
    assert cli.main([]) == 2


def test_cli_concise_and_scanner_report_flags_are_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    report = tmp_path / "SCAN_REPORT.md"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["concise_readme"] = kwargs.get("concise_readme")
        calls["scanner_report_output"] = kwargs.get("scanner_report_output")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "concise.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--concise-readme",
            "--scanner-report-output",
            str(report),
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()


def test_cli_variable_sources_defaults_only_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["include_vars_main"] = kwargs.get("include_vars_main")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "defaults-only.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--variable-sources",
            "defaults-only",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()


def test_cli_variable_sources_default_excludes_vars(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["include_vars_main"] = kwargs.get("include_vars_main")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "default-sources.md"
    rc = cli.main(["role", str(role), "-o", str(out)])

    assert rc == 0
    assert out.exists()


def test_cli_scanner_report_link_flag_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["include_scanner_report_link"] = kwargs.get("include_scanner_report_link")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "no-link.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--concise-readme",
            "--no-include-scanner-report-link",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_adopt_heading_mode_flag_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["adopt_heading_mode"] = kwargs.get("adopt_heading_mode")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "adopt-headings.md"
    rc = cli.main(["role", str(role), "--adopt-heading-mode", "style", "-o", str(out)])

    assert rc == 0


def test_cli_keep_unknown_style_sections_flag_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["keep_unknown_style_sections"] = kwargs.get("keep_unknown_style_sections")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "keep-unknown.md"
    rc = cli.main(["role", str(role), "--keep-unknown-style-sections", "-o", str(out)])

    assert rc == 0


def test_cli_style_source_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    style_source = tmp_path / "STYLE_GUIDE_SOURCE.md"
    role.mkdir()
    style_source.write_text("# Guide\n", encoding="utf-8")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["style_source_path"] = kwargs.get("style_source_path")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "style-source.md"
    rc = cli.main(
        ["role", str(role), "--style-source", str(style_source), "-o", str(out)]
    )

    assert rc == 0


def test_cli_policy_config_is_forwarded(monkeypatch, tmp_path):
    calls: dict = {}

    role = tmp_path / "role"
    policy_cfg = tmp_path / "policy.yml"
    role.mkdir()
    policy_cfg.write_text("ignored_identifiers: []\n", encoding="utf-8")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["policy_config_path"] = kwargs.get("policy_config_path")
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "policy.md"
    rc = cli.main(
        ["role", str(role), "--policy-config", str(policy_cfg), "-o", str(out)]
    )

    assert rc == 0


def test_cli_fail_on_unconstrained_dynamic_includes_is_forwarded_for_role(
    monkeypatch, tmp_path
):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["fail_on_unconstrained_dynamic_includes"] = kwargs.get(
            "fail_on_unconstrained_dynamic_includes"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "fail-policy.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--fail-on-unconstrained-dynamic-includes",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_fail_on_unconstrained_dynamic_includes_is_forwarded_for_repo(
    monkeypatch, tmp_path
):
    calls: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["fail_on_unconstrained_dynamic_includes"] = kwargs.get(
            "fail_on_unconstrained_dynamic_includes"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-fail-policy.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--fail-on-unconstrained-dynamic-includes",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_fail_on_unconstrained_dynamic_includes_is_forwarded_for_collection(
    monkeypatch, tmp_path
):
    calls: dict = {}
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    def fake_scan_collection(collection_path, **kwargs):
        calls["fail_on_unconstrained_dynamic_includes"] = kwargs.get(
            "fail_on_unconstrained_dynamic_includes"
        )
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 0, "scanned_roles": 0, "failed_roles": 0},
            "roles": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "collection-fail-policy"
    rc = cli.main(
        [
            "collection",
            str(collection_root),
            "--fail-on-unconstrained-dynamic-includes",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_fail_on_yaml_like_task_annotations_is_forwarded_for_role(
    monkeypatch, tmp_path
):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["fail_on_yaml_like_task_annotations"] = kwargs.get(
            "fail_on_yaml_like_task_annotations"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "annotation-policy.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--fail-on-yaml-like-task-annotations",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_fail_on_yaml_like_task_annotations_is_forwarded_for_repo(
    monkeypatch, tmp_path
):
    calls: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["fail_on_yaml_like_task_annotations"] = kwargs.get(
            "fail_on_yaml_like_task_annotations"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-annotation-policy.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--fail-on-yaml-like-task-annotations",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_fail_on_yaml_like_task_annotations_is_forwarded_for_collection(
    monkeypatch, tmp_path
):
    calls: dict = {}
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    def fake_scan_collection(collection_path, **kwargs):
        calls["fail_on_yaml_like_task_annotations"] = kwargs.get(
            "fail_on_yaml_like_task_annotations"
        )
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 0, "scanned_roles": 0, "failed_roles": 0},
            "roles": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "collection-annotation-policy"
    rc = cli.main(
        [
            "collection",
            str(collection_root),
            "--fail-on-yaml-like-task-annotations",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_ignore_unresolved_internal_underscore_references_is_forwarded_for_role(
    monkeypatch, tmp_path
):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["ignore_unresolved_internal_underscore_references"] = kwargs.get(
            "ignore_unresolved_internal_underscore_references"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "underscore-policy.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--no-ignore-unresolved-internal-underscore-references",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_ignore_unresolved_internal_underscore_references_is_forwarded_for_repo(
    monkeypatch, tmp_path
):
    calls: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["ignore_unresolved_internal_underscore_references"] = kwargs.get(
            "ignore_unresolved_internal_underscore_references"
        )
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-underscore-policy.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--no-ignore-unresolved-internal-underscore-references",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_ignore_unresolved_internal_underscore_references_is_forwarded_for_collection(
    monkeypatch, tmp_path
):
    calls: dict = {}
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    def fake_scan_collection(collection_path, **kwargs):
        calls["ignore_unresolved_internal_underscore_references"] = kwargs.get(
            "ignore_unresolved_internal_underscore_references"
        )
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 0, "scanned_roles": 0, "failed_roles": 0},
            "roles": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "collection-underscore-policy"
    rc = cli.main(
        [
            "collection",
            str(collection_root),
            "--no-ignore-unresolved-internal-underscore-references",
            "-o",
            str(out),
        ]
    )

    assert rc == 0


def test_cli_repo_style_readme_path_is_resolved(monkeypatch, tmp_path):
    calls: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "README.md").write_text(
            "Guide\n"
            "=====\n\n"
            "Unknown Custom Notes\n"
            "--------------------\n\n"
            "Human-authored unknown section body.\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["style_readme_path"] = kwargs.get("style_readme_path")
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)
    monkeypatch.setattr(cli, "_fetch_repo_file", lambda *args, **kwargs: None)

    out = tmp_path / "repo-style.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-style-readme-path",
            "README.md",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    source_sidecar = tmp_path / "style_role" / "SOURCE_STYLE_GUIDE.md"
    demo_sidecar = tmp_path / "style_role" / "DEMO_GENERATED.md"
    keep_demo_sidecar = tmp_path / "style_role" / "DEMO_GENERATED_KEEP_UNKNOWN.md"
    cfg_sidecar = tmp_path / "style_role" / "ROLE_README_CONFIG.yml"
    assert source_sidecar.exists()
    assert "Unknown Custom Notes" in source_sidecar.read_text(encoding="utf-8")
    assert demo_sidecar.exists()
    assert demo_sidecar.read_text(encoding="utf-8") == "generated"
    assert keep_demo_sidecar.exists()
    assert keep_demo_sidecar.read_text(encoding="utf-8") == "generated"
    assert cfg_sidecar.exists()
    cfg_text = cfg_sidecar.read_text(encoding="utf-8")
    assert "unknown_style_sections" in cfg_text
    assert "title: Unknown Custom Notes" in cfg_text
    assert "Human-authored unknown section body." in cfg_text


def test_cli_repo_style_readme_fetch_skips_sparse_style_path(monkeypatch, tmp_path):
    calls: dict = {}
    fetched_style = tmp_path / "remote-style.md"
    fetched_style.write_text("# Remote Guide\n", encoding="utf-8")

    def fake_fetch_repo_file(repo_url, repo_path, destination, ref=None, timeout=60):
        calls["fetched_repo_path"] = repo_path
        calls["fetch_destination"] = destination
        return fetched_style

    def fake_clone_repo(repo_url, destination, ref=None, timeout=60, sparse_paths=None):
        calls["clone_sparse_paths"] = sparse_paths
        role_dir = destination / "roles" / "demo"
        role_dir.mkdir(parents=True, exist_ok=True)

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["style_readme_path"] = kwargs.get("style_readme_path")
        return _write_generated_output(output)

    monkeypatch.setattr(
        cli,
        "_fetch_repo_directory_names",
        lambda *args, **kwargs: {"tasks", "defaults", "meta"},
    )
    monkeypatch.setattr(cli, "_fetch_repo_file", fake_fetch_repo_file)
    monkeypatch.setattr(cli, "_clone_repo", fake_clone_repo)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "repo-style-fetched.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/demo-role.git",
            "--repo-role-path",
            "roles/demo",
            "--repo-style-readme-path",
            "README.md",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert out.exists()


def test_cli_repo_rejects_non_role_directory_listing(monkeypatch, tmp_path, capsys):
    def fail_clone(*args, **kwargs):
        raise AssertionError("clone should not run for non-role repos")

    monkeypatch.setattr(
        cli,
        "_fetch_repo_directory_names",
        lambda *args, **kwargs: {"docs", ".github"},
    )
    monkeypatch.setattr(cli, "_clone_repo", fail_clone)

    out = tmp_path / "non-role.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/not-a-role.git",
            "-o",
            str(out),
        ]
    )

    captured = capsys.readouterr()
    assert rc == 3
    assert "repository path does not look like an Ansible role" in captured.err


def test_clone_repo_timeout_raises_runtime_error(monkeypatch, tmp_path):
    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    with pytest.raises(RuntimeError, match="repository clone timed out"):
        cli._clone_repo(
            "https://github.com/example/role.git", tmp_path / "repo", timeout=5
        )


def test_clone_repo_failure_raises_runtime_error(monkeypatch, tmp_path):
    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        raise subprocess.CalledProcessError(
            returncode=1, cmd=cmd, stderr="fatal: denied"
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    with pytest.raises(RuntimeError, match="repository clone failed: fatal: denied"):
        cli._clone_repo("https://github.com/example/role.git", tmp_path / "repo")


def test_save_style_comparison_artifacts_requires_existing_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="style README not found"):
        cli._save_style_comparison_artifacts(
            str(tmp_path / "missing.md"),
            str(tmp_path / "generated.md"),
        )


def test_save_style_comparison_artifacts_handles_same_source_path(tmp_path):
    style_dir = tmp_path / "style_demo"
    style_dir.mkdir()
    source = style_dir / "SOURCE_STYLE_GUIDE.md"
    source.write_text("# Guide\n", encoding="utf-8")
    generated = tmp_path / "generated.html"
    generated.write_text("<html></html>", encoding="utf-8")

    source_path, demo_path = cli._save_style_comparison_artifacts(
        str(source),
        str(generated),
        "style_demo",
    )

    assert Path(source_path) == source
    assert Path(demo_path) == style_dir / "DEMO_GENERATED.html"
    assert Path(demo_path).read_text(encoding="utf-8") == "<html></html>"


def test_cli_repo_role_path_must_exist(monkeypatch, tmp_path, capsys):
    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    out = tmp_path / "missing-subpath.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "--repo-role-path",
            "missing-role",
            "-o",
            str(out),
        ]
    )

    captured = capsys.readouterr()
    assert rc == 3
    assert "role path not found in cloned repository" in captured.err


def test_repo_name_from_url_returns_none_for_unparseable_values():
    assert cli._repo_name_from_url("not-a-url") is None
    assert cli._repo_name_from_url("git@github.com") is None


def test_clone_repo_keeps_non_repo_github_url_as_is(monkeypatch, tmp_path):
    clone_cmd: dict = {}

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        clone_cmd["cmd"] = cmd
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    cli._clone_repo("https://github.com", tmp_path / "repo")
    assert clone_cmd["cmd"][-2] == "https://github.com"


def test_build_sparse_clone_paths_returns_empty_for_repo_root():
    assert cli._build_sparse_clone_paths(".", None) == []
    assert cli._build_sparse_clone_paths("", "README.md") == []


def test_build_sparse_clone_paths_collects_role_and_style_path():
    assert cli._build_sparse_clone_paths("roles/demo", "README.md") == [
        "roles/demo",
        "README.md",
    ]
    assert cli._build_sparse_clone_paths("roles/demo", "roles/demo") == ["roles/demo"]


def test_resolve_repo_scan_scanner_report_relpath_normalizes_windows_separators(
    monkeypatch,
):
    monkeypatch.setattr(
        repo_services.os.path,
        "relpath",
        lambda *args, **kwargs: r"..\reports\nested\repo.scan.md",
    )

    relpath = repo_services._resolve_repo_scan_scanner_report_relpath(
        concise_readme=True,
        scanner_report_output="reports/repo.scan.md",
        primary_output_path="artifacts/repo-scan.json",
    )

    assert relpath == "../reports/nested/repo.scan.md"


def test_clone_repo_uses_sparse_checkout_when_paths_provided(monkeypatch, tmp_path):
    commands: list[list[str]] = []

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        commands.append(cmd)
        if cmd[:2] == ["git", "clone"]:
            destination = Path(cmd[-1])
            destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    cli._clone_repo(
        "https://github.com/example/role.git",
        tmp_path / "repo",
        sparse_paths=["roles/demo", "README.md"],
    )

    assert len(commands) == 2
    assert "--filter=blob:none" in commands[0]
    assert "--sparse" in commands[0]
    assert commands[1][:5] == [
        "git",
        "-C",
        str(tmp_path / "repo"),
        "sparse-checkout",
        "set",
    ]
    assert "--no-cone" in commands[1]
    assert "roles/demo" in commands[1]
    assert "README.md" in commands[1]


def test_clone_repo_falls_back_when_sparse_checkout_fails(monkeypatch, tmp_path):
    commands: list[list[str]] = []

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        commands.append(cmd)
        if cmd[:2] == ["git", "clone"]:
            destination = Path(cmd[-1])
            destination.mkdir(parents=True, exist_ok=True)
        if "sparse-checkout" in cmd:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="boom")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    cli._clone_repo(
        "https://github.com/example/role.git",
        tmp_path / "repo",
        sparse_paths=["roles/demo"],
    )

    clone_commands = [cmd for cmd in commands if cmd[:2] == ["git", "clone"]]
    assert len(clone_commands) == 2
    assert "--sparse" in clone_commands[0]
    assert "--filter=blob:none" in clone_commands[0]
    assert "--sparse" not in clone_commands[1]
    assert "--filter=blob:none" not in clone_commands[1]


def test_clone_repo_does_not_fallback_when_sparse_fallback_disabled(
    monkeypatch, tmp_path
):
    commands: list[list[str]] = []

    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        commands.append(cmd)
        if cmd[:2] == ["git", "clone"]:
            destination = Path(cmd[-1])
            destination.mkdir(parents=True, exist_ok=True)
        if "sparse-checkout" in cmd:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="boom")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)

    with pytest.raises(RuntimeError, match="repository sparse checkout failed"):
        cli._clone_repo(
            "https://github.com/example/role.git",
            tmp_path / "repo",
            sparse_paths=["roles/demo"],
            allow_sparse_fallback_to_full=False,
        )

    clone_commands = [cmd for cmd in commands if cmd[:2] == ["git", "clone"]]
    assert len(clone_commands) == 1


def test_save_style_comparison_artifacts_uses_parent_name_for_readme_slug(tmp_path):
    source_dir = tmp_path / "ansible-role-demo"
    source_dir.mkdir()
    source = source_dir / "README.md"
    source.write_text("# Guide\n", encoding="utf-8")
    output = tmp_path / "generated.md"
    output.write_text("generated", encoding="utf-8")

    source_path, demo_path = cli._save_style_comparison_artifacts(
        str(source),
        str(output),
        style_source_name="readme",
    )

    assert Path(source_path).parent.name == "style_ansible_role_demo"
    assert Path(demo_path).name == "DEMO_GENERATED.md"


def test_save_style_comparison_artifacts_skips_copy_when_demo_output_already_target(
    tmp_path,
):
    style_dir = tmp_path / "style_demo"
    style_dir.mkdir()
    source = tmp_path / "guide.md"
    source.write_text("# Guide\n", encoding="utf-8")
    demo_target = style_dir / "DEMO_GENERATED.md"
    demo_target.write_text("existing", encoding="utf-8")

    _, demo_path = cli._save_style_comparison_artifacts(
        str(source),
        str(demo_target),
        style_source_name="demo",
    )

    assert Path(demo_path) == demo_target
    assert demo_target.read_text(encoding="utf-8") == "existing"


def test_cli_verbose_repo_scan_prints_clone_and_write(monkeypatch, tmp_path, capsys):
    def fake_clone_run(cmd, check, stdout, stderr, text, timeout, env):
        destination = Path(cmd[-1])
        destination.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli.subprocess, "run", fake_clone_run)
    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "verbose.md"
    rc = cli.main(
        [
            "repo",
            "--repo-url",
            "https://github.com/example/role.git",
            "-o",
            str(out),
            "-v",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert "Cloning: https://github.com/example/role.git" in captured.out
    assert "Wrote:" in captured.out


def test_cli_verbose_local_scan_prints_style_and_demo_paths(
    monkeypatch, tmp_path, capsys
):
    """Covers the verbose style_source_path and style_demo_path print lines (local role path flow)."""
    role_dir = tmp_path / "role"
    role_dir.mkdir()
    style_guide = tmp_path / "guide.md"
    style_guide.write_text(
        "# Style\n\n## Role Variables\n\nsome body\n", encoding="utf-8"
    )
    out = tmp_path / "out.md"

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return _write_generated_output(output)

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    rc = cli.main(
        [
            "role",
            str(role_dir),
            "--style-readme",
            str(style_guide),
            "-o",
            str(out),
            "-v",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert "Wrote:" in captured.out
    assert "Style guide source:" in captured.out
    assert "Generated demo copy:" in captured.out


def test_cli_dry_run_and_json_are_forwarded(monkeypatch, tmp_path, capsys):
    calls: dict = {}

    role = tmp_path / "role"
    role.mkdir()

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        calls["role_path"] = role_path
        calls["output_format"] = output_format
        calls["dry_run"] = kwargs.get("dry_run")
        return '{"role_name":"demo"}\n'

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "dry-run-json"
    rc = cli.main(["role", str(role), "-f", "json", "--dry-run", "-o", str(out), "-v"])
    captured = capsys.readouterr()

    assert rc == 0
    assert not out.exists()
    assert '{"role_name":"demo"}' in captured.out
    assert "Dry run: no files written." in captured.out


def test_cli_dry_run_skips_style_comparison_artifacts(monkeypatch, tmp_path):
    role = tmp_path / "role"
    role.mkdir()
    style_guide = tmp_path / "guide.md"
    style_guide.write_text("# Style\n", encoding="utf-8")

    def fake_run_scan(role_path, output, template, output_format, **kwargs):
        return "# preview\n"

    monkeypatch.setattr(cli, "run_scan", fake_run_scan)

    out = tmp_path / "dry-run-output.md"
    rc = cli.main(
        [
            "role",
            str(role),
            "--style-readme",
            str(style_guide),
            "--dry-run",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    assert not out.exists()
    assert not (tmp_path / "style_guide").exists()


def test_cli_completion_bash_outputs_generated_script(capsys):
    rc = cli.main(["completion", "bash"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "_prism_completion()" in captured.out
    assert "complete -F _prism_completion prism" in captured.out
    for command in ("role", "collection", "repo", "completion"):
        assert command in captured.out
    assert "--repo-url" in captured.out
    assert "--detailed-catalog" in captured.out


def test_cli_completion_requires_shell_choice():
    assert cli.main(["completion"]) == 2


def test_render_collection_markdown_handles_conflicts_and_failures_overflow():
    payload = {
        "collection": {"metadata": {"namespace": "demo", "name": "toolkit"}},
        "dependencies": {
            "collections": [
                "invalid",
                {"key": "community.general", "version": "9.0.0"},
            ],
            "roles": ["invalid", {"key": "geerlingguy.mysql", "version": "3.3.0"}],
            "conflicts": [
                "invalid",
                {"key": "community.general", "versions": ["8", "9"]},
            ],
        },
        "roles": [
            {"role": f"role_{i:02d}", "payload": {"metadata": {"scanner_counters": {}}}}
            for i in range(65)
        ],
        "plugin_catalog": {
            "summary": {"total_plugins": 100, "files_scanned": 10, "files_failed": 1},
            "by_type": {
                **{f"type_{i:02d}": [{"name": f"plugin_{i}"}] for i in range(45)},
                "filter": [
                    {
                        "name": "cap-rich",
                        "symbols": ["a", "b", "c", "d", "e", "f", "g"],
                        "confidence": "high",
                    },
                    {"name": "a-no-symbols", "symbols": "n/a", "confidence": "low"},
                ]
                + [
                    {"name": f"extra_{i}", "symbols": ["x"], "confidence": "medium"}
                    for i in range(30)
                ],
            },
            "failures": [
                "invalid",
                {
                    "relative_path": "plugins/filter/a.py",
                    "stage": "parse",
                    "error": "boom",
                },
            ],
        },
        "failures": ["invalid"]
        + [{"role": f"failed_{i:02d}", "error": "broken"} for i in range(35)],
        "summary": {"total_roles": 100, "scanned_roles": 65, "failed_roles": 35},
    }

    rendered = cli._render_collection_markdown(payload)

    assert "## Dependency Conflicts" in rendered
    assert "`community.general`: 8, 9" in rendered
    assert "... and 5 more roles" in rendered
    assert "... and 6 more plugin types" in rendered
    assert "`cap-rich` [high]: a, b, c, d, e, f, ..." in rendered
    assert "`a-no-symbols` [low]: (none discovered)" in rendered
    assert "... and 7 more filter plugins" in rendered
    assert "### Plugin Scan Failures" in rendered
    assert "plugins/filter/a.py" in rendered
    assert "## Role Scan Failures" in rendered
    assert "... and 5 more role failures" in rendered


def test_build_bash_completion_script_raises_without_subparsers(monkeypatch):
    parser = cli.argparse.ArgumentParser(prog="prism")
    monkeypatch.setattr(cli, "build_parser", lambda: parser)

    with pytest.raises(RuntimeError, match="subcommand parser is not configured"):
        cli._build_bash_completion_script()


def test_resolve_effective_readme_config_returns_explicit_path(tmp_path):
    role_dir = tmp_path / "role"
    role_dir.mkdir()

    assert (
        cli._resolve_effective_readme_config(role_dir, "/tmp/explicit.yml")
        == "/tmp/explicit.yml"
    )


def test_handle_completion_command_rejects_non_bash(capsys):
    rc = cli._handle_completion_command(SimpleNamespace(shell="zsh"))
    captured = capsys.readouterr()

    assert rc == 2
    assert "unsupported completion shell: zsh" in captured.err


def test_github_repo_from_url_supports_git_ssh_form():
    assert cli._github_repo_from_url("git@github.com:org/repo.git") == ("org", "repo")


def test_github_repo_from_url_returns_none_for_malformed_git_ssh_forms():
    assert cli._github_repo_from_url("git@github.com:") is None
    assert cli._github_repo_from_url("git@github.com:owner/") is None


def test_fetch_repo_directory_names_returns_none_for_non_list_payload(monkeypatch):
    monkeypatch.setattr(
        cli,
        "_fetch_repo_contents_payload",
        lambda *args, **kwargs: {"type": "file"},
    )
    assert (
        cli._fetch_repo_directory_names("https://github.com/example/repo.git") is None
    )


def test_repo_path_looks_like_role_returns_false_for_missing_required_dirs():
    assert cli._repo_path_looks_like_role({"tasks", "defaults"}) is False


@pytest.mark.parametrize(
    "payload,expected",
    [
        (None, None),
        ({"type": "dir"}, None),
        ({"type": "file", "content": 123, "encoding": "base64"}, None),
        ({"type": "file", "content": "abc", "encoding": "utf-8"}, None),
        ({"type": "file", "content": "***", "encoding": "base64"}, None),
    ],
)
def test_fetch_repo_file_invalid_payload_shapes_return_none(
    monkeypatch, tmp_path, payload, expected
):
    monkeypatch.setattr(
        cli, "_fetch_repo_contents_payload", lambda *args, **kwargs: payload
    )
    out = cli._fetch_repo_file(
        "https://github.com/example/repo.git",
        "README.md",
        tmp_path / "README.md",
    )
    assert out is expected


def test_save_style_comparison_artifacts_marks_truncated_unknown_sections(
    monkeypatch, tmp_path
):
    style_readme = tmp_path / "STYLE.md"
    style_readme.write_text("# Source\n", encoding="utf-8")
    generated = tmp_path / "README.generated.md"
    generated.write_text("# Generated\n", encoding="utf-8")

    monkeypatch.setattr(
        cli,
        "parse_style_readme",
        lambda _: {
            "sections": [
                {"id": "unknown", "title": "One", "body": "alpha"},
                {"id": "unknown", "title": "One", "body": "duplicate"},
                {"id": "unknown", "title": "Two", "body": "x" * 200},
                {"id": "unknown", "title": "Three", "body": "tail"},
            ]
        },
    )
    monkeypatch.setattr(cli, "_CAPTURE_MAX_SECTIONS", 50)
    monkeypatch.setattr(cli, "_CAPTURE_MAX_CONTENT_CHARS", 20)
    monkeypatch.setattr(cli, "_CAPTURE_MAX_TOTAL_CHARS", 40)

    source_path, demo_path = cli._save_style_comparison_artifacts(
        str(style_readme),
        str(generated),
        keep_unknown_style_sections=False,
    )

    cfg_path = Path(demo_path).parent / "ROLE_README_CONFIG.yml"
    cfg_text = cfg_path.read_text(encoding="utf-8")
    assert source_path is not None
    assert "truncated: true" in cfg_text
    assert "title: One" in cfg_text
    assert "title: Two" in cfg_text
