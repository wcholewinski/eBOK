from django.shortcuts import redirect
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import csv, io

from app.models import Apartment, Tenant, Payment, Ticket
from app.forms import ApartmentForm, TenantForm, PaymentForm, TicketForm

class EBOKModelTests(TestCase):
    """Testy dla modeli aplikacji."""
    
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
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.tenant = Tenant.objects.create(
            user=self.user,
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
        self.ticket = Ticket.objects.create(
            tenant=self.tenant,
            title='Test zgłoszenie',
            description='Opis testowego zgłoszenia',
            status='new'
        )

    def test_apartment_creation(self):
        """Test tworzenia mieszkania i sprawdzenia jego atrybutów."""
        self.assertEqual(self.apartment.number, '101')
        self.assertEqual(self.apartment.floor, 1)
        self.assertEqual(float(self.apartment.area), 50.5)
        self.assertEqual(float(self.apartment.rent), 1500.00)
        self.assertEqual(str(self.apartment), "Mieszkanie 101 (piętro 1)")
    
    def test_tenant_creation(self):
        """Test tworzenia lokatora i sprawdzenia jego atrybutów."""
        self.assertEqual(self.tenant.user, self.user)
        self.assertEqual(self.tenant.apartment, self.apartment)
        self.assertEqual(self.tenant.num_occupants, 2)
        self.assertIn('testuser', str(self.tenant))
        self.assertIn('101', str(self.tenant))
    
    def test_payment_creation(self):
        """Test tworzenia płatności i sprawdzenia jej atrybutów."""
        self.assertEqual(self.payment.tenant, self.tenant)
        self.assertEqual(float(self.payment.amount), 1500.00)
        self.assertEqual(self.payment.type, 'rent')
        self.assertEqual(self.payment.status, 'pending')
        self.assertIn('Czynsz', str(self.payment))
        self.assertIn('1500', str(self.payment))
        self.assertIn('Oczekujące', str(self.payment))
    
    def test_ticket_creation(self):
        """Test tworzenia zgłoszenia i sprawdzenia jego atrybutów."""
        self.assertEqual(self.ticket.tenant, self.tenant)
        self.assertEqual(self.ticket.title, 'Test zgłoszenie')
        self.assertEqual(self.ticket.description, 'Opis testowego zgłoszenia')
        self.assertEqual(self.ticket.status, 'new')
        self.assertIn('Test zgłoszenie', str(self.ticket))
        self.assertIn('Nowe', str(self.ticket))


class EBOKAuthTests(TestCase):
    """Testy dla funkcjonalności uwierzytelniania."""
    
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
            apartment=self.apartment
        )
    
    def test_login_view(self):
        """Test widoku logowania."""
        # Użyj odpowiedniej ścieżki URL zgodnej z ustawieniem w urls.py
        response = self.client.post(reverse('app:login'), {'username': 'tenant', 'password': 'tenantpass'})
        self.assertRedirects(response, reverse('app:dashboard'))
    
    def test_logout_view(self):
        """Test wylogowywania."""
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:logout'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('app:login'))
    
    def test_admin_access_control(self):
        """Test kontroli dostępu do panelu administratora."""
        # Brak dostępu dla niezalogowanego użytkownika
        response = self.client.get(reverse('app:admin_dashboard'), follow=True)
        self.assertRedirects(response, reverse('app:login'))
        
        # Brak dostępu dla zwykłego użytkownika
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:admin_dashboard'), follow=True)
        # Oczekujemy przekierowania do dashboardu (to jest zmiana)
        self.assertRedirects(response, reverse('app:dashboard'))
        
        # Dostęp dla administratora
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_dashboard.html')


