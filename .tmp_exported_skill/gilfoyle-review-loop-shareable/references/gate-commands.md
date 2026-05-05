# Gate Commands

These are templates. Replace placeholders with the repo's real commands during calibration.

## Suggested Profiles

- `minimal`: fastest confidence check during active fixing
- `standard`: default full-cycle closure gate
- `strict`: standard gate plus slow or deeper checks

## Path-Filtered Gate

Run between fix waves.

```bash
CHANGED=$(git diff --name-only HEAD -- '*.py')
TEST_TARGETS="<map changed files to relevant tests>"
[ -n "$TEST_TARGETS" ] && <test-command> $TEST_TARGETS
[ -n "$CHANGED" ] && <lint-command> $CHANGED
[ -n "$CHANGED" ] && <format-check-command> $CHANGED
```

## Standard Full Gate

Run before closing findings.

```bash
<primary-test-command>
<secondary-test-command-if-needed>
<lint-command-on-scope>
<format-check-command-on-scope>
<typecheck-command-if-required>
```

## Auto-Format Then Re-Check

```bash
<format-command> <changed files>
<lint-command-on-scope>
<format-check-command-on-scope>
```

## Gate Rules

- Path-filtered gate between waves
- Full gate before closing findings
- Typecheck required for structural changes if the repo has a typecheck step
- Do not claim closure on a wave that only passed a narrow smoke test
