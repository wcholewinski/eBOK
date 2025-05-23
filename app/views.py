from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import Apartment, Tenant, Payment, Ticket
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm, TicketForm, TicketStatusForm

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

# ─── MODUŁ ZGŁOSZEŃ S ERWISOWYCH ───
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

# ─── IMPORT MIESZKAŃ z CSV ───
@user_passes_test(lambda u: u.is_superuser)
def import_apartments(request):
    import csv, io
    from .forms import CSVImportForm
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            decoded = request.FILES['csv_file'].read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            for row in reader:
                Apartment.objects.update_or_create(
                    number=row['number'],
                    defaults={
                        'floor': int(row['floor']),
                        'area': float(row['area']),
                        'rent': float(row['rent']),
                        'trash_fee': float(row['trash_fee']),
                        'water_fee': float(row['water_fee']),
                        'gas_fee': float(row['gas_fee']),
                    }
                )
                count += 1
            return redirect('admin_dashboard')
    else:
        form = CSVImportForm()
    return render(request, 'import_apartments.html', {'form': form})


def dashboard(request):
    return render(request, 'dashboard.html')