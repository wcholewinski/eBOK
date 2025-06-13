from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from app.models import Apartment, UtilityConsumption
from app.decorators import admin_required
from app.utils.csv_import import CSVImporter
from app.utils.ml_analysis import PredictiveAnalysis


@admin_required
@require_http_methods(["GET", "POST"])
def import_and_analyze(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Proszę wybrać plik CSV')
            return redirect('app:import_and_analyze')

        csv_file = request.FILES['csv_file']
        model_type = request.POST.get('model_type', 'utility_consumption')
        run_ml = request.POST.get('run_ml', 'off') == 'on'

        # Import danych z pliku CSV
        # 1. Tworzymy instancję importera z wybranym plikiem i typem modelu
        importer = CSVImporter(csv_file, model_type)

        if not importer.load_preview() or not importer.import_data():
            for error in importer.errors:
                messages.error(request, error)
            return redirect('app:import_and_analyze')

        summary = importer.get_summary()
        messages.success(request, f"Zaimportowano {summary['imported']} rekordów")

        if run_ml:
            analyzer = PredictiveAnalysis()

            try:
                if model_type == 'utility_consumption':
                    # Prognozy dla mieszkań
                    apartment_ids = UtilityConsumption.objects.values_list('apartment_id', flat=True).distinct()[
                                    :5]  # Max 5 mieszkań

                    predictions = {}
                    for apt_id in apartment_ids:
                        predictions[apt_id] = analyzer.predict_utility_consumption(apt_id)

                    request.session['ml_predictions'] = str(len(predictions))
                    messages.success(request, f"Wygenerowano prognozy ML dla {len(predictions)} mieszkań")

                    # Wykryj anomalie
                    anomalies = analyzer.detect_anomalies()
                    if anomalies:
                        messages.warning(request, f"Wykryto {len(anomalies)} anomalii w zużyciu")

                    return redirect('app:consumption_trends')

                elif model_type == 'apartment':
                    # Clustering mieszkań
                    clusters = analyzer.apartment_clustering()
                    if 'error' not in clusters:
                        messages.info(request, f"Pogrupowano mieszkania w {len(clusters['clusters'])} klastry")

                    # Wskaźnik efektywności
                    efficiency = analyzer.building_efficiency_score()
                    messages.info(request, f"Efektywność budynku: {efficiency}%")

                    return redirect('app:analytics_dashboard')

                elif model_type == 'payment':
                    # Prognozy finansowe
                    profit_predictions = analyzer.calculate_profit_predictions()
                    request.session['profit_count'] = str(len(profit_predictions))
                    messages.success(request, "Wygenerowano prognozy finansowe ML")

                    return redirect('app:profit_prediction')

            except Exception as e:
                messages.error(request, f"Błąd analizy ML: {str(e)}")

        return redirect('app:import_and_analyze')

    # Formularz - używamy nowego szablonu bazowego
    return render(request, 'import_analyze.html', {
        'title': 'Import i analiza ML',
        'model_types': [
            ('apartment', 'Mieszkania'),
            ('utility_consumption', 'Zużycie mediów'),
            ('payment', 'Płatności')
        ]
    })
