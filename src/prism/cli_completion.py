"""Completion command execution for prism CLI."""

from __future__ import annotations

import argparse
import sys

from .cli_commands import _build_bash_completion_script


def handle_completion_command(args: argparse.Namespace) -> int:
    """Execute the completion command."""
    if args.shell != "bash":
        print(
            f"Error: unsupported completion shell: {args.shell}",
            file=sys.stderr,
        )
        return 2
    print(_build_bash_completion_script(), end="")
    return 0
