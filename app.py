"""
SAIVEX Production Entry Point

This file keeps your original SAIVEX features from legacy_app.py and adds
production-ready configuration for deployment platforms and Docker.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Your original Flask app lives in legacy_app.py
from legacy_app import app  # noqa: E402

try:
    from utils.security import add_security_headers
except Exception:
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
        return response

try:
    from utils.logging_config import setup_logging
except Exception:
    def setup_logging(flask_app):
        return None


BASE_DIR = Path(__file__).resolve().parent

# Required runtime folders. Safe to create even if already present.
for folder in [
    BASE_DIR / "instance",
    BASE_DIR / "uploads",
    BASE_DIR / "uploads" / "generated",
    BASE_DIR / "uploads" / "temp",
    BASE_DIR / "static" / "generated",
    BASE_DIR / "static" / "generated" / "uploads",
    BASE_DIR / "logs",
]:
    folder.mkdir(parents=True, exist_ok=True)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    os.getenv("SAIVEX_SECRET_KEY", "change-this-secret-key-before-production")
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    app.config.get("SQLALCHEMY_DATABASE_URI", "sqlite:///instance/saivex.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("SAIVEX_MAX_UPLOAD_MB", "100")) * 1024 * 1024

# Cookies. Keep SECURE false locally; set SESSION_COOKIE_SECURE=True on HTTPS production.
secure_cookie = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = secure_cookie
app.config["REMEMBER_COOKIE_SECURE"] = secure_cookie

setup_logging(app)


@app.after_request
def apply_production_security(response):
    return add_security_headers(response)


@app.route("/health")
def health():
    return {
        "status": "ok",
        "app": "SAIVEX",
        "mode": "production-ready",
    }


@app.route("/production/status")
def production_status():
    return {
        "app": "SAIVEX",
        "status": "running",
        "public_url": os.getenv("SAIVEX_PUBLIC_URL", "http://127.0.0.1:5000"),
        "database": app.config.get("SQLALCHEMY_DATABASE_URI", ""),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "upload_limit_mb": os.getenv("SAIVEX_MAX_UPLOAD_MB", "100"),
    }


@app.errorhandler(404)
def not_found(error):
    try:
        from flask import render_template
        return render_template("404.html"), 404
    except Exception:
        return "404 - Page not found", 404


@app.errorhandler(500)
def server_error(error):
    try:
        from flask import render_template
        return render_template("500.html"), 500
    except Exception:
        return "500 - SAIVEX server error", 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1" and os.getenv("PRODUCTION", "0") != "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
