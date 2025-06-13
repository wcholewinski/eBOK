import datetime
import csv
import io
import pandas as pd

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.utils import translation

from app.models import Apartment, UtilityConsumption, Payment, Tenant
from app.utils.csv_export import CSVExporter
from app.views import admin_required
from app.utils.ml_analysis import PredictiveAnalysis


def _parse_date(date_str):
    """Parsuje datę z formatu Y-m-d"""
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    except ValueError:
        return None


@admin_required
@require_GET
def export_utility_consumption_csv(request):
    """Eksportuje dane zużycia mediów do pliku CSV"""
    apartment_id = request.GET.get('apartment_id', None)
    utility_type = request.GET.get('utility_type', None)

    # Parsowanie dat
    start_date = _parse_date(request.GET.get('start_date', None))
    end_date = _parse_date(request.GET.get('end_date', None))

    if not start_date and request.GET.get('start_date'):
        messages.error(request, 'Nieprawidłowy format daty początkowej. Używam domyślnej wartości.')

    if not end_date and request.GET.get('end_date'):
        messages.error(request, 'Nieprawidłowy format daty końcowej. Używam domyślnej wartości.')

    locale = translation.get_language() or 'pl'
    headers, df = CSVExporter.get_utility_consumption_data(
        apartment_id=apartment_id,
        utility_type=utility_type,
        start_date=start_date,
        end_date=end_date,
        locale=locale
    )

    if df.empty:
        messages.warning(request, 'Brak danych do eksportu z wybranymi filtrami.')
        return redirect(request.META.get('HTTP_REFERER', 'app:consumption_trends'))

    # Nazwa pliku
    filename = 'zuzycie_mediow.csv' if locale == 'pl' else 'utility_consumption.csv'
    if apartment_id:
        try:
            apt_number = Apartment.objects.get(id=apartment_id).number
            filename = f'zuzycie_mediow_mieszkanie_{apt_number}.csv' if locale == 'pl' else f'utility_consumption_apt_{apt_number}.csv'
        except Apartment.DoesNotExist:
            pass

    return CSVExporter.export_to_response(df, filename)


@admin_required
@require_GET
def export_payment_csv(request):
    """Eksportuje dane płatności do pliku CSV"""
    tenant_id = request.GET.get('tenant_id', None)
    status = request.GET.get('status', None)

    # Parsowanie dat
    start_date = _parse_date(request.GET.get('start_date', None))
    end_date = _parse_date(request.GET.get('end_date', None))

    if not start_date and request.GET.get('start_date'):
        messages.error(request, 'Nieprawidłowy format daty początkowej. Używam domyślnej wartości.')

    if not end_date and request.GET.get('end_date'):
        messages.error(request, 'Nieprawidłowy format daty końcowej. Używam domyślnej wartości.')

    locale = translation.get_language() or 'pl'
    headers, df = CSVExporter.get_payment_data(
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
        status=status,
        locale=locale
    )

    if df.empty:
        messages.warning(request, 'Brak danych do eksportu z wybranymi filtrami.')
        return redirect(request.META.get('HTTP_REFERER', 'app:payment_list'))

    filename = 'platnosci.csv' if locale == 'pl' else 'payments.csv'
    return CSVExporter.export_to_response(df, filename)


