"""Guide section/body rendering helpers extracted from scanner."""

from __future__ import annotations

from .style import (
    _render_role_notes_section,
    _render_role_variables_for_style,
    _render_template_overrides_section,
    _render_variable_summary_section,
)
from .doc_insights import parse_comma_values
from ..scanner_extract.requirements import normalize_requirements
from ..scanner_config.patterns import load_pattern_config

_POLICY = load_pattern_config()
_VARIABLE_GUIDANCE_KEYWORDS: tuple[str, ...] = tuple(
    _POLICY["variable_guidance"]["priority_keywords"]
)


def _render_guide_identity_sections(
    section_id: str,
    role_name: str,
    description: str,
    requirements: list,
    galaxy: dict,
    metadata: dict,
) -> str | None:
    """Render style-guide sections focused on role identity and metadata."""
    if section_id == "galaxy_info":
        return _render_identity_galaxy_info_section(role_name, description, galaxy)
    if section_id == "requirements":
        return _render_identity_requirements_section(requirements)
    if section_id == "installation":
        return _render_identity_installation_section(role_name, galaxy)
    if section_id == "license":
        return _render_identity_license_section(galaxy)
    if section_id == "author_information":
        return _render_identity_author_section(galaxy)
    if section_id == "license_author":
        return _render_identity_license_author_section(galaxy)
    if section_id == "sponsors":
        return "No sponsorship metadata detected for this role."
    if section_id == "purpose":
        return _render_identity_purpose_section(metadata)
    if section_id == "role_notes":
        return _render_role_notes_section(metadata.get("role_notes"))
    return None


def _plan_galaxy_info(role_name: str, description: str, galaxy: dict) -> dict | None:
    """Plan galaxy info data model for rendering."""
    if not galaxy:
        return None
    return {
        "role_name": galaxy.get("role_name", role_name),
        "description": galaxy.get("description", description),
        "license": galaxy.get("license", "N/A"),
        "min_ansible_version": galaxy.get("min_ansible_version", "N/A"),
        "tags": galaxy.get("galaxy_tags"),
    }


def _render_galaxy_info(plan: dict) -> str:
    """Render galaxy info section from planned data."""
    lines = [
        f"- **Role name**: {plan['role_name']}",
        f"- **Description**: {plan['description']}",
        f"- **License**: {plan['license']}",
        f"- **Min Ansible Version**: {plan['min_ansible_version']}",
    ]
    if plan["tags"]:
        lines.append(f"- **Tags**: {', '.join(plan['tags'])}")
    return "\n".join(lines)


def _render_identity_galaxy_info_section(
    role_name: str,
    description: str,
    galaxy: dict,
) -> str:
    """Render Galaxy metadata section details."""
    plan = _plan_galaxy_info(role_name, description, galaxy)
    if plan is None:
        return "No Galaxy metadata found."
    return _render_galaxy_info(plan)


def _plan_requirements(requirements: list) -> list[str] | None:
    """Plan requirements data model for rendering."""
    requirement_lines = normalize_requirements(requirements)
    if not requirement_lines:
        return None
    return requirement_lines


def _render_requirements(plan: list[str]) -> str:
    """Render requirements section from planned data."""
    return "\n".join(f"- {line}" for line in plan)


def _render_identity_requirements_section(requirements: list) -> str:
    """Render normalized requirements bullet list."""
    plan = _plan_requirements(requirements)
    if plan is None:
        return "No additional requirements."
    return _render_requirements(plan)


def _plan_installation(role_name: str, galaxy: dict) -> dict:
    """Plan installation data model for rendering."""
    install_name = str(galaxy.get("role_name") or role_name)
    return {"install_name": install_name}


def _render_installation(plan: dict) -> str:
    """Render installation section from planned data."""
    return (
        "Install the role with Ansible Galaxy:\n\n"
        "```bash\n"
        f"ansible-galaxy install {plan['install_name']}\n"
        "```\n\n"
        "Or pin it in `requirements.yml`:\n\n"
        "```yaml\n"
        f"- src: {plan['install_name']}\n"
        "```"
    )


def _render_identity_installation_section(role_name: str, galaxy: dict) -> str:
    """Render installation guidance using Ansible Galaxy and requirements.yml."""
    plan = _plan_installation(role_name, galaxy)
    return _render_installation(plan)


