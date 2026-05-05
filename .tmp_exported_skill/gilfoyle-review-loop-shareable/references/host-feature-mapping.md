# Host Feature Mapping

This reference is for humans adapting the shareable skill to a concrete agent host.

## Original Host-Specific Concepts

- `vscode_askQuestions`: structured option selection inside a VS Code-centric host
- `Explore` and `search_subagent`: delegated discovery passes
- `replace_string_in_file` and `multi_replace_string_in_file`: direct file-edit tools
- `run_in_terminal` and `execution_subagent`: command execution for validation gates
- `grep_search`, `file_search`, `semantic_search`, `read_file`: host-provided code navigation tools

## Portable Interpretation

- Structured option selection -> present explicit options in chat and persist the chosen one
- Discovery subagents -> parallel explorer agents if available, separate chat sessions if not
- Direct file-edit tools -> editor refactors, rename, multi-file replace, or agent edit tools
- Command execution -> integrated terminal, tasks, CI, or agent-run command execution
- Code navigation -> editor search, references, outline, language server, and repo search

## VS Code + GitHub Approximation

- Use GitHub Copilot Chat in VS Code for the orchestrator conversation.
- Use multiple chat tabs or sessions to simulate discovery parallelism when true subagents are unavailable.
- Use VS Code search, "Find All References", rename symbol, and refactor actions for discovery and safe edits.
- Use the integrated terminal and Testing panel for path-filtered and full gates.
- Use GitHub Actions for the remote equivalent of the gate.
- Use pull requests plus review comments for the human decision step when the change is ambiguous.

## If You Want The Original Feel

Make a local, host-specific fork of the skill and reintroduce the exact tool names in `SKILL.md` for the environment you control. Keep the shareable export generic, and keep your local fork opinionated.
