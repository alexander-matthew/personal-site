import os
from flask import Flask


# Global site variables - easy to update in one place
SITE_CONFIG = {
    'name': 'Alexander',
    'linkedin_url': 'https://www.linkedin.com/in/alex-matthew1/',
    'github_url': 'https://github.com/alexander-matthew',
    'email': 'your@email.com',  # Update this
}


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-local-only')

    # Inject site config into all templates
    @app.context_processor
    def inject_site_config():
        return {'site': SITE_CONFIG}

    # Register main routes
    from app.routes import main
    app.register_blueprint(main.bp)

    # Register blog routes
    from app.routes import blog
    app.register_blueprint(blog.bp)

    # Register news routes
    from app.routes import news
    app.register_blueprint(news.bp)

    return app