from django.core.management.base import BaseCommand
from app.models import BuildingAlert

class Command(BaseCommand):
    help = 'Konwertuje wszystkie krytyczne alerty na ostrzeżenia'

    def handle(self, *args, **options):
        self.stdout.write('Rozpoczynam konwersję krytycznych alertów...')

        # Znajdź wszystkie krytyczne alerty
        critical_alerts = BuildingAlert.objects.filter(severity='critical')
        count = critical_alerts.count()

        # Konwertuj na ostrzeżenia
        critical_alerts.update(severity='warning')

        self.stdout.write(self.style.SUCCESS(
            f'Zakończono konwersję alertów. Przekonwertowano {count} alertów.'
        ))
