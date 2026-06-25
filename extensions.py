from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth


db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()


def init_extensions(app):
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "login"

    oauth.init_app(app)

    return app
