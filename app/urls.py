from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from .views import custom_logout

app_name = 'app'

admin_patterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('apartments/add/', views.add_apartment, name='add_apartment'),
    path('tenants/add/', views.add_tenant, name='add_tenant'),
    path('payments/', views.admin_payments, name='payments'),
    path('payments/add/', views.payment_form, name='add_payment'),
    path('payments/<int:pk>/edit/', views.payment_form, name='edit_payment'),
    path('tickets/', views.admin_tickets, name='tickets'),
    path('tickets/<int:pk>/edit/', views.ticket_edit, name='edit_ticket'),
]

urlpatterns = [
    # ----- AUTH -----
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/', custom_logout, name='logout'),

    # ----- DASHBOARD -----
    path('', views.dashboard, name='dashboard'),
    path('admin/', include((admin_patterns, 'app'), namespace='admin')),

    # ----- USER -----
    path('payments/', views.payments, name='user_payments'),
    path('tickets/', views.tickets, name='user_tickets'),
    path('tickets/add/', views.ticket_add, name='add_ticket'),

    # ----- IMPORT / EXPORT -----
    path('export/apartments/', views.export_apartment_csv, name='export_apartments'),
    path('import/apartments/', views.import_apartment_csv, name='import_apartments'),
]
