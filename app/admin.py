from django.contrib import admin
from .models import (Apartment, Tenant, Payment, Ticket, 
                     UtilityConsumption, BuildingAlert)

# Prostsze klasy admin bez zbędnej konfiguracji
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'area', 'rent')
    search_fields = ('number',)

class TenantAdmin(admin.ModelAdmin):
    list_display = ('user', 'apartment', 'phone_number')
    search_fields = ('user__username', 'phone_number')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'date', 'amount', 'status')
    list_filter = ('status',)

class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'status', 'created_at')
    list_filter = ('status',)
    ordering = ('-created_at',)

# Rejestracja modeli
admin.site.register(Apartment, ApartmentAdmin)  # Upewnij się, że ten model jest prawidłowo zarejestrowany
admin.site.register(Tenant, TenantAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(UtilityConsumption)
admin.site.register(BuildingAlert)

# Sprawdź, czy modele są prawidłowo zarejestrowane
print(f"Zarejestrowane modele w admin: {', '.join([m.__name__ for m in admin.site._registry.keys() if hasattr(m, '__name__')])}") # Diagnostyka
