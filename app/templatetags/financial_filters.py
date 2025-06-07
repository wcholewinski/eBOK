from django import template

register = template.Library()

def safe_operation(func):
    """Dekorator do bezpiecznego wykonywania operacji matematycznych"""
    def wrapper(value, arg):
        try:
            return func(float(value), float(arg))
        except (ValueError, TypeError, ZeroDivisionError):
            return 0
    return wrapper

@register.filter(name='mul')
@safe_operation
def multiply(value, arg):
    """Mnoży wartość przez argument"""
    return value * arg

@register.filter(name='div')
@safe_operation
def divide(value, arg):
    """Dzieli wartość przez argument"""
    return value / arg if arg != 0 else 0

@register.filter(name='sub')
@safe_operation
def subtract(value, arg):
    """Odejmuje argument od wartości"""
    return value - arg

@register.filter(name='percent')
@safe_operation
def percentage(value, arg):
    """Oblicza procent wartości"""
    return value * 100 / arg if arg != 0 else 0
