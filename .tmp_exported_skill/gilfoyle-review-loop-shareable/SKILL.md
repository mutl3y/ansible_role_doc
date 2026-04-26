---
name: gilfoyle-review-loop
description: "Shareable critical review, plan, investigate, decide, fix, and validate loop for Python codebases. Use when: performing a hard-nosed code review with numbered findings; saving findings to a plan file; iterating in light or thorough cycles; delegating discovery to subagents when available; fixing issues in category-based waves; and validating changes with repo-specific test, lint, and typecheck gates."
argument-hint: "Path to the module or package to review, or an existing findings.yaml to continue"
---

# Gilfoyle Review Loop

## Tone

Findings stay clinical. Status updates, user-facing wrappers, and summary lines may use a dry deadpan wrapper if the user has not asked for a different tone. Read [tone-guide.md](./references/tone-guide.md) once per cycle before posting wrappers.

## First Use In A New Repo

Before the first real cycle in a new codebase, run the calibration prompt in [codebase-customization-prompt.md](./references/codebase-customization-prompt.md).

Use that pass to:

- infer package roots, test entrypoints, lint/typecheck commands, and ownership boundaries
- identify codebase-specific invariants that should always be checked in thorough reviews
- write the resolved calibration to `docs/plan/.gilfoyle-lessons/codebase-profile.md` if the repo allows local project notes
- update the gate commands in [gate-commands.md](./references/gate-commands.md) or mirror them in the codebase profile

If the repo does not yet have runnable test, lint, format, or typecheck commands, pause review work and run the validation bootstrap in [validation-bootstrap.md](./references/validation-bootstrap.md) first.

If the repo already has its own plan, notes, or governance folder, mirror that structure instead of forcing `docs/plan/`.

Before starting the calibration, run the host capability bootstrap in [capability-bootstrap.md](./references/capability-bootstrap.md).
The bootstrap determines:

- which discovery, edit, terminal, and delegation features are actually available
- which missing capabilities can be enabled or approved interactively
- which close alternatives should be recommended if the exact feature is unavailable
- what operating mode this cycle should use: `full-host`, `partial-host`, or `fallback`

## What This Produces

1. A graded findings report with numbered `FIND-NN` entries
2. A persisted `findings.yaml` plan file
3. Investigated decisions for ambiguous findings
4. Batched fix waves grouped by finding category
5. A green validation gate appropriate for the host repository

## When To Use

- You want a strict code review of a Python module or package
- You already have a `findings.yaml` and want to continue the loop
- You want a repeatable review -> plan -> investigate -> fix -> gate cycle
- You want to iterate until Critical and High findings are gone
- You want a reviewer that treats architecture, typing, ownership, fallbacks, and API boundaries as first-class concerns

## Invocation Options

The caller can specify these directly in the prompt. If omitted, infer sensible defaults and state them in the first update.

- `target`: module path, package path, or existing `findings.yaml`
- `cycle_mode`: `thorough`, `light`, or `continue`
- `focus_axis`: `architecture`, `typing`, `ownership`, `concurrency`, `error_handling`, `performance`, `security`, or `test_gaps`
- `gate_profile`: `minimal`, `standard`, `strict`, or a repo-specific custom profile
- `ledger_mode`: `use-existing`, `seed-if-missing`, or `ignore`
- `tone_mode`: `clinical`, `deadpan-wrapper`, or `user-specified`
- `stop_condition`: `findings-only`, `one-fix-wave`, `all-critical-high`, or `full-clean-signoff`

## Iteration Cadence

Repeated cycles `gN`. Depth scales inversely with cleanliness:

- Critical or High still open -> light review of recently changed files plus immediate neighbors
- Light review returns zero Critical or High -> thorough whole-target review
- Thorough review returns zero Critical or High on two different focus axes -> eligible for sign-off

Never sign off after a light review. Full cadence and sign-off discipline: [iteration-cadence.md](./references/iteration-cadence.md). Diff-scoped light-cycle rules: [light-cycle.md](./references/light-cycle.md).

## Safeguards Against False-Clean Verdicts

A clean review can be wrong because discovery failed or because the sweep was too shallow. Before accepting any zero-Critical/High verdict from a thorough review, run the floor checks in [safeguards.md](./references/safeguards.md).

## Procedure

### Phase 0 - Parallel Sweep

Dispatch four discovery passes in one batch when subagents are available:

