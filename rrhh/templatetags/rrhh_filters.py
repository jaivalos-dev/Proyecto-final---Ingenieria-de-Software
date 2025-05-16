from django import template

register = template.Library()

@register.filter
def get_item(list, index):
    """
    Obtiene un elemento de una lista por su índice
    Uso: {{ mylist|get_item:index }}
    """
    try:
        return list[index]
    except (IndexError, TypeError):
        return None