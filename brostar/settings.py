import os
from pathlib import Path

FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
NENS_AUTH_ISSUER = os.getenv("NENS_AUTH_ISSUER")
NENS_AUTH_CLIENT_ID = os.getenv("NENS_AUTH_CLIENT_ID")
NENS_AUTH_CLIENT_SECRET = os.getenv("NENS_AUTH_CLIENT_SECRET")
# Environment variables can get a default value from docker-compose itself *or* from a
# `.env` file, as docker-compose automatically reads that (if the environment variable
# itself is mentioned in the compose file).

TIME_ZONE = "CET"
USE_TZ = True


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-r4_51z=)9re0wxnj(fwanhzi($42k#usdr37z!o2c-a04*4p06"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:4200',
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


ROOT_URLCONF = "brostar.urls"

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
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "django_log.log"),
        },
    },
    "loggers": {
        "": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

WSGI_APPLICATION = "brostar.wsgi.application"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "brostar",
        "USER": "brostar",
        "PASSWORD": "brostar",
        "HOST": "db",
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

STATIC_URL = "static/"

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

# BRO SETTINGS
BRO_UITGIFTE_SERVICE_URL = "https://publiek.broservices.nl"
BRONHOUDERSPORTAAL_URL = "https://acc.bronhouderportaal-bro.nl"
# BRONHOUDERSPORTAAL_URL = "https://www.bronhouderportaal-bro.nl"