@admin_required
@require_GET
def export_prediction_csv(request):
    """Eksportuje dane predykcyjne do pliku CSV"""
    prediction_type = request.GET.get('type', None)
    apartment_id = request.GET.get('apartment_id', None)
    utility_type = request.GET.get('utility_type', None)

    # Walidacja i konwersja forecast_months
    try:
        forecast_months = int(request.GET.get('months', 6))
        if forecast_months < 1 or forecast_months > 24:
            forecast_months = 6
    except ValueError:
        forecast_months = 6

    # Walidacja typu predykcji
    valid_types = ['consumption', 'cost', 'income', 'profit']
    if prediction_type not in valid_types:
        messages.error(request, 'Nieprawidłowy typ predykcji.')
        return redirect('app:analytics_dashboard')

    # Sprawdź czy wymagane parametry są obecne
    if prediction_type == 'consumption' and (not apartment_id or not utility_type):
        messages.error(request, 'Brak wymaganego ID mieszkania lub typu mediów.')
        return redirect('app:consumption_trends')
    elif prediction_type == 'cost' and not apartment_id:
        messages.error(request, 'Brak wymaganego ID mieszkania.')
        return redirect('app:consumption_trends')

    locale = translation.get_language() or 'pl'
    analyzer = PredictiveAnalysis()

    # Mapowanie typów predykcji na funkcje i nazwy plików
    prediction_handlers = {
        'consumption': {
            'func': lambda: analyzer.predict_utility_consumption(apartment_id, utility_type, forecast_months),
            'filename': 'prognoza_zuzycia.csv' if locale == 'pl' else 'consumption_prediction.csv'
        },
        'cost': {
            'func': lambda: _handle_cost_predictions(analyzer, apartment_id, utility_type, forecast_months, locale),
            'filename': _get_cost_filename(utility_type, locale)
        },
        'income': {
            'func': lambda: analyzer.calculate_profit_predictions(forecast_months),  # Używamy calculate_profit_predictions zamiast predict_income
            'filename': 'prognoza_przychodow.csv' if locale == 'pl' else 'income_prediction.csv'
        },
        'profit': {
            'func': lambda: analyzer.calculate_profit_predictions(forecast_months),
            'filename': 'prognoza_zyskow.csv' if locale == 'pl' else 'profit_prediction.csv'
        }
    }

    # Wygeneruj odpowiednie predykcje
    handler = prediction_handlers[prediction_type]
    predictions = handler['func']()
    filename = handler['filename']

    if not predictions:
        messages.warning(request, 'Brak danych predykcyjnych do eksportu.')
        return redirect('app:analytics_dashboard')

    # Eksport do CSV
    headers, df = CSVExporter.get_predictive_data(predictions, prediction_type, locale)
    return CSVExporter.export_to_response(df, filename)


def _handle_cost_predictions(analyzer, apartment_id, utility_type, forecast_months, locale):
    """Obsługuje generowanie predykcji kosztów"""
    cost_data = analyzer.predict_costs(apartment_id, forecast_months)

    if utility_type and utility_type in cost_data['detailed']:
        return cost_data['detailed'][utility_type]
    return cost_data['total']


def _get_cost_filename(utility_type, locale):
    """Zwraca nazwę pliku dla predykcji kosztów"""
    if utility_type:
        return f'prognoza_kosztow_{utility_type}.csv' if locale == 'pl' else f'cost_prediction_{utility_type}.csv'
    return 'prognoza_kosztow.csv' if locale == 'pl' else 'cost_prediction.csv'


@admin_required
@require_GET
def export_ml_dataset(request):
    """Eksportuje kompletny zestaw danych do analiz ML w formacie CSV zamiast Excel"""
    import csv
    try:
        # Definicje pól do eksportu
        data_models = {
            'Mieszkania': {
                'queryset': Apartment.objects.all().order_by('number'),
                'fields': None  # Wszystkie pola
            },
            'Zużycie mediów': {
                'queryset': UtilityConsumption.objects.all().order_by('period_start'),
                'fields': ['id', 'apartment_id', 'apartment__number', 'utility_type', 
                          'period_start', 'period_end', 'consumption', 'unit', 'cost'],
                'rename': {'apartment__number': 'apartment_number'}
            },
            'Płatności': {
                'queryset': Payment.objects.all().order_by('date'),
                'fields': ['id', 'tenant_id', 'tenant__apartment_id', 'tenant__apartment__number',
                          'date', 'amount', 'type', 'status'],
                'rename': {
                    'tenant__apartment_id': 'apartment_id',
                    'tenant__apartment__number': 'apartment_number'
                }
            }
        }

        # Przygotowujemy odpowiedź CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=dane_do_analizy_ml.csv'

        writer = csv.writer(response)

        # Wybieramy tylko jeden model dla prostszej implementacji CSV
        # Można później rozbudować o eksport wielu plików ZIP
        config = data_models['Mieszkania']

        # Pobierz dane z queryset
        if config['fields']:
            data_values = list(config['queryset'].values(*config['fields']))
        else:
            data_values = list(config['queryset'].values())

        # Jeśli mamy dane, zapisz nagłówki i wiersze
        if data_values:
            # Zapisz nagłówki
            headers = list(data_values[0].keys())
            writer.writerow(headers)

            # Zapisz wiersze
            for item in data_values:
                row = [str(item[field]) for field in headers]
                writer.writerow(row)

        return response
    except Exception as e:
        messages.error(request, f"Błąd podczas eksportu danych: {e}")
        return redirect('app:analytics_dashboard')
