import os
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


def _read_sha() -> str:
    # Prefer an explicit build-time env var so deployed images don't need a .git dir.
    env_sha = os.environ.get('GIT_SHA')
    if env_sha:
        return env_sha.strip()[:7]
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return 'unknown'


_SHA = _read_sha()
_BUILT_AT = datetime.now(timezone.utc).isoformat()


@router.get('/version', name='version.get')
async def get_version():
    return {'sha': _SHA, 'built_at': _BUILT_AT}
