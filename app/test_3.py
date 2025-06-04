from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import csv
import io

from .models import Apartment, Tenant, Payment, Ticket, Sensor, SensorReading, UtilityConsumption
from .forms import ApartmentForm, TenantForm, PaymentForm


class EBOKTests(TestCase):
    """Podstawowe testy funkcjonalności eBOK"""

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
            number='101',
            floor=1,
            area=50.5,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )
        self.tenant = Tenant.objects.create(
            user=self.tenant_user,
            apartment=self.apartment,
            num_occupants=2
        )

    def test_dashboard_view_for_logged_in_tenant(self):
        """Test dashboard dla zalogowanego lokatora"""
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Numer mieszkania')
        self.assertContains(response, 'Czynsz')
        self.assertContains(response, '101')  # Numer mieszkania
        self.assertContains(response, '1500')  # Czynsz

    def test_dashboard_view_redirect_for_anonymous_user(self):
        """Test przekierowania dla niezalogowanego użytkownika"""
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('app:login')}?next=/dashboard/")

    def test_admin_dashboard_view_for_admin(self):
        """Test dashboard administratora"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel Administratora')
        self.assertContains(response, 'Mieszkania')

    def test_admin_dashboard_redirect_for_non_admin(self):
        """Test przekierowania dla nie-administratora"""
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_add_apartment_as_admin(self):
        """Test dodawania mieszkania przez administratora"""
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('app:admin_add_apartment'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ApartmentForm)

        # Dodaj nowe mieszkanie
        apartment_data = {
            'number': '103',
            'floor': 3,
            'area': 70.0,
            'rent': 1700,
            'trash_fee': 70,
            'water_fee': 50,
            'gas_fee': 30
        }
        response = self.client.post(reverse('app:admin_add_apartment'), apartment_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy mieszkanie zostało dodane
        self.assertTrue(Apartment.objects.filter(number='103').exists())

    def test_edit_apartment_as_admin(self):
        """Test edycji mieszkania przez administratora"""
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('app:admin_edit_apartment', args=[self.apartment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ApartmentForm)
        self.assertEqual(response.context['apartment'], self.apartment)

        # Edytuj mieszkanie
        updated_data = {
            'number': '101',
            'floor': 1,
            'area': 55.0,  # Zmiana powierzchni
            'rent': 1600,  # Zmiana czynszu
            'trash_fee': 55,
            'water_fee': 35,
            'gas_fee': 25
        }
        response = self.client.post(
            reverse('app:admin_edit_apartment', args=[self.apartment.pk]),
            updated_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy zmiany zostały zapisane
        self.apartment.refresh_from_db()
        self.assertEqual(float(self.apartment.area), 55.0)
        self.assertEqual(float(self.apartment.rent), 1600.0)

    def test_add_apartment_redirect_for_non_admin(self):
        """Test przekierowania dla nie-administratora przy dodawaniu mieszkania"""
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.post(reverse('app:admin_add_apartment'), {
            'number': '103',
            'floor': 3,
            'area': 70.0,
            'rent': 1700,
            'trash_fee': 70,
            'water_fee': 50,
            'gas_fee': 30
        })
        self.assertEqual(response.status_code, 302)

    def test_payments_view(self):
        """Test widoku płatności lokatora"""
        Payment.objects.create(
            tenant=self.tenant,
            amount=1500,
            date=timezone.now().date(),
            status='paid',
            type='rent'
        )
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:user_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1500')
        self.assertContains(response, 'Opłata została zaksięgowana.')

    def test_payments_view_no_data(self):
        """Test widoku płatności bez danych"""
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:user_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Brak płatności')

    def test_ticket_creation(self):
        """Test tworzenia zgłoszenia"""
        self.client.login(username='tenant', password='tenantpass')

        response = self.client.post(reverse('app:add_ticket'), {
            'title': 'Problem z ogrzewaniem',
            'description': 'Brak ciepła w mieszkaniu',
            'status': 'new'
        })

        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Problem z ogrzewaniem')
        self.assertEqual(ticket.tenant, self.tenant)
        self.assertEqual(ticket.status, 'new')

    def test_tickets_view(self):
        """Test widoku zgłoszeń"""
        Ticket.objects.create(
            tenant=self.tenant,
            title='Test zgłoszenie',
            description='Opis testowego zgłoszenia',
            status='new'
        )

        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test zgłoszenie')


class EBOKApartmentTests(TestCase):
    """Testy dla zarządzania mieszkaniami"""

    def setUp(self):
        self.client = Client()
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

    def test_add_apartment(self):
        """Test dodawania mieszkania"""
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('app:admin_add_apartment'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ApartmentForm)

        # Dodaj mieszkanie
        apartment_data = {
            'number': '102',
            'floor': 2,
            'area': 60.0,
            'rent': 1600.00,
            'trash_fee': 60.00,
            'water_fee': 40.00,
            'gas_fee': 25.00
        }
        response = self.client.post(reverse('app:admin_add_apartment'), apartment_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy mieszkanie zostało dodane do bazy
        self.assertTrue(Apartment.objects.filter(number='102').exists())
        apartment = Apartment.objects.get(number='102')
        self.assertEqual(apartment.floor, 2)
        self.assertEqual(float(apartment.area), 60.0)
        self.assertEqual(float(apartment.rent), 1600.00)

    def test_csv_export(self):
        """Test eksportu mieszkań do CSV"""
        # Utwórz mieszkania do eksportu
        Apartment.objects.create(
            number='101', floor=1, area=50.0,
            rent=1500.00, trash_fee=50.00, water_fee=30.00, gas_fee=20.00
        )
        Apartment.objects.create(
            number='102', floor=2, area=60.0,
            rent=1600.00, trash_fee=60.00, water_fee=40.00, gas_fee=25.00
        )

        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app:export_apartment_csv'))

        # Sprawdź odpowiedź
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="apartments.csv"')

        # Sprawdź zawartość CSV
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(content.splitlines())
        rows = list(csv_reader)

        self.assertEqual(len(rows), 3)  # Nagłówek + 2 mieszkania
        self.assertEqual(rows[0], ['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee'])
        self.assertEqual(rows[1][0], '101')  # Numer pierwszego mieszkania
        self.assertEqual(rows[2][0], '102')  # Numer drugiego mieszkania

    def test_csv_import(self):
        """Test importu mieszkań z CSV"""
        self.client.login(username='admin', password='adminpass')

        # Utwórz plik CSV w pamięci
        csv_content = "number,floor,area,rent,trash_fee,water_fee,gas_fee\n101,1,50.5,1500,50,30,20\n102,2,60.0,1600,60,40,25"
        csv_file = io.StringIO(csv_content)

        from django.core.files.uploadedfile import SimpleUploadedFile
        uploaded_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )

        response = self.client.post(reverse('app:import_apartment_csv'), {
            'csv_file': uploaded_file
        }, follow=True)

        # Sprawdź przekierowanie
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy mieszkania zostały zaimportowane
        self.assertEqual(Apartment.objects.count(), 2)
        self.assertTrue(Apartment.objects.filter(number='101').exists())
        self.assertTrue(Apartment.objects.filter(number='102').exists())


class EBOKTenantTests(TestCase):
    """Testy dla zarządzania lokatorami"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.apartment = Apartment.objects.create(
            number='101',
            floor=1,
            area=50.5,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )

    def test_add_tenant(self):
        """Test dodawania lokatora"""
        self.client.login(username='admin', password='adminpass')

        # Sprawdź wyświetlanie formularza
        response = self.client.get(reverse('app:admin_add_tenant'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], TenantForm)

        # Dodaj lokatora
        tenant_data = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'jan.kowalski@example.com',
            'phone': '123456789',
            'apartment': self.apartment.id,
            'num_occupants': 3
        }
        response = self.client.post(reverse('app:admin_add_tenant'), tenant_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy użytkownik został utworzony
        self.assertTrue(User.objects.filter(email='jan.kowalski@example.com').exists())
        new_user = User.objects.get(email='jan.kowalski@example.com')

        # Sprawdź czy lokator został dodany do bazy
        self.assertTrue(Tenant.objects.filter(user=new_user).exists())


class EBOKPaymentTests(TestCase):
    """Testy dla zarządzania płatnościami"""

    def setUp(self):
        self.client = Client()
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
            number='101',
            floor=1,
            area=50.5,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )
        self.tenant = Tenant.objects.create(
            user=self.tenant_user,
            apartment=self.apartment,
            num_occupants=2
        )
        self.payment = Payment.objects.create(
            tenant=self.tenant,
            date=timezone.now().date(),
            amount=1500.00,
            type='rent',
            status='pending'
        )

    def test_admin_payments_view(self):
        """Test widoku płatności dla administratora"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app:admin_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_payments.html')

    def test_add_payment(self):
        """Test dodawania płatności"""
        self.client.login(username='admin', password='adminpass')

        payment_data = {
            'tenant': self.tenant.id,
            'date': timezone.now().date(),
            'amount': 1600.00,
            'type': 'rent',
            'status': 'paid'
        }
        response = self.client.post(reverse('app:admin_add_payment'), payment_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy płatność została dodana
        self.assertTrue(Payment.objects.filter(amount=1600.00).exists())

    def test_edit_payment(self):
        """Test edycji płatności"""
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('app:admin_edit_payment', args=[self.payment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], PaymentForm)

        # Edytuj płatność
        updated_data = {
            'tenant': self.tenant.id,
            'date': self.payment.date,
            'amount': 1500.00,
            'type': 'rent',
            'status': 'paid'  # Zmiana statusu
        }
        response = self.client.post(
            reverse('app:admin_edit_payment', args=[self.payment.id]),
            updated_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy status został zmieniony
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'paid')


class EBOKSensorTests(TestCase):
    """Testy dla nowych funkcjonalności sensorów"""

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
        self.sensor = Sensor.objects.create(
            name='Temperatura salon',
            sensor_type='temperature',
            apartment=self.apartment,
            location='salon',
            is_active=True
        )

    def test_sensor_creation(self):
        """Test tworzenia sensora"""
        self.assertEqual(self.sensor.name, 'Temperatura salon')
        self.assertEqual(self.sensor.sensor_type, 'temperature')
        self.assertEqual(self.sensor.apartment, self.apartment)
        self.assertTrue(self.sensor.is_active)

    def test_sensor_reading_creation(self):
        """Test tworzenia odczytu sensora"""
        reading = SensorReading.objects.create(
            sensor=self.sensor,
            value=22.5,
            unit='°C'
        )

        self.assertEqual(reading.sensor, self.sensor)
        self.assertEqual(reading.value, 22.5)
        self.assertEqual(reading.unit, '°C')

    def test_utility_consumption_creation(self):
        """Test tworzenia wpisu zużycia mediów"""
        consumption = UtilityConsumption.objects.create(
            apartment=self.apartment,
            utility_type='water',
            consumption=15.5,
            month=timezone.now().date(),
            cost_per_unit=Decimal('3.50'),
            total_cost=Decimal('54.25')
        )

        self.assertEqual(consumption.apartment, self.apartment)
        self.assertEqual(consumption.utility_type, 'water')
        self.assertEqual(consumption.consumption, 15.5)
        self.assertEqual(consumption.total_cost, Decimal('54.25'))


class EBOKURLTests(TestCase):
    """Testy dla wszystkich URL"""

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
            number='101',
            floor=1,
            area=50.5,
            rent=1500.00,
            trash_fee=50.00,
            water_fee=30.00,
            gas_fee=20.00
        )

    def test_admin_urls(self):
        """Test wszystkich URL administratora"""
        self.client.login(username='admin', password='adminpass')

        admin_urls = [
            'app:admin_dashboard',
            'app:admin_add_apartment',
            'app:admin_add_tenant',
            'app:admin_payments',
            'app:admin_add_payment',
            'app:admin_tickets',
            'app:export_apartment_csv',
            'app:import_apartment_csv',
        ]

        for url_name in admin_urls:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertIn(response.status_code, [200, 302])  # 200 OK lub 302 Redirect

    def test_user_urls(self):
        """Test URL dostępnych dla lokatorów"""
        self.client.login(username='tenant', password='tenantpass')

        user_urls = [
            'app:dashboard',
            'app:user_payments',
            'app:tickets',
            'app:add_ticket',
        ]

        for url_name in user_urls:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertIn(response.status_code, [200, 302])

    def test_edit_apartment_url(self):
        """Test URL edycji mieszkania"""
        self.client.login(username='admin', password='adminpass')

        response = self.client.get(reverse('app:admin_edit_apartment', args=[self.apartment.pk]))
        self.assertEqual(response.status_code, 200)
