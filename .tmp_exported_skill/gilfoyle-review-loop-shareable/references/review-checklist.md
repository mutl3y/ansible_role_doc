# Review Checklist

Use this to force coverage across the boring files, not just the dramatic ones.

## Duplication

- Are near-identical helpers split across modules?
- Did a compatibility layer become a shadow implementation?
- Are test fixtures duplicating production parsing or setup logic?

## Ownership

- Does a supposedly generic layer import platform, framework, or transport details?
- Are factories or registries bypassed by direct concrete imports?
- Are defaults living in the wrong layer?

## Weak Typing

- Are bare tuples carrying structural meaning?
- Are high-arity callbacks anonymous instead of modeled?
- Are sentinel `None` or `object()` values masking contract gaps?
- Did a recent refactor weaken types to get the code through?

## Silent Fallback And Guards

- Are broad exceptions swallowing real failures?
- Is missing context replaced with default behavior silently?
- Are state preconditions assumed but never checked?

## Abstraction Leakage

- Are private helpers imported across module boundaries?
- Are `_`-prefixed symbols exported publicly?
- Does the public API expose internal transitional seams?

## Tests

- Are there direct tests for the changed seam?
- Do tests import moved symbols from stale paths?
- Is the absence of tests hiding a risky structural change?

## Concurrency And State

- Is mutable shared state threaded implicitly?
- Are caches keyed too loosely?
- Is async or threaded control flow missing ownership or locking boundaries?
