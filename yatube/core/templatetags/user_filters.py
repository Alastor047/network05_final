from django import template
from django.forms import BoundField

register = template.Library()


@register.filter
def addclass(field: BoundField, css: str) -> str:
    """View-функция фильтра регистрации."""
    return field.as_widget(attrs={'class': css})
