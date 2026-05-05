# Iteration Cadence

Use repeated cycles `g1`, `g2`, `g3`, and so on.

## Light Cycle

Use when Critical or High findings are already open and recent changes are scoped.

- review changed files
- review immediate neighbors and import consumers
- verify prior findings were actually fixed
- avoid broad sign-off claims

## Thorough Cycle

Use when a light cycle returns zero Critical and High, or when starting fresh on a large target.

- run the full Phase 0 sweep
- cover every module in the target package or slice
- rotate the primary focus axis
- apply the false-clean safeguards

## Sign-Off Rule

Do not sign off after a light cycle.

Require:

- two consecutive thorough reviews with zero Critical and High
- different primary focus axes across those reviews
- a green full validation gate
- ledger history showing all required focus axes have had at least one clean pass over time
