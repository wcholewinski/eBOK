from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment
from app.utils.statistics import calculate_statistics
from app.utils.reports import generate_report
from datetime import datetime, timedelta
import tempfile
import os

class UtilsTests(TestCase):
    """Testy dla funkcji pomocniczych"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number='1101',
            floor=11,
            area=100.0,
            rent=2500.00,
            trash_fee=105.00,
            water_fee=85.00,
            gas_fee=75.00
        )

        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username='utilsuser',
            password='utilspass',
            email='utils@example.com'
        )

        # Tworzenie najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment
        )

        # Tworzenie płatności
        self.current_month = datetime.now().month
        for month in range(1, 13):
            payment_date = datetime(2023, month, 15).date()
            status = 'paid' if month < self.current_month else 'pending'
            Payment.objects.create(
                tenant=self.tenant,
                amount=2500.00,
                type='rent',
                status=status,
                date=payment_date
            )

    def test_calculate_statistics(self):
        """Test obliczania statystyk"""
        # Wywołanie funkcji do obliczania statystyk
        stats = calculate_statistics(self.apartment.id)

        # Sprawdzenie wyników
        self.assertIn('payment_history', stats)
        self.assertEqual(len(stats['payment_history']), 12)

        # Sprawdzenie statystyk płatności
        paid_count = sum(1 for payment in stats['payment_history'] if payment['status'] == 'paid')
        self.assertEqual(paid_count, self.current_month - 1)


