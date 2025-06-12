# eBOK — Elektroniczne Biuro Obsługi Klienta

## Opis projektu
Aplikacja webowa stworzona w Django, służąca do zarządzania budynkiem wielorodzinnym z integracją danych eksploatacyjnych i analizą predykcyjną.

Zapewnia dwa panele dostępu:
- **Panel administratora** (właściciel budynku) — do zarządzania mieszkaniami, mieszkańcami i analizami predykcyjnymi.
- **Panel lokatora** — pozwala lokatorowi na podgląd danych dotyczących jego mieszkania, zużycia mediów i opłat.

## Funkcjonalności

### Podstawowe
- Zarządzanie mieszkaniami i lokatorami
- System opłat i płatności
- Zgłoszenia serwisowe i awarie

### Zaawansowane
- Analiza predykcyjna zużycia mediów
- Predykcja kosztów utrzymania mieszkań

## Wymagania

- Python 3.11 lub nowszy
- Django 4.2.7
- Inne zależności wymienione w pliku `requirements.txt`

## Instrukcje instalacji

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/twoje-konto/ebok.git
cd ebok
```

### 2. Konfiguracja środowiska

#### Dla systemów Linux/macOS:

```bash
# Nadaj uprawnienia wykonywania dla skryptu
chmod +x setup.sh

# Uruchom skrypt konfiguracyjny
./setup.sh
```

#### Dla systemów Windows:

```bash
# Utwórz wirtualne środowisko
python -m venv .venv

# Aktywuj wirtualne środowisko
.venv1\Scripts\activate

# Zainstaluj zależności
pip install -r requirements.txt

# Wykonaj migracje
python manage.py makemigrations app
python manage.py migrate



### 3. Uruchomienie serwera

```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000/

## Dane logowania

- **Administrator**: login: `admin`, hasło: `admin`
- **Najemcy**: loginy `lokator1` do `lokator10`, hasła takie same jak loginy







