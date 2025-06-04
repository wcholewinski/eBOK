from django.contrib.auth import views as auth_views
from . import views
from .views import custom_logout
from django.urls import path

app_name = 'app'

urlpatterns = [
    # Panel admina
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/apartments/add/', views.add_apartment, name='admin_add_apartment'),
    path('admin/apartments/<int:pk>/edit/', views.edit_apartment, name='admin_edit_apartment'),

    # Admin może dodawać najemców
    path('admin/tenants/add/', views.add_tenant, name='admin_add_tenant'),
    path('admin/payments/', views.admin_payments, name='admin_payments'),
    path('admin/payments/add/', views.payment_form, name='admin_add_payment'),
    path('admin/payments/<int:pk>/edit/', views.payment_form, name='admin_edit_payment'),
    path('admin/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin/tickets/<int:pk>/edit/', views.ticket_edit, name='admin_edit_ticket'),

    # AUTH
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True,
        next_page='app:dashboard'
    ), name='login'),
    path('logout/', custom_logout, name='logout'),

    # DASHBOARD
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # USER SECTION
    path('user/payments/', views.payments, name='user_payments'),
    path('tickets/', views.tickets, name='tickets'),
    path('add_ticket/', views.add_ticket, name='add_ticket'),
    path('my-tickets/', views.tickets, name='user_tickets'),

    # IMPORT / EXPORT
    path('export/apartments/', views.export_apartment_csv, name='export_apartment_csv'),
    path('import/apartments/', views.import_apartment_csv, name='import_apartment_csv'),

    # Analytics
    path('admin/analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('admin/consumption-trends/', views.consumption_trends, name='consumption_trends'),
    path('admin/sensors/', views.sensor_management, name='sensor_management'),
    path('admin/alerts/', views.alerts_management, name='alerts_management'),

# API dla danych w czasie rzeczywistym
    path('api/sensor-data/<int:apartment_id>/', views.sensor_data_api, name='sensor_data_api'),
    path('api/predictions/<int:apartment_id>/', views.predictions_api, name='predictions_api'),
]
