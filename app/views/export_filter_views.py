import datetime
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.urls import reverse

from app.models import Apartment, UtilityConsumption
from app.views import admin_required


def _get_common_filter_context(request, apartments=None, utility_types=None):
    """Zwraca wspólny kontekst dla formularzy filtrowania"""
    return {
        'apartments': apartments or Apartment.objects.all().order_by('number'),
        'utility_types': utility_types or UtilityConsumption.UTILITY_TYPES,
        'apartment_id': request.GET.get('apartment_id', ''),
        'utility_type_selected': request.GET.get('utility_type', ''),
        'months': request.GET.get('months', '6'),
    }


@admin_required
@require_GET
def utility_export_filter(request):
    """Formularz do filtrowania eksportu danych zużycia mediów"""
    context = _get_common_filter_context(request)
    context.update({
        'title': 'Eksport danych zużycia mediów',
        'form_action': reverse('app:export_utility_consumption_csv'),
        'cancel_url': reverse('app:consumption_trends'),
        'show_apartment_filter': True,
        'show_utility_filter': True,
        'show_date_filter': True,
        'export_info': 'Wybierz filtry, aby wyeksportować dane zużycia mediów do pliku CSV.'
    })

    return render(request, 'export_filter_form.html', context)


@admin_required
@require_GET
def prediction_export_filter(request):
    """Formularz do filtrowania eksportu danych predykcyjnych"""
    # Typ predykcji i konfiguracja w zależności od typu
    prediction_type = request.GET.get('type', 'consumption')

    # Konfiguracja opcji dla różnych typów predykcji
    prediction_configs = {
        'consumption': {
            'title': 'Eksport predykcji zużycia mediów',
            'export_info': 'Wybierz mieszkanie i rodzaj mediów, aby wyeksportować predykcje zużycia do pliku CSV.',
            'show_apartment_filter': True,
            'show_utility_filter': True,
        },
        'cost': {
            'title': 'Eksport predykcji kosztów',
            'export_info': 'Wybierz mieszkanie i opcjonalnie rodzaj mediów, aby wyeksportować predykcje kosztów do pliku CSV.',
            'show_apartment_filter': True,
            'show_utility_filter': True,
        },
        'income': {
            'title': 'Eksport predykcji przychodów',
            'export_info': 'Wybierz liczbę miesięcy, aby wyeksportować predykcje przychodów do pliku CSV.',
            'show_apartment_filter': False,
            'show_utility_filter': False,
        },
        'profit': {
            'title': 'Eksport predykcji zysków',
            'export_info': 'Wybierz liczbę miesięcy, aby wyeksportować predykcje zysków do pliku CSV.',
            'show_apartment_filter': False,
            'show_utility_filter': False,
        }
    }

    # Użyj domyślnej konfiguracji, jeśli typ nie jest obsługiwany
    config = prediction_configs.get(prediction_type, prediction_configs['consumption'])

    # Przygotuj kontekst
    context = _get_common_filter_context(request)
    context.update({
        'title': config['title'],
        'form_action': reverse('app:export_prediction_csv') + f'?type={prediction_type}',
        'cancel_url': reverse('app:analytics_dashboard'),
        'show_apartment_filter': config['show_apartment_filter'],
        'show_utility_filter': config['show_utility_filter'],
        'show_months_filter': True,
        'export_info': config['export_info']
    })

    return render(request, 'export_filter_form.html', context)
