"""Sensitivity detection for variables.

Functions to detect sensitive or secret variables based on names and values.
"""

from .variable_policy import _active_sensitivity_tokens


def _looks_secret_name(name: str) -> bool:
    """Return True when a variable name suggests secret/sensitive content."""
    secret_name_tokens, _vault_markers, _credential_prefixes, _url_prefixes = (
        _active_sensitivity_tokens()
    )
    lowered = name.lower()
    return any(token in lowered for token in secret_name_tokens)


def _resembles_password_like(value: object) -> bool:
    """Return True when a string value looks like a credential/token."""
    _secret_name_tokens, vault_markers, credential_prefixes, url_prefixes = (
        _active_sensitivity_tokens()
    )

    if not isinstance(value, str):
        return False

    raw = value.strip().strip("'\"")
    if not raw:
        return False
    lowered = raw.lower()

    if any(marker in lowered for marker in vault_markers):
        return True
    if raw.startswith(credential_prefixes):
        return True
    if raw.startswith(url_prefixes):
        return False
    if " " in raw or "{{" in raw or "}}" in raw:
        return False

    has_lower = any(char.islower() for char in raw)
    has_upper = any(char.isupper() for char in raw)
    has_digit = any(char.isdigit() for char in raw)
    has_symbol = any(not char.isalnum() for char in raw)
    class_count = sum((has_lower, has_upper, has_digit, has_symbol))

    if len(raw) >= 24 and class_count >= 2:
        return True
    if len(raw) >= 12 and class_count >= 3:
        return True
    return False


def _is_sensitive_variable(name: str, value: object) -> bool:
    """Return True when variable should be treated as sensitive for output."""
    if _looks_secret_value(value):
        return True
    if _looks_secret_name(name) and _resembles_password_like(value):
        return True
    return False


def _looks_secret_value(value: object) -> bool:
    """Return True when a value appears to be vaulted or sensitive."""
    if isinstance(value, str):
        _secret_name_tokens, vault_markers, _credential_prefixes, _url_prefixes = (
            _active_sensitivity_tokens()
        )
        lowered = value.lower()
        return any(marker in lowered for marker in vault_markers) or lowered.startswith(
            "vault_"
        )
    return False


# Public exports
looks_secret_name = _looks_secret_name
resembles_password_like = _resembles_password_like
