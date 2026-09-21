"""
Django settings for con-wms project.

Cấu hình chạy theo môi trường qua biến môi trường (xem DEPLOY.md):

- `DEBUG`            — mặc định `True` (dev); prod phải đặt `False`
- `SECRET_KEY`       — bắt buộc khi `DEBUG=False` (không dùng fallback trong prod)
- `ALLOWED_HOSTS`    — chuỗi phân tách bằng dấu phẩy; prod bắt buộc (không dùng `*`)
- `DATABASE_URL`     — khi đặt sẽ dùng PostgreSQL (vd Neon: `postgres://user:pass@host/db?sslmode=require`); không đặt → SQLite (dev)
- `ENABLE_DEMO_SEED` — mặc định theo `DEBUG`; tắt ở prod để loại `demo_seed` khỏi INSTALLED_APPS
- `CORS_ALLOWED_ORIGINS` — chuỗi phân tách dấu phẩy (chỉ dùng nếu browser gọi thẳng API; kiến trúc BFF+proxy không cần)
- `WEB_CONCURRENCY`  — số worker Gunicorn (docker, mặc định 2)
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "t", "yes")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

DEBUG = env_bool("DEBUG", "True")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Fallback chỉ dành cho dev — prod phải cung cấp SECRET_KEY qua env.
        SECRET_KEY = "django-insecure-d$ar#kl%x$=o-34&8^&s5#s5*!kgx6&7y4+jl&$#!(-0=o$-(t"
    else:
        raise ImproperlyConfigured("SECRET_KEY bắt buộc khi DEBUG=False.")

ALLOWED_HOSTS = (
    ["*"]
    if DEBUG
    else [
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
)

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS bắt buộc khi DEBUG=False.")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    # Local apps
    "iam",
    "warehouse",
    "catalog",
    "supplier",
    "sites",
    "inventory",
]

# Dữ liệu demo (seed_all...) chỉ dành cho dev — tắt ở prod.
if env_bool("ENABLE_DEMO_SEED", str(DEBUG)):
    INSTALLED_APPS.append("demo_seed")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "djangorestframework_camel_case.middleware.CamelCaseMiddleWare",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS")
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

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


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# Prod: đặt DATABASE_URL (PostgreSQL, vd Neon/Supabase). Dev: SQLite mặc định.
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)} if DATABASE_URL else {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "iam.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# DRF
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "config.exceptions.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "TOKEN_OBTAIN_SERIALIZER": "iam.serializers.LoginSerializer",
}

# drf-spectacular + camelCase integration
SPECTACULAR_SETTINGS = {
    "TITLE": "WMS API",
    "DESCRIPTION": "Warehouse Management System API",
    "VERSION": "1.0.0",
    "CAMELIZE_NAMES": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
}