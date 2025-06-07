from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from app.decorators import admin_required
from app.utils.api_helpers import get_admin_stats, get_tenant_stats
from app.models import Tenant

@admin_required
def api_admin_stats(request):
    """
    Zwraca statystyki dla panelu administratora w formacie JSON.
    """
    stats = get_admin_stats()
    return JsonResponse(stats)

@login_required
def api_tenant_stats(request):
    """
    Zwraca statystyki dla zalogowanego najemcy w formacie JSON.
    """
    # Sprawdzenie czy użytkownik ma profil najemcy
    try:
        tenant = Tenant.objects.get(user=request.user)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Użytkownik nie jest najemcą'}, status=403)

    stats = get_tenant_stats(tenant.id)
    return JsonResponse(stats)

