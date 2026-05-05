# Validation Bootstrap

Use this when the repository does not already expose clear test, lint, format, and typecheck commands.

## Goal

Help the user establish a minimal, repeatable validation gate before the review loop starts making structural changes.

## Model Behavior Contract

If the repo lacks any of these:

- a runnable test command
- a lint command
- a format or format-check command
- a typecheck command, when the language ecosystem normally supports one

then do not invent fake green gates and do not proceed as if the repo already has validation.

Instead:

1. inspect the repo to discover the language, package manager, test framework, and existing scripts
2. identify what already exists but is undocumented
3. propose the smallest credible validation bundle for this repo
4. ask the user for approval before adding or changing tooling
5. scaffold the commands or scripts if the user approves
6. record the resulting commands in the codebase profile and gate commands reference

## What To Look For

- `package.json`, `pyproject.toml`, `tox.ini`, `Makefile`, `justfile`, `requirements*.txt`
- existing CI workflows
- existing test directories and naming conventions
- existing lint or formatter config files
- existing typecheck config files

## Minimal Acceptable Gate

Prefer the smallest useful bundle:

- tests: whatever framework the repo is already closest to
- lint: the simplest established linter for the language
- format: the simplest established formatter for the language
- typecheck: only if the ecosystem and repo size make it reasonable

Avoid introducing an entire tooling stack when a smaller one will do.

## Human-Facing Questions To Ask

- "I don't see a runnable test command yet. Do you want me to scaffold a minimal one for this repo?"
- "There is no existing lint or format command. Should I wire up a lightweight default based on the current stack?"
- "I found tests but no single command to run them. Do you want me to add a script, task, or make target so the review gate is repeatable?"
- "Typecheck is not set up. Do you want a minimal typecheck step now, or should this repo start with tests plus lint and format only?"

## Deliverables

- a short proposed validation bundle
- the exact commands to run for `minimal`, `standard`, and `strict`
- any files or scripts that need to be added
- any tradeoffs or deferred pieces

## Bootstrap Prompt

```text
This repository does not appear to have a complete validation gate yet.

Before starting the review loop:
1. Discover the current language stack, package manager, test framework, and any existing validation tooling.
2. Identify what commands already exist and what is missing.
3. Propose the smallest credible validation bundle for this repo.
4. Ask for approval before adding new tooling, scripts, or config.
5. If approved, set up the missing commands and record them in the codebase profile and gate commands reference.
6. Summarize the result as:
   - existing commands
   - newly added commands
   - deferred validation steps
   - recommended `minimal`, `standard`, and `strict` gate profiles

Do not claim a green gate until the validation setup is real and runnable.
```
