from django.apps import AppConfig


class GmwConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gmw"

    def ready(self):
        import gmw.signals  # noqa
