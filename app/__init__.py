import os
import json
import logging

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    app = Flask(__name__)

    # ── Security configuration ────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["SESSION_COOKIE_NAME"] = "admissions_session"
    app.config["SESSION_COOKIE_PATH"] = os.environ.get("SESSION_COOKIE_PATH", "/")
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
        "SESSION_COOKIE_SECURE", "false"
    ).lower() in ("true", "1", "yes")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # ── Database path ─────────────────────────────────────────────────
    data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    app.config["DATA_DIR"] = os.path.abspath(data_dir)
    app.config["DATABASE"] = os.path.join(app.config["DATA_DIR"], "admissions.db")

    # ── Kindo agent config ────────────────────────────────────────────
    app.config["KINDO_API_KEY"] = os.environ.get("KINDO_API_KEY", "")
    app.config["KINDO_REVIEW_AGENT_ID"] = os.environ.get("KINDO_REVIEW_AGENT_ID", "")
    app.config["KINDO_API_URL"] = os.environ.get(
        "KINDO_API_URL", "https://api.kindo.ai/v1/chat/completions"
    )

    # ── Logging ───────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    )

    # ── Proxy fix ─────────────────────────────────────────────────────
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Database initialization ───────────────────────────────────────
    from app.models.database import init_db
    with app.app_context():
        init_db(app)

    # ── Register blueprints ───────────────────────────────────────────
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Theme context processor ───────────────────────────────────────
    @app.context_processor
    def inject_theme():
        from flask import session
        return {"theme": session.get("theme", "light")}

    return app
