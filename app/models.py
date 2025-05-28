from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
        return f"Mieszkanie {self.number} (piętro {self.floor})"

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
    num_occupants = models.PositiveIntegerField(
        default=1,
        verbose_name='Liczba osób'
    )

    class Meta:
        verbose_name = 'Najemca'
        verbose_name_plural = 'Najemcy'

    def __str__(self):
        return f"{self.user.username} – mieszkanie {self.apartment.number}"

class Payment(models.Model):
    RENT = 'rent'
    GARBAGE = 'garbage'
    WATER = 'water'
    GAS = 'gas'
    PAYMENT_TYPES = [
        (RENT,    'Czynsz'),
        (GARBAGE, 'Śmieci'),
        (WATER,   'Woda'),
        (GAS,     'Gaz'),
    ]

    PENDING = 'pending'
    PAID = 'paid'
    STATUS_CHOICES = [
        (PENDING, 'Oczekujące'),
        (PAID,    'Opłacone'),
    ]

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
        max_length=10,
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
        return f"{self.get_type_display()} – {self.amount} zł ({self.get_status_display()})"

class Ticket(models.Model):
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    CLOSED = 'closed'
    STATUS_CHOICES = [
        (NEW,        'Nowe'),
        (IN_PROGRESS,'W trakcie'),
        (CLOSED,     'Zamknięte'),
    ]

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
        return f"[{self.get_status_display()}] {self.title}"
