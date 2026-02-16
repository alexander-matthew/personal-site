import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

# Load .env file for local development (no-op if file doesn't exist)
load_dotenv()


# Global site variables - easy to update in one place
SITE_CONFIG = {
    'name': 'Alexander',
    'linkedin_url': 'https://www.linkedin.com/in/alex-matthew1/',
    'github_url': 'https://github.com/alexander-matthew',
    'email': 'your@email.com',  # Update this
}


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(docs_url=None, redoc_url=None)

    # Security headers middleware
    is_production = os.environ.get('FLASK_DEBUG', 'true').lower() == 'false'

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            if is_production:
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Session middleware (replaces Flask's signed cookie sessions)
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get('SECRET_KEY', 'dev-key-for-local-only'),
        same_site='lax',
        https_only=is_production,
        max_age=14 * 24 * 3600,  # 2 weeks
    )

    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.mount('/static', StaticFiles(directory=static_dir), name='static')

    # Set up Jinja2 templates with custom url_for
    from app.templating import setup_templates
    setup_templates(app)

    # Register routers
    from app.routes import main
    app.include_router(main.router)

    from app.routes import blog
    app.include_router(blog.router)

    from app.routes import news
    app.include_router(news.router)

    from app.routes import spotify
    app.include_router(spotify.router)

    from app.routes import blackjack
    app.include_router(blackjack.router)

    from app.routes import pr_review
    app.include_router(pr_review.router)

    from app.routes import sudoku
    app.include_router(sudoku.router)

    from app.routes import weather
    app.include_router(weather.router)

    from app.routes import resume
    app.include_router(resume.router)

    from app.routes.tools import router as tools_router
    app.include_router(tools_router)

    # Error handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc):
        from fastapi.responses import JSONResponse
        status = exc.status_code if hasattr(exc, 'status_code') else 500

        # API endpoints return JSON errors
        if '/api/' in request.url.path:
            detail = exc.detail if hasattr(exc, 'detail') else 'Error'
            return JSONResponse({'error': detail}, status_code=status)

        # Page requests get HTML error pages
        if status == 404:
            from app.templating import templates
            return templates.TemplateResponse(request, '404.html', status_code=404)
        if status == 500:
            from app.templating import templates
            return templates.TemplateResponse(request, '500.html', status_code=500)

        # Other HTTP errors for pages (401, 403, etc.)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(str(exc.detail), status_code=status)

    return app