def _plan_license(galaxy: dict) -> str | None:
    """Plan license data for rendering."""
    if galaxy and galaxy.get("license"):
        return str(galaxy.get("license"))
    return None


def _render_license(plan: str) -> str:
    """Render license section from planned data."""
    return plan


def _render_identity_license_section(galaxy: dict) -> str:
    """Render license value from Galaxy metadata when present."""
    plan = _plan_license(galaxy)
    return plan if plan else "N/A"


def _plan_author(galaxy: dict) -> str | None:
    """Plan author data for rendering."""
    if galaxy and galaxy.get("author"):
        return str(galaxy.get("author"))
    return None


def _render_author(plan: str) -> str:
    """Render author section from planned data."""
    return plan


def _render_identity_author_section(galaxy: dict) -> str:
    """Render author value from Galaxy metadata when present."""
    plan = _plan_author(galaxy)
    return plan if plan else "N/A"


def _plan_license_author(galaxy: dict) -> dict:
    """Plan license and author data for rendering."""
    license_value = str(galaxy.get("license", "N/A")) if galaxy else "N/A"
    author_value = str(galaxy.get("author", "N/A")) if galaxy else "N/A"
    return {"license": license_value, "author": author_value}


def _render_license_author(plan: dict) -> str:
    """Render combined license/author section from planned data."""
    return f"License: {plan['license']}\n\nAuthor: {plan['author']}"


def _render_identity_license_author_section(galaxy: dict) -> str:
    """Render combined license/author identity section."""
    plan = _plan_license_author(galaxy)
    return _render_license_author(plan)


def _plan_purpose(metadata: dict) -> dict | None:
    """Plan purpose data model for rendering."""
    insights = metadata.get("doc_insights") or {}
    purpose_summary = insights.get("purpose_summary")
    capabilities = insights.get("capabilities", [])
    if not purpose_summary:
        return None
    return {"purpose_summary": purpose_summary, "capabilities": capabilities}


def _render_purpose(plan: dict) -> str:
    """Render purpose section from planned data."""
    lines = [plan["purpose_summary"]]
    if plan["capabilities"]:
        lines.extend(["", "Capabilities:"])
        lines.extend(f"- {capability}" for capability in plan["capabilities"])
    return "\n".join(lines)


def _render_identity_purpose_section(metadata: dict) -> str:
    """Render inferred purpose and capabilities from doc insights."""
    plan = _plan_purpose(metadata)
    if plan is None:
        return "No inferred role summary available."
    return _render_purpose(plan)


def _render_guide_variable_sections(
    section_id: str,
    variables: dict,
    metadata: dict,
    variable_guidance_keywords: tuple[str, ...] | None = None,
) -> str | None:
    """Render style-guide sections focused on variable inventory and guidance."""
    if section_id == "variable_summary":
        return _render_variable_summary_section(metadata)
    if section_id == "variable_guidance":
        return _render_variable_guidance_section(
            metadata,
            variable_guidance_keywords=variable_guidance_keywords,
        )
    if section_id == "template_overrides":
        return _render_template_overrides_section(metadata)
    if section_id == "role_variables":
        return _render_role_variables_for_style(variables, metadata)
    return None


def _plan_variable_guidance(
    metadata: dict, variable_guidance_keywords: tuple[str, ...]
) -> list[dict] | None:
    """Plan variable guidance data model for rendering."""
    rows = metadata.get("variable_insights") or []
    if not rows:
        return None
    priority = [
        row
        for row in rows
        if any(keyword in row["name"] for keyword in variable_guidance_keywords)
    ]
    if not priority:
        priority = rows[:5]
    return priority[:8]


def _render_variable_guidance(plan: list[dict]) -> str:
    """Render variable guidance section from planned data."""
    lines = ["Recommended variables to tune:"]
    for row in plan:
        lines.append(
            f"- `{row['name']}` (default: `{str(row['default']).replace('`', "'")}`)"
        )
    lines.append("")
    lines.append("Use these as initial overrides for environment-specific behavior.")
    return "\n".join(lines)


def _render_variable_guidance_section(
    metadata: dict,
    variable_guidance_keywords: tuple[str, ...] | None = None,
) -> str:
    """Render recommended variable override candidates."""
    keywords = variable_guidance_keywords or _VARIABLE_GUIDANCE_KEYWORDS
    plan = _plan_variable_guidance(metadata, keywords)
    if plan is None:
        return "No variable guidance available because no variable defaults were discovered."
    return _render_variable_guidance(plan)


