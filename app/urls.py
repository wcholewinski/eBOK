from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/add-apartment/', views.add_apartment, name='add_apartment'),
    path('admin-panel/add-tenant/', views.add_tenant, name='add_tenant'),
    path('payments/', views.payments, name='payments'),
    path('admin-panel/payments/', views.admin_payments, name='admin_payments'),
    path('admin-panel/payments/add/', views.payment_form, name='add_payment'),
    path('admin-panel/payments/<int:pk>/edit/', views.payment_form, name='edit_payment'),
    path('tickets/', views.tickets, name='tickets'),
    path('tickets/add/', views.ticket_add, name='ticket_add'),
    path('admin-panel/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin-panel/tickets/<int:pk>/edit/', views.ticket_edit, name='ticket_edit'),
    path('export/mieszkania/', views.export_apartment_csv, name='export_mieszkania'),
    path('import/mieszkania/', views.import_apartment_csv, name='import_mieszkania'),

]
