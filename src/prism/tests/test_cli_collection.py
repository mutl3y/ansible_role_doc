import json


from prism import cli


def test_cli_collection_root_json_mode_calls_scan_collection(monkeypatch, tmp_path):
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text("---\nname: demo\n", encoding="utf-8")

    def fake_scan_collection(collection_path, **kwargs):
        return {
            "collection": {"path": collection_path},
            "summary": {"total_roles": 0, "scanned_roles": 0, "failed_roles": 0},
            "dependencies": {"collections": [], "roles": [], "conflicts": []},
            "plugin_catalog": {
                "summary": {
                    "total_plugins": 0,
                    "types_present": [],
                    "files_scanned": 0,
                    "files_failed": 0,
                },
                "by_type": {
                    "filter": [],
                    "modules": [],
                    "lookup": [],
                    "inventory": [],
                    "callback": [],
                    "connection": [],
                    "strategy": [],
                    "test": [],
                    "doc_fragments": [],
                    "module_utils": [],
                },
                "failures": [],
            },
            "roles": [],
            "failures": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "collection-output"
    rc = cli.main(
        [
            "collection",
            str(collection_root),
            "-f",
            "json",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
    expected_out = out.with_suffix(".json")
    assert expected_out.exists()
    payload = json.loads(expected_out.read_text(encoding="utf-8"))
    assert payload["summary"]["total_roles"] == 0


def test_cli_collection_root_md_mode_writes_collection_and_role_docs(
    monkeypatch, tmp_path
):
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    def fake_scan_collection(collection_path, **kwargs):
        assert kwargs["include_rendered_readme"] is True
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 1, "scanned_roles": 1, "failed_roles": 0},
            "dependencies": {"collections": [], "roles": [], "conflicts": []},
            "plugin_catalog": {
                "summary": {
                    "total_plugins": 0,
                    "types_present": [],
                    "files_scanned": 0,
                    "files_failed": 0,
                },
                "by_type": {
                    "filter": [],
                    "modules": [],
                    "lookup": [],
                    "inventory": [],
                    "callback": [],
                    "connection": [],
                    "strategy": [],
                    "test": [],
                    "doc_fragments": [],
                    "module_utils": [],
                },
                "failures": [],
            },
            "roles": [
                {
                    "role": "web",
                    "rendered_readme": "# web role\n",
                }
            ],
            "failures": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "docs" / "collection-doc"
    rc = cli.main(["collection", str(collection_root), "-f", "md", "-o", str(out)])

    assert rc == 0
    collection_readme = out.with_suffix(".md")
    assert collection_readme.exists()
    assert "demo.toolkit Collection Documentation" in collection_readme.read_text(
        encoding="utf-8"
    )
    role_doc = out.parent / "roles" / "web.md"
    assert role_doc.exists()


def test_cli_collection_markdown_includes_plugin_catalog_sections(
    monkeypatch, tmp_path
):
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\nversion: 2.1.0\n",
        encoding="utf-8",
    )

    def fake_scan_collection(collection_path, **kwargs):
        assert kwargs["include_rendered_readme"] is True
        return {
            "collection": {
                "path": collection_path,
                "metadata": {
                    "namespace": "demo",
                    "name": "toolkit",
                    "version": "2.1.0",
                },
            },
            "summary": {"total_roles": 1, "scanned_roles": 1, "failed_roles": 0},
            "dependencies": {
                "collections": [{"key": "community.general", "version": "9.0.0"}],
                "roles": [{"key": "acme.base", "version": "1.2.3"}],
                "conflicts": [],
            },
            "plugin_catalog": {
                "summary": {
                    "total_plugins": 2,
                    "types_present": ["filter", "lookup"],
                    "files_scanned": 2,
                    "files_failed": 1,
                },
                "by_type": {
                    "filter": [
                        {
                            "name": "network",
                            "symbols": ["cidr_contains", "ip_version"],
                            "confidence": "high",
                        }
                    ],
                    "lookup": [{"name": "vault_lookup"}],
                },
                "failures": [
                    {
                        "relative_path": "plugins/filter/broken.py",
                        "stage": "ast_parse",
                        "error": "invalid syntax",
                    }
                ],
            },
            "roles": [
                {
                    "role": "web",
                    "rendered_readme": "# web role\n",
                    "payload": {
                        "metadata": {
                            "scanner_counters": {"task_files": 3, "templates": 5}
                        }
                    },
                }
            ],
            "failures": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "docs" / "collection-doc"
    rc = cli.main(["collection", str(collection_root), "-f", "md", "-o", str(out)])

    assert rc == 0
    readme = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "## Plugin Catalog" in readme


def test_cli_collection_markdown_bounds_large_role_lists(monkeypatch, tmp_path):
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    roles = [
        {
            "role": f"role_{index:03d}",
            "rendered_readme": f"# role_{index:03d}\n",
            "payload": {
                "metadata": {
                    "scanner_counters": {"task_files": index, "templates": index}
                }
            },
        }
        for index in range(70)
    ]

    def fake_scan_collection(collection_path, **kwargs):
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 70, "scanned_roles": 70, "failed_roles": 0},
            "dependencies": {"collections": [], "roles": [], "conflicts": []},
            "plugin_catalog": {
                "summary": {
                    "total_plugins": 0,
                    "types_present": [],
                    "files_scanned": 0,
                    "files_failed": 0,
                },
                "by_type": {
                    "filter": [],
                    "modules": [],
                    "lookup": [],
                    "inventory": [],
                    "callback": [],
                    "connection": [],
                    "strategy": [],
                    "test": [],
                    "doc_fragments": [],
                    "module_utils": [],
                },
                "failures": [],
            },
            "roles": roles,
            "failures": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "docs" / "collection-doc"
    rc = cli.main(["collection", str(collection_root), "-f", "md", "-o", str(out)])

    assert rc == 0
    readme = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "... and 10 more roles" in readme


def test_cli_collection_root_rejects_non_json_or_md_format(tmp_path):
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )

    out = tmp_path / "collection-doc"
    rc = cli.main(["collection", str(collection_root), "-f", "txt", "-o", str(out)])

    assert rc == 2


