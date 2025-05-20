import csv, io
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Apartment, Tenant, Payment
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm
from django.contrib import messages



@login_required
def dashboard(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
    except Tenant.DoesNotExist:
        tenant = None  # np. administrator

    context = {
        'tenant': tenant
    }
    return render(request, 'dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    apartments = Apartment.objects.all()
    tenants = Tenant.objects.select_related('apartment', 'user')
    return render(request, 'admin_dashboard.html', {
        'apartments': apartments,
        'tenants': tenants,
    })

@user_passes_test(lambda u: u.is_superuser)
def add_apartment(request):
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = ApartmentForm()
    return render(request, 'add_apartment.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = TenantForm()
    return render(request, 'add_tenant.html', {'form': form})

# Panel lokatora: lista jego płatności
@login_required
def payments(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    payments = Payment.objects.filter(tenant=tenant).order_by('-date')
    return render(request, 'payments.html', {'payments': payments})

# Panel admina: lista wszystkich płatności
@user_passes_test(lambda u: u.is_superuser)
def admin_payments(request):
    payments = Payment.objects.select_related('tenant__user').order_by('-date')
    return render(request, 'admin_payments.html', {'payments': payments})

# Dodaj/edytuj płatność (admin)
@user_passes_test(lambda u: u.is_superuser)
def payment_form(request, pk=None):
    if pk:
        payment = get_object_or_404(Payment, pk=pk)
    else:
        payment = None

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('admin_payments')
    else:
        form = PaymentForm(instance=payment)

    return render(request, 'payment_form.html', {'form': form, 'is_edit': bool(pk)})

@user_passes_test(lambda u: u.is_superuser)
def import_apartments(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            for row in reader:
                # twórz lub aktualizuj mieszkanie po numerze
                obj, created = Apartment.objects.update_or_create(
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
            messages.success(request, f'Zaimportowano/aktualizowano {count} mieszkań.')
            return redirect('admin_dashboard')
    else:
        form = CSVImportForm()
    return render(request, 'import_apartments.html', {'form': form})





