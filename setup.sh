#!/bin/bash

echo "🏠 Konfiguracja projektu eBOK..."

# Sprawdź czy Python jest dostępny
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python nie jest zainstalowany!"
        exit 1
    else
        PY_CMD="python"
    fi
else
    PY_CMD="python3"
fi

# Utwórz wirtualne środowisko jeśli nie istnieje
if [ ! -d ".venv" ]; then
    echo "📦 Tworzenie wirtualnego środowiska..."
    $PY_CMD -m venv .venv
fi

# Aktywuj wirtualne środowisko
echo "🔧 Aktywacja wirtualnego środowiska..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    source .venv/Scripts/activate
fi

# Aktualizacja pip i setuptools
echo "📤 Aktualizacja pip i setuptools..."
pip install --upgrade pip setuptools wheel

# Instaluj zależności
echo "📥 Instalacja zależności..."
pip install -r requirements.txt

# Migracje bazy danych
echo "🗄️ Wykonywanie migracji..."
python manage.py makemigrations app
python manage.py migrate

# Utworzenie skryptu Python do generowania danych testowych
echo "📊 Generowanie skryptu do tworzenia danych testowych..."

cat > generate_test_data.py << 'EOF'
import os
import django
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eBOK.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption, MaintenanceRequest, BuildingAlert

# Czyszczenie danych (opcjonalne)
print("Czyszczenie istniejących danych...")
MaintenanceRequest.objects.all().delete()
BuildingAlert.objects.all().delete()
UtilityConsumption.objects.all().delete()
Ticket.objects.all().delete()
Payment.objects.all().delete()
Tenant.objects.all().delete()
Apartment.objects.all().delete()
User.objects.filter(is_superuser=False).delete()

# Tworzenie administratora
if not User.objects.filter(username="admin").exists():
    print("Tworzenie administratora...")
    admin = User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin",
        first_name="Administrator",
        last_name="Systemu"
    )

# Tworzenie 10 mieszkań
print("Tworzenie mieszkań...")
apartments = []
for i in range(1, 11):
    floor = (i - 1) // 2 + 1  # 2 mieszkania na piętro
    area = random.uniform(30, 120)  # Losowa powierzchnia między 30 a 120 m²
    rent = area * random.uniform(30, 50)  # Czynsz zależny od powierzchni

    apartment = Apartment.objects.create(
        number=f"{floor}0{i%2+1}",  # Np. 101, 102, 201, 202, ...
        floor=floor,
        area=round(area, 2),
        rent=round(rent, 2),
        trash_fee=round(random.uniform(40, 80), 2),
        water_fee=round(random.uniform(30, 60), 2),
        gas_fee=round(random.uniform(30, 70), 2)
    )
    apartments.append(apartment)
    print(f"  - Utworzono mieszkanie {apartment.number}")

