# Codebase Customization Prompt

Use this prompt before the first real review cycle in a new repository.

```text
You are calibrating the gilfoyle-review-loop skill to this repository before using it for real review work.

Goals:
1. Discover the canonical package roots and test roots.
2. Identify the project's preferred validation gate: tests, lint, format check, and typecheck.
3. Identify the planning/notes location the repo already uses. If none exists, propose `docs/plan/.gilfoyle-lessons/`.
4. Identify architectural invariants this reviewer should always check in thorough cycles.
5. Identify obvious false positives this reviewer should avoid re-raising.
6. Identify whether explorer/search subagents are available and how discovery should be delegated in this host.

Deliverables:
- A short codebase profile with:
  - package roots
  - test commands
  - lint/format/typecheck commands
  - planning path
  - import/dependency analysis approach
  - invariants to always verify
  - likely false positives to suppress
  - recommended default focus-axis rotation order
- A proposed gate profile named `minimal`, `standard`, and `strict` for this repo.
- Any changes needed to `references/gate-commands.md` for this repo.

Constraints:
- Do not start the actual review yet.
- Keep the profile concise and operational.
- Prefer existing repo conventions over introducing new structure.
- If the repo lacks a formal command for a gate step, say so explicitly instead of inventing one.
- If validation commands are materially missing, stop and route to `references/validation-bootstrap.md` before starting the review loop.
```
