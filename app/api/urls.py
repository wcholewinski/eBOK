urlpatterns = [
    path('admin_stats/', views.api_admin_stats, name='api_admin_stats'),
    path('tenant_stats/', views.api_tenant_stats, name='api_tenant_stats'),
]
