from django.utils import timezone
from datetime import timedelta


def calculate_total_due(tenant):
    """Oblicza łączną kwotę do zapłaty dla najemcy"""
    from .models import Payment

    # Pobierz wszystkie niezapłacone płatności
    pending_payments = Payment.objects.filter(
        tenant=tenant,
        status='pending'
    )

    # Sumuj kwoty
    total = sum(payment.amount for payment in pending_payments)

    return total


def is_payment_overdue(payment):
    """Sprawdza czy płatność jest zaległa"""
    if payment.status == 'pending' and payment.date < timezone.now().date():
        return True
    return False


def get_overdue_days(payment):
    """Zwraca liczbę dni opóźnienia dla płatności"""
    if not is_payment_overdue(payment):
        return 0

    return (timezone.now().date() - payment.date).days


def format_currency(amount):
    """Formatuje kwotę jako walutę"""
    return f"{amount:.2f} PLN"


def get_payment_status_badge(status):
    """Zwraca klasę badge dla statusu płatności"""
    if status == 'paid':
        return 'bg-success'
    elif status == 'pending':
        return 'bg-warning'
    else:
        return 'bg-secondary'


def get_ticket_status_badge(status):
    """Zwraca klasę badge dla statusu zgłoszenia"""
    if status == 'new':
        return 'bg-danger'
    elif status == 'in_progress':
        return 'bg-warning'
    elif status == 'closed':
        return 'bg-success'
    else:
        return 'bg-secondary'
