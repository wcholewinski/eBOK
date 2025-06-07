from django import template

register = template.Library()

@register.filter
def index(lst, i):
    try:
        return lst[i]
    except (IndexError, TypeError):
        return None

@register.filter
def add(value, arg):
    return value + arg

@register.filter
def dict_values_first(dict_obj):
    """Zwraca pierwszą wartość z obiektu dict_values"""
    if not dict_obj:
        return []
    try:
        values = list(dict_obj.values())
        if values:
            return values[0]
        return []
    except (AttributeError, TypeError):
        return []
