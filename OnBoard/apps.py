from django.apps import AppConfig


class OnboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'OnBoard'

    def ready(self):
        from .Ban import signals
