# Ten plik jest wymagany, aby Python traktował katalog jako pakiet
# Ten plik jest wymagany, aby katalog views był traktowany jako pakiet Python
# Import wszystkich widoków aby były dostępne przez app.views
from .views_main import *
from .admin_views import *
from .export_views import *
from .ml_import_view import *
from .export_filter_views import *
# Importowanie funkcji dekoratorów
from app.decorators import admin_required