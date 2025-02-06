from django.apps import AppConfig


class GarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gar"

    def ready(self):
        import gar.signals  # noqa
