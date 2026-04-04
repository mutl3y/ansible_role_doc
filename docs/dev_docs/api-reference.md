---
layout: default
title: API Reference
---

This document provides reference documentation for Prism's public API functions.

## scan_role

```python
def scan_role(
    role_path: str,
    *,
    compare_role_path: str | None = None,
    style_readme_path: str | None = None,
    role_name_override: str | None = None,
    vars_seed_paths: list[str] | None = None,
    concise_readme: bool = False,
    scanner_report_output: str | None = None,
    include_vars_main: bool = True,
    include_scanner_report_link: bool = True,
    readme_config_path: str | None = None,
    adopt_heading_mode: str | None = None,
    style_guide_skeleton: bool = False,
    keep_unknown_style_sections: bool = True,
    exclude_path_patterns: list[str] | None = None,
    style_source_path: str | None = None,
    policy_config_path: str | None = None,
    fail_on_unconstrained_dynamic_includes: bool | None = None,
    fail_on_yaml_like_task_annotations: bool | None = None,
    ignore_unresolved_internal_underscore_references: bool | None = None,
    detailed_catalog: bool = False,
    include_collection_checks: bool = False,
    include_task_parameters: bool = True,
    include_task_runbooks: bool = True,
    inline_task_runbooks: bool = True,
    failure_policy: FailurePolicy | None = None,
) -> RoleScanResult:
```

Return the scanner payload as a Python dictionary for a single Ansible role.

**Parameters:**

- `role_path`: Path to the Ansible role directory
- `compare_role_path`: Optional path to another role for comparison
- `style_readme_path`: Path to style guide README
- `role_name_override`: Override the role name
- `vars_seed_paths`: List of paths to seed variable files
- `concise_readme`: Generate concise README
- `scanner_report_output`: Path to write scanner report
- `include_vars_main`: Include vars/main.yml
- `include_scanner_report_link`: Include scanner report link in README
- `readme_config_path`: Path to README configuration
- `adopt_heading_mode`: Heading adoption mode
- `style_guide_skeleton`: Generate style guide skeleton
- `keep_unknown_style_sections`: Keep unknown style sections
- `exclude_path_patterns`: Patterns to exclude from scanning
- `style_source_path`: Path to style source
- `policy_config_path`: Path to policy configuration
- `fail_on_unconstrained_dynamic_includes`: Fail on unconstrained includes
- `fail_on_yaml_like_task_annotations`: Fail on YAML-like annotations
- `ignore_unresolved_internal_underscore_references`: Ignore unresolved underscore references
- `detailed_catalog`: Include detailed task catalog
- `include_collection_checks`: Include collection checks
- `include_task_parameters`: Include task parameters
- `include_task_runbooks`: Include task runbooks
- `inline_task_runbooks`: Inline runbooks in output
- `failure_policy`: Failure handling policy

**Returns:** `RoleScanResult` dictionary containing scan results

## scan_collection

```python
def scan_collection(
    collection_path: str,
    *,
    compare_role_path: str | None = None,
    style_readme_path: str | None = None,
    vars_seed_paths: list[str] | None = None,
    concise_readme: bool = False,
    scanner_report_output: str | None = None,
    include_vars_main: bool = True,
    include_scanner_report_link: bool = True,
    readme_config_path: str | None = None,
    adopt_heading_mode: str | None = None,
    style_guide_skeleton: bool = False,
    keep_unknown_style_sections: bool = True,
    exclude_path_patterns: list[str] | None = None,
    style_source_path: str | None = None,
    policy_config_path: str | None = None,
    fail_on_unconstrained_dynamic_includes: bool | None = None,
    fail_on_yaml_like_task_annotations: bool | None = None,
    ignore_unresolved_internal_underscore_references: bool | None = None,
    include_rendered_readme: bool = False,
    detailed_catalog: bool = False,
    include_collection_checks: bool = False,
    include_task_parameters: bool = True,
    include_task_runbooks: bool = True,
    inline_task_runbooks: bool = True,
    runbook_output_dir: str | None = None,
    runbook_csv_output_dir: str | None = None,
    include_traceback: bool = False,
) -> CollectionScanResult:
```

Scan an Ansible collection root and return per-role payloads + metadata.

**Parameters:** Similar to `scan_role`, with additional collection-specific options:

- `collection_path`: Path to the Ansible collection directory
- `include_rendered_readme`: Include rendered README in output
- `runbook_output_dir`: Directory for runbook outputs
- `runbook_csv_output_dir`: Directory for CSV runbook outputs
- `include_traceback`: Include traceback in error reports

**Returns:** `CollectionScanResult` dictionary containing collection scan results

## scan_repo

```python
def scan_repo(
    repo_url: str,
    *,
    repo_ref: str | None = None,
    repo_role_path: str = ".",
    repo_timeout: int = 60,
    repo_style_readme_path: str | None = None,
    compare_role_path: str | None = None,
    style_readme_path: str | None = None,
    vars_seed_paths: list[str] | None = None,
    concise_readme: bool = False,
    scanner_report_output: str | None = None,
    include_vars_main: bool = True,
    include_scanner_report_link: bool = True,
    readme_config_path: str | None = None,
    adopt_heading_mode: str | None = None,
    style_guide_skeleton: bool = False,
    keep_unknown_style_sections: bool = True,
    exclude_path_patterns: list[str] | None = None,
    style_source_path: str | None = None,
    policy_config_path: str | None = None,
    fail_on_unconstrained_dynamic_includes: bool | None = None,
    fail_on_yaml_like_task_annotations: bool | None = None,
    ignore_unresolved_internal_underscore_references: bool | None = None,
    lightweight_readme_only: bool = False,
    include_collection_checks: bool = False,
    include_task_parameters: bool = True,
    include_task_runbooks: bool = True,
    inline_task_runbooks: bool = True,
    failure_policy: FailurePolicy | None = None,
) -> RepoScanResult:
```

Clone a repository source, scan the requested role path, and return a dict.

**Parameters:** Includes repository-specific options:

- `repo_url`: URL of the repository to clone
- `repo_ref`: Git reference (branch/tag/commit)
- `repo_role_path`: Path within repo to the role (default ".")
- `repo_timeout`: Clone timeout in seconds (default 60)
- `repo_style_readme_path`: Style README path in repo
- `lightweight_readme_only`: Generate lightweight README only

**Returns:** `RepoScanResult` dictionary containing repository scan results

## Data Types

- `RoleScanResult`: TypedDict containing role scan results
- `CollectionScanResult`: TypedDict containing collection scan results
- `RepoScanResult`: TypedDict containing repository scan results
- `FailurePolicy`: Enum for failure handling policies
