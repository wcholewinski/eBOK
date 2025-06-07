from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.urls import reverse
def admin_required(view_func):
    """Sprawdza czy użytkownik jest administratorem"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect(reverse('app:dashboard'))
    return login_required(_wrapped_view)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.decorators import admin_required
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption

@admin_required
def admin_dashboard(request):
    """Główny dashboard administratora"""
    apartments_count = Apartment.objects.count()
    tenants_count = Tenant.objects.count()
    active_tickets = Ticket.objects.exclude(status='closed').count()
    pending_payments = Payment.objects.filter(status='pending').count()

    context = {
        'apartments_count': apartments_count,
        'tenants_count': tenants_count,
        'active_tickets': active_tickets,
        'pending_payments': pending_payments,
        'title': 'Panel administratora'
    }

    return render(request, 'admin/dashboard.html', context)