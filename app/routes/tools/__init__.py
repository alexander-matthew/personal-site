"""
Tools Blueprint - Framework for mini-apps.

Each tool self-registers with metadata for the index page.
"""
from flask import Blueprint, render_template

bp = Blueprint('tools', __name__, url_prefix='/tools')

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


@bp.route('/')
def index():
    """Tools listing page."""
    return render_template('tools/index.html', tools=TOOLS_REGISTRY)


# Import tool modules to trigger registration
from app.routes.tools import spotify  # noqa: E402, F401
