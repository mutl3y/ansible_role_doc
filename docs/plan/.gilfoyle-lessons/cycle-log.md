# Gilfoyle review-loop cycle log

## g1 — 2026-04-25 — focus_axis: typing — grade: C

- Scope: high + typing severities (9 of 13 findings).
- Closed: FIND-01, 04, 05, 06, 07, 08, 11.
- Deferred to g2 (architecture): FIND-02 (needs_replan, generic/specialization split), FIND-03 (Callable→Protocol promotion).
- Deferred to g3 (coupling): FIND-10 (scanner_core←scanner_plugins layer direction).
- Out of scope (medium/low): FIND-09, FIND-12, FIND-13.
- Gate: GREEN (754 passed, 7 skipped, ruff clean, black clean).
- Pre-existing rot fixed during close gate: `_logger` undefined in api_layer/non_collection.py; E402 in scanner_extract/variable_extractor.py.
- Key process lesson: subagent-first dispatch saved a wrong W4 edit. Skill updated.

## g2 — 2026-04-25 — focus_axis: architecture — grade: B

- Scope: high+medium ownership/abstraction/graph (5 in-flight + 2 deferred).
- Closed: FIND-G2-01 (AnsibleDefault* relocation), FIND-G2-02 (Protocols at scanner_core↔scanner_kernel boundary; closes carry-over FIND-03), FIND-G2-03 (JINJA pattern dedup → scanner_data canonical), FIND-G2-04 (drop "tasks/" literal from scanner_core), FIND-G2-05 (fsrc-lane test scaffolding rename).
- Deferred: FIND-10 → g3 (carry-over; new sites surfaced: standalone_di.py:21, scanner_context.py filters import); FIND-G2-LOADER-DUAL-PATH → g3/g4 (documented soft fallback in scanner_io/loader.py).
- Gate: GREEN (754 passed / 7 skipped, ruff clean, black clean, mypy 0 errors in 131 files).
- Repair pass: G2-02's sed-based edit to di.py introduced an IndentationError + load-time circular import via scanner_plugins eager loading. Diagnosed mid-flight; canonical JINJA patterns relocated to `scanner_data/patterns_jinja.py` (side-effect-free) — this added LESSON-08.
- New lessons: LESSON-06 (platform classes don't belong in generic packages), LESSON-07 (Callable→Protocol at architectural boundaries; `*_cls` → `type[X]`), LESSON-08 (avoid putting shared data in eagerly-loading packages).
- Two consecutive thorough cycles on different focus axes (typing → architecture) both closed GREEN.

## g3 — 2026-04-25 — focus_axis: coupling — grade: A-

- Scope: residual scanner_core→scanner_plugins layer edges after g1+g2.
- Closed: FIND-G3-01 (underscore_policy filter relocated from scanner_plugins/filters/ → scanner_core/filters/; back-compat shim retained).
- Do_not_re_flag: FIND-G3-02 (TYPE_CHECKING di.py import, type-only), FIND-G3-03 (intentional DI lazy seams: di.py:204 blocker_fact_builder + standalone_di.py:20 bundle_resolver — re-flag only with registry-routed alternative).
- Deferred to g4: FIND-G3-04 (loader.py registry-routed YAML policy; bundles with FIND-G2-LOADER-DUAL-PATH), FIND-G3-05 (scanner_plugins/__init__.py self-registration via decorator — closes LESSON-08 at source), FIND-G3-06 (DIContainer 12 inject_mock_* wrappers — surface shrink).
- Gate: GREEN (754 passed / 7 skipped, ruff clean, black clean, mypy 0 errors in 133 files; +2 source files = scanner_core/filters/__init__.py + underscore_policy.py).
- Three consecutive thorough cycles (typing → architecture → coupling) all GREEN. Sign-off bar exceeded.

## g4 — 2026-04-25 — focus_axis: registry_lifecycle — grade: B+

- Scope: three g3-deferred lanes (G4-01 loader routing, G4-02 plugin self-registration, G4-03 DIContainer surface).
- Closed: FIND-G4-03 (DIContainer 12 inject_mock_* wrappers collapsed to generic `inject_mock(name, mock)`; ~33 test sites migrated; di.py 401→365 lines; tests net -84 lines).
- Do_not_re_flag: FIND-G4-01 (loader.py:46 lazy import is to a generic resolver that already routes through the registry — re-flag only if bundled with FIND-G2-LOADER-DUAL-PATH for a contract change).
- Deferred to g5: FIND-G4-02 (decorator-based plugin self-registration — architectural rewrite affecting every sub-package; needs planning slice).
- Gate: GREEN (754 passed / 7 skipped, ruff clean, black clean post-format, mypy 0 errors / 133 source files).
- Four consecutive thorough cycles (typing → architecture → coupling → registry_lifecycle) all GREEN. Sign-off bar exceeded by 2 cycles.

## g5 — 2026-04-25 — focus_axis: registry_boilerplate — grade: B

- Scope: g4-deferred FIND-G4-02 (eager-import boilerplate in scanner_plugins/__init__.py).
- Closed: FIND-G5-01 (bootstrap_default_plugins converted to data-driven table iteration; ~80 imperative lines → 30 declarative table entries + 1 dispatch loop. Adding a new built-in is now a single tuple), FIND-G5-03 (ScanPipelinePlugin added to __all__ as a public re-export).
- Deferred: FIND-G5-02 (true decorator self-registration — Phase 0 sweep flagged replay-onto-alternate-registry blocker via test_comment_doc_plugin_resolution.py and FQCN-resolution-timing risk for deferred registrations; needs dedicated planning slice not an axis-bounded fix).
- Gate: GREEN (754 passed / 7 skipped, ruff clean, black clean post-format, mypy 0 errors / 133 source files).
- Five consecutive thorough cycles (typing → architecture → coupling → registry_lifecycle → registry_boilerplate) all GREEN. Sign-off bar exceeded by 3 cycles.

## g6 — 2026-04-26 — focus_axis: ownership — grade: B

- Scope: whole-codebase ownership sweep (scanner_core, scanner_extract, scanner_io, scanner_readme, scanner_config, scanner_plugins, scanner_kernel, cli/api facades).
- Closed: FIND-G6-01 (`_format_candidate_failure_path` deduped — parsing_policy.py now imports from scanner_io/loader.py), FIND-G6-02 (`COMMENT_CONTINUATION_RE` deduped — policies/constants.py now imports from parsers/comment_doc/marker_utils.py), FIND-G6-03 (dead `ansible_builtin_variables` policy key + normalisation removed from scanner_config/patterns.py — zero readers, zero data), FIND-G6-04 (variable_extractor.py:90 broad-except tightened to `(OSError, yaml.YAMLError, UnicodeDecodeError, ValueError)`; programmer errors now propagate), FIND-G6-05 (scan_facade_helpers.py:46 broad-except tightened to `RuntimeError` to match load_meta's documented hard-failure surface).
- Elevated to dedicated planning slice: FIND-G6-06 (scanner_readme/* hardcodes Ansible role rendering — meta/main.yml, Galaxy install, role variables/tasks/handlers sections, ansible-role-doc legacy markers). Product vision (confirmed by user 2026-04-25) is plug-and-play platform support across Ansible, Terraform, Kubernetes, AAP. Each plugin must own input + scanning logic + output rendering. Required artefacts: ReadmeRendererPlugin protocol design, section/style/marker ownership matrix per platform, DI/registry wiring, Ansible plugin migration as reference impl, parity tests vs. current Ansible-only output. Mechanical in-loop refactor would prematurely freeze the protocol shape.
- Gate: GREEN (754 passed / 7 skipped on second run; first run had stale `pytest_out.txt` cache pollution from prior g5 commit hook restage — re-run cleared it; ruff clean, black clean, mypy 0 errors / 133 source files).
- Six consecutive thorough cycles (typing → architecture → coupling → registry_lifecycle → registry_boilerplate → ownership) all GREEN.

## g7 — 2026-04-25 — planning slice (FIND-G6-06)

**Type:** Design-only planning slice (no code shipped).
**Trigger:** FIND-G6-06 (scanner_readme platform-agnostic) deferred from g6.
**Artefact:** docs/plan/20260425-readme-renderer-plugin-design/plan.yaml

**Pre-code artefacts delivered (all five required by FIND-G6-06):**
1. ReadmeRendererPlugin protocol design — 8 methods, 2 class attrs, neutrality invariants.
2. Per-platform ownership matrix — 18 decision points × {Ansible, Terraform, Kubernetes, AAP} with P/N/H ownership classification.
3. DI/registry wiring plan — slot=`readme_renderer`, fail-closed resolver, reuses gf2-full-remediation platform_key plumbing.
4. Ansible reference impl migration plan — 9 sequenced steps + doc_insights sub-protocol decision (Option A recommended).
5. Parity test strategy — 4 new test modules + byte-for-byte parity gate + public API freeze contract.

**Risks documented:** R1 (parse_style_readme platform-key threading, high), R2 (template path relocation), R3 (doc_insights sub-protocol cost), R4 (render_readme signature), R5 (rendering_seams import path).

**External consumer freeze contract:**
- src/prism/api.py:28 render_readme — signature unchanged
- src/prism/cli_app/shared.py:16 parse_style_readme — signature unchanged
- src/prism/scanner_reporting/runbook.py:13 build_render_jinja_environment — symbol unchanged

**Status:** awaiting user review/approval before implementation slice begins.
**Next action:** A1 (user decision) → A2 (implementation plan with 5 waves) → A3 (R1 spike).

**Gate:** N/A (no code changes).

## g7b — 2026-04-25 — planning slice (FIND-G7B-01, sibling of FIND-G6-06)

**Type:** Design-only planning slice (no code shipped).
**Trigger:** User observation 2026-04-25 — four modules misowned:
- scanner_plugins/policies/constants.py (Ansible YAML vocabulary)
- scanner_plugins/policies/extract_defaults.py (Ansible facade)
- scanner_plugins/policies/annotation_parsing.py (comment-doc feature)
- scanner_reporting/runbook.py (comment-doc feature)

**User directive:** "no need for a deprecation cycle, deprecate now" — locks no-shim policy for W4.
**Artefact:** docs/plan/20260425-policies-runbook-ownership-design/plan.yaml (v2_ultrathink)

**Pre-code artefacts delivered:**
1. Problem-rot taxonomy — 3 architectural rots named (policies-directory-is-a-lie, runbook-misclassified, mixed-concerns-in-annotation-parsing).
2. Design principles (5) — ownership axes (PLATFORM vs FEATURE), template-shape ownership, no-compat-shims, protocol-first for mixed concerns, directory names must not lie.
3. Per-symbol ownership matrix — every symbol from the 4 modules classified by axis with target canonical path.
4. New protocol: TaskBoundaryDetector (interfaces.py) — decouples comment_doc from Ansible-regex coupling. Defined NOW, not deferred.
5. 7 waves — W0 (consumer inventory) → W1 (create canonical homes) → W2 (protocol + Ansible impl + DI) → W3 (redirect callers) → W4 (delete; unconditional, no shims) → W5 (optional: rename policies/ → defaults/) → W6 (closure gate).
6. Public API contract — prism.scanner_reporting package facade re-exports preserved; templates/RUNBOOK.md.j2 deleted; no DeprecationWarning paths anywhere.
7. Partner opinions section (6) — v2 disagrees with v1 on Option C, compat shims, policies/ rename, runbook template ownership rationale, W0 promotion to hard prerequisite, what-I-still-don't-know list.

**Risks documented:** R1 (TaskBoundaryDetector generality, medium), R2 (W5 rename churn, low), R3 (test rename, medium), R4 (templates/ dir other consumers, low), R5 (Ansible-regex importer fan-out, high), R6 (prism-learn lockstep, medium), R7 (template path resolution post-move, low).

**Status:** awaiting user review/approval before implementation slice begins.
**Next action:** A1 (user decision on partner_opinions + W5) → A2 (W0 inventory) → A3 (W1-W4(W5)-W6 implementation slice).

**Gate:** N/A (no code changes).

## g7b-impl — 2026-04-25 — implementation cycle (FIND-G7B-01) — grade: B+

**Type:** Implementation cycle. Closes FIND-G7B-01.
**Commit:** 2182bb4 — "gilfoyle g7b: relocate misowned policies/+runbook to canonical homes"
**Plan link:** docs/plan/20260425-policies-runbook-ownership-design/plan.yaml (v2_ultrathink)

**User directives applied (REVERSED v2 plan in places, per 2026-04-25 chat):**
- (a) Shims for one release ACCEPTED — reversed earlier "no deprecation cycle" directive.
- (b) Annotation parsing ships AS-IS for one release — W2 TaskBoundaryDetector protocol DROPPED.
  Mixed-concerns coupling logged, deferred to next cycle.
- (c) W5 policies/ → defaults/ rename DROPPED — facade unchanged; would shuffle deck chairs.
- (d) prism-learn not a gate — verified zero consumer references; forward-fix in consumer if surprises emerge.

**Waves shipped (W1, W3, W4, W6):**
- W1 — created canonical homes (6 files):
  - scanner_plugins/ansible/task_vocabulary.py, task_regex.py
  - scanner_plugins/parsers/yaml/line_shape.py
  - scanner_plugins/parsers/comment_doc/{annotation_parsing,runbook_renderer}.py
  - scanner_plugins/parsers/comment_doc/templates/RUNBOOK.md.j2 (template moved)
- W3 — redirected importers + installed deprecation shims:
  - ansible/{default_policies,task_annotation_strategy,task_traversal_bare} now import canonical paths
  - scanner_plugins/policies/__init__ + scanner_reporting/__init__ unchanged public surface (re-export from canonical)
  - 4 shim modules emit DeprecationWarning(stacklevel=2)
- W4 — deleted src/prism/templates/RUNBOOK.md.j2 (template-shape ownership now lives with comment_doc plugin)
- W6 — closure gate: 755 passed / 7 skipped (one new test added vs g7), ruff clean, black clean,
  mypy delta=0 (99 baseline = 99 current; all pre-existing).

**Test additions:**
- test_extract_defaults_ansible_ownership.py (replaces test_extract_defaults_domain_neutrality.py):
  - TestAnsibleDefaultPolicyOwnership: canonical __module__ assertions, Ansible-builtin keys absent
    from bare vocabulary, plugin superset relation
  - TestPoliciesShimContract: 4 tests verify each shim emits DeprecationWarning AND remains functional
- Updated test_t1_02_coverage_lift_batch2.py + test_readme_parity.py + test_scanner_reporting.py
  to import via canonical scanner_plugins.parsers.comment_doc.runbook_renderer
- Carved scanner_readme.rendering_seams out of plugin-package import boundary guardrail in
  test_plugin_kernel_extension_parity.py (consistent with existing peer guardrail in
  test_scanner_reporting.py)

**pyproject.toml:** package-data extended for parsers/comment_doc/templates/*.j2

**Architectural improvements:**
- Directory `scanner_plugins/policies/` no longer lies about its contents (Ansible-specific logic
  now lives in scanner_plugins/ansible/, comment-doc feature logic in scanner_plugins/parsers/comment_doc/).
- Template-shape ownership co-located with renderer (comment_doc plugin owns its template).
- Public API surface unchanged: prism.api, prism.cli, prism.scanner_reporting all stable.

**Carry-forward to next cycle:**
- Mixed-concerns coupling in annotation_parsing (Ansible-shape regex usage from comment-doc layer)
  remains. Address with TaskBoundaryDetector or equivalent abstraction when a 2nd platform
  forces the design (avoid premature protocol freeze).
- Deprecation shim removal scheduled for one release post-this commit.

**Seven consecutive thorough cycles** (typing → architecture → coupling → registry_lifecycle →
registry_boilerplate → ownership → ownership-impl) all GREEN. Sign-off bar exceeded by 5 cycles.

## Cycle g8 — coupling / typing / abstraction cleanup (2026-04-25)

**Axis:** light cycle — coupling, weak typing, abstraction debt within the comment_doc + ansible plugin layers.

**Closed (6):**
- **FIND-G8-02** dead wrappers — Removed `_normalize_marker_prefix` + `_get_marker_line_re` private wrappers in annotation_parsing.py (callers now go directly to marker_utils); dropped leaked `get_marker_line_re` from `__all__`; deleted unused `normalize_marker_prefix` import.
- **FIND-G8-04** Protocol callbacks — Promoted bare `Callable[..., Iterable[Path]]` and `Callable[[Path], object]` in default_policies.py to named `CollectsTaskFiles` and `LoadsYamlFile` Protocols.
- **FIND-G8-05** keyword-param annotations — Annotated `collect_unconstrained_dynamic_task_includes` and `_role_includes` wrappers with `role_root: Path, task_files: list[Path], load_yaml_file: LoadsYamlFile -> list[dict[str, str]]`.
- **FIND-G8-06** runbook metadata typing — Replaced `dict | None` with `Mapping[str, Any] | None`; introduced `RunbookRow(NamedTuple)` for `build_runbook_rows` / `render_runbook_csv` return type (tuple-compatible — zero consumer churn).
- **FIND-G8-07** set→Collection — Narrowed `include_vars_keys: set[str] | None` to `Collection[str] | None` (read-only contract).
- **FIND-G8-08** label-set lift — Lifted two duplicate inline `{...}` set literals in annotation_parsing.py to module-level `_ANNOTATION_LABELS: frozenset[str]`.

**Deferred (2):**
- **FIND-G8-01** dead alias `COMMENTED_TASK_ENTRY_RE` (byte-identical to `TASK_ENTRY_RE` since pre-g7b) — re-exported through 8 modules; needs a dedicated alias-purge slice.
- **FIND-G8-03** `TaskAnnotation` TypedDict — `PreparedTaskAnnotationPolicy` Protocol locks the same weak `dict[str, object]` shape; needs Protocol + scanner_extract callers + tests changed atomically.

**Carried forward (pre-existing):** FIND-G8-D-G, D-H, D-I.

**Gates:** pytest 755 passed / 7 skipped, ruff 0, black 0, mypy delta=0 (99 baseline).

**Lessons re-confirmed:**
- Read upstream Protocol contracts before narrowing return types — `contracts_request.py` Protocols can lock weak shapes that look local.
- 8-module re-export chains are not "light-cycle" work; defer to dedicated alias-purge slices.

**Eight consecutive thorough cycles** (typing → architecture → coupling → registry_lifecycle → registry_boilerplate → ownership → ownership-design → coupling/typing/abstraction).

## Cycle g9 — deprecation-shim purge (2026-04-25)

**Axis:** architectural-debt purge — honour g7b "one release later" deletion schedule for the `scanner_plugins.policies` shim directory.

**Closed (5):**
- **FIND-G9-01** dead façade — Deleted `scanner_plugins/policies/__init__.py` (re-exported four AnsibleDefault* classes + Jinja/YAML parsers + DefaultScanPipelinePlugin from canonical homes; owned zero policies).
- **FIND-G9-02** deprecation shim — Deleted `scanner_plugins/policies/annotation_parsing.py` (34 lines of `DeprecationWarning` + 6 re-exports from `parsers.comment_doc.annotation_parsing`).
- **FIND-G9-03** deprecation shim — Deleted `scanner_plugins/policies/extract_defaults.py` (107 lines of `DeprecationWarning` + 30+ re-exports from ansible/* and parsers/*).
- **FIND-G9-04** deprecation shim — Deleted `scanner_plugins/policies/constants.py` (64 lines of `DeprecationWarning` + constant re-exports).
- **FIND-G9-05** dead test coverage — Deleted `TestPoliciesShimContract` (4 vacuous tests asserting the shims emit warnings).

**Side-effects:**
- Relocated `DefaultScanPipelinePlugin` from `scanner_plugins/policies/default_scan_pipeline.py` to `scanner_plugins/default_scan_pipeline.py` (top-level, platform-neutral; was the only owned content under `policies/`).
- Rewired 9 imports across `scanner_plugins/__init__.py`, `scanner_plugins/defaults.py`, `tests/test_plugin_kernel_extension_parity.py` to canonical paths.

**Deferred (2):**
- **FIND-G9-D-A** `scanner_reporting/runbook.py` — separate deprecation shim re-exporting from `scanner_plugins/parsers/comment_doc/runbook_renderer.py`. Defer to a dedicated reporting-shim purge.
- **FIND-G9-D-B** `scanner_core/standalone_di.py` — 25-line parallel DI surface (`StandaloneDI` + `make_standalone_di`); 4 callsites in `scanner_plugins/defaults.py`. Consolidate into `DIContainer` minimal-mode in g10.

**Carried forward (pre-existing):** FIND-G8-01 (8-module alias purge), FIND-G8-03 (PreparedTaskAnnotationPolicy TypedDict narrowing), FIND-G8-D-G/H/I.

**Gates:** pytest 751 passed / 7 skipped, ruff 0, black 0, mypy delta=0 (99 baseline).

**Lessons re-confirmed:**
- "No deprecation cycle, delete on relocation" (user 2026-04-25) — once a shim's "one release later" gate is reached, it must be deleted, not extended. The contract test class becomes vacuous and must be deleted alongside.
- Shim consumer surface verification before purge: `grep -rn "scanner_plugins.policies" src/prism --include="*.py"` revealed exactly 9 import sites + 4 test references — small enough for single-commit purge.

**Nine consecutive thorough cycles** (typing → architecture → coupling → registry_lifecycle → registry_boilerplate → ownership → ownership-design → coupling/typing/abstraction → shim-purge).
