"""Variable extraction and sensitivity helpers.

These functions are extracted from scanner.py to improve cohesion.
They depend only on _jinja_analyzer, _task_parser, pattern_config,
and stdlib.

Policy is now request-scoped via ContextVar, no longer using mutable globals.

Exported names consumed by scanner.py:
  Constants: DEFAULT_TARGET_RE, JINJA_VAR_RE, JINJA_IDENTIFIER_RE,
             VAULT_KEY_RE, IGNORED_IDENTIFIERS (now a function),
             _SECRET_NAME_TOKENS, _VAULT_MARKERS,
             _CREDENTIAL_PREFIXES, _URL_PREFIXES
  Functions: _extract_default_target_var, _collect_include_vars_files,
                         _collect_set_fact_names, _collect_register_names,
                         _find_variable_line_in_yaml,
             _collect_dynamic_include_vars_refs,
             _collect_dynamic_task_include_refs,
             _collect_referenced_variable_names,
             _looks_secret_name, _resembles_password_like,
             _is_sensitive_variable, _looks_secret_value,
             _infer_variable_type,
             _read_seed_yaml, _resolve_seed_var_files, load_seed_variables
"""
