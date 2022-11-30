from django.apps import AppConfig
from .cron import CronTask

class DjangoOptimizerConfig(AppConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def ready(self, *args, **kwargs):
        CronTask.setup()
        CronTask.crontask.run_all_tasks()
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_optimizer'