# Tworzenie najemców
print("Tworzenie najemców...")
for i, apartment in enumerate(apartments, 1):
    username = f"lokator{i}"

    # Utworzenie użytkownika dla najemcy
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=username,  # Hasło takie samo jak nazwa użytkownika
        first_name=random.choice(["Jan", "Anna", "Marek", "Piotr", "Ewa", "Katarzyna", "Michał", "Tomasz", "Alicja", "Magdalena"]),
        last_name=random.choice(["Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak"])
    )

    # Utworzenie najemcy
    tenant = Tenant.objects.create(
        user=user,
        apartment=apartment,
        phone_number=f"+48 {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}",
        num_occupants=random.randint(1, 4)
    )
    print(f"  - Utworzono najemcę {user.first_name} {user.last_name} (login: {username})")

    # Generowanie historii płatności dla każdego najemcy (12 miesięcy wstecz)
    print(f"    Generowanie historii płatności dla {username}...")
    today = datetime.now().date()
    for j in range(12, 0, -1):  # 12 miesięcy wstecz
        payment_date = today - timedelta(days=30*j)

        # Czynsz
        Payment.objects.create(
            tenant=tenant,
            date=payment_date,
            amount=apartment.rent,
            type='rent',
            status=random.choices(['paid', 'pending'], weights=[0.9, 0.1])[0]
        )

        # Śmieci
        Payment.objects.create(
            tenant=tenant,
            date=payment_date,
            amount=apartment.trash_fee,
            type='garbage',
            status=random.choices(['paid', 'pending'], weights=[0.95, 0.05])[0]
        )

        # Woda
        Payment.objects.create(
            tenant=tenant,
            date=payment_date,
            amount=apartment.water_fee,
            type='water',
            status=random.choices(['paid', 'pending'], weights=[0.9, 0.1])[0]
        )

        # Gaz
        Payment.objects.create(
            tenant=tenant,
            date=payment_date,
            amount=apartment.gas_fee,
            type='gas',
            status=random.choices(['paid', 'pending'], weights=[0.9, 0.1])[0]
        )

    # Generowanie historii zużycia mediów (12 miesięcy wstecz)
    print(f"    Generowanie historii zużycia mediów dla mieszkania {apartment.number}...")
    for j in range(12, 0, -1):
        period_start = today.replace(day=1) - timedelta(days=30*j)
        period_end = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        # Elektryczność
        baseline_electricity = random.uniform(100, 200)
        seasonal_factor = 1.0 + 0.2 * np.sin(np.pi * j / 6)  # Sinusoidalna zmiana sezonowa
        random_factor = random.uniform(0.9, 1.1)  # Losowe wahania ±10%

        UtilityConsumption.objects.create(
            apartment=apartment,
            period_start=period_start,
            period_end=period_end,
            utility_type='electricity',
            consumption=round(baseline_electricity * seasonal_factor * random_factor, 2),
            unit='kWh',
            cost=round(baseline_electricity * seasonal_factor * random_factor * 0.8, 2)  # koszt = zużycie * stawka
        )

        # Woda
        baseline_water = random.uniform(3, 10) * tenant.num_occupants
        UtilityConsumption.objects.create(
            apartment=apartment,
            period_start=period_start,
            period_end=period_end,
            utility_type='water',
            consumption=round(baseline_water * random.uniform(0.9, 1.1), 2),
            unit='m³',
            cost=round(baseline_water * random.uniform(0.9, 1.1) * 12, 2)  # koszt = zużycie * stawka
        )

        # Gaz
        baseline_gas = random.uniform(10, 30)
        winter_factor = 1.0 + 1.5 * max(0, np.cos(np.pi * j / 6))  # Więcej zimą, mniej latem
        UtilityConsumption.objects.create(
            apartment=apartment,
            period_start=period_start,
            period_end=period_end,
            utility_type='gas',
            consumption=round(baseline_gas * winter_factor * random.uniform(0.9, 1.1), 2),
            unit='m³',
            cost=round(baseline_gas * winter_factor * random.uniform(0.9, 1.1) * 3.2, 2)  # koszt = zużycie * stawka
        )

        # Ogrzewanie (tylko w sezonie grzewczym: październik-kwiecień)
        month = period_start.month
        if month >= 10 or month <= 4:  # Sezon grzewczy
            heating_factor = 1.0 + 0.5 * (4 - abs(month - 1 if month >= 10 else month - 3)) / 4
            baseline_heating = random.uniform(50, 150) * (apartment.area / 50)
            UtilityConsumption.objects.create(
                apartment=apartment,
                period_start=period_start,
                period_end=period_end,
                utility_type='heating',
                consumption=round(baseline_heating * heating_factor * random.uniform(0.9, 1.1), 2),
                unit='kWh',
                cost=round(baseline_heating * heating_factor * random.uniform(0.9, 1.1) * 0.65, 2)  # koszt = zużycie * stawka
            )

    # Generowanie zgłoszeń
    if random.random() < 0.7:  # 70% najemców ma jakieś zgłoszenia
        num_tickets = random.randint(1, 3)
        for _ in range(num_tickets):
            days_ago = random.randint(0, 180)  # Zgłoszenie z ostatnich 6 miesięcy
            ticket_date = today - timedelta(days=days_ago)

            ticket_titles = [
                "Awaria ogrzewania", "Cieknący kran", "Problem z prądem", 
                "Uszkodzona klamka", "Głośni sąsiedzi", "Zepsuta lodówka", 
                "Problem z internetem", "Pleśń w łazience", "Awaria pieca"
            ]

            status_options = ['new', 'in_progress', 'closed']
            status_weights = [0.2, 0.3, 0.5]  # Większość zgłoszeń jest już zamknięta
            if days_ago < 7:  # Świeże zgłoszenia częściej są nowe
                status_weights = [0.6, 0.3, 0.1]

            Ticket.objects.create(
                tenant=tenant,
                title=random.choice(ticket_titles),
                description=f"Zgłoszenie problemu w mieszkaniu {apartment.number}. Proszę o szybką interwencję.",
                status=random.choices(status_options, weights=status_weights)[0],
                priority=random.choice(['low', 'medium', 'high']),
                created_at=ticket_date
            )

# Tworzenie alertów budynku
print("Tworzenie alertów budynku...")
alert_titles = [
    "Planowane prace konserwacyjne", 
    "Przerwa w dostawie wody", 
    "Przegląd instalacji gazowej", 
    "Zmiana harmonogramu wywozu śmieci", 
    "Zebranie wspólnoty mieszkańców"
]