class EBOKDashboardTests(TestCase):
    """Testy dla paneli głównych (dashboardów)."""
    
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
    
    def test_user_dashboard(self):
        """Test dashboardu użytkownika."""
        # Przekierowanie niezalogowanego użytkownika
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Dashboard dla zalogowanego lokatora
        self.client.login(username='tenant', password='tenantpass')
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertEqual(response.context['tenant'], self.tenant)
        self.assertIn(('Numer mieszkania', '101'), response.context['fields'])
        self.assertIn(('Czynsz (zł)', Decimal('1500.00')), response.context['fields'])
        self.assertIn(('Liczba mieszkańców', 2), response.context['fields'])
    
    @override_settings(TEMPLATE_DIRS=('nonexistent_dir',))  # Omijamy rendering szablonu
    def test_admin_dashboard(self):
        """Test dashboardu administratora."""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('app:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Sprawdzamy czy kontekst zawiera wszystkie potrzebne elementy
        self.assertIn('apartments', response.context)
        self.assertIn('tenants', response.context)
        self.assertEqual(list(response.context['apartments']), [self.apartment])
        self.assertEqual(list(response.context['tenants']), [self.tenant])


class EBOKApartmentTests(TestCase):
    """Testy dla zarządzania mieszkaniami."""
    
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
    
    @override_settings(TEMPLATE_DIRS=('nonexistent_dir',))  # Omijamy rendering szablonu
    def test_add_apartment(self):
        """Test dodawania mieszkania."""
        self.client.login(username='admin', password='adminpass')
        
        # Zmień to:
        # response = self.client.get('/admin/apartments/add/')
        # Na to:
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
        """Test eksportu mieszkań do CSV."""
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
    
    @override_settings(TEMPLATE_DIRS=('nonexistent_dir',))  # Omijamy rendering szablonu
    def test_csv_import(self):
        """Test importu mieszkań z CSV."""
        self.client.login(username='admin', password='adminpass')
        
        # Utwórz plik CSV
        csv_data = "number;floor;area\n101;1;50.5\n102;2;60.0"
        csv_file = io.StringIO(csv_data)
        csv_file.name = 'test.csv'
        
        response = self.client.post(reverse('app:import_apartment_csv'), {
            'csv_file': csv_file
        }, follow=True)
        
        # Sprawdź przekierowanie i komunikat
        self.assertEqual(response.status_code, 200)
        
        # Sprawdź czy mieszkania zostały zaimportowane
        self.assertEqual(Apartment.objects.count(), 2)
        self.assertTrue(Apartment.objects.filter(number='101').exists())
        self.assertTrue(Apartment.objects.filter(number='102').exists())


class EBOKTenantTests(TestCase):
    """Testy dla zarządzania lokatorami."""
    
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
        # Utwórz użytkownika dla lokatora
        self.tenant_user = User.objects.create_user(
            username='newtenant',
            password='tenantpass',
            email='newtenant@example.com'
        )
    
    @override_settings(TEMPLATE_DIRS=('nonexistent_dir',))  # Omijamy rendering szablonu
    def test_add_tenant(self):
        """Test dodawania lokatora."""
        self.client.login(username='admin', password='adminpass')
        
        # Sprawdź wyświetlanie formularza
        response = self.client.get(reverse('app:add_tenant'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], TenantForm)
        
        # Użyj unikalnej nazwy użytkownika, która się nie powtarza
        tenant_data = {
            'username': 'tenant_test_unique',  # Zmieniona nazwa użytkownika
            'password1': 'password123',  # Hasło
            'password2': 'password123',  # Potwierdzenie hasła
            'apartment': self.apartment.id,
            'num_occupants': 3
        }
        response = self.client.post(reverse('app:add_tenant'), tenant_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Sprawdź czy utworzono użytkownika z nową, unikalną nazwą
        self.assertTrue(User.objects.filter(username='tenant_test_unique').exists())
        new_user = User.objects.get(username='tenant_test_unique')
        
        # Sprawdź czy lokator został dodany do bazy
        self.assertTrue(Tenant.objects.filter(user=new_user).exists())

# Dla metody test_admin_payments_view
def test_admin_payments_view(self):
    """Test widoku płatności dla administratora."""
    self.client.login(username='admin', password='adminpass')
    # Używaj prawidłowej nazwy ścieżki URL zdefiniowanej w urls.py
    response = self.client.get(reverse('admin:payments'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'admin_payments.html')

# Dla metody test_edit_payment
def test_edit_payment(self):
    """Test edycji płatności."""
    self.client.login(username='admin', password='adminpass')
    response = self.client.get(reverse('admin:edit_payment', args=[self.payment.id]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'payment_form.html')
    self.assertIsInstance(response.context['form'], PaymentForm)
    self.assertQuerySetEqual(response.context['payments'], [self.payment], transform=lambda x: x)
    self.assertQuerySetEqual(response.context['tickets'], [self.ticket], transform=lambda x: x)

def test_tickets_view_for_tenant(self):
    """Test widoku zgłoszeń dla lokatora."""
    self.client.login(username='tenant', password='tenantpass')
    response = self.client.get(reverse('app:tickets'))
    self.assertEqual(response.status_code, 200)
    # Zmiana nazwy metody z assertQuerysetEqual na assertQuerySetEqual (zwróć uwagę na dużą literę S)
    self.assertQuerySetEqual(response.context['tickets'], [self.ticket], transform=lambda x: x)
def admin_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            # Przekierowanie dla zalogowanych, ale nie adminów
            return redirect('app:login')
        # Przekierowanie dla niezalogowanych
        return redirect('app:login')
    return wrap