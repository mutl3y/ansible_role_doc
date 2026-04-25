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
