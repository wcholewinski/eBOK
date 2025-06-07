from django.apps import AppConfig

class EbokConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = "eBOK"

    def ready(self):
        """Wykonywane po zarejestrowaniu aplikacji"""

        pass
