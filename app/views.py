from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import logout
import csv

from .models import Apartment, Tenant, Payment, Ticket
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm, TicketForm
from django.shortcuts import redirect

def admin_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            return redirect('app:login')
        return redirect('app:login')
    return wrap


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
    if request.method == "POST":
        form = ApartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app:admin_dashboard')  # Zmieniona nazwa
    else:
        form = ApartmentForm()
    return render(request, 'add_apartment.html', {'form': form})

@admin_required
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, f"Lokator {tenant.user.username} został dodany")
            return redirect('app:admin_dashboard')
        else:
            print(f"Błędy formularza: {form.errors}")
            messages.error(request, "Formularz zawiera błędy")
    else:
        form = TenantForm()
    
    # Dodaj kontekst z dostępnymi mieszkaniami
    apartments = Apartment.objects.all()
    return render(request, 'add_tenant.html', {
        'form': form,
        'apartments': apartments
    })


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
        return redirect('app:admin_payments')
    return render(request, 'payment_form.html', {'form': form, 'is_edit': bool(pk)})

# ─── ZGŁOSZENIA ─────────────────────────────────────────
@login_required
def tickets(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    return render(request, 'tickets.html', {'tickets': tenant.tickets.all()})

@login_required
def add_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.tenant = get_object_or_404(Tenant, user=request.user)
            ticket.save()
            return redirect('app:tickets')  # Przekierowanie!
        else:
            print(form.errors)
    else:
        form = TicketForm()
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
        return redirect('app:admin_tickets')
    return render(request, 'ticket_form.html', {'form': form, 'ticket': ticket})

# ─── IMPORT / EKSPORT CSV ───────────────────────────────
@admin_required
def export_apartment_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="apartments.csv"'

    writer_csv = csv.writer(response)
    writer_csv.writerow(['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee'])
    for apt in Apartment.objects.all().order_by('number'):
        writer_csv.writerow([
            apt.number, apt.floor, apt.area,
            apt.rent, apt.trash_fee, apt.water_fee, apt.gas_fee
        ])
    return response

@admin_required
def import_apartment_csv(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        try:
            csv_file = form.cleaned_data['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = decoded_file.splitlines()

            # Wykrywamy separator (średnik lub przecinek)
            if ';' in csv_data[0]:
                delimiter = ';'
            else:
                delimiter = ','

            reader = csv.DictReader(csv_data, delimiter=delimiter)

            for row in reader:
                Apartment.objects.update_or_create(
                    number=row['number'],
                    defaults={
                        'floor': int(row['floor']),
                        'area': float(row['area']),
                        # Ustaw domyślne wartości dla pozostałych pól, jeśli nie są podane
                        'rent': float(row.get('rent', 0)),
                        'trash_fee': float(row.get('trash_fee', 0)),
                        'water_fee': float(row.get('water_fee', 0)),
                        'gas_fee': float(row.get('gas_fee', 0))
                    }
                )
            messages.success(request, 'Mieszkania zaimportowane pomyślnie.')
            return redirect('app:admin_dashboard')
        except Exception as e:
            messages.error(request, f"Błąd importu: {e}")
    return render(request, 'import_apartment.html', {'form': form})


# ─── PANEL UŻYTKOWNIKA / GŁÓWNY ─────────────────────────
@login_required
def dashboard(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
    except Tenant.DoesNotExist:
        tenant = None

    fields = []
    if tenant:
        apt = tenant.apartment
        fields = [
            ("Numer mieszkania", apt.number),
            ("Piętro", apt.floor),
            ("Powierzchnia (m²)", apt.area),
            ("Czynsz (zł)", apt.rent),
            ("Śmieci (zł)", apt.trash_fee),
            ("Woda (zł)", apt.water_fee),
            ("Gaz (zł)", apt.gas_fee),
            ("Liczba mieszkańców", tenant.num_occupants),
        ]

    return render(request, 'dashboard.html', {
        'tenant': tenant,
        'fields': fields,
    })

# ─── WYLOGOWANIE ────────────────────────────────────────
def custom_logout(request):
    logout(request)
    return redirect('app:login')

# REDIRECT VIEWS
def redirect_to_add_apartment(request):
    return redirect('app:admin_add_apartment')


def redirect_to_admin_payments(request):
    return redirect('app:admin_payments')


def redirect_to_admin_tickets(request):
    return redirect('app:admin_tickets')

def redirect_to_add_tenant(request):
    return redirect('app:admin_add_tenant')