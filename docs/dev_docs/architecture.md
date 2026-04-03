---
layout: default
title: Architecture
---

Prism is a static-analysis documentation engine for Ansible roles and collections.

It is best understood as a contract-and-governance pipeline, not only a renderer.

## Pipeline Overview

1. discover role/collection structure
2. parse YAML and Jinja signals
3. compute variable insights and scanner counters
4. render docs and machine-readable payloads

## Primary Components

- scanner core for role analysis
- collection plugin catalog extraction
- CLI orchestration (`role`, `collection`, `repo`)
- output rendering (`md`, `json`, `html`, `pdf`)

## Scanner Package Decomposition

`scanner.py` remains a public facade and delegates canonical runtime behavior to package-owned modules under `src/prism/`:

| Package | Ownership boundary |
| --- | --- |
| `scanner_core/` | request normalization, DI-driven orchestration, scan runtime/context assembly, variable discovery orchestration |
| `scanner_data/` | typed contracts and builders for request/result envelopes, scan payloads, report metadata, and variable rows |
| `scanner_extract/` | YAML/task traversal, variable/reference extraction, role feature collection, requirements and discovery loaders |
| `scanner_readme/` | README rendering, style parsing/normalization, documentation insights, section composition |
| `scanner_analysis/` | scanner metrics, report shaping, runbook generation, dependency analysis helpers |
| `scanner_io/` | output rendering/writing, scan output emission, YAML candidate loading and parse-failure reporting |
| `scanner_config/` | policy/config loading, style/section markers, legacy retirement behavior, runtime scan policy switches |
| `scanner_compat/` | compatibility bridge helpers isolated from canonical runtime paths |

Cross-package architecture guardrails enforce one-way decomposition: canonical scanner packages must not reverse-import `prism.scanner`, and private cross-package imports are blocked except for explicitly whitelisted seams.

`src/prism/repo_services.py` holds shared repo-intake, clone, fetch, sparse-checkout, and temp-workspace orchestration extracted from `cli.py`. Both `api.py` and `cli.py` import from `repo_services`.

## Package Migration Rules

API, CLI, and repo internals may move into dedicated packages when that improves ownership clarity, but `api.py`, `cli.py`, and `repo_services.py` must remain as thin stable shims preserving backward-compatible top-level imports.

Internal modules should prefer direct imports from canonical contract-owner modules (e.g., `contracts_output.py`) instead of the umbrella compatibility module `contracts.py` when no compatibility role is intended.

## Typed Seam Contracts

Typed contracts are centralized in `scanner_data/` and exposed via `scanner_data/contracts.py` and domain split modules (`contracts_request.py`, `contracts_output.py`, `contracts_report.py`, `contracts_variables.py`, `contracts_collection.py`, `contracts_errors.py`).

Primary scanner boundaries:

- request/runtime: `ScanOptionsDict`, `ScanContext`, `ScanBaseContext`, `ScanContextPayload`, `FailurePolicyContract`
- output envelopes: `ScanRenderPayload`, `RunScanOutputPayload`, `RunbookSidecarPayload`, `FinalOutputPayload`
- reporting: `ScannerReportMetadata`, `NormalizedScannerReportMetadata`, `ScannerCounters`, `AnnotationQualityCounters`, report row contracts
- public API results: `RoleScanResult`, `CollectionScanResult`, `RepoScanResult`

## Mypy Gate

`tox -e typecheck` runs `mypy` over `src/`. The gate is also wired as a pre-commit hook (`mypy-seams`) and runs in CI on every push/PR via `.github/workflows/prism.yml`.

Flags: `--ignore-missing-imports --disable-error-code=import-untyped --follow-imports=silent`

## Contract And Governance Layers

- contract layer: generated markdown/json defines automation interface behavior
- confidence layer: provenance and uncertainty flags mark non-deterministic areas
- governance layer: CI policies consume scanner flags and JSON fields
- learning loop: `prism-learn` aggregates fleet-wide trends and recommendations

## Design Principle

Prefer deterministic, reviewable output over speculative runtime inference.
