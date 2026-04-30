# Light Cycle

A light cycle is a disciplined diff-scoped review, not a casual skim.

## Scope

- changed files in the active cycle
- tests changed alongside them
- direct import consumers
- direct dependencies if the change touched shared contracts, typing, ownership, or control flow

## Minimum Checks

- re-open any prior finding that was only partially fixed
- look for new typing regressions created by the edits
- verify exports, import chains, and moved symbols
- probe for one-step blast radius beyond the changed files

## Escalate Back To Thorough

Switch to a thorough cycle if:

- the light cycle finds zero Critical and High
- the change touched shared contracts, dependency injection, routing, or package exports
- the diff is small but architecturally central
- the discovery pass looks suspiciously thin
