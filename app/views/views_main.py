from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption, MaintenanceRequest, BuildingAlert
from app.forms import ApartmentForm, TenantForm, PaymentForm, TicketForm
from django.contrib.auth.models import User
from django.db.models import Sum, Avg, Count, F
from app.views.admin_views import admin_required
from django.contrib.auth import logout
import csv
import datetime
from dateutil.relativedelta import relativedelta
import random


def custom_logout(request):
    logout(request)
    return redirect('app:login')


@login_required
def dashboard(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
        apartment = tenant.apartment

        # Pobranie ostatnich płatności
        recent_payments = Payment.objects.filter(tenant=tenant).order_by('-date')[:5]

        # Pobranie ostatnich zgłoszeń
        recent_tickets = Ticket.objects.filter(tenant=tenant).order_by('-created_at')[:5]

        context = {
            'tenant': tenant,
            'apartment': apartment,
            'recent_payments': recent_payments,
            'recent_tickets': recent_tickets,
        }
        return render(request, 'dashboard.html', context)
    except Tenant.DoesNotExist:
        # Jeśli użytkownik nie jest najemcą, to przekieruj do panelu admina
        if request.user.is_staff:
            return redirect('app:admin_dashboard')
        # W innym przypadku pokazujemy standardowy dashboard z informacją
        return render(request, 'dashboard.html', {'error': 'Nie znaleziono przypisanego mieszkania.'})


@admin_required
def admin_dashboard(request):
    context = {
        'apartments': Apartment.objects.all(),
        'tenants': Tenant.objects.select_related('user', 'apartment'),
    }
    return render(request, 'admin_dashboard.html', context)


@admin_required
def add_apartment(request):
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app:admin_dashboard')
    else:
        form = ApartmentForm()
    return render(request, 'admin/add_apartment.html', {'form': form})


@admin_required
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            # Pobierz dane z formularza
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            apartment = form.cleaned_data['apartment']
            phone_number = form.cleaned_data['phone_number']
            move_in_date = form.cleaned_data['move_in_date']
            contract_end_date = form.cleaned_data['contract_end_date']

            # Utwórz użytkownika
            username = f"{first_name.lower()}.{last_name.lower()}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password="changeme",  # Tymczasowe hasło
                first_name=first_name,
                last_name=last_name
            )

            # Utwórz najemcę
            tenant = Tenant.objects.create(
                user=user,
                apartment=apartment,
                phone_number=phone_number,
                move_in_date=move_in_date,
                contract_end_date=contract_end_date
            )

            return redirect('app:admin_dashboard')
    else:
        form = TenantForm()
    return render(request, 'admin/add_tenant.html', {'form': form})


@admin_required
def edit_apartment(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)
    if request.method == 'POST':
        form = ApartmentForm(request.POST, instance=apartment)
        if form.is_valid():
            form.save()
            return redirect('app:apartment_detail', pk=apartment.pk)
    else:
        form = ApartmentForm(instance=apartment)

    # Pobierz wszystkich najemców dla tego mieszkania
    tenants = Tenant.objects.filter(apartment=apartment).select_related('user')

    context = {
        'form': form,
        'apartment': apartment,
        'tenants': tenants,
    }
    return render(request, 'admin/edit_apartment.html', context)


@login_required
def payments(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    payments = Payment.objects.filter(tenant=tenant).order_by('-date')
    return render(request, 'payments.html', {'payments': payments, 'tenant': tenant})


@admin_required
def admin_payments(request):
    payments = Payment.objects.all().order_by('-date')
    return render(request, 'admin/admin_payments.html', {'payments': payments})


@admin_required
def payment_form(request, pk=None):
    payment = None if pk is None else get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('app:admin_payments')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'admin/payment_form.html', {'form': form, 'payment': payment})


@login_required
def tickets(request):
    tickets = Ticket.objects.filter(tenant__user=request.user).order_by('-created_at')
    return render(request, 'tickets.html', {'tickets': tickets})


