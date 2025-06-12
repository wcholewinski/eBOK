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
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from app.models import Apartment, Tenant
from django.contrib.auth.models import User
from app.forms import TenantForm

# Dekorator sprawdzający czy użytkownik jest administratorem
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('app:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_required
def delete_apartment(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)
    if request.method == 'POST':
        # Sprawdź czy mieszkanie ma lokatorów
        if Tenant.objects.filter(apartment=apartment).exists():
            messages.error(request, f'Nie można usunąć mieszkania {apartment.number}, ponieważ ma przypisanych lokatorów.')
            return redirect('app:admin_dashboard')

        # Usuń mieszkanie
        apartment_number = apartment.number
        apartment.delete()
        messages.success(request, f'Mieszkanie {apartment_number} zostało usunięte.')
        return redirect('app:admin_dashboard')

    return render(request, 'admin/delete_apartment.html', {'apartment': apartment})


@admin_required
def edit_tenant(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dane lokatora {tenant.user.first_name} {tenant.user.last_name} zostały zaktualizowane.')
            return redirect('app:admin_dashboard')
    else:
        # Wypełnij formularz danymi najemcy i użytkownika
        initial_data = {
            'first_name': tenant.user.first_name,
            'last_name': tenant.user.last_name,
            'email': tenant.user.email,
            'apartment': tenant.apartment,
            'phone_number': tenant.phone_number,
            'move_in_date': tenant.move_in_date,
            'contract_end_date': tenant.contract_end_date
        }
        form = TenantForm(instance=tenant, initial=initial_data)

    return render(request, 'admin/edit_tenant.html', {'form': form, 'tenant': tenant})


@admin_required
def delete_tenant(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        # Zapisz informacje o najemcy przed usunięciem
        tenant_name = f'{tenant.user.first_name} {tenant.user.last_name}'
        user = tenant.user

        # Usuń najemcę
        tenant.delete()

        # Usuń użytkownika powiązanego z najemcą
        user.delete()

        messages.success(request, f'Lokator {tenant_name} został usunięty wraz z kontem użytkownika.')
        return redirect('app:admin_dashboard')

    return render(request, 'admin/delete_tenant.html', {'tenant': tenant})


@admin_required
def bulk_delete_apartments(request):
    if request.method == 'POST':
        apartment_ids = request.POST.getlist('apartment_ids')

        if not apartment_ids:
            messages.error(request, 'Nie wybrano żadnych mieszkań do usunięcia.')
            return redirect('app:admin_dashboard')

        # Pobierz wszystkie wybrane mieszkania
        apartments = Apartment.objects.filter(id__in=apartment_ids)

        # Sprawdź, czy któreś z wybranych mieszkań ma lokatorów
        apartments_with_tenants = []
        for apartment in apartments:
            if Tenant.objects.filter(apartment=apartment).exists():
                apartments_with_tenants.append(apartment.number)

        if apartments_with_tenants:
            # Jeśli któreś mieszkanie ma lokatorów, wyświetl błąd
            messages.error(request, f'Nie można usunąć mieszkań: {", ".join(str(x) for x in apartments_with_tenants)}, ponieważ mają przypisanych lokatorów.')
            return redirect('app:admin_dashboard')

        # Usuń wybrane mieszkania
        deleted_count = apartments.count()
        apartments.delete()

        messages.success(request, f'Usunięto {deleted_count} mieszkań.')
        return redirect('app:admin_dashboard')

    return redirect('app:admin_dashboard')


@admin_required
def bulk_delete_tenants(request):
    if request.method == 'POST':
        tenant_ids = request.POST.getlist('tenant_ids')

        if not tenant_ids:
            messages.error(request, 'Nie wybrano żadnych lokatorów do usunięcia.')
            return redirect('app:admin_dashboard')

        # Pobierz wszystkich wybranych lokatorów
        tenants = Tenant.objects.filter(id__in=tenant_ids).select_related('user')

        deleted_count = 0
        for tenant in tenants:
            # Zapisz użytkownika przed usunięciem najemcy
            user = tenant.user

            # Usuń najemcę
            tenant.delete()

            # Usuń użytkownika
            user.delete()
            deleted_count += 1

        messages.success(request, f'Usunięto {deleted_count} lokatorów wraz z ich kontami użytkowników.')
        return redirect('app:admin_dashboard')

    return redirect('app:admin_dashboard')

@admin_required
def delete_all_tenants_and_apartments(request):
    """Usuwa wszystkich lokatorów i mieszkania z systemu"""
    if request.method == 'POST':
        # Pobierz wszystkich lokatorów
        tenants = Tenant.objects.all().select_related('user')
        tenants_count = tenants.count()

        # Usuń wszystkich lokatorów i ich konta użytkowników
        for tenant in tenants:
            user = tenant.user
            tenant.delete()
            user.delete()

        # Usuń wszystkie mieszkania
        apartments_count = Apartment.objects.count()
        Apartment.objects.all().delete()

        messages.success(request, f'Usunięto wszystkie dane: {tenants_count} lokatorów i {apartments_count} mieszkań.')
        return redirect('app:admin_dashboard')

    return redirect('app:admin_dashboard')
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