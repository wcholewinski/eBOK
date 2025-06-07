# Klasa dla zachowania kompatybilności wstecznej
from app.utils.ml_analysis import PredictiveAnalysis

class MLAnalysis(PredictiveAnalysis):
    """Klasa zachowana dla kompatybilności wstecznej.

    Ta klasa pozwala na używanie starych importów z app.ml_analysis
    i kieruje wszystkie wywołania do właściwej implementacji w app.utils.ml_analysis.
    """
    pass