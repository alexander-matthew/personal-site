import os
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _read_sha() -> str:
    """Resolve the build SHA.

    Production images set ``GIT_SHA`` at build time because the runtime
    container ships without ``git`` or ``.git/`` (see Dockerfile + .dockerignore).
    Local dev falls back to ``git rev-parse`` against the worktree, and finally
    to ``"unknown"`` so import-time never crashes the app.
    """
    env_sha = os.environ.get('GIT_SHA', '').strip()
    if env_sha:
        return env_sha
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=_REPO_ROOT,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return 'unknown'


def _read_built_at() -> str:
    env_built = os.environ.get('BUILT_AT', '').strip()
    if env_built:
        return env_built
    return datetime.now(timezone.utc).isoformat()


_SHA = _read_sha()
_BUILT_AT = _read_built_at()


@router.get('/version', name='version.get')
async def get_version():
    return {'sha': _SHA, 'built_at': _BUILT_AT}
