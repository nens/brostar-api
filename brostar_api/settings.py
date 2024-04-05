import os
from pathlib import Path

import sentry_sdk

# Environment variables can get a value from an .env file via docker-compose.
# In development, you'll need to set the NENS_AUTH_* ones.
FIELD_ENCRYPTION_KEY = os.getenv(
    "FIELD_ENCRYPTION_KEY", default="DUMMY-NEEDS-PROD-SETTING-Xgb1GczqZe909UMNc4="
)
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    default="django-insecure-r4_51z=)9re0wxnj(fwanhzi($42k#usdr37z!o2c-a04*4p06",
)
NENS_AUTH_ISSUER = os.getenv("NENS_AUTH_ISSUER")
NENS_AUTH_CLIENT_ID = os.getenv("NENS_AUTH_CLIENT_ID")
NENS_AUTH_CLIENT_SECRET = os.getenv("NENS_AUTH_CLIENT_SECRET")
DEBUG_ENV = os.getenv("DEBUG", default="true")
DATABASE_HOST = os.getenv("DATABASE_HOST", "db")
DATABASE_USER = os.getenv("DATABASE_USER", "brostar")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "brostar")
SENTRY_DSN = os.getenv("SENTRY_DSN")  # Not required, only used in staging/production.

# Convert the environment variable (which is a string) to a boolean.
DEBUG = DEBUG_ENV.lower() == "true"  # True is the default


TIME_ZONE = "CET"
USE_TZ = True

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


ALLOWED_HOSTS = []
if not DEBUG:
    ALLOWED_HOSTS = [".brostar.nl"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "https://staging.brostar.nl",
]


# Application definition

INSTALLED_APPS = [
    "api.apps.ApiConfig",
    "gmn.apps.GmnConfig",
    "gmw.apps.GmwConfig",
    "nens_auth_client",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "corsheaders",
    "django_filters",
    "encrypted_model_fields",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]


AUTHENTICATION_BACKENDS = [
    "nens_auth_client.backends.RemoteUserBackend",
    "nens_auth_client.backends.AcceptNensBackend",
    "nens_auth_client.backends.TrustedProviderMigrationBackend",
    "django.contrib.auth.backends.ModelBackend",
]


ROOT_URLCONF = "brostar_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "api", "bro_upload", "templates")],
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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",  # DEBUG level would also print sql statements
            "propagate": False,
        },
    },
}

WSGI_APPLICATION = "brostar_api.wsgi.application"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "https://staging.brostar.nl",
]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "brostar",
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# In production, they're
# hosted via "whitenoise": https://whitenoise.readthedocs.io/en/latest/django.html
STATIC_URL = "static/"
STATIC_ROOT = "/staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF configuration
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 1000,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "nens_auth_client.rest_framework.OAuth2TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}


# Automatically discover tasks in Django app
CELERY_IMPORTS = ("api.tasks",)
# TODO: fix celery env settings
CELERY_BROKER_URL = "redis://redis:6379/0"

if SENTRY_DSN:
    # SENTRY_DSN will only be set on staging/production, btw.
    sentry_sdk.init(dsn=SENTRY_DSN)

# BRO SETTINGS:
# TODO: voor nu is het hardcoded op True. We zouden het zo moeten inrichten dat
#       de staging standaard op demo staat en productie op de BRO productie omgeving
BRO_DEMO_OMGEVING = True

if BRO_DEMO_OMGEVING:
    BRO_UITGIFTE_SERVICE_URL = "https://int-publiek.broservices.nl"
    BRONHOUDERSPORTAAL_URL = "https://demo.bronhouderportaal-bro.nl"
else:
    BRO_UITGIFTE_SERVICE_URL = "https://publiek.broservices.nl"
    BRONHOUDERSPORTAAL_URL = "https://bronhouderportaal-bro.nl"
    # BRONHOUDERSPORTAAL_URL = "https://www.bronhouderportaal-bro.nl"