@login_required
def add_ticket(request):
    tenant = get_object_or_404(Tenant, user=request.user)
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.tenant = tenant
            ticket.status = 'new'
            ticket.save()
            return redirect('app:tickets')
    else:
        form = TicketForm()

    return render(request, 'ticket_form.html', {'form': form})


@admin_required
def admin_tickets(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'admin/admin_tickets.html', {'tickets': tickets})


@admin_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('app:admin_tickets')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'admin/ticket_edit.html', {'form': form, 'ticket': ticket})


@admin_required
def export_apartment_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="apartments.csv"'

    writer = csv.writer(response)
    writer.writerow(['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee'])

    apartments = Apartment.objects.all().values_list('number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee')
    for apartment in apartments:
        writer.writerow(apartment)

    return response


@admin_required
def import_apartment_csv(request):
    from django.contrib import messages
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Proszę wybrać plik CSV')
            return redirect('app:import_apartment_csv')

        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Plik musi być w formacie CSV')
            return redirect('app:import_apartment_csv')

        # Sprawdzenie wielkości pliku
        if csv_file.size > 2_000_000:  # 2MB
            messages.error(request, 'Plik jest zbyt duży (max 2MB)')
            return redirect('app:admin_dashboard')

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            # Walidacja nagłówków
            required_headers = ['number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee']
            if not all(header in reader.fieldnames for header in required_headers):
                messages.error(request, 'Brakujące kolumny w pliku CSV')
                return redirect('app:admin_dashboard')

            # Import danych
            for row in reader:
                apartment, created = Apartment.objects.update_or_create(
                    number=row['number'],
                    defaults={
                        'floor': row['floor'],
                        'area': float(row['area']),
                        'rent': float(row['rent']),
                        'trash_fee': float(row['trash_fee']),
                        'water_fee': float(row['water_fee']),
                        'gas_fee': float(row['gas_fee'])
                    }
                )

            messages.success(request, 'Dane mieszkań zostały zaimportowane')
        except Exception as e:
            messages.error(request, f'Wystąpił błąd podczas importu: {str(e)}')

        return redirect('app:admin_dashboard')

    # Obsługa żądania GET
    return render(request, 'import_apartment.html')


def import_utility_data(request):
    """Funkcja obsługująca import danych o zużyciu mediów"""
    from django.contrib import messages

    if request.method == 'POST' and request.FILES.get('csv_file'):
        # Tutaj dodaj kod do obsługi importu
        messages.info(request, 'Funkcja importu danych jest w trakcie implementacji')
        return redirect('app:admin_dashboard')

    return render(request, 'admin/import_utility.html', {
        'title': 'Import danych o zużyciu mediów'
    })


@login_required
def analytics_dashboard(request):
    # Pobierz wszystkie płatności
    all_payments = Payment.objects.all()

    # Statystyki płatności
    payment_stats = {
        'total_amount': all_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_count': all_payments.count(),
        'avg_amount': all_payments.aggregate(Avg('amount'))['amount__avg'] or 0,
    }

    # Statystyki płatności według typu
    payment_types = ['rent', 'water', 'electricity', 'gas', 'other']
    payment_by_type = {}

    for payment_type in payment_types:
        type_payments = all_payments.filter(type=payment_type)
        payment_by_type[payment_type] = {
            'total': type_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'count': type_payments.count(),
            'avg': type_payments.aggregate(Avg('amount'))['amount__avg'] or 0
        }

    # Statystyki mieszkań
    apartments = Apartment.objects.all()
    apartment_stats = {
        'total_count': apartments.count(),
        'avg_area': apartments.aggregate(Avg('area'))['area__avg'] or 0,
        'avg_rent': apartments.aggregate(Avg('rent'))['rent__avg'] or 0,
    }

    # Statystyki zgłoszeń
    tickets = Ticket.objects.all()
    ticket_stats = {
        'total_count': tickets.count(),
        'open_count': tickets.filter(status__in=['new', 'in_progress']).count(),
        'closed_count': tickets.filter(status='closed').count(),
    }

    context = {
        'payment_stats': payment_stats,
        'payment_by_type': payment_by_type,
        'apartment_stats': apartment_stats,
        'ticket_stats': ticket_stats,
    }

    return render(request, 'admin/analytics_dashboard.html', context)


