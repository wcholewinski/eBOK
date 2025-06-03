from django.urls import path
from . import views

app_name = 'admin'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('apartments/add/', views.add_apartment, name='add_apartment'),
    path('tenants/add/', views.add_tenant, name='add_tenant'),
    path('payments/', views.admin_payments, name='payments'),
    path('payments/add/', views.payment_form, name='add_payment'),
    path('payments/<int:pk>/edit/', views.payment_form, name='edit_payment'),
    path('tickets/', views.admin_tickets, name='tickets'),
    path('tickets/<int:pk>/edit/', views.ticket_edit, name='edit_ticket'),
]