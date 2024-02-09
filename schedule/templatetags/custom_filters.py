from django import template
import json

register = template.Library()

@register.filter(name='is_included')
def is_included(value, arg):
    return value in arg

@register.filter(name='to_json')
def to_json(value):
    return json.dumps(value)
