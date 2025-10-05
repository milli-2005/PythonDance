from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        return value

@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value