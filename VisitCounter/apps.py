from django.apps import AppConfig


class VisitCounterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'VisitCounter'
    
    def ready(self):
        import VisitCounter.signals