@login_required
def profit_prediction(request):
    from app.utils.ml_analysis import PredictiveAnalysis

    # Dane do przewidywania zysków
    months = ['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru']

    # Przykładowe dane do symulacji przyszłych zysków
    current_month = datetime.datetime.now().month - 1  # 0-based index

    # Wyliczamy przewidywane zyski na podstawie obecnych czynszów
    apartments = Apartment.objects.all()
    # Konwertujemy wartość Decimal na float przed operacjami matematycznymi
    total_rent = float(sum(float(a.rent) for a in apartments))

    # Symulacja zysków z uwzględnieniem sezonowości
    # Zima - wyższe koszty, niższe zyski; Lato - niższe koszty, wyższe zyski
    season_factors = [0.85, 0.87, 0.9, 0.95, 1.0, 1.05, 1.1, 1.1, 1.05, 0.95, 0.9, 0.85]

    # Generujemy dane dla wykresu
    predicted_profits = []
    for i in range(12):
        month_index = (current_month + i) % 12
        predicted_profits.append(round(total_rent * season_factors[month_index], 2))

    # Przewidywane koszty utrzymania budynku
    maintenance_costs = [round(total_rent * 0.3 * (1.1 if m in [0, 1, 11] else 0.9), 2) for m in range(12)]

    # Przygotowanie danych w formacie bardziej przyjaznym dla szablonu
    monthly_data = []
    for i in range(12):
        month_index = (current_month + i) % 12
        month_profit = predicted_profits[i]
        month_cost = maintenance_costs[i]
        month_net = month_profit - month_cost
        month_margin = (month_net / month_profit * 100) if month_profit > 0 else 0

        monthly_data.append({
            'month': months[month_index],
            'profit': month_profit,
            'cost': month_cost,
            'net': month_net,
            'margin': month_margin
        })

    # Dane do wykresu w formacie JSON
    chart_data = {
        'labels': [item['month'] for item in monthly_data],
        'predicted_profits': predicted_profits,
        'maintenance_costs': maintenance_costs,
        'net_profits': [item['net'] for item in monthly_data]
    }

    # Podsumowanie roczne
    annual_profit = sum(predicted_profits)
    annual_costs = sum(maintenance_costs)
    net_annual_profit = annual_profit - annual_costs
    annual_margin = (net_annual_profit / annual_profit * 100) if annual_profit > 0 else 0

    context = {
        'chart_data': chart_data,
        'monthly_data': monthly_data,
        'annual_profit': annual_profit,
        'annual_costs': annual_costs,
        'net_annual_profit': net_annual_profit,
        'annual_margin': annual_margin
    }

    return render(request, 'admin/profit_prediction.html', context)


