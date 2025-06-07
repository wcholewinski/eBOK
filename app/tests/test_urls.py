from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from app.models import Apartment, Tenant
from app import views

class EBOKURLTests(TestCase):
    """Testy URLi aplikacji eBOK"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            password='admin', 
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
            apartment=self.apartment
        )

    def test_admin_urls(self):
        """Test URLi panelu administracyjnego"""
        urls = [
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_payments'),
            reverse('app:admin_tickets'),
            reverse('app:analytics_dashboard'),
            reverse('app:consumption_trends'),
            reverse('app:sensor_management'),
            reverse('app:alerts_management'),
        ]

        # Sprawdzenie czy admin ma dostęp do wszystkich adresów
        self.client.login(username='admin', password='admin')
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # Sprawdzenie czy tenant nie ma dostępu do adresów admina
        self.client.login(username='tenant', password='tenantpass')
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_user_urls(self):
        """Test URLi dla użytkownika"""
        urls = [
            reverse('app:dashboard'),
            reverse('app:user_payments'),
            reverse('app:tickets'),
            reverse('app:add_ticket'),
        ]

        # Sprawdzenie czy tenant ma dostęp do swoich adresów
        self.client.login(username='tenant', password='tenantpass')
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_url_resolves(self):
        """Test poprawności rozwiązywania URLi"""
        # Sprawdzenie czy URLe prowadzą do odpowiednich widoków
        self.assertEqual(resolve(reverse('app:dashboard')).func, views.dashboard)
        self.assertEqual(resolve(reverse('app:admin_dashboard')).func, views.admin_dashboard)
        self.assertEqual(resolve(reverse('app:user_payments')).func, views.payments)
        self.assertEqual(resolve(reverse('app:tickets')).func, views.tickets)
        self.assertEqual(resolve(reverse('app:add_ticket')).func, views.add_ticket)
        self.assertEqual(resolve(reverse('app:admin_add_apartment')).func, views.add_apartment)
