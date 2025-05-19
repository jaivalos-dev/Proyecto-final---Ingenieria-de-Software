# rrhh/templatetags/rrhh_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(lista, indice):
    """Obtener un elemento de una lista por su índice"""
    try:
        return lista[indice]
    except:
        return None