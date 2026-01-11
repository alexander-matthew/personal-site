import os
from flask import Flask
from flask_login import LoginManager
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

# Initialize Flask-Login
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-local-only')

    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///goals.db')
    # Heroku uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    from app.models import db, bcrypt
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'goals.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Create database tables
    with app.app_context():
        db.create_all()

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

    # Register Weather dashboard
    from app.routes import weather
    app.register_blueprint(weather.bp)

    # Register Goals tracker
    from app.routes import goals
    app.register_blueprint(goals.bp)

    return app
