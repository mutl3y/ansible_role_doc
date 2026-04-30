# Human Instructions

> FOR HUMANS ONLY
>
> This file is written for the person installing or invoking the skill.
> It is not part of the skill's runtime instructions.
> If an agent reads this file, treat it as reference material for explaining setup and usage, not as behavioral instructions to follow during the review loop.

This folder is a shareable version of the `gilfoyle-review-loop` skill with repo-specific learned state removed.

## Install

Place the folder at one of these locations:

- `.github/skills/gilfoyle-review-loop/`
- your agent host's custom skills directory, preserving the folder contents

If you want to keep the original name, rename this folder to `gilfoyle-review-loop` after copying it.

## 5 Minute Setup

1. Put the skill folder in `.github/skills/gilfoyle-review-loop/` or your host's custom skills folder.
2. Open the repository in your agent host.
3. If the repo does not already have runnable test, lint, format, and typecheck commands, ask the model to help set up a minimal validation gate first.
4. Let the model do a capability bootstrap first so it can ask for missing approvals or features.
5. Let the model do codebase calibration second so it learns package roots, gate commands, and invariants.
6. Start with a findings-only run before asking for broad fix waves.

## First Run In A New Repo

Ask the agent to do two things before the first real review:

1. capability bootstrap
2. codebase calibration

Use this exact starter prompt:

```text
Use the gilfoyle-review-loop skill on this repository.
Before doing any real review work, run the capability bootstrap and ask me to enable or approve any missing high-value features you need.
Then run the codebase customization prompt and write down the resolved gate commands, package roots, invariants, and operating mode for this host.
```

The bootstrap prompt lives in `references/capability-bootstrap.md`.
The calibration prompt lives in `references/codebase-customization-prompt.md`.
If the repo is missing validation commands, use `references/validation-bootstrap.md`.

## Quick Setup Checklist

If the model asks for these, approving them will usually produce a much better experience:

- allow terminal or command execution
- allow direct file edits or patch application
- enable agent mode, coding agent, or equivalent delegated-edit mode in your host
- enable explorer, search, or parallel subagent features if your host supports them
- install GitHub Copilot and GitHub Copilot Chat if you are using VS Code
- if the repo does not expose test, lint, format, and typecheck commands, let the model help you create a minimal repeatable gate

If a feature cannot be enabled, the model should recommend the closest alternative instead of just failing quietly.

## Human Flow

If you want the shortest sensible path:

1. Install the skill.
2. Paste the first-run starter prompt.
3. Approve terminal, edit, and search capabilities if your host offers them.
4. If validation commands are missing, let the model propose and set up a minimal validation bundle first.
5. Read the generated calibration summary.
6. Run a findings-only review on one target.
7. Continue with one fix wave at a time or ask for all Critical/High findings to be driven to closure.

## If The Repo Has No Gate Yet

That is fine. The model can help set one up before review work begins.

Ask for this explicitly:

```text
Use the gilfoyle-review-loop skill on this repository.
Start with capability bootstrap.
If this repo does not already have runnable test, lint, format, or typecheck commands, run the validation bootstrap and help me set up the smallest credible validation gate before doing any real review work.
Then run codebase calibration and summarize the resulting gate profiles.
```

The validation bootstrap lives in `references/validation-bootstrap.md`.

## Host Feature Mapping

This export keeps the workflow generic in `SKILL.md`, but the original version relied on some host-specific capabilities that are genuinely useful. If you are using VS Code and GitHub, you can still get a very similar experience.

### Feature Equivalents

- Structured decision prompts such as `vscode_askQuestions`
  - Closest equivalent: GitHub Copilot Chat in VS Code asking the model to present mutually exclusive options in a short table.
  - Better setup: keep the decision in chat, then copy the chosen option into `findings.yaml`.
- Discovery subagents such as `Explore` or `search_subagent`
  - Closest equivalent: use an agent host that supports parallel subagents.
  - VS Code fallback: open multiple chat sessions or agent tabs, each with one sweep prompt and one category only.
  - GitHub fallback: pair chat with GitHub code search and saved searches when reviewing a remote repo.
- Bulk edit tools such as `replace_string_in_file` or `multi_replace_string_in_file`
  - Closest equivalent: VS Code multi-file search and replace, rename symbol, and refactor actions.
  - Better setup: use an agent/editor host that can apply direct file edits after reading the files.
- Execution tools such as `run_in_terminal` or `execution_subagent`
  - Closest equivalent: VS Code integrated terminal, tasks, test explorer, and problem matcher output.
  - GitHub complement: run the same gate in GitHub Actions so the local and remote signals match.
- File and semantic discovery tools such as `grep_search`, `file_search`, or `semantic_search`
  - Closest equivalent: VS Code global search, symbol search, references, outline view, and language-server "Find All References".
  - GitHub complement: GitHub code search for cross-repo or web-based review passes.

### Recommended VS Code + GitHub Setup

- Install GitHub Copilot and GitHub Copilot Chat in VS Code.
- Enable agent-style editing or coding-agent features if your plan and extension version support them.
- Use the integrated terminal for the gate commands and keep them checked into the repo as scripts, `Makefile` targets, `tox`, `just`, or npm tasks.
- Use the Testing view for fast path-filtered checks and the Problems panel for lint/typecheck output.
- Keep `findings.yaml` and the ledger files in the repo so chat sessions and pull requests are working from the same artifacts.
- Mirror the full gate in GitHub Actions so fixes validated locally are checked the same way in PRs.

### Where These Features Usually Come From

