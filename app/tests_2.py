from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import csv
import io

from .models import (
    Apartment, Tenant, Payment, Ticket,
    Sensor, SensorReading, UtilityConsumption
)
from .forms import ApartmentForm, TenantForm, PaymentForm


class EBOKModelTests(TestCase):
    """Testy dla wszystkich modeli"""

    def setUp(self):
        self.apartment = Apartment.objects.create(
            number='101',
            floor=1,
            area=50.5,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )

        self.user = User.objects.create_user(
            username='tenant',
            password='tenantpass',
            email='tenant@example.com'
        )

        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment,
            num_occupants=2
        )

    def test_apartment_model(self):
        """Test modelu Apartment"""
        apt = self.apartment
        self.assertEqual(str(apt), "Mieszkanie 101")
        self.assertEqual(apt.total_fees(), Decimal('1600.00'))

    def test_tenant_model(self):
        """Test modelu Tenant"""
        tenant = self.tenant
        self.assertEqual(str(tenant), f"{tenant.user.username} - Mieszkanie {tenant.apartment.number}")
        self.assertEqual(tenant.num_occupants, 2)

    def test_payment_model(self):
        """Test modelu Payment"""
        payment = Payment.objects.create(
            tenant=self.tenant,
            date=timezone.now().date(),
            amount=1500.00,
            type='rent',
            status='paid'
        )

        expected_str = f"Płatność {payment.get_type_display()} - {payment.amount} zł"
        self.assertEqual(str(payment), expected_str)

    def test_ticket_model(self):
        """Test modelu Ticket"""
        ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Test zgłoszenie',
            description='Opis testowego zgłoszenia',
            status='new'
        )

        expected_str = f"[Nowe] Test zgłoszenie"
        self.assertEqual(str(ticket), expected_str)

    def test_sensor_model(self):
        """Test modelu Sensor"""
        sensor = Sensor.objects.create(
            name='Temperatura salon',
            sensor_type='temperature',
            apartment=self.apartment,
            location='salon',
            is_active=True
        )

        self.assertEqual(sensor.name, 'Temperatura salon')
        self.assertEqual(sensor.sensor_type, 'temperature')
        self.assertTrue(sensor.is_active)

    def test_sensor_reading_model(self):
        """Test modelu SensorReading"""
        sensor = Sensor.objects.create(
            name='Temperatura salon',
            sensor_type='temperature',
            apartment=self.apartment,
            location='salon'
        )

        reading = SensorReading.objects.create(
            sensor=sensor,
            value=22.5,
            unit='°C'
        )

        self.assertEqual(reading.value, 22.5)
        self.assertEqual(reading.unit, '°C')

    def test_utility_consumption_model(self):
        """Test modelu UtilityConsumption"""
        consumption = UtilityConsumption.objects.create(
            apartment=self.apartment,
            utility_type='water',
            consumption=15.5,
            month=timezone.now().date(),
            cost_per_unit=Decimal('3.50'),
            total_cost=Decimal('54.25')
        )

        self.assertEqual(consumption.utility_type, 'water')
        self.assertEqual(consumption.consumption, 15.5)
        self.assertEqual(consumption.total_cost, Decimal('54.25'))