def _render_guide_task_sections(
    section_id: str,
    default_filters: list,
    metadata: dict,
) -> str | None:
    """Render style-guide sections focused on task, handler, and test activity."""
    if section_id == "task_summary":
        return _render_task_summary_section(metadata)
    if section_id == "example_usage":
        return _render_example_usage_section(metadata)
    if section_id == "local_testing":
        return _render_local_testing_section(metadata)
    if section_id == "handlers":
        return _render_handlers_section(metadata)
    if section_id == "faq_pitfalls":
        return _render_faq_pitfalls_section(default_filters, metadata)
    return None


def _plan_task_summary(metadata: dict) -> dict | None:
    """Plan task summary data model for rendering."""
    summary = (metadata.get("doc_insights") or {}).get("task_summary", {})
    if not summary:
        return None
    yaml_parse_failures = metadata.get("yaml_parse_failures") or []
    unconstrained_dynamic_task_includes = (
        metadata.get("unconstrained_dynamic_task_includes") or []
    )
    unconstrained_dynamic_role_includes = (
        metadata.get("unconstrained_dynamic_role_includes") or []
    )
    unconstrained_dynamic_includes = [
        *unconstrained_dynamic_task_includes,
        *unconstrained_dynamic_role_includes,
    ]
    task_catalog = metadata.get("task_catalog") or []
    detailed_catalog = metadata.get("detailed_catalog", False)
    return {
        "summary": summary,
        "yaml_parse_failures": yaml_parse_failures,
        "unconstrained_dynamic_task_includes": unconstrained_dynamic_task_includes,
        "unconstrained_dynamic_role_includes": unconstrained_dynamic_role_includes,
        "unconstrained_dynamic_includes": unconstrained_dynamic_includes,
        "task_catalog": task_catalog,
        "detailed_catalog": detailed_catalog,
    }


def _render_task_summary(plan: dict) -> str:
    """Render task summary section from planned data."""
    summary = plan["summary"]
    yaml_parse_failures = plan["yaml_parse_failures"]
    unconstrained_dynamic_task_includes = plan["unconstrained_dynamic_task_includes"]
    unconstrained_dynamic_role_includes = plan["unconstrained_dynamic_role_includes"]
    unconstrained_dynamic_includes = plan["unconstrained_dynamic_includes"]
    task_catalog = plan["task_catalog"]
    detailed_catalog = plan["detailed_catalog"]
    lines = [
        f"- **Task files scanned**: {summary.get('task_files_scanned', 0)}",
        f"- **Tasks scanned**: {summary.get('tasks_scanned', 0)}",
        f"- **Recursive includes**: {summary.get('recursive_task_includes', 0)}",
        f"- **Unique modules**: {summary.get('module_count', 0)}",
        f"- **Handlers referenced**: {summary.get('handler_count', 0)}",
        f"- **YAML parse failures**: {len(yaml_parse_failures)}",
        f"- **Unconstrained dynamic task includes**: {len(unconstrained_dynamic_task_includes)}",
        f"- **Unconstrained dynamic role includes**: {len(unconstrained_dynamic_role_includes)}",
    ]
    if yaml_parse_failures:
        lines.extend(["", "Parse failures detected:"])
        for item in yaml_parse_failures[:5]:
            file_name = str(item.get("file") or "<unknown>")
            line = item.get("line")
            column = item.get("column")
            location = (
                f"{file_name}:{line}:{column}"
                if line is not None and column is not None
                else file_name
            )
            error_text = str(item.get("error") or "parse error")
            lines.append(f"- `{location}`: {error_text}")
        if len(yaml_parse_failures) > 5:
            lines.append(
                f"- ... and {len(yaml_parse_failures) - 5} additional parse failures"
            )

    if unconstrained_dynamic_includes:
        lines.extend(["", "Unconstrained dynamic include hazards detected:"])
        for item in unconstrained_dynamic_includes[:5]:
            if not isinstance(item, dict):
                continue
            file_name = str(item.get("file") or "<unknown>")
            task_name = str(item.get("task") or "(unnamed task)")
            target = str(item.get("target") or "")
            lines.append(f"- `{file_name}` / {task_name}: `{target}`")
        if len(unconstrained_dynamic_includes) > 5:
            lines.append(
                "- ... and "
                f"{len(unconstrained_dynamic_includes) - 5} additional unconstrained dynamic includes"
            )

    if detailed_catalog and task_catalog:
        lines.extend(
            [
                "",
                "Detailed task catalog:",
                "",
                "| File | Task | Module | Parameters |",
                "| --- | --- | --- | --- |",
            ]
        )
        for entry in task_catalog:
            if not isinstance(entry, dict):
                continue
            lines.append(
                f"| `{entry.get('file', '')}` | {entry.get('name', '')} | `{entry.get('module', '')}` | {entry.get('parameters', '')} |"
            )

    return "\n".join(lines)


