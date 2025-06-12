import csv
import io
import datetime
import pandas as pd
from django.http import HttpResponse
from django.db.models import Q
from app.models import Apartment, UtilityConsumption, Payment, Tenant


class CSVExporter:
    """Klasa odpowiedzialna za eksport danych do CSV"""

    @staticmethod
    def get_utility_consumption_data(apartment_id=None, utility_type=None, start_date=None, end_date=None, locale='pl'):
        """Pobiera dane zużycia mediów i zwraca nagłówki oraz ramkę danych pandas"""
        # Filtrowanie danych
        queryset = UtilityConsumption.objects.all().order_by('period_start')

        if apartment_id:
            queryset = queryset.filter(apartment_id=apartment_id)

        if utility_type:
            queryset = queryset.filter(utility_type=utility_type)

        if start_date:
            queryset = queryset.filter(period_start__gte=start_date)

        if end_date:
            queryset = queryset.filter(period_end__lte=end_date)

        # Pobieranie danych
        data = queryset.values(
            'apartment__number', 'utility_type', 'period_start', 'period_end',
            'consumption', 'unit', 'cost'
        )

        # Konwersja na DataFrame
        df = pd.DataFrame(list(data))

        if df.empty:
            return [], df

        # Lokalizacja nagłówków
        headers_map = {
            'pl': {
                'apartment__number': 'Numer mieszkania',
                'utility_type': 'Rodzaj medium',
                'period_start': 'Data początkowa',
                'period_end': 'Data końcowa',
                'consumption': 'Zużycie',
                'unit': 'Jednostka',
                'cost': 'Koszt (PLN)'
            },
            'en': {
                'apartment__number': 'Apartment Number',
                'utility_type': 'Utility Type',
                'period_start': 'Start Date',
                'period_end': 'End Date',
                'consumption': 'Consumption',
                'unit': 'Unit',
                'cost': 'Cost (PLN)'
            }
        }

        # Mapowanie nazw typów mediów
        utility_type_map = {
            'pl': {
                'electricity': 'Prąd',
                'water': 'Woda',
                'gas': 'Gaz',
                'heating': 'Ogrzewanie'
            },
            'en': {
                'electricity': 'Electricity',
                'water': 'Water',
                'gas': 'Gas',
                'heating': 'Heating'
            }
        }

        # Zastosowanie mapowania typów mediów
        if 'utility_type' in df.columns:
            df['utility_type'] = df['utility_type'].map(lambda x: utility_type_map.get(locale, {}).get(x, x))

        # Zmiana nazw kolumn
        df = df.rename(columns=headers_map.get(locale, headers_map['pl']))

        # Lista nagłówków w kolejności
        headers = list(headers_map.get(locale, headers_map['pl']).values())

        return headers, df

    @staticmethod
    def get_payment_data(start_date=None, end_date=None, tenant_id=None, status=None, locale='pl'):
        """Pobiera dane płatności i zwraca nagłówki oraz ramkę danych pandas"""
        # Filtrowanie danych
        queryset = Payment.objects.all().order_by('date')

        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        if status:
            queryset = queryset.filter(status=status)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Pobieranie danych
        data = queryset.values(
            'tenant__user__username', 'tenant__apartment__number', 'date',
            'amount', 'type', 'status'
        )

        # Konwersja na DataFrame
        df = pd.DataFrame(list(data))

        if df.empty:
            return [], df

        # Lokalizacja nagłówków
        headers_map = {
            'pl': {
                'tenant__user__username': 'Użytkownik',
                'tenant__apartment__number': 'Numer mieszkania',
                'date': 'Data płatności',
                'amount': 'Kwota (PLN)',
                'type': 'Rodzaj płatności',
                'status': 'Status'
            },
            'en': {
                'tenant__user__username': 'User',
                'tenant__apartment__number': 'Apartment Number',
                'date': 'Payment Date',
                'amount': 'Amount (PLN)',
                'type': 'Payment Type',
                'status': 'Status'
            }
        }

        # Mapowanie typów płatności
        payment_type_map = {
            'pl': {
                'rent': 'Czynsz',
                'water': 'Woda',
                'gas': 'Gaz',
                'electricity': 'Prąd',
                'garbage': 'Śmieci',
                'heating': 'Ogrzewanie',
                'other': 'Inne'
            },
            'en': {
                'rent': 'Rent',
                'water': 'Water',
                'gas': 'Gas',
                'electricity': 'Electricity',
                'garbage': 'Garbage',
                'heating': 'Heating',
                'other': 'Other'
            }
        }

        # Mapowanie statusów płatności
        payment_status_map = {
            'pl': {
                'pending': 'Oczekująca',
                'paid': 'Opłacona'
            },
            'en': {
                'pending': 'Pending',
                'paid': 'Paid'
            }
        }

        # Zastosowanie mapowań
        if 'type' in df.columns:
            df['type'] = df['type'].map(lambda x: payment_type_map.get(locale, {}).get(x, x))
        if 'status' in df.columns:
            df['status'] = df['status'].map(lambda x: payment_status_map.get(locale, {}).get(x, x))

        # Zmiana nazw kolumn
        df = df.rename(columns=headers_map.get(locale, headers_map['pl']))

        # Lista nagłówków w kolejności
        headers = list(headers_map.get(locale, headers_map['pl']).values())

        return headers, df

    @staticmethod
    def get_predictive_data(predictions, prediction_type, locale='pl'):
        """Formatuje dane predykcyjne do eksportu"""
        df = pd.DataFrame(predictions)

        # Mapowanie typów predykcji do nagłówków
        headers_map = {
            'consumption': {
                'pl': {
                    'date': 'Data',
                    'value': 'Prognozowane zużycie',
                    'unit': 'Jednostka'
                },
                'en': {
                    'date': 'Date',
                    'value': 'Predicted Consumption',
                    'unit': 'Unit'
                }
            },
            'cost': {
                'pl': {
                    'date': 'Data',
                    'value': 'Prognozowany koszt (PLN)'
                },
                'en': {
                    'date': 'Date',
                    'value': 'Predicted Cost (PLN)'
                }
            },
            'income': {
                'pl': {
                    'date': 'Data',
                    'value': 'Prognozowany przychód (PLN)'
                },
                'en': {
                    'date': 'Date',
                    'value': 'Predicted Income (PLN)'
                }
            },
            'profit': {
                'pl': {
                    'date': 'Data',
                    'income': 'Przychód (PLN)',
                    'costs': 'Koszty (PLN)',
                    'profit': 'Zysk (PLN)'
                },
                'en': {
                    'date': 'Date',
                    'income': 'Income (PLN)',
                    'costs': 'Costs (PLN)',
                    'profit': 'Profit (PLN)'
                }
            }
        }

        # Wybór odpowiedniego mapowania
        type_headers = headers_map.get(prediction_type, {})
        current_headers = type_headers.get(locale, type_headers.get('pl', {}))

        # Zmiana nazw kolumn
        if current_headers:
            df = df.rename(columns=current_headers)

        # Lista nagłówków w kolejności
        headers = list(current_headers.values()) if current_headers else list(df.columns)

        return headers, df

    @staticmethod
    def export_to_response(df, filename):
        """Eksportuje ramkę danych do odpowiedzi HTTP z plikiem CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Eksport do CSV
        df.to_csv(path_or_buf=response, index=False, encoding='utf-8-sig')

        return response
