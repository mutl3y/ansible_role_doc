# Parallel Execution

Use parallelism to keep discovery fast and edit context small.

## Phase 0 Sweep Clusters

Dispatch up to four concurrent discovery passes:

- `sweep-typing`: vague types, tuples, callbacks, protocol gaps, sentinel abuse
- `sweep-ownership`: platform leakage, boundary confusion, misplaced defaults, DI hardwiring
- `sweep-control-flow`: silent fallbacks, broad exceptions, missing guards, hidden state mutation
- `sweep-graph`: import chains, re-export surfaces, cyclic-risk moves, orphan wrappers

Each pass should return a compact observation list with file references and candidate categories.

## Per-Category Fix Waves

Group fixes by category to reduce context churn:

- typing
- abstraction
- silent_fallback and guard
- duplication
- ownership

Run categories in parallel only when their file sets do not overlap.

## File-Conflict Check

Before parallel waves, compare the affected file sets.

If any file appears in both sets, serialize those waves.

## Full Gate Concurrency

When the repo supports it, run:

- primary test lane
- secondary or broader test lane
- lint
- format check
- typecheck if fast enough

in parallel with fail-fast aggregation. If the machine is CPU-bound, serialize the heaviest test lanes and keep lint running in parallel.
