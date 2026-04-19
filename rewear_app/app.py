import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from models import db
from routes import auth_bp, items_bp, outfits_bp, detection_bp, uploads_bp

logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Application Factory to create and configure the Flask app."""
    app = Flask(__name__)

    # ── Configuration ─────────────────────────────────────────────────────────────
    if test_config is None:
        # Load standard configuration when NOT running tests
        _secret_key = os.environ.get('SECRET_KEY')
        if not _secret_key:
            _secret_key = 'dev-secret-key-change-in-production'
            logger.warning(
                'SECRET_KEY env var not set — using insecure default. '
                'Set SECRET_KEY in your environment before deploying.'
            )
        app.config['SECRET_KEY'] = _secret_key
        
        # Ensure database is in the instance folder relative to this file
        _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'database.db')
        os.makedirs(os.path.dirname(_db_path), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_path}'
    else:
        # Load the testing configuration passed in from conftest.py
        app.config.update(test_config)

    # Standard configs that apply regardless of environment
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    _production = os.environ.get('PRODUCTION', '').lower() in ('1', 'true', 'yes')
    app.config['SESSION_COOKIE_SAMESITE'] = 'None' if _production else 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = _production
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ── Extensions ────────────────────────────────────────────────────────────────
    db.init_app(app)
    Migrate(app, db, render_as_batch=True)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:3001"])

    # db.create_all() is no longer needed as we are using Flask-Migrate.
    # Run 'flask db upgrade' from the terminal to apply schema changes.

    # ── Blueprints ────────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(outfits_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(uploads_bp)

    # ── Routes ────────────────────────────────────────────────────────────────────
    @app.route("/")
    def home():
        return "ReWear backend is running!"

    return app


if __name__ == "__main__":
    # Create an app instance and run the dev server if executing this file directly
    app = create_app()
    app.run(debug=True, port=5001)
