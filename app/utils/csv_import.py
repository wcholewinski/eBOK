import csv
import codecs
import io
import chardet
from datetime import datetime
from django.db import transaction
from app.models import Apartment, UtilityConsumption, Payment, Tenant

class CSVImporter:
    """Klasa odpowiedzialna za import danych z plików CSV"""

    def __init__(self, file_obj, model_type):
        self.file_obj = file_obj
        self.model_type = model_type
        self.encoding = self._detect_encoding()
        self.delimiter = None
        self.headers = []
        self.preview_data = []
        self.errors = []
        self.imported_count = 0
        self.updated_count = 0
        self.skipped_count = 0

    def _detect_encoding(self):
        raw_data = self.file_obj.read()
        result = chardet.detect(raw_data)
        self.file_obj.seek(0)  # Reset pozycji pliku
        return result['encoding']

    def _detect_delimiter(self, sample_line):
        if ';' in sample_line:
            return ';'
        elif ',' in sample_line:
            return ','
        elif '\t' in sample_line:
            return '\t'
        return ','

    def validate_headers(self, required_fields):
        missing_fields = [field for field in required_fields if field not in self.headers]
        if missing_fields:
            self.errors.append(f"Brakujące pola w pliku CSV: {', '.join(missing_fields)}")
            return False
        return True

    def load_preview(self, max_rows=5):
        try:
            # Otwieranie pliku z wykrytym kodowaniem
            decoded_file = codecs.iterdecode(self.file_obj, self.encoding)
            sample_line = next(decoded_file)
            self.file_obj.seek(0)  # Reset pozycji pliku

            # Wykrywanie separatora
            self.delimiter = self._detect_delimiter(sample_line)

            # Wczytywanie danych do podglądu
            decoded_file = codecs.iterdecode(self.file_obj, self.encoding)
            reader = csv.reader(decoded_file, delimiter=self.delimiter)

            # Pobranie nagłówków
            self.headers = next(reader)

            # Wczytanie wierszy do podglądu
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                self.preview_data.append(row)

            self.file_obj.seek(0)  # Reset pozycji pliku ponownie
            return True

        except Exception as e:
            self.errors.append(f"Błąd wczytywania podglądu: {str(e)}")
            return False

    def import_data(self, mapping=None, date_format='%Y-%m-%d'):
        """Importuje dane z pliku CSV do bazy danych"""
        try:
            # Wczytanie pliku CSV bezpośrednio bez używania pandas
            self.file_obj.seek(0)  # Reset pozycji pliku
            content = self.file_obj.read().decode(self.encoding)
            csv_reader = csv.DictReader(io.StringIO(content), delimiter=self.delimiter)

            # Zastosowanie mapowania kolumn, jeśli podano
            if mapping:
                # Przygotowanie listy wierszy z mapowaniem nazw kolumn
                rows = []
                for row in csv_reader:
                    mapped_row = {}
                    for key, value in row.items():
                        mapped_key = mapping.get(key, key)
                        mapped_row[mapped_key] = value
                    rows.append(mapped_row)
            else:
                # Bez mapowania używamy oryginalnych wierszy
                rows = list(csv_reader)

            # Wywołanie odpowiedniej metody importu w zależności od typu modelu
            with transaction.atomic():
                if self.model_type == 'apartment':
                    self._import_apartments_csv(rows)
                elif self.model_type == 'utility_consumption':
                    self._import_utility_consumption_csv(rows, date_format)
                elif self.model_type == 'payment':
                    self._import_payments_csv(rows, date_format)
                else:
                    self.errors.append(f"Nieznany typ modelu: {self.model_type}")
                    return False

            return True

        except Exception as e:
            self.errors.append(f"Błąd importu danych: {str(e)}")
            return False

    def _import_apartments_csv(self, rows):
        """Import danych mieszkań z pliku CSV"""
        required_columns = ['number', 'floor', 'area']

        # Sprawdzanie wymaganych kolumn w pierwszym wierszu
        if rows and all(col in rows[0] for col in required_columns):
            pass  # Wszystkie wymagane kolumny istnieją
        else:
            missing = [col for col in required_columns if col not in (rows[0] if rows else {})]
            self.errors.append(f"Brak wymaganych kolumn: {', '.join(missing)}")
            return

        # Import danych
        for index, row in enumerate(rows):
            try:
                # Konwersja typów danych
                apartment_data = {
                    'floor': int(row['floor']),
                    'area': float(row['area']),
                    'rent': float(row.get('rent', 0)),
                    'trash_fee': float(row.get('trash_fee', 0)),
                    'water_fee': float(row.get('water_fee', 0)),
                    'gas_fee': float(row.get('gas_fee', 0))
                }

                # Aktualizacja lub utworzenie nowego rekordu
                obj, created = Apartment.objects.update_or_create(
                    number=str(row['number']),
                    defaults=apartment_data
                )

                if created:
                    self.imported_count += 1
                else:
                    self.updated_count += 1

            except Exception as e:
                self.errors.append(f"Błąd w wierszu {index+2}: {str(e)}")
                self.skipped_count += 1

    def _import_utility_consumption_csv(self, rows, date_format):
        """Import danych zużycia mediów z pliku CSV"""
        required_columns = ['apartment_number', 'utility_type', 'period_start', 'period_end', 'consumption', 'unit', 'cost']

        # Sprawdzanie wymaganych kolumn w pierwszym wierszu
        if rows and all(col in rows[0] for col in required_columns):
            pass  # Wszystkie wymagane kolumny istnieją
        else:
            missing = [col for col in required_columns if col not in (rows[0] if rows else {})]
            self.errors.append(f"Brak wymaganych kolumn: {', '.join(missing)}")
            return

        # Sprawdzenie typów mediów
        valid_utility_types = [u[0] for u in UtilityConsumption.UTILITY_TYPES]

        # Import danych
        for index, row in enumerate(rows):
            try:
                # Sprawdzenie czy mieszkanie istnieje
                try:
                    apartment = Apartment.objects.get(number=str(row['apartment_number']))
                except Apartment.DoesNotExist:
                    self.errors.append(f"Mieszkanie {row['apartment_number']} nie istnieje (wiersz {index+2})")
                    self.skipped_count += 1
                    continue

                # Sprawdzenie typu mediów
                if row['utility_type'] not in valid_utility_types:
                    self.errors.append(f"Nieprawidłowy typ mediów: {row['utility_type']} (wiersz {index+2})")
                    self.skipped_count += 1
                    continue

                # Konwersja dat
                try:
                    period_start = datetime.strptime(str(row['period_start']), date_format).date()
                    period_end = datetime.strptime(str(row['period_end']), date_format).date()
                except ValueError:
                    self.errors.append(f"Nieprawidłowy format daty w wierszu {index+2}")
                    self.skipped_count += 1
                    continue

                # Konwersja typów danych
                consumption_data = {
                    'period_end': period_end,
                    'consumption': float(row['consumption']),
                    'unit': str(row['unit']),
                    'cost': float(row['cost'])
                }

                # Aktualizacja lub utworzenie nowego rekordu
                obj, created = UtilityConsumption.objects.update_or_create(
                    apartment=apartment,
                    period_start=period_start,
                    utility_type=row['utility_type'],
                    defaults=consumption_data
                )

                if created:
                    self.imported_count += 1
                else:
                    self.updated_count += 1

            except Exception as e:
                self.errors.append(f"Błąd w wierszu {index+2}: {str(e)}")
                self.skipped_count += 1

    def _import_payments_csv(self, rows, date_format):
        """Import danych płatności z pliku CSV"""
        required_columns = ['tenant_id', 'date', 'amount', 'type', 'status']

        # Sprawdzanie wymaganych kolumn w pierwszym wierszu
        if rows and all(col in rows[0] for col in required_columns):
            pass  # Wszystkie wymagane kolumny istnieją
        else:
            missing = [col for col in required_columns if col not in (rows[0] if rows else {})]
            self.errors.append(f"Brak wymaganych kolumn: {', '.join(missing)}")
            return

        # Import danych
        for index, row in enumerate(rows):
            try:
                # Sprawdzenie czy najemca istnieje
                try:
                    tenant = Tenant.objects.get(id=int(row['tenant_id']))
                except Tenant.DoesNotExist:
                    self.errors.append(f"Najemca o ID {row['tenant_id']} nie istnieje (wiersz {index+2})")
                    self.skipped_count += 1
                    continue

                # Konwersja daty
                try:
                    payment_date = datetime.strptime(str(row['date']), date_format).date()
                except ValueError:
                    self.errors.append(f"Nieprawidłowy format daty w wierszu {index+2}")
                    self.skipped_count += 1
                    continue

                # Konwersja typów danych
                payment_data = {
                    'tenant': tenant,
                    'date': payment_date,
                    'amount': float(row['amount']),
                    'type': str(row['type']),
                    'status': str(row['status']),
                    'description': str(row.get('description', ''))
                }

                # Tworzenie nowego rekordu płatności
                # Używamy create zamiast update_or_create, bo płatności raczej nie aktualizujemy
                Payment.objects.create(**payment_data)
                self.imported_count += 1

            except Exception as e:
                self.errors.append(f"Błąd w wierszu {index+2}: {str(e)}")
                self.skipped_count += 1

    def get_summary(self):
        """Zwraca podsumowanie importu"""
        return {
            'imported': self.imported_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count,
            'errors': self.errors
        }