@login_required
def consumption_trends(request):
    from app.utils.ml_analysis import PredictiveAnalysis

    # Analiza trendów zużycia mediów
    utility_data = UtilityConsumption.objects.all().order_by('period_start')

    # Pobieramy dane dla różnych typów mediów
    electricity_data = utility_data.filter(utility_type='electricity')
    water_data = utility_data.filter(utility_type='water')
    gas_data = utility_data.filter(utility_type='gas')
    heating_data = utility_data.filter(utility_type='heating')

    # Agregujemy dane miesięcznie
    months = ['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru']

    # Funkcja do agregacji danych miesięcznie
    def aggregate_monthly_data(queryset):
        monthly_data = [0] * 12
        monthly_costs = [0] * 12

        for item in queryset:
            month = item.period_start.month - 1  # 0-based index
            # Konwersja wartości Decimal na float
            monthly_data[month] += float(item.consumption)
            monthly_costs[month] += float(item.cost)

        return monthly_data, monthly_costs

    # Agregujemy dane dla każdego typu mediów
    electricity_monthly, electricity_costs = aggregate_monthly_data(electricity_data)
    water_monthly, water_costs = aggregate_monthly_data(water_data)
    gas_monthly, gas_costs = aggregate_monthly_data(gas_data)
    heating_monthly, heating_costs = aggregate_monthly_data(heating_data)

    # Przygotowanie danych do tabelki
    monthly_consumption_data = []
    for i in range(12):
        total_cost = electricity_costs[i] + water_costs[i] + gas_costs[i] + heating_costs[i]
        monthly_consumption_data.append({
            'month': months[i],
            'electricity': electricity_monthly[i],
            'water': water_monthly[i],
            'gas': gas_monthly[i],
            'heating': heating_monthly[i],
            'total_cost': total_cost
        })

    # Przygotowujemy dane do wykresów
    consumption_chart_data = {
        'labels': months,
        'electricity': electricity_monthly,
        'water': water_monthly,
        'gas': gas_monthly,
        'heating': heating_monthly
    }

    cost_chart_data = {
        'labels': months,
        'electricity': electricity_costs,
        'water': water_costs,
        'gas': gas_costs,
        'heating': heating_costs,
        'total': [sum(x) for x in zip(electricity_costs, water_costs, gas_costs, heating_costs)]
    }

    # Analiza trendów i anomalii
    # Przykład: wykrywamy miesiące z nadzwyczaj wysokim zużyciem
    anomalies = []

    # Sprawdzamy czy zużycie jest znacząco wyższe niż średnia
    for utility, data in [
        ('Prąd', electricity_monthly),
        ('Woda', water_monthly),
        ('Gaz', gas_monthly),
        ('Ogrzewanie', heating_monthly)
    ]:
        avg = sum(data) / len([x for x in data if x > 0]) if any(data) else 0
        for i, value in enumerate(data):
            if value > avg * 1.5 and value > 0:  # 50% powyżej średniej
                anomalies.append({
                    'utility': utility,
                    'month': months[i],
                    'value': round(value, 2),
                    'avg': round(avg, 2),
                    'percent': round((value - avg) / avg * 100 if avg else 0, 1)
                })

    context = {
        'consumption_chart_data': consumption_chart_data,
        'cost_chart_data': cost_chart_data,
        'anomalies': anomalies,
        'monthly_data': monthly_consumption_data,  # Dodajemy dane miesięczne
        'total_electricity': sum(electricity_monthly),
        'total_water': sum(water_monthly),
        'total_gas': sum(gas_monthly),
        'total_heating': sum(heating_monthly),
        'total_costs': sum(sum(x) for x in zip(electricity_costs, water_costs, gas_costs, heating_costs))
    }

    return render(request, 'admin/consumption_trends.html', context)


@admin_required
def alerts_management(request):
    alerts = BuildingAlert.objects.all().order_by('-created_at')
    context = {
        'alerts': alerts,
    }
    return render(request, 'admin/alerts_management.html', context)


