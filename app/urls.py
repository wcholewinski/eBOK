from django.urls import path
from django.contrib.auth import views as auth_views
from app.views.views_main import (
    custom_logout, dashboard, admin_dashboard, add_apartment, edit_apartment,
    add_tenant, payments, admin_payments, payment_form, tickets, add_ticket,
    admin_tickets, ticket_edit, export_apartment_csv, import_apartment_csv,
    import_utility_data, analytics_dashboard, consumption_trends, profit_prediction,
    alerts_management, alerts_system, apartment_list, apartment_detail,
    tenant_list, tenant_detail, payment_list, payment_detail, ticket_detail
)
from app.views.admin_views import delete_all_tenants_and_apartments
from app.views.admin_views import (
    delete_apartment, edit_tenant, delete_tenant, bulk_delete_apartments, bulk_delete_tenants,
    delete_all_tenants_and_apartments
)
from app.api import views as api_views
from app.views import ml_import_view

app_name = 'app'

urlpatterns = [
    # AUTH
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True,
        next_page='app:dashboard'
    ), name='login'),
    path('logout/', custom_logout, name='logout'),

    # DASHBOARD
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),

    # Panel admina
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/apartments/add/', add_apartment, name='admin_add_apartment'),
    path('admin-panel/apartments/<int:pk>/edit/', edit_apartment, name='admin_edit_apartment'),
    path('admin-panel/tenants/add/', add_tenant, name='admin_add_tenant'),
    path('admin-panel/payments/', admin_payments, name='admin_payments'),
    path('admin-panel/payments/add/', payment_form, name='admin_add_payment'),
    path('admin-panel/payments/<int:pk>/edit/', payment_form, name='admin_edit_payment'),
    path('admin-panel/tickets/', admin_tickets, name='admin_tickets'),
    path('admin-panel/tickets/<int:pk>/edit/', ticket_edit, name='admin_edit_ticket'),

    # Zarządzanie mieszkaniami
    path('apartments/', apartment_list, name='apartment_list'),
    path('apartments/<int:pk>/', apartment_detail, name='apartment_detail'),

    # Zarządzanie najemcami
    path('tenants/', tenant_list, name='tenant_list'),
    path('tenants/<int:pk>/', tenant_detail, name='tenant_detail'),

    # Płatności
    path('payments/', payment_list, name='payment_list'),
    path('payments/<int:pk>/', payment_detail, name='payment_detail'),
    path('user/payments/', payments, name='user_payments'),

    # Zgłoszenia
    path('tickets/', tickets, name='tickets'),
    path('tickets/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('add_ticket/', add_ticket, name='add_ticket'),
    path('my-tickets/', tickets, name='user_tickets'),

    # IMPORT / EXPORT
    path('export/apartments/', export_apartment_csv, name='export_apartment_csv'),
    path('import/apartments/', import_apartment_csv, name='import_apartment_csv'),

    # Analytics
    path('admin-panel/analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('admin-panel/consumption-trends/', consumption_trends, name='consumption_trends'),
    path('admin-panel/profit-prediction/', profit_prediction, name='profit_prediction'),

    # Zarządzanie mieszkaniami i lokatorami
    path('admin-panel/delete-apartment/<int:pk>/', delete_apartment, name='delete_apartment'),
    path('admin-panel/edit-tenant/<int:pk>/', edit_tenant, name='edit_tenant'),
    path('admin-panel/delete-tenant/<int:pk>/', delete_tenant, name='delete_tenant'),
    path('admin-panel/bulk-delete-apartments/', bulk_delete_apartments, name='bulk_delete_apartments'),
    path('admin-panel/bulk-delete-tenants/', bulk_delete_tenants, name='bulk_delete_tenants'),
    path('admin-panel/delete-all/', delete_all_tenants_and_apartments, name='delete_all_tenants_and_apartments'),

    # Import utility consumption data
    path('import-utility-consumption/', import_utility_data, name='import_utility_consumption'),

    # ML Import and Analysis
    path('admin-panel/ml-import/', ml_import_view.import_and_analyze, name='import_and_analyze'),

    # Alerts system
    path('admin-panel/alerts/', alerts_management, name='alerts_management'),
    path('admin-panel/reset-data/', delete_all_tenants_and_apartments, name='delete_all_data'),
    path('alerts-system/', alerts_system, name='alerts_system'),

    # Sensor management
    path('admin-panel/sensors/', alerts_management, name='sensor_management'),  # Tymczasowo używa widoku alerts_management

    # API
    path('api/admin-stats/', api_views.api_admin_stats, name='api_admin_stats'),
    path('api/tenant-stats/', api_views.api_tenant_stats, name='api_tenant_stats'),
]
