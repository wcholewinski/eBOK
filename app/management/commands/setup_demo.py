from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Apartment, Tenant, Payment, Ticket, UtilityConsumption
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Konfiguruje dane demonstracyjne dla eBOK'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Rozpoczęcie konfiguracji danych demonstracyjnych'))

        # Tworzenie administratora
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Utworzono administratora (login: admin, hasło: admin)'))

        # Tworzenie mieszkań
        if Apartment.objects.count() == 0:
            self.create_apartments()
            self.stdout.write(self.style.SUCCESS('Utworzono mieszkania'))

        # Tworzenie najemców
        if Tenant.objects.count() == 0 and Apartment.objects.exists():
            self.create_tenants()
            self.stdout.write(self.style.SUCCESS('Utworzono najemców'))

        # Tworzenie płatności
        if Payment.objects.count() == 0 and Tenant.objects.exists():
            self.create_payments()
            self.stdout.write(self.style.SUCCESS('Utworzono płatności'))

        # Tworzenie zgłoszeń
        if Ticket.objects.count() == 0 and Tenant.objects.exists():
            self.create_tickets()
            self.stdout.write(self.style.SUCCESS('Utworzono zgłoszenia'))

        # Tworzenie zużycia mediów
        if UtilityConsumption.objects.count() == 0 and Apartment.objects.exists():
            self.create_utility_consumption()
            self.stdout.write(self.style.SUCCESS('Utworzono dane zużycia mediów'))

        self.stdout.write(self.style.SUCCESS('\nKonfiguracja zakończona pomyślnie!'))
        self.stdout.write(self.style.SUCCESS('Administrator: login: admin, hasło: admin'))
        self.stdout.write(self.style.SUCCESS('Najemca: login: lokator1, hasło: lokator1'))
        self.stdout.write(self.style.SUCCESS('Serwer: http://127.0.0.1:8000/'))

    def create_apartments(self):
        """Tworzenie przykładowych mieszkań"""
        for i in range(1, 11):  # 10 mieszkań
            floor = (i - 1) // 3 + 1  # 3 mieszkania na piętro
            Apartment.objects.create(
                number=f'{floor}{i%3 + 1}',
                floor=floor,
                area=40.0 + random.randint(0, 60),
                rent=1200.00 + random.randint(0, 1000),
                trash_fee=50.00 + random.randint(0, 50),
                water_fee=30.00 + random.randint(0, 40),
                gas_fee=20.00 + random.randint(0, 30)
            )

    def create_tenants(self):
        """Tworzenie przykładowych najemców"""
        apartments = list(Apartment.objects.all())
        first_names = ['Jan', 'Anna', 'Piotr', 'Maria', 'Tomasz', 'Katarzyna', 'Michał', 'Ewa']
        last_names = ['Kowalski', 'Nowak', 'Wiśniewski', 'Dąbrowski', 'Lewandowski', 'Wójcik', 'Zieliński']

        # Tworzenie przykładowych użytkowników i najemców
        for i, apartment in enumerate(apartments[:5]):  # Przypisz najemców do 5 mieszkań
            username = f'lokator{i+1}'
            email = f'lokator{i+1}@example.com'
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            # Tworzenie użytkownika
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password=username,  # hasło takie samo jak login
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )

                # Tworzenie najemcy
                Tenant.objects.create(
                    user=user,
                    apartment=apartment,
                    phone_number=f'50{i}' + ''.join([str(random.randint(0, 9)) for _ in range(7)]),
                    num_occupants=random.randint(1, 4)
                )

    def create_payments(self):
        """Tworzenie przykładowych płatności"""
        tenants = Tenant.objects.all()
        payment_types = ['rent', 'garbage', 'water', 'gas']
        statuses = ['pending', 'paid']

        # Dla każdego najemcy
        for tenant in tenants:
            # Dodaj 6 ostatnich miesięcy płatności
            for i in range(6):
                payment_date = timezone.now() - timedelta(days=30*i)

                # Dodaj kilka różnych typów płatności
                for payment_type in payment_types:
                    # Określ kwotę na podstawie typu
                    if payment_type == 'rent':
                        amount = tenant.apartment.rent
                    elif payment_type == 'garbage':
                        amount = tenant.apartment.trash_fee
                    elif payment_type == 'water':
                        amount = tenant.apartment.water_fee
                    elif payment_type == 'gas':
                        amount = tenant.apartment.gas_fee

                    # Starsze płatności raczej opłacone
                    status = 'paid' if i > 1 or random.random() > 0.3 else 'pending'

                    Payment.objects.create(
                        tenant=tenant,
                        date=payment_date,
                        amount=amount,
                        type=payment_type,
                        status=status
                    )

    def create_tickets(self):
        """Tworzenie przykładowych zgłoszeń"""
        tenants = Tenant.objects.all()
        ticket_titles = [
            'Awaria ogrzewania', 'Problem z instalacją wodno-kanalizacyjną',
            'Uszkodzony kran w łazience', 'Hałas od sąsiadów',
            'Przeciekający sufit', 'Uszkodzona kuchenka', 
            'Problem z drzwiami wejściowymi', 'Usterka oświetlenia'
        ]
        ticket_descriptions = [
            'Proszę o szybką interwencję.',
            'Problem występuje od tygodnia.',
            'Bardzo proszę o naprawę w najbliższym możliwym terminie.',
            'Sytuacja jest uciążliwa i wymaga pilnej interwencji.'
        ]
        statuses = ['new', 'in_progress', 'closed']
        priorities = ['high', 'normal', 'low']

        # Dla każdego najemcy dodaj 1-3 zgłoszenia
        for tenant in tenants:
            for _ in range(random.randint(1, 3)):
                Ticket.objects.create(
                    tenant=tenant,
                    title=random.choice(ticket_titles),
                    description=random.choice(ticket_descriptions),
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60))
                )

    def create_utility_consumption(self):
        """Tworzenie danych zużycia mediów"""
        apartments = Apartment.objects.all()
        utility_types = ['electricity', 'water', 'gas', 'heating']

        # Dla każdego mieszkania
        for apartment in apartments:
            # Dodaj dane zużycia za ostatnie 12 miesięcy
            for i in range(12):
                month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
                next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
                month_end = next_month - timedelta(days=1)

                # Dla każdego typu mediów
                for utility_type in utility_types:
                    # Określ jednostkę i podstawowe zużycie
                    if utility_type == 'electricity':
                        unit = 'kWh'
                        base_consumption = 150.0 + random.uniform(-20, 20)
                        unit_cost = 0.65
                    elif utility_type == 'water':
                        unit = 'm³'
                        base_consumption = 3.0 + random.uniform(-0.5, 0.5)
                        unit_cost = 9.0
                    elif utility_type == 'gas':
                        unit = 'm³'
                        base_consumption = 10.0 + random.uniform(-2, 2)
                        unit_cost = 2.5
                    else:  # heating
                        unit = 'GJ'
                        base_consumption = 1.5 + random.uniform(-0.3, 0.3)
                        unit_cost = 65.0

                    # Sezonowość - więcej ogrzewania zimą, więcej wody latem
                    month_factor = 1.0
                    if utility_type == 'heating':
                        # Więcej ogrzewania w miesiącach zimowych (1, 2, 3, 10, 11, 12)
                        if month_start.month in [1, 2, 3, 10, 11, 12]:
                            month_factor = 2.0
                        elif month_start.month in [4, 5, 9]:
                            month_factor = 1.0
                        else:
                            month_factor = 0.3  # Minimalne latem
                    elif utility_type == 'water':
                        # Więcej wody w miesiącach letnich
                        if month_start.month in [6, 7, 8]:
                            month_factor = 1.3

                    # Obliczanie zużycia i kosztu
                    consumption = base_consumption * month_factor * (1 + random.uniform(-0.1, 0.1))
                    cost = consumption * unit_cost

                    # Tworzenie rekordu zużycia
                    UtilityConsumption.objects.create(
                        apartment=apartment,
                        period_start=month_start,
                        period_end=month_end,
                        utility_type=utility_type,
                        consumption=round(consumption, 2),
                        unit=unit,
                        cost=round(cost, 2)
                    )
