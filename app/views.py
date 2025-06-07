
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from app.utils.ml_analysis import PredictiveAnalysis

import csv
import io

from .models import Apartment, Tenant, Payment, Ticket, UtilityConsumption, BuildingAlert, MaintenanceRequest
from .forms import ApartmentForm, TenantForm, PaymentForm, CSVImportForm, TicketForm
from django.shortcuts import redirect
from app.decorators import admin_required


# ─── PANEL ADMINA ───────────────────────────────────────
from app.decorators import admin_required

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
            return redirect('app:admin_dashboard')
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

    apartments = Apartment.objects.all()
    return render(request, 'add_tenant.html', {
        'form': form,
        'apartments': apartments
    })


@admin_required
def edit_apartment(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)
    if request.method == "POST":
        form = ApartmentForm(request.POST, instance=apartment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mieszkanie {apartment.number} zostało zaktualizowane")
            return redirect('app:admin_dashboard')
        else:
            messages.error(request, "Formularz zawiera błędy")
    else:
        form = ApartmentForm(instance=apartment)

    return render(request, 'admin/edit_apartment.html', {
        'form': form,
        'apartment': apartment
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
    return render(request, 'admin/admin_payments.html', {'payments': payments})


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
            return redirect('app:tickets')
        else:
            print(form.errors)
    else:
        form = TicketForm()
    return render(request, 'ticket_form.html', {'form': form})


@admin_required
def admin_tickets(request):
    tickets = Ticket.objects.select_related('tenant__user')
    return render(request, 'admin_tickets.html', {'tickets': tickets, 'title': 'Zgłoszenia'})


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
def import_apartment_csv(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        try:
            csv_file = form.cleaned_data['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = decoded_file.splitlines()

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


@admin_required
def import_utility_data(request):
    """Zaawansowany import danych zużycia mediów z CSV"""
    import uuid
    import tempfile
    import os
    from django.core.files.storage import default_storage
    from app.utils.csv_import import CSVImporter
    from app.forms import AdvancedCSVImportForm

    # Przygotowanie kontekstu
    context = {
        'form': AdvancedCSVImportForm(initial={'model_type': 'utility_consumption'}),
        'step': request.POST.get('step', 'upload')
    }

    # Krok 1: Wczytanie pliku i podgląd
    if request.method == 'POST' and context['step'] == 'preview':
        form = AdvancedCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Zapisanie pliku tymczasowo
                csv_file = form.cleaned_data['csv_file']
                file_id = str(uuid.uuid4())
                temp_path = default_storage.save(f'temp/csv_import_{file_id}.csv', csv_file)

                # Wczytanie pliku do podglądu
                with default_storage.open(temp_path, 'rb') as f:
                    importer = CSVImporter(f, 'utility_consumption')
                    if importer.load_preview():
                        # Walidacja struktury pliku
                        required_fields = ['apartment_number', 'utility_type', 'period_start', 'period_end', 'consumption', 'unit', 'cost']
                        validation_passed = importer.validate_headers(required_fields)

                        context.update({
                            'preview_data': importer.preview_data,
                            'headers': importer.headers,
                            'delimiter': importer.delimiter,
                            'encoding': importer.encoding,
                            'file_id': file_id,
                            'date_format': form.cleaned_data['date_format'],
                            'validation_errors': importer.errors if not validation_passed else []
                        })
                    else:
                        context['errors'] = importer.errors
            except Exception as e:
                context['errors'] = [f"Błąd wczytywania pliku: {str(e)}"]

    # Krok 2: Import danych
    elif request.method == 'POST' and context['step'] == 'import':
        try:
            file_id = request.POST.get('file_id')
            date_format = request.POST.get('date_format')
            temp_path = f'temp/csv_import_{file_id}.csv'

            # Sprawdzenie czy plik istnieje
            if default_storage.exists(temp_path):
                with default_storage.open(temp_path, 'rb') as f:
                    importer = CSVImporter(f, 'utility_consumption')
                    # Mapowanie kolumn (jeśli potrzebne)
                    mapping = {}

                    # Import danych
                    import_success = importer.import_data(mapping, date_format)
                    summary = importer.get_summary()

                    context.update({
                        'import_success': import_success,
                        'summary': summary,
                        'errors': importer.errors
                    })

                    # Wyświetlenie komunikatu
                    if import_success:
                        messages.success(
                            request, 
                            f"Import zakończony pomyślnie. Zaimportowano {summary['imported']} nowych rekordów, "
                            f"zaktualizowano {summary['updated']} istniejących, pominięto {summary['skipped']} z błędami."
                        )
                    else:
                        messages.error(request, f"Błąd podczas importu: {', '.join(importer.errors)}")

                # Usunięcie pliku tymczasowego
                default_storage.delete(temp_path)
            else:
                context['errors'] = ["Plik tymczasowy nie istnieje. Spróbuj ponownie."]
                context['import_success'] = False
        except Exception as e:
            context['errors'] = [f"Błąd podczas importu: {str(e)}"]
            context['import_success'] = False

    return render(request, 'import_utility_consumption.html', context)


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


# ─── ANALYTICS (PODSTAWOWE) ─────────────────────────────
@admin_required
def analytics_dashboard(request):
    """Dashboard analityczny z predykcjami i analizą efektywności"""
    # Inicjalizacja analizatora ML
    ml_analyzer = PredictiveAnalysis()

    # Pobieranie statystyk ogólnych
    from app.utils.api_helpers import get_admin_stats
    admin_stats = get_admin_stats()

    # Podstawowy kontekst
    context = {
        # Podstawowe statystyki
        'total_apartments': admin_stats['total_apartments'],
        'occupied_apartments': admin_stats['occupied_apartments'],
        'vacancy_rate': admin_stats['vacancy_rate'],
        'pending_tickets': admin_stats['maintenance_requests']['new'],

        # Efektywność i predykcje
        'efficiency_score': ml_analyzer.building_efficiency_score(),
        'predictions': {},
        'anomalies_count': 0,

        # Dane finansowe
        'profit_predictions': ml_analyzer.calculate_profit_predictions(forecast_months=6)
    }

    # Pobierz przykładowe predykcje dla kilku mieszkań
    sample_apartments = Apartment.objects.all()[:3]  # Weź tylko 3 mieszkania dla przykładu
    for apartment in sample_apartments:
        predictions = ml_analyzer.predict_utility_consumption(
            apartment.id, 'electricity', 3
        )
        if predictions:
            context['predictions'][apartment.number] = predictions

    return render(request, 'analytics_dashboard.html', context)


@admin_required
def profit_prediction(request):
    """Widok szczegółowej predykcji finansowej"""
    from app.utils.ml_analysis import PredictiveAnalysis

    # Inicjalizacja analizatora ML
    ml_analyzer = PredictiveAnalysis()

    # Pobieranie predykcji finansowych
    profit_predictions = ml_analyzer.calculate_profit_predictions(forecast_months=6)

    context = {
        'profit_predictions': profit_predictions,
        'title': 'Predykcje finansowe'
    }

    return render(request, 'profit_prediction.html', context)


def consumption_trends(request):
    """Uproszczona analiza trendów zużycia mediów"""
    from django.db.models import Avg, Sum
    import json
    from app.utils.ml_analysis import PredictiveAnalysis

    # Pobieranie danych o zużyciu
    consumptions = UtilityConsumption.objects.all().order_by('period_start')[:50]  # Limit danych
    apartments = Apartment.objects.all()

    # Filtrowanie danych na podstawie parametrów zapytania
    apartment_id = request.GET.get('apartment')
    utility_type = request.GET.get('utility_type')

    # Filtrowanie wg mieszkania
    if apartment_id:
        try:
            apartment_id = int(apartment_id)
            consumptions = consumptions.filter(apartment_id=apartment_id)
        except ValueError:
            pass

    # Filtrowanie wg typu mediów
    if utility_type:
        consumptions = consumptions.filter(utility_type=utility_type)

    # Przygotowanie danych do wykresów
    consumption_data = {}
    periods_list = []

    # Agregacja danych
    for consumption in consumptions:
        period_str = consumption.period_start.strftime('%m/%Y')
        if period_str not in periods_list:
            periods_list.append(period_str)

        utility_type = consumption.utility_type
        if utility_type not in consumption_data:
            consumption_data[utility_type] = []

        consumption_data[utility_type].append({
            'period': period_str,
            'consumption': float(consumption.consumption),
            'cost': float(consumption.cost),
            'apartment': consumption.apartment.number
        })

    # Inicjalizacja analizatora ML dla predykcji
    ml_analyzer = PredictiveAnalysis()
    predictions = {}

    # Pobieranie predykcji dla wybranego mieszkania
    if apartment_id:
        for utility in ['electricity', 'water', 'gas', 'heating']:
            predictions[utility] = ml_analyzer.predict_utility_consumption(apartment_id, utility, 3)

    # Predykcje finansowe dla całego budynku
    profit_predictions = ml_analyzer.calculate_profit_predictions(3)

    # Przygotowanie kontekstu
    context = {
        'apartments': apartments,
        'consumption_data': consumption_data,
        'periods': periods_list,
        'title': 'Trendy zużycia mediów',
        'selected_apartment': apartment_id,
        'selected_utility': utility_type,
        'predictions': predictions,
        'profit_predictions': profit_predictions,
        'utility_types': UtilityConsumption.UTILITY_TYPES
    }

    return render(request, 'consumption_trends.html', context)




@admin_required
def alerts_management(request):

    context = {
        'title': 'Zarządzanie alertami',
        'message': 'Funkcjonalność alertów będzie dostępna w przyszłych wersjach.',
    }
    return render(request, 'alerts_management.html', context)


@login_required
@admin_required
def import_utility_data(request):
    """Import danych zużycia mediów z CSV"""
    from .forms import UtilityConsumptionImportForm
    from datetime import datetime

    if request.method == 'POST':
        form = UtilityConsumptionImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            count = 0
            for row in reader:
                try:
                    apartment = Apartment.objects.get(number=row['apartment_number'])

                    # Formatowanie dat
                    period_start = datetime.strptime(row['period_start'], '%Y-%m-%d').date()
                    period_end = datetime.strptime(row['period_end'], '%Y-%m-%d').date()

                    # Tworzenie lub aktualizacja zużycia
                    consumption, created = UtilityConsumption.objects.update_or_create(
                        apartment=apartment,
                        utility_type=row['utility_type'],
                        period_start=period_start,
                        defaults={
                            'period_end': period_end,
                            'consumption': float(row['consumption']),
                            'unit': row['unit'],
                            'cost': float(row['cost'])
                        }
                    )
                    count += 1

                except Exception as e:
                    messages.error(request, f"Błąd w wierszu {count+1}: {e}")

            messages.success(request, f"Zaimportowano dane zużycia dla {count} rekordów")
            return redirect('app:consumption_trends')
    else:
        form = UtilityConsumptionImportForm()

    return render(request, 'utility_consumption_import.html', {
        'form': form,
        'title': 'Import danych zużycia'
    })


def alerts_system(request):
    """Uproszczony system alertów"""
    alerts = []

    # Sprawdzenie zaległych płatności
    overdue_payments = Payment.objects.filter(
        status='pending',
        date__lt=timezone.now().date()
    )[:5]  # Limit do 5 najpilniejszych

    for payment in overdue_payments:
        alerts.append({
            'type': 'warning',
            'apartment': payment.tenant.apartment,
            'message': f'Mieszkanie {payment.tenant.apartment.number} zalega z płatnością',
            'amount': payment.amount
        })

    # Pobierz aktywne alerty z bazy danych
    db_alerts = BuildingAlert.objects.filter(is_active=True)[:10]  # Limit do 10 alertów

    return render(request, 'alerts_system.html', {
        'alerts': alerts,
        'db_alerts': db_alerts,
        'title': 'System alertów i powiadomień',
        'message': 'System alertów jest w pełni funkcjonalny. Poniżej wyświetlane są aktywne alerty.'
    })


# ─── ZARZĄDZANIE MIESZKANIAMI ───────────────────────────
@admin_required
def apartment_list(request):
    """Lista mieszkań"""
    apartments = Apartment.objects.all()
    context = {'apartments': apartments}
    return render(request, 'apartment_list.html', context)


@login_required
def apartment_detail(request, pk):
    """Szczegóły mieszkania"""
    apartment = get_object_or_404(Apartment, pk=pk)

    # Sprawdzenie uprawnień
    if not request.user.is_staff:
        try:
            tenant = Tenant.objects.get(user=request.user)
            if tenant.apartment.id != apartment.id:
                raise PermissionDenied
        except Tenant.DoesNotExist:
            raise PermissionDenied

    context = {'apartment': apartment}
    return render(request, 'apartment_detail.html', context)


# ─── ZARZĄDZANIE NAJEMCAMI ─────────────────────────────
@admin_required
def tenant_list(request):
    """Lista najemców"""
    tenants = Tenant.objects.select_related('user', 'apartment')
    context = {'tenants': tenants}
    return render(request, 'tenant_list.html', context)


@login_required
def tenant_detail(request, pk):
    """Szczegóły najemcy"""
    tenant = get_object_or_404(Tenant, pk=pk)

    # Sprawdzenie uprawnień
    if not request.user.is_staff and request.user != tenant.user:
        raise PermissionDenied

    context = {'tenant': tenant}
    return render(request, 'tenant_detail.html', context)


# ─── ZARZĄDZANIE PŁATNOŚCIAMI ───────────────────────────
@login_required
def payment_list(request):
    """Lista płatności"""
    if request.user.is_staff:
        payments = Payment.objects.select_related('tenant', 'tenant__apartment')
    else:
        tenant = get_object_or_404(Tenant, user=request.user)
        payments = Payment.objects.filter(tenant=tenant)

    context = {'payments': payments}
    return render(request, 'payment_list.html', context)


@login_required
def payment_detail(request, pk):
    """Szczegóły płatności"""
    payment = get_object_or_404(Payment, pk=pk)

    # Sprawdzenie uprawnień
    if not request.user.is_staff and payment.tenant.user != request.user:
        raise PermissionDenied

    context = {'payment': payment}
    return render(request, 'payment_detail.html', context)


# ─── SZCZEGÓŁY ZGŁOSZENIA ─────────────────────────────
@login_required
def ticket_detail(request, pk):
    """Szczegóły zgłoszenia"""
    ticket = get_object_or_404(Ticket, pk=pk)

    # Sprawdzenie uprawnień
    if not request.user.is_staff and ticket.tenant.user != request.user:
        raise PermissionDenied

    context = {'ticket': ticket}
    return render(request, 'ticket_detail.html', context)
