from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment, Ticket
import csv
import io
from datetime import datetime

class UserViewsTests(TestCase):
    """Testy widoków dla zwykłych użytkowników"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.client = Client()

        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number='201',
            floor=2,
            area=55.0,
            rent=1600.00,
            trash_fee=60.00,
            water_fee=40.00,
            gas_fee=30.00
        )

        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Jan',
            last_name='Kowalski'
        )

        # Tworzenie najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment,
            phone_number='123456789',
            num_occupants=2
        )

        # Tworzenie testowej płatności
        self.payment = Payment.objects.create(
            tenant=self.tenant,
            amount=1600.00,
            type='rent',
            status='pending',
            date=datetime.now().date()
        )

        # Tworzenie testowego zgłoszenia
        self.ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Awaria ogrzewania',
            description='Grzejnik nie działa prawidłowo',
            status='new',
            priority='high'
        )

    def test_dashboard_view(self):
        """Test widoku dashboard dla zalogowanego użytkownika"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertEqual(response.context['tenant'], self.tenant)
        self.assertEqual(response.context['apartment'], self.apartment)

    def test_dashboard_view_redirect_for_anonymous(self):
        """Test przekierowania dla niezalogowanego użytkownika"""
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('app:login')}?next=/dashboard/")

    def test_payments_view(self):
        """Test widoku płatności dla zalogowanego użytkownika"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('app:user_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments.html')
        self.assertIn(self.payment, response.context['payments'])

    def test_tickets_view(self):
        """Test widoku zgłoszeń dla zalogowanego użytkownika"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('app:tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets.html')
        self.assertIn(self.ticket, response.context['tickets'])

    def test_add_ticket_view(self):
        """Test widoku dodawania zgłoszenia"""
        self.client.login(username='testuser', password='testpass123')
        ticket_data = {
            'title': 'Awaria prądu',
            'description': 'Brak prądu w mieszkaniu',
            'priority': 'high'
        }
        response = self.client.post(reverse('app:add_ticket'), ticket_data)
        self.assertRedirects(response, reverse('app:tickets'))
        self.assertTrue(Ticket.objects.filter(title='Awaria prądu').exists())

class AdminViewsTests(TestCase):
    """Testy widoków dla administratorów"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.client = Client()

        # Tworzenie administratora
        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )

        # Tworzenie zwykłego użytkownika
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            email='user@example.com'
        )

        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number='301',
            floor=3,
            area=65.0,
            rent=1800.00,
            trash_fee=70.00,
            water_fee=50.00,
            gas_fee=40.00
        )

        # Tworzenie najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment
        )

        # Tworzenie testowej płatności
        self.payment = Payment.objects.create(
            tenant=self.tenant,
            amount=1800.00,
            type='rent',
            status='pending',
            date=datetime.now().date()
        )

        # Tworzenie testowego zgłoszenia
        self.ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Awaria instalacji wodnej',
            description='Wyciek wody w łazience',
            status='new',
            priority='high'
        )

    def test_admin_dashboard_view(self):
        """Test widoku panelu administratora"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/admin_dashboard.html')
        self.assertIn(self.apartment, response.context['apartments'])

    def test_add_apartment_view(self):
        """Test widoku dodawania mieszkania"""
        self.client.login(username='admin', password='admin123')
        apartment_data = {
            'number': '302',
            'floor': 3,
            'area': 70.0,
            'rent': 1900.00,
            'trash_fee': 75.00,
            'water_fee': 55.00,
            'gas_fee': 45.00
        }
        response = self.client.post(reverse('app:admin_add_apartment'), apartment_data)
        self.assertRedirects(response, reverse('app:admin_dashboard'))
        self.assertTrue(Apartment.objects.filter(number='302').exists())

    def test_admin_payments_view(self):
        """Test widoku płatności dla administratora"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('app:admin_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/admin_payments.html')
        self.assertIn(self.payment, response.context['payments'])

    def test_admin_tickets_view(self):
        """Test widoku zgłoszeń dla administratora"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('app:admin_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/admin_tickets.html')
        self.assertIn(self.ticket, response.context['tickets'])

    def test_csv_export(self):
        """Test eksportu danych do CSV"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('app:export_apartment_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        self.assertEqual(rows[0], ['Numer', 'Piętro', 'Powierzchnia', 'Czynsz', 'Opłata za śmieci', 'Opłata za wodę', 'Opłata za gaz'])
