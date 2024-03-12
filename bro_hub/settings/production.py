from .base import *  # noqa: F403

DEBUG = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bro_hub_prod",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "5432",
    }
}

# Celery configuration
CELERY_BROKER_URL = ""

# BRO SETTINGS
BRO_UITGIFTE_SERVICE_URL = "https://publiek.broservices.nl"
BRONHOUDERSPORTAAL_URL = "https://www.bronhouderportaal-bro.nl"