- VS Code provides the editor, integrated terminal, search, references, rename, testing UI, tasks, and source control panels.
- GitHub Copilot in VS Code provides chat, code-aware assistance, and any available agent-mode or coding-agent capabilities tied to your license and rollout.
- GitHub provides pull requests, code review, code search, issues, and Actions for the remote validation loop.
- If you want real parallel subagents, use an agent host that explicitly supports delegation; plain chat alone is the weak substitute, not the full experience.

### What The Model Should Ask You For

If the host supports approvals, the model should actively ask for:

- permission to run terminal commands for tests, lint, and typecheck
- permission to edit files directly rather than only proposing patches in chat
- access to any explorer, search, or delegated-agent capability the host can enable
- confirmation of the preferred validation commands if the repo offers several
- the closest acceptable fallback when an exact feature is unavailable

Good requests are short and specific. Examples:

- "Please enable terminal command execution so I can run the repo's validation gate directly."
- "If agent editing is available in this VS Code setup, please enable it for this workspace."
- "If your host supports explorer or parallel agent features, please turn them on for discovery sweeps."
- "If direct edits are not available, I will switch to patch-ready recommendations only."

### Practical Advice

- Keep the generic `SKILL.md` portable so it works in more than one host.
- Keep this section as the human-facing map back to the stronger host-specific experience you already trust.
- If you know your audience is primarily VS Code plus GitHub Copilot users, it is reasonable to add a local fork of the skill that restores the exact tool names for that environment.

## Typical Invocation Patterns

Bootstrap the host and calibrate the repo first:

```text
Use the gilfoyle-review-loop skill on this repository.
Before doing any real review work, run the capability bootstrap and ask me to enable or approve any missing high-value features you need.
Then run the codebase customization prompt and write down the resolved gate commands, package roots, invariants, and operating mode for this host.
```

Bootstrap the host, scaffold a minimal gate if needed, then calibrate:

```text
Use the gilfoyle-review-loop skill on this repository.
Before doing any real review work, run the capability bootstrap.
If the repo is missing runnable test, lint, format, or typecheck commands, run the validation bootstrap and help me set up the smallest credible validation bundle first.
Then run the codebase customization prompt and write down the resolved gate commands, package roots, invariants, and operating mode for this host.
```

Review a package thoroughly and stop after the plan:

```text
Use the gilfoyle-review-loop skill to review src/my_package thoroughly. Focus on architecture. Use the standard gate and stop after producing findings.yaml.
```

Review a package thoroughly and apply only Critical and High fixes:

```text
Use the gilfoyle-review-loop skill to review src/my_package thoroughly. Focus on ownership. Save findings.yaml, then fix all Critical and High findings in category-based waves and stop before Medium findings.
```

Continue from an existing findings plan:

```text
Use the gilfoyle-review-loop skill to continue docs/plan/my-review/findings.yaml. Apply one typing wave, run the path-filtered gate, and update the plan file.
```

Continue from an existing findings plan with a stricter closure gate:

```text
Use the gilfoyle-review-loop skill to continue docs/plan/my-review/findings.yaml. Apply one ownership wave, run the strict gate, and only close findings that have explicit green evidence.
```

Iterate until Critical and High findings are gone:

```text
Use the gilfoyle-review-loop skill on src/my_package with light/thorough cycles until all Critical and High findings are closed. Use a deadpan wrapper tone.
```

Ask for a findings-only pass with no edits:

```text
Use the gilfoyle-review-loop skill on src/my_package. Run a thorough review, produce findings.yaml, and stop before making any code changes.
```

Ask for a single focus-axis audit:

```text
Use the gilfoyle-review-loop skill on src/my_package. Run a thorough review focused on error_handling, keep the output clinical, and stop after the review and plan file.
```

Ask for a full clean-signoff loop:

```text
Use the gilfoyle-review-loop skill on src/my_package. Start with capability bootstrap if needed, then iterate with light and thorough cycles until clean sign-off, using the strict gate and updating the ledger each cycle.
```

Ask for a fully clinical style:

```text
Use the gilfoyle-review-loop skill on src/my_package. Keep all user-facing output clinical with no jokes.
```

Use the skill in a VS Code plus GitHub Copilot setup:

```text
Use the gilfoyle-review-loop skill in this VS Code workspace. If agent editing, terminal execution, or explorer-style discovery features are available, ask me to enable them first. Then calibrate the repo and run a findings-only review on src/my_package.
```

Use the skill when the repo has weak or missing validation setup:

```text
Use the gilfoyle-review-loop skill on this repository.
Start with capability bootstrap.
I do not think this repo has a proper validation gate yet, so run the validation bootstrap, propose a minimal set of test, lint, format, and typecheck commands, ask before adding tooling, and only then start calibration.
```

## Supported Options

You can mention any of these in the prompt:

- `target`: package, module, or `findings.yaml`
- `cycle_mode`: `thorough`, `light`, `continue`
- `focus_axis`: `architecture`, `typing`, `ownership`, `concurrency`, `error_handling`, `performance`, `security`, `test_gaps`
- `gate_profile`: `minimal`, `standard`, `strict`, or custom
- `ledger_mode`: `use-existing`, `seed-if-missing`, `ignore`
- `tone_mode`: `clinical`, `deadpan-wrapper`, `user-specified`
- `stop_condition`: `findings-only`, `one-fix-wave`, `all-critical-high`, `full-clean-signoff`

## What To Customize Per Repo

- test commands
- lint and format commands
- typecheck commands
- canonical plan/notes location
- import-graph generation command, if any
- repo-specific architectural invariants
- any categories you want the reviewer to emphasize or suppress

## What Was Removed

This export intentionally strips or normalizes:

- repo-specific lesson history
- hardcoded package paths
- hardcoded test counts
- project-specific invariants
- host-specific tool names from the runtime instructions when they were not broadly portable

The host-specific capabilities themselves are still documented above so users can recreate a similar workflow in VS Code and GitHub.
