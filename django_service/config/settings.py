"""Django settings for the Payment System (Django API service)."""

import os
from datetime import timedelta
from pathlib import Path

import pymysql
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Let Django use PyMySQL as the MySQL driver (no C compiler needed on Windows)
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

# Load the .env file from the project root (ignored if absent, e.g. in Docker)
load_dotenv(BASE_DIR.parent / ".env")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"Environment variable {name} is not set")
    return value


# Core settings
SECRET_KEY = require_env("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "accounts",
    "cards",
    "transactions",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Only the listed frontend origins may call the API
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database (MySQL; host and port come from .env)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE"),
        "USER": os.getenv("MYSQL_USER"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3307"),
    }
}

# Custom user model (table name: users)
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Django REST Framework + JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "30/min", "user": "120/min"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    # Must be identical to JWT_SECRET_KEY used by the FastAPI service
    "SIGNING_KEY": require_env("JWT_SECRET_KEY"),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Payment System - Django API",
    "DESCRIPTION": "Authentication, cards, transactions and admin reporting. "
                   "Authorize with the access token from POST /api/auth/login/. "
                   "CVV is never stored.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # "Try it out" calls the Django server, also when opened from port 8001
    "SERVERS": [{"url": "http://127.0.0.1:8000"}],
    # Order of the groups in Swagger UI
    "TAGS": [
        {"name": "auth", "description": "Register, login, refresh, logout and current user"},
        {"name": "admin", "description": "Staff-only users, cards, transactions, export and summary"},
        {"name": "cards", "description": "Manage your saved cards (no CVV stored)"},
        {"name": "transactions", "description": "Your payment history with filters"},
    ],
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Email (console backend, no real mail is sent)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Set SECURE_COOKIES=True in .env only when the site is served over HTTPS
if os.getenv("SECURE_COOKIES", "False") == "True":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True