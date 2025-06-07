import io
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from app.models import Apartment, UtilityConsumption
from app.decorators import admin_required
from app.utils.csv_import import CSVImporter
from app.ml_analysis import MLAnalysis as PredictiveAnalysis


@admin_required
@require_http_methods(["GET", "POST"])
def import_and_analyze(request):
    """Import danych z CSV z następującą analizą predykcyjną"""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Proszę wybrać plik CSV do importu')
            return redirect('app:import_and_analyze')

        csv_file = request.FILES['csv_file']
        model_type = request.POST.get('model_type', 'utility_consumption')
        date_format = request.POST.get('date_format', '%Y-%m-%d')
        run_prediction = request.POST.get('run_prediction', 'off') == 'on'

        # Inicjalizacja importera
        importer = CSVImporter(csv_file, model_type)

        # Ładowanie podglądu
        if not importer.load_preview():
            for error in importer.errors:
                messages.error(request, error)
            return redirect('app:import_and_analyze')

        # Wymagane pola dla różnych typów danych
        required_fields = {
            'apartment': ['number', 'floor', 'area'],
            'utility_consumption': ['apartment_number', 'utility_type', 'period_start', 'period_end', 'consumption', 'unit', 'cost'],
            'payment': ['tenant_id', 'date', 'amount', 'type', 'status']
        }

        # Walidacja nagłówków
        if not importer.validate_headers(required_fields.get(model_type, [])):
            for error in importer.errors:
                messages.error(request, error)
            return redirect('app:import_and_analyze')

        # Import danych
        import_success = importer.import_data(date_format=date_format)

        # Podsumowanie importu
        summary = importer.get_summary()

        messages.success(
            request, 
            f"Zaimportowano {summary['imported']} rekordów, zaktualizowano {summary['updated']}, pominięto {summary['skipped']}"
        )

        # Wyświetlenie błędów
        for error in summary['errors']:
            messages.warning(request, error)

        # Uruchomienie analizy predykcyjnej, jeśli wybrano
        if import_success and run_prediction:
            analyzer = PredictiveAnalysis()
            predictions = {}

            if model_type == 'utility_consumption':
                # Pobranie unikalnych mieszkań z zaimportowanych danych
                apartment_ids = UtilityConsumption.objects.values_list('apartment_id', flat=True).distinct()

                # Generowanie predykcji dla każdego mieszkania
                for apt_id in apartment_ids:
                    predictions[apt_id] = {
                        'consumption': analyzer.predict_utility_consumption(apt_id),
                        'costs': analyzer.predict_costs(apt_id)
                    }

                # Zapisz wyniki analizy w sesji
                request.session['prediction_results'] = str(predictions)
                messages.success(request, f"Wygenerowano predykcje dla {len(apartment_ids)} mieszkań")

                # Przekierowanie do widoku analizy
                return redirect('app:consumption_trends')

            elif model_type == 'apartment':
                # Generowanie predykcji dla zaimportowanych mieszkań
                apartment_ids = Apartment.objects.values_list('id', flat=True)

                # Obliczanie ogólnej efektywności budynku
                efficiency_score = analyzer.building_efficiency_score()
                messages.info(request, f"Wynik efektywności budynku: {efficiency_score}")

                # Przekierowanie do panelu analitycznego
                return redirect('app:analytics_dashboard')

            elif model_type == 'payment':
                # Generowanie prognoz finansowych
                profit_predictions = analyzer.calculate_profit_predictions()

                # Zapisz wyniki w sesji
                request.session['profit_predictions'] = str(profit_predictions)
                messages.success(request, "Wygenerowano prognozy finansowe")

                # Przekierowanie do widoku prognoz finansowych
                return redirect('app:profit_prediction')

        return redirect('app:import_and_analyze')

    # Wyświetlenie formularza
    return render(request, 'import_analyze_form.html', {
        'title': 'Import i analiza danych',
        'model_types': [
            ('apartment', 'Mieszkania'),
            ('utility_consumption', 'Zużycie mediów'),
            ('payment', 'Płatności')
        ],
        'date_formats': [
            ('%Y-%m-%d', 'YYYY-MM-DD (np. 2023-01-31)'),
            ('%d.%m.%Y', 'DD.MM.YYYY (np. 31.01.2023)'),
            ('%m/%d/%Y', 'MM/DD/YYYY (np. 01/31/2023)')
        ]
    })
