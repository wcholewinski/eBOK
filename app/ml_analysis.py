
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import numpy as np

from app.models import UtilityConsumption, SensorReading, Apartment


class PredictiveAnalysis:
    
    def predict_utility_consumption(self, apartment_id, utility_type, months_ahead=3):
        """Przewiduje zużycie mediów na podstawie danych historycznych"""
        
        # Pobierz dane historyczne
        consumption_data = UtilityConsumption.objects.filter(
            apartment_id=apartment_id,
            utility_type=utility_type
        ).order_by('month')
        
        if consumption_data.count() < 6:
            return None  # Za mało danych
            
        # Przygotuj dane do ML
        df = pd.DataFrame(list(consumption_data.values()))
        
        # Feature engineering
        df['month_num'] = pd.to_datetime(df['month']).dt.month
        df['year'] = pd.to_datetime(df['month']).dt.year
        
        # Model regresji
        X = df[['month_num', 'year']].values
        y = df['consumption'].values
        
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)
        
        # Przewidywania
        predictions = []
        current_date = datetime.now()
        
        for i in range(1, months_ahead + 1):
            future_date = current_date + timedelta(days=30*i)
            prediction = model.predict([[future_date.month, future_date.year]])[0]
            predictions.append({
                'month': future_date.strftime('%Y-%m'),
                'predicted_consumption': round(prediction, 2)
            })
            
        return predictions
    
    def detect_anomalies(self, apartment_id):
        """Wykrywa anomalie w zużyciu mediów"""
        
        readings = SensorReading.objects.filter(
            sensor__apartment_id=apartment_id
        ).order_by('-timestamp')[:100]
        
        if not readings:
            return []
            
        df = pd.DataFrame(list(readings.values()))
        
        # Wykrywanie anomalii metodą IQR
        Q1 = df['value'].quantile(0.25)
        Q3 = df['value'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        anomalies = df[(df['value'] < lower_bound) | (df['value'] > upper_bound)]
        
        return anomalies.to_dict('records')
    
    def building_efficiency_score(self):
        """Oblicza wskaźnik efektywności budynku"""
        
        apartments = Apartment.objects.all()
        total_score = 0
        
        for apt in apartments:
            # Średnie zużycie na m²
            avg_consumption = UtilityConsumption.objects.filter(
                apartment=apt
            ).aggregate(avg=models.Avg('consumption'))['avg'] or 0
            
            consumption_per_sqm = avg_consumption / apt.area if apt.area > 0 else 0
            
            # Prosta punktacja (im niższe zużycie, tym lepiej)
            score = max(0, 100 - consumption_per_sqm * 10)
            total_score += score
            
        return total_score / apartments.count() if apartments.count() > 0 else 0