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
admin.site.register(Apartment, ApartmentAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(UtilityConsumption)
admin.site.register(BuildingAlert)
