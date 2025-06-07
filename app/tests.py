# Plik pomocniczy do uruchamiania testów
# Zawiera podstawowe testy potrzebne do weryfikacji działania systemu

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import datetime
import io, csv

# Import modeli aplikacji
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption, MaintenanceRequest, BuildingAlert


class BasicTest(TestCase):
    """Najbardziej podstawowe testy funkcjonalności"""

    def test_basic(self):
        """Podstawowy test połączenia"""
        self.assertEqual(1 + 1, 2)

    def test_login_page(self):
        """Test czy strona logowania jest dostępna"""
        response = self.client.get(reverse('app:login'))
        self.assertEqual(response.status_code, 200)


class ModelTest(TestCase):
    """Testy modeli aplikacji"""

    def setUp(self):
        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number="101",
            floor=1,
            area=50.0,
            rent=1000.00,
            trash_fee=100.00,
            water_fee=150.00,
            gas_fee=200.00
        )

        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        # Tworzenie testowego najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment,
            phone_number="123456789",
            num_occupants=2
        )

        # Tworzenie testowej płatności
        self.payment = Payment.objects.create(
            tenant=self.tenant,
            amount=1000.00,
            type=Payment.RENT,
            status=Payment.PENDING
        )

        # Tworzenie testowego zgłoszenia
        self.ticket = Ticket.objects.create(
            tenant=self.tenant,
            title="Test ticket",
            description="Test description",
            status=Ticket.NEW,
            priority="medium"
        )

    def test_apartment_model(self):
        """Test modelu Apartment"""
        self.assertEqual(str(self.apartment), "Mieszkanie 101")
        self.assertEqual(self.apartment.total_fees(), 1450.00)

    def test_tenant_model(self):
        """Test modelu Tenant"""
        self.assertEqual(str(self.tenant), "Test User")
        self.assertEqual(self.tenant.apartment, self.apartment)

    def test_payment_model(self):
        """Test modelu Payment"""
        self.assertIn("Płatność: 1000.00 zł", str(self.payment))
        self.assertEqual(self.payment.tenant, self.tenant)
        self.assertEqual(self.payment.status, Payment.PENDING)

    def test_ticket_model(self):
        """Test modelu Ticket"""
        self.assertEqual(str(self.ticket), "Test ticket (Nowe)")
        self.assertEqual(self.ticket.tenant, self.tenant)
        self.assertEqual(self.ticket.status, Ticket.NEW)


class ViewTest(TestCase):
    """Testy widoków aplikacji"""

    def setUp(self):
        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="test@example.com"
        )

        # Tworzenie testowego administratora
        self.admin_user = User.objects.create_user(
            username="admin",
            password="adminpass",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True
        )

    def test_login_view(self):
        """Test widoku logowania"""
        response = self.client.get(reverse('app:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_successful(self):
        """Test udanego logowania"""
        response = self.client.post(reverse('app:login'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertRedirects(response, reverse('app:dashboard'))

    def test_login_failed(self):
        """Test nieudanego logowania"""
        response = self.client.post(reverse('app:login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        # Pozostajemy na stronie logowania po nieudanej próbie
        self.assertTemplateUsed(response, 'login.html')
