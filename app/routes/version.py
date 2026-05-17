import os
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _read_sha() -> str:
    result = subprocess.run(
        ['git', 'rev-parse', '--short', 'HEAD'],
        capture_output=True,
        text=True,
        timeout=2,
        cwd=_REPO_ROOT,
        check=True,
    )
    return result.stdout.strip()


_SHA = _read_sha()
_BUILT_AT = datetime.now(timezone.utc).isoformat()


@router.get('/version', name='version.get')
async def get_version():
    return {'sha': _SHA, 'built_at': _BUILT_AT}
