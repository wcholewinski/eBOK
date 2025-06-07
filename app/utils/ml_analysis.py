import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from app.models import Apartment, UtilityConsumption, Payment, Tenant


class PredictiveAnalysis:
    """Klasa do analizy predykcyjnej danych budynku."""

    def __init__(self):
        """Inicjalizacja klasy analizy predykcyjnej."""
        self.seasonal_factors = {
            'electricity': [0.9, 0.85, 0.8, 0.75, 0.8, 0.85, 0.9, 0.95, 0.85, 0.9, 1.0, 1.1],
            'water': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'gas': [1.5, 1.4, 1.2, 1.0, 0.8, 0.6, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4],
            'heating': [1.8, 1.6, 1.2, 0.8, 0.3, 0.0, 0.0, 0.0, 0.2, 0.6, 1.0, 1.4]
        }

    def predict_utility_consumption(self, apartment_id, utility_type=None, months=6):
        """
        Przewiduje zużycie mediów dla mieszkania.

        Args:
            apartment_id: ID mieszkania
            utility_type: Typ medium ('electricity', 'water', 'gas', 'heating')
            months: Liczba miesięcy do prognozy

        Returns:
            Dict z prognozami lub lista prognoz dla wszystkich typów mediów
        """
        try:
            apartment = Apartment.objects.get(id=apartment_id)
        except Apartment.DoesNotExist:
            return {}

        # Jeśli nie podano typu medium, zwróć prognozy dla wszystkich
        if utility_type is None:
            predictions = {}
            for ut in ['electricity', 'water', 'gas', 'heating']:
                predictions[ut] = self._predict_single_utility(apartment, ut, months)
            return predictions

        return self._predict_single_utility(apartment, utility_type, months)

    def _predict_single_utility(self, apartment, utility_type, months):
        """Przewiduje zużycie dla jednego typu medium."""
        # Pobierz historyczne dane
        historical_data = UtilityConsumption.objects.filter(
            apartment=apartment,
            utility_type=utility_type
        ).order_by('period_start')

        if not historical_data.exists():
            return self._generate_default_prediction(apartment, utility_type, months)

        # Analiza historyczna
        consumption_values = [record.consumption for record in historical_data]

        # Oblicz średnie zużycie
        avg_consumption = np.mean(consumption_values)

        # Oblicz trend (prosta regresja liniowa)
        if len(consumption_values) > 1:
            x = np.arange(len(consumption_values))
            trend = np.polyfit(x, consumption_values, 1)[0]
        else:
            trend = 0

        # Generuj prognozy
        predictions = []
        current_date = datetime.now().date()

        for i in range(months):
            # Data przyszła
            future_date = current_date + timedelta(days=30 * (i + 1))
            month_index = (future_date.month - 1) % 12

            # Czynnik sezonowy
            seasonal_factor = self.seasonal_factors.get(utility_type, [1.0] * 12)[month_index]

            # Czynnik trendu
            trend_factor = 1 + (trend * i * 0.01)  # Ograniczony wpływ trendu

            # Czynnik losowy (niewielkie wahania)
            random_factor = np.random.uniform(0.95, 1.05)

            # Oblicz przewidywane zużycie
            predicted_consumption = avg_consumption * seasonal_factor * trend_factor * random_factor

            # Ograniczenia realistyczne
            predicted_consumption = max(0, predicted_consumption)

            predictions.append({
                'date': future_date,
                'consumption': round(predicted_consumption, 2),
                'unit': self._get_unit(utility_type),
                'confidence': self._calculate_confidence(len(consumption_values), i)
            })

        return predictions

    def _generate_default_prediction(self, apartment, utility_type, months):
        """Generuje domyślne prognozy w przypadku braku danych historycznych."""
        # Domyślne wartości bazowe w zależności od powierzchni mieszkania
        base_values = {
            'electricity': apartment.area * 1.5,  # kWh na m²
            'water': apartment.area * 0.1,  # m³ na m²
            'gas': apartment.area * 0.8,  # m³ na m²
            'heating': apartment.area * 2.0  # kWh na m²
        }

        base_consumption = base_values.get(utility_type, 100)
        predictions = []
        current_date = datetime.now().date()

        for i in range(months):
            future_date = current_date + timedelta(days=30 * (i + 1))
            month_index = (future_date.month - 1) % 12

            seasonal_factor = self.seasonal_factors.get(utility_type, [1.0] * 12)[month_index]
            random_factor = np.random.uniform(0.9, 1.1)

            predicted_consumption = base_consumption * seasonal_factor * random_factor

            predictions.append({
                'date': future_date,
                'consumption': round(predicted_consumption, 2),
                'unit': self._get_unit(utility_type),
                'confidence': 0.5  # Niska pewność dla domyślnych prognoz
            })

        return predictions

    def predict_costs(self, apartment_id, months=6):
        """
        Przewiduje koszty mediów dla mieszkania.

        Args:
            apartment_id: ID mieszkania
            months: Liczba miesięcy do prognozy

        Returns:
            Dict z prognozami kosztów
        """
        # Stawki za media (PLN za jednostkę)
        unit_rates = {
            'electricity': 0.8,  # PLN/kWh
            'water': 12.0,  # PLN/m³
            'gas': 3.2,  # PLN/m³
            'heating': 0.65  # PLN/kWh
        }

        consumption_predictions = self.predict_utility_consumption(apartment_id, months=months)

        cost_predictions = {
            'total': [],
            'detailed': {}
        }

        # Oblicz koszty dla każdego typu medium
        for utility_type, predictions in consumption_predictions.items():
            utility_costs = []
            rate = unit_rates.get(utility_type, 1.0)

            for prediction in predictions:
                cost = prediction['consumption'] * rate
                utility_costs.append({
                    'date': prediction['date'],
                    'cost': round(cost, 2),
                    'consumption': prediction['consumption'],
                    'unit': prediction['unit'],
                    'rate': rate
                })

            cost_predictions['detailed'][utility_type] = utility_costs

        # Oblicz łączne koszty miesięczne
        for i in range(months):
            total_cost = 0
            date = None

            for utility_type in cost_predictions['detailed']:
                if i < len(cost_predictions['detailed'][utility_type]):
                    total_cost += cost_predictions['detailed'][utility_type][i]['cost']
                    if date is None:
                        date = cost_predictions['detailed'][utility_type][i]['date']

            cost_predictions['total'].append({
                'date': date,
                'total_cost': round(total_cost, 2)
            })

        return cost_predictions

    def calculate_profit_predictions(self, months=6):
        """
        Oblicza prognozy zysków z całego budynku.

        Args:
            months: Liczba miesięcy do prognozy

        Returns:
            Lista z prognozami zysków
        """
        apartments = Apartment.objects.all()
        predictions = []

        # Oblicz bazowe przychody i koszty
        monthly_income_base = sum(apt.rent for apt in apartments)
        monthly_cost_base = monthly_income_base * 0.3  # Szacunkowe koszty 30% przychodów

        current_date = datetime.now().date()

        for i in range(months):
            future_date = current_date + timedelta(days=30 * (i + 1))

            # Czynnik sezonowy dla kosztów (wyższe zimą)
            month_index = (future_date.month - 1) % 12
            seasonal_cost_factor = 1.0 + 0.3 * max(0, np.cos(np.pi * month_index / 6))

            # Przewidywane przychody (z małymi wahaniami)
            income = monthly_income_base * np.random.uniform(0.95, 1.05)

            # Przewidywane koszty (z czynnikiem sezonowym)
            cost = monthly_cost_base * seasonal_cost_factor * np.random.uniform(0.9, 1.1)

            # Zysk
            profit = income - cost

            predictions.append({
                'date': future_date,
                'income': round(income, 2),
                'cost': round(cost, 2),
                'profit': round(profit, 2),
                'profit_margin': round((profit / income) * 100, 1) if income > 0 else 0
            })

        return predictions

    def building_efficiency_score(self):
        """
        Oblicza wskaźnik efektywności budynku.

        Returns:
            Float: Wskaźnik efektywności (0-100)
        """
        try:
            # Pobierz dane z ostatnich 6 miesięcy
            six_months_ago = timezone.now().date() - timedelta(days=180)

            # Wskaźniki do analizy
            recent_consumption = UtilityConsumption.objects.filter(
                period_start__gte=six_months_ago
            )

            if not recent_consumption.exists():
                return 50.0  # Domyślna wartość

            # Średnie zużycie na m²
            total_area = sum(apt.area for apt in Apartment.objects.all())
            if total_area == 0:
                return 50.0

            # Analiza zużycia energii
            electricity_consumption = recent_consumption.filter(
                utility_type='electricity'
            ).aggregate(avg_consumption=Avg('consumption'))['avg_consumption'] or 0

            electricity_per_sqm = electricity_consumption / total_area if total_area > 0 else 0

            # Benchmarki (kWh/m²/miesiąc)
            excellent_benchmark = 8.0
            good_benchmark = 12.0
            poor_benchmark = 20.0

            # Oblicz wskaźnik efektywności
            if electricity_per_sqm <= excellent_benchmark:
                efficiency = 90 + (excellent_benchmark - electricity_per_sqm) * 2
            elif electricity_per_sqm <= good_benchmark:
                efficiency = 70 + (good_benchmark - electricity_per_sqm) * 5
            elif electricity_per_sqm <= poor_benchmark:
                efficiency = 30 + (poor_benchmark - electricity_per_sqm) * 2
            else:
                efficiency = max(10, 30 - (electricity_per_sqm - poor_benchmark))

            # Dodatkowe punkty za regularność płatności
            recent_payments = Payment.objects.filter(
                date__gte=six_months_ago,
                status='paid'
            ).count()

            total_payments = Payment.objects.filter(
                date__gte=six_months_ago
            ).count()

            payment_rate = recent_payments / total_payments if total_payments > 0 else 1.0
            payment_bonus = payment_rate * 10

            final_score = min(100, max(0, efficiency + payment_bonus))

            return round(final_score, 1)

        except Exception:
            return 50.0  # Domyślna wartość w przypadku błędu

    def detect_anomalies(self, apartment_id=None):
        """
        Wykrywa anomalie w zużyciu mediów.

        Args:
            apartment_id: ID mieszkania (opcjonalne)

        Returns:
            Lista wykrytych anomalii
        """
        anomalies = []

        # Filtr mieszkań
        if apartment_id:
            apartments = Apartment.objects.filter(id=apartment_id)
        else:
            apartments = Apartment.objects.all()

        for apartment in apartments:
            for utility_type in ['electricity', 'water', 'gas', 'heating']:
                consumption_data = UtilityConsumption.objects.filter(
                    apartment=apartment,
                    utility_type=utility_type
                ).order_by('period_start')

                if consumption_data.count() < 3:
                    continue

                values = [record.consumption for record in consumption_data]
                mean_consumption = np.mean(values)
                std_consumption = np.std(values)

                # Wykryj wartości odstające (powyżej 2 odchyleń standardowych)
                threshold = mean_consumption + 2 * std_consumption

                for record in consumption_data:
                    if record.consumption > threshold:
                        anomalies.append({
                            'apartment': apartment.number,
                            'utility_type': utility_type,
                            'date': record.period_start,
                            'consumption': record.consumption,
                            'expected_max': round(threshold, 2),
                            'severity': 'high' if record.consumption > threshold * 1.5 else 'medium'
                        })

        return anomalies

    def _get_unit(self, utility_type):
        """Zwraca jednostkę dla danego typu medium."""
        units = {
            'electricity': 'kWh',
            'water': 'm³',
            'gas': 'm³',
            'heating': 'kWh'
        }
        return units.get(utility_type, 'jednostka')

    def _calculate_confidence(self, historical_data_points, forecast_period):
        """Oblicza poziom pewności prognozy."""
        # Bazowy poziom pewności zależny od ilości danych historycznych
        base_confidence = min(0.9, historical_data_points * 0.1)

        # Zmniejsz pewność dla dalszych prognoz
        time_decay = max(0.3, 1.0 - (forecast_period * 0.1))

        return round(base_confidence * time_decay, 2)
