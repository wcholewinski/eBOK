from django import template

register = template.Library()

@register.filter
def filter_alerts(alerts, severity):
    """Filtruje alerty po poziomie ważności (warning, info)"""
    return [alert for alert in alerts if alert.severity == severity]

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
