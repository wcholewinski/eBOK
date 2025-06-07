from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from app.models import Apartment, Payment, Tenant, BuildingAlert
from app.utils.ml_analysis import PredictiveAnalysis


class Command(BaseCommand):
    help = 'Sprawdza system pod kątem alertów i wysyła powiadomienia'

    def handle(self, *args, **options):
        self.stdout.write('Rozpoczynam sprawdzanie alertów...')

        # Inicjalizacja licznika
        alerts_created = 0

        # 1. Sprawdzenie zaległych płatności
        overdue_payments = Payment.objects.filter(
            status='pending',
            date__lt=timezone.now().date()
        )

        for payment in overdue_payments:
            # Tworzenie alertu dla zaległej płatności
            alert, created = BuildingAlert.objects.get_or_create(
                apartment=payment.tenant.apartment,
                alert_type='payment',
                is_active=True,
                defaults={
                    'title': f'Mieszkanie {payment.tenant.apartment.number} zalega z płatnością',
                    'message': f'Zaległa płatność {payment.get_type_display()} w kwocie {payment.amount} PLN',
                    'severity': 'warning',
                }
            )

            if created:
                alerts_created += 1
                self.stdout.write(f'Utworzono alert dla zaległej płatności w mieszkaniu {payment.tenant.apartment.number}')

        self.stdout.write(f'Sprawdzono {overdue_payments.count()} zaległych płatności.')

        # 2. Usuwanie wygasłych alertów
        expired_count = BuildingAlert.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Zakończono sprawdzanie alertów. Utworzono {alerts_created} nowych alertów. '
            f'Dezaktywowano {expired_count} wygasłych alertów.'
        ))
