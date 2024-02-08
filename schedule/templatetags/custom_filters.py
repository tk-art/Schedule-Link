from django import template

register = template.Library()

@register.filter(name='is_included')
def is_included(value, arg):
    return value in arg
