from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.migrations import writer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth import logout

import csv


from .models import Apartment, Tenant, Payment, Ticket
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm, TicketForm

# alias
admin_required = user_passes_test(lambda u: u.is_superuser)

# ─── PANEL ADMINA ───────────────────────────────────────
@admin_required
def admin_dashboard(request):
    context = {
        'apartments': Apartment.objects.all(),
        'tenants': Tenant.objects.select_related('user', 'apartment'),
    }
    return render(request, 'admin_dashboard.html', context)

@admin_required
def add_apartment(request):
    form = ApartmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('app:admin:dashboard')
    return render(request, 'add_apartment.html', {'form': form})

@admin_required
def add_tenant(request):
    form = TenantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('app:admin:dashboard')
    return render(request, 'add_tenant.html', {'form': form})

# ─── PŁATNOŚCI ───────────────────────────────────────────
@login_required
def payments(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    payments = tenant.payments.all()
    return render(request, 'payments.html', {'payments': payments})

@admin_required
def admin_payments(request):
    payments = Payment.objects.select_related('tenant__user')
    return render(request, 'admin_payments.html', {'payments': payments})

@admin_required
def payment_form(request, pk=None):
    instance = get_object_or_404(Payment, pk=pk) if pk else None
    form = PaymentForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('app:admin:payments')
    return render(request, 'payment_form.html', {'form': form, 'is_edit': bool(pk)})

# ─── ZGŁOSZENIA ─────────────────────────────────────────
@login_required
def tickets(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    return render(request, 'tickets.html', {'tickets': tenant.tickets.all()})

@login_required
def ticket_add(request):
    form = TicketForm(request.POST or None)
    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.tenant = get_object_or_404(Tenant, user=request.user)
        ticket.save()
        return redirect('app:tickets')
    return render(request, 'ticket_form.html', {'form': form})

@admin_required
def admin_tickets(request):
    tickets = Ticket.objects.select_related('tenant__user')
    return render(request, 'admin_tickets.html', {'tickets': tickets})

@admin_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = TicketForm(request.POST or None, instance=ticket)
    if form.is_valid():
        form.save()
        return redirect('app:admin:tickets')
    return render(request, 'ticket_form.html', {'form': form, 'ticket': ticket})

# ─── IMPORT / EKSPORT CSV ───────────────────────────────
@admin_required
def export_apartment_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="apartments.csv"'
    writer.writerow(['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee'])
    for apt in Apartment.objects.all().order_by('number'):
        writer.writerow([
            apt.number, apt.floor, apt.area,
            apt.rent, apt.trash_fee, apt.water_fee, apt.gas_fee
        ])
    return response

@admin_required
def import_apartment_csv(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        reader = csv.DictReader(form.cleaned_data['csv_file'].read().decode().splitlines(), delimiter=';')
        for row in reader:
            Apartment.objects.update_or_create(
                number=row['number'],
                defaults={
                    'floor': row['floor'],
                    'area':  row['area'],
                }
            )
        messages.success(request, 'Mieszkania zaimportowane pomyślnie.')
        return redirect('app:admin:dashboard')
    return render(request, 'import_apartment.html', {'form': form})

# ─── PANEL UŻYTKOWNIKA / GŁÓWNY ─────────────────────────
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def custom_logout(request):
    logout(request)
    return redirect('/')
