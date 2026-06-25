import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        os.getenv("SAIVEX_SECRET_KEY", "saivex-secret-key-change-later")
    )

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/saivex.db")


    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    REMEMBER_COOKIE_SECURE = os.getenv("REMEMBER_COOKIE_SECURE", "False") == "True"

    MAX_CONTENT_LENGTH = int(os.getenv("SAIVEX_MAX_UPLOAD_MB", "100")) * 1024 * 1024

    UPLOAD_FOLDER = os.getenv("SAIVEX_UPLOAD_FOLDER", "uploads")
    GENERATED_FOLDER = os.getenv("SAIVEX_GENERATED_FOLDER", "static/generated")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
