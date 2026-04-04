"""
Migration utilities for config evolution.
"""

from typing import Any, Dict


def migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate old config keys to new ones.

    Example: old_key -> new_key
    """
    new_config = config.copy()
    if "old_key" in new_config:
        new_config["new_key"] = new_config.pop("old_key")
    return new_config


def rollback_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rollback new config keys to old ones for compatibility.

    Example: new_key -> old_key
    """
    old_config = config.copy()
    if "new_key" in old_config:
        old_config["old_key"] = old_config.pop("new_key")
    return old_config
