from django.apps import AppConfig
from .cron import crontask

class DjangoOptimizerConfig(AppConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_optimizer'
