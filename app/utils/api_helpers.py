from django.utils import timezone
from django.db import models
from app.models import Apartment, Tenant, Payment, Ticket

def get_admin_stats():
    """Pobiera podstawowe statystyki dla panelu administratora."""
    # Statystyki mieszkań
    total_apartments = Apartment.objects.count()
    occupied_apartments = Tenant.objects.values('apartment').distinct().count()
    vacancy_rate = 0 if total_apartments == 0 else round(((total_apartments - occupied_apartments) / total_apartments) * 100, 1)

    # Statystyki finansowe
    total_rent = Apartment.objects.filter(tenants__isnull=False).aggregate(sum=models.Sum('rent'))['sum'] or 0

    # Zaległe płatności
    overdue_payments = Payment.objects.filter(status='pending', date__lt=timezone.now().date()).count()

    # Zgłoszenia
    tickets = {
        'new': Ticket.objects.filter(status='new').count(),
        'in_progress': Ticket.objects.filter(status='in_progress').count(),
        'closed': Ticket.objects.filter(status='closed').count()
    }

    return {
        'total_apartments': total_apartments,
        'occupied_apartments': occupied_apartments,
        'vacancy_rate': vacancy_rate,
        'total_rent': total_rent,
        'overdue_payments': overdue_payments,
        'maintenance_requests': tickets  # Zachowanie zgodności ze zmienną używaną w szablonach
    }

def get_tenant_stats(tenant_id):
    """Pobiera statystyki dla najemcy."""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return {'error': f'Najemca o ID {tenant_id} nie istnieje'}

    apartment = tenant.apartment
    payments = Payment.objects.filter(tenant=tenant).order_by('-date')[:10]  # Tylko 10 ostatnich płatności

    return {
        'tenant': {
            'name': tenant.user.get_full_name() or tenant.user.username,
            'email': tenant.user.email,
            'phone': tenant.phone_number
        },
        'apartment': {
            'number': apartment.number,
            'floor': apartment.floor,
            'area': apartment.area,
            'rent': apartment.rent,
            'total_fees': apartment.total_fees()
        },
        'payments': list(payments.values('date', 'amount', 'type', 'status'))
    }
