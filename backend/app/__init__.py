import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    load_dotenv(_BACKEND_DIR / ".env")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    origins = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    ]
    CORS(app, origins=origins)

    from app.routes import api_bp
    app.register_blueprint(api_bp)

    return app
