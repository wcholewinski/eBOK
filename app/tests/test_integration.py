from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption
import datetime
import json

class WorkflowTests(TestCase):
    """Testy integracyjne dla przepływów pracy"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.client = Client()

        # Tworzenie administratora
        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )

        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Jan',
            last_name='Kowalski'
        )

        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number='501',
            floor=5,
            area=60.0,
            rent=1700.00,
            trash_fee=65.00,
            water_fee=45.00,
            gas_fee=35.00
        )

        # Tworzenie najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment,
            phone_number='123456789',
            num_occupants=2
        )

    def test_user_workflow(self):
        """Test przepływu pracy najemcy"""
        # Logowanie użytkownika
        self.client.login(username='testuser', password='testpass123')

        # Sprawdzenie dashboardu
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Twoje mieszkanie')

        # Utworzenie płatności
        payment = Payment.objects.create(
            tenant=self.tenant,
            amount=1700.00,
            type='rent',
            status='pending',
            date=datetime.datetime.now().date()
        )

        # Sprawdzenie widoku płatności
        response = self.client.get(reverse('app:user_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1700.00')

        # Utworzenie zgłoszenia
        response = self.client.post(reverse('app:add_ticket'), {
            'title': 'Awaria ogrzewania',
            'description': 'Grzejnik nie działa prawidłowo',
            'priority': 'high'
        })
        self.assertEqual(response.status_code, 302)

        # Sprawdzenie widoku zgłoszeń
        response = self.client.get(reverse('app:tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Awaria ogrzewania')

    def test_admin_workflow(self):
        """Test przepływu pracy administratora"""
        # Logowanie administratora
        self.client.login(username='admin', password='admin123')

        # Sprawdzenie dashboardu administratora
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel administratora')

        # Dodanie nowego mieszkania
        response = self.client.post(reverse('app:admin_add_apartment'), {
            'number': '601',
            'floor': 6,
            'area': 70.0,
            'rent': 1900.00,
            'trash_fee': 75.00,
            'water_fee': 55.00,
            'gas_fee': 45.00
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Apartment.objects.filter(number='601').exists())

        # Dodanie zgłoszenia dla testów
        ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Awaria instalacji elektrycznej',
            description='Brak prądu w mieszkaniu',
            status='new',
            priority='high'
        )

        # Sprawdzenie widoku zgłoszeń administratora
        response = self.client.get(reverse('app:admin_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Awaria instalacji elektrycznej')

        # Aktualizacja statusu zgłoszenia
        response = self.client.post(reverse('app:ticket_edit', args=[ticket.id]), {
            'title': ticket.title,
            'description': ticket.description,
            'status': 'in_progress',
            'priority': ticket.priority
        })
        self.assertEqual(response.status_code, 302)

        # Sprawdzenie czy status został zaktualizowany
        updated_ticket = Ticket.objects.get(id=ticket.id)
        self.assertEqual(updated_ticket.status, 'in_progress')

    def test_analytics_view(self):
        """Test widoku analityki"""
        # Logowanie administratora
        self.client.login(username='admin', password='admin123')

        # Sprawdzenie widoku analityki
        response = self.client.get(reverse('app:analytics_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Sprawdzenie widoku trendów zużycia
        response = self.client.get(reverse('app:consumption_trends'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trendy zużycia mediów')
