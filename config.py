import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBuleqRwUwRu1OypX7-FCAE3nui-3WnUpQ")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBuleqRwUwRu1OypX7-FCAE3nui-3WnUpQ")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@ourhome.local")
