import os

from celery import Celery

from bro_hub.settings.base import ENVIRONMENT

if ENVIRONMENT == "production":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bro_hub.settings.production")
elif ENVIRONMENT == "development":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bro_hub.settings.development")

app = Celery("bro_hub")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
