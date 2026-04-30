# Learning Ledger

The loop gets better when it records what it already learned.

## Suggested Files

All paths are relative to the repository root unless the repo already has a better home for them.

| File | Scope | Purpose |
|---|---|---|
| `docs/plan/<plan-id>/closed_findings.yaml` | Per plan | Closed finding history and skip-patterns |
| `docs/plan/.gilfoyle-lessons/lessons.yaml` | Repo-wide | Confirmed anti-patterns and recurring false positives |
| `docs/plan/.gilfoyle-lessons/focus-axis-log.yaml` | Repo-wide | Track focus-axis rotation and clean passes |
| `docs/plan/.gilfoyle-lessons/import-graph.json` | Repo-wide | Cached import/dependency graph |
| `docs/plan/.gilfoyle-lessons/cycle-log.md` | Repo-wide | Append-only cycle summaries |
| `docs/plan/.gilfoyle-lessons/digest.yaml` | Repo-wide | Compact single-read summary for discovery subagents |

## Minimal Formats

### `closed_findings.yaml`

```yaml
plan_id: example-review-20260425
closed:
  - id: FIND-01
    category: duplication
    title: "Duplicate parsing helper in two modules"
    closed_in_cycle: g2
    closed_evidence: "tests, lint, and typecheck green"
    skip_pattern: "Do not re-flag the old helper pair; they were consolidated."
```

### `lessons.yaml`

```yaml
anti_patterns:
  - id: LESSON-01
    pattern: "Factory hardcodes a concrete implementation instead of resolving via registry"
    category: ownership
    why: "Breaks extensibility and bypasses the declared seam."

false_positives:
  - id: FP-01
    pattern: "Compatibility wrappers retained with explicit deprecation notice"
    suppress_in_categories: [duplication, abstraction]

invariants:
  - "Core orchestration modules should not import platform-specific adapters directly."
  - "Validation helpers must fail closed when required context is missing."
```

### `focus-axis-log.yaml`

```yaml
axes:
  - cycle: g1
    primary: typing
    result: 2_critical_3_high
  - cycle: g2
    primary: ownership
    result: zero_critical_high
required_axes:
  - architecture
  - typing
  - ownership
  - concurrency
  - error_handling
  - performance
  - security
  - test_gaps
```

### `digest.yaml`

```yaml
generated_at: 2026-04-25T19:00:00Z
focus_axis_due_next: error_handling
anti_patterns: []
false_positives: []
closed_skip_patterns: {}
invariants: []
```

## Subagent Read Contract

Before flagging anything, discovery subagents should read only:

- `docs/plan/.gilfoyle-lessons/digest.yaml`
- `docs/plan/.gilfoyle-lessons/import-graph.json`

Fall back to the raw ledger files only if the digest is missing.