alert_messages = [
    "W dniu 15.07.2025 planowane są prace konserwacyjne instalacji elektrycznej. Możliwe przerwy w dostawie prądu w godzinach 10:00-14:00.",
    "Informujemy, że w dniu 20.07.2025 w godzinach 8:00-16:00 nastąpi przerwa w dostawie wody z powodu prac modernizacyjnych.",
    "W dniach 1-5.08.2025 odbędzie się obowiązkowy przegląd instalacji gazowej. Prosimy o udostępnienie mieszkań w wyznaczonych terminach.",
    "Od sierpnia zmienia się harmonogram wywozu odpadów. Śmieci zmieszane będą odbierane w poniedziałki i czwartki, a segregowane w środy.",
    "Zapraszamy na zebranie wspólnoty mieszkańców w dniu 25.07.2025 o godz. 18:00 w świetlicy budynku. Tematem będzie plan remontów na 2026 rok."
]

for i in range(5):
    # Używamy timezone.now() zamiast zwykłego datetime aby uniknąć ostrzeżeń o naiwnych datach
    future_date = timezone.now() + timedelta(days=random.randint(10, 60))
    BuildingAlert.objects.create(
        title=alert_titles[i],
        message=alert_messages[i],
        alert_type=random.choice(['maintenance', 'security', 'utility', 'payment', 'other']),
        severity=random.choice(['info', 'warning']),
        is_active=True,
        created_at=timezone.now() - timedelta(days=random.randint(0, 5)),
        expires_at=future_date
    )

# Tworzenie zleceń konserwacji
print("Tworzenie zleceń konserwacji...")
maintenance_titles = [
    "Naprawa windy", "Konserwacja pompy ciepła", "Czyszczenie rynien", 
    "Malowanie klatki schodowej", "Przegląd instalacji ppoż.", 
    "Naprawa domofonu", "Konserwacja kotłowni", "Naprawa dachu"
]

for i in range(8):
    days_ago = random.randint(0, 90)  # Zlecenie z ostatnich 3 miesięcy
    created_date = today - timedelta(days=days_ago)

    status_options = ['new', 'scheduled', 'in_progress', 'completed', 'cancelled']
    status_weights = [0.1, 0.2, 0.3, 0.35, 0.05]  # Różne prawdopodobieństwa statusów
    if days_ago < 7:  # Świeże zlecenia
        status_weights = [0.5, 0.3, 0.2, 0, 0]
    elif days_ago > 30:  # Starsze zlecenia
        status_weights = [0, 0.1, 0.2, 0.65, 0.05]

    status = random.choices(status_options, weights=status_weights)[0]

    # Daty dla różnych statusów
    scheduled_date = created_date + timedelta(days=random.randint(3, 14)) if status != 'new' else None
    completed_date = scheduled_date + timedelta(days=random.randint(1, 5)) if status == 'completed' else None

    apartment = random.choice(apartments) if random.random() < 0.5 else None  # 50% zleceń przypisanych do konkretnego mieszkania

    MaintenanceRequest.objects.create(
        apartment=apartment,
        title=maintenance_titles[i],
        description=f"Zlecenie konserwacji: {maintenance_titles[i]}",
        status=status,
        priority=random.randint(1, 4),
        created_at=created_date,
        scheduled_date=scheduled_date,
        completed_date=completed_date,
        estimated_cost=round(random.uniform(100, 5000), 2) if random.random() < 0.8 else None
    )

print("\nDane testowe zostały pomyślnie wygenerowane!")
print("Utworzono:")
print(f" - {Apartment.objects.count()} mieszkań")
print(f" - {Tenant.objects.count()} najemców")
print(f" - {Payment.objects.count()} płatności")
print(f" - {UtilityConsumption.objects.count()} wpisów zużycia mediów")
print(f" - {Ticket.objects.count()} zgłoszeń")
print(f" - {MaintenanceRequest.objects.count()} zleceń konserwacji")
print(f" - {BuildingAlert.objects.count()} alertów budynku")

print("\nDane do logowania:")
print("Administrator: login 'admin', hasło 'admin'")
for i, tenant in enumerate(Tenant.objects.all(), 1):
    print(f"Najemca {i}: login '{tenant.user.username}', hasło '{tenant.user.username}'")
EOF

# Uruchomienie skryptu generowania danych
echo "🧪 Generowanie danych testowych..."
python generate_test_data.py

echo "✅ Setup zakończony pomyślnie!"
echo "🚀 Uruchom serwer: python manage.py runserver"
