from .base import *  # noqa: F403

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bro_hub_dev",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Celery configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"

# BRO SETTINGS
BRO_UITGIFTE_SERVICE_URL = "https://publiek.broservices.nl"
BRONHOUDERSPORTAAL_URL = "https://acc.bronhouderportaal-bro.nl"