def _render_task_summary_section(metadata: dict) -> str:
    """Render task-summary section details including optional parse failures/catalog."""
    plan = _plan_task_summary(metadata)
    if plan is None:
        return "No task summary available."
    return _render_task_summary(plan)


def _plan_example_usage(metadata: dict) -> str | None:
    """Plan example usage data for rendering."""
    example = (metadata.get("doc_insights") or {}).get("example_playbook")
    return example


def _render_example_usage(plan: str) -> str:
    """Render example usage section from planned data."""
    return f"```yaml\n{plan}\n```"


def _render_example_usage_section(metadata: dict) -> str:
    """Render inferred example playbook block for style guide output."""
    plan = _plan_example_usage(metadata)
    if not plan:
        return "No inferred example available."
    return _render_example_usage(plan)


def _plan_local_testing(metadata: dict) -> dict:
    """Plan local testing data model for rendering."""
    role_tests = metadata.get("tests") or []
    molecule_scenarios = metadata.get("molecule_scenarios") or []
    scenario_lines = []
    if molecule_scenarios:
        scenario_lines.extend(["", "Molecule scenarios detected:"])
        for scenario in molecule_scenarios:
            if not isinstance(scenario, dict):
                continue
            name = str(scenario.get("name") or "default")
            driver = str(scenario.get("driver") or "unknown")
            verifier = str(scenario.get("verifier") or "unknown")
            platforms = scenario.get("platforms") or []
            platform_summary = ", ".join(
                str(item) for item in platforms if isinstance(item, str)
            )
            if not platform_summary:
                platform_summary = "unspecified"
            scenario_lines.append(
                f"- `{name}` (driver: `{driver}`, verifier: `{verifier}`, platforms: {platform_summary})"
            )
    return {
        "role_tests": role_tests,
        "scenario_lines": scenario_lines,
    }


def _render_local_testing(plan: dict) -> str:
    """Render local testing section from planned data."""
    role_tests = plan["role_tests"]
    scenario_lines = plan["scenario_lines"]

    if role_tests:
        inventory = next(
            (item for item in role_tests if "inventory" in item), role_tests[0]
        )
        playbook = next(
            (
                item
                for item in role_tests
                if item.endswith(".yml") or item.endswith(".yaml")
            ),
            role_tests[0],
        )
        guidance = (
            "Run a quick local validation using bundled role tests:\n\n"
            "```bash\n"
            f"ansible-playbook -i {inventory} {playbook}\n"
            "```"
        )
        if scenario_lines:
            guidance += "\n" + "\n".join(scenario_lines)
        return guidance

    fallback = "Run `tox` or `pytest -q` locally to validate scanner behavior and generated output."
    if scenario_lines:
        fallback += "\n" + "\n".join(scenario_lines)
    return fallback


def _render_local_testing_section(metadata: dict) -> str:
    """Render local testing guidance including role-test and molecule hints."""
    plan = _plan_local_testing(metadata)
    return _render_local_testing(plan)


def _plan_handlers(metadata: dict) -> dict | None:
    """Plan handlers data model for rendering."""
    features = metadata.get("features") or {}
    handler_names = parse_comma_values(str(features.get("handlers_notified", "none")))
    handler_files = metadata.get("handlers") or []
    summary = (metadata.get("doc_insights") or {}).get("task_summary", {})
    if not handler_names and not handler_files and not summary:
        return None
    handler_catalog = metadata.get("handler_catalog") or []
    detailed_catalog = metadata.get("detailed_catalog", False)
    return {
        "handler_names": handler_names,
        "handler_files": handler_files,
        "summary": summary,
        "handler_catalog": handler_catalog,
        "detailed_catalog": detailed_catalog,
    }