@login_required
def alerts_system(request):
    if not request.user.is_staff:
        return redirect('app:dashboard')

    # Sprawdzamy różne warunki, które mogą generować alerty
    alerts = []

    # 1. Mieszkania bez najemców
    vacant_apartments = Apartment.objects.filter(tenant__isnull=True).count()
    if vacant_apartments > 0:
        alerts.append({
            'type': 'info',
            'message': f'Liczba pustych mieszkań: {vacant_apartments}',
            'action': 'Rozważ marketing w celu znalezienia najemców'
        })

    # 2. Kończące się umowy najmu (w ciągu miesiąca)
    from datetime import date, timedelta
    one_month_later = date.today() + timedelta(days=30)
    expiring_contracts = Tenant.objects.filter(contract_end_date__lte=one_month_later, contract_end_date__gte=date.today()).count()

    if expiring_contracts > 0:
        alerts.append({
            'type': 'warning',
            'message': f'Liczba umów wygasających w ciągu 30 dni: {expiring_contracts}',
            'action': 'Skontaktuj się z najemcami w sprawie przedłużenia'
        })

    # 3. Zaległe płatności
    overdue_payments = Payment.objects.filter(status='overdue').count()
    if overdue_payments > 0:
        alerts.append({
            'type': 'danger',
            'message': f'Liczba zaległych płatności: {overdue_payments}',
            'action': 'Sprawdź listę płatności i skontaktuj się z najemcami'
        })

    # 4. Nowe zgłoszenia serwisowe
    new_tickets = Ticket.objects.filter(status='new').count()
    if new_tickets > 0:
        alerts.append({
            'type': 'primary',
            'message': f'Nowe zgłoszenia serwisowe: {new_tickets}',
            'action': 'Przejrzyj zgłoszenia i przydziel techników'
        })

    context = {
        'alerts': alerts,
    }

    return render(request, 'admin/alerts_system.html', context)


@login_required
def apartment_list(request):
    apartments = Apartment.objects.all()
    return render(request, 'apartments/apartment_list.html', {'apartments': apartments})


@login_required
def apartment_detail(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)
    tenants = Tenant.objects.filter(apartment=apartment).select_related('user')

    # Dane o zużyciu mediów
    utility_data = UtilityConsumption.objects.filter(apartment=apartment).order_by('-period_start')

    # Przygotowanie danych do wykresu zużycia
    utility_types = ['electricity', 'water', 'gas', 'heating']
    chart_data = {}

    for utility_type in utility_types:
        data = list(utility_data.filter(utility_type=utility_type).values('period_start', 'consumption'))
        chart_data[utility_type] = {
            'labels': [item['period_start'].strftime('%m/%Y') for item in data],
            'data': [item['consumption'] for item in data]
        }

    context = {
        'apartment': apartment,
        'tenants': tenants,
        'utility_data': utility_data,
        'chart_data': chart_data
    }

    return render(request, 'apartments/apartment_detail.html', context)


@login_required
def tenant_list(request):
    tenants = Tenant.objects.all().select_related('user', 'apartment')
    return render(request, 'tenants/tenant_list.html', {'tenants': tenants})


@login_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    payments = Payment.objects.filter(tenant=tenant).order_by('-date')
    tickets = Ticket.objects.filter(tenant=tenant).order_by('-created_at')

    context = {
        'tenant': tenant,
        'payments': payments,
        'tickets': tickets
    }

    return render(request, 'tenants/tenant_detail.html', context)


@login_required
def payment_list(request):
    # Sprawdź czy użytkownik jest administratorem
    if request.user.is_staff:
        payments = Payment.objects.all().order_by('-date')
    else:
        # Dla zwykłego użytkownika pokazujemy tylko jego płatności
        try:
            tenant = Tenant.objects.get(user=request.user)
            payments = Payment.objects.filter(tenant=tenant).order_by('-date')
        except Tenant.DoesNotExist:
            payments = Payment.objects.none()

    return render(request, 'payments/payment_list.html', {'payments': payments})


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    # Sprawdź czy użytkownik ma dostęp do tej płatności
    if not request.user.is_staff and payment.tenant.user != request.user:
        return redirect('app:dashboard')

    # Pobierz historię płatności dla tego najemcy
    tenant_payments = Payment.objects.filter(
        tenant=payment.tenant,
        type=payment.type
    ).exclude(pk=payment.pk).order_by('-date')[:5]

    context = {
        'payment': payment,
        'tenant_payments': tenant_payments
    }

    return render(request, 'payments/payment_detail.html', context)


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Sprawdź czy użytkownik ma dostęp do tego zgłoszenia
    if not request.user.is_staff and ticket.tenant.user != request.user:
        return redirect('app:dashboard')

    context = {
        'ticket': ticket
    }

    return render(request, 'tickets/ticket_detail.html', context)
