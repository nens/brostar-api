from django.apps import AppConfig


class GldConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gld"

    def ready(self):
        import gld.signals  # noqa