def _render_handlers(plan: dict) -> str:
    """Render handler summary section from planned data."""
    handler_names = plan["handler_names"]
    handler_files = plan["handler_files"]
    summary = plan["summary"]
    handler_catalog = plan["handler_catalog"]
    detailed_catalog = plan["detailed_catalog"]
    lines = [
        f"- **Handler files detected**: {len(handler_files)}",
        f"- **Handlers referenced by tasks**: {summary.get('handler_count', len(handler_names))}",
    ]
    if handler_names:
        lines.append("- **Named handlers**: " + ", ".join(handler_names))
    if handler_files:
        lines.append("")
        lines.append("Handler definition files:")
        lines.extend(f"- `{path}`" for path in handler_files)

    if detailed_catalog and handler_catalog:
        lines.extend(
            [
                "",
                "Detailed handler catalog:",
                "",
                "| File | Handler | Module | Parameters |",
                "| --- | --- | --- | --- |",
            ]
        )
        for entry in handler_catalog:
            if not isinstance(entry, dict):
                continue
            lines.append(
                f"| `{entry.get('file', '')}` | {entry.get('name', '')} | `{entry.get('module', '')}` | {entry.get('parameters', '')} |"
            )

    return "\n".join(lines)


def _render_handlers_section(metadata: dict) -> str:
    """Render handler summary and optional handler catalog for style output."""
    plan = _plan_handlers(metadata)
    if plan is None:
        return "No handler activity was detected."
    return _render_handlers(plan)


def _plan_faq_pitfalls(default_filters: list, metadata: dict) -> dict:
    """Plan FAQ pitfalls data model for rendering."""
    features = metadata.get("features") or {}
    return {
        "recursive_task_includes": int(features.get("recursive_task_includes", 0) or 0),
        "default_filters": default_filters,
    }


def _render_faq_pitfalls(plan: dict) -> str:
    """Render FAQ pitfalls section from planned data."""
    recursive_task_includes = plan["recursive_task_includes"]
    default_filters = plan["default_filters"]
    lines = [
        "- Ensure default values are defined in `defaults/main.yml` so they are discoverable.",
        "- Keep task includes file-based when possible for better recursive scanning.",
    ]
    if recursive_task_includes > 0:
        lines.append(
            "- Nested include chains are detected; avoid heavily dynamic include paths when possible."
        )
    if default_filters:
        lines.append(
            "- `default()` usages are captured from source files; keep expressions readable for better docs."
        )
    return "\n".join(lines)


def _render_faq_pitfalls_section(default_filters: list, metadata: dict) -> str:
    """Render common scanner-detected pitfalls for role docs."""
    plan = _plan_faq_pitfalls(default_filters, metadata)
    return _render_faq_pitfalls(plan)


def _render_guide_operations_sections(section_id: str, metadata: dict) -> str | None:
    """Render style-guide sections for operational guidance."""
    if section_id == "basic_authorization":
        return (
            "Use custom vhost or directory directives to add HTTP Basic Authentication where needed.\n\n"
            "- Provide credential files such as `.htpasswd` from your playbook or a companion role.\n"
            "- Prefer explicit configuration blocks or custom templates over editing generated files in place.\n"
            "- Keep authentication settings alongside the related virtual host configuration so the access policy remains reviewable."
        )

    if section_id == "contributing":
        return (
            "Contributions are welcome.\n\n"
            "- Run `pytest -q` before submitting changes.\n"
            "- Run `tox` for full local validation and review artifact generation.\n"
            "- Update docs/templates when scanner behavior changes."
        )

    return None


def _render_guide_section_body(
    section_id: str,
    role_name: str,
    description: str,
    variables: dict,
    requirements: list,
    default_filters: list,
    metadata: dict,
    *,
    variable_guidance_keywords: tuple[str, ...] | None = None,
) -> str:
    """Render one canonical section body for guided README output."""
    galaxy = (
        metadata.get("meta", {}).get("galaxy_info", {}) if metadata.get("meta") else {}
    )

    rendered = _render_guide_identity_sections(
        section_id,
        role_name,
        description,
        requirements,
        galaxy,
        metadata,
    )
    if rendered is not None:
        return rendered

    rendered = _render_guide_variable_sections(
        section_id,
        variables,
        metadata,
        variable_guidance_keywords=variable_guidance_keywords,
    )
    if rendered is not None:
        return rendered

    rendered = _render_guide_task_sections(section_id, default_filters, metadata)
    if rendered is not None:
        return rendered

    rendered = _render_guide_operations_sections(section_id, metadata)
    if rendered is not None:
        return rendered

    rendered = _render_guide_misc_sections(section_id, default_filters, metadata)
    if rendered is not None:
        return rendered

    return ""


