from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from app.models import Apartment, Tenant, Ticket

class PermissionTests(TestCase):
    """Testy uprawnień w systemie"""

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

        # Tworzenie użytkownika obsługi technicznej
        self.tech_user = User.objects.create_user(
            username='techuser',
            password='tech123',
            email='tech@example.com'
        )

        # Tworzenie grupy dla obsługi technicznej
        self.tech_group = Group.objects.create(name='Obsługa techniczna')

        # Dodanie odpowiednich uprawnień do grupy
        ticket_permissions = Permission.objects.filter(codename__contains='ticket')
        for perm in ticket_permissions:
            self.tech_group.permissions.add(perm)

        # Dodanie użytkownika do grupy
        self.tech_user.groups.add(self.tech_group)

        # Tworzenie testowego mieszkania
        self.apartment = Apartment.objects.create(
            number='1001',
            floor=10,
            area=90.0,
            rent=2300.00,
            trash_fee=95.00,
            water_fee=75.00,
            gas_fee=65.00
        )

        # Tworzenie najemcy
        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment
        )

        # Tworzenie zgłoszenia
        self.ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Usterka klimatyzacji',
            description='Klimatyzacja nie działa',
            status='new',
            priority='high'
        )

    def test_admin_access(self):
        """Test dostępu administratora do wszystkich stron"""
        # Logowanie administratora
        self.client.login(username='admin', password='admin123')

        # Lista adresów URL do sprawdzenia
        urls = [
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_payments'),
            reverse('app:admin_tickets'),
            reverse('app:ticket_edit', args=[self.ticket.id]),
            reverse('app:dashboard'),
            reverse('app:user_payments'),
            reverse('app:tickets')
        ]

        # Sprawdzenie dostępu do wszystkich adresów
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_tenant_restricted_access(self):
        """Test ograniczonego dostępu najemcy"""
        # Logowanie najemcy
        self.client.login(username='user', password='user123')

        # Lista adresów URL, do których najemca powinien mieć dostęp
        allowed_urls = [
            reverse('app:dashboard'),
            reverse('app:user_payments'),
            reverse('app:tickets'),
            reverse('app:add_ticket')
        ]

        # Lista adresów URL, do których najemca NIE powinien mieć dostępu
        restricted_urls = [
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_payments'),
            reverse('app:admin_tickets'),
            reverse('app:ticket_edit', args=[self.ticket.id])
        ]

        # Sprawdzenie dostępu do dozwolonych adresów
        for url in allowed_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # Sprawdzenie braku dostępu do zastrzeżonych adresów
        for url in restricted_urls:
            response = self.client.get(url)
            # Powinno przekierować (kod 302) na stronę logowania lub dostęp zabroniony
            self.assertEqual(response.status_code, 302)

    def test_tech_support_access(self):
        """Test dostępu pracownika obsługi technicznej"""
        # Logowanie pracownika obsługi technicznej
        self.client.login(username='techuser', password='tech123')

        # Lista adresów URL, do których pracownik powinien mieć dostęp
        allowed_urls = [
            reverse('app:admin_tickets'),
            reverse('app:ticket_edit', args=[self.ticket.id])
        ]

        # Lista adresów URL, do których pracownik NIE powinien mieć dostępu
        restricted_urls = [
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_payments')
        ]

        # Sprawdzenie dostępu do dozwolonych adresów
        for url in allowed_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # Sprawdzenie braku dostępu do zastrzeżonych adresów
        for url in restricted_urls:
            response = self.client.get(url)
            # Powinno przekierować (kod 302) na stronę logowania lub dostęp zabroniony
            self.assertEqual(response.status_code, 302)

    def test_anonymous_user_access(self):
        """Test dostępu niezalogowanego użytkownika"""
        # Lista adresów URL, do których niezalogowany użytkownik NIE powinien mieć dostępu
        restricted_urls = [
            reverse('app:dashboard'),
            reverse('app:user_payments'),
            reverse('app:tickets'),
            reverse('app:add_ticket'),
            reverse('app:admin_dashboard'),
            reverse('app:admin_add_apartment'),
            reverse('app:admin_payments'),
            reverse('app:admin_tickets'),
            reverse('app:ticket_edit', args=[self.ticket.id])
        ]

        # Sprawdzenie braku dostępu do zastrzeżonych adresów
        for url in restricted_urls:
            response = self.client.get(url)
            # Powinno przekierować (kod 302) na stronę logowania
            self.assertEqual(response.status_code, 302)
            # Sprawdzenie czy URL przekierowania zawiera 'login'
            self.assertIn('login', response.url)

    def test_tenant_can_only_access_own_data(self):
        """Test dostępu najemcy tylko do własnych danych"""
        # Utworzenie drugiego mieszkania i najemcy
        second_apartment = Apartment.objects.create(
            number='1002',
            floor=10,
            area=95.0,
            rent=2400.00,
            trash_fee=100.00,
            water_fee=80.00,
            gas_fee=70.00
        )

        second_user = User.objects.create_user(
            username='second_user',
            password='second123',
            email='second@example.com'
        )

        second_tenant = Tenant.objects.create(
            user=second_user,
            apartment=second_apartment
        )

        second_ticket = Ticket.objects.create(
            tenant=second_tenant,
            title='Usterka drzwi',
            description='Drzwi wejściowe nie zamykają się prawidłowo',
            status='new',
            priority='medium'
        )

        # Logowanie pierwszego najemcy
        self.client.login(username='user', password='user123')

        # Próba dostępu do szczegółów zgłoszenia drugiego najemcy
        response = self.client.get(reverse('app:ticket_details', args=[second_ticket.id]))

        # Sprawdzenie braku dostępu lub przekierowania
        self.assertNotEqual(response.status_code, 200)
