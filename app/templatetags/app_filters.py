from django import template

register = template.Library()

@register.filter
def get_range(value):
    """
    Filtr, który generuje zakres liczb od 0 do value-1.
    Użycie: {% for i in value|get_range %}
    """
    return range(value)

@register.filter
def get_item(dictionary, key):
    """
    Filtr do pobierania elementu z listy/słownika po indeksie/kluczu.
    Użycie: {{ my_list|get_item:index }}
    """
    if isinstance(dictionary, list) and key < len(dictionary):
        return dictionary[key]
    return None

@register.filter
def div(value, arg):
    """
    Dzieli value przez arg.
    Użycie: {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    Mnoży value przez arg.
    Użycie: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0
