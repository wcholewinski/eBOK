from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from django.core.exceptions import PermissionDenied
from functools import wraps

def admin_required(view_func):
    """Dekorator sprawdzający czy użytkownik jest administratorem"""
    @wraps(view_func)  # Poprawne zachowanie metadanych funkcji
    @login_required    # Upewnij się, że użytkownik jest zalogowany
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('app:login')
        if not request.user.is_staff and not request.user.is_superuser:
            raise PermissionDenied("Nie masz uprawnień do tej strony")
        return view_func(request, *args, **kwargs)
    return wrapper

def tenant_required(view_func):
    """Sprawdza czy użytkownik jest najemcą"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'tenant'):
            return view_func(request, *args, **kwargs)
        return redirect(reverse('app:dashboard'))
    return login_required(_wrapped_view)
