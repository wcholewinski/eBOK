from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from app.models import Apartment, Payment, Tenant, BuildingAlert, SensorReading
from app.ml_analysis import PredictiveAnalysis


class Command(BaseCommand):
    help = 'Sprawdza system pod kątem alertów i wysyła powiadomienia'

    def handle(self, *args, **options):
        self.stdout.write('Rozpoczynam sprawdzanie alertów...')

        # Inicjalizacja analizatora ML
        ml_analyzer = PredictiveAnalysis()
        alerts_created = 0

        # 1. Sprawdzenie zaległych płatności
        overdue_payments = Payment.objects.filter(
            status='pending',
            date__lt=timezone.now().date()
        )

        for payment in overdue_payments:
            # Tworzenie alertu
            alert, created = BuildingAlert.objects.get_or_create(
                apartment=payment.tenant.apartment,
                alert_type='payment',
                is_active=True,
                defaults={
                    'title': f'Zaległa płatność - Mieszkanie {payment.tenant.apartment.number}',
                    'message': f'Zaległa płatność {payment.get_type_display()} w kwocie {payment.amount} PLN',
                    'severity': 'warning' if (timezone.now().date() - payment.date).days < 14 else 'critical',
                }
            )

            # Jeśli alert został właśnie utworzony, powiadamiamy
            if created:
                alerts_created += 1
                # Wysyłanie maila (przykład)
                try:
                    if payment.tenant.user.email:
                        send_mail(
                            subject='eBOK - Przypomnienie o płatności',
                            message=f'Przypominamy o zaległej płatności: {payment.get_type_display()} w kwocie {payment.amount} PLN',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[payment.tenant.user.email],
                            fail_silently=True
                        )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Błąd wysyłania maila: {e}'))

        self.stdout.write(f'Sprawdzono {overdue_payments.count()} zaległych płatności.')

        # 2. Analiza anomalii w odczytach sensorów
        for apartment in Apartment.objects.all():
            anomalies = ml_analyzer.detect_anomalies(apartment.id)

            if anomalies:
                alert, created = BuildingAlert.objects.get_or_create(
                    apartment=apartment,
                    alert_type='utility',
                    is_active=True,
                    defaults={
                        'title': f'Anomalia w zużyciu - Mieszkanie {apartment.number}',
                        'message': f'Wykryto {len(anomalies)} anomalie w zużyciu mediów',
                        'severity': 'warning',
                        'expires_at': timezone.now() + timedelta(days=7)
                    }
                )

                if created:
                    alerts_created += 1

        # 3. Przewidywanie przyszłego zużycia i alertowanie o wysokich wartościach
        for apartment in Apartment.objects.all():
            predictions = ml_analyzer.predict_utility_consumption(apartment.id, 'electricity', 1)

            if predictions and len(predictions) > 0:
                # Jeśli przewidywane zużycie jest o 30% wyższe niż średnia
                predicted = predictions[0]['predicted_consumption']

                # Pobieranie ostatnich 3 odczytów do porównania
                recent_readings = SensorReading.objects.filter(
                    sensor__apartment=apartment,
                    sensor__sensor_type='electricity'
                ).order_by('-timestamp')[:3]

                if recent_readings.exists():
                    avg_consumption = sum(r.value for r in recent_readings) / recent_readings.count()

                    # Jeśli predykcja jest znacząco wyższa, tworzymy alert
                    if predicted > avg_consumption * 1.3:  # 30% więcej
                        alert, created = BuildingAlert.objects.get_or_create(
                            apartment=apartment,
                            alert_type='utility',
                            severity='info',
                            is_active=True,
                            defaults={
                                'title': f'Prognoza wysokiego zużycia - Mieszkanie {apartment.number}',
                                'message': f'Przewidywane zużycie energii: {predicted} kWh (o {((predicted/avg_consumption)-1)*100:.0f}% więcej niż średnia)',
                                'expires_at': timezone.now() + timedelta(days=30)
                            }
                        )

                        if created:
                            alerts_created += 1

        # 4. Usuwanie wygasłych alertów
        expired_count = BuildingAlert.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Zakończono sprawdzanie alertów. Utworzono {alerts_created} nowych alertów. '
            f'Dezaktywowano {expired_count} wygasłych alertów.'
        ))
