"""Stałe używane w aplikacji"""

# Statusy płatności
PAYMENT_STATUS = (
    ('pending', 'Oczekująca'),
    ('paid', 'Opłacona'),
    ('canceled', 'Anulowana'),
)

# Typy płatności
PAYMENT_TYPES = (
    ('rent', 'Czynsz'),
    ('trash', 'Śmieci'),
    ('water', 'Woda'),
    ('gas', 'Gaz'),
    ('electricity', 'Prąd'),
    ('other', 'Inne'),
)

# Statusy zgłoszeń
TICKET_STATUS = (
    ('new', 'Nowe'),
    ('in_progress', 'W realizacji'),
    ('waiting', 'Oczekujące'),
    ('closed', 'Zakończone'),
)

# Priorytety zgłoszeń
TICKET_PRIORITIES = (
    ('low', 'Niski'),
    ('medium', 'Średni'),
    ('high', 'Wysoki'),
    ('critical', 'Krytyczny'),
)

# Typy mediów
UTILITY_TYPES = (
    ('electricity', 'Prąd'),
    ('water', 'Woda'),
    ('gas', 'Gaz'),
    ('heating', 'Ogrzewanie'),
)

# Jednostki zużycia
UTILITY_UNITS = (
    ('kWh', 'kWh'),
    ('m3', 'm³'),
    ('GJ', 'GJ'),
)

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