def _render_guide_misc_sections(
    section_id: str,
    default_filters: list,
    metadata: dict,
) -> str | None:
    """Render remaining style-guide sections not covered by other groups."""
    renderers = {
        "role_contents": lambda: _render_role_contents_section(metadata),
        "features": lambda: _render_features_section(metadata),
        "comparison": lambda: _render_comparison_section(metadata),
        "default_filters": lambda: _render_default_filters_section(default_filters),
    }
    renderer = renderers.get(section_id)
    return renderer() if renderer else None


def _plan_role_contents(metadata: dict) -> dict:
    """Plan role contents data model for rendering."""
    contents = {}
    for key, items in metadata.items():
        if key in {
            "meta",
            "features",
            "comparison",
            "variable_insights",
            "doc_insights",
            "style_guide",
            "role_notes",
            "scanner_counters",
        }:
            continue
        if isinstance(items, list):
            contents[key] = len(items)
    return contents


def _render_role_contents(plan: dict) -> str:
    """Render role contents section from planned data."""
    lines = ["The scanner collected these role subdirectories (counts):", ""]
    for key, count in plan.items():
        lines.append(f"- **{key}**: {count} files")
    return "\n".join(lines)


def _render_role_contents_section(metadata: dict) -> str:
    """Render a compact count summary of discovered role subdirectories."""
    plan = _plan_role_contents(metadata)
    return _render_role_contents(plan)


def _plan_features(metadata: dict) -> dict | None:
    """Plan features data for rendering."""
    features = metadata.get("features") or {}
    if not features:
        return None
    return features


def _render_features(plan: dict) -> str:
    """Render features section from planned data."""
    return "\n".join(f"- **{key}**: {value}" for key, value in plan.items())


def _render_features_section(metadata: dict) -> str:
    """Render extracted role feature heuristics."""
    plan = _plan_features(metadata)
    if plan is None:
        return "No role features detected."
    return _render_features(plan)


def _plan_comparison(metadata: dict) -> dict | None:
    """Plan comparison data for rendering."""
    comparison = metadata.get("comparison")
    if not comparison:
        return None
    return comparison


def _render_comparison(plan: dict) -> str:
    """Render comparison section from planned data."""
    lines = [
        f"- **Baseline path**: {plan['baseline_path']}",
        f"- **Target score**: {plan['target_score']}/100",
        f"- **Baseline score**: {plan['baseline_score']}/100",
        f"- **Score delta**: {plan['score_delta']}",
        "",
    ]
    for metric, values in plan["metrics"].items():
        lines.append(
            f"- **{metric}**: target={values['target']}, baseline={values['baseline']}, delta={values['delta']}"
        )
    return "\n".join(lines)


def _render_comparison_section(metadata: dict) -> str:
    """Render baseline comparison metrics when available."""
    plan = _plan_comparison(metadata)
    if plan is None:
        return "No comparison baseline provided."
    return _render_comparison(plan)


def _plan_default_filters(default_filters: list) -> list[dict] | None:
    """Plan default filters data for rendering."""
    if not default_filters:
        return None
    return default_filters


def _render_default_filters(plan: list[dict]) -> str:
    """Render default filters section from planned data."""
    lines = [
        "The scanner found undocumented variables using `default()` in role files:",
        "",
    ]
    for occ in plan:
        match = occ["match"].replace("`", "'")
        args = occ["args"].replace("`", "'")
        lines.append(f"- {occ['file']}:{occ['line_no']} - `{match}`")
        lines.append(f"  args: `{args}`")
    return "\n".join(lines)


def _render_default_filters_section(default_filters: list) -> str:
    """Render undocumented default() findings in bullet-list form."""
    plan = _plan_default_filters(default_filters)
    if plan is None:
        return "No undocumented variables using `default()` were detected."
    return _render_default_filters(plan)
