from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Odejmuje arg od value"""
    try:
        if isinstance(value, str):
            value = value.replace(',', '.')
        if isinstance(arg, str):
            arg = arg.replace(',', '.')
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Dodaje arg do value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Mnoży value przez arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Dzieli value przez arg"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, arg):
    """Oblicza procent value z arg"""
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
