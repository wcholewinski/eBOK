from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment, Ticket
from datetime import datetime, timedelta

# Funkcje pomocnicze do tworzenia obiektów testowych

def create_admin_user():
    """Tworzy użytkownika administratora"""
    return User.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@example.com'
    )

def create_regular_user():
    """Tworzy zwykłego użytkownika"""
    return User.objects.create_user(
        username='user',
        password='user123',
        email='user@example.com',
        first_name='Jan',
        last_name='Kowalski'
    )

def create_apartment():
    """Tworzy mieszkanie"""
    return Apartment.objects.create(
        number='1201',
        floor=12,
        area=110.0,
        rent=2600.00,
        trash_fee=110.00,
        water_fee=90.00,
        gas_fee=80.00
    )

def create_tenant(user=None, apartment=None):
    """Tworzy najemcę"""
    if user is None:
        user = create_regular_user()
    if apartment is None:
        apartment = create_apartment()
    return Tenant.objects.create(
        user=user,
        apartment=apartment,
        phone_number='123456789',
        num_occupants=2
    )

def create_payment(tenant=None):
    """Tworzy płatność"""
    if tenant is None:
        tenant = create_tenant()
    return Payment.objects.create(
        tenant=tenant,
        amount=2600.00,
        type='rent',
        status='pending',
        date=datetime.now().date()
    )

def create_ticket(tenant=None):
    """Tworzy zgłoszenie"""
    if tenant is None:
        tenant = create_tenant()
    return Ticket.objects.create(
        tenant=tenant,
        title='Awaria prądu',
        description='Brak prądu w całym mieszkaniu',
        status='new',
        priority='high'
    )
