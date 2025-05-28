from django.contrib import admin
from .models import Apartment, Tenant, Payment, Ticket

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'area', 'rent', 'trash_fee', 'water_fee', 'gas_fee')
    list_filter = ('floor',)
    search_fields = ('number',)
    ordering = ('number',)

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('user', 'apartment', 'num_occupants')
    list_filter = ('apartment',)
    search_fields = ('user__username',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'date', 'amount', 'type', 'status')
    list_filter = ('status', 'type')
    date_hierarchy = 'date'
    search_fields = ('tenant__user__username',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'tenant__user__username')
    ordering = ('-created_at',)
