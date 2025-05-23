from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import Apartment, Tenant, Payment, Ticket
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm, TicketForm, TicketStatusForm
import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages

# ─── PANEL ADMINA: MIESZKANIA i LOKATORZY ───
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    apartments = Apartment.objects.all()
    tenants = Tenant.objects.select_related('user', 'apartment')
    return render(request, 'admin_dashboard.html', {
        'apartments': apartments,
        'tenants': tenants,
    })

@user_passes_test(lambda u: u.is_superuser)
def add_apartment(request):
    form = ApartmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'add_apartment.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def add_tenant(request):
    form = TenantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('admin_dashboard')
    return render(request, 'add_tenant.html', {'form': form})

# ─── MODUŁ PŁATNOŚCI ───
@login_required
def payments(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    payments = tenant.payments.all()
    return render(request, 'payments.html', {'payments': payments})

@user_passes_test(lambda u: u.is_superuser)
def admin_payments(request):
    payments = Payment.objects.select_related('tenant__user')
    return render(request, 'admin_payments.html', {'payments': payments})

@user_passes_test(lambda u: u.is_superuser)
def payment_form(request, pk=None):
    instance = get_object_or_404(Payment, pk=pk) if pk else None
    form = PaymentForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('admin_payments')
    return render(request, 'payment_form.html', {'form': form, 'is_edit': bool(pk)})

# ─── MODUŁ ZGŁOSZEŃ SERWISOWYCH ───
@login_required
def tickets(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    tickets = tenant.tickets.all()
    return render(request, 'tickets.html', {'tickets': tickets})

@login_required
def ticket_add(request):
    form = TicketForm(request.POST or None)
    if form.is_valid():
        ticket = form.save(commit=False)
        ticket.tenant = get_object_or_404(Tenant, user=request.user)
        ticket.save()
        return redirect('tickets')
    return render(request, 'ticket_form.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def admin_tickets(request):
    tickets = Ticket.objects.select_related('tenant__user')
    return render(request, 'admin_tickets.html', {'tickets': tickets})

@user_passes_test(lambda u: u.is_superuser)
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = TicketStatusForm(request.POST or None, instance=ticket)
    if form.is_valid():
        form.save()
        return redirect('admin_tickets')
    return render(request, 'ticket_edit.html', {'form': form, 'ticket': ticket})

# ─── IMPORT/ EKSPORT z CSV ───
def export_apartment_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="apartment.csv"'

    writer = csv.writer(response)
    writer.writerow(['numer', 'pietro', 'powierzchnia'])

    for m in Apartment.objects.all():
        writer.writerow([m.numer, m.pietro, m.powierzchnia])

    return response

def import_apartment_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        for row in reader:
            Apartment.objects.update_or_create(
                numer=row['numer'],
                defaults={
                    'pietro': row['pietro'],
                    'powierzchnia': row['powierzchnia']
                }
            )
        messages.success(request, 'Dane zaimportowane!')
        return redirect('lista_mieszkan')  # dostosuj URL

    return render(request, 'import_apartment.html')


def dashboard(request):
    return render(request, 'dashboard.html')