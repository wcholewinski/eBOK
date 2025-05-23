from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Apartment(models.Model):
    number = models.CharField(max_length=3)
    floor = models.IntegerField()
    area = models.DecimalField(max_digits=3, decimal_places=2)
    rent = models.DecimalField(max_digits=4, decimal_places=2)
    trash_fee = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    water_fee = models.DecimalField(max_digits=3, decimal_places=2)
    gas_fee = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return f"Mieszkanie nr {self.number} (piętro {self.floor})"


class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    num_occupants = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} ({self.apartment})"

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('rent',    'Czynsz'),
        ('garbage', 'Śmieci'),
        ('water',   'Woda'),
        ('gas',     'Gaz'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Oczekujące'),
        ('paid',    'Opłacone'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField(default=timezone.now, help_text="Termin płatności")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    type = models.CharField(max_length=10, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} zł – {self.get_status_display()}"


class Ticket(models.Model):
    STATUS = [
        ('new',        'Nowe'),
        ('in_progress','W trakcie'),
        ('closed',     'Zamknięte'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"