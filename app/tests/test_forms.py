from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Ticket
from app.forms import ApartmentForm, TenantForm, TicketForm, PaymentForm

class ApartmentFormTests(TestCase):
    """Testy dla formularza ApartmentForm"""

    def test_valid_apartment_form(self):
        """Test poprawnego formularza mieszkania"""
        form_data = {
            'number': '401',
            'floor': 4,
            'area': 60.0,
            'rent': 1700.00,
            'trash_fee': 65.00,
            'water_fee': 45.00,
            'gas_fee': 35.00,
            'description': 'Przestronne mieszkanie z balkonem'
        }
        form = ApartmentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_apartment_form(self):
        """Test niepoprawnego formularza mieszkania"""
        # Brak wymaganego pola 'number'
        form_data = {
            'floor': 4,
            'area': 60.0,
            'rent': 1700.00,
            'trash_fee': 65.00,
            'water_fee': 45.00,
            'gas_fee': 35.00
        }
        form = ApartmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('number', form.errors)

    def test_negative_values_apartment_form(self):
        """Test formularza z ujemnymi wartościami"""
        form_data = {
            'number': '402',
            'floor': 4,
            'area': -60.0,  # ujemna wartość
            'rent': 1700.00,
            'trash_fee': 65.00,
            'water_fee': 45.00,
            'gas_fee': 35.00
        }
        form = ApartmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('area', form.errors)

class TenantFormTests(TestCase):
    """Testy dla formularza TenantForm"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.apartment = Apartment.objects.create(
            number='403',
            floor=4,
            area=65.0,
            rent=1800.00,
            trash_fee=70.00,
            water_fee=50.00,
            gas_fee=40.00
        )

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_valid_tenant_form(self):
        """Test poprawnego formularza najemcy"""
        form_data = {
            'user': self.user.id,
            'apartment': self.apartment.id,
            'phone_number': '123456789',
            'num_occupants': 2,
            'move_in_date': '2023-01-01'
        }
        form = TenantForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_tenant_form(self):
        """Test niepoprawnego formularza najemcy"""
        # Brak wymaganego pola 'user'
        form_data = {
            'apartment': self.apartment.id,
            'phone_number': '123456789',
            'num_occupants': 2
        }
        form = TenantForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('user', form.errors)

class TicketFormTests(TestCase):
    """Testy dla formularza TicketForm"""

    def test_valid_ticket_form(self):
        """Test poprawnego formularza zgłoszenia"""
        form_data = {
            'title': 'Awaria klimatyzacji',
            'description': 'Klimatyzacja nie chłodzi',
            'priority': 'medium'
        }
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_ticket_form(self):
        """Test niepoprawnego formularza zgłoszenia"""
        form_data = {
            'description': 'Klimatyzacja nie chłodzi',
            'priority': 'medium'
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_empty_description_ticket_form(self):
        """Test formularza zgłoszenia z pustym opisem"""
        form_data = {
            'title': 'Awaria klimatyzacji',
            'description': '',  # pusty opis
            'priority': 'medium'
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

class PaymentFormTests(TestCase):
    """Testy dla formularza PaymentForm"""

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.apartment = Apartment.objects.create(
            number='404',
            floor=4,
            area=70.0,
            rent=1900.00,
            trash_fee=75.00,
            water_fee=55.00,
            gas_fee=45.00
        )

        self.user = User.objects.create_user(
            username='paymentuser',
            password='paymentpass',
            email='payment@example.com'
        )

        self.tenant = Tenant.objects.create(
            user=self.user,
            apartment=self.apartment
        )

    def test_valid_payment_form(self):
        """Test poprawnego formularza płatności"""
        form_data = {
            'tenant': self.tenant.id,
            'amount': 1900.00,
            'type': 'rent',
            'status': 'pending',
            'date': '2023-01-15',
            'description': 'Czynsz za styczeń 2023'
        }
        form = PaymentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_payment_form(self):
        """Test niepoprawnego formularza płatności"""
        # Brak wymaganego pola 'amount'
        form_data = {
            'tenant': self.tenant.id,
            'type': 'rent',
            'status': 'pending',
            'date': '2023-01-15'
        }
        form = PaymentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_negative_amount_payment_form(self):
        """Test formularza płatności z ujemną kwotą"""
        form_data = {
            'tenant': self.tenant.id,
            'amount': -1900.00,  # ujemna kwota
            'type': 'rent',
            'status': 'pending',
            'date': '2023-01-15'
        }
        form = PaymentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

