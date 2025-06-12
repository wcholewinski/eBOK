"""Stałe używane w aplikacji"""
# Stałe dla płatności
PENDING = 'pending'
PAID = 'paid'

PAYMENT_STATUS = [
    (PENDING, 'Oczekująca'),
    (PAID, 'Opłacona'),
]

PAYMENT_TYPES = [
    ('rent', 'Czynsz'),
    ('water', 'Woda'),
    ('gas', 'Gaz'),
    ('electricity', 'Prąd'),
    ('garbage', 'Śmieci'),
    ('heating', 'Ogrzewanie'),
    ('other', 'Inne'),
]

# Stałe dla zgłoszeń
NEW = 'new'
IN_PROGRESS = 'in_progress'
CLOSED = 'closed'

TICKET_STATUS = [
    (NEW, 'Nowe'),
    (IN_PROGRESS, 'W realizacji'),
    (CLOSED, 'Zamknięte'),
]

TICKET_PRIORITIES = [
    ('low', 'Niski'),
    ('medium', 'Średni'),
    ('high', 'Wysoki'),
]

# Stałe dla mediów
UTILITY_TYPES = [
    ('electricity', 'Prąd'),
    ('water', 'Woda'),
    ('gas', 'Gaz'),
    ('heating', 'Ogrzewanie'),
]

UTILITY_UNITS = [
    ('kWh', 'kWh'),
    ('m3', 'm³'),
    ('GJ', 'GJ'),
]


# Typy alertów budynkowych
ALERT_TYPES = (
    ('maintenance', 'Konserwacja'),
    ('safety', 'Bezpieczeństwo'),
    ('info', 'Informacja'),
)

# Poziomy ważności alertów
ALERT_SEVERITY = (
    ('low', 'Niski'),
    ('medium', 'Średni'),
    ('high', 'Wysoki'),
    ('critical', 'Krytyczny'),
)