class EBOKIntegrationTests(TestCase):
    """Testy integracyjne - sprawdzają czy całe funkcjonalności działają razem"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.client = Client()

    def test_complete_apartment_workflow(self):
        """Test pełnego workflow zarządzania mieszkaniem"""
        self.client.login(username='admin', password='adminpass')

        # 1. Dodaj mieszkanie
        apartment_data = {
            'number': '201',
            'floor': 2,
            'area': 65.0,
            'rent': 1800.00,
            'trash_fee': 65.00,
            'water_fee': 45.00,
            'gas_fee': 30.00
        }
        response = self.client.post(reverse('app:admin_add_apartment'), apartment_data)
        self.assertEqual(response.status_code, 302)

        apartment = Apartment.objects.get(number='201')

        # 2. Dodaj lokatora
        tenant_data = {
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'email': 'anna.nowak@example.com',
            'phone': '987654321',
            'apartment': apartment.id,
            'num_occupants': 1
        }
        response = self.client.post(reverse('app:admin_add_tenant'), tenant_data)
        self.assertEqual(response.status_code, 302)

        tenant = Tenant.objects.get(apartment=apartment)

        # 3. Dodaj płatność
        payment_data = {
            'tenant': tenant.id,
            'date': timezone.now().date(),
            'amount': 1800.00,
            'type': 'rent',
            'status': 'paid'
        }
        response = self.client.post(reverse('app:admin_add_payment'), payment_data)
        self.assertEqual(response.status_code, 302)

        payment = Payment.objects.get(tenant=tenant)
        self.assertEqual(float(payment.amount), 1800.00)

        # 4. Edytuj mieszkanie
        updated_data = {
            'number': '201',
            'floor': 2,
            'area': 70.0,  # Zmiana powierzchni
            'rent': 1900.00,  # Zmiana czynszu
            'trash_fee': 65.00,
            'water_fee': 45.00,
            'gas_fee': 30.00
        }
        response = self.client.post(
            reverse('app:admin_edit_apartment', args=[apartment.pk]),
            updated_data
        )
        self.assertEqual(response.status_code, 302)

        apartment.refresh_from_db()
        self.assertEqual(float(apartment.area), 70.0)
        self.assertEqual(float(apartment.rent), 1900.00)

    def test_sensor_and_consumption_integration(self):
        """Test integracji sensorów z danymi zużycia"""
        # Utwórz mieszkanie
        apartment = Apartment.objects.create(
            number='301',
            floor=3,
            area=55.0,
            rent=1600.00,
            trash_fee=55.00,
            water_fee=35.00,
            gas_fee=25.00
        )

        # Dodaj sensor
        sensor = Sensor.objects.create(
            name='Licznik wody',
            sensor_type='water_flow',
            apartment=apartment,
            location='łazienka'
        )

        # Dodaj odczyty
        readings = [
            SensorReading.objects.create(sensor=sensor, value=10.5, unit='m³'),
            SensorReading.objects.create(sensor=sensor, value=12.0, unit='m³'),
            SensorReading.objects.create(sensor=sensor, value=9.8, unit='m³'),
        ]

        # Dodaj dane zużycia
        consumption = UtilityConsumption.objects.create(
            apartment=apartment,
            utility_type='water',
            consumption=32.3,  # Suma odczytów
            month=timezone.now().date(),
            cost_per_unit=Decimal('3.50'),
            total_cost=Decimal('113.05')
        )

        # Sprawdź powiązania
        self.assertEqual(SensorReading.objects.filter(sensor=sensor).count(), 3)
        self.assertEqual(consumption.apartment, apartment)
        self.assertEqual(sensor.apartment, apartment)

    def test_tenant_permissions_and_access(self):
        """Test uprawnień lokatora"""
        # Utwórz mieszkanie i lokatora
        apartment = Apartment.objects.create(
            number='401',
            floor=4,
            area=50.0,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )

        tenant_user = User.objects.create_user(
            username='lokator401',
            password='password',
            email='lokator401@example.com'
        )

        tenant = Tenant.objects.create(
            user=tenant_user,
            apartment=apartment,
            num_occupants=2
        )

        # Zaloguj lokatora
        self.client.login(username='lokator401', password='password')

        # Sprawdź dostęp do własnych danych
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '401')  # Numer mieszkania

        # Sprawdź brak dostępu do panelu admina
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Przekierowanie

        # Sprawdź dostęp do własnych płatności
        Payment.objects.create(
            tenant=tenant,
            date=timezone.now().date(),
            amount=1500.00,
            type='rent',
            status='paid'
        )

        response = self.client.get(reverse('app:user_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1500')


class EBOKPerformanceTests(TestCase):
    """Testy wydajności"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )

        # Utwórz więcej danych testowych
        for i in range(50):
            apartment = Apartment.objects.create(
                number=f'{i + 100}',
                floor=(i % 10) + 1,
                area=50.0 + i,
                rent=1500.00 + i * 100,
                trash_fee=50.00,
                water_fee=30.00,
                gas_fee=20.00
            )

            user = User.objects.create_user(
                username=f'tenant{i}',
                password='password',
                email=f'tenant{i}@example.com'
            )

            tenant = Tenant.objects.create(
                user=user,
                apartment=apartment,
                num_occupants=(i % 4) + 1
            )

            # Dodaj płatności
            for j in range(5):
                Payment.objects.create(
                    tenant=tenant,
                    date=timezone.now().date(),
                    amount=apartment.rent,
                    type='rent',
                    status='paid' if j % 2 == 0 else 'pending'
                )

    def test_dashboard_performance_with_many_apartments(self):
        """Test wydajności dashboard z wieloma mieszkaniami"""
        self.client.login(username='admin', password='adminpass')

        import time
        start_time = time.time()

        response = self.client.get(reverse('app:admin_dashboard'))

        end_time = time.time()
        execution_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 2.0)  # Powinno wykonać się w mniej niż 2 sekundy

    def test_payments_view_performance(self):
        """Test wydajności widoku płatności"""
        self.client.login(username='admin', password='adminpass')

        import time
        start_time = time.time()

        response = self.client.get(reverse('app:admin_payments'))

        end_time = time.time()
        execution_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.5)  # Powinno wykonać się w mniej niż 1.5 sekundy


class EBOKSecurityTests(TestCase):
    """Testy bezpieczeństwa"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )

        self.tenant_user = User.objects.create_user(
            username='tenant',
            password='tenantpass',
            email='tenant@example.com'
        )

        self.apartment = Apartment.objects.create(
            number='501',
            floor=5,
            area=60.0,
            rent=1700.00,
            trash_fee=60.00,
            water_fee=40.00,
            gas_fee=30.00
        )

    def test_admin_required_decorator(self):
        """Test czy decorator @admin_required działa"""
        # Lokator próbuje dostać się do panelu admina
        self.client.login(username='tenant', password='tenantpass')

        admin_urls = [
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_add_tenant'),
            reverse('app:admin_payments'),
        ]

        for url in admin_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)  # Przekierowanie

    def test_csrf_protection(self):
        """Test ochrony CSRF"""
        self.client.login(username='admin', password='adminpass')

        # Próba POST bez CSRF token
        response = self.client.post(reverse('app:admin_add_apartment'), {
            'number': '999',
            'floor': 9,
            'area': 99.0,
            'rent': 9999.00,
            'trash_fee': 99.00,
            'water_fee': 99.00,
            'gas_fee': 99.00
        }, HTTP_X_CSRFTOKEN='invalid_token')

        # Django powinien odrzucić żądanie
        self.assertEqual(response.status_code, 403)

    def test_authentication_required(self):
        """Test czy wymagane jest uwierzytelnienie"""
        # Niezalogowany użytkownik
        protected_urls = [
            reverse('app:dashboard'),
            reverse('app:user_payments'),
            reverse('app:tickets'),
            reverse('app:admin_dashboard'),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)  # Przekierowanie do logowania
