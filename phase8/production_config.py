import os

def configure_production_app(app):
    app.config["SECRET_KEY"] = os.environ.get("SAIVEX_SECRET_KEY", app.config.get("SECRET_KEY", "change-me"))

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if os.environ.get("RENDER") or os.environ.get("PRODUCTION"):
        app.config["SESSION_COOKIE_SECURE"] = True

    return app