- `sweep-typing`
- `sweep-ownership`
- `sweep-control-flow`
- `sweep-graph`

Cluster details and prompt skeletons: [parallel-execution.md](./references/parallel-execution.md) and [subagent-prompts.md](./references/subagent-prompts.md).

Every sweep should consult the learning ledger first if it exists. Ledger structure: [learning-ledger.md](./references/learning-ledger.md).

If an import graph cache exists, reuse it unless source mtimes prove it stale.

### Phase 1 - Review

Perform a critical review of the target. Grade overall quality and assign a `FIND-NN` ID to every finding.

Use [review-checklist.md](./references/review-checklist.md) to cover:

- duplication
- misplaced ownership
- weak typing
- silent fallbacks
- missing guards
- abstraction leakage
- brittle tests
- unsafe concurrency or state flow

If the target is non-trivial and you find almost nothing, assume the sweep was shallow and re-run Phase 0 more broadly.

### Phase 2 - Save Plan File

Persist findings to `docs/plan/<plan-id>/findings.yaml` or the repo's canonical planning location. Template: [plan-template.yaml](./references/plan-template.yaml).

### Phase 3 - Investigate Before Deciding

For any finding marked `needs_investigation`:

1. Read all involved files
2. Check import and dependency impact
3. Check tests that import or rely on the symbol
4. Check exports and re-export chains
5. Write a concrete conclusion before presenting options

### Phase 4 - Decide

Present mutually exclusive options only when a real decision remains. Record the chosen decision and rationale back into `findings.yaml`.

### Phase 5 - Per-Category Fix Waves

Default order from cheapest to riskiest:

- typing
- abstraction leakage
- silent fallback and missing guard
- duplication
- ownership

Run file-conflict checks before dispatching waves in parallel. Guidance: [parallel-execution.md](./references/parallel-execution.md).

For each fix:

- read the exact file before editing
- update exports and re-export chains
- preserve behavior unless the decision explicitly changes it
- scan [common-traps.md](./references/common-traps.md) before closing the wave

### Phase 6 - Gate

Between waves, run a path-filtered gate. Before closing findings, run the full gate. Start from [gate-commands.md](./references/gate-commands.md) and adapt it to the repo's actual commands.

### Phase 7 - Close Findings And Update Ledger

After a green gate:

1. Mark findings closed with evidence in `findings.yaml`
2. Append closed findings and new lessons to the ledger
3. Update focus-axis history and cycle log
4. Refresh the import graph cache if source mtimes exceed its timestamp

## Subagent-First Discovery

When the host supports explorer/search subagents, discovery work belongs there:

- symbol usage audits
- import consumer enumeration
- broad anti-pattern searches
- package-wide evidence gathering
- post-wave verification sweeps

Keep the orchestrator focused on decisions, edits, and integration.

If the host does not support subagents, emulate the same separation locally: do discovery first, summarize results tightly, then edit.

When capabilities are missing but the host supports approvals, extensions, or tool enablement, request access before falling back. Prefer this order:

1. use the exact capability already known to work in this host
2. request access, approval, or enablement for the closest missing capability
3. recommend the nearest practical alternative and explain the tradeoff
4. fall back to manual or single-threaded workflow only if the above are unavailable

## Key Principles

- Phase 0 is not optional for thorough reviews
- Read exact file content before editing
- Batch related edits within a wave
- Investigation is not guessing
- Treat docstrings and module boundaries as contracts
- `__all__` and re-export files are public API surfaces
- Bare tuples and anonymous high-arity callables are typing smells
- Silent fallbacks need justification or removal
- Delete dead compatibility paths only when imports and tests prove they are dead

## References

- [Tone Guide](./references/tone-guide.md)
- [Codebase Customization Prompt](./references/codebase-customization-prompt.md)
- [Capability Bootstrap](./references/capability-bootstrap.md)
- [Validation Bootstrap](./references/validation-bootstrap.md)
- [Iteration Cadence](./references/iteration-cadence.md)
- [Light Cycle](./references/light-cycle.md)
- [Safeguards](./references/safeguards.md)
- [Parallel Execution](./references/parallel-execution.md)
- [Learning Ledger](./references/learning-ledger.md)
- [Subagent Prompts](./references/subagent-prompts.md)
- [Common Traps](./references/common-traps.md)
- [Review Checklist](./references/review-checklist.md)
- [Plan Template](./references/plan-template.yaml)
- [Gate Commands](./references/gate-commands.md)
