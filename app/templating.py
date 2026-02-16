"""
Jinja2 template setup for FastAPI.

Provides a custom url_for() global that matches Flask's calling convention,
so zero template files need to change.
"""
import logging
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.routing import NoMatchFound
from app import SITE_CONFIG

logger = logging.getLogger(__name__)

templates: Jinja2Templates = None  # type: ignore


def setup_templates(app: FastAPI) -> None:
    global templates
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    templates = Jinja2Templates(directory=template_dir)

    def url_for(name: str, **kwargs) -> str:
        """
        Flask-compatible url_for for Jinja2 templates.

        Handles:
          url_for('static', filename='css/style.css') -> /static/css/style.css
          url_for('main.home') -> /
          url_for('blog.post', slug='foo') -> /blog/foo
        """
        if name == 'static':
            filename = kwargs.get('filename', '')
            return f'/static/{filename}'

        # Use FastAPI's route resolution
        try:
            return app.url_path_for(name, **kwargs)
        except NoMatchFound:
            logger.warning("url_for: no route found for %r with %r", name, kwargs)
            return '#'

    # Register as Jinja2 global (available in all templates)
    templates.env.globals['url_for'] = url_for
    templates.env.globals['site'] = SITE_CONFIG
