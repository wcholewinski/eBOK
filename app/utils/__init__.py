# Pakiet z funkcjami pomocniczymi dla aplikacji eBOK
# Ten plik jest wymagany, aby katalog utils był traktowany jako pakiet Python

def calculate_statistics(apartment_id):
    """
    Oblicza podstawowe statystyki dla mieszkania o podanym ID.
    """
    # Importy wewnątrz funkcji aby uniknąć problemów z zależnościami cyklicznymi
    # i problemów z kompatybilnością przy starcie aplikacji
    from app.models import Apartment, Tenant, Payment

    try:
        apartment = Apartment.objects.get(id=apartment_id)
    except Apartment.DoesNotExist:
        return {'error': f'Mieszkanie o ID {apartment_id} nie istnieje'}

    # Historia płatności
    payment_history = []
    for tenant in Tenant.objects.filter(apartment_id=apartment_id):
        for payment in Payment.objects.filter(tenant=tenant).order_by('date'):
            payment_history.append({
                'date': payment.date,
                'amount': payment.amount,
                'type': payment.type,
                'status': payment.status
            })

    return {
        'apartment_number': apartment.number,
        'apartment_floor': apartment.floor,
        'apartment_area': apartment.area,
        'total_fees': apartment.total_fees(),
        'payment_history': payment_history
    }