def test_cli_collection_vars_context_alias_is_forwarded(monkeypatch, tmp_path, capsys):
    calls: dict = {}
    collection_root = tmp_path / "collection"
    (collection_root / "roles").mkdir(parents=True)
    (collection_root / "galaxy.yml").write_text(
        "---\nnamespace: demo\nname: toolkit\n",
        encoding="utf-8",
    )
    context_dir = tmp_path / "group_vars"
    context_dir.mkdir()

    def fake_scan_collection(collection_path, **kwargs):
        calls["vars_seed_paths"] = kwargs.get("vars_seed_paths")
        return {
            "collection": {
                "path": collection_path,
                "metadata": {"namespace": "demo", "name": "toolkit"},
            },
            "summary": {"total_roles": 0, "scanned_roles": 0, "failed_roles": 0},
            "dependencies": {"collections": [], "roles": [], "conflicts": []},
            "plugin_catalog": {
                "summary": {
                    "total_plugins": 0,
                    "types_present": [],
                    "files_scanned": 0,
                    "files_failed": 0,
                },
                "by_type": {
                    "filter": [],
                    "modules": [],
                    "lookup": [],
                    "inventory": [],
                    "callback": [],
                    "connection": [],
                    "strategy": [],
                    "test": [],
                    "doc_fragments": [],
                    "module_utils": [],
                },
                "failures": [],
            },
            "roles": [],
            "failures": [],
        }

    import prism.api as api_module

    monkeypatch.setattr(api_module, "scan_collection", fake_scan_collection)

    out = tmp_path / "collection-output"
    rc = cli.main(
        [
            "collection",
            str(collection_root),
            "--vars-context-path",
            str(context_dir),
            "--vars-seed",
            str(context_dir),
            "-f",
            "json",
            "-o",
            str(out),
        ]
    )

    assert rc == 0
