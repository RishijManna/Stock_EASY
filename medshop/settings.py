from pathlib import Path
import os

# ------------------------------------------------------------
# Base
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Keep this ONLY for local dev fallback; in production set via env
SECRET_KEY = os.getenv("SECRET_KEY", "dev-not-secret-change-me")

# In Render you should set DEBUG=False (env var)
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    # Render domains
    "med-stock.onrender.com",
    ".onrender.com",
]

# Important for Django 4+/5+ behind proxies (Render)
CSRF_TRUSTED_ORIGINS = [
    "https://med-stock.onrender.com",
    "https://*.onrender.com",
]

# ------------------------------------------------------------
# Applications
# ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",   # ← add this
    "inventory",
    "accounts",
    "reports",
]

# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files in prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "medshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "medshop.wsgi.application"

# ------------------------------------------------------------
# Database
#  - Dev: SQLite
#  - Prod: REQUIRE DATABASE_URL (PostgreSQL on Render)
# ------------------------------------------------------------
try:
    import dj_database_url
except Exception:
    dj_database_url = None

if DEBUG:
    # Local development: SQLite is fine
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Production: refuse to start without DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not (db_url and dj_database_url):
        raise RuntimeError(
            "DATABASE_URL missing (or dj_database_url not installed). "
            "Set DATABASE_URL to your Render PostgreSQL External Connection string."
        )
    DATABASES = {
        "default": dj_database_url.parse(db_url, conn_max_age=600, ssl_require=True)
    }

# ------------------------------------------------------------
# Password validation
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------
# I18N / TZ
# ------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Static & Media
# ------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # for collectstatic on Render
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Whitenoise optimized storage
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------
# Security (safe defaults for prod; tweak as needed)
# ------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24  # 1 day to start; raise after verifying HTTPS works
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
