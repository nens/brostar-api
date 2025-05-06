import os

import sentry_sdk
from kombu import Exchange, Queue

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

_debug_env = os.getenv("DEBUG", default="true")
DATABASE_HOST = os.getenv("DATABASE_HOST", "db")
DATABASE_USER = os.getenv("DATABASE_USER", "brostar")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "brostar")
SENTRY_DSN = os.getenv("SENTRY_DSN")  # Not required, only used in staging/production.
_use_bro_production_env = os.getenv("USE_BRO_PRODUCTION", default="false")

# Convert string-based environment variables to booleans.
DEBUG = _debug_env.lower() == "true"  # default: True
USE_BRO_PRODUCTION = _use_bro_production_env.lower() == "true"  # Default: False


TIME_ZONE = "CET"
USE_TZ = True

# SETTINGS_DIR allows media paths and so to be relative to this settings file
# instead of hardcoded to c:\only\on\my\computer.
SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

# BUILDOUT_DIR is for access to the "surrounding" buildout, for instance for
# BUILDOUT_DIR/var/static files to give django-staticfiles a proper place
# to place all collected static files.
BASE_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, "../"))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, "../.."))

ALLOWED_HOSTS = ["localhost", "host.docker.internal", "127.0.0.1", "0.0.0.0"]

if not DEBUG:
    ALLOWED_HOSTS = [".brostar.nl"]


# Application definition

INSTALLED_APPS = [
    "api.apps.ApiConfig",
    "gmn.apps.GmnConfig",
    "gmw.apps.GmwConfig",
    "gar.apps.GarConfig",
    "gld.apps.GldConfig",
    "frd.apps.FrdConfig",
    "nens_auth_client",
    "django_prometheus",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_api_key",
    "drf_yasg",
    "corsheaders",
    "django_filters",
    "encrypted_model_fields",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "https://staging.brostar.nl",
]


MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

# PROMETHEUS
PROMETHEUS_METRIC_NAMESPACE = "brostar"

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

LOG_FOLDERS = ["general", "access", "task_file"]
LOG_DIR = "/var/logs"
os.makedirs(LOG_DIR, exist_ok=True)
for log in LOG_FOLDERS:
    os.makedirs(f"{LOG_DIR}/{log}", exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s: %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        },
        "task_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "task.log"),
            "formatter": "detailed",
        },
        "access_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "access.log"),
            "formatter": "detailed",
        },
        "general_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "general.log"),
            "formatter": "detailed",
        },
    },
    "loggers": {
        "task": {
            "handlers": ["task_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "access": {
            "handlers": ["access_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "general": {
            "handlers": ["general_file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


WSGI_APPLICATION = "brostar_api.wsgi.application"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "https://staging.brostar.nl",
    "https://www.brostar.nl",
]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
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
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# User-uploaded files. The docker compose mounts the media dir ("./media" in the current
# dir for development, for instance).
MEDIA_ROOT = "/media"
MEDIA_URL = "/media/"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF configuration
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.api_keys.authentication.APIKeyBasicAuthentication",
        "api.api_keys.authentication.CustomSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "api.api_keys.permissions.InScope",
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# Automatically discover tasks in Django app
CELERY_IMPORTS = ("api.tasks",)

# TODO: fix celery env settings
CELERY_BROKER_URL = "redis://redis:6379/0"
# Auto-expire results after 1 day
CELERY_RESULT_EXPIRES = 60 * 60 * 24

# New queue configuration
CELERY_TASK_QUEUES = (
    # Define all your requested queues
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("upload", Exchange("upload"), routing_key="upload"),
)

# Default queue if not specified
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_EXCHANGE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"

# Add memory limits to prevent memory issues
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 150000  # in KB, adjust as needed

if SENTRY_DSN:
    # SENTRY_DSN will only be set on staging/production, btw.
    sentry_sdk.init(dsn=SENTRY_DSN)

if USE_BRO_PRODUCTION:
    BRO_UITGIFTE_SERVICE_URL = "https://publiek.broservices.nl"
    BRONHOUDERSPORTAAL_URL = "https://www.bronhouderportaal-bro.nl"
else:
    BRO_UITGIFTE_SERVICE_URL = "https://int-publiek.broservices.nl"
    BRONHOUDERSPORTAAL_URL = "https://demo.bronhouderportaal-bro.nl"

if not DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "int-smtp.nens"
    DEFAULT_FROM_EMAIL = "BROSTAR <noreply@nelen-schuurmans.nl>"
    NENS_AUTH_INVITATION_EMAIL_SUBJECT = "Uitnodiging voor BROSTAR"
