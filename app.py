"""
SAIVEX Deployment Step 2 — Production Environment

This file keeps your current SAIVEX app working through legacy_app.py
and adds production-ready environment loading, security headers,
logging, and health/status endpoints.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from legacy_app import app

try:
    from utils.security import add_security_headers
except Exception:
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

try:
    from utils.logging_config import setup_logging
except Exception:
    def setup_logging(flask_app):
        return None


app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    os.getenv("SAIVEX_SECRET_KEY", "saivex-secret-key-change-later")
)

database_url = os.getenv(
    "DATABASE_URL",
    app.config.get("SQLALCHEMY_DATABASE_URI", "sqlite:///instance/saivex.db")
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("SAIVEX_MAX_UPLOAD_MB", "100")) * 1024 * 1024

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
app.config["REMEMBER_COOKIE_SECURE"] = os.getenv("REMEMBER_COOKIE_SECURE", "False") == "True"

setup_logging(app)


@app.after_request
def apply_production_security(response):
    return add_security_headers(response)


@app.route("/health")
def health():
    return {
        "status": "ok",
        "app": "SAIVEX",
        "deployment_step": "2"
    }


@app.route("/production/status")
def production_status():
    return {
        "app": "SAIVEX",
        "version": "v1.0-deployment-step-2",
        "status": "running",
        "database": app.config.get("SQLALCHEMY_DATABASE_URI", ""),
        "public_url": os.getenv("SAIVEX_PUBLIC_URL", "http://127.0.0.1:5000"),
        "features": [
            "dotenv_environment",
            "secure_headers",
            "logging",
            "gunicorn_ready",
            "sqlite_now_postgresql_later"
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("PRODUCTION", "0") != "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
