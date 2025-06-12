from django.utils import timezone

def calculate_total_due(tenant):
    """Oblicza łączną kwotę do zapłaty dla najemcy"""
    from .models import Payment
    pending_payments = Payment.objects.filter(tenant=tenant, status='pending')
    return sum(payment.amount for payment in pending_payments)

def is_payment_overdue(payment):
    """Sprawdza czy płatność jest zaległa"""
    return payment.status == 'pending' and payment.date < timezone.now().date()

def get_overdue_days(payment):
    """Zwraca liczbę dni opóźnienia dla płatności"""
    if not is_payment_overdue(payment):
        return 0
    return (timezone.now().date() - payment.date).days

def format_currency(amount):
    """Formatuje kwotę jako walutę"""
    return f"{amount:.2f} PLN"

def get_status_badge(status, entity_type='payment'):
    """Zwraca klasę badge dla statusu

    Args:
        status: Status elementu
        entity_type: Typ elementu ('payment' lub 'ticket')
    """
    if entity_type == 'payment':
        badges = {
            'paid': 'bg-success',
            'pending': 'bg-warning'
        }
    else:  # ticket
        badges = {
            'new': 'bg-danger',
            'in_progress': 'bg-warning',
            'closed': 'bg-success'
        }

    return badges.get(status, 'bg-secondary')
