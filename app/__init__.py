import os
from flask import Flask
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


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-local-only')

    # Inject site config into all templates
    @app.context_processor
    def inject_site_config():
        return {'site': SITE_CONFIG}

    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    # Register main routes
    from app.routes import main
    app.register_blueprint(main.bp)

    # Register blog routes
    from app.routes import blog
    app.register_blueprint(blog.bp)

    # Register news routes
    from app.routes import news
    app.register_blueprint(news.bp)

    # Register Spotify dashboard
    from app.routes import spotify
    app.register_blueprint(spotify.bp)

    # Register Blackjack trainer
    from app.routes import blackjack
    app.register_blueprint(blackjack.bp)

    # Register PR Review Tool showcase
    from app.routes import pr_review
    app.register_blueprint(pr_review.bp)

    # Register Sudoku game
    from app.routes import sudoku
    app.register_blueprint(sudoku.bp)

    return app
