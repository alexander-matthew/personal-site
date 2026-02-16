"""
Tools Router - Framework for mini-apps.

Each tool self-registers with metadata for the index page.
"""
from fastapi import APIRouter, Request

from app.templating import templates

router = APIRouter(prefix='/tools')

# Tool registry - tools self-register here
TOOLS_REGISTRY = []


def register_tool(tool_config):
    """
    Register a tool with the framework.

    tool_config = {
        'id': 'spotify',                    # URL slug
        'name': 'Spotify Listening Trends', # Display name
        'description': 'Visualize your listening habits over time',
        'icon': 'music',                    # Icon identifier
        'tags': ['API', 'Charts'],          # For filtering
        'requires_auth': True,              # OAuth required
    }
    """
    TOOLS_REGISTRY.append(tool_config)


@router.get('/', name='tools.index')
async def index(request: Request):
    """Tools listing page."""
    return templates.TemplateResponse(request, 'tools/index.html', {'tools': TOOLS_REGISTRY})


# Import tool modules to trigger registration
from app.routes.tools import spotify as _spotify  # noqa: E402, F401
