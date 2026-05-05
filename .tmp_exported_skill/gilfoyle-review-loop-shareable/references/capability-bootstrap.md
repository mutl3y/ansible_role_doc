# Capability Bootstrap

Run this before the first real cycle in a new host or repository.

## Goal

Detect what the destination host can do, request access to the best available features, and only then fall back.

## Model Behavior Contract

At the start of a session, determine whether the host supports these capability groups:

- structured decisions
- code and symbol search
- parallel subagents or delegated discovery
- direct file editing
- terminal or command execution
- test, lint, and typecheck execution
- interactive approval or permission requests

If a capability is missing, do not silently degrade immediately.

Instead:

1. check whether the host can enable it through an extension, plugin, permission grant, or settings change
2. if yes, ask the human for that specific enablement in one concise step
3. if no, recommend the closest viable alternative
4. state the operating mode for this session: `full-host`, `partial-host`, or `fallback`

## Human-Facing Questions To Ask

Ask only short, concrete questions. Prefer one at a time.

Examples:

- "Can you enable terminal command execution for this session so I can run the validation gate directly?"
- "Does your host support parallel subagents or explorer agents? If yes, please enable them for discovery sweeps."
- "If direct file edits are available, please allow them; otherwise I will switch to patch-ready recommendations."
- "If GitHub Copilot agent mode or coding agent is available in VS Code, please enable it for this workspace."

## Preferred Capability Order

### Discovery

1. parallel explorer or search subagents
2. semantic or code search tools
3. editor references, symbol search, and repo search
4. manual file-by-file discovery

### Editing

1. direct agent file edits
2. patch application tools
3. editor rename/refactor plus multi-file replace
4. manual diff instructions

### Validation

1. direct terminal execution by the model
2. host task runner or test runner accessible to the model
3. human-run commands pasted back into the session

## Bootstrap Prompt

```text
Before using this skill normally, do a capability bootstrap for the current host.

1. Detect whether you have:
   - structured decision prompts
   - code search or semantic search
   - explorer/search subagents or parallel delegation
   - direct file edit capability
   - terminal/command execution
   - interactive permission or approval requests
2. If an important capability is missing, first see whether you can ask the user to enable it, approve it, or install the relevant extension/plugin.
3. If the exact capability is not possible, recommend the closest alternative and explain the tradeoff in one sentence.
4. Summarize the result as:
   - operating mode: full-host, partial-host, or fallback
   - enabled capabilities
   - missing capabilities
   - requested approvals or setup steps
   - recommended substitutions
5. Then proceed with the codebase customization prompt.
6. If codebase customization finds that validation commands are missing, route to the validation bootstrap before starting the review.

Do not start the review until the capability bootstrap is complete.
```
