import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db.models import Avg
from django.utils import timezone
from app.models import Apartment, UtilityConsumption, Payment

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings('ignore')


class PredictiveAnalysis:
    """Uproszczona klasa analizy predykcyjnej z sklearn."""

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.clusterer = KMeans(n_clusters=3, random_state=42)

    def _get_data(self, apartment_id=None, utility_type=None):
        """Pobiera i przygotowuje dane do ML."""
        queryset = UtilityConsumption.objects.all()
        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)
        if utility_type:
            queryset = queryset.filter(utility_type=utility_type)

        data = []
        for record in queryset:
            tenant = record.apartment.tenant_set.first()
            data.append({
                'consumption': record.consumption,
                'area': record.apartment.area,
                'occupants': tenant.num_occupants if tenant else 1,
                'month': record.period_start.month,
                'apartment_id': record.apartment.id
            })

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
        return df

    def predict_utility_consumption(self, apartment_id, utility_type=None, months=6):
        """Przewiduje zużycie używając Random Forest."""
        if utility_type is None:
            return {ut: self.predict_utility_consumption(apartment_id, ut, months)
                    for ut in ['electricity', 'water', 'gas', 'heating']}

        # Pobierz dane
        df = self._get_data(apartment_id, utility_type)
        if df.empty or len(df) < 5:
            return self._fallback_prediction(apartment_id, utility_type, months)

        # Trenuj model
        features = ['area', 'occupants', 'sin_month', 'cos_month']
        X = df[features]
        y = df['consumption']

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        # Generuj prognozy
        apartment = Apartment.objects.get(id=apartment_id)
        tenant = apartment.tenant_set.first()

        predictions = []
        for i in range(months):
            future_date = datetime.now().date() + timedelta(days=30 * (i + 1))
            month = future_date.month

            X_pred = [[
                apartment.area,
                tenant.num_occupants if tenant else 1,
                np.sin(2 * np.pi * month / 12),
                np.cos(2 * np.pi * month / 12)
            ]]

            X_pred_scaled = self.scaler.transform(X_pred)
            consumption = max(0, self.model.predict(X_pred_scaled)[0])

            predictions.append({
                'date': future_date,
                'consumption': round(consumption, 2),
                'unit': self._get_unit(utility_type),
                'confidence': round(0.8 - i * 0.1, 2)  # Spadająca pewność
            })

        return predictions

    def detect_anomalies(self, apartment_id=None):
        """Wykrywa anomalie używając Isolation Forest."""
        df = self._get_data(apartment_id)
        if df.empty or len(df) < 10:
            return []

        features = ['consumption', 'area', 'occupants']
        X = df[features].fillna(0)

        anomalies = self.anomaly_detector.fit_predict(X)

        results = []
        for idx, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:  # Anomalia
                row = df.iloc[idx]
                results.append({
                    'apartment_id': row['apartment_id'],
                    'consumption': row['consumption'],
                    'severity': 'high' if row['consumption'] > df['consumption'].mean() * 2 else 'medium'
                })

        return results

    def apartment_clustering(self):
        """Grupuje mieszkania używając K-Means."""
        df = self._get_data()
        if df.empty or len(df) < 3:
            return {'error': 'Za mało danych'}

        # Agreguj dane po mieszkaniach
        apartment_data = df.groupby('apartment_id').agg({
            'consumption': 'mean',
            'area': 'first',
            'occupants': 'first'
        }).reset_index()

        features = ['consumption', 'area', 'occupants']
        X = apartment_data[features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        clusters = self.clusterer.fit_predict(X_scaled)
        apartment_data['cluster'] = clusters

        return {
            'clusters': {f'cluster_{i}': apartment_data[apartment_data['cluster'] == i]['apartment_id'].tolist()
                         for i in range(3)},
            'data': apartment_data.to_dict('records')
        }

    def building_efficiency_score(self):
        """Oblicza wskaźnik efektywności."""
        df = self._get_data()
        if df.empty:
            return 50.0

        # Prosta metryka: średnie zużycie na m²
        efficiency = df['consumption'] / df['area']
        score = max(0, 100 - efficiency.mean() * 5)  # Im mniej tym lepiej

        return round(min(100, score), 1)

    def predict_costs(self, apartment_id, months=6):
        """Przewiduje koszty."""
        rates = {'electricity': 0.8, 'water': 12.0, 'gas': 3.2, 'heating': 0.65}
        consumption_predictions = self.predict_utility_consumption(apartment_id, months=months)

        total_costs = []
        for i in range(months):
            total_cost = 0
            date = None

            for utility_type, predictions in consumption_predictions.items():
                if i < len(predictions):
                    cost = predictions[i]['consumption'] * rates.get(utility_type, 1.0)
                    total_cost += cost
                    if date is None:
                        date = predictions[i]['date']

            total_costs.append({
                'date': date,
                'total_cost': round(total_cost, 2)
            })

        return {'total': total_costs, 'detailed': consumption_predictions}

    def calculate_profit_predictions(self, months=6):
        """Oblicza prognozy zysków."""
        apartments = Apartment.objects.all()
        monthly_income = sum(apt.rent for apt in apartments)

        predictions = []
        for i in range(months):
            future_date = datetime.now().date() + timedelta(days=30 * (i + 1))
            income = monthly_income * np.random.uniform(0.95, 1.05)
            cost = income * 0.3 * np.random.uniform(0.9, 1.1)
            profit = income - cost

            predictions.append({
                'date': future_date,
                'income': round(income, 2),
                'cost': round(cost, 2),
                'profit': round(profit, 2)
            })

        return predictions

    def _fallback_prediction(self, apartment_id, utility_type, months):
        """Fallback gdy nie ma dość danych."""
        apartment = Apartment.objects.get(id=apartment_id)
        base_values = {
            'electricity': apartment.area * 1.5,
            'water': apartment.area * 0.1,
            'gas': apartment.area * 0.8,
            'heating': apartment.area * 2.0
        }

        predictions = []
        for i in range(months):
            future_date = datetime.now().date() + timedelta(days=30 * (i + 1))
            consumption = base_values.get(utility_type, 100) * np.random.uniform(0.9, 1.1)

            predictions.append({
                'date': future_date,
                'consumption': round(consumption, 2),
                'unit': self._get_unit(utility_type),
                'confidence': 0.4
            })

        return predictions

    def _get_unit(self, utility_type):
        """Zwraca jednostkę."""
        units = {'electricity': 'kWh', 'water': 'm³', 'gas': 'm³', 'heating': 'kWh'}
        return units.get(utility_type, 'jednostka')
