from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from app.constants import (
    PAYMENT_TYPES, PAYMENT_STATUS, PENDING,
    TICKET_STATUS, TICKET_PRIORITIES, NEW,
    UTILITY_TYPES, UTILITY_UNITS
)


class Apartment(models.Model):
    number = models.CharField(
        max_length=3,
        unique=True,
        verbose_name='Numer mieszkania',
        help_text='Podaj numer mieszkania'
    )
    floor = models.IntegerField(
        verbose_name='Piętro'
    )
    area = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Powierzchnia (m²)',
        help_text='Powierzchnia w metrach kwadratowych'
    )
    rent = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name='Czynsz (PLN)'
    )
    trash_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name='Opłata za śmieci (PLN)'
    )
    water_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Opłata za wodę (PLN)'
    )
    gas_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Opłata za gaz (PLN)'
    )

    class Meta:
        ordering = ['number']
        verbose_name = 'Mieszkanie'
        verbose_name_plural = 'Mieszkania'

    def __str__(self):
        return f'Mieszkanie {self.number}'

    def total_fees(self):
        """Oblicza sumę wszystkich opłat za mieszkanie"""
        return self.rent + self.trash_fee + self.water_fee + self.gas_fee


class Tenant(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tenant_profile',
        verbose_name='Konto użytkownika'
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='tenants',
        verbose_name='Mieszkanie'
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Numer telefonu'
    )
    num_occupants = models.PositiveIntegerField(
        default=1,
        verbose_name='Liczba osób'
    )

    class Meta:
        verbose_name = 'Najemca'
        verbose_name_plural = 'Najemcy'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'


class Payment(models.Model):
    PAYMENT_TYPES = PAYMENT_TYPES
    STATUS_CHOICES = PAYMENT_STATUS

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Najemca'
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name='Termin płatności'
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Kwota (PLN)'
    )
    type = models.CharField(
        max_length=15,
        choices=PAYMENT_TYPES,
        verbose_name='Rodzaj płatności'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name='Status'
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'Płatność'
        verbose_name_plural = 'Płatności'

    def __str__(self):
        return f'Płatność: {self.amount:.2f} zł - {self.tenant.user.username} (Mieszkanie {self.tenant.apartment.number})'


class Ticket(models.Model):
    STATUS_CHOICES = TICKET_STATUS
    PRIORITY_CHOICES = TICKET_PRIORITIES

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Najemca'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Tytuł'
    )
    description = models.TextField(
        verbose_name='Opis zgłoszenia'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=NEW,
        verbose_name='Status'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Priorytet'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data utworzenia'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Data aktualizacji'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Zgłoszenie'
        verbose_name_plural = 'Zgłoszenia'

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class UtilityConsumption(models.Model):
    UTILITY_TYPES = UTILITY_TYPES

    apartment = models.ForeignKey(
        Apartment, 
        on_delete=models.CASCADE,
        related_name='utility_consumption',
        verbose_name='Mieszkanie'
    )
    period_start = models.DateField(
        verbose_name='Początek okresu'
    )
    period_end = models.DateField(
        verbose_name='Koniec okresu'
    )
    utility_type = models.CharField(
        max_length=20, 
        choices=UTILITY_TYPES,
        verbose_name='Rodzaj medium'
    )
    consumption = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Zużycie'
    )
    unit = models.CharField(
        max_length=10,
        verbose_name='Jednostka',
        help_text='np. kWh, m³'
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Koszt',
        default=0.00
    )

    class Meta:
        verbose_name = 'Zużycie mediów'
        verbose_name_plural = 'Zużycie mediów'
        ordering = ['-period_start']
        unique_together = ['apartment', 'period_start', 'utility_type']

    def __str__(self):
        return f'{self.get_utility_type_display()} - {self.consumption} {self.unit} ({self.period_start.strftime("%Y-%m-%d")} do {self.period_end.strftime("%Y-%m-%d")})'    


class MaintenanceRequest(models.Model):
    NEW = 'new'
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (NEW, 'Nowe'),
        (SCHEDULED, 'Zaplanowane'),
        (IN_PROGRESS, 'W trakcie'),
        (COMPLETED, 'Zakończone'),
        (CANCELLED, 'Anulowane'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Niska'),
        (2, 'Średnia'),
        (3, 'Wysoka'),
        (4, 'Krytyczna'),
    ]

    apartment = models.ForeignKey(
        Apartment, 
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        verbose_name='Mieszkanie'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Tytuł'
    )
    description = models.TextField(
        verbose_name='Opis'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default=NEW,
        verbose_name='Status'
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        verbose_name='Priorytet'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data utworzenia'
    )
    scheduled_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Planowana data'
    )
    completed_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Data zakończenia'
    )
    estimated_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        verbose_name='Szacowany koszt'
    )

    class Meta:
        verbose_name = 'Zlecenie konserwacji'
        verbose_name_plural = 'Zlecenia konserwacji'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f'Zgłoszenie: {self.title}'


class BuildingAlert(models.Model):
    ALERT_TYPES = [
        ('maintenance', 'Konserwacja'),
        ('security', 'Bezpieczeństwo'),
        ('utility', 'Media'),
        ('payment', 'Płatności'),
        ('other', 'Inne'),
    ]

    SEVERITY_CHOICES = [
        ('info', 'Informacja'),
        ('warning', 'Ostrzeżenie'),
    ]

    apartment = models.ForeignKey(
        Apartment, 
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True,
        verbose_name='Mieszkanie'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Tytuł'
    )
    message = models.TextField(
        verbose_name='Treść'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        verbose_name='Typ alertu'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        verbose_name='Ważność'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Aktywny'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data utworzenia'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data wygaśnięcia'
    )

    class Meta:
        verbose_name = 'Alert budynku'
        verbose_name_plural = 'Alerty budynku'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_severity_display()})'



