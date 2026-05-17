"""Agent personas — declarative config + prompt body per phase.

A persona is a named role (worker, reviewer, responder, proposer) backed by
a single markdown file at `agents/personas/<name>.md`. The file is parsed as:

    +++
    <TOML frontmatter — config>
    +++

    <markdown body — prompt template>

Phase scripts load a persona, render its template with run-specific variables,
and invoke `agent_run.run_persona(...)` which dispatches to the right CLI
(claude or codex) using the persona's declared settings.

The persona is the single source of truth for everything *about* a phase
agent: which CLI to use, sandboxing, timeouts, tool restrictions, expected
output format, and error-handling policy. Phase scripts handle phase-specific
post-processing (GitHub mutations, db logging) but not LLM execution config.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from string import Template

from .paths import AGENTS_DIR


PERSONAS_DIR = AGENTS_DIR / "personas"


# Allowed values for policy fields. The phase scripts switch on these strings;
# adding a new value here is opt-in and requires script updates.
ON_RATE_LIMIT = {"skip_until_reset", "fail"}
ON_PARSE_FAIL = {"comment_and_retry", "fail"}
ON_NO_OUTPUT = {"log_and_skip", "fail"}
OUTPUT_FORMAT = {"free", "structured-markers"}


@dataclass(frozen=True)
class Persona:
    name: str
    cli: str                                 # 'claude' | 'codex'
    role: str
    voice: str
    timeout_min: int

    # CLI-specific (mutually exclusive in practice but tracked separately
    # so the persona file doesn't need a per-CLI branch).
    sandbox: str | None = None               # codex: 'read-only' | 'workspace-write'
    permission_mode: str | None = None       # claude: 'bypassPermissions' | 'acceptEdits' | 'plan'
    max_turns: int | None = None             # claude
    allowed_tools: tuple[str, ...] | None = None
    disallowed_tools: tuple[str, ...] | None = None

    # Error-handling policy. Phase scripts consult these strings to decide
    # what to do when their persona's invocation goes sideways. The orchestrator
    # consults `on_rate_limit` to decide whether to gate future ticks.
    on_rate_limit: str = "skip_until_reset"
    on_parse_fail: str = "comment_and_retry"
    on_no_output: str = "log_and_skip"
    escalation_label: str = "agent:needs-human"

    # Output expectations.
    output_format: str = "free"
    required_markers: tuple[str, ...] = field(default_factory=tuple)

    # Prompt body. Use $VAR placeholders (Python string.Template) so that
    # accidental curly braces in the prompt don't blow up rendering.
    prompt_template: str = ""

    def render(self, **vars: str | int) -> str:
        """Substitute $VAR placeholders in the prompt body."""
        return Template(self.prompt_template).safe_substitute(vars)

    @classmethod
    def load(cls, name: str) -> "Persona":
        path = PERSONAS_DIR / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"no persona at {path}")
        return _load_from_path(path)


def _load_from_path(path: Path) -> Persona:
    text = path.read_text()
    fm, body = _split_frontmatter(text)
    data = tomllib.loads(fm) if fm else {}

    # Validate enums; raise loudly if a persona file declares a value we don't
    # handle — easier to catch at load time than after a 60s agent run.
    _check_enum("on_rate_limit", data.get("on_rate_limit"), ON_RATE_LIMIT)
    _check_enum("on_parse_fail", data.get("on_parse_fail"), ON_PARSE_FAIL)
    _check_enum("on_no_output", data.get("on_no_output"), ON_NO_OUTPUT)
    _check_enum("output_format", data.get("output_format"), OUTPUT_FORMAT)

    return Persona(
        name=data.get("name", path.stem),
        cli=data["cli"],
        role=data.get("role", ""),
        voice=data.get("voice", ""),
        timeout_min=int(data.get("timeout_min", 30)),
        sandbox=data.get("sandbox"),
        permission_mode=data.get("permission_mode"),
        max_turns=data.get("max_turns"),
        allowed_tools=_tuple_or_none(data.get("allowed_tools")),
        disallowed_tools=_tuple_or_none(data.get("disallowed_tools")),
        on_rate_limit=data.get("on_rate_limit", "skip_until_reset"),
        on_parse_fail=data.get("on_parse_fail", "comment_and_retry"),
        on_no_output=data.get("on_no_output", "log_and_skip"),
        escalation_label=data.get("escalation_label", "agent:needs-human"),
        output_format=data.get("output_format", "free"),
        required_markers=tuple(data.get("required_markers", ())),
        prompt_template=body,
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Returns (frontmatter, body). Empty frontmatter if the file has no +++ fence."""
    if not text.startswith("+++\n"):
        return "", text
    try:
        end = text.index("\n+++\n", 4)
    except ValueError:
        raise ValueError("persona frontmatter started with +++ but never closed")
    return text[4:end], text[end + 5:]


def _check_enum(field_name: str, value: str | None, allowed: set[str]) -> None:
    if value is not None and value not in allowed:
        raise ValueError(
            f"persona field {field_name}={value!r} not in {sorted(allowed)}"
        )


def _tuple_or_none(v) -> tuple[str, ...] | None:
    if v is None:
        return None
    return tuple(v)


__all__ = ["Persona", "PERSONAS_DIR", "replace"]
