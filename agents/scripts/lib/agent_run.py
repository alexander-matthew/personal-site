"""Subprocess wrappers around `claude` and `codex` CLIs in headless mode.

Both CLIs auth via the user's subscription. The wrappers normalize:
- binary location (works under systemd where PATH may be minimal)
- working directory
- timeout (hard SIGKILL)
- tool / sandbox restrictions
- structured stdout capture (final agent message goes to a file)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class AgentRunError(RuntimeError):
    pass


_CLAUDE_CANDIDATES = (
    "/home/alex-matthew/.local/bin/claude",
    "/home/alex-matthew/.npm-global/bin/claude",
)
_CODEX_CANDIDATES = (
    "/home/alex-matthew/.npm-global/bin/codex",
    "/home/alex-matthew/.local/bin/codex",
)


def _resolve(name: str, candidates: tuple[str, ...]) -> str:
    p = shutil.which(name)
    if p:
        return p
    for c in candidates:
        if Path(c).is_file() and os.access(c, os.X_OK):
            return c
    raise AgentRunError(f"{name!r} not found on PATH or in known locations")


def _base_env() -> dict[str, str]:
    """systemd may strip PATH; ensure both CLI bin dirs are present."""
    env = os.environ.copy()
    extra = ["/home/alex-matthew/.local/bin", "/home/alex-matthew/.npm-global/bin"]
    env["PATH"] = ":".join([*extra, env.get("PATH", "/usr/bin:/bin")])
    env.setdefault("HOME", "/home/alex-matthew")
    return env


def run_claude(
    *,
    prompt: str,
    cwd: Path,
    timeout_min: int,
    permission_mode: str = "bypassPermissions",
    allowed_tools: Optional[list[str]] = None,
    disallowed_tools: Optional[list[str]] = None,
    max_turns: int = 80,
    extra_env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """Invoke `claude -p` headlessly.

    Defaults to `bypassPermissions` because the worktree is the blast radius:
    `--add-dir` is NOT passed, so filesystem writes outside `cwd` are blocked
    by Claude Code's permission layer even with bypass. The protected-paths
    post-check provides defense-in-depth before any PR is opened.
    """
    bin_ = _resolve("claude", _CLAUDE_CANDIDATES)
    args: list[str] = [
        bin_, "-p", prompt,
        "--permission-mode", permission_mode,
        "--max-turns", str(max_turns),
    ]
    if allowed_tools is not None:
        args += ["--allowed-tools", ",".join(allowed_tools)]
    if disallowed_tools is not None:
        args += ["--disallowed-tools", ",".join(disallowed_tools)]

    env = _base_env()
    if extra_env:
        env.update(extra_env)

    return subprocess.run(
        args, cwd=cwd, env=env,
        capture_output=True, text=True,
        timeout=timeout_min * 60,
    )


def run_codex(
    *,
    prompt: str,
    cwd: Path,
    timeout_min: int,
    sandbox: str = "read-only",
    model: Optional[str] = None,
    extra_env: Optional[dict[str, str]] = None,
) -> tuple[subprocess.CompletedProcess, str]:
    """Invoke `codex exec` headlessly.

    `sandbox` ∈ {'read-only','workspace-write','danger-full-access'}.
    The reviewer always uses 'read-only'.

    Returns (CompletedProcess, last_message). `last_message` is the agent's
    final reply text, captured via `--output-last-message` to avoid stdout
    parsing fragility.
    """
    bin_ = _resolve("codex", _CODEX_CANDIDATES)
    with tempfile.NamedTemporaryFile(
        "r+", prefix="codex-final-", suffix=".txt", delete=False
    ) as last_msg_file:
        last_msg_path = Path(last_msg_file.name)

    args: list[str] = [
        bin_, "exec",
        "-C", str(cwd),
        "--sandbox", sandbox,
        "--skip-git-repo-check",
        "--ephemeral",
        "--color", "never",
        "--output-last-message", str(last_msg_path),
    ]
    if model:
        args += ["-m", model]
    args.append(prompt)

    env = _base_env()
    if extra_env:
        env.update(extra_env)

    try:
        proc = subprocess.run(
            args, cwd=cwd, env=env,
            capture_output=True, text=True,
            timeout=timeout_min * 60,
        )
        last_msg = last_msg_path.read_text(errors="replace") if last_msg_path.exists() else ""
        return proc, last_msg
    finally:
        if last_msg_path.exists():
            last_msg_path.unlink(missing_ok=True)